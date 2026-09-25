import axios from "axios";
import type { FieldErrors, NormalizedApiError } from "@/types/api";

function toMessages(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(toMessages);
  if (typeof value === "string") return [value];
  if (value && typeof value === "object") {
    return Object.values(value as Record<string, unknown>).flatMap(toMessages);
  }
  return [];
}

export function normalizeApiError(error: unknown): NormalizedApiError {
  if (!axios.isAxiosError(error)) {
    return { message: "Something went wrong. Please try again.", fields: {} };
  }

  if (!error.response) {
    return {
      message: "Unable to reach the server. Check your connection and try again.",
      fields: {},
    };
  }

  const status = error.response.status;
  const body = error.response.data as Record<string, unknown> | undefined;
  const rawFields = (body?.errors ?? body) as Record<string, unknown> | undefined;
  const fields: FieldErrors = {};

  if (rawFields && typeof rawFields === "object") {
    for (const [key, value] of Object.entries(rawFields)) {
      if (["success", "message", "detail"].includes(key)) continue;
      const messages = toMessages(value);
      if (messages.length) fields[key] = messages;
    }
  }

  const fallback: Record<number, string> = {
    400: "Please review the highlighted information.",
    401: "Your session is invalid or has expired.",
    403: "You do not have permission to perform this action.",
    404: "The requested record could not be found.",
    429: "Too many requests. Please wait and try again.",
    500: "The server encountered an error. Please try again later.",
  };
  const detail = typeof body?.detail === "string" ? body.detail : undefined;
  const message = typeof body?.message === "string" ? body.message : undefined;
  const firstFieldMessage = Object.values(fields)[0]?.[0];

  return {
    status,
    fields,
    message: message ?? detail ?? firstFieldMessage ?? fallback[status] ?? "Request failed.",
  };
}
