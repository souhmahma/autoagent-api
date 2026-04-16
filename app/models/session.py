from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class SessionStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task = Column(Text, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.running)
    steps = Column(JSON, default=list)       # List of ReAct steps (thought/action/observation)
    final_answer = Column(Text, nullable=True)
    tools_used = Column(JSON, default=list)  # Track which tools were called
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")