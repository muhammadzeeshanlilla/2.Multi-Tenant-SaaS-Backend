import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { tokenStore } from "@/lib/auth-tokens";
import type { RefreshResponse } from "@/types/api";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export const apiClient = axios.create({ baseURL, timeout: 15_000 });
const refreshClient = axios.create({ baseURL, timeout: 15_000 });

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };
let refreshPromise: Promise<string> | null = null;
let authFailureHandler: (() => void) | null = null;

export function setAuthFailureHandler(handler: (() => void) | null) {
  authFailureHandler = handler;
}

async function refreshAccessToken() {
  const refresh = tokenStore.getRefresh();
  if (!refresh) throw new Error("No refresh token is available.");

  const response = await refreshClient.post<RefreshResponse>(
    "/api/auth/token/refresh/",
    { refresh },
  );
  tokenStore.updateAccess(response.data.access, response.data.refresh);
  return response.data.access;
}

apiClient.interceptors.request.use((config) => {
  const access = tokenStore.getAccess();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    const isAuthEndpoint = original?.url?.startsWith("/api/auth/login/") ||
      original?.url?.startsWith("/api/auth/token/refresh/");

    if (error.response?.status !== 401 || !original || original._retry || isAuthEndpoint) {
      return Promise.reject(error);
    }

    original._retry = true;
    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
      const access = await refreshPromise;
      original.headers.Authorization = `Bearer ${access}`;
      return apiClient(original);
    } catch (refreshError) {
      tokenStore.clear();
      authFailureHandler?.();
      return Promise.reject(refreshError);
    }
  },
);
