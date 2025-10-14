import streamlit as st
from rag_backend import chatbot_response, session_chat_histories

st.set_page_config(page_title="AskAI - Human Rights Q&A", page_icon="🗣️", layout="centered")
st.markdown("""
    <style>
        .chat-bubble {
            border-radius: 10px;
            padding: 10px 15px;
            margin: 10px 0;
            max-width: 70%;
            display: inline-block;
        }
        .user-bubble {
            background-color: #DCF8C6;
            align-self: flex-end;
            float: right;
        }
        .bot-bubble {
            background-color: #F1F0F0;
            align-self: flex-start;
            float: left;
        }
        .think {
            color: #888;
            font-style: italic;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🗣️ AskAI - Human Rights Q&A")

# Session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.text_input("Type your message here...", key="user_input", on_change=None)

if st.button("Send") and user_input.strip():
    # Add user message to chat history
    st.session_state.messages.append(("user", user_input))
    # Get bot response
    bot_response = chatbot_response(user_input, session_id="streamlit")
    # Parse <think> and main answer
    if "<think>" in bot_response and "</think>" in bot_response:
        think_content = bot_response.split('<think>')[1].split('</think>')[0].strip()
        answer_content = bot_response.split('</think>')[1].strip()
    else:
        think_content = ""
        answer_content = bot_response
    st.session_state.messages.append(("bot", (think_content, answer_content)))
    st.rerun()

# Render chat history
for who, msg in st.session_state.messages:
    if who == "user":
        st.markdown(f'<div class="chat-bubble user-bubble"><strong>You:</strong> {msg}</div>', unsafe_allow_html=True)
    else:
        think_content, answer_content = msg
        st.markdown(
            f'<div class="chat-bubble bot-bubble">'
            f'<div class="think">🤔 {think_content}</div>'
            f'<strong>AskAI:</strong> {answer_content}'
            f'</div>',
            unsafe_allow_html=True
        )