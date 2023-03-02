#! /usr/bin/python
"""
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env

artist => performer
title => title
duration => duration
album => album
released => released (but spot data needs a massage)
label => label

format #1 is 'performer','title','album','duration'
format #2 is 'title','duration','performer','album','released','label','composer','notes'
format #3 is 'title', 'duration', 'performer', 'album', 'spot_id'
format #4 is 'title', 'duration', 'performer', 'album', 'released', 'label', 'composer', 'notes', 'spot_id'

format 1 is old style to feed into noburn pass 1
format 2 mimics what noburn pass 1 would emit
format 3 is format 1 but has spotify track id number
format 4 is format 2 plus spot_id

"""

import argparse
import csv
import json
import os
import warnings
import yaml
import spotipy
import logging
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

warnings.simplefilter('always', DeprecationWarning)

logger = logging.getLogger('pl_csv')


def check_file(fn, overwrite):
    if not fn:
        return False
    if os.path.exists(fn):
        if overwrite and os.path.isfile(fn):
            return True
        print(f'{fn} already exists')
        return False
    return True


def fm_ms(ms):
    """ convert milliseconds to MM:SS """
    mins, seconds = divmod(round(ms / 1000), 60)
    return f'{int(mins)}:{int(seconds):02d}'


def pl_iter(sp, playlist):
    """iterator for playlist_items"""

    pl = playlist['tracks']

    yield from pl['items']
    while pl['next']:
        pl = sp.next(pl)
        yield from pl['items']


def create_items(sp, playlist):
    """ turn items into tracklist suitable for YAML dump"""

    tracklist = []
    items = pl_iter(sp, playlist)
    for item in items:
        track = item['track']

        track_info = {
            'artist': track['artists'][0]['name'],
            'performer': track['artists'][0]['name'],
            'title': track['name'],
            'album': track['album']['name'],
            'duration': fm_ms(track['duration_ms']),
            'fullpath': 'spotify',
            'spot_id': track['id'],
            'added_at': item['added_at']
        }

        # Secondary query for album details
        if track['album']['uri'] is not None:
            album = sp.album(track['album']['uri'])
            track_info['label'] = album['label']
            track_info['released'] = album['release_date'][:4]
            track_info['release_date'] = album['release_date']
            track_info['release_date_precision'] = album['release_date_precision']

        tracklist.append(track_info)

    return tracklist


def write_yaml(fp, tl):
    with open(fp, 'w', encoding='utf-8') as outfile:
        yaml.dump(tl, outfile, explicit_start=True)

def write_json(fp, tl):
    with open(fp, 'w', encoding='utf-8') as outfile:
        json.dump(tl, outfile, indent=1, ensure_ascii=False)

# add (NEW) logic!


def write_csv(args, tl, brk):
    fp = args.csv
    noheader = args.noheader
    fnum = args.format_number

    formats = [['performer', 'title', 'album', 'duration'],
               [
                   'title', 'duration', 'performer', 'album', 'released',
                   'label', 'composer', 'notes'
               ],
               ['title', 'duration', 'performer', 'album', 'spot_id'],
               [
                   'title', 'duration', 'performer', 'album', 'released',
                   'label', 'composer', 'notes', 'spot_id', 'added_at'
               ]]

    brk_row = {'duration': '!'}

    with open(fp, 'w', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile,
                                dialect='unix',
                                extrasaction='ignore',
                                fieldnames=formats[int(fnum) - 1])

        if not noheader:
            writer.writeheader()

        for idx, row in enumerate(tl, start=1):
            if args.nolabel:
                row['label'] = ''
            writer.writerow(row)
            if idx in brk:
                writer.writerow(brk_row)


def main():
    argp = argparse.ArgumentParser(
        description='Download Spotify Playlist as CSV or YAML')
    argp_csv = argp.add_argument_group('csv', 'write to a csv file')
    argp_yaml = argp.add_argument_group('yaml', 'write to a yaml file')
    argp_json = argp.add_argument_group('json', 'write to a json file')
    argp_csv.add_argument('--csv', help='name of CSV file to write')
    argp_csv.add_argument('--format',
                          help='output format',
                          type=int,
                          choices=range(1, 5),
                          default=4,
                          dest='format_number')
    argp_csv.add_argument('--nolabel',
                          help='do not add record labels',
                          action='store_true')
    argp_csv.add_argument('--noheader',
                          help='do not write header line',
                          action='store_true')
    argp_csv.add_argument('--breaks',
                          help='file listing line numbers to break after')
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

    brk = []
    if args.csv and args.breaks:
        if not os.path.exists(args.breaks):
            raise argparse.ArgumentTypeError(f"breakfile {str(args.breaks)} doesn't exist")
        with open(args.breaks, 'r', encoding='utf-8') as f:
            for i in f:
                try:
                    brk.append(int(i))
                except ValueError:
                    pass

    if not check_file(args.csv, args.overwrite) and not check_file(
            args.yaml, args.overwrite) and not check_file(
                args.json, args.overwrite):
        print('must provide a csv, yaml, or json file name')
        return


    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())


    try:
        pl = sp.playlist(args.pl_id)
    except SpotifyException:
        print('playlist not found')
        return

    tracklist = create_items(sp, pl)


    if args.csv:
        write_csv(args, tracklist, brk)

    if args.yaml:
        write_yaml(args.yaml, tracklist)

    if args.json:
        write_json(args.json, tracklist)


if __name__ == '__main__':
    main()
