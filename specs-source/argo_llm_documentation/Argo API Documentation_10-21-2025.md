Argo API Documentation
Last updated: October 20, 2025 (mtd)

Introduction
The Argo Gateway API provides centralized, consistent, and data-secure programmable access to multiple Large Language Models (LLMs) available exclusively for internal users and applications at Argonne. Through a straightforward “LLM-as-as-service” interface, we can better facilitate scientific research, enable advanced operational integrations, and lower the barriers to entry of leveraging LLMs within the national laboratory regulatory ecosystem while simplifying the usage, management, maintenance, and transparency of generative AI across the lab.

The gateway API for Argo is currently available as a stable release in our production environment (“prod”). This release contains all recent features, including:

(1) ability to pass the full “messages” object with turn-by-turn conversation elements,
(2) all available OpenAI LLM inference and embedding models,
(3) additional error handling and reporting of incorrect call structures and values, and
(3) a new API docs interface for testing individual calls.
We will continue to develop new features within our development environments (“dev”, “test”) that will include the latest features and enhancements implemented for testing before releasing to prod. We now strongly recommend switching your existing calls to the production environment and no longer routinely use dev or test, unless you are helping evaluate new functionality.

Please refer to the table of contents on the right side of this document for navigation → → → or Try out Box AI to “chat” with this document to expedite answers to your questions.

Argo Gateway API deployed to production! All latest stable features are now available in production.

Update your endpoints to:

https://apps.inside.anl.gov/argoapi/api/v1/resource/chat/
https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/
API explore web interface (Swagger UI): https://apps.inside.anl.gov/argoapi/docs
Test your API calls from your browser.

IMPORTANT: All API calls should include your ANL domain name
Please use your ANL domain name in the “user” field of your Argo calls. If you would like to create a service account to represent an application calling Argo, please reach out to mdearing@anl.gov for instructions.

In the near future, we will be adding authentication to make sure that the username included in the Argo API call is valid.

What’s New!
NEW! Claude Haiku 4.5 model is available. See details below. It’s fast. It’s good. It’s cheaper! :-)
If you are using a local host with argo-proxy, simply restart your host and the Claude Haiku 4.5 model will be available. No library upgrade required.
Important: You can only specify ONE of temperature or top_p, not both. So: Argo API does not pass either — only if you set one or the other.
Available in the dev endpoint only for testing.
If you are vibe coding with Continue.dev (with Argo), the config file template has been updated to include Claude Haiku 4.5. Grab the update here.
NEW! Tool / Function Calling with OpenAI, Google, and Anthropic models. Let’s build some agents!
Available only on at the dev endpoint and through the argo-proxy OpenAI-compatible interface. Please consider this very much a beta release.
When you start out, run some basic testing to verify it is working for your code before running large/long processes.
The function call schemas for OpenAI, Google, and Anthropic LLMs are all a bit different, so there are likely some more complex scenarios we have not test for yet that will trip things up. Specifically, there may still be some issues to Gemini models, but with your detailed sharing of any errors, we can knock out fixes asap.
For the /chat endpoint, tool calling for all LLM vendors is fully functional. For the /streaming endpoint, the tool calling is currently disabled and will return an informational error.
Initial documentation is available (here!) that contains sample code blocks and example scripts you can test out basic tool calling techniques. These documents are just the beginning and do not provide an introduction to LLM tool calling techniques. So, there is an expectation right now that as a user, you have some familiarity with this approach.
If you find any edits or would like to contribute more complex samples that would be useful for the community, please share with me at mdearing@anl.gov.
Prior Updates
Claude Sonnet 4.5 model is available.
If you are using a local host with argo-proxy, simply restart your host and the Claude Sonnet 4.5 model will be available. No library upgrade required.
You can only specify ONE of temperature or top_p, not both.
Available in the dev endpoint only for testing.
If you are vibe coding with Continue.dev (with Argo), the config file template has been updated to include Claude Sonnet 4.5.
Claude Opus 4.1 model is now available.
If you are using a local host with argo-proxy, simply restart your host and the Claude Opus 4.1 model will be available. No library upgrade required.
If you are vibe coding with Continue.dev (with Argo), the config file template has been updated to include Claude Opus 4.1.
OpenAI GPT-5 model suite now available.
If you are using a local host with argo-proxy, simply restart your host and the GPT-5 models will be available. No library upgrade required.
If you are vibe coding with Continue.dev, the config file template has been updated to include GPT-5.
Ready for testing/feedback: Streaming endpoint
Now available for testing and use in the API apps-dev environment, we have a separate endpoint to return streaming responses through the Argo Gateway API:

