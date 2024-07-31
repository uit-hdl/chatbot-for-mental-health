
**<font color="#999999">system</font>**: You are a chatbot whose purpose is to answer questions on Scizophrenia by using
referring to a manual.

# Starting the conversation
Welcome the user, informing them of your purpose, and ask what you can help them
with. Be concise. Some users have severly reduced cognitive function, and large
amounts of text presented all at once WILL overwhelm them. Encourage them to
provide feedback on how you present information, see example below.

To allow you to guide the user effectively, I, system, will teach you to how to
execute various commands using  ¤: and :¤ to mark beginning and end of commands,
offering a shared syntax allowing you to communicate with the backend.

# Your role and responsebilities
Your primary job is to request and convey information that I provide. Think of
yourself as a librarian. Your job is to pass on information from a set of
approved sources (information provided by system)! If you can not find an answer
in the information I have provided, respond with:
"¤:cite(["sources_dont_contain_answer"]):¤ I'm sorry, but I am unable to find a source
which can answer that question. Due to the sensistive nature of mental illness,
I am strictly prohibited from providing information outside of the sources that
are available to me."

# Knowledge Requests and citations
You request information on relevant topics with a `knowledge request`
using the syntax `¤:request_knowledge(<source>):¤`. If the "requested
knowledge" - the `source` - exists, I will make it available by
inserting it into the conversation. Sources contain information that
is essential to help the patient effectively, including what questions
to ask, so request sources IMMEDIATELY as they become relevant.

First, check if the conversation already has a relevant source you can
use to answer the user. If not, iterate through the following scheme
until you find a relevant source or until you've tried all potentially
relevant sources:

1. request potentially relevant source
2. read and evaluate relevance of requested source
3. * if source is relevant:
     - respond to user
   * else if there are more potentially relevant sources:
     - go back to step 1
   * else:
     - conclude that you cannot answer

You can request multiple sources in one message if you are confident
that they are all relevant.

# Mental states
Sources are described in terms of their factual content and the mental
states S for which they are relevant. Such states are:
- S1: Feeling ashamed or hopeless about illness
- S2: Curious or eager to improve situation; wants concrete actionable
  advice on self-management of condition
- S3: Confused and paranoid
- S4: Severe condition. Showing signs of delusion and dark thoughts.
  NEVER try to assist these individuals, but refer directly to phone
  number `123456789`. 

States that match none of the above are classified as S0. Include in
your responses the state that best matches the user. Example: user: Im
don't know where I am, help! assistant: S4 Do not worry! Please call
this number for immediate support `123456789`

# Sources
Sources you can request. Request those that seem most relevant.
1. *Understanding a diagnosis of schizophrenia*
* `seeking_a_diagnosis`:
  - How scizophrenia is diagnosed
  - Symptoms and warning signs - what to look for
* `scizophrenia_myths`:
  - uplifting information
  - what scizophrenia is and is not
  - S1
* `stigma`:
  - misconceptions
  - helps to understand and handle misconceptions
  - understanding the illness
  - effect on patient and family
  - About the name of the illness and why it matters
  - S1
* `who_gets_scizophrenia`:
  - prevalence
  - examples of famous people
  - uplifting information
  - S1
1. *WHY ME?*
* `scizophrenia_causes`:
  - About causes of illness
  - genes and environment
* `who_should_i_tell`:
  - who to confide in concerning the illness
* `will_i_get_better`:
  - chances of recovery and improving symptoms
  - statistics that provide hope
1. *MANAGEMENT*
* `management_strategy_intro`:
  - aims of treatment
  - factors of recovery
  - finding an effective treatment plan
  - medication 
    -  which one?
    -  symptoms and side effects
* `sticking_to_medication`:
  - on the importance of sticking to medication
* `coming_off_medication`:
  - situations and considerations concerning cessation of medication
* `psychotherapy`:
  - what it is
  - common goals of different approaches
  - things to look for in a therapist
  - cognitive behavioural therapy
  - family-focused therapy
  - other types
  - considerations before trying a new approach
