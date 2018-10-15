"""xAPI Statements and Activities for verbs on courses as a whole."""

import json

from tincan import Activity, ActivityDefinition, Extensions, LanguageMap, Result, Verb

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
}


class VideoStatement(block.BaseCoursewareBlockStatement):
    """ Statement base for video interaction events."""

    def get_object(self, event):
        """
        Get object for the statement.
        """
        # TODO: Yuck.  Try to use course blocks API or other way to get a proper id
        # event only passes a bare id like '1f7c045b23084e2b8f9f8a2a303c0940'
        event_data = json.loads(event['event'])
        bare_course_id = event['context']['course_id'].replace("course-v1:", "")
        block_id = 'block-v1:{}+type@video+block@{}'.format(bare_course_id, event_data['id'])
        return Activity(
            id='{}/courses/{}/jump_to/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id'], block_id),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_VIDEO,
                name=LanguageMap({'en': 'Video'}),
                description=LanguageMap({'en': 'A video in an Open edX course'}),
            ),
        )

    def get_verb(self, event):
        verb_props = VIDEO_STATE_CHANGE_VERB_MAP[event['event_type']]
        return Verb(
            id=verb_props['id'],
            display=verb_props['display'],
        )


class VideoPlayStatement(VideoStatement):
    def get_context(self, event):
        event_data = json.loads(event['event'])
        context = super(VideoStatement, self).get_context(event)
        context.extensions = Extensions({
            'http://id.tincanapi.com/extension/starting-point': event_data['currentTime']
        })
        return context


class VideoPauseStatement(VideoStatement):
    def get_context(self, event):
        event_data = json.loads(event['event'])
        context = super(VideoStatement, self).get_context(event)
        context.extensions = Extensions({
            'http://id.tincanapi.com/extension/ending-point': event_data['currentTime']
        })
        return context


class VideoSeekStatement(VideoStatement):
    def get_context(self, event):
        event_data = json.loads(event['event'])
        context = super(VideoStatement, self).get_context(event)
        context.extensions = Extensions({
            'http://id.tincanapi.com/extension/starting-point': event_data['old_time'],
            'http://id.tincanapi.com/extension/ending-point': event_data['new_time']
        })
        return context


class VideoCompleteStatement(VideoStatement):
    def get_context(self, event):
        event_data = json.loads(event['event'])
        context = super(VideoStatement, self).get_context(event)
        context.extensions = Extensions({
            'http://id.tincanapi.com/extension/ending-point': event_data['currentTime']
        })
        return context

    def get_result(self, event):
        return Result(completion=True)


class VideoTranscriptStatement(VideoStatement):
    pass
