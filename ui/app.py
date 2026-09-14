import logging
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
import streamlit as st


LOGGER = logging.getLogger(__name__)
load_dotenv()

API_URL_ENV_VAR = "PM_KISAN_API_URL"
REQUEST_TIMEOUT_SECONDS = 30

QUICK_ACTIONS = {
    "Report Civic Issue": "I want to report a civic issue.",
    "Find Government Scheme": "What government schemes are available?",
    "Track Complaint": "I want to track my complaint.",
    "Ask About Scheme": "I have a question about a government scheme.",
}


def _initialize_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "processing" not in st.session_state:
        st.session_state.processing = False


def _request_answer(question: str) -> str:
    api_url = os.getenv(API_URL_ENV_VAR)
    if not api_url:
        raise RuntimeError(f"{API_URL_ENV_VAR} is not configured")

    request = Request(
        api_url,
        data=json.dumps({"question": question}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise RuntimeError(f"API returned status {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"API returned status {error.code}") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("API request failed") from error

    answer = payload.get("answer") if isinstance(payload, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("API response did not contain an answer")
    return answer


def _run_agent_turn(prompt: str) -> None:
    if not prompt or not prompt.strip():
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        response_text = _request_answer(prompt.strip())
    except Exception as error:
        LOGGER.warning("Chatbot request failed: %s", type(error).__name__)
        response_text = (
            "I couldn't process that request right now. "
            "Please try again later."
        )
    st.session_state.messages.append({"role": "assistant", "content": response_text})


def _display_response(content: str) -> None:
    st.markdown(content)
    if "Source:" in content:
        with st.expander("Retrieved source information"):
            source_lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip().startswith("Source:")
            ]
            if source_lines:
                st.write("\n".join(source_lines))
            else:
                st.write("The response includes retrieved source information.")


def main() -> None:
    st.set_page_config(
        page_title="Jan-SahayakAI",
        page_icon="JS",
        layout="centered",
    )
    _initialize_session()

    st.title("Jan-SahayakAI")
    st.caption("Civic assistance and government scheme guidance")

    st.subheader("Quick actions")
    action_columns = st.columns(4)
    for column, (label, prompt) in zip(action_columns, QUICK_ACTIONS.items()):
        if column.button(label, use_container_width=True):
            st.session_state.pending_prompt = prompt
            st.rerun()

    pending_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    typed_prompt = st.chat_input(
        "Describe your question or civic issue",
        disabled=st.session_state.processing,
    )
    prompt = typed_prompt or pending_prompt
    if prompt:
        st.session_state.processing = True
        try:
            with st.spinner("Getting assistance..."):
                _run_agent_turn(prompt)
        finally:
            st.session_state.processing = False

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _display_response(message["content"])
            else:
                st.markdown(message["content"])


if __name__ == "__main__":
    main()