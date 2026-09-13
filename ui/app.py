import logging

import streamlit as st

from agents.jan_sahayak import create_agent


LOGGER = logging.getLogger(__name__)

QUICK_ACTIONS = {
    "Report Civic Issue": "I want to report a civic issue.",
    "Find Government Scheme": "What government schemes are available?",
    "Track Complaint": "I want to track my complaint.",
    "Ask About Scheme": "I have a question about a government scheme.",
}


def _initialize_session() -> None:
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = create_agent()
        except Exception as error:
            LOGGER.warning("Agent initialization failed: %s", type(error).__name__)
            st.session_state.agent = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None


def _run_agent_turn(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        if st.session_state.agent is None:
            raise RuntimeError("Agent is unavailable")
        response = st.session_state.agent(prompt)
        response_text = str(response)
    except Exception as error:
        LOGGER.warning("Agent request failed: %s", type(error).__name__)
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
    typed_prompt = st.chat_input("Describe your question or civic issue")
    prompt = typed_prompt or pending_prompt
    if prompt:
        _run_agent_turn(prompt)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _display_response(message["content"])
            else:
                st.markdown(message["content"])


if __name__ == "__main__":
    main()