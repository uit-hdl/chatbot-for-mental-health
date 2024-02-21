import gradio as gr
import sys
import time


from console_chat import PROMPTS
from console_chat import initiate_prompt_engineered_ai_agent
from console_chat import remove_inactive_sources
from console_chat import generate_processed_bot_response
from console_chat import grab_last_assistant_response
from console_chat import overseer_check_of_source_fidelity
from console_chat import dump_current_conversation_to_json
from console_chat import direct_to_new_assistant
from console_chat import truncate_if_too_long
from utils.general import remove_syntax_from_message

DEEP_CHAT = []


def chat_with_bot_in_gradio_interface(chatbot_id, server_port=None):
    global DEEP_CHAT
    DEEP_CHAT = initiate_prompt_engineered_ai_agent(
        PROMPTS[chatbot_id],
    )

    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label="Your input")
        msg = gr.Textbox()

        msg.submit(respond, [msg, chatbot], [msg, chatbot])

    demo.launch(share=True, server_port=server_port)


def respond(user_message, surface_chat):
    global DEEP_CHAT
    DEEP_CHAT.append({"role": "user", "content": user_message})
    DEEP_CHAT, harvested_syntax = generate_processed_bot_response(DEEP_CHAT, chatbot_id)
    raw_response = grab_last_assistant_response(DEEP_CHAT)
    DEEP_CHAT = overseer_check_of_source_fidelity(
        DEEP_CHAT, harvested_syntax, chatbot_id
    )
    surface_response = remove_syntax_from_message(raw_response)

    surface_chat.append((user_message, surface_response))

    image_url_list = get_image_urls(harvested_syntax)
    for image_url in image_url_list:
        surface_chat.append((None, (image_url,)))

    dump_current_conversation_to_json(DEEP_CHAT)

    if harvested_syntax["referral"]:
        if harvested_syntax["referral"]["file_exists"]:
            DEEP_CHAT = direct_to_new_assistant(harvested_syntax["referral"])
            surface_response = grab_last_assistant_response(DEEP_CHAT)
            surface_chat.append((None, surface_response))

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
