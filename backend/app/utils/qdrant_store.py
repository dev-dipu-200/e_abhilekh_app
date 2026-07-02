import uuid
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.settings.config import settings
from app.utils.embeddings import encode_query


COLLECTION_NAME = "documents_v3"
VECTOR_SIZE = settings.OLLAMA_EMBEDDING_DIMENSIONS


@lru_cache(maxsize=None)
def _get_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


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
        raw_id = chunk["id"]
        hex_part = raw_id.split("_", 1)[-1] if "_" in raw_id else raw_id
        point_id = uuid.UUID(hex=hex_part) if len(hex_part) == 32 else raw_id
        points.append(
            models.PointStruct(
                id=point_id,
                vector=chunk["vector"],
                payload={
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "page_number": chunk.get("page_number"),
                    "subject": chunk.get("subject"),
                    "organization_id": chunk["organization_id"],
                },
            )
        )
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def delete_document_chunks(document_id: str):
    client = _get_client()
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


def search(query: str, organization_id: str, limit: int = 10) -> list[dict]:
    ensure_collection()
    client = _get_client()
    query_vector = encode_query(query)
    hits = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="organization_id",
                    match=models.MatchValue(value=organization_id),
                )
            ]
        ),
        limit=limit,
    ).points
    return [
        {
            "document_id": hit.payload["document_id"],
            "chunk_id": hit.payload["chunk_id"],
            "content": hit.payload["content"],
            "score": round(hit.score, 4),
            "page_number": hit.payload.get("page_number"),
            "subject": hit.payload.get("subject"),
        }
        for hit in hits
    ]
