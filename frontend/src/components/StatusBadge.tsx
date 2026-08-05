const STATUS_STYLES: Record<string, string> = {
  SCHEDULED: "bg-gray-100 text-gray-700",
  REMINDER_SENT: "bg-blue-100 text-blue-700",
  PENDING_REVIEW: "bg-amber-100 text-amber-700",
  RESOLVED: "bg-green-100 text-green-700",
  UNRESOLVED: "bg-red-100 text-red-700",
  ANNOUNCED: "bg-green-100 text-green-700",
  CONFIRMED: "bg-green-100 text-green-700",
  CANCELLED: "bg-red-100 text-red-700",
  DELAYED: "bg-amber-100 text-amber-700",
  RELOCATED: "bg-blue-100 text-blue-700",
  ONLINE: "bg-purple-100 text-purple-700",
  ACTIVE: "bg-green-100 text-green-700",
  PAUSED: "bg-amber-100 text-amber-700",
  COMPLETED: "bg-gray-100 text-gray-700",
};

export function StatusBadge({ value }: { value: string }) {
  const style = STATUS_STYLES[value] ?? "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${style}`}
    >
      {value.replace(/_/g, " ")}
    </span>
  );
}
