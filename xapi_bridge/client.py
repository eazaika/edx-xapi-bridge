"""
Клиент для отправки xAPI-высказываний в LRS.

Мигрировано на Python 3.10 с:
- Аннотациями типов
- Современными библиотеками
- Улучшенной обработкой ошибок
"""

import importlib
import json
import logging
import socket
from typing import Any, Optional

from tincan import RemoteLRS, StatementList
from tincan.remote_lrs import RemoteLRSResponse

from xapi_bridge import exceptions, settings
from xapi_bridge.lrs_backends.learninglocker import LRSBackend


logger = logging.getLogger(__name__)


class XAPIBridgeLRSPublisher:
    """Обертка для отправки xAPI-высказываний в LRS."""

    def __init__(self):
        self.lrs = self._configure_lrs()
        self.backend = LRSBackend()

    def _configure_lrs(self) -> RemoteLRS:
        """Конфигурация подключения к LRS."""
        config = {
            'endpoint': settings.LRS_ENDPOINT,
            'version': "1.0.3"
        }

        if settings.LRS_BASICAUTH_HASH:
            config['auth'] = f"Basic {settings.LRS_BASICAUTH_HASH}"
        else:
            config.update({
                'username': settings.LRS_USERNAME,
                'password': settings.LRS_PASSWORD
            })

        return RemoteLRS(**config)

    def publish_statements(self, statements: StatementList) -> RemoteLRSResponse:
        """
        Отправка пакета высказываний в LRS.
        
        Args:
            statements: Список xAPI-высказываний
            
        Returns:
            Ответ от LRS
            
        Raises:
            XAPIBridgeLRSConnectionError: Ошибка подключения
            XAPIBridgeStatementStorageError: Ошибка сохранения
        """
        try:
            response = self.lrs.save_statements(statements)
            self._handle_response(response, statements)
            return response
        except (socket.gaierror, ConnectionRefusedError) as e:
            error_msg = f"Ошибка подключения к LRS: {str(e)}"
            logger.error(error_msg)
            raise exceptions.XAPIBridgeLRSConnectionError(message=error_msg) from e

    def _handle_response(self, response: RemoteLRSResponse, statements: StatementList) -> None:
        """Обработка ответа от LRS."""
        if response.success:
            logger.info(f"Успешно отправлено {len(statements)} высказываний")
            return

        try:
            response_data = json.loads(response.data)
        except json.JSONDecodeError:
            response_data = {}

        if self.backend.request_unauthorised(response_data):
            error_msg = "Ошибка авторизации в LRS"
            logger.error(error_msg)
            raise exceptions.XAPIBridgeLRSConnectionError(message=error_msg)

        if self.backend.response_has_storage_errors(response_data):
            bad_index = self.backend.parse_error_response_for_bad_statement(response_data)
            bad_statement = statements[bad_index] if bad_index is not None else None
            error_msg = f"Ошибка сохранения высказывания: {response_data.get('message', '')}"
            logger.error(error_msg)
            raise exceptions.XAPIBridgeStatementStorageError(
                statement=bad_statement,
                message=error_msg
            )


# Инициализация клиента по умолчанию
lrs_publisher = XAPIBridgeLRSPublisher()
