"""xAPI Statements and Activities for verbs on courses as a whole."""


from tincan import Activity, ActivityDefinition, LanguageMap, Verb

import block
from xapi_bridge import constants, settings



class ProblemStatement(block.BaseCoursewareBlockStatement):
    """ Statement base for problem events."""

    def get_object(self, event):
        """
        Get object for the statement.
        """
        return Activity(
            id='{}/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['path']),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_QUESTION,
                name=LanguageMap({'en': 'Problem'}),
                description=LanguageMap({'en': 'A problem in an Open edX course'}),
            ),
        )


class ProblemCheckStatement(ProblemStatement):
    """Statement for student checking answer to a problem."""

    def __init__(self, event, *args, **kwargs):
        # 'problem_check' events are emitted from both browser and server
        # and we only want the server event
        if event['event_source'].lower() != 'server':
            return None  # will be excluded from StatementList
        super(ProblemCheckStatement, self).__init__(event, *args, **kwargs)

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_ATTEMPTED,
            display=LanguageMap({'en': 'attempted'}),
        )
