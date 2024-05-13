"""In this script I develop the AI agent whose responsibility is to modify the chatbots messages 
so that it complies with the warning message of system."""
# %%
import path_setup

from utils_testing_judges import run_experiment_for_test_case
from utils_testing_judges import run_experiment_general
from utils_testing_judges import load_local_prompt_template
from utils_testing_judges import load_test_cases
from utils_testing_judges import gen_llm_response
from utils_testing_judges import get_source
from utils_testing_judges import fill_in_variables_in_prompt_template
from utils_general import dump_to_json_locally
from utils_general import print_wrap

# %%
prompt_template = load_local_prompt_template(
    "files/prompt-templates/other/kill_topic.md"
)
user_message = "And laughing at their joke, that is also appreciated right?"

chatbot_message = "Yes, laughing at someone's jokes can be a sign that you appreciate their humor and are engaged in the interaction. It's a natural way to show interest and can help create a more relaxed and enjoyable social atmosphere. Keep in mind that social cues like laughter should be genuine, as authenticity often helps build stronger connections with others."

system_message = "Your message about laughter and social cues goes beyond what's provided in the source. Focus on social strategies discussed in the manual."

prompt_variables = {
    "user_message": user_message,
    "chatbot_message": chatbot_message,
    "system_message": system_message,
}

prompt_filled = fill_in_variables_in_prompt_template(prompt_template, prompt_variables)
response = gen_llm_response(prompt_filled)
response = f'¤:cite(["no_advice_or_claims"]):¤ {response}'
print_wrap(response)


# %%

load