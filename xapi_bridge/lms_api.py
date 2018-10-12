"""Utility functions for xapi bridge."""

import logging

from edx_rest_api_client.client import EdxRestApiClient
from requests.exceptions import ConnectionError, Timeout  # pylint: disable=unused-import
from slumber.exceptions import SlumberBaseException

from xapi_bridge import constants
from xapi_bridge import settings


logger = logging.getLogger(__name__)


class UserApiClient(object):
    """
    Object builds an API client to make calls to the edxapp User API.
    Authenticates using settings.OPENEDX_EDX_API_KEY.
    """

    API_BASE_URL = settings.OPENEDX_USER_API_URI
    APPEND_SLASH = False

    def __init__(self):
        """
        Create an LMS API client, authenticated with the OAuth2 token for client in settings
        """
        # session = Session()
        # # session.headers = {"X-Edx-Api-Key": settings.OPENEDX_EDX_API_KEY}
        token = EdxRestApiClient.get_oauth_access_token(
            url="{}{}".format(settings.OPENEDX_PLATFORM_URI, constants.OPENEDX_OAUTH2_TOKEN_URL),
            client_id=settings.OPENEDX_OAUTH2_CLIENT_ID,
            client_secret=settings.OPENEDX_OAUTH2_CLIENT_SECRET,
        )
        self.client = EdxRestApiClient(
            self.API_BASE_URL, append_slash=self.APPEND_SLASH,
            username="xapi_bridge", oauth_access_token=token[0]
        )

    def get_edx_user_info(self, username):
        """
        Query the User API for the course details of the given course_id.
        Args:
            username (str): The username of the user
        Returns:
            dict with keys 'email', 'fullname'
        """

        # TODO: store/retrieve already retrieved in memcached, with timeout

        if username == '':
            # we shouldn't even get to this point I think
            return {'email': '', 'fullname': ''}
        try:
            resp = self.client.accounts(username).get()
            return {'email': resp['email'], 'fullname': resp['name']}
        except (SlumberBaseException, ConnectionError, Timeout) as exc:
            logger.exception(
                'Failed to retrieve user details for username {} due to: {}'.format(username, str(exc))
            )
            # should we interrupt the publishing of the statement here?


user_api_client = UserApiClient()
