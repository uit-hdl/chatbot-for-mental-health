from utils.general import remove_code_syntax_from_message


def remove_code_syntax_from_whole_conversation(conversation):
    """Removes code syntax from every message in the conversation."""
    for i, message in enumerate(conversation):
        if message["role"] == "Assistant":
            conversation[i]["content"] = remove_code_syntax_from_message(message)
    return conversation


def reconstruct_conversation_with_summary(system_messages, summary):
    """Reconstruct conversation after summarising the conversation."""
    conversation_reconstructed = system_messages
    conversation_reconstructed.append({"role": "system", "content": summary})
    return conversation_reconstructed


def separate_system_from_conversation(conversation):
    """Finds the system messages, and returns the conversation without system
    messages and a list of the system messages."""
    conversation_messages = [
        message for message in conversation if message["role"] != "system"
    ]
    system_messages = [
        message for message in conversation if message["role"] == "system"
    ]
    return conversation_messages, system_messages


def insert_information_in_prompt(prompt: str, info: str):
    """Inserts information contained in a dictionary format into the prompt."""
    return prompt.replace("<insert_info>", info)
