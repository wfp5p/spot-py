#! /usr/bin/python3
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

"""

import argparse
import csv
import os
import sys
import warnings
import yaml
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth

warnings.simplefilter('always', DeprecationWarning)

logger = logging.getLogger('pl_csv')


def check_file(fn):
    if not fn:
        return
    if os.path.exists(fn):
        print('{} already exists'.format(fn))
        sys.exit()


def fm_ms(ms):
    """ convert milliseconds to MM:SS """
    mins, seconds = divmod(round(ms / 1000), 60)
    return '{}:{:02}'.format(int(mins), int(seconds))


def create_items(sp, playlist_id):
    """ turn items into tracklist suitable for YAML dump"""

    results = sp.playlist_items(playlist_id)
    tracklist = []
    while True:
        items = results['items']
        for item in items:
            track = item['track']

            # Secondary query for album details
            album = sp.album(track['album']['uri'])

            track_info = {
                'artist': track['artists'][0]['name'],
                'performer': track['artists'][0]['name'],
                'title': track['name'],
                'album': album['name'],
                'duration': fm_ms(track['duration_ms']),
                'fullpath': 'spotify',
                'label': album['label'],
                'released': album['release_date'][:4],
                'release_date': album['release_date'],
                'release_date_precision': album['release_date_precision'],
                'spot_id': track['id']
            }
            tracklist.append(track_info)

        if results['next']:
            results = sp.next(results)
        else:
            break

    return tracklist


def write_yaml(fp, tl):
    with open(fp, 'w', encoding='utf-8') as outfile:
        yaml.dump(tl, outfile, explicit_start=True)


# add (NEW) logic!
# format 1 is old style to feed into noburn pass 1
# format 2 mimics what noburn pass 1 would emit
# format 3 is like format 2 but has spotify track id number
# format 4 is 2 plus spot_id


def write_csv(fp, delimiter, tl, noheader, fnum, brk):
    formats = [['performer', 'title', 'album', 'duration'],
               [
                   'title', 'duration', 'performer', 'album', 'released',
                   'label', 'composer', 'notes'
               ], ['title', 'duration', 'performer', 'album', 'spot_id'],
               [
                   'title', 'duration', 'performer', 'album', 'released',
                   'label', 'composer', 'notes', 'spot_id'
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
            writer.writerow(row)
            if idx in brk:
                writer.writerow(brk_row)


def main():
    argp = argparse.ArgumentParser(
        description='Download Spotify Playlist as CSV or YAML')
    argp_csv = argp.add_argument_group('csv', 'write to a csv file')
    argp_yaml = argp.add_argument_group('yaml', 'write to a yaml file')
    argp_csv.add_argument('--csv', help='name of CSV file to write')
    argp_csv.add_argument('--delimiter', help='field delimiter', default=',')
    argp_csv.add_argument('--format',
                          help='output format',
                          type=int,
                          choices=range(1, 5),
                          default=2)
    argp_csv.add_argument('--noheader',
                          help='do not write header line',
                          action='store_true')
    argp_csv.add_argument('--breaks',
                          help='file listing line numbers to break after')
    argp_yaml.add_argument('--yaml', help='name of YAML file to write')
    argp.add_argument('-o',
                      '--overwrite',
                      help='overwrite files',
                      action='store_true')
    argp.add_argument('pl_id',
                      help='Spotify id of playlist',
                      metavar='playlist_id')
    args = argp.parse_args()

    if not args.csv and not args.yaml:
        print('must provide a csv or yaml file name')
        return

    brk = []
    if args.csv and args.breaks:
        if not os.path.exists(args.breaks):
            raise argparse.ArgumentTypeError("breakfile %s doesn't exist" %
                                             args.breaks)
        with open(args.breaks, 'r') as f:
            for i in f:
                try:
                    brk.append(int(i))
                except ValueError:
                    next
    if not args.overwrite:
        check_file(args.csv)
        check_file(args.yaml)

    scope = "playlist-read-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    # 6CoGeD2spqwCj5qneYEAt0 show94
    # 4JDfhw91zUmmqLemqaVp6F future shows
    # 1CAwKEuuTl2AllTvBOtc2K over 100 test

    tracklist = create_items(sp, args.pl_id)

    if args.csv:
        write_csv(args.csv, args.delimiter, tracklist, args.noheader,
                  args.format, brk)

    if args.yaml:
        write_yaml(args.yaml, tracklist)


if __name__ == '__main__':
    main()
