import tiktoken
import re
import textwrap
import numpy as np

from utils.backend import MODEL_ID
from utils.backend import CONVERSATIONS_RAW_DIR
from utils.backend import CONVERSATIONS_FORMATTED_DIR
from utils.backend import dump_to_json
from utils.backend import dump_conversation_to_textfile
from utils.backend import SETTINGS

# Chat colors
GREY = "\033[2;30m"  # info messages
GREEN = "\033[92m"  # user
BLUE = "\033[94m"  # assistant
RESET_COLOR = "\033[0m"


def contains_only_whitespace(input_string):
    """Checks if a message is empty (can happen after syntax is removed)."""
    return all(char.isspace() or char == "" for char in input_string)


def print_summary_info(
    tokens_used=None,
    response_costs=None,
    sources=None,
    inactivity_times=None,
    inactive_source=None,
    source_name=None,
    regen_response=None,
    new_assistant_id=None,
    show_image_attempts=None,
    warning_messages=None,
):
    """Prints useful information. Controlled by parameters in config/settings.yaml. Prints the lines
    corresponding to the provided arguments."""
    global SETTINGS
    if SETTINGS["print_cumulative_tokens"] and tokens_used:
        print(f"{GREY} Total number of tokens used: {tokens_used[-1]} {RESET_COLOR}")

    if SETTINGS["print_cumulative_cost"] and response_costs:
        total_cost = np.array(response_costs).sum()
        print(f"{GREY} Total cost of chat is: {total_cost:.4} kr {RESET_COLOR}")

    if SETTINGS["print_info_on_sources"] and sources:
        print(f"{GREY} Sources used: {sources} {RESET_COLOR}")

    if SETTINGS["print_info_on_sources"] and inactivity_times:
        print(f"{GREY} Source inactivity times: {inactivity_times} {RESET_COLOR}")

    if SETTINGS["print_removal_of_inactive_source"] and inactive_source:
        print(f"{GREY} Removing inactive source {inactive_source} {RESET_COLOR}")

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

    if SETTINGS["print_system_warnings"] and warning_messages:
        for message in warning_messages:
            print(
                f"{GREY} system: {message} {RESET_COLOR}"
            )

# ## Conversation processesing ##
def delete_last_bot_response(conversation):
    """Identifies which responses are from the assistant, and deletes the last
    response from the conversation. Used when the bot response has broken some
    rule, and we want it to create a new response."""
    assistant_indices = identify_assistant_responses(conversation)
    assistant_indices[-1]
    del conversation[assistant_indices[-1]]
    return conversation


def grab_last_response(conversation: list) -> str:
    """Grab the last response. Convenience function for better code-readability."""
    return conversation[-1]["content"]


def grab_last_assistant_response(conversation: list) -> str:
    """Grab the latest assistant response."""
    index_assistant_messages = identify_assistant_responses(conversation)
    return conversation[index_assistant_messages[-1]]["content"]


