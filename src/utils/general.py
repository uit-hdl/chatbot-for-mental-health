import ast
import tiktoken
import re
import textwrap
import os
import json
import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from typing import List
from typing import Dict

from utils.backend import MODEL_ID
from utils.backend import COMMAND_TO_DIR_MAP
from utils.backend import COMMAND_TO_EXTENSION_MAP
from utils.backend import CONVERSATIONS_DIR
from utils.backend import CONVERSATIONS_RAW_DIR
from utils.backend import CONVERSATIONS_FORMATTED_DIR
from utils.backend import get_full_path_and_create_dir
from utils.backend import load_json_from_path
from utils.backend import add_extension
from utils.backend import get_shared_subfolder_name
from utils.backend import dump_to_json
from utils.backend import SETTINGS
from moviepy.editor import VideoFileClip

GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


def display_image(image_path):
    """Displays the image in the provided path."""
    img = mpimg.imread(image_path)
    plt.imshow(img)
    plt.gca().set_axis_off()  # Turn off the axes
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.gca().yaxis.set_major_locator(plt.NullLocator())

    plt.show(block=False)
    plt.pause(SETTINGS["plot_duration"])
    plt.close()


def play_video(video_file):
    """Plays the video."""
    video = VideoFileClip(video_file)
    video.preview()
    video.close()


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


def remove_quotes_from_string(input_str):
    """Removes quotation marks, `"` or `'`, from a string."""
    pattern = r"[\'\"]"  # Matches either single or double quotes
    result_str = re.sub(pattern, "", input_str)
    return result_str


def remove_code_syntax_from_message(message):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_json = re.sub(r"\¤¤(.*?)\¤¤", "", message, flags=re.DOTALL)
    message_no_code = re.sub(r"\¤:(.*?)\:¤", "", message_no_json)
    # Remove surplus spaces
    message_cleaned = re.sub(r" {2,}(?![\n])", " ", message_no_code)
    message_cleaned = remove_trailing_newlines(message_cleaned)
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


def wrap_and_print_message(role, message, line_length=80):
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
            formatted_message = f"\n{colour + role + RESET}: {formatted_paragraph}\n"
        else:
            formatted_message = f"{formatted_paragraph}\n"

        print(formatted_message)


def strip_trailing_linebreaks(message):
    """Strip trailing line breaks (newlines) from the end of a string."""
    return message.rstrip("\n")


def remove_lineabreaks_from_conversation(conversation):
    """Removes linebreaks `\n` from conversation."""
    modified_conversation = []
    for message in conversation:
        modified_message = message.copy()  # Create a copy of the original message
        if "content" in modified_message:
            modified_message["content"] = remove_linebreaks(modified_message["content"])
        modified_conversation.append(modified_message)

    return modified_conversation


def remove_linebreaks(text):
    """Removes line breaks"""
    return text.replace("\n", " ")


def conversation_list_to_string(conversation: list) -> str:
    """Takes a conversation in the form of a list of dictionaries, and returns the
    whole conversation as a string."""
    return "\n".join([f"{d['role']}: {d['content']}" for d in conversation])


def extract_commands_and_filepaths(response: str, chatbot_id) -> List[Dict]:
    """Scans response for '¤:command_name(file_name):¤', and extracts the command name and
    filepath for each commmand. Extracted commands are returned as list of dictionaries with keys
    `file` and `type` indicating the command type and the file argument of the command. For example
    [{'type': 'display_image', 'file':
    '/home/per/UIt/chatbots/chatGPT4/insomnia-assistant/images/login_sleep_diary.png'}]
    """
    command_pattern = r"¤:(.*?):¤"
    command_strings = re.findall(command_pattern, response)
    commands = []

    for command_string in command_strings:
        command_dict = get_command_file_and_type(command_string, chatbot_id)
        commands.append(command_dict)

    return commands


def get_command_file_and_type(command_string: str, chatbot_id: str):
    """Takes a string of the form 'command_name(file_name)' and returns a dictionary with command
    type (name of the command, e.g. `command_name`) and file path (None if command has no
    argument)."""
    open_parenthesis_index = command_string.find("(")
    command_type = command_string[:open_parenthesis_index]

    if command_type in COMMAND_TO_DIR_MAP.keys():
        directory_for_filetype = COMMAND_TO_DIR_MAP[command_type]
        shared_subfolder = get_shared_subfolder_name(chatbot_id)
        directory = os.path.join(directory_for_filetype, shared_subfolder)
        extension = COMMAND_TO_EXTENSION_MAP[command_type]
        filename = extract_filename_from_command(command_string, extension)

        if filename:
            return {"type": command_type, "file": os.path.join(directory, filename)}

    return {"type": command_type, "file": None}


