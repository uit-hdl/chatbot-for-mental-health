"""Functions responsible for generating a valid chatbot response and updating the chat
accordingly. Relies on modules `filtes` and `overseers`."""

from utils.process_syntax import process_syntax_of_bot_response
from utils.managing_sources import insert_requested_knowledge
from utils.chat_utilities import delete_last_bot_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.backend import CHATBOT_CONFIG
from utils.backend import LOGGER
from utils.backend import dump_chat_to_dashboard
from utils.filters import perform_quality_check_and_give_feedback
from utils.filters import correct_erroneous_show_image_command
from utils.general import silent_print
from utils.manage_response_length import manage_length_of_chatbot_response


def respond_to_user(conversation, chatbot_id: str) -> tuple[list, dict]:
    """Generates and appends a response to the conversation. Assistant can
    iteratively request sources untill it is satisfied. Requested sources are
    inserted into the conversation.

    Returns updated conversation and dictionary with harvested syntax."""
    # Generate initial valid response
    (
        conversation,
        harvested_syntax,
    ) = generate_valid_chatbot_output(conversation, chatbot_id)

    knowledge_requests = harvested_syntax["knowledge_extensions"]
    counter = 0
    # Iteratively create responses untill the output is NOT a request for sources
    while knowledge_requests and counter < CHATBOT_CONFIG["max_requests"]:
        conversation = insert_requested_knowledge(conversation, knowledge_requests)
        (
            conversation,
            harvested_syntax,
        ) = generate_valid_chatbot_output(conversation, chatbot_id)
        knowledge_requests = harvested_syntax["knowledge_extensions"]
        counter += 1
        dump_chat_to_dashboard(conversation, dump_md_copy=True)

    return conversation, harvested_syntax


def generate_valid_chatbot_output(conversation, chatbot_id):
    """Attempts to generate a response untill the response passes quality check
    based on criteria such as whether or not the requested files exist."""
    
    for attempt in range(CHATBOT_CONFIG["n_attempts_at_producing_valid_response"]):
        conversation, harvested_syntax = create_tentative_bot_response(
            conversation, chatbot_id
        )
        conversation = manage_length_of_chatbot_response(conversation)
        conversation, flag = perform_quality_check_and_give_feedback(
            conversation, harvested_syntax, chatbot_id
        )

        if flag == "REJECT":
            conversation = delete_last_bot_response(conversation)
            silent_print("Failed quality check (check log for details)")
        elif flag == "ACCEPT":
            break

    if flag == "REJECT":
        # Has used up max number of attempts; keep the next one regardless of outcome
        conversation, harvested_syntax = create_tentative_bot_response(
            conversation, chatbot_id
        )
        conversation = manage_length_of_chatbot_response(conversation)
        conversation, flag = perform_quality_check_and_give_feedback(
            conversation, harvested_syntax, chatbot_id
        )
        LOGGER.info("Ran out of attempts to pass quality check.")

    return conversation, harvested_syntax


def create_tentative_bot_response(conversation, chatbot_id):
    """Generates a bot message, corrects common bot errors where they can be
    easily corrected, extracts commands from the raw message, and checks if the
    files requested by the commands actually exists. If they do not exist, then
    system messages are added to the chat to inform the bot of its errors, and
    quality_check is set to "failed" so to inform that the bot should generate a
    new response."""
    silent_print(f"Generating raw bot response ...")
    conversation = generate_and_add_raw_bot_response(conversation)
    silent_print(f"Raw bot response generated")
    conversation = correct_erroneous_show_image_command(conversation)
    harvested_syntax = process_syntax_of_bot_response(conversation, chatbot_id)
    return conversation, harvested_syntax
