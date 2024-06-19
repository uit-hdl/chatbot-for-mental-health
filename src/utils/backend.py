"""Backend functions concerned with loading and dumpind data, and configuring
file and directory paths."""

import yaml
import json
import os
import pathlib
import yaml
import pickle
from typing import Tuple
import shutil

from utils.logging import setup_logger

# Directory paths
ROOT_DIR = pathlib.Path(__file__).parents[2]
CONVERSATIONS_DIR = os.path.join(ROOT_DIR, "conversations")
CONVERSATIONS_CURRENT_DIR = os.path.join(ROOT_DIR, "conversations/current")
CONVERSATIONS_RAW_DIR = os.path.join(CONVERSATIONS_DIR, "raw")
CONVERSATIONS_FORMATTED_DIR = os.path.join(CONVERSATIONS_DIR, "formatted")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user-data")
IMAGES_DIR = os.path.join(ROOT_DIR, "media/images")
VIDEOS_DIR = os.path.join(ROOT_DIR, "media/videos")
LIBRARY_DIR = os.path.join(ROOT_DIR, "library")
PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts")
CHAT_DASHBOARD_DIR = os.path.join(ROOT_DIR, "chat-dashboard")
OVERSEER_DUMP_DIR = os.path.join(CHAT_DASHBOARD_DIR, "judge-dumps")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
CHAT_DUMPS_DIR = os.path.join(RESULTS_DIR, "chat-dumps")

# Configuration-file paths
CONFIG_PATH = os.path.join(ROOT_DIR, "config/config.yaml")
CITATIONS_PATH = os.path.join(ROOT_DIR, "config/citations.yaml")
OVERSEER_CONFIG_PATH = os.path.join(ROOT_DIR, "config/overseer_stage.yaml")
SETTINGS_PATH = os.path.join(ROOT_DIR, "config/settings.yaml")
SYSTEM_MESSAGES_PATH = os.path.join(ROOT_DIR, "config/system_messages.yaml")
URL_MAP_PATH = os.path.join(ROOT_DIR, "config/url.yaml")

# File-dump paths
LOGFILE_DUMP_PATH = os.path.join(CHAT_DASHBOARD_DIR, "chat.log")
LOGFILE_REJECTED_RESPONSES_DUMP_PATH = os.path.join(
    CHAT_DASHBOARD_DIR, "rejected_responses.log"
)
DELETED_MESSAGES_DUMP_PATH = os.path.join(CHAT_DASHBOARD_DIR, "truncated_messages.json")
PRE_SUMMARY_DUMP_PATH = os.path.join(CHAT_DASHBOARD_DIR, "pre_summary_response.md")
TRANSCRIPT_DUMP_PATH = os.path.join(CHAT_DASHBOARD_DIR, "transcript.json")
CONVERSATION_DUMP_PATH = os.path.join(CHAT_DASHBOARD_DIR, "conversation.json")
OVERSEER_DUMP_PATH = os.path.join(
    CHAT_DASHBOARD_DIR, "prompts-&-evaluations/overseer.md"
)
SWIFT_JUDGEMENT_DUMP_PATH = os.path.join(
    CHAT_DASHBOARD_DIR, "prompts-&-evaluations/prelim_judgement.md"
)
HARVESTED_SYNTAX_DUMP_PATH = os.path.join(CHAT_DASHBOARD_DIR, "harvested_syntax.json")
TOKEN_USAGE_DUMP_PATH = os.path.join(
    CHAT_DASHBOARD_DIR, "token-usage/chat_consumption.json"
)

# Loggers
LOGGER = setup_logger(LOGFILE_DUMP_PATH)
LOGGER_REJECTED_RESPONSES = setup_logger(LOGFILE_REJECTED_RESPONSES_DUMP_PATH)


def convert_json_string_to_dict(json_data: str) -> dict:
    """Converts json file content extracted from a string into a dictionary."""
    # Ensure proper JSON format (deal with special characters)
    json_data = json_data.replace("\n", "")
    json_string_valid_format = json.dumps(json_data)
    try:
        # To string (dont know why this works...)
        python_string = json.loads(json_string_valid_format)
        dictionary = json.loads(python_string)  # To dictionary
    except json.JSONDecodeError as e:
        print(f"Warning: error decoding JSON string: {e}")
        dictionary = None
    return dictionary


