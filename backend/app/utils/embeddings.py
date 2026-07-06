import time
import httpx
import numpy as np
from app.utils.ai_runtime import AIRuntimeConfig
from app.settings.config import settings


def _ollama_embed(texts: list[str], runtime: AIRuntimeConfig) -> list[list[float]]:
    if not texts:
        return []
    for attempt in range(3):
        try:
            resp = httpx.post(
                f"{runtime.ollama_base_url or settings.OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": runtime.embedding_model,
                    "input": texts,
                    "dimensions": runtime.embedding_dimensions,
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


def _openai_embed(texts: list[str], runtime: AIRuntimeConfig) -> list[list[float]]:
    if not texts:
        return []
    headers = {
        "Authorization": f"Bearer {runtime.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, object] = {
        "model": runtime.embedding_model,
        "input": texts,
    }
    if runtime.embedding_model.startswith("text-embedding-3"):
        payload["dimensions"] = runtime.embedding_dimensions
    for attempt in range(3):
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def encode_documents(texts: list[str], runtime: AIRuntimeConfig) -> list[list[float]]:
    if runtime.provider == "openai":
        return _openai_embed(texts, runtime)
    return _ollama_embed(texts, runtime)


def encode_query(text: str, runtime: AIRuntimeConfig) -> list[float]:
    return encode_documents([text], runtime)[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    arr_a = np.array(a, dtype=np.float64)
    arr_b = np.array(b, dtype=np.float64)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))
