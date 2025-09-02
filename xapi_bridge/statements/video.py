"""
xAPI Statements and Activities for video interactions in Open edX.

"""

import datetime
import json
import logging
from typing import Dict, Any, Optional

from tincan import (
    Activity, ActivityDefinition, ActivityList, Context,
    ContextActivities, Extensions, LanguageMap, Result, Verb
)
from tincan.conversions.iso8601 import jsonify_timedelta

from . import block, course
from xapi_bridge import constants, exceptions, settings


logger = logging.getLogger(__name__)

VIDEO_STATE_CHANGE_VERB_MAP = {
    'watch_video': {
        'id': constants.XAPI_VERB_WATCHED,
        'display': LanguageMap({'en-US': 'watched', 'ru-RU': 'просмотр видео'})
    },
    'play_video': {
        'id': constants.XAPI_VERB_PLAYED,
        'display': LanguageMap({'en-US': 'played', 'ru-RU': 'воспроизведение видео'})
    },
    'pause_video': {
        'id': constants.XAPI_VERB_PAUSED,
        'display': LanguageMap({'en-US': 'paused', 'ru-RU': 'пауза видео'})
    },
    'stop_video': {
        'id': constants.XAPI_VERB_EXITED,
        'display': LanguageMap({'en-US': 'stopped', 'ru-RU': 'остановка видео'})
    },
}

class VideoStatement(block.BaseCoursewareBlockStatement):
    """Base statement for video interaction events in Open edX."""

    def _get_activity_id(self, event: Dict[str, Any]) -> str:
        """
        Constructs activity ID based on event source.

        Args:
            event: Video interaction event data

        Returns:
            str: Unique activity ID in IRI format
        """
        if event['event_source'] == 'server':
            return super()._get_activity_id(event)

        # Генерация ID для событий из браузера
        bare_course_id = event['context']['course_id'].replace("course-v1:", "")
        block_type = "video+xblock" if 'xblock-video' in event['event_type'] else "video+block"
        block_id = f'block-v1:{bare_course_id}+type@{block_type}@{self.get_event_data(event)["id"]}'
        return constants.BLOCK_OBJECT_ID_FORMAT.format(
            platform=settings.OPENEDX_PLATFORM_URI,
            block_usage_key=block_id
        )

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """
        Constructs video activity object.

        Args:
            event: Tracking log event data

        Returns:
            Activity: xAPI video activity
        """
        event_data = self.get_event_data(event)
        duration = event_data.get('duration', 0)

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_VIDEO,
                name=LanguageMap({'en-US': event_data.get('name', 'Unnamed Video')}),
                description=LanguageMap({'en-US': 'Open edX course video'}),
                extensions={
                    constants.XAPI_CONTEXT_VIDEO_LENGTH: jsonify_timedelta(
                        datetime.timedelta(seconds=duration)
                    )
                }
            )
        )

    def get_verb(self, event: Dict[str, Any]) -> Verb:
        """
        Maps Open edX video events to xAPI verbs.

        Args:
            event: Video interaction event

        Returns:
            Verb: xAPI verb object

        Raises:
            XAPIBridgeSkippedConversion: For unhandled event types
        """
        event_type = event['event_type'].replace("xblock-video.", "").strip()
        try:
            verb_props = VIDEO_STATE_CHANGE_VERB_MAP[event_type]
        except KeyError as exc:
            raise exceptions.XAPIBridgeSkippedConversion(
                event_type,
                f"Unhandled video event: {event_type}"
            ) from exc

        return Verb(
            id=verb_props['id'],
            display=verb_props['display']
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        """Constructs result with video playback progress."""
        event_data = self.get_event_data(event)
        current_time = float('{:.2f}'.format(
            event_data.get('currentTime', event_data.get('current_time', 0))
        ))

        return Result(
            success=True,
            completion=False,
            duration=jsonify_timedelta(
                datetime.timedelta(seconds=current_time))
        )

    def get_context_activities(self, event: Dict[str, Any]) -> ContextActivities:
        """Builds parent course and block context."""
        parent_activities = [
            Activity(
                id=f"{settings.OPENEDX_PLATFORM_URI}/courses/{event['context']['course_id']}",
                definition=course.CourseActivityDefinition(event)
            ),
            Activity(
                id=event['referer'],
                definition=block.BlockActivityDefinition(event)
            )
        ]
        return ContextActivities(parent=ActivityList(parent_activities))


class VideoCheckStatement(VideoStatement):
    """Handles video progress check events (problem_check)."""

    def get_object(self, event: Dict[str, Any]) -> Activity:
        """Constructs activity from problem check data."""
        event_data = self.get_event_data(event)
        event_type = event['event_type']
        try:
            answer_key = list(event_data['answers'].keys())[0]  # Python 3 dict key handling
            data = json.loads(json.loads(event_data['answers'][answer_key])['answer'])
        except (KeyError, json.JSONDecodeError) as exc:
            logger.error("Invalid video check data: %s", exc)
            raise exceptions.XAPIBridgeSkippedConversion(
                event_type,
                "Invalid video check format"
            ) from exc

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_VIDEO,
                name=LanguageMap({'en-US': data['video_title']}),
                extensions={
                    constants.XAPI_CONTEXT_VIDEO_LENGTH: jsonify_timedelta(
                        datetime.timedelta(seconds=data['video_length']))
                }
            )
        )

    def get_result(self, event: Dict[str, Any]) -> Result:
        """Constructs graded result."""
        event_data = self.get_event_data(event)
        return Result(
            success=event_data.get('success') == 'correct',
            score={
                'raw': event_data['grade'],
                'min': 0,
                'max': event_data['max_grade'],
                'scaled': event_data['grade'] / event_data['max_grade']
            }
        )


class VideoSeekStatement(VideoStatement):
    """Handles video seeking events."""

    def get_result(self, event: Dict[str, Any]) -> Result:
        """Adds seek time extensions."""
        result = super().get_result(event)
        event_data = self.get_event_data(event)
        result.extensions.update({
            constants.XAPI_RESULT_VIDEO_TIME_FROM: event_data.get('old_time', 0),
            constants.XAPI_RESULT_VIDEO_TIME_TO: event_data.get('new_time', 0)
        })
        return result


class VideoCompleteStatement(VideoStatement):
    """Marks video as fully completed."""

    def get_result(self, event: Dict[str, Any]) -> Result:
        """Marks completion as True."""
        result = super().get_result(event)
        result.completion = True
        return result


class VideoTranscriptStatement(VideoStatement):
    """Handles transcript/captions interactions."""

    def get_result(self, event: Dict[str, Any]) -> Result:
        """Adds CC enabled extension."""
        result = super().get_result(event)
        result.extensions[constants.XAPI_RESULT_VIDEO_CC_ENABLED] = any(
            key in event['event_type'] for key in ['show_transcript', 'closed_captions.shown']
        )
        return result

    def get_context(self, event: Dict[str, Any]) -> Context:
        """Adds CC language context."""
        context = super().get_context(event)
        context.extensions = Extensions({
            constants.XAPI_CONTEXT_VIDEO_CC_LANGUAGE: "en"  # TODO: Get from event when available
        })
        return context
