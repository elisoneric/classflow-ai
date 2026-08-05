import { useState } from "react";
import { useClassSessions, useClassSession, useApproveSession } from "@/api/classSessions";
import { useCourses } from "@/api/courses";
import { OverrideDialog } from "@/components/OverrideDialog";

export function PendingReviewPage() {
  const { data: sessions, isLoading } = useClassSessions({ status: "PENDING_REVIEW" });
  const { data: courses } = useCourses();
  const courseById = new Map((courses ?? []).map((c) => [c.id, c]));

  if (isLoading) {
    return <p className="text-sm text-gray-500">Loading…</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Pending Review</h1>
      <p className="mt-1 text-sm text-gray-500">
        Lecturer replies the AI wasn't confident enough to auto-announce.
      </p>

      <div className="mt-6 space-y-3">
        {(sessions ?? []).map((session) => (
          <PendingReviewCard
            key={session.id}
            sessionId={session.id}
            courseLabel={courseById.get(session.course_id)?.code ?? session.course_id}
          />
        ))}
        {(sessions ?? []).length === 0 && (
          <p className="text-sm text-gray-500">Nothing needs review right now.</p>
        )}
      </div>
    </div>
  );
}

function PendingReviewCard({
  sessionId,
  courseLabel,
}: {
  sessionId: string;
  courseLabel: string;
}) {
  const { data: session } = useClassSession(sessionId);
  const approve = useApproveSession();
  const [showReject, setShowReject] = useState(false);

  const latestResponse = session?.responses
    .slice()
    .sort((a, b) => b.received_at.localeCompare(a.received_at))[0];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-gray-900">{courseLabel}</p>
          <p className="text-sm text-gray-500">{session?.session_date}</p>
          {latestResponse && (
            <div className="mt-3 space-y-1 text-sm">
              <p className="text-gray-700">&ldquo;{latestResponse.cleaned_message}&rdquo;</p>
              <p className="text-gray-500">
                AI read: <span className="font-medium">{latestResponse.ai_status ?? "UNCLEAR"}</span>
                {latestResponse.ai_confidence != null &&
                  ` (${Math.round(latestResponse.ai_confidence * 100)}% confidence)`}
              </p>
            </div>
          )}
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() => approve.mutate({ id: sessionId })}
            disabled={approve.isPending}
            className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            Approve AI reading
          </button>
          <button
            type="button"
            onClick={() => setShowReject(true)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
          >
            Correct manually
          </button>
        </div>
      </div>
      {showReject && (
        <OverrideDialog sessionId={sessionId} mode="reject" onClose={() => setShowReject(false)} />
      )}
    </div>
  );
}
