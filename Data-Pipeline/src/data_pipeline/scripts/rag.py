import os
import docx2txt
import logging

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

from dotenv import load_dotenv

# If you're still on langchain_community, keep those imports;
# otherwise, if you installed langchain-openai, update accordingly.
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Please set it in .env or as an environment variable.")

DOC_PATH = os.path.join("docs", "knowledge_source.docx")
EMBEDDINGS_FOLDER = os.path.join("embeddings", "faiss_index")

# Global references
retrieval_chain = None
vectorstore = None

# For FAISS (default L2 distance), smaller => more similar
SIMILARITY_THRESHOLD = 1.5

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def load_or_create_vectorstore():
    """
    On startup, load or create the vectorstore from the docx knowledge_source.
    """
    global retrieval_chain, vectorstore

    logger.info("Loading docx file for knowledge source...")
    text = docx2txt.process(DOC_PATH)

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

    logger.info("Startup complete! API is ready.")

@app.post("/query")
async def query_endpoint(request_data: QueryRequest):
    """
    Logic:
      1. Attempt doc-based retrieval. 
         - If top doc chunk is relevant (score < threshold), get doc-based answer.
      2. Analyze doc-based answer: 
         - If short, includes "I do not know," or is unhelpful, fallback to a general LLM.
      3. If doc-based is obviously irrelevant (score > threshold), fallback immediately.
    """
    global retrieval_chain, vectorstore

    question = request_data.question
    logger.info(f"Received question: {question}")

    if not retrieval_chain or not vectorstore:
        logger.error("Retrieval chain or vectorstore not initialized.")
        return {"error": "Retrieval chain or vectorstore not initialized."}

    # Step 1: Check if doc is relevant
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=1)
    if not docs_with_scores:
        logger.info("No relevant doc chunk found => fallback.")
        return fallback_answer(question)

    top_doc, top_score = docs_with_scores[0]
    logger.info(f"Top doc score: {top_score} (lower=more similar for L2 distance).")

    if top_score <= SIMILARITY_THRESHOLD:
        # Potentially relevant to doc
        doc_answer = retrieval_chain.run(question)
        logger.info(f"Doc-based answer: {doc_answer}")

        # Step 2: Evaluate doc-based answer
        # If it's too short or "doesn't know," fallback
        if is_unhelpful_answer(doc_answer):
            logger.info("Doc-based answer is unhelpful => fallback.")
            fb = fallback_answer(question)
            return {"question": question, "answer": fb["answer"]}
        else:
            # Return doc-based answer
            logger.info("Doc-based answer is sufficiently good.")
            return {"question": question, "answer": doc_answer}
    else:
        # Step 3: Not relevant => fallback
        logger.info("Doc not relevant => fallback.")
        return fallback_answer(question)

def is_unhelpful_answer(answer: str) -> bool:
    """
    Checks if the doc-based answer is too short, includes 'I don't know', or
    otherwise unhelpful. Adjust logic to your needs.
    """
    text = answer.strip().lower()
    if len(text) < 30:  # arbitrary length check
        return True
    if "i don't know" in text or "i am not sure" in text:
        return True
    # You could add other checks, e.g. "i don't have information"
    return False

def fallback_answer(question: str) -> dict:
    """
    Calls a general LLM with a domain prompt.
    If question is obviously out of domain, instruct LLM to say "I don't know."
    Otherwise, the LLM can answer from general knowledge (like definitions of AI).
    """
    logger.info("Using fallback LLM approach.")
    fallback_llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3,  # slightly creative
        model_name="gpt-4o-mini"
    )

    system_prompt = (
        "You are a helpful AI assistant working for an AI-based company. "
        "The user asked a question that is not explicitly covered in the doc. "
        "If the question is relevant to AI or the company's domain, provide a helpful general answer. "
        "If the question is obviously unrelated (e.g., how to bake a cake), respond with 'I don't know.'\n\n"
        f"User question: {question}\n"
    )

    fallback_answer = fallback_llm.call_as_llm(system_prompt)
    return {"question": question, "answer": fallback_answer}

@app.get("/")
async def root():
    return {"message": "RAG API is running. Use the /query endpoint to ask questions."}
