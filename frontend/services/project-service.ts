import { apiClient } from "@/lib/api-client";
import type { ApiEnvelope, PaginatedResponse, Project, ProjectMutationRequest } from "@/types/api";

export const projectService = {
  async list(params: { page?: number; page_size?: number; status?: Project["status"] } = {}) {
    const { data } = await apiClient.get<PaginatedResponse<Project>>("/api/projects/", { params });
    return data;
  },
  async listAll() {
    const first = await this.list({ page: 1, page_size: 100 });
    const items = [...first.data];
    for (let page = 2; items.length < first.count; page += 1) {
      const next = await this.list({ page, page_size: 100 });
      items.push(...next.data);
      if (!next.next) break;
    }
    return items;
  },
  async get(id: number) {
    const { data } = await apiClient.get<ApiEnvelope<Project>>(`/api/projects/${id}/`);
    return data.data;
  },
  async create(payload: ProjectMutationRequest) {
    const { data } = await apiClient.post<ApiEnvelope<Project>>("/api/projects/", payload);
    return data.data;
  },
  async update(id: number, payload: Partial<ProjectMutationRequest>) {
    const { data } = await apiClient.patch<ApiEnvelope<Project>>(`/api/projects/${id}/`, payload);
    return data.data;
  },
  async assignUsers(id: number, userIds: number[]) {
    const { data } = await apiClient.post<ApiEnvelope<Project>>(
      `/api/projects/${id}/assign-users/`,
      { user_ids: userIds },
    );
    return data.data;
  },
  async softDelete(id: number) {
    const { data } = await apiClient.delete<{ success: boolean; message: string }>(
      `/api/projects/${id}/`,
    );
    return data;
  },
  async restore(id: number) {
    const { data } = await apiClient.post<ApiEnvelope<Project>>(`/api/projects/${id}/restore/`);
    return data.data;
  },
};
