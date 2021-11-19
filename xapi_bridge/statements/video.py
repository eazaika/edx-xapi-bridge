# -*- coding: utf-8 -*-
"""xAPI Statements and Activities for verbs on courses as a whole.

Conformant with ADLNet Video xAPI Profile https://w3id.org/xapi/video/v1.0.2
"""
import datetime
import json
from tincan import Activity, ActivityDefinition, ActivityList, Context, ContextActivities, Extensions, LanguageMap, Result, Verb
from tincan.conversions.iso8601 import jsonify_timedelta

import block
import course
from xapi_bridge import constants, exceptions, settings


VIDEO_STATE_CHANGE_VERB_MAP = {
    'watch_video': {
        'id': constants.XAPI_VERB_WATCHED,
        'display': LanguageMap({'en-US': 'watched', 'ru-RU': 'просмотр видео'})
    },
    'problem_check': {
        'id': constants.XAPI_VERB_COMPLETED,
        'display': LanguageMap({'en-US': 'check video watched', 'ru-RU': 'подтвердил просмотр видео'})
    },
    'load_video': {
        'id': constants.XAPI_VERB_INITIALIZED,
        'display': LanguageMap({'en-US': 'loaded'})
    },
    'ready_video': {
        'id': constants.XAPI_VERB_INITIALIZED,
        'display': LanguageMap({'en-US': 'loaded'})
    },
    'play_video': {
        'id': constants.XAPI_VERB_PLAYED,
        'display': LanguageMap({'en-US': 'played'})
    },
    'pause_video': {
        'id': constants.XAPI_VERB_PAUSED,
        'display': LanguageMap({'en-US': 'paused', 'ru-RU': 'видео приостановлено'})
    },
    'stop_video': {
        'id': constants.XAPI_VERB_COMPLETED,
        'display': LanguageMap({'en-US': 'completed'})
    },
    'show_transcript': {
        'id': constants.XAPI_VERB_INTERACTED,
        'display': LanguageMap({'en-US': 'video transcript shown'})
    },
    'hide_transcript': {
        'id': constants.XAPI_VERB_INTERACTED,
        'display': LanguageMap({'en-US': 'video transcript hidden'})
    },
    'edx.video.closed_captions.shown': {
        'id': constants.XAPI_VERB_INTERACTED,
        'display': LanguageMap({'en-US': 'video captions shown'})
    },
    'edx.video.closed_captions.hidden': {
        'id': constants.XAPI_VERB_INTERACTED,
        'display': LanguageMap({'en-US': 'video captions hidden'})
    },

}


class VideoStatement(block.BaseCoursewareBlockStatement):
    """ Statement base for video interaction events."""

    def _get_activity_id(self, event):
        if event['event_source'] == 'server':
            return super(VideoStatement, self)._get_activity_id(event)

        # TODO: Yuck.  Try to use course blocks API or other way to get a proper id
        # browser event source event won't have the module id
        # event only passes a bare id like '1f7c045b23084e2b8f9f8a2a303c0940'
        format_str = constants.BLOCK_OBJECT_ID_FORMAT
        platform_str = settings.OPENEDX_PLATFORM_URI
        bare_course_id = event['context']['course_id'].replace("course-v1:", "")
        block_type = "video+xblock" if 'xblock-video' in event['event_type'] else "video+block"
        block_id = 'block-v1:{}+type@{}@{}'.format(bare_course_id, block_type, self.get_event_data(event)['id'])
        return format_str.format(platform=platform_str, block_usage_key=block_id)

    def get_object(self, event):
        """
        Get object for the statement.
        """
        event_data = self.get_event_data(event)
        duration = event_data.get('duration', event_data.get('duration', 0))
        total_time = jsonify_timedelta(datetime.timedelta(seconds=duration))

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_VIDEO,
                name=LanguageMap({'en-EN': event_data.get('name', event_data.get('name', 'video'))}),
                description=LanguageMap({'en-US': 'A video in an Open edX course'}),
                extensions={
                    constants.XAPI_CONTEXT_VIDEO_LENGTH: total_time,
                }
            ),
        )

    def get_verb(self, event):
        event_type = event['event_type']
        try:
            verb_props = VIDEO_STATE_CHANGE_VERB_MAP[event_type]
        except KeyError:
            return exceptions.XAPIBridgeSkippedConversion("unhandled video event: {}".format(event_type))
        return Verb(
            id=verb_props['id'],
            display=verb_props['display'],
        )

    def get_result(self, event):
        event_data = self.get_event_data(event)
        cur_time = event_data.get('currentTime', event_data.get('current_time', 0))
        cur_time = float('{:.2f}'.format(cur_time))
        cur_time = jsonify_timedelta((datetime.timedelta(seconds=cur_time)))

        return Result(
            success=True,
            completion=False,
            duration=cur_time
        )

    def get_context(self, event):
        return super(VideoStatement, self).get_context(event)

    def get_context_activities(self, event):
        parent_activities = [
            Activity(
                id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
                definition=course.CourseActivityDefinition(event)
            ),
            Activity(
                id=event['referer'],
                definition=block.BlockActivityDefinition(event)
            )
        ]

        return ContextActivities(
            parent=ActivityList(parent_activities)
        )


