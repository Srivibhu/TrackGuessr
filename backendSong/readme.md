# TrackGuessr

A Spotify-powered music quiz where you guess the track from a short preview.
Play with your **Top Tracks** or **Global Hits**, with scoring, high scores and a local leaderboard.

## Tech Stack

- Frontend: Vanilla HTML/CSS/JS
- Backend: Flask (Python) + Spotify Web API
- Auth: Spotify OAuth (Authorization Code flow)
- Deployment:
  - Frontend -> Vercel
  - Backend -> Render

## Project Structure

```text
TrackGuessr/
?? frontend/          # Static site deployed to Vercel
?  ?? index.html
?  ?? static/
?     ?? style.css
?     ?? game.js
?
?? backend/           # Flask API for Spotify + quiz generation
?  ?? app.py
?  ?? spotify_auth.py
?  ?? spotify_client.py
?  ?? quiz_generator.py
?  ?? config.py          # local only (not committed)
?  ?? example_config.py  # safe template
?  ?? requirements.txt
?? .gitignore
```
