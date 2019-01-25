"""Exception types for xAPI operations."""

import logging

from xapi_bridge import settings

HAS_SENTRY_INTEGRATION = False


try:
    from sentry_sdk import capture_exception, capture_message, configure_scope
    HAS_SENTRY_INTEGRATION = True
except ImportError:
    logger.info("No Sentry.io integration defined for xapi Bridge")


logger = logging.getLogger(__name__)


class XAPIBridgeSentryMixin(object):
    """Defines exception class methods for exceptions to explicityly send messages or exceptions to Sentry.io."""

    MSG_SENT_TO_SENTRY = 'Sent to Sentry.io' if HAS_SENTRY_INTEGRATION else ''

    def update_sentry_scope(self, scope, level='warning', user=None, **kwargs):
        """Set up Scope context for Sentry logging."""
        scope.level = level
        scope.user = {"username": "Foo test"}
        if kwargs:
            for key, value in kwargs.iteritems():
                scope.set_extra(key, value)
        return scope

    def log_error(self, log_type):
        """Send exception information to Sentry if integrated.
        Typically called if we need to know about the exception but we don't want to fail the application.
        """
        if HAS_SENTRY_INTEGRATION:
            with configure_scope() as scope:
                extra_context = dict()
                if hasattr(self, 'statement'):
                    extra_context.update({'xAPI Statement': self.statement.to_json()})
                if hasattr(self, 'event'):
                    extra_context.update({'Tracking Log Event': self.event.to_json()})
                scope = self.update_sentry_scope(scope, 'warning', **extra_context)
                if log_type == 'exception':
                    capture_exception(self)
                else:
                    capture_message(self.msg)
        logger.warn('xAPI Bridge caught exception type {}:{}. {}'.format(str(self.__class__), self.msg, self.MSG_SENT_TO_SENTRY))


class XAPIBridgeException(Exception, XAPIBridgeSentryMixin):
    """Base exception class for xAPI bridge application."""

    def __init__(self, msg=None, *args):
        if msg is None:
            self.msg = 'An XAPIBridgeException occurred without a specific message'
        super(XAPIBridgeException, self).__init__(msg, *args)

    def err_continue_exc(self):
        """Handle non-fatal errors, tracking an exception in Sentry.io."""

        if settings.EXCEPTIONS_NO_CONTINUE:  # debug setting
            self.err_fail()
        else:
            self.log_error('exception')

    def err_continue_msg(self):
        """Handle non-fatal errors, tracking just a message in Sentry.io."""

        if settings.EXCEPTIONS_NO_CONTINUE:  # debug setting
            self.err_fail()
        else:
            self.log_error('message')

    def err_fail(self):
        raise


class XAPIBridgeConnectionError(XAPIBridgeException):
    """Base exception class for errors connecting to external services in xAPI bridge application."""


class XAPIBridgeLRSConnectionError(XAPIBridgeConnectionError):
    """Exception class for problems connecting to an LRS."""


class XAPIBridgeStatementConversionError(XAPIBridgeException):
    """Catch-all exception for bad Statements."""

    def __init__(self, event=None, msg=None, *args):
        self.event = event
        self.msg = msg
        super(XAPIBridgeException, self).__init__(self.msg, *args)
