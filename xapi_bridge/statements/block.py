# -*- coding: utf-8 -*-
"""Statement base classes for courseware blocks."""


from tincan import Activity, ActivityDefinition, ActivityList, Context, ContextActivities, LanguageMap

import base
import course
from xapi_bridge import constants, settings


class BlockActivityDefinition(ActivityDefinition):
    def __init__(self, event, *args, **kwargs):
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            # not all events will have in the context
            display_name = "Составной КИМ"
        kwargs.update({
            'type': constants.XAPI_ACTIVITY_MODULE,
            'name': LanguageMap({'ru-RU': display_name}),
            'description': LanguageMap({'en-US': 'A course vertical section in a course delivered through Open edX'})
        })
        super(BlockActivityDefinition, self).__init__(*args, **kwargs)


class BlockAssessmentDefinition(ActivityDefinition):
    def __init__(self, event, *args, **kwargs):
        try:
            display_name = event['display_name']
        except KeyError:
            # not all events will have in the context
            display_name = "Course Block"

        if event['usage_key'].find('vertical+block') > 0:
            block_type = 'vertical block'
        elif event['usage_key'].find('sequential+block') > 0:
            block_type = 'sequential block'
        elif event['usage_key'].find('chapter+block') > 0:
            block_type = 'chapter block'
        else:
            block_type = 'undefined'

        kwargs.update({
            'type': constants.XAPI_ASSESSMENT_MODULE,
            'name': LanguageMap({'ru-RU': display_name}),
            'description': LanguageMap({'en-US': block_type})
        })

        try:
            ext_url = u'{}/question_amount'.format(settings.UNTI_XAPI_EXT_URL)
            kwargs.update({
                'extensions': { ext_url: event['childrens'] }
            })
        except:
            pass

        super(BlockAssessmentDefinition, self).__init__(*args, **kwargs)


class BaseCoursewareBlockStatement(base.LMSTrackingLogStatement):
    """Base for any interaction with a courseware block."""

    def _get_activity_id(self, event):
        format_str = constants.BLOCK_OBJECT_ID_FORMAT
        platform_str = settings.OPENEDX_PLATFORM_URI
        block_id = event['context']['module']['usage_key']
        return format_str.format(platform=platform_str, block_usage_key=block_id)

    def get_context_activities(self, event):
        parent_activities = [
            Activity(
                id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
                definition=course.CourseActivityDefinition(event)
            ),
        ]
        # browser source events don't know as much about their context
        if event['event_source'].lower() == 'server':
            parent_activities.append(
                Activity(
                    id=event['referer'],
                    definition=BlockActivityDefinition(event)
                ),
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

    def get_context(self, event):
        """Get Context for the statement.

        For problems this can include the course and the block id.
        """
        context = super(BaseCoursewareBlockStatement, self).get_context(event)
        context.context_activities=self.get_context_activities(event)
        return context
