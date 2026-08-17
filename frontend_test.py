import streamlit as st
import requests
import json

# Configuration
API_URL = "http://127.0.0.1:8000/chat"  # Your FastAPI endpoint
API_KEY = "sogqgqjAumSW_iSFkbuNElE0BCuhDXuhSTUefntR9fo"  # Replace if custom

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Streamlit UI
st.title("RAG Chatbot Tester")
st.caption("Test conversation flow, proactive questions, and email triggers.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your message..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare payload
    payload = {"query": prompt}
    if st.session_state.session_id:
        payload["session_id"] = st.session_state.session_id

    # Send request to FastAPI
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()

        # Append assistant response
        st.session_state.messages.append({"role": "assistant", "content": data["answer"]})
        with st.chat_message("assistant"):
            st.markdown(data["answer"])

        # Update session_id if new
        if not st.session_state.session_id:
            st.session_state.session_id = data["session_id"]
            st.sidebar.success(f"New session ID: {st.session_state.session_id}")

    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")

# Sidebar for controls
st.sidebar.title("Testing Tools")
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.session_id = None
    st.rerun()

st.sidebar.markdown("**Monitor Emails**: After chats, check your recipient inbox for summaries/details.")