https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/

The streaming endpoint is now working for all OpenAI, Google, and Anthropic models.

A Python testing script is available as a starting point here: argoapi_streamchat_test.py
Please note that the httpx library is used to enable streaming and the requests library does not support this feature.

If you want to take a look at some interesting metadata of the streaming text returned from the LLMs, then you can use this testing script: argoapi_streamchat_metadata_test.py

Please test and feedback: A few more error handling needs to still be included and I welcome your feedback ASAP. As soon as we feel this endpoint is stable, then we can push it through to production. Post your testing results/experience in the Teams Argo API CoP or email mdearing@anl.gov.

More OpenAI models are here!
These latest models are available as for use in the API apps-dev environment for testing (apps-dev). Model IDs:

gpto3 | gpto4mini | gpt41 | gpt41mini | gpt41nano
Google Gemini and Anthropic Claude models are here!
These latest models are available as for use in the API apps-dev environment for testing (apps-dev). Initially, we have these accessible for text-only via the /chat/ (non-streaming) endpoint. There are also some different configuration requirements and options compared to OpenAI models.

Model IDs: gemini25pro | gemini25flash | claudeopus4 | claudesonnet4 | claudesonnet37 | claudesonnet35v2

Want to Vibe Code with Argo?
Check out the new instructions documentation: https://anl.box.com/s/hxc72dkm0a8mlmo7ownfl4ixwx6iu3ko — please let Matthew Dearing know what you think and share any edits/suggestions. Thank you!

Continue, Cline, aider, Void IDE:

The o1 model is now available as for use in the API apps-dev environment for testing (apps-dev). Please note that the prompting structure allows for separate “system” and “user” prompts. However, all o-series reasoning models do not accept “temperature” and “top_p” and requires “max_completion_tokens” instead of “max_tokens”. (Read more)
The latest snapshot of GPT-4o (“2024-11-20”) model is now available as for use in the API apps-dev environment for testing (apps-dev). Please use the model name: gpt4olatest.
The o3-mini model is now available as for use in the API apps-dev environment for testing (apps-dev). It does not accept “temperature” and “top_p” and requires max_completion_tokens instead of max_tokens.
The o1-mini model is now available as for use in the API apps-dev environment for testing (apps-dev). The prompting structure is similar to o1-preview; the model does not accept the “system” prompt.
Getting started and connected
Quick Starts are available below in the ‘Example & Code Template’ sections for the Chat Completion and Embedding endpoint.

Recommendation: If you do not have a local Python development environment already configured, then we recommend downloading and installing Postman (free for individual use) as the most straightforward way to test calling the Argo Gateway API. Or, you may use the Argo API test docs UI at:

DEV: https://apps-dev.inside.anl.gov/argoapi/docs
PROD: https://apps.inside.anl.gov/argoapi/docs
Usage request (general users)
At this time, you are welcome to leverage the Argo Gateway API for your Argonne-focused LLM-as-a-service needs.

Because each call to Argo incurs a small cost per prompt and per response with GPT-3.5, GPT-4, GPT-4o, GPT o1-preview, and all text embedding models, we ask that any large or long-term, automated runs are first reviewed and coordinated with Matthew Dearing, mdearing@anl.gov, for awareness.

For large (and expensive) runs, we can work with you and your division to configure an existing funded project pay for any high-volume use of the GPT models through Argo. Please reach out to Matthew Dearing (mdearing@anl.gov) for more information. Your cooperation will help with transparency of early user while we continue to develop this service and help ensure funds are available to support your needs.

Usage request (within CELS)
We have a separate collection of the same GPT LLMs for exclusive use by Argo users within CELS. If you are an Argo Gateway API user working on a CELS-funded project, then you now have the option to utilize the OpenAI models that are financially supported by CELS.

Current process:

To use the CELS-funded models in your API calls, you first need to be included in a special user role that will enable your access.
This role-based user feature allows you to set the “user” field to your ANL domain name or a service account to gain access the CELS-specific OpenAI models.
Action: If you are a user of the CELS Argo LLM models, then please email:

Craig Stacey (stace@anl.gov)
Anthony Avarca (aavarca@anl.gov) to be included in this role.
Technical Questions
For technical questions, please contact Matthew Dearing (mdearing@anl.gov)

