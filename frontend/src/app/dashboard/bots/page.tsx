"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AppShell } from "../../../components/dashboard/app-shell";
import { API_BASE_URL } from "../../../services/api";
import { getToken } from "../../../services/auth";
import {
  archiveBot,
  listBots,
  listDocuments,
  reindexBot,
  updateBot,
  uploadDocument,
  deleteDocument,
  type Bot,
  type DocumentSummary,
} from "../../../services/bot";
import { askBot, createChatThread, deleteChatThread, listChatThreads, renameChatThread } from "../../../services/chat";

type Section = "manage" | "chat" | "integrations";
type ManageTab = "documents" | "settings";
type IntegrationTab = "widget" | "api";

type Message = {
  role: "assistant" | "user";
  text: string;
  createdAt: string;
};

type ChatThread = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  conversationId: string | null;
  messages: Message[];
  logs: string[];
};

const EXTENSION_ICONS: Record<string, string> = {
  pdf: "PDF",
  txt: "TXT",
  docx: "DOCX",
  md: "MD",
};

function mapThreadFromApi(thread: {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: { role: "assistant" | "user"; text: string; created_at: string }[];
  logs: string[];
}): ChatThread {
  return {
    id: thread.id,
    title: thread.title,
    createdAt: thread.created_at,
    updatedAt: thread.updated_at,
    conversationId: thread.id,
    logs: thread.logs ?? [],
    messages: (thread.messages ?? []).map((message) => ({
      role: message.role,
      text: message.text,
      createdAt: new Date(message.created_at).toLocaleTimeString(),
    })),
  };
}

