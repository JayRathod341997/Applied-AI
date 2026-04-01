"""Tests for graph builder."""

import pytest
from unittest.mock import MagicMock, patch


class TestBuildGraph:
    @patch("support.graph.nodes._get_llm")
    @patch("support.graph.nodes.KnowledgeBaseSearch")
    @patch("support.graph.nodes.EscalationHandler")
    def test_build_graph_with_memory_saver(self, mock_esc, mock_kb, mock_llm):
        from support.graph.builder import build_graph

        graph = build_graph()
        assert graph is not None

    @patch("support.graph.nodes._get_llm")
    @patch("support.graph.nodes.KnowledgeBaseSearch")
    @patch("support.graph.nodes.EscalationHandler")
    def test_build_graph_with_custom_checkpointer(self, mock_esc, mock_kb, mock_llm):
        from support.graph.builder import build_graph
        from langgraph.checkpoint.memory import MemorySaver

        checkpointer = MemorySaver()
        graph = build_graph(checkpointer=checkpointer)
        assert graph is not None

    def test_build_graph_returns_compiled_graph(self):
        from support.graph.builder import build_graph

        graph = build_graph()
        # Compiled LangGraph has an 'invoke' method
        assert hasattr(graph, "invoke")
