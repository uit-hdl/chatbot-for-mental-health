import openai
import re
import sys
import os
import cv2
import time
import logging

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pprint

from typing import List
from typing import Dict

from utils.general import wrap_and_print_message
from utils.general import count_tokens
from utils.general import play_video
from utils.general import conversation_list_to_string
from utils.general import extract_commands
from utils.general import scan_for_json_data
from utils.general import dump_conversation_to_textfile
from utils.general import remove_none
from utils.general import count_tokens_used_to_create_last_response
from utils.backend import MODEL_ID
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import USER_DATA_DIR
from utils.backend import SETTINGS
from utils.backend import CONFIG
from utils.backend import CONVERSATIONS_RAW_DIR
from utils.backend import CONVERSATIONS_FORMATTED_DIR
from utils.backend import dump_to_json
from utils.backend import dump_current_conversation
from utils.backend import load_textfile_as_string
from utils.backend import load_yaml_file
from utils.backend import get_filename
from utils.backend import file_exists

openai.api_key = API_KEY
openai.api_type = CONFIG["api_type"]
openai.api_base = CONFIG["api_base"]
openai.api_version = CONFIG["api_version"]

BREAK_CONVERSATION_PROMPT = "break"
BREAK_CONVERSATION = False
REGENERATE = False
N_STRIP = 0
INACTIVITY_THRESHOLD = 1
VERBOSE = 1
KNOWLEDGE = []
N_TOKENS_USED = []
RESPONSE_TIMES = []

GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

pp = pprint.PrettyPrinter(indent=2, width=100)
logging.basicConfig(filename='experiment.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')



def sleep_diary_assistant_bot(chatbot_id, chat_filepath=None):
    """Running this function starts a conversation with a tutorial bot that
    helps explain how a web-app (https://app.consensussleepdiary.com)
    functions. The web app is a free online app for collecting sleep data."""
    prompt = PROMPTS[chatbot_id]

    if chat_filepath:
        conversation = continue_previous_conversation(chat_filepath, prompt)
    else:
        conversation = initiate_new_conversation(prompt)
        display_chatbot_response(conversation)

    while True:
        conversation = create_user_input(conversation)
        if conversation_is_ended():
            offer_to_store_conversation(conversation)
            break
        conversation = generate_bot_response(conversation)
        commands, knowledge_requests = process_syntax_of_bot_response(conversation)

        while knowledge_requests:
            conversation = insert_knowledge(conversation, knowledge_requests)
            conversation = generate_bot_response(conversation)
            commands, knowledge_requests = process_syntax_of_bot_response(conversation)

        json_dictionaries = scan_last_response_for_json_data(conversation)
        display_chatbot_response(conversation)
        dump_current_conversation(conversation)

        if commands:
            display_if_media(commands)

        if json_dictionaries:
            referral_ticket, sources = process_json_data(json_dictionaries)
            if referral_ticket:
                conversation = direct_to_new_assistant(referral_ticket)
                display_chatbot_response(conversation)
                continue

        if count_tokens(conversation) > SETTINGS["max_tokens_before_summary"]:
            conversation = summarize_conversation(conversation)
            conversation = generate_bot_response(conversation)
        
        conversation = remove_inactive_sources(conversation)


def initiate_new_conversation(inital_prompt):
    """Initiates a conversation with the chat bot."""
    conversation = []
    conversation.append({'role': 'system', 'content': inital_prompt})
    conversation = generate_bot_response(conversation)
    return conversation


def continue_previous_conversation(chat_filepath, prompt):
    """Inserts the current prompt into a previous conversation that was discontinued."""
    conversation = load_yaml_file(chat_filepath)
    # Replace original prompt with requested prompt
    conversation[0] = {'role': 'system', 'content': prompt}
    print_whole_conversation(conversation)
    return conversation


