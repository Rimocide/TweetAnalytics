import pandas as pd
import json
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords
import datetime
import os # Import os for path joining

# Download necessary NLTK data (if you haven't already)
# You only need to run this once
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')
except LookupError:
    nltk.download('stopwords')


# --- Configuration ---
# Replace with the path to your downloaded Twitter dataset file
DATASET_PATH = "twitter_dataset.csv" # e.g., "tweets.csv"

# Define the column names in your dataset for relevant data
# *** IMPORTANT: Update these based on your actual dataset columns ***
TEXT_COLUMN = "Text"       # Column containing the tweet content
TIMESTAMP_COLUMN = "Timestamp"   # Column containing the timestamp
LIKES_COLUMN = "Likes"           # Column for likes count
RETWEETS_COLUMN = "Retweets"     # Column for retweets count
# Add other relevant columns like 'replies', 'quotes', etc. if available

# Output directory for processed data
OUTPUT_DIR = "processed_data"
ACTIVITY_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "daily_activity.json")
ENGAGEMENT_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "daily_engagement.json")
TERMS_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "most_common_terms.json")


# --- Data Loading ---
def load_data(file_path):
    """Loads data from a CSV or JSON file."""
    print(f"Loading data from {file_path}...")
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith('.json') or file_path.lower().endswith('.jsonl'):
            # Assuming JSON Lines format if .jsonl, otherwise standard JSON
            try:
                df = pd.read_json(file_path, lines=file_path.lower().endswith('.jsonl'))
            except ValueError:
                 # Try reading as a single JSON object if not JSON Lines
                 with open(file_path, 'r', encoding='utf-8') as f:
                     data = json.load(f)
                 df = pd.DataFrame(data)
        else:
            print("Unsupported file format. Please use CSV or JSON/JSONL.")
            return None
        print("Data loaded successfully.")
        print(f"Dataset shape: {df.shape}")
        return df
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# --- Data Processing and Analysis ---
def analyze_tweets(df):
    """Performs activity and term frequency analysis on the tweets."""
    if df is None or df.empty:
        print("No data to analyze.")
        return None, None, None

    print("Starting data analysis...")

    # --- Data Cleaning and Preparation ---
    # Ensure timestamp column is in datetime format
    # Attempt to infer format, or specify if known
    try:
        df[TIMESTAMP_COLUMN] = pd.to_datetime(df[TIMESTAMP_COLUMN], errors='coerce')
        # Drop rows with invalid timestamps
        df.dropna(subset=[TIMESTAMP_COLUMN], inplace=True)
    except KeyError:
        print(f"Timestamp column '{TIMESTAMP_COLUMN}' not found.")
        return None, None, None
    except Exception as e:
        print(f"Error converting timestamp column: {e}")
        return None, None, None

    # Ensure text column is string type and handle potential missing values
    try:
        df[TEXT_COLUMN] = df[TEXT_COLUMN].astype(str).fillna("")
    except KeyError:
         print(f"Text column '{TEXT_COLUMN}' not found.")
         return None, None, None


    # --- Activity Analysis ---
    print("Analyzing activity over time...")
    # Group by day and count tweets
    df['date'] = df[TIMESTAMP_COLUMN].dt.date
    daily_activity = df['date'].value_counts().sort_index()

    # --- Engagement Analysis (Example: Daily Average Likes and Retweets) ---
    print("Analyzing engagement metrics...")
    if LIKES_COLUMN in df.columns and RETWEETS_COLUMN in df.columns:
        # Ensure engagement columns are numeric
        df[LIKES_COLUMN] = pd.to_numeric(df[LIKES_COLUMN], errors='coerce').fillna(0)
        df[RETWEETS_COLUMN] = pd.to_numeric(df[RETWEETS_COLUMN], errors='coerce').fillna(0)

        daily_engagement = df.groupby('date')[[LIKES_COLUMN, RETWEETS_COLUMN]].mean()
        daily_engagement = daily_engagement.sort_index()
    else:
        daily_engagement = None
        print("Engagement columns not found. Skipping engagement analysis.")


    # --- Term Frequency Analysis ---
    print("Analyzing frequently mentioned terms...")
    all_text = ' '.join(df[TEXT_COLUMN].tolist())

    # Simple text cleaning: remove URLs, mentions, hashtags, punctuation, and numbers
    all_text = re.sub(r'http\S+|www\S+|https\S+', '', all_text, flags=re.MULTILINE)
    all_text = re.sub(r'@\w+', '', all_text)
    all_text = re.sub(r'#\w+', '', all_text) # Decide if you want to keep hashtags - removing for simple term freq
    all_text = re.sub(r'\d+', '', all_text) # Remove numbers
    all_text = re.sub(r'[^\w\s]', '', all_text) # Remove punctuation

    # Tokenization and lowercasing
    words = all_text.lower().split()

    # Remove stop words
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1] # Remove single characters

    # Count term frequencies
    term_counts = Counter(filtered_words)
    most_common_terms = term_counts.most_common(50) # Get top 50 most common terms

    print("Analysis complete.")
    return daily_activity, daily_engagement, most_common_terms

# --- Data Saving ---
def save_processed_data(activity, engagement, common_terms, output_dir=OUTPUT_DIR):
    """Saves the processed data to JSON files."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if activity is not None:
        # Convert Series to dictionary with date strings as keys
        activity_data = {str(date): int(count) for date, count in activity.items()}
        with open(os.path.join(output_dir, "daily_activity.json"), 'w', encoding='utf-8') as f:
            json.dump(activity_data, f, indent=4)
        print(f"Daily activity data saved to {os.path.join(output_dir, 'daily_activity.json')}")

    if engagement is not None:
        # Convert DataFrame to dictionary (e.g., oriented by index/date)
        engagement_data = engagement.to_dict(orient='index')
        # Convert date keys to strings
        engagement_data_str_keys = {str(date): values for date, values in engagement_data.items()}
        with open(os.path.join(output_dir, "daily_engagement.json"), 'w', encoding='utf-8') as f:
            json.dump(engagement_data_str_keys, f, indent=4)
        print(f"Daily engagement data saved to {os.path.join(output_dir, 'daily_engagement.json')}")

    if common_terms is not None:
        # common_terms is already a list of tuples, which is JSON serializable
        with open(os.path.join(output_dir, "most_common_terms.json"), 'w', encoding='utf-8') as f:
            json.dump(common_terms, f, indent=4)
        print(f"Most common terms data saved to {os.path.join(output_dir, 'most_common_terms.json')}")


# --- Main Execution ---
if __name__ == "__main__":
    # Load the dataset
    tweets_df = load_data(DATASET_PATH)

    if tweets_df is not None:
        # Perform analysis
        activity, engagement, common_terms = analyze_tweets(tweets_df)

        # Save the processed data
        save_processed_data(activity, engagement, common_terms)

        print("\nData processing and saving complete.")
        print(f"Processed data saved in the '{OUTPUT_DIR}' directory.")

