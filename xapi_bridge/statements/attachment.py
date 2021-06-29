# -*- coding: utf-8 -*-
"""xAPI Statements and Activities for verbs on courses as a whole."""

from tincan import Activity, ActivityDefinition, Verb, Attachment, LanguageMap, ContextActivities, ActivityList, Result

import block
import course
from xapi_bridge import settings, constants




class AttachmentStatement(block.BaseCoursewareBlockStatement):

    def get_object(self, event):
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            display_name = "Решение задания"

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_INTERACTION, # could be _QUESTION if not CAPA
                name=LanguageMap({'ru-RU': display_name}),
                # TODO: interactionType, correctResponsesPattern, choices, if possible
            ),
        )

    def get_attachment(self, event):
        data = event['event']

        return Attachment(
            usageType="http://id.tincanapi.com/attachment/supporting_media",
            display=LanguageMap({"ru-RU": data['filename']}),
            contentType=data['type'],
            length=data['size'],
            sha2=data['sha2'],
            fileUrl='{}{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['path'])
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

        return ContextActivities(
            parent=ActivityList(parent_activities)
        )

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_ATTACHED,
            display=LanguageMap({'en-US': 'attached', 'ru-RU': 'приложен'}),
        )

    def get_result(self, event):
        return Result(
            completion=True,
            success=True
        )

