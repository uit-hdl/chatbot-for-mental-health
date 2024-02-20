"""Functions involved only in the process of presenting the assistant output in the console and
making it look nice to humans."""
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from moviepy.editor import VideoFileClip
import textwrap

from utils.backend import file_exists
from utils.backend import SETTINGS
from utils.chat_utilities import grab_last_assistant_response
from utils.general import remove_syntax_from_message
from utils.general import RESET_COLOR
from utils.general import ROLE_TO_ANSI_COLOR_MAP


def print_whole_conversation_with_backend_info(conversation):
    """Prints the entire conversation (excluding the prompt) in the console. Includes system
    messages, and does not remove bot syntax."""
    for message_dict in conversation[1:]:
        role = message_dict["role"]
        message_text = message_dict["content"].strip()
        message_with_role = prepend_role(message_text, role)
        message_wrapped = wrap_message(message_with_role)
        print(message_wrapped)


def prepend_role(message: str, role: str):
    """Prepends the role (with colour coding) to the beginning of the message."""
    colour_ansi = ROLE_TO_ANSI_COLOR_MAP[role]
    return f"\n{colour_ansi + role + RESET_COLOR}: {message}\n"


def wrap_message(message: str, line_length=80):
    """Wraps the message so that line lengths does not exceed a given maximum."""
    paragraphs = message.split("\n\n")
    wrapped_paragraphs = []

    for paragraph in paragraphs:
        lines = paragraph.split("\n")
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

        wrapped_paragraph = "\n".join(wrapped_paragraph)
        wrapped_paragraphs.append(wrapped_paragraph)

    wrapped_message = "\n\n".join(wrapped_paragraphs)

    return wrapped_message


def display_last_response(conversation):
    """Displays the last response of the conversation after stripping away syntax."""
    display_message_without_syntax(message_dict=conversation[-1])


def display_last_assistant_response(conversation):
    """Displays the last assistant response of the conversation after stripping away syntax."""
    display_message_without_syntax(
        message_dict={
            "role": "assistant",
            "content": grab_last_assistant_response(conversation),
        }
    )


def display_message_without_syntax(message_dict: dict):
    """Takes a message in dictionary form, removes the code syntax, and prints
    it in the console."""
    role = message_dict["role"].strip()
    message = message_dict["content"].strip()
    message_plain_text = remove_syntax_from_message(message)
    if not contains_only_whitespace(message_plain_text):
        message_with_role = prepend_role(message_plain_text, role)
        message_presentable = wrap_message(message_with_role)
        print(message_presentable)


def contains_only_whitespace(input_string) -> bool:
    """Checks if a message is empty (can happen after syntax is removed)."""
    return all(char.isspace() or char == "" for char in input_string)


def reprint_whole_conversation_without_syntax(
    conversation, include_system_messages=True
):
    """Reprints whole conversation (not including the prompt) without showing encoded commands."""
    for message in conversation[1:]:
        if not include_system_messages and message["role"] == "system":
            continue
        else:
            display_message_without_syntax(message)


def display_images(images: dict):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:play_video{<file>}:¤ (replace with `display_video` for
    video)."""
    for image in images:
        if file_exists(image["path"]):
            display_image(image["path"])
        else:
            print(image["path"])


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
    syntax used to display an image is ¤:play_video{<file>}:¤ (replace with `display_video` for
    video)."""
    for video in videos:
        if file_exists(video["path"]):
            play_video(video["path"])


def play_video(video_path: str):
    """Plays the video."""
    video = VideoFileClip(video_path)
    video.preview()
    video.close()
