"""Functions involved in the process of presenting the chat in the console and making it look nice
to humans."""
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from moviepy.editor import VideoFileClip

from utils.general import remove_code_syntax_from_message
from utils.general import contains_only_whitespace
from utils.general import wrap_and_print_message
from utils.backend import file_exists
from utils.backend import SETTINGS


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
