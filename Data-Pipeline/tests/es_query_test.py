import os
import pytest
from unittest.mock import patch, MagicMock
import logging
import shutil

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs')))

from es_query import get_es_client, search_custom
from logging_config import get_logger

logger = get_logger("es_query_test.log", logger_name=__name__)

@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client"""
    es_client = MagicMock()
    es_client.ping.return_value = True 
    return es_client

@pytest.fixture
def sample_hits():
    """Sample hits returned from Elasticsearch"""
    return {
        "hits": {
            "hits": [
                {"_id": "123", "_score": 1.5, "_source": {"text": "Sample tweet 1"}},
                {"_id": "456", "_score": 2.0, "_source": {"text": "Sample tweet 2"}}
            ],
            "total": {"value": 2},
        },
        "took": 50
    }

@patch("es_query.Elasticsearch")
def test_get_es_client(mock_es):
    """Test Elasticsearch client connection"""
    mock_es.return_value.ping.return_value = True  # Mock successful ping

    es_client = get_es_client()

    assert es_client.ping() is True
    mock_es.assert_called_once_with(["http://localhost:9200"], timeout=30)

@patch("es_query.Elasticsearch")
def test_get_es_client_fail(mock_es):
    """Test Elasticsearch client failure"""
    mock_es.return_value.ping.return_value = False  # Simulate failed ping

    es_client = get_es_client()

    assert es_client.ping() is False
    mock_es.assert_called_once_with(["http://localhost:9200"], timeout=30)

@patch("es_query.get_es_client")
def test_search_custom(mock_get_es, mock_es_client, sample_hits, caplog):
    """Test custom search query execution"""
    mock_es_client.search.return_value = sample_hits
    mock_get_es.return_value = mock_es_client

    index_name = "tweets_ukraine_version_1"
    query_string = "test query"

    with caplog.at_level(logging.INFO):
        results = search_custom(index_name, query_string)

    assert len(results) == 2 
    mock_es_client.search.assert_called_once()
    
    # Verify logs
    assert "Executing search query: 'test query'" in caplog.text
    assert "Search completed: 2 hits returned" in caplog.text

@patch("logging.getLogger")
def test_logging(mock_get_logger):
    """Test that logging works as expected."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    test_message = "This is a test log for search_custom function."
    logger.info(test_message)

def test_directory_creation():
    """Test directory creation and cleanup."""
    log_folder = "test_logs"

    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)

    os.makedirs(log_folder)
    assert os.path.exists(log_folder)

    shutil.rmtree(log_folder)
    assert not os.path.exists(log_folder)
