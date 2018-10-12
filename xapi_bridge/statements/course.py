"""xAPI Statements and Activities for verbs on courses as a whole."""


from tincan import Activity, ActivityDefinition, LanguageMap, Verb

import base
from xapi_bridge import constants, settings


class CourseActivityDefinition(ActivityDefinition):

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'type': constants.XAPI_ACTIVITY_COURSE,
            'name': LanguageMap({'en-US': 'Course'}),
            'description': LanguageMap({'en-US': 'A course delivered through Open edX'})
        })
        super(CourseActivityDefinition, self).__init__(*args, **kwargs)


class CourseStatement(base.LMSTrackingLogStatement):
    """ Statement base for course enrollment and unenrollment events."""


    def get_object(self, event):
        """
        Get object for the statement.
        """
        return Activity(
            id='{}/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
            definition=CourseActivityDefinition()
        )


class CourseEnrollmentStatement(CourseStatement):
    """Statement for course enrollment."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_REGISTERED,
            display=LanguageMap({'en-US': 'enrolled', 'en-GB': 'enroled'}),
        )


class CourseUnenrollmentStatement(CourseStatement):
    """Statement for course unenrollment."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_UNREGISTERED,
            display=LanguageMap({'en-US': 'unenrolled', 'en-GB': 'unenroled'}),
        )


class CourseCompletionStatement(CourseStatement):
    """Statement for student completion of a course."""

    # event indicates a course has been completed by virtue of a certificate being received
    # eventually this will not be the marker of course completion

    # TODO: what happens when a course is un-completed? (e.g., certificate is revoked or other)

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_COMPLETED,
            display=LanguageMap({'en-US': 'completed', 'en-GB': 'completed'}),
        )

