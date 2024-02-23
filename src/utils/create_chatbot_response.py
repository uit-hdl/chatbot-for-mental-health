"""Functions responsible for generating a valid chatbot response and updating the chat
accordingly."""

from utils.process_syntax import process_syntax_of_bot_response
from utils.managing_sources import get_currently_inserted_sources
from utils.chat_utilities import delete_last_bot_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import grab_last_assistant_response
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.backend import LOGGER_REJECTED_RESPONSES
from utils.backend import CONFIG
from utils.backend import dump_to_json
from utils.filters import perform_quality_check
from utils.filters import correct_erroneous_show_image_command
from utils.general import silent_print


def respond_to_user(conversation, chatbot_id: str) -> list:
    """Generates and appends a response to the user, as well as Assistant can iteratively request sources untill it is satisfied. Sources are
    inserted into the conversation by system."""

    # Generate initial valid response
    (
        conversation,
        harvested_syntax,
    ) = generate_valid_chatbot_output(conversation, chatbot_id)

    knowledge_requests = harvested_syntax["knowledge_extensions"]
    counter = 0
    # Iteratively create responses untill the output is NOT a request for sources
    while knowledge_requests and counter < SETTINGS["max_requests"]:
        conversation = insert_knowledge(conversation, knowledge_requests)
        (
            conversation,
            harvested_syntax,
        ) = generate_valid_chatbot_output(conversation, chatbot_id)
        counter += 1

    return conversation, harvested_syntax


def generate_valid_chatbot_output(conversation, chatbot_id):
    """Attempts to generate a response untill the response passes quality check based on
    criteria such as whether or not the requested files exist."""

    for attempt in range(SETTINGS["n_attempts_at_producing_valid_response"]):
        conversation, harvested_syntax = create_tentative_bot_response(
            conversation, chatbot_id
        )
        flag = perform_quality_check(conversation, harvested_syntax, chatbot_id)

        if flag == "NOT ACCEPTED":
            LOGGER_REJECTED_RESPONSES.info(grab_last_assistant_response(conversation))
            conversation = delete_last_bot_response(conversation)
            silent_print("Failed quality check, retrying (check log for details)")
        elif flag == "ACCEPTED":
            break

    if flag == "NOT ACCEPTED":
        # Has used up max number of attempts; keep the next one regardless of outcome
        conversation, harvested_syntax = create_tentative_bot_response(
            conversation, chatbot_id
        )
        flag = perform_quality_check(conversation, harvested_syntax, chatbot_id)
        LOGGER.info("Ran out of attempts to pass quality check.")

    return conversation, harvested_syntax


def create_tentative_bot_response(conversation, chatbot_id):
    """Generates a bot message, corrects common bot errors where they can be easily
    corrected, extracts commands from the raw message, and checks if the files requested
    by the commands actually exists. If they do not exist, then system messages are added
    to the chat to inform the bot of its errors, and quality_check is set to "failed" so
    to inform that the bot should generate a new response."""
    conversation = generate_and_add_raw_bot_response(conversation, CONFIG)
    conversation = correct_erroneous_show_image_command(conversation)
    harvested_syntax = process_syntax_of_bot_response(conversation, chatbot_id)
    return conversation, harvested_syntax


def insert_knowledge(conversation, knowledge_extensions: list[str]):
    """Checks for request to insert knowledge, and inserts knowledge into the
    conversation. First checks if there sources are already in the chat."""
    inserted_sources = get_currently_inserted_sources(conversation)

    for source in knowledge_extensions:
        source_name = source["name"]
        if source["content"] is not None:
            # Check if source is in chat already
            if source["name"] in inserted_sources:
                message = (
                    f"The source {source['name']} is already available in the chat!"
                )
                LOGGER.info(message)
            else:
                # Put source content in system message
                message = f"source {source_name}: {source['content']}"
                LOGGER.info("Source %s inserted in conversation.", source["name"])
                if SETTINGS["print_knowledge_requests"]:
                    silent_print(f"Source {source_name} inserted in conversation.")

        conversation.append({"role": "system", "content": message})

    return conversation
