"""Functions involved only in the process of presenting the assistant output in the console and
making it look nice to humans."""
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from moviepy.editor import VideoFileClip
import re
import textwrap

from utils.backend import file_exists
from utils.backend import SETTINGS
from utils.general import remove_superflous_linebreaks

# Chat colors
GREY = "\033[2;30m"  # info messages
GREEN = "\033[92m"  # user
BLUE = "\033[94m"  # assistant
RESET_COLOR = "\033[0m"


def print_whole_conversation(conversation):
    """Prints the entire conversation (excluding the prompt) in the console."""
    for message in conversation[1:]:
        role = message["role"]
        message = message["content"].strip()
        wrap_and_print_message(role, message)


def wrap_and_print_message(role, message, line_length=80):
    """Prints message, and ensures that line lengths does not exceed a given maximum."""
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


def remove_code_syntax_from_message(message: str):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_code = re.sub(r"\¤:(.*?)\:¤", "", message, flags=re.DOTALL)
    # Remove surplus spaces
    message_cleaned = re.sub(r" {2,}(?![\n])", " ", message_no_code)
    if message_cleaned:
        message_cleaned = remove_superflous_linebreaks(message_cleaned)
    return message_cleaned


def display_last_response(conversation):
    """Displays the last response of the conversation (removes syntax)."""
    display_message_without_syntax(message_dict=conversation[-1])


def display_message_without_syntax(message_dict: dict):
    """Takes a message in dictionary form, removes the code syntax, and prints
    it in the console."""
    role = message_dict["role"].strip()
    message = message_dict["content"].strip()
    message_cleaned = remove_code_syntax_from_message(message)
    if not contains_only_whitespace(message_cleaned):
        wrap_and_print_message(role, message_cleaned)


def contains_only_whitespace(input_string) -> bool:
    """Checks if a message is empty (can happen after syntax is removed)."""
    return all(char.isspace() or char == "" for char in input_string)


def reprint_whole_conversation_without_syntax(
    conversation, include_system_messages=True
):
    """Reprints whole conversation (not including the prompt)."""
    for message in conversation[1:]:
        if not include_system_messages and message["role"] == "system":
            continue
        else:
            display_message_without_syntax(message)


def display_images(images: dict):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:play_video{<file>}:¤ (replace with
    `display_video` for video)."""
    for image in images:
        if file_exists(image["path"]):
            display_image(image["path"])


def display_image(image_path: str):
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


def play_videos(videos: dict):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:play_video{<file>}:¤ (replace with
    `display_video` for video)."""
    for video in videos:
        if file_exists(video["path"]):
            play_video(video["path"])


def play_video(video_path: str):
    """Plays the video."""
    video = VideoFileClip(video_path)
    video.preview()
    video.close()
