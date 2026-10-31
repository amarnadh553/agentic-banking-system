"""
Simple chat UI for the Fictional Bank Bot. Shows only the answer, not the trace.

1. Start the API:      uvicorn fictional_bank.api.main:app
2. Start this app:     streamlit run streamlit_app.py
"""
import os

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/banking/ask")
TIMEOUT_SECONDS = 180          # gpt-5 models can be slow, so give the API enough time
EXAMPLES = [
    "Show C003's name, last 3 transactions and pending requests",
    "What is the total balance for C004?",
    "Does C007 have any pending service requests?",
]

st.set_page_config(page_title="Fictional Bank Assistant", page_icon="🏦")
st.title("🏦 Fictional Bank Assistant")
st.caption("Ask about customers, accounts, transactions and service requests. All data is fictional.")

# ---------------- sidebar ----------------
with st.sidebar:
    api_url = st.text_input("API URL", value=DEFAULT_API_URL)
    st.markdown("**Try an example**")
    example = None
    for text in EXAMPLES:
        if st.button(text, use_container_width=True):
            example = text
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------- chat history ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def ask_api(question: str) -> str:
    """Send the question to the API and return only the answer text."""
    try:
        reply = requests.post(api_url, json={"question": question, "keep_formatting": True}, timeout=TIMEOUT_SECONDS)
        reply.raise_for_status()
        return reply.json().get("response", "No response received.")
    except requests.exceptions.ConnectionError:
        return "Cannot reach the API. Is it running? Start it with `uvicorn fictional_bank.main:app`."
    except requests.exceptions.Timeout:
        return f"The API took longer than {TIMEOUT_SECONDS} seconds. Please try again."
    except requests.exceptions.HTTPError as exc:
        return f"The API returned an error: {exc.response.status_code}. Please try again."
    except Exception as exc:
        return f"Something went wrong: {exc}"


# ---------------- new question ----------------
question = st.chat_input("Ask a banking question, for example: What accounts does C001 have?") or example
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask_api(question)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})