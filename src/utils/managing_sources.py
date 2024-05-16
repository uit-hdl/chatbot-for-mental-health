"""Functions responsible for managing sources that have been inserted into the
conversation and removing inactive sources that are not being actively cited."""

import numpy as np
import re

from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.general import message_is_intended_for_user
from utils.general import silent_print


def remove_inactive_sources(conversation) -> list:
    """Scans the conversation for sources that have not been used recently
    (inactive sources) and removes them from the conversation (updates system messages).
    """
    inserted_sources = get_names_of_currently_inserted_sources(conversation)

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
        conversation = remove_inserted_sources_from_conversation(
            conversation, inactive_sources
        )

    return conversation


def get_names_of_currently_inserted_sources(conversation):
    """Extracts name of sources cited and inserted into the chat by system in
    the form of system messages."""
    source_indices = get_index_of_currently_inserted_sources(conversation)
    # Get message dictionaries of inserted sources
    inserted_sources = [conversation[index] for index in source_indices]
    # Get source name for each message dictionary
    source_names = [
        extract_source_name_from_system_message(message["content"])
        for message in inserted_sources
    ]
    source_names = remove_nones(source_names)
    # Remove repetitions
    source_names = list(set(source_names))
    return source_names


def get_index_of_currently_inserted_sources(conversation) -> list[int]:
    """Gets the location of the sources that have been insrted in the chat."""
    source_indices = [
        index
        for index, msg in enumerate(conversation)
        if msg["role"] == "system" and msg["content"].startswith("source")
    ]
    return source_indices


def extract_source_name_from_system_message(message: str):
    """Takes a message/response and scans for the name of the source being used,
    if there are any."""
    pattern = r"source (\w+):"
    match = re.search(pattern, message)
    if match:
        return match.group(1)


def get_inactivity_times_for_sources(
    conversation, inserted_sources: list[str]
) -> list[int]:
    """For each source (name) in list of sources, calculates the number of
    responses since they were last referenced by system."""
    inactivity_times = [
        count_time_since_last_citation(conversation, source)
        for source in inserted_sources
    ]
    inactivity_times = remove_nones(inactivity_times)
    return inactivity_times


def count_time_since_last_citation(conversation, source_name: str) -> list[int]:
    """Returns list with number of responses since each source was last cited by
    the assistant. If cited in the last assistant response, inactivity_time ==
    0."""
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


def remove_inserted_sources_from_conversation(
    conversation,
    sources_to_remove: list[str],
    replacement_message="Source removed due to inactivity.",
) -> list:
    """Iterates over system messages, identifies the ones are in the provided
    list of sources to remove, removes them, and replaces them with a
    substitution message."""
    for message_index, message in enumerate(conversation):
        if message_index == 0:
            # Do not remove initial prompt
            continue
        if message["role"] == "system":
            source_name = extract_source_name_from_system_message(message["content"])
            if source_name in sources_to_remove:
                conversation[message_index]["content"] = replacement_message
                LOGGER.info("Inactive sources removed: %s", source_name)
    return conversation


def remove_nones(array: list):
    """Remove elements of list of type `None`"""
    return [x for x in array if x is not None]


def insert_requested_knowledge(conversation, knowledge_requests: list[dict]):
    """Goes through a list of knowledge requests (dictionaries with `name` and `content`)
    and inserts the source content into the chat if they are not already in the chat.
    First checks if there sources are already in the chat."""
    inserted_sources = get_names_of_currently_inserted_sources(conversation)

    for knowledge_request in knowledge_requests:
        source_name = knowledge_request["name"]
        source_content = knowledge_request["content"]
        if source_content:
            # Non-empty source content means that the source exists
            # Check if requested source is in chat already
            if source_name in inserted_sources:
                message = f"The requested source {source_name} is already available in the chat!"
                LOGGER.info(message)
            else:
                # Put source content in system message
                message = f"source {source_name}: {source_content}"
                LOGGER.info("Source %s inserted in conversation.", source_name)
                if SETTINGS["print_knowledge_requests"]:
                    silent_print(f"Source {source_name} inserted in conversation.")

            # Insert system message into conversation
            conversation.append({"role": "system", "content": message})

    return conversation
