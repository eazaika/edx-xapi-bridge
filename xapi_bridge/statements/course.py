"""
xAPI Statements для событий курса в Open edX: записи, завершения, отчисления.

Соответствует профилю курсовой активности ADL xAPI:
https://w3id.org/xapi/cmi5/v1.0.3/

"""

from typing import Dict, Any, Optional

from tincan import Activity, ActivityDefinition, LanguageMap, Verb, Result

from . import base
from xapi_bridge import constants, lms_api, settings


class CourseActivityDefinition(ActivityDefinition):
    """Определение активности курса с расширениями для UNTI."""

    enrollment_api_client = lms_api.enrollment_api_client

    def __init__(self, event: Dict[str, Any], *args, **kwargs):
        """
        Инициализирует метаданные курса.

        Args:
            event: Событие трекинга с контекстом курса
        """
        course_info = self.enrollment_api_client.get_course_info(event)

        kwargs.update({
            'type': constants.XAPI_ACTIVITY_COURSE,
            'name': LanguageMap({'ru-RU': course_info.get('name', 'Курс')}),
            'description': LanguageMap({'ru-RU': course_info.get('description', '')})
        })

        # Добавление расширений для UNTI
        if settings.UNTI_XAPI:
            self._add_unti_extensions(course_info, kwargs)

        super().__init__(*args, **kwargs)

    def _add_unti_extensions(self, course_info: Dict[str, Any], kwargs: Dict[str, Any]):
        """Добавляет специфичные для UNTI расширения."""
        ext_url = f"{settings.UNTI_XAPI_EXT_URL}/rall_id"
        if '2035_id' in course_info:
            kwargs.setdefault('extensions', {})[ext_url] = course_info['2035_id']


class CourseStatement(base.LMSTrackingLogStatement):
    """Базовый класс для событий, связанных с курсом."""

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """
        Создает объект Activity для курса.

        Args:
            event: Событие с контекстом курса

        Returns:
            Activity: xAPI активность курса
        """
        return Activity(
            id=f"{settings.OPENEDX_PLATFORM_URI}/courses/{event['context']['course_id']}",
            definition=CourseActivityDefinition(event)
        )


class CourseEnrollmentStatement(CourseStatement):
    """Обрабатывает события записи на курс."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_REGISTERED,
            display=LanguageMap({'ru-RU': 'записался', 'en-US': 'registered'}),
        )


class CourseUnenrollmentStatement(CourseStatement):
    """Обрабатывает события добровольного отчисления."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_EXITED,
            display=LanguageMap({'ru-RU': 'отчислился', 'en-US': 'exited'}),
        )


class CourseExpellStatement(CourseStatement):
    """Обрабатывает события принудительного отчисления."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_FAILED,
            display=LanguageMap({'ru-RU': 'отчислен', 'en-US': 'failed'}),
        )


class CourseCompletionStatement(CourseStatement):
    """Обрабатывает события успешного завершения курса."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_COMPLETED,
            display=LanguageMap({'ru-RU': 'закончил курс', 'en-US': 'completed'}),
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        event_data = self.get_event_data(event)
        return Result(
            success=event_data.get('completion', True),
            completion=True
        )
