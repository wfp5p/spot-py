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
"""

import argparse
import csv
import json
import yaml
import spotipy

from functools import partial
from pathlib import Path
from pylibwfp import file_arg_exist, check_file_for_overwrite
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException



def fm_ms(ms):
    """convert milliseconds to MM:SS"""
    mins, seconds = divmod(round(ms / 1000), 60)
    return f'{int(mins)}:{int(seconds):02d}'


def pl_iter(sp, playlist):
    """iterator for playlist_items"""

    pl = playlist['tracks']

    yield from pl['items']
    while pl['next']:
        pl = sp.next(pl)
        yield from pl['items']


def readBreaks(breakfile):
    """read file of line numbers to break at, return list of lines to break at"""
    brks = set()
    if not breakfile:
        return brks

    p = Path(breakfile)
    with p.open('r', encoding='utf-8') as f:
        for i in f:
            try:
                brks.add(int(i))
            except ValueError:
                pass

    return brks




def create_items(sp, playlist):
    """turn items into tracklist suitable for YAML dump"""

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
            try:
                album = sp.album(track['album']['uri'])
            except SpotifyException:
                pass
            else:
                track_info['label'] = album['label']
                track_info['released'] = album['release_date'][:4]
                track_info['release_date'] = album['release_date']
                track_info['release_date_precision'] = album['release_date_precision']

        tracklist.append(track_info)

    return tracklist


def write_yaml(filename, tracklist):
    with open(filename, 'w', encoding='utf-8') as outfile:
        yaml.dump(tracklist, outfile, explicit_start=True)

def write_json(filename, tracklist):
    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(tracklist, outfile, indent=1, ensure_ascii=False)

# add (NEW) logic!


def write_csv(args, tracklist, brk):
    fp = args.csv
    noheader = args.noheader

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

    brk_row = {'duration': '!'}

    with open(fp, 'w', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile,
                                dialect='unix',
                                extrasaction='ignore',
                                fieldnames=outputFormat)

        if not noheader:
            writer.writeheader()

        for idx, row in enumerate(tracklist, start=1):
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
    argp_csv.add_argument('--nolabel',
                          help='do not add record labels',
                          action='store_true')
    argp_csv.add_argument('--noheader',
                          help='do not write header line',
                          action='store_true')
    argp_csv.add_argument('--breaks',
                          help='file listing line numbers to break after',
                          type=file_arg_exist())
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
    outfiles = []
    if check_file_for_overwrite(args.csv, args.overwrite):
        outfiles.append(partial(write_csv, args=args, brk=readBreaks(args.breaks)))

    if check_file_for_overwrite(args.yaml, args.overwrite):
        outfiles.append(partial(write_yaml, filename=args.yaml))

    if check_file_for_overwrite(args.json, args.overwrite):
        outfiles.append(partial(write_json, filename=args.json))

    if not outfiles:
        print('no valid output files found')
        return

    scope = 'playlist-read-private'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    try:
        pl = sp.playlist(args.pl_id)
    except SpotifyException:
        print('playlist not found')
        return

    tracklist = create_items(sp, pl)

    for output in outfiles:
        output(tracklist=tracklist)


if __name__ == '__main__':
    main()
