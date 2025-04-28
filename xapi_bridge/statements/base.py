"""
Базовые классы для построения xAPI-высказываний из данных трекинга Open edX.

Мигрировано на Python 3.10 с:
- Современным синтаксисом super()
- Аннотациями типов
- Обработкой исключений Python 3
- F-строками
- Явным преобразованием типов данных
"""

from copy import deepcopy
import json
from typing import Dict, Optional, Any

from tincan import (
    Agent, AgentAccount, Context, Statement,
    ActivityDefinition, LanguageMap, Result
)

from xapi_bridge import constants, exceptions, lms_api, settings


class LMSTrackingLogStatement(Statement):
    """Базовый класс для преобразования событий трекинга Open edX в xAPI-высказывания."""

    user_api_client = lms_api.user_api_client

    def __init__(self, event: Dict[str, Any], *args, **kwargs):
        """
        Инициализирует xAPI-высказывание на основе события трекинга.

        Args:
            event: Событие из логов трекинга Open edX
            args: Позиционные аргументы базового класса
            kwargs: Именованные аргументы базового класса

        Raises:
            XAPIBridgeStatementConversionError: Ошибка преобразования данных
        """
        try:
            kwargs.update(
                actor=self.get_actor(event),
                verb=self.get_verb(event),
                object=self.get_object(event),
                result=self.get_result(event),
                context=self.get_context(event),
                timestamp=self.get_timestamp(event),
                authority=self.get_authority(),
            )
            
            # Обработка вложений (для событий типа 'edx.attachment')
            if event.get('event_type') == 'edx.attachment':
                kwargs['attachments'] = self.get_attachment(event)

            super().__init__(*args, **kwargs)

        except (ValueError, TypeError, AttributeError) as e:
            error_msg = f"Ошибка преобразования в классе {self.__class__.__name__}: {str(e)}"
            raise exceptions.XAPIBridgeStatementConversionError(event=event, message=error_msg) from e

    def _get_edx_user_info(self, username: str) -> Dict[str, Any]:
        """Получает информацию о пользователе через API Open edX."""
        return self.user_api_client.get_edx_user_info(username)

    def get_authority(self) -> Agent:
        """Возвращает агента-источника для xAPI-высказываний."""
        return Agent(
            name=settings.ORG_NAME,
            mbox=f'mailto:{settings.ORG_EMAIL}',
        )

    def get_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает и парсит данные события в зависимости от источника."""
        if event.get('event_source', 'server').lower() == 'browser':
            return json.loads(event.get('event', '{}'))
        return event.get('event', {})

    def get_actor(self, event: Dict[str, Any]) -> Optional[Agent]:
        """Создает xAPI Agent на основе данных пользователя."""
        try:
            username = event['event']['username']
        except KeyError:
            username = event['context']['module'].get('username', 'anonymous')

        try:
            user_info = self._get_edx_user_info(username)
        except exceptions.UserNotFoundError:
            return None

        # Обработка анонимных пользователей
        if not user_info.get('email'):
            return None

        # Конфигурация для системы UNTI
        if settings.UNTI_XAPI and user_info.get('unti_id'):
            return Agent(
                name=user_info['fullname'],
                account=AgentAccount(
                    name=str(user_info['unti_id']),  # Явное преобразование в строку
                    home_page='https://my.2035.university'
                )
            )

        return Agent(
            name=user_info['fullname'],
            mbox=f'mailto:{user_info["email"]}',
        )

    def get_context(self, event: Dict[str, Any]) -> Context:
        """Создает контекст xAPI с информацией о платформе."""
        return Context(platform=settings.OPENEDX_PLATFORM_URI)

    def get_timestamp(self, event: Dict[str, Any]) -> str:
        """Извлекает временную метку из события."""
        return event['time']

    def get_result(self, event: Dict[str, Any]) -> Result:
        """Формирует результат выполнения действия."""
        event_data = self.get_event_data(event)
        return Result(
            success=event_data.get('success', True),
            completion=event_data.get('completion', True),
        )


class ReferringActivityDefinition(ActivityDefinition):
    """Определение активности-источника для контекста xAPI."""
    
    def __init__(self, event: Dict[str, Any], *args, **kwargs):
        """
        Инициализирует определение активности-источника.

        Args:
            event: Событие трекинга для построения контекста
        """
        kwargs.update({
            'type': constants.XAPI_CONTEXT_REFERRER,
            'name': LanguageMap({'en-US': 'Referrer'}),
            'description': LanguageMap({'en-US': 'Referring activity in Open edX course'})
        })
        super().__init__(*args, **kwargs)
