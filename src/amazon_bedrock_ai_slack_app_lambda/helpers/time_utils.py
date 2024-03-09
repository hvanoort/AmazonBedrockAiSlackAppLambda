import uuid
from datetime import datetime

from amazon_bedrock_ai_slack_app_lambda.helpers.logging import LOGGER

NO_DATE = datetime.fromordinal(1)


class StopWatch:
    def __init__(self):
        self.__id = uuid.uuid4()
        self.__start_time = NO_DATE
        self.__stop_time = NO_DATE
        self.__elapsed_time_ms = - 1.0
        LOGGER.debug("New StopWatch created with id: {}".format(self.__id))

    def start(self):
        """
        :return: the object for chaining
        """
        assert self.__start_time == NO_DATE, "StopWatch started already. id: {}".format(self.__id)
        self.__start_time = datetime.now()
        return self

    def stop(self):
        """
        :return: the object for chaining
        """
        assert self.__start_time != NO_DATE, "StopWatch must be started before calling stop. id: {}".format(self.__id)
        assert self.__stop_time == NO_DATE, "StopWatch stopped already. id: {}".format(self.__id)
        self.__stop_time = datetime.now()
        return self

    def get_elapsed_time(self) -> float:
        assert (self.__start_time != NO_DATE and self.__stop_time != NO_DATE), (
            "StopWatch start time or stop time has not been recorded before calculating elapsed time. id: {}"
            .format(self.__id))
        self.__elapsed_time_ms = (self.__stop_time - self.__start_time).total_seconds() * 1000
        return self.__elapsed_time_ms
