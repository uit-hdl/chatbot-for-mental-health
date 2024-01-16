import openai
import re
import sys
import os
import cv2
import time
import logging

import matplotlib.pyplot as plt
import numpy as np
import pprint

from typing import List
from typing import Dict

from utils.general import wrap_and_print_message
from utils.general import count_tokens
from utils.general import play_video
from utils.general import conversation_list_to_string
from utils.general import extract_commands_and_filepaths
from utils.general import scan_for_json_data
from utils.general import remove_nones
from utils.general import count_tokens_used_to_create_last_response
from utils.general import grab_last_response
from utils.general import print_whole_conversation
from utils.general import rewind_chat_by_n_assistant_responses
from utils.general import offer_to_store_conversation
from utils.general import display_image
from utils.general import identify_assistant_reponses
from utils.user_commands import scan_user_message_for_commands
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import USER_DATA_DIR
from utils.backend import SETTINGS
from utils.backend import CONFIG
from utils.backend import dump_to_json
from utils.backend import dump_current_conversation
from utils.backend import load_textfile_as_string
from utils.backend import load_yaml_file
from utils.backend import get_filename
from utils.backend import file_exists

openai.api_key = API_KEY
openai.api_type = CONFIG["api_type"]
openai.api_base = CONFIG["api_base"]
openai.api_version = CONFIG["api_version"]

# Initiate global variables
BREAK_CONVERSATION = False
# If chat is reset back in time, this variable controlls how many responses should be stripped from chat
N_TOKENS_USED = []
RESPONSE_TIMES = []  # Tracks the time that the bot takes to generate a response
SYSTEM_WARNING = (
    []
)  # Collects warnings and reminders when erroneous bot behaviour is detected
REGENERATE_RESPONSE = (
    False  # Triggered when the output of the bot violates certain rules
)

# Chat colors
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"  # used to reset colour

