import httpx
from app.core.config import settings


async def get_weather(city: str) -> str:
    if not settings.OPENWEATHER_API_KEY:
        return (
            f"[MOCK] Weather in {city}: 22°C, partly cloudy, humidity 60%, wind 10 km/h. "
            "(Set OPENWEATHER_API_KEY in .env for real data)"
        )

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "en",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        country = data["sys"]["country"]

        return (
            f"Weather in {city}, {country}: {desc}. "
            f"Temperature: {temp}°C (feels like {feels}°C). "
            f"Humidity: {humidity}%. Wind: {wind} m/s."
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"City '{city}' not found. Please check the city name."
        return f"Weather API error: {e.response.status_code}"
    except Exception as e:
        return f"Failed to fetch weather: {str(e)}"