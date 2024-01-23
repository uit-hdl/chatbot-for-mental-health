import openai
import sys
import time
import logging

import pprint

from utils.general import wrap_and_print_message
from utils.general import count_tokens
from utils.general import play_video
from utils.general import conversation_list_to_string
from utils.general import count_tokens_used_to_create_last_response
from utils.general import grab_last_response
from utils.general import print_whole_conversation
from utils.general import offer_to_store_conversation
from utils.general import display_image
from utils.general import identify_assistant_responses
from utils.general import calculate_cost_of_response
from utils.general import remove_code_syntax_from_message
from utils.general import contains_only_whitespace
from utils.general import print_summary_info
from utils.general import correct_erroneous_show_image_command
from utils.general import append_system_messages
from utils.general import delete_last_bot_response
from utils.general import GREEN
from utils.general import RESET_COLOR
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import SETTINGS
from utils.backend import CONFIG
from utils.backend import dump_current_conversation
from utils.backend import load_yaml_file
from utils.backend import file_exists
from utils.process_syntax import process_syntax_of_bot_response
from utils.managing_sources import remove_inactive_sources
from utils.managing_sources import extract_sources_inserted_by_system
from utils.manage_conversation_length import reconstruct_conversation_with_summary
from utils.manage_conversation_length import separate_system_from_conversation
from utils.manage_conversation_length import remove_code_syntax_from_whole_conversation
from utils.manage_conversation_length import insert_information_in_prompt
from utils.user_commands import scan_user_message_for_commands

openai.api_key = API_KEY
openai.api_type = CONFIG["api_type"]
openai.api_base = CONFIG["api_base"]
openai.api_version = CONFIG["api_version"]

# Initiate global variables
BREAK_CONVERSATION = False
N_TOKENS_USED = []  # Tracks the number of tokens used to generate each response
RESPONSE_TIMES = []  # Tracks the time that the bot takes to generate a response
RESPONSE_COSTS = []  # Tracks the cost (in kr) per response

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
        conversation = truncate_conversation_if_nessecary(conversation)


def continue_previous_conversation(chat_filepath, prompt):
    """Inserts the current prompt into a previous stored conversation that was
    discontinued, so that you can pick up where you left of."""
    conversation = load_yaml_file(chat_filepath)
    # Replace original prompt with requested prompt
    conversation[0] = {"role": "system", "content": prompt}
    print_whole_conversation(conversation)
    return conversation


def initiate_new_conversation(inital_prompt, system_message=None):
    """Initiates a conversation with the chat bot."""
    conversation = []
    conversation.append({"role": "system", "content": inital_prompt})
    if system_message:
        conversation.append({"role": "system", "content": system_message})
    conversation = generate_raw_bot_response(conversation)
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
            reprint_whole_conversation_without_syntax(conversation)
        else:
            break
    conversation.append({"role": "user", "content": user_message})
    return conversation


