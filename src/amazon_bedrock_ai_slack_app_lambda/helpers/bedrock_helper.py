import json
import os
import threading
import time

import boto3

from amazon_bedrock_ai_slack_app_lambda.helpers.comprehend_helper import (
    detect_and_redact_pii,
    remove_unwanted_text_from_llm_response,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.constants import (
    THINKING_FACE,
    UPDATE_TIME_DELAY_SECONDS,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.error_message_helper import (
    bedrock_streaming_api_call_error,
    comprehend_pii_error_message,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER
from amazon_bedrock_ai_slack_app_lambda.helpers.metrics_publisher import (
    report_bedrock_invoke_model_latency,
    report_bedrock_invoke_model_latency_first_chunk,
    report_bedrock_invoke_model_response_size_bytes,
    report_bedrock_invoke_model_response_status,
    report_comprehend_pii_metrics,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.slack_helper import send_chat, update_chat
from amazon_bedrock_ai_slack_app_lambda.helpers.time_utils import StopWatch
from amazon_bedrock_ai_slack_app_lambda.validation.request_response_validator import (
    validate_response_from_bedrock,
)
from amazon_bedrock_ai_slack_app_lambda.validation.slack_params_validator import (
    SLACK_PARAMETER_VALIDATOR,
)


class ResponseTracker:
    def __init__(self, uid, message, status):
        """
        Tracker for synchronizing the bedrock event stream and Slack message updates
        :param uid: uuid for logging purposes
        :param message: the message the is buffered from the bedrock invoke model response stream
        :param status: true indicates that end of stream has been reached and there is no need to process the messages further
        """
        self.uid = uid
        self.message = message
        self.status = status


def invoke_bedrock(payload):
    """
    Invoke a Bedrock model with the given prompt.
    NOTE: Only for testing purposes

    :return: A dictionary containing the status code and completion from the Bedrock model response.
    """
    bedrock_runtime = boto3.client(service_name="bedrock-runtime",
                                   region_name=os.getenv('AWS_REGION', default='us-west-2'))

    LOGGER.info("Making bedrock call with prompt: {}".format(payload.get("body")))

    response = bedrock_runtime.invoke_model(
        body=payload.get("body"),
        modelId=payload.get("model_id"),
        accept=payload.get("accept"),
        contentType=payload.get("content_type"),
    )

    LOGGER.info("Bedrock response - {}".format(response))

    http_status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode", 500)
    if http_status_code == 200:
        completion = json.loads(response.get("body", {}).read()).get("completion", "")
        return {"statusCode": http_status_code, "completion": completion}
    else:
        return {
            "statusCode": http_status_code,
            "completion": "Error: {} when calling bedrock".format(http_status_code),
        }


def invoke_bedrock_streaming(bedrock_invoker_metadata, payload, thread_ts=None):
    """
    Invoke a Bedrock model with the given prompt.

    :return: None
    """
    response_tracker = ResponseTracker("", "", False)
    processing_slack_api_response = send_chat(
        bedrock_invoker_metadata.channel_id,
        THINKING_FACE,
        thread_ts
    )

    model_id = bedrock_invoker_metadata.model_id

    processing_slack_api_response = json.loads(processing_slack_api_response.decode("UTF-8"))
    LOGGER.debug("disclaimer response: {}".format(processing_slack_api_response))
    processing_ts = processing_slack_api_response.get("ts")
    SLACK_PARAMETER_VALIDATOR.set_disclaimer_ts(processing_ts)

    # call comprehend to validate the payload for PII and redact if needed
    body = json.loads(payload["body"])
    if model_id == 'anthropic.claude-3-sonnet-20240229-v1:0':
        un_allowed_pii_entities = set()
        messages = body.get('messages')
        for msg in messages:
            redacted_msg, un_allowed_pii_entities_tmp = detect_and_redact_pii(msg.get('content'))
            msg['content'] = redacted_msg
            un_allowed_pii_entities.update(un_allowed_pii_entities_tmp)
    else:
        prompt = body["prompt"]
        redacted_prompt, un_allowed_pii_entities = detect_and_redact_pii(prompt)
        body["prompt"] = redacted_prompt

    payload["body"] = json.dumps(body)

    if len(un_allowed_pii_entities) > 0:
        # publish metrics for comprehend PII detection
        report_comprehend_pii_metrics(True, True)
        comprehend_pii_error_message(
            bedrock_invoker_metadata.channel_id, un_allowed_pii_entities, is_request=True, thread_ts=processing_ts)
    else:
        # publish metrics for comprehend PII detection
        report_comprehend_pii_metrics(True, False)

    # Asynchronously generate response
    generate_response_thread = threading.Thread(
        target=__generate_response,
        args={},
        kwargs={"bedrock_invoker_metadata": bedrock_invoker_metadata, "payload": payload, "response_tracker": response_tracker, "thread_ts": thread_ts},
    )
    generate_response_thread.start()
    __update_message_until_completion(response_tracker, bedrock_invoker_metadata=bedrock_invoker_metadata,
                                      parent_ts=processing_ts)


def __update_message_until_completion(response_tracker, bedrock_invoker_metadata, parent_ts):
    """
    Every n seconds, update the Slack message until status is complete.
    :param response_tracker: the ResponseTracker object for synchronization
    :param bedrock_invoker_metadata: the channel id
    :param parent_ts: parent time stamp of the response message which needs to be updated with the message
    :return: None
    """
    status = False
    counter = 0
    while (status is False) and (counter < 500):
        time.sleep(UPDATE_TIME_DELAY_SECONDS)
        status = response_tracker.status
        counter += 1
        LOGGER.debug("counter value is {}. Message={}".format(counter, str(response_tracker.message)))
        if response_tracker.message:
            # validate the response from bedrock
            if validate_response_from_bedrock(channel_id=bedrock_invoker_metadata.channel_id,
                                              message=response_tracker.message, thread_ts=parent_ts) is not True:
                return False

            # call comprehend to validate the payload for PII
            redacted_message, un_allowed_pii_entities = detect_and_redact_pii(response_tracker.message)
            clean_message = remove_unwanted_text_from_llm_response(redacted_message)
            if len(un_allowed_pii_entities) > 0:
                # publish metrics for comprehend PII detection
                report_comprehend_pii_metrics(False, True)
                comprehend_pii_error_message(bedrock_invoker_metadata.channel_id, un_allowed_pii_entities,
                                             is_request=False, thread_ts=parent_ts)
            else:
                # publish metrics for comprehend PII detection
                report_comprehend_pii_metrics(False, False)

            update_chat(bedrock_invoker_metadata, clean_message, parent_ts)


def __generate_response(bedrock_invoker_metadata, payload, response_tracker, thread_ts=None):
    """
    Invoke bedrock asynchronously
    :param bedrock_invoker_metadata: metadata
    :param payload: Payload for bedrock model
    :param response_tracker: the ResponseTracker object for synchronization
    :return: None
    """
    bedrock_runtime = boto3.client(service_name="bedrock-runtime",
                                   region_name=os.getenv('AWS_REGION', default='us-west-2'))

    stop_watch_first_chunk = StopWatch().start()
    stop_watch_last_chunk = StopWatch().start()
    LOGGER.debug("Making streaming bedrock call with : {}".format(payload))
    try:
        api_response = bedrock_runtime.invoke_model_with_response_stream(
            body=payload.get("body"),
            modelId=payload.get("model_id"),
            accept=payload.get("accept"),
            contentType=payload.get("content_type"),
        )
        LOGGER.debug("Api response of streaming bedrock call: {}".format(api_response))
    except Exception as exception:
        bedrock_streaming_api_call_error(bedrock_invoker_metadata.channel_id, exception, thread_ts)
        report_bedrock_invoke_model_response_status(bedrock_invoker_metadata=bedrock_invoker_metadata,
                                                    response_status=False,
                                                    exception_name=exception.__class__.__name__)
    else:
        stream = api_response.get("body")
        model_name = payload.get("model_name")

    if stream:
        for chunk_count, event in enumerate(stream, start=1):
            chunk = event.get("chunk")
            if chunk:
                # record first chunk time
                if chunk_count == 1:
                    report_bedrock_invoke_model_latency_first_chunk(
                        bedrock_invoker_metadata=bedrock_invoker_metadata,
                        latency_first_chunk_ms=stop_watch_first_chunk.stop().get_elapsed_time()
                    )

                chunk_obj = json.loads(chunk.get("bytes").decode())

                if model_name in ["claude-v2", "claude-instant"]:
                    chunk_part = chunk_obj.get("completion")
                elif model_name == "claude-v3-sonet":
                    chunk_part = chunk_obj.get("delta", {}).get("text", '')
                elif model_name == "titan":
                    chunk_part = chunk_obj.get("outputText")
                elif model_name == "llama2":
                    chunk_part = chunk_obj.get("generation")

                response_tracker.message += chunk_part

        response_tracker.status = True
        report_bedrock_invoke_model_latency(bedrock_invoker_metadata=bedrock_invoker_metadata,
                                            latency_ms=stop_watch_last_chunk.stop().get_elapsed_time())
        report_bedrock_invoke_model_response_status(bedrock_invoker_metadata=bedrock_invoker_metadata,
                                                    response_status=True,
                                                    bedrock_request_id=api_response["ResponseMetadata"]["RequestId"])
        report_bedrock_invoke_model_response_size_bytes(bedrock_invoker_metadata=bedrock_invoker_metadata,
                                                        size_bytes=len(response_tracker.message.encode('utf-8')))
