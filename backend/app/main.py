from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.api_v1.api import api_router
from app.core.config import settings
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.scheduler import generate_daily_sessions
from app.services.email_ingestion import poll_inbox

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = BackgroundScheduler()
    
    # Run at 00:01 every day
    scheduler.add_job(generate_daily_sessions, 'cron', hour=0, minute=1)
    
    # Run every 1 minute
    scheduler.add_job(poll_inbox, 'interval', minutes=1)
    
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to ClassFlow AI API"}
