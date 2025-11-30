from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import requests, math
from typing import TypedDict, Annotated, Generator, Literal
from dotenv import load_dotenv
import sqlite3, datetime

load_dotenv()

# --------------
# 1. LLMs
# --------------
llm = ChatOpenAI()
llm_title = ChatOpenAI()

# ______________
# 2. Tools
# ______________


search_tool = DuckDuckGoSearchRun(region='us-en')

@tool
def calculator(first_num: float, second_num: float, operation: Literal['add', 'mul', 'sub', 'div', 'mod', 'pow', 'log']):
    '''
    Perform a basic arithemtic operations on two numbers.
    Supported operations: 'add', 'mul', 'sub', 'div', 'mod', 'pow', 'log
    '''
    try:
        match(operation):
            case 'add':
                result = first_num + second_num
            case 'mul':
                result = first_num * second_num
            case 'sub':
                result = first_num - second_num
            case 'div':
                if second_num == 0:
                    return {'error': ZeroDivisionError('Division by zero is not allowed')}
                result = first_num / second_num
            case 'mod':
                result = first_num % second_num
            case 'pow':
                result = first_num ** second_num
            case 'log':
                if first_num <= 0 or second_num <= 0:
                    return {'error': ValueError('Logarithm argument must be positive')}
                result = math.log(first_num, second_num)
            case _:
                return {'error': f'Unsupported operation "{operation}"'}
        return {
            'first_num': first_num,
            'second_num': second_num,
            'operation': operation,
            'result': result
        }
    except Exception as e:
        return {'error': str(e)}


@tool
def advanced_calculator(number: float, operation: Literal['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh', 'factorial', 'exp']):
    '''
    Perform advanced mathematical operations on a single number with error handling for edge cases.
    Supported operations: 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh', 'factorial', 'exp'
    '''
    try:
        match(operation):
            case 'sin':
                result = math.sin(number)
            case 'cos':
                result = math.cos(number)
            case 'tan':
                result = math.tan(number)
            case 'asin':
                if -1 <= number <= 1:
                    result = math.asin(number)
                else:
                    return {'error': ValueError('Input out of range for arcsine function')}
            case 'acos':
                if -1 <= number <= 1:
                    result = math.acos(number)
                else:
                    return {'error': ValueError('Input out of range for arccosine function')}
            case 'atan':
                result = math.atan(number)
            case 'sinh':
                result = math.sinh(number)
            case 'cosh':
                result = math.cosh(number)
            case 'tanh':
                result = math.tanh(number)
            case 'asinh':
                result = math.asinh(number)
            case 'acosh':
                if number >= 1:
                    result = math.acosh(number)
                else:
                    return {'error': ValueError('Input must be >= 1 for hyperbolic arccosine function')}
            case 'atanh':
                if -1 < number < 1:
                    result = math.atanh(number)
                else:
                    return {'error': ValueError('Input out of range for hyperbolic arctangent function')}
            case 'factorial':
                if number < 0:
                    return {'error': ValueError('Factorial function requires a non-negative integer')}
                result = math.factorial(int(number))
            case 'exp':
                result = math.exp(number)
            case _:
                return {'error': f'Unsupported operation "{operation}"'}

        return {
            'number': number,
            'operation': operation,
            'result': result
        }

    except Exception as e:
        return {'error': str(e)}

@tool
def mathematical_conversions(value: float, frm: Literal['deg', 'rad'], to: Literal['deg','rad']):
    '''
    Perform unit conversions between degrees and radians for trigonometric functions.
    :param value: The value to be converted.
    :param frm: The unit of the input value ('deg' for degrees, 'rad' for radians).
    :param to: The unit to convert the value to ('deg' for degrees, 'rad' for radians).
    :return: A dictionary containing the original value, input unit, converted value, and output unit.
    '''
    if frm == to:
        result = value
    elif frm == 'rad' and to == 'deg':
        result = value * (180 / math.pi)
    elif frm == 'deg' and to == 'rad':
        result = value * (math.pi / 180)
    else:
        return {'error': 'Invalid input conversion units'}
    return {
        'result': result,
        'input_unit': frm,
        'output_unit': to,
        'original_value':value
    }
    
@tool
def get_stock_price(symbol: str) -> dict:
    '''
    Fetch latest stock price for a given symbol (e.g. - 'AAPL', 'TSLA')
    with Alpha Vantage with API key in the URL.
    '''
    url = f'https://www.alphavantage.co/query?apikey=7S92EVEUCWASARWC&function=GLOBAL_QUOTE&symbol={symbol}'
    r = requests.get(url)
    return r.json()

@tool
def current_datetime():
    '''
    Docstring for current_datetime
    '''

    return {'current_datetime_now': datetime.datetime.now()}

