"""Statement base classes for courseware blocks."""


from tincan import Activity, ActivityDefinition, ActivityList, Context, ContextActivities, LanguageMap

import base
import course
from xapi_bridge import constants, settings


class BlockActivityDefinition(ActivityDefinition):
    def __init__(self, event, *args, **kwargs):
        kwargs.update({
            'type': constants.XAPI_ACTIVITY_BLOCK,
            'name': LanguageMap({'en': event['context']['module']['display_name']}),
            'description': LanguageMap({'en': 'A course block in a course delivered through Open edX'})
        })
        super(BlockActivityDefinition, self).__init__(*args, **kwargs)


class BaseCoursewareBlockStatement(base.LMSTrackingLogStatement):
    """Base for any interaction with a courseware block."""

    def get_context_activities(self, event):
        parent_activities = [
            Activity(
                id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
                definition=course.CourseActivityDefinition()
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
        return Context(
            platform=settings.OPENEDX_PLATFORM_URI,
            context_activities=self.get_context_activities(event)
        )
