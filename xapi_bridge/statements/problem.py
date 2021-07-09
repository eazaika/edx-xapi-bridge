# -*- coding: utf-8 -*-
"""xAPI Statements and Activities for verbs on courses as a whole."""


import json
import re

from tincan import Activity, ActivityDefinition, ActivityList, LanguageMap, Result, Verb, ContextActivities

import block
import course
from xapi_bridge import constants, exceptions, settings



class ProblemStatement(block.BaseCoursewareBlockStatement):
    """ Statement base for problem events."""

    def get_object(self, event):
        """
        Get object for the statement.
        """
        try:
            display_name = event['context']['module']['display_name']
        except KeyError:
            display_name = "Problem"

        try:
            event_data = self.get_event_data(event)
            submission = event_data['submission'][event_data['submission'].keys()[0]]
            question = submission['question'].replace('\"', '').replace('\\', '')
            question = re.sub(r'\(\$(\w+)\)', r'<\1>', question)
        except KeyError:
            question = event['context']['question']

        return Activity(
            id=self._get_activity_id(event),
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_INTERACTION, # could be _QUESTION if not CAPA
                name=LanguageMap({'ru-RU': question}),
                description=LanguageMap({'ru-RU': display_name}),
                # TODO: interactionType, correctResponsesPattern, choices, if possible
            ),
        )

class ProblemGradedStatement(ProblemStatement):
    """Statement for student gave answer to a problem."""


class ProblemCheckStatement(ProblemStatement):
    """Statement for student checking answer to a problem."""

    def __init__(self, event, *args, **kwargs):
        # 'problem_check' events are emitted from both browser and server
        # and we only want the server event
        if event['event_source'].lower() != 'server':
            raise exceptions.XAPIBridgeSkippedConversion("Don't convert problem checks from server")
        super(ProblemCheckStatement, self).__init__(event, *args, **kwargs)

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_ANSWERED,
            display=LanguageMap({'en-US': 'answered', 'ru-RU': 'дан ответ'}),
        )

    def get_result(self, event):
        event_data = self.get_event_data(event)
        # for now we are going to assume one submission
        # TODO: when is that not true? is it ever not true? What problem types?
        try:
            data = event_data['submission']
            answer = []
            for key in data:
                log.error('key {} - {}'.format(key, data[key]))
                trash = data[key]['answer']
                log.error(trash)
                if type(trash) is not unicode:
                    for i in trash:
                        p = re.sub(r"(\n.*)", r'', i)
                        answer.append(p)
                else:
                    answer.append(trash)
            if len(answer) > 1:
                answer = ', '.join("<%s>" % item for item in answer)
            else:
                answer = ''.join(answer[0])
            answer = answer.replace('\"', '').strip() #.replace('\\\\', '')
        except:
            answer = event['context']['answer'].strip() #.replace('\\\\', '')

        try:
            success = event_data['success'] == 'correct'
        except:
            success = event['event']['grade'] == event['event']['max_grade']

        return Result(
            score={
                'raw': event_data['grade'],
                'min': 0,
                'max': event_data['max_grade'],
                'scaled': float(event_data['grade']) / float(event_data['max_grade'])
            },
            success=success,
            # TODO: to determine completion would need to know max allowed attempts?
            # probably should return True here but uswe a result extension for num attempts/attempts left 
            response=answer.encode('utf-8')
        )

    def get_context_activities(self, event):
        parent_activities = [
            Activity(
                id='{}/courses/{}'.format(settings.OPENEDX_PLATFORM_URI, event['context']['course_id']),
                definition=course.CourseActivityDefinition(event)
            ),
        ]
        parent = settings.OPENEDX_PLATFORM_URI + ':18010/container/' + event['context']['parent']['usage_key']
        #parent = event['context']['parent']['usage_key'] #FOR TEST
        parent_activities.append(
            Activity(
                id=parent,
                definition=block.BlockAssessmentDefinition(event['context']['parent'])
            ),
        )

        return ContextActivities(
            parent=ActivityList(parent_activities)
        )


class ProblemSubmittedStatement(ProblemStatement):
    """Statement for student submitting an answer.

    Recorded in some problem types instead of problem_check; e.g., drag and drop v2.
    """

    def get_verb(self, event):
        return Verb(
            id=constants.XAPI_VERB_ATTEMPTED,
            display=LanguageMap({'en': 'attempted'}),
        )

    def get_result(self, event):
        event_data = self.get_event_data(event)
        earned = event_data['weighted_earned']
        possible = event_data['weighted_possible']
        return Result(
            score={
                'raw': earned,
                'min': 0,
                'max': possible,
                'scaled': float(earned / possible) if possible > 0 else 0
            },
            success=True if earned >= possible else False,
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
