"""Functions responsible for checking the quality of the chatbots response."""

import re
import json

from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import count_tokens_in_message
from utils.chat_utilities import append_system_messages
from utils.overseers import CLASSIFICATION_CITATIONS
from utils.general import silent_print
from utils.general import list_intersection
from utils.general import list_subtraction
from utils.backend import MODEL_ID
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.backend import get_file_names_in_directory


FLAG = "ACCEPTED"


def perform_quality_check(conversation, harvested_syntax: dict, chatbot_id: str) -> str:
    """Performs a quality check for the bot response based on the extracted
    information."""
    global FLAG
    warnings_file_existance = check_if_requested_files_exist(harvested_syntax)
    warnings_citations = citation_check(harvested_syntax, chatbot_id)
    warnings_length = check_length_of_chatbot_response(conversation)
    warnings = warnings_file_existance + warnings_citations + warnings_length
    conversation = append_system_messages(conversation, warnings)

    if FLAG == "NOT ACCEPTED":
        LOGGER.info(warnings)
        LOGGER.info(
            "Harvested syntax from failed message: %s",
            json.dumps(harvested_syntax, indent=2),
        )

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


def citation_check(harvested_syntax: dict, chatbot_id: str) -> list:
    """Compares the sources cited by the bot with the set of existing sources."""
    global FLAG
    citations = harvested_syntax["citations"]
    available_sources = get_file_names_in_directory(chatbot_id)
    valid_citations = available_sources + CLASSIFICATION_CITATIONS

    # Compare bots citations against valid citations
    valid_citations_by_bot = list_intersection(valid_citations, citations)
    invalid_citations_by_bot = list_subtraction(citations, valid_citations_by_bot)

    warning_messages = []
    making_knowledge_request = len(harvested_syntax["knowledge_extensions"]) > 0

    if not making_knowledge_request:
        if invalid_citations_by_bot:
            warning_messages = [f"Citations {invalid_citations_by_bot} are not valid!"]
            LOGGER.info(f"Bot cited invalid sources: {invalid_citations_by_bot}")
        if not citations:
            FLAG = "NOT ACCEPTED"
            warning_messages = [f"All your messages must start with a citation!"]

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
