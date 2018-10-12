"""xAPI Statements and Activities for verbs on courses as a whole."""


from tincan import Activity, ActivityDefinition, ActivityList, Context, ContextActivities, LanguageMap, Verb

import base, course
from xapi_bridge import constants, settings


class BlockActivityDefinition(ActivityDefinition):
    def __init__(self, event, *args, **kwargs):
        kwargs.update({
            'type': constants.XAPI_ACTIVITY_BLOCK,
            'name': LanguageMap({'en-US': event['context']['module']['display_name']}),
            'description': LanguageMap({'en-US': 'A course block in a course delivered through Open edX'})
        })
        super(BlockActivityDefinition, self).__init__(*args, **kwargs)


class ProblemStatement(base.LMSTrackingLogStatement):
    """ Statement base for problem events."""

    def get_object(self, event):
        """
        Get object for the statement.
        """
        return Activity(
            id='{}/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['path']),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_QUESTION,
                name=LanguageMap({'en-US': 'Problem'}),
                description=LanguageMap({'en-US': 'A problem in an Open edX course'}),
            ),
        )


class ProblemCheckStatement(ProblemStatement):
    """Statement for student checking answer to a problem."""

    def __init__(self, event, *args, **kwargs):
        # 'problem_check' events are emitted from both browser and server
        # and we only want the server event
        if event['event_source'] != 'server':
            return None  # will be excluded from StatementList
        super(ProblemCheckStatement, self).__init__(event, *args, **kwargs)

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_ATTEMPTED,
            display=LanguageMap({'en-US': 'attempted'}),
        )

    def get_context_activities(self, event):
        parent_activities = [
            Activity(
                id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
                definition=course.CourseActivityDefinition()
            ),
            Activity(
                id=event['referer'],
                definition=BlockActivityDefinition(event)
            ),
        ]
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
