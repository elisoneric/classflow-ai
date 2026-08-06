from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, lecturers, courses, timetables

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(lecturers.router, prefix="/lecturers", tags=["lecturers"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(timetables.router, prefix="/timetables", tags=["timetables"])
