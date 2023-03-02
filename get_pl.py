#! /usr/bin/python3

'''
Example how to get list of playlists

requires SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to be in shell env
'''

import argparse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def main():

    argp = argparse.ArgumentParser(description='List a users playlists')
    argp.add_argument('user',
                      help='Spotify id')
    args = argp.parse_args()

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    try:
        playlists = sp.user_playlists(args.user)
    except SpotifyException:
        print('error getting user playlists')
        return

    while playlists:
        for i, playlist in enumerate(playlists['items']):
            print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

if __name__ == '__main__':
    main()
