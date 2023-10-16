import openai
import re
import sys
import os
import cv2

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pprint

from typing import List
from typing import Dict

from utils.general import wrap_and_print_message
from utils.general import count_number_of_tokens
from utils.general import play_video
from utils.general import conversation_list_to_string
from utils.general import extract_commands
from utils.general import scan_for_json_data
from utils.general import dump_conversation_to_textfile
from utils.backend import MODEL_ID
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import USER_DATA_DIR
from utils.backend import SETTINGS
from utils.backend import CONVERSATIONS_RAW_DIR
from utils.backend import CONVERSATIONS_FORMATTED_DIR
from utils.backend import dump_to_json
from utils.backend import load_textfile_as_string
from utils.backend import load_yaml_file
from utils.backend import get_filename

openai.api_key = API_KEY
BREAK_CONVERSATION_PROMPT = "break"
BREAK_CONVERSATION = False
REGENERATE = False
N_STRIP = 0
KNOWLEDGE = []

GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

pp = pprint.PrettyPrinter(indent=2, width=100)


def sleep_diary_assistant_bot(chatbot_id, chat_filepath=None):
    """Running this function starts a conversation with a tutorial bot that
    helps explain how a web-app (https://app.consensussleepdiary.com)
    functions. The web app is a free online app for collecting sleep data."""
    prompt = PROMPTS[chatbot_id]
    
    if chat_filepath is None:
        conversation = initiate_new_conversation(prompt)
        display_chatbot_response(conversation)
    else:
        conversation = continue_previous_conversation(chat_filepath, prompt)

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
    
        if commands:
            display_if_media(commands)

        if json_dictionaries:
            referral_ticket, sources = process_json_data(json_dictionaries)
            if referral_ticket:
                conversation = direct_to_new_assistant(referral_ticket)
                display_chatbot_response(conversation)
            if sources:
                print("sources found")
    
        if count_number_of_tokens(conversation) > SETTINGS["max_tokens_before_summary"]:
            conversation = summarize_conversation(conversation)
            conversation = generate_bot_response(conversation)


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
    response = openai.ChatCompletion.create(
        model=MODEL_ID,
        messages=conversation,
    )
    conversation.append({
        'role': response.choices[0].message.role,
        'content': response.choices[0].message.content.strip()
    })
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
                "history"]
    
    while user_message in commands:
        if user_message == "break":
            BREAK_CONVERSATION = True
            break
        # conversation_no_linebreaks = remove_linebreaks(conversation)
        elif user_message == "options":
            print(f"Possible commands are {commands}")
        elif user_message == "count_tokens":
            print(f"The number of tokens is: {count_number_of_tokens(conversation)}")
        elif user_message == "calc_cost":
            print(f"The number of tokens is: {count_number_of_tokens(conversation)*.0003246:.3} kr")
        elif user_message == "print_response":
            print(grab_last_response(conversation))
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
        elif "strip_last" in user_message:
            REGENERATE = True
            N_STRIP = int(user_message[-1])
            break
    
        user_message = input("user: ")
    
    return user_message


def grab_last_response(conversation):
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
                knowledge["content"] = load_textfile_as_string(command["file"])
                knowledge_list.append(knowledge)
    return knowledge_list


def insert_knowledge(conversation, knowledge_list):
    """Inserts knowledge into the conversation, and lets bot produce a new
    response using that information."""
    for knowledge in knowledge_list:
        print(f"\nInserting information `{get_filename(knowledge['file'])}` into conversation...")
        conversation.append({'role': 'system', 'content': knowledge["content"]})
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
    """The dictionaries can be of type user_data, """
    referral_ticket = None
    sources = None

    for dictionary in json_dictionaries:
        if "assistant_id" in dictionary:
            referral_ticket = dictionary
        elif "source" in dictionary:
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
    return scan_for_json_data(grab_last_response(conversation))


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
    message_no_json = re.sub(r'\¤¤¤(.*?)\¤¤¤', '', message, flags=re.DOTALL)
    message_no_code = re.sub(r'\¤:(.*?)\:¤', '', message_no_json)
    # Remove surplus spaces
    message_cleaned = re.sub(r' {2,}(?![\n])', ' ', message_no_code)
    return message_cleaned


def remove_code_syntax_from_whole_conversation(conversation):
    for i, message in enumerate(conversation):
        if message["role"] == "Assistant":
            conversation[i]["content"] = remove_code_syntax_from_message(message)
    return conversation


def separate_system_from_conversation(conversation):
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