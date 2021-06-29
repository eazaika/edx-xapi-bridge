"""Statements base for xAPI."""


# indebted to authors of https://github.com/edx/edx-enterprise/tree/master/integrated_channels/xapi

from copy import deepcopy
import json

from tincan import Agent, AgentAccount, Context, Statement, ActivityDefinition, LanguageMap, Result

from xapi_bridge import constants, exceptions, lms_api, settings


class LMSTrackingLogStatement(Statement):
    """Base class for xAPI Bridge Statements from Open edX LMS tracking logs."""

    user_api_client = lms_api.user_api_client

    def __init__(self, event, *args, **kwargs):
        """
        Initialize an xAPI Statement from a tracking log event.
        """
        try:
            kwargs.update(
                actor=self.get_actor(event),
                verb=self.get_verb(event),
                object=self.get_object(event),
                result=self.get_result(event),
                context=self.get_context(event),
                timestamp=self.get_timestamp(event),
                authority=self.get_authority(),
            )
            if event['event_type'] == 'edx.attachment':
                kwargs.update(
                    attachments=self.get_attachment(event)
                )
            super(LMSTrackingLogStatement, self).__init__(*args, **kwargs)
        # wrap base exception types used in tincan package
        except (ValueError, TypeError, AttributeError) as e:
            message = "xAPI Bridge could not generate Statement from class {}. {}".format(str(self.__class__), e.message)
            raise exceptions.XAPIBridgeStatementConversionError(event=event, message=message)

    def _get_edx_user_info(self, username):
        return self.user_api_client.get_edx_user_info(username)

    def _get_enrollment_id(self, event):
        api_url = constants.ENROLLMENT_API_URL_FORMAT.format(username=event['username'], course_id=event['context']['course_id'])
        return "{}{}".format(settings.OPENEDX_PLATFORM_URI, api_url)

    def get_authority(self):
        return Agent(
            name=settings.ORG_NAME,
            mbox='mailto:{}'.format(settings.ORG_EMAIL),
        )

    def get_event_data(self, event):
        if event['event_source'] == 'browser':
            return json.loads(event.get('event', "{}"))
        else:
            return event.get('event', {})

    def get_actor(self, event):
        """Get Actor for the statement."""
        try:
            edx_user_info = self._get_edx_user_info(event['event']['username'])
        except:
            if event['username'] == 'anonymous':
                edx_user_info = self._get_edx_user_info(event['context']['module']['username'])
            else:
                edx_user_info = self._get_edx_user_info(event['username'])

        # this can happen in case a user was just deleted, or
        # in cases a user is automatically logged out while
        # they are interacting with courseware (e.g., a video is playing),
        # due to an LMS restart or other circumstance, in which
        # case an event with no username can be sent to the tracking
        # logs.  In this case don't send a Statement
        if not edx_user_info['email']:
            return None

        if settings.UNTI_XAPI and edx_user_info['unti_id']:
            return Agent(
                name=edx_user_info['fullname'],
                account=AgentAccount(name=edx_user_info['unti_id'], home_page='https://my.2035.university'),
            )
        else:
            return Agent(
                name=edx_user_info['fullname'],
                mbox='mailto:{}'.format(edx_user_info['email']),
            )

    def get_context(self, event):
        """Get Context for the statement."""
        return Context(
            platform=settings.OPENEDX_PLATFORM_URI,
        )

    def get_timestamp(self, event):
        """Get the Timestamp for the statement."""
        return event['time']

    def get_result(self, event):
        event_data = self.get_event_data(event)
        return Result(
            success=event_data.get('success', True),
            completion=True,
        )


class ReferringActivityDefinition(ActivityDefinition):
    def __init__(self, event, *args, **kwargs):
        kwargs.update({
            'type': constants.XAPI_CONTEXT_REFERRER,
            'name': LanguageMap({'en-US': 'Referrer'}),
            'description': LanguageMap({'en-US': 'A referring course activity'})
        })
        super(ReferringActivityDefinition, self).__init__(*args, **kwargs)
