"""Utility functions for xapi bridge."""


from edx_rest_api_client.client import EdxRestApiClient
from requests import Session

import settings


class UserApiClient(object):
    """
    Object builds an API client to make calls to the edxapp User API.
    Authenticates using settings.OPENEDX_EDX_API_KEY.
    """

    API_BASE_URL = settings.OPENEDX_PLATFORM_URI + '/api/user/v1'
    APPEND_SLASH = False

    def __init__(self):
        """
        Create an LMS API client, authenticated with the API token from Django settings.
        """
        # session = Session()
        # # session.headers = {"X-Edx-Api-Key": settings.OPENEDX_EDX_API_KEY}
        token = EdxRestApiClient.get_oauth_access_token(
            url="{}/oauth2/access_token".format(settings.OPENEDX_PLATFORM_URI),
            client_id=settings.OPENEDX_OAUTH2_CLIENT_ID,
            client_secret=settings.OPENEDX_OAUTH2_CLIENT_SECRET,
        )
        self.client = EdxRestApiClient(
            self.API_BASE_URL, append_slash=self.APPEND_SLASH,
            username="xapi_bridge", oauth_access_token=token[0]
        )

    def get_edx_user_email(self, username):
        """
        Query the User API for the course details of the given course_id.
        Args:
            username (str): The username of the user
        Returns:
            string: The email associated with the username
        """
        if username == '':
            return ''
        try:
            resp = self.client.accounts(username).get()
            return resp['email']
        except Exception:
            #except (SlumberBaseException, ConnectionError, Timeout) as exc:
            # LOGGER.exception(
            #     'Failed to retrieve course enrollment details for course [%s] due to: [%s]',
            #     course_id, str(exc)
            # )
            return ''


# def get_edx_user_email(username):
#     """Retrieve user email from cache or Open edX user api."""
#     headers = {'X-Edx-Api-Key': '{}'.format(settings.OPENEDX_EDX_API_KEY)}
#     api_url = '{}{}'.format(settings.OPENEDX_USER_API_URI, username)
#     response = requests.get(api_url, headers=headers)
#     import pdb; pdb.set_trace()
#     if response.status_code == 200:
#         email = response.email
#         return email
#     else:
#         # raise some specific exception type
#         pass
