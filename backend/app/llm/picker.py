import logging
from typing import Any, Union

import httpx
from langchain_groq import ChatGroq

from app.config.settings import settings

logger = logging.getLogger(__name__)


class OllamaResponse:
    """Simple container matching LangChain-like response with a .content attribute."""

    def __init__(self, content: str):
        self.content = content

    def __str__(self) -> str:
        return self.content


class OllamaChat:
    """Pure-Python client for local Ollama without heavy DLL dependencies."""

    def __init__(self, model: str = "qwen2.5-coder:3b", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")

    def invoke(self, prompt: Any) -> OllamaResponse:
        """Send prompt to Ollama and return response with .content string.

        Supports strings, ChatPromptValue, PromptValue, or lists of BaseMessage/dicts.
        """
        # Convert ChatPromptValue or PromptValue into a list of messages if applicable
        if hasattr(prompt, "to_messages"):
            prompt = prompt.to_messages()

        if isinstance(prompt, list):
            messages = []
            for item in prompt:
                if hasattr(item, "content"):
                    msg_type = getattr(item, "type", "user")
                    if msg_type == "human":
                        role = "user"
                    elif msg_type == "ai":
                        role = "assistant"
                    elif msg_type == "system":
                        role = "system"
                    else:
                        role = getattr(item, "role", "user")
                    messages.append({"role": role, "content": str(item.content)})
                elif isinstance(item, dict):
                    messages.append(item)
                else:
                    messages.append({"role": "user", "content": str(item)})

            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": self.temperature},
                },
                timeout=60.0,
            )
            response.raise_for_status()
            text = response.json().get("message", {}).get("content", "")
            return OllamaResponse(content=text)

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": str(prompt),
                "stream": False,
                "options": {"temperature": self.temperature},
            },
            timeout=60.0,
        )
        response.raise_for_status()
        text = response.json().get("response", "")
        return OllamaResponse(content=text)


def pick_llm(level: str = "medium") -> Union[ChatGroq, OllamaChat]:
    """Pick LLM instance with temperature tuned for task complexity.

    If GROQ_API_KEY is configured in .env, returns high-speed ChatGroq.
    Otherwise, falls back to local Ollama.
    """
    level = level.strip().lower()

    # Temperature mapping based on reasoning level
    temp_map = {
        "low": 0.1,
        "medium": 0.3,
        "high": 0.5,
    }
    if level not in temp_map:
        raise ValueError("level must be 'low', 'medium', or 'high'")

    temperature = temp_map[level]

    # Prioritize Groq Cloud if API key is provided
    groq_api_key = settings.GROQ_API_KEY.strip()
    if groq_api_key:
        model_name = settings.GROQ_MODEL.strip() or "qwen/qwen3.8-27b"
        return ChatGroq(
            model_name=model_name,
            groq_api_key=groq_api_key,
            temperature=temperature,
        )

    # Fallback to local Ollama
    return OllamaChat(temperature=temperature)
