import os
import pytest
from unittest.mock import patch, MagicMock
import logging
import hashlib
from unittest import mock
from elasticsearch7 import Elasticsearch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs')))

from data_indexing_elasticsearch import (get_es_client,create_index,index_tweets,generate_id_from_text,index_elasticsearch)
from logging_config import get_logger

logger = get_logger("test_logs/data_indexing_elasticsearch_test.log", logger_name=__name__)

@pytest.fixture(scope="module")
def mock_es_client():
    """
    This fixture mocks the Elasticsearch client for testing purposes.
    """
    mock_client = MagicMock()
    yield mock_client

@pytest.fixture
def tweets_dict():
    """
    This fixture provides a mock dictionary of tweet data for indexing.
    """
    return {
        "12345": {
            "userid": "1",
            "username": "user1",
            "text": "This is a tweet",
            "hashtags": ["hashtag1", "hashtag2"],
            "language": "en",
            "is_retweet": False,
        },
        "67890": {
            "userid": "2",
            "username": "user2",
            "text": "Another tweet with some #hashtag",
            "hashtags": ["hashtag3"],
            "language": "en",
            "is_retweet": False,
        },
    }

@patch('data_indexing_elasticsearch.Elasticsearch')
def test_get_es_client(mock_es_class):
    """
    Test to verify if the Elasticsearch client is initialized and can ping the host.
    """
    mock_es_client = MagicMock()
    mock_es_client.ping.return_value = True
    mock_es_class.return_value = mock_es_client

    es_client = get_es_client(host="http://localhost:9200")
    assert es_client.ping() is True
    mock_es_class.assert_called_once_with(["http://localhost:9200"], timeout=30)
    logger.info("test_get_es_client passed.")


# Mock tweets dictionary fixture
@pytest.fixture
def tweets_dict():
    return {
        "1": {"text": "This is a tweet", "user": "user1"},
        "2": {"text": "Another tweet", "user": "user2"}
    }

@patch("data_indexing_elasticsearch.Elasticsearch") 
def test_create_index(mock_es):
    """Test that the create_index function creates an index when it doesn't exist"""
    es_client = MagicMock()
    mock_es.return_value = es_client

    es_client.indices = MagicMock()
    es_client.indices.exists.return_value = False 

    index_name = "test_index"
    stopwords = ["the", "is", "in"]

    result = create_index(es_client, index_name, stopwords)

    es_client.indices.create.assert_called_once()
    assert result is True  

@patch("data_indexing_elasticsearch.Elasticsearch")
@patch("data_indexing_elasticsearch.create_index")
@patch("data_indexing_elasticsearch.index_tweets")
def test_index_elasticsearch(mock_index_tweets, mock_create_index, mock_es, tweets_dict):
    """Test indexing process"""
    es_client = MagicMock()
    mock_es.return_value = es_client

    mock_create_index.return_value = True
    mock_index_tweets.return_value = None 

    index_name = "tweets_test"

    index_elasticsearch(tweets_dict, index_name)

    mock_create_index.assert_called_once_with(es_client, index_name, mock.ANY)
    mock_index_tweets.assert_called_once_with(es_client, index_name, tweets_dict)

@patch('data_indexing_elasticsearch.Elasticsearch')
def test_index_tweets(mock_es_class, mock_es_client, tweets_dict):
    """
    Test the indexing of tweets into Elasticsearch.
    """
    mock_es_client.indices.exists.return_value = False
    mock_es_class.return_value = mock_es_client

    mock_es_client.index.return_value = {"result": "created"}

    index_tweets(mock_es_client, "tweets_test_index", tweets_dict)

    assert mock_es_client.index.call_count == len(tweets_dict)
    logger.info(f"test_index_tweets passed for {len(tweets_dict)} tweets.")

def test_generate_id_from_text():
    """
    Test to verify the generation of IDs from tweet text.
    """
    tweet_text = "This is a tweet"
    generated_id = generate_id_from_text(tweet_text)
    expected_id = hashlib.md5(tweet_text.encode('utf-8')).hexdigest()
    assert generated_id == expected_id
    logger.info("test_generate_id_from_text passed.")








