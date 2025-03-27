import os
import math

# Import LangChain components
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

from logging_config import get_logger
from data_preprocessing import remove_special_characters, remove_links


logger = get_logger("rag.log", logger_name=__name__)

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

# --- Configuration ---

open_api_key = os.getenv("OPENAI_API_KEY")
EMBEDDINGS_FOLDER = os.path.join("embeddings", "faiss_index")

# Global references for the vectorstore and retrieval chain
retrieval_chain = None
vectorstore = None

def load_or_create_vectorstore(data_source: str, temperature):
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
    embeddings = OpenAIEmbeddings(openai_api_key=open_api_key)

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
        openai_api_key=open_api_key,
        temperature=temperature,
        model_name="gpt-4o-mini"  # or "gpt-4"/"gpt-3.5-turbo"
    )
    logger.info(f"Temperature: {temperature}")

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
        openai_api_key=open_api_key,
        temperature=0.3,  # slightly creative
        model_name="gpt-4o-mini"
    )
    logger.info(f"Temperature: {0.3}")
    system_prompt = (
        f"You are an expert analyst in social media and current affairs. The user's query is: \"{question}\". "
        "You have access to a large repository of relevant tweets that capture public sentiment, key trends, and opinions on this topic. "
        "Based on the tweet data processed in your retrieval chain, please provide a detailed and insightful response that summarizes prevailing opinions, highlights key trends, "
        "and, if possible, estimates any potential timeframe or conditions related to the query. "
        "If the available tweet data does not offer sufficient context, clearly state that the data is insufficient for a confident prediction."
    )

    fallback_ans = fallback_llm.call_as_llm(system_prompt)
    return {"question": question, "answer": fallback_ans}


def query_question(question: str, similarity_threshold, k) -> dict:
    """
    Given a question, uses the retrieval chain to produce an answer based on the tweet data.
    If the answer is unhelpful or the top tweet chunk is irrelevant, falls back to the general LLM.
    """
    global retrieval_chain, vectorstore
    logger.info(f"Received question: {question}")

    if not retrieval_chain or not vectorstore:
        logger.error("Vectorstore or retrieval chain not initialized.")
        return {"error": "Vectorstore or retrieval chain not initialized."}

    docs_with_scores = vectorstore.similarity_search_with_score(question, k)

    context = "\n---\n".join([doc.page_content for doc, score in docs_with_scores])
    logger.info("Aggregated context from retrieved tweets:")

    system_prompt = (
        "You are an expert analyst in social media and digital content, specializing in interpreting YouTube video comment data. "
        "The user is asking questions about a specific YouTube video, and the aggregated comment data below provides context about the video's content and audience sentiment:\n\n"
        f"{context}\n\n"
        f"Based on this comment data, please provide a specific response to the user's query: \"{question}\". "
        "If the user asks for a detailed, insightful response, provide detailed, insightful response based on the aggregated comment data."
        "If the comment data does not provide sufficient context for a confident analysis, clearly state that additional information is needed."
    )

    if not docs_with_scores:
        logger.info("No relevant tweet chunk found => fallback.")
        return fallback_answer(question)

    top_doc, top_score = docs_with_scores[0]
    logger.info(f"Top tweet chunk score: {top_score} (lower means more similar).")

    if top_score <= similarity_threshold:
        doc_answer = retrieval_chain.invoke(system_prompt)
        logger.info(f"Tweet-based answer: {doc_answer}")
        return {"question": question, "answer": doc_answer["result"]}
    else:
        logger.info("Tweet chunk not relevant => fallback.")
        return {"question": question,
                "answer": "Compound score exceeded the similarity threshold. No answers were found."}


def get_top_tweets(query) -> list:
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=5)
    results = []
    for idx, (doc, score) in enumerate(docs_with_scores, 1):
        results.append({
            "tweet_index": idx,
            "score": score,
            "tweet_text": doc.page_content,
            "sentiment": classify_tweet(doc.page_content)
        })
    return results


def classify_tweet(tweet):
    score = sia.polarity_scores(tweet)["compound"]
    if score >= 0.05:
        return "positive", score
    elif score <= -0.05:
        return "negative", score
    else:
        return "neutral", score


# def classify_with_threshold(text, pos_thresh, neg_thresh):
#     score = sia.polarity_scores(text)["compound"]
#     if score >= pos_thresh:
#         return "positive", score
#     elif score <= neg_thresh:
#         return "negative", score
#     else:
#         return "neutral", score


def find_sentiment_analysis(tweets):
    tweet_sentiments = []
    for tweet in tweets:
        label, score = classify_tweet(tweet)
        tweet_sentiments.append({"text": tweet, "label": label, "score": score})
    return tweet_sentiments


