import sys, os, uuid
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
import streamlit as st
from backend.langgraph_tool_backend import (
    get_chat_stream,
    get_chat_history,
    get_user_rooms,
    get_thread_title,
    get_user_details,
    AIMessage,
    ToolMessage
)
from backend.auth import sign_up, sign_in, create_reset_token, reset_password
from backend.db import init_db

# ---------------------- INIT DB ----------------------
init_db()  # ensure tables exist

# ---------------------- SESSION ----------------------
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

if 'user_details' not in st.session_state:
    st.session_state['user_details'] = None

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = None

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'auth_page_type' not in st.session_state:
    st.session_state['auth_page_type'] = 'sign_in' 

if 'is_authenticated' not in st.session_state:
    st.session_state['is_authenticated'] = False

# ---------------------- AUTH UI ----------------------
def login_ui():
    st.title('Welcome to LangGraph Chatbot')
    match(st.session_state['auth_page_type']):
        case 'sign_in':
            signin_ui()
        case 'sign_up':
            signup_ui()
        case 'forgot_password':
            forgot_password_ui()
        case _:
            st.session_state['auth_page_type'] = 'sign_in'
            st.rerun()

    extra_buttons()

def extra_buttons():
    with st.container(horizontal=True, horizontal_alignment='distribute'):
        if st.session_state['auth_page_type'] != 'sign_up' and not st.session_state['is_authenticated']:
            create_new()
        if st.session_state['auth_page_type'] != 'sign_in':
            already_have_account()
        if st.session_state['auth_page_type'] != 'forgot_password':
            forgot_password()
        if st.session_state['auth_page_type'] == 'forgot_password' and st.session_state['is_authenticated']:
            change_email()


def create_new():
    if st.button('Create new account', type='tertiary', icon=":material/person_add:"):
        st.session_state['auth_page_type'] = 'sign_up'
        st.rerun()

def already_have_account():
    if st.button('Already have an account', type='tertiary', icon=":material/login:"):
        st.session_state['auth_page_type'] = 'sign_in'
        st.rerun()

def forgot_password():
    if st.button('Forgot password', type='tertiary', icon=":material/password_2_off:"):
        st.session_state['auth_page_type'] = 'forgot_password'
        st.rerun()

def change_email():
    if st.button('Change the email', type='tertiary', icon=":material/email:"):
        st.session_state['is_authenticated'] = False
        st.session_state['password_reset_token'] = None

    btn_label = 'Create new account' if st.session_state['auth_page_type'] == 'sign_in' else 'Already have an account'
    icon = ":material/person_add:" if btn_label == 'Create new account'  else ':material/login:'
    with st.container(horizontal=True, horizontal_alignment='distribute'):
        if st.button(btn_label, type='tertiary', icon=icon):
            auth_page_type = st.session_state['auth_page_type']
            st.session_state['auth_page_type'] = 'sign_up' if auth_page_type == 'sign_in' else 'sign_in'
            st.rerun()
        extra_btn_label = 'Change the email' if st.session_state.get('is_authenticated', False) and st.session_state['auth_page_type'] == 'forgot_password' else 'Forgot password'
        extra_icon = ":material/password_2_off:" if extra_btn_label == 'Forgot password' else ':material/mail:'

        if (st.session_state['auth_page_type'] != 'forgot_password' 
            or st.session_state.get('is_authenticated', False)) and \
            st.button(extra_btn_label, type='tertiary', icon=extra_icon):
            if st.session_state['auth_page_type'] != 'forgot_password':
                st.session_state['auth_page_type'] = 'forgot_password'
            elif st.session_state.get('is_authenticated', False):
                st.session_state['is_authenticated'] = False
                st.session_state['password_reset_token'] = None

            st.rerun()

def signin_ui():
    st.subheader('Sign In')
    with st.form(enter_to_submit=True, key='signin'):
        email = st.text_input('Email :red[*]', key='login_email')
        password = st.text_input('Password :red[*]', type='password', key='login_pass')
        global col2
        if st.form_submit_button('Sign In', type='primary', icon=":material/login:"):
            try:
                if not email or not password:
                    raise ValueError('Email & password fields are required')
                user_id = sign_in(email, password)
                st.session_state['user_id'] = user_id
                st.success('Logged in successfully!')
                st.session_state['celebrate'] = True
                st.rerun()
            except Exception as e:
                st.error(str(e))

def signup_ui():
    st.subheader('Sign Up')
    with st.form(enter_to_submit=True, key='signup'):
        first_name = st.text_input('First Name :red[*]', placeholder='Enter your First Name', key='first_name')
        last_name = st.text_input('Last Name', key='last_name', placeholder='Enter your Last Name',)
        new_email = st.text_input('Email :red[*]', placeholder='Enter your email address', key='signup_email')
        new_pass = st.text_input('Password :red[*]', placeholder='Enter your password', type='password', key='signup_pass')
        confirm_pass = st.text_input('Confirm Password :red[*]', placeholder='Confirm password', type='password', key='confirm_pass')
        if st.form_submit_button('Sign Up', type='primary', icon=":material/person_add:"):
            try:
                if not new_email or not new_pass:
                    raise ValueError('Email & password fields are required')
                if new_pass != confirm_pass:
                    raise ValueError('Passward didn\'t match')
                user_id = sign_up(new_email, new_pass, first_name, last_name)
                st.session_state['user_id'] = user_id
                st.session_state['celebrate'] = True
                st.success('Account created and logged in!')
                st.rerun()
            except Exception as e:
                st.error(str(e))

