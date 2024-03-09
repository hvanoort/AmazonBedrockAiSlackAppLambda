import json
import urllib.parse
import urllib.request

from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER
from amazon_bedrock_ai_slack_app_lambda.helpers.secrets_helper import get_bot_user_token
from amazon_bedrock_ai_slack_app_lambda.helpers.utils import get_sorted_messages
from amazon_bedrock_ai_slack_app_lambda.validation.slack_params_validator import (
    SLACK_PARAMETER_VALIDATOR,
)

SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
SLACK_USER_INFO_URL = "https://slack.com/api/users.info?user="
SLACK_UPDATE_CHAT_URL = "https://slack.com/api/chat.update"
SLACK_CONVERSATION_HISTORY = "https://slack.com/api/conversations.history"
SLACK_CONVERSATION_REPLIES = "https://slack.com/api/conversations.replies"
SLACK_CONVERSATION_INFO = "https://slack.com/api/conversations.info"
SLACK_AUTH_TEST = "https://slack.com/api/auth.test"


def get_channel_type(channel_id):
    """
    Retrieve the conversation info , like IM/Private/Chat/etc based on channel id.
    :param channel_id:
    :return: slack api response
    """
    SLACK_PARAMETER_VALIDATOR.validate_channel_id(channel_id)
    data = {
        "channel": channel_id,
    }

    data_content = urllib.parse.urlencode(data).encode("ascii")

    headers = {"Authorization": "Bearer " + get_bot_user_token()}

    request = urllib.request.Request(SLACK_CONVERSATION_INFO, data=data_content, headers=headers)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    response_json = json.loads(response.decode("utf-8"))
    LOGGER.debug("slack_conversation_info = {}".format(response_json))
    if response_json.get('channel').get('is_im'):
        return 'im'

    return 'channel'


def get_bot_user_id():
    """
    This method checks authentication and tells "you" who you are, even if you might be a bot.
    :return: slack api response
    """

    headers = {"Authorization": "Bearer " + get_bot_user_token()}

    request = urllib.request.Request(SLACK_AUTH_TEST, headers=headers)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    response_json = json.loads(response.decode("utf-8"))

    LOGGER.debug("get_bot_user_id = {}".format(response_json))
    return response_json.get("user_id")


def get_thread_replies(channel_id, parent_ts):
    """
    Retrieve the conversation replies the conversation conversations.replies API.
    :param channel_id:
    :param parent_ts: parent message ts
    :return: slack api response
    """
    SLACK_PARAMETER_VALIDATOR.validate_channel_id(channel_id)
    data = {
        "channel": channel_id,
        "ts": parent_ts,
    }

    data_content = urllib.parse.urlencode(data).encode("ascii")

    headers = {"Authorization": "Bearer " + get_bot_user_token()}

    request = urllib.request.Request(SLACK_CONVERSATION_REPLIES, data=data_content, headers=headers)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    response_json = json.loads(response.decode("utf-8"))

    LOGGER.debug("get_conversation_history = {}".format(response_json))
    return get_sorted_messages(response_json.get("messages"))


def get_conversation_history(channel_id, limit):
    """
    Retrieve the conversation history for a Slack channel using the conversations.history API.
    :param channel_id:
    :return: slack api response
    """
    SLACK_PARAMETER_VALIDATOR.validate_channel_id(channel_id)
    data = {
        "channel": channel_id,
        "limit": limit,
    }

    data_content = urllib.parse.urlencode(data).encode("ascii")

    headers = {"Authorization": "Bearer " + get_bot_user_token()}

    request = urllib.request.Request(SLACK_CONVERSATION_HISTORY, data=data_content, headers=headers)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    response_json = json.loads(response.decode("utf-8"))

    LOGGER.debug("get_conversation_history = {}".format(response_json))
    return get_sorted_messages(response_json.get("messages"))


def send_chat(channel_id, response_message, parent_ts=None):
    """
    Sends a new message to the channel.
    :param channel_id:
    :param response_message:
    :return: slack api response
    """
    SLACK_PARAMETER_VALIDATOR.validate_channel_id(channel_id)
    data = {
        "token": get_bot_user_token(),
        "channel": channel_id,
        "text": response_message,
    }
    if parent_ts:
        data['thread_ts'] = parent_ts

    LOGGER.info("Sending message at {}".format(channel_id))
    data_content = urllib.parse.urlencode(data).encode("ascii")

    request = urllib.request.Request(SLACK_POST_MESSAGE_URL, data=data_content, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    LOGGER.debug("send_chat = {}".format(json.loads(response.decode("utf-8"))))
    return response


def update_chat(bedrock_invoker_metadata, response_message, parent_ts):
    """
    Updates the message with the parent_ts timestamp with the new message.
    :param bedrock_invoker_metadata: metadata
    :param response_message:
    :param parent_ts:
    :return: slack api response
    """
    SLACK_PARAMETER_VALIDATOR.validate_channel_id(bedrock_invoker_metadata.channel_id)
    SLACK_PARAMETER_VALIDATOR.validate_disclaimer_ts(parent_ts)
    data = {
        "token": get_bot_user_token(),
        "channel": bedrock_invoker_metadata.channel_id,
        "text": response_message,
        "ts": parent_ts,
    }
    LOGGER.info("Updating message at {}/{}".format(bedrock_invoker_metadata.channel_id, parent_ts))
    data_content = urllib.parse.urlencode(data).encode("ascii")

    request = urllib.request.Request(SLACK_UPDATE_CHAT_URL, data=data_content, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    LOGGER.debug("update_chat = {}".format(json.loads(response.decode("utf-8"))))
    return response


def get_user_from_userid(user):
    """
    Gets user details from slack.
    :param user:
    :return: slack api response
    """
    url = SLACK_USER_INFO_URL + user
    headers = {"Authorization": "Bearer " + get_bot_user_token()}

    request = urllib.request.Request(url, headers=headers)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    response = urllib.request.urlopen(request).read()
    LOGGER.debug("get_user_from_userid = {}".format(json.loads(response.decode("utf-8"))))
    return json.loads(response.decode("utf-8"))
