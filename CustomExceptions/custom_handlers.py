"""This part of the code defines possible exceptions and error that might occur during the recording.
"""
import signal


def sigterm_handler(signum, frame):
    raise SystemExit


# define Python user-defined exceptions
class Error(Exception):
    pass


class StreamConnectionError(Error):
    pass


class DisconnectionError(Error):
    pass
