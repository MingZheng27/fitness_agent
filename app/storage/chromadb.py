import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from typing import List, Dict, Any, Optional
from app.config import get_settings


class ChromaDBClient:
    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.embedding_fn = DefaultEmbeddingFunction()

    def get_collection_name(self, user_id: str) -> str:
        return f"user_{user_id}_fitness"

    def get_collection(self, user_id: str):
        name = self.get_collection_name(user_id)
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn
        )

    def add_document(self, user_id: str, document: Dict[str, Any]):
        collection = self.get_collection(user_id)
        collection.add(
            ids=[document["id"]],
            documents=[document["content"]],
            metadatas=[document["metadata"]]
        )

    def search(self, user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        collection = self.get_collection(user_id)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def delete_user_data(self, user_id: str):
        name = self.get_collection_name(user_id)
        try:
            self.client.delete_collection(name)
        except Exception:
            pass


chroma_client = ChromaDBClient()