from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.weather import Weather
from pydantic import BaseModel

router = APIRouter(prefix="/weather", tags=["weather"])

class WeatherCreate(BaseModel):
    temperature: float
    humidity: float
    windspeed: float


class WeatherUpdate(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    windspeed: float | None = None


@router.get("/current")
async def current(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Weather).order_by(Weather.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()

@router.get("/")
async def list_weather(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Weather))
    return result.scalars().all()


@router.get("/{weather_id}")
async def get_weather(weather_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Weather).where(Weather.id == weather_id))
    weather = result.scalar_one_or_none()
    if not weather:
        raise HTTPException(status_code=404, detail="Запись о погоде не найдена")
    return weather


from app.nats.producer import publish_weather

@router.post("/")
async def create_weather(data: WeatherCreate, db: AsyncSession = Depends(get_db)):
    weather = Weather(**data.dict())
    db.add(weather)
    await db.commit()
    await db.refresh(weather)

    print(
        f"[БД] Запись обновлена | "
        f"id={weather.id}, "
        f"temperature={weather.temperature}, "
        f"humidity={weather.humidity}, "
        f"windspeed={weather.windspeed}"
    )
    message = {
        "id": weather.id,
        "temperature": weather.temperature,
        "humidity": weather.humidity,
        "windspeed": weather.windspeed,
        "created_at": str(weather.created_at),
        "event": "created"
    }

    await publish_weather(message)

    return weather


@router.patch("/{weather_id}")
async def update_weather(weather_id: int, data: WeatherUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Weather).where(Weather.id == weather_id))
    weather = result.scalar_one_or_none()
    if not weather:
        raise HTTPException(status_code=404, detail="Запись о погоде не найдена")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(weather, key, value)
    await db.commit()
    await db.refresh(weather)

    print(
        f"[БД] Запись обновлена | "
        f"id={weather.id}, "
        f"temperature={weather.temperature}, "
        f"humidity={weather.humidity}, "
        f"windspeed={weather.windspeed}"
    )
    await publish_weather({
        "id": weather.id,
        "temperature": weather.temperature,
        "humidity": weather.humidity,
        "windspeed": weather.windspeed,
        "event": "updated"
    })

    return weather


@router.delete("/{weather_id}")
async def delete_weather(weather_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Weather).where(Weather.id == weather_id))
    weather = result.scalar_one_or_none()
    if not weather:
        raise HTTPException(status_code=404, detail="Запись о погоде не найдена")
    await db.delete(weather)
    await db.commit()

    await publish_weather({
        "id": weather.id,
        "event": "deleted"
    })
    print(f"[БД] Запись удалена | id={weather.id}")
    return {"status": "Удален"}