def generate_bot_response(conversation):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history."""
    start_time = time.time()
    response = openai.ChatCompletion.create(
        model=CONFIG["model_id"],
        messages=conversation,
        engine=CONFIG["deployment_name"],
    )
    end_time = time.time()
    conversation.append({
        'role': response.choices[0].message.role,
        'content': response.choices[0].message.content.strip()
    })
    RESPONSE_TIMES.append(end_time - start_time)
    N_TOKENS_USED.append(count_tokens_used_to_create_last_response(conversation))
    return conversation


def create_user_input(conversation):
    """Prompts user to input a prompt (the "question") in the command line."""
    global REGENERATE, N_STRIP
    user_message = input(GREEN + "user" + RESET  + ": ")
    user_message = scan_user_message_for_commands(user_message, conversation)
    if REGENERATE:
        REGENERATE = False
        return conversation[:-N_STRIP]
    conversation.append({"role": "user", "content": user_message})
    return conversation


def scan_user_message_for_commands(user_message, conversation):
    """Here I create an interpreter that scans for key phrases that
    allows me to execute commands from the command line during a chat and print useful
    information."""
    global BREAK_CONVERSATION, REGENERATE, SUMMARY, N_STRIP
    commands = ["options", 
                "break",
                "count_tokens", 
                "count_words",
                "calc_cost", 
                "print_response",
                "print_response_times",
                "print_last3",
                "print_chat",
                "print_prompt",
                "print_knowledge",
                "print_summary",
                "strip_last1",
                "strip_last2",
                "strip_last3",
                "strip_last4",
                "strip_last5",
                "clear",
                "history",
                "log"]
    
    while user_message in commands:
        if user_message == "break":
            BREAK_CONVERSATION = True
            break
        # conversation_no_linebreaks = remove_linebreaks(conversation)
        elif user_message == "options":
            print(f"Possible commands are {commands}")
        elif user_message == "count_tokens":
            print(f"The number of tokens used is: {np.sum(np.array(N_TOKENS_USED))}")
        elif user_message == "calc_cost":
            print(f"The number of tokens is: {count_tokens(conversation)*.0003246:.3} kr")
        elif user_message == "print_response":
            print(grab_last_response(conversation))
        elif user_message == "print_response_times":
            print(f"Response_times:{RESPONSE_TIMES} ({np.sum(np.array(RESPONSE_TIMES)):.4}s total)")
        elif user_message == "print_prompt":
            print(f"The system prompt is: \n\n{conversation[0]['content']}")
        elif user_message == "print_last3":
            print("\n*** Printing last 3 messages... ***")
            print(f"The last 3 messages are: \n\n{conversation[-3:]}")
            print("*** End of printing last 3 messages ***\n")
        elif user_message == "print_chat":
            print("\n*** Printing whole chat... ***")
            print_whole_conversation(conversation)
            print("*** End of printing whole chat ***\n")
        elif user_message == "print_knowledge":
            print(f"Knowledge inserted is: \n{KNOWLEDGE}")
        elif user_message == "print_summary":
            print(f"\n{SUMMARY}")
        elif user_message == "clear":
            os.system("clear")
        elif user_message == "history":
            print_whole_conversation(conversation)
        elif user_message == "log":
            response_times_rounded = [np.round(t, 4) for t in RESPONSE_TIMES]
            time_total = np.sum(np.array(RESPONSE_TIMES))
            tokens_total = np.sum(np.array(N_TOKENS_USED))
            logging.info(f"\nResponse times: {response_times_rounded} ({time_total:.4}s total)")
            logging.info(f"Tokens used: {N_TOKENS_USED} ({tokens_total} total)")
        elif "strip_last" in user_message:
            REGENERATE = True
            N_STRIP = int(user_message[-1])
            break
    
        user_message = input("user: ")
    
    return user_message


def grab_last_response(conversation):
    """Grab the last response. Convenience function for better code-readability."""
    return conversation[-1]["content"]


def process_syntax_of_bot_response(conversation):
    """Scans the response for symbols ¤: and :¤, and extracts the name of the commands, the
    file-arguments of the commands. Returns two lists of dictionaries."""
    chatbot_response = grab_last_response(conversation)
    commands = extract_commands(chatbot_response)
    knowledge_requests = check_for_knowledge_requests(commands)
    return commands, knowledge_requests


def check_for_knowledge_requests(commands: List[Dict]) -> List[Dict]:
    """Fetches the text associated with each knowledge request command."""
    knowledge_list = []
    if commands:
        for command in commands:
            if command["type"] == "request_knowledge":
                knowledge = {}
                knowledge["file"] = command["file"]
                if file_exists(knowledge["file"]):
                    knowledge["content"] = load_textfile_as_string(command["file"])
                else:
                    knowledge["content"] = None
                knowledge_list.append(knowledge)
    return knowledge_list


def insert_knowledge(conversation, knowledge_list):
    """Inserts knowledge into the conversation, and lets bot produce a new
    response using that information."""
    for knowledge in knowledge_list:
        source_name = get_filename(knowledge['file'])
        if file_exists(knowledge['file']):
            print(f"\nInserting information `{source_name}` into conversation...")
            message = f"source {source_name}: {knowledge['content']}"
        else:
            message = "Requested source not available."
        conversation.append({'role': 'system', 'content': message})
    return conversation


def display_if_media(commands: list):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:display_image{<file>}:¤ (replace with `display_video` for
    video)."""
    for command in commands:
        if command["type"] == "display_image":
            img = mpimg.imread(command["file"])
            plt.imshow(img)
            plt.gca().set_axis_off()  # Turn off the axes
            plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            plt.margins(0, 0)
            plt.gca().yaxis.set_major_locator(plt.NullLocator())

            plt.show(block=False)
            plt.pause(SETTINGS["plot_duration"])
            plt.close()

        elif command["type"] == "play_video":
            play_video(command["file"])