def get_file_names_in_directory(directory_path):
    """Retrieve the names of all files (without extensions) within the specified directory
    and its subdirectories."""
    file_names = []
    full_directory_path = get_full_path(directory_path)
    for _, _, files in os.walk(full_directory_path):
        for file in files:
            file_name, _ = os.path.splitext(file)
            file_names.append(file_name)
    return file_names


def load_textfile_as_string(file_path, extension=None) -> str:
    """Loads a text file and returns the contents as a string."""
    if extension:
        file_path = add_extension(file_path, extension)
    file_path = get_full_path(file_path)
    with open(file_path, "r") as file:
        file_string = file.read()
    return file_string


def load_yaml_file(file_path) -> dict:
    file_path = add_extension(file_path, ".json")
    with open(file_path, "r") as file:
        yaml_data = yaml.safe_load(file)
    return yaml_data


def load_json_from_path(file_path: str) -> dict:
    """Read yaml file from `path`."""
    file_path = get_full_path(file_path)
    with open(file_path, mode="r", encoding="utf-8") as jfl:
        json_loaded = json.load(jfl)
    return json_loaded


def load_python_variable(path_relative):
    """Loads a python object stored in the output folder."""
    full_path = get_full_path(path_relative)
    with open(full_path, "rb") as file:
        obj = pickle.load(file)
    return obj


def get_full_path_and_create_dir(file_path):
    """Takes a path relative to the project folder and creates the full path.
    Also creates the specified directory if it does not exist."""
    path = get_full_path(file_path)
    create_directory(path)
    return path


def create_directory(path):
    """Creates the specified directory if it does not exist."""
    dirpath = os.path.dirname(path)
    if dirpath != "":
        os.makedirs(dirpath, exist_ok=True)


def get_full_path(path_relative):
    """Takes a path relative to the project root folder and produces the full path."""
    return os.path.join(ROOT_DIR, path_relative)


def dump_to_json(dump_dict, file_path):
    """Save thr `dump_dict` to the json file under the path given in relation to
    the root directory."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, mode="w", encoding="utf-8") as json_file:
        json.dump(dump_dict, json_file, sort_keys=False, indent=4)


def dump_chat_to_markdown(conversation: list[dict], file_path):
    """Dumps a chat to a textfile (.md or .txt) file for better readability."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, "w") as file:
        for message in conversation:
            formatted_message = f"\n{message['role']}: {message['content']}\n\n"
            file.write(formatted_message)


