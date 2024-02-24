"""Functions responsible for checking the quality of the chatbots response."""

import re
import json

from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import append_system_messages
from utils.managing_sources import get_currently_inserted_sources
from utils.consumption_of_tokens import count_tokens_in_message
from utils.overseers import CLASSIFICATION_CITATIONS
from utils.general import silent_print
from utils.general import list_intersection
from utils.general import list_subtraction
from utils.backend import MODEL_ID
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.backend import LOGGER_REJECTED_RESPONSES
from utils.backend import get_sources_available_to_chatbot


FLAG = "ACCEPTED"


def perform_quality_check(conversation, harvested_syntax: dict, chatbot_id: str) -> str:
    """Performs a quality check for the bot response based on the extracted
    information."""
    global FLAG
    warnings_file_existance = check_if_requested_files_exist(harvested_syntax)
    warnings_citations = citation_check(harvested_syntax, chatbot_id, conversation)
    warnings_length = check_length_of_chatbot_response(conversation)
    warnings = warnings_file_existance + warnings_citations + warnings_length
    conversation = append_system_messages(conversation, warnings)

    if FLAG == "NOT ACCEPTED":
        LOGGER.info(warnings)

    return FLAG


def check_if_requested_files_exist(harvested_syntax) -> list:
    """Checks whether the requested files exists. For each non-existant files that has
    been requested, it creates a corresponding warning message (to be inserted into chat
    by `system`).
    """
    global FLAG
    failure_messages = []

    for request in harvested_syntax["knowledge_extensions"]:
        if request["file_exists"] == False:
            failure_messages.append(
                f"`{request['name']}` does not exist! Request only sources and assistants I have referenced."
            )
            FLAG = "NOT ACCEPTED"

    for image in harvested_syntax["images"]:
        if image["file_exists"] == False:
            failure_messages.append(
                f"Image `{image['name']}` does not exist! Request only images I have referenced."
            )
            FLAG = "NOT ACCEPTED"

    for video in harvested_syntax["videos"]:
        if video["file_exists"] == False:
            failure_messages.append(
                f"Video `{video['name']}` does not exist! Request only videos I have referenced."
            )
            FLAG = "NOT ACCEPTED"

    return failure_messages


def check_length_of_chatbot_response(conversation) -> list:
    """Appends system warning to chat if message is too long."""
    global FLAG
    bot_response = grab_last_assistant_response(conversation)
    response_length = count_tokens_in_message(bot_response, MODEL_ID)

    warning_messages = []

    if response_length >= SETTINGS["max_tokens_per_message"]:
        silent_print("Response exceeds length...")
        warning_messages = ["Your response was too long, try again!"]
        FLAG = "NOT ACCEPTED"

    if response_length > SETTINGS["warning_limit_tokens_per_message"]:
        silent_print(f"Response has length {response_length} tokens...")
        warning_messages = [
            f"Your response was {response_length} tokens long; try to be more concise"
        ]

    return warning_messages


def citation_check(harvested_syntax: dict, chatbot_id: str, conversation: list) -> list:
    """Compares validity of chatbot citations. Checks for the following errors:

    1. The bot is citing sources outside of the valid/existing citations
    2. The bot response contains no citation at all
    3. The bot is citing sources that exist, but are not in the conversation
    """

    global FLAG
    bot_citations = harvested_syntax["citations"]
    available_sources = get_sources_available_to_chatbot(chatbot_id)
    valid_citations = available_sources + CLASSIFICATION_CITATIONS
    inserted_citations = get_currently_inserted_sources(conversation)

    # Compare bots citations against valid citations
    bot_valid_citations = list_intersection(valid_citations, bot_citations)
    bot_invalid_citations = list_subtraction(bot_citations, bot_valid_citations)
    citations_that_are_not_inserted = list_subtraction(
        bot_valid_citations, inserted_citations
    )

    making_knowledge_request = len(harvested_syntax["knowledge_extensions"]) > 0
    warning_messages = []

    if not making_knowledge_request:

        if bot_invalid_citations:
            FLAG = "NOT ACCEPTED"
            warning_messages.append(f"Citations {bot_invalid_citations} are not valid!")
            LOGGER.info(f"Bot cited invalid sources: {bot_invalid_citations}")

        if not bot_citations:
            FLAG = "NOT ACCEPTED"
            warning_messages.append(f"All your messages MUST start with a citation!")

        if citations_that_are_not_inserted:
            warning_messages.append(
                f"Warning: you are citing sources ({citations_that_are_not_inserted}) that are not inserted in the chat."
            )

    return warning_messages


def correct_erroneous_show_image_command(conversation) -> list:
    """Sometimes the bot uses `show: image_name.png`, which is really just a reference to
    the command ¤:display_image(image_name):¤ that is used as a shorthand in the prompt.
    If such an error is identified, converts it to a proper syntax, and appends a system
    warning.
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
