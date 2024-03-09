from amazon_bedrock_ai_slack_app_lambda.helpers.argument_parser import CustomArgumentParser
from amazon_bedrock_ai_slack_app_lambda.helpers.constants import (
    AVAILABLE_MODELS,
    AVAILABLE_MODES,
    DEFAULT_MODE,
    DEFAULT_MODEL,
    MODE_DESCRIPTION,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.ddb_helper import get_user_settings, save_settings
from amazon_bedrock_ai_slack_app_lambda.helpers.error_message_helper import (
    send_invalid_model_id_mode_message,
    settings_parse_error,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER
from amazon_bedrock_ai_slack_app_lambda.helpers.slack_helper import send_chat
from amazon_bedrock_ai_slack_app_lambda.helpers.utils import validate_and_set
from amazon_bedrock_ai_slack_app_lambda.validation.user_validator import validate_slack_user  # noqa: F401


SETTINGS_PARSER = CustomArgumentParser(description='parse settings')
SETTINGS_PARSER.add_argument('--model-id', metavar='N', type=str, nargs='?', default=None, help='Bedrock model id')
SETTINGS_PARSER.add_argument('--mode', metavar='N', type=str, nargs='?', default=None, help='Chat mode')


def handle_command(channel_id, user_id, message, bot_user_id, thread_ts=None):
    """
    Handle user commands in a Slack environment.

    :param channel_id: Slack Channel_id.
    :param message: Slack Incomming Message.
    :param available_models: List of supported models.
    :param default_model: Default model to be used.
    :return: A dictionary indicating the status of the command execution; None if the message was not a command
    """

    if message.startswith(f'<@{bot_user_id}>'):
        message_parts = message.split(' ')
        if len(message_parts) > 1:
            message = ' '.join(message_parts[1:]).strip()
        else:
            message = ''

    if message.startswith("help"):
        return __help_command(channel_id, thread_ts)
    elif message.startswith("settings"):
        return __save_settings(channel_id, user_id, message, thread_ts)
    elif message.startswith("list-settings"):
        return __user_settings(channel_id, user_id, thread_ts)
    elif message.startswith("new-conversation"):
        return __new_conversation(channel_id)
    else:
        LOGGER.debug("Input {} is not a valid command..".format(message))
        return None


def __new_conversation(channel_id):
    send_chat(
        channel_id,
        "[SYSTEM] Starting new conversation. Previous messages will be ignored.",
    )
    return {"status": "success"}


def __user_settings(channel_id, user_id, thread_ts=None):
    """
    Retrieve user settings, format them, and send a chat message with the formatted settings.

    :param channel_id: Slack Channel_id.
    :param user_id: Slack User_id.

    :return: A dictionary indicating the status of the command execution;
    """
    try:
        LOGGER.debug("Getting user settings")
        settings = get_user_settings(channel_id, user_id)
        formatted_settings = "\n>".join(f"{key}: _{value}_" for key, value in settings.items())
        send_chat(channel_id, "[SYSTEM] Your settings are:\n>{}".format(formatted_settings), thread_ts)
        return {"status": "success"}
    except Exception as e:
        LOGGER.error("Could not get user settings error:={}".format(str(e)))
        return {"status": "error"}


def __save_settings(channel_id, user_id, message, thread_ts=None):
    """
    settings --modelId
    """
    arguments = message.split(" ")[1:]
    try:
        args = SETTINGS_PARSER.parse_args(arguments)

        settings = get_user_settings(channel_id, user_id)
        selected_model = validate_and_set(args.model_id, AVAILABLE_MODELS, DEFAULT_MODEL, settings.get('model_id', ''))
        selected_mode = validate_and_set(args.mode, AVAILABLE_MODES, DEFAULT_MODE, settings.get('mode', ''))

        if not selected_model or not selected_mode:
            invalid_model_id = args.model_id if not selected_model else None
            invalid_mode = args.mode if not selected_mode else None
            send_invalid_model_id_mode_message(channel_id, invalid_model_id, invalid_mode, thread_ts)
            return {"status": "failure"}

        # if not validate_slack_user(channel_id, login, 'model', selected_model):
        #     return {"status": "failure"}

        if save_settings(channel_id, user_id, model_id=selected_model, mode=selected_mode):
            send_chat(channel_id, "[SYSTEM] Settings saved successfully", thread_ts)
            return {"status": "success"}
        else:
            return {"status": "failure"}
    except AssertionError as e:
        settings_parse_error(channel_id, SETTINGS_PARSER, e, thread_ts)
        return {"status": "failure"}


def __help_command(channel_id, thread_ts=None):
    LOGGER.info("Processing help command")
    models_info = "\n".join(
        [f"> {idx + 1}. `{model}`" for idx, model in enumerate(AVAILABLE_MODELS)]
    )
    modes_info = "\n".join(
        [f"> {idx + 1}. `{mode}` - {MODE_DESCRIPTION.get(mode)}" for idx, mode in enumerate(AVAILABLE_MODES)]
    )
    send_chat(
        channel_id,
        "[SYSTEM] :rock: *Welcome to Bedrock App Help Center* :rock:"
        "\n\nNeed assistance? You're in the right place! Below are available commands to get you started:"
        "\n\n1. `settings --model-id <modelId> --mode <mode>` : Sets desired model, mode."
        f"\n\n>By default model is set to *{DEFAULT_MODEL}* and mode is set to *{DEFAULT_MODE}*."
        f"\nSupported model-ids are: \n{models_info}"
        f"\nSupported modes are: \n{modes_info}"
        "\n\n2. `list-settings` : Lists currently set settings"
        "\n\n3. `new-conversation` : Starts new conversation, all history prior to this command is ignored"
        f"\n\nFor more info refer to the wiki - https://w.amazon.com/bin/view/BedrockChatSlackApp/"
        "\n\nHappy exploring!",
        thread_ts
    )
    return {"status": "success"}
