import os
from typing import Any

import httpx

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_OLLAMA_MODEL = "qwen3:8b"
DEFAULT_TIMEOUT_SECONDS = 20.0


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/")


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


def _build_messages(prompt: str, system: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def is_ollama_available(timeout_seconds: float = 2.0) -> bool:
    try:
        response = httpx.get(f"{get_ollama_base_url()}/models", timeout=timeout_seconds)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def _generate_via_openai_sdk(prompt: str, system: str, timeout_seconds: float) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url=get_ollama_base_url(),
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        timeout=timeout_seconds,
    )
    response = client.chat.completions.create(
        model=get_ollama_model(),
        messages=_build_messages(prompt, system),
        temperature=0.2,
    )
    content = response.choices[0].message.content if response.choices else ""
    return (content or "").strip()


def _generate_via_httpx(prompt: str, system: str, timeout_seconds: float) -> str:
    payload: dict[str, Any] = {
        "model": get_ollama_model(),
        "messages": _build_messages(prompt, system),
        "temperature": 0.2,
        "stream": False,
    }
    response = httpx.post(
        f"{get_ollama_base_url()}/chat/completions",
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    body = response.json()
    choices = body.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "").strip()


def generate(prompt: str, system: str = "", timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    if not is_ollama_available():
        raise RuntimeError("Ollama 当前离线或不可达，请先启动本地模型服务。")

    try:
        return _generate_via_openai_sdk(prompt, system, timeout_seconds)
    except ImportError:
        try:
            return _generate_via_httpx(prompt, system, timeout_seconds)
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise RuntimeError(f"Ollama 调用失败：{exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Ollama 调用失败：{exc}") from exc
