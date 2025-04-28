"""
Базовый абстрактный класс для бэкендов xAPI хранилищ.

Мигрировано на Python 3.10 с:
- Современным объявлением метаклассов
- Аннотациями типов
- Улучшенной документацией
"""

from abc import ABC, abstractmethod
from typing import Any


class LRSBackendBase(ABC):
    """
    Абстрактный базовый класс для реализации бэкендов xAPI LRS.

    Определяет обязательные методы для обработки ответов хранилища.
    """

    @abstractmethod
    def request_unauthorised(self, response_data: Any) -> bool:
        """
        Проверяет наличие ошибки авторизации в ответе.

        Args:
            response_data: Данные ответа от LRS

        Returns:
            True если обнаружена ошибка авторизации
        """

    @abstractmethod
    def response_has_errors(self, response_data: Any) -> bool:
        """
        Проверяет общее наличие ошибок в ответе.

        Args:
            response_data: Данные ответа от LRS
            
        Returns:
            True если ответ содержит ошибки
        """

    @abstractmethod
    def response_has_storage_errors(self, response_data: Any) -> bool:
        """
        Проверяет ошибки хранения данных.

        Args:
            response_data: Данные ответа от LRS
            
        Returns:
            True если есть ошибки сохранения данных
        """

    @abstractmethod
    def parse_error_response_for_bad_statement(self, response_data: Any) -> int:
        """
        Идентифицирует индекс некорректного высказывания.

        Args:
            response_data: Данные ответа с ошибкой

        Returns:
            Индекс проблемного высказывания

        Raises:
            XAPIBridgeLRSBackendResponseParseError: Ошибка парсинга ответа
        """
