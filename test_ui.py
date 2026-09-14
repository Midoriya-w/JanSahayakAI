import ui.app as ui_app


class FakeSessionState:
    def __init__(self):
        self.messages = []
        self.processing = False


def test_ui_sends_questions_and_keeps_message_history(monkeypatch):
    calls = []

    def fake_request_answer(prompt):
        calls.append(prompt)
        return f"response for: {prompt}"

    session = FakeSessionState()
    monkeypatch.setattr(ui_app.st, "session_state", session)
    monkeypatch.setattr(ui_app, "_request_answer", fake_request_answer)

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


def test_ui_hides_api_errors(monkeypatch):
    def failing_request_answer(prompt):
        raise RuntimeError("secret internal failure")

    session = FakeSessionState()
    monkeypatch.setattr(ui_app.st, "session_state", session)
    monkeypatch.setattr(ui_app, "_request_answer", failing_request_answer)

    ui_app._run_agent_turn("test request")

    response = session.messages[-1]["content"]
    assert response == (
        "I couldn't process that request right now. Please try again later."
    )
    assert "secret internal failure" not in response


def test_ui_does_not_send_empty_messages(monkeypatch):
    session = FakeSessionState()
    monkeypatch.setattr(ui_app.st, "session_state", session)
    request_called = False

    def fake_request_answer(prompt):
        nonlocal request_called
        request_called = True
        return "unexpected response"

    monkeypatch.setattr(ui_app, "_request_answer", fake_request_answer)

    ui_app._run_agent_turn("   ")

    assert session.messages == []
    assert request_called is False


def test_request_answer_posts_json_and_returns_answer(monkeypatch):
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"answer":"PM-Kisan provides farmer income support."}'

    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("PM_KISAN_API_URL", "https://example.test/PMKisanChatbot")
    monkeypatch.setattr(ui_app, "urlopen", fake_urlopen)

    answer = ui_app._request_answer("What is PM-Kisan?")

    assert answer == "PM-Kisan provides farmer income support."
    assert captured["request"].method == "POST"
    assert captured["request"].get_header("Content-type") == "application/json"
    assert captured["request"].data == b'{"question": "What is PM-Kisan?"}'
    assert captured["timeout"] == ui_app.REQUEST_TIMEOUT_SECONDS


def test_request_answer_rejects_missing_answer(monkeypatch):
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"message":"no answer"}'

    monkeypatch.setenv("PM_KISAN_API_URL", "https://example.test/PMKisanChatbot")
    monkeypatch.setattr(ui_app, "urlopen", lambda request, timeout: FakeResponse())

    try:
        ui_app._request_answer("What is PM-Kisan?")
    except RuntimeError as error:
        assert str(error) == "API response did not contain an answer"
    else:
        raise AssertionError("Expected missing answer to fail")


def test_request_answer_rejects_non_success_status(monkeypatch):
    class FakeResponse:
        status = 503

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setenv("PM_KISAN_API_URL", "https://example.test/PMKisanChatbot")
    monkeypatch.setattr(ui_app, "urlopen", lambda request, timeout: FakeResponse())

    try:
        ui_app._request_answer("What is PM-Kisan?")
    except RuntimeError as error:
        assert str(error) == "API returned status 503"
    else:
        raise AssertionError("Expected non-success status to fail")


def test_ui_defines_required_quick_actions():
    assert set(ui_app.QUICK_ACTIONS) == {
        "Report Civic Issue",
        "Find Government Scheme",
        "Track Complaint",
        "Ask About Scheme",
    }
