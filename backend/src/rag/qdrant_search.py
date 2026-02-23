"""Qdrant RAG Search — multi-collection support for VyapaarSetu."""

from typing import Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from src.core.logging import log
from src.config import settings

# Collection constants
TAXONOMY_COLLECTION = settings.get("QDRANT_COLLECTION_TAXONOMY", "vyapaarsetu_taxonomy")
SNP_COLLECTION = settings.get("QDRANT_COLLECTION_SNP", "vyapaarsetu_snp")
KNOWLEDGE_COLLECTION = settings.get("QDRANT_COLLECTION_KNOWLEDGE", "vyapaarsetu_knowledge")


class QdrantSearch:
    """Search service using Qdrant for ONDC taxonomy, SNP knowledge, and TEAM scheme knowledge."""

    _client: Optional[QdrantClient] = None
    _encoder: Optional[SentenceTransformer] = None
    _collections_initialized: set[str] = set()

    QDRANT_URL = settings.get("QDRANT_URL", "http://localhost:6333")
    EMBEDDING_MODEL = settings.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = settings.get("EMBEDDING_DIMENSION", 384)

    @classmethod
    def get_client(cls) -> QdrantClient:
        if cls._client is None:
            cls._client = QdrantClient(url=cls.QDRANT_URL)
            log.info(f"Connected to Qdrant at {cls.QDRANT_URL}")
        return cls._client

    @classmethod
    def get_encoder(cls) -> SentenceTransformer:
        if cls._encoder is None:
            cls._encoder = SentenceTransformer(cls.EMBEDDING_MODEL)
            log.info(f"Loaded embedding model: {cls.EMBEDDING_MODEL}")
        return cls._encoder

    @classmethod
    def ensure_collection(cls, collection_name: str) -> str:
        if collection_name in cls._collections_initialized:
            return collection_name

        client = cls.get_client()
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)

        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=cls.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            log.info(f"Created Qdrant collection: {collection_name}")

            for field in ["source", "type", "category_code"]:
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass

        cls._collections_initialized.add(collection_name)
        return collection_name

    @classmethod
    def index_chunks(
        cls,
        chunks: list[dict],
        source: str = "",
        collection_name: str = KNOWLEDGE_COLLECTION,
        extra_payload: dict | None = None,
    ) -> int:
        """Index text chunks into a Qdrant collection."""
        client = cls.get_client()
        encoder = cls.get_encoder()
        cls.ensure_collection(collection_name)

        points = []
        for chunk in chunks:
            content = chunk["content"]
            embedding = encoder.encode(content, show_progress_bar=False).tolist()

            payload = {
                "content": content,
                "source": source or chunk.get("source", ""),
                "type": "document",
                "chunk_index": chunk.get("index", 0),
            }
            if extra_payload:
                payload.update(extra_payload)

            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            ))

        if points:
            for i in range(0, len(points), 100):
                batch = points[i:i + 100]
                client.upsert(collection_name=collection_name, points=batch)
            log.info(f"Indexed {len(points)} chunks from {source} into {collection_name}")

        return len(points)

    @classmethod
    def search(
        cls,
        query: str,
        collection_name: str = KNOWLEDGE_COLLECTION,
        limit: int = 5,
        score_threshold: float = 0.3,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for relevant document chunks in a specific collection."""
        client = cls.get_client()
        encoder = cls.get_encoder()
        cls.ensure_collection(collection_name)

        try:
            query_vector = encoder.encode(query, show_progress_bar=False).tolist()

            must_conditions = [
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(value="document"),
                ),
            ]

            if filters:
                for key, value in filters.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                    )

            results = client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=models.Filter(must=must_conditions),
                with_payload=True,
            )

            return [
                {
                    "id": str(r.id),
                    "content": r.payload.get("content", ""),
                    "score": r.score,
                    "source": r.payload.get("source", ""),
                    "chunk_index": r.payload.get("chunk_index", 0),
                }
                for r in results
            ]

        except Exception as e:
            log.error(f"Search error in {collection_name}: {e}")
            return []

    @classmethod
    def build_context(
        cls,
        query: str,
        collection_name: str = KNOWLEDGE_COLLECTION,
        max_tokens: int = 2000,
        limit: int = 5,
        filters: dict | None = None,
    ) -> str:
        """Build RAG context string from search results."""
        results = cls.search(
            query,
            collection_name=collection_name,
            limit=limit * 2,
            filters=filters,
        )
        max_chars = max_tokens * 4

        parts = []
        total_chars = 0
        for r in results[:limit]:
            content = r["content"]
            if total_chars + len(content) > max_chars:
                break
            parts.append(content)
            total_chars += len(content)

        if parts:
            return "## Knowledge Base\n" + "\n\n---\n\n".join(parts)
        return ""
