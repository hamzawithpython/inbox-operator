"""Inbox Operator RAG service: retrieves from the knowledge base and drafts a grounded support reply."""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

load_dotenv()

DB_PATH = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "nimbus_support"
TOP_K = 3

# Load once at startup (not per request).
print("Loading embedding model...")
_model = SentenceTransformer("all-MiniLM-L6-v2")
_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _client.get_collection(COLLECTION_NAME)
_groq = Groq(api_key=os.environ["GROQ_API_KEY"])
print("RAG service ready.")

app = FastAPI(title="Inbox Operator RAG Service")


class SupportRequest(BaseModel):
    subject: str = ""
    body: str = ""
    from_name: str = ""


class SupportResponse(BaseModel):
    draft: str
    sources: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "documents": _collection.count()}


@app.post("/support-reply", response_model=SupportResponse)
def support_reply(req: SupportRequest) -> SupportResponse:
    # 1. Retrieve relevant knowledge base entries for the email content.
    query = f"{req.subject}\n{req.body}"
    q_emb = _model.encode([query]).tolist()
    results = _collection.query(query_embeddings=q_emb, n_results=TOP_K)

    retrieved = results["metadatas"][0]
    sources = [m["question"] for m in retrieved]
    context = "\n\n".join(
        f"FAQ: {m['question']}\nAnswer: {m['answer']}" for m in retrieved
    )

    # 2. Generate a grounded reply using only the retrieved context.
    system_prompt = (
        "You are a customer support assistant for a SaaS product called Nimbus. "
        "Write a concise, friendly, professional reply to the customer email below, "
        "using ONLY the information in the provided knowledge base context. "
        "If the context does not contain the answer, say you will escalate the question "
        "to the team rather than inventing details. Do not make up features, prices, or policies. "
        "Output ONLY the email body text: no subject line, no markdown. Sign off as Best regards, Nimbus Support."
    )
    user_prompt = (
        f"Knowledge base context:\n{context}\n\n"
        f"Customer email:\nFrom: {req.from_name}\nSubject: {req.subject}\n\n{req.body}"
    )

    completion = _groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    draft = completion.choices[0].message.content.strip()

    return SupportResponse(draft=draft, sources=sources)
