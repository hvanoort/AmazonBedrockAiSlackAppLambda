import boto3
import os
import re

from amazon_bedrock_ai_slack_app_lambda.helpers.constants import ALLOWED_COMPREHEND_PII_ENTITIES
from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER


class ComprehendHelper:
    def __init__(self, uid, message):
        """
        Tracker for synchronizing the bedrock event stream and Slack message updates
        :param uid: uuid for logging purposes
        :param message: the message the is buffered from the bedrock invoke model response stream
        :param status: true indicates that end of stream has been reached and there is no need to process the messages further
        """
        self.uid = uid
        self.message = message


def detect_and_redact_pii(message):
    comprehend_client = boto3.client(service_name="comprehend",
                                     region_name=os.getenv('AWS_REGION', default='us-west-2'))

    """
        Detects personally identifiable information (PII) in a document. PII can be
        things like names, account numbers, or addresses.

        :param message: The text message to inspect.
        :return: tuple (redacted prompt, The list of PII entities that the slack app cannot process)
        """
    LOGGER.debug("comprehend.detect_pii_entities message = {}".format(message))
    response = comprehend_client.detect_pii_entities(
        Text=message, LanguageCode='en'
    )
    LOGGER.debug("comprehend.detect_pii_entities response = {}".format(response))

    # Extract just the types into a list
    entities = []
    for entity in response['Entities']:
        entities.append(entity['Type'])
    un_allowed_entities = set(entities).difference(ALLOWED_COMPREHEND_PII_ENTITIES)

    redacted = []
    prev_end = 0
    for entity in response['Entities']:
        if entity['Type'] in ALLOWED_COMPREHEND_PII_ENTITIES:
            continue
        redacted.append(message[prev_end:entity["BeginOffset"]])
        redacted.append("<REDACTED>")
        prev_end = entity["EndOffset"]
    redacted.append(message[prev_end:])
    redacted_text = "".join(redacted)

    LOGGER.debug("comprehend.detect_pii_entities redacted prompt = {}".format(redacted_text))

    return redacted_text, un_allowed_entities


def remove_unwanted_text_from_llm_response(message):
    # remove all text between the <function> </function> from bedrock response
    clean_message = re.sub(r"<function>.*?</function>", "", message)
    return clean_message
