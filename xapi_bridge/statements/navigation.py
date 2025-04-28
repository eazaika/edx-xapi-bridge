"""
xAPI Statements для событий навигации в Open edX.

Соответствует профилю навигации ADL xAPI:
https://w3id.org/xapi/navigation/v1.0.0/

Мигрировано на Python 3.10 с:
- Аннотациями типов
- Современным синтаксисом super()
- F-строками
- Безопасным доступом к данным
"""

from typing import Dict, Any, Optional

from tincan import (
    Activity, ActivityDefinition, ActivityList,
    Context, ContextActivities, Extensions, LanguageMap, Verb
)

from . import base, block, course
from xapi_bridge import constants, settings


class NavigationSequenceStatement(base.LMSTrackingLogStatement):
    """Обрабатывает события навигации между секциями курса."""

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """
        Создает объект Activity для навигационного события.

        Args:
            event: Событие перехода между разделами

        Returns:
            Activity: xAPI активность с позицией в курсе
        """
        event_data = self.get_event_data(event)
        return Activity(
            id=event['page'],
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_MODULE,
                name=LanguageMap({'en': 'Course Unit Tab'}),
                extensions=Extensions({
                    constants.XAPI_ACTIVITY_POSITION: event_data.get('target_tab', 0)
                })
            ),
        )

    def get_context(self, event: Dict[str, Any]) -> Context:
        """
        Добавляет контекстные расширения для навигации.

        Args:
            event: Исходное событие трекинга

        Returns:
            Context: Контекст с информацией о текущей позиции
        """
        event_data = self.get_event_data(event)
        context = super().get_context(event)
        context.extensions = Extensions({
            constants.XAPI_CONTEXT_STARTING_POSITION: event_data.get('current_tab', 0),
        })
        context.context_activities = self.get_context_activities(event)
        return context

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """Строит иерархию родительских активностей."""
        parent_activities = [
            Activity(
                id=event.get('page', ''),
                definition=block.BlockActivityDefinition(event)
            ),
        ]
        return ContextActivities(parent=ActivityList(parent_activities))


class NavigationSequenceTabStatement(NavigationSequenceStatement):
    """Обрабатывает выбор вкладки внутри учебного модуля."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_INITIALIZED,
            display=LanguageMap({'en': 'initialized'}),
        )


class NavigationLinkStatement(base.LMSTrackingLogStatement):
    """Обрабатывает переходы по ссылкам внутри курса."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_EXPERIENCED,
            display=LanguageMap({'en': 'experienced'})
        )

    def get_object(self, event: Dict[str, Any]) -> Activity:
        event_data = self.get_event_data(event)
        return Activity(
            id=event_data.get('target_url', ''),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_LINK,
                name=LanguageMap({'en': 'Link name'})
            )
        )

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """Строит контекст курса и родительских элементов."""
        parent_activities = [
            Activity(
                id=f"{settings.OPENEDX_PLATFORM_URI}/courses/{event['context']['course_id']}",
                definition=course.CourseActivityDefinition(event)
            ),
        ]
        other_activities = [
            Activity(
                id=event_data.get('current_url', ''),
                definition=base.ReferringActivityDefinition(event)
            ),
        ]
        return ContextActivities(
            parent=ActivityList(parent_activities),
            other=ActivityList(other_activities)
        )

    def get_context(self, event: Dict[str, Any]) -> Context:
        return Context(
            platform=settings.OPENEDX_PLATFORM_URI,
            context_activities=self.get_context_activities(event)
        )


class NavigationSectionSelectionStatement(base.LMSTrackingLogStatement):
    """Обрабатывает выбор разделов курса."""

    def get_object(self, event: Dict[str, Any]) -> Activity:
        event_data = self.get_event_data(event)
        return Activity(
            id=event_data.get('target_url', ''),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_MODULE,
                name=LanguageMap({'en': event_data.get('target_name', 'Section')}),
            ),
        )

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_INITIALIZED,
            display=LanguageMap({'en': 'initialized'}),
        )

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        other_activities = [
            Activity(
                id=self.get_event_data(event).get('current_url', ''),
                definition=base.ReferringActivityDefinition(event)
            ),
        ]
        return ContextActivities(other=ActivityList(other_activities))

    def get_context(self, event: Dict[str, Any]) -> Context:
        return Context(
            platform=settings.OPENEDX_PLATFORM_URI,
            context_activities=self.get_context_activities(event)
        )
