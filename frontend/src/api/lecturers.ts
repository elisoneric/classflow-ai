import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ContactMethod, CourseLecturerLink, Lecturer } from "./types";

export function useLecturers() {
  return useQuery({
    queryKey: ["lecturers"],
    queryFn: async () => {
      const { data } = await apiClient.get<Lecturer[]>("/lecturers");
      return data;
    },
  });
}

export function useCourseLecturers(courseId: string | undefined) {
  return useQuery({
    queryKey: ["course-lecturers", courseId],
    queryFn: async () => {
      const { data } = await apiClient.get<CourseLecturerLink[]>(
        `/courses/${courseId}/lecturers`,
      );
      return data;
    },
    enabled: Boolean(courseId),
  });
}

interface LecturerPayload {
  name: string;
  email: string;
  phone?: string;
  preferred_contact_method?: ContactMethod;
  fallback_contact_method?: ContactMethod;
}

export function useCreateLecturer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LecturerPayload) => {
      const { data } = await apiClient.post<Lecturer>("/lecturers", payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lecturers"] }),
  });
}

export function useDeleteLecturer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/lecturers/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lecturers"] }),
  });
}

export function useAttachLecturer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      courseId,
      lecturerId,
      isPrimary = true,
    }: {
      courseId: string;
      lecturerId: string;
      isPrimary?: boolean;
    }) => {
      const { data } = await apiClient.post<CourseLecturerLink>(
        `/courses/${courseId}/lecturers`,
        { lecturer_id: lecturerId, is_primary: isPrimary },
      );
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["course-lecturers"] }),
  });
}

export function useDetachLecturer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ courseId, lecturerId }: { courseId: string; lecturerId: string }) => {
      await apiClient.delete(`/courses/${courseId}/lecturers/${lecturerId}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["course-lecturers"] }),
  });
}
