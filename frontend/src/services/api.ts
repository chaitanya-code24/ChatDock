export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiJson<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const raw = await response.text();
  let payload: unknown = null;
  try {
    payload = raw ? JSON.parse(raw) : null;
  } catch {
    payload = raw;
  }

  if (!response.ok) {
    throw new Error(extractApiError(payload, "Request failed"));
  }
  return payload as T;
}

function extractApiError(payload: unknown, fallback: string): string {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }
  if (typeof payload !== "object" || payload === null) {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: unknown; loc?: unknown } | undefined;
    if (!first) {
      return fallback;
    }
    const msg = typeof first.msg === "string" ? first.msg : "Validation failed";
    const loc = Array.isArray(first.loc) ? first.loc.join(".") : "";
    return loc ? `${loc}: ${msg}` : msg;
  }

  return fallback;
}
