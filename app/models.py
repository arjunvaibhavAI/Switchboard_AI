from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from datetime import datetime
from app.database import Base

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user_id = Column(String, index=True)
    prompt_length = Column(Integer)
    risk_detected = Column(Boolean)
    status = Column(String)  # PROCESSED | REDACTED | BLOCKED | ERROR

    
    # Cost Savings" logic
    cost_saved = Column(Float, default=0.0)
    model_used = Column(String, default="none")

