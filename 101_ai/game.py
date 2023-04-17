import random


def get_result(p1, p2):
    game_result = {}
    if p1.objectName in RPSChoices and p2.objectName in RPSChoices[p1.objectName]:
        # p1 wins
        game_result = {
            'win': p1,
            'lose': p2,
            'verb': RPSChoices[p1.objectName][p2.objectName],
        }
    elif p2.objectName in RPSChoices and p1.objectName in RPSChoices[p2.objectName]:
        # p2 wins
        game_result = {
            'win': p2,
            'lose': p1,
            'verb': RPSChoices[p2.objectName][p1.objectName],
        }
    else:
        # tie -- win/lose don't
        game_result = {'win': p1, 'lose': p2, 'verb': 'tie'}

    return format_result(game_result)


def format_result(result):
    win, lose, verb = result['win'], result['lose'], result['verb']
    return f'<@{win.id}>\'s **{win.objectName}** {verb} <@{lose.id}>\'s **{lose.objectName}**' if verb != 'tie' else f'<@{win.id}> and <@{lose.id}> draw with **{win.objectName}**'


# this is just to figure out winner + verb
RPSChoices = {
    'rock': {
        'description': 'sedimentary, igneous, or perhaps even metamorphic',
        'virus': 'outwaits',
        'computer': 'smashes',
        'scissors': 'crushes',
    },
    'cowboy': {
        'description': 'yeehaw~',
        'scissors': 'puts away',
        'wumpus': 'lassos',
        'rock': 'steel-toe kicks',
    },
    'scissors': {
        'description': 'careful ! sharp ! edges !!',
        'paper': 'cuts',
        'computer': 'cuts cord of',
        'virus': 'cuts DNA of',
    },
    'virus': {
        'description': 'genetic mutation, malware, or something inbetween',
        'cowboy': 'infects',
        'computer': 'corrupts',
        'wumpus': 'infects',
    },
    'computer': {
        'description': 'beep boop beep bzzrrhggggg',
        'cowboy': 'overwhelms',
        'paper': 'uninstalls firmware for',
        'wumpus': 'deletes assets for',
    },
    'wumpus': {
        'description': 'the purple Discord fella',
        'paper': 'draws picture on',
        'rock': 'paints cute face on',
        'scissors': 'admires own reflection in',
    },
    'paper': {
        'description': 'versatile and iconic',
        'virus': 'ignores',
        'cowboy': 'gives papercut to',
        'rock': 'covers',
    },
}


def get_rps_choices():
    return list(RPSChoices.keys())


# Function to fetch shuffled options for select menu
def get_shuffled_options():
    all_choices = get_rps_choices()
    options = []
    for choice in all_choices:
        # Formatted for select menus
        # https://discord.com/developers/docs/interactions/message-components#select-menu-object-select-option-structure
        options.append({
            'label': choice.capitalize(),

            'value': choice.lower(),
            'description': RPSChoices[choice]['description'],
        })

    return sorted(options, key=lambda x: random.random())
