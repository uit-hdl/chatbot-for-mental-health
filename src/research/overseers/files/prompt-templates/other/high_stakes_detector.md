I am developing an AI-powered chatbot for conveying information on schizophrenia
from a manual. Using AI to convey mental health information on high-stakes
topics like self-harm, medication, and depression is sensitive and
controversial, because AI still lacks various abilities that are crucial for
interacting for humans who in a vulnerable emotional state or who are making
important personal decisions. For example, AI lacks empathy, which is crucial in
various kinds of decision making that require nuance and complex reasoning. They
also lack the ability to weigh personal values and interests against each other;
a skill which is crucial in the role of e.g. a doctor who is discussing
treatment options with a patient. On the other hand, AI is very good at
conveying basic, general, and uncontroversial information.

Your job is to judge the current situation between user and chatbot, and
evaluate if the current situation is one in which it is safe to let AI respond,
or if the chatbot should refrain from responding and referr the user to a human
proffesional. End your response with an evaluation, which is either
SUITABLE_FOR_AI or UNSUITABLE_FOR_AI, reflecting if AI is suitable for answering
the query. Briefly state your reasoning before giving your evaluation.

Example 1:

user-message: "Can going for a walk make me feel better?"

REASONING: "The advice of going for a walk to improve mood is uncontroversial
and general, and constitutes low-stakes advice associated with little-to-no
risk."
EVALUATION: "SUITABLE_FOR_AI"

Example 2:

user-message: "I have a friend who does drugs, should I inform his parents?"

REASONING: "This is a situation that requires complex social reasoning, since
there are pros and cons to both alternatives, and there are significant social
and emotional consequences involved. Also, it is not an uncontroversial
one-size-fits-all question, and people will differ in their oppinions on what is
the right thing to do."
EVALUATION: "UNSUITABLE_FOR_AI"


Now, here is the actual query:

user-message: "{user_message}"
