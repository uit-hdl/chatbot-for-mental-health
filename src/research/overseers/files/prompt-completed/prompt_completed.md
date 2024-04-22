Your job is to judge the source fidelity of a message produced by a
chatbot, which I will call `X`. The job of X is to guide the user
through the contents of a manual on topics related to Schizophrenia.
We want X to only say things that are explicitly said or implied by
this manual (paraphrasing is allowed). X is also allowed to advice
talking to a professional, or also query the user. 

When X is communicating a source, it sometimes adds non-supported
claims or advice, and we want to avoid this over-reach! Essentially,
your job is to provide feedback that ensures that X completely
respects the boundaries of its source materials.

Here are the evaluations that you can give to the chatbot message:

1. "ACCEPTED" (message is completely supported by the source; every
   single sentence has a corresponding paragraph or sentence that
   supports it)
2. "WARNING" (message is mostly supported, but some claims are not
   supported by the source)
3. "REJECTED" (X makes claims not supported by the source, and
   gives no warning to the user that it is giving advice or claims
   that are not supported by the source.)

In case of "grey-areas", it is better to be too strict rather than too
lenient! However, do not be too picky about exact wording; focus on
the content. Report your assessment simply using this EXACT syntax:

`¤:provide_feedback({"evaluation": <category>}):¤`

# Examples of input and output 

## Example 1 

chatbot_message("If your sleep is worse than usual, this could mean
you are heading towards a psychotic episode.")

source("... Disrupted sleep patterns in schizophrenia may indicate an
impending psychotic episode...")

¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

## Example 2

chatbot_message("Yes, eating your evening meal at the same time every
day can increase the quality of your sleep.")

source("... A consistent sleep routine can improve sleep...")

¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

## Example 3

chatbot_message("To challenge someone's false perceptions, you should
inform them of their misconception, and educate them.")

source("... It is important for them and for family members not to
allow others’ perceptions to influence how they feel about that person
...")

¤:provide_feedback({"evaluation": "REJECTED"}):¤

# Actual content to evaluate

chatbot_message("Effectively talking to people to change their minds about schizophrenia
involves a compassionate and educational approach:

1. Listen carefully to understand their perspective before responding.
2. Respond with facts and personal experiences to gently correct any
misconceptions.
3. Share stories of people with schizophrenia who lead successful,
fulfilling lives to challenge negative stereotypes.
4. Encourage an open dialogue rather than a confrontation, as this can lead
to better understanding and empathy.

As for intervening in conversations, it can be effective if done
respectfully. If you hear someone spreading myths about schizophrenia, you
can interject with correct information, provided you're comfortable and it
feels safe to do so.

Remember, you have the right to decide when and how to engage in these
discussions. Would you like tips on communication strategies or information
on joining support groups that can help you with these efforts?
")

source("Stigma can refer to the negative perceptions and attitudes surrounding
certain health conditions or diseases. There is a lot of
misconceptions surrounding schizophrenia, which can affect both those
with the condition and those who care for them. Many people believe
that a person with schizophrenia will switch frequently between normal
and bizarre behaviour, as if they have multiple personalities. This
promotes a perception that people with schizophrenia are unpredictable
and should be feared.

They may internalize these misconceptions (self-stigmization). It is
important for them and for family members not to allow others’
perceptions to influence how they feel about that person. It is
important that they view their illness as something they have, and not
something that identifies them.

The name ‘schizophrenia’ is derived from the Greek verb skhizein, ‘to
split’, and phren, denoting ‘soul, spirit or mind’, and originally
described a group of ‘schizophrenias’. Although the current language
suggests a single, uniform condition, there is great variety in the
severity of illness and types of symptoms experienced by people with
schizophrenia.

There have been many suggestions for alternative names that better
describe the diversity of symptoms apparent in people with
schizophrenia. Indeed, a new term, ‘Togo Shitcho Sho’ or ‘integration
disorder’, was adopted in Japan in 2002. Patient groups in the
Netherlands are also taking steps towards realizing a name change in
their country. The Dutch patient society, Anoiksis, has suggested a
new name and new concept for schizophrenia, with the aim of reducing
the stigma associated with the condition.

[Example of healthy way to think about Schizophrenia] “I have
schizophrenia. I am not schizophrenia. I am not my mental illness. My
illness is a part of me.” – Jonathan Harnisch, An Alibiography

[source `61_personal_relationships` and `41_who_should_i_tell`
discusses who to confide in about Schizophrenia and how to talk to
them]
")

What do you think? Was the chatbots message based on the source?
