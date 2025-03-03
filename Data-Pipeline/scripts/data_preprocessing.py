"""
data_preprocessing.py

Handles all data preprocessing logic (cleaning, parsing CSVs, etc.).
"""

import re
import json
import csv
import os

# You may need NLTK or other libraries if you do more advanced preprocessing
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

nltk.download('stopwords')
ps = PorterStemmer()
nltk_stopwords = stopwords.words('english')

all_tweets = {}

def remove_substring(s, start, end):
    return s[:start] + s[end:]

def removeHashTags(text, hashtags):
    """
    Removes hashtags from text based on 'indices' in the JSON representation of hashtags.
    Returns cleaned text and a list of extracted hashtags.
    """
    parse_hashtags = hashtags.replace("'", '"')
    hashtags_json = json.loads(parse_hashtags)
    # Sort so we remove from end to start (avoid messing up indices)
    hashtags_json = sorted(hashtags_json, key=lambda h: h['indices'][0], reverse=True)
    tweet_hashtags = []
    for hashtag in hashtags_json:
        indices = hashtag['indices']
        tweet_hashtags.append(hashtag['text'])
        text = remove_substring(text, indices[0], indices[0] + 1)

    return text, tweet_hashtags

def remove_links(text):
    """
    Removes all http/https links from text.
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|' \
                  r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.sub(url_pattern, '', text)

def remove_special_characters(text):
    """
    Remove all special characters, punctuation, and non-alphanumeric characters.
    """
    return re.sub(r'[^\w\s]|_', '', text)

def createTweetObject(row):
    """
    Given a row from CSV, returns (tweet_id, tweet_dict).
    """
    tweet = {}
    text, tweet_hashtags = removeHashTags(row[12], row[13])
    text = remove_links(text)
    text = remove_special_characters(text)

    tweet["userid"] = row[1]
    tweet["username"] = row[2]
    tweet["location"] = row[4]
    tweet["following"] = row[5]
    tweet["followers"] = row[6]
    tweet["totaltweets"] = row[7]
    tweet["usercreatedts"] = row[8]
    tweet["tweetcreatedts"] = row[10]
    tweet["retweetcount"] = row[11]
    tweet["text"] = text
    tweet["hashtags"] = tweet_hashtags
    tweet["language"] = row[14]
    tweet["is_retweet"] = row[17]
    return row[9], tweet

def parseFile(filename):
    """
    Reads a CSV file, processes each row, and populates all_tweets dict.
    """
    with open(filename, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row[1] == "userid":
                # Skip header
                continue
            if row[14] == "en":
                tweetid, tweet = createTweetObject(row)
                all_tweets[tweetid] = tweet

def parse_folder(folder_path="./data"):
    """
    Iterates over all files in 'folder_path' and processes them (except readme/.DS_Store).
    """
    for filename in os.listdir(folder_path):
        if filename not in ['readme', '.DS_Store']:
            file_path = os.path.join(folder_path, filename)
            print(f"Processing: {file_path}")
            parseFile(file_path)
    print("Parsing Completed")

