import json
import os

import boto3

from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER

BOT_USER_TOKEN_SECRET_ARN = "BOT_USER_TOKEN_SECRET_ARN"
BOT_USER_TOKEN = "BOT_USER_TOKEN"

USER_TOKEN_SECRET_ARN = "USER_TOKEN_SECRET_ARN"
USER_TOKEN = 'USER_TOKEN'


def get_bot_user_token():
    """
    Returns the slack bot user oauth token. Requires the secret manager arn for the bot user oauth token
    to be set as an environment variable.
    :return:
    """
    client = boto3.client(service_name="secretsmanager", region_name=os.getenv('AWS_REGION', default='us-west-2'))

    secret_response = client.get_secret_value(SecretId=os.environ[BOT_USER_TOKEN_SECRET_ARN])
    LOGGER.debug(
        "Secrets response for arn {} = {}".format(
            os.environ[BOT_USER_TOKEN_SECRET_ARN], secret_response
        )
    )

    return json.loads(secret_response["SecretString"]).get(BOT_USER_TOKEN, "")


def get_user_token():
    """
    Returns the slack user oauth token. Requires the secret manager arn for the bot user oauth token
    to be set as an environment variable.
    :return:
    """
    client = boto3.client(service_name="secretsmanager",
                          region_name=os.getenv('AWS_REGION', default='us-west-2'))

    secret_response = client.get_secret_value(SecretId=os.environ[USER_TOKEN_SECRET_ARN])
    LOGGER.debug(
        "Secrets response for arn {} = {}".format(
            os.environ[USER_TOKEN_SECRET_ARN], secret_response
        )
    )

    return json.loads(secret_response["SecretString"]).get(USER_TOKEN, "")
