import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class SemanticMemory:
    def __init__(self, persist_dir="data/chroma"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir
        ))
        self.collection = self.client.get_or_create_collection("mazgpt_memory")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def add_message(self, message_id, text, metadata=None, project_id="default"):
        meta = metadata.copy() if metadata else {}
        meta["project_id"] = project_id
        embedding = self.embedder.encode(text).tolist()
        self.collection.add(
            ids=[message_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta]
        )

    def query(self, query_text, n_results=5, project_id="default"):
        embedding = self.embedder.encode(query_text).tolist()
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=50  # get more, filter by project below
        )
        filtered = [
            (doc, meta, score)
            for doc, meta, score in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
            if meta.get("project_id", "default") == project_id
        ]
        return filtered[:n_results]

    def persist(self):
        self.client.persist()
