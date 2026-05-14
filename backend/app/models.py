from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from .database import Base

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, index=True)
    phone = Column(String, nullable=True)
    skills = Column(JSON, default=[])
    status = Column(String, default="new")
    cv_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)