# backend/config_example.py

# COPY this file to config.py and fill in real values.
# Do NOT commit config.py to GitHub.

FLASK_SECRET_KEY = "replace-with-a-long-random-string"

SPOTIFY_CLIENT_ID = "your-spotify-client-id"
SPOTIFY_CLIENT_SECRET = "your-spotify-client-secret"

# For local dev
REDIRECT_URI = "http://127.0.0.1:5000/callback"
FRONTEND_URL = "http://127.0.0.1:5500"  # or wherever you open index.html
# For production, use your actual domain, e.g.:
# REDIRECT_URI = "https://yourdomain.com/callback"