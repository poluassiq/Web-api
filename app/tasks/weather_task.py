import asyncio
import httpx
from app.models.weather import Weather
from app.db.session import AsyncSessionLocal
from app.nats.producer import publish_weather
from app.config import WEATHER_API_URL, WEATHER_INTERVAL

async def fetch_weather():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(WEATHER_API_URL)
        response.raise_for_status()

        data = response.json()["current"]

        return {
            "temperature": data["temperature_2m"],
            "humidity": data["relativehumidity_2m"],
            "windspeed": data["windspeed_10m"],
        }


async def weather_background_task():
    while True:
        try:
            print("[Фоновая задача] Запрос данных о погоде...")

            data = await fetch_weather()

            async with AsyncSessionLocal() as db:
                weather = Weather(**data)
                db.add(weather)
                await db.commit()
                await db.refresh(weather)

                print(f"[БД] Данные о погоде сохранены с id={weather.id}")

                message = {
                    "id": weather.id,
                    "temperature": weather.temperature,
                    "humidity": weather.humidity,
                    "windspeed": weather.windspeed,
                    "created_at": str(weather.created_at)
                }

            await publish_weather(message)
            print("[Фоновая задача] Данные отправлены через NATS\n")

        except httpx.RequestError as e:
            print(f"[Ошибка сети] Не удалось получить погоду: {e}")

        except Exception as e:
            print(f"[Ошибка фоновой задачи] {e}")

        await asyncio.sleep(WEATHER_INTERVAL)


async def run_weather_task_once():
    try:
        async with AsyncSessionLocal() as db:
            data = await fetch_weather()
            weather = Weather(**data)
            db.add(weather)
            await db.commit()
            await db.refresh(weather)

            message = {
                "id": weather.id,
                "temperature": weather.temperature,
                "humidity": weather.humidity,
                "windspeed": weather.windspeed,
                "created_at": str(weather.created_at)
            }

        await publish_weather(message)

    except httpx.RequestError as e:
        print(f"[Ошибка сети] Не удалось получить погоду вручную: {e}")

    except Exception as e:
        print(f"[Ошибка] {e}")
