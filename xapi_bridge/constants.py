"""Constants for xAPI vocabulary."""

# xAPI verbs
XAPI_VERB_ATTEMPTED = "http://adlnet.gov/expapi/verbs/attempted"
XAPI_VERB_FAILED = "http://adlnet.gov/expapi/verbs/failed"
XAPI_VERB_PASSED = "http://adlnet.gov/expapi/verbs/passed"
XAPI_VERB_LAUNCHED = "http://adlnet.gov/expapi/verbs/launched"
XAPI_VERB_REGISTERED = "http://adlnet.gov/expapi/verbs/registered"
XAPI_VERB_UNREGISTERED = "http://id.tincanapi.com/verb/unregistered"
XAPI_VERB_COMPLETED = "http://adlnet.gov/expapi/verbs/completed"

XAPI_VERB_INITIALIZED = "http://adlnet.gov/expapi/verbs/initialized"
XAPI_VERB_PLAYED = "https://w3id.org/xapi/video/verbs/played"
XAPI_VERB_PAUSED = "https://w3id.org/xapi/video/verbs/paused"
XAPI_VERB_SEEKED = "https://w3id.org/xapi/video/verbs/seeked"
XAPI_VERB_INTERACTED = "http://adlnet.gov/expapi/verbs/interacted"

# xAPI activities
XAPI_ACTIVITY_QUESTION = 'http://adlnet.gov/expapi/activities/question'
XAPI_ACTIVITY_COURSE = 'http://adlnet.gov/expapi/activities/course'
XAPI_ACTIVITY_BLOCK = 'https://w3id.org/xapi/cmi5/activities/block'
XAPI_ACTIVITY_VIDEO = 'https://w3id.org/xapi/video/activity-type/video'

# xAPI context
XAPI_CONTEXT_REFERRER = "http://id.tincanapi.com/extension/referrer"
XAPI_CONTEXT_VIDEO_LENGTH = "https://w3id.org/xapi/video/extensions/length"
XAPI_CONTEXT_VIDEO_CC_LANGUAGE = "https://w3id.org/xapi/video/extensions/cc-subtitle-lang"

# xAPI result
XAPI_RESULT_VIDEO_TIME = "https://w3id.org/xapi/video/extensions/time"
XAPI_RESULT_VIDEO_TIME_FROM = "https://w3id.org/xapi/video/extensions/time-from"
XAPI_RESULT_VIDEO_TIME_TO = "https://w3id.org/xapi/video/extensions/time-to"
XAPI_RESULT_VIDEO_CC_ENABLED = "https://w3id.org/xapi/video/extensions/cc-enabled"
XAPI_RESULT_VIDEO_PROGRESS = "https://w3id.org/xapi/video/extensions/progress"

# Open edX
OPENEDX_OAUTH2_TOKEN_URL = "/oauth2/access_token"
