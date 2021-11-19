"""Convert tracking log entries to xAPI statements."""

import logging

from xapi_bridge import exceptions, settings
from xapi_bridge.statements import base, course, problem, video, vertical_block, attachment


logger = logging.getLogger(__name__)


TRACKING_EVENTS_TO_XAPI_STATEMENT_MAP = {

    # course enrollment
    'edx.course.enrollment.activated': course.CourseEnrollmentStatement,
    'edx.course.enrollment.deactivated': course.CourseUnenrollmentStatement,
    'edx.course.completed': course.CourseCompletionStatement,
    'edx.course.expell': course.CourseExpellStatement,

    # course completion
    #'edx.certificate.created': course.CourseCompletionStatement,

    # vertical block - composite kim completion
    'complete_vertical': vertical_block.VerticalBlockCompleteStatement,

    # problems
    'problem_check': problem.ProblemCheckStatement,
    'edx.attachment': attachment.AttachmentStatement,

    # 'edx.drag_and_drop_v2.item.dropped'

    # video
    #'ready_video': video.VideoStatement,
    #'load_video': video.VideoStatement,
    #'edx.video.loaded': video.VideoStatement,

    #'play_video': video.VideoPlayStatement,
    #'edx.video.played': video.VideoPlayStatement,

    'pause_video': video.VideoStatement,
    'video_check': video.VideoCheckStatement,
    'stop_video': video.VideoCompleteStatement,
    #'edx.video.stopped': video.VideoCompleteStatement,

    #'show_transcript': video.VideoTranscriptStatement,
    #'hide_transcript': video.VideoTranscriptStatement,
    #'edx.video.transcript.shown': video.VideoTranscriptStatement,
    #'edx.video.transcript.hidden': video.VideoTranscriptStatement,
    #'edx.video.closed_captions.shown': video.VideoTranscriptStatement,
    #'edx.video.closed_captions.hidden': video.VideoTranscriptStatement,
}


def to_xapi(evt):
    """Return tuple of xAPI statements or None if ignored or unhandled event type."""

    # strip Video XBlock prefixes for checking
    event_type = evt['event_type'].replace("xblock-video.", "")

    if event_type in settings.IGNORED_EVENT_TYPES:
        return  # deliberately ignored event

    # filter video_check from problem_check
    event_source = evt['event_source']
    if event_type == 'problem_check' and event_source == 'server':
        event_data = evt['event']
        data = event_data['answers'][event_data['answers'].keys()[0]]
        if 'watch_times' in data:
            event_type = 'video_check'

    try:
        statement_class = TRACKING_EVENTS_TO_XAPI_STATEMENT_MAP[event_type]
    except KeyError:  # untracked event
        return

    try:
        statement = statement_class(evt)
        if hasattr(statement, 'version'):  # make sure it's a proper statement
            return (statement, )
        else:
            message = "Statement missing version."
            raise exceptions.XAPIBridgeStatementConversionError(event=evt, message=message)
    except exceptions.XAPIBridgeSkippedConversion as e:
        logger.debug("Skipping conversion of event with message {}.  Event was {}".format(e.message, evt))
