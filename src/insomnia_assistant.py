import openai
import ast
import re
import sys
import os
import time
import cv2

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pprint
from utils.general import remove_quotes_from_string
from utils.general import wrap_and_print_message
from utils.general import count_number_of_tokens
from utils.general import play_video
from utils.backend import MODEL_ID
from utils.backend import API_KEY
from utils.backend import PROMPTS
from utils.backend import USER_DATA_DIR
from utils.backend import SETTINGS
from utils.backend import IMAGES_DIR
from utils.backend import VIDEOS_DIR
from utils.backend import VIDEOS_DIR
from utils.backend import dump_dict_to_json
from utils.backend import dump_conversation_with_timestamp
from utils.backend import load_textfile_as_string

openai.api_key = API_KEY
BREAK_CONVERSATION_PROMPT = "break"
BREAK_CONVERSATION = False
REGENERATE = False
KNOWLEDGE = []

pp = pprint.PrettyPrinter(indent=10)


def sleep_diary_assistant_bot(chatbot_id="referral"):
    """Running this function starts a conversation with a tutorial bot that
    helps explain how a web-app (https://app.consensussleepdiary.com)
    functions. The web app is a free online app for collecting sleep data."""
    conversation = initiate_new_conversation(PROMPTS[chatbot_id])
    display_chatbot_response(conversation)

    while True:
        conversation = create_user_input(conversation)
        if conversation_is_ended():
            ask_user_if_conversation_should_be_stored(conversation)
            break
        conversation = generate_bot_response(conversation)

        chatbot_response = grab_last_response(conversation)
        json_data = scan_for_json_data(chatbot_response)
        extracted_code = scan_for_command(chatbot_response)
        knowledge = get_knowledge_if_requested(extracted_code)

        if knowledge:
            print(f"\nInserting requested information into conversation...")
            conversation = insert_knowledge_and_generate_response(conversation, knowledge)
            chatbot_response = grab_last_response(conversation)
            json_data = scan_for_json_data(chatbot_response)
            extracted_code = scan_for_command(chatbot_response)
    
        display_chatbot_response(conversation)
    
        if extracted_code:
            display_if_media(extracted_code)

        if json_data:
            json_dict = convert_json_string_to_dict(json_data)
            if json_dict["data_type"] == "referral_ticket":
                conversation = direct_to_new_assistant(json_ticket=json_dict)
                display_chatbot_response(conversation)
            else:
                general_info_dict = convert_json_string_to_dict(json_data)
                dump_dict_to_json(general_info_dict, f"{USER_DATA_DIR}/user_data.json")


def initiate_new_conversation(inital_prompt):
    """Initiates a conversation with the chat bot."""
    conversation = []
    conversation.append({'role': 'system', 'content': inital_prompt})
    conversation = generate_bot_response(conversation)
    return conversation


