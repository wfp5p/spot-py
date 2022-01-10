#! /usr/bin/python3

'''
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
'''

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import csv
import os
from datetime import timedelta


# convert milliseconds to MM:SS
def fm_ms(ms):
    mins, seconds = divmod(round(ms / 1000), 60)
    return '{:02}:{:02}'.format(int(mins), int(seconds))

def write_csv(fp, items):

    # format that spot_csv.pl understands
    csv_headers = ["performer", "title", "album", "duration_ms"]
    tracklist = []
    tracklist.append(csv_headers)


    for item in items: #tracks['items']:
        track = item['track']

        # Secondary query for album details
        album=sp.album( track['album']['uri'] )

        track_info =[ track['artists'][0]['name'],
                      track['name'],
                      album['name'],
                      fm_ms(track['duration_ms']),
                    ]
        tracklist.append(track_info)

    with open(fp, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='unix', delimiter='|')
        writer.writerows(tracklist)


filepath = "/tmp/spot.csv"
if os.path.exists(filepath):
    print("File already exists!")
    quit()

scope = "playlist-read-private"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
results = sp.user_playlist('joewahoo', '6CoGeD2spqwCj5qneYEAt0')
write_csv(filepath, results['tracks']['items'])
