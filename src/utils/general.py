import tiktoken
import re
import textwrap
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from utils.backend import MODEL_ID
from utils.backend import CONVERSATIONS_RAW_DIR
from utils.backend import CONVERSATIONS_FORMATTED_DIR
from utils.backend import dump_to_json
from utils.backend import dump_conversation_to_textfile
from utils.backend import SETTINGS
from moviepy.editor import VideoFileClip

GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


def remove_nones(array: list):
    """Remove elements of list of type `None`"""
    return [x for x in array if x is not None]


def contains_only_whitespace(input_string):
    """Checks if a message is empty (can happen after syntax is removed)."""
    return all(char.isspace() or char == '' for char in input_string)

# ## Media ##
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


# ## Conversation processesing ##
def grab_last_response(conversation: list) -> str:
    """Grab the last response. Convenience function for better code-readability."""
    return conversation[-1]["content"]


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
        message_cleaned = remove_trailing_newlines(message_cleaned)
        message_cleaned = remove_excessive_linebreaks(message_cleaned)
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


def remove_excessive_linebreaks(text: str):
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
            formatted_message = f"\n{colour + role + RESET}: {formatted_paragraph}\n"
        else:
            formatted_message = f"{formatted_paragraph}\n"

        print(formatted_message)


def conversation_list_to_string(conversation: list) -> str:
    """Takes a conversation in the form of a list of dictionaries, and returns the
    whole conversation as a string."""
    return "\n".join([f"{d['role']}: {d['content']}" for d in conversation])
