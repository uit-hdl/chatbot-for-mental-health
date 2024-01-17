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

from utils.general import wrap_and_print_message
from utils.general import count_tokens
from utils.general import play_video
from utils.general import conversation_list_to_string
from utils.general import remove_nones
from utils.general import count_tokens_used_to_create_last_response
from utils.general import grab_last_response
from utils.general import print_whole_conversation
from utils.general import offer_to_store_conversation
from utils.general import display_image
from utils.general import identify_assistant_responses
from utils.general import calculate_cost_of_response
from utils.general import remove_code_syntax_from_message
from utils.general import contains_only_whitespace
from utils.process_syntax import process_syntax_of_bot_response
from utils.user_commands import scan_user_message_for_commands
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import USER_DATA_DIR
from utils.backend import SETTINGS
from utils.backend import CONFIG
from utils.backend import dump_to_json
from utils.backend import dump_current_conversation
from utils.backend import load_yaml_file
from utils.backend import file_exists

openai.api_key = API_KEY
openai.api_type = CONFIG["api_type"]
openai.api_base = CONFIG["api_base"]
openai.api_version = CONFIG["api_version"]

# Initiate global variables
BREAK_CONVERSATION = False
# If chat is reset back in time, this variable controlls how many responses should be stripped from chat
N_TOKENS_USED = []  # Tracks the number of tokens used to generate each response
RESPONSE_TIMES = []  # Tracks the time that the bot takes to generate a response
RESPONSE_COSTS = []  # Tracks the cost (in kr) per response

# Chat colors
GREY = "\033[2;30m"  # info messages
GREEN = "\033[92m"  # user
BLUE = "\033[94m"  # assistant
RESET_COLOR = "\033[0m"  # used to reset colour

