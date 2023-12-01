import yaml
import json
import os
import pathlib
import yaml
import datetime
from collections import namedtuple

ROOT_DIR = pathlib.Path(__file__).parents[2]
API_DIR = os.path.join(pathlib.Path(__file__).parents[3], "api-keys")
CONVERSATIONS_DIR = os.path.join(ROOT_DIR, "conversations")
CONVERSATIONS_CURRENT_DIR = os.path.join(ROOT_DIR, "conversations/current")
CONVERSATIONS_RAW_DIR = os.path.join(CONVERSATIONS_DIR, "raw")
CONVERSATIONS_FORMATTED_DIR = os.path.join(CONVERSATIONS_DIR, "formatted")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user-data")
IMAGES_DIR = os.path.join(ROOT_DIR, "images")
VIDEOS_DIR = os.path.join(ROOT_DIR, "videos")
LIBRARY_DIR = os.path.join(ROOT_DIR, "library")
PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts")

CONFIG_PATH = os.path.join(ROOT_DIR, "config/config.yaml")
API_KEY_PATH = os.path.join(API_DIR, "insomnia_bot_azure.yaml")
SETTINGS_PATH = os.path.join(ROOT_DIR, "config/settings.yaml")
URL_MAP_PATH = os.path.join(ROOT_DIR, "config/url.yaml")

CONVERSATION_BREAK_CUE = "Have a nice day!"
# Map showing location of files related to each type of command.
COMMAND_TO_DIR_MAP = {"request_knowledge": LIBRARY_DIR,
                      "display_image": IMAGES_DIR,
                      "play_video": VIDEOS_DIR}
# Extensions associated with the files of each type of command.
COMMAND_TO_EXTENSION_MAP = {"request_knowledge": ".md",
                            "display_image": ".png",
                            "play_video": ".mkv"}


def collect_prompts_in_dictionary(directory_path):
    """Finds paths for all files in directory and subdirectories, and creates a dictionary where the
    keys are file names and the values are file paths."""
    all_files = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_name_without_extension = os.path.splitext(file)[0]
            all_files[file_name_without_extension] = load_textfile_as_string(file_path)
    return all_files


def load_textfile_as_string(file_path):
    """Loads a text file and returns the contents as a string."""
    with open(file_path, 'r') as file:
        file_string = file.read()
    return file_string


def load_yaml_file(file_path, return_named_tuple=False):
    with open(file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    if return_named_tuple:
        return convert_dict_to_namedtuple(yaml_data)
    else:
        return yaml_data


def load_json_from_path(
        file_path: str,
) -> dict:
    """Read yaml file from `path`."""
    file_path = get_full_path(file_path)
    with open(file_path, mode="r", encoding="utf-8") as jfl:
        json_loaded = json.load(jfl)
    return json_loaded


def get_full_path_and_create_dir(file_path):
    """Takes a path relative to the output folder and creates the full path.
    Also creates the specified directory if it does not exist."""
    path = get_full_path(file_path)
    dirpath = os.path.dirname(path)
    if dirpath != '':
        os.makedirs(dirpath, exist_ok=True)
    return path


def get_full_path(path_relative):
    return os.path.join(ROOT_DIR, path_relative)


def dump_to_json(
        file,
        file_path,
) -> None:
    """Save thr `dump_dict` to the json file under the path given in relation to
    the root directory."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, mode="w", encoding='utf-8') as json_file:
        json.dump(
            file,
            json_file,
            sort_keys=True,
            indent=4)


def dump_current_conversation(conversation, filename="conversation"):
    file_path = f"{CONVERSATIONS_CURRENT_DIR}/{filename}.json"
    dump_to_json(conversation, file_path)


def dump_conversation_with_timestamp(conversation, label="conversation"):
    """Dumps the chatbot conversation in conversations/ with the date of the
    conversation in the name. The name can be given a more descriptive name
    through the 'label' argument."""
    # Get the current date and time
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{label}_{formatted_datetime}.txt"
    dump_conversation_to_textfile(filename, conversation)
    print(f"Conversation stored in {filename}")


def dump_conversation_to_textfile(filename, conversation):
    """Dumps a conversation to a textfile."""
    path_relative = f"{CONVERSATIONS_DIR}/formatted/{filename}"
    full_path = get_full_path_and_create_dir(path_relative)
    # Remove the initial prompt
    conversation = conversation[1:]
    with open(full_path, "w") as file:
        for message in conversation:
            role = message["role"]
            content = message["content"]
            file.write(f"{role.capitalize()}: {content}\n\n")


def convert_dict_to_namedtuple(dictionary: dict):
    """Converts a dictionary to a named tuple."""
    names = list(dictionary.keys())
    values = list(dictionary.values())
    named_tuple = namedtuple('named_tuple', names)
    return named_tuple(*values)

def add_extension(path, extension):
    """Takes a path relative to the output folder and adds the specified extension (e.g., '.csv') if the path has no extension."""
    if os.path.splitext(path)[-1] == '':
        path += extension
    return path


def get_filename(file_path, include_extension=False):
    file_name = os.path.basename(file_path)
    if include_extension:
        return file_name
    return os.path.splitext(file_name)[0]


def file_exists(file_path):
    return os.path.isfile(file_path)
    


PROMPTS = collect_prompts_in_dictionary(PROMPTS_DIR)

CONFIG = load_yaml_file(CONFIG_PATH)
SETTINGS = load_yaml_file(SETTINGS_PATH)
URL = load_yaml_file(URL_MAP_PATH)
API_KEY = load_yaml_file(API_KEY_PATH)["key"]

MODEL_ID = CONFIG["model_id"]