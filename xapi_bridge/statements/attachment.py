"""
xAPI Statements для работы с вложениями в заданиях Open edX.

Соответствует спецификации xAPI для файловых вложений:
https://xapi.com/profiles/file-attachments/

Мигрировано на Python 3.10 с:
- Аннотациями типов
- Современной обработкой строк
- Безопасным доступом к данным
"""

from typing import Dict, Any, List

from tincan import (
    Activity, ActivityDefinition, Attachment, ContextActivities,
    ActivityList, LanguageMap, Result, Verb
)

from . import block, course
from xapi_bridge import constants, settings


class AttachmentStatement(block.BaseCoursewareBlockStatement):
    """Обрабатывает события прикрепления файлов к заданиям."""

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """
        Создает объект Activity для прикрепленного файла.

        Args:
            event: Событие с данными о вложении

        Returns:
            Activity: xAPI активность с метаданными файла
        """
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            display_name = "Решение задания"

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_INTERACTION,
                name=LanguageMap({'ru-RU': display_name}),
            )
        )

    def get_attachment(self, event: Dict[str, Any]) -> Attachment:
        """
        Формирует объект вложения xAPI.

        Args:
            event: Событие с метаданными файла

        Returns:
            Attachment: Объект xAPI Attachment
        """
        file_data = event.get('event', {})
        context = event.get('context', {})
        
        return Attachment(
            usage_type="http://id.tincanapi.com/attachment/supporting_media",
            display=LanguageMap({"ru-RU": file_data.get('filename', 'Файл')}),
            content_type=file_data.get('type', 'application/octet-stream'),
            length=file_data.get('size', 0),
            sha2=file_data.get('sha2', ''),
            file_url=f"{settings.OPENEDX_PLATFORM_URI}{context.get('path', '')}"
        )

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """
        Строит контекст родительских активностей.

        Args:
            event: Событие с информацией о положении элемента

        Returns:
            ContextActivities: Иерархия активностей курса
        """
        parent_activities = [
            Activity(
                id=f"{settings.OPENEDX_PLATFORM_URI}/courses/{event['context']['course_id']}",
                definition=course.CourseActivityDefinition(event)
            ),
            Activity(
                id=f"{settings.OPENEDX_PLATFORM_URI}:18010/container/"
                f"{event['context']['parent']['usage_key']}",
                definition=block.BlockAssessmentDefinition(event['context']['parent'])
            )
        ]
        return ContextActivities(parent=ActivityList(parent_activities))

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_ATTACHED,
            display=LanguageMap({'en-US': 'attached', 'ru-RU': 'приложен'}),
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        return Result(
            completion=True,
            success=True,
            extensions={
                constants.XAPI_RESULT_EXTENSION_FILE_SIZE: 
                event.get('event', {}).get('size', 0)
            }
        )
