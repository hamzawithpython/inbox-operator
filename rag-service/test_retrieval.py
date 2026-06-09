"""Quick standalone test of retrieval — not part of the service."""
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "chroma_db")
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection("nimbus_support")

query = "I forgot my login details, how can I get back in?"
q_emb = model.encode([query]).tolist()
results = collection.query(query_embeddings=q_emb, n_results=2)

print(f"Query: {query}\n")
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"- Matched: {meta['question']}")
