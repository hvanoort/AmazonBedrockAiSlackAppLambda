import unittest

from amazon_bedrock_ai_slack_app_lambda.validation.request_response_validator import \
    validate_request_message_from_slack, validate_response_from_bedrock

TEST_MESSAGE_GOOD = "x" * 3000
TEST_CHANNEL_ID = "TEST_ID"


class RequestResponseValidatorTests(unittest.TestCase):
    def test_validate_request_message_from_slack_good_case(self):
        self.assertTrue(validate_request_message_from_slack(TEST_CHANNEL_ID, TEST_MESSAGE_GOOD))

    def test_validate_request_message_from_slack_message_exceeds_limit(self):
        # fails assertion error once the validation fails and the error message is posted to slack due to unit test env
        with self.assertRaises(AssertionError):
            validate_request_message_from_slack(TEST_CHANNEL_ID, "x" * 30000)

    def test_validate_response_from_bedrock_good_case(self):
        self.assertTrue(validate_response_from_bedrock(TEST_CHANNEL_ID, TEST_MESSAGE_GOOD))

    def test_validate_response_from_bedrock_response_exceeds_limit(self):
        # fails assertion error once the validation fails and the error message is posted to slack due to unit test env
        with self.assertRaises(AssertionError):
            validate_response_from_bedrock(TEST_CHANNEL_ID, "x" * 11000)


if __name__ == '__main__':
    unittest.main()
