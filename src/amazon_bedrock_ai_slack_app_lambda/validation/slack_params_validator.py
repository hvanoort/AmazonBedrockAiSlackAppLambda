

class SlackParameterValidator:
    """
    A class to validate that the response is indeed sent to the right channel id. This validator is created as per
    Appsec recommendation.

    This happens in parallel to the main code path invoking the Slack post message api and is in place as a
    secondary check to ensure we do not update to a different channel inadvertently.
    """
    def __init__(self):
        self.__channel_id = None
        self.__disclaimer_ts = -1

    def set_channel_id(self, ts):
        self.__channel_id = ts

    def set_disclaimer_ts(self, ts):
        self.__disclaimer_ts = ts

    def validate_disclaimer_ts(self, ts):
        assert self.__disclaimer_ts == ts, ("SlackParameterValidator failed in disclaimer_ts validation. "
                                            "Please make sure you are updating the right slack message. "
                                            "This is a code bug.")

    def validate_channel_id(self, channel_id):
        assert self.__channel_id == channel_id, ("SlackParameterValidator failed in channel_id validation. "
                                                 "Please make sure you are updating the right slack message. "
                                                 "This is a code bug.")


SLACK_PARAMETER_VALIDATOR = SlackParameterValidator()
