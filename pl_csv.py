#! /usr/bin/python3

'''
Export playlist as CSV

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
'''

import spotipy
from spotipy.oauth2 import SpotifyOAuth

def show_tracks():

    for i, item in enumerate(tracks['items']):

        track = item['track']

        # Secondary query for album details
        album=sp.album( track['album']['uri'] )

        output=["{:s}".format(track['artists'][0]['name']),
                "{:s}".format(album['name']),
                "{:s}".format(track['name']),
                "{:02d}".format(track['track_number']),
                "{:02d}".format(track['disc_number']),
                "{:d}".format(track['duration_ms']),
                "{:s}".format(album['release_date']),
                "{:s}".format(album['release_date_precision']),
                ]

        # Form and print the ; separated string
        print(";".join(output))

scope = "playlist-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
fields="tracks,next"
results = sp.user_playlist('joewahoo', '6CoGeD2spqwCj5qneYEAt0', fields=fields)
tracks = results['tracks']
show_tracks()
while tracks['next']:
    tracks = sp.next[tracks]
    show_tracks()
