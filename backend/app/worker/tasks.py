import logging
from app.infrastructure.database import SessionLocal
from app.domain import models
from app.services import notifications

logger = logging.getLogger(__name__)

def send_reminder_task(class_session_id: int):
    """
    Task executed by RQ worker to send a reminder to the lecturer.
    """
    logger.info(f"Executing send_reminder_task for session {class_session_id}")
    db = SessionLocal()
    try:
        session = db.query(models.ClassSession).filter(models.ClassSession.id == class_session_id).first()
        if not session:
            logger.error(f"Class session {class_session_id} not found.")
            return

        if session.status != models.SessionStatus.SCHEDULED:
            logger.info(f"Session {class_session_id} is no longer SCHEDULED. Skipping reminder.")
            return

        timetable = session.timetable
        course = timetable.course
        lecturer = course.lecturer
        
        if not lecturer:
            logger.error(f"No lecturer assigned to course {course.code}")
            return
            
        # Send Email notification
        success = notifications.send_email_reminder(session, lecturer)
        
        if success:
            session.status = models.SessionStatus.WAITING
            # Log the action
            audit = models.AuditLog(session_id=session.id, action="REMINDER_SENT")
            db.add(audit)
            db.commit()
            logger.info(f"Reminder sent successfully for session {class_session_id}")
        else:
            logger.error(f"Failed to send reminder for session {class_session_id}")
            
    finally:
        db.close()

def parse_lecturer_response_task(session_id: int, response_text: str):
    """
    Task to call AI service to parse response, update status, and send announcement.
    """
    from app.services import ai_parser
    logger.info(f"Parsing response for session {session_id}")
    db = SessionLocal()
    try:
        session = db.query(models.ClassSession).filter(models.ClassSession.id == session_id).first()
        if not session:
            return
            
        interpretation = ai_parser.interpret_response(response_text)
        
        session.status = interpretation.status
        if interpretation.new_time:
            # Need to parse string to time
            pass
        if interpretation.new_venue:
            session.actual_venue = interpretation.new_venue
            
        session.lecturer_response = response_text
        
        audit = models.AuditLog(session_id=session.id, action="RESPONSE_PARSED", metadata_json=interpretation.model_dump_json())
        db.add(audit)
        db.commit()
        
        # Now trigger announcement
        if session.status != models.SessionStatus.REVIEW_NEEDED:
            notifications.send_whatsapp_announcement(session)
            
    finally:
        db.close()
