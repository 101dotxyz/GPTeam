import os
from discord_utils import install_global_commands, capitalize
from game import get_rps_choices


def create_command_choices():
    choices = get_rps_choices()
    command_choices = []

    for choice in choices:
        command_choices.append({
            'name': capitalize(choice),
            'value': choice.lower(),
        })

    return command_choices


# Simple test command
TEST_COMMAND = {
    'name': 'test',
    'description': 'Basic command',
    'type': 1,
}

# Command containing options
CHALLENGE_COMMAND = {
    'name': 'challenge',
    'description': 'Challenge to a match of rock paper scissors',
    'options': [
        {
            'type': 3,
            'name': 'object',
            'description': 'Pick your object',
            'required': True,
            'choices': create_command_choices(),
        },
    ],
    'type': 1,
}

ALL_COMMANDS = [TEST_COMMAND, CHALLENGE_COMMAND]

install_global_commands(os.environ['APP_ID'], ALL_COMMANDS)
