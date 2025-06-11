"""
Основной модуль для обработки событий трекинга Open edX и отправки xAPI-высказываний.

"""

from datetime import datetime
import json
import logging
import os
import signal
import sys
import threading
import time
from types import FrameType
from typing import Any, Dict, Optional
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

from pyinotify import WatchManager, Notifier, NotifierError, EventsCodes, ProcessEvent
from tincan import StatementList

from xapi_bridge import client, converter, exceptions, settings
from xapi_bridge.constants import OPENEDX_OAUTH2_TOKEN_URL
from xapi_bridge.historical_processor import process_historical_logs

if settings.HTTP_PUBLISH_STATUS:
    from xapi_bridge.server import httpd


logger = logging.getLogger('edX-xapi-bridge main')


class QueueManager:
    """Управление очередью и пакетной отправкой xAPI-высказываний."""

    def __init__(self):
        self.cache: list = []
        self.cache_lock = threading.Lock()
        self.publish_timer: Optional[threading.Timer] = None
        self.publish_retries = 0
        self.total_published = 0

    def __del__(self):
        self.destroy()

    def destroy(self) -> None:
        """Очистка ресурсов."""
        if self.publish_timer:
            self.publish_timer.cancel()

    def push(self, stmt: Dict[str, Any]) -> None:
        """Добавление высказывания в очередь."""
        with self.cache_lock:
            self.cache.append(stmt)

        if len(self.cache) == 1 and settings.PUBLISH_MAX_WAIT_TIME > 0:
            self.publish_timer = threading.Timer(settings.PUBLISH_MAX_WAIT_TIME, self.publish)
            self.publish_timer.start()

        if len(self.cache) >= settings.PUBLISH_MAX_PAYLOAD:
            self.publish()

    def publish(self) -> None:
        """Отправка высказываний в LRS."""
        with self.cache_lock:
            if not self.cache:
                return

            statements = StatementList(self.cache)
            while statements:
                try:
                    client.lrs_publisher.publish_statements(statements)
                    self.total_published += len(statements)
                    logger.info(f"Отправлено {self.total_published} высказываний")
                    self._check_benchmark()
                    break
                except exceptions.XAPIBridgeLRSConnectionError as e:
                    self._handle_connection_error(e, statements)
                except exceptions.XAPIBridgeStatementError as e:
                    self._handle_storage_error(e, statements)

            self.cache.clear()
            if self.publish_timer:
                self.publish_timer.cancel()

    def _check_benchmark(self) -> None:
        """Проверка достижения тестового показателя."""
        if settings.TEST_LOAD_SUCCESSFUL_STATEMENTS_BENCHMARK > 0:
            if self.total_published >= settings.TEST_LOAD_SUCCESSFUL_STATEMENTS_BENCHMARK:
                logger.info(f"Достигнут показатель: {self.total_published} высказываний")

    def _handle_connection_error(self, e: exceptions.XAPIBridgeLRSConnectionError, statements: StatementList) -> None:
        """Обработка ошибок соединения."""
        if self.publish_retries >= settings.PUBLISH_MAX_RETRIES:
            e.err_fail()
        self.publish_retries += 1
        time.sleep(1)

    def _handle_storage_error(self, e: exceptions.XAPIBridgeStatementError, statements: StatementList) -> None:
        """Обработка ошибок хранения."""
        logger.warning(f"Ошибка хранения: {e.message}")
        statements.remove(e.statement)


class NotifierLostINodeException(NotifierError):
    """Исключение при потере отслеживаемого файла."""


