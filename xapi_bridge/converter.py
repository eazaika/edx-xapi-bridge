"""
Конвертер событий трекинга Open edX в xAPI-высказывания.

"""

import logging
from typing import Dict, Optional, Tuple

from xapi_bridge import exceptions, settings
from xapi_bridge.statements import (
    base, course, problem,
    video, vertical_block, attachment
)


logger = logging.getLogger(__name__)


# Соответствие типов событий классам xAPI-высказываний
TRACKING_EVENTS_TO_XAPI_STATEMENT_MAP = {
    # События курса
    'edx.course.enrollment.activated': course.CourseEnrollmentStatement,
    'edx.course.enrollment.deactivated': course.CourseUnenrollmentStatement,
    'edx.course.completed': course.CourseCompletionStatement,
    'edx.course.expell': course.CourseExpellStatement,

    # course completion
    #'edx.certificate.created': course.CourseCompletionStatement,

    # 'edx.drag_and_drop_v2.item.dropped'

    # Завершение составных блоков
    'complete_vertical': vertical_block.VerticalBlockCompleteStatement,

    # Работа с заданиями
    'problem_check': problem.ProblemCheckStatement,
    'edx.attachment': attachment.AttachmentStatement,

    # Видео события
    'pause_video': video.VideoStatement,
    'video_check': video.VideoCheckStatement,
    'stop_video': video.VideoCompleteStatement,
}


def to_xapi(evt: Dict) -> Optional[Tuple[base.LMSTrackingLogStatement]]:
    """
    Конвертирует событие трекинга в одно или несколько xAPI-высказываний.

    Args:
        evt: Сырое событие из логов трекинга

    Returns:
        Кортеж xAPI-высказываний или None если событие игнорируется

    Raises:
        XAPIBridgeSkippedConversion: Для пропускаемых событий
    """
    try:
        event_type = _normalize_event_type(evt['event_type'])
        _check_ignored_events(evt['event_source'], event_type)

        # Специальная обработка video_check
        if event_type == 'problem_check':
            event_type = _handle_video_check(evt, event_type)

        statement_class = TRACKING_EVENTS_TO_XAPI_STATEMENT_MAP[event_type]
        return _create_statement(statement_class, evt)

    except exceptions.XAPIBridgeSkippedConversion as e:
        logger.debug(f"Событие пропущено: {e.message}. Данные: {evt}")
    except KeyError as e:
        logger.debug(f"Необрабатываемый тип события: {event_type}. Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Критическая ошибка конвертации: {str(e)}. Событие: {evt}")

    return None


def _normalize_event_type(event_type: str) -> str:
    """Нормализация типа события."""
    return event_type.replace("xblock-video.", "").strip()

def _check_ignored_events(event_source: str, event_type: str) -> None:
    """Проверка игнорируемых событий."""
    if event_source == 'browser':
        raise exceptions.XAPIBridgeSkippedConversion(
            event_source,
            f"Событие из источника {event_source} игнорируется"
        )
    if event_type in settings.IGNORED_EVENT_TYPES:
        raise exceptions.XAPIBridgeSkippedConversion(
            event_type,
            f"Событие {event_type} в списке игнорируемых"
        )


def _handle_video_check(evt: Dict, event_type: str) -> str:
    """Обработка специального случая проверки видео."""
    if evt['event_source'] == 'server':
        answers = evt['event']['answers']
        first_key = next(iter(answers))
        if 'watch_times' in answers[first_key]:
            return 'video_check'
    return event_type


def _create_statement(statement_class, evt: Dict) -> Tuple[base.LMSTrackingLogStatement]:
    """Создание экземпляра высказывания с валидацией."""
    try:
        statement = statement_class(evt)
        if not hasattr(statement, 'version'):
            raise exceptions.XAPIBridgeStatementConversionError(
                event_type=evt['event_type'],
                event_data=evt,
                reason="Отсутствует обязательное поле version"
            )
        return (statement,)
    except exceptions.XAPIBridgeSkippedConversion as e:
        raise e
    except Exception as e:
        raise exceptions.XAPIBridgeStatementError(
            raw_event=evt,
            validation_errors=e
        ) from e
