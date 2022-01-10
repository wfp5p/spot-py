#! /usr/bin/python3

"""
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import csv
import yaml # maybe do the crazy stuff to get the C bindings?
import os



def fm_ms(ms):
    """ convert milliseconds to MM:SS """
    mins, seconds = divmod(round(ms / 1000), 60)
    return '{:02}:{:02}'.format(int(mins), int(seconds))


def create_yaml(items):
    """ turn items into tracklist suitable for YAML dump"""

    tracklist = []
    for item in items:
        track = item['track']

        # Secondary query for album details
        album=sp.album( track['album']['uri'] )

        track_info ={ 'artist' : track['artists'][0]['name'],
                      'title' : track['name'],
                      'album' : album['name'],
                      'duration' : fm_ms(track['duration_ms']),
                      'fullpath' : 'spotify'
                    }
        tracklist.append(track_info)

    return tracklist

def create_tracklist(items):
    """ turn items into tracklist suitable for CSV"""

    tracklist = []
    for item in items:
        track = item['track']

        # Secondary query for album details
        album=sp.album( track['album']['uri'] )

        track_info =[ track['artists'][0]['name'],
                      track['name'],
                      album['name'],
                      fm_ms(track['duration_ms']),
                    ]
        tracklist.append(track_info)

    return tracklist


def write_yaml(fp, items):

    tracklist = create_yaml(items)

    with open(fp, 'w', encoding='utf-8') as file:
        yaml.dump(tracklist,file,explicit_start=True)


def write_csv(fp, items):

    # format that spot_csv.pl understands
    csv_headers = ["performer", "title", "album", "duration"]

    tracklist = create_tracklist(items)
    tracklist.insert(0, csv_headers)

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
#write_yaml(filepath, results['tracks']['items'])