pp = pprint.PrettyPrinter(indent=2, width=100)
logging.basicConfig(
    filename="chat-info/chat.log",
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
        if BREAK_CONVERSATION:
            break
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
    discontinued, so that you can pick up where you left of."""
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
        harvested_syntax = process_syntax_of_bot_response(conversation, chatbot_id)

        while harvested_syntax["knowledge_requests"]:
            # In this loop the bot can request sources until relevant information has been found
            conversation = insert_knowledge(
                conversation, harvested_syntax["knowledge_requests"]
            )
            conversation = generate_raw_bot_response(conversation)
            harvested_syntax = process_syntax_of_bot_response(conversation, chatbot_id)

        if more_than_1_media_are_requested_check(harvested_syntax):
            conversation = delete_last_bot_response(conversation)
            conversation.append(
                {
                    "role": "system",
                    "content": "It is illegal to present more than 1 video/image per response!",
                }
            )
            if SETTINGS["print_system_messages"]:
                display_last_response(conversation)
                print_summary_info()
            # Illegal response: go back to the beginning of the while-loop
            continue

        display_last_response(conversation)
        dump_current_conversation(conversation)

        if harvested_syntax["images"] or harvested_syntax["videos"]:
            conversation = display_media(harvested_syntax, conversation)

        check_for_request_to_end_chat(harvested_syntax)
        generate_response = False  # Response has passed criteria -> end while-loop

        if BREAK_CONVERSATION:
            offer_to_store_conversation(conversation)
            break

        if harvested_syntax["referral"]:
            conversation = direct_to_new_assistant(harvested_syntax["referral"])
            display_last_response(conversation)
            continue

        conversation = truncate_conversation_if_nessecary(conversation)
        conversation = remove_inactive_sources(conversation)

        print_summary_info(tokens_used=N_TOKENS_USED, response_costs=RESPONSE_COSTS)

    return conversation


def delete_last_bot_response(conversation):
    """Identifies which responses are from the assistant, and deletes the last
    response from the conversation. Used when the bot response has broken some
    rule, and we want it to create a new response."""
    assistant_indices = identify_assistant_responses(conversation)
    assistant_indices[-1]
    del conversation[assistant_indices[-1]]
    return conversation


def generate_raw_bot_response(conversation):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history."""
    global RESPONSE_TIMES, N_TOKENS_USED, RESPONSE_COSTS
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
    RESPONSE_COSTS.append(calculate_cost_of_response(conversation))
    return conversation


def create_user_input(conversation):
    """Prompts user to input a prompt (the "question") in the command line."""
    global BREAK_CONVERSATION

    while True:
        user_message = input(GREEN + "user" + RESET_COLOR + ": ")
        user_message, n_rewind, BREAK_CONVERSATION = scan_user_message_for_commands(
            user_message,
            conversation,
            BREAK_CONVERSATION,
            N_TOKENS_USED,
            RESPONSE_TIMES,
            RESPONSE_COSTS,
        )
        if n_rewind:
            conversation = rewind_chat_by_n_assistant_responses(n_rewind, conversation)
            print(f"** Rewinding by {n_rewind} bot responses **")
            reprint_whole_conversation(conversation)
        else:
            break
    conversation.append({"role": "user", "content": user_message})
    return conversation


def insert_knowledge(conversation, knowledge_list: list[str]):
    """Inserts knowledge into the conversation, and lets bot produce a new
    response using that information."""
    for knowledge in knowledge_list:
        if knowledge["content"]:
            print_summary_info(source_name=knowledge["source_name"])
            message = f"source {knowledge['source_name']}: {knowledge['content']}"
        else:
            message = f"Source {knowledge['source_name']} does not exist! Request only sources I have told you to use."
        conversation.append({"role": "system", "content": message})
    return conversation


def display_media(harvested_syntax: list, conversation: list):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:display_image{<file>}:¤ (replace with
    `display_video` for video)."""
    non_existing_file = False
    for image in harvested_syntax["images"]:
        if file_exists(image):
            display_image(image)
        else:
            non_existing_file = True
    for video in harvested_syntax["videos"]:
        if file_exists(video):
            play_video(video)
        else:
            non_existing_file = True

    if non_existing_file:
        {
            "role": "system",
            "content": "File does not exist. Display only files that I have referenced.",
        }
        conversation.append(
            "File does not exist. Display only files that I have referenced."
        )
    return conversation


def more_than_1_media_are_requested_check(harvested_syntax):
    """Checks if the bot attempts to display more than one piece of media (video
    or image) at a time (which is not desired)."""
    if not harvested_syntax["images"] and not harvested_syntax["videos"]:
        return False

    if len(harvested_syntax["images"]) + len(harvested_syntax["videos"]) >= 2:
        return True
    else:
        return False


def check_for_request_to_end_chat(harvested_syntax: dict):
    global BREAK_CONVERSATION
    if harvested_syntax["end_chat"]:
        BREAK_CONVERSATION = True


def direct_to_new_assistant(json_ticket):
    """Takes information about the users issue condensed into a json string, and
    redirects to the appropriate chatbot assistant."""
    print_summary_info(new_assistant_id=json_ticket["assistant_id"])
    prompt = get_prompt_for_assistant(json_ticket["assistant_id"])
    system_message = f"Here is a summary of the users issue: {json_ticket['topic']}"
    new_conversation = initiate_new_conversation(prompt, system_message)
    return new_conversation


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
        print_summary_info(sources=sources, inactivity_times=inactivity_times)

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
    if not contains_only_whitespace(message_cleaned):
        wrap_and_print_message(role, message_cleaned)


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
    """Gets the prompt (as a string) assosicated with the assistant id."""
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


def truncate_conversation_if_nessecary(conversation):
    """Shortens conversation when it gets too long. Uses and GPT assistant to summarize
    conversation. Work in progress..."""
    if count_tokens(conversation) > SETTINGS["max_tokens_before_truncation"]:
        if SETTINGS["truncation_method"] == "summarize":
            conversation = summarize_conversation(conversation)
            conversation = generate_raw_bot_response(conversation)
    return conversation


def rewind_chat_by_n_assistant_responses(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to bot-response n_current - n_rewind. If n_rewind == 1 then
    conversation resets to the second to last bot-response, allowing you to investigate the bots
    behaviour given the chat up to that point. Useful for testing how likely the bot is to reproduce
    an error (such as forgetting an instruction) or a desired response, since you don't have to
    restart the conversation from scratch."""
    assistant_indices = identify_assistant_responses(conversation)
    n_rewind = min([n_rewind, len(assistant_indices) - 1])
    index_reset = assistant_indices[-(n_rewind + 1)]
    return conversation[: index_reset + 1]


def print_summary_info(
    tokens_used=None,
    response_costs=None,
    sources=None,
    inactivity_times=None,
    source_name=None,
    regen_response=None,
    new_assistant_id=None,
):
    """Prints useful information. Controlled by parameters in config/settings.yaml. Prints the lines
    corresponding to the provided arguments."""

    if SETTINGS["print_cumulative_tokens"] and tokens_used:
        print(f"{GREY} Total number of tokens used: {tokens_used[-1]} {RESET_COLOR}")

    if SETTINGS["print_cumulative_cost"] and response_costs:
        total_cost = np.array(response_costs).sum()
        print(f"{GREY} Total cost of chat is: {total_cost:.4} kr {RESET_COLOR}")

    if SETTINGS["print_info_on_sources"] and sources:
        print(f"{GREY} Sources used: {sources} {RESET_COLOR}")

    if SETTINGS["print_info_on_sources"] and inactivity_times:
        print(f"{GREY} Source inactivity times: {inactivity_times} {RESET_COLOR}")

    if SETTINGS["print_when_source_is_inserted"] and source_name:
        print(
            f"{GREY} \nInserting information `{source_name}` into conversation... {RESET_COLOR}"
        )

    if SETTINGS["print_when_regen_response"] and regen_response:
        print(f"{GREY} \nRegenerating response... {RESET_COLOR}")

    if SETTINGS["print_when_user_is_redirected"] and new_assistant_id:
        print(
            f"{GREY} user is redirected to assistant {new_assistant_id}... {RESET_COLOR}"
        )


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
