import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.domain.models import ClassSession, Lecturer
import logging
import requests

logger = logging.getLogger(__name__)

def send_email_reminder(session: ClassSession, lecturer: Lecturer) -> bool:
    try:
        msg = EmailMessage()
        
        # We append a reference ID to track the reply
        course = session.timetable.course
        subject = f"Class Reminder: {course.code} on {session.date}"
        
        body = f"""Hello {lecturer.name},

This is an automated reminder for your upcoming class {course.code} scheduled at {session.timetable.start_time} in {session.timetable.venue}.

Will this class hold as scheduled?
You can reply simply with "Yes", or provide any changes (e.g. "We will start by 5pm", "Move to Lab 2", "Hold online", or "No class today").

Regards,
ClassFlow AI

---
Ref: [{session.id}]
"""
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = lecturer.email
        
        # Connect to SMTP server
        if settings.SMTP_SERVER:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email sent to {lecturer.email} for session {session.id}")
            return True
        else:
            logger.warning("SMTP configuration is missing. Simulating email send.")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send email to {lecturer.email}: {e}")
        return False

def send_whatsapp_announcement(session: ClassSession) -> bool:
    """
    Calls the external WhatsApp bot microservice to send the announcement to the class group.
    """
    try:
        course = session.timetable.course
        
        if session.status == "CONFIRMED":
            message = f"📢 *{course.code} Announcement*\n\nClass holds today at {session.timetable.start_time} in {session.timetable.venue}."
        elif session.status == "CANCELLED":
            message = f"📢 *{course.code} Announcement*\n\nToday's class has been CANCELLED."
        elif session.status == "DELAYED":
            message = f"📢 *{course.code} Announcement*\n\nToday's class is DELAYED. We will start at {session.actual_time} in {session.timetable.venue}."
        elif session.status == "RELOCATED":
            message = f"📢 *{course.code} Announcement*\n\nToday's class holds at {session.timetable.start_time} but has been RELOCATED to {session.actual_venue}."
        elif session.status == "ONLINE":
            message = f"📢 *{course.code} Announcement*\n\nToday's class will hold ONLINE at {session.timetable.start_time}."
        else:
            # We don't announce REVIEW_NEEDED
            return False
            
        payload = {
            "course_code": course.code,
            "message": message
        }
        
        if settings.WHATSAPP_BOT_URL:
            # Uncomment below to actually hit the bot
            # response = requests.post(f"{settings.WHATSAPP_BOT_URL}/send_group", json=payload)
            # response.raise_for_status()
            logger.info(f"Mocked WhatsApp message sent for {course.code}: {message}")
            return True
        else:
            logger.warning("WHATSAPP_BOT_URL missing. Simulated announcement.")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp announcement: {e}")
        return False
