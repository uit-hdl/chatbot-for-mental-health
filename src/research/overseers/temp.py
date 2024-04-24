import path_setup

from utils.backend import load_json_from_path
from utils.process_syntax import extract_command_names_and_arguments
from utils.process_syntax import extract_command_names_and_arguments
from utils.overseers import extract_command_names_and_arguments
from utils.backend import convert_json_string_to_dict



response = """¤:provide_feedback({"evaluation": "REJECTED", "message_to_bot": "Stick to referring users to the manual or professionals, avoid giving direct advice."}):¤"""

response = """¤:provide_feedback({"evaluation": "REJECTED", "message_to_bot": "The source does not discuss mirroring or non-verbal communication tips."}):¤"""

_, overseer_evaluation = extract_command_names_and_arguments(response)
if overseer_evaluation:
    evaluation_dict = convert_json_string_to_dict(overseer_evaluation[0])
else:
    evaluation_dict = None
