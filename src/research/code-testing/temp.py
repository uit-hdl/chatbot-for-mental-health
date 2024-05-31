import path_setup

import gradio as gr
from gradio_chat_with_history_and_images import chat_with_bot_in_gradio_interface

def converse(x, y, z):
    return z


def reset(z):
    return [], []


def greet(name):
    return f"Hello, {name}!"


with gr.Blocks() as demo:
    input = gr.Textbox()
    output = gr.Textbox()

    botton1 = gr.Button("My first button")

    botton1.click(fn=greet, inputs=input, outputs=output)

demo.launch()
