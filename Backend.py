from flask import Flask, jsonify
from flask_cors import CORS # Import CORS for handling cross-origin requests
import json
import os

# --- Configuration ---
PROCESSED_DATA_DIR = "processed_data"
ACTIVITY_FILE = os.path.join(PROCESSED_DATA_DIR, "daily_activity.json")
ENGAGEMENT_FILE = os.path.join(PROCESSED_DATA_DIR, "daily_engagement.json")
TERMS_FILE = os.path.join(PROCESSED_DATA_DIR, "most_common_terms.json")

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS to allow the frontend (running on a different origin) to access the API

# --- Data Loading Function ---
def load_processed_data(file_path):
    """Loads processed data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: Processed data file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None
    except Exception as e:
        print(f"Error loading processed data from {file_path}: {e}")
        return None

# --- API Endpoints ---

@app.route('/api/activity', methods=['GET'])
def get_daily_activity():
    """Returns daily tweet activity data."""
    activity_data = load_processed_data(ACTIVITY_FILE)
    if activity_data is not None:
        return jsonify(activity_data)
    else:
        return jsonify({"error": "Could not load daily activity data"}), 500

@app.route('/api/engagement', methods=['GET'])
def get_daily_engagement():
    """Returns daily engagement data."""
    engagement_data = load_processed_data(ENGAGEMENT_FILE)
    if engagement_data is not None:
        return jsonify(engagement_data)
    else:
        return jsonify({"error": "Could not load daily engagement data"}), 500

@app.route('/api/terms', methods=['GET'])
def get_most_common_terms():
    """Returns most common terms data."""
    terms_data = load_processed_data(TERMS_FILE)
    if terms_data is not None:
        return jsonify(terms_data)
    else:
        return jsonify({"error": "Could not load most common terms data"}), 500

@app.route('/')
def index():
    """Basic route to confirm the backend is running."""
    return "Analytics Backend is running!"

# --- Run the Flask App ---
if __name__ == '__main__':
    # Ensure the processed data directory exists (though the processing script should create it)
    if not os.path.exists(PROCESSED_DATA_DIR):
        print(f"Warning: Processed data directory '{PROCESSED_DATA_DIR}' not found.")
        print("Please run the data processing script first.")
        # You might want to exit or handle this more gracefully in a production app
        # For this example, we'll let it try to run, but API calls will fail if files are missing.


    # In a production environment, you would use a production-ready WSGI server like Gunicorn or uWSGI
    # For local testing, run with debug=True
    app.run(debug=True)
