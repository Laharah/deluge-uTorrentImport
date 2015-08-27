"""
Functions for extracting and translating metadata from utorrent resume data to deluge
compatable values
"""

import deluge.component as component
from common import Log

log = Log()
log.transmitting=True

_translate_inf = lambda x: -1 if x == 0 else x

def max_download_speed(info):
    downspeed = float(info['downspeed'])/1024
    return _translate_inf(downspeed)

def max_upload_speed(info):
    upspeed = float(info['upspeed'])/1024
    return _translate_inf(upspeed)

def max_connections(info):
    return info['max_connections']

def max_upload_slots(info):
    return _translate_inf(info['ulslots'])


def transfer(torrent_id, info, tags):
    torrent = component.get('TorrentManager')[torrent_id]
    tags = set(tags)
    if 'time_added' in tags:
        log.debug('Setting time_added on torrent {0}'.format(torrent_id))
        torrent.time_added = info['added_on']
        tags.remove('time_added')
    translators = {
        'max_download_speed': max_download_speed,
        'max_upload_speed': max_upload_speed,
        'max_connections': max_connections,
        'max_upload_slots': max_upload_slots,
    }

    options = {}
    for tag in tags:
        try:
            translate = translators[tag]
        except KeyError:
            log.error('{0} is not a valid torrent option for transfer'.format(tag))
            continue
        value = translate(info)
        log.debug('Setting {0} -> {1} on torrent {2}'.format(
            tag, value, torrent_id))
        options[tag] = value

    torrent.set_options(options)
