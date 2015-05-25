#!/usr/bin/env python2
__author__ = 'Laharah'

import os
import os.path
import re
import sys
from getpass import getuser, getpass
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
        self.torrentBlacklist = ['.fileguard', 'rec']
        self.wineDrives = None

    def setLogPath(self, path):
        self.logFile = os.path.join(path, 'uTorrent_import_errors.txt')

    def enable_wine_drive_mapping(self):
        devs = os.path.join(os.path.expanduser('~'), '.wine/dosdevices')
        if os.path.isdir(devs):
            self.wineDrives = {}
            print 'WINE drive mappings:'
            for drive in [l for l in os.listdir(devs) if re.match('^[A-Z]:$', l, re.IGNORECASE)]:
                self.wineDrives[drive.lower()] = os.path.realpath(os.path.join(devs, drive))
                print drive.upper(), '=>', self.wineDrives[drive.lower()]

    def read_resume_dat(self, filename):
        try:
            f = open(filename, 'rb')
        except:
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
            print line
            f.write((line + '\n').encode('utf8'))
        f.close()

    def wine_map_path(self, path):
        mapped = path
        drive = re.match('^([A-Z]:)', path, re.IGNORECASE)
        try:
            if self.wineDrives is not None and drive is not None:
                mapped = self.wineDrives[drive.group(1).lower()] + path[2:]
        except KeyError:
            print 'No WINE mapping for drive', drive.group(1)
        return mapped

    def add_torrent(self, torrent, data):
        if torrent in self.torrentBlacklist:
            return

        fullSavePath = unicode(data['path'], 'utf-8')

        topLevelTitle = fullSavePath.split('\\')[-1]
        delugeSavePath = os.sep.join(fullSavePath.split('\\')[:-1])
        fileDump = b64encode(open(unicode(torrent, 'utf-8'), 'rb').read())

        fullSavePath = self.wine_map_path(fullSavePath)
        delugeSavePath = self.wine_map_path(delugeSavePath)

        self.torrentsToAdd[fullSavePath] = False
        self.torrentCounter += 1
        client.core.add_torrent_file(
            unicode(torrent, 'utf-8'),
            fileDump,
            options={'download_location': delugeSavePath, 'add_paused': True}
        ).addCallback(
            self.get_torrent_data,
            topLevelTitle,
            fullSavePath)


    def begin_export(self, result):
        print "Connection was successful! (Result: {})".format(result)

        client.register_event_handler("TorrentFolderRenamedEvent", self.torrent_folder_renamed)
        print "folder_renamed registered"
        client.register_event_handler("TorrentFileRenamedEvent", self.torrent_file_renamed)
        print 'file_renamed registered'
        data = self.read_resume_dat(self.rsmDataPath)
        failures = {}

        print 'Attempting to add Torrents...'
        for torrent in data.keys():
            try:
                self.add_torrent(torrent, data[torrent])
            except:
                print 'FAILURE', torrent, sys.exc_info()
                failures[torrent] = data[torrent]

    def list_torrents(self, val, torrent_id):
        print torrent_id, val


    def torrent_folder_renamed(self, id, old, new):
        print u"Folder renamed, checking ({} => {})".format(old,new).encode('utf8')
        self.torrent_check(id)
        self.check_done()

    def torrent_file_renamed(self, id, index, name):
        print u"File renamed, checking ({})".format(name).encode('utf8')
        self.torrent_check(id)
        self.check_done()

    def torrent_check(self, id):
        client.core.force_recheck([id])
        self.waitingOnTorrents.pop(id, None)

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

            self.disconnect()


    def disconnect(self):
        client.disconnect()
        reactor.stop()


    def check_already_exists(self, info, fullSavePath):
        if info == None:
            self.torrent_accounting(fullSavePath, False)
            return
        for id in info:
            delugeTorrentPath = os.path.join(info[id]['save_path'], info[id]['name'])
            if delugeTorrentPath == fullSavePath:
                self.torrent_accounting(fullSavePath, True)
                return
        self.torrent_accounting(fullSavePath, False)


    def get_torrent_data(self, torrent_id, topLevelTitle, fullSavePath):
        done = len(self.torrentsToAdd) - self.torrentCounter
        print u"Added {}/{} {} ({})".format(done, len(self.torrentsToAdd),
                                            topLevelTitle, fullSavePath).encode('utf8')
        if torrent_id == None:
            client.core.get_torrents_status({'name': topLevelTitle}, ['save_path', 'name']).addCallback(
                self.check_already_exists, fullSavePath)
            return
        client.core.pause_torrent([torrent_id])
        self.waitingOnTorrents[torrent_id] = True
        self.torrent_accounting(fullSavePath, True)
        client.core.get_torrent_status(torrent_id, ['name', 'files', 'save_path']).addCallback(self.resolve_paths,
                                                                                               torrent_id,
                                                                                               topLevelTitle)


    def resolve_paths(self, info, torrent_id, topLevelTitle):
        saveName = topLevelTitle
        if len(info['files']) > 1:
            mainFolder = info['files'][0]['path'].split('/')[0]
            if mainFolder != saveName:
                print u"Renaming {} => {}".format(mainFolder, saveName).encode('utf8')
                client.core.rename_folder(torrent_id, mainFolder + '/', saveName)
                return
        else:
            mainFile = info['files'][0]['path']
            if mainFile != saveName:
                print u"Renaming {} => {}".format(mainFile, saveName).encode('utf8')
                client.core.rename_files(torrent_id, [(0, saveName)])
                return

        # file/folder not renamed, check now and remove from waiting list
        self.torrent_check(torrent_id)
        self.check_done()

    def could_not_connect(self, result):
        self.log_error(['Connection failed!',
                        'Please ensure that deluge is running and is in client/server mode, not "classic" mode.'])
        self.disconnect()

def defaultResumePath():
    appData = os.path.expanduser('~')
    if os.getenv('APPDATA'):
        appData = os.getenv('APPDATA')
    elif os.path.isdir(os.path.join(appData, '.wine')):
        appData = os.path.join(appData, '.wine/drive_c/users', getuser(), 'Application Data')
    return os.path.join(appData, 'uTorrent', 'resume.dat')

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description = 'Import torrents from uTorrent into Deluge.',
        formatter_class = argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('resumePath', nargs='?', default=defaultResumePath(), help="path of uTorrent resume.dat file")
    parser.add_argument('--host', default='127.0.0.1', help="deluge daemon host")
    parser.add_argument('--port', '-p', type=int, default=58846, help="deluge daemon port")
    parser.add_argument('--user', '-u', help="deluge daemon user")
    parser.add_argument('--password', help="deluge daemon password (omit to be asked)")
    parser.add_argument('--no-wine-mapping', action='store_true', help="disable wine drive letter mapping")

    args = parser.parse_args()
    log_location = os.getcwd()

    if args.user is not None and args.password is None:
        args.password = getpass("Password for {}: ".format(args.user))

    resumePathParts = args.resumePath.split(os.path.sep)
    os.chdir(os.path.sep.join(resumePathParts[:-1]))
    pathToResumeDat = args.resumePath

    Exporter = UtorrentToDeluge(pathToResumeDat)
    Exporter.setLogPath(log_location)

    if not args.no_wine_mapping:
        Exporter.enable_wine_drive_mapping()

    d = client.connect(
        args.host,
        args.port,
        args.user if args.user is not None else '',
        args.password if args.password is not None else '')
    d.addCallback(Exporter.begin_export)
    d.addErrback(Exporter.could_not_connect)
    reactor.run()


if __name__ == '__main__':
    main()
