from amazon_bedrock_ai_slack_app_lambda.helpers.error_message_helper import (
    bedrock_response_validation_error,
    slack_request_message_validation_error,
)

MAX_REQUEST_MESSAGE_SIZE = 20000
MAX_RESPONSE_MESSAGE_SIZE = 10000


def validate_request_message_from_slack(channel_id, message, thread_ts=None):
    if len(message.encode('utf-8')) > MAX_REQUEST_MESSAGE_SIZE:
        error_message = "Input message from slack exceeded max size {}".format(MAX_REQUEST_MESSAGE_SIZE)
        slack_request_message_validation_error(channel_id=channel_id, error_string=error_message, thread_ts=thread_ts)
        return False
    return True


def validate_response_from_bedrock(channel_id, message, thread_ts=None):
    if len(message.encode('utf-8')) > MAX_RESPONSE_MESSAGE_SIZE:
        error_message = "Bedrock response exceeded max size {}".format(MAX_RESPONSE_MESSAGE_SIZE)
        bedrock_response_validation_error(channel_id=channel_id, error_string=error_message, thread_ts=thread_ts)
        return False

    return True