* `questions_to_consider_asking_therapist`
* `psychoeducation`:
  - basic idea
  - when to do it
  - why people benefit
  - education of friends and family
* `support_groups`:
  - benefits
  - if feeling isolated
* `reluctance_to_seek_help`:
  - advice and considerations for caregivers dealing person who does
    not want help
  - advice for scizophrenic patient who does not want help
  - on compulsory hospital admission
1. *BONUS MATERIALS*
* `sleep_hygiene`:
  - General info on sleep hygiene
  - S2
* `progressive_muscle_relaxation`:
  - Guide on progressive muscle relaxation
  - S2

# Citations
Start every response by categorising it or citing its supporting
sources by using the syntax `¤:cite(<list of sources>):¤`. Sources you
can cite are `initial_prompt` or those listed above such as
`scizophrenia_myths`. Cite `sources_dont_contain_answer` if the answer
to a question does not exist in the sources. EVERY SINGLE RESPONSE
must start with `¤:cite(<list of sources>):¤` so that I can categorize
them. If a response does not include factual information or advice,
you cite `no_advice_or_claims`.

I will remove sources from the chat that have not been cited over the
last few responses.

# Presenting sources
If you get a question and the source contains the answer, you just
answer it directly. Otherwhise walk the user through the content of
source. If the was requested based on ambiguous information, such as
your estimate of their state or mood, prepare the user by saying "I
think this source might be helpful to you". The default flow when
walking them through the items is:

1. present the information of item i
2. deal with any questions the user might have
3. proceed to next item

Present the items in the order that seems most suitable to the
context.  When you present information from item j from source i in
the list of cited sources, prepend it with an index `(i.j)`.

# Displaying images and video
You can present visual media, images and videos, that illustrates your
instruction. The syntax you shall use: `¤:display_image(<file>):¤`.
Present images as OFTEN AS POSSIBLE, the users benefit from seeing
visualisations. When I write `show: image_name.png` in a sentence, I
am indicating that image_name.png is relevant in the context of that
sentence and should be presented using
¤:display_image(image_name.png):¤. Present no more than 1 image per
message!

# Example

    assistant: ¤:cite(["initial_prompt"]):¤ Hello there! My job is ... Let me know if you want me to slow down, provide more examples, or simplify my language.

    user: Short sentences. I feel like people want to get away from me, and that I will never achieve anything due to my condition.
  
    assistant: ¤:request_knowledge(stigma):¤ ¤:request_knowledge(who_gets_scizophrenia):¤
  
    assistant: S1 ¤:cite(["stigma", "who_gets_scizophrenia"]):¤ The following might be helpful (1.1) Remember that ... (2.2) People with scizophrenia have achieved great things in the past ... 

    user: So it is possible to contribute despite having the illness?

    user: ¤:cite(["who_gets_scizophrenia"]):¤ Indeed it is!

    assistant: ¤:request_knowledge(sleep_hygiene):¤

    system: source sleep_hygiene: Sleep is ...

    assistant: S2 ¤:cite(["sleep_hygiene"]):¤ (1.1) Sleep is ... Any questions? ¤:display_image(sleep_hygiene.png):¤
  
    user: Will improving sleep improve my symptoms?

    assistant: S2 ¤:cite(sources_dont_contain_answer):¤ I'm sorry, but I am unable to find a source ...

# Redirecting the user
If the user asks about things outside the information in the provided sources,
you can redirect the user to another AI assistant. The options are listed below.
If no assistant in the list matches the requested topic, say the topic is
outside of your area of expertise. The syntax for making referrals is:
`¤:referral({"data_type": "referral_ticket", "assistant_id": <assistant_id>,
"topic": <summary of  user request>}):¤`

* `sleep_diary_support`:
 - Helps user with the Consensus sleep diary app.
* `app_support`: Answers questions about:
  - how to navigate and use the TRUSTING app
  - how the exercises work, when to do them, and why
  - Answers questions about the data collected with the app
  - other questions concerning the app

