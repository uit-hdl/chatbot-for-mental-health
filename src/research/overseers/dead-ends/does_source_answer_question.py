"""It is not too bad, but not good enough to be used either. I may revesit this
idea in the future"""
# %%
import path_setup

from functions import run_experiment_general
from functions import load_local_prompt
from functions import load_test_cases
from functions import f_get_response_gpt35turbo
from functions import get_source

# %%
prompt_template_path_relative = "is_question_answerable"

prompt_variables = {
    "source": get_source("13_stigma"),
    "user_message": "How can I contribute to starting a social movement?"
}
prompt_variables["user_message"] = "How can I contribute to social change?"

run_experiment_general(
    prompt_variables=prompt_variables,
    n_exp=5,
    prompt_template_path_relative=prompt_template_path_relative,
)

prompt_variables["user_message"] = "Why does everyone seem so afraid of me?"
run_experiment_general(
    prompt_variables=prompt_variables,
    n_exp=5,
    prompt_template_path_relative=prompt_template_path_relative,
)

# %% Correcting message
from functions import print_wrap

prompt_template_path_relative = "add_disclaimer_to_message"

prompt_variables = {
    "warning_message": """Lean proteins or saturated fats are not specifically
                       mentioned in the source.""",
    "chatbot_message": """Indeed, choosing lean proteins can be a healthier
                       option as they contain less saturated fat. Lean proteins
                       include skinless poultry, fish, beans, lentils, and tofu.
                       Including these in your diet can help with maintaining a
                       healthy weight and reducing the risk of certain health
                       issues. It's still a good idea to talk to a healthcare
                       professional for individualized advice, especially in the
                       context of schizophrenia treatment and overall health
                       management."""
}

prompt_variables = {
    "warning_message": """The source does not advice or give tips on raising
                       awareness.""",
    "chatbot_message": """Raising awareness about alternative names for
                        schizophrenia can be done through open conversations and
                        sharing educational resources. (1.4) For example, you
                        could mention how Japan has adopted a new term,
                        'integration disorder', to better reflect the
                        condition's diverse symptoms. 

                        You can also support organizations or initiatives that
                        work towards similar goals, like patient groups in the
                        Netherlands advocating for a name change.

                        Would you like suggestions on organizations to connect
                        with or ways to engage with your community on this
                        topic?"""
}

results = run_experiment_general(
    prompt_variables=prompt_variables,
    n_exp=5,
    prompt_template_path_relative=prompt_template_path_relative,
)

print_wrap(results["raw_data"]["response_raw"][0])


