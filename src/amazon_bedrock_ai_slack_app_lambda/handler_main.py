import json
import os
import time
from datetime import date, datetime

from amazon_bedrock_ai_slack_app_lambda.helpers.bedroc_invoker_metadata import (
    BedrockInvokerMetadata,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.bedrock_helper import (  # noqa: F401
    invoke_bedrock_streaming,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.command_helper import handle_command
from amazon_bedrock_ai_slack_app_lambda.helpers.constants import (
    DEFAULT_LAST_DISCLAIMER_DATE,
    DISCLAIMER,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.ddb_helper import get_user_settings, save_settings
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER
from amazon_bedrock_ai_slack_app_lambda.helpers.metrics_publisher import (
    report_slack_request_message_size_bytes,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.model_helper import get_model
from amazon_bedrock_ai_slack_app_lambda.helpers.payload_generator import (  # noqa: F401
    DEFAULT_ASSISTANT_PROMPT,
    generate_payload,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.slack_helper import (  # noqa: F401
    get_bot_user_id,
    get_channel_type,
    get_conversation_history,
    get_thread_replies,
    get_user_from_userid,
    send_chat,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.utils import check_if_mentioning_bot, get_thread_ts
from amazon_bedrock_ai_slack_app_lambda.validation.request_response_validator import (
    validate_request_message_from_slack,
)
from amazon_bedrock_ai_slack_app_lambda.validation.slack_params_validator import (
    SLACK_PARAMETER_VALIDATOR,
)
from amazon_bedrock_ai_slack_app_lambda.validation.user_validator import (  # noqa: F401
    validate_slack_user,
)


def lambda_handler(event, context):
    """
    Main entry point for the lambda.
    The JSON body of the request is provided in the event slot.
    """

    # By default, treat the user request as coming from Eastern Standard Time.
    os.environ["TZ"] = "America/New_York"
    time.tzset()
    LOGGER.debug("event={}".format(json.dumps(event, indent=4)))

    bot_user_id = get_bot_user_id()
    LOGGER.debug("bot_user_id={}".format(bot_user_id))

    records = json.dumps(event.get("Records"))
    body = json.loads(records)[0].get("body")
    slack_event = json.loads(body).get("event")
    channel_id = slack_event.get("channel")
    user_id = slack_event.get("user")
    parent_ts = slack_event.get('event_ts')
    event_thread_ts = slack_event.get('thread_ts')
    SLACK_PARAMETER_VALIDATOR.set_channel_id(channel_id)

    channel_type = get_channel_type(channel_id)

    thread_ts = get_thread_ts({"channel_type": channel_type, "parent_ts": parent_ts, 'thread_ts': event_thread_ts})

    if user_id == bot_user_id:
        LOGGER.info("Skipping response generation as the message if from the BedrockAiApp")
        return {"status": "success"}

    if "subtype" in slack_event:
        LOGGER.info("Skipping response generation due to subtype present")
        return {"status": "success"}

    # checking if Bot was mentioned
    if channel_type != 'im' and not check_if_mentioning_bot(slack_event, bot_user_id):
        LOGGER.info("Skipping response generation due to message sent not in IM and Bot wasn't mentioned")
        return {"status": "success"}

    user_settings: dict = get_user_settings(channel_id, user_id)
    model_id = user_settings.get('model_id')
    model_attr = get_model(model_id)
    mode = user_settings.get('mode')
    last_disclaimer_date = datetime.strptime(
        user_settings.get('last_disclaimer_date', str(DEFAULT_LAST_DISCLAIMER_DATE)), '%Y-%m-%d').date()
    days_elapsed = date.today() - last_disclaimer_date
    # send disclaimer at least once a day
    if days_elapsed.days > 0:
        send_chat(
            channel_id,
            DISCLAIMER,
            thread_ts
        )
        save_settings(channel_id, user_id, model_id, mode)

    login = get_user_from_userid(user_id).get('user').get('name')
    # if not validate_slack_user(channel_id, login, 'user', user_settings.get('model_id'), thread_ts=thread_ts):
    #      return {"status": "failure"}

    message = slack_event.get("text")
    if validate_request_message_from_slack(channel_id=channel_id, message=message, thread_ts=thread_ts) is not True:
        return {"status": "failure"}

    command_handler_response = handle_command(channel_id, user_id, message, bot_user_id, thread_ts)
    if command_handler_response:
        LOGGER.info("Command {} processed with response {}".format(message, command_handler_response))
        return command_handler_response

    bedrock_invoker_metadata = BedrockInvokerMetadata(model_id, mode, channel_id, user_id, login)
    report_slack_request_message_size_bytes(bedrock_invoker_metadata=bedrock_invoker_metadata,
                                            size_bytes=len(message.encode('utf-8')))

    conversation_history = (
        get_thread_replies(channel_id, thread_ts)
        if channel_type != 'im' and event_thread_ts
        else get_conversation_history(channel_id, 5)
    )

    payload = generate_payload(
        conversation_history, bot_user_id, model_attr, mode
    )
    LOGGER.debug("Channel Type - {}; Payload={}".format(channel_type, json.dumps(payload, indent=4)))

    invoke_bedrock_streaming(bedrock_invoker_metadata, payload, thread_ts)
    return {"status": "success"}
