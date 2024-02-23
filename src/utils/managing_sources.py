"""Functions responsible for keeping down the length of the conversation by 
removing sources that are not being actively cited/used."""

import numpy as np
import re

from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.general import message_is_intended_for_user


def remove_inactive_sources(conversation) -> list:
    """Scans the conversation for sources that have not been used recently
    (inactive sources) and removes them from the conversation (updates system messages).
    """
    inserted_sources = get_currently_inserted_sources(conversation)

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


def get_currently_inserted_sources(conversation):
    """Extracts name of sources cited and inserted into the chat by system in the
    form of system messages."""
    # Find system messages
    system_messages = [
        message["content"]
        for message in conversation[1:]
        if message["role"] == "system"
    ]
    sources = [
        extract_source_name_from_system_message(message)
        for message in system_messages
        if message.startswith("source")
    ]
    sources = remove_nones(sources)
    sources = list(set(sources))  # Remove repetitions
    return sources


def extract_source_name_from_system_message(message: str):
    """Takes a message/response and scans for the name of the source being used,
    if there are any."""
    pattern = r"source (\w+):"
    match = re.search(pattern, message)
    if match:
        return match.group(1)


def get_inactivity_times_for_sources(conversation, cited_sources):
    """For each source, calculates the number of responses since they were last referenced
    by system."""
    inactivity_times = [
        count_time_since_last_citation(conversation, source) for source in cited_sources
    ]
    inactivity_times = remove_nones(inactivity_times)
    return inactivity_times


def count_time_since_last_citation(conversation, source_name) -> list[int]:
    """Counts the number of responses since the source was last cited by the assistant. If
    cited in the last assistant response, inactivity_time == 0."""
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
) -> list:
    """Iterates over system messages, identifies the ones that contain information that is
    not being actively used (inactive source), and removes that information."""
    for message_index, message in enumerate(conversation):
        if message_index == 0:
            continue
        if message["role"] == "system":
            source_name = extract_source_name_from_system_message(message["content"])
            if source_name in inactive_sources:
                conversation[message_index][
                    "content"
                ] = "Inactive source removed due to not being actively cited."
                LOGGER.info("Inactive sources removed: %s", source_name)
    return conversation


def remove_nones(array: list):
    """Remove elements of list of type `None`"""
    return [x for x in array if x is not None]
