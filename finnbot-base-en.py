#!/usr/bin/env python3#!/usr/bin/env python3

import openai

MODEL='gpt-4'
OPENAI_API_KEY = ""
client = openai.OpenAI(api_key=(OPENAI_API_KEY))


def llm(prompt: str, **kwargs):
    num_retries = 0
    while True:
        try:
            response = client.chat.completions.create(model=MODEL, messages=[{
                'role': 'user',
                'content': prompt,
            }], **kwargs)
            break
        except openai.error.ServiceUnavailableError:
            num_retries += 1
            if num_retries >= 3:
                raise
    if response.choices[0].finish_reason == 'content_filter':
        raise RuntimeError(f'OpenAI content filter kicked in for prompt: {prompt}')
    return response.choices[0].message.content


MAX_NUM_ROUNDS_SAVED = 15
NUM_UNTIL_GUESS = 5
num_rounds = 0
user_input = []
bot_output = []
place = ""
player_character = ""
bot_character = ""

def call_llm_for_chat():
    global player_character, place, bot_character, bot_output, user_input, num_rounds
    CHAT_PROMPT = '''
    The PERSON YOU are talking to has chosen a CHARACTER and a PLACE that YOU do not know.
    During the conversation, your task is to find out what CHARACTER the other person is playing and what LOCATION you are in.
    In addition, the PERSON has chosen a CHARACTER DESCRIPTION for you that YOU should follow in your answers.
    Your CHARACTER DESCRIPTION: {bot_character}
    YOU may not explicitly ask about the LOCATION or the CHARACTER, but still try to find out as much as possible about it. Limit your answer to a maximum of 3 sentences.
    YOU start the conversation. The conversation so far looks like this:

    '''
    chat_prompt = CHAT_PROMPT.format(bot_character=bot_character)
    j=0
    while(j < num_rounds):
        chat_prompt += "YOU: " + bot_output[j] + "\n" + "PERSON: " + user_input[j] + "\n"
        j = j + 1
    chat_prompt += "YOU: "
    output = llm(chat_prompt)
    bot_output.append(output)
    return output


def call_llm_after_decision():
    global player_character, place, bot_character, bot_output, user_input, num_rounds
    CHAT_AFTER_SELECTION_PROMPT = '''
    The PERSON YOU are talking to has chosen the following CHARACTER and LOCATION:
    CHARACTER: {player_character}
    LOCATION: {place}
    You also gave yourself the following CHARACTER DESCRIPTION:
    {beschreibung}
    Continue the conversation with the PERSON.
    Your conversation so far looked like this:

    '''
    chat_after_selection_prompt = CHAT_AFTER_SELECTION_PROMPT.format(player_character=player_character, place=place, beschreibung=bot_character)
    i=0
    while(i < len(bot_output)):
        chat_after_selection_prompt += "DU: " + bot_output[i] + "\n" + "PERSON: " + user_input[i] + "\n"
        i = i + 1
    chat_after_selection_prompt += "DU: "
    if(num_rounds >= MAX_NUM_ROUNDS_SAVED):
        bot_output.pop(0)
    output = llm(chat_after_selection_prompt)
    bot_output.append(output)
    return output

def init_bot():
    global player_character, place, bot_character, bot_output, user_input, num_rounds
    num_rounds = 0;
    user_input = []
    bot_output = []
    place = ""
    player_character = ""
    print("(*optional) Please enter a shplace character description for the bot.")
    bot_character = input()
    print("Initiliazed bot")
    return call_llm_for_chat()

