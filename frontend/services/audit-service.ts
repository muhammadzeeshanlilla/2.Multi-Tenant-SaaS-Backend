import { apiClient } from "@/lib/api-client";
import type { AuditLog, PaginatedResponse } from "@/types/api";

export const auditService = {
  async list(params: { page?: number; page_size?: number; action?: string } = {}) {
    const { data } = await apiClient.get<PaginatedResponse<AuditLog>>("/api/audit-logs/", { params });
    return data;
  },
};
