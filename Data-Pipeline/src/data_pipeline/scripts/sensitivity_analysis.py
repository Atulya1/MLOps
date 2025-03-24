import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from .es_query import search_custom
from .data_indexing_elasticsearch import get_index_name
from .logging_config import get_logger

# Set up a global logger and VADER sentiment analyzer
logger = get_logger("sensitivity_analysis.log", logger_name=__name__)
sia = SentimentIntensityAnalyzer()

# Define threshold grids for sensitivity analysis
pos_thresholds = [0.05, 0.1, 0.2]
neg_thresholds = [-0.05, -0.1, -0.2]

def classify_with_threshold(text, pos_thresh, neg_thresh):
    """
    Classify the sentiment of 'text' using VADER with custom thresholds.
    Returns a tuple of (sentiment_label, compound_score).
    """
    score = sia.polarity_scores(text)["compound"]
    if score >= pos_thresh:
        return "positive", score
    elif score <= neg_thresh:
        return "negative", score
    else:
        return "neutral", score

def run_analysis(index_name, question, size):

    # Retrieve tweets from Elasticsearch
    response = search_custom(index_name, question, size)

    # Loop through each combination of thresholds and classify sentiments
    for p_thresh in pos_thresholds:
        for n_thresh in neg_thresholds:
            counts = {"positive": 0, "neutral": 0, "negative": 0}
            for hit in response["hits"]["hits"]:
                source = hit.get("_source", {})
                tweet_text = source.get("text", "")
                sentiment, score = classify_with_threshold(tweet_text, p_thresh, n_thresh)
                counts[sentiment] += 1

            logger.info(f"\nThresholds: pos_thresh = {p_thresh}, neg_thresh = {n_thresh}")
            logger.info(f"Sentiment counts: {counts}")

def create_sentiment_sets(response, pos_thresh, neg_thresh):
    positive_tweets = []
    neutral_tweets = []
    negative_tweets = []

    for hit in response["hits"]["hits"]:
        source = hit.get("_source", {})
        tweet_text = source.get("text", "")

        # Classify using your existing function
        sentiment_label, score = classify_with_threshold(tweet_text, pos_thresh, neg_thresh)

        if sentiment_label == "positive":
            positive_tweets.append(tweet_text)
        elif sentiment_label == "negative":
            negative_tweets.append(tweet_text)
        else:
            neutral_tweets.append(tweet_text)

    return positive_tweets, neutral_tweets, negative_tweets


def main():
    # Define the question to retrieve tweets and perform sentiment analysis
    question = "Who is winning the Russia-Ukraine war?"
    response = search_custom(get_index_name(3), "Who is winning the Russia-Ukraine war?", size=100)

    run_analysis(question)

    pos_thresh = 0.05
    neg_thresh = -0.05

    pos_tweets, neu_tweets, neg_tweets = create_sentiment_sets(response, pos_thresh, neg_thresh)

    print(f"Number of positive tweets: {len(pos_tweets)}")
    print(f"Number of neutral tweets: {len(neu_tweets)}")
    print(f"Number of negative tweets: {len(neg_tweets)}")

if __name__ == "__main__":
    main()
