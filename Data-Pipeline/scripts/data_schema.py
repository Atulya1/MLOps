"""
data_schema.py

Contains logic for validating the schema of a tweet CSV row.
Logs any schema violations or anomalies.
"""

import logging
from logging_config import get_logger

logger = get_logger("data_schema.log", logger_name=__name__)

# Example: define the required indices for your CSV row
REQUIRED_INDICES = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17]
MAX_INDEX_NEEDED = max(REQUIRED_INDICES)  # 17

def validate_tweet_row_schema(row):
    """
    Checks if 'row' has all required columns, logs warnings if missing.
    Returns True if schema is valid, else False.
    """
    # Check length
    if len(row) <= MAX_INDEX_NEEDED:
        logger.warning(
            f"Schema issue: row has only {len(row)} fields, expected at least {MAX_INDEX_NEEDED+1}. Row={row}"
        )
        return False

    # (Optional) Check data types or specific column constraints
    # e.g. row[5], row[6], row[7], row[10], row[11] might be integer-like or date-like.
    # If something isn't correct, log and return False

    return True

def get_es_mappings():
    """
    Returns the Elasticsearch mappings configuration for the tweet index.
    This can be used inside create_index to cleanly separate out the schema.
    """
    return {
        "properties": {
            "userid":         {"type": "keyword"},
            "username":       {"type": "text"},
            "location":       {"type": "text"},
            "following":      {"type": "integer"},
            "followers":      {"type": "integer"},
            "totaltweets":    {"type": "integer"},
            "usercreatedts": {
                "type":   "date",
                "format": "yyyy-MM-dd HH:mm:ss.SSSSSS"
            },
            "tweetcreatedts": {
                "type":   "date",
                "format": "yyyy-MM-dd HH:mm:ss"
            },
            "retweetcount":  {"type": "integer"},
            "text": {
                "type":     "text",
                "analyzer": "stopped"  # referencing your custom analyzer
            },
            "hashtags":      {"type": "keyword"},
            "language":      {"type": "keyword"},
            "is_retweet":    {"type": "keyword"}
        }
    }
