"""
A Class for getting deferrds to specific torrent events
"""
__author__ = 'Laharah'

import time

from twisted.internet import defer, reactor
import deluge.component as component
from common import Log

log = Log()


class Error(Exception):
    """"base exception"""
    pass


class TorrentEventLedgerNotListening(Error):
    """raised when no events are listening"""

    def __init__(self, message=None):
        if not message:
            message = "The ledger is not currently listening for any events"
        super(self.__class__, self).__init__(message)


class TorrentEventLedger(object):
    """
    keeps track of specific torrent events the plugin is waiting on.

    Holds a dict of torrent events the plugin is watching for and executes
    their deferred callbacks when events are complete.

    Contains a context manager to register and deregister its handlers
    """

    def __init__(self, timeout=None):
        """If timeout is given, it is used as the ammount of time before forcing
        de-register"""
        self.timeout = timeout
        self.timeout_start = None
        self.ledgers = {}
        self.event_manager = component.get('EventManager')
        self.registered_events = set()

    def start(self, events=None):
        """begins listening for given list of (event, cb) pairs"""
        self.__enter__(events, defaults=False)

    def stop(self, events=None):
        """stops listening for a given event, defaults to all events if none given."""
        events = events if events else self.registered_events
        self._force_deregister(events)

    def _force_deregister(self, events):
        """forces de-register of give (event, cb) pairs"""
        for event, cb in events:
            self.event_manager.deregister_event_handler(event, cb)
            del self.ledgers[event]
            return

    def __enter__(self, events=None, defaults=True):
        """
        begins the context manager with optionl (event, cb) pairs
        """
        _default_events = [
            ('TorrentFolderRenamedEvent', self._on_folder_renamed),
            ('TorrentFileRenamedEvent', self._on_file_renamed)
        ]

        events = events if events else []
        if defaults:
            events += _default_events
        for event, cb in events:
            self.event_manager.register_event_handler(event, cb)
            self.registered_events.add((event, cb))
            self.ledgers[event] = {}
        self.context_events = events

    def __exit__(self, exc_type, exc_val, exc_tb):
        """deregisters the context manager listeners"""
        if not self.timeout_start:
            self.timeout_start = time.time()
        ledgers = {}
        for event, _ in self.context_events:
            ledgers[event] = self.ledgers[event]
        for ledger, entries in ledgers.iteritems():
            if self.timeout:
                if time.time() - self.timeout_start > self.timeout:
                    log.debug('timeout reached, turning off listners')
                    self._force_deregister(self.context_events)
                    return

            if entries:
                log.debug(
                    'TorrentEventLedger is still waiting on events: {0}, waiting...'.format(
                        self.ledgers))
                reactor.callLater(1, self.__exit__, None, None, None)
                return

        self._force_deregister(self.context_events)
        self.context_events = set()

    def _on_folder_renamed(self, torrent_id, old, new):
        """
        default callback for the TorrentFolderRenamedEvent
        """
        valid_tuples = [(old, new), (old, None), (None, None)]
        self._fire_deferreds('TorrentFolderRenamedEvent', torrent_id, valid_tuples)

    def _on_file_renamed(self, torrent_id, index, new_name):
        """
        default callback for the TorrentFileRenamedEvent
        """
        valid_tuples = {(index, new_name), (index, None), (None, None)}

        self._fire_deferreds('TorrentFileRenamedEvent', torrent_id, valid_tuples)

    def _fire_deferreds(self, event, torrent_id, valid_tuples):
        """fires approprate deferreds for a given event, torrent, and event variables"""
        try:
            entry = self.ledgers[event][torrent_id]
        except KeyError:
            return

        for t in valid_tuples:
            try:
                entry[t].callback(None)
                del entry[t]
            except KeyError:
                pass

        if not entry:
            del self.ledgers[event][torrent_id]

    def watch_for_file_rename(self, torrent_id, index=None, new_name=None):
        """get a deferred for a specific torrent file rename"""
        if not self.registered_events:
            raise TorrentEventLedgerNotListening()
        d = defer.Deferred()
        try:
            self.ledgers['TorrentFileRenamedEvent'][torrent_id][(index, new_name)] = d
        except KeyError:
            self.ledgers['TorrentFileRenamedEvent'][torrent_id] = {(index, new_name): d}
        return d

    def watch_for_folder_rename(self, torrent_id, old=None, new=None):
        """get a deferred for a specific torrent folder rename"""
        if not self.registered_events:
            raise TorrentEventLedgerNotListening()

        for arg in (old, new):
            if arg:
                if not arg.endswith('/'):
                    arg = arg + '/'
        d = defer.Deferred()
        try:
            self.ledgers['TorrentFolderRenamedEvent'][torrent_id][(old, new)] = d
        except KeyError:
            self.ledgers['TorrentFolderRenamedEvent'][torrent_id] = {(old, new): d}
        return d