We have an Argo API CoP group on Teams — please let Matthew know if you would like to join this channel to contribute to the continued development and use cases of the Argo Gateway API. You will have notifications of the latest updates and direct access for questions and discussions related to the use of the Argo Gateway API.

Enhancement Requests
To request an enhancement, please use Vector to ‘Make a Request’ and select the ‘Argonne Application Enhancement’ item. On the form, enter “Argo Gateway API Prod” as the Application Service Name.

Special Networking Connection Needs
The machine or server making the API calls to Argo must be connected to Argonne internal network or through VPN on an Argonne-managed computer if you are working off-site. If your internal Argonne machine does not have access to the apps.inside.anl.gov domain space, then a firewall conduit can be configured to enable access from your local IP address to the Argo Gateway API.

To request this firewall conduit, please submit a Vector ticket here:

Description: “Need access to the Argo Gateway API endpoints.”
Object Group Information: Select “BIS_Argo_Access” from the drop-down menu
Object-Group Additions: Click [Add] button
Pop-up window: IP Address or Network: Enter IP address. Repeat the process to add more than one IP address.
Feature Listing
Exponential backoff is included to support concurrent response during high-volume use and alleviate bottlenecks if we experience token count limits by the LLM hosting service (Azure).
Informative error handling for incorrect API calls details or structure.
Two ways to prompt (1) pass the complete “messages” object or (2) individual “system” and “prompt” (user) fields.
… (TODO: fill out this list)
Coming soon
The current token count rate for cumulative incoming requests is set at 240,000 tokens per minute. This rate is dynamically increased as resources are available within the Azure instance that hosts the selected LLM. We expect to be able to request higher rates in the future — but this limit is what we have today.

To alleviate code crashes (or what appear to be timeouts) when this limit is reached during high volume API call routines, we will implement an exponential backoff process that will briefly pause your next request until the one-minute timing is reset. This will eliminate the need for users to manage this server error responses and should allow for fairness in the pausing of requests when multiple users are calling the API simultaneously.

Argo Community Developer Code Share
We have a DOE-hosted GitLab repository (offered through DOE CODE) to curate our Argonne community development of Argo-related codes and tools, such as a proxy to make Argo compatible with OpenAI calls. This repository is public so anyone here can clone tools for use within your Argonne-related work.

https://gitlab.osti.gov/ai-at-argonne

If you are interested in contributing your code (everyone is welcome!), please email Matthew Dearing (mdearing@anl.gov). A quick registration process required with DOE CODE to give you contributor access, and then we will set up a new project for you to push your code. Detailed instructions for this process are available here.

Endpoint: Chat Completion
POST to (PROD environment)
https://apps.inside.anl.gov/argoapi/api/v1/resource/chat/

or POST to (TEST environment)
https://apps-test.inside.anl.gov/argoapi/api/v1/resource/chat/

or POST to (DEV environment)
https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/

Structure of the API Call Object
Required: Please include your personal Argonne domain account user name or a service account in the “user” field. This value is logged so we can track usage at the Division level. If you created a service account to represent calls from an application, then this name may be included in the “user” field instead.

