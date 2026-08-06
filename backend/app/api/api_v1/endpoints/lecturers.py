from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.domain import schemas, models

router = APIRouter()

@router.get("/", response_model=List[schemas.LecturerResponse])
def read_lecturers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    lecturers = db.query(models.Lecturer).offset(skip).limit(limit).all()
    return lecturers

@router.post("/", response_model=schemas.LecturerResponse)
def create_lecturer(
    *,
    db: Session = Depends(deps.get_db),
    lecturer_in: schemas.LecturerCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    lecturer = models.Lecturer(**lecturer_in.model_dump())
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)
    return lecturer
