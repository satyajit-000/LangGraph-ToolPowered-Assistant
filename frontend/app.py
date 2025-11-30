import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

import streamlit as st
import uuid
from backend.langgraph_tool_backend import get_chat_stream, get_chat_history, get_all_unique_threads, get_thread_title, AIMessage, ToolMessage


# ******************************* Utility Functions **********************************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = uuid.uuid4()
    st.session_state['thread_id'] = thread_id 
    st.session_state['message_history'] = []
    add_thread(thread_id)

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

# ****************************** Session set up *************************************

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = get_all_unique_threads() or []

if 'thread_id' not in st.session_state:
    threads = st.session_state['chat_threads']
    st.session_state['thread_id'] = generate_thread_id() if not threads else threads[-1]

if 'message_history' not in st.session_state:
    thread_id = st.session_state['thread_id']
    st.session_state['message_history'] = get_chat_history(thread_id=thread_id) or []

add_thread(st.session_state['thread_id'])

# ***************************** Sidebar UI *****************************************
with st.sidebar:
    st.title('LangGraph Chatbot')
    if st.button('New Chat'):
        reset_chat()
    st.divider()
    st.header('My Conversations')


# ***************************** Main UI *********************************************
st.title('Welcome to LangGraph Chatbot')
st.divider()

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.write(message['content'])


user_input = st.chat_input('Ask me anything')

if user_input:
    # store user input in session state
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })
    # show user input
    with st.chat_message('user'):
        st.write(user_input)

    # get assistant output



    # show assisstant output
    stream = get_chat_stream(user_input, thread_id=st.session_state['thread_id'])
    with st.chat_message('assistant'):
        status_holder = {'box': None}
        # Generator to stream AI message only
        def stream_ai_only():
            for message_chunk, metadata in stream:
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, 'name', 'tool')
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )
                        # with status_holder['box']:
                        status_holder['box'].write(f"🔧 Using `{tool_name}` …")
                        status_holder['box'].write(message_chunk)
                        status_holder['box'].write('---')
                
                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage) and metadata.get('langgraph_node') == 'chat_node':
                    yield message_chunk

        assistant_response = st.write_stream(stream_ai_only())
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
    
    # store assistant output in session state
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': assistant_response
    })

# ***************************** Sidebar UI Chat Rooms *****************************************
with st.sidebar:
    for thread_id in reversed(st.session_state['chat_threads']):
        if st.button(get_thread_title(str(thread_id)) or str(thread_id), key=str(thread_id)):
            st.session_state['thread_id'] = thread_id
            message_history = get_chat_history(thread_id=thread_id)
            st.session_state['message_history'] = message_history
