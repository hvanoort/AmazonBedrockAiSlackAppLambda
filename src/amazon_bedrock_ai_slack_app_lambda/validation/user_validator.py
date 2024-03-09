from amazon_bedrock_ai_slack_app_lambda.helpers.allowlist import ALLOWLISTED_USERS
from amazon_bedrock_ai_slack_app_lambda.helpers.error_message_helper import (
    slack_user_validation_error,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER


def validate_slack_user(channel_id, login, check_type, model_id=None, thread_ts=None):
    """
    Validates whether a Slack user is authorized based on the whitelist.

    :param channel_id (str): The ID of the Slack channel.
    :param login (str): The login name of the Slack user.
    :param check_type (str): Depending on the check type different error message is send. Available values model/user.
    :param model_name (str): The name of the model.

    Returns:
        bool: True if the user is authorized, False otherwise.
    """

    user_error_message = "BedrockChat App is in limited private beta release and is available only to a limited user set. Please reach out via bedrock-chat-slack-app@amazon.com for any access related queries. Thank you!"
    model_error_message = "User is not authorised to use selected model. Please reach out via bedrock-chat-slack-app@amazon.com for any access related queries. Thank you!"

    model_users = ALLOWLISTED_USERS.get(model_id, [])
    all_models = ALLOWLISTED_USERS.get('all', [])

    if login not in model_users and login not in all_models:
        LOGGER.error("USER_NOT_FOUND - login: {} channel_id: {} model_id: {}".format(login, channel_id, model_id))
        slack_user_validation_error(channel_id=channel_id, error_string=user_error_message if check_type == 'user' else model_error_message, thread_ts=thread_ts)
        return False
    return True
