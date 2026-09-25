import { apiClient } from "@/lib/api-client";
import type {
  ApiEnvelope,
  LoginRequest,
  LoginResponse,
  RegistrationRequest,
  RegistrationResponse,
  User,
} from "@/types/api";

export const authService = {
  async login(payload: LoginRequest) {
    const { data } = await apiClient.post<LoginResponse>("/api/auth/login/", payload);
    return data;
  },
  async register(payload: RegistrationRequest) {
    const { data } = await apiClient.post<RegistrationResponse>(
      "/api/auth/company-register/",
      payload,
    );
    return data;
  },
  async me() {
    const { data } = await apiClient.get<ApiEnvelope<User>>("/api/auth/me/");
    return data.data;
  },
  async logout(refresh: string) {
    await apiClient.post("/api/auth/logout/", { refresh });
  },
};
