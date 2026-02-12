from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Conversation(Base):
    """Optimized schema - no audio blobs"""
    __tablename__ = "conversations_v2"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    
    # Audio stored externally (S3/filesystem)
    audio_storage_key = Column(String)  # Instead of audio_data blob
    
    # Conversation data
    transcription = Column(Text)
    response = Column(Text)
    language = Column(String)
    
    # Lead data
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True, index=True)  # Index for lookups
    company = Column(String, nullable=True)
    requirements = Column(Text, nullable=True)
    
    # Metadata for monitoring
    intent = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    turn_number = Column(Integer, nullable=True)
    
    # Cost tracking
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class LeadSummary(Base):
    """Aggregated lead view for analytics"""
    __tablename__ = "lead_summaries"
    
    session_id = Column(String, primary_key=True)
    name = Column(String)
    phone = Column(String, index=True)
    company = Column(String)
    requirements = Column(Text)
    language = Column(String)
    
    # Metrics
    total_turns = Column(Integer)
    total_tokens = Column(Integer)
    total_cost_usd = Column(Float)
    avg_confidence = Column(Float)
    
    # Status
    status = Column(String)  # complete, incomplete, objection
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
