# backendSong/quiz_generator.py

import random
from typing import List, Dict, Any, Optional

from itunes_client import find_itunes_preview


def _get_artist_names(track: Dict[str, Any]) -> str:
    """
    Build a nice 'Artist 1, Artist 2' string from a Spotify track object.
    """
    if not isinstance(track, dict):
        return ""

    artists = track.get("artists") or []
    names = [a.get("name", "") for a in artists if isinstance(a, dict) and a.get("name")]
    return ", ".join(names)


def _get_album_image_url(track: Dict[str, Any]) -> Optional[str]:
    """
    Get the first album image URL from a Spotify track object, if any.
    """
    if not isinstance(track, dict):
        return None

    album = track.get("album") or {}
    images = album.get("images") or []
    if images and isinstance(images, list):
        # Usually largest first
        first = images[0]
        if isinstance(first, dict):
            return first.get("url")
    return None


def generate_quiz_from_tracks(
    tracks: List[Dict[str, Any]],
    num_questions: int = 10,
    options_per_q: int = 4
) -> Dict[str, Any]:
    """
    Build a quiz JSON object from a list of Spotify track objects.

    Each question looks like:
    {
        "audio_url": "...",         # may be None if no preview found
        "image": "...",             # album cover URL or None
        "artist": "Artist 1, Artist 2",
        "correct": "Song Title",
        "options": ["Song A", "Song B", "Song C", "Song D"],
        "external_url": "https://open.spotify.com/track/..."
    }

    This function is defensive:
      - skips None / malformed track entries
      - handles missing titles / artists / images
      - returns {"questions": []} if nothing usable is found
    """

    if not tracks:
        return {"questions": []}

    # Clean tracks: keep only dictionaries with a name
    cleaned_tracks: List[Dict[str, Any]] = []
    for t in tracks:
        if isinstance(t, dict) and t.get("name"):
            cleaned_tracks.append(t)

    if not cleaned_tracks:
        return {"questions": []}

    # Shuffle for randomness
    shuffled_tracks = list(cleaned_tracks)
    random.shuffle(shuffled_tracks)

    # Limit how many we will use to build questions
    chosen_tracks = shuffled_tracks[:num_questions]

    # Pool of all track titles for distractor options
    all_titles = []
    for t in cleaned_tracks:
        name = t.get("name")
        if isinstance(name, str) and name.strip():
            all_titles.append(name)

    questions = []

    for track in chosen_tracks:
        if not isinstance(track, dict):
            continue

        name = track.get("name")
        if not isinstance(name, str) or not name.strip():
            continue  # skip tracks with no usable title

        artist_names = _get_artist_names(track)
        image_url = _get_album_image_url(track)

        # Try Spotify preview first
        preview_url = track.get("preview_url")

        # If Spotify has no preview, try iTunes fallback (smart)
        if not preview_url:
            primary_artist = (
                artist_names.split(",")[0].strip()
                if artist_names else None
            )
            preview_url = find_itunes_preview(name, primary_artist)

        # External Spotify URL (for "open in Spotify" links)
        external_url = (track.get("external_urls") or {}).get("spotify")

        # Build options: correct title + some random other titles
        other_titles = [t for t in all_titles if t != name]
        random.shuffle(other_titles)
        distractors = other_titles[: max(0, options_per_q - 1)]

        options = [name] + distractors
        random.shuffle(options)

        questions.append(
            {
                "audio_url": preview_url,       # might be None if neither Spotify nor iTunes has a good preview
                "image": image_url,
                "artist": artist_names,
                "correct": name,
                "options": options,
                "external_url": external_url,
            }
        )

    return {"questions": questions}
