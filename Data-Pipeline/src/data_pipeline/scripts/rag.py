import os
import logging
from dotenv import load_dotenv

# Import LangChain components
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI

import ssl
import nltk

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('vader_lexicon')

from nltk.sentiment.vader import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()

# Configure logging
from logging_config import get_logger

logger = get_logger("rag.log", logger_name=__name__)

# --- Configuration ---
OPENAI_API_KEY = ""

EMBEDDINGS_FOLDER = os.path.join("embeddings", "faiss_index")

# Global references for the vectorstore and retrieval chain
retrieval_chain = None
vectorstore = None

# For FAISS (default L2 distance), smaller => more similar
SIMILARITY_THRESHOLD = 3


def load_or_create_vectorstore(data_source: str):
    """
    Load or create the vectorstore from the provided data source.
    In this case, the data source is the output of an Elasticsearch query,
    containing tweets that serve as our knowledge base.
    """
    global retrieval_chain, vectorstore

    logger.info("Using provided tweet data as the knowledge source...")
    text = data_source  # In this example, data_source is a multiline string of tweets

    logger.info("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    docs = text_splitter.create_documents([text])
    logger.info(f"Number of chunks created: {len(docs)}")

    logger.info("Initializing embeddings...")
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    logger.info("Checking for existing FAISS index...")
    faiss_index_file = os.path.join(EMBEDDINGS_FOLDER, "index.faiss")
    faiss_pickle_file = os.path.join(EMBEDDINGS_FOLDER, "index.pkl")

    if os.path.exists(faiss_index_file) and os.path.exists(faiss_pickle_file):
        logger.info("Loading existing FAISS index...")
        vectorstore = FAISS.load_local(
            EMBEDDINGS_FOLDER,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        logger.info("Creating new FAISS index...")
        os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)
        vectorstore = FAISS.from_documents(docs, embeddings)
        logger.info("Saving FAISS index...")
        vectorstore.save_local(EMBEDDINGS_FOLDER)

    logger.info("Setting up retrieval chain...")
    domain_llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0.0,
        model_name="gpt-4o-mini"  # or "gpt-4"/"gpt-3.5-turbo"
    )

    retrieval_chain = RetrievalQA.from_chain_type(
        llm=domain_llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
    )

    logger.info("Vectorstore and retrieval chain setup complete.")


def is_unhelpful_answer(answer: str) -> bool:
    """
    Checks if the document-based answer is too short or includes phrases
    like "I don't know" that indicate an unhelpful response.
    """
    text = answer.strip().lower()
    if len(text) < 30:
        return True
    if "i don't know" in text or "i am not sure" in text:
        return True
    return False


def fallback_answer(question: str) -> dict:
    """
    Uses a general LLM with a domain prompt to generate an answer.
    The prompt includes the original question to provide context.
    """
    logger.info("Using fallback LLM approach.")
    fallback_llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3,  # slightly creative
        model_name="gpt-4o-mini"
    )

    system_prompt = (
        f"You are an expert analyst in social media and current affairs. The user's query is: \"{question}\". "
        "You have access to a large repository of relevant tweets that capture public sentiment, key trends, and opinions on this topic. "
        "Based on the tweet data processed in your retrieval chain, please provide a detailed and insightful response that summarizes prevailing opinions, highlights key trends, "
        "and, if possible, estimates any potential timeframe or conditions related to the query. "
        "If the available tweet data does not offer sufficient context, clearly state that the data is insufficient for a confident prediction."
    )

    fallback_ans = fallback_llm.call_as_llm(system_prompt)
    return {"question": question, "answer": fallback_ans}


