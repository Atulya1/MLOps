"""
es_query.py

Queries Elasticsearch with a custom function_score query that combines text relevance
with weighted numeric factors (followers, retweets, etc.). The search query is taken as input.
Logs all events to console and a log file.

Usage:
python es_query_custom.py "your search query"
If no query is provided, a default query ("russia war end") is used.
"""

import sys
from elasticsearch7 import Elasticsearch
from .logging_config import get_logger

logger = get_logger("es_query_custom.log", logger_name=__name__)

def get_es_client(host="http://localhost:9200", timeout=30):
    """
    Returns an Elasticsearch client.
    """
    es = Elasticsearch([host], timeout=timeout)
    if es.ping():
        logger.info(f"Connected to Elasticsearch at {host}")
    else:
        logger.warning(f"Failed to connect to Elasticsearch at {host}")
    return es

def search_custom(index_name, query_string, size=10):
    """
    Executes a custom search query on the given index.
    Combines a multi_match text query with a script_score that normalizes numeric fields.

    Args:
        es_client: Elasticsearch client instance.
        index_name: Name of the index to search.
        query_string: The text query.
        size: Number of results to return.

    Returns:
        List of hits (documents) from Elasticsearch.
    """
    logger.info(f"Executing search query: '{query_string}' on index '{index_name}' (size={size})")

    query_body = {
        "size": size,
        "query": {
            "function_score": {
                "query": {
                    "multi_match": {
                        "query": query_string,
                        "fields": ["text", "hashtags"]
                    }
                },
                "score_mode": "sum",
                "boost_mode": "replace",
                "functions": [
                    {
                        "script_score": {
                            "script": {
                                "lang": "painless",
                                "source": """
                                    double textScore = _score;
                                    
                                    // If a field doesn't exist or is empty, default to 0.0
                                    double followers  = (doc['followers'].size() > 0) ? doc['followers'].value : 0.0;
                                    double likes      = 0.0;
                                    double retweets   = (doc['retweetcount'].size() > 0) ? doc['retweetcount'].value : 0.0;
                                    double replies    = 0.0;
                                    double totaltweets= (doc['totaltweets'].size() > 0) ? doc['totaltweets'].value : 0.0;
                                    double following  = (doc['following'].size() > 0) ? doc['following'].value : 0.0;
                                    
                                    // Normalize using log1p (i.e., log(1+x)) and scale down by divisor
                                    double followersNorm    = Math.log1p(followers)   / 10.0;
                                    double likesNorm        = Math.log1p(likes)       / 10.0;
                                    double retweetsNorm     = Math.log1p(retweets)    / 10.0;
                                    double repliesNorm      = Math.log1p(replies)     / 10.0;
                                    double followingNorm    = Math.log1p(following)   / 10.0;
                                    double totaltweetsNorm  = Math.log1p(totaltweets) / 10.0;
                                    
                                    // Weighted combination:
                                    // 60% text score, and 10% each for followers, retweets, following, and totaltweets.
                                    double finalScore = 0.6 * textScore
                                                      + 0.15 * followersNorm
                                                      + 0.15 * retweetsNorm
                                                      + 0.05 * followingNorm
                                                      + 0.05 * totaltweetsNorm;
                                    return finalScore;
                                """
                            }
                        }
                    }
                ]
            }
        }
    }

    try:
        response = get_es_client().search(index=index_name, body=query_body)
        hits = response.get("hits", {}).get("hits", [])
        logger.info(f"Search completed: {len(hits)} hits returned (took {response.get('took')} ms).")
        return hits
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return []

def main():
    """
    Main function for standalone testing.
    Accepts a query string from the command-line or uses a default.
    """
    # if len(sys.argv) > 1:
    #     query_string = " ".join(sys.argv[1:])
    # else:
    #     query_string = "russia war end"

    index_name = "tweets_ukraine_version_3"  # Change if needed
    es_client = get_es_client()

    hits = search_custom(index_name, "russia war end", size=10)

    logger.info("Search results:")
    for hit in hits:
        tweet_id = hit.get("_id", "unknown")
        score = hit.get("_score", 0)
        text = hit.get("_source", {}).get("text", "")
        logger.info(f"Tweet ID: {tweet_id}, Score: {score}, Text: {text}")
        print(f"Tweet ID: {tweet_id}\nScore: {score}\nText: {text}\n{'-'*40}")

if __name__ == "__main__":
    main()
