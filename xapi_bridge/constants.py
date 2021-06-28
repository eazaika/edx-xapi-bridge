"""Constants for xAPI vocabulary."""

# xAPI verbs
XAPI_VERB_ATTACHED = "http://activitystrea.ms/schema/1.0/attach"
XAPI_VERB_ATTEMPTED = "http://adlnet.gov/expapi/verbs/attempted"
XAPI_VERB_ANSWERED = "http://adlnet.gov/expapi/verbs/answered"
XAPI_VERB_FAILED = "http://adlnet.gov/expapi/verbs/failed"
# XAPI_VERB_PASSED = "http://adlnet.gov/expapi/verbs/passed"
XAPI_VERB_WATCHED = "http://activitystrea.ms/schema/1.0/watch"
XAPI_VERB_EXITED = "http://adlnet.gov/expapi/verbs/exited"
XAPI_VERB_LAUNCHED = "http://adlnet.gov/expapi/verbs/launched"
XAPI_VERB_REGISTERED = "http://adlnet.gov/expapi/verbs/registered"
XAPI_VERB_UNREGISTERED = "http://id.tincanapi.com/verb/unregistered"
XAPI_VERB_COMPLETED = "http://adlnet.gov/expapi/verbs/completed"
XAPI_VERB_EXPERIENCED = "http://activitystrea.ms/schema/1.0/experience"

XAPI_VERB_INITIALIZED = "http://adlnet.gov/expapi/verbs/initialized"
XAPI_VERB_PLAYED = "http://activitystrea.ms/schema/1.0/play"
XAPI_VERB_PAUSED = "http://id.tincanapi.com/verb/paused"
XAPI_VERB_INTERACTED = "http://activitystrea.ms/schema/1.0/interact"

# xAPI activities
XAPI_ACTIVITY_QUESTION = 'http://adlnet.gov/expapi/activities/question'
XAPI_ACTIVITY_INTERACTION = 'http://adlnet.gov/expapi/activities/interaction'
XAPI_ACTIVITY_COURSE = 'http://adlnet.gov/expapi/activities/course'
XAPI_ASSESSMENT_MODULE = 'http://adlnet.gov/expapi/activities/assessment'
XAPI_ACTIVITY_VIDEO = 'http://activitystrea.ms/schema/1.0/video'
XAPI_ACTIVITY_LINK = 'http://adlnet.gov/expapi/activities/link'
XAPI_ACTIVITY_POSITION = 'http://id.tincanapi.com/extension/position'

# xAPI context
XAPI_CONTEXT_REFERRER = "http://id.tincanapi.com/extension/referrer"
XAPI_CONTEXT_VIDEO_LENGTH = "http://id.tincanapi.com/extension/duration"
XAPI_CONTEXT_VIDEO_CC_LANGUAGE = "https://w3id.org/xapi/video/extensions/cc-subtitle-lang"
XAPI_CONTEXT_STARTING_POSITION = "http://id.tincanapi.com/extension/starting-position"
XAPI_CONTEXT_ENDING_POSITION = "http://id.tincanapi.com/extension/ending-point"

# xAPI result
XAPI_RESULT_VIDEO_TIME = "https://w3id.org/xapi/video/extensions/time"
XAPI_RESULT_VIDEO_TIME_FROM = "https://w3id.org/xapi/video/extensions/time-from"
XAPI_RESULT_VIDEO_TIME_TO = "https://w3id.org/xapi/video/extensions/time-to"
XAPI_RESULT_VIDEO_CC_ENABLED = "https://w3id.org/xapi/video/extensions/cc-enabled"
XAPI_RESULT_VIDEO_PROGRESS = "https://w3id.org/xapi/video/extensions/progress"

# Open edX
OPENEDX_OAUTH2_TOKEN_URL = "/oauth2/access_token"
BLOCK_OBJECT_ID_FORMAT = "{platform}/xblock/{block_usage_key}"
ENROLLMENT_API_URL_FORMAT = "/api/enrollment/v1/enrollment/{username},{course_id}"
