# %%
import path_setup

from utils.backend import load_json_from_pathen

from functions import load_local_prompt

# %%

conversation = load_json_from_path(
    "results/chat-dumps/ai_thinks_it_is_socialisation_expert/conversation.json"
)