class TailHandler(ProcessEvent):
    """Обработчик изменений лог-файла."""

    MASK = EventsCodes.OP_FLAGS['IN_MODIFY'] | EventsCodes.OP_FLAGS['IN_MOVE_SELF'] | EventsCodes.OP_FLAGS['IN_DELETE_SELF']

    def __init__(self, filename: str, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.ifp = open(filename, 'r', 1)
        self.ifp.seek(0, 2)
        self.publish_queue = QueueManager()
        self.race_buffer = ''

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.publish_queue.publish()
        self.publish_queue.destroy()
        self.ifp.close()

    def check_NOT_DAMAGED(self, event) -> Any:
        """
        Проверка на целостность полученного события
        в логе события от Оценки просмотренного события
        (с watch_times) превышают лимит и ломают формат
        """
        if event[-1] != '}':
            return event + '\"}}}}'
        return event

    def process_IN_MODIFY(self, event) -> None:
        """Обработка изменений файла."""
        buff = self.race_buffer + self.ifp.read()

        if buff and buff[-1] != '\n':
            self.race_buffer = buff
            return

        self.race_buffer = ''
        for line in buff.split('\n'):
            if not line:
                continue
            try:
                line = self.check_NOT_DAMAGED(line)
                event = json.loads(line)
                statements = converter.to_xapi(event)
                if statements:
                    for stmt in statements:
                        self.publish_queue.push(stmt)
            except json.JSONDecodeError as e:
                logger.warning(f"Ошибка json-конвертации события: {e}. Событие {event}")
            except Exception as e:
                raise exceptions.XAPIBridgeSkippedConversion(
                    event_type=event['event_type'],
                    reason=f"Ошибка обработки события: {e}"
                ) from e

    def process_IN_MOVE_SELF(self, event) -> None:
        logger.info("Файл перемещен")
        raise NotifierLostINodeException("IN_MOVE_SELF")

    def process_IN_DELETE_SELF(self, event) -> None:
        logger.info("Файл удален")
        raise NotifierLostINodeException("IN_DELETE_SELF")


def watch(file_path: str) -> None:
    """Запуск наблюдения за файлом."""
    logger.info(f"Начало наблюдения за {file_path}")
    wm = WatchManager()

    try:
        with TailHandler(file_path) as handler:
            notifier = Notifier(wm, handler,
                read_freq=settings.NOTIFIER_READ_FREQ,
                timeout=settings.NOTIFIER_POLL_TIMEOUT)
            wm.add_watch(file_path, TailHandler.MASK)
            notifier.loop()
    except NotifierLostINodeException:
        logger.info("Перезапуск наблюдения...")
        watch(file_path)
    finally:
        logger.info("Завершение наблюдения")


def signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Обработчик сигналов завершения."""
    logger.info("Получен сигнал завершения")
    if settings.HTTP_PUBLISH_STATUS:
        logger.info("Остановка HTTP-сервера")
        httpd.shutdown()
        httpd.server_close()
    sys.exit(0)


# Регистрация обработчиков сигналов
for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
    signal.signal(sig, signal_handler)


def setup_logging() -> None:
    """Настройка логирования."""
    level = logging.DEBUG if settings.DEBUG_MODE else logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        level=level,
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler()
        ]
    )

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[LoggingIntegration()]
            )
        except ImportError:
            logger.warning("Sentry SDK не установлен")


class StatusOKRequestHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для проверки статуса."""

    def do_GET(self):
        """Обработка GET-запроса."""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        """Переопределение логирования HTTP-сервера."""
        logger.info("%s - %s", self.client_address[0], format % args)


def main():
    """Основная функция запуска."""
    parser = argparse.ArgumentParser(description='xAPI Bridge для Open edX')
    parser.add_argument('log_file', nargs='?', default='/edx/var/log/tracking/tracking.log',
                      help='Путь к файлу логов (по умолчанию: /edx/var/log/tracking/tracking.log)')
    parser.add_argument('--historical-log', action='store_true',
                      help='Обработать исторический лог')
    parser.add_argument('--test-mode', action='store_true',
                      help='Запустить в тестовом режиме (без отправки в LRS)')
    parser.add_argument('--output-file',
                      help='Путь к файлу для сохранения высказываний в тестовом режиме')
    
    args = parser.parse_args()

    setup_logging()

    # Инициализация HTTP-сервера
    if settings.HTTP_PUBLISH_STATUS:
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

    if args.historical_log:
        process_historical_logs(args.log_file, test_mode=args.test_mode, output_file=args.output_file)
    else:
        # Запуск наблюдения за свежим логом
        logger.info(f"Начало работы: {datetime.now().isoformat()}")
        watch(args.log_file)


if __name__ == '__main__':
    main()
