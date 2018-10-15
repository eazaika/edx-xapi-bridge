"""xAPI Statements and Activities for verbs on courses as a whole.

Conformant with ADLNet Video xAPI Profile https://w3id.org/xapi/video/v1.0.2
"""

from tincan import Activity, ActivityDefinition, Context, ContextActivities, Extensions, LanguageMap, Result, Verb

import block
from xapi_bridge import constants, settings


VIDEO_STATE_CHANGE_VERB_MAP = {
    'load_video': {
        'id': constants.XAPI_VERB_INITIALIZED,
        'display': LanguageMap({'en': 'loaded'})
    },
    'play_video': {
        'id': constants.XAPI_VERB_PLAYED,
        'display': LanguageMap({'en': 'played'})
    },
    'pause_video': {
        'id': constants.XAPI_VERB_PAUSED,
        'display': LanguageMap({'en': 'paused'})
    },
    'stop_video': {
        'id': constants.XAPI_VERB_COMPLETED,
        'display': LanguageMap({'en': 'completed'})
    },
    'seek_video': {
        'id': constants.XAPI_VERB_SEEKED,
        'display': LanguageMap({'en': 'seeked'})
    },
    'show_transcript': {
        'id': constants.XAPI_VERB_INTERACTED,
        'display': LanguageMap({'en': 'show transcript'})
    },
    'hide_transcript': {
        'id': constants.XAPI_VERB_INTERACTED,
        'display': LanguageMap({'en': 'hide transcript'})
    },
}


class VideoStatement(block.BaseCoursewareBlockStatement):
    """ Statement base for video interaction events."""

    def get_object(self, event):
        """
        Get object for the statement.
        """
        # TODO: Yuck.  Try to use course blocks API or other way to get a proper id
        # event only passes a bare id like '1f7c045b23084e2b8f9f8a2a303c0940'
        bare_course_id = event['context']['course_id'].replace("course-v1:", "")
        block_id = 'block-v1:{}+type@video+block@{}'.format(bare_course_id, self.get_event_data(event)['id'])
        return Activity(
            id='{}/courses/{}/jump_to/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id'], block_id),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_VIDEO,
                name=LanguageMap({'en': 'Video'}),
                description=LanguageMap({'en': 'A video in an Open edX course'}),
            ),
        )

    def get_verb(self, event):
        event_type = event['event_type'].replace("xblock-video.", "")
        verb_props = VIDEO_STATE_CHANGE_VERB_MAP[event_type]
        return Verb(
            id=verb_props['id'],
            display=verb_props['display'],
        )

    def get_result(self, event):
        return Result(
            extensions={
                constants.XAPI_RESULT_VIDEO_TIME: self.get_event_data(event)['currentTime'],
            })

    def get_context(self, event):
        return super(VideoStatement, self).get_context(event)


class VideoPlayStatement(VideoStatement):
    pass


class VideoPauseStatement(VideoStatement):
    def get_context(self, event):
        # TODO: not implemented but float video length value required for spec
        # info is not included in tracking log event.  We should add that information
        # in the Video XBlock
        context = super(VideoPauseStatement, self).get_context(event)
        context.extensions = {
            constants.XAPI_CONTEXT_VIDEO_LENGTH: 0.0
        }
        return context


class VideoSeekStatement(VideoStatement):
    def get_result(self, event):
        result = super(VideoSeekStatement, self).get_result(event)
        result.extensions = Extensions(result.extensions.update({
            constants.XAPI_RESULT_VIDEO_TIME_FROM: self.get_event_data(event)['old_time'],
            constants.XAPI_RESULT_VIDEO_TIME_TO: self.get_event_data(event)['new_time']
        }))
        return result


class VideoCompleteStatement(VideoStatement):
    def get_context(self, event):
        context = super(VideoCompleteStatement, self).get_context(event)
        context.extensions = Extensions({
            #  length will be same as current time once stopped
            constants.XAPI_CONTEXT_VIDEO_LENGTH: self.get_event_data(event)['currentTime']
        })
        return context

    def get_result(self, event):
        # TODO: consider calculating real progress. For now assume 100% if played til end
        # profile includes concept of a completion threshold which could be below 100% anyhow
        result = super(VideoCompleteStatement, self).get_result(event)
        result.completion = True
        result.extensions = {
            constants.XAPI_RESULT_VIDEO_TIME: self.get_event_data(event)['currentTime'],
            constants.XAPI_RESULT_VIDEO_PROGRESS: 100  # this isn't necessarily true if student skipped content
        }
        return result


class VideoTranscriptStatement(VideoStatement):

    def get_result(self, event):
        # xAPI video profile doesn't differentiate between transcripts, subtitles, and closed captioning :(
        result = super(VideoTranscriptStatement, self).get_result(event)
        result.extensions = {
            constants.XAPI_RESULT_VIDEO_CC_ENABLED: True if event['event_type'].contains('show_transcript') else False,
        }
        return result

    def get_context(self, event):
        # Show transcript and hide transcript only offer currentTime as context data.
        # TODO: get language from Video XBlock events at least, once available
        context = super(VideoTranscriptStatement, self).get_context(event)
        context.context_activities = ContextActivities(super(VideoTranscriptStatement, self).get_object(event))
        context.extensions = Extensions({
            constants.XAPI_CONTEXT_VIDEO_CC_LANGUAGE: "en"  # we don't get this info from tracking log
        })
        return context
