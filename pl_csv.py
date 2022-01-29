#! /usr/bin/python3

"""
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

import argparse
import csv
import os
import sys
import warnings
import yaml
import spotipy
from spotipy.oauth2 import SpotifyOAuth


warnings.simplefilter('always', DeprecationWarning)


def check_file(fn):
    if not fn:
        return
    if os.path.exists(fn):
        print('{} already exists'.format(fn))
        sys.exit()


def fm_ms(ms):
    """ convert milliseconds to MM:SS """
    mins, seconds = divmod(round(ms / 1000), 60)
    return '{:02}:{:02}'.format(int(mins), int(seconds))


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

            track_info = {'artist': track['artists'][0]['name'],
                          'performer': track['artists'][0]['name'],
                          'title': track['name'],
                          'album': album['name'],
                          'duration': fm_ms(track['duration_ms']),
                          'fullpath': 'spotify',
                          'label': album['label'],
                          'released': album['release_date'],
                          'release_date_precision': album['release_date_precision']
                          }
            tracklist.append(track_info)

        if results['next']:
            results = sp.next(results)
        else:
            break

    return tracklist


def tl_to_csv(items):
    """ turn items into tracklist suitable for CSV"""

    tracklist = []
    for track in items:
        track_info = [track['artist'],
                      track['title'],
                      track['album'],
                      track['duration'],
                      ]
        tracklist.append(track_info)

    return tracklist


def write_yaml(fp, tl):
    with open(fp, 'w', encoding='utf-8') as file:
        yaml.dump(tl, file, explicit_start=True)


def write_csv(fp, delimiter, tl, noheader):

    tracklist = tl_to_csv(tl)

    # format that spot_csv.pl understands
    if not noheader:
        tracklist.insert(0, ["performer", "title", "album", "duration"])

    with open(fp, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='unix', delimiter=delimiter)
        writer.writerows(tracklist)


def main():
    argp = argparse.ArgumentParser(description='Download Spotify Playlist as CSV or YAML')
    argp_csv = argp.add_argument_group('csv', 'write to a csv file')
    argp_yaml = argp.add_argument_group('yaml', 'write to a yaml file')
    argp_csv.add_argument('--csv', help='name of CSV file to write')
    argp_csv.add_argument('--delimiter', help='field delimiter', default=',')
    argp_csv.add_argument('--noheader', help='do not write header line', action='store_true')
    argp_yaml.add_argument('--yaml', help='name of YAML file to write')
    argp.add_argument('-o', '--overwrite', help='overwrite files', action='store_true')
    argp.add_argument('pl_id', help='Spotify id of playlist', metavar='playlist_id')
    args = argp.parse_args()

    if not args.csv and not args.yaml:
        print('must provide a csv or yaml file name')
        return

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
        write_csv(args.csv, args.delimiter, tracklist, args.noheader)

    if args.yaml:
        write_yaml(args.yaml, tracklist)


if __name__ == '__main__':
    main()
