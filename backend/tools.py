import datetime, math, requests
from typing import Literal
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from googlesearch import search
from yt_dlp import YoutubeDL


from bs4 import BeautifulSoup

search_tool = DuckDuckGoSearchRun(region='us-en')

@tool
def calculator(first_num: float, second_num: float, operation: Literal['add', 'mul', 'sub', 'div', 'mod', 'pow', 'log']):
    """
    Perform basic arithmetic operations on two numbers.
    Supported operations: add, mul, sub, div, mod, pow, log
    """
    try:
        match operation:
            case 'add': result = first_num + second_num
            case 'sub': result = first_num - second_num
            case 'mul': result = first_num * second_num
            case 'div':
                if second_num == 0:
                    raise ZeroDivisionError("Division by zero")
                result = first_num / second_num
            case 'mod': result = first_num % second_num
            case 'pow': result = first_num ** second_num
            case 'log':
                if first_num <= 0 or second_num <= 0:
                    raise ValueError("Log arguments must be positive")
                result = math.log(first_num, second_num)
            case _:
                raise ValueError(f"Unsupported operation {operation}")

        return {'first_num': first_num, 'second_num': second_num, 'operation': operation, 'result': result}

    except Exception as e:
        return {'error': str(e)}


@tool
def advanced_calculator(number: float, operation: Literal['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh', 'factorial', 'exp']):
    '''
    Perform advanced mathematical operations on a single number with error handling for edge cases.
    Supported operations: 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh', 'factorial', 'exp'
    Number unit should be either radian or plain number, it should not be degree
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

@tool
def calculate_bmi(height: float, weight: float) -> float:
    """
    Calculate the Body Mass Index (BMI) based on the given height in meters and weight in kilograms.

    :param height: Height in meters
    :type height: float
    :param weight: Weight in kilograms
    :type weight: float

    :return: Calculated BMI value
    :rtype: float
    """
    return {'BMI': weight / (height * height)} if height else {'error': 'Please provide some height'}

# import streamlit as st

# @tool
# def play_video_from_url(video_url: str):
#     """
#     Play a video from the given URL using Streamlit's st.video function.

#     :param video_url: URL of the video to be played
#     :type video_url: str
#     """
#     st.video(video_url)
#     return {'video_url': video_url}

@tool
def google_search(query: str, max_results: int = 15) -> list[str]:
    """
    Perform a Google web search and return a list of result URLs.

    This tool uses an unofficial Google search library that scrapes
    publicly available search results. It is intended for lightweight,
    low-frequency searches only.

    Args:
        query (str): The search query text (e.g., "LangGraph tool usage").
        max_results (int): Maximum number of URLs to return. Default is 5.

    Returns:
        list[str]: A list of result URLs in order of relevance.

    Notes:
        - This tool does NOT use an official Google API.
        - Excessive usage may result in CAPTCHA or temporary blocking.
        - Intended for informational and research purposes only.
    """
    try:
        return {'query': query, 'result_urls': list(search(query,num_results=max_results, unique=True,  advanced=True, sleep_interval=2))}

    except Exception as e:
        return [f"Search failed: {str(e)}"]



@tool
def scrape_webpage(url: str, max_chars: int = 4000) -> dict:
    """
    Scrape and extract readable text content from a webpage.

    This tool fetches a webpage using HTTP GET, parses the HTML using
    BeautifulSoup, removes scripts/styles, and returns cleaned visible text.

    Args:
        url (str): Fully qualified webpage URL (must start with http or https).
        max_chars (int): Maximum number of characters to return from the page
                         to avoid excessive token usage. Default is 4000.

    Returns:
        dict: {
            "url": str,
            "content": str,
            "truncated": bool
        }

    Notes:
        - JavaScript-rendered content will NOT be scraped.
        - Some websites may block scraping via User-Agent rules.
        - Intended for informational text extraction only.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LangGraphBot/1.0)"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = " ".join(soup.stripped_strings)

        truncated = len(text) > max_chars
        text = text[:max_chars]

        return {
            "url": url,
            "content": text,
            "truncated": truncated
        }

    except Exception as e:
        return {
            "url": url,
            "error": str(e)
        }

@tool
def search_youtube(content_name: str, limit: int = 5) -> list[dict]:
    """
    Search YouTube for a song or video using yt-dlp.

    Args:
        content_name: Name of the content or keywords to search on YouTube.
        limit: Number of video results to return (default is 5).

    Returns:
        A list of videos with title, uploader, duration, views, and URL.
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "extract_flat": False,   # <-- resolve video info
    "default_search": f"ytsearch{limit}"
    }

    results = []
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(content_name, download=False)
        for entry in info.get("entries", []):
            results.append({
                "title": entry.get("title"),
                "uploader": entry.get("uploader"),
                "duration": entry.get("duration"),
                "views": entry.get("view_count"),
                "url": entry.get("url")
            })

    return {'searched_content_name': content_name,'results': results}
