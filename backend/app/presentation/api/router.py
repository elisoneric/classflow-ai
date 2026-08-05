from fastapi import APIRouter

from app.presentation.api.routes.auth import router as auth_router
from app.presentation.api.routes.course_lecturers import router as course_lecturers_router
from app.presentation.api.routes.courses import router as courses_router
from app.presentation.api.routes.lecturers import router as lecturers_router
from app.presentation.api.routes.semesters import router as semesters_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(semesters_router)
api_router.include_router(courses_router)
api_router.include_router(lecturers_router)
api_router.include_router(course_lecturers_router)

# Further feature routers are included here as they're built.
