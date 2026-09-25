import { apiClient } from "@/lib/api-client";
import type {
  ApiEnvelope,
  CreateUserRequest,
  PaginatedResponse,
  UpdateUserRequest,
  User,
} from "@/types/api";

export const userService = {
  async list(page = 1, pageSize = 20) {
    const { data } = await apiClient.get<PaginatedResponse<User>>("/api/users/", {
      params: { page, page_size: pageSize },
    });
    return data;
  },
  async listAllActive() {
    const first = await this.list(1, 100);
    const users = [...first.data];
    for (let page = 2; users.length < first.count; page += 1) {
      const next = await this.list(page, 100);
      users.push(...next.data);
      if (!next.next) break;
    }
    return users.filter((user) => user.is_active && !user.is_deleted);
  },
  async get(id: number) {
    const { data } = await apiClient.get<ApiEnvelope<User>>(`/api/users/${id}/`);
    return data.data;
  },
  async create(payload: CreateUserRequest) {
    const { data } = await apiClient.post<ApiEnvelope<User>>("/api/users/", payload);
    return data.data;
  },
  async update(id: number, payload: UpdateUserRequest) {
    const { data } = await apiClient.patch<ApiEnvelope<User>>(`/api/users/${id}/`, payload);
    return data.data;
  },
  async softDelete(id: number) {
    const { data } = await apiClient.delete<{ success: boolean; message: string }>(
      `/api/users/${id}/`,
    );
    return data;
  },
  async restore(id: number) {
    const { data } = await apiClient.post<ApiEnvelope<User>>(`/api/users/${id}/restore/`);
    return data.data;
  },
};
