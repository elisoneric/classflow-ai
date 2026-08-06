import imaplib
import email
import re
import logging
from app.core.config import settings
from app.worker.tasks import parse_lecturer_response_task
from rq import Queue
from redis import Redis

logger = logging.getLogger(__name__)

# RQ Setup
redis_conn = Redis.from_url(settings.REDIS_URL)
task_queue = Queue('classflow_tasks', connection=redis_conn)

def poll_inbox():
    """
    Connects to IMAP, fetches UNREAD emails, extracts the Ref ID and the response text,
    and enqueues the AI parsing task.
    """
    if not settings.IMAP_SERVER or not settings.IMAP_USER:
        logger.warning("IMAP configuration missing. Skipping inbox polling.")
        return
        
    try:
        mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        mail.select("inbox")
        
        status, messages = mail.search(None, "UNREAD")
        if status != "OK":
            logger.error("Failed to search inbox")
            return
            
        email_ids = messages[0].split()
        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract Body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                        
                    # Extract Session ID using regex looking for "Ref: [ID]"
                    match = re.search(r"Ref:\s*\[(\d+)\]", body)
                    if match:
                        session_id = int(match.group(1))
                        # We just take the top part of the reply, assuming standard email quoting.
                        # For a robust MVP, we just send the whole body to AI, the AI can ignore the quoted original message.
                        logger.info(f"Received reply for session {session_id}")
                        task_queue.enqueue(parse_lecturer_response_task, session_id, body)
                    else:
                        logger.warning("Received unread email without a valid Ref ID. Ignoring.")
                        
            # Mark as read (implicitly done by FETCH if we didn't specify PEEK, but just in case)
            mail.store(e_id, '+FLAGS', '\\Seen')
            
        mail.logout()
    except Exception as e:
        logger.error(f"Error polling IMAP: {e}")
