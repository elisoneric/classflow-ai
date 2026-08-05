import uuid


def send_reminder_job_id(class_session_id: uuid.UUID, attempt_number: int) -> str:
    return f"send-reminder-{class_session_id}-{attempt_number}"


def check_deadline_job_id(class_session_id: uuid.UUID, attempt_number: int) -> str:
    return f"check-deadline-{class_session_id}-{attempt_number}"
