import asyncio
import json
from nats.aio.client import Client as NATS
from app.ws.weather_ws import manager
from app.config import NATS_URL
from app.config import NATS_SUBJECT
from app.db.session import AsyncSessionLocal
from app.models.weather import Weather


async def message_handler(msg):
    try:
        data = json.loads(msg.data.decode())

        weather_id = data.get("id")
        event_type = data.get("event")

        print(
            f"[NATS] Получено сообщение с id={weather_id}:{data}" if weather_id else f"[NATS] Получено сообщение:{data}")

        if event_type == 'deleted':
            print(f"[NATS] Запись удалена, id={weather_id}")
            await manager.broadcast(data)
            print("[WebSocket] Уведомление об удалении отправлено")
            return

        async with AsyncSessionLocal() as db:
            if weather_id:
                weather = await db.get(Weather, weather_id)

                if weather:
                    if 'temperature' in data:
                        weather.temperature = data['temperature']
                    if 'humidity' in data:
                        weather.humidity = data['humidity']
                    if 'windspeed' in data:
                        weather.windspeed = data['windspeed']
                    print(f"[БД] Запись обновлена через NATS | id={weather.id}")
                else:
                    filtered_data = data.copy()
                    if 'event' in filtered_data:
                        del filtered_data['event']

                    required_fields = ['temperature', 'humidity', 'windspeed']
                    if all(field in filtered_data for field in required_fields):
                        weather = Weather(**filtered_data)
                        db.add(weather)
                        print(f"[БД] Новая запись создана через NATS | id={weather_id}")
                    else:
                        print(f"[NATS] Пропущено сообщение {weather_id}: недостаточно данных")
                        return

                await db.commit()

                ws_data = data.copy()
                if 'event' in ws_data:
                    del ws_data['event']
                await manager.broadcast(ws_data)
                print("[WebSocket] Данные отправлены всем подключённым клиентам")

    except Exception as e:
        print(f"[NATS] Ошибка обработки сообщения: {e}")
        import traceback
        traceback.print_exc()


async def start_nats_consumer():
    nc = NATS()
    print("[NATS] Запуск...")

    try:
        await nc.connect(NATS_URL)
        print(f"[NATS] Подключение к серверу...")
        print(f"[NATS] Успешно подключено")
        print(f"[NATS] Подписка на канал '{NATS_SUBJECT}' выполнена")

        await nc.subscribe(NATS_SUBJECT, cb=message_handler)

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"[NATS] Ошибка подключения: {e}")
        await asyncio.sleep(5)
        await start_nats_consumer()