def process_json_data(json_dictionaries):
    """Takes a list of json dictionaries, infers the type of data they contain, and handles them
    accordingly. Datatypes can be referrals, sources, or data describing the user."""
    referral_ticket = None
    sources = None
    for dictionary in json_dictionaries:
        if "assistant_id" in dictionary:
            referral_ticket = dictionary
        elif "sources" in dictionary:
            sources = dictionary
        else:
            dump_to_json(dictionary, f"{USER_DATA_DIR}/user_data.json")

    return referral_ticket, sources


def direct_to_new_assistant(json_ticket):
    """Takes information about the users issue condensed into a json string, and
    redirects to the appropriate chatbot assistant."""
    prompt = get_prompt_for_assistant(json_ticket["assistant_id"])
    prompt_modified = insert_information_in_prompt(prompt, info=json_ticket["topic"])
    new_conversation = initiate_new_conversation(prompt_modified)
    print(f"user is redirected to assistant {json_ticket['assistant_id']}")
    return new_conversation


def scan_last_response_for_json_data(conversation):
    """Grabs last resonse and scans for json data nested in the response."""
    return scan_for_json_data(grab_last_response(conversation))


def remove_inactive_sources(conversation):
    """Scans the conversation for sources that have not been used recently."""
    system_messages = [message["content"] for message in conversation[1:] if message["role"]=="system"]
    sources = [extract_source_name(message) for message in system_messages if message.startswith("source")]
    sources = remove_none(sources)
    if sources:
        
        inactivity_times = [count_time_since_last_citation(conversation, source) for source in sources]
        inactivity_times = remove_none(inactivity_times)
        print(f"\nInactivity times: {inactivity_times}\n")
        print(f"\nsources: {sources}\n")
        sources_to_remove = np.array(sources)[np.array(inactivity_times) >= INACTIVITY_THRESHOLD]
        
        for index, message in enumerate(conversation):
            if index == 0:
                # Skip prompt
                continue
            if message["role"] == "system":
                source_name = extract_source_name(message["content"])
                if source_name in sources_to_remove:
                    conversation[index]["content"] = "inactive source removed"
                    if VERBOSE==2:
                        print(f"Removing inactive source {source_name}\n")

    return conversation


def extract_source_name(message):
    pattern = r'source (\w+):'
    match = re.search(pattern, message)
    if match:
        return match.group(1)


def count_time_since_last_citation(conversation, source_name):
    """Counts the number of responses since the source was last cited. If cited in the last
    response, this value is 0."""
    assistant_messages = [message["content"] for message in conversation if message["role"]=="assistant"]
    inactivity_time = 0
    for i in range(1, len(assistant_messages) + 1):
        if source_name in assistant_messages[-i]:
            inactivity_time = i - 1
            break
    return inactivity_time


