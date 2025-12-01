# backendSong/app.py

from flask import Flask, jsonify, session, redirect, render_template
from flask_cors import CORS

from config import FLASK_SECRET_KEY, FRONTEND_URL
from spotify_auth import spotify_login, spotify_callback
from spotify_client import (
    spotify_get,
    get_user_top_tracks,
    get_playlist_tracks,
    search_playlists,
)
from quiz_generator import generate_quiz_from_tracks

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
)

# Allow both Vercel domain spellings plus any env override.
ALLOWED_ORIGINS = [
    FRONTEND_URL,                    # e.g. "https://trackguessr.vercel.app"
    "https://trackguessr.vercel.app",
    "https://track-guessr.vercel.app",
    "http://localhost:5002",         # (optional: for local dev)
]

CORS(
    app,
    supports_credentials=True,
    origins=[o for o in ALLOWED_ORIGINS if o],
)

@app.route("/")
def root():
    return render_template("index.html")


@app.route("/login")
def login_route():
    return spotify_login()


@app.route("/callback")
def callback_route():
    return spotify_callback()


@app.route("/logout")
def logout_route():
    session.clear()
    return redirect(FRONTEND_URL)


@app.route("/api/me")
def api_me_route():
    data = spotify_get("me")
    if isinstance(data, tuple):
        body, status = data
        return jsonify(body), status
    return jsonify(data)


@app.route("/auth/status")
def auth_status():
    """
    Used by frontend to show 'Welcome, username' + avatar.
    Never throws, always returns logged_in flag.
    """
    data = spotify_get("me")

    if isinstance(data, tuple):
        body, status = data
        # Treat any failure as 'not logged in' for UI
        return jsonify({"logged_in": False}), 200

    if isinstance(data, dict) and data.get("error"):
        return jsonify({"logged_in": False}), 200

    display_name = data.get("display_name") or data.get("id")
    images = data.get("images") or []
    image_url = images[0].get("url") if images else None

    return jsonify({
        "logged_in": True,
        "display_name": display_name,
        "image_url": image_url,
        "id": data.get("id")
    })


# ---------- QUIZ: YOUR TOP TRACKS ----------

@app.route("/api/quiz/top-tracks")
def quiz_top_tracks():
    """
    Build a quiz from the current user's top tracks.

    For *any* error (auth / no history / weird response),
    we return: {"questions": [], "source": "top-tracks", "error": {...optional...}}
    with HTTP 200 so the frontend never breaks.
    """
    data = get_user_top_tracks(limit=50)

    # Error case: spotify_get returned (body, status)
    if isinstance(data, tuple):
        body, status = data
        print("TOP_TRACKS error:", body)
        return jsonify({
            "questions": [],
            "source": "top-tracks",
            "error": body
        }), 200

    if not isinstance(data, dict):
        print("TOP_TRACKS non-dict response:", data)
        return jsonify({
            "questions": [],
            "source": "top-tracks",
            "error": "unexpected_response"
        }), 200

    items = data.get("items") or []
    print("TOP_TRACKS items:", len(items))

    # Clean tracks: only proper dicts with a name
    tracks = [
        t for t in items
        if isinstance(t, dict) and t.get("name")
    ]

    quiz = generate_quiz_from_tracks(tracks, num_questions=5, options_per_q=4)
    return jsonify(quiz)


# ---------- QUIZ: GLOBAL HITS (playlist-based, safe) ----------

@app.route("/api/quiz/global-hits")
def quiz_global_hits():
    """
    Build a quiz from a global/popular playlist.

    For any Spotify error, we return {"questions": []} with HTTP 200.
    """
    search_terms = ["Top 50 Global", "Today's Top Hits", "Global Top 50"]
    playlist_id = None

    for term in search_terms:
        search_data = search_playlists(term, limit=5)

        if isinstance(search_data, tuple):
            body, status = search_data
            print(f"GLOBAL_HITS search '{term}' error:", body)
            continue

        raw_playlists = (search_data.get("playlists") or {}).get("items") or []
        print(f"GLOBAL_HITS search '{term}' found {len(raw_playlists)} playlists (raw)")

        playlists = [
            p for p in raw_playlists
            if isinstance(p, dict) and p.get("id")
        ]
        print(f"GLOBAL_HITS usable playlists for '{term}': {len(playlists)}")

        if playlists:
            playlist_id = playlists[0]["id"]
            print("GLOBAL_HITS using playlist:", term, "→", playlist_id)
            break

    if not playlist_id:
        print("GLOBAL_HITS: no suitable playlist found from search.")
        return jsonify({
            "questions": [],
            "source": "global-hits",
            "error": "no_playlist_found"
        }), 200

    # Fetch tracks from the chosen playlist
    data = get_playlist_tracks(playlist_id, limit=50)

    if isinstance(data, tuple):
        body, status = data
        print("GLOBAL_HITS playlist error:", body)
        return jsonify({
            "questions": [],
            "source": "global-hits",
            "error": body
        }), 200

    if not isinstance(data, dict):
        print("GLOBAL_HITS non-dict playlist response:", data)
        return jsonify({
            "questions": [],
            "source": "global-hits",
            "error": "unexpected_playlist_response"
        }), 200

    items = (data.get("items") or [])
    print("GLOBAL_HITS items:", len(items))

    tracks = [
        it.get("track")
        for it in items
        if isinstance(it, dict) and it.get("track")
    ]

    quiz = generate_quiz_from_tracks(tracks, num_questions=5, options_per_q=4)
    return jsonify(quiz)


if __name__ == "__main__":
    app.run(debug=True)
