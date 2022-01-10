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

filepath = "/tmp/spot.csv"
if os.path.exists(filepath):
    print("File already exists!")
    quit()

# globals?  Damn Python seems to love them
def write_csv():

    # format that spot_csv.pl understands
    csv_headers = ["performer", "title", "album", "duration_ms"]
    tracklist = []
    tracklist.append(csv_headers)


    for item in tracks['items']:
        track = item['track']

        # Secondary query for album details
        album=sp.album( track['album']['uri'] )

        track_info =[ track['artists'][0]['name'],
                      track['name'],
                      album['name'],
                      track['duration_ms'],
                    ]
        tracklist.append(track_info)

    with open(filepath, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='unix', delimiter='|')
        writer.writerows(tracklist)

scope = "playlist-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
fields="tracks,next"
results = sp.user_playlist('joewahoo', '6CoGeD2spqwCj5qneYEAt0')
tracks = results['tracks']
write_csv()
# while tracks['next']:
#     tracks = sp.next[tracks]
#     show_tracks()
