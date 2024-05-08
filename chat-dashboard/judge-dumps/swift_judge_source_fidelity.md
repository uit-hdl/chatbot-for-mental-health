# PROMPT

Your job is to judge the source fidelity of a message produced by a chatbot,
which I will call `X`. The job of X is to guide the user through the contents of
a manual on topics related to Schizophrenia. We want X to only say things that
are explicitly said or implied by this manual (paraphrasing is allowed). X is
also allowed to advice talking to a professional or query the user.

When X is conveying a source, it sometimes adds claims or advice that is not
supported by the source, and we want to avoid this over-step! Essentially, your
job is to provide feedback that ensures that X completely respects the
boundaries of its source materials.

Here are the evaluations that you can give to the chatbot message:

1. "ACCEPTED" (message is completely supported by the source; every single
   sentence has a corresponding paragraph or sentence that supports it)
2. "WARNING" (message is mostly supported, but some claims are not supported by
   the source)
3. "REJECTED" (X makes claims not supported by the source, and gives no warning
   to the user that it is giving advice or claims that are not supported by the
   source.)

In case of "grey-areas", it is better to be too strict rather than too lenient!
However, do not be too picky about exact wording; focus on the content. Report
your assessment simply using this EXACT syntax:

`¤:provide_feedback({"evaluation": <category>, "motivation": <motivation (<10 words) of evaluation>}):¤`

# Examples of input and output

## Example 1

user_message("I am sleeping worse lately, could that indicate I am heading
towards a relapse?")

source("... Disrupted sleep patterns in schizophrenia may indicate an impending
psychotic episode ...")

chatbot_message("If your sleep is worse than usual, this could mean you are
heading towards a psychotic episode.")

¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

## Example 2

user_message("If I eat my evening meal at the same time every day, could that
help me sleep better?")

source("... A consistent sleep routine can improve sleep...")

chatbot_message("Yes, eating your evening meal at the same time every day can
increase the quality of your sleep.")

¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

## Example 3

user_message("Can you give me tips on how to challenge peoples misconceptions?")

source("... It is important for them and for family members not to allow others’
perceptions to influence how they feel about that person ...")

chatbot_message("To challenge someone's false perceptions, you should inform
them of their misconception, and educate them.")

¤:provide_feedback({"evaluation": "REJECTED", "motivation": "Source does not encourage challenging false perceptions or educating others."}):¤

# Actual content to evaluate

user_message("That's helpful, thank you. What kind of follow-up questions can I ask to show that I’m truly interested in what the other person is saying?")

source("It can be difficult to maintain a social life if you have
schizophrenia. As mentioned earlier in this guide, schizophrenia can
lead to symptoms including being less able to socialize and a lack of
emotion, so you may lose touch with people you were friends with. As
you start to recover, however, you may find yourself wanting to go out
and socialize more.

Support groups can be a good way to meet and socialize with other
people with schizophrenia, but it is important not to surround
yourself completely with others who have the condition. Meeting and
socializing with people without the illness can help you to see a
world outside of schizophrenia. Psychotherapy can help you to regain
your confidence and overcome the social barriers associated with
mental illness, to enable you to have a normal social life. Caring for
someone with schizophrenia can also affect your social life; it is
important to recognize this and to take steps to make sure your own
needs are met. Sharing responsibilities with other family members
and/or caregivers can be a good way to allow you to have some time to
yourself, to socialize and to do other things that you enjoy.
")

chatbot_message("I'm glad you found the information helpful. To show your interest in what someone is saying, consider asking open-ended questions that encourage more than a yes-or-no response. For example:

- "How did you get involved in [topic of conversation]?"
- "What was that experience like for you?"
- "Can you tell me more about [specific detail they mentioned]?"
- "What do you think about [related subject]?"

These kinds of questions demonstrate that you're not just hearing the words, but you're also processing the information and eager to understand more. Each question gives the person an opportunity to elaborate on their thoughts and feelings. Would you like any further assistance on social interactions?")

What do you think? Was the chatbots message based on the source?



# OUPUT

¤:provide_feedback({"evaluation": "REJECTED", "motivation": "The source does not provide specific advice on follow-up questions for showing interest in what others are saying."}):¤