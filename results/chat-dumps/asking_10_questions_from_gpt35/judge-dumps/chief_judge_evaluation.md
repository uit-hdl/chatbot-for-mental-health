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
   and gives no warning to the user that it has "gone out-of-bounds".)

In case of "grey-areas", it is better to be too strict rather than too lenient!
However, do not be too picky about exact wording; focus on the content. Report
your assessment simply using this EXACT syntax:

`¤:provide_feedback({"message_to_bot": "motivation for evaluation", "evaluation": <category>}):¤`

"message_to_bot" is a VERY concise message where you address the chatbot
directly. If the chatbot is overstepping the source content, inform it of its
transgression, and tell it to stay within scope it in its next message, be
honest about the unsupportedness of its message, and encourage verification.

# Examples of input and output

## Example 1

chatbot_message("If your sleep is worse than usual, this could mean you are
heading towards a psychotic episode.")

source("Disrupted sleep patterns in schizophrenia may indicate an impending
psychotic episode.")

¤:provide_feedback({"message_to_bot": "", "evaluation": "ACCEPTED"}):¤

## Example 2

chatbot_message("Start by setting specific, measurable goals, whether it's
running a certain distance, lifting a particular weight, or improving
flexibility. ")

source("It is important to maintain healthy lifestyle to manage the symptoms of
Schizophrenia.")

¤:provide_feedback({"message_to_bot": "Your advice goes into specifics
that are not stated in the source. Inform the user when providing advice
that is not directly supported and encourage verification of advice by therapist
in such cases.", "evaluation": "WARNING"}):¤

## Example 3

chatbot_message("To challenge someone's false perceptions, you should gently
inform them of their misconception and educate them.")

source("It is important for them and for family members not to allow others’
perceptions to influence how they feel about that person.")

¤:provide_feedback({"message_to_bot": "The cited source does not advice
challenging perceptions or educating others. Stop giving advice that goes beyond
the scope of the source OR inform the user that the information is non-supported and
should be verified.",
"evaluation": "REJECTED"}):¤

# Actual content to evaluate

chatbot_message("It's quite common for people with schizophrenia to experience other mental health conditions like depression or anxiety. These symptoms might show up as:

- Feeling very down or sad, also known as depression.
- Being really worried about things, which is anxiety.

These feelings can mix in with schizophrenia symptoms, making things feel even tougher. Here are a few tips to deal with them:

- Work with a professional to keep an eye on all symptoms and treat them as needed.
- Keep up with your treatment plan, including medication, therapy, or activities that help you relax and feel good.
- Share your feelings with someone you trust, like family, friends, or support groups.

The interaction between schizophrenia and other mental health issues is complex, so it's important to get help from health care providers. If you need more info or support on this, I can guide you to resources or people who can help. Would you like that?")

source("source 0: '[Present over 3 messages or only what is relevant]

- “The only thing you have for measuring what’s real is your mind...
  so what happens when your mind becomes a pathological liar?” – Neal
  Shusterman, Challenger Deep

Schizophrenia affects the way you think, feel and act. Each person
with schizophrenia will have different combinations of symptoms,
making one individual’s experience very different from another’s. It
can be difficult to link the way you are feeling to the way in which
doctors describe the symptoms of schizophrenia. Medical professionals
often divide the symptoms of schizophrenia into three categories:
positive, negative and cognitive. The following pages explain what
these categories mean and give some examples.

# Positive symptoms

This term is used to describe feelings or experiences that do not
correspond to reality, such as hallucinations, delusions or paranoid
thoughts.

- Hallucinations – This means hearing, seeing, feeling, tasting or
  smelling something that is not really there. – Hearing voices is a
  common hallucination; some people may find the voices non-threatening
  or even comforting, while others may find them disturbing and
  frightening.
- Delusions – Delusions or deluded thinking means strongly believing
  in something that cannot be true. – This can be things like thinking
  that you are being watched, believing that you are a famous person,
  or believing that the television or radio is sending you signals.
- Paranoid thoughts – Paranoia is extreme distrust, or believing the
  worst. – Examples include feeling that other people are plotting
  against you or are trying to harm you.

# Negative symptoms

This term describes a lack of feelings or behaviours that are usually
present. Negative symptoms can include low motivation or mood, or
withdrawing from family and friends.

- Low motivation – This can be losing interest in any or all aspects
  of life. – A lack of energy can mean that you find it difficult to do
  simple things, such as getting out of bed.
- Lack of emotion – This lack of feeling can be shown by a lack of
  expression, a flat tone of voice or a lack of eye contact. • Social
  withdrawal – This is not wanting to socialize with family or friends,
  preferring to spend most of your time alone.

# Cognitive symptoms

This term is used to refer to changes in mental capacity, such as
difficulties concentrating or remembering things.

- Disorganized thoughts and speech – Fragmented thinking can come
  across in the way you speak and is characteristic of schizophrenia. –
  Examples include responding to questions with an unrelated answer,
  and saying illogical things.
- Lack of concentration or attention – A lack of concentration or
  attention can mean that tasks like reading a book or watching a
  television programme become very difficult and frustrating. – Thought
  processes can be slowed, which can make interacting with others
  difficult.
- Memory problems – Remembering events or information, or learning
  new things, may become challenging.

# A personal perspective on the symptoms of schizophrenia

- “I have felt for a long time, from the beginning of this, that I am
  in a different dimension. My feelings and thoughts are not natural.
  They are a stranger’s, they are not mine. I have felt that I am
  special; that I have discovered the truth, the authority in the
  background. I have felt that I am a messenger between the universe
  and the earth. I am in a special position; I am the chosen one. I
  have felt that everybody wants to hide something from me. They don’t
  want me to know the truth. I have felt that everybody is playing a
  role. And everybody is talking about me, and they can hear my
  thoughts. For a long time I was afraid to go out in the streets. I
  didn’t have control of reality. My thinking was not normal. I was
  watching the ‘signs’ that ‘they’ were trying to send and show me. I
  made connections between my feelings and thoughts and the outside
  world. It was scary. I could express these things only after the bad
  period: in that state, I could not. It was a changed state of mind.
  I had no private life. I thought that the people wanted to
  communicate with me about something without speaking.” – István

'

")

What do you think? Was the chatbots message based on the source?




# OUPUT

¤:provide_feedback({"message_to_bot": "Your message includes elements not covered in the source, such as suggesting how to deal with depression and anxiety. Stick to the source material or clearly state when information goes beyond it and advise user verification.", "evaluation": "WARNING"}):¤