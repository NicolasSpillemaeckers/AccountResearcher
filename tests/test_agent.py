"""Tests for the website researcher agent."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from src.agent import create_account_researcher, research_account


class TestCreateAccountResearcher:
    def test_returns_compiled_state_graph(self):
        from langgraph.graph.state import CompiledStateGraph

        with patch("src.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            researcher = create_account_researcher()
        assert isinstance(researcher, CompiledStateGraph)

    def test_uses_default_model(self):
        with patch("src.agent.ChatOpenAI") as mock_llm_cls, patch.dict(
            "os.environ", {"OPENAI_MODEL": "gpt-4o-mini"}, clear=False
        ):
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            create_account_researcher()
        mock_llm_cls.assert_called_once_with(model="gpt-4o-mini", temperature=0)

    def test_uses_custom_model(self):
        with patch("src.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            create_account_researcher(model="gpt-4o")
        mock_llm_cls.assert_called_once_with(model="gpt-4o", temperature=0)

    def test_agent_has_all_tools(self):
        from src.tools import extract_links, fetch_linkedin_page, fetch_webpage

        with patch("src.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            researcher = create_account_researcher()

        tool_names = {node for node in researcher.nodes}
        assert "tools" in tool_names


class TestResearchAccount:
    def _make_mock_agent(self, output_text: str) -> MagicMock:
        ai_message = AIMessage(content=output_text)
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [ai_message]}
        return mock_agent

    def test_returns_string_output(self):
        mock_agent = self._make_mock_agent("Research report for acme.com")
        with patch("src.agent.create_account_researcher", return_value=mock_agent):
            result = research_account(["https://acme.com"])
        assert result == "Research report for acme.com"

    def test_includes_website_source_in_prompt(self):
        mock_agent = self._make_mock_agent("Report")
        with patch("src.agent.create_account_researcher", return_value=mock_agent):
            research_account(["https://acme.com"])
        call_args = mock_agent.invoke.call_args[0][0]
        prompt_text = call_args["messages"][0].content
        assert "https://acme.com" in prompt_text
        assert "website" in prompt_text

    def test_includes_linkedin_source_in_prompt(self):
        mock_agent = self._make_mock_agent("Report")
        with patch("src.agent.create_account_researcher", return_value=mock_agent):
            research_account(["https://www.linkedin.com/company/acme"])
        call_args = mock_agent.invoke.call_args[0][0]
        prompt_text = call_args["messages"][0].content
        assert "linkedin.com" in prompt_text
        assert "LinkedIn" in prompt_text

    def test_includes_both_sources_in_prompt(self):
        mock_agent = self._make_mock_agent("Report")
        with patch("src.agent.create_account_researcher", return_value=mock_agent):
            research_account(
                ["https://acme.com", "https://www.linkedin.com/company/acme"]
            )
        call_args = mock_agent.invoke.call_args[0][0]
        prompt_text = call_args["messages"][0].content
        assert "https://acme.com" in prompt_text
        assert "linkedin.com" in prompt_text

    def test_passes_model_to_researcher(self):
        mock_agent = self._make_mock_agent("Report")
        with patch("src.agent.create_account_researcher", return_value=mock_agent) as mock_create:
            research_account(["https://acme.com"], model="gpt-4o")
        mock_create.assert_called_once_with(model="gpt-4o")

    def test_raises_on_empty_sources(self):
        with pytest.raises(ValueError, match="At least one source"):
            research_account([])

    def test_multiple_sources_invoke_once(self):
        mock_agent = self._make_mock_agent("Report")
        with patch("src.agent.create_account_researcher", return_value=mock_agent):
            research_account(
                ["https://acme.com", "https://www.linkedin.com/company/acme"]
            )
        assert mock_agent.invoke.call_count == 1
