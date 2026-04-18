from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.models.session import SessionStatus


class AgentRunRequest(BaseModel):
    task: str = Field(..., min_length=1)
    max_steps: int = 8


class ReActStep(BaseModel):
    step: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Any] = None
    observation: Optional[str] = None


class AgentSessionOut(BaseModel):
    id: int
    user_id: int
    task: str
    status: SessionStatus
    steps: List[dict]
    final_answer: Optional[str]
    tools_used: List[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentRunResponse(BaseModel):
    session_id: int
    task: str
    status: SessionStatus
    steps: List[dict]
    final_answer: Optional[str]
    tools_used: List[str]
