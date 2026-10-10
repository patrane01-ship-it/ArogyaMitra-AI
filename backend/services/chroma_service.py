"""
ArogyaMitra AI - Chroma Vector Store Service
Handles local persistent embeddings and semantic indexing for health records and drug interactions.
Per TECH_STACK.md §1 and PRODUCTION_BACKEND.md §5.1.
"""

import os
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.core.logger import logger


class ChromaService:
    """Service wrapping ChromaDB persistent client."""

    _instance = None

    def __init__(self):
        self.client = None
        self.collection = None
        self._init_db()

    def _init_db(self):
        """Initialize ChromaDB local persistent client."""
        try:
            import chromadb
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
            self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            self.collection = self.client.get_or_create_collection(
                name="health_records",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[ChromaService] Initialized collection at {settings.CHROMA_DB_PATH}")
        except Exception as e:
            logger.warning(f"[ChromaService] ChromaDB initialization deferred/failed: {e}")
            self.client = None
            self.collection = None

    def add_record(self, record_id: str, text: str, metadata: Dict[str, Any]):
        """Index a health record with text content and metadata."""
        if not self.collection:
            logger.debug("[ChromaService] ChromaDB not available, skipping index")
            return
        try:
            self.collection.upsert(
                ids=[record_id],
                documents=[text[:4000]],
                metadatas=[metadata]
            )
            logger.debug(f"[ChromaService] Record indexed: {record_id}")
        except Exception as e:
            logger.warning(f"[ChromaService] Failed to index record {record_id}: {e}")

    def query_similar(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Find most relevant documents using cosine similarity."""
        if not self.collection:
            return []
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.warning(f"[ChromaService] Query failed: {e}")
            return []


_chroma_service_instance: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """Singleton getter for ChromaService."""
    global _chroma_service_instance
    if _chroma_service_instance is None:
        _chroma_service_instance = ChromaService()
    return _chroma_service_instance