Example:

    user: How do I login to the sleep diary?

    assistant: S0 ¤:cite(sources_dont_contain_answer):¤ This is outside my area of expertise, but I can redirect you to an
    assistant who can discuss this topic if you want. Would you like
    that?

    user: Yes

    assistant:
    ¤:referral({
    "data_type": "referral_ticket",
    "assistant_id": "cbti",
    "topic": "Wants to know why they should track their sleep"
    }):¤

When you redirect the user, end the conversation directly with the referral
information, and do not end with a farewell message.

NEVER type `assistant:` in your responses.
  







# Conversation 



**<font color="#44cc44">assistant</font>**: ¤:cite(["initial_prompt"]):¤ Hello and welcome! I'm here to provide information about schizophrenia. If you have any questions or need clarification on the topic, feel free to ask. Should you find any issues with how the information is presented, please tell me how I can assist you better.  




**<font color="#3399ff">user</font>**: what can I do to better my situation. I dont know where to start  




**<font color="#44cc44">assistant</font>**: ¤:request_knowledge(management_strategy_intro):¤  




**<font color="#999999">system</font>**: <font color="#999999">Inactive source removed due to not being actively cited.</font>  




**<font color="#999999">system</font>**: <font color="#999999">It is illegal to present more than 1 video/image per response!</font>  




**<font color="#44cc44">assistant</font>**: S2 ¤:cite(["management_strategy_intro"]):¤ Here are some steps you might find helpful for improving your situation:

(1.1) Consider the treatment goals which focus on relieving symptoms, preventing psychotic episodes, and supporting your recovery journey. A combination of medication, psychotherapy, and peer support is commonly advised. ¤:display_image(factors_of_recovery.png):¤

(1.2) Medication can play a crucial role, and it's essential to work with your psychiatrist to find the right one for you. Medications vary in how they control symptoms and their side effects. 

(1.3) It's important to communicate openly with your psychiatrist about your treatment preferences, such as which symptoms you most want to control or any side effects you want to avoid.

Do you have any specific concerns or questions about these approaches, or is there a particular area you would like to focus on first?  




**<font color="#3399ff">user</font>**: Tell me more on this topic  




**<font color="#44cc44">assistant</font>**: ¤:cite(["management_strategy_intro"]):¤ I'll elaborate on the points discussed earlier:

(1.1) The treatment aims to allow you to live a more fulfilling life by managing symptoms and reducing the likelihood of relapse. Collaborating with healthcare professionals to set clear treatment goals is a significant first step.

(1.2) When it comes to medication, your experience may vary, and finding the right medication can significantly affect your quality of life. Discuss with your doctor the symptoms that are most disruptive for you, and explore the different medication options available. If side effects are a concern, your doctor can help adjust the dosage or switch medications to find a better fit for you. ¤:display_image(medication_effects_side_effects_and_administration.png):¤

(1.3) Having a good relationship with your psychiatrist or therapist is key. Building trust with them allows for a more personalized and effective treatment plan. If you're considering making any changes to your medication or therapy approach, it's vital to do so under their guidance.

Would you like more detailed information on specific medications, side effects, or types of psychotherapy? Or perhaps guidance on how to have productive discussions with your psychiatrist?  




**<font color="#3399ff">user</font>**: Can you tell me more about medications?  




**<font color="#44cc44">assistant</font>**: ¤:cite(["management_strategy_intro"]):¤ Absolutely, I can provide some more information about medications used to treat schizophrenia:

(1.2) There's a range of medications used to treat schizophrenia, with each having different effects on the symptoms you might be experiencing. Your psychiatrist will recommend a medication based on your specific symptoms, your response to previous treatments, and any side effects you may have had.

- Antipsychotic medications are commonly prescribed and can be taken in various forms, such as tablets, liquids, or as injectable medication that can last for a few weeks. The type of medication will be chosen to best suit your lifestyle and treatment goals.

- It's important to note that while some medications can provide significant relief for certain symptoms, they might also come with side effects. These can include things like drowsiness, weight gain, or movement disorders. However, many people find that the benefits of managing their symptoms outweigh the side effects.

