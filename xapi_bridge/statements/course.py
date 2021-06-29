# -*- coding: utf-8 -*-
"""xAPI Statements and Activities for verbs on courses as a whole."""


from tincan import Activity, ActivityDefinition, LanguageMap, Verb, Agent, AgentAccount, Result

import base
from xapi_bridge import lms_api, constants, settings



class CourseActivityDefinition(ActivityDefinition):
    enrollment_api_client = lms_api.enrollment_api_client

    def __init__(self, event, *args, **kwargs):
        # TODO get course name, probably from enrollment API
        # in course_details['course_name']
        unti = settings.UNTI_XAPI
        course_info = self.enrollment_api_client.get_course_info(event['context']['course_id'], unti=unti)
        ext_url = u'{}/rall_id'.format(settings.UNTI_XAPI_EXT_URL)

        kwargs.update({
            'type': constants.XAPI_ACTIVITY_COURSE,
            'name': LanguageMap({'ru-RU': course_info['name']}),
            'description': LanguageMap({'ru-RU': course_info['description']})
        })
        if unti:
            kwargs.update({'extensions': {ext_url: course_info['2035_id']}})

        logger.error('CourseActivityDefinition {}'.format(kwargs))
        super(CourseActivityDefinition, self).__init__(*args, **kwargs)


class CourseStatement(base.LMSTrackingLogStatement):
    """ Statement base for course enrollment and unenrollment events."""


    def get_object(self, event):
        """
        Get object for the statement.
        """
        return Activity(
            id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
            definition=CourseActivityDefinition(event)
        )


class CourseEnrollmentStatement(CourseStatement):
    """Statement for course enrollment."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_REGISTERED,
            display=LanguageMap({'en-US': 'registered', 'ru-RU': u'записался'}),
        )


class CourseUnenrollmentStatement(CourseStatement):
    """Statement for course unenrollment."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_EXITED,
            display=LanguageMap({'en-US': 'exited', 'ru-RU': u'отчислился'}),
        )


class CourseExpellStatement(CourseStatement):
    """Statement for course unenrollment."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_FAILED,
            display=LanguageMap({'en-US': 'failed', 'ru-RU': u'отчислен'}),
        )


class CourseCompletionStatement(CourseStatement):
    """Statement for student completion of a course."""

    # event indicates a course has been completed by virtue of a certificate being received
    # eventually this will not be the marker of course completion

    # TODO: what happens when a course is un-completed? (e.g., certificate is revoked or other)

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_COMPLETED,
            display=LanguageMap({'en-US': 'completed', 'ru-RU': u'закончил курс'}),
        )

    def get_result(self, event):
        event_data = self.get_event_data(event)
        return Result(
            success=event_data.get('completion', True),
            completion=True,
    )
