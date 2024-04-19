"""Functions responsible for checking the quality of the chatbots response."""

import re

from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import append_system_messages
from utils.managing_sources import get_names_of_currently_inserted_sources
from utils.overseers import MESSAGE_CLASSIFICATIONS
from utils.overseers import evaluate_with_overseers
from utils.general import silent_print
from utils.backend import SETTINGS
from utils.backend import LOGGER_REJECTED_RESPONSES
from utils.backend import LOGGER
from utils.backend import dump_current_conversation_to_json
from utils.backend import get_sources_available_to_chatbot


def perform_quality_check_and_give_feedback(
    conversation, harvested_syntax: dict, chatbot_id: str
) -> str:
    """Performs a quality check for the bot response based on the extracted
    information. Warnings are produced for undesired behaviours which get appended to the
    conversation so that the chatbot can learn from its mistakes. Certain errors (those
    that get hard warnings) will result in the bot having to regenerate its
    response."""
    flag = "ACCEPTED"

    # -- HARD CODED FILTER --
    if SETTINGS["enable_hard_coded_filter"]:
        existance_hard_warnings = check_if_requested_files_exist(harvested_syntax)
        citation_soft_warnings, citation_hard_warnings = citation_check(
            harvested_syntax, chatbot_id, conversation
        )
        # Collect warnings
        soft_warnings = citation_soft_warnings
        hard_warnings = existance_hard_warnings + citation_hard_warnings
        all_warnings = hard_warnings + soft_warnings

        conversation = append_system_messages(conversation, all_warnings)

        if hard_warnings:
            flag = "NOT ACCEPTED"
            LOGGER.info(all_warnings)
            log_failure(conversation, harvested_syntax, hard_warnings)

    # -- OVERSEER FILTER --
    if SETTINGS["enable_overseer_filter"] and not hard_warnings:
        overseer_evaluation, warning_overseer = evaluate_with_overseers(
            conversation, harvested_syntax, chatbot_id
        )
        conversation = append_system_messages(conversation, warning_overseer)

        if overseer_evaluation == "NOT ACCEPTED":
            flag = "NOT ACCEPTED"
            LOGGER.info(all_warnings)
            log_failure(conversation, harvested_syntax, warning_overseer)
            silent_print(all_warnings)

        dump_current_conversation_to_json(conversation)

    return conversation, flag


def check_if_requested_files_exist(harvested_syntax) -> list:
    """Checks whether the requested files exists. For each non-existant files that has
    been requested, it creates a corresponding warning message (to be inserted into chat
    by `system`).
    """
    hard_warnings = []

    for request in harvested_syntax["knowledge_extensions"]:
        if request["file_exists"] == False:
            hard_warnings.append(
                f"`{request['name']}` does not exist! Request only sources and assistants I have referenced."
            )

    for image in harvested_syntax["images"]:
        if image["file_exists"] == False:
            hard_warnings.append(
                f"Image `{image['name']}` does not exist! Request only images I have referenced."
            )

    for video in harvested_syntax["videos"]:
        if video["file_exists"] == False:
            hard_warnings.append(
                f"Video `{video['name']}` does not exist! Request only videos I have referenced."
            )

    return hard_warnings


def citation_check(harvested_syntax: dict, chatbot_id: str, conversation: list):
    """Compares validity of chatbot citations. Checks for the following errors:

    1. The bot response contains no citation at all
    2. The bot is citing sources outside of the set of valid citations (i.e. citations
       that have been referenced in the system prompt)
    3. The bot is citing sources that exist, but are not in the conversation

    errors are categorized as warnings and failures, where `failure` means tha the bot
    will have to create a new response.
    """
    if len(harvested_syntax["knowledge_extensions"]) > 0:
        return [], []

    bot_citations = harvested_syntax["citations"]
    available_sources = get_sources_available_to_chatbot(chatbot_id)
    inserted_citations = get_names_of_currently_inserted_sources(conversation)

    soft_warnings = []
    hard_warnings = []

    # Check if there are any citations
    if not bot_citations and not harvested_syntax["referral"]:
        hard_warnings.append(f"All your messages MUST start with a citation!")

    for citation in bot_citations:

        if citation in available_sources:
            if citation not in inserted_citations:
                soft_warnings.append(
                    f"You cited a source ({citation}) that has not been inserted in the chat! Ensure the source is in the chat BEFORE you cite it."
                )
        else:
            if citation not in MESSAGE_CLASSIFICATIONS:
                hard_warnings.append(f"({citation}) is not a valid citation!")

    return soft_warnings, hard_warnings


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


def log_failure(conversation, harvested_syntax, hard_warnings: list[str]):
    """Dumps logging information about the failed attempt to
    chat-info/rejected_messages.py."""
    message = f"""
    REJECTED RESPONSE:\n{grab_last_assistant_response(conversation)}\n
    HARVESTED SYNTAX:\n {harvested_syntax}\n
    REASONS FOR REJECTION:\n{hard_warnings}"""
    LOGGER_REJECTED_RESPONSES.info(message)