def rewind_chat_by_n_assistant_responses(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to bot-response number = n_current - n_rewind. If n_rewind == 1
    then conversation resets to the second to last bot-response, allowing you to investigate the
    bots behaviour given the chat up to that point. Useful for testing how likely the bot is to
    reproduce an error (such as forgetting an instruction) or a desired response, since you don't
    have to restart the conversation from scratch. Works by Identifing and deleting messages between
    the current message and the bot message you are resetting to, but does not nessecarily reset the
    overall conversation to the state it was in at the time that message was produced (for instance,
    the prompt might have been altered)."""
    assistant_indices = identify_assistant_responses(conversation)
    n_rewind = min([n_rewind, len(assistant_indices) - 1])
    index_reset = assistant_indices[-(n_rewind + 1)]
    return conversation[: index_reset + 1]


def reprint_whole_conversation_without_syntax(
    conversation, include_system_messages=True
):
    """Reprints whole conversation (not including the prompt)."""
    for message in conversation[1:]:
        if not include_system_messages and message["role"] == "system":
            continue
        else:
            display_message_without_syntax(message)


def conversation_status():
    """Checks if conversation has ended by scanning for a predefined substring
    that acts as a cue to end the conversation."""
    if BREAK_CONVERSATION:
        return "ended"
    else:
        return "active"


def generate_bot_response(conversation, chatbot_id):
    """Generates and interprets a message from the assistant. The response is generated iteratively
    since the bot may first have to request sources and then react to those sources, and also the
    message has to pass quality checks (primarily checking existance of requested files).
    """
    global BREAK_CONVERSATION

    (
        conversation,
        harvested_syntax,
    ) = generate_valid_response(conversation, chatbot_id)

    conversation, harvested_syntax = request_and_insert_sources_until_satisfied(
        conversation, harvested_syntax, chatbot_id
    )

    display_last_response(conversation)
    dump_current_conversation(conversation)

    conversation = display_if_media(harvested_syntax, conversation)

    BREAK_CONVERSATION = check_for_request_to_end_chat(harvested_syntax)
    if BREAK_CONVERSATION:
        offer_to_store_conversation(conversation)

    if harvested_syntax["referral"]:
        if harvested_syntax["referral"]["file_exists"]:
            conversation = direct_to_new_assistant(harvested_syntax["referral"])
            display_last_response(conversation)

    conversation = remove_inactive_sources(conversation)

    print_summary_info(tokens_used=N_TOKENS_USED, response_costs=RESPONSE_COSTS)

    return conversation


def generate_valid_response(conversation, chatbot_id):
    """Generates responses iteratively untill the response passes quality check based criteria such
    as whether or not the requested files exist."""
    for attempt in range(SETTINGS["n_attempts_at_producing_valid_response"]):
        (
            conversation,
            harvested_syntax,
            quality_check,
        ) = generate_bot_response_and_check_quality(conversation, chatbot_id)

        if quality_check == "failed":
            conversation = delete_last_bot_response(conversation)
            print(f"Quality check results: {quality_check}")
        elif quality_check == "passed":
            break

    if quality_check == "failed":
        # Generate a response regardless...
        (
            conversation,
            harvested_syntax,
            _,
        ) = generate_bot_response_and_check_quality(conversation, chatbot_id)
        print("Ran out of attempts to pass quality check.")

    return conversation, harvested_syntax


def generate_bot_response_and_check_quality(conversation, chatbot_id):
    """Generates a bot message, corrects common bot errors where they can be easily corrected,
    extracts commands from the raw message, and checks if the files requested by the commands
    actually exists. If they do not exist, then system messages are added to the chat to inform the
    bot of its errors, and quality_check is set to "failed" so to inform that the bot
    should generate a new response."""
    conversation = generate_raw_bot_response(conversation)
    conversation = correct_erroneous_show_image_command(conversation)
    (
        harvested_syntax,
        warning_messages,
    ) = process_syntax_of_bot_response(conversation, chatbot_id)
    if warning_messages:
        conversation = append_system_messages(conversation, warning_messages)
        print_summary_info(regen_response=True)
        quality_check = "failed"
    else:
        quality_check = "passed"

    return conversation, harvested_syntax, quality_check


def request_and_insert_sources_until_satisfied(
    conversation, harvested_syntax, chatbot_id
):
    """Assistant can iteratively request sources untill it is satisfied. Sources are inserted into
    the conversation by system."""
    counter = 0
    while harvested_syntax["knowledge_requests"] and counter < SETTINGS["max_requests"]:
        conversation = insert_knowledge(
            conversation, harvested_syntax["knowledge_requests"]
        )
        (
            conversation,
            harvested_syntax,
        ) = generate_valid_response(conversation, chatbot_id)
        counter += 1
    return conversation, harvested_syntax


def insert_knowledge(conversation, knowledge_list: list[str]):
    """Inserts knowledge into the conversation, and lets bot produce a new
    response using that information."""

    for knowledge in knowledge_list:
        if knowledge["content"]:
            inserted_sources = extract_sources_inserted_by_system(conversation)
            requested_source = knowledge["source_name"]
            if requested_source in inserted_sources:
                message = f"The source {requested_source} is already inserted in chat. Never request sources that are already provided!"
            else:
                print_summary_info(source_name=requested_source)
                message = f"source {requested_source}: {knowledge['content']}"
        else:
            message = f"Source {requested_source} does not exist! Request only sources I have told you to use."

        conversation.append({"role": "system", "content": message})

    return conversation


def display_if_media(harvested_syntax: list, conversation: list):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:display_image{<file>}:¤ (replace with
    `display_video` for video)."""
    non_existing_file = False
    for image in harvested_syntax["images"]:
        if file_exists(image["path"]):
            display_image(image["path"])
    for video in harvested_syntax["videos"]:
        if file_exists(video["path"]):
            play_video(video["path"])
    return conversation


def check_for_request_to_end_chat(harvested_syntax: dict):
    global BREAK_CONVERSATION
    if harvested_syntax["end_chat"]:
        BREAK_CONVERSATION = True
    return BREAK_CONVERSATION


def direct_to_new_assistant(json_ticket):
    """Takes information about the users issue condensed into a json string, and
    redirects to the appropriate chatbot assistant."""
    print_summary_info(new_assistant_id=json_ticket["assistant_id"])
    prompt = get_prompt_for_assistant(json_ticket["assistant_id"])
    system_message = f"Here is a summary of the users issue: {json_ticket['topic']}"
    new_conversation = initiate_new_conversation(prompt, system_message)
    return new_conversation


def get_prompt_for_assistant(assistant_id):
    """Gets the prompt (as a string) assosicated with the assistant id."""
    return PROMPTS[assistant_id]


def truncate_conversation_if_nessecary(conversation):
    """Shortens conversation when it gets too long. Uses and GPT assistant to summarize
    conversation. Work in progress..."""
    if count_tokens(conversation) > SETTINGS["max_tokens_before_truncation"]:
        if SETTINGS["truncation_method"] == "summarize":
            conversation = summarize_conversation(conversation)
            conversation = generate_raw_bot_response(conversation)
    return conversation


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


if __name__ == "__main__":
    chatbot_id = "referral"
    chat_filepath = None

    if len(sys.argv) > 1:
        chatbot_id = sys.argv[1]
        if chatbot_id == "":
            chatbot_id = "referral"
    if len(sys.argv) > 2:
        chat_filepath = sys.argv[2]

    sleep_diary_assistant_bot(chatbot_id, chat_filepath)
