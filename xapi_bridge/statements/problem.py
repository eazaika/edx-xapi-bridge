"""xAPI Statements and Activities for verbs on courses as a whole."""


import json

from tincan import Activity, ActivityDefinition, LanguageMap, Result, Verb

import block
from xapi_bridge import constants, settings



class ProblemStatement(block.BaseCoursewareBlockStatement):
    """ Statement base for problem events."""

    # def _get_answer_as_string(answer):
    #     if hasattr(answer, '__iter__'):
    #         answer_string = ';'.join(answer)


    def get_object(self, event):
        """
        Get object for the statement.
        """
        return Activity(
            id='{}/courses/{}/jump_to/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id'], event['event']['problem_id']),
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

    def get_result(self, event):
        event_data = self.get_event_data(event)
        # for now we are going to assume one submission
        # TODO: when is that not true? is it ever not true? What problem types?
        submission = event_data['submission'][event_data['submission'].keys()[0]]
        return Result(
            score={
                'raw': event_data['grade'],
                'min': 0,
                'max': event_data['max_grade'],
                'scaled': float(event_data['grade'] / event_data['max_grade'])
            },
            success=event_data['success'] == 'correct',
            # TODO: to determine completion would need to know max allowed attempts?
            # probably should return True here but uswe a result extension for num attempts/attempts left 
            completion=True,
            response=json.dumps(submission['answer'])
        )


class ProblemResetStatement(ProblemStatement):
    """Statement for student resetting answer to a problem."""

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_INITIALIZED,
            display=LanguageMap({'en': 'reset'}),
        )

    def get_result(self, event):
        event_data = self.get_event_data(event)
        return Result(
            completion=False,
            response=json.dumps("[]")
        )
