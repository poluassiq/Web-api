from fastapi import APIRouter
from app.tasks.weather_task import run_weather_task_once

router = APIRouter(
    prefix="/weather/tasks",
    tags=["tasks"]
)

@router.post(
    "/run",
    summary="Запуск фоновой задачи вручную",
    description="Принудительно запускает загрузку данных погоды"
)
async def run_task():
    await run_weather_task_once()
    return {"status": "фоновая задача запущена"}
