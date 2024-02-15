import openai
import sys
import re

from utils.general import silent_print
from utils.general import offer_to_store_conversation
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.backend import CONFIG
from utils.backend import dump_current_conversation
from utils.backend import load_yaml_file
from utils.process_syntax import process_syntax_of_bot_response
from utils.managing_sources import remove_inactive_sources
from utils.managing_sources import extract_sources_inserted_by_system
from utils.chat_utilities import rewind_chat_by_n_assistant_responses
from utils.chat_utilities import append_system_messages
from utils.chat_utilities import delete_last_bot_response
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import initiate_prompt_engineered_ai_agent
from utils.chat_utilities import generate_raw_bot_response
from utils.chat_utilities import check_length_of_chatbot_response
from utils.overseer import check_sources
from utils.console_chat_display import display_last_response
from utils.console_chat_display import display_last_assistant_response
from utils.console_chat_display import reprint_whole_conversation_without_syntax
from utils.console_chat_display import play_videos
from utils.console_chat_display import print_whole_conversation_with_backend_info
from utils.console_chat_display import display_images
from utils.console_chat_display import ROLE_TO_ANSI_COLOR_MAP
from utils.console_chat_display import RESET_COLOR

openai.api_key = API_KEY
openai.api_type = CONFIG["api_type"]
openai.api_base = CONFIG["api_base"]
openai.api_version = CONFIG["api_version"]

# Initiate global variables
BREAK_CONVERSATION = False


def sleep_diary_assistant_bot(chatbot_id, chat_filepath=None):
    """Running this function starts a conversation with a tutorial bot that
    helps explain how a web-app (https://app.consensussleepdiary.com) functions.
    The web app is a free online app for collecting sleep data."""
    LOGGER.info(f"\n*** Starting new console chat ***\n")
    if chat_filepath:
        conversation = continue_previous_conversation(chat_filepath, chatbot_id)
    else:
        conversation = initiate_new_conversation(chatbot_id)
        display_last_response(conversation)

    while True:
        conversation = create_user_input(conversation)

        if BREAK_CONVERSATION:
            offer_to_store_conversation(conversation)
            break

        conversation, harvested_syntax = generate_processed_bot_response(
            conversation, chatbot_id
        )

        display_last_assistant_response(conversation)
        display_images(harvested_syntax["images"])
        play_videos(harvested_syntax["videos"])

        conversation = check_sources(conversation, harvested_syntax, chatbot_id)
        dump_current_conversation(conversation)

        if harvested_syntax["referral"]:
            if harvested_syntax["referral"]["file_exists"]:
                conversation = direct_to_new_assistant(harvested_syntax["referral"])
                display_last_response(conversation)

        conversation = remove_inactive_sources(conversation)


def continue_previous_conversation(chat_filepath: str, chatbot_id: str) -> list:
    """Inserts the current prompt into a previous stored conversation that was
    discontinued, so that you can pick up where you left of."""
    conversation = load_yaml_file(chat_filepath)
    prompt = PROMPTS[chatbot_id]
    # Replace original prompt with requested prompt
    conversation[0] = {"role": "system", "content": prompt}
    print_whole_conversation_with_backend_info(conversation)
    return conversation


def initiate_new_conversation(chatbot_id: str, system_message=None):
    """Initiates a conversation with the chat bot."""
    conversation = initiate_prompt_engineered_ai_agent(
        PROMPTS[chatbot_id], system_message
    )
    LOGGER.info("Starting new conversation with %s.", chatbot_id)
    conversation = generate_raw_bot_response(conversation, CONFIG)
    return conversation


def create_user_input(conversation) -> list:
    """Prompts user to input a prompt (the "question") in the command line."""
    global BREAK_CONVERSATION

    while True:
        user_message = input(
            ROLE_TO_ANSI_COLOR_MAP["user"] + "user" + RESET_COLOR + ": "
        )
        if "rewind_by" in user_message:
            n_rewind = int(user_message[-1])
            conversation = rewind_chat_by_n_assistant_responses(n_rewind, conversation)
            reprint_whole_conversation_without_syntax(conversation)
            dump_current_conversation(conversation)
        else:
            if user_message == "break":
                BREAK_CONVERSATION = True
            break
    conversation.append({"role": "user", "content": user_message})
    return conversation


