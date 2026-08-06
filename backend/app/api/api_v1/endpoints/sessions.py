from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from datetime import date
from app.api import deps
from app.domain import schemas, models

router = APIRouter()

@router.get("/today", response_model=List[schemas.ClassSessionResponse])
def get_todays_sessions(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get all class sessions scheduled for today.
    """
    today = date.today()
    sessions = (
        db.query(models.ClassSession)
        .options(
            joinedload(models.ClassSession.timetable)
            .joinedload(models.Timetable.course)
        )
        .filter(models.ClassSession.date == today)
        .all()
    )
    return sessions

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get statistics for the dashboard.
    """
    today = date.today()
    
    total_courses = db.query(models.Course).count()
    todays_classes = db.query(models.ClassSession).filter(models.ClassSession.date == today).count()
    
    # Announcements sent today
    announcements_sent = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.action == "ANNOUNCEMENT_SENT",
            models.AuditLog.timestamp >= today
        )
        .count()
    )
    
    return {
        "total_courses": total_courses,
        "todays_classes": todays_classes,
        "announcements_sent": announcements_sent
    }