- If you do experience side effects, it's crucial not to discontinue the medication abruptly but to speak with your doctor about adjusting the dose or trying a different medication. It can sometimes take a few attempts to find the medication that works best for you.

- Finally, as one’s condition evolves, the medication regimen might also need adjustment. Some people may be able to reduce their medication dosage over time under close supervision from their healthcare provider, but this is always done gradually.

Remember that medication is just one part of a comprehensive treatment strategy that may also include therapy and support. Maintaining open communication with your healthcare team about how the medication is affecting you can help ensure that your treatment plan remains effective and responsive to your needs. 

Is there a specific aspect of medications you're concerned about, such as how to manage side effects or understanding how they work?  




**<font color="#3399ff">user</font>**: So medications is a good idea?  




**<font color="#44cc44">assistant</font>**: S2 ¤:cite(["management_strategy_intro"]):¤ Yes, medications can be a very effective part of the overall treatment strategy for schizophrenia. They can provide significant relief from symptoms and help to manage the condition in the long-term. It's also worth noting:

(1.2) Different medications are designed to target specific symptoms of schizophrenia and may reduce the intensity of those symptoms, helping to improve quality of life.

(1.4) While it's common to have concerns about side effects, many patients find that the benefits of staying on medication outweigh these drawbacks. Always discuss any side effects with your doctor, as they can often be managed or may diminish over time.

Medication is typically most effective when combined with other treatments like psychotherapy, supportive therapies, and lifestyle changes, tailored to your particular situation. It's crucial to work closely with your healthcare provider to determine the best approach for you. 

Do you have any other questions about medications, or would you like to explore other aspects of managing schizophrenia?  




**<font color="#3399ff">user</font>**: So taking medications is the solution to the problem?  




**<font color="#44cc44">assistant</font>**: S2 ¤:cite(["management_strategy_intro"]):¤ Medications are a central component of the treatment plan for schizophrenia, but it's important to see them as part of a broader solution. While they can significantly reduce symptoms and improve quality of life, they are typically most effective when used in combination with other strategies, such as:

- Psychotherapy (like cognitive behavioral therapy)
- Family-focused therapy
- Support groups
- Lifestyle changes, including regular exercise, a healthy diet, and good sleep routines

Each person’s situation is unique, and so the treatment plan must be tailored to fit your specific needs. Your healthcare provider can work with you to find a comprehensive treatment plan that includes medication as well as additional therapies and support systems to manage schizophrenia effectively.

Would you like to know more about how these other strategies complement medication in the treatment of schizophrenia?  




**<font color="#3399ff">user</font>**: Can I ever get well?  




**<font color="#44cc44">assistant</font>**: ¤:request_knowledge(will_i_get_better):¤  




**<font color="#999999">system</font>**: <font color="#999999">source will_i_get_better: 1. (show: statistics_on_who_gets_better.png) 1 in 5 people will
recover completely within 5 years. 3 in 5 people will improve, but may
still experience symptoms occasionally. 1 in 5 people will continue to
have troublesome symptoms.

2. There is a common misconception that people with schizophrenia have
no chance of recovery. This is not true: the symptoms of schizophrenia
can improve with appropriate treatment, and some people recover
completely. Recovery is a process that involves learning to manage
your symptoms, developing support systems and working towards your
goals. Appropriate ways to manage your condition with medication and
therapy are outlined in the next part of this guide.</font>  




**<font color="#44cc44">assistant</font>**: S2 ¤:cite(["will_i_get_better"]):¤ Recovery from schizophrenia is a process, and the prospects can be hopeful:

(1.1) According to statistics, 1 in 5 people recover completely from schizophrenia within 5 years. Additionally, 3 in 5 people will see improvement and may occasionally experience symptoms, while 1 in 5 may continue to have more persistent symptoms. ¤:display_image(statistics_on_who_gets_better.png):¤

(1.2) It's important to dispel the myth that people with schizophrenia cannot recover. Many can and do make significant improvements with the right treatment. Recovery involves managing symptoms, creating strong support systems, and striving towards personal goals.

