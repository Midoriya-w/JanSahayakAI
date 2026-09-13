from agents.jan_sahayak import create_agent
from tools.knowledge_base import search_scheme_knowledge
from tools.schemes import search_schemes


def test_knowledge_base_tool_is_safe_without_configuration(monkeypatch):
    monkeypatch.delenv("BEDROCK_KNOWLEDGE_BASE_ID", raising=False)

    assert search_scheme_knowledge("official scholarship documents") == (
        "Knowledge Base is not configured yet."
    )


def test_knowledge_base_tool_is_registered_and_json_search_still_works():
    agent = create_agent()

    assert "search_scheme_knowledge" in agent.tool_names
    assert search_schemes("education", "Andhra Pradesh")