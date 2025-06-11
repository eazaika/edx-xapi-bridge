"""
Модуль для обработки исторических логов Open edX.
"""

import argparse
import json
import logging
import os
import time  # Для замера времени
from tincan import StatementList
import uuid
import datetime
import zoneinfo  # для работы с часовыми поясами

from xapi_bridge import client, exceptions, settings
from xapi_bridge.statements.video import (
    VideoStatement, VideoCompleteStatement, VideoCheckStatement
)
from xapi_bridge.statements.problem import (
    ProblemCheckStatement
)
from xapi_bridge.statements.vertical_block import VerticalBlockCompleteStatement
from xapi_bridge.statements.course import (
    CourseEnrollmentStatement, CourseUnenrollmentStatement,
    CourseCompletionStatement, CourseExpellStatement
)
from xapi_bridge.statements.attachment import AttachmentStatement

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Список поддерживаемых типов событий
SUPPORTED_EVENT_TYPES = {
    'pause_video': VideoStatement,
    'stop_video': VideoCompleteStatement,
    'video_check': VideoCheckStatement,
    'problem_check': ProblemCheckStatement,
    'edx.attachment': AttachmentStatement,
    'complete_vertical': VerticalBlockCompleteStatement,
    'edx.course.enrollment.activated': CourseEnrollmentStatement,
    'edx.course.enrollment.deactivated': CourseUnenrollmentStatement,
    'edx.course.completed': CourseCompletionStatement,
    'edx.course.expell': CourseExpellStatement
}

def save_statements_to_file(statements, output_file):
    """
    Сохраняет высказывания в JSON файл.

    Args:
        statements: Список xAPI высказываний
        output_file: Путь к файлу для сохранения
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for statement in statements:
                f.write(json.dumps(statement, ensure_ascii=False) + '\n')
        logger.info(f"Высказывания сохранены в файл: {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в файл: {e}")

def process_historical_logs(log_file, batch_size=100, test_mode=False, output_file=None):
    """
    Обрабатывает исторические логи, преобразует в xAPI и отправляет в LRS.

    Args:
        log_file (str): Путь к файлу логов.
        batch_size (int): Размер пакета для отправки в LRS.
        test_mode (bool): Если True, высказывания сохраняются в файл вместо отправки в LRS.
        output_file (str): Путь к файлу для сохранения высказываний в тестовом режиме.
    """
    logger.info(f"Начинаем обработку исторического лога: {log_file}")

    if not test_mode:
        # Проверка подключения к LRS
        try:
            response = client.lrs_publisher.lrs.about()
            if response.success:
                logger.info(f"Успешное подключение к LRS: {settings.LRS_ENDPOINT}")
            else:
                raise exceptions.XAPIBridgeLRSConnectionError(response)
        except Exception as e:
            logger.error(f"Ошибка подключения к LRS: {e}")
            return

    try:
        start_time = time.time()
        statements = read_and_transform_logs(log_file)

        if test_mode:
            if output_file:
                save_statements_to_file(statements, output_file)
            else:
                # Если файл не указан, выводим в консоль
                for statement in statements:
                    print(json.dumps(statement, ensure_ascii=False, indent=2))
        else:
            # Разделение на пакеты и отправка в LRS
            for i in range(0, len(statements), batch_size):
                batch = statements[i:i + batch_size]
                try:
                    client.lrs_publisher.publish_statements(batch)
                    logger.info(f"Отправлено {len(batch)} утверждений в LRS.")
                except Exception as e:
                    logger.error(f"Ошибка при отправке пакета в LRS: {e}")

        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Обработка исторического лога завершена. Время выполнения: {duration:.2f} секунд")

    except FileNotFoundError:
        logger.error(f"Файл не найден: {log_file}")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return

def read_and_transform_logs(log_file):
    """
    Читает JSON лог, преобразует записи в формат xAPI.

    Args:
        log_file (str): Путь к файлу JSON лога.

    Returns:
        list: Список xAPI утверждений.
    """
    statements = []
    with open(log_file, 'r') as f:
        for line in f:  # Читать построчно для больших файлов
            try:
                log_entry = json.loads(line)
                xapi_statement = transform_json_log_entry_to_xapi(log_entry)  # Функция преобразования
                if xapi_statement:
                    statements.append(xapi_statement)
            except json.JSONDecodeError:
                logger.warning(f"Не удалось декодировать JSON: {line}")
            except Exception as e:
                logger.error(f"Ошибка при обработке JSON: {e}")

    return statements

def transform_json_log_entry_to_xapi(log_entry):
    """
    Преобразует запись из JSON лога в xAPI утверждение.

    Args:
        log_entry (dict): Запись из JSON лога.

    Returns:
        dict: xAPI утверждение в формате словаря (или None, если преобразование не удалось).

    Raises:
        XAPIBridgeSkippedConversion: Если тип события не поддерживается или требует пропуска.
    """
    try:
        event_type = log_entry.get('event_type')
        
        # Нормализуем тип события только для видео-событий
        if 'xblock-video' in event_type:
            event_type = event_type.replace("xblock-video.", "").strip()
        
        # Проверяем, поддерживается ли тип события
        if event_type not in SUPPORTED_EVENT_TYPES:
            raise exceptions.XAPIBridgeSkippedConversion(
                event_type,
                f"Тип события не поддерживается: {event_type}"
            )
        
        # Создаем соответствующий statement
        statement = SUPPORTED_EVENT_TYPES[event_type](log_entry)
        
        # Преобразуем statement в словарь для отправки в LRS
        statement_dict = statement.as_version('1.0.3')
        
        # Добавляем стандартные поля xAPI
        moscow_tz = zoneinfo.ZoneInfo('Europe/Moscow')
        moscow_time = datetime.datetime.now(moscow_tz)
        statement_dict.update({
            "stored": moscow_time.isoformat()
        })
        
        return statement_dict
        
    except exceptions.XAPIBridgeSkippedConversion as e:
        logger.info(f"Пропуск события: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Ошибка преобразования JSON в xAPI: {e}")
        return None