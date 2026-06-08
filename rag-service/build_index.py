"""Build a persistent Chroma vector store from the synthetic knowledge base."""
import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

KB_PATH = Path(__file__).parent / "knowledge_base.json"
DB_PATH = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "nimbus_support"

def main() -> None:
    with open(KB_PATH, "r", encoding="utf-8-sig") as f:
        kb = json.load(f)

    print(f"Loaded {len(kb)} knowledge base entries.")

    # Local embedding model (downloads once, ~80MB).
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=DB_PATH)
    # Reset collection so re-running is idempotent.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    # Embed the question+answer text for richer retrieval.
    documents = [f"Q: {item['question']}\nA: {item['answer']}" for item in kb]
    ids = [item["id"] for item in kb]
    metadatas = [{"question": item["question"], "answer": item["answer"]} for item in kb]
    embeddings = model.encode(documents).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Built vector store at {DB_PATH} with {collection.count()} documents.")

if __name__ == "__main__":
    main()
