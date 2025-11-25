# backendSong/spotify_client.py

import requests
from spotify_auth import get_valid_token

BASE_URL = "https://api.spotify.com/v1"


def spotify_get(endpoint, params=None):
    """
    Generic helper for GET requests to the Spotify Web API
    using the logged-in user's access token.

    Returns EITHER:
      - dict (normal successful JSON response)
      - (dict, status_code) on errors (auth, parse, non-JSON, etc.)
    """
    token = get_valid_token()

    if not token:
        return {"error": "not_authenticated"}, 401

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
    except requests.RequestException as e:
        print("Spotify request error:", e)
        return {"error": "spotify_request_failed"}, 500

    # Try JSON; if it fails, report explicitly
    try:
        data = response.json()
    except ValueError:
        body_text = (response.text or "")[:500]
        print(
            f"Spotify non-JSON response from {url} "
            f"status={response.status_code} body={body_text!r}"
        )
        return {
            "error": "spotify_non_json",
            "status": response.status_code,
            "body_excerpt": body_text,
        }, response.status_code

    # If Spotify returns an error JSON (4xx/5xx), bubble it with the status
    if not response.ok:
        print(f"Spotify error response from {url}: {data}")
        return data, response.status_code

    return data


def get_user_top_tracks(limit=20, time_range="long_term"):
    """Wraps GET /me/top/tracks."""
    return spotify_get("me/top/tracks", {"limit": limit, "time_range": time_range})


def get_user_top_artists(limit=50, time_range="long_term"):
    """Wraps GET /me/top/artists."""
    return spotify_get("me/top/artists", {"limit": limit, "time_range": time_range})


def get_playlist_tracks(playlist_id, limit=100):
    """Wraps GET /playlists/{playlist_id}/tracks."""
    return spotify_get(f"playlists/{playlist_id}/tracks", {"limit": limit})


def search_playlists(query, limit=5):
    """Wraps GET /search?q=...&type=playlist."""
    params = {"q": query, "type": "playlist", "limit": limit}
    return spotify_get("search", params)