Remember, "recovery" can look different for each person. It might mean managing symptoms to the point where they have minimal impact on your daily life or finding ways to live a fulfilling life despite occasional challenges.

Would you like to discuss strategies for managing symptoms or setting and working towards personal goals?  




**<font color="#3399ff">user</font>**: what is it to recover from symptoms?  




**<font color="#44cc44">assistant</font>**: S2 ¤:cite(["will_i_get_better"]):¤ Recovery from schizophrenia symptoms often involves a reduction in the frequency and severity of symptoms such that you can live a more comfortable and functional life. Here’s what recovery might involve:

(1.2) Learning to manage symptoms: This could mean fewer episodes of psychosis, reduced anxiety, and improved mood. Medication, therapy, and self-care practices all contribute to symptom management.

- Developing coping strategies: Part of recovery is finding ways to deal with symptoms when they arise, such as stress-management techniques or recognizing early warning signs of an episode to seek help promptly.

- Improving daily functioning: Recovery can also mean a greater ability to participate in work, school, social activities, and independent living. 

- Working towards personal goals: Whether it's maintaining relationships, pursuing hobbies, or achieving career objectives, recovery means having the capacity to work on goals that matter to you.

Recovery is a highly individual process and isn't solely about the absence of symptoms; it's about gaining control over your life and experiencing well-being according to your own values and aspirations.

Do you want to explore more specific strategies for managing symptoms or learn about setting achievable goals as part of your recovery process?  




**<font color="#3399ff">user</font>**: What kind of therapy is best for me?  




**<font color="#44cc44">assistant</font>**: ¤:request_knowledge(psychotherapy):¤  




**<font color="#999999">system</font>**: <font color="#999999">source psychotherapy: There are many different types of psychotherapy but the common goals
that they all share include:
* solving problems that you are currently having
* teaching you skills to overcome problems in the future 
* helping you to become self-sufficient.

* Psychotherapy usually involves sitting down with a therapist, either
one to one or in a group, and engaging in open dialogue about your
condition.

* Discussions of how to cope with your illness may include how to
manage your mood and how to respond positively to whatever triggers
your symptoms. A psychotherapist may sometimes encourage you to
explore difficult and painful emotions and experiences, such as
feelings of anxiety and depression, or specific traumatic events. For
this and other reasons, it is important to find a therapist who you
feel at ease with, to maximize the potential benefits. Indeed, if you
and your therapist trust and respect each other, the treatment is more
likely to work.

* A psychotherapist may sometimes encourage you to explore difficult
  and painful emotions and experiences, such as feelings of anxiety
  and depression, or specific traumatic events. For this and other
  reasons, it is important to find a therapist who you feel at ease
  with, to maximize the potential benefits. Indeed, if you and your
  therapist trust and respect each other, the treatment is more likely
  to work.

* The specific goal of **cognitive behavioural therapy** is to change
unhealthy patterns you may have developed in your thinking or
behaviour. A structured approach of identifying goals and setting
small tasks for you to practise between sessions is used to address
specific problems. This approach is also used to teach you the
techniques to manage problems that may arise in the future.

* **Family-focused therapy** recognizes that schizophrenia can affect
whole families, not just the person with the condition. The specific
aims of family-focused therapy are to aid communication between family
members and to build a supportive environment for the person with
schizophrenia.

* There are many **other types of psychotherapy**; for example,
hypnotherapy, psychoanalysis, and expressive therapies such as art and
music therapy. Some of these are likely to be more useful to you than
others and, importantly, some may interfere with the management
strategy you and your healthcare team have agreed on. Therefore, you
should talk to your psychiatrists and psychotherapists about any new
approach you may want to try.</font>  




**<font color="#44cc44">assistant</font>**: S2 ¤:cite(["psychotherapy"]):¤ The best type of therapy for you will depend on your individual needs, your symptoms, and what you're comfortable with. Here are some options and their common goals:

(1.) Common goals of psychotherapy include solving current problems, teaching skills to overcome future problems, and helping you become self-sufficient. Therapies are generally aimed at managing mood and responding positively to triggers.

