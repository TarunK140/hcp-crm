"""
Thin wrapper around the Groq API.

Centralizing this in one place means:
- the API key is read from .env exactly once
- every tool/prompt call goes through the same error handling & logging
- swapping models (gemma2-9b-it <-> llama-3.3-70b-versatile) is a one-line change
"""

import json
from typing import Optional
from groq import Groq
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY is not set — LLM calls will fail until it is configured.")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def chat_completion(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.2,
    json_mode: bool = False,
) -> str:
    """
    Send a chat completion request to Groq and return the raw text content.

    json_mode=True asks the model to return valid JSON only — used by the
    tools that need structured extraction (Log Interaction, Edit Interaction).
    """
    client = get_client()
    model_name = model or settings.groq_model

    kwargs = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("Groq API call failed with model=%s: %s", model_name, exc)
        # Fall back to the secondary model once before giving up.
        if model_name != settings.groq_model_fallback:
            logger.info("Retrying with fallback model=%s", settings.groq_model_fallback)
            kwargs["model"] = settings.groq_model_fallback
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        raise


def safe_json_parse(raw_text: str) -> dict:
    """Parse LLM JSON output defensively (models sometimes wrap JSON in prose/fences)."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise
