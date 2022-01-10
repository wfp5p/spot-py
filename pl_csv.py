#! /usr/bin/python3

"""
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import csv
import yaml
import os
import warnings

warnings.simplefilter('always', DeprecationWarning)



def fm_ms(ms):
    """ convert milliseconds to MM:SS """
    mins, seconds = divmod(round(ms / 1000), 60)
    return '{:02}:{:02}'.format(int(mins), int(seconds))


def create_items(tracklist, items):
    """ turn items into tracklist suitable for YAML dump"""

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

def tl_to_csv(items):
    """ turn items into tracklist suitable for CSV"""

    tracklist = []
    for track in items:
        track_info =[ track['artist'],
                      track['title'],
                      track['album'],
                      track['duration'],
                    ]
        tracklist.append(track_info)

    return tracklist


def write_yaml(fp, tl):
     with open(fp, 'w', encoding='utf-8') as file:
        yaml.dump(tl,file,explicit_start=True)


def write_csv(fp, tl):

    # format that spot_csv.pl understands
    csv_headers = ["performer", "title", "album", "duration"]

    tracklist = tl_to_csv(tl)
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

results = sp.playlist_items('6CoGeD2spqwCj5qneYEAt0') # show94
#results = sp.playlist_items('4JDfhw91zUmmqLemqaVp6F') # future shows
#results = sp.playlist_items('1CAwKEuuTl2AllTvBOtc2K') # over 100 test

#tracks = results['tracks']
tracklist = []
create_items(tracklist,results['items'])

while results['next']:
    results = sp.next(results)
    create_items(tracklist,results['items'])

write_csv(filepath, tracklist)
#write_yaml(filepath, tracklist)
