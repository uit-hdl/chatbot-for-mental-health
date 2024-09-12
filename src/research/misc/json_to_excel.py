# %%
import path_setup
import os
from utils.backend import load_json_from_path
from utils.backend import ROOT_DIR
import pandas as pd


chat_paths = [
    "results/conversations/chat-dumps/start_of_dietary_expert/conversation.json",
    "results/conversations/chat-dumps/start_of_social_activist/conversation.json",
    "results/conversations/chat-dumps/start_of_social_expert/conversation.json",
]


for chat_path in chat_paths:
    chat = load_json_from_path(chat_path)
    df = pd.DataFrame(chat[1:])
    dump_path = os.path.join(ROOT_DIR, os.path.dirname(chat_path), "conversation.csv")
    df.to_csv(dump_path)
