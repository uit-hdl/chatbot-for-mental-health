"""Functions that are related to processing of commands made by the bot, specifically: extracting
the part of strings that contain command syntax, separating the name of the command from the
argument of the command, and collecting the information in a managable format."""
import re
import os
import json
import ast

from typing import List
from typing import Dict

from utils.general import grab_last_assistant_response
from utils.general import remove_quotes_from_string
from utils.backend import file_exists
from utils.backend import IMAGES_DIR
from utils.backend import VIDEOS_DIR
from utils.backend import LIBRARY_DIR
from utils.backend import load_textfile_as_string
from utils.backend import get_shared_subfolder_name
from utils.backend import dump_to_json


def process_syntax_of_bot_response(conversation, chatbot_id) -> dict:
    """Scans the response for symbols ¤: and :¤ and extracts the name of the
    commands and their arguments. Returns a dictionary with keys being the command types, with each
    type containing the information collected for that type. Commands are 'referral',
    'request_knowledge', 'display_image', 'play_video', and 'show_sources'. Dumps the resulting
    dictionary to chat-info/harvested_syntax.json."""
    subfolder = get_shared_subfolder_name(chatbot_id)
    chatbot_response = grab_last_assistant_response(conversation)
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
    harvested_syntax["referral"] = get_referral(commands, arguments)
    harvested_syntax["end_chat"] = "end_chat" in commands

    dump_to_json(harvested_syntax, "chat-info/harvested_syntax.json")

    return harvested_syntax


def extract_command_names_and_arguments(chatbot_response: str) -> (list, list):
    """Takes a response that may contain substrings of the form ¤:command_name(argument):¤ and
    extracts the command names (command_name) and command arguments in lists."""
    chatbot_response_without_newlines = chatbot_response.replace("\n", "")
    command_pattern = r"¤:(.*?):¤"
    command_strings = re.findall(command_pattern, chatbot_response_without_newlines)
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
                source_path = os.path.join(LIBRARY_DIR, subfolder, argument) + ".md"
                knowledge["source_name"] = remove_quotes_from_string(argument)
                if file_exists(source_path):
                    knowledge["content"] = load_textfile_as_string(source_path)
                else:
                    knowledge["content"] = None
                sources.append(knowledge)
    return sources


def get_citations(commands: list, arguments: list) -> list[str]:
    """Get sources that the chatbot has cited in its response. TODO: Need to add checks..."""
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
            filename = remove_quotes_from_string(argument)
            images.append(os.path.join(IMAGES_DIR, subfolder, filename))
        if command == "play_video":
            filename = remove_quotes_from_string(argument)
            videos.append(os.path.join(VIDEOS_DIR, subfolder, filename))

    return images, videos


def get_referral(commands, arguments) -> dict:
    """Gets the referral dictionary with information on who to redirect the user to,
    and what the user needs help with."""
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
    """Extract command argument from strings. E.g. 'show_video(video_name)' -> 'show_video'."""
    arg = re.search(r"\((.*?)\)", command_string)
    if arg:
        return arg.group(1)
