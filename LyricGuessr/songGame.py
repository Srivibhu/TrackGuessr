# songGame.py

from flask import Flask, render_template, jsonify
import json
import random
import os
import copy

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize the Flask app with explicit paths
app = Flask(
    __name__,
    template_folder=os.path.join(script_dir, 'templates'),
    static_folder=os.path.join(script_dir, 'static')
)

# Disable caching so audio files don't load from a stale/broken cache
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


# --- Load Song Database ---
def load_songs():
    try:
        songs_path = os.path.join(script_dir, 'songs.json')
        with open(songs_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: songs.json file not found at {songs_path}")
        return {}
    except json.JSONDecodeError:
        print("Error: Could not decode songs.json. Check for syntax errors.")
        return {}


# --- Main Page Route ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')


# --- API Route ---
@app.route('/api/get-all-songs')
def get_all_songs():
    """
    API endpoint to send the entire song database organized by genre.
    Shuffles the options for each song so the correct answer isn't always first.
    """
    # Reload songs.json each request so changes take effect without restarting the server
    current_db = load_songs()
    if not current_db:
        return jsonify({"error": "No songs available"}), 500

    # Create a deep copy of the database to avoid modifying the original
    shuffled_db = copy.deepcopy(current_db)

    # Shuffle options for each song in each genre
    for genre in shuffled_db:
        for song in shuffled_db[genre]:
            random.shuffle(song['options'])

    return jsonify(shuffled_db)


# --- Run the App (FRONTEND) on port 5002 ---
if __name__ == '__main__':
    # Frontend game lives on http://127.0.0.1:5002
    app.run(debug=True, port=5002)
