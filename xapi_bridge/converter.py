"""Convert tracking log entries to xAPI statements."""

from xapi_bridge import exceptions, settings
from xapi_bridge.statements import base, course, problem, video


TRACKING_EVENTS_TO_XAPI_STATEMENT_MAP = {

    # course enrollment
    'edx.course.enrollment.activated': course.CourseEnrollmentStatement,
    'edx.course.enrollment.deactivated': course.CourseUnenrollmentStatement,

    # course completion
    'edx.certificate.created': course.CourseCompletionStatement,

    # problems
    'problem_check': problem.ProblemCheckStatement,

    # video
    'ready_video': video.VideoStatement,
    'load_video': video.VideoStatement,
    'edx.video.loaded': video.VideoStatement,

    'play_video': video.VideoPlayStatement,
    'edx.video.played': video.VideoPlayStatement,

    'pause_video': video.VideoPauseStatement,
    'edx.video.paused': video.VideoPauseStatement,

    'stop_video': video.VideoCompleteStatement,
    'edx.video.stopped': video.VideoCompleteStatement,

    'seek_video': video.VideoSeekStatement,
    'edx.video.position.changed': video.VideoSeekStatement,

    'show_transcript': video.VideoTranscriptStatement,
    'hide_transcript': video.VideoTranscriptStatement,
    'edx.video.transcript.shown': video.VideoTranscriptStatement,
    'edx.video.transcript.hidden': video.VideoTranscriptStatement,
    # 'edx.video.language_menu.shown': u'video_show_cc_menu',
    # 'edx.video.language_menu.hidden': u'video_hide_cc_menu',
}


def to_xapi(evt):
    """Return tuple of xAPI statements or None if ignored or unhandled event type."""

    # strip Video XBlock prefixes for checking
    event_type = evt['event_type'].replace("xblock-video.", "")

    if event_type in settings.IGNORED_EVENT_TYPES:
        return

    try:
        statement_class = TRACKING_EVENTS_TO_XAPI_STATEMENT_MAP[event_type]
    except KeyError:
        return

    try:
        statement = statement_class(evt)
        if hasattr(statement, 'version'):  # make sure it's a proper statement
            return (statement, )
    except exceptions.XAPIMalformedStatementError:
        print "Refusing to send statement {}".format(statement.to_json())

    #     xapi_result = {
    #         'score': {
    #             'raw': evt['event']['grade'],
    #             'min': 0,
    #             'max': evt['event']['max_grade'],
    #             'scaled': float(evt['event']['grade']) / evt['event']['max_grade']
    #         },
    #         'success': evt['event']['success'] == 'correct',
    #         # 'response': evt['event']['submission']['answer']
    #     }

    #     attempt = merge(statement, {
    #         'verb': constants.XAPI_VERB_ATTEMPTED,
    #         'object': xapi_obj,
    #         'result': xapi_result,
    #         'context': xapi_context
    #     })

    #     pf = merge(statement, {
    #         'verb': constants.XAPI_VERB_PASSED if evt['event']['success'] == 'correct' else constants.XAPI_VERB_FAILED,
    #         'object': xapi_obj,
    #         'result': xapi_result,
    #         'context': xapi_context
    #     })

    #     return attempt, pf

    # # event indicates a video was loaded
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'load_video':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': constants.XAPI_VERB_LAUNCHED,
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Loaded Video"}
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video was played
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'play_video':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/progressed',
    #             'display': {
    #                 'en-US': 'Progressed'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Played Video"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:currentTime': event['currentTime']
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video was paused
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'pause_video':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/suspended',
    #             'display': {
    #                 'en-US': 'Suspended'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Paused Video"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:currentTime': event['currentTime']
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video was stopped
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'stop_video':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/completed',
    #             'display': {
    #                 'en-US': 'Completed'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Completed Video"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:currentTime': event['currentTime']
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video was seeked
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'seek_video':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/interacted',
    #             'display': {
    #                 'en-US': 'Interacted'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Video seek"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:old_time': event['old_time'],
    #                 'ext:new_time': event['new_time'],
    #                 'ext:type': event['type']
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video speed was changed
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'speed_change_video':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/interacted',
    #             'display': {
    #                 'en-US': 'Interacted'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Video speed change"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:currentTime': event['current_time'],
    #                 'ext:old_speed': event['old_speed'],
    #                 'ext:new_speed': event['new_speed'],
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video transcript was hidden
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'hide_transcript':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/interacted',
    #             'display': {
    #                 'en-US': 'Interacted'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Video transcript hidden"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:currentTime': event['currentTime']
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # # event indicates a video transcript was shown
    # # TODO: event type has bad (not URI) object format
    # elif evt['event_type'] == 'show_transcript':

    #     event = json.loads(evt['event'])

    #     stmt = merge(statement, {
    #         'verb': {
    #             'id': 'http://adlnet.gov/expapi/verbs/interacted',
    #             'display': {
    #                 'en-US': 'Interacted'
    #             }
    #         },
    #         'object': {
    #             'objectType': 'Activity',
    #             'id': 'i4x://' + evt['context']['course_id'] + event['id'],
    #             'definition': {
    #                 'name': {'en-US': "Video transcript shown"}
    #             }
    #         },
    #         'result': {
    #             'extensions': {
    #                 'ext:currentTime': event['currentTime']
    #             }
    #         },
    #         'context': {
    #             'contextActivities': {
    #                 'parent': [{'id': 'i4x://' + evt['context']['course_id']}]
    #             }
    #         }
    #     })

    #     return (stmt, )

    # else:
    #     return None
