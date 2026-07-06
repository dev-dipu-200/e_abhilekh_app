import json
import httpx
from app.settings.config import settings
from app.utils.ai_runtime import AIRuntimeConfig


def generate(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.7,
    num_predict: int = 1024,
    runtime: AIRuntimeConfig | None = None,
) -> str:
    runtime = runtime or AIRuntimeConfig(
        organization_id="global",
        provider="ollama",
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
        generation_model=settings.OLLAMA_GENERATION_MODEL,
        embedding_dimensions=settings.OLLAMA_EMBEDDING_DIMENSIONS,
        collection_name="documents_global",
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )
    if runtime.provider == "openai":
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return chat(messages, temperature=temperature, num_predict=num_predict, runtime=runtime)
    payload = {
        "model": runtime.generation_model,
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
        f"{runtime.ollama_base_url or settings.OLLAMA_BASE_URL}/api/generate",
        json=payload,
        verify=False,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def chat(
    messages: list[dict],
    temperature: float = 0.7,
    num_predict: int = 1024,
    runtime: AIRuntimeConfig | None = None,
) -> str:
    runtime = runtime or AIRuntimeConfig(
        organization_id="global",
        provider="ollama",
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
        generation_model=settings.OLLAMA_GENERATION_MODEL,
        embedding_dimensions=settings.OLLAMA_EMBEDDING_DIMENSIONS,
        collection_name="documents_global",
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )
    if runtime.provider == "openai":
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {runtime.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": runtime.generation_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": num_predict,
            },
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    payload = {
        "model": runtime.generation_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "repeat_penalty": 1.1,
        },
    }
    resp = httpx.post(
        f"{runtime.ollama_base_url or settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        verify=False,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def stream_chat(
    messages: list[dict],
    temperature: float = 0.7,
    num_predict: int = 1024,
    runtime: AIRuntimeConfig | None = None,
):
    runtime = runtime or AIRuntimeConfig(
        organization_id="global",
        provider="ollama",
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
        generation_model=settings.OLLAMA_GENERATION_MODEL,
        embedding_dimensions=settings.OLLAMA_EMBEDDING_DIMENSIONS,
        collection_name="documents_global",
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )
    if runtime.provider == "openai":
        with httpx.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {runtime.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": runtime.generation_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": num_predict,
                "stream": True,
            },
            timeout=300,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        yield content
        return

    payload = {
        "model": runtime.generation_model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "repeat_penalty": 1.1,
        },
    }
    with httpx.stream(
        "POST",
        f"{runtime.ollama_base_url or settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        verify=False,
        timeout=300,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            content = data.get("message", {}).get("content", "")
            if content:
                yield content
            if data.get("done"):
                break
