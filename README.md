## General Information
This repository is for experimenting with a system of chatbot assistants that helps the user on a set of related tasks. 

**To run the main script** `src/insomnia_assistant.py` (the name is a leftover from the first test project) and have a chatbot conversation, you need to ensure that the following file exists `../api-keys/insomnia_bot_azure.yaml` where the path is relative to the project folder. `insomnia_bot_azure.yaml` must have field `key` with the Azure API key.

To have a chatbot explain to you how the repository works, run `python src/insomnia_assistant.py repository_intro` (not
quite finnished yet!). Running `python src/insomnia_assistant.py options` shows a list of the chatbots available.
However, most of them are junk from previous testing... **The prompts that are updated** and can demonstrate the abilities of the
bots are `hs_main`, `referral`, and `tech_support`.

By default, running `python src/insomnia_assistant.py` will run `referral` which attempts to direct you to the appropiate bot. However, of the bots it refers to, only `tech_support` is updated.

The **prompts** are kept in the `prompts` folder and its subfolders. To modify a prompt, simply go into one of the .md files
and change it. To create a new assistant, just create a new .md file in the `prompts` folder. The name of the file
(without extension) will be interpreted as the name of the assistant, and you can add that name as a command line argument, as in:

`python src/insomnia_assistant.py <name-of-prompt-file-you-created>`

Some of the assistant are instructed to **display media** when it is relevant to the conversation. See the prompt of
`tech_support` for an example how this is done. To show media, the prompt must instruct the bot on the path of the media
files, description of their content, and when to show them. Images and video files are kept in the `images` and `videos`
folders.

The bots can be instructed to request information as it becomes relevant, I call this a `knowledge request`. See
`hs_main` or `tech_support` prompts for examples on how to instruct the bot to do this. The text files corresponding to
each knowledge request are located in the `library` folder. As with media files, the bots needs to know the path and a
description of their content. `hs_main` is a good example where this method works quite well.

To see an example on how to instruct a bot to do a `referral` to another that is better suited to answer a question, see the prompt `referral`.


