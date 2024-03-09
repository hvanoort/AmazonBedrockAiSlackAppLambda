from amazon_bedrock_ai_slack_app_lambda.helpers.constants import (
    AVAILABLE_MODELS,
    AVAILABLE_MODES,
    PII_ERROR_MESSAGE,
    PII_SYSTEM_MESSAGE_TAG,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER
from amazon_bedrock_ai_slack_app_lambda.helpers.slack_helper import send_chat


def send_invalid_model_id_mode_message(channel_id, error_model_id, error_mode, thread_ts=None):
    if error_model_id and not error_mode:
        models_info = "\n".join(
            [f">{idx + 1}. `{model}`" for idx, model in enumerate(AVAILABLE_MODELS)]
        )
        error_message = ("[ERROR] Invalid model-id `{}`..\nPlease use a valid model-id from list below\n{}"
                         "\nAlternatively use `help` command").format(error_model_id, models_info)
        LOGGER.error("Invalid Model-Id:={}".format(error_message))
        return send_chat(channel_id, error_message, thread_ts)

    if error_mode and not error_model_id:
        modes_info = "\n".join(
            [f">{idx + 1}. `{model}`" for idx, model in enumerate(AVAILABLE_MODES)]
        )
        error_message = ("[ERROR] Invalid mode `{}`..\nPlease use a valid mode from list below\n{}"
                         "\nAlternatively use `help` command").format(error_mode, modes_info)
        LOGGER.error("Invalid Mode:={}".format(error_message))
        return send_chat(channel_id, error_message, thread_ts)

    if error_mode and error_model_id:
        error_message = ("[ERROR] Invalid model-id `{}` and mode `{}` selected."
                         "\nPlease use `help` command to see available options").format(error_model_id, error_mode)
        LOGGER.error("Invalid Model-Id:={}; Invalid Mode:={}".format(error_model_id, error_mode))
        return send_chat(channel_id, error_message)


def settings_parse_error(channel_id, settings_parser, assertion_error, thread_ts=None):
    error_message = ("[ERROR] *Error while parsing settings:*\n>{}\n{}"
                     .format(assertion_error, settings_parser.format_help()))
    LOGGER.error(error_message)
    send_chat(channel_id, error_message, thread_ts)


def bedrock_streaming_api_call_error(channel_id, exception, thread_ts=None):
    error_message = ("[ERROR] *Error while making bedrock invoke model in streaming mode:*\n>{}"
                     .format(exception))
    LOGGER.error(error_message)
    send_chat(channel_id, error_message, thread_ts)


def slack_request_message_validation_error(channel_id, error_string, thread_ts=None):
    error_message = ("[ERROR] *Slack request message failed validation error:*\n>{}"
                     .format(error_string))
    LOGGER.error(error_message)
    send_chat(channel_id, error_message, thread_ts)


def slack_user_validation_error(channel_id, error_string, thread_ts=None):
    error_message = ("[ERROR] *User Validation Error:*\n>{}"
                     .format(error_string))
    LOGGER.error(error_message)
    send_chat(channel_id, error_message, thread_ts)


def bedrock_response_validation_error(channel_id, error_string, thread_ts=None):
    error_message = ("[ERROR] *Bedrock response failed validation error:*\n>{}"
                     .format(error_string))
    LOGGER.error(error_message)
    send_chat(channel_id, error_message, thread_ts)


def comprehend_pii_error_message(channel_id, un_allowed_pii_entities, is_request, thread_ts=None):
    request_response_string = "Information in Slack message" if is_request else "Response from Bedrock FM"
    error_message = (PII_ERROR_MESSAGE.format(PII_SYSTEM_MESSAGE_TAG, request_response_string, str(un_allowed_pii_entities)))
    LOGGER.error(error_message)
    LOGGER.error("[ERROR] Comprehend PII detected in channel_id: {}".format(channel_id))
    send_chat(channel_id, error_message, thread_ts)
