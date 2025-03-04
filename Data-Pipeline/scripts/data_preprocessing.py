"""
data_preprocessing_tests.py

Preprocessing logic for tweet data, including:
- Removing '#' from hashtags
- Removing links
- Removing special characters
- Parsing rows into tweet objects

Usage:
    1) python data_preprocessing_tests.py  # runs main(), parses default folder
    2) parse_folder(data_folder) from another script or DAG, returns tweets dict

Dependencies:
    - logging_config.get_logger for logging
    - CSVs in the data folder with tweet columns at known indices
"""

import os
import re
import json
import csv

from logging_config import get_logger
from data_schema import validate_tweet_row_schema

logger = get_logger("data_preprocessing.log", logger_name=__name__)

def remove_substring(s, start, end):
    """
    Removes the substring from s[start:end].
    """
    return s[:start] + s[end:]

def removeHashTags(text, hashtags):
    """
    Removes only the '#' character from hashtags, leaving the rest of the word.
    Also collects hashtags in a separate list.

    Example:
      If row[13] is a JSON-like string with 'indices' & 'text',
      we remove '#' from each hashtag location.
    """
    # Attempt to parse hashtag info
    parse_hashtags = hashtags.replace("'", '"')
    try:
        hashtags_json = json.loads(parse_hashtags)
    except json.JSONDecodeError as e:
        logger.warning(f"Hashtag JSON parse error: {e}, skipping hashtags.")
        return text, []

    # Sort in reverse so we remove '#' from end to start (avoid messing up indices)
    hashtags_json = sorted(hashtags_json, key=lambda h: h['indices'][0], reverse=True)
    tweet_hashtags = []
    for hashtag in hashtags_json:
        indices = hashtag.get('indices', [])
        if len(indices) == 2:
            tweet_hashtags.append(hashtag.get('text', ''))
            # Remove only the '#' char (assuming indices[0] is the start of '#')
            text = remove_substring(text, indices[0], indices[0] + 1)
    return text, tweet_hashtags

def remove_links(text):
    """
    Removes http/https links from text.
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.sub(url_pattern, '', text)

def remove_special_characters(text):
    """
    Removes special characters and punctuation, leaving only alphanumerics + whitespace.
    """
    return re.sub(r'[^\w\s]|_', '', text)

def createTweetObject(row):
    """
    Builds a tweet dict from a CSV row. Indices may need adjusting based on your CSV format.

    Example columns:
      row[1] -> userid
      row[2] -> username
      row[12] -> text
      row[13] -> hashtags (JSON-like)
      row[14] -> language
      row[17] -> is_retweet
    """
    # Start with raw text
    raw_text = row[12]
    raw_hashtags = row[13]

    # Remove '#' from text, collect hashtags
    text_no_hash, tweet_hashtags = removeHashTags(raw_text, raw_hashtags)
    # Remove links
    text_no_links = remove_links(text_no_hash)
    # Remove special chars
    final_text = remove_special_characters(text_no_links)

    tweet = {
        "userid": row[1],
        "username": row[2],
        "location": row[4],
        "following": row[5],
        "followers": row[6],
        "totaltweets": row[7],
        "usercreatedts": row[8],
        "tweetcreatedts": row[10],
        "retweetcount": row[11],
        "text": final_text,
        "hashtags": tweet_hashtags,
        "language": row[14],
        "is_retweet": row[17],
    }

    # row[9] is the tweet ID
    tweet_id = row[9]
    return tweet_id, tweet

def parseFile(filename, tweets_dict):
    logger.info(f"Parsing file: {filename}")
    count = 0
    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                if not row:
                    continue
                if row[1] == "userid":  # Skip header
                    continue
                if not validate_tweet_row_schema(row):
                    continue
                if row[14] == "en":
                    tid, tweet_obj = createTweetObject(row)
                    if tid and tweet_obj:
                        tweets_dict[tid] = tweet_obj
                        count += 1
        logger.info(f"Finished parsing {filename}. Valid tweets: {count}")
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
    except Exception as e:
        logger.error(f"Error parsing file {filename}: {e}")


def parse_folder(folder_path):
    """
    Processes all CSV files in folder_path.
    Returns a dict of tweet_id -> tweet_object.
    """
    logger.info(f"Parsing folder: {folder_path}")
    tweets_dict = {}

    if not os.path.isdir(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return tweets_dict

    for filename in os.listdir(folder_path):
        if filename.lower() in ["readme", ".ds_store"]:
            continue
        full_path = os.path.join(folder_path, filename)
        # Process only .csv files or any file that suits your format
        if os.path.isfile(full_path) and filename.endswith(".csv"):
            parseFile(full_path, tweets_dict)

    logger.info(f"Completed parsing folder: {folder_path}. Total tweets: {len(tweets_dict)}")
    return tweets_dict

def main():
    """
    Main method for standalone testing:
    1) Define a default data folder
    2) Parse the folder
    3) Print how many tweets were processed
    """
    default_folder = "../data/version_1"  # Adjust as needed
    results = parse_folder(default_folder)
    logger.info(f"Standalone run: {len(results)} tweets processed.")

    for tw in results:
        print(tw)
        print(results[tw])
        break

if __name__ == "__main__":
    main()
