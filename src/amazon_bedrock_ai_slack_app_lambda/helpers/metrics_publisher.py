import os

import boto3

from amazon_bedrock_ai_slack_app_lambda.helpers.bedroc_invoker_metadata import BedrockInvokerMetadata
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER

cloudwatch = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', default='us-west-2'))

METRIC_NAMESPACE = "BedrockAiSlackApp"


def report_bedrock_invoke_model_response_status(bedrock_invoker_metadata: BedrockInvokerMetadata, response_status: bool,
                                                bedrock_request_id="None", exception_name="None"):
    """
    Metric to record every bedrock invocation along with the status.

    Note: This metric also ties each bedrock request to a particular user request via logging and this log
    can be used to trace a particular bedrock request to a user request in case of a security incident as per Appsec
    recommendation.

    :param exception_name: exception name string
    :param bedrock_invoker_metadata: metadata
    :param response_status: True or False
    :param bedrock_request_id: request id for logging purposes to facilitate dive deep during security incidents
    :return: True if metric was published successfully, False otherwise

    """
    metric_data_response_status_with_login = [{
        'MetricName': 'BedrockInvokeModelResponseStatus',
        'Dimensions': [
            {
                'Name': 'ModelId',
                'Value': bedrock_invoker_metadata.model_id
            },
            {
                'Name': 'Mode',
                'Value': bedrock_invoker_metadata.mode
            },
            {
                'Name': 'UserId',
                'Value': bedrock_invoker_metadata.user_id
            },
            {
                'Name': 'Login',
                'Value': bedrock_invoker_metadata.login
            },
            {
                'Name': 'ChannelId',
                'Value': bedrock_invoker_metadata.channel_id
            },
            {
                'Name': 'ResponseStatusWithLogin',
                'Value': str(response_status)
            },
            {
                'Name': 'Exception',
                'Value': exception_name
            }
        ],
        'Value': 1
    }]
    LOGGER.debug("Metric data is {}".format(metric_data_response_status_with_login))
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data_response_status_with_login
    )
    # info log level for debuggability during security incidents as per Appsec recommendation
    LOGGER.info("CloudWatch metric reported: {} Bedrock request id is {}".format(metric_data_response_status_with_login,
                                                                                 bedrock_request_id))
    LOGGER.info("CloudWatch metric response0: {} Bedrock request id is {}".format(response, bedrock_request_id))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")

    metric_data_response_status_aggregate_with_modelid_and_mode = [{
        'MetricName': 'BedrockInvokeModelResponseStatus',
        'Dimensions': [
            {
                'Name': 'ModelId',
                'Value': bedrock_invoker_metadata.model_id
            },
            {
                'Name': 'Mode',
                'Value': bedrock_invoker_metadata.mode
            },
            {
                'Name': 'ResponseStatusAggregateWithModelIdAndMode',
                'Value': str(response_status)
            },
            {
                'Name': 'Exception',
                'Value': exception_name
            }
        ],
        'Value': 1
    }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data_response_status_aggregate_with_modelid_and_mode
    )
    LOGGER.info("CloudWatch metric response1: {} Bedrock request id is {}".format(response, bedrock_request_id))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")

    metric_data_response_status_aggregate = [{
        'MetricName': 'BedrockInvokeModelResponseStatus',
        'Dimensions': [
            {
                'Name': 'ResponseStatusAggregate',
                'Value': str(response_status)
            },
            {
                'Name': 'Exception',
                'Value': exception_name
            }
        ],
        'Value': 1
    }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data_response_status_aggregate
    )

    # info log level for debuggability during security incidents as per Appsec recommendation
    LOGGER.info("CloudWatch metric reported: {} Bedrock request id is {}".format(metric_data_response_status_aggregate,
                                                                                 bedrock_request_id))
    LOGGER.info("CloudWatch metric response: {} Bedrock request id is {}".format(response, bedrock_request_id))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")
        return False

    return True


