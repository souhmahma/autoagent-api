from app.agent.tools.calculator import calculate
from app.agent.tools.weather import get_weather
from app.agent.tools.web_search import web_search
from app.agent.tools.summarizer import summarize_text

TOOLS_REGISTRY = {
    "calculator": {
        "fn": calculate,
        "async": False,
        "description": "Evaluate a mathematical expression. Input: a math expression string like '(3+5)*2'.",
    },
    "weather": {
        "fn": get_weather,
        "async": True,
        "description": "Get current weather for a city. Input: city name as a string, e.g. 'Paris' or 'New York'.",
    },
    "web_search": {
        "fn": web_search,
        "async": True,
        "description": "Search the web for information. Input: a search query string.",
    },
    "summarizer": {
        "fn": summarize_text,
        "async": True,
        "description": "Summarize a long text into key points. Input: the text to summarize.",
    },
}