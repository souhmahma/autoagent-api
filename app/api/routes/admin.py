from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.session import AgentSession
from app.models.user import User
from app.schemas.agent import AgentSessionOut
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return None


@router.get("/sessions", response_model=List[AgentSessionOut])
def all_sessions(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(AgentSession).order_by(AgentSession.created_at.desc()).all()


@router.get("/stats")
def stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from app.models.session import SessionStatus

    total_users = db.query(User).count()
    total_sessions = db.query(AgentSession).count()
    completed = (
        db.query(AgentSession).filter(AgentSession.status == SessionStatus.completed).count()
    )
    failed = db.query(AgentSession).filter(AgentSession.status == SessionStatus.failed).count()

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completed_sessions": completed,
        "failed_sessions": failed,
        "success_rate": round((completed / total_sessions * 100) if total_sessions > 0 else 0, 1),
    }
