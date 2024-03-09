import logging
import os

from aws_lambda_powertools import Logger

APPLICATION_STAGE = "APPLICATION_STAGE"

LOGGER = Logger(service="amazon_bedrock_ai_slack_app_lambda")
app_stage = os.environ.get(APPLICATION_STAGE) or "prod"
log_level = logging.DEBUG if app_stage == "dev" else logging.INFO
LOGGER.info("Setting log level to {}".format(log_level))
LOGGER.setLevel(log_level)
