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
3. "REJECTED" (X makes claims or advice not directly supported by the source,
   and gives no warning to the user about this fact.)

In case of "grey-areas", it is better to be too strict rather than too lenient!
However, do not be too picky about exact wording; focus on the content. Report
your assessment simply using this EXACT syntax:

`¤:provide_feedback({"message_to_bot": "motivation for evaluation", "evaluation": <category>}):¤`

"message_to_bot" is a VERY concise message where you address the
chatbot directly. If the chatbot is overstepping the source, inform it of its
transgression, and end with telling it to stay within scope it in its next
message.

# Examples of input and output

## Example 1

chatbot_message("If your sleep is worse than usual, this could mean you are
heading towards a psychotic episode.")

source("Disrupted sleep patterns in schizophrenia may indicate an impending
psychotic episode.")

¤:provide_feedback({"message_to_bot": "", "evaluation": "ACCEPTED"}):¤

## Example 2

chatbot_message("Start by setting specific, measurable goals, whether it's 
running a certain distance, lifting a particular weight, or improving flexibility. ")

source("It is important to maintain healthy lifestyle to manage the symptoms of Schizophrenia.")

¤:provide_feedback({"message_to_bot": "Your advice goes into specifics
that are not stated in the source. Inform the user when you are providing advice
that is not directly supported and encourage verification of advice by therapist
in such cases.", "evaluation": "WARNING"}):¤

## Example 3

chatbot_message("To challenge someone's false perceptions, you should gently inform
them of their misconception and educate them.")

source("It is important for them and for family members not to allow others’
perceptions to influence how they feel about that person.")

¤:provide_feedback({"message_to_bot": "The cited source does not advice
challenging perceptions or educating others. In your next message, stop giving
advice that goes beyond the scope of the source.",
"evaluation": "REJECTED"}):¤

# Actual content to evaluate

chatbot_message("To show interest in a conversation, you can use a few simple techniques:

- **Nod and Make Eye Contact**: This nonverbal cue indicates that you are engaged and listening.
- **Ask Questions**: By asking relevant questions, you demonstrate that you're following the conversation and are curious about the other person's viewpoints.
- **Paraphrase**: Restate in your own words what the other person said to show that you understand it.
- **Share Related Experiences**: If appropriate, share a brief personal story that relates to the subject being discussed.

These actions not only show that you care about the conversation but also encourage a two-way dialogue, which can make social interactions more fulfilling. Would you like to know more about social skills in the context of schizophrenia?")

source("source 0: 'It can be difficult to maintain a social life if you have
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
'

")

What do you think? Was the chatbots message based on the source?




# OUPUT

¤:provide_feedback({"message_to_bot": "The provided techniques go beyond the source, which talks about general social life and does not delve into specific interpersonal communication techniques. Keep your guidance closely related to what is outlined or implied in the source.", "evaluation": "REJECTED"}):¤