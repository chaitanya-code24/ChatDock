import { API_BASE_URL, apiJson } from "./api";

export type Bot = {
  id: string;
  user_id: string;
  bot_name: string;
  description: string | null;
  created_at: string;
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

export type AnalyticsOverview = {
  user_id: string;
  total_bots: number;
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  cached_queries: number;
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

export async function getAnalytics(token: string) {
  return apiJson<AnalyticsOverview>("/analytics/overview", { method: "GET" }, token);
}