def dump_file(variable, file_path):
    """Dumps the variable to the specified location (relative to project
    root)."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, "w") as file:
        file.write(variable)


def dump_prompt_response_pair_to_md(prompt, output, dump_name):
    """Use to dump prompt and response into a single formatted .md (markdown)
    file for convenience and readability. Makes it easier to debug
    monitoring/overseer agents when they are behaving strangely."""
    dump_path = os.path.join(OVERSEER_DUMP_DIR, add_extension(dump_name, ".md"))
    full_path = get_full_path_and_create_dir(dump_path)
    dump_file(
        f"# PROMPT\n\n{prompt}\n\n\n\n# OUPUT\n\n{output}",
        full_path,
    )


def dump_current_conversation_to_json(
    conversation, filename="conversation", also_dump_formatted=False
):
    """Dumps the conversation to the conversation directory as a json file."""
    dump_to_json(conversation, f"{CONVERSATIONS_CURRENT_DIR}/{filename}.json")
    dump_to_json(conversation, f"{CHAT_DASHBOARD_DIR}/{filename}.json")
    if also_dump_formatted:
        dump_chat_to_markdown(conversation, f"{CHAT_DASHBOARD_DIR}/{filename}.md")


def dump_conversation(conversation: list, label: str = "conversation"):
    """Stores conversation in json format in conversations/raw and in formatted
    markdown file in conversations/formatted. Default name is `conversation`."""
    json_file_path = f"{CONVERSATIONS_RAW_DIR}/{label}.json"
    txt_file_path = f"{CONVERSATIONS_FORMATTED_DIR}/{label}.md"
    if conversation[-1]["content"] == "break":
        conversation = conversation[:-1]
    dump_to_json(conversation, json_file_path)
    LOGGER.info(f"Conversation stored in {json_file_path} and {txt_file_path}")


def dump_python_variable_to_file(variable, path_relative):
    """Save python object to pickle file. file_path_relative is file path
    relative to the output folder."""
    full_path = get_full_path_and_create_dir(path_relative)
    with open(full_path, "wb") as file:
        pickle.dump(variable, file)
        print(f'Object successfully saved to "{path_relative}"')


def update_field_value_in_json(file_path, field: str, new_value):
    """Updates the value of the specified field."""
    dictionary = load_json_from_path(file_path)
    dictionary[field] = new_value
    dump_to_json(dictionary, file_path)


def add_element_to_existing_json_file(dump_object, file_path):
    """Adds the object to the specified json file."""
    # Load or initiate JSON file
    if file_exists(file_path):
        json_list = load_json_from_path(file_path)
    else:
        # File does not exist: initiate empty JSON file
        dump_to_json([], file_path)
        json_list = []

    # Update JSON file
    if isinstance(dump_object, list):
        json_list += dump_object
    else:
        json_list.append(dump_object)
    dump_to_json(json_list, file_path)


def reset_json_file(file_path):
    """Resets json file to an empty list"""
    if file_exists(file_path):
        dump_to_json([], file_path)


def add_extension(path, extension):
    """Takes a path relative to the output folder and adds the specified
    extension (e.g., '.csv') IF the path has no extension."""
    if os.path.splitext(path)[-1] == "":
        path += extension
    return path


def remove_extension(path):
    """Removes the extension from the path or file"""
    path_without_extension, _ = os.path.splitext(path)
    return path_without_extension


def file_exists(file_path):
    """Checks if the file in the specified path exists."""
    if file_path is None:
        return False
    return os.path.isfile(get_full_path(file_path))


def get_sources_available_to_chatbot(chatbot_id: str) -> list[str]:
    """Gets a list of sources that the specified chatbot can request."""
    chatbot_subfolder = get_subfolder_of_assistant(chatbot_id)
    return get_file_names_in_directory(os.path.join(LIBRARY_DIR, chatbot_subfolder))


def get_source_content_and_path(chatbot_id: str, source_name: str) -> Tuple[str, str]:
    """Finds the content and path of a source. The filename of the prompt is
    used to find the subfolder that the source is expected to be located in.

    Returns: content, source_path"""
    source_path = get_path_to_source(source_name, chatbot_id)
    if source_path:
        content = load_textfile_as_string(source_path)
    else:
        content = None
    return content, source_path


def get_path_to_source(source_name: str, chatbot_id: str):
    """Finds the full path to the specified source."""
    bot_subfolder = get_subfolder_of_assistant(chatbot_id)
    sources_directory = os.path.join(LIBRARY_DIR, bot_subfolder)
    source_paths = get_file_paths_in_directory(sources_directory)
    source_names = [get_filename(source_path) for source_path in source_paths]
    if source_name in source_names:
        return source_paths[source_names.index(source_name)]
    else:
        return None


def get_subfolder_of_assistant(prompt_file_name: str):
    """Convention -> all directories that contain files associated with an
    assistant must consist of the following two components: the file-specific
    directory (such as media/images) and an assistant-specific path relative to
    the file-specific directory. This function takes the name of the assistant
    and inferrs the assistant-specific relative path. For example, if images are
    located in 'media/images/ex_bots/ex_bot_A/', then the assistant-specific
    path is 'ex_bots/ex_bot_A/'. Following this convention makes it easier to
    write prompts, since only the file name needs to be specified."""
    prompt_path = get_relative_path_of_prompt_file(prompt_file_name)

    # Get the directory name from the file path
    directory = os.path.dirname(prompt_path)
    # Split the directory path into components
    components = directory.split(os.path.sep)
    # Check if there is a subfolder (at least two components)
    if len(components) >= 2:
        subfolder = os.path.join(*components[1:])
        return subfolder
    else:
        return None  # Return None if there is no subfolder


def get_relative_path_of_prompt_file(prompt_file_name: str) -> str:
    """Identifies the prompts in the prompts directory for all, and finds the
    relative path for the file name provided. Note that prompts should have
    unique names for this to work well.
    """
    full_path = PROMPTS_DIR
    prompt_file_name = add_extension(prompt_file_name, ".md")
    matches = []
    # Iterate over the files in the directory
    for root, dirs, files in os.walk(full_path):
        if prompt_file_name in files:
            # File found, find the path relative to the root directory
            matches.append(
                os.path.relpath(os.path.join(root, prompt_file_name), start=ROOT_DIR)
            )

    if len(matches) == 0:
        print("No match found")
        return None
    elif len(matches) > 1:
        print("Warning: name of prompt file is not unique")
        return matches[0]
    if len(matches) == 1:
        return matches[0]


def get_file_paths_in_directory(directory_path):
    """Get the paths of all files within the specified directory and its
    subdirectories."""
    file_names = []
    full_directory_path = get_full_path(directory_path)
    for root, _, files in os.walk(full_directory_path):
        for file in files:
            file_names.append(os.path.join(root, file))
    return file_names


def get_filename(file_path, include_extension=False):
    """Gets the name of the file associated with the path."""
    file_name = os.path.basename(file_path)
    if include_extension:
        return file_name
    return os.path.splitext(file_name)[0]


def collect_prompts_in_dictionary(chatbot_id=None, directory_path=PROMPTS_DIR):
    """Finds paths for all files in directory and subdirectories, and creates a
    dictionary where the keys are file names and the values are file paths."""
    all_files = {}
    if chatbot_id:
        # Collect only prompts in subfolder associated with chatbot
        subfolder_path = get_subfolder_of_assistant(chatbot_id)
        directory_path = os.path.join(directory_path, subfolder_path)
    file_paths = get_file_paths_in_directory(directory_path)

    for file_path in file_paths:
        file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
        all_files[file_name_without_extension] = load_textfile_as_string(file_path)

    return all_files


def reset_files_that_track_cumulative_variables():
    """Resets files that track cumulative variables: chat_consumption.json and
    truncated_messages.json, which tracks the resource consumption (tokens and
    cost in kr) of a chat and removed messages respectively. This function is
    executed at the start of each new conversation.
    """
    dump_to_json(
        {"token_usage_total": 0, "chat_cost_kr_total": 0}, TOKEN_USAGE_DUMP_PATH
    )
    reset_json_file(DELETED_MESSAGES_DUMP_PATH)


def dump_copy_of_chat_info_to_results(dump_name: str):
    """Dumps information about the chat, including things like the
    conversation history (both json and markdown format) to
    /results/chat-dumps."""
    folder_to_copy = CHAT_DASHBOARD_DIR
    folder_destination = os.path.join(CHAT_DUMPS_DIR, dump_name)

    while os.path.exists(folder_destination):
        print(f"Folder {folder_destination} already exists.")
        response = get_input_from_command_line(
            f"Type 'y' to overwrite, or provide a new name:"
        )
        if response == "y":
            shutil.rmtree(folder_destination)
        else:
            folder_destination = response

    copy_and_dump_folder(folder_to_copy, folder_destination)

    # Provide brief description of context (why did you take this snapshot?)
    description = get_input_from_command_line("Description:")
    write_to_file(
        file_path=os.path.join(folder_destination, "comments.txt"), content=description
    )


def copy_and_dump_folder(folder_to_copy, folder_destination):
    """Copies a folder to a destination folder."""
    try:
        # Copy contents of source folder to destination folder
        shutil.copytree(
            folder_to_copy,
            folder_destination,
        )
        print(f"Successfully copied {folder_to_copy} to {folder_destination}")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_input_from_command_line(commandline_prompt):
    """Used to get input from the command line. Example of command-line question
    is 'Do you want to save this file (Y/N)?'"""
    return input(f"{commandline_prompt} ").strip().lower()


def write_to_file(file_path, content):
    """Write content to specified file path (relative to project
    root-folder)."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, "w") as file:
        file.write(content)


PROMPTS = collect_prompts_in_dictionary()

CONFIG = load_yaml_file(CONFIG_PATH)
OVERSEERS_CONFIG = load_yaml_file(OVERSEER_CONFIG_PATH)
CITATIONS = load_yaml_file(CITATIONS_PATH)
SETTINGS = load_yaml_file(SETTINGS_PATH)
SYSTEM_MESSAGES = load_yaml_file(SYSTEM_MESSAGES_PATH)
API_KEY = os.environ["AZURE_API_KEY"]

MODEL_TO_DEPLOYMENT_MAP = CONFIG["model_to_deployment_map"]
MODEL_ID = CONFIG["model_id"]
