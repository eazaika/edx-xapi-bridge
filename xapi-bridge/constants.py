"""Constants for xAPI vocabulary."""


# verbs
XAPI_VERB_ATTEMPTED = {"id": "http://adlnet.gov/expapi/verbs/attempted", "display": {"en-US": "attempted", "en-GB": "attempted"}}
XAPI_VERB_FAILED = {"id": "http://adlnet.gov/expapi/verbs/failed", "display": {"en-US": "failed", "en-GB": "failed"}}
XAPI_VERB_PASSED = {"id": "http://adlnet.gov/expapi/verbs/passed", "display": {"en-US": "passed", "en-GB": "passed"}}
XAPI_VERB_LAUNCHED = {"id": "http://adlnet.gov/expapi/verbs/launched", "display": {"en-US": "launched", "en-GB": "launched"}}
XAPI_VERB_REGISTERED = {"id": "http://adlnet.gov/expapi/verbs/registered", "display": {"en-US": "enrolled", "en-GB": "enroled"}}
XAPI_VERB_UNREGISTERED = {"id": "http://id.tincanapi.com/verb/unregistered", "display": {"en-US": "unenrolled", "en-GB": "unenroled"}}
XAPI_VERB_COMPLETED = {"id": "http://adlnet.gov/expapi/verbs/completed", "display": {"en-US": "completed", "en-GB": "completed"}}

# activities
XAPI_ACTIVITY_QUESTION = 'http://adlnet.gov/expapi/activities/question'
XAPI_ACTIVITY_COURSE = 'http://adlnet.gov/expapi/activities/course'
XAPI_ACTIVITY_BLOCK = 'https://w3id.org/xapi/cmi5/activities/block'

#context
XAPI_CONTEXT_REFERRER = "http://id.tincanapi.com/extension/referrer"
