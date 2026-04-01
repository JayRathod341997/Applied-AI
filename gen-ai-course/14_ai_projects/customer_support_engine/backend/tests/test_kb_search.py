"""Tests for KnowledgeBaseSearch tool."""

import pytest
from unittest.mock import MagicMock, patch

from support.tools.kb_search import KnowledgeBaseSearch


@pytest.fixture
def mock_search_client():
    with patch("support.tools.kb_search.SearchClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


class TestKnowledgeBaseSearch:
    def test_search_returns_content_chunks(self, mock_search_client):
        mock_search_client.search.return_value = [
            {"content": "How to reset password"},
            {"content": "Billing FAQ"},
        ]

        kb = KnowledgeBaseSearch(
            endpoint="https://fake.search.windows.net",
            api_key="fake-key",
            index_name="kb-index",
        )
        results = kb.search("reset password", top_k=5)

        assert results == ["How to reset password", "Billing FAQ"]

    def test_search_supports_chunk_field_name(self, mock_search_client):
        mock_search_client.search.return_value = [
            {"chunk": "chunk content here"},
        ]

        kb = KnowledgeBaseSearch(
            endpoint="https://fake.search.windows.net",
            api_key="fake-key",
            index_name="kb-index",
        )
        results = kb.search("some query")

        assert results == ["chunk content here"]

    def test_search_skips_empty_content(self, mock_search_client):
        mock_search_client.search.return_value = [
            {"content": ""},
            {"content": "valid content"},
            {"content": None},
        ]

        kb = KnowledgeBaseSearch(
            endpoint="https://fake.search.windows.net",
            api_key="fake-key",
            index_name="kb-index",
        )
        results = kb.search("query")

        assert results == ["valid content"]

    def test_search_returns_empty_for_blank_query(self, mock_search_client):
        kb = KnowledgeBaseSearch(
            endpoint="https://fake.search.windows.net",
            api_key="fake-key",
            index_name="kb-index",
        )
        results = kb.search("   ")

        assert results == []
        mock_search_client.search.assert_not_called()

    def test_search_returns_empty_on_exception(self, mock_search_client):
        mock_search_client.search.side_effect = Exception("Connection error")

        kb = KnowledgeBaseSearch(
            endpoint="https://fake.search.windows.net",
            api_key="fake-key",
            index_name="kb-index",
        )
        results = kb.search("some query")

        assert results == []

    def test_search_passes_top_k_to_client(self, mock_search_client):
        mock_search_client.search.return_value = []

        kb = KnowledgeBaseSearch(
            endpoint="https://fake.search.windows.net",
            api_key="fake-key",
            index_name="kb-index",
        )
        kb.search("test", top_k=3)

        call_kwargs = mock_search_client.search.call_args[1]
        assert call_kwargs["top"] == 3
