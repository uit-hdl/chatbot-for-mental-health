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
from utils.backend import PROMPTS_DIR
from utils.backend import load_textfile_as_string
from utils.backend import get_shared_subfolder_name
from utils.backend import dump_to_json


def process_syntax_of_bot_response(conversation, chatbot_id) -> (dict, list[str]):
    """Scans the response for symbols ¤: and :¤ and extracts the name of the
    commands and their arguments. Returns a dictionary with keys being the command types, with each
    type containing the information collected for that type. Commands are 'referral',
    'request_knowledge', 'display_image', 'play_video', and 'show_sources'. Dumps the resulting
    dictionary to chat-info/harvested_syntax.json."""
    subfolder = get_shared_subfolder_name(chatbot_id)
    chatbot_response = grab_last_assistant_response(conversation)
    commands, arguments = extract_command_names_and_arguments(chatbot_response)
    harvested_syntax = process_and_organize_commands_and_arguments(
        commands, arguments, subfolder
    )
    warning_messages = generate_warning_messages(harvested_syntax)
    dump_to_json(harvested_syntax, "chat-info/harvested_syntax.json")

    return harvested_syntax, warning_messages


def generate_warning_messages(harvested_syntax) -> list[str]:
    """Checks whether the requested files exists. For each non-existant files that has been
    requested, it creates a corresponding warning message (to be inserted into chat by `system`).
    """
    warning_messages = []
    for knowledge_request in harvested_syntax["knowledge_requests"]:
        if not knowledge_request["file_exists"]:
            warning_messages.append(
                f"Source `{knowledge_request['source_name']}` does not exist! Request only sources I have referenced."
            )
    for image in harvested_syntax["images"]:
        if not image["file_exists"]:
            warning_messages.append(
                f"Image `{image['name']}` does not exist! Request only images I have referenced."
            )
    for video in harvested_syntax["videos"]:
        if not video["file_exists"]:
            warning_messages.append(
                f"Video `{video['name']}` does not exist! Request only videos I have referenced."
            )
    if harvested_syntax["referral"]:
        if not harvested_syntax["referral"]["file_exists"]:
            warning_messages.append(
                f"The assistant `{harvested_syntax['referral']['assistant_id']}` does not exist! Only redirect the user to assistants I have referenced."
            )
    if len(harvested_syntax["images"]) + len(harvested_syntax["videos"]) >= 2:
        warning_messages.append(
            "It is illegal to present more than 1 video/image per response!"
        )
    return warning_messages


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


def process_and_organize_commands_and_arguments(
    commands: list, arguments: list, subfolder: str
):
    """Processes the list of commands and associated arguments, and organizes this information in a
    dictionary."""
    harvested_syntax = {}
    harvested_syntax["knowledge_requests"] = get_knowledge_requests(
        commands, arguments, subfolder
    )
    harvested_syntax["sources"] = get_citations(commands, arguments)
    harvested_syntax["images"] = get_image_requests(commands, arguments, subfolder)
    harvested_syntax["videos"] = get_video_requests(commands, arguments, subfolder)
    harvested_syntax["referral"] = get_referral(commands, arguments, subfolder)
    harvested_syntax["end_chat"] = "end_chat" in commands
    return harvested_syntax


def get_knowledge_requests(
    commands: list, arguments: list, subfolder: str
) -> List[Dict]:
    """Fetches the text associated with each knowledge request command."""
    knoweldge_requests = []
    if commands:
        for command, argument in zip(commands, arguments):
            if command == "request_knowledge":
                knowledge = {}
                source_path = os.path.join(LIBRARY_DIR, subfolder, argument) + ".md"
                knowledge["source_name"] = remove_quotes_from_string(argument)
                if file_exists(source_path):
                    knowledge["content"] = load_textfile_as_string(source_path)
                    knowledge["file_exists"] = True
                else:
                    knowledge["content"] = None
                    knowledge["file_exists"] = False
                knoweldge_requests.append(knowledge)
    return knoweldge_requests


def get_citations(commands: list, arguments: list) -> list[str]:
    """Get sources that the chatbot has cited in its response."""
    citations = []
    for command, argument in zip(commands, arguments):
        if command == "cite":
            if argument is None:
                print("Warning: Empty citation argument.")
            else:
                try:
                    citations = ast.literal_eval(argument)
                except (SyntaxError, ValueError):
                    print(f"Warning: could not evaluate citation: {argument}")
    return citations


def get_image_requests(commands, arguments, subfolder) -> list[dict]:
    """Finds file paths and other info for the images. Returns list with dictionary for each
    requested video, containing the name of the video, status for its existance, and file path.
    """
    images = []
    for command, argument in zip(commands, arguments):
        if command == "display_image":
            image = {}
            image_path = os.path.join(IMAGES_DIR, subfolder, argument)
            image["name"] = remove_quotes_from_string(argument)
            if file_exists(image_path):
                image["path"] = image_path
                image["file_exists"] = True
            else:
                image["path"] = None
                image["file_exists"] = False
            images.append(image)
    return images


def get_video_requests(commands, arguments, subfolder) -> list[dict]:
    """Finds file paths and other info for the videos (same logic as get_image_requests). Returns
    list with dictionary for each requested video, indicating the name of the video, status for its
    existance, and file path."""
    videos = []
    for command, argument in zip(commands, arguments):
        if command == "play_video":
            video = {}
            video_path = os.path.join(VIDEOS_DIR, subfolder, argument)
            video["name"] = remove_quotes_from_string(argument)
            if file_exists(video_path):
                video["path"] = video_path
                video["file_exists"] = True
            else:
                video["path"] = None
                video["file_exists"] = False
            videos.append(video)
    return videos


def get_referral(commands, arguments, subfolder: str) -> dict:
    """Gets the referral dictionary with information on who to redirect the user to,
    and what the user needs help with."""
    for command, argument in zip(commands, arguments):
        if command == "referral":
            referral_ticket = convert_json_string_to_dict(argument)
            assistant_path = (
                os.path.join(PROMPTS_DIR, subfolder, referral_ticket["assistant_id"])
                + ".md"
            )
            if file_exists(assistant_path):
                referral_ticket["file_exists"] = True
            else:
                referral_ticket["file_exists"] = False

            return referral_ticket


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
