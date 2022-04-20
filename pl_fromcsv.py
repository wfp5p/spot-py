#! /usr/bin/python3

"""
Read a playist from CSV and create a new playlist

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

# Creates a playlist for a user

import argparse
import csv
import warnings
import logging
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger('pl_fromcsv')

def file_exists(value):
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError("%s does not exist" % value)
    return value


def get_args():
    parser = argparse.ArgumentParser(description='Creates a playlist from a CSV')
    parser.add_argument('-p', '--playlist', required=True,
                        help='Name of Playlist')
    parser.add_argument('-d', '--description', required=False, default='',
                        help='Description of Playlist')
    parser.add_argument('--csv', type=file_exists,
                        required=True, help='name of CSV file to read')
    return parser.parse_args()


def main():
    args = get_args()

    tracks = []

    with open(args.csv) as csvfile:
        reader = csv.DictReader(csvfile, dialect='unix')
        headers = reader.fieldnames

        if not 'spot_id' in headers:
            raise Exception('csv file does not have spot_id field')

        for row in reader:
            if row['spot_id']:
                tracks.append(row['spot_id'])

    scope = "playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    user_id = sp.me()['id']
    result = sp.user_playlist_create(user_id, args.playlist)
    pl_id = result['id']

    sp.playlist_add_items(pl_id, tracks)



if __name__ == '__main__':
    main()
