import logging
import json

from django.conf import settings
from requests.exceptions import ConnectionError
from track.backends import BaseBackend

from xapi_bridge import client
from xapi_bridge import converter
from xapi_bridge import exceptions

LOGGER = logging.getLogger(__name__)
TRACKING_LOGGER = logging.getLogger('tracking')


def log_success(event_id, status_code):
    """
    This function logs the successful delivery of the caliper event
    to the external API

    @params:
    event_id: (str) UUID of the caliper event
    status_code: (int) HTTP status code of the repsonse from the API
    """
    LOGGER.info('Success {}: Caliper event delivery successful for event id: {} to endpoint: {}'.format(
        status_code,
        event_id,
        settings.XAPI_DELIVERY_ENDPOINT
    ))


def log_failure(event_id, status_code):
    """
    This function logs the failed delivery of the caliper event
    to the external API

    @params:
    event_id: (str) UUID of the caliper event
    status_code: (int) HTTP status code of the repsonse from the API
    """
    LOGGER.error('Failure {}: xApi event delivery failed for event id: {} to endpoint: {}'.format(
        status_code,
        event_id,
        settings.XAPI_DELIVERY_ENDPOINT
    ))



class XApiProcessor(BaseBackend):
    """
    Is responsible for capturing, transforming and sending all the event tracking logs
    generated by Open edX platform.

    This transformer is used in the commong.djangoapps.track django app as a replacement
    for the default tracking backend.

    It is also used as an addition to the event tracking pipeline in the event_tracking app
    by Open edX
    """

    def __call__(self, event):
        """
        handles the transformation and delivery of an event. Delivers the event to the caliper log file as well as
        delivers it to an external API if configured to do so.

        @params:
        event: raw event from edX event tracking pipeline
        """
        try:
            xapi = None
            try:
                xapi = converter.to_xapi(event)
            except (exceptions.XAPIBridgeStatementConversionError, ) as e:
                e.err_continue_msg()

            if xapi is not None:
                for statement in xapi:
                    client.lrs_publisher.publish_statement(statement)

            return event
        except KeyError:
            TRACKING_LOGGER.exception("Missing transformer method implementation for {}".format(
                event.get('event_type')))
        except Exception as ex:
            TRACKING_LOGGER.exception(ex.args)

    def send(self, event):
        """
        Implements the abstract send method in track.backends.BaseBackend

        @params:
        event: (dict) raw event from edX event tracking pipeline:
        """
        if not event['event_type'].startswith('/'):
            TRACKING_LOGGER.info(self.__call__(event))
        else:
            TRACKING_LOGGER.info(json.dumps(event))