def extract_filename_from_command(command: str, extension=None):
    """Takes code such as `request_knowledge(discussion_comparison_with_jaffe_study)` and
    finds the full path of the file referenced in the argument. `directory` is the directory that
    holds the file in extracted code."""
    match = re.search(r"\((.*?)\)", command)
    if match:
        file = match.group(1)
        # In case bot as enclosed filename with quotation marks, remove them
        file = remove_quotes_from_string(file)
        if extension:
            file = add_extension(file, extension)
        return file
    else:
        print("No file provided as argument in command")
        return None


def scan_for_json_data(response: str) -> list[Dict]:
    """Scans a string for '¤¤ <json content> ¤¤'. If multiple '¤¤' pairs are detected,
    returns a list of content between these substrings."""
    clean_text = response.replace("\n", "")
    json_strings = re.findall(r"\¤¤(.*?)\¤¤", clean_text)
    json_dicts = [convert_json_string_to_dict(string) for string in json_strings]
    return json_dicts


def convert_json_string_to_dict(json_data: str) -> dict:
    """Converts json file content extracted from a string into a dictionary."""
    # Standardize quotation marks
    json_data = json_data.replace("'", '"')
    try:
        result = json.loads(json_data)
    except json.JSONDecodeError as e:
        print(f"Warning: error decoding JSON string: {e}")
        result = None
    return result


def dump_conversation_to_textfile(conversation: list, filepath: str):
    """Dumps a conversation to a Markdown file with color-coded roles."""
    full_path = get_full_path_and_create_dir(filepath)

    with open(full_path, "w") as file:
        for i, message in enumerate(conversation):
            role = message["role"]
            content = message["content"]

            if role == "assistant":
                colored_role = '**<font color="#44cc44">assistant</font>**'
            elif role == "user":
                colored_role = '**<font color="#3399ff">user</font>**'
            elif role == "system":
                if i > 0:
                    content = f'<font color="#999999">{content}</font>'
                colored_role = '**<font color="#999999">system</font>**'
            else:
                colored_role = role  # For any other roles

            if i == 1:
                header = "\n\n\n\n# Conversation \n\n\n\n"
                formatted_message = f"{header}{colored_role}: {content}  \n\n\n\n"
            else:
                formatted_message = f"\n{colored_role}: {content}  \n\n\n\n"

            file.write(formatted_message)


def remove_nones(array: list):
    """Remove elements of list of type `None`"""
    return [x for x in array if x is not None]


def grab_last_response(conversation: list) -> str:
    """Grab the last response. Convenience function for better code-readability."""
    return conversation[-1]["content"]


def rewind_chat_by_n_assistant_responses(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to bot-response n_current - n_rewind. If n_rewind == 1 then
    conversation resets to the second to last bot-response, allowing you to investigate the bots
    behaviour given the chat up to that point. Useful for testing how likely the bot is to reproduce
    an error (such as forgetting an instruction) or a desired response, since you don't have to
    restart the conversation from scratch."""
    assistant_indices = identify_assistant_reponses(conversation)
    n_rewind = min([n_rewind, len(assistant_indices) - 1])
    index_reset = assistant_indices[-(n_rewind + 1)]
    return conversation[: index_reset + 1]


def identify_assistant_reponses(conversation) -> list[int]:
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


def store_conversation(conversation: list, label: str = "conversation"):
    """Stores conversation in json format in conversations/raw and in formatted
    markdown file in conversations/formatted. Default name is `conversation`."""
    json_file_path = f"{CONVERSATIONS_RAW_DIR}/{label}.json"
    txt_file_path = f"{CONVERSATIONS_FORMATTED_DIR}/{label}.md"
    if grab_last_response(conversation) == "break":
        # Remove break
        conversation = conversation[:-1]
    dump_to_json(conversation, json_file_path)
    dump_conversation_to_textfile(conversation, txt_file_path)
    print(f"Conversation stored in {json_file_path} and {txt_file_path}")