@tool
def get_geocoding(cityname: str):
    '''
    Docstring for get_geocoding to get latitude and longitude of a city. 
    This is an helper function for 'get_weather' function to get Latitute and Longitude by cityname.
    Then by hitting 'get_weather' API we can get weather condition
    
    :param cityname: City name in lower case and stripped without any punctuations
    :type cityname: str
    '''
    geocoding_url = f'https://geocoding-api.open-meteo.com/v1/search?name={cityname}'
    geocoding = requests.get(geocoding_url)
    return geocoding.json()

@tool
def get_weather(latitude: float, longitude: float):
    '''
    Docstring for get_weather by given latitude and longitude
    'get_geocoding' function can be used, to get Latitude and Longitude from cityname
    Then by hitting 'open-meteo' API we can get weather conditions parameters like "temperature_2m,relative_humidity_2m,dew_point_2m,rain,snow_depth"
    
    :param latitude: Latitude of the city
    :type latitude: float
    :param longitude: Longitude of the city
    :type longitude: float
    '''

    weather_url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,rain,snow_depth&timezone=auto&format=json'
    weather_response = requests.get(weather_url)
    return weather_response.json()

# make tool lists

tools = [search_tool, calculator, get_stock_price, current_datetime,get_geocoding, get_weather, advanced_calculator, mathematical_conversions]

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

    # send to llm_with_tools
    response = llm_with_tools.invoke(messages)

    # response store state
    return {'messages': [response]}

def check_title_condition(state: ChatState, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    title = get_thread_title(thread_id)

    if title is None:
        return "generate_title"
    else:
        return "skip_title"

def generate_title_node(state: ChatState, config) -> ChatState:
    thread_id = config["configurable"]["thread_id"]
    
    # First human message
    intial_chats = state["messages"][:4]
    prompt = [
        SystemMessage("Generate a short chatroom title (3–6 words) and important don't give any single, double or triple quotes."),
        *intial_chats
    ]

    title = llm_title.invoke(prompt).content.strip()
    cleaned_title = ''.join((i if i.isalnum() or i in {' ', '?', "'", '-'} else '' for i in title)).replace('  ', ' ').strip()
    set_thread_title(thread_id, cleaned_title)

    return state

tool_node = ToolNode(tools)

# -------------
# 5. SqlLite
# -------------

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

# create title thread_id table

conn.execute("""
CREATE TABLE IF NOT EXISTS threads (
    thread_id TEXT PRIMARY KEY,
    thread_title TEXT
);
""")
conn.commit()


checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)

graph.add_node("generate_title", generate_title_node)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

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
graph.add_edge(START, "chat_node")
graph.add_edge("tools", "chat_node")
graph.add_edge("chat_node", END)
graph.add_edge("generate_title", END)

chatbot = graph.compile(checkpointer=checkpointer)


def get_config(thread_id: str):
    config = {
        'configurable': {'thread_id': thread_id},
        'metadata': {'thread_id': thread_id},
        'run_name': 'chat_turn'
        }
    return config

def get_chat_response(user_message:str, thread_id: str = '1') -> str:

    config = get_config(thread_id)
    response = chatbot.invoke({'messages' : [
        HumanMessage(content=user_message)
        ]}, config=config)
    
    assistant_message = response['messages'][-1].content
    return assistant_message

def get_chat_stream(user_message:str, thread_id: str = '1') -> Generator:
    config = get_config(thread_id)
    stream = chatbot.stream({'messages' : [
        HumanMessage(content=user_message)
        ]}, config=config, stream_mode='messages')
    
    # for msg, metadata in stream:
    #     if isinstance(msg, ToolMessage) and metadata.get('langgraph_node') == 'chat_node':
    #         yield {'chat_response': msg}
    #     elif isinstance(msg, ToolMessage):
    #         tool_name = getattr(msg, 'name', 'tool')
    #         yield {'tool_name': tool_name}
    return stream

def get_chat_history(thread_id):
    config = get_config(thread_id)
    messages = chatbot.get_state(config=config).values.get('messages', None)
    if not messages:
        return []
    history = [
        {
            'role': 'user' if isinstance(message, HumanMessage) else 'assistant',
            'content': message.content
        } for message in filter(lambda message: message.content and (isinstance(message, HumanMessage) or isinstance(message, AIMessage)) ,messages)
    ]

    return history

def get_all_unique_threads():
    cur = conn.cursor()
    cur.execute("SELECT thread_id FROM threads")
    rows = [x[0] for x in cur.fetchall()]
    return rows

    # for checkpoint in checkpointer.list():

def get_thread_title(thread_id: str):
    cur = conn.cursor()
    cur.execute("SELECT thread_title FROM threads WHERE thread_id = ?", (str(thread_id),))
    row = cur.fetchone()
    return row[0] if row else None

def set_thread_title(thread_id: str, title: str):
    conn.execute(
        "INSERT OR REPLACE INTO threads (thread_id, thread_title) VALUES (?, ?)",
        (str(thread_id), title)
    )
    conn.commit()
