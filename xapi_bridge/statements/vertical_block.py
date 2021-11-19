# -*- coding: utf-8 -*-
"""xAPI Statements and Activities for verbs on courses as a whole."""

import json

from tincan import Activity, ActivityDefinition, ActivityList, LanguageMap, Result, Verb, ContextActivities

import block
import course
from xapi_bridge import constants, exceptions, settings

import logging
log = logging.getLogger(__name__)


class VerticalBlockCompleteStatement(block.BaseCoursewareBlockStatement):
    """ Statement for vertical block complete event."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_COMPLETED,
            display=LanguageMap({'en-US': 'completed', 'ru-RU': 'завершен'}),
        )

    def get_object(self, event):
        """
        Get object for the statement.
        """
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            display_name = "Составной КИМ"

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ASSESSMENT_MODULE,
                name=LanguageMap({'ru-RU': question}),
                description=LanguageMap({'ru-RU': display_name}),
            ),
        )

    def get_result(self, event):

        log.error(event)
        try:
            return Result(
                score={
                    'raw': event['context']['module']['progress'][0],
                    'min': 0,
                    'max': event['context']['module']['progress'][1],
                    'scaled': float(event['context']['module']['progress'][0] / event['context']['module']['progress'][1])
                },
                success=event['context']['module']['done'],
                completion = True
            )
        except:
            return Result(
                success = True,
                completion = True,
            )

    def get_context_activities(self, event):
        parent_activities = [
            Activity(
                id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
                definition=course.CourseActivityDefinition(event)
            ),
        ]
        parent = settings.OPENEDX_PLATFORM_URI + ':18010/container/' + event['context']['parent']['usage_key']
        #parent = event['context']['parent']['usage_key'] #FOR TEST
        parent_activities.append(
            Activity(
                id=parent,
                definition=block.BlockAssessmentDefinition(event['context']['parent'])
            ),
        )

        section = settings.OPENEDX_PLATFORM_URI + ':18010/container/' + event['context']['grandparent']['usage_key']
        parent_activities.append(
            Activity(
                id=section,
                definition=block.BlockAssessmentDefinition(event['context']['grandparent'])
            ),
        )

        return ContextActivities(
            parent=ActivityList(parent_activities)
        )