pp = pprint.PrettyPrinter(indent=2, width=100)
logging.basicConfig(
    filename="log/chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def sleep_diary_assistant_bot(chatbot_id, chat_filepath=None):
    """Running this function starts a conversation with a tutorial bot that
    helps explain how a web-app (https://app.consensussleepdiary.com) functions.
    The web app is a free online app for collecting sleep data."""

    prompt = PROMPTS[chatbot_id]

    if chat_filepath:
        conversation = continue_previous_conversation(chat_filepath, prompt)
    else:
        conversation = initiate_new_conversation(prompt)
        display_last_response(conversation)

    while True:
        conversation = create_user_input(conversation)

        if conversation_status() == "ended":
            offer_to_store_conversation(conversation)
            break

        conversation = generate_bot_response(conversation, chatbot_id)


def initiate_new_conversation(inital_prompt, system_message=None):
    """Initiates a conversation with the chat bot."""
    conversation = []
    conversation.append({"role": "system", "content": inital_prompt})
    if system_message:
        conversation.append({"role": "system", "content": system_message})
    conversation = generate_raw_bot_response(conversation)
    return conversation


def continue_previous_conversation(chat_filepath, prompt):
    """Inserts the current prompt into a previous stored conversation that was
    discontinued."""
    conversation = load_yaml_file(chat_filepath)
    # Replace original prompt with requested prompt
    conversation[0] = {"role": "system", "content": prompt}
    print_whole_conversation(conversation)
    return conversation


def generate_bot_response(conversation, chatbot_id):
    """Takes a conversation where the last message is from the user and
    generates a response from the bot. The response is generated iteratively
    since the bot may first have to request sources and then react to those
    sources."""
    global BREAK_CONVERSATION

    generate_response = True
    while generate_response:
        conversation = generate_raw_bot_response(conversation)
        commands, knowledge_requests = process_syntax_of_bot_response(
            conversation, chatbot_id
        )

        while knowledge_requests:
            conversation = insert_knowledge(conversation, knowledge_requests)
            conversation = generate_raw_bot_response(conversation)
            commands, knowledge_requests = process_syntax_of_bot_response(
                conversation, chatbot_id
            )

        json_dictionaries = scan_last_response_for_json_data(conversation)

        if more_than_1_media_are_requested_check(commands):
            conversation = delete_last_bot_response(conversation)
            conversation.append(
                {
                    "role": "system",
                    "content": "It is illegal to present more than 1 video/image per response!",
                }
            )
            if SETTINGS["print_system_messages"]:
                display_last_response(conversation)
            # Illegal response: go back to the beginning of the while-loop
            continue

        display_last_response(conversation)
        dump_current_conversation(conversation)

        if commands:
            conversation = display_if_media(commands, conversation)
            check_for_request_to_end_chat(commands)

        generate_response = False  # Response has passed criteria: end while-loop

        if BREAK_CONVERSATION:
            offer_to_store_conversation(conversation)
            break

        if json_dictionaries:
            referral_ticket, sources = process_json_data(json_dictionaries)
            if referral_ticket:
                conversation = direct_to_new_assistant(referral_ticket)
                display_last_response(conversation)
                continue

        if count_tokens(conversation) > SETTINGS["max_tokens_before_summary"]:
            conversation = summarize_conversation(conversation)
            conversation = generate_raw_bot_response(conversation)

        conversation = remove_inactive_sources(conversation)

    return conversation


def delete_last_bot_response(conversation):
    """Identifies which responses are from the assistant, and deletes the last
    response from the conversation. Used when the bot response has broken some
    rule, and we want it to create a new response."""
    assistant_indices = identify_assistant_reponses(conversation)
    assistant_indices[-1]
    del conversation[assistant_indices[-1]]
    return conversation


def generate_raw_bot_response(conversation):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history."""
    start_time = time.time()
    response = openai.ChatCompletion.create(
        model=CONFIG["model_id"],
        messages=conversation,
        engine=CONFIG["deployment_name"],
    )
    end_time = time.time()
    conversation.append(
        {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content.strip(),
        }
    )
    RESPONSE_TIMES.append(end_time - start_time)
    N_TOKENS_USED.append(count_tokens_used_to_create_last_response(conversation))
    return conversation


def create_user_input(conversation):
    """Prompts user to input a prompt (the "question") in the command line."""
    global BREAK_CONVERSATION

    while True:
        user_message = input(GREEN + "user" + RESET + ": ")
        user_message, n_rewind, BREAK_CONVERSATION = scan_user_message_for_commands(
            user_message,
            conversation,
            BREAK_CONVERSATION,
            N_TOKENS_USED,
            RESPONSE_TIMES,
        )
        if n_rewind:
            conversation = rewind_chat_by_n_assistant_responses(n_rewind, conversation)
            print(f"** Rewinding by {n_rewind} bot responses **")
            reprint_whole_conversation(conversation)
        else:
            break
    conversation.append({"role": "user", "content": user_message})
    return conversation


def process_syntax_of_bot_response(conversation, chatbot_id):
    """Scans the response for symbols ¤: and :¤, and extracts the name of the commands, the
    file-arguments of the commands. Returns two lists of dictionaries."""
    chatbot_response = grab_last_response(conversation)
    commands = extract_commands_and_filepaths(chatbot_response, chatbot_id)
    knowledge_requests = check_for_knowledge_requests(commands)
    return commands, knowledge_requests


def check_for_knowledge_requests(commands: List[Dict]) -> List[Dict]:
    """Fetches the text associated with each knowledge request command."""
    knowledge_list = []
    if commands:
        for command in commands:
            if command["type"] == "request_knowledge":
                knowledge = {}
                knowledge["file"] = command["file"]
                if file_exists(knowledge["file"]):
                    knowledge["content"] = load_textfile_as_string(command["file"])
                else:
                    knowledge["content"] = None
                knowledge_list.append(knowledge)
    return knowledge_list


def insert_knowledge(conversation, knowledge_list):
    """Inserts knowledge into the conversation, and lets bot produce a new
    response using that information."""
    for knowledge in knowledge_list:
        source_name = get_filename(knowledge["file"])
        if file_exists(knowledge["file"]):
            print(f"\nInserting information `{source_name}` into conversation...")
            message = f"source {source_name}: {knowledge['content']}"
        else:
            message = "Requested source does not exist! Request only sources I have told you to use."
        conversation.append({"role": "system", "content": message})
    return conversation


def display_if_media(commands: list, conversation: list):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:display_image{<file>}:¤ (replace with
    `display_video` for video)."""
    for command in commands:
        if file_exists(command["file"]):
            if command["type"] == "display_image":
                display_image(command["file"])
            elif command["type"] == "play_video":
                play_video(command["file"])
        else:
            {
                "role": "system",
                "content": "File does not exist. Display only files that I have referenced.",
            }
            conversation.append(
                "File does not exist. Display only files that I have referenced."
            )
    return conversation


def more_than_1_media_are_requested_check(commands):
    """Checks if the bot attempts to display more than one piece of media (video
    or image) at a time (which is not desired)."""
    if commands is None:
        return False

    types = np.array([command["type"] for command in commands])
    index_image_request = types == "display_image"
    index_video_request = types == "display_video"

    if np.sum(index_image_request) + np.sum(index_video_request) >= 2:
        return True
    else:
        return False


def check_for_request_to_end_chat(commands: dict):
    global BREAK_CONVERSATION
    for command in commands:
        if command["type"] == "end_chat":
            BREAK_CONVERSATION = True


def process_json_data(json_dictionaries):
    """Takes a list of json dictionaries, infers the type of data they contain,
    and handles them accordingly. Datatypes can be referrals, sources, or data
    describing the user."""
    referral_ticket = None
    sources = None
    for dictionary in json_dictionaries:
        if "assistant_id" in dictionary:
            referral_ticket = dictionary
        elif "sources" in dictionary:
            sources = dictionary
        else:
            dump_to_json(dictionary, f"{USER_DATA_DIR}/user_data.json")

    return referral_ticket, sources


def direct_to_new_assistant(json_ticket):
    """Takes information about the users issue condensed into a json string, and
    redirects to the appropriate chatbot assistant."""
    prompt = get_prompt_for_assistant(json_ticket["assistant_id"])
    # prompt_modified = insert_information_in_prompt(prompt, info=json_ticket["topic"])
    system_message = f"Here is a summary of the users issue: {json_ticket['topic']}"
    new_conversation = initiate_new_conversation(prompt, system_message)
    print(f"user is redirected to assistant {json_ticket['assistant_id']}")
    return new_conversation


def scan_last_response_for_json_data(conversation):
    """Grabs last resonse and scans for json data nested in the response."""
    return scan_for_json_data(grab_last_response(conversation))


def remove_inactive_sources(conversation):
    """Scans the conversation for sources that have not been used recently
    (inactive sources)."""
    system_messages = [
        message["content"]
        for message in conversation[1:]
        if message["role"] == "system"
    ]
    sources = [
        extract_source_name(message)
        for message in system_messages
        if message.startswith("source")
    ]
    sources = remove_nones(sources)
    if sources:
        inactivity_times = [
            count_time_since_last_citation(conversation, source) for source in sources
        ]
        inactivity_times = remove_nones(inactivity_times)
        print_source_info(sources, inactivity_times)

        sources_to_remove = np.array(sources)[
            np.array(inactivity_times) >= SETTINGS["inactivity_threshold"]
        ]

        for index, message in enumerate(conversation):
            if index == 0:
                # Skip prompt
                continue
            if message["role"] == "system":
                source_name = extract_source_name(message["content"])
                if source_name in sources_to_remove:
                    conversation[index]["content"] = "inactive source removed"
                    if SETTINGS["print_removal_of_inactive_source"]:
                        print(f"Removing inactive source {source_name}\n")

    return conversation


def extract_source_name(message: str):
    """Takes a message/response and scans for the name of the source being used,
    if any."""
    pattern = r"source (\w+):"
    match = re.search(pattern, message)
    if match:
        return match.group(1)


def count_time_since_last_citation(conversation, source_name):
    """Counts the number of responses since the source was last cited. If cited
    in the last response, this value is 0."""
    assistant_messages = [
        message["content"] for message in conversation if message["role"] == "assistant"
    ]
    inactivity_time = 0
    # Look backwards in conversation to find how long ago since the source was last cited
    for i in range(1, len(assistant_messages) + 1):
        if source_name in assistant_messages[-i]:
            inactivity_time = i - 1
            break
    return inactivity_time


def summarize_conversation(conversation):
    """Uses chatbot to summarize the conversation. This did not work too
    well..."""
    global SUMMARY
    conversation_messages, system_messages = separate_system_from_conversation(
        conversation
    )
    conversation_messages = remove_code_syntax_from_whole_conversation(
        conversation_messages
    )
    conversation_string = conversation_list_to_string(conversation_messages)
    prompt_summary_bot = insert_information_in_prompt(
        prompt=PROMPTS["summary_bot"], info=conversation_string
    )
    conversation_with_summary_bot = initiate_new_conversation(prompt_summary_bot)
    SUMMARY = grab_last_response(conversation_with_summary_bot)
    conversation_summarized = reconstruct_conversation_with_summary(
        system_messages, SUMMARY
    )
    return conversation_summarized


def reconstruct_conversation_with_summary(system_messages, summary):
    conversation_reconstructed = system_messages
    conversation_reconstructed.append({"role": "system", "content": summary})
    return conversation_reconstructed


def reprint_whole_conversation(conversation, include_system_messages=True):
    """Reprints whole conversation (not including the prompt)."""
    for message in conversation[1:]:
        if not include_system_messages and message["role"] == "system":
            continue
        else:
            display_message_without_syntax(message)


def display_last_response(conversation):
    """Displays the last response of the conversation (removes syntax)."""
    display_message_without_syntax(message_dict=conversation[-1])


def display_message_without_syntax(message_dict: dict):
    """Takes a message in dictionary form, removes the code syntax, and prints
    it in the console."""
    role = message_dict["role"].strip()
    message = message_dict["content"].strip()
    message_cleaned = remove_code_syntax_from_message(message)
    wrap_and_print_message(role, message_cleaned)


def remove_code_syntax_from_message(message):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_json = re.sub(r"\¤¤(.*?)\¤¤", "", message, flags=re.DOTALL)
    message_no_code = re.sub(r"\¤:(.*?)\:¤", "", message_no_json)
    # Remove surplus spaces
    message_cleaned = re.sub(r" {2,}(?![\n])", " ", message_no_code)
    return message_cleaned


def remove_code_syntax_from_whole_conversation(conversation):
    """Removes code syntax from every message in the conversation."""
    for i, message in enumerate(conversation):
        if message["role"] == "Assistant":
            conversation[i]["content"] = remove_code_syntax_from_message(message)
    return conversation


def separate_system_from_conversation(conversation):
    """Finds the system messages, and returns the conversation without system
    messages and a list of the system messages."""
    conversation_messages = [
        message for message in conversation if message["role"] != "system"
    ]
    system_messages = [
        message for message in conversation if message["role"] == "system"
    ]
    return conversation_messages, system_messages


def get_prompt_for_assistant(assistant_id):
    return PROMPTS[assistant_id]


def insert_information_in_prompt(prompt: str, info: str):
    """Inserts information contained in a dictionary format into the prompt."""
    return prompt.replace("<insert_info>", info)


def conversation_status():
    """Checks if conversation has ended by scanning for a predefined substring
    that acts as a cue to end the conversation."""
    if BREAK_CONVERSATION:
        return "ended"
    else:
        return "active"


def display_collected_data(collected_info=None):
    if collected_info:
        print(f"\nThe collected data is\n")
        print(f"{collected_info}")


def print_source_info(sources, inactivity_times):
    """Prints information about the sources (requested) that are being used."""
    if SETTINGS["print_info_on_sources"]:
        print(f"\nDuration of inactivity for sources: {inactivity_times}\n")
        print(f"\nsources: {sources}\n")


if __name__ == "__main__":
    arg1 = "referral"
    arg2 = None

    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 == "":
            arg1 = "referral"
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]

    if arg1 == "options":
        print(f"The assistant IDs are: \n{pp.pformat(list(PROMPTS.keys()))}")
    else:
        sleep_diary_assistant_bot(chatbot_id=arg1, chat_filepath=arg2)