Option 1: Messages Object
Sample Python script: [ https://anl.box.com/s/aza35gmlti5ylh8ae2w3onhqkaprowda ]

json
{
  "user": "<your ANL domain user, e.g., mdearing>",
  "model": "<required, input a valid name>",
  "messages": [
    {"role": "system",
      "content": "You are a large language model with the name Argo"},
    {"role": "user",
      "content": "What is your name?"},
    {"role": "assistant",
      "content": "My name is Argo."},
    {"role": "user",
      "content": "What are you?"}
  ],
  "stop": [],
  "temperature": 0.1,
  "top_p": 0.9
}
Important for o1-preview and o1-mini:
This LLM model only accepts the {"role": "user", "content": "<your prompt>"} dictionary in the messages object. The “system”, “temperature”, “top_p”, and “max_tokens” field values will be ignored.

Option 2: Singular System + prompt
Sample Python script: [ argoapi_chat_test.py ]

json
{
  "user": "<your ANL domain user, e.g., mdearing>",
  "model": "<required, input a valid name>",
  "system": "<NULL, or e.g., You are a large language model with the name Argo",
  "prompt": ["what is your name?"],
  "stop": [],
  "temperature": 0.1,
  "top_p": 0.9,
  "max_tokens": 1000,
  "max_completion_tokens": 1000
}
Important for o1-preview and o1-mini:
This LLM model only accepts the "prompt": ["<your prompt>"] field. The “system”, “temperature”, “top_p”, and “max_tokens” field values will be ignored.

Valid LLM Model Names
Streaming and tool/function calling is available in all models unless specified. The model field must include one of the following strings:

OpenAI
gpt35 GPT-3.5 Turbo: 4,096 max token input Training data: up to Sept 2021
gpt35large GPT-3.5 Turbo 16k: 16,384 max token input Training data: up to Sept 2021
gpt35large GPT-4: 8,192 max token input Training data: up to Sept 2021
gpt4large GPT-4 32k: 32,768 max token input Training data: up to Sept 2021
gpt4turbo GPT-4 Turbo: 128,000 max token input, 4,096 max token output Training data: up to Dec 2023 (slower response)
gpt4o GPT-4o “2024-08-06”: 128,000 max token input, 16,384 max token output Training data: up to Oct 2023 Text-based interactions only
gpt4olatest - For all users, only in dev. GPT-4o “2024-11-20”: 128,000 max token input, 16,384 max token output Training data: up to Oct 2023 Text-based interactions only
gpto1preview o1-preview will be retired on July 27, 2025! GPT o1-preview: 128,000 max token input, 32,768 max token output Training data: up to Oct 2023 Tools/function calling not supported. Text-based interactions only. NOTE: Only the “user prompt” and “max_completion_tokens” fields are used for this model.
gpto1mini - For all users, only in dev. GPT o1-mini: 128,000 max token input 65,536 max token output Training data: up to Oct 2023 Does not accept system role in the messages object. Tools/function calling not supported.
gpto3mini - For all users, only in dev. GPT o3-mini: 200,000 max token input (context window) 100,000 max token output (completion tokens) Does not accept “temperature”, “top_p”, and “max_tokens” Does accept “max_completion_tokens”
gpto1 - For all users, only in dev. GPT o1: 200,000 max token input 100,000 max token output Does not accept “temperature”, “top_p”, and “max_tokens” Does accept “max_completion_tokens”
gpto3 - For all users, only in dev. Does not accept “temperature”, “top_p”, and “max_tokens” Does accept “max_completion_tokens”
gpto4mini - For all users, only in dev. Does not accept “temperature”, “top_p”, and “max_tokens” Does accept “max_completion_tokens”
gpt41 - For all users, only in dev. Does accept “temperature”, “top_p”, and “max_completion_tokens” 1,000,000 max tokens input (context window) 16,384 max token output (completion tokens)
gpt41mini - For all users, only in dev. Does accept “temperature”, “top_p”, and “max_completion_tokens” 1,000,000 max tokens input 16,384 max token output
gpt41nano - For all users, only in dev. Does accept “temperature”, “top_p”, and “max_completion_tokens” 1,000,000 max tokens input 16,384 max token output
gpt5 - For all users, only in dev. Does accept “temperature”, “top_p”, and “max_completion_tokens” Does not accept “max_tokens”. 272,000 max tokens input (context window) 128,000 max token output Training Data: Up To October 24, 2024
gpt5mini - For all users, only in dev. Does accept “temperature”, “top_p”, and “max_completion_tokens” Does not accept “max_tokens”. 272,000 max tokens input 128,000 max token output Training Data: Up To June 24, 2024
gpt5nano - For all users, only in dev. Does accept “temperature”, “top_p”, and “max_completion_tokens” Does not accept “max_tokens”. 272,000 max tokens input 128,000 max token output Training Data: Up To May 31, 2024
Google
gemini25pro - For all users, only in dev. Google Gemini Pro 2.5. Text-only model (for now). 1,048,576 max tokens input 65,536 max tokens output. The Argo ‘max_tokens’ field maps to Gemini’s ‘max_output_tokens’ field. The Argo ‘stop’ field maps to Gemini’s ‘stop_sequences’ field. Requires user prompt content. Thinking features not yet enabled.
gemini25flash - For all users, only in dev. Google Gemini 2.5 Flash. Text-only model (for now). 1,048,576 max tokens input 64,536 max tokens output. Same mapping notes as gemini25pro.
Anthropic
claudeopus41 - For all users, only in dev. Anthropic Claude Opus 4.1 200,000 max tokens input 32,000 max tokens output. Text-only model (for now). Requires user prompt content. Requires max_tokens, temperature, top_p to be set. Defaults if not provided: max_tokens = 21000, temperature = 0.7, top_p = 0.9. NOTE: More than 21,000 output tokens requires streaming mode.
claudeopus4 - For all users, only in dev. Anthropic Claude Opus 4 200,000 max tokens input 32,000 max tokens output. Similar requirement and defaults as above.
claudehaiku45 - For all users, only in dev. Anthropic Claude Haiku 4.5 200,000 max tokens input 64,000 max tokens output. Does NOT ACCEPT both temperature and top_p parameters. Pass only one or neither. If both are passed, then top_p is ignored and temperature passes. NOTE: More than 21,000 output tokens requires streaming mode.
claudesonnet45 - For all users, only in dev. Anthropic Claude Sonnet 4.5 200,000 max tokens input 64,000 max tokens output. Does NOT ACCEPT both temperature and top_p parameters. NOTE: More than 21,000 output tokens requires streaming mode.
claudesonnet4 - For all users, only in dev. Anthropic Claude Sonnet 4 200,000 max tokens input 64,000 max tokens output. Requires max_tokens, temperature, top_p. Defaults if not provided. NOTE: More than 21,000 output tokens requires streaming mode.
claudesonnet37 - For all users, only in dev. Anthropic Sonnet 3.7 200,000 max tokens input 128,000 max tokens output. Requires max_tokens, temperature, top_p. NOTE: More than 21,000 output tokens requires streaming.
claudesonnet35v2 - For all users, only in dev. Anthropic Sonnet 3.5 v2 200,000 max tokens input 8,000 max tokens output. Requires max_tokens, temperature, top_p. Defaults if not provided: max_tokens = 8000, temperature = 0.7, top_p = 0.9.
claudehaiku35 - For all users, only in dev. Anthropic Claude Haiku 3.5. Requires max_tokens, temperature, top_p. Defaults if not provided.
Additional Fields
stop - Default value: null
Type: String or array Optional
Up to four sequences where the API will stop generating further tokens. The returned text won’t contain the stop sequence. Not available for the GPT o1-preview model.
temperature - Default value: null
Type: number Optional
What sampling temperature to use, between 0 and 2. Higher values mean the model takes more risks. Try 0.9 for more creative applications, and 0 (argmax sampling) for ones with a well-defined answer. We generally recommend altering this or top_p but not both. Not available for the GPT o1-preview model.
top_p - Default value: null
Type: number Optional
An alternative to sampling with temperature, called nucleus sampling. We generally recommend altering this or temperature but not both. Not available for the GPT o1-preview model.
max_tokens - Default: null
Type: integer Optional
The maximum number of tokens to generate in the completion. The token count of your prompt plus max_tokens can’t exceed the model’s context length. Not available for the GPT o1-preview model.
max_completion_tokens - Default: null
Type: integer Optional
Only available for the GPT o1-preview model.
Example & Code Template
Example Python scripts: [ argoapi_chat_test.py ] and [ argoapi_chat_messages_test.py ]

Example using the Postman API platform (using system + prompt fields): (example omitted here; see code samples above)

If an invalid model value is passed in the model field, then the API will return an error response indicating an invalid model.

Endpoint: Embeddings
POST to (PROD environment)
https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/

or POST to (TEST environment)
https://apps-test.inside.anl.gov/argoapi/api/v1/resource/embed/

or POST to (DEV environment)
https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/

Structure of the API Call Object
Required: Please include your personal Argonne domain account user name or a service account in the “user” field. This value is logged so we can track usage at the Division level. If you created a service account to represent calls from an application, then this name may be included in the “user” field instead.

json
{
  "user": "<your ANL domain user, e.g., mdearing>",
  "model": "<required, input a valid name>",
  "prompt": [
    "string_one",
    "string_two",
    "string_three"
  ]
}
Valid LLM Model Names (Embeddings)
Three text embedding models are available for all users:

Model	Max input tokens	Output dimension
ada002 (text-embedding-ada-002)	8,191	1,536
v3large (text-embedding-3-large)	8,191	3,072
v3small (text-embedding-3-small)	8,191	1,536
Maximum number of elements in the prompt list: 16 – the return object will include a separate embedding as a 1D array/list for each string in the prompt list.

Example & Code Template (Embeddings)
Example Python script: [ argoapi_embedding_test.py ]

Example using the Postman API platform: (example omitted in-line here; see above resources)