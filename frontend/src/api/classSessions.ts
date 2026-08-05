import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  ClassMode,
  ClassSession,
  ClassSessionDetail,
  Reminder,
  SessionOutcome,
  SessionStatus,
} from "./types";

interface ListFilters {
  courseId?: string;
  status?: SessionStatus;
  dateFrom?: string;
  dateTo?: string;
}

export function useClassSessions(filters: ListFilters = {}) {
  return useQuery({
    queryKey: ["class-sessions", filters],
    queryFn: async () => {
      const { data } = await apiClient.get<ClassSession[]>("/class-sessions", {
        params: {
          course_id: filters.courseId,
          status: filters.status,
          date_from: filters.dateFrom,
          date_to: filters.dateTo,
        },
      });
      return data;
    },
  });
}

export function useClassSession(id: string | undefined) {
  return useQuery({
    queryKey: ["class-sessions", "detail", id],
    queryFn: async () => {
      const { data } = await apiClient.get<ClassSessionDetail>(`/class-sessions/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export interface OverridePayload {
  outcome: SessionOutcome;
  venue?: string;
  start_time?: string;
  mode?: ClassMode;
  note?: string;
}

function useSessionAction<TPayload = void, TResponse = ClassSession>(action: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload?: TPayload }) => {
      const { data } = await apiClient.post<TResponse>(
        `/class-sessions/${id}/${action}`,
        payload ?? {},
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["class-sessions"] });
    },
  });
}

export function useOverrideSession() {
  return useSessionAction<OverridePayload>("override");
}

export function useRejectSession() {
  return useSessionAction<OverridePayload>("reject");
}

export function useApproveSession() {
  return useSessionAction("approve");
}

export function useResendReminder() {
  return useSessionAction<void, Reminder>("resend-reminder");
}