def summarize_conversation(conversation):
    global SUMMARY
    conversation_messages, system_messages = separate_system_from_conversation(conversation)
    conversation_messages = remove_code_syntax_from_whole_conversation(conversation_messages)
    conversation_string = conversation_list_to_string(conversation_messages)
    prompt_summary_bot = insert_information_in_prompt(prompt=PROMPTS["summary_bot"], info=conversation_string)
    conversation_with_summary_bot = initiate_new_conversation(prompt_summary_bot)
    SUMMARY = grab_last_response(conversation_with_summary_bot)
    conversation_summarized = reconstruct_conversation_with_summary(system_messages, SUMMARY)
    return conversation_summarized


def reconstruct_conversation_with_summary(system_messages, summary):
    conversation_reconstructed = system_messages
    conversation_reconstructed.append({'role': 'system', 'content': summary})
    return conversation_reconstructed


def display_chatbot_response(conversation):
    role = conversation[-1]['role'].strip()
    message = conversation[-1]['content'].strip()
    message_cleaned = remove_code_syntax_from_message(message)
    wrap_and_print_message(role, message_cleaned)


def print_whole_conversation(conversation):
    """Prints the entire conversation (excluding the prompt) in the console."""
    for message in conversation[1:]:
        role = message["role"]
        message = message['content'].strip()
        wrap_and_print_message(role, message)


def remove_code_syntax_from_message(message):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_json = re.sub(r'\¤¤(.*?)\¤¤', '', message, flags=re.DOTALL)
    message_no_code = re.sub(r'\¤:(.*?)\:¤', '', message_no_json)
    # Remove surplus spaces
    message_cleaned = re.sub(r' {2,}(?![\n])', ' ', message_no_code)
    return message_cleaned


def remove_code_syntax_from_whole_conversation(conversation):
    """Removes code syntax from every message in the conversation."""
    for i, message in enumerate(conversation):
        if message["role"] == "Assistant":
            conversation[i]["content"] = remove_code_syntax_from_message(message)
    return conversation


def separate_system_from_conversation(conversation):
    """Finds the system messages, and returns the conversation without system messages and a list of
    the system messages."""
    conversation_messages = [message for message in conversation if message["role"] != "system"]
    system_messages = [message for message in conversation if message["role"] == "system"]
    return conversation_messages, system_messages


def get_prompt_for_assistant(assistant_id):
    return PROMPTS[assistant_id]


def insert_information_in_prompt(prompt: str, info: str):
    """Inserts information contained in a dictionary format into the prompt."""
    return prompt.replace("<insert_info>", info)


def conversation_is_ended():
    """Checks if conversation has ended by scanning for a predefined substring
    that acts as a cue to end the conversation."""
    if BREAK_CONVERSATION:
        return True
    else:
        return False


def offer_to_store_conversation(conversation):
    """Asks the user in the console if he wants to store the conversation, and
    if so, how to name it."""
    store_conversation = input("Store conversation? (Y/N): ").strip().lower()
    if store_conversation == "y":
        label = input("File name (hit enter for default): ").strip().lower()
        if label == "":
            label = "conversation"
        json_file_path = f"{CONVERSATIONS_RAW_DIR}/{label}.json"
        txt_file_path = f"{CONVERSATIONS_FORMATTED_DIR}/{label}.md"
        if grab_last_response(conversation) == "break":
            # Remove break
            conversation = conversation[:-1]
        dump_to_json(conversation, json_file_path)
        dump_conversation_to_textfile(conversation, txt_file_path)
        print(f"Conversation stored in {json_file_path} and {txt_file_path}")
    else:
        print("Conversation not stored")


def display_collected_data(collected_info=None):
    if collected_info:
        print(f"\nThe collected data is\n")
        print(f"{collected_info}")


if __name__  ==  "__main__":
    arg1 = "referral"
    arg2 = None

    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 == "":
            arg1 = "referral"
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        
    if arg1 == "options":
        print(f"The assistant IDs are: \n{pp.pformat(list(PROMPTS.keys()))}")
    else:
        sleep_diary_assistant_bot(chatbot_id=arg1, chat_filepath=arg2)