"""General utilities."""

import re

RESET_COLOR = "\033[0m"
COLOR_TO_ANSI_MAP = {
    "grey": "\033[2;30m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "reset": "\033[0m",
}
ROLE_TO_ANSI_COLOR_MAP = {
    "assistant": COLOR_TO_ANSI_MAP["blue"],
    "user": COLOR_TO_ANSI_MAP["green"],
    "system": COLOR_TO_ANSI_MAP["grey"],
}


def silent_print(text: str):
    """Prints text in console in dark grey."""
    print(color_text(text, "grey"))


def color_text(text: str, color="grey"):
    """Returns text in the desired colour (grey, green, or blue)."""
    return f"{COLOR_TO_ANSI_MAP[color]}{text}{RESET_COLOR}"


def list_intersection(list_1, list_2) -> list:
    """Returns the elements that the lists have in common."""
    return list(set(list_1).intersection(set(list_2)))


def list_subtraction(list_1, list_2) -> list:
    """Returns "list_1 - list_2" (removes the elements of list 2 from list 1)."""
    return list(set(list_1).difference(set(list_2)))


def remove_syntax_from_message(message_content: str):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_code = re.sub(r"\¤:(.*?)\:¤", "", message_content, flags=re.DOTALL)
    # Remove surplus spaces
    message_cleaned = re.sub(r" {2,}(?![\n])", " ", message_no_code)
    # Remove leading space
    message_cleaned = message_cleaned.lstrip()
    if message_cleaned:
        message_cleaned = remove_superflous_linebreaks(message_cleaned)
    return message_cleaned


def message_is_intended_for_user(message: str) -> bool:
    """Checks if message is strictly for backend (starts and ends with code
    syntax) or intended to be read by user."""
    message = remove_superflous_linebreaks(message)
    message = message.replace(" ", "")
    if message[:2] == "¤:" and message[-2:] == ":¤":
        return False
    else:
        return True


def remove_quotes_and_backticks(input_str) -> str:
    """Removes quotation marks, `"` or `'`, from a string. Used for standardization
    in cases where bot is not always consistent, such as play_video("video_name") instead
    of play_video(video_name)."""
    pattern = r"[\'\"]"  # Pattern that recognizes single and double quotes
    result_str = re.sub(pattern, "", input_str)  # Remove single and double quotes
    result_str = result_str.replace("`", "")  # Remove backticks
    return result_str


# -- Dealing with linebreak characters --


def remove_superflous_linebreaks(message):
    """Removes all superflous linebreak characters that may arise after removing
    commands."""
    message_cleaned = remove_trailing_newlines(message)
    message_cleaned = remove_superflous_linebreaks_between_paragraphs(message_cleaned)
    return message_cleaned


def remove_trailing_newlines(text):
    """Removes trailing newline characters (may emerge after stripping away commands from
    bot messages)."""
    if len(text) == 1:
        return ""
    while text[-1] == " " or text[-1] == "\n":
        if text[-1] == " ":
            text = text.rstrip(" ")
        elif text[-1] == "\n":
            text = text.rstrip("\n")
    return text


def remove_superflous_linebreaks_between_paragraphs(text: str):
    """Replaces consecutive line breaks with just two line breaks (may emerge after
    ""stripping away commands from bot messages)."""
    cleaned_text = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned_text
