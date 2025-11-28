from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base

class CallLog(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String, index=True)  # ID único de llamada de Twilio
    user_phone = Column(String, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    interaction_log = Column(JSON, default=[])  # Lista de interacciones (pregunta/respuesta)
    status = Column(String, default="active")
    
    # Campos opcionales para análisis
    duration = Column(Integer, nullable=True)
    user_intent = Column(String, nullable=True)
