import unittest

from amazon_bedrock_ai_slack_app_lambda.validation.slack_params_validator import SlackParameterValidator

TEST_TS = 123456.0
TEST_CHANNEL_ID = "TEST_ID"


class SlackParameterValidatorTests(unittest.TestCase):
    def test_validate_disclaimer_ts_good_case(self):
        test_unit = SlackParameterValidator()
        test_unit.set_disclaimer_ts(TEST_TS)
        test_unit.validate_disclaimer_ts(TEST_TS)

    def test_validate_channel_id_good_case(self):
        test_unit = SlackParameterValidator()
        test_unit.set_channel_id(TEST_CHANNEL_ID)
        test_unit.validate_channel_id(TEST_CHANNEL_ID)

    def test_validate_disclaimer_ts_bad_case(self):
        test_unit = SlackParameterValidator()
        test_unit.set_disclaimer_ts(TEST_TS)
        with self.assertRaises(AssertionError):
            test_unit.validate_disclaimer_ts(TEST_TS + 1)

    def test_validate_channel_id_bad_case(self):
        test_unit = SlackParameterValidator()
        test_unit.set_channel_id(TEST_CHANNEL_ID)
        with self.assertRaises(AssertionError):
            test_unit.validate_channel_id(TEST_CHANNEL_ID + "STRING")


if __name__ == '__main__':
    unittest.main()