def generate_processed_bot_response(conversation, chatbot_id) -> list:
    """Generates and interprets a message from the assistant. The response is generated iteratively
    since the bot may first have to request sources and then react to those sources, and also the
    message has to pass quality checks (primarily checking existance of requested files).
    """
    (
        conversation,
        harvested_syntax,
    ) = generate_valid_response(conversation, chatbot_id)

    conversation, harvested_syntax = collect_sources_until_satisfied(
        conversation, harvested_syntax, chatbot_id
    )
    return conversation, harvested_syntax


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
            silent_print(
                "Bot failed quality check, regenerating response (check log for details)."
            )
        elif quality_check == "passed":
            break

    if quality_check == "failed":
        (
            conversation,
            harvested_syntax,
            _,
        ) = generate_bot_response_and_check_quality(conversation, chatbot_id)
        LOGGER.info("Ran out of attempts to pass quality check.")

    return conversation, harvested_syntax


def generate_bot_response_and_check_quality(conversation, chatbot_id):
    """Generates a bot message, corrects common bot errors where they can be easily corrected,
    extracts commands from the raw message, and checks if the files requested by the commands
    actually exists. If they do not exist, then system messages are added to the chat to inform the
    bot of its errors, and quality_check is set to "failed" so to inform that the bot
    should generate a new response."""
    conversation = generate_raw_bot_response(conversation, CONFIG)
    conversation = correct_erroneous_show_image_command(conversation)
    (
        harvested_syntax,
        failure_messages,
    ) = process_syntax_of_bot_response(conversation, chatbot_id)
    length_warning, length_status = check_length_of_chatbot_response(conversation)

    if length_status == "REDO":
        failure_messages += length_warning
    if length_status == "WARNING":
        conversation.append(length_warning)

    if failure_messages:
        conversation = append_system_messages(conversation, failure_messages)
        LOGGER.info(failure_messages)
        quality_check = "failed"
        silent_print("")
    else:
        quality_check = "passed"

    return conversation, harvested_syntax, quality_check


def correct_erroneous_show_image_command(conversation) -> list:
    """Sometimes the bot uses (show: image_name.png), which is really just a reference to the
    command ¤:display_image(image_name):¤ that is used as a shorthand in the prompt. If such an
    error is identified, converts it to a proper syntax, and appends a system warning.
    """
    message = grab_last_assistant_response(conversation)
    pattern = r"[`'\"]show:\s*([^`'\"]+\.png)[`'\"]"
    matches = re.findall(pattern, message, flags=re.IGNORECASE)

    if matches:
        corrected_message = re.sub(pattern, r"¤:display_image(\1):¤", message)
        system_message = "Warning: expressions of the form (show: image.png) have been corrected to ¤:display_image(image.png):¤"
        conversation[-1]["content"] = corrected_message
        conversation.append({"role": "system", "content": system_message})

    return conversation


def collect_sources_until_satisfied(conversation, harvested_syntax, chatbot_id):
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
    """Checks for request to insert knowledge, and inserts knowledge into the conversation under the
    role of system."""

    for knowledge in knowledge_list:
        requested_source = knowledge["source_name"]
        if knowledge["content"]:
            inserted_sources = extract_sources_inserted_by_system(conversation)
            if requested_source in inserted_sources:
                message = f"The source {requested_source} is already in chat. Never request sources that are already provided!"
                LOGGER.info(message)
            else:
                message = f"source {requested_source}: {knowledge['content']}"
                LOGGER.info("Source %s inserted in conversation.", requested_source)
                if SETTINGS["print_knowledge_requests"]:
                    silent_print(f"Source {requested_source} inserted in conversation.")
        else:
            message = f"Source {requested_source} does not exist! Request only sources I have told you to use."
            LOGGER.info(message)

        conversation.append({"role": "system", "content": message})

    return conversation


def direct_to_new_assistant(referral: dict) -> list:
    """Receives information about the users issue collected in json format, and
    redirects to the requested chatbot assistant."""
    LOGGER.info("Transferring to assistant %s", referral["assistant_id"])
    new_conversation = initiate_new_conversation(referral["assistant_id"])
    return new_conversation


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
