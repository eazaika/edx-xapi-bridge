"""Statements base for xAPI."""


# indebted to authors of https://github.com/edx/edx-enterprise/tree/master/integrated_channels/xapi


from tincan import Agent, Context, Statement

from xapi_bridge import lms_api
from xapi_bridge import settings


class LMSTrackingLogStatement(Statement):
    """Base class for xAPI Bridge Statements from Open edX LMS tracking logs."""

    user_api_client = lms_api.user_api_client

    def __init__(self, event, *args, **kwargs):
        """
        Initialize an xAPI Statement from a tracking log event.
        """
        kwargs.update(
            actor=self.get_actor(event),
            verb=self.get_verb(event),
            object=self.get_object(event),
            result=self.get_result(event),
            context=self.get_context(event),
            timestamp=self.get_timestamp(event)
        )
        super(LMSTrackingLogStatement, self).__init__(*args, **kwargs)

    def _get_edx_user_info(self, username):
        return self.user_api_client.get_edx_user_info(username)

    def get_actor(self, event):
        """Get Actor for the statement."""
        edx_user_info = self._get_edx_user_info(event['username'])
        return Agent(
            name=edx_user_info['fullname'],
            mbox='mailto:{}'.format(edx_user_info['email']),
        )

    def get_context(self, event):
        """Get Context for the statement."""
        return Context(platform=settings.OPENEDX_PLATFORM_URI)

    def get_timestamp(self, event):
        """Get the Timestamp for the statement."""
        return event['time']

    def get_result(self, event):
        # Not all activities have a result.
        return None
