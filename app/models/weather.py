from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Weather(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    windspeed = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
