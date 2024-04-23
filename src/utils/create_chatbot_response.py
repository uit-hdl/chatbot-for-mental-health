"""Functions responsible for generating a valid chatbot response and updating the chat
accordingly. Relies on modules `filtes` and `overseers`."""

from utils.process_syntax import process_syntax_of_bot_response
from utils.managing_sources import insert_requested_knowledge
from utils.chat_utilities import delete_last_bot_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import grab_last_assistant_response
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.backend import MODEL_ID
from utils.backend import dump_current_conversation_to_json
from utils.filters import perform_quality_check_and_give_feedback
from utils.filters import correct_erroneous_show_image_command
from utils.general import silent_print
from utils.consumption_of_tokens import count_tokens_in_message
from utils.overseers import trim_message_length


def respond_to_user(conversation, chatbot_id: str) -> list:
    """Generates and appends a response to the conversation. Assistant can iteratively
    request sources untill it is satisfied. Requested sources are inserted into the
    conversation by system."""
    # Generate initial valid response
    (
        conversation,
        harvested_syntax,
    ) = generate_valid_chatbot_output(conversation, chatbot_id)

    knowledge_requests = harvested_syntax["knowledge_extensions"]
    counter = 0
    # Iteratively create responses untill the output is NOT a request for sources
    while knowledge_requests and counter < SETTINGS["max_requests"]:
        conversation = insert_requested_knowledge(conversation, knowledge_requests)
        (
            conversation,
            harvested_syntax,
        ) = generate_valid_chatbot_output(conversation, chatbot_id)
        knowledge_requests = harvested_syntax["knowledge_extensions"]
        counter += 1
        dump_current_conversation_to_json(conversation)

    return conversation, harvested_syntax


def generate_valid_chatbot_output(conversation, chatbot_id):
    """Attempts to generate a response untill the response passes quality check
    based on criteria such as whether or not the requested files exist."""

    for attempt in range(SETTINGS["n_attempts_at_producing_valid_response"]):
        conversation, harvested_syntax = create_tentative_bot_response(
            conversation, chatbot_id
        )
        conversation = manage_length_of_chatbot_response(conversation)
        conversation, flag = perform_quality_check_and_give_feedback(
            conversation, harvested_syntax, chatbot_id
        )

        if flag == "REJECTED":
            conversation = delete_last_bot_response(conversation)
            silent_print("Failed quality check (check log for details)")
        elif flag == "ACCEPTED":
            break

    if flag == "REJECTED":
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
    """Generates a bot message, corrects common bot errors where they can be easily
    corrected, extracts commands from the raw message, and checks if the files requested
    by the commands actually exists. If they do not exist, then system messages are added
    to the chat to inform the bot of its errors, and quality_check is set to "failed" so
    to inform that the bot should generate a new response."""
    silent_print(f"Generating raw bot response ...")
    conversation = generate_and_add_raw_bot_response(conversation)
    silent_print(f"Raw bot response generated")
    conversation = correct_erroneous_show_image_command(conversation)
    harvested_syntax = process_syntax_of_bot_response(conversation, chatbot_id)
    return conversation, harvested_syntax


def manage_length_of_chatbot_response(conversation) -> list:
    """Appends system warning to chat if message is too long. Very long messages
    get summarized."""
    bot_response = grab_last_assistant_response(conversation)
    response_length = count_tokens_in_message(bot_response, MODEL_ID)

    warning = None

    if response_length >= SETTINGS["max_tokens_before_summarization"]:
        silent_print("Response exceeds max length, shortening message with GPT-3.5...")
        conversation = trim_message_length(conversation)
        warning = "Your response was shortened as it exceeded the maximum allowed length; keep messages short."
    elif response_length > SETTINGS["limit_2_tokens_per_message"]:
        silent_print(f"Response has length {response_length} tokens...")
        warning = f"You almost reached the maximum message length. Limit information per message to not overwhelm the user."

    elif response_length > SETTINGS["limit_1_tokens_per_message"]:
        silent_print(f"Response has length {response_length} tokens...")
        warning = f"Response length: {response_length} tokens. Recall, cover at most 2 paragraphs per response when walking through information."

    if warning:
        conversation.append({"role": "system", "content": warning})

    return conversation
