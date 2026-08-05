import { useState, type FormEvent } from "react";
import { useCreateLecturer, useDeleteLecturer, useLecturers } from "@/api/lecturers";

export function LecturersPage() {
  const { data: lecturers, isLoading } = useLecturers();
  const createLecturer = useCreateLecturer();
  const deleteLecturer = useDeleteLecturer();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    createLecturer.mutate(
      { name, email, phone: phone || undefined },
      {
        onSuccess: () => {
          setName("");
          setEmail("");
          setPhone("");
        },
        onError: () => setError("Could not create lecturer — that email may already be in use."),
      },
    );
  }

  function handleDelete(id: string) {
    deleteLecturer.mutate(id, {
      onError: () => setError("Could not remove lecturer — detach them from any courses first."),
    });
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Lecturers</h1>
      {isLoading && <p className="mt-4 text-sm text-gray-500">Loading…</p>}

      <div className="mt-4 divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
        {(lecturers ?? []).map((lecturer) => (
          <div key={lecturer.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="font-medium text-gray-900">{lecturer.name}</p>
              <p className="text-sm text-gray-500">
                {lecturer.email}
                {lecturer.phone ? ` · ${lecturer.phone}` : ""}
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleDelete(lecturer.id)}
              className="rounded-md px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
            >
              Remove
            </button>
          </div>
        ))}
        {(lecturers ?? []).length === 0 && !isLoading && (
          <p className="px-4 py-3 text-sm text-gray-500">No lecturers yet.</p>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-6 max-w-md space-y-3 rounded-lg border border-gray-200 bg-white p-4"
      >
        <h3 className="font-medium text-gray-900">New lecturer</h3>
        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Phone (optional)</span>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
          />
        </label>
        <button
          type="submit"
          disabled={createLecturer.isPending}
          className="rounded-md bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
        >
          {createLecturer.isPending ? "Adding…" : "Add lecturer"}
        </button>
      </form>
    </div>
  );
}
