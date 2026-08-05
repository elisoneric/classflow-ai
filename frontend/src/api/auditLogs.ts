import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { AuditLog } from "./types";

export function useAuditLogs(entityId: string | undefined) {
  return useQuery({
    queryKey: ["audit-logs", entityId],
    queryFn: async () => {
      const { data } = await apiClient.get<AuditLog[]>("/audit-logs", {
        params: { entity_type: "CLASS_SESSION", entity_id: entityId },
      });
      return data;
    },
    enabled: Boolean(entityId),
  });
}
