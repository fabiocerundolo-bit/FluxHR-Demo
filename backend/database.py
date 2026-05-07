from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fluxhr:fluxhr_secret@postgres:5432/fluxhr_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    skills = Column(JSON, default=list)
    phone = Column(String, nullable=True)
    status = Column(String, default="new")  # new, reviewed, shortlisted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cv_file_path = Column(String, nullable=True)

# Crea tabelle all'avvio (solo sviluppo)
def init_db():
    Base.metadata.create_all(bind=engine)