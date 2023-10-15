
import tiktoken
import re
import textwrap
import os
import datetime

from typing import List
from typing import Dict

from utils.backend import MODEL_ID
from utils.backend import COMMAND_TO_DIR_MAP
from utils.backend import COMMAND_TO_EXTENSION_MAP
from utils.backend import CONVERSATIONS_DIR
from utils.backend import CONVERSATIONS_RAW_DIR
from utils.backend import get_full_path_and_create_dir
from utils.backend import load_json_from_path
from utils.backend import add_extension
from moviepy.editor import VideoFileClip

GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


def count_number_of_tokens(conversation):
    """Counts the number of tokens in a conversation. Uses token encoder
    https://github.com/openai/tiktoken/blob/main/tiktoken/model.py"""
    encoding = tiktoken.encoding_for_model(MODEL_ID)
    num_tokens = 0
    for message in conversation:
        # "user: assistant:" corresponds to 4 tokens
        num_tokens += 4
        num_tokens += len(encoding.encode(message["content"]))
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def remove_quotes_from_string(input_str):
    pattern = r'[\'\"]'  # Matches either single or double quotes
    result_str = re.sub(pattern, '', input_str)
    return result_str


def wrap_and_print_message(role, message, line_length=80):
    paragraphs = message.split('\n\n')  # Split message into paragraphs

    for i, paragraph in enumerate(paragraphs):
        lines = paragraph.split('\n')  # Split each paragraph into lines
        wrapped_paragraph = []

        for line in lines:
            # Split the line by line breaks and wrap each part separately
            parts = line.split('\n')
            wrapped_parts = [textwrap.wrap(part, line_length) for part in parts]

            # Join the wrapped parts using line breaks and append to the paragraph
            wrapped_line = '\n'.join('\n'.join(wrapped_part) for wrapped_part in wrapped_parts)
            wrapped_paragraph.append(wrapped_line)

        formatted_paragraph = '\n'.join(wrapped_paragraph)

        if i == 0:
            if role == "user":
                colour = GREEN
            else:
                colour = BLUE
            formatted_message = f'\n{colour + role + RESET}: {formatted_paragraph}\n'
        else:
            formatted_message = f'{formatted_paragraph}\n'

        print(formatted_message)


def strip_trailing_linebreaks(message):
    """Strip trailing line breaks (newlines) from the end of a string."""
    return message.rstrip('\n')


def play_video(video_file):
    video = VideoFileClip(video_file)
    video.preview()
    video.close()


def remove_lineabreaks_from_conversation(conversation):
    modified_conversation = []
    for message in conversation:
        modified_message = message.copy()  # Create a copy of the original message
        if 'content' in modified_message:
            modified_message['content'] = modified_message['content'].replace('\n', ' ')
        modified_conversation.append(modified_message)

    return modified_conversation


def remove_linebreaks(text):
    return text['content'].replace('\n', ' ')


def conversation_list_to_string(conversation):
    """Takes a conversation in the form of a list of dictionaries, and returns a string with the
    whole conversation"""
    return "\n".join([f"{d['role']}: {d['content']}" for d in conversation])


def extract_commands(response: str) -> List[Dict]:
    """Scans response for '¤:command_name(file_name):¤', and extracts the command name and
    filepath for each commmand. Extracted commands are returned as list of dictionaries with keys
    `file` and `type` indicating the command type and the file argument of the command."""
    command_pattern = r'¤:(.*?):¤'
    command_strings = re.findall(command_pattern, response)
    commands = []
    
    for command_string in command_strings:
        command = {}
        open_parenthesis_index = command_string.find("(")
        command["type"] = command_string[:open_parenthesis_index]
        directory = COMMAND_TO_DIR_MAP[command["type"]]
        extension = COMMAND_TO_EXTENSION_MAP[command["type"]]
        command["file"] = extract_filename_from_command(command_string, directory, extension)
        commands.append(command)

    return commands


def extract_filename_from_command(command, directory, extension=None):
    """Takes code such as `request_knowledge(discussion_comparison_with_jaffe_study)` and
    finds the full path of the file. `directory` is the directory that holds the file in extracted
    code."""
    match = re.search(r'\((.*?)\)', command)
    if match:
        file = match.group(1)
        file = remove_quotes_from_string(file)
        if extension:
            file = add_extension(file, extension)
        return os.path.join(directory, file)
    else:
        print("No file provided as argument in command")


def scan_for_json_data(response: str) -> str:
    """Scans a string for '¤¤¤ <json contet> ¤¤¤'. If two '¤¤¤' are detected,
    returns the content between these substrings."""
    clean_text = response.replace("\n", "")
    json_string = re.findall(r'\¤¤¤(.*?)\¤¤¤', clean_text)
    if len(json_string) == 0:
        return None
    else:
        return json_string[0]


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
                colored_role = '**<font color="#999999">system</font>**'
            else:
                colored_role = role  # For any other roles

            if i==1:
                header = "\n\n\n\n# Conversation \n\n\n\n"
                formatted_message = f"{header}{colored_role}: {content}  \n\n\n\n"
            else:
                formatted_message = f"\n{colored_role}: {content}  \n\n\n\n"
    
            file.write(formatted_message)