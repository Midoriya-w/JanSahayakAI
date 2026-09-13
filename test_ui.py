from types import SimpleNamespace

import ui.app as ui_app


class FakeSessionState:
    def __init__(self):
        self.messages = []
        self.agent = None


def test_ui_keeps_agent_context_and_message_history(monkeypatch):
    calls = []

    class FakeAgent:
        def __call__(self, prompt):
            calls.append(prompt)
            return f"response for: {prompt}"

    session = FakeSessionState()
    session.agent = FakeAgent()
    monkeypatch.setattr(ui_app.st, "session_state", session)

    ui_app._run_agent_turn("first message")
    ui_app._run_agent_turn("second message")

    assert calls == ["first message", "second message"]
    assert [message["role"] for message in session.messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert session.messages[-1]["content"] == "response for: second message"


def test_ui_hides_agent_errors(monkeypatch):
    class FailingAgent:
        def __call__(self, prompt):
            raise RuntimeError("secret internal failure")

    session = FakeSessionState()
    session.agent = FailingAgent()
    monkeypatch.setattr(ui_app.st, "session_state", session)

    ui_app._run_agent_turn("test request")

    response = session.messages[-1]["content"]
    assert response == (
        "I couldn't process that request right now. Please try again later."
    )
    assert "secret internal failure" not in response


def test_ui_defines_required_quick_actions():
    assert set(ui_app.QUICK_ACTIONS) == {
        "Report Civic Issue",
        "Find Government Scheme",
        "Track Complaint",
        "Ask About Scheme",
    }
