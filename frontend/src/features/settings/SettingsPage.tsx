import { useState, type FormEvent } from "react";
import { useActivateSemester, useCreateSemester, useSemesters } from "@/api/semesters";
import { StatusBadge } from "@/components/StatusBadge";

export function SettingsPage() {
  const { data: semesters, isLoading } = useSemesters();
  const createSemester = useCreateSemester();
  const activateSemester = useActivateSemester();
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createSemester.mutate(
      { name, start_date: startDate, end_date: endDate },
      {
        onSuccess: () => {
          setName("");
          setStartDate("");
          setEndDate("");
        },
      },
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>

      <section className="mt-6">
        <h2 className="text-lg font-medium text-gray-900">Semesters</h2>
        {isLoading && <p className="mt-2 text-sm text-gray-500">Loading…</p>}

        <div className="mt-3 divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {(semesters ?? []).map((semester) => (
            <div key={semester.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="font-medium text-gray-900">{semester.name}</p>
                <p className="text-sm text-gray-500">
                  {semester.start_date} – {semester.end_date}
                </p>
              </div>
              {semester.is_active ? (
                <StatusBadge value="ACTIVE" />
              ) : (
                <button
                  type="button"
                  onClick={() => activateSemester.mutate(semester.id)}
                  disabled={activateSemester.isPending}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Set active
                </button>
              )}
            </div>
          ))}
          {(semesters ?? []).length === 0 && !isLoading && (
            <p className="px-4 py-3 text-sm text-gray-500">No semesters yet — create one below.</p>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-6 max-w-md space-y-3 rounded-lg border border-gray-200 bg-white p-4"
        >
          <h3 className="font-medium text-gray-900">New semester</h3>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700">Name</span>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="2025/2026 Second Semester"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
            />
          </label>
          <div className="flex gap-3">
            <label className="block flex-1 text-sm">
              <span className="mb-1 block font-medium text-gray-700">Start date</span>
              <input
                type="date"
                required
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
              />
            </label>
            <label className="block flex-1 text-sm">
              <span className="mb-1 block font-medium text-gray-700">End date</span>
              <input
                type="date"
                required
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={createSemester.isPending}
            className="rounded-md bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {createSemester.isPending ? "Creating…" : "Create semester"}
          </button>
        </form>
      </section>
    </div>
  );
}
