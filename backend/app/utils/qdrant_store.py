import uuid
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.settings.config import settings
from app.utils.embeddings import encode_query


COLLECTION_NAME = "documents_v4"
VECTOR_SIZE = settings.OLLAMA_EMBEDDING_DIMENSIONS


@lru_cache(maxsize=None)
def _get_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL, timeout=120)


def ensure_collection():
    client = _get_client()
    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )


def upsert_chunks(chunks: list[dict]):
    ensure_collection()
    client = _get_client()
    points = []
    for chunk in chunks:
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=chunk["vector"],
                payload={
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "page_number": chunk.get("page_number"),
                    "subject": chunk.get("subject"),
                    "organization_id": chunk["organization_id"],
                    "department_id": chunk.get("department_id"),
                    "document_type_id": chunk.get("document_type_id"),
                    "file_number": chunk.get("file_number"),
                },
            )
        )
    # Batch in groups of 10 to avoid Qdrant timeouts
    batch_size = 10
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)


def delete_document_chunks(document_id: str):
    client = _get_client()
    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        return
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                )
            ]
        ),
    )


def search(
    query: str,
    organization_id: str,
    limit: int = 10,
    score_threshold: float = 0.30,
    department_id: str | None = None,
    document_type_id: str | None = None,
) -> list[dict]:
    """Semantic search with score threshold and optional metadata pre-filtering.
    
    Score threshold of 0.30 removes clearly irrelevant results while keeping
    most semantically relevant results for qwen3-embedding:8b vectors.
    Results are re-ranked with a small keyword-boost to surface exact matches.
    """
    ensure_collection()
    client = _get_client()
    query_vector = encode_query(query)

    # Build metadata filter
    must_conditions = [
        models.FieldCondition(
            key="organization_id",
            match=models.MatchValue(value=organization_id),
        )
    ]
    if department_id:
        must_conditions.append(
            models.FieldCondition(
                key="department_id",
                match=models.MatchValue(value=department_id),
            )
        )
    if document_type_id:
        must_conditions.append(
            models.FieldCondition(
                key="document_type_id",
                match=models.MatchValue(value=document_type_id),
            )
        )

    hits = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=models.Filter(must=must_conditions),
        limit=limit * 3,  # over-fetch for re-ranking
        score_threshold=score_threshold,
        with_payload=True,
    ).points

    # Keyword-boost re-ranking: promote chunks that contain query words
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    def _boost(hit) -> float:
        content_lower = hit.payload.get("content", "").lower()
        subject_lower = hit.payload.get("subject", "").lower()
        keyword_hits = sum(1 for w in query_words if w in content_lower)
        subject_hits = sum(1 for w in query_words if w in subject_lower)
        # Small boost: 0.02 per keyword hit in content, 0.05 per subject hit
        return hit.score + keyword_hits * 0.02 + subject_hits * 0.05

    ranked = sorted(hits, key=_boost, reverse=True)

    return [
        {
            "document_id": hit.payload["document_id"],
            "chunk_id": hit.payload["chunk_id"],
            "content": hit.payload["content"],
            "score": round(_boost(hit), 4),
            "page_number": hit.payload.get("page_number"),
            "subject": hit.payload.get("subject"),
            "department_id": hit.payload.get("department_id"),
            "document_type_id": hit.payload.get("document_type_id"),
            "file_number": hit.payload.get("file_number"),
        }
        for hit in ranked[:limit]
    ]
