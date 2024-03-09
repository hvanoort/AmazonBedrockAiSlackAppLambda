import unittest

from amazon_bedrock_ai_slack_app_lambda.validation.user_validator import validate_slack_user

TEST_LOGIN_BAD = "gainanovs"
TEST_LOGIN_GOOD = "testUser"
TEST_CHANNEL_ID = 'C123ABC456'
CHECK_TYPE = 'user'


class UserValidatorTests(unittest.TestCase):

    def test_validate_slack_user_good_case(self):
        self.assertTrue(validate_slack_user(TEST_CHANNEL_ID, TEST_LOGIN_GOOD, CHECK_TYPE))

    def test_validate_slack_user_bad_case(self):
        with self.assertRaises(AssertionError):
            self.assertTrue(validate_slack_user(TEST_CHANNEL_ID, TEST_LOGIN_BAD, CHECK_TYPE))


if __name__ == '__main__':
    unittest.main()
