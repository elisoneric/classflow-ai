import logging
from datetime import datetime, date, timedelta
from rq import Queue
from redis import Redis
from sqlalchemy.orm import Session
from app.infrastructure.database import SessionLocal
from app.domain import models
from app.core.config import settings
from app.worker.tasks import send_reminder_task

logger = logging.getLogger(__name__)

# RQ Setup
redis_conn = Redis.from_url(settings.REDIS_URL)
task_queue = Queue('classflow_tasks', connection=redis_conn)

def generate_daily_sessions():
    """
    Cron job function to run every midnight.
    Finds all timetables for the current day of the week and creates ClassSession entries.
    Also enqueues RQ tasks for the reminders.
    """
    logger.info("Running daily session generation")
    db = SessionLocal()
    try:
        today = date.today()
        # In Python, Monday is 0, Sunday is 6. Our model matches this.
        current_day_of_week = today.weekday()
        
        timetables = db.query(models.Timetable).filter(models.Timetable.day_of_week == current_day_of_week).all()
        
        for timetable in timetables:
            # Check if course is active
            if timetable.course.status != models.CourseStatus.ACTIVE:
                continue
                
            # Check if a session already exists for today to avoid duplicates
            existing_session = db.query(models.ClassSession).filter(
                models.ClassSession.timetable_id == timetable.id,
                models.ClassSession.date == today
            ).first()
            
            if existing_session:
                logger.info(f"Session already exists for timetable {timetable.id} on {today}")
                continue
                
            # Create session
            new_session = models.ClassSession(
                timetable_id=timetable.id,
                date=today,
                status=models.SessionStatus.SCHEDULED
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            logger.info(f"Created session {new_session.id} for timetable {timetable.id}")
            
            # Schedule the reminder via RQ
            # Calculate reminder time
            # For simplicity, combine today's date with the timetable's start_time
            class_datetime = datetime.combine(today, timetable.start_time)
            reminder_datetime = class_datetime - timedelta(minutes=timetable.reminder_offset_minutes)
            
            # Use RQ's enqueue_at to schedule the job
            # Note: enqueue_at is part of rq-scheduler which requires the rq-scheduler worker,
            # OR we can just use APScheduler to manage the jobs natively, but for RQ we can use 'enqueue_in'
            time_until_reminder = (reminder_datetime - datetime.now()).total_seconds()
            
            if time_until_reminder > 0:
                task_queue.enqueue_in(
                    timedelta(seconds=time_until_reminder),
                    send_reminder_task,
                    new_session.id
                )
                logger.info(f"Scheduled reminder for session {new_session.id} in {time_until_reminder} seconds")
            else:
                logger.warning(f"Reminder time for session {new_session.id} is in the past! Enqueuing immediately.")
                task_queue.enqueue(send_reminder_task, new_session.id)
                
    except Exception as e:
        logger.error(f"Error in generate_daily_sessions: {e}")
    finally:
        db.close()
