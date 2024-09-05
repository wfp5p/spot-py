#! /usr/bin/python
"""
Export playlist as CSV, JSON, or YAML

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

import argparse
import csv
import dataclasses
import json
from typing import Optional

import spotipy
import yaml
from pylibwfp import check_file_for_overwrite
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth


@dataclasses.dataclass(slots=True, kw_only=True)
class LabelInfo:
    label: str
    release_date: str
    release_date_precision: str
    released: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.released = self.release_date[:4]

    @classmethod
    def fromAlbum(cls, album):
        return cls(
            label=album['label'],
            release_date=album['release_date'],
            release_date_precision=album['release_date_precision'],
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class TrackInfo:
    artist: str
    title: str
    album: str
    duration: str
    fullpath: str
    added_at: Optional[str] = None
    spot_id: Optional[str] = None
    label: Optional[LabelInfo] = None

    def asdict(self):
        """Expand label into toplevel dict"""
        d = dataclasses.asdict(self)
        if label := d.pop('label', None):
            d = d | label
        return d

    @classmethod
    def add_yaml_representer(cls):
        """add a yaml representer for this class"""
        yaml.add_representer(cls,
                             lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.asdict()))

    @classmethod
    def fromItem(cls, item, fullpath='spotify'):
        def fm_ms(ms):
            """convert milliseconds to MM:SS"""
            mins, seconds = divmod(round(ms / 1000), 60)
            return f'{int(mins)}:{int(seconds):02d}'

        track = item['track']
        return cls(
            artist=track['artists'][0]['name'],
            title=track['name'],
            album=track['album']['name'],
            duration=fm_ms(track['duration_ms']),
            fullpath=fullpath,
            spot_id=track['id'],
            added_at=item['added_at'],
        )


class Playlist:
    __slots__ = ['tracks', 'csvoptions']

    def __init__(self, tracks=None, csvoptions=None):
        self.tracks = list(tracks) if tracks else list()
        self.csvoptions = {'noheader': False, 'nolabel': False}
        if csvoptions:
            self.csvoptions = self.csvoptions | csvoptions

    def readPlaylist(self, sp, playlistID):
        """read playlist tracks using playlist ID"""

        items = self.pl_iter(sp, sp.playlist(playlistID))

        for item in items:
            trackinfo = TrackInfo.fromItem(item)

            # Secondary query for album details
            if album_id := item['track']['album']['id']:
                try:
                    album = sp.album(album_id)
                except SpotifyException:
                    pass
                else:
                    trackinfo.label = LabelInfo.fromAlbum(album)

            self.tracks.append(trackinfo)

        return

    @staticmethod
    def pl_iter(sp, playlist):
        """iterator for playlist_items"""

        pl = playlist['tracks']

        yield from pl['items']
        while pl['next']:
            pl = sp.next(pl)
            yield from pl['items']

    def writeOutput(self, *, fileformat, filename):
        match fileformat:
            case 'yaml':
                self.write_yaml(filename)
            case 'json':
                self.write_json(filename)
            case 'csv':
                self.write_csv(filename)

        return

    def write_yaml(self, filename):
        TrackInfo.add_yaml_representer()
        with open(filename, 'w', encoding='utf-8') as outfile:
            yaml.dump(self.tracks, outfile, explicit_start=True)

    def write_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as outfile:
            json.dump(self.tracks, outfile, default=lambda o: o.asdict(), indent=1, ensure_ascii=False)

    def write_csv(self, filename):
        outputFormat = [
            'title',
            'duration',
            'performer',
            'album',
            'released',
            'label',
            'composer',
            'notes',
            'spot_id',
            'added_at',
        ]

        with open(filename, 'w', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile,
                                    dialect='unix',
                                    extrasaction='ignore',
                                    fieldnames=outputFormat)

            if not self.csvoptions['noheader']:
                writer.writeheader()

            for track in self.tracks:
                row = track.asdict()
                row['performer'] = row['artist']
                if self.csvoptions['nolabel']:
                    row['label'] = ''
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
    outfiles = list()
    for outType in ['yaml', 'json', 'csv']:
        if outFname := vars(args)[outType]:
            if check_file_for_overwrite(outFname, args.overwrite):
                outfiles.append({'fileformat': outType, 'filename': outFname})

    if not outfiles:
        print('no valid output files found')
        return

    playlist = Playlist(csvoptions={'noheader': args.noheader, 'nolabel': args.nolabel})

    scope = 'playlist-read-private'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    try:
        playlist.readPlaylist(sp, args.pl_id)
    except SpotifyException:
        print('playlist not found')
        return

    for output in outfiles:
        playlist.writeOutput(**output)


if __name__ == '__main__':
    main()
