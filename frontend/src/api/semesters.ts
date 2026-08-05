import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Semester } from "./types";

export function useSemesters() {
  return useQuery({
    queryKey: ["semesters"],
    queryFn: async () => {
      const { data } = await apiClient.get<Semester[]>("/semesters");
      return data;
    },
  });
}

export function useCreateSemester() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name: string;
      start_date: string;
      end_date: string;
      timezone?: string;
    }) => {
      const { data } = await apiClient.post<Semester>("/semesters", payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["semesters"] }),
  });
}

export function useActivateSemester() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<Semester>(`/semesters/${id}/activate`);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["semesters"] }),
  });
}
