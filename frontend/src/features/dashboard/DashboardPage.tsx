import { useState } from "react";
import { format } from "date-fns";
import { useCourses } from "@/api/courses";
import { useClassSessions, useResendReminder } from "@/api/classSessions";
import type { ClassSession } from "@/api/types";
import { StatusBadge } from "@/components/StatusBadge";
import { OverrideDialog } from "@/components/OverrideDialog";

export function DashboardPage() {
  const today = format(new Date(), "yyyy-MM-dd");
  const { data: courses, isLoading: coursesLoading } = useCourses();
  const { data: sessions, isLoading: sessionsLoading } = useClassSessions({
    dateFrom: today,
    dateTo: today,
  });
  const resendReminder = useResendReminder();
  const [overrideSessionId, setOverrideSessionId] = useState<string | null>(null);

  if (coursesLoading || sessionsLoading) {
    return <p className="text-sm text-gray-500">Loading…</p>;
  }

  const activeCourses = (courses ?? []).filter((c) => c.status === "ACTIVE");
  const sessionByCourse = new Map<string, ClassSession>();
  for (const session of sessions ?? []) {
    sessionByCourse.set(session.course_id, session);
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">
        Today — {format(new Date(), "EEEE, MMMM d")}
      </h1>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {activeCourses.map((course) => {
          const session = sessionByCourse.get(course.id);
          return (
            <div
              key={course.id}
              className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-gray-900">{course.code}</p>
                  <p className="text-sm text-gray-500">{course.title}</p>
                </div>
                {session && <StatusBadge value={session.outcome ?? session.status} />}
              </div>

              {!session && (
                <p className="mt-3 text-sm text-gray-400">No class scheduled today.</p>
              )}

              {session && session.status !== "ANNOUNCED" && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setOverrideSessionId(session.id)}
                    className="rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
                  >
                    Override
                  </button>
                  <button
                    type="button"
                    onClick={() => resendReminder.mutate({ id: session.id })}
                    disabled={resendReminder.isPending}
                    className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Resend reminder
                  </button>
                </div>
              )}

              {session && session.status === "ANNOUNCED" && (
                <p className="mt-3 text-xs text-gray-400">
                  Announced
                  {session.announced_at && ` at ${format(new Date(session.announced_at), "p")}`}
                </p>
              )}
            </div>
          );
        })}

        {activeCourses.length === 0 && (
          <p className="text-sm text-gray-500">No active courses yet.</p>
        )}
      </div>

      {overrideSessionId && (
        <OverrideDialog
          sessionId={overrideSessionId}
          mode="override"
          onClose={() => setOverrideSessionId(null)}
        />
      )}
    </div>
  );
}
