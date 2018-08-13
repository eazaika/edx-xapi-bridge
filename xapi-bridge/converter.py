"""Convert tracking log entries to xAPI statements."""

import json

import constants
import settings


def merge(d1, d2):

    if isinstance(d1, dict) and isinstance(d2, dict):

        final = {}
        for k, v in d1.items() + d2.items():
            if k not in final:
                final[k] = v
            else:
                final[k] = merge(final[k], v)

        return final

    elif d2 is not None:
        return d2
    else:
        return d1


def to_xapi(evt):
    """Return tuple of xAPI statements or None if ignored or unhandled event type."""
    if evt['event_type'] in settings.IGNORED_EVENT_TYPES:
        return

    # set up common elements in statement
    statement = {
        'actor': {
            'account': {
                'homePage': '{}/u/{}'.format(settings.OPENEDX_PLATFORM_URI, evt['username']),
                'name': evt['username']
            },
            'name': evt['username']
        },
        'timestamp': evt['time'],
        'context': {
            'platform': settings.OPENEDX_PLATFORM_URI
        }
    }

    # event indicates a course enrollment has occurred
    if evt['event_type'] == 'edx.course.enrollment.activated':
        xapi_obj = {
            'objectType': 'Activity',
            'id': '{}/{}'.format(settings.OPENEDX_PLATFORM_URI, evt['context']['course_id']),
            'definition': {
                'type': constants.XAPI_ACTIVITY_COURSE,
                'name': {'en-US': 'Course'}
            }
        }

        xapi = merge(statement, {
            'verb': constants.XAPI_VERB_REGISTERED,
            'object': xapi_obj,
        })

        return (xapi, )


    # event indicates a course unenrollment has occurred
    if evt['event_type'] == 'edx.course.enrollment.deactivated':
        xapi_obj = {
            'objectType': 'Activity',
            'id': '{}/{}'.format(settings.OPENEDX_PLATFORM_URI, evt['context']['course_id']),
            'definition': {
                'type': constants.XAPI_ACTIVITY_COURSE,
                'name': {'en-US': 'Course'}
            }
        }

        xapi = merge(statement, {
            'verb': constants.XAPI_VERB_UNREGISTERED,
            'object': xapi_obj,
        })

        return (xapi, )

    # event indicates a problem has been attempted
    elif evt['event_type'] == 'problem_check' and evt['event_source'] == 'server':

        xapi_context = {
            'contextActivities': {
                'parent': [
                    {
                        'id': '{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, evt['context']['course_id']),
                        'definition': {
                            'name': {
                                'en-US': evt['context']['course_id'],
                            },
                            'type': constants.XAPI_ACTIVITY_COURSE
                        }
                    },
                    {
                        'id': evt['referer'],
                        'definition': {
                            'name': {
                                'en-US': evt['context']['module']['display_name'],
                            },
                            'type': constants.XAPI_ACTIVITY_BLOCK
                        }
                    }
                ],
                'other': [
                    {
                        'id': evt['referer'],
                        'definition': {
                            'type': constants.XAPI_CONTEXT_REFERRER,
                        }
                    }
                ]

            }
        }

        xapi_obj = {
            'objectType': 'Activity',
            'id': '{}{}'.format(settings.OPENEDX_PLATFORM_URI, evt['context']['path']),
            'definition': {
                'type': constants.XAPI_ACTIVITY_QUESTION,
                'name': {'en-US': evt['event_type']}
            }
        }

        xapi_result = {
            'score': {
                'raw': evt['event']['grade'],
                'min': 0,
                'max': evt['event']['max_grade'],
                'scaled': float(evt['event']['grade']) / evt['event']['max_grade']
            },
            'success': evt['event']['success'] == 'correct',
            # 'response': evt['event']['submission']['answer']
        }

        attempt = merge(statement, {
            'verb': constants.XAPI_VERB_ATTEMPTED,
            'object': xapi_obj,
            'result': xapi_result,
            'context': xapi_context
        })

        pf = merge(statement, {
            'verb': constants.XAPI_VERB_PASSED if evt['event']['success'] == 'correct' else constants.XAPI_VERB_FAILED,
            'object': xapi_obj,
            'result': xapi_result,
            'context': xapi_context
        })

        return attempt, pf

    # event indicates a video was loaded
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'load_video':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': constants.XAPI_VERB_LAUNCHED,
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Loaded Video"}
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video was played
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'play_video':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/progressed',
                'display': {
                    'en-US': 'Progressed'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Played Video"}
                }
            },
            'result': {
                'extensions': {
                    'ext:currentTime': event['currentTime']
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video was paused
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'pause_video':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/suspended',
                'display': {
                    'en-US': 'Suspended'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Paused Video"}
                }
            },
            'result': {
                'extensions': {
                    'ext:currentTime': event['currentTime']
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video was stopped
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'stop_video':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/completed',
                'display': {
                    'en-US': 'Completed'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Completed Video"}
                }
            },
            'result': {
                'extensions': {
                    'ext:currentTime': event['currentTime']
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video was seeked
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'seek_video':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/interacted',
                'display': {
                    'en-US': 'Interacted'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Video seek"}
                }
            },
            'result': {
                'extensions': {
                    'ext:old_time': event['old_time'],
                    'ext:new_time': event['new_time'],
                    'ext:type': event['type']
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video speed was changed
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'speed_change_video':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/interacted',
                'display': {
                    'en-US': 'Interacted'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Video speed change"}
                }
            },
            'result': {
                'extensions': {
                    'ext:currentTime': event['current_time'],
                    'ext:old_speed': event['old_speed'],
                    'ext:new_speed': event['new_speed'],
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video transcript was hidden
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'hide_transcript':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/interacted',
                'display': {
                    'en-US': 'Interacted'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Video transcript hidden"}
                }
            },
            'result': {
                'extensions': {
                    'ext:currentTime': event['currentTime']
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    # event indicates a video transcript was shown
    # TODO: event type has bad (not URI) object format
    elif evt['event_type'] == 'show_transcript':

        event = json.loads(evt['event'])

        stmt = merge(statement, {
            'verb': {
                'id': 'http://adlnet.gov/expapi/verbs/interacted',
                'display': {
                    'en-US': 'Interacted'
                }
            },
            'object': {
                'objectType': 'Activity',
                'id': 'i4x://' + evt['context']['course_id'] + event['id'],
                'definition': {
                    'name': {'en-US': "Video transcript shown"}
                }
            },
            'result': {
                'extensions': {
                    'ext:currentTime': event['currentTime']
                }
            },
            'context': {
                'contextActivities': {
                    'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
                }
            }
        })

        return (stmt, )

    else:
        return None
