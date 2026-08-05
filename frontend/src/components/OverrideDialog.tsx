import { useState, type FormEvent } from "react";
import { useOverrideSession, useRejectSession } from "@/api/classSessions";
import type { SessionOutcome } from "@/api/types";

interface OverrideDialogProps {
  sessionId: string;
  mode: "override" | "reject";
  onClose: () => void;
}

const OUTCOMES: { value: SessionOutcome; label: string }[] = [
  { value: "CONFIRMED", label: "Confirmed — holding as scheduled" },
  { value: "CANCELLED", label: "Cancelled — no class today" },
  { value: "DELAYED", label: "Delayed — starting later" },
  { value: "RELOCATED", label: "Relocated — different venue" },
  { value: "ONLINE", label: "Online — moved online" },
];

export function OverrideDialog({ sessionId, mode, onClose }: OverrideDialogProps) {
  const [outcome, setOutcome] = useState<SessionOutcome>("CANCELLED");
  const [venue, setVenue] = useState("");
  const [startTime, setStartTime] = useState("");
  const [note, setNote] = useState("");

  const overrideMutation = useOverrideSession();
  const rejectMutation = useRejectSession();
  const mutation = mode === "override" ? overrideMutation : rejectMutation;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(
      {
        id: sessionId,
        payload: {
          outcome,
          venue: outcome === "RELOCATED" ? venue : undefined,
          start_time: outcome === "DELAYED" ? `${startTime}:00` : undefined,
          mode: outcome === "ONLINE" ? "ONLINE" : undefined,
          note: note || undefined,
        },
      },
      { onSuccess: onClose },
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg"
      >
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          {mode === "override" ? "Override class status" : "Correct AI interpretation"}
        </h2>

        <label className="mb-3 block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Outcome</span>
          <select
            value={outcome}
            onChange={(e) => setOutcome(e.target.value as SessionOutcome)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
          >
            {OUTCOMES.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        {outcome === "DELAYED" && (
          <label className="mb-3 block text-sm">
            <span className="mb-1 block font-medium text-gray-700">New start time</span>
            <input
              type="time"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
            />
          </label>
        )}

        {outcome === "RELOCATED" && (
          <label className="mb-3 block text-sm">
            <span className="mb-1 block font-medium text-gray-700">New venue</span>
            <input
              type="text"
              required
              value={venue}
              onChange={(e) => setVenue(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
            />
          </label>
        )}

        <label className="mb-4 block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Note (optional)</span>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
          />
        </label>

        {mutation.isError && (
          <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            Something went wrong. Please try again.
          </p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-md bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Saving…" : "Announce"}
          </button>
        </div>
      </form>
    </div>
  );
}
