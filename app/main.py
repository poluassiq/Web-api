import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.ws.weather_ws import manager
from app.tasks.weather_task import weather_background_task
from app.db.session import engine
from app.db.base import Base
from app.nats.consumer import start_nats_consumer
from app.api.weather import router as weather_router
from app.api.tasks import router as tasks_router

app = FastAPI(
    title="Weather Async API",
    description="Погодный мониторинг Екатеринбурга",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather_router)
app.include_router(tasks_router)


@app.get("/")
async def root():
    return {
        "message": "Weather Async API для Екатеринбурга",
        "version": "1.0.0",
        "endpoints": {
            "current_weather": "/weather/current",
            "all_weather": "/weather/",
            "weather_by_id": "/weather/{id}",
            "create_weather": "POST /weather/",
            "update_weather": "PATCH /weather/{id}",
            "delete_weather": "DELETE /weather/{id}",
            "run_task": "POST /weather/tasks/run",
            "health": "/health",
            "websocket": "/ws/weather"
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "weather-api",
        "timestamp": datetime.now().isoformat()
    }


@app.websocket("/ws/weather")
async def weather_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_json({
            "type": "welcome",
            "message": "Подключено к Weather WebSocket!",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await ws.receive_text()
            print(f"[WebSocket] Получено: {data}")

            if data == "ping":
                await ws.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            elif data == "get_weather":
                await ws.send_json({
                    "type": "info",
                    "message": "Используйте GET /weather/current для получения текущей погоды",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                await ws.send_json({
                    "type": "echo",
                    "message": f"Сообщение: {data}",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(ws)
        print("[WebSocket] Клиент отключился")
    except Exception as e:
        print(f"[WebSocket] Ошибка: {e}")
        manager.disconnect(ws)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("База данных инициализирована")

    asyncio.create_task(weather_background_task())
    print("Фоновая задача запущена")

    asyncio.create_task(start_nats_consumer())
    print("NATS запущен")

    print("Сервер запущен и готов к работе!")
    print("REST API: http://localhost:8001/")
    print("WebSocket: ws://localhost:8001/ws/weather")
    print("Документация: http://localhost:8001/docs")


@app.on_event("shutdown")
async def shutdown():
    print("Сервер останавливается...")