def generate_bot_response(conversation_log):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history."""
    response = openai.ChatCompletion.create(
        model=MODEL_ID,
        messages=conversation_log,
    )
    conversation_log.append({
        'role': response.choices[0].message.role,
        'content': response.choices[0].message.content.strip()
    })
    return conversation_log


def create_user_input(conversation):
    """Prompts user to input a prompt (the "question") in the command line."""
    global REGENERATE
    user_message = input("User: ")
    user_message = scan_user_message_for_commands(user_message, conversation)
    if REGENERATE:
        REGENERATE = False
        return conversation[:-1]
    conversation.append({"role": "user", "content": user_message})
    return conversation


def scan_user_message_for_commands(user_message, conversation):
    """Here I create an interpreter that scans for key phrases that
    allows me to execute commands from the command line during a chat and print useful
    information."""
    global BREAK_CONVERSATION, REGENERATE
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
                "regenerate"]
    
    while user_message in commands:
        if user_message == "break":
            BREAK_CONVERSATION = True
            break
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
            print(f"The last 3 messages are: \n\n{conversation[-3:]}")
        elif user_message == "print_chat":
            print(f"The whole conversation: \n\n{conversation}")
        elif user_message == "print_knowledge":
            print(f"Knowledge inserted is: \n{KNOWLEDGE}")
        elif user_message == "regenerate":
            REGENERATE = True
            break

        user_message = input("User: ")
    
    return user_message


def grab_last_response(conversation):
    return conversation[-1]["content"]


def scan_for_json_data(response: str):
    """Scans a string for '¤¤¤ <json contet> ¤¤¤'. If two '¤¤¤' are detected,
    returns the content between these substrings."""
    clean_text = response.replace("\n", "")
    json_string = re.findall(r'\¤¤¤(.*?)\¤¤¤', clean_text)
    if len(json_string) == 0:
        return None
    else:
        return json_string[0]


def scan_for_command(response: str):
    """Scans a string for '¤: <command> :¤', and extracts the command."""
    match = re.search(r'\¤:(.*?)\:¤', response, flags=re.DOTALL)
    if match:
        extracted_code = match.group(1)
        return extracted_code


def get_knowledge_if_requested(extracted_code):
    if extracted_code and "request_knowledge" in extracted_code:
        if "1password" in extracted_code:
            knowledge = load_textfile_as_string("library/1password.md")
        elif "google_password_manager" in extracted_code:
            knowledge = load_textfile_as_string("library/google_password_manager.md")
        KNOWLEDGE.append(knowledge)
        return knowledge


def insert_knowledge_and_generate_response(conversation, knowledge):
    """Inserts knowledge into the conversation, and lets bot produce a new
    response using that information."""
    conversation.append({'role': 'system', 'content': knowledge})
    conversation = generate_bot_response(conversation)
    return conversation


def display_if_media(extracted_code):
    """If extracted code contains command to display image, displays image. The
    syntax used to display an image is ¤:display_image{<file>}:¤ (replace with `display_video` for
    video)."""
    if "display_image" in extracted_code:
        file = re.search(r'\{(.*?)}', extracted_code)
        file = file.group(1)
        file = remove_quotes_from_string(file)
        file = os.path.join(IMAGES_DIR, file)
        img = mpimg.imread(file)
        plt.imshow(img)
        
        plt.gca().set_axis_off()  # Turn off the axes
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.margins(0, 0)
        plt.gca().yaxis.set_major_locator(plt.NullLocator())

        plt.show(block=False)
        plt.pause(SETTINGS["plot_duration"])
        plt.close()

    elif "play_video" in extracted_code:
        file = re.search(r'\{(.*?)}', extracted_code)
        file = file.group(1)
        file = remove_quotes_from_string(file)
        file = os.path.join(VIDEOS_DIR, file)
        play_video(file)


def direct_to_new_assistant(json_ticket):
    """Takes information about the users issue condensed into a json string, and
    redirects to the appropriate chatbot assistant."""
    prompt = get_prompt_for_assistant(json_ticket["assistant_id"])
    prompt_modified = insert_information_in_prompt(prompt, info=json_ticket["topic"])
    new_conversation = initiate_new_conversation(prompt_modified)
    print(f"User is redirected to assistant {json_ticket['assistant_id']}")
    return new_conversation


def display_chatbot_response(conversation):
    role = conversation[-1]['role'].strip()
    message = conversation[-1]['content'].strip()
    message_cleaned = remove_code_syntax_from_message(message)
    wrap_and_print_message(role, message_cleaned)


def remove_code_syntax_from_message(message):
    """Removes code syntax which is intended for backend purposes only."""
    message_no_json = re.sub(r'\¤¤¤(.*?)\¤¤¤', '', message, flags=re.DOTALL)
    message_no_code = re.sub(r'\¤:(.*?)\:¤', '', message_no_json)
    # Remove surplus spaces
    message_cleaned = re.sub(r' {2,}(?![\n])', ' ', message_no_code)
    return message_cleaned


def convert_json_string_to_dict(json_data: str):
    """Converts json file content extracted from a string into a dictionary."""
    return ast.literal_eval(json_data)


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


def ask_user_if_conversation_should_be_stored(conversation):
    """Asks the user in the console if he wants to store the conversation, and
    if so, how to name it."""
    store_conversation = input("Store conversation? (Y/N): ").strip().lower()
    if store_conversation == "y":
        label = input("Do you want to label the file? Hit enter for no label: ").strip().lower()
        if label == "":
            label = "conversation"
        label = label.replace(" ", "_")
        dump_conversation_with_timestamp(conversation, label)
    else:
        print("Conversation not stored")


def display_collected_data(collected_info=None):
    if collected_info:
        print(f"\nThe collected data is\n")
        print(f"{collected_info}")


if __name__  ==  "__main__":
    if len(sys.argv) > 1:
        argument = sys.argv[1]  # First command-line argument
    else:
        argument = "referral"
    if argument == "options":
        print(f"The assistant IDs are: \n{pp.pformat(list(PROMPTS.keys()))}")
    else:
        sleep_diary_assistant_bot(chatbot_id=argument)