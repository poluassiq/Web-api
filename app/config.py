DATABASE_URL = "sqlite+aiosqlite:///./weather.db"

WEATHER_API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=56.85&longitude=60.60"
    "&current=temperature_2m,relativehumidity_2m,windspeed_10m"
)

WEATHER_INTERVAL = 60
NATS_URL = "nats://127.0.0.1:4222"
NATS_SUBJECT = "weather.updates"
