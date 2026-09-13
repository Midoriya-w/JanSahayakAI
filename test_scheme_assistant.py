import json

import tools.knowledge_base as knowledge_base_module
from agents.jan_sahayak import SYSTEM_PROMPT, create_agent
from tools.knowledge_base import search_scheme_knowledge
from tools.schemes import (
    check_scheme_eligibility,
    get_scheme_details,
    search_schemes,
)


def test_scheme_discovery_uses_structured_json():
    results = json.loads(search_schemes("education", None))

    assert len(results) == 1
    assert results[0]["scheme_id"] == "SCH001"
    assert results[0]["category"] == "education"


def test_scheme_details_accepts_name_and_returns_full_record():
    details = json.loads(get_scheme_details("PM-KISAN"))

    assert details["scheme_id"] == "SCH002"
    assert details["name"].startswith("Pradhan Mantri Kisan")
    assert details["benefits"]
    assert details["documents"]
    assert details["important_note"]


def test_eligibility_is_preliminary_and_uses_canonical_id():
    result = json.loads(
        check_scheme_eligibility(
            "PM-KISAN",
            {"state": "Andhra Pradesh", "landholding": "unknown"},
        )
    )

    assert result["scheme_id"] == "SCH002"
    assert result["preliminary_status"] == "MORE_INFORMATION_NEEDED"
    assert result["verification_required"] is True
    assert "official eligibility decision" in result["note"]


def test_unknown_scheme_returns_useful_errors():
    details = json.loads(get_scheme_details("UNKNOWN-SCHEME"))
    eligibility = json.loads(check_scheme_eligibility("UNKNOWN-SCHEME", {}))

    assert "error" in details
    assert "error" in eligibility


def test_empty_scheme_identifier_fails_gracefully():
    assert "error" in json.loads(get_scheme_details(""))
    assert "error" in json.loads(check_scheme_eligibility("", {}))


def test_rag_without_id_is_safe(monkeypatch):
    monkeypatch.delenv("BEDROCK_KNOWLEDGE_BASE_ID", raising=False)

    assert search_scheme_knowledge("official scheme conditions") == (
        "Knowledge Base is not configured yet."
    )


def test_rag_no_results_is_clear(monkeypatch):
    class EmptyClient:
        def retrieve(self, **kwargs):
            return {"retrievalResults": []}

    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "test-id")
    monkeypatch.setattr(
        knowledge_base_module.boto3,
        "client",
        lambda *args, **kwargs: EmptyClient(),
    )

    assert search_scheme_knowledge("official scholarship conditions") == (
        "No relevant information was found in the official documents."
    )


def test_rag_preserves_returned_source(monkeypatch):
    class SourceClient:
        def retrieve(self, **kwargs):
            return {
                "retrievalResults": [
                    {
                        "content": {"text": "Required documents are listed here."},
                        "location": {"s3Location": {"uri": "s3://official-doc.pdf"}},
                    }
                ]
            }

    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "test-id")
    monkeypatch.setattr(
        knowledge_base_module.boto3,
        "client",
        lambda *args, **kwargs: SourceClient(),
    )

    result = search_scheme_knowledge("What documents are required?")

    assert "Required documents are listed here." in result
    assert "s3://official-doc.pdf" in result


def test_agent_has_part_14_tools_and_routing_rules():
    agent = create_agent()

    assert {
        "search_schemes",
        "get_scheme_details",
        "check_scheme_eligibility",
        "search_scheme_knowledge",
    } <= set(agent.tool_names)
    for rule in (
        "Do not use RAG for simple discovery",
        "Use search_scheme_knowledge",
        "Use get_scheme_details",
        "Use check_scheme_eligibility",
        "same conversation",
        "official-document retrieval",
    ):
        assert rule in SYSTEM_PROMPT
