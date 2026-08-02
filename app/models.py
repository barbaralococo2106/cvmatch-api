from sqlalchemy import Column, String, Float, JSON, DateTime
from sqlalchemy.dialects.sqlite import TEXT
from datetime import datetime 
import uuid 

from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Input
    jd_text = Column(TEXT)
    company_name = Column(String)
    role_title = Column(String)
    
    # Output del agente
    score = Column(JSON)
    rewritten_cv = Column(TEXT)
    cover_letter = Column(TEXT)
    parsed_cv = Column(JSON)
    jd_analysis = Column(JSON)