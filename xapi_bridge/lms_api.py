"""Utility functions for xapi bridge."""

import logging

import memcache
from requests.exceptions import ConnectionError, Timeout  # pylint: disable=unused-import
from slumber.exceptions import SlumberBaseException

from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import HttpClientError

from xapi_bridge import constants, exceptions, settings


logger = logging.getLogger(__name__)


class EnrollmentApiClient(object):
    """
    Object builds an API client to make calls to the edxapp Enrollment API.
    Authenticates using settings.OPENEDX_EDX_API_KEY.
    """

    API_BASE_URL = settings.OPENEDX_ENROLLMENT_API_URI
    APPEND_SLASH = False
    CACHE_ACCOUNTS_PREFIX = "enrollmentapi_data__"

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
        self.cache = False
        if settings.LMS_API_USE_MEMCACHED:
            self.cache = memcache.Client([settings.MEMCACHED_ADDRESS], debug=0)
        self.client = EdxRestApiClient(
            self.API_BASE_URL, append_slash=self.APPEND_SLASH,
            username="xapi_bridge", oauth_access_token=token[0]
        )

    def get_course_info(self, course_id, unti=False):
        """
        Query the Enrollment API for the course details of the given course_id.
        unti is flag for University 2035 LRS data inegration
        """
        try:
            resp = self.client.course(u'{}?include_expired=1'.format(course_id)).get()

            if resp:
                data = {'name': resp['course_name'], 'description': resp['description']}
                if unti and resp['integrate_2035_id'].strip():
                    data.update({'2035_id': resp['integrate_2035_id']})
                logger.error('get_course_info {}'.format(data))
                return data
            #if unti and resp:
            #    if resp['integrate_2035_id'].strip():
            #        return {'name': resp['course_name'], '2035_id': resp['integrate_2035_id'], 'description': resp['description']}
            #    else:
            #       message = 'Course {} not found in University 2035 database'.format(course_id)
            #       raise exceptions.XAPIBridgeCourseNotFoundError(message)
            #elif resp:
            #    return {'name': resp['course_name'], 'description': resp['description']}
            else:
                # TODO: look at other reasons for no resp.success
                message = 'Failed to retrieve course details for course id {}. Course not found in LMS'.format(course_id)
                raise exceptions.XAPIBridgeCourseNotFoundError(message)
        except (SlumberBaseException, ConnectionError, Timeout, HttpClientError) as e:
            message = 'Failed to retrieve course details for course id {} due to: {}'.format(course_id, str(e))
            e = exceptions.XAPIBridgeConnectionError(message)
            e.err_continue_exc()
            raise exceptions.XAPIBridgeCourseNotFoundError(message)


class UserApiClient(object):
    """
    Object builds an API client to make calls to the edxapp User API.
    Authenticates using settings.OPENEDX_EDX_API_KEY.
    """

    API_BASE_URL = settings.OPENEDX_USER_API_URI
    APPEND_SLASH = False
    CACHE_ACCOUNTS_PREFIX = "userapi_accounts__"

    def __init__(self):
        """
        Create an LMS API client, authenticated with the OAuth2 token for client in settings
        """
        # session = Session()
        # # session.headers = {"X-Edx-Api-Key": settings.OPENEDX_EDX_API_KEY}
        token = EdxRestApiClient.get_oauth_access_token(
            url="{}{}".format(settings.OPENEDX_PLATFORM_URI, constants.OPENEDX_OAUTH2_TOKEN_URL),
            client_id=settings.OPENEDX_OAUTH2_CLIENT_ID,
            client_secret=settings.OPENEDX_OAUTH2_CLIENT_SECRET
        )
        self.cache = False
        if settings.LMS_API_USE_MEMCACHED:
            self.cache = memcache.Client([settings.MEMCACHED_ADDRESS], debug=0)
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
            dict with keys 'email', 'fullname' and 'unti_id' optionally
        """

        def _get_user_info_from_api(username, unti=False):

            try:
                resp = self.client.accounts(username).get()

                if resp:
                    data = {'email': resp['email'], 'fullname': resp['name']}
                    if unti and resp['unti_id']:
                        data.update({'unti_id': resp['unti_id']})
                    return data
                else:
                    # TODO: look at other reasons for no resp.success
                    message = 'Failed to retrieve user details for username {}. User not found in LMS'.format(username)
                    raise exceptions.XAPIBridgeUserNotFoundError(message)

            except (SlumberBaseException, ConnectionError, Timeout, HttpClientError) as e:
                message = 'Failed to retrieve user details for username {} due to: {}'.format(username, str(e))
                e = exceptions.XAPIBridgeConnectionError(message)
                e.err_continue_exc()
                raise exceptions.XAPIBridgeUserNotFoundError(message)

        if username == '':
            raise exceptions.XAPIBridgeUserNotFoundError()
            # return {'email': '', 'fullname': ''}

        if hasattr(self, 'cache') and self.cache:
            cached_user_info = self.cache.get(self.CACHE_ACCOUNTS_PREFIX + username)
            if not cached_user_info:
                user_info = _get_user_info_from_api(username, unti=settings.UNTI_XAPI)
                self.cache.set(self.CACHE_ACCOUNTS_PREFIX + username, user_info, time=300)
                return user_info
            else:
                return cached_user_info
        else:
            return _get_user_info_from_api(username, unti=settings.UNTI_XAPI)


user_api_client = UserApiClient()
enrollment_api_client = EnrollmentApiClient()
