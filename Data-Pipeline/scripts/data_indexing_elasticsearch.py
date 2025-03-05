"""
data_index_elasticsearch_tests.py

Creates an Elasticsearch index with a custom schema/analysis,
then indexes tweet documents into that index.

Usage:
    1) python data_index_elasticsearch_tests.py
       (For a standalone test, it will create the index and optionally index some example docs.)
    2) In your DAG or another script, call:
       from index_elasticsearch import create_index, index_tweets
       create_index("tweets_ukraine", stopwords_list)
       index_tweets("tweets_ukraine", tweets_dict)

Requires:
    - elasticsearch7 library (pip install elasticsearch7)
    - logging_config.get_logger for logging
    - nltk stopwords if you use them in the "english_stop" filter
"""
import hashlib
from elasticsearch7 import Elasticsearch
from logging_config import get_logger
from data_preprocessing import parse_folder
from data_schema import get_es_mappings

import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
nltk_stopwords = stopwords.words('english')

logger = get_logger("data_indexing_elasticsearch.log", logger_name=__name__)


def get_es_client(host="http://localhost:9200", timeout=30):
    """
    Returns an Elasticsearch client pointing to the specified host with the given timeout.
    """
    es = Elasticsearch([host], timeout=timeout)
    if es.ping():
        logger.info(f"Successfully connected to Elasticsearch at {host}")
    else:
        logger.warning(f"Failed to connect to Elasticsearch at {host}")
    return es


def create_index(es_client, index_name, stopwords):
    """
    Creates an index in Elasticsearch with custom analyzers + mappings.
    If the index already exists, logs the event, returns False, and does nothing.
    Otherwise, creates it and returns True.
    """
    if es_client.indices.exists(index=index_name):
        logger.info(f"Index '{index_name}' already exists. Skipping creation.")
        return False

    configurations = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "max_result_window": 100000,
            "analysis": {
                "filter": {
                    "english_stop": {
                        "type": "stop",
                        "stopwords": stopwords
                    },
                },
                "analyzer": {
                    "stopped": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "porter_stem"
                        ]
                    }
                }
            }
        },
        "mappings": get_es_mappings()
    }

    es_client.indices.create(index=index_name, body=configurations)
    logger.info(f"Index '{index_name}' has been created with custom settings.")
    return True


def generate_id_from_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def index_tweets(es_client, index_name, tweets_dict):
    """
    Indexes the tweet objects into Elasticsearch under the given index.
    tweets_dict is expected to be {tweet_id: tweet_data}.
    """
    logger.info(f"Indexing {len(tweets_dict)} tweets into '{index_name}'...")
    count = 0
    for tweet_id, tweet_data in tweets_dict.items():
        try:
            tweet_text = tweet_data.get("text", "")
            # Use generate_id_from_text to produce a consistent ID for duplicate texts
            doc_id = generate_id_from_text(tweet_text)
            es_client.index(index=index_name, id=doc_id, body=tweet_data)

            count += 1
        except Exception as e:
            logger.error(f"Failed to index tweet_id {tweet_id}: {e}")

    logger.info(f"Finished indexing. Total successful: {count}")


def index_elasticsearch(es_client, tweets, index_name):
    if create_index(es_client, index_name, nltk_stopwords):

        index_tweets(es_client, index_name, tweets)
        logger.info(f"Index '{index_name}'. Indexing Completed.")

    else:
        logger.info(f"Index '{index_name}' already exists. Skipping indexing.")


def get_index_name(version):
    version_map = {
        1: "tweets_ukraine_version_1",
        2: "tweets_ukraine_version_2",
        3: "tweets_ukraine_version_3",
    }
    return version_map.get(version, False)


def main():
    tweets = parse_folder("../data/version_1")

    index_elasticsearch(get_es_client(), tweets, get_index_name(1))


if __name__ == "__main__":
    main()
