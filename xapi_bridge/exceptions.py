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

    def log_exception(self):
        """Send exception information to Sentry if integrated.
        Typically called if we need to know about the exception but we don't want to fail the application.
        """
        if HAS_SENTRY_INTEGRATION:
            with configure_scope() as scope:
                statement_context = {'xAPI Statement' : self.statement.to_json()}
                scope = self.update_sentry_scope(scope, 'warning', **statement_context)
                capture_exception(self)
        logger.warn('xAPI Bridge caught exception type {}. {}'.format(self.__class__, self.MSG_SENT_TO_SENTRY))

    def log_message(self):
        """Send message to Sentry if integrated.
        Typically called if we need to understand something about behavior but we don't want to fail the application.
        """
        if HAS_SENTRY_INTEGRATION:
            msg = self.msg  # TODO: maybe some other wrapping information in message
            with configure_scope() as scope:
                statement_context = {'xAPI Statement' : self.statement.to_json()}
                scope = self.update_sentry_scope(scope, 'warning', **statement_context)
                capture_message(msg)
        logger.warn('xAPI Bridge caught exception type {}. {}'.format(self.__class__, self.MSG_SENT_TO_SENTRY))


class XAPIBridgeException(Exception, XAPIBridgeSentryMixin):
    """Base exception class for xAPI bridge application."""

    def __init__(self, msg=None, *args):
        if msg is None:
            self.msg = 'Some XAPIBridgeException occurred without a specific message'
        if HAS_SENTRY_INTEGRATION:
            self.set_sentry_scope(level, )
        super(XAPIBridgeException, self).__init__(msg, *args)

    def err_continue_exc(self):
        """Handle non-fatal errors, tracking an exception in Sentry.io."""

        if settings.EXCEPTIONS_NO_CONTINUE:  # debug setting
            self.err_fail()
        else:
            self.log_exception()

    def err_continue_msg(self):
        """Handle non-fatal errors, tracking just a message in Sentry.io."""

        if settings.EXCEPTIONS_NO_CONTINUE:  # debug setting
            self.err_fail()
        else:
            self.log_message()

    def err_fail(self):
        raise


class XAPIBridgeConnectionError(XAPIBridgeException):
    """Base exception class for errors connecting to external services in xAPI bridge application."""


class XAPIBridgeLRSConnectionError(XAPIBridgeConnectionError):
    """Exception class for problems connecting to an LRS."""


class XAPIBridgeStatementError(XAPIBridgeException):
    """Catch-all exception for bad Statements."""

    def __init__(self, err_reason="", statement=None, msg=None, *args):
        self.statement = statement
        self.msg = "Caught error:{}".format(err_reason)
        super(XAPIBridgeException, self).__init__(self.msg, *args)
