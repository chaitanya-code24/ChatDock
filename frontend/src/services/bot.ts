import { API_BASE_URL, apiJson } from "./api";

export type Bot = {
  id: string;
  user_id: string;
  bot_name: string;
  description: string | null;
  created_at: string;
  archived: boolean;
  tone: "professional" | "friendly" | "technical";
  answer_length: "short" | "balanced" | "detailed";
  fallback_behavior: "strict" | "helpful";
  system_prompt: string | null;
  greeting_message: string | null;
  updated_at?: string | null;
  document_count: number;
  chunk_count: number;
};

export type DocumentSummary = {
  id: string;
  bot_id: string;
  file_name: string;
  uploaded_at: string;
  chunk_count: number;
  mime_type: string;
};

export async function listDocuments(token: string, botId: string) {
  return apiJson<DocumentSummary[]>(`/bot/documents?bot_id=${botId}`, { method: "GET" }, token);
}

export async function deleteDocument(token: string, botId: string, documentId: string) {
  return apiJson<{ status: string }>(`/bot/document/${documentId}?bot_id=${botId}`, { method: "DELETE" }, token);
}

export type TopQuery = {
  question: string;
  count: number;
};

export type BotQueryStat = {
  bot_id: string;
  bot_name: string;
  queries: number;
};

export type AnalyticsOverview = {
  user_id: string;
  selected_bot_id?: string | null;
  selected_bot_name?: string | null;
  total_bots: number;
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  cached_queries: number;
  top_queries?: TopQuery[];
  query_trend_last_7_days?: number[];
  bot_queries?: BotQueryStat[];
};

export async function createBot(token: string, botName: string, description?: string) {
  return apiJson<Bot>(
    "/bot/create",
    {
      method: "POST",
      body: JSON.stringify({ bot_name: botName, description: description || null }),
    },
    token,
  );
}

export async function listBots(token: string) {
  return apiJson<Bot[]>("/bot/list", { method: "GET" }, token);
}

export async function getBot(token: string, botId: string) {
  return apiJson<Bot>(`/bot/${botId}`, { method: "GET" }, token);
}

export async function updateBot(
  token: string,
  botId: string,
  payload: {
    bot_name?: string;
    description?: string | null;
    tone?: "professional" | "friendly" | "technical";
    answer_length?: "short" | "balanced" | "detailed";
    fallback_behavior?: "strict" | "helpful";
    system_prompt?: string | null;
    greeting_message?: string | null;
  },
) {
  return apiJson<Bot>(
    `/bot/${botId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export async function archiveBot(token: string, botId: string, archived: boolean) {
  return apiJson<Bot>(
    `/bot/${botId}/archive`,
    {
      method: "POST",
      body: JSON.stringify({ archived }),
    },
    token,
  );
}

export async function reindexBot(token: string, botId: string) {
  return apiJson<Bot>(`/bot/${botId}/reindex`, { method: "POST" }, token);
}

export async function deleteBot(token: string, botId: string) {
  return apiJson<{ status: string }>(`/bot/${botId}`, { method: "DELETE" }, token);
}

export async function uploadDocument(token: string, botId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}/bot/upload?bot_id=${botId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.detail || "Upload failed");
  }
  return payload as DocumentSummary;
}

export async function getAnalytics(token: string, botId?: string) {
  const suffix = botId ? `?bot_id=${encodeURIComponent(botId)}` : "";
  return apiJson<AnalyticsOverview>(`/analytics/overview${suffix}`, { method: "GET" }, token);
}
