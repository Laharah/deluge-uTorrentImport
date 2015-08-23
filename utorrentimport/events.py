
from deluge.event import DelugeEvent


class uTorrentImportLoggingEvent(DelugeEvent):
    """emmited by uTorrentImport plugin for messaging purposes"""
    def __init__(self, level, message):
        """
        :param level: The log level of the message
        :param message: The message to transmit to listeners
        """
        self._args=[level, message]