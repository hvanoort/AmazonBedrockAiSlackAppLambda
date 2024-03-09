import argparse


class CustomArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parse which exposes the error message as an AssertionError instead of exiting
    """
    def error(self, message):
        raise AssertionError(message)
