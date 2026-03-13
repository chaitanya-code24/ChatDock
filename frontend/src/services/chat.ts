import { API_BASE_URL } from "./api";

export type SourceChunk = {
  document_id: string;
  document_name: string;
  chunk_id: string;
  score: number;
  excerpt: string;
};

export type ChatResponse = {
  bot_id: string;
  answer: string;
  cached: boolean;
  sources: SourceChunk[];
};

export async function askBot(botId: string, message: string, token: string) {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ bot_id: botId, message }),
  });
  const raw = await res.text();
  let payload: unknown = null;
  try {
    payload = raw ? JSON.parse(raw) : null;
  } catch {
    payload = raw;
  }
  if (!res.ok) {
    throw new Error(extractApiError(payload, "Chat request failed"));
  }
  return payload as ChatResponse;
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