def make_decisions():
    global player_character, place, bot_character, bot_output, user_input, num_rounds
    DECISION_PROMPT = '''
    The PERSON you are talking to has chosen a CHARACTER and a PLACE that you do not know.
    YOU should find out which CHARACTER your counterpart is playing and what LOCATION you are in.
    Your conversation so far looks like this:'''
    decision_prompt = DECISION_PROMPT
    i=0
    while(i < NUM_UNTIL_GUESS):
        decision_prompt += "YOU: " + bot_output[i] + "\n" + "PERSON: " + user_input[i] + "\n"
        i = i + 1
    decision_prompt_player_character = decision_prompt + "Limit your answer to one sentence. What CHARACTER does the PERSON play?\nCHARACTER: "
    player_character = llm(decision_prompt_player_character)
    decision_prompt_place = decision_prompt + "Limit your answer to one sentence. Where are you?\nLOCATION: "
    place = llm(decision_prompt_place)

    print("PLAYER player_character: " + player_character)
    print("LOCATION: " + place)

    SELECTION_PROMPT = '''
    The PERSON YOU are talking to has chosen the following CHARACTER and LOCATION:
    CHARACTER: {player_character}
    LOCATION: {place}
    Your conversation so far looked like this:

    '''
    selection_prompt = SELECTION_PROMPT.format(player_character=player_character, place=place, beschreibung=bot_character)
    i=0
    while(i < NUM_UNTIL_GUESS):
        selection_prompt += "YOU: " + bot_output[i] + "\n" + "PERSON: " + user_input[i] + "\n"
        i = i + 1
    selection_prompt += "Using the information given, write a CHARACTER DESCRIPTION for a character that YOU would like to play in order to converse with the CHARACTER. Limit yourself to one sentence.\nCHARACTER DESCRIPTION: "
    bot_character = llm(selection_prompt)
    print("BOT CHARACTER DESCRIPTION: " + bot_character)
    
def make_new_char():
    global player_character, place, bot_character, bot_output, user_input, num_rounds
    CHAR_SELECTION_PROMPT = '''
    The PERSON YOU are talking to has chosen the following CHARACTER and LOCATION:
    CHARACTER: {player_character}
    LOCATION: {place}
    You also gave yourself the following PREVIOUS DESCRIPTION up to now:
    PREVIOUS DESCRIPTION: {beschreibung}
    Your conversation so far looked like this:

    '''
    char_selection_prompt = player_character.format(player_character=player_character, place=place, beschreibung=bot_character)
    i=0
    while(i < len(bot_output)):
        char_selection_prompt += "YOU: " + bot_output[i] + "\n" + "PERSON: " + user_input[i] + "\n"
        i = i + 1
    char_selection_prompt += "Using the information provided, write a NEW CHARACTER DESCRIPTION for a character that YOU would like to play to converse with the PERSON. This should differ from the PREVIOUS DESCRIPTION. Limit yourself to one sentence.\nNEW CHARACTER DESCRIPTION: "
    bot_character = llm(char_selection_prompt)
    print("NEW CHARACTER DESCRIPTION: " + bot_character)


def display_input(_text):
    print(f'[INPUT ] {_text}')

def push_text(_text):
    print(f'[OUTPUT] {_text}')

def generate_text(_user_input,_first=False):
    global player_character, place, bot_character, bot_output, user_input, num_rounds
    if _first:
        _reply = init_bot()
    else:
        display_input (_user_input)
        if _user_input == "":
            # empty input = voice recognition timeout before user spoke
            # repeat last thing said
            _reply = bot_output[num_rounds]
        elif "abplace" in _user_input and "restart" in _user_input:
            _reply = init_bot()
        else:
            if(num_rounds >= MAX_NUM_ROUNDS_SAVED):
                user_input.pop(0)
            user_input.append(_user_input)
            num_rounds = num_rounds + 1
            if num_rounds < NUM_UNTIL_GUESS:
                _reply = call_llm_for_chat()
            elif num_rounds == NUM_UNTIL_GUESS:
                make_decisions()
                _reply = call_llm_after_decision()
            elif (num_rounds % NUM_UNTIL_GUESS) == 0:
                make_new_char()
                _reply = call_llm_after_decision()
            else:
                _reply = call_llm_after_decision()
    push_text(_reply)

print("Starting:")
generate_text("", True)
while(True):
    cur_input = input()
    generate_text(cur_input)
