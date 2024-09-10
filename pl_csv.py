#! /usr/bin/python
"""
Export playlist as CSV, JSON, or YAML

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

import argparse
import csv
import json
from functools import partial

import spotipy
import yaml
from pylibwfp import check_file_for_overwrite
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth


def trackFromItem(item, fullpath='spotify'):
    def fm_ms(ms):
        """convert milliseconds to MM:SS"""
        mins, seconds = divmod(round(ms / 1000), 60)
        return f'{int(mins)}:{int(seconds):02d}'

    track = item['track']
    return {
        'artist': track['artists'][0]['name'],
        'title': track['name'],
        'duration': fm_ms(track['duration_ms']),
        'duration_ms': track['duration_ms'],
        'fullpath': fullpath,
        'spot_id': track['id'],
        'added_at': item['added_at'],
        'album': track['album']['name'],
        'album_id': track['album']['id'],
        'release_date': track['album']['release_date'],
        'release_date_precision': track['album']['release_date_precision'],
        'album_track_number': track['track_number'],
    }


class Playlist:
    def __init__(self, sp, playlistID):
        self.tracks = list()
        self._sp = sp
        self._spot_pl = self._sp.playlist(playlistID)

    def readTracks(self, nolabel=False):
        """read playlist tracks using playlist ID"""

        # add a track_number
        for itemNumber, item in enumerate(self.sp_iter(self._spot_pl['tracks']), start=1):
            trackinfo = trackFromItem(item)
            trackinfo['track_number'] = itemNumber

            if nolabel:
                trackinfo['label'] = None
            else:
                if album_id := trackinfo['album_id']:
                    try:
                        album = self._sp.album(album_id)
                    except SpotifyException:
                        pass
                    else:
                        trackinfo['label'] = album['label']

            self.tracks.append(trackinfo)

        return

    def sp_iter(self, iterable):
        yield from iterable['items']
        while iterable['next']:
            iterable = self._sp.next(iterable)
            yield from iterable['items']


def write_csv(data, fp, noheader=False, fieldnames=None):
    """fp is assumed to be an open file pointer"""
    defaultFields = [
        'title',
        'duration',
        'performer',
        'album',
        'released',
        'label',
        'composer',
        'notes',
        'spot_id',
        'album_id',
    ]

    if fieldnames is not None:
        defaultFields = fieldnames

    writer = csv.DictWriter(
        fp, dialect='unix', extrasaction='ignore', fieldnames=defaultFields
    )

    if not noheader:
        writer.writeheader()

    for row in data:
        if r := row['release_date']:
            row['released'] = r[:4]
        row['performer'] = row['artist']
        writer.writerow(row)


def main():
    argp = argparse.ArgumentParser(
        description='Download Spotify Playlist as CSV or YAML')
    argp_csv = argp.add_argument_group('csv', 'write to a csv file')
    argp_yaml = argp.add_argument_group('yaml', 'write to a yaml file')
    argp_json = argp.add_argument_group('json', 'write to a json file')
    argp_csv.add_argument('--csv', help='name of CSV file to write')
    argp_csv.add_argument('--nolabel',
                          help='do not add record labels',
                          action='store_true')
    argp_csv.add_argument('--noheader',
                          help='do not write header line',
                          action='store_true')
    argp_yaml.add_argument('--yaml', help='name of YAML file to write')
    argp_json.add_argument('--json', help='name of JSON file to write')
    argp.add_argument('-o',
                      '--overwrite',
                      help='overwrite files',
                      action='store_true')
    argp.add_argument('pl_id',
                      help='Spotify id of playlist',
                      metavar='playlist_id')
    args = argp.parse_args()

    # check for output files first to save the spotify call if there are none
    outTypes = (
        ('yaml', partial(yaml.dump, explicit_start=True)),
        ('json', partial(json.dump, indent=1, ensure_ascii=False)),
        ('csv', partial(write_csv, noheader=args.noheader)),
    )
    outfiles = list()
    for outType, writer in outTypes:
        if outFname := vars(args)[outType]:
            if check_file_for_overwrite(outFname, args.overwrite):
                outfiles.append(
                    {'fileformat': outType, 'filename': outFname, 'writer': writer}
                )

    if not outfiles:
        print('no valid output files found')
        return

    scope = 'playlist-read-private'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    try:
        playlist = Playlist(sp, args.pl_id)
    except SpotifyException:
        print('playlist not found')
        return

    playlist.readTracks(nolabel=args.nolabel)

    for output in outfiles:
        with open(output['filename'], 'w', encoding='utf-8') as outfile:
            output['writer'](playlist.tracks, outfile)


if __name__ == '__main__':
    main()