class VideoCheckStatement(VideoStatement):
    """Statement for student check out of video watching."""
    def get_object(self, event):
        """
        Get object for the statement.
        """
        event_data = self.get_event_data(event)
        data = event_data['answers'][event_data['answers'].keys()[0]]
        answer = json.loads(json.loads(data)['answer'])

        duration = answer['video_length']
        total_time = jsonify_timedelta(datetime.timedelta(seconds=duration))

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_VIDEO,
                name=LanguageMap({'en-EN': answer['video_title']}),
                description=LanguageMap({'en-US': 'A video in an Open edX course'}),
                extensions={
                    constants.XAPI_CONTEXT_VIDEO_LENGTH: total_time,
                }
            ),
        )

    def get_result(self, event):
        event_data = self.get_event_data(event)

        correct = False
        if event_data['success'] == 'correct':
            correct = True

        return Result(
            success=True,
            completion=correct,
            score={
                'raw': event_data['grade'],
                'min': 0,
                'max': event_data['max_grade'],
                'scaled': event_data['grade'] / event_data['max_grade']
            }
        )


class VideoSeekStatement(VideoStatement):
    def get_result(self, event):
        result = super(VideoSeekStatement, self).get_result(event)
        event_data = self.get_event_data(event)
        prev_time = event_data.get('old_time', event_data['previous_time'])
        new_time = event_data.get('new_time')
        result.extensions.update({
            constants.XAPI_RESULT_VIDEO_TIME_FROM: prev_time,
            constants.XAPI_RESULT_VIDEO_TIME_TO: new_time
        })
        return result


class VideoCompleteStatement(VideoStatement):

    def get_result(self, event):
        # TODO: consider calculating real progress. For now assume 100% if played til end
        # profile includes concept of a completion threshold which could be below 100% anyhow
        result = super(VideoCompleteStatement, self).get_result(event)
        result.completion = True
        return result


class VideoTranscriptStatement(VideoStatement):

    def get_result(self, event):
        # xAPI video profile doesn't differentiate between transcripts, subtitles, and closed captioning :(
        result = super(VideoTranscriptStatement, self).get_result(event)
        result.extensions.update({
            constants.XAPI_RESULT_VIDEO_CC_ENABLED: True if 'show_transcript' in event['event_type'] or
            'closed_captions.shown' in event['event_type'] else False,
        })
        return result

    def get_context(self, event):
        # Show transcript and hide transcript only offer currentTime as context data.
        # TODO: get language from Video XBlock events at least, once available
        context = super(VideoTranscriptStatement, self).get_context(event)
        context.extensions = Extensions({
            constants.XAPI_CONTEXT_VIDEO_CC_LANGUAGE: "en"  # we don't get this info from tracking log
        })
        return context