def identify_assistant_responses(conversation) -> list[int]:
    """Gets the index/indices for `assistant` responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "assistant"]


def offer_to_store_conversation(conversation):
    """Asks the user in the console if he wants to store the conversation, and
    if so, how to name it."""
    store_conversation_response = input("Store conversation? (Y/N): ").strip().lower()
    if store_conversation_response == "y":
        label = input("File name (hit enter for default): ").strip().lower()
        if label == "":
            label = "conversation"
        store_conversation(conversation, label)
    else:
        print("Conversation not stored")


def correct_erroneous_show_image_command(conversation) -> list:
    """Sometimes the bot uses (show: image_name.png), which is really just a reference to the
    command ¤:display_image(image_name):¤ that is used as a shorthand in the prompt. If such an
    error is identified, converts it to a proper syntax, and appends a system warning.
    """
    message = grab_last_assistant_response(conversation)
    pattern = r"\(show: (\w+\.png)\)"
    matches = re.findall(pattern, message, flags=re.IGNORECASE)

    if matches:
        corrected_message = re.sub(pattern, r"¤:display_image(\1):¤", message)
        system_message = "Warning: expressions of the form (show: image.png) have been corrected to ¤:display_image(image.png):¤"
        conversation[-1]["content"] = corrected_message
        conversation.append({"role": "system", "content": system_message})
        print_summary_info(show_image_attempts=matches)

    return conversation


def append_system_messages(conversation, system_messages: list[str]):
    """Appends each message to the conversation under the role of system."""
    for message in system_messages:
        conversation.append({"role": "system", "content": message})
    return conversation


def store_conversation(conversation: list, label: str = "conversation"):
    """Stores conversation in json format in conversations/raw and in formatted
    markdown file in conversations/formatted. Default name is `conversation`."""
    json_file_path = f"{CONVERSATIONS_RAW_DIR}/{label}.json"
    txt_file_path = f"{CONVERSATIONS_FORMATTED_DIR}/{label}.md"
    if grab_last_response(conversation) == "break":
        conversation = conversation[:-1]
    dump_to_json(conversation, json_file_path)
    dump_conversation_to_textfile(conversation, txt_file_path)
    print(f"Conversation stored in {json_file_path} and {txt_file_path}")


def print_whole_conversation(conversation):
    """Prints the entire conversation (excluding the prompt) in the console."""
    for message in conversation[1:]:
        role = message["role"]
        message = message["content"].strip()
        wrap_and_print_message(role, message)


def count_tokens_used_to_create_last_response(conversation):
    """Counts the number of tokens used to generate the last message in the conversation."""
    tokens_in = count_tokens(conversation[:-1])
    tokens_out = count_tokens(conversation[-1])
    return tokens_in + tokens_out


def calculate_cost_of_response(conversation):
    """Calculates the cost of generating the last repsonse (which is assumed to be from
    assistant)."""
    tokens_in = count_tokens(conversation[:-1])
    tokens_out = count_tokens(conversation[-1])
    dollars_tokens_in = tokens_in * SETTINGS["dollars_per_1k_input_token"] / 1000
    dollars_tokens_out = tokens_out * SETTINGS["dollars_per_1k_output_token"] / 1000
    kroners_total = (dollars_tokens_in + dollars_tokens_out) * SETTINGS[
        "kr_to_dollar_ratio"
    ]
    return kroners_total


def count_tokens(conversation):
    """Counts the number of tokens in a conversation. Uses token encoder
    https://github.com/openai/tiktoken/blob/main/tiktoken/model.py. Input argument can be either a
    list or a dictionary (for instance the last response in the conversation).
    """
    if isinstance(conversation, dict):
        # Ensure list format
        conversation = [conversation]
    encoding = tiktoken.encoding_for_model(MODEL_ID)
    num_tokens = 0
    for message in conversation:
        # "user: assistant:" corresponds to 4 tokens
        num_tokens += 4
        num_tokens += len(encoding.encode(message["content"]))
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


# ## Presenting messages ##
def remove_quotes_from_string(input_str):
    """Removes quotation marks, `"` or `'`, from a string. Used for standardization
    in cases where bot is not always consistent, such as play_video("video_name") instead of
    play_video(video_name)."""
    pattern = r"[\'\"]"  # Matches either single or double quotes
    result_str = re.sub(pattern, "", input_str)
    return result_str


def remove_code_syntax_from_message(message: str):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_code = re.sub(r"\¤:(.*?)\:¤", "", message)
    # Remove surplus spaces
    message_cleaned = re.sub(r" {2,}(?![\n])", " ", message_no_code)
    if message_cleaned:
        message_cleaned = remove_superflous_linebreaks(message_cleaned)
    return message_cleaned


def remove_superflous_linebreaks(message):
    """Removes all superflous linebreak characters that may arise after removing commands."""
    message_cleaned = remove_trailing_newlines(message)
    message_cleaned = remove_superflous_linebreaks_between_paragraphs(message_cleaned)
    return message_cleaned


def remove_trailing_newlines(text):
    """Removes trailing newline characters (may emerge after stripping away commands from bot
    messages)."""
    while text[-1] == " " or text[-1] == "\n":
        if text[-1] == " ":
            text = text.rstrip(" ")
        elif text[-1] == "\n":
            text = text.rstrip("\n")
    return text


def remove_superflous_linebreaks_between_paragraphs(text: str):
    """Replaces consecutive line breaks with just two line breaks (may emerge after stripping away
    commands from bot messages)."""
    cleaned_text = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned_text


def wrap_and_print_message(role, message, line_length=80):
    """Prints measures, and ensures that line lengths does not exceed a given maximum."""
    paragraphs = message.split("\n\n")  # Split message into paragraphs

    for i, paragraph in enumerate(paragraphs):
        lines = paragraph.split("\n")  # Split each paragraph into lines
        wrapped_paragraph = []

        for line in lines:
            # Split the line by line breaks and wrap each part separately
            parts = line.split("\n")
            wrapped_parts = [textwrap.wrap(part, line_length) for part in parts]

            # Join the wrapped parts using line breaks and append to the paragraph
            wrapped_line = "\n".join(
                "\n".join(wrapped_part) for wrapped_part in wrapped_parts
            )
            wrapped_paragraph.append(wrapped_line)

        formatted_paragraph = "\n".join(wrapped_paragraph)

        if i == 0:
            if role == "user":
                colour = GREEN
            else:
                colour = BLUE
            formatted_message = (
                f"\n{colour + role + RESET_COLOR}: {formatted_paragraph}\n"
            )
        else:
            formatted_message = f"{formatted_paragraph}\n"

        print(formatted_message)


def conversation_list_to_string(conversation: list) -> str:
    """Takes a conversation in the form of a list of dictionaries, and returns the
    whole conversation as a string."""
    return "\n".join([f"{d['role']}: {d['content']}" for d in conversation])
