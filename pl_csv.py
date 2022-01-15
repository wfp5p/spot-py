#! /usr/bin/python3

"""
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import argparse
import csv
import yaml
import os
import warnings

warnings.simplefilter('always', DeprecationWarning)


def check_file(fn):
    if not fn:
        return
    if os.path.exists(fn):
        print('{} already exists'.format(fn))
        quit()


def fm_ms(ms):
    """ convert milliseconds to MM:SS """
    mins, seconds = divmod(round(ms / 1000), 60)
    return '{:02}:{:02}'.format(int(mins), int(seconds))


def create_items(tracklist, items):
    """ turn items into tracklist suitable for YAML dump"""

    for item in items:
        track = item['track']

        # Secondary query for album details
        album = sp.album(track['album']['uri'])

        track_info = {'artist': track['artists'][0]['name'],
                      'title': track['name'],
                      'album': album['name'],
                      'duration': fm_ms(track['duration_ms']),
                      'fullpath': 'spotify'
                      }
        tracklist.append(track_info)

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


def write_csv(fp, delimiter, tl):

    # format that spot_csv.pl understands
    csv_headers = ["performer", "title", "album", "duration"]

    tracklist = tl_to_csv(tl)
    tracklist.insert(0, csv_headers)

    with open(fp, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='unix', delimiter=delimiter)
        writer.writerows(tracklist)


argp = argparse.ArgumentParser(description='Download Spotify Playlist as CSV or YAML')
argp_csv = argp.add_argument_group('csv', 'write to a csv file')
argp_yaml = argp.add_argument_group('yaml', 'write to a yaml file')
argp_csv.add_argument('--csv', help='name of CSV file to write')
argp_csv.add_argument('--delimiter', help='field delimiter', default=',')
argp_yaml.add_argument('--yaml', help='name of YAML file to write')
argp.add_argument('-o', '--overwrite', help='overwrite files', action='store_true')
argp.add_argument('pl_id', help='Spotify id of playlist', metavar='playlist_id')
args = argp.parse_args()

if not args.csv and not args.yaml:
    print('must provide a csv or yaml file name')
    quit()

if not args.overwrite:
    check_file(args.csv)
    check_file(args.yaml)

scope = "playlist-read-private"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.playlist_items(args.pl_id)
# results = sp.playlist_items('6CoGeD2spqwCj5qneYEAt0') # show94
# results = sp.playlist_items('4JDfhw91zUmmqLemqaVp6F') # future shows
# results = sp.playlist_items('1CAwKEuuTl2AllTvBOtc2K') # over 100 test

tracklist = []
create_items(tracklist, results['items'])

while results['next']:
    results = sp.next(results)
    create_items(tracklist, results['items'])

if args.csv:
    write_csv(args.csv, args.delimiter, tracklist)

if args.yaml:
    write_yaml(args.yaml, tracklist)
