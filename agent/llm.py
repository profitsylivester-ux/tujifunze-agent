"""
LLM wrapper for the Tujifunze agent.

Two backends are supported:
  - "ollama"  (local)  : uses Ollama at http://localhost:11434
  - "groq"    (cloud)  : uses Groq's OpenAI-compatible API

Which one is used is controlled by the LLM_BACKEND environment variable:
    LLM_BACKEND=ollama  (default)
    LLM_BACKEND=groq

For groq, set GROQ_API_KEY in your environment or in a .env file.

Both backends are exposed as LangChain chat models, so the rest of the
agent code does not care which one is live.
"""

import os
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel


# ---- Default model names ------------------------------------------------
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_GROQ_MODEL = "qwen/qwen3-32b"


def get_llm(temperature: float = 0.2) -> BaseChatModel:
    """
    Return a LangChain chat model based on LLM_BACKEND env var.

    Args:
        temperature: 0.0 = deterministic, 1.0 = creative. We default low
                     because the agent should reason consistently.

    Returns:
        A LangChain BaseChatModel (ChatOllama or ChatGroq).
    """
    backend = os.getenv("LLM_BACKEND", "ollama").lower().strip()

    if backend == "ollama":
        from langchain_ollama import ChatOllama
        model_name = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    if backend == "groq":
        # Imported lazily so that local-only users don't need groq installed.
        from langchain_groq import ChatGroq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "LLM_BACKEND=groq requires GROQ_API_KEY to be set in the environment."
            )
        model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        return ChatGroq(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )

    raise ValueError(
        f"Unknown LLM_BACKEND='{backend}'. Use 'ollama' or 'groq'."
    )


def describe_backend() -> dict[str, Any]:
    """Return a small dict describing the active backend (for logging/UI)."""
    backend = os.getenv("LLM_BACKEND", "ollama").lower().strip()
    if backend == "ollama":
        return {
            "backend": "ollama",
            "model": os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            "location": "local",
        }
    if backend == "groq":
        return {
            "backend": "groq",
            "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
            "location": "cloud",
        }
    return {"backend": backend, "model": "unknown", "location": "unknown"}
