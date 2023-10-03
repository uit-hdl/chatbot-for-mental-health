
import tiktoken
import re
import textwrap

from utils.backend import MODEL_ID
from moviepy.editor import VideoFileClip

def count_number_of_tokens(conversation):
    """Counts the number of tokens in a conversation. Uses token encoder
    https://github.com/openai/tiktoken/blob/main/tiktoken/model.py"""
    encoding = tiktoken.encoding_for_model(MODEL_ID)
    num_tokens = 0
    for message in conversation:
        # "User: assistant:" corresponds to 4 tokens
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
            formatted_message = f'\n{role}: {formatted_paragraph}\n'
        else:
            formatted_message = f'{formatted_paragraph}\n'

        print(formatted_message)


def play_video(video_file):
    video = VideoFileClip(video_file)
    video.preview()
    video.close()


def strip_trailing_linebreaks(message):
    """Strip trailing line breaks (newlines) from the end of a string."""
    return message.rstrip('\n')