import httpx
from app.settings.config import settings


def generate(prompt: str, system: str | None = None, temperature: float = 0.7) -> str:
    payload = {
        "model": settings.OLLAMA_GENERATION_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
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


def chat(messages: list[dict], temperature: float = 0.7) -> str:
    payload = {
        "model": settings.OLLAMA_GENERATION_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        verify=False,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
