"""Reusable Groq HTTP client with a shared requests.Session.
This wrapper mimics the subset of the official Groq SDK used by the
application (client.chat.completions.create). It keeps a single
requests.Session for the lifetime of the process, re‑using TCP
connections and the Authorization header.
"""

import json
from typing import Any, Dict, List, Optional

import requests


class _GroqResponseChoice:
    def __init__(self, content: str):
        self.message = type("Message", (), {"content": content})


class _GroqResponseResult:
    def __init__(self, data: Dict[str, Any]):
        # The Groq API returns a list of choices; we expose them similarly.
        self.choices: List[_GroqResponseChoice] = []
        for choice in data.get("choices", []):
            message = choice.get("message", {})
            content = message.get("content", "")
            self.choices.append(_GroqResponseChoice(content))


class GroqClient:
    """Thin wrapper around the Groq HTTP endpoint.

    The class holds a **single** ``requests.Session`` shared across all
    instances, ensuring connection reuse. It implements the minimal API
    surface required by the existing ``ai_service`` module.
    """

    _session: Optional[requests.Session] = None
    _base_url = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, max_retries: int = 2, timeout: float = 20.0):
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        if GroqClient._session is None:
            s = requests.Session()
            s.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            GroqClient._session = s

    @property
    def session(self) -> requests.Session:
        return GroqClient._session  # type: ignore[return-value]

    class _Chat:
        def __init__(self, client: "GroqClient"):
            self._client = client
            # expose ``completions`` attribute that has a ``create`` method
            self.completions = self

        def create(
            self,
            *,
            model: str,
            messages: List[Dict[str, Any]],
            temperature: float,
            max_tokens: int,
            response_format: Optional[Dict[str, Any]] = None,
        ) -> _GroqResponseResult:
            payload: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                payload["response_format"] = response_format
            url = f"{self._client._base_url}/chat/completions"
            resp = self._client.session.post(url, json=payload, timeout=self._client.timeout)
            resp.raise_for_status()
            data = resp.json()
            return _GroqResponseResult(data)

    @property
    def chat(self) -> "GroqClient._Chat":
        return self._Chat(self)
