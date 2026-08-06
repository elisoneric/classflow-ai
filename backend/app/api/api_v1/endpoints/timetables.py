from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.domain import schemas, models

router = APIRouter()

@router.get("/", response_model=List[schemas.TimetableResponse])
def read_timetables(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    timetables = db.query(models.Timetable).offset(skip).limit(limit).all()
    return timetables

@router.post("/", response_model=schemas.TimetableResponse)
def create_timetable(
    *,
    db: Session = Depends(deps.get_db),
    timetable_in: schemas.TimetableCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    timetable = models.Timetable(**timetable_in.model_dump())
    db.add(timetable)
    db.commit()
    db.refresh(timetable)
    return timetable
