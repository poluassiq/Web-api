import json
from nats.aio.client import Client as NATS
from app.config import NATS_URL
from app.config import NATS_SUBJECT

nc = NATS()

async def publish_weather(data: dict):
    if not nc.is_connected:
        print("[NATS] Подключение к серверу...")
        await nc.connect(NATS_URL)
        print("[NATS] Успешно подключено")

    await nc.publish(
        NATS_SUBJECT,
        json.dumps(data, ensure_ascii=False).encode()
    )
