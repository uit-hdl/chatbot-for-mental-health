import gradio as gr
import sys

from console_chat import PROMPTS
from console_chat import initiate_conversation_with_prompt
from console_chat import remove_inactive_sources
from console_chat import respond_to_user
from console_chat import dump_current_conversation_to_json
from console_chat import direct_to_new_assistant
from console_chat import truncate_if_too_long
from utils.general import remove_syntax_from_message
from utils.backend import reset_files_that_track_cumulative_variables
from utils.chat_utilities import grab_last_assistant_response

DEEP_CHAT = []


def chat_with_bot_in_gradio_interface(chatbot_id, server_port=None):
    """Allows you to have a conversation with the chatbot in a gradio
    interface. racks two versions of the chat in parallell. DEEP_CHAT contains
    the raw conversation history, including system messages and raw chatbot
    responses which commands intended for backend interpretation. The
    surface_chat is the representation of the chat which is seen by the user and
    presented in the gradio interface."""
    global DEEP_CHAT

    def initiate_new_chat():
        reset_files_that_track_cumulative_variables()
        return initiate_conversation_with_prompt(
            PROMPTS[chatbot_id],
        )

    def respond(user_message, surface_chat):
        """Submit expects a function handle that takes only two arguments."""
        return create_response(user_message, surface_chat, chatbot_id)

    def reset_conversation():
        global DEEP_CHAT
        DEEP_CHAT = initiate_new_chat()
        return "", []

    DEEP_CHAT = initiate_new_chat()

    with gr.Blocks() as demo:
        surface_chat = gr.Chatbot(label="Your input")
        user_message = gr.Textbox(label="Enter message and hit enter")
        reset_button = gr.Button("Restart conversation")

        user_message.submit(
            respond,
            inputs=[user_message, surface_chat],
            outputs=[user_message, surface_chat],
        )
        reset_button.click(
            reset_conversation, inputs=[], outputs=[user_message, surface_chat]
        )

    demo.launch(share=True, server_port=server_port)


def create_response(user_message, surface_chat, chatbot_id):
    """Returns a tuple: ("", surface_chat). The surface chat has been updated
    with a response from the chatbot."""
    global DEEP_CHAT
    DEEP_CHAT.append({"role": "user", "content": user_message})
    DEEP_CHAT, harvested_syntax = respond_to_user(DEEP_CHAT, chatbot_id)
    raw_response = grab_last_assistant_response(DEEP_CHAT)
    surface_response = remove_syntax_from_message(raw_response)

    surface_chat.append((user_message, surface_response))

    image_url_list = get_image_urls(harvested_syntax)
    for image_url in image_url_list:
        surface_chat.append((None, (image_url,)))

    dump_current_conversation_to_json(DEEP_CHAT)

    if harvested_syntax["referral"]:
        if harvested_syntax["referral"]["file_exists"]:
            assistant_name = harvested_syntax["referral"]["name"]
            DEEP_CHAT = direct_to_new_assistant(assistant_name)
            surface_response = grab_last_assistant_response(DEEP_CHAT)
            surface_response_no_syntax = remove_syntax_from_message(surface_response)
            surface_chat.append((None, surface_response_no_syntax))

    DEEP_CHAT = remove_inactive_sources(DEEP_CHAT)
    DEEP_CHAT = truncate_if_too_long(DEEP_CHAT)

    return "", surface_chat


def get_image_urls(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url_list = []
    for image in harvested_syntax["images"]:
        image_url_list.append(image["path"])
    return image_url_list


if __name__ == "__main__":
    chatbot_id = "mental_health"
    if len(sys.argv) == 2:
        chatbot_id = sys.argv[1]
    if len(sys.argv) == 3:
        server_port = sys.argv[2]
    chat_with_bot_in_gradio_interface(chatbot_id)
