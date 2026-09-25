import type { TokenPair } from "@/types/api";

const ACCESS_TOKEN_KEY = "tenantflow.access";
const REFRESH_TOKEN_KEY = "tenantflow.refresh";

function storage() {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

export const tokenStore = {
  getAccess(): string | null {
    return storage()?.getItem(ACCESS_TOKEN_KEY) ?? null;
  },
  getRefresh(): string | null {
    return storage()?.getItem(REFRESH_TOKEN_KEY) ?? null;
  },
  set(tokens: TokenPair) {
    const target = storage();
    if (!target) return;
    target.setItem(ACCESS_TOKEN_KEY, tokens.access);
    target.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  },
  updateAccess(access: string, refresh?: string) {
    const target = storage();
    if (!target) return;
    target.setItem(ACCESS_TOKEN_KEY, access);
    if (refresh) target.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  clear() {
    const target = storage();
    target?.removeItem(ACCESS_TOKEN_KEY);
    target?.removeItem(REFRESH_TOKEN_KEY);
  },
};
