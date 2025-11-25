# backendSong/itunes_client.py

import re
import requests

# Simple in-memory cache: {(track_lower, artist_lower): preview_url_or_empty}
_ITUNES_CACHE = {}


def _normalize_title(s: str) -> str:
    """
    Normalize song titles so we can compare iTunes results to the
    expected track name more robustly.

    Examples:
      "Bound 2 (Album Version)"  -> "bound 2"
      "Bound 2 - Radio Edit"     -> "bound 2"
      "Heartless"                -> "heartless"
    """
    if not s:
        return ""
    s = s.lower()
    # remove parentheses and bracket content: (..), [..]
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\[.*?\]", "", s)
    # keep only letters, digits, and spaces
    s = re.sub(r"[^a-z0-9\s]", "", s)
    # collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def find_itunes_preview(track, artist=None):
    """
    Query Apple's iTunes Search API for a preview MP3, but only accept
    results whose track title *really* matches the requested track name.

    If no close match is found, returns None instead of a wrong song.
    """
    if not track:
        return None

    key = (track.strip().lower(), (artist or "").strip().lower())

    # 1) Check cache first (even cached failures)
    if key in _ITUNES_CACHE:
        cached = _ITUNES_CACHE[key]
        return cached or None

    base = "https://itunes.apple.com/search"

    # Build search query
    query = track
    if artist:
        query += f" {artist}"

    params = {
        "term": query,
        "media": "music",
        "limit": 5
    }

    try:
        resp = requests.get(base, params=params, timeout=3)
    except requests.RequestException as e:
        print("iTunes API request error:", e)
        _ITUNES_CACHE[key] = ""
        return None

    if resp.status_code != 200:
        print("iTunes API error:", resp.status_code, resp.text)
        _ITUNES_CACHE[key] = ""
        return None

    data = resp.json()
    results = data.get("results", [])
    if not results:
        _ITUNES_CACHE[key] = ""
        return None

    norm_target = _normalize_title(track)

    # Only accept results with a normalized title that matches exactly
    for item in results:
        preview = item.get("previewUrl")
        title = item.get("trackName") or item.get("collectionName")
        if not preview or not title:
            continue

        norm_title = _normalize_title(title)

        # Strict: must be the same normalized title
        if norm_title == norm_target:
            _ITUNES_CACHE[key] = preview
            return preview

    # If nothing matches well, don't use iTunes preview at all
    _ITUNES_CACHE[key] = ""
    return None
