import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ClassMode, ContactMethod, DayOfWeek, TimetableSlot } from "./types";

export function useTimetableSlots(courseId: string | undefined) {
  return useQuery({
    queryKey: ["timetable-slots", courseId],
    queryFn: async () => {
      const { data } = await apiClient.get<TimetableSlot[]>(
        `/courses/${courseId}/timetable-slots`,
      );
      return data;
    },
    enabled: Boolean(courseId),
  });
}

export interface TimetableSlotPayload {
  day_of_week: DayOfWeek;
  start_time: string;
  end_time: string;
  venue: string;
  mode: ClassMode;
  reminder_time: string;
  response_deadline_minutes: number;
  retry_attempts: number;
  retry_interval_minutes: number;
  fallback_contact_method_override?: ContactMethod;
}

export function useCreateTimetableSlot(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TimetableSlotPayload) => {
      const { data } = await apiClient.post<TimetableSlot>(
        `/courses/${courseId}/timetable-slots`,
        payload,
      );
      return data;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["timetable-slots", courseId] }),
  });
}

export function useDeleteTimetableSlot(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (slotId: string) => {
      await apiClient.delete(`/timetable-slots/${slotId}`);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["timetable-slots", courseId] }),
  });
}