def report_bedrock_invoke_model_latency_first_chunk(bedrock_invoker_metadata: BedrockInvokerMetadata,
                                                    latency_first_chunk_ms):
    """
    Metric to record invoke model latency for the first chunk

    :return: True if metric was published successfully, False otherwise

    """
    metric_data = [{
        'MetricName': 'BedrockInvokeModelResponseLatencyFirstChunkMs',
        'Dimensions': [
            {
                'Name': 'ModelId',
                'Value': bedrock_invoker_metadata.model_id
            },
            {
                'Name': 'Mode',
                'Value': bedrock_invoker_metadata.mode
            },
        ],
        'Value': latency_first_chunk_ms
    }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data
    )

    LOGGER.debug("CloudWatch metric reported: {}".format(metric_data))
    LOGGER.debug("CloudWatch metric response: {}".format(response))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")
        return False

    return True


def report_bedrock_invoke_model_latency(bedrock_invoker_metadata: BedrockInvokerMetadata,
                                        latency_ms):
    """
    Metric to record invoke model latency for the bedrock invoke model call up until the last byte is received.

    :return: True if metric was published successfully, False otherwise

    TODO: Catch errors appropriately and test this out
    """
    metric_data = [{
        'MetricName': 'BedrockInvokeModelResponseLatencyMs',
        'Dimensions': [
            {
                'Name': 'ModelId',
                'Value': bedrock_invoker_metadata.model_id
            },
            {
                'Name': 'Mode',
                'Value': bedrock_invoker_metadata.mode
            }
        ],
        'Value': latency_ms
    }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data
    )

    LOGGER.debug("CloudWatch metric reported: {}".format(metric_data))
    LOGGER.debug("CloudWatch metric response: {}".format(response))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")
        return False

    return True


def report_slack_request_message_size_bytes(bedrock_invoker_metadata: BedrockInvokerMetadata, size_bytes):
    """
    Metric to record the Slack message size.

    :return: True if metric was published successfully, False otherwise

    TODO: Catch errors appropriately and test this out
    """
    metric_data = [{
        'MetricName': 'SlackRequestMessageSizeBytes',
        'Dimensions': [
            {
                'Name': 'ModelId',
                'Value': bedrock_invoker_metadata.model_id
            },
            {
                'Name': 'Mode',
                'Value': bedrock_invoker_metadata.mode
            }
        ],
        'Value': size_bytes
    }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data
    )

    LOGGER.debug("CloudWatch metric reported: {}".format(metric_data))
    LOGGER.debug("CloudWatch metric response: {}".format(response))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")
        return False

    return True


def report_bedrock_invoke_model_response_size_bytes(bedrock_invoker_metadata: BedrockInvokerMetadata, size_bytes):
    """
    Metric to record bedrock invoke model response size.

    :return: True if metric was published successfully, False otherwise

    TODO: Catch errors appropriately and test this out
    """
    metric_data = [{
        'MetricName': 'BedrockInvokeModelResponseMessageSizeBytes',
        'Dimensions': [
            {
                'Name': 'ModelId',
                'Value': bedrock_invoker_metadata.model_id
            },
            {
                'Name': 'Mode',
                'Value': bedrock_invoker_metadata.mode
            }
        ],
        'Value': size_bytes
    }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data
    )

    LOGGER.debug("CloudWatch metric reported: {}".format(metric_data))
    LOGGER.debug("CloudWatch metric response: {}".format(response))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_bedrock_response_status call failed")
        return False

    return True


def report_comprehend_pii_metrics(is_request, is_detected):
    """
    Metric to record comprehend PII detection.

    :return: True if metric was published successfully, False otherwise

    """
    if is_detected:
        if is_request:
            metric_data = [{
                'MetricName': 'ComprehendPIIDetectedInUserRequest',
                'Value': 1
            }]
        else:
            metric_data = [{
                'MetricName': 'ComprehendPIIDetectedInLLMResponse',
                'Value': 1
            }]
    else:
        if is_request:
            metric_data = [{
                'MetricName': 'ComprehendPIIDetectedInUserRequest',
                'Value': 0
            }]
        else:
            metric_data = [{
                'MetricName': 'ComprehendPIIDetectedInLLMResponse',
                'Value': 0
            }]
    response = cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data
    )

    LOGGER.debug("CloudWatch metric reported: {}".format(metric_data))
    LOGGER.debug("CloudWatch metric response: {}".format(response))

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error("CloudWatch report_comprehend_pii_metrics call failed")
        return False

    return True
