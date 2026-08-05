import { useState } from "react";
import { format } from "date-fns";
import { useClassSession, useClassSessions } from "@/api/classSessions";
import { useCourses } from "@/api/courses";
import { useAuditLogs } from "@/api/auditLogs";
import { StatusBadge } from "@/components/StatusBadge";

export function SessionHistoryPage() {
  const { data: courses } = useCourses();
  const [courseId, setCourseId] = useState("");
  const { data: sessions, isLoading } = useClassSessions({ courseId: courseId || undefined });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const courseById = new Map((courses ?? []).map((c) => [c.id, c]));

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <h1 className="text-2xl font-semibold text-gray-900">Session History</h1>
        <div className="mt-4">
          <select
            value={courseId}
            onChange={(e) => setCourseId(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All courses</option>
            {(courses ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.code}
              </option>
            ))}
          </select>
        </div>

        {isLoading && <p className="mt-4 text-sm text-gray-500">Loading…</p>}

        <div className="mt-4 overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs font-medium tracking-wide text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Course</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(sessions ?? []).map((session) => (
                <tr
                  key={session.id}
                  onClick={() => setSelectedId(session.id)}
                  className={`cursor-pointer hover:bg-gray-50 ${
                    selectedId === session.id ? "bg-purple-50" : ""
                  }`}
                >
                  <td className="px-4 py-2">{session.session_date}</td>
                  <td className="px-4 py-2">
                    {courseById.get(session.course_id)?.code ?? session.course_id}
                  </td>
                  <td className="px-4 py-2">
                    <StatusBadge value={session.status} />
                  </td>
                  <td className="px-4 py-2">
                    {session.outcome ? <StatusBadge value={session.outcome} /> : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(sessions ?? []).length === 0 && !isLoading && (
            <p className="px-4 py-6 text-center text-sm text-gray-500">No sessions found.</p>
          )}
        </div>
      </div>

      {selectedId && (
        <SessionDetailDrawer sessionId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}

function SessionDetailDrawer({
  sessionId,
  onClose,
}: {
  sessionId: string;
  onClose: () => void;
}) {
  const { data: session } = useClassSession(sessionId);
  const { data: auditLogs } = useAuditLogs(sessionId);

  return (
    <div className="w-96 shrink-0 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Session detail</h2>
        <button type="button" onClick={onClose} className="text-sm text-gray-400 hover:text-gray-600">
          Close
        </button>
      </div>

      {session && (
        <div className="mt-3 space-y-4 text-sm">
          <div>
            <p className="text-gray-500">Scheduled</p>
            <p>
              {session.session_date} at {session.scheduled_start_time.slice(0, 5)} ·{" "}
              {session.venue}
            </p>
          </div>

          {session.reminders.length > 0 && (
            <div>
              <p className="mb-1 font-medium text-gray-700">Reminders</p>
              {session.reminders.map((r) => (
                <p key={r.id} className="text-gray-600">
                  Attempt {r.attempt_number} — {r.status} ({format(new Date(r.sent_at), "PPp")})
                </p>
              ))}
            </div>
          )}

          {session.responses.length > 0 && (
            <div>
              <p className="mb-1 font-medium text-gray-700">Lecturer responses</p>
              {session.responses.map((r) => (
                <p key={r.id} className="text-gray-600">
                  &ldquo;{r.cleaned_message}&rdquo; — AI: {r.ai_status ?? "UNCLEAR"}
                  {r.ai_confidence != null && ` (${Math.round(r.ai_confidence * 100)}%)`}
                </p>
              ))}
            </div>
          )}

          {session.announcements.length > 0 && (
            <div>
              <p className="mb-1 font-medium text-gray-700">Announcements</p>
              {session.announcements.map((a) => (
                <p key={a.id} className="text-gray-600">
                  {a.status} to {a.recipient}
                </p>
              ))}
            </div>
          )}

          <div>
            <p className="mb-1 font-medium text-gray-700">Audit trail</p>
            {(auditLogs ?? []).map((log) => (
              <p key={log.id} className="text-gray-600">
                {format(new Date(log.created_at), "PPp")} — {log.action} ({log.actor})
              </p>
            ))}
            {(auditLogs ?? []).length === 0 && (
              <p className="text-gray-400">No audit entries.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
