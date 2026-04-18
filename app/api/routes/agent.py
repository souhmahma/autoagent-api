from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.engine import run_agent
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.session import AgentSession, SessionStatus
from app.models.user import User
from app.schemas.agent import (AgentRunRequest, AgentRunResponse,
                               AgentSessionOut)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/run", response_model=AgentRunResponse, status_code=201)
async def run(
    payload: AgentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = AgentSession(
        user_id=current_user.id,
        task=payload.task,
        status=SessionStatus.running,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        result = await run_agent(payload.task, max_steps=payload.max_steps)
        session.steps = result["steps"]
        session.final_answer = result["final_answer"]
        session.tools_used = result["tools_used"]
        session.status = SessionStatus.completed
        session.completed_at = datetime.utcnow()
    except Exception as e:
        session.status = SessionStatus.failed
        session.final_answer = f"Agent error: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    db.commit()
    db.refresh(session)

    return AgentRunResponse(
        session_id=session.id,
        task=session.task,
        status=session.status,
        steps=session.steps,
        final_answer=session.final_answer,
        tools_used=session.tools_used,
    )


@router.get("/sessions", response_model=List[AgentSessionOut])
def get_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(AgentSession).filter(AgentSession.user_id == current_user.id).all()


@router.get("/sessions/{session_id}", response_model=AgentSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(AgentSession)
        .filter(
            AgentSession.id == session_id,
            AgentSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(AgentSession)
        .filter(
            AgentSession.id == session_id,
            AgentSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
