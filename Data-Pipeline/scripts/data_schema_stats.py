"""
data_schema_stats.py

Here you can define your data schema validation and
generate basic statistics about the data.
"""

import logging

def validate_schema(tweet_dict):
    """
    Example of a simple schema check for required fields.
    """
    required_fields = ["userid", "username", "text", "language"]
    for field in required_fields:
        if field not in tweet_dict:
            logging.warning(f"Schema warning: {field} is missing from tweet dict.")
            return False
    return True

def generate_stats(all_tweets):
    """
    Returns some simple statistics (e.g., number of tweets,
    average followers, etc.)
    """
    total = len(all_tweets)
    if total == 0:
        return {"count": 0, "avg_followers": 0}
    sum_followers = 0
    for twid, tweet in all_tweets.items():
        try:
            sum_followers += int(tweet.get("followers", 0))
        except ValueError:
            pass
    avg_followers = sum_followers / total
    return {
        "count": total,
        "avg_followers": avg_followers
    }
