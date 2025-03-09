import os
import pytest
import logging
from unittest.mock import patch, mock_open
import json 
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from data_preprocessing import (
    removeHashTags, remove_links, remove_special_characters, 
    createTweetObject, parseFile, parse_folder
)
from logging_config import get_logger

logger = get_logger("test_logs/test_data_preprocessing.log", logger_name=__name__)

@pytest.fixture
def sample_tweet_row():
    return [
        "", "123", "test_user", "", "USA", "100", "200", "300",
        "2021-01-01", "tweet_999", "2023-01-01", "5",
        "This is a #test tweet with a #hashtag and link https://example.com",
        "[{'text': 'test', 'indices': [10, 15]}, {'text': 'hashtag', 'indices': [28, 36]}]",
        "en", "", "", "False"
    ]

@pytest.fixture
def sample_tweets_dict():
    return {}

def test_removeHashTags_simple():
    """Test basic hashtag removal"""
    text = "Hello #world"
    hashtags = "[{'text': 'world', 'indices': [6, 12]}]"
    result, extracted = removeHashTags(text, hashtags)
    assert result == "Hello world"
    assert extracted == ["world"]

def test_removeHashTags_multiple():
    """Test multiple hashtag removal"""
    text = "This #is a #test"
    hashtags = "[{'text': 'is', 'indices': [5, 8]}, {'text': 'test', 'indices': [11, 16]}]"
    result, extracted = removeHashTags(text, hashtags)
    assert result == "This is a test"
    assert sorted(extracted) == ["is", "test"]

def test_removeHashTags_invalid_json():
    """Test handling of invalid JSON"""
    text = "Hello #world"
    hashtags = "invalid json"
    result, extracted = removeHashTags(text, hashtags)
    assert result == text
    assert extracted == []

def test_remove_links_multiple():
    """Test removing multiple links"""
    text = "Check http://example.com and https://test.com/path"
    result = remove_links(text)
    assert result == "Check  and "

def test_remove_links_no_links():
    """Test text without links"""
    text = "Hello world!"
    result = remove_links(text)
    assert result == text

def test_remove_special_characters_comprehensive():
    """Test removing various special characters"""
    text = "Hello! @world #nice, (test) [123] {wow}"
    result = remove_special_characters(text)
    assert result == "Hello world nice test 123 wow"

def test_createTweetObject_complete(sample_tweet_row):
    """Test creating a complete tweet object"""
    tweet_id, tweet = createTweetObject(sample_tweet_row)
    
    assert tweet_id == "tweet_999"
    assert tweet["userid"] == "123"
    assert tweet["username"] == "test_user"
    assert "test" in tweet["hashtags"]
    assert "hashtag" in tweet["hashtags"]
    assert "https://example.com" not in tweet["text"]

def test_createTweetObject_minimal():
    """Test with minimal required fields"""
    minimal_row = [""] * 18
    minimal_row[1] = "user_1"  # userid
    minimal_row[2] = "name_1"  # username
    minimal_row[12] = "plain text"  # text
    minimal_row[13] = "[]"  # hashtags
    minimal_row[14] = "en"  # language
    
    tweet_id, tweet = createTweetObject(minimal_row)
    assert tweet["text"] == "plain text"
    assert tweet["hashtags"] == []

@patch('builtins.open', new_callable=mock_open, read_data='userid,username\n123,test_user\n')
def test_parseFile_basic(mock_file, sample_tweets_dict):
    """Test basic file parsing"""
    parseFile("dummy.csv", sample_tweets_dict)
    assert len(sample_tweets_dict) == 0  # Should be 0 as row doesn't match schema

@patch('os.path.isdir')
@patch('os.listdir')
def test_parse_folder_empty(mock_listdir, mock_isdir):
    """Test parsing an empty folder"""
    mock_isdir.return_value = True
    mock_listdir.return_value = []
    
    result = parse_folder("/dummy/path")
    assert len(result) == 0

@patch('os.path.isdir')
def test_parse_folder_nonexistent(mock_isdir):
    """Test handling nonexistent folder"""
    mock_isdir.return_value = False
    
    result = parse_folder("/dummy/path")
    assert len(result) == 0

def test_parse_folder_integration(tmp_path):
    """Integration test with actual file"""
    # Create a test CSV file
    test_csv = tmp_path / "test.csv"
    csv_content = (
        "col1,userid,username,col4,location,following,followers,totaltweets,"
        "usercreatedts,tweetid,tweetcreatedts,retweetcount,text,hashtags,language,col16,col17,is_retweet\n"
        f",123,test_user,,USA,100,200,300,2021-01-01,999,2023-01-01,5,"
        f"Test tweet #hello,\"[{{'text': 'hello', 'indices': [11, 17]}}]\",en,,,False"
    )
    test_csv.write_text(csv_content)
    
    result = parse_folder(str(tmp_path))
    assert len(result) == 1
    assert "999" in result

@pytest.mark.parametrize("text,expected", [
    ("Normal text", "Normal text"),
    ("Text with @mention", "Text with mention"),
    ("Text with #hashtag", "Text with hashtag"),
    ("Text with http://link.com", "Text with "),
    ("Text with special chars !@#", "Text with special chars ")
])
def test_text_processing_variations(text, expected):
    """Test various text processing scenarios"""
    result = remove_special_characters(remove_links(text))
    assert result.strip() == expected.strip()

