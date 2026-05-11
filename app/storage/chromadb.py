import logging
import os
import posthog

os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
posthog.disabled = True
posthog.capture = lambda *args, **kwargs: None

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from typing import List, Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)


class ChromaDBClient:
    def __init__(self):
        settings = get_settings()
        chromadb.configure(anonymized_telemetry=False)
        self.client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
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
        try:
            collection = self.get_collection(user_id)
            collection.add(
                ids=[document["id"]],
                documents=[document["content"]],
                metadatas=[document["metadata"]]
            )
            logger.info(f"[ChromaDB] document added user_id={user_id} doc_id={document['id']} type={document['metadata'].get('type')}")
        except Exception as e:
            logger.error(f"[ChromaDB] add_document failed user_id={user_id} error={e}")
            raise

    def search(self, user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        try:
            collection = self.get_collection(user_id)
            collection_size = collection.count()
            if collection_size == 0:
                logger.info(f"[ChromaDB] search skipped user_id={user_id} query={query[:30]} results=0")
                return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}

            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection_size),
                where={"user_id": user_id}
            )
            logger.info(f"[ChromaDB] search user_id={user_id} query={query[:30]} results={len(results.get('documents', [[]])[0])}")
            return results
        except Exception as e:
            logger.error(f"[ChromaDB] search failed user_id={user_id} error={e}")
            raise

    def delete_user_data(self, user_id: str):
        name = self.get_collection_name(user_id)
        try:
            self.client.delete_collection(name)
            logger.info(f"[ChromaDB] deleted collection user_id={user_id}")
        except Exception:
            pass


chroma_client = ChromaDBClient()
