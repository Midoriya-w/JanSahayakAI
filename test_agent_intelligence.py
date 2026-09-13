import json

import tools.knowledge_base as knowledge_base_module
from data.store import MOCK_COMPLAINTS_DB
from agents.jan_sahayak import SYSTEM_PROMPT, create_agent
from tools.civic import create_civic_complaint, identify_department
from tools.complaint import track_complaint
from tools.followup import follow_up_complaint
from tools.knowledge_base import search_scheme_knowledge
from tools.schemes import check_scheme_eligibility, get_scheme_details


def test_agent_has_all_part_12_tools():
    agent = create_agent()

    assert {
        "identify_department",
        "create_civic_complaint",
        "track_complaint",
        "follow_up_complaint",
        "search_schemes",
        "search_scheme_knowledge",
        "check_scheme_eligibility",
        "get_scheme_details",
    } <= set(agent.tool_names)


def test_prompt_defines_tool_routing_and_grounding_rules():
    for rule in (
        "Use identify_department",
        "Use search_schemes",
        "Use search_scheme_knowledge",
        "Use track_complaint",
        "Use follow_up_complaint",
        "Use check_scheme_eligibility",
        "same conversation",
        "READY_FOR_SUBMISSION",
        "do not expose stack traces",
    ):
        assert rule in SYSTEM_PROMPT


def test_missing_complaint_id_fails_gracefully():
    tracking = json.loads(track_complaint("JSA-DOES-NOT-EXIST"))
    follow_up = json.loads(follow_up_complaint("JSA-DOES-NOT-EXIST"))

    assert tracking["status"] == "NOT_FOUND"
    assert follow_up["status"] == "NOT_FOUND"


def test_local_civic_workflow_creates_tracks_and_follows_up():
    MOCK_COMPLAINTS_DB.clear()

    assert "Solid Waste Management" in identify_department(
        "garbage dumping", "main road"
    )
    created = json.loads(
        create_civic_complaint(
            "garbage dumping",
            "near the main road",
            "Garbage is being dumped near homes.",
        )
    )
    complaint_id = created["complaint_id"]

    tracked = json.loads(track_complaint(complaint_id))
    followed_up = json.loads(follow_up_complaint(complaint_id))

    assert tracked["complaint_id"] == complaint_id
    assert tracked["status"] == "READY_FOR_SUBMISSION"
    assert followed_up["complaint_id"] == complaint_id
    assert "demo follow-up" in followed_up["note"]


def test_common_civic_issue_departments():
    assert "Roads Department" in identify_department("large pothole", "college")
    assert "Solid Waste Management" in identify_department("garbage", "main road")
    assert "Electricity Board" in identify_department("streetlight", "market")


def test_complaint_creation_rejects_missing_information():
    MOCK_COMPLAINTS_DB.clear()

    result = json.loads(create_civic_complaint("pothole", "", "Large pothole"))

    assert result["status"] == "INVALID_INPUT"
    assert result["missing_fields"] == ["location"]
    assert MOCK_COMPLAINTS_DB == {}


def test_complaint_creation_prevents_exact_duplicates():
    MOCK_COMPLAINTS_DB.clear()
    first = json.loads(
        create_civic_complaint("streetlight", "Main Street", "Light is broken")
    )
    second = json.loads(
        create_civic_complaint(" STREETLIGHT ", "main street", "light is broken")
    )

    assert first["complaint_id"] == second["complaint_id"]
    assert second["status"] == "DUPLICATE"
    assert len(MOCK_COMPLAINTS_DB) == 1


def test_unknown_civic_issue_uses_general_department():
    assert identify_department("fallen tree blocking a lane", "Park Road") == (
        "General Civic Administration"
    )


def test_missing_scheme_fails_gracefully():
    details = json.loads(get_scheme_details("SCHEME-DOES-NOT-EXIST"))
    eligibility = json.loads(
        check_scheme_eligibility("SCHEME-DOES-NOT-EXIST", {})
    )

    assert "error" in details
    assert "error" in eligibility


def test_rag_without_id_fails_gracefully(monkeypatch):
    monkeypatch.delenv("BEDROCK_KNOWLEDGE_BASE_ID", raising=False)

    assert search_scheme_knowledge("official scholarship documents") == (
        "Knowledge Base is not configured yet."
    )


def test_blank_rag_query_fails_gracefully():
    assert search_scheme_knowledge("   ") == (
        "Please provide a question about an official government scheme document."
    )


def test_rag_aws_failure_fails_gracefully(monkeypatch):
    class FailingClient:
        def retrieve(self, **kwargs):
            raise knowledge_base_module.ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
                "Retrieve",
            )

    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "test-id")
    monkeypatch.setattr(
        knowledge_base_module.boto3,
        "client",
        lambda *args, **kwargs: FailingClient(),
    )

    assert search_scheme_knowledge("What is this scheme?") == (
        "Official document search is currently unavailable. Please try again later."
    )