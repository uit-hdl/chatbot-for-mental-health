"""Functions responsible for keeping the length of the conversation down by 
removing sources that are not being actively cited (used)."""
import numpy as np
import re
import logging

from utils.general import remove_superflous_linebreaks
from utils.backend import SETTINGS

logging.basicConfig(
    filename="chat-info/chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)


def remove_inactive_sources(conversation):
    """Scans the conversation for sources that have not been used recently
    (inactive sources) and removes them from the conversation (updates system messages).
    """
    inserted_sources = extract_sources_inserted_by_system(conversation)

    if inserted_sources:
        inactivity_times = get_inactivity_times_for_sources(
            conversation, inserted_sources
        )
        inactive_sources = get_inactive_sources(inserted_sources, inactivity_times)
        LOGGER.info(
            "Inserted sources: %s, Time of inactivity for each source:%s",
            inserted_sources,
            inactivity_times,
        )
        conversation = remove_inactive_sources_from_system_messages(
            conversation, inactive_sources
        )

    return conversation


def extract_sources_inserted_by_system(conversation):
    """Extracts name of sources cited and inserted into the chat by system in the
    form of system messages."""
    system_messages = [
        message["content"]
        for message in conversation[1:]
        if message["role"] == "system"
    ]
    sources = [
        extract_source_name(message)
        for message in system_messages
        if message.startswith("source")
    ]
    sources = remove_nones(sources)
    sources = list(set(sources))  # Remove repetitions
    return sources


def extract_source_name(message: str):
    """Takes a message/response and scans for the name of the source being used,
    if any."""
    pattern = r"source (\w+):"
    match = re.search(pattern, message)
    if match:
        return match.group(1)


def get_inactivity_times_for_sources(conversation, cited_sources):
    """For each source, calculates the number of responses since they were last referenced by
    system."""
    inactivity_times = [
        count_time_since_last_citation(conversation, source) for source in cited_sources
    ]
    inactivity_times = remove_nones(inactivity_times)
    return inactivity_times


def count_time_since_last_citation(conversation, source_name) -> list[int]:
    """Counts the number of responses since the source was last cited by the assistant. If cited
    in the last assistant response, inactivity_time == 0."""
    assistant_messages = [
        message["content"]
        for message in conversation
        if message["role"] == "assistant"
        and message_is_intended_for_user(message["content"])
    ]
    inactivity_time = 0
    # Look backwards in conversation to find how long ago since the source was last cited
    for i in range(1, len(assistant_messages) + 1):
        if source_name in assistant_messages[-i]:
            inactivity_time = i - 1
            break
    return inactivity_time


def get_inactive_sources(cited_sources, inactivity_times):
    """Identifies sources whose inactivity time exceeds inactivity threshold."""
    return np.array(cited_sources)[
        np.array(inactivity_times) >= SETTINGS["inactivity_threshold"]
    ]


def remove_inactive_sources_from_system_messages(
    conversation, inactive_sources: list[str]
):
    """Iterates over system messages, identifies the ones that contain information that is not being
    actively used (inactive source), and removes that information."""
    for message_index, message in enumerate(conversation):
        if message_index == 0:
            continue
        if message["role"] == "system":
            source_name = extract_source_name(message["content"])
            if source_name in inactive_sources:
                conversation[message_index][
                    "content"
                ] = "Inactive source removed due to not being actively cited."
                LOGGER.info("Inactive sources removed: %s", source_name)
    return conversation


def message_is_intended_for_user(message: str):
    """Used to check if a message contains text intended to be read by the user, or if it contains
    only syntax to be interpreted by the backend."""
    message = remove_superflous_linebreaks(message)
    message = message.replace(" ", "")
    if message[:2] == "¤:" and message[-2:] == ":¤":
        return False
    else:
        return True


def remove_nones(array: list):
    """Remove elements of list of type `None`"""
    return [x for x in array if x is not None]
