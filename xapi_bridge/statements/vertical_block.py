"""
xAPI Statements для составных блоков (vertical blocks) в Open edX.

Соответствует профилю xAPI для составных учебных модулей:
https://xapi.com/profiles/composite-modules/

"""

import logging
from typing import Dict, Any

from tincan import Activity, ActivityDefinition, ActivityList, LanguageMap, Result, Verb, ContextActivities

from . import block, course
from xapi_bridge import constants, settings


logger = logging.getLogger(__name__)


class VerticalBlockCompleteStatement(block.BaseCoursewareBlockStatement):
    """Обрабатывает события завершения составных блоков (vertical)."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        """
        Возвращает глагол xAPI для события завершения.

        Args:
            event: Событие из трекинга Open edX

        Returns:
            Verb: xAPI Verb с правильным отображением
        """
        return Verb(
            id=constants.XAPI_VERB_COMPLETED,
            display=LanguageMap({'ru-RU': 'завершен', 'en-US': 'completed'}),
        )

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """
        Создает объект Activity для составного блока.

        Args:
            event: Данные события из логов

        Returns:
            Activity: xAPI активность с метаданными блока
        """
        try:
            display_name = event['context']['module']['display_name']
        except KeyError as e:
            logger.warning("Отсутствует display_name в контексте: %s", str(e))
            display_name = "Составной КИМ"

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ASSESSMENT_MODULE,
                description=LanguageMap({'ru-RU': display_name}),
            )
        )


    def get_result(self, event: Dict[str, Any]) -> Result:
        """
        Формирует результат выполнения блока.

        Args:
            event: Событие с данными о прогрессе

        Returns:
            Result: Объект результата с показателями выполнения
        """
        try:
            module_data = event['context'].get('module', {})
            
            # Пытаемся получить прогресс
            progress_data = module_data.get('progress')
            if progress_data and len(progress_data) == 2:
                raw = float(progress_data[0])
                max_val = float(progress_data[1])
                scaled = raw / max_val if max_val > 0 else 0
                
                return Result(
                    score={
                        'raw': raw,
                        'min': 0,
                        'max': max_val,
                        'scaled': scaled
                    },
                    success=module_data.get('done', True),
                    completion=True
                )
            
            # Если нет данных о прогрессе, проверяем количество дочерних элементов
            children_count = module_data.get('childrens', 0)
            if children_count:
                return Result(
                    score={
                        'raw': children_count,
                        'min': 0,
                        'max': children_count,
                        'scaled': 1.0  # Если блок завершен, считаем что все дочерние элементы пройдены
                    },
                    success=True,
                    completion=True
                )
            
            # Если нет никаких данных о прогрессе, возвращаем базовый результат
            return Result(
                success=True,
                completion=True
            )
            
        except Exception as e:
            logger.debug(f"Детали события: {event}")
            logger.warning(f"Ошибка обработки прогресса: {str(e)}")
            return Result(
                success=True,
                completion=True
            )


    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """
        Строит иерархию родительских активностей.

        Args:
            event: Событие с информацией о структуре курса

        Returns:
            ContextActivities: Контекстные активности родительских элементов
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
            ),
            Activity(
                id=f"{settings.OPENEDX_PLATFORM_URI}:18010/container/"
                f"{event['context']['grandparent']['usage_key']}",
                definition=block.BlockAssessmentDefinition(event['context']['grandparent'])
            )
        ]

        return ContextActivities(parent=ActivityList(parent_activities))
