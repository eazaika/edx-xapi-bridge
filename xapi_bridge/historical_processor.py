"""
Берет старые логи edX и считывает их и отправляет в LRS
"""

import argparse
import json
import logging
import os
import time  # Для замера времени
from tincan import StatementList

from xapi_bridge import client

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_historical_logs(log_file, batch_size=100):
    """
    Обрабатывает исторические логи, преобразует в xAPI и отправляет в LRS.

    Args:
        log_file (str): Путь к файлу логов.
        batch_size (int): Размер пакета для отправки в LRS.
    """
    logger.info(f"Начинаем обработку исторического лога: {log_file}, формат: {log_format}")

    # Проверка подключения к LRS
    try:
        response = client.lrs_publisher.lrs.about()
        if response.success:
            logger.info(f"Успешное подключение к LRS: {settings.LRS_ENDPOINT}")
        else:
            raise exceptions.XAPIBridgeLRSConnectionError(response)
    except Exception as e:
        logger.error(f"Ошибка подключения к LRS: {e}")

    try:
        start_time = time.time()
        statements = read_and_transform_logs(log_file)

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
        dict: xAPI утверждение (или None, если преобразование не удалось).
    """
    #  Реализуйте логику преобразования данных
    #  Логика преобразования уже есть в остальных файлах, надо только на нее направить обработку

    #  Пример (просто чтобы не падало):
    try:
        actor = {
            "objectType": "Agent",
            "mbox": f"mailto:{log_entry['user_email']}" # Пример
        }
        verb = {
            "id": "http://adlnet.gov/expapi/verbs/viewed", # Пример
            "display": {"en-US": "viewed"}
        }
        object = {
            "objectType": "Activity",
            "id": log_entry['course_id'] # Пример
        }
        statement = {
            "actor": actor,
            "verb": verb,
            "object": object,
            "timestamp": log_entry.get('time')  # Важно: Учитывайте формат времени
        }
        return statement
    except Exception as e:
        logger.error(f"Ошибка преобразования JSON в xAPI: {e}")
        return None

