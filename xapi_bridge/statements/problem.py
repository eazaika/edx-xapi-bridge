"""
xAPI Statements for problem interactions in Open edX.

Migrated to Python 3.10 with:
- Modern dict key handling
- Type annotations
- F-strings
- Improved error handling
"""

import json
import re
import logging
from typing import Dict, Any, List, Union

from tincan import (
    Activity, ActivityDefinition, ActivityList,
    LanguageMap, Result, Verb, ContextActivities
)

from . import block, course
from xapi_bridge import constants, exceptions, settings


logger = logging.getLogger(__name__)


class ProblemStatement(block.BaseCoursewareBlockStatement):
    """Base class for problem interaction statements."""

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """
        Constructs problem activity object.

        Args:
            event: Problem interaction event data

        Returns:
            Activity: xAPI activity representing the problem
        """
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            display_name = "Problem"

        try:
            event_data = self.get_event_data(event)
            submission = event_data['submission']
            first_key = next(iter(submission.keys()))  # Python 3 dict handling
            question = submission[first_key]['question']
            question = re.sub(r'\(\$(\w+)\)', r'<\1>', question)
        except KeyError:
            question = event['context']['question']

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_INTERACTION,
                name=LanguageMap({'ru-RU': question}),
                description=LanguageMap({'ru-RU': display_name}),
            ),
        )


class ProblemGradedStatement(ProblemStatement):
    """Handles graded problem submissions."""


class ProblemCheckStatement(ProblemStatement):
    """Handles problem answer check events."""

    def __init__(self, event: Dict[str, Any], *args, **kwargs):
        if event['event_source'].lower() != 'server':
            raise exceptions.XAPIBridgeSkippedConversion(
                "Skipping browser-originated problem check"
            )
        super().__init__(event, *args, **kwargs)  # Modern super call

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_ANSWERED,
            display=LanguageMap({'en-US': 'answered', 'ru-RU': 'дан ответ'}),
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        """
        Constructs result with problem response and score.

        Args:
            event: Problem check event data

        Returns:
            Result: xAPI result object with scoring details
        """
        event_data = self.get_event_data(event)
        answer: List[str] = []
        
        try:
            submission = event_data['submission']
            for key in submission:
                answer_data = submission[key]['answer']
                if isinstance(answer_data, list):
                    answer.extend(
                        re.sub(r"(\n.*)", '', item) for item in answer_data
                    )
                else:
                    answer.append(str(answer_data))  # Explicit string conversion

            formatted_answer = ', '.join(f"<{item}>" for item in answer)
        except KeyError as exc:
            logger.error("Problem check data error: %s", exc)
            formatted_answer = event['context'].get('answer', 'Unknown')

        try:
            success = event_data['success'] == 'correct'
        except KeyError:
            success = event_data.get('grade', 0) >= event_data.get('max_grade', 1)

        return Result(
            score={
                'raw': event_data['grade'],
                'min': 0,
                'max': event_data['max_grade'],
                'scaled': float(event_data['grade']) / float(event_data['max_grade'])
            },
            success=success,
            response=formatted_answer  # Already Unicode in Python 3
        )

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """Builds parent course and assessment context."""
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


class ProblemSubmittedStatement(ProblemStatement):
    """Handles problem submission attempts."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_ATTEMPTED,
            display=LanguageMap({'en': 'attempted'}),
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        event_data = self.get_event_data(event)
        earned = event_data['weighted_earned']
        possible = event_data['weighted_possible']
        
        return Result(
            score={
                'raw': earned,
                'min': 0,
                'max': possible,
                'scaled': float(earned / possible) if possible > 0 else 0
            },
            success=earned >= possible
        )


class ProblemResetStatement(ProblemStatement):
    """Handles problem reset events."""

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        return Verb(
            id=constants.XAPI_VERB_INITIALIZED,
            display=LanguageMap({'en': 'reset'}),
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        return Result(
            completion=False,
            response=json.dumps([])  # Empty response array
        )
