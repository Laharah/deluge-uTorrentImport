__author__ = 'Laharah'

import os

import sys

from base64 import b64encode

from deluge.bencode import bdecode

from deluge.ui.client import client

from twisted.internet import reactor

from deluge.log import setupLogger

setupLogger()


class UtorrentToDeluge():
    def __init__(self, pathToResumeDat):
        self.rsmDataPath = pathToResumeDat
        self.torrentsToAdd = {}
        self.waitingOnTorrents = {}
        self.couldNotAdd = []
        self.torrentCounter = 0
        self.logFile = 'uTorrent_import_errors.txt'

    def setLogPath(self, path):
        self.logFile = path + '\\uTorrent_import_errors.txt'

    def read_resume_dat(self, filename):
        try:
            f = open(filename, 'rb')
        except:
            print 'could not find or open resume.dat'
            self.log_error(['could not find or open resume.dat'])
        raw = f.read()
        f.close()
        data = bdecode(raw)
        return data

    def log_error(self, errors):
        try:
            f = open(self.logFile, 'a')
        except:
            print 'could not open log file'
        for line in errors:
            f.write(unicode(line, 'UTF-8') + '\n')
        f.close()

    def begin_export(self, result):
        print "Connection was succesful!"
        print "result:", result
        client.register_event_handler("TorrentFolderRenamedEvent", self.torrent_folder_renamed)
        print "folder_renamed registered"
        client.register_event_handler("TorrentFileRenamedEvent", self.torrent_file_renamed)
        print 'file_renamed registered'
        data = self.read_resume_dat(self.rsmDataPath)
        failures = {}
        superErrors = {}

        for torrent in data.keys():
            try:
                fullSavePath = unicode(data[torrent]['path'], 'utf-8')
            except:
                fullSavePath = None
                superErrors[fullSavePath] = 1
            if fullSavePath != None:
                topLevelTitle = fullSavePath.split('\\')[-1]
                delugeSavePath = '\\'.join(fullSavePath.split('\\')[:-1])
            try:
                fileDump = b64encode(open(unicode(torrent, 'utf-8'), 'rb').read())
            except:
                fileDump = None
                print 'FAILURE!!', torrent
                failures[torrent] = data[torrent]

            if fullSavePath != None:
                self.torrentsToAdd[fullSavePath] = False
                self.torrentCounter += 1
                client.core.add_torrent_file(unicode(torrent, 'utf-8'), fileDump,
                                             options={'download_location': delugeSavePath}).addCallback(
                    self.get_torrent_data,
                    topLevelTitle,
                    fullSavePath)
        print 'Attempting to add Torrents...'

    def list_torrents(self, val, torrent_id):
        print torrent_id, val


    def torrent_folder_renamed(self, id, old, new):
        client.core.force_recheck([id])
        del self.waitingOnTorrents[id]
        self.check_done()


    def torrent_file_renamed(self, id, index, name):
        client.core.force_recheck([id])
        del self.waitingOnTorrents[id]
        self.check_done()


    def torrent_accounting(self, fullSavePath, accountedFor):
        self.torrentCounter -= 1
        if accountedFor:
            self.torrentsToAdd[fullSavePath] = True
        self.check_done()


    def check_done(self):
        if len(self.waitingOnTorrents) == 0 and self.torrentCounter == 0:
            failedTorrents = []
            for torrent in self.torrentsToAdd.keys():
                if self.torrentsToAdd[torrent] == False:
                    failedTorrents.append(torrent + ' ')
            if len(failedTorrents) > 0:
                self.log_error(['Could not load the following torrents:'] + failedTorrents)
                print 'Could not load the following torrents:'
                for torrent in failedTorrents:
                    print torrent

            self.disconnect()


    def disconnect(self):
        client.disconnect()
        reactor.stop()


    def check_already_exists(self, info, fullSavePath):
        if info == None:
            self.torrent_accounting(fullSavePath, False)
            return
        for id in info:
            delugeTorrentPath = info[id]['save_path'] + '\\' + info[id]['name']
            if delugeTorrentPath == fullSavePath:
                self.torrent_accounting(fullSavePath, True)
                return
        self.torrent_accounting(fullSavePath, False)


    def get_torrent_data(self, torrent_id, topLevelTitle, fullSavePath):
        if torrent_id == None:
            client.core.get_torrents_status({'name': topLevelTitle}, ['save_path', 'name']).addCallback(
                self.check_already_exists, fullSavePath)
            return
        client.core.pause_torrent([torrent_id])
        self.torrent_accounting(fullSavePath, True)
        client.core.get_torrent_status(torrent_id, ['name', 'files', 'save_path']).addCallback(self.resolve_paths,
                                                                                               torrent_id,
                                                                                               topLevelTitle)


    def resolve_paths(self, info, torrent_id, topLevelTitle):
        saveName = topLevelTitle
        if len(info['files']) > 1:
            mainFolder = info['files'][0]['path'].split('/')[0]
            client.core.rename_folder(torrent_id, mainFolder + '/', saveName)
        else:
            client.core.rename_files(torrent_id, [(0, saveName)])
        self.waitingOnTorrents[torrent_id] = 0


    def could_not_connect(self, result):
        print "connection failed!"
        error = 'Please ensure that deluge is running and is in client/server mode, not "classic" mode.'
        print error
        self.log_error([error])
        self.disconnect()


def main():

    log_location = os.getcwd()

    args = sys.argv[1:]

    if not args:
        APPDATA = os.environ['USERPROFILE'] + '\\Appdata\\Roaming\\uTorrent'
        os.chdir(APPDATA)
        pathToResumeDat = 'resume.dat'

    else:
        os.chdir('\\'.join(args[0].split('\\')[:-1]))
        pathToResumeDat = args[0]


    Exporter = UtorrentToDeluge(pathToResumeDat)
    Exporter.setLogPath(log_location)
    d = client.connect()
    d.addCallback(Exporter.begin_export)
    d.addErrback(Exporter.could_not_connect)
    reactor.run()


if __name__ == '__main__':
    main()