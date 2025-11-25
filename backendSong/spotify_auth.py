# backendSong/spotify_auth.py

import base64
import requests
import time
from flask import session, redirect, request

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, REDIRECT_URI, FRONTEND_URL

TOKEN_URL = "https://accounts.spotify.com/api/token"


def _encode_client_credentials():
    creds = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    return base64.b64encode(creds.encode()).decode()


# -------------------------------------------
# 1. Redirect user to Spotify login
# -------------------------------------------
def spotify_login():
    scope = "user-top-read playlist-read-private playlist-read-collaborative"

    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
        f"&show_dialog=true"  # <-- this forces Spotify to show the chooser every time
    )

    return redirect(auth_url)


# -------------------------------------------
# 2. Spotify redirects back → exchange code
# -------------------------------------------
def spotify_callback():
    code = request.args.get("code")

    if not code:
        return "Authorization failed.", 400

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {
        "Authorization": f"Basic {_encode_client_credentials()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(TOKEN_URL, data=token_data, headers=headers)
    tokens = response.json()

    if "access_token" not in tokens:
        return f"Error fetching token: {tokens}", 400

    # Save tokens in session
    session["access_token"] = tokens["access_token"]
    session["refresh_token"] = tokens.get("refresh_token")
    session["expires_at"] = time.time() + tokens["expires_in"]

    return redirect(FRONTEND_URL)


# -------------------------------------------
# 3. Auto-refresh access token if expired
# -------------------------------------------
def get_valid_token():
    """
    Returns a valid access token from the session, refreshing if needed.
    """
    if "access_token" not in session:
        return None

    expires_at = session.get("expires_at", 0)

    # If not close to expiring, just use current token
    if time.time() < expires_at - 60:
        return session["access_token"]

    # Need to refresh token
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return None

    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    headers = {
        "Authorization": f"Basic {_encode_client_credentials()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(TOKEN_URL, data=refresh_data, headers=headers)
    tokens = response.json()

    if "access_token" not in tokens:
        print("Failed to refresh token:", tokens)
        return None

    new_access = tokens["access_token"]
    expires_in = tokens.get("expires_in", 3600)

    session["access_token"] = new_access
    session["expires_at"] = time.time() + expires_in

    return new_access
