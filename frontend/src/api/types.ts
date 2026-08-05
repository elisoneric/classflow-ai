export type CourseStatus = "ACTIVE" | "PAUSED" | "COMPLETED";
export type SessionStatus =
  | "SCHEDULED"
  | "REMINDER_SENT"
  | "PENDING_REVIEW"
  | "RESOLVED"
  | "UNRESOLVED"
  | "ANNOUNCED";
export type SessionOutcome = "CONFIRMED" | "CANCELLED" | "DELAYED" | "RELOCATED" | "ONLINE";
export type ClassMode = "IN_PERSON" | "ONLINE" | "HYBRID";
export type ContactMethod = "EMAIL" | "WHATSAPP";
export type ResolutionSource =
  | "PENDING"
  | "LECTURER_RESPONSE"
  | "MANUAL_OVERRIDE"
  | "NO_RESPONSE_FALLBACK";
export type AIInterpretedStatus =
  | "CONFIRMED"
  | "CANCELLED"
  | "DELAYED"
  | "RELOCATED"
  | "ONLINE"
  | "UNCLEAR";
export type ReminderStatus = "SENT" | "RESPONDED" | "EXPIRED" | "CANCELLED";
export type AnnouncementStatus = "SENT" | "FAILED";
export type NotificationChannelType = "EMAIL" | "WHATSAPP";
export type DayOfWeek =
  | "MONDAY"
  | "TUESDAY"
  | "WEDNESDAY"
  | "THURSDAY"
  | "FRIDAY"
  | "SATURDAY"
  | "SUNDAY";

export interface Semester {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  timezone: string;
  is_active: boolean;
}

export interface Course {
  id: string;
  semester_id: string;
  code: string;
  title: string;
  status: CourseStatus;
  announcement_email: string;
}

export interface Lecturer {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  preferred_contact_method: ContactMethod;
  fallback_contact_method: ContactMethod;
}

export interface CourseLecturerLink {
  course_id: string;
  lecturer_id: string;
  is_primary: boolean;
}

export interface TimetableSlot {
  id: string;
  course_id: string;
  day_of_week: DayOfWeek;
  start_time: string;
  end_time: string;
  venue: string;
  mode: ClassMode;
  reminder_time: string;
  response_deadline_minutes: number;
  retry_attempts: number;
  retry_interval_minutes: number;
  fallback_contact_method_override: ContactMethod | null;
  is_active: boolean;
}

export interface ClassSession {
  id: string;
  course_id: string;
  timetable_slot_id: string | null;
  session_date: string;
  scheduled_start_time: string;
  scheduled_end_time: string;
  venue: string;
  mode: ClassMode;
  status: SessionStatus;
  outcome: SessionOutcome | null;
  final_start_time: string | null;
  final_venue: string | null;
  final_mode: ClassMode | null;
  resolution_source: ResolutionSource;
  announced_at: string | null;
}

export interface Reminder {
  id: string;
  attempt_number: number;
  channel: NotificationChannelType;
  sent_at: string;
  deadline_at: string;
  status: ReminderStatus;
}

export interface LecturerResponseRead {
  id: string;
  reminder_id: string;
  raw_message: string;
  cleaned_message: string;
  received_at: string;
  ai_status: AIInterpretedStatus | null;
  ai_new_time: string | null;
  ai_new_venue: string | null;
  ai_new_mode: ClassMode | null;
  ai_confidence: number | null;
  requires_review: boolean;
}

export interface Announcement {
  id: string;
  channel: NotificationChannelType;
  recipient: string;
  content: string;
  sent_at: string | null;
  status: AnnouncementStatus | null;
}

export interface ClassSessionDetail extends ClassSession {
  reminders: Reminder[];
  responses: LecturerResponseRead[];
  announcements: Announcement[];
}

export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor: "SYSTEM" | "LECTURER" | "COURSE_REP";
  previous_state: Record<string, unknown> | null;
  new_state: Record<string, unknown> | null;
  note: string | null;
  created_at: string;
}