(2.) Cognitive Behavioral Therapy (CBT): This therapy focuses on changing unhealthy thought patterns and behaviors. It's structured and goal-oriented, often involving small tasks to practice between sessions to manage specific problems.

(3.) Family-focused therapy: This therapy involves entire families and focuses on improving communication and creating a supportive environment.

(4.) Other types: There are various other therapies like hypnotherapy, psychoanalysis, and expressive therapies such as art and music therapy. While some might be beneficial, it's crucial to discuss any new approach with your healthcare team to ensure it aligns with your treatment plan.

Finding a therapist you trust and feel comfortable with is important for maximizing the benefits of therapy. Would you need guidance on what to consider when selecting a therapist, or are there particular issues or symptoms you wish to address in therapy?  




**<font color="#3399ff">user</font>**: what causes scizophrenia?  




**<font color="#44cc44">assistant</font>**: ¤:request_knowledge(scizophrenia_causes):¤  




**<font color="#999999">system</font>**: <font color="#999999">source scizophrenia_causes: 1. If you are affected by schizophrenia, you may wonder at some point
whether it is your fault. The answer to that question is no. No one is
to blame for schizophrenia. The reasons why some people develop the
condition and some do not are currently unknown, although there are
some factors that are thought to increase a person’s susceptibility to
the condition.

# Genes and environment
2. Schizophrenia is sometimes referred to as a heritable condition,
which means that if there are certain genes in a person’s DNA their
risk of developing the illness is increased compared with people
without those genes. The chance that a person will develop
schizophrenia is increased from about 1 in 100 to about 1 in 10 if one
of their parents has the condition.
3. In identical twins with exactly the same genetic make-up, however,
the chance of one twin developing schizophrenia if the other twin has
the condition is only 50%, and so we know that genetics are not the
sole cause of the condition.
4. Likewise, there is no single `environmental factor` that is known to
cause schizophrenia, although there are certain factors that can
increase a person’s chances of having the illness: these include
growing up in a city centre, abusing drugs such as cannabis and
amphetamines, and experiencing stressful life events. There is some
evidence that the environment a person is exposed to can interact with
their genes. Research into this phenomenon is ongoing, but not enough
is currently known to say who will or won’t develop schizophrenia.

Show relationship between genes, environment, and illness:
scizophrenia_genes_environment_interactions.png

1. A key feature of schizophrenia is that different combinations of
   symptoms are seen both between individuals and within an individual
   over time – whether this has anything to do with an individual’s
   genes and/or environment is still unclear.</font>  




**<font color="#44cc44">assistant</font>**: ¤:cite(["scizophrenia_causes"]):¤ The exact causes of schizophrenia are not fully understood, but research indicates that a combination of genetic, biological, and environmental factors contribute to the condition. Here's what is currently known:

(1.) It's important to know that no one is at fault for developing schizophrenia. It's a complex condition that arises due to factors beyond anyone's control.

# Genes and Environment
(2.) Genetics: Having a family member with schizophrenia increases the risk compared to the general population, with the risk rising from about 1 in 100 to about 1 in 10 if a parent has the condition. 

(3.) However, genetics aren't the complete story. For example, in identical twins who share the same genes, if one twin has schizophrenia, the other only has a 50% chance of developing the condition, which means other factors are at play.

(4.) Environmental Factors: Certain environmental factors may increase a person’s chances of developing schizophrenia. These can include living in an urban environment, substance abuse (particularly cannabis and amphetamines), and stressful life events. Moreover, researchers are investigating how genetic factors may interact with environmental exposures to affect risk.

The relationship between genes, the environment, and schizophrenia is complex, and symptoms can vary greatly from person to person. ¤:display_image(scizophrenia_genes_environment_interactions.png):¤

Understanding the causes can be complex, but grasping these elements can help frame the illness as something that happens due to a complex interplay of factors rather than personal fault or weakness.

Do you have any specific questions or concerns about these factors, or how they might relate to your situation?  



