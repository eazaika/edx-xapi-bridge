"""
Утилита для нагрузочного тестирования xAPI-бриджа.

"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import TextIO

from xapi_bridge import settings


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_test_data(src_file: Path, output_file: Path, iterations: int, delay: float) -> None:
    """
    Генерирует тестовые данные для нагрузочного тестирования.

    Args:
        src_file: Путь к файлу с исходными событиями
        output_file: Путь к файлу для записи тестовых данных
        iterations: Количество итераций записи
        delay: Задержка между итерациями в секундах
    """
    try:
        with src_file.open('r', encoding='utf-8') as src:
            base_data = src.read()

        with output_file.open('a', encoding='utf-8') as log:
            for i in range(1, iterations + 1):
                log.write(f"{base_data}\n")
                log.flush()
                logger.info(f"Итерация {i}/{iterations} записана")
                time.sleep(delay)

    except IOError as e:
        logger.error(f"Ошибка работы с файлами: {str(e)}")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Генератор тестовой нагрузки для xAPI-бриджа"
    )
    parser.add_argument(
        '-s', '--source',
        type=Path,
        default=Path("xapi_bridge/test/fixtures/test_loadtest_events_0.json"),
        help="Путь к исходному файлу с событиями"
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path("xapi_bridge/test/fixtures/test_loadtest_event_log.log"),
        help="Путь к файлу для записи тестовых данных"
    )
    return parser.parse_args()


def main() -> None:
    """Основная функция выполнения."""
    args = parse_args()

    logger.info("Старт генерации тестовой нагрузки")
    logger.info(f"Источник: {args.source}")
    logger.info(f"Назначение: {args.output}")
    logger.info(f"Итераций: {settings.TEST_LOAD_TRACKING_TOTAL_LOG_WRITES}")
    logger.info(f"Интервал: {settings.TEST_LOAD_SLEEP_SECS_BETWEEN_WRITES} сек")

    generate_test_data(
        src_file=args.source,
        output_file=args.output,
        iterations=settings.TEST_LOAD_TRACKING_TOTAL_LOG_WRITES,
        delay=settings.TEST_LOAD_SLEEP_SECS_BETWEEN_WRITES
    )

    logger.info("Генерация тестовых данных завершена успешно")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        sys.exit(0)
