import httpx
from app.settings.config import settings


def generate(prompt: str, system: str | None = None, temperature: float = 0.7, num_predict: int = 1024) -> str:
    payload = {
        "model": settings.OLLAMA_GENERATION_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "repeat_penalty": 1.1,
        },
    }
    if system:
        payload["system"] = system

    resp = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json=payload,
        verify=False,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def chat(messages: list[dict], temperature: float = 0.7, num_predict: int = 1024) -> str:
    """Use /api/chat endpoint for better instruction-following via message role structure."""
    payload = {
        "model": settings.OLLAMA_GENERATION_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "repeat_penalty": 1.1,
        },
    }
    resp = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        verify=False,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
