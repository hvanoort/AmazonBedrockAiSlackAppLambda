import time
import unittest

from amazon_bedrock_ai_slack_app_lambda.helpers.time_utils import StopWatch


class TimeUtilsTests(unittest.TestCase):
    def test_stop_watch_good_case(self):
        test_unit = StopWatch().start()
        time.sleep(2)
        elapsed_time = test_unit.stop().get_elapsed_time()
        print(elapsed_time)
        # verify the time elapsed within +- 200ms range
        self.assertTrue(1800 < elapsed_time < 2200)

    def test_stop_watch_throws_at_elapse_without_starting(self):
        test_unit = StopWatch()
        with self.assertRaises(AssertionError):
            test_unit.get_elapsed_time()

    def test_stop_watch_throws_at_stop_without_starting(self):
        test_unit = StopWatch()
        with self.assertRaises(AssertionError):
            test_unit.stop()

    def test_stop_watch_throws_at_elapse_without_stopping(self):
        test_unit = StopWatch().start()
        with self.assertRaises(AssertionError):
            test_unit.get_elapsed_time()

    def test_stop_watch_throws_when_started_twice(self):
        test_unit = StopWatch().start()
        with self.assertRaises(AssertionError):
            test_unit.start()

    def test_stop_watch_throws_when_stopped_twice(self):
        test_unit = StopWatch().start().stop()
        with self.assertRaises(AssertionError):
            test_unit.stop()


if __name__ == '__main__':
    # print("Time utils tests disabled due to build issues")
    unittest.main()
