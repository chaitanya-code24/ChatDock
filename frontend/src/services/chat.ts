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
  conversation_id: string;
  answer: string;
  cached: boolean;
  sources: SourceChunk[];
  logs: string[];
};

export type ChatThreadMessage = {
  role: "assistant" | "user";
  text: string;
  created_at: string;
};

export type ChatThread = {
  id: string;
  bot_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatThreadMessage[];
  logs: string[];
};

export async function askBot(botId: string, message: string, token: string, conversationId?: string | null) {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ bot_id: botId, message, conversation_id: conversationId ?? undefined }),
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

export async function listChatThreads(botId: string, token: string) {
  const res = await fetch(`${API_BASE_URL}/chat/threads?bot_id=${botId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await res.json();
  if (!res.ok) {
    throw new Error(extractApiError(payload, "Could not load chat threads"));
  }
  return payload as ChatThread[];
}

export async function createChatThread(botId: string, token: string, title?: string) {
  const res = await fetch(`${API_BASE_URL}/chat/threads`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ bot_id: botId, title: title ?? null }),
  });
  const payload = await res.json();
  if (!res.ok) {
    throw new Error(extractApiError(payload, "Could not create chat thread"));
  }
  return payload as ChatThread;
}

export async function renameChatThread(botId: string, threadId: string, title: string, token: string) {
  const res = await fetch(`${API_BASE_URL}/chat/threads/${threadId}?bot_id=${botId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title }),
  });
  const payload = await res.json();
  if (!res.ok) {
    throw new Error(extractApiError(payload, "Could not rename chat thread"));
  }
  return payload as ChatThread;
}

export async function deleteChatThread(botId: string, threadId: string, token: string) {
  const res = await fetch(`${API_BASE_URL}/chat/threads/${threadId}?bot_id=${botId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await res.json();
  if (!res.ok) {
    throw new Error(extractApiError(payload, "Could not delete chat thread"));
  }
  return payload as { status: string };
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
