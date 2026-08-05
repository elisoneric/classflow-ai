import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Course, CourseStatus } from "./types";

export function useCourses(semesterId?: string) {
  return useQuery({
    queryKey: ["courses", semesterId],
    queryFn: async () => {
      const { data } = await apiClient.get<Course[]>("/courses", {
        params: semesterId ? { semester_id: semesterId } : undefined,
      });
      return data;
    },
  });
}

export function useCourse(id: string | undefined) {
  return useQuery({
    queryKey: ["courses", id],
    queryFn: async () => {
      const { data } = await apiClient.get<Course>(`/courses/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

interface CreateCoursePayload {
  semester_id: string;
  code: string;
  title: string;
  announcement_email: string;
}

export function useCreateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateCoursePayload) => {
      const { data } = await apiClient.post<Course>("/courses", payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["courses"] }),
  });
}

export function useUpdateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: {
      id: string;
      title?: string;
      announcement_email?: string;
    }) => {
      const { data } = await apiClient.patch<Course>(`/courses/${id}`, payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["courses"] }),
  });
}

const LIFECYCLE_ACTION: Record<"pause" | "resume" | "complete", string> = {
  pause: "pause",
  resume: "resume",
  complete: "complete",
};

export function useCourseLifecycleAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      action,
    }: {
      id: string;
      action: "pause" | "resume" | "complete";
    }) => {
      const { data } = await apiClient.post<Course>(
        `/courses/${id}/${LIFECYCLE_ACTION[action]}`,
      );
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["courses"] }),
  });
}

export type { CourseStatus };
