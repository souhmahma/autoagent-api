import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch, MagicMock
from app.agent.tools.summarizer import summarize_text


class TestSummarizerFallback:

    @pytest.mark.asyncio
    async def test_short_text_returned_as_is(self):
        text = "Hello world."
        result = await summarize_text(text)
        assert result == text.strip()

    @pytest.mark.asyncio
    async def test_empty_text(self):
        result = await summarize_text("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_whitespace_only(self):
        result = await summarize_text("   ")
        assert result == ""

    @pytest.mark.asyncio
    async def test_long_text_truncated_to_sentences(self):
        text = (
            "Artificial intelligence is transforming the world. "
            "Machine learning allows computers to learn from data. "
            "Deep learning uses neural networks with many layers. "
            "Natural language processing enables text understanding. "
            "Computer vision allows machines to interpret images."
        )
        result = await summarize_text(text, max_sentences=2)
        assert len(result) > 0
        assert len(result) < len(text)

    @pytest.mark.asyncio
    async def test_returns_string(self):
        result = await summarize_text("Some text here for testing purposes only.")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_max_sentences_respected(self):
        sentences = [f"Sentence number {i}" for i in range(10)]
        text = ". ".join(sentences) + "."
        result = await summarize_text(text, max_sentences=1)
        assert len(result) > 0
        assert len(result) < len(text)


class TestSummarizerWithMockedGemini:

    @pytest.mark.asyncio
    async def test_uses_gemini_when_key_present(self):
        mock_response = MagicMock()
        mock_response.text = "This is a Gemini summary."

        with patch("app.agent.tools.summarizer.settings") as mock_settings, \
             patch("google.generativeai.GenerativeModel") as mock_model_cls:

            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model_cls.return_value = mock_instance

            result = await summarize_text("Long text " * 20)
            assert result == "This is a Gemini summary."

    @pytest.mark.asyncio
    async def test_falls_back_on_gemini_error(self):
        with patch("app.agent.tools.summarizer.settings") as mock_settings, \
             patch("google.generativeai.GenerativeModel") as mock_model_cls:

            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_instance = MagicMock()
            mock_instance.generate_content.side_effect = Exception("API error")
            mock_model_cls.return_value = mock_instance

            text = "First sentence. Second sentence. Third sentence. Fourth sentence."
            result = await summarize_text(text, max_sentences=2)
            assert isinstance(result, str)
            assert len(result) > 0
