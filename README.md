TrackGuessr
TrackGuessr is a full-stack web application that gamifies your Spotify listening history. By integrating with the Spotify Web API, it generates interactive quizzes based on either your personal "Top Tracks" or real-time "Global Hits."

Features 

Spotify OAuth 2.0 Integration: Secure login flow allowing users to authenticate directly with Spotify.

Personalized Quizzes: Generates questions based on the user's most-played songs (Top 50 tracks).

Global Hits Mode: Dynamically searches and fetches tracks from curated playlists like "Top 50 Global" and "Today's Top Hits" to test your knowledge of mainstream music.

Comparison Logic: Uses a custom algorithm to generate multiple-choice options (4 per question) and track difficulty levels.

Cross-Origin Ready: Configured for deployment with Render and local development environments. 

Tech Stack

Backend: Python, Flask

Frontend: JavaScript (Vanilla), HTML5, CSS3

API: Spotify Web API

Authentication: OAuth 2.0

Deployment: Render (Frontend), Flask (Backend) 

Installation & Setup
1. Clone the Repository
   git clone https://github.com/Srivibhu/TrackGuessr.git
   cd TrackGuessr
2. Set Up Environment Variables
   Create a config.py file (or set environment variables) with the following credentials obtained from the Spotify Developer Dashboard:
   PythonFLASK_SECRET_KEY = "your_flask_secret"
   SPOTIFY_CLIENT_ID = "your_spotify_client_id"
   SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
   SPOTIFY_REDIRECT_URI = "your_callback_url" # e.g., http://localhost:5002/callback
   FRONTEND_URL = "your_frontend_domain"      # e.g., https://trackguessr.vercel.app
3. Install Dependencies
   pip install flask flask-cors requests
4. Run the ApplicationBashpython app.py
The backend will start on http://localhost:5000 (default) or 5002 as per your configuration.

Developed by Srivibhu Ponakala Computer Science Major @ UMass Amherst
