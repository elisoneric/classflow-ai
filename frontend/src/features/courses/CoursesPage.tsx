import { useState, type FormEvent } from "react";
import { useCourseLifecycleAction, useCourses, useCreateCourse } from "@/api/courses";
import { useSemesters } from "@/api/semesters";
import { useAttachLecturer, useCourseLecturers, useDetachLecturer, useLecturers } from "@/api/lecturers";
import {
  useCreateTimetableSlot,
  useDeleteTimetableSlot,
  useTimetableSlots,
} from "@/api/timetable";
import { StatusBadge } from "@/components/StatusBadge";
import type { ClassMode, Course, DayOfWeek } from "@/api/types";

const DAYS: DayOfWeek[] = [
  "MONDAY",
  "TUESDAY",
  "WEDNESDAY",
  "THURSDAY",
  "FRIDAY",
  "SATURDAY",
  "SUNDAY",
];
const MODES: ClassMode[] = ["IN_PERSON", "ONLINE", "HYBRID"];

export function CoursesPage() {
  const { data: semesters } = useSemesters();
  const activeSemester = (semesters ?? []).find((s) => s.is_active) ?? semesters?.[0];
  const { data: courses, isLoading } = useCourses(activeSemester?.id);
  const createCourse = useCreateCourse();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [announcementEmail, setAnnouncementEmail] = useState("");

  function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!activeSemester) return;
    createCourse.mutate(
      { semester_id: activeSemester.id, code, title, announcement_email: announcementEmail },
      {
        onSuccess: () => {
          setCode("");
          setTitle("");
          setAnnouncementEmail("");
        },
      },
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Courses</h1>
      {!activeSemester && (
        <p className="mt-2 text-sm text-amber-700">
          No active semester yet — create and activate one in Settings first.
        </p>
      )}
      {isLoading && <p className="mt-4 text-sm text-gray-500">Loading…</p>}

      <div className="mt-4 space-y-3">
        {(courses ?? []).map((course) => (
          <CourseRow
            key={course.id}
            course={course}
            isExpanded={expandedId === course.id}
            onToggle={() => setExpandedId(expandedId === course.id ? null : course.id)}
          />
        ))}
      </div>

      {activeSemester && (
        <form
          onSubmit={handleCreate}
          className="mt-6 max-w-md space-y-3 rounded-lg border border-gray-200 bg-white p-4"
        >
          <h3 className="font-medium text-gray-900">New course</h3>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700">Code</span>
            <input
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="CSC803"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700">Title</span>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700">
              Class group announcement email
            </span>
            <input
              type="email"
              required
              value={announcementEmail}
              onChange={(e) => setAnnouncementEmail(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
            />
          </label>
          <button
            type="submit"
            disabled={createCourse.isPending}
            className="rounded-md bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {createCourse.isPending ? "Creating…" : "Add course"}
          </button>
        </form>
      )}
    </div>
  );
}

function CourseRow({
  course,
  isExpanded,
  onToggle,
}: {
  course: Course;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const lifecycleAction = useCourseLifecycleAction();

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <p className="font-semibold text-gray-900">{course.code}</p>
          <p className="text-sm text-gray-500">{course.title}</p>
        </div>
        <StatusBadge value={course.status} />
      </button>

      {isExpanded && (
        <div className="border-t border-gray-100 px-4 py-4">
          <div className="flex flex-wrap gap-2">
            {course.status === "ACTIVE" && (
              <button
                type="button"
                onClick={() => lifecycleAction.mutate({ id: course.id, action: "pause" })}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                Pause
              </button>
            )}
            {course.status === "PAUSED" && (
              <button
                type="button"
                onClick={() => lifecycleAction.mutate({ id: course.id, action: "resume" })}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                Resume
              </button>
            )}
            {course.status !== "COMPLETED" && (
              <button
                type="button"
                onClick={() => lifecycleAction.mutate({ id: course.id, action: "complete" })}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                Mark completed
              </button>
            )}
          </div>

          <LecturerAssignment courseId={course.id} />
          <TimetableManagement courseId={course.id} />
        </div>
      )}
    </div>
  );
}

function LecturerAssignment({ courseId }: { courseId: string }) {
  const { data: lecturers } = useLecturers();
  const { data: links } = useCourseLecturers(courseId);
  const attach = useAttachLecturer();
  const detach = useDetachLecturer();
  const [selectedLecturerId, setSelectedLecturerId] = useState("");

  const lecturerById = new Map((lecturers ?? []).map((l) => [l.id, l]));
  const attachedIds = new Set((links ?? []).map((l) => l.lecturer_id));
  const available = (lecturers ?? []).filter((l) => !attachedIds.has(l.id));

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700">Lecturers</h4>
      <div className="mt-2 space-y-1">
        {(links ?? []).map((link) => (
          <div key={link.lecturer_id} className="flex items-center justify-between text-sm">
            <span>
              {lecturerById.get(link.lecturer_id)?.name ?? link.lecturer_id}
              {link.is_primary && <span className="ml-2 text-xs text-purple-600">(primary)</span>}
            </span>
            <button
              type="button"
              onClick={() => detach.mutate({ courseId, lecturerId: link.lecturer_id })}
              className="text-xs font-medium text-red-600 hover:underline"
            >
              Detach
            </button>
          </div>
        ))}
        {(links ?? []).length === 0 && (
          <p className="text-sm text-gray-400">No lecturer assigned yet.</p>
        )}
      </div>
      {available.length > 0 && (
        <div className="mt-2 flex gap-2">
          <select
            value={selectedLecturerId}
            onChange={(e) => setSelectedLecturerId(e.target.value)}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
          >
            <option value="">Select a lecturer…</option>
            {available.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={!selectedLecturerId}
            onClick={() => {
              attach.mutate({ courseId, lecturerId: selectedLecturerId });
              setSelectedLecturerId("");
            }}
            className="rounded-md bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-700 disabled:opacity-50"
          >
            Attach
          </button>
        </div>
      )}
    </div>
  );
}

function TimetableManagement({ courseId }: { courseId: string }) {
  const { data: slots } = useTimetableSlots(courseId);
  const createSlot = useCreateTimetableSlot(courseId);
  const deleteSlot = useDeleteTimetableSlot(courseId);
  const [showForm, setShowForm] = useState(false);
  const [dayOfWeek, setDayOfWeek] = useState<DayOfWeek>("MONDAY");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [venue, setVenue] = useState("");
  const [mode, setMode] = useState<ClassMode>("IN_PERSON");
  const [reminderTime, setReminderTime] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    createSlot.mutate(
      {
        day_of_week: dayOfWeek,
        start_time: `${startTime}:00`,
        end_time: `${endTime}:00`,
        venue,
        mode,
        reminder_time: `${reminderTime}:00`,
        response_deadline_minutes: 60,
        retry_attempts: 1,
        retry_interval_minutes: 30,
      },
      {
        onSuccess: () => {
          setShowForm(false);
          setStartTime("");
          setEndTime("");
          setVenue("");
          setReminderTime("");
        },
        onError: () =>
          setError(
            "Check your times — reminder must be at or before the start time, and end must be after start.",
          ),
      },
    );
  }

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700">Timetable</h4>
      <div className="mt-2 space-y-1">
        {(slots ?? []).map((slot) => (
          <div key={slot.id} className="flex items-center justify-between text-sm">
            <span>
              {slot.day_of_week} {slot.start_time.slice(0, 5)}–{slot.end_time.slice(0, 5)} ·{" "}
              {slot.venue} · reminder at {slot.reminder_time.slice(0, 5)}
            </span>
            <button
              type="button"
              onClick={() => deleteSlot.mutate(slot.id)}
              className="text-xs font-medium text-red-600 hover:underline"
            >
              Remove
            </button>
          </div>
        ))}
        {(slots ?? []).length === 0 && (
          <p className="text-sm text-gray-400">No timetable slots yet.</p>
        )}
      </div>

      {!showForm && (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="mt-2 text-xs font-medium text-purple-600 hover:underline"
        >
          + Add slot
        </button>
      )}
      {showForm && (
        <form onSubmit={handleSubmit} className="mt-3 space-y-2 rounded-md border border-gray-200 p-3">
          {error && (
            <p className="rounded-md bg-red-50 px-2 py-1 text-xs text-red-700">{error}</p>
          )}
          <div className="flex flex-wrap gap-2">
            <select
              value={dayOfWeek}
              onChange={(e) => setDayOfWeek(e.target.value as DayOfWeek)}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            >
              {DAYS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <input
              type="time"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
            <span className="self-center text-sm text-gray-400">to</span>
            <input
              type="time"
              required
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
            <input
              required
              value={venue}
              onChange={(e) => setVenue(e.target.value)}
              placeholder="Venue"
              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as ClassMode)}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            >
              {MODES.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-1 text-sm text-gray-600">
              Reminder at
              <input
                type="time"
                required
                value={reminderTime}
                onChange={(e) => setReminderTime(e.target.value)}
                className="rounded-md border border-gray-300 px-2 py-1 text-sm"
              />
            </label>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createSlot.isPending}
              className="rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700 disabled:opacity-50"
            >
              {createSlot.isPending ? "Saving…" : "Save"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-md px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