function buildThreadTitle(messages: Message[]) {
  const firstUserMessage = messages.find((message) => message.role === "user")?.text.trim();
  if (!firstUserMessage) {
    return "New chat";
  }
  return firstUserMessage.length > 42 ? `${firstUserMessage.slice(0, 42).trim()}...` : firstUserMessage;
}

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBotId, setSelectedBotId] = useState("");
  const [section, setSection] = useState<Section>("manage");
  const [manageTab, setManageTab] = useState<ManageTab>("documents");
  const [integrationTab, setIntegrationTab] = useState<IntegrationTab>("widget");
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState("");
  const [selectedUploadFiles, setSelectedUploadFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState({ done: 0, total: 0 });
  const [uploadedDocuments, setUploadedDocuments] = useState<DocumentSummary[]>([]);
  const [settingsForm, setSettingsForm] = useState({
    bot_name: "",
    description: "",
    tone: "professional" as "professional" | "friendly" | "technical",
    answer_length: "balanced" as "short" | "balanced" | "detailed",
    fallback_behavior: "strict" as "strict" | "helpful",
    system_prompt: "",
    greeting_message: "",
  });
  const [savingSettings, setSavingSettings] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [archiving, setArchiving] = useState(false);
  const [threadActionId, setThreadActionId] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [chatLogs, setChatLogs] = useState<string[]>([]);
  const [chatThreads, setChatThreads] = useState<ChatThread[]>([]);
  const [activeChatId, setActiveChatId] = useState("");
  const chatContainerRef = useRef<HTMLDivElement | null>(null);


  const router = useRouter();
  const selectedBot = bots.find((bot) => bot.id === selectedBotId) ?? null;
  const botArchived = selectedBot?.archived ?? false;
  const activeThread = useMemo(
    () => chatThreads.find((thread) => thread.id === activeChatId) ?? chatThreads[0] ?? null,
    [activeChatId, chatThreads],
  );
  const messages = useMemo(() => activeThread?.messages ?? [], [activeThread]);
  const conversationId = activeThread?.conversationId ?? null;
  const sessionToken = useMemo(() => getToken() ?? "YOUR_SESSION_TOKEN", []);
  const widgetScriptUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return "/widget.js";
    }
    return `${window.location.origin}/widget.js`;
  }, []);
  const statusTone = useMemo(() => {
    const normalized = status.toLowerCase();
    if (!normalized) {
      return "info";
    }
    if (
      normalized.includes("failed") ||
      normalized.includes("could not") ||
      normalized.includes("error") ||
      normalized.includes("delete failed") ||
      normalized.includes("upload failed")
    ) {
      return "error";
    }
    if (
      normalized.includes("uploading") ||
      normalized.includes("reindexing") ||
      normalized.includes("generating") ||
      normalized.includes("replying")
    ) {
      return "loading";
    }
    if (normalized.includes("archived") || normalized.includes("restore")) {
      return "warn";
    }
    return "success";
  }, [status]);

  const updateActiveThread = useCallback(
    (updater: (thread: ChatThread) => ChatThread) => {
      setChatThreads((prev) => {
        const currentThread = prev.find((thread) => thread.id === activeChatId) ?? prev[0];
        if (!currentThread) {
          return prev;
        }
        const nextThreads = prev.map((thread) => (
          thread.id === currentThread.id
            ? updater(thread)
            : thread
        )).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
        return nextThreads;
      });
    },
    [activeChatId],
  );

  const refreshBots = useCallback(
    async (token: string) => {
      const data = await listBots(token);
      setBots(data);
      const queryBotId =
        typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("botId") : null;
      if (queryBotId && data.some((bot) => bot.id === queryBotId)) {
        setSelectedBotId(queryBotId);
        return;
      }
      setSelectedBotId((prev) => (prev && data.some((bot) => bot.id === prev) ? prev : data[0]?.id ?? ""));
    },
    [],
  );

  const refreshDocuments = useCallback(
    async (token: string, botId: string) => {
      if (!botId) {
        setUploadedDocuments([]);
        return;
      }
      const docs = await listDocuments(token, botId);
      setUploadedDocuments(docs);
    },
    [],
  );

  const refreshThreads = useCallback(
    async (token: string, botId: string) => {
      const data = await listChatThreads(botId, token);
      const mapped = data.map(mapThreadFromApi);
      if (mapped.length === 0) {
        const created = await createChatThread(botId, token);
        const createdMapped = mapThreadFromApi(created);
        setChatThreads([createdMapped]);
        setActiveChatId(createdMapped.id);
        setChatLogs(createdMapped.logs);
        return;
      }
      setChatThreads(mapped);
      setActiveChatId((prev) => (prev && mapped.some((thread) => thread.id === prev) ? prev : mapped[0].id));
      setChatLogs(mapped[0]?.logs ?? []);
    },
    [],
  );

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    void refreshBots(token).catch(() => setStatus("Failed to load bot list."));
  }, [refreshBots, router]);

  useEffect(() => {
    const token = getToken();
    if (!token || !selectedBotId) {
      return;
    }
    void refreshDocuments(token, selectedBotId).catch((err) => {
      setStatus(readError(err, "Failed to load documents."));
    });
  }, [refreshDocuments, selectedBotId]);

  useEffect(() => {
    const token = getToken();
    if (!token || !selectedBotId) {
      return;
    }
    void refreshThreads(token, selectedBotId).catch((err) => {
      setStatus(readError(err, "Failed to load chat history."));
    });
  }, [refreshThreads, selectedBotId]);

  useEffect(() => {
    if (!chatContainerRef.current) return;
    chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
  }, [messages, activeChatId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const s = params.get("section");
    if (s === "manage" || s === "chat" || s === "integrations") {
      setSection(s);
    }
  }, []);

  useEffect(() => {
    if (!selectedBot) {
      return;
    }
    setSettingsForm({
      bot_name: selectedBot.bot_name,
      description: selectedBot.description ?? "",
      tone: selectedBot.tone ?? "professional",
      answer_length: selectedBot.answer_length ?? "balanced",
      fallback_behavior: selectedBot.fallback_behavior ?? "strict",
      system_prompt: selectedBot.system_prompt ?? "",
      greeting_message: selectedBot.greeting_message ?? "",
    });
  }, [selectedBot]);

  useEffect(() => {
    setChatLogs(activeThread?.logs ?? []);
  }, [activeThread]);

  useEffect(() => {
    if (!status) {
      return;
    }
    const timeout = window.setTimeout(() => setStatus(""), statusTone === "loading" ? 1800 : 3200);
    return () => window.clearTimeout(timeout);
  }, [status, statusTone]);

  async function onSaveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !selectedBotId || savingSettings) {
      return;
    }
    if (settingsForm.bot_name.trim().length < 2) {
      setStatus("Bot name should be at least 2 characters.");
      return;
    }
    setSavingSettings(true);
    setStatus("");
    try {
      await updateBot(token, selectedBotId, {
        bot_name: settingsForm.bot_name.trim(),
        description: settingsForm.description.trim() || null,
        tone: settingsForm.tone,
        answer_length: settingsForm.answer_length,
        fallback_behavior: settingsForm.fallback_behavior,
        system_prompt: settingsForm.system_prompt.trim() || null,
        greeting_message: settingsForm.greeting_message.trim() || null,
      });
      await refreshBots(token);
      setStatus("Bot settings updated.");
    } catch (err) {
      setStatus(readError(err, "Could not update bot settings."));
    } finally {
      setSavingSettings(false);
    }
  }

  async function onArchiveToggle() {
    const token = getToken();
    if (!token || !selectedBotId || !selectedBot || archiving) {
      return;
    }
    setArchiving(true);
    setStatus("");
    try {
      await archiveBot(token, selectedBotId, !selectedBot.archived);
      await refreshBots(token);
      setStatus(selectedBot.archived ? "Bot restored." : "Bot archived.");
    } catch (err) {
      setStatus(readError(err, "Could not update bot archive state."));
    } finally {
      setArchiving(false);
    }
  }

  async function onReindexBot() {
    const token = getToken();
    if (!token || !selectedBotId || reindexing) {
      return;
    }
    setReindexing(true);
    setStatus("");
    try {
      await reindexBot(token, selectedBotId);
      await refreshBots(token);
      await refreshDocuments(token, selectedBotId);
      setStatus("Bot knowledge reindexed.");
    } catch (err) {
      setStatus(readError(err, "Reindex failed."));
    } finally {
      setReindexing(false);
    }
  }

  async function onCreateNewChat() {
    const token = getToken();
    if (!selectedBotId || !token) {
      return;
    }
    try {
      const created = await createChatThread(selectedBotId, token);
      const nextThread = mapThreadFromApi(created);
      setChatThreads((prev) => [nextThread, ...prev].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)));
      setActiveChatId(nextThread.id);
      setChatLogs([]);
      setChatInput("");
      setStatus("Started a new chat.");
    } catch (err) {
      setStatus(readError(err, "Could not create a new chat."));
    }
  }

  function onSelectChat(threadId: string) {
    setActiveChatId(threadId);
  }

  async function onRenameChat(thread: ChatThread) {
    const token = getToken();
    if (!selectedBotId || !token) {
      return;
    }
    const nextTitle = window.prompt("Rename chat", thread.title)?.trim();
    if (!nextTitle || nextTitle === thread.title) {
      return;
    }
    setThreadActionId(thread.id);
    try {
      const updated = mapThreadFromApi(await renameChatThread(selectedBotId, thread.id, nextTitle, token));
      setChatThreads((prev) => prev.map((item) => (item.id === thread.id ? updated : item)));
      setStatus("Chat renamed.");
    } catch (err) {
      setStatus(readError(err, "Could not rename chat."));
    } finally {
      setThreadActionId("");
    }
  }

  async function onDeleteChat(thread: ChatThread) {
    const token = getToken();
    if (!selectedBotId || !token) {
      return;
    }
    if (!window.confirm(`Delete "${thread.title}"?`)) {
      return;
    }
    setThreadActionId(thread.id);
    try {
      await deleteChatThread(selectedBotId, thread.id, token);
      setChatThreads((prev) => {
        const next = prev.filter((item) => item.id !== thread.id);
        setActiveChatId((current) => (current === thread.id ? (next[0]?.id ?? "") : current));
        return next;
      });
      setStatus("Chat deleted.");
    } catch (err) {
      setStatus(readError(err, "Could not delete chat."));
    } finally {
      setThreadActionId("");
    }
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !selectedBotId || uploading || botArchived) {
      return;
    }
    if (selectedUploadFiles.length === 0) {
      setStatus("Please select at least one file to upload.");
      return;
    }

    setUploading(true);
    setUploadProgress({ done: 0, total: selectedUploadFiles.length });
    setStatus(`Uploading ${selectedUploadFiles.length} document(s)...`);
    try {
      let done = 0;
      for (const file of selectedUploadFiles) {
        await uploadDocument(token, selectedBotId, file);
        done += 1;
        setUploadProgress({ done, total: selectedUploadFiles.length });
        setStatus(`Uploading ${done}/${selectedUploadFiles.length}...`);
      }
      await refreshBots(token);
      await refreshDocuments(token, selectedBotId);
      setStatus(`Uploaded ${selectedUploadFiles.length} file(s) successfully.`);
      setSelectedUploadFiles([]);
    } catch (err) {
      setStatus(readError(err, "Upload failed."));
    } finally {
      setUploading(false);
      setUploadProgress({ done: 0, total: 0 });
    }
  }

  async function onDeleteDocument(documentId: string) {
    const token = getToken();
    if (!token || !selectedBotId || botArchived) {
      return;
    }
    try {
      await deleteDocument(token, selectedBotId, documentId);
      await refreshDocuments(token, selectedBotId);
      await refreshBots(token);
      setStatus("Document deleted.");
    } catch (err) {
      setStatus(readError(err, "Delete failed."));
    }
  }

  async function typeAssistantResponse(fullText: string) {
    const parts = fullText.match(/\s+|[^\s]+/g) ?? [fullText];
    updateActiveThread((thread) => {
      const nextMessages = [
        ...thread.messages,
        { role: "assistant" as const, text: "", createdAt: new Date().toLocaleTimeString() },
      ];
      return {
        ...thread,
        messages: nextMessages,
        updatedAt: new Date().toISOString(),
        title: buildThreadTitle(nextMessages),
      };
    });

    for (let i = 0; i < parts.length; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, 20));
      updateActiveThread((thread) => {
        const updated = [...thread.messages];
        const last = updated[updated.length - 1];
        if (!last || last.role !== "assistant") {
          return thread;
        }
        updated[updated.length - 1] = { ...last, text: `${last.text}${parts[i]}` };
        return {
          ...thread,
          messages: updated,
          updatedAt: new Date().toISOString(),
          title: buildThreadTitle(updated),
        };
      });
    }
  }

  async function onChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    const question = chatInput.trim();
    if (!token || !selectedBotId || !question || isChatting || botArchived) {
      return;
    }

    setChatInput("");
    updateActiveThread((thread) => {
      const nextMessages = [
        ...thread.messages,
        { role: "user" as const, text: question, createdAt: new Date().toLocaleTimeString() },
      ];
      return {
        ...thread,
        messages: nextMessages,
        updatedAt: new Date().toISOString(),
        title: buildThreadTitle(nextMessages),
      };
    });
    setIsChatting(true);
    try {
      const answer = await askBot(selectedBotId, question, token, conversationId);
      if (answer.conversation_id) {
        updateActiveThread((thread) => ({
          ...thread,
          conversationId: answer.conversation_id,
          updatedAt: new Date().toISOString(),
        }));
      }
      await typeAssistantResponse(answer.answer);
      setChatLogs(answer.logs ?? []);
      updateActiveThread((thread) => ({
        ...thread,
        logs: answer.logs ?? [],
        updatedAt: new Date().toISOString(),
      }));
      setStatus(answer.cached ? "Response served from cache." : "Response generated.");
    } catch (err) {
      setStatus(readError(err, "Chat failed."));
      setIsChatting(false);
    } finally {
      setIsChatting(false);
    }
  }

  async function copyCode(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      setStatus(`${label} copied.`);
    } catch {
      setStatus("Copy failed.");
    }
  }

  function renderMarkdown(raw: string) {
    return (
      <div className="cd-md">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => <h1 className="cd-md-h1">{children}</h1>,
            h2: ({ children }) => <h2 className="cd-md-h2">{children}</h2>,
            h3: ({ children }) => <h3 className="cd-md-h3">{children}</h3>,
            p: ({ children }) => <p className="cd-md-p">{children}</p>,
            ul: ({ children }) => <ul className="cd-md-ul">{children}</ul>,
            ol: ({ children }) => <ol className="cd-md-ol">{children}</ol>,
            li: ({ children }) => <li className="cd-md-li">{children}</li>,
            a: ({ children, href }) => (
              <a href={href} target="_blank" rel="noreferrer" className="cd-md-a">
                {children}
              </a>
            ),
            code: ({ children }) => <code className="cd-md-code">{children}</code>,
            pre: ({ children }) => <pre className="cd-md-pre">{children}</pre>,
          }}
        >
          {raw}
        </ReactMarkdown>
      </div>
    );
  }

  function renderAssistantMessage(raw: string) {
    const trimmed = raw.trim();
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
      try {
        const parsed = JSON.parse(trimmed);
        return <pre className="cd-md-pre">{JSON.stringify(parsed, null, 2)}</pre>;
      } catch {
        // ignore parse error
      }
    }
    return renderMarkdown(raw);
  }

  const widgetCode = selectedBotId
    ? `<!-- Add this script to your HTML -->
<script src="${widgetScriptUrl}"></script>

<!-- Initialize the widget -->
<script>
  ChatDock.init({
    botId: "${selectedBotId}",
    apiUrl: "${API_BASE_URL}",
    token: "${sessionToken}",
    title: "${selectedBot?.bot_name || "ChatDock Bot"}",
    greeting: "${(selectedBot?.greeting_message || "Hello! Ask a question about this bot.").replace(/"/g, '\\"')}",
    primaryColor: "#2459ea"
  });
</script>`
    : "Select a bot first.";

  const apiCode = selectedBotId
    ? `const response = await fetch("${API_BASE_URL}/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer ${sessionToken}"
  },
  body: JSON.stringify({
    bot_id: "${selectedBotId}",
    message: "How do I configure my settings?"
  })
});

const payload = await response.json();
console.log(payload.answer);
console.log(payload.sources);`
    : "Select a bot first.";

  const curlCode = selectedBotId
    ? `curl -X POST ${API_BASE_URL}/chat \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${sessionToken}" \\
  -d '{
  "bot_id": "${selectedBotId}",
  "message": "How do I configure my settings?"
}'`
    : "Select a bot first.";

  const widgetPreviewDoc = selectedBotId
    ? `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        background: linear-gradient(180deg, #eff4fb 0%, #e8eef8 100%);
        font-family: Arial, sans-serif;
        color: #0b1737;
        overflow: hidden;
      }
      .preview-shell {
        min-height: 100vh;
        padding: 18px 18px 96px;
      }
      .preview-card {
        border: 1px solid #cfd7e2;
        border-radius: 18px;
        background: rgba(248, 250, 252, 0.92);
        padding: 18px;
        box-shadow: 0 16px 40px rgba(17, 38, 82, 0.08);
      }
      .preview-title {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
      }
      .preview-copy {
        margin: 8px 0 0;
        font-size: 13px;
        line-height: 1.5;
        color: #506688;
        max-width: 420px;
      }
      .preview-note {
        margin-top: 12px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        background: #edf3ff;
        color: #1a4adb;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 600;
      }
    </style>
  </head>
  <body>
    <div class="preview-shell">
      <div class="preview-card">
        <h1 class="preview-title">Live widget preview</h1>
        <p class="preview-copy">Use the launcher in the bottom-right corner to test the exact widget script and backend chat API for this bot.</p>
        <div class="preview-note">Bot: ${(selectedBot?.bot_name || "ChatDock Bot").replace(/</g, "&lt;")}</div>
      </div>
    </div>
    <script src="${widgetScriptUrl}"></script>
    <script>
      window.ChatDock.init({
        botId: "${selectedBotId}",
        apiUrl: "${API_BASE_URL}",
        token: "${sessionToken}",
        title: "${(selectedBot?.bot_name || "ChatDock Bot").replace(/"/g, '\\"')}",
        greeting: "${(selectedBot?.greeting_message || "Hello! Ask a question about this bot.").replace(/"/g, '\\"')}",
        primaryColor: "#2459ea"
      });
    </script>
  </body>
</html>`
    : "";

  return (
    <AppShell>
      <section className="cd-page-head">
        <div className="flex items-start gap-2">
          <button
            type="button"
            className="cd-page-back"
            aria-label="Back"
            onClick={() => {
              if (window.history.length > 2) {
                router.back();
              } else {
                router.push("/dashboard");
              }
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5 stroke-current">
              <path d="M15 5l-7 7 7 7" strokeWidth="1.7" />
            </svg>
          </button>
          <div>
            <h1 className="cd-page-title">{section === "manage" ? "Manage Bot" : section === "chat" ? "Chat Interface" : "Integrations"}</h1>
            <p className="cd-page-subtitle">
              {section === "manage"
                ? "Upload documents and configure your bot"
                : section === "chat"
                  ? "Test your bot with real queries"
                  : "Integrate your bot using API or widget"}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {section === "manage" ? (
            <>
              <button className="cd-btn-light" onClick={() => setSection("chat")} type="button">
                <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
                  <path d="M4 6.5A2.5 2.5 0 016.5 4h11A2.5 2.5 0 0120 6.5v6A2.5 2.5 0 0117.5 15H9l-3.5 3v-3.6A2.5 2.5 0 014 12V6.5z" strokeWidth="1.6" />
                </svg>
                Test Chat
              </button>
              <button className="cd-btn-dark" onClick={() => setSection("integrations")} type="button">
                <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
                  <path d="M7 8l-4 4 4 4M17 8l4 4-4 4M14 5l-4 14" strokeWidth="1.7" />
                </svg>
                Integrations
              </button>
            </>
          ) : null}
          {section === "chat" ? (
            <button className="cd-btn-dark" onClick={() => setSection("integrations")} type="button">
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
                <path d="M7 8l-4 4 4 4M17 8l4 4-4 4M14 5l-4 14" strokeWidth="1.7" />
              </svg>
              Get Integration Code
            </button>
          ) : null}
        </div>
      </section>

      {section === "manage" ? (
        <>
          <div className="cd-tab-wrap mb-4">
            <button
              type="button"
              className={`cd-tab-btn${manageTab === "documents" ? " is-active" : ""}`}
              onClick={() => setManageTab("documents")}
            >
              Documents
            </button>
            <button
              type="button"
              className={`cd-tab-btn${manageTab === "settings" ? " is-active" : ""}`}
              onClick={() => setManageTab("settings")}
            >
              Settings
            </button>
          </div>

          {manageTab === "documents" ? (
            <div className="space-y-4">
              <section className="cd-card p-4">
                <h3 className="m-0 text-[28px] font-semibold text-[#06153b] scale-[0.5] origin-left -mb-3">Upload Documents</h3>
                <p className="m-0 text-[28px] text-[#4b6283] scale-[0.5] origin-left -mb-2">
                  Upload PDF, TXT, DOCX, or MD files to train your bot
                </p>
                <form className="mt-3" onSubmit={onUpload}>
                  <label className="block rounded-xl border border-dashed border-[#c0ccda] bg-[#f5f8fc] p-8 text-center cursor-pointer">
                    <div className="mx-auto mb-2 w-fit text-[#8b9db9]">
                      <svg viewBox="0 0 24 24" fill="none" className="h-10 w-10 stroke-current">
                        <path d="M12 16V4M12 4l-4 4M12 4l4 4M5 14.5V18a2 2 0 002 2h10a2 2 0 002-2v-3.5" strokeWidth="1.6" />
                      </svg>
                    </div>
                    <p className="text-[#1d56eb] text-[28px] scale-[0.5] origin-center -mb-3">Click to upload</p>
                    <p className="text-[25px] text-[#35557a] scale-[0.5] origin-center -mb-3">PDF, TXT, DOCX, MD up to 10MB</p>
                    <input
                      name="documents"
                      type="file"
                      accept=".pdf,.txt,.docx,.md"
                      multiple
                      className="sr-only"
                      onChange={(e) => setSelectedUploadFiles(Array.from(e.target.files ?? []))}
                    />
                  </label>
                  {uploading ? (
                    <div className="mt-3 rounded-lg border border-[#cfd7e3] bg-[#eff4ff] p-3 text-sm text-[#234d9a]">
                      Uploading {uploadProgress.done}/{uploadProgress.total} files...
                    </div>
                  ) : null}
                  <div className="mt-2 text-[#1f456f] text-sm">
                    {selectedUploadFiles.length > 0
                      ? `Selected: ${selectedUploadFiles.map((f) => f.name).join(', ')}`
                      : "No files selected."}
                  </div>
                  <div className="mt-3 flex justify-end gap-2">
                    <button
                      className="cd-btn-light"
                      type="button"
                      onClick={() => setSelectedUploadFiles([])}
                      disabled={botArchived}
                    >
                      Clear
                    </button>
                    <button className="cd-btn-dark" type="submit" disabled={uploading || !selectedBotId || selectedUploadFiles.length === 0 || botArchived}>
                      {uploading ? "Uploading..." : "Upload"}
                    </button>
                  </div>
                </form>
              </section>

              <section className="cd-card p-4">
                <h3 className="m-0 text-[28px] font-semibold text-[#06153b] scale-[0.5] origin-left -mb-3">Uploaded Documents</h3>
                <p className="m-0 text-[26px] text-[#4c6383] scale-[0.5] origin-left -mb-2">
                  {selectedBot?.document_count ?? 0} documents in your bot
                </p>

                <div className="mt-3 space-y-2">
                  {uploadedDocuments.length > 0 ? uploadedDocuments.map((doc) => {
                    const ext = doc.file_name.split(".").pop()?.toLowerCase() ?? "file";
                    return (
                      <div key={doc.id} className="rounded-[10px] border border-[#cfd7e3] bg-[#f8fafc] px-3 py-2">
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <span className="text-[#3460e7]">
                              <img src="/file.svg" alt="Document" className="doc-icon" />
                            </span>
                            <div>
                              <p className="m-0 text-[27px] font-medium text-[#03153b] scale-[0.5] origin-left -mb-2">{doc.file_name}</p>
                              <p className="m-0 text-[24px] text-[#4c6384] scale-[0.5] origin-left -mb-2">
                                {doc.chunk_count} chunks • {EXTENSION_ICONS[ext] || ext.toUpperCase()}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="cd-pill-dark">ready</span>
                            <button type="button" className="text-[#ff2435] disabled:opacity-40" onClick={() => void onDeleteDocument(doc.id)} disabled={botArchived}>
                              <img src="/delete.svg" alt="Delete" className="h-4.5 w-4.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  }) : (
                    <div className="rounded-[10px] border border-[#cfd7e3] bg-[#f8fafc] px-3 py-2 text-[#4c6384]">
                      No documents uploaded yet.
                    </div>
                  )}
                </div>
              </section>
            </div>
          ) : (
            <section className="cd-card p-4">
              <h3 className="m-0 text-[28px] font-semibold text-[#06153b] scale-[0.5] origin-left -mb-3">Bot Settings</h3>
              <p className="m-0 text-[28px] text-[#4b6283] scale-[0.5] origin-left -mb-3">
                Configure your bot&apos;s behavior and preferences
              </p>
              <div className="mt-3 rounded-lg border border-[#d3dbe5] bg-[#fbfcfe] p-3 text-sm text-[#294465]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="m-0 font-semibold text-[#0a2249]">Bot status</p>
                    <p className="m-0 mt-1 text-[#55708f]">
                      {botArchived ? "This bot is archived. Uploads and chat are paused until you restore it." : "This bot is active and available for chat and document updates."}
                    </p>
                  </div>
                  <span className={botArchived ? "cd-pill-inactive" : "cd-pill-dark"}>{botArchived ? "archived" : "active"}</span>
                </div>
              </div>

              <form className="mt-4 space-y-4" onSubmit={onSaveSettings}>
                <div className="grid gap-4 lg:grid-cols-2">
                  <label className="block">
                    <span className="block text-sm font-semibold text-[#0a1b42]">Bot Name</span>
                    <input
                      value={settingsForm.bot_name}
                      onChange={(e) => setSettingsForm((prev) => ({ ...prev, bot_name: e.target.value }))}
                      className="cd-input mt-2"
                      placeholder="Customer Support Bot"
                    />
                  </label>
                  <label className="block">
                    <span className="block text-sm font-semibold text-[#0a1b42]">Tone</span>
                    <select
                      value={settingsForm.tone}
                      onChange={(e) => setSettingsForm((prev) => ({ ...prev, tone: e.target.value as typeof prev.tone }))}
                      className="cd-select mt-2"
                    >
                      <option value="professional">Professional</option>
                      <option value="friendly">Friendly</option>
                      <option value="technical">Technical</option>
                    </select>
                  </label>
                </div>

                <label className="block">
                  <span className="block text-sm font-semibold text-[#0a1b42]">Description</span>
                  <textarea
                    value={settingsForm.description}
                    onChange={(e) => setSettingsForm((prev) => ({ ...prev, description: e.target.value }))}
                    className="cd-textarea mt-2"
                    placeholder="Describe what this bot helps with."
                  />
                </label>

                <div className="grid gap-4 lg:grid-cols-2">
                  <label className="block">
                    <span className="block text-sm font-semibold text-[#0a1b42]">Answer Length</span>
                    <select
                      value={settingsForm.answer_length}
                      onChange={(e) => setSettingsForm((prev) => ({ ...prev, answer_length: e.target.value as typeof prev.answer_length }))}
                      className="cd-select mt-2"
                    >
                      <option value="short">Short</option>
                      <option value="balanced">Balanced</option>
                      <option value="detailed">Detailed</option>
                    </select>
                  </label>
                  <label className="block">
                    <span className="block text-sm font-semibold text-[#0a1b42]">Fallback Behavior</span>
                    <select
                      value={settingsForm.fallback_behavior}
                      onChange={(e) => setSettingsForm((prev) => ({ ...prev, fallback_behavior: e.target.value as typeof prev.fallback_behavior }))}
                      className="cd-select mt-2"
                    >
                      <option value="strict">Strict</option>
                      <option value="helpful">Helpful</option>
                    </select>
                  </label>
                </div>

                <label className="block">
                  <span className="block text-sm font-semibold text-[#0a1b42]">Greeting Message</span>
                  <textarea
                    value={settingsForm.greeting_message}
                    onChange={(e) => setSettingsForm((prev) => ({ ...prev, greeting_message: e.target.value }))}
                    className="cd-textarea mt-2"
                    placeholder="Hello! I'm your support assistant. Ask me anything about your uploaded documents."
                  />
                </label>

                <label className="block">
                  <span className="block text-sm font-semibold text-[#0a1b42]">System Prompt</span>
                  <textarea
                    value={settingsForm.system_prompt}
                    onChange={(e) => setSettingsForm((prev) => ({ ...prev, system_prompt: e.target.value }))}
                    className="cd-textarea mt-2"
                    placeholder="Optional extra instructions to steer the bot's answers."
                  />
                </label>

                <div className="flex flex-wrap gap-2">
                  <button className="cd-btn-dark" type="submit" disabled={savingSettings}>
                    {savingSettings ? "Saving..." : "Save Settings"}
                  </button>
                  <button className="cd-btn-light" type="button" onClick={() => void onReindexBot()} disabled={reindexing || !selectedBotId}>
                    {reindexing ? "Reindexing..." : "Reindex Bot"}
                  </button>
                  <button className="cd-btn-light" type="button" onClick={() => void onArchiveToggle()} disabled={archiving || !selectedBotId}>
                    {archiving ? "Updating..." : botArchived ? "Restore Bot" : "Archive Bot"}
                  </button>
                </div>
              </form>
            </section>
          )}
        </>
      ) : null}

      {section === "chat" ? (
        <section className="cd-chat-layout">
          <aside className="cd-card p-3 cd-chat-sidebar">
            <div className="cd-chat-sidebar-head">
              <div className="cd-chat-sidebar-copy">
                <p className="cd-chat-sidebar-title">Previous Chats</p>
                <p className="cd-chat-sidebar-subtitle">Stored per bot like a real workspace.</p>
              </div>
              <button className="cd-btn-dark cd-chat-new-btn" type="button" onClick={onCreateNewChat} disabled={!selectedBotId}>
                New Chat
              </button>
            </div>

            <div className="mt-3 space-y-2">
              {chatThreads.map((thread) => (
                <div key={thread.id} className={`cd-chat-thread${thread.id === activeThread?.id ? " is-active" : ""}`}>
                  <button type="button" className="cd-chat-thread-main" onClick={() => onSelectChat(thread.id)}>
                    <span className="cd-chat-thread-title">{thread.title}</span>
                    <span className="cd-chat-thread-meta">
                      {new Date(thread.updatedAt).toLocaleDateString()} · {thread.messages.length} messages
                    </span>
                  </button>
                  <div className="cd-chat-thread-actions">
                    <button type="button" className="cd-chat-thread-icon" onClick={() => void onRenameChat(thread)} disabled={threadActionId === thread.id}>
                      Rename
                    </button>
                    <button type="button" className="cd-chat-thread-icon danger" onClick={() => void onDeleteChat(thread)} disabled={threadActionId === thread.id}>
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </aside>

          <div className="cd-card p-3 flex min-h-[640px] flex-col">
            <div className="flex items-center justify-between gap-3 border-b border-[#d8e0ea] pb-3">
              <div>
                <p className="m-0 text-sm font-semibold text-[#07183f]">{activeThread?.title ?? "New chat"}</p>
                <p className="m-0 mt-1 text-xs text-[#5b7191]">
                  {selectedBot?.bot_name ? `Talking with ${selectedBot.bot_name}` : "Select a bot to start chatting"}
                </p>
              </div>
              <span className="cd-pill-inactive">{messages.length} messages</span>
            </div>

            <div ref={chatContainerRef} className="chat-scroll mt-3 h-[470px] rounded-lg border border-[#cfd7e3] bg-[#f8fafc] p-3 overflow-auto">
              <div className="space-y-3">
                {messages.map((msg, index) => (
                  <div key={`${msg.createdAt}-${index}`}>
                    <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`chat-bubble ${msg.role === "assistant" ? "assistant" : "user"}`}>
                        {msg.role === "assistant" ? renderAssistantMessage(msg.text) : msg.text}
                      </div>
                    </div>
                    <p className={`m-0 mt-1 text-xs text-[#61708f] ${msg.role === "assistant" ? "text-left" : "text-right"}`}>
                      {msg.createdAt}
                    </p>
                  </div>
                ))}
                {isChatting ? <p className="text-sm text-[#4c6385]">Bot is replying...</p> : null}
              </div>
            </div>

            {chatLogs.length > 0 ? (
              <div className="mt-2 rounded-lg border border-[#d6e1f0] bg-[#f5f7ff] p-2 text-[12px] text-[#1f3c68]">
                <div className="mb-1 font-semibold text-[#0f2b60]">LLM Logs</div>
                <ul className="list-disc pl-4">
                  {chatLogs.map((line, idx) => (
                    <li key={`${idx}-${line}`}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <form onSubmit={onChatSubmit} className="mt-3 rounded-b-lg border border-t-0 border-[#cfd7e3] bg-[#f8fafc] p-3">
              <div className="cd-chat-composer">
                <input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  className="cd-input"
                  placeholder={botArchived ? "Restore this bot to chat again..." : "Ask a question about your documents..."}
                  disabled={isChatting || !selectedBotId || botArchived || !activeThread}
                />
                <button type="submit" className="cd-chat-send-btn" disabled={isChatting || !selectedBotId || botArchived || !activeThread}>
                  <svg viewBox="0 0 24 24" fill="none" className="h-4.5 w-4.5 stroke-current">
                    <path d="M5 12l14-7-4 14-3.5-4.5L5 12z" strokeWidth="1.6" />
                  </svg>
                  <span>{isChatting ? "Sending..." : "Send"}</span>
                </button>
              </div>
              <p className="mt-2 mb-0 text-[20px] text-[#5e7394] scale-[0.5] origin-left -mb-3">
                Powered by RAG (Retrieval-Augmented Generation)
              </p>
            </form>
          </div>
        </section>
      ) : null}

      {section === "integrations" ? (
        <>
          <div className="cd-tab-wrap mb-4">
            <button
              type="button"
              className={`cd-tab-btn${integrationTab === "widget" ? " is-active" : ""}`}
              onClick={() => setIntegrationTab("widget")}
            >
              Widget
            </button>
            <button
              type="button"
              className={`cd-tab-btn${integrationTab === "api" ? " is-active" : ""}`}
              onClick={() => setIntegrationTab("api")}
            >
              API
            </button>
          </div>

          {integrationTab === "widget" ? (
            <div className="space-y-4">
              <section className="cd-card p-4">
                <h3 className="m-0 text-[28px] font-semibold text-[#06153b] scale-[0.5] origin-left -mb-3">Embed Chat Widget</h3>
                <p className="m-0 text-[27px] text-[#4b6283] scale-[0.5] origin-left -mb-2">
                  Add a chat widget to your website with a simple script tag
                </p>
                <div className="mt-3 flex justify-end">
                  <button className="cd-btn-light h-8 px-3 text-xs" onClick={() => void copyCode(widgetCode, "Widget code")}>
                    Copy
                  </button>
                </div>
                <pre className="cd-code mt-2">{widgetCode}</pre>

                <div className="mt-3 rounded-lg border border-[#aac7f1] bg-[#e8f1ff] p-3">
                  <p className="m-0 text-[27px] font-semibold text-[#0d3c9b] scale-[0.5] origin-left -mb-3">Features</p>
                  <ul className="mb-0 mt-1 list-disc pl-4 text-[24px] text-[#1f4aa5] scale-[0.5] origin-left -mb-8">
                    <li>Uses your real ChatDock `/chat` API</li>
                    <li>Supports multi-turn conversation ids automatically</li>
                    <li>Can be hosted from your deployed frontend at `/widget.js`</li>
                    <li>Works with the selected bot id immediately</li>
                  </ul>
                </div>

                <div className="mt-3 rounded-lg border border-[#edd17a] bg-[#fbf6e3] p-3">
                  <p className="m-0 text-[27px] font-semibold text-[#9c6500] scale-[0.5] origin-left -mb-3">Important</p>
                  <p className="m-0 text-[24px] text-[#9c6500] scale-[0.5] origin-left -mb-3">
                    This example currently uses your signed-in session token. Keep it private and rotate it by logging in again if needed.
                  </p>
                </div>
              </section>

              <section className="cd-card p-4">
                <h3 className="m-0 text-[28px] font-semibold text-[#06153b] scale-[0.5] origin-left -mb-3">Widget Preview</h3>
                <p className="m-0 text-[27px] text-[#4b6283] scale-[0.5] origin-left -mb-2">A real widget script is available at /widget.js and can call your backend chat API.</p>
                {selectedBotId ? (
                  <div className="mt-3 overflow-hidden rounded-xl border border-[#c2cfdd] bg-[#f4f8fd]">
                    <iframe
                      title="ChatDock widget preview"
                      srcDoc={widgetPreviewDoc}
                      sandbox="allow-scripts allow-same-origin allow-forms"
                      className="h-[620px] w-full border-0 bg-transparent"
                    />
                  </div>
                ) : (
                  <div className="mt-3 rounded-xl border border-dashed border-[#c2cfdd] bg-[#f4f8fd] p-8 text-center">
                    <div className="mx-auto w-fit text-[#879aba]">
                      <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8 stroke-current">
                        <path d="M8 7l-5 5 5 5M16 7l5 5-5 5M14 5l-4 14" strokeWidth="1.7" />
                      </svg>
                    </div>
                    <p className="m-0 text-[26px] text-[#4f6788] scale-[0.5] origin-center -mb-3">Select a bot to preview the widget</p>
                    <p className="m-0 text-[22px] text-[#5f7595] scale-[0.5] origin-center -mb-3">
                      The live widget preview needs a selected bot and your current session token.
                    </p>
                  </div>
                )}
              </section>
            </div>
          ) : (
            <div className="space-y-4">
              <section className="cd-card p-4">
                <h3 className="m-0 text-[28px] font-semibold text-[#06153b] scale-[0.5] origin-left -mb-3">API Integration</h3>
                <p className="m-0 text-[27px] text-[#4b6283] scale-[0.5] origin-left -mb-2">Integrate ChatDock into your application using the live REST API this app already exposes.</p>

                <div className="mt-3 flex justify-end">
                  <button className="cd-btn-light h-8 px-3 text-xs" onClick={() => void copyCode(apiCode, "API example")}>
                    Copy
                  </button>
                </div>
                <pre className="cd-code mt-2">{apiCode}</pre>

                <h4 className="mt-4 mb-1 text-[30px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">cURL Example</h4>
                <pre className="cd-code">{curlCode}</pre>
              </section>

              <section className="cd-card p-4">
                <h4 className="m-0 text-[30px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Available Endpoints</h4>
                <p className="m-0 text-[27px] text-[#4b6283] scale-[0.5] origin-left -mb-2">Complete API reference for ChatDock</p>
                <div className="mt-3 space-y-2">
                  <EndpointRow method="POST" path="/chat" desc="Send a query to your bot and receive a RAG-powered response" />
                  <EndpointRow method="GET" path={`/chat/threads?bot_id=${selectedBotId || "bot-1"}`} desc="Load persisted chat threads for the selected bot" />
                  <EndpointRow method="POST" path="/bot/upload" desc="Upload documents programmatically to your bot" />
                  <EndpointRow method="GET" path="/analytics/overview" desc="Retrieve usage analytics and insights" />
                </div>
                <div className="mt-3 rounded-lg border border-[#cfd7e3] bg-[#f5f8fc] p-3">
                  <p className="m-0 text-[28px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Rate Limiting</p>
                  <p className="m-0 text-[24px] text-[#4d6385] scale-[0.5] origin-left -mb-3">Redis-based rate limiting is enabled. Default limits:</p>
                  <ul className="mb-0 mt-1 list-disc pl-4 text-[23px] text-[#4d6385] scale-[0.5] origin-left -mb-6">
                    <li>100 requests per minute per API key</li>
                    <li>1000 requests per day per API key</li>
                  </ul>
                </div>
              </section>
            </div>
          )}
        </>
      ) : null}

      {status ? (
        <div className={`cd-toast is-${statusTone}`} role="status" aria-live="polite">
          <div className="cd-toast-icon" aria-hidden="true">
            {statusTone === "success" ? "✓" : statusTone === "error" ? "!" : statusTone === "warn" ? "!" : "•"}
          </div>
          <div className="cd-toast-copy">
            <p className="cd-toast-title">
              {statusTone === "success"
                ? "Done"
                : statusTone === "error"
                  ? "Something went wrong"
                  : statusTone === "warn"
                    ? "Update"
                    : "Working"}
            </p>
            <p className="cd-toast-message">{status}</p>
          </div>
          <button type="button" className="cd-toast-close" onClick={() => setStatus("")} aria-label="Dismiss notification">
            ×
          </button>
        </div>
      ) : null}
    </AppShell>
  );
}

function EndpointRow({ method, path, desc }: { method: "GET" | "POST"; path: string; desc: string }) {
  return (
    <div className="rounded-[10px] border border-[#cfd7e3] bg-[#f8fafc] p-3">
      <div className="flex items-center gap-2">
        <span className={`rounded px-2 py-0.5 text-[11px] font-bold ${method === "POST" ? "bg-[#d9f5df] text-[#0f7c3a]" : "bg-[#dbe8ff] text-[#2557d9]"}`}>
          {method}
        </span>
        <code className="text-sm text-[#04163b]">{path}</code>
      </div>
      <p className="mt-2 mb-0 text-[23px] text-[#4b6283] scale-[0.5] origin-left -mb-3">{desc}</p>
    </div>
  );
}

function readError(err: unknown, fallback: string): string {
  if (err instanceof Error) {
    return err.message;
  }
  if (typeof err === "object" && err !== null && "detail" in err) {
    const detail = (err as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return fallback;
}
