"""xAPI Statements and Activities for verbs on courses as a whole."""


from tincan import Activity, ActivityDefinition, LanguageMap, Verb

import base
from xapi_bridge import constants, settings



class VideoStatement(base.LMSTrackingLogStatement):
    """ Statement base for video interaction events."""


    def get_object(self, event):
        """
        Get object for the statement.
        """

        # return Activity(
        #     id='{}/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
        #     definition=ActivityDefinition(
        #         type=constants.XAPI_ACTIVITY_COURSE,
        #         name=LanguageMap({'en-US': 'Course'}),
        #         description=LanguageMap({'en-US': 'A course delivered through Open edX'}),
        #     ),
        # )
