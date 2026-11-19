import pytest
from unittest.mock import patch

from app.llm.picker import pick_llm, OllamaChat
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI


def test_pick_llm_invalid_level():
    with pytest.raises(ValueError, match="level must be"):
        pick_llm("ultra_high")


def test_pick_llm_gemini_explicit():
    with patch("app.llm.picker.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "test_gemini_key"
        mock_settings.GEMINI_MODEL = "gemini-2.5-flash"
        mock_settings.LLM_PROVIDER = "gemini"

        llm = pick_llm("medium", provider="gemini")
        assert isinstance(llm, ChatGoogleGenerativeAI)
        assert llm.model == "gemini-2.5-flash"
        assert llm.temperature == 0.3


def test_pick_llm_groq_explicit():
    with patch("app.llm.picker.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = "test_groq_key"
        mock_settings.GROQ_MODEL = "qwen/qwen3.8-27b"
        mock_settings.LLM_PROVIDER = "groq"

        llm = pick_llm("low", provider="groq")
        assert isinstance(llm, ChatGroq)
        assert llm.model_name == "qwen/qwen3.8-27b"
        assert llm.temperature == 0.1


def test_pick_llm_ollama_explicit():
    with patch("app.llm.picker.settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.LLM_PROVIDER = "ollama"

        llm = pick_llm("high", provider="ollama")
        assert isinstance(llm, OllamaChat)
        assert llm.temperature == 0.5


def test_pick_llm_auto_prefers_gemini_when_key_present():
    with patch("app.llm.picker.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "test_gemini_key"
        mock_settings.GEMINI_MODEL = "gemini-2.5-flash"
        mock_settings.GROQ_API_KEY = "test_groq_key"
        mock_settings.LLM_PROVIDER = "auto"

        llm = pick_llm("medium")
        assert isinstance(llm, ChatGoogleGenerativeAI)


def test_pick_llm_auto_falls_back_to_groq_when_no_gemini():
    with patch("app.llm.picker.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.GROQ_API_KEY = "test_groq_key"
        mock_settings.GROQ_MODEL = "qwen/qwen3.8-27b"
        mock_settings.LLM_PROVIDER = "auto"

        llm = pick_llm("medium")
        assert isinstance(llm, ChatGroq)


def test_pick_llm_auto_falls_back_to_ollama_when_no_cloud_keys():
    with patch("app.llm.picker.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.GROQ_API_KEY = ""
        mock_settings.LLM_PROVIDER = "auto"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"

        llm = pick_llm("medium")
        assert isinstance(llm, OllamaChat)
