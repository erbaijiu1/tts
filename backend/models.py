from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base

class AudioTask(Base):
    __tablename__ = "audio_tasks"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    text_snippet = Column(Text, nullable=False)
    audio_url = Column(String(512), nullable=False)
    voice = Column(String(100), nullable=True)
    rate = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
