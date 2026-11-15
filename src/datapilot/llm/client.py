from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from datapilot.config.settings import get_settings


T = TypeVar("T", bound=BaseModel)


class LLMClientError(Exception):
    """Raised when the local LLM request fails."""


class LLMClient:

    def __init__(self):
        settings = get_settings()

        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

        self.timeout = 120.0

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        schema = response_model.model_json_schema()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a reliable AI assistant. "
                        "Follow the supplied JSON schema exactly. "
                        "Return only information supported by the request."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "format": schema,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            content = response.json()["message"]["content"]

            return response_model.model_validate_json(content)

        except httpx.HTTPError as exc:
            raise LLMClientError(
                f"Ollama request failed: {exc}"
            ) from exc

        except (KeyError, ValueError) as exc:
            raise LLMClientError(
                f"Invalid response returned by Ollama: {exc}"
            ) from exc

        except ValidationError as exc:
            raise LLMClientError(
                f"LLM output failed Pydantic validation: {exc}"
            ) from exc