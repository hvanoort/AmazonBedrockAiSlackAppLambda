import os

from amazon_bedrock_ai_slack_app_lambda.handler_main import lambda_handler


def hello_world(event, context):
    print("Received request")
    return lambda_handler(event, context)


# Setup the Bedrock API model for boto
package_path = os.path.dirname(__file__)
aws_data_path = set(os.environ.get("AWS_DATA_PATH", "").split(os.pathsep))
aws_data_path.add(f"{package_path}/models")
os.environ.update({"AWS_DATA_PATH": os.pathsep.join(aws_data_path)})
