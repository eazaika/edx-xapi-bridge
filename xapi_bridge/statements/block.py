"""
Определения активностей для курсовых блоков Open edX.

Мигрировано на Python 3.10 с:
- Аннотациями типов
- Современными super() вызовами
- F-строками
- Обработкой Unicode по умолчанию
"""

from typing import Dict, Any, Optional

from tincan import (
    Activity, ActivityDefinition, ActivityList,
    Context, ContextActivities, LanguageMap
)

from . import base, course
from xapi_bridge import constants, settings


class BlockActivityDefinition(ActivityDefinition):
    """Определение активности для курсового блока."""
    
    def __init__(self, event: Dict[str, Any], *args, **kwargs):
        """
        Инициализирует определение активности блока.

        Args:
            event: Событие трекинга с данными о блоке
        """
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            display_name = "Составной КИМ"

        kwargs.update({
            'type': constants.XAPI_ACTIVITY_MODULE,
            'name': LanguageMap({'ru-RU': display_name}),
            'description': LanguageMap({'en-US': 'Course vertical section in Open edX'})
        })
        super().__init__(*args, **kwargs)  # Современный вызов super


class BlockAssessmentDefinition(ActivityDefinition):
    """Определение активности для оценочного блока."""
    
    def __init__(self, event: Dict[str, Any], *args, **kwargs):
        """
        Инициализирует определение оценочного блока.

        Args:
            event: Данные события с информацией о блоке
        """
        try:
            display_name = event['display_name']
        except KeyError:
            display_name = "Course Block"

        # Определение типа блока по usage_key
        usage_key = event.get('usage_key', '')
        if 'vertical+block' in usage_key:
            block_type = 'vertical block'
        elif 'sequential+block' in usage_key:
            block_type = 'sequential block'
        elif 'chapter+block' in usage_key:
            block_type = 'chapter block'
        else:
            block_type = 'undefined'

        kwargs.update({
            'type': constants.XAPI_ASSESSMENT_MODULE,
            'name': LanguageMap({'ru-RU': display_name}),
            'description': LanguageMap({'en-US': block_type})
        })

        # Добавление расширений для UNTI
        if settings.UNTI_XAPI:
            self._add_unti_extensions(event, kwargs)

        super().__init__(*args, **kwargs)

    def _add_unti_extensions(self, event: Dict[str, Any], kwargs: Dict[str, Any]):
        """Добавляет расширения для интеграции с UNTI."""
        try:
            ext_url = f'{settings.UNTI_XAPI_EXT_URL}/question_amount'
            kwargs.setdefault('extensions', {})[ext_url] = event['childrens']
        except KeyError:
            pass


class BaseCoursewareBlockStatement(base.LMSTrackingLogStatement):
    """Базовый класс для взаимодействий с курсовыми блоками."""
    
    def _get_activity_id(self, event: Dict[str, Any]) -> str:
        """
        Генерирует IRI идентификатор активности.

        Args:
            event: Событие с контекстом блока

        Returns:
            Строка с IRI идентификатором
        """
        return constants.BLOCK_OBJECT_ID_FORMAT.format(
            platform=settings.OPENEDX_PLATFORM_URI,
            block_usage_key=event['context']['module']['usage_key']
        )

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """
        Строит иерархию родительских активностей.

        Args:
            event: Событие с данными о положении блока

        Returns:
            ContextActivities: Контекстные активности
        """
        parent_activities = [
            Activity(
                id=f"{settings.OPENEDX_PLATFORM_URI}/courses/{event['context']['course_id']}",
                definition=course.CourseActivityDefinition(event)
            )
        ]

        # Добавление информации о родительском блоке для серверных событий
        if event['event_source'].lower() == 'server':
            parent_activities.append(
                Activity(
                    id=event['referer'],
                    definition=BlockActivityDefinition(event)
                )
            )

        other_activities = [
            Activity(
                id=event['referer'],
                definition=base.ReferringActivityDefinition(event)
            ),
        ]

        return ContextActivities(
            parent=ActivityList(parent_activities),
            other=ActivityList(other_activities)
        )

    def get_context(self, event: Dict[str, Any]) -> Context:
        """
        Создает контекст выполнения для высказывания.

        Args:
            event: Исходное событие трекинга

        Returns:
            Context: Наполненный контекст xAPI
        """
        context = super().get_context(event)
        context.context_activities = self.get_context_activities(event)
        return context
