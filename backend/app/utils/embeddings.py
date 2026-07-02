import time
import httpx
import numpy as np
from app.settings.config import settings


def _ollama_embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    for attempt in range(3):
        try:
            resp = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": settings.OLLAMA_EMBEDDING_MODEL,
                    "input": texts,
                    "dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
                },
                verify=False,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def encode_documents(texts: list[str]) -> list[list[float]]:
    return _ollama_embed(texts)


def encode_query(text: str) -> list[float]:
    return _ollama_embed([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    arr_a = np.array(a, dtype=np.float64)
    arr_b = np.array(b, dtype=np.float64)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))
