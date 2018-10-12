
# the maximum age of an event, in seconds, before it is published to the LRS
PUBLISH_MAX_WAIT_TIME = 60

# the number of statements to publish per batch
PUBLISH_MAX_PAYLOAD = 10

# lrs credentials
LRS_ENDPOINT = 'https://lrs.adlnet.gov/xAPI/'
LRS_USERNAME = 'fakeuser'
LRS_PASSWORD = 'fakepassword'
LRS_BASICAUTH_HASH = None

OPENEDX_PLATFORM_URI = 'https://open.edx.org'
OPENEDX_USER_API_URI = OPENEDX_PLATFORM_URI + "/api/user/v1/"
OPENEDX_OAUTH2_CLIENT_ID = "foo"
OPENEDX_OAUTH2_CLIENT_SECRET = "notasecret"

# events configuration
# list of ignored event ids
IGNORED_EVENT_TYPES = []
