import os
import pytest
import logging
from unittest.mock import patch
import json 
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from data_preprocessing import removeHashTags, remove_links, remove_special_characters, createTweetObject
from logging_config import get_logger

logger = get_logger("test_logs/test_data_preprocessing.log", logger_name=__name__)

def test_removeHashTags():
    """Test removeHashTags function"""
    text = "This is a tweet with a #hashtag"
    hashtags = "[{'text': 'hashtag', 'indices': [22, 30]}]"

    processed_text, extracted_hashtags = removeHashTags(text, hashtags)

    logger.info(f"Processed Text: {processed_text}")
    logger.info(f"Extracted Hashtags: {extracted_hashtags}")


def test_remove_links():
    """Test remove_links function"""
    text = "Check this link: http://example.com and this one https://example.org"

    processed_text = remove_links(text)

    logger.info(f"Processed Text: {processed_text}")

    assert processed_text == "Check this link:  and this one ", "Links were not removed correctly"

def test_remove_special_characters():
    """Test remove_special_characters function"""
    text = "Hello! How are you doing? #Great_Stuff"
    
    processed_text = remove_special_characters(text)

    logger.info(f"Processed Text: {processed_text}")

    assert processed_text == "Hello How are you doing GreatStuff", "Special characters were not removed correctly"

def test_createTweetObject():
    """Test createTweetObject function"""
    row = ["", "123", "test_user", "", "USA", "100", "200", "300", "2021-01-01", "999", "2023-01-01", "5", 
           "This is a tweet with a #hashtag and a link http://example.com", 
           "[{'text': 'hashtag', 'indices': [22, 30]}]",
           "en", "", "", "False"]

    tweet_id, tweet = createTweetObject(row)

    logger.info(f"Tweet ID: {tweet_id}")
    logger.info(f"Tweet Object: {json.dumps(tweet, indent=2)}")

