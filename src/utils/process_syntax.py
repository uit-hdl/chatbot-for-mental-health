"""Functions that are related to processing of commands made by the bot, specifically: extracting
the part of strings that contain command syntax, separating the name of the command from the
argument of the command, and collecting the information in a managable format."""
import re
import os
import json
import ast

from typing import List
from typing import Dict

from utils.general import grab_last_response
from utils.general import remove_quotes_from_string
from utils.backend import add_extension
from utils.backend import file_exists
from utils.backend import COMMAND_TO_DIR_MAP
from utils.backend import COMMAND_TO_EXTENSION_MAP
from utils.backend import load_textfile_as_string
from utils.backend import get_shared_subfolder_name


def process_syntax_of_bot_response(
    conversation, chatbot_id
) -> (List[Dict], List[Dict]):
    """Scans the response for symbols ¤: and :¤, and extracts the name of the
    commands, the file-arguments of the commands. Commands are 'referral', 'request_knowledge',
    'display_image', 'play_video', and 'show_sources'. Returns two lists of dictionaries.
    """
    subfolder = get_shared_subfolder_name(chatbot_id)
    chatbot_response = grab_last_response(conversation)
    commands, arguments = extract_command_names_and_arguments(chatbot_response)

    harvested_syntax = {}
    harvested_syntax["knowledge_requests"] = get_knowledge_requests(
        commands, arguments, subfolder
    )
    harvested_syntax["sources"] = get_citations(commands, arguments)
    (
        harvested_syntax["images"],
        harvested_syntax["videos"],
    ) = get_image_and_video_requests(commands, arguments, subfolder)
    harvested_syntax["referrals"] = get_referrals(commands, arguments)
    harvested_syntax["end_chat"] = "end_chat" in commands

    return harvested_syntax


def extract_command_names_and_arguments(chatbot_response: str) -> (list, list):
    """Takes a response that may contain substrings of the form ¤:command_name(argument):¤ and
    extracts the command names (command_name) and command arguments in lists."""
    command_pattern = r"¤:(.*?):¤"
    command_strings = re.findall(command_pattern, chatbot_response)
    commands = []
    arguments = []
    for command_string in command_strings:
        open_parenthesis_index = command_string.find("(")
        command_name = command_string[:open_parenthesis_index]
        argument = extract_command_argument(command_string)
        commands.append(command_name)
        arguments.append(argument)
    return commands, arguments


def get_knowledge_requests(
    commands: list, arguments: list, subfolder: str
) -> List[Dict]:
    """Fetches the text associated with each knowledge request command."""
    sources = []
    if commands:
        for command, argument in zip(commands, arguments):
            if command == "request_knowledge":
                knowledge = {}
                source_path = os.path.join("library", subfolder, argument) + ".md"
                knowledge["source_name"] = argument
                if file_exists(source_path):
                    knowledge["content"] = load_textfile_as_string(source_path)
                else:
                    knowledge["content"] = None
                sources.append(knowledge)
    return sources


def get_citations(commands: list, arguments: list) -> list[str]:
    """Get sources that the chatbot has cited in its response."""
    sources = None
    for command, argument in zip(commands, arguments):
        if command == "cite":
            sources = ast.literal_eval(argument)
    return sources


def get_image_and_video_requests(commands, arguments, subfolder) -> list[dict]:
    """Finds file paths for the images and videos."""
    images = []
    videos = []
    for command, argument in zip(commands, arguments):
        if command == "display_image":
            images.append(os.path.join("media/images", subfolder, argument))
        if command == "play_video":
            videos.append(os.path.join("media/videos", subfolder, argument))

    return images, videos


def get_referrals(commands, arguments) -> dict:
    for command, argument in zip(commands, arguments):
        if command == "referral":
            return convert_json_string_to_dict(argument)


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


def extract_command_argument(command_string: str) -> str:
    """Extract command argument from strings such as 'show_video(video_name)'."""
    arg = re.search(r"\((.*?)\)", command_string)
    if arg:
        return arg.group(1)


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
