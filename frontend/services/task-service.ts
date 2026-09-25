import { apiClient } from "@/lib/api-client";
import type { ApiEnvelope, PaginatedResponse, Task, TaskMutationRequest, TaskStatus } from "@/types/api";

export const taskService = {
  async list(params: {
    page?: number;
    page_size?: number;
    status?: Task["status"];
    project?: number;
    assignee?: number | "null";
  } = {}) {
    const { data } = await apiClient.get<PaginatedResponse<Task>>("/api/tasks/", { params });
    return data;
  },
  async get(id: number) {
    const { data } = await apiClient.get<ApiEnvelope<Task>>(`/api/tasks/${id}/`);
    return data.data;
  },
  async create(payload: TaskMutationRequest) {
    const { data } = await apiClient.post<ApiEnvelope<Task>>("/api/tasks/", payload);
    return data.data;
  },
  async update(id: number, payload: Partial<TaskMutationRequest>) {
    const { data } = await apiClient.patch<ApiEnvelope<Task>>(`/api/tasks/${id}/`, payload);
    return data.data;
  },
  async updateStatus(id: number, status: TaskStatus) {
    const { data } = await apiClient.patch<ApiEnvelope<Task>>(
      `/api/tasks/${id}/status/`,
      { status },
    );
    return data.data;
  },
  async softDelete(id: number) {
    const { data } = await apiClient.delete<{ success: boolean; message: string }>(
      `/api/tasks/${id}/`,
    );
    return data;
  },
  async restore(id: number) {
    const { data } = await apiClient.post<ApiEnvelope<Task>>(`/api/tasks/${id}/restore/`);
    return data.data;
  },
};
