from datetime import date

import json
import os

import boto3

from amazon_bedrock_ai_slack_app_lambda.helpers.constants import (
    DEFAULT_MODE,
    DEFAULT_MODEL,
    METADATA_TABLE_NAME, DEFAULT_LAST_DISCLAIMER_DATE,
)
from amazon_bedrock_ai_slack_app_lambda.helpers.payload_generator import DEFAULT_ASSISTANT_PROMPT
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER

dynamodb = boto3.client("dynamodb", region_name=os.getenv('AWS_REGION', default='us-west-2'))


def save_settings(channel_id, user_id, model_id, mode, last_disclaimer_date=date.today()):
    """
    TODO: Handle exceptions
    """
    get_item_response = dynamodb.get_item(
        TableName=METADATA_TABLE_NAME,
        Key={
            'qualified_user_id': {'S': "{}/{}".format(channel_id, user_id)}
        }
    )
    LOGGER.info("GetItem response: {}".format(get_item_response))

    item = get_item_response.get("Item")
    if item:
        settings = json.loads(get_item_response["Item"]["settings"]["S"])
    else:
        settings = {}

    settings.update({'model_id': model_id})
    settings.update({'mode': mode})
    settings.update({'last_disclaimer_date': str(last_disclaimer_date)})

    LOGGER.info("Writing settings: {}".format(settings))

    put_item_response = dynamodb.put_item(
        TableName=METADATA_TABLE_NAME,
        Item={
            'qualified_user_id': {'S': "{}/{}".format(channel_id, user_id)},
            'settings': {'S': json.dumps(settings)}
        }
    )
    LOGGER.info(put_item_response)
    return settings


def get_user_settings(channel_id, user_id) -> dict:
    """
    Get user settings from DynamoDB.

    :param channel_id (str): The channel ID.
    :param user_id (str): The user ID.

    Returns:
        str: dict with user settings

    Raises:
        Exception: If an error occurs during DynamoDB operation.
    """
    try:
        get_item_response = dynamodb.get_item(
            TableName=METADATA_TABLE_NAME,
            Key={
                'qualified_user_id': {'S': "{}/{}".format(channel_id, user_id)}
            }
        )
        item = get_item_response.get("Item")
        if item:
            settings = json.loads(get_item_response["Item"]["settings"]["S"])
            LOGGER.info("user_settings_found:={}".format(json.dumps(settings, indent=4)))
            return settings
        else:
            response = save_settings(channel_id, user_id, DEFAULT_MODEL, DEFAULT_MODE, DEFAULT_LAST_DISCLAIMER_DATE)
            LOGGER.info("defaulting_user_settings:={}".format(json.dumps(response, indent=4)))
            return response
    except Exception as e:
        LOGGER.error(f"An error occurred getting user settings: {e}")
        return {'model_id': DEFAULT_MODEL, 'mode': DEFAULT_MODE, 'assistant_prompt': DEFAULT_ASSISTANT_PROMPT}
