"use client";

import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { setAuthFailureHandler } from "@/lib/api-client";
import { tokenStore } from "@/lib/auth-tokens";
import { normalizeApiError } from "@/lib/api-error";
import { authService } from "@/services/auth-service";
import type { LoginRequest, NormalizedApiError, User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  company: User["company"];
  role: User["role"] | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login(payload: LoginRequest): Promise<void>;
  logout(): Promise<void>;
  refreshSession(): Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  const refreshSession = useCallback(async () => {
    if (!tokenStore.getRefresh()) {
      clearSession();
      return;
    }
    const currentUser = await authService.me();
    setUser(currentUser);
  }, [clearSession]);

  useEffect(() => {
    setAuthFailureHandler(() => {
      clearSession();
      router.replace("/login?session=expired");
    });
    return () => setAuthFailureHandler(null);
  }, [clearSession, router]);

  useEffect(() => {
    let active = true;
    async function bootstrap() {
      try {
        if (!tokenStore.getRefresh()) return;
        const currentUser = await authService.me();
        if (active) setUser(currentUser);
      } catch {
        if (active) clearSession();
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void bootstrap();
    return () => {
      active = false;
    };
  }, [clearSession]);

  const login = useCallback(async (payload: LoginRequest) => {
    try {
      const response = await authService.login(payload);
      tokenStore.set(response.data.tokens);
      const currentUser = await authService.me();
      setUser(currentUser);
    } catch (error) {
      clearSession();
      throw normalizeApiError(error) satisfies NormalizedApiError;
    }
  }, [clearSession]);

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefresh();
    try {
      if (refresh) await authService.logout(refresh);
    } finally {
      clearSession();
      router.replace("/login");
    }
  }, [clearSession, router]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    company: user?.company ?? null,
    role: user?.role ?? null,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    logout,
    refreshSession,
  }), [isLoading, login, logout, refreshSession, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
