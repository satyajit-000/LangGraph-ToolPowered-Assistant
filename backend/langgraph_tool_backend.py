from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from .tools import *
from .db import *
from typing import TypedDict, Annotated, Generator
from dotenv import load_dotenv
import os

load_dotenv()

# --------------
# 1. LLMs
# --------------
llm = ChatOpenAI()
llm_title = ChatOpenAI()


# make tool lists

tools = [
    search_tool, 
    google_search,
    scrape_webpage,
    calculator, 
    get_stock_price, 
    current_datetime,
    get_geocoding, 
    get_weather, 
    search_youtube,
    advanced_calculator, 
    mathematical_conversions, 
    calculate_bmi, 
]

llm_with_tools = llm.bind_tools(tools)

# -------------
# 3. State
# -------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# --------------
# 4. Nodes
# --------------
def chat_node(state: ChatState) -> ChatState:
    # take user querry from state
    messages = state['messages']
    if not isinstance(messages[0], SystemMessage):
        assistant_name = os.getenv('ASSISTANT_NAME') or ''
        messages.insert(0, SystemMessage(
                content=(
                    f"You are {assistant_name}, an intelligent, polite, and professional AI assistant. "
                    "You help users by providing clear, accurate, and concise answers. "
                    "If a question is ambiguous, ask for clarification. "
                    "When explaining technical topics, be structured and practical. "
                    "Do not hallucinate; if you are unsure, say so. "
                    "Maintain a friendly and respectful tone at all times."
                )
            )
        )

    # send to llm_with_tools
    response = llm_with_tools.invoke(messages)

    # response store state
    return {'messages': [response]}

def check_title_condition(state: ChatState, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"]["user_id"]

    title = get_thread_title(thread_id, user_id)
    return "generate_title" if title is None else "skip_title"

def generate_title_node(state: ChatState, config) -> ChatState:
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"]["user_id"]

    initial_chats = state["messages"][:4]
    prompt = [SystemMessage("""
You are generating a chatroom title.
Rules:
1. Output EXACTLY one line.
2. Length: 3 to 6 words ONLY.
3. Use plain English words.
4. Do NOT use quotes, emojis, punctuation (except hyphen).
5. Do NOT add explanations or extra text.
6. Title should be based on the question asked by user
6. If unsure, generate a neutral descriptive title related to the question asked by user.
Return only the title text.
"""
    ),
        *initial_chats
    ]

    title = llm_title.invoke(prompt).content.strip()
    cleaned = ''.join(c for c in title if c.isalnum() or c in {' ', '-', '?'})
    set_thread_title(thread_id, user_id, cleaned.strip())

    return state

tool_node = ToolNode(tools)

# -------------
# 5. SqlLite
# -------------

init_db()


checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)

graph.add_node("generate_title", generate_title_node)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

# # 1️⃣ Conditional routing for titles
graph.add_conditional_edges(
    START,
    check_title_condition,
    {
        "generate_title": "generate_title",
        "skip_title": END,
    }
)

# 2️⃣ Conditional routing for tools (FIX)
graph.add_conditional_edges(
    "chat_node",
    tools_condition,
)

# 3️⃣ Flow
graph.add_edge("tools", "chat_node")
graph.add_edge("chat_node", END)
graph.add_edge("generate_title", END)

chatbot = graph.compile(checkpointer=checkpointer)


def get_config(thread_id: str, user_id: int):
    config =  {
        'configurable': {
            'thread_id': thread_id,
            'user_id': user_id
        },
        'metadata': {
            'thread_id': thread_id.capitalize,
            'user_id': user_id
        },
        'run_name': 'chat_turn'
    }

    return config

def get_chat_response(user_message: str, thread_id: str, user_id: int) -> str:

    config = get_config(thread_id, user_id)
    response = chatbot.invoke(
        {'messages': [HumanMessage(content=user_message)]},
        config=config
    )
    assistant_message = response['messages'][-1].content
    return assistant_message

def get_chat_stream(user_message: str, thread_id: str, user_id: int) -> Generator:

    config = get_config(thread_id, user_id)

    stream = chatbot.stream(
        { 'messages': [HumanMessage(content=user_message)] },
        config=config,
        stream_mode='messages'
    )

    return stream

def get_chat_history(thread_id: str, user_id: int):
    config = get_config(thread_id, user_id)

    state = chatbot.get_state(config=config)
    messages = state.values.get('messages', [])

    history = [
        {
            'role': 'user' if isinstance(msg, HumanMessage) else 'assistant',
            'content': msg.content
        }
        for msg in messages
        if msg.content and isinstance(msg, (HumanMessage, AIMessage))
    ]

    return history

