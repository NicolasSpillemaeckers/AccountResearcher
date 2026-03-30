"""Tests for the website researcher agent."""

from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from src.agent import create_website_researcher, research_website


class TestCreateWebsiteResearcher:
    def test_returns_agent_executor(self):
        from langchain.agents import AgentExecutor

        with patch("src.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_cls.return_value = mock_llm
            executor = create_website_researcher()
        assert isinstance(executor, AgentExecutor)

    def test_uses_default_model(self):
        with patch("src.agent.ChatOpenAI") as mock_llm_cls, patch.dict(
            "os.environ", {"OPENAI_MODEL": "gpt-4o-mini"}, clear=False
        ):
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_cls.return_value = mock_llm
            create_website_researcher()
        mock_llm_cls.assert_called_once_with(model="gpt-4o-mini", temperature=0)

    def test_uses_custom_model(self):
        with patch("src.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_cls.return_value = mock_llm
            create_website_researcher(model="gpt-4o")
        mock_llm_cls.assert_called_once_with(model="gpt-4o", temperature=0)

    def test_executor_has_correct_tools(self):
        from src.tools import extract_links, fetch_webpage

        with patch("src.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_cls.return_value = mock_llm
            executor = create_website_researcher()

        tool_names = {t.name for t in executor.tools}
        assert "fetch_webpage" in tool_names
        assert "extract_links" in tool_names


class TestResearchWebsite:
    def test_returns_string_output(self):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": "Research report for example.com"}
        with patch("src.agent.create_website_researcher", return_value=mock_executor):
            result = research_website("https://example.com")
        assert result == "Research report for example.com"

    def test_invokes_with_correct_url(self):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": "Report"}
        with patch("src.agent.create_website_researcher", return_value=mock_executor):
            research_website("https://example.com")
        mock_executor.invoke.assert_called_once_with(
            {"input": "Research the following website: https://example.com"}
        )

    def test_passes_model_to_executor(self):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": "Report"}
        with patch("src.agent.create_website_researcher", return_value=mock_executor) as mock_create:
            research_website("https://example.com", model="gpt-4o")
        mock_create.assert_called_once_with(model="gpt-4o")
