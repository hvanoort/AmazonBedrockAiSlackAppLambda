import json

from amazon_bedrock_ai_slack_app_lambda.helpers.constants import (
    DEFAULT_ASSISTANT_PROMPT,
    DISCLAIMER_TAG,
    PII_SYSTEM_MESSAGE_TAG,
    SYSTEM_MESSAGES,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER


def __get_assistant_prompt(model_name, history, user_input):
    """
    Generates a conversation prompt for various AI models.

    Parameters:
    - model_name (str): The name of the AI model ('claude-v2', 'claude-instant', 'titan', 'llama2').
    - history (str): The conversation history between the human and the AI.
    - user_input (str): The human's next reply in the conversation.

    Returns:
    str: The formatted conversation prompt for the specified AI model.
    """

    prompt_format = {
        "claude": """Human:{initial_prompt}

The conversation history is given below for context.
<conversation_history>
{history}
</conversation_history>

Human: {user_input}

Assistant:
""",
    }

    return prompt_format.get(model_name, "").format(initial_prompt=DEFAULT_ASSISTANT_PROMPT, history=history,
                                                    user_input=user_input)


def __get_passthrough_prompt(model_name, history, user_input):
    """
    Generates a conversation prompt for various AI models without inital prompt.

    Parameters:
    - model_name (str): The name of the AI model ('claude-v2', 'claude-instant', 'titan', 'llama2').
    - history (str): The conversation history between the human and the AI.
    - user_input (str): The human's next reply in the conversation.

    Returns:
    str: The formatted conversation prompt for the specified AI model.
    """
    prompt_format = {
        "claude": """Human:
{history}
Human: {user_input}
Assistant:
""",
    }

    return prompt_format.get(model_name, "").format(history=history, user_input=user_input)


def __generate_claude_prompt(messages, bot_user_id, mode):
    """
    Generate a conversation prompt for a Anthropic Claude models based on a list of messages and the bot's user ID.

    :param messages: A list of messages, each represented as a dictionary.
                     Each message dictionary should contain 'user' and 'msg' keys.
    :param bot_user_id: The user ID of the bot.
    :return: A formatted string representing the conversation prompt.
    """
    model_name = 'claude'

    bot_user_id_msg = f"<@{bot_user_id}>"
    last_message = ""
    #  find the last non bot message and replace bot mention with 'Bot'
    for message in reversed(messages):
        if message['user'] != bot_user_id:
            last_message = message['msg'].replace(bot_user_id_msg, 'Bot')
            break

    LOGGER.debug("Messages: {}".format(messages))
    history = ""
    for idx, msg in enumerate(messages):
        if idx < len(messages) - 1:
            # Check if command or system message
            stripped_message: str = msg["msg"].strip()
            is_system_message = (stripped_message.startswith(SYSTEM_MESSAGES)
                                 or PII_SYSTEM_MESSAGE_TAG in stripped_message
                                 or DISCLAIMER_TAG in stripped_message)

            if not is_system_message:
                speaker = "Assistant" if msg["user"] == bot_user_id else "Human"
                history += f"\n\n{speaker}: {msg['msg'].replace(bot_user_id_msg, 'Bot')}"

    if mode == 'assistant':
        return __get_assistant_prompt(model_name, history, last_message)
    if mode == 'passthrough':
        return __get_passthrough_prompt(model_name, history, last_message)


def __generate_claude_v3_prompt(messages, bot_user_id, mode):
    """
    Generate a conversation prompt for a Anthropic Claude v3 Sonet models based on a list of messages and the bot's user ID.

    :param messages: A list of messages, each represented as a dictionary.
                     Each message dictionary should contain 'user' and 'msg' keys.
    :param bot_user_id: The user ID of the bot.
    :return: A formatted list of dict(role: str, content: str) representing the conversation prompt.
    """
    bot_user_id_msg = f"<@{bot_user_id}>"

    LOGGER.debug("Messages: {}".format(messages))
    history = []
    speakers = ["user", "assistant"]
    current_speaker = None
    for msg in messages:
        # Check if command or system message
        stripped_message: str = msg["msg"].strip()
        is_system_message = (
            stripped_message.startswith(SYSTEM_MESSAGES)
            or PII_SYSTEM_MESSAGE_TAG in stripped_message
            or DISCLAIMER_TAG in stripped_message
        )

        if not is_system_message:
            speaker = "assistant" if msg["user"] == bot_user_id else "user"

            if current_speaker == speaker:
                history.append(
                    {"role": speakers[1 - speakers.index(speaker)], "content": "-"}
                )

            content = stripped_message.replace(bot_user_id_msg, 'Bot')
            history.append({'role': speaker, 'content': content})
            current_speaker = speaker

    return history


def generate_payload(messages, bot_user_id, model, mode):
    """
    Generate payload for making a request to a language model.

    :param messages: A list of messages, each represented as a dictionary.
                     Each message dictionary should contain 'user' and 'msg' keys.
    :param bot_user_id: The user ID of the bot.
    :param model: A dictionary containing information about the language model,
                  including its name, max_token_sample, model_id, accept, and content_type.
    :return: A dictionary containing the payload for the language model request.
    """

    LOGGER.info("Generating payload using settings: model:={}".format(model))

    body = {}

    if model.get("name") in ["claude-v2", "claude-instant"]:
        body["prompt"] = __generate_claude_prompt(messages, bot_user_id, mode)
        body["max_tokens_to_sample"] = model.get("max_token_sample")
        body["temperature"] = 0.5

    if model.get('name') == 'claude-v3-sonet':
        body["anthropic_version"] = "bedrock-2023-05-31"
        body["max_tokens"] = model.get("max_token_sample")
        body["system"] = DEFAULT_ASSISTANT_PROMPT if mode == 'assistant' else ""
        body["messages"] = __generate_claude_v3_prompt(messages, bot_user_id, mode)
        body["temperature"] = model.get("temperature")

    return {
        "body": json.dumps(body),
        "model_name": model.get("name"),
        "model_id": model.get("id"),
        "accept": model.get("accept"),
        "content_type": model.get("content_type"),
    }