def detect_and_remove_bias(query_response_es):
    tweet_texts_without_bias = []
    tweet_texts_with_bias = []
    for hit in query_response_es["hits"]["hits"]:
        source = hit.get("_source", {})
        tweet_text = source.get("text", "")
        username = source.get("username", "")
        tweet_timestamp = source.get("tweetcreatedts", "")
        hashtags = source.get("hashtags", [])
        retweet_count = source.get("retweetcount", "")
        following = source.get("following", "")
        followers = source.get("followers", "")
        total_tweets = source.get("totaltweets", "")

        combined_text_with_bias = f"{tweet_text}"
        if username:
            combined_text_with_bias += f" | Username: {username}"
        if tweet_timestamp:
            combined_text_with_bias += f" | Timestamp: {tweet_timestamp}"
        if hashtags:
            combined_text_with_bias += f" | Hashtags: {' '.join(hashtags)}"
        if retweet_count:
            combined_text_with_bias += f" | Retweets: {retweet_count}"
        if following:
            combined_text_with_bias += f" | Following: {following}"
        if followers:
            combined_text_with_bias += f" | Followers: {followers}"
        if total_tweets:
            combined_text_with_bias += f" | TotalTweets: {total_tweets}"

        tweet_texts_with_bias.append(combined_text_with_bias)

        # Convert numeric fields to float; if conversion fails or value is not positive, default to 0.0.
        try:
            f1 = float(followers) if followers and float(followers) > 0 else 0.0
        except:
            f1 = 0.0

        try:
            r1 = float(retweet_count) if retweet_count and float(retweet_count) > 0 else 0.0
        except:
            r1 = 0.0

        try:
            t = float(total_tweets) if total_tweets and float(total_tweets) > 0 else 0.0
        except:
            t = 0.0

        try:
            f2 = float(following) if following and float(following) > 0 else 0.0
        except:
            f2 = 0.0

        # Normalize using math.log1p (i.e., log(1+x)) and scale down by divisor (10.0)
        followersNorm = math.log1p(f1) / 10.0
        retweetsNorm = math.log1p(r1) / 10.0
        followingNorm = math.log1p(t) / 10.0
        totaltweetsNorm = math.log1p(f2) / 10.0

        # Reweighing: compute a factor inversely proportional to the normalized followers.
        # Tweets from users with high followersNorm receive lower weight.
        reweight_factor = 1 / (1 + followersNorm)

        # Adjust normalized values with the reweight factor.
        retweetsNorm_adjusted = retweetsNorm * reweight_factor
        followingNorm_adjusted = followingNorm * reweight_factor
        totaltweetsNorm_adjusted = totaltweetsNorm * reweight_factor

        # Construct a combined representation for the tweet.
        combined_text = tweet_text
        if username:
            combined_text += f" | Username: {username}"
        if tweet_timestamp:
            combined_text += f" | Timestamp: {tweet_timestamp}"
        if hashtags:
            combined_text += f" | Hashtags: {' '.join(hashtags)}"
        if retweet_count:
            combined_text += f" | Retweets: {retweetsNorm_adjusted}"
        if following:
            combined_text += f" | Following: {followingNorm_adjusted}"
        if followers:
            combined_text += f" | Followers: {followersNorm}"
        if total_tweets:
            combined_text += f" | TotalTweets: {totaltweetsNorm_adjusted}"

        tweet_texts_without_bias.append(combined_text)

    knowledge_text_without_bias = "\n".join(tweet_texts_without_bias)
    knowledge_text_with_bias = "\n".join(tweet_texts_with_bias)

    return {
        "knowledge_text_with_bias": knowledge_text_with_bias,
        "knowledge_text_without_bias": knowledge_text_without_bias
    }


def get_results(question, comments, similarity_threshold, document_count, temperature):
    # Reset the global state to force reinitialization with new parameters
    global retrieval_chain, vectorstore
    retrieval_chain = None
    vectorstore = None

    logger.info(f"Similarity Threshold: {similarity_threshold}")
    logger.info(f"k value: {document_count}")
    logger.info(f"Temperature: {temperature}")


    processed_comment = []
    for comment in comments:
            comment = remove_links(comment)
            comment = remove_special_characters(comment)
            processed_comment.append(comment)

    knowledge_text = "\n".join(processed_comment)
    load_or_create_vectorstore(knowledge_text, temperature)
    return query_question(question, similarity_threshold, document_count)

    # Now pass knowledge_text_without_bias text as knowledge source:
    # load_or_create_vectorstore(knowledge_text['knowledge_text_without_bias'], temperature)
    #
    # result = query_question(question, similarity_threshold, document_count)
    #
    # return result


# def run_analysis(result):
#     """
#     Perform sensitivity analysis on the sentiment classification by
#     varying positive and negative thresholds. It retrieves tweets using
#     the provided question and logs the sentiment distribution for each
#     threshold combination.
#     """
#
#     pos_thresholds = [0.0, 0.05, 0.1, 0.2]
#     neg_thresholds = [-0.05, -0.1, -0.2]
#     # Retrieve tweets from Elasticsearch using the provided question
#     # Loop through each combination of thresholds and classify sentiments
#     for p_thresh in pos_thresholds:
#         for n_thresh in neg_thresholds:
#             counts = {"positive": 0, "neutral": 0, "negative": 0}
#             sentiment, score = classify_with_threshold(result, p_thresh, n_thresh)
#             counts[sentiment] += 1
#             logger.info(f"\nThresholds: pos_thresh = {p_thresh}, neg_thresh = {n_thresh}")
#             logger.info(f"Sentiment counts: {counts}")


def main():
    # question = "When do you expect the Russia-Ukraine war to end? Additionally, please provide statistics on how many people view this war as just, unjust, or neutral."
    question = "Who is winning the Russia-Ukraine war?"
    # question = "Will apple release iphone 200?"

    similarity_threshold = 1.5
    document_count = 10
    temperature = 0.0
    result = get_results(question, get_index_name(3), similarity_threshold, document_count, temperature)
    logger.info(result)

    # run_analysis(result)
    # Extract tweet texts and append additional relevant fields
    top_tweets = get_top_tweets(question)
    logger.info(top_tweets)


if __name__ == "__main__":
    main()
