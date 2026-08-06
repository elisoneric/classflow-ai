from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.infrastructure.database import Base

class CourseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class SessionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    WAITING = "WAITING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"
    RELOCATED = "RELOCATED"
    ONLINE = "ONLINE"
    REVIEW_NEEDED = "REVIEW_NEEDED"

class ContactMethod(str, enum.Enum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    is_active = Column(Boolean, default=True)

class Lecturer(Base):
    __tablename__ = "lecturers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    preferred_contact = Column(Enum(ContactMethod), default=ContactMethod.EMAIL)
    fallback_contact = Column(Enum(ContactMethod), default=ContactMethod.EMAIL)
    
    courses = relationship("Course", back_populates="lecturer")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, nullable=False)  # e.g., CSC 803
    name = Column(String, nullable=False)
    status = Column(Enum(CourseStatus), default=CourseStatus.ACTIVE)
    
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=True)
    lecturer = relationship("Lecturer", back_populates="courses")
    
    timetables = relationship("Timetable", back_populates="course")

class Timetable(Base):
    __tablename__ = "timetables"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0 = Monday, 6 = Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    venue = Column(String, nullable=False)
    
    # Scheduling configurations
    reminder_offset_minutes = Column(Integer, default=120)  # Remind 2 hours before
    deadline_offset_minutes = Column(Integer, default=30)   # Need response by 30 mins before
    
    course = relationship("Course", back_populates="timetables")
    sessions = relationship("ClassSession", back_populates="timetable")

class ClassSession(Base):
    __tablename__ = "class_sessions"
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    lecturer_response = Column(Text, nullable=True)
    
    # Overrides / AI extracted details
    actual_time = Column(Time, nullable=True)
    actual_venue = Column(String, nullable=True)
    actual_mode = Column(String, nullable=True) # e.g. "Online"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    timetable = relationship("Timetable", back_populates="sessions")
    audit_logs = relationship("AuditLog", back_populates="session")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=True)
    action = Column(String, nullable=False) # e.g., REMINDER_SENT, ANNOUNCEMENT_SENT
    metadata_json = Column(Text, nullable=True) # JSON payload string
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ClassSession", back_populates="audit_logs")