def forgot_password_ui():
    st.subheader('Forgot password')
    is_authenticated = st.session_state.get('is_authenticated', False)
    with st.form(enter_to_submit=True, key='forgot_password'):
        email = st.text_input('Email :red[*]', placeholder='Enter your email address' ,key='authenticate_email', disabled=is_authenticated)
        if is_authenticated:
            new_pass = st.text_input('Password :red[*]', placeholder='Enter your password', type='password', key='update_pass')
            confirm_pass = st.text_input('Confirm Password :red[*]', placeholder='Confirm password', type='password', key='confirm_update_pass')
        btn_label = 'Authenticate' if not is_authenticated else 'Update password'
        if st.form_submit_button(btn_label, type='primary'):
            try:
                if not st.session_state['is_authenticated']:
                    if not email:
                        raise ValueError('Email field is required')
                    reset_token = create_reset_token(email=email)
                    st.session_state['password_reset_token'] = reset_token
                    st.session_state['is_authenticated'] = True
                    st.rerun()
                else:
                    if not new_pass:
                        raise ValueError('Password field is required')
                    if new_pass != confirm_pass:
                        raise ValueError('Passward didn\'t match')
                    reset_password(token=st.session_state['password_reset_token'], new_password=new_pass)
                    st.session_state['is_authenticated'] = False
                    st.session_state['password_reset_token'] = None
                    st.session_state['auth_page_type'] = 'sign_in'
                    st.success('Password updated successfully')
                    st.rerun()
            except Exception as e:
                st.error(str(e))

if st.session_state['user_id'] is None:
    login_ui()
    st.stop()  # stop here until user logs in

user_id = st.session_state['user_id']
assistant_name = os.getenv('ASSISTANT_NAME')

if not st.session_state['user_details']:
    global user_details
    user_details = get_user_details(user_id)

if st.session_state.get('celebrate'):
    st.balloons()
    st.session_state['celebrate'] = None

# ---------------------- UTILS ----------------------
def generate_thread_id():
    return uuid.uuid4().hex

def reset_chat():
    # Prevent creating chatroom if one empty chatroom is already created
    if not st.session_state['message_history']:
        return
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_thread(thread_id)

def add_thread(thread_id):
    if thread_id not in st.session_state['thread_ids']:
        st.session_state['chat_threads'].insert(0, {'thread_id': thread_id, 'thread_title': None})
        st.session_state['thread_ids'].add(thread_id)

# ---------------------- LOAD USER THREADS ----------------------
st.session_state['chat_threads'] = get_user_rooms(user_id)

if 'thread_ids' not in st.session_state:
    st.session_state['thread_ids'] = {t['thread_id'] for t in st.session_state['chat_threads']}


if 'thread_id' not in st.session_state or st.session_state['thread_id'] is None:
    threads = st.session_state['chat_threads']
    st.session_state['thread_id'] = threads[0]['thread_id'] if threads else generate_thread_id()

st.session_state['message_history'] = get_chat_history(
    st.session_state['thread_id'], user_id
) or []

add_thread(st.session_state['thread_id'])

# ---------------------- SIDEBAR ----------------------
with st.sidebar:
    st.title('LangGraph Chatbot')
    with st.container(horizontal=True, horizontal_alignment='distribute'):
        if st.button('Logout', icon=":material/logout:"):
            st.session_state['user_id'] = None
            st.session_state['user_details'] = None
            st.rerun()
        if st.button('New Chat', icon=":material/edit_square:"):
            reset_chat()
    # st.link_button(f":blue[{user_details.get('email')}]",url=f"/mailto:{user_details.get('email')}", type='tertiary' )
    # st.divider()

# ---------------------- CHAT UI ----------------------
st.title(f"👋 Hello {user_details.get('first_name') or 'there'}!")

st.subheader("Welcome to the Chat Room")
st.caption(f"You’re chatting with {f':green[**{assistant_name}**],' if assistant_name else ''} your AI assistant — ready to help anytime 😊")

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
    try:
        # stream assistant response
        # show assisstant output
        stream = get_chat_stream(user_input, thread_id=st.session_state['thread_id'], user_id=user_id)
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
            if status_holder['box'] is not None:
                status_holder['box'].update(
                    label='✅ Tool finished', state='complete', expanded=False
                )


        # store assistant output in session state
        st.session_state['message_history'].append({
            'role': 'assistant',
            'content': assistant_response
        })
    except Exception as e:
        st.error(str(e))

def stripped(s: str, max_len = 30):
    if len(s.strip()) <= max_len + 1:
        return False, s.strip()
    return True, s.strip()[:(max_len + 1)] + '...'

# ***************************** Sidebar UI Chat Rooms *****************************************
with st.sidebar:
    with st.container(border=True):
        st.header('My Conversations')
        for thread in st.session_state['chat_threads']:
            thread_id, thread_title =  thread['thread_id'], thread['thread_title']
            thread_title = thread_title or get_thread_title(thread_id, user_id)
            if not thread_title:
                continue
            is_stripped, stripped_title = stripped(thread_title)
            if st.button(stripped_title, help=thread_title if is_stripped else None, key=str(thread_id), use_container_width=True, type='primary' if thread_id == st.session_state['thread_id'] else 'secondary'):
                st.session_state['thread_id'] = thread_id
                message_history = get_chat_history(thread_id=thread_id, user_id=user_id)
                st.session_state['message_history'] = message_history
                st.rerun()
