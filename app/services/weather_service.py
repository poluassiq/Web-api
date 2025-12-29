import httpx
from app.config import WEATHER_API_URL

async def fetch_weather():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(WEATHER_API_URL)
        response.raise_for_status()
        data = response.json()["current_weather"]
        return {
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "windspeed": data["windspeed"]
        }