def query_question(question: str) -> dict:
    """
    Given a question, uses the retrieval chain to produce an answer based on the tweet data.
    If the answer is unhelpful or the top tweet chunk is irrelevant, falls back to the general LLM.
    """
    global retrieval_chain, vectorstore
    logger.info(f"Received question: {question}")

    if not retrieval_chain or not vectorstore:
        logger.error("Vectorstore or retrieval chain not initialized.")
        return {"error": "Vectorstore or retrieval chain not initialized."}

    docs_with_scores = vectorstore.similarity_search_with_score(question, k=24)

    context = "\n---\n".join([doc.page_content for doc, score in docs_with_scores])
    logger.info("Aggregated context from retrieved tweets:")
    logger.info(context)

    system_prompt = (
        f"You are an expert analyst in social media and current affairs. The user's query is: \"{question}\". "
        "Below is the aggregated tweet data that provides context on this topic:\n\n"
        f"{context}\n\n"
        "Based on these tweets, please provide a detailed, insightful response that summarizes prevailing opinions, "
        "highlights key trends, and if possible, estimates any potential timeframe or conditions related to the query. "
        "If the tweet data does not offer enough information, clearly state that the available data is insufficient for a confident prediction."
    )
    if not docs_with_scores:
        logger.info("No relevant tweet chunk found => fallback.")
        return fallback_answer(question)

    top_doc, top_score = docs_with_scores[0]
    logger.info(f"Top tweet chunk score: {top_score} (lower means more similar).")

    if top_score <= SIMILARITY_THRESHOLD:
        doc_answer = retrieval_chain.invoke(system_prompt)
        logger.info(f"Tweet-based answer: {doc_answer}")
        return {"question": question, "answer": doc_answer}
        # if is_unhelpful_answer(doc_answer):
        #     logger.info("Tweet-based answer is unhelpful => fallback.")
        #     return fallback_answer(question)
        # else:
        #     logger.info("Tweet-based answer is sufficiently good.")
        #     return {"question": question, "answer": doc_answer}
    else:
        logger.info("Tweet chunk not relevant => fallback.")
        return {"question": question, "answer": "FallBack Answer"}
        #return fallback_answer(question)


def classify_tweet(tweet):
    score = sia.polarity_scores(tweet)["compound"]
    if score >= 0.05:
        return "positive", score
    elif score <= -0.05:
        return "negative", score
    else:
        return "neutral", score


def find_sentiment_analysis(tweets):
    tweet_sentiments = []
    for tweet in tweets:
        label, score = classify_tweet(tweet)
        tweet_sentiments.append({"text": tweet, "label": label, "score": score})
    return tweet_sentiments


def main():
    # Sample data source: output from an Elasticsearch query containing tweets.

    from es_query import search_custom
    from data_indexing_elasticsearch import get_index_name

   # question = "When do you expect the Russia-Ukraine war to end? Additionally, please provide statistics on how many people view this war as just, unjust, or neutral."
    #question = "Who is winning the Russia-Ukraine war?"
    question = "Will apple release iphone 200?"
    response = search_custom(get_index_name(3), question, size=100)

    tweet_texts = []
    for hit in response["hits"]["hits"]:
        source = hit.get("_source", {})
        tweet_text = source.get("text", "")
        username = source.get("username", "")
        tweet_timestamp = source.get("tweetcreatedts", "")
        hashtags = source.get("hashtags", [])
        retweet_count = source.get("retweetcount", "")
        following = source.get("following", "")
        followers = source.get("followers", "")
        totaltweets = source.get("totaltweets", "")

        tweet_texts.append(tweet_text)

        # Construct a combined representation for each tweet
        # combined_text = f"{tweet_text}"
        # if username:
        #     combined_text += f" | Username: {username}"
        # if tweet_timestamp:
        #     combined_text += f" | Timestamp: {tweet_timestamp}"
        # if hashtags:
        #     combined_text += f" | Hashtags: {' '.join(hashtags)}"
        # if retweet_count:
        #     combined_text += f" | Retweets: {retweet_count}"
        # if following:
        #     combined_text += f" | Following: {following}"
        # if followers:
        #     combined_text += f" | Followers: {followers}"
        # if totaltweets:
        #     combined_text += f" | TotalTweets: {totaltweets}"

        # tweet_texts.append(combined_text)

    # Combine all enriched tweet texts into a single aggregated string.
    knowledge_text = "\n".join(tweet_texts)

    tweet_sentiments = find_sentiment_analysis(tweet_texts)

    # Get top 2 positive tweets (highest compound scores)
    positive_tweets = sorted(
        [t for t in tweet_sentiments if t["label"] == "positive"],
        key=lambda x: x["score"],
        reverse=True
    )[:2]

    # Get top 2 negative tweets (lowest compound scores)
    negative_tweets = sorted(
        [t for t in tweet_sentiments if t["label"] == "negative"],
        key=lambda x: x["score"]
    )[:2]

    # Get top 2 neutral tweets (lowest absolute compound difference from 0)
    neutral_tweets = sorted(
        [t for t in tweet_sentiments if t["label"] == "neutral"],
        key=lambda x: abs(x["score"])
    )[:2]

    print("Top Positive Tweets:")
    for tweet in positive_tweets:
        print(tweet)

    print("\nTop Negative Tweets:")
    for tweet in negative_tweets:
        print(tweet)

    print("\nTop Neutral Tweets:")
    for tweet in neutral_tweets:
        print(tweet)

    # Now pass this aggregated text as your knowledge source:
    load_or_create_vectorstore(knowledge_text)

    result = query_question(question)

    print("Final Answer:")
    print(result)

    # Extract tweet texts and append additional relevant fields


if __name__ == "__main__":
    main()
