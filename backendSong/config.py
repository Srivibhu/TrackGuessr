# backendSong/config.py
import os

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5000")  # or whatever local dev URL
