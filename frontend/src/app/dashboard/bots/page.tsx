"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { getToken } from "../../../services/auth";
import { deleteBot, listBots, uploadDocument, type Bot } from "../../../services/bot";
import { askBot } from "../../../services/chat";
import { API_BASE_URL } from "../../../services/api";

type Message = {
  role: "user" | "assistant";
  text: string;
};

const CACHED_STATUS_NOTES = [
  "Fast reply from cache.",
  "Quick answer reused from recent context.",
  "Instant response served from cache.",
];

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBotId, setSelectedBotId] = useState("");
  const [section, setSection] = useState<"manage" | "chat" | "integrations">("manage");
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copiedTag, setCopiedTag] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedBot = bots.find((bot) => bot.id === selectedBotId) ?? null;

  const refreshBots = useCallback(
    async (token: string) => {
      try {
        const botList = await listBots(token);
        setBots(botList);
        const queryBotId = searchParams.get("botId");
        if (queryBotId && botList.some((bot) => bot.id === queryBotId)) {
          setSelectedBotId(queryBotId);
          return;
        }
        if (!selectedBotId || !botList.some((bot) => bot.id === selectedBotId)) {
          setSelectedBotId(botList[0]?.id ?? "");
        }
      } catch (err) {
        setStatus(readError(err, "Failed to load bots"));
      }
    },
    [searchParams, selectedBotId],
  );

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    const timer = setTimeout(() => {
      void refreshBots(token);
    }, 0);
    return () => clearTimeout(timer);
  }, [refreshBots, router]);

  useEffect(() => {
    const querySection = searchParams.get("section");
    if (querySection === "manage" || querySection === "chat" || querySection === "integrations") {
      setSection(querySection);
    }
  }, [searchParams]);

  async function onUploadExisting(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !selectedBotId) {
      return;
    }
    const form = event.currentTarget;
    const target = form.elements.namedItem("document") as HTMLInputElement;
    const file = target?.files?.[0];
    if (!file) {
      return;
    }

    setStatus("Uploading document...");
    try {
      const result = await uploadDocument(token, selectedBotId, file);
      await refreshBots(token);
      setStatus(`Uploaded ${result.file_name} (${result.chunk_count} chunks).`);
      form.reset();
    } catch (err) {
      setStatus(readError(err, "Upload failed"));
    }
  }

  async function onChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !selectedBotId || !chatInput.trim() || isChatting) {
      return;
    }

    const question = chatInput.trim();
    setChatInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setStatus("Bot is processing your question...");
    setIsChatting(true);

    try {
      const response = await askBot(selectedBotId, question, token);
      setMessages((prev) => [...prev, { role: "assistant", text: response.answer }]);
      if (response.cached) {
        const note = CACHED_STATUS_NOTES[Math.floor(Math.random() * CACHED_STATUS_NOTES.length)];
        setStatus(`${note} Sources: ${response.sources.length}`);
      } else {
        setStatus(`Response ready. Sources: ${response.sources.length}`);
      }
    } catch (err) {
      setStatus(readError(err, "Chat failed"));
    } finally {
      setIsChatting(false);
    }
  }

  async function onDeleteSelectedBot() {
    const token = getToken();
    if (!token || !selectedBotId || isDeleting) {
      return;
    }
    const target = bots.find((bot) => bot.id === selectedBotId);
    const label = target?.bot_name ?? "this bot";
    const confirmed = window.confirm(`Delete '${label}'? This will remove its documents and chat history.`);
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setStatus("Deleting bot...");
    try {
      await deleteBot(token, selectedBotId);
      const nextBots = await listBots(token);
      setBots(nextBots);
      setSelectedBotId(nextBots[0]?.id ?? "");
      setMessages([]);
      setStatus("Bot deleted.");
    } catch (err) {
      setStatus(readError(err, "Delete failed"));
    } finally {
      setIsDeleting(false);
    }
  }

  async function copyText(text: string, tag: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedTag(tag);
      setStatus(`${tag} copied.`);
      window.setTimeout(() => setCopiedTag(""), 1400);
    } catch {
      setStatus("Copy failed. Please copy manually.");
    }
  }

  const widgetEmbedCode = selectedBotId
    ? `<script src="https://chatdock.ai/widget.js"></script>
<script>
  ChatDock.init({ botId: "${selectedBotId}", position: "bottom-right" });
</script>`
    : "Select a bot to generate widget code.";

  const apiExample = selectedBotId
    ? `curl -X POST "${API_BASE_URL}/chat" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -d '{
    "bot_id": "${selectedBotId}",
    "message": "How can you help me?"
  }'`
    : "Select a bot to generate API example.";

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#09070f] via-[#120b1f] to-[#09070f] p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="panel rounded-xl p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-purple-300/80">Workspace</p>
              <h1 className="mt-1 text-2xl font-bold text-purple-200">Bot Manager</h1>
              <p className="text-sm text-purple-100/70">
                Manage a bot, test chat behavior, and configure integration snippets.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <a href="/dashboard" className="btn-secondary rounded-md px-3 py-2 text-sm font-semibold">
                Back to dashboard
              </a>
              <div className="rounded-md border border-purple-900/70 bg-[#0f0c18] px-3 py-2 text-xs text-purple-200/80">
                {selectedBot ? `Active bot: ${selectedBot.bot_name}` : "No bot selected"}
              </div>
            </div>
          </div>
        </div>

        <div className="panel rounded-xl p-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setSection("manage")}
              className={`${section === "manage" ? "btn-primary" : "btn-secondary"} rounded-md px-4 py-2 text-sm font-semibold`}
            >
              Manage Bot
            </button>
            <button
              type="button"
              onClick={() => setSection("chat")}
              className={`${section === "chat" ? "btn-primary" : "btn-secondary"} rounded-md px-4 py-2 text-sm font-semibold`}
            >
              Chat Interface
            </button>
            <button
              type="button"
              onClick={() => setSection("integrations")}
              className={`${section === "integrations" ? "btn-primary" : "btn-secondary"} rounded-md px-4 py-2 text-sm font-semibold`}
            >
              Integrations
            </button>
          </div>
        </div>

        {section === "manage" ? (
          <div className="panel rounded-xl p-5">
            <h2 className="text-lg font-semibold text-purple-200">Manage Bot</h2>
            <p className="text-sm text-purple-100/70">Select a bot, upload documents, or delete it.</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <select
                value={selectedBotId}
                onChange={(e) => setSelectedBotId(e.target.value)}
                className="input-dark w-full rounded-md px-3 py-2"
              >
                <option value="">Choose bot</option>
                {bots.map((bot) => (
                  <option key={bot.id} value={bot.id}>
                    {bot.bot_name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={onDeleteSelectedBot}
                disabled={!selectedBotId || isDeleting}
                className="btn-danger rounded-md px-4 py-2 font-semibold disabled:opacity-50"
              >
                {isDeleting ? "Deleting..." : "Delete Selected Bot"}
              </button>
            </div>

            <form className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={onUploadExisting}>
              <input
                name="document"
                type="file"
                accept=".txt,.md,.pdf,.docx"
                className="input-dark w-full rounded-md px-3 py-2 text-sm"
                required
              />
              <button
                disabled={!selectedBotId}
                className="btn-primary rounded-md px-4 py-2 font-semibold disabled:opacity-50"
              >
                Upload Document
              </button>
            </form>
          </div>
        ) : null}

        {section === "chat" ? (
          <div className="panel rounded-xl p-5">
            <h2 className="text-lg font-semibold text-purple-200">Chat Interface</h2>
            <p className="text-sm text-purple-100/70">Test user conversations for the selected bot.</p>
            <div className="mt-4 h-[560px] overflow-auto rounded-lg border border-purple-900/60 bg-[#0f0c18] p-4">
              {messages.length === 0 ? <p className="text-sm text-purple-100/70">Ask a question after uploading docs.</p> : null}
              <div className="space-y-3">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={
                      message.role === "user"
                        ? "ml-auto max-w-[82%] rounded-lg bg-[#a855f7] px-3 py-2 text-sm text-black"
                        : "max-w-[82%] rounded-lg border border-purple-900/60 bg-[#171224] px-3 py-2 text-sm text-purple-100 shadow-sm"
                    }
                  >
                    {message.text}
                  </div>
                ))}
                {isChatting ? (
                  <div className="max-w-[82%] rounded-lg border border-purple-700/60 bg-[#1c1530] px-3 py-2 text-sm text-purple-100/90 animate-pulse">
                    Bot is replying...
                  </div>
                ) : null}
              </div>
            </div>
            <form className="mt-4 flex gap-2" onSubmit={onChat}>
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask your bot..."
                className="input-dark flex-1 rounded-md px-3 py-2"
                disabled={isChatting}
                required
              />
              <button
                disabled={!selectedBotId || isChatting}
                className="btn-primary rounded-md px-4 py-2 font-semibold disabled:opacity-50"
              >
                {isChatting ? "Processing..." : "Send"}
              </button>
            </form>
          </div>
        ) : null}

        {section === "integrations" ? (
          <div className="panel rounded-xl p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-purple-200/80">Integrations</h3>
              {copiedTag ? <span className="text-xs text-purple-300">{copiedTag}</span> : null}
            </div>
            <p className="mt-1 text-xs text-purple-100/70">
              Ship this bot to your site or backend with production-ready snippets.
            </p>

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-purple-200/80">Widget Embed</p>
                <button
                  type="button"
                  onClick={() => copyText(widgetEmbedCode, "Widget code")}
                  disabled={!selectedBotId}
                  className="btn-primary rounded-md px-3 py-1 text-xs font-semibold disabled:opacity-50"
                >
                  Copy
                </button>
              </div>
              <pre className="overflow-x-auto rounded-md border border-purple-900/60 bg-[#120d1f] p-3 text-xs text-purple-100">
{widgetEmbedCode}
              </pre>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-purple-200/80">API Request</p>
                <button
                  type="button"
                  onClick={() => copyText(apiExample, "API example")}
                  disabled={!selectedBotId}
                  className="btn-primary rounded-md px-3 py-1 text-xs font-semibold disabled:opacity-50"
                >
                  Copy
                </button>
              </div>
              <pre className="overflow-x-auto rounded-md border border-purple-900/60 bg-[#120d1f] p-3 text-xs text-purple-100">
{apiExample}
              </pre>
            </div>
          </div>
        ) : null}

        <p className="rounded-md border border-purple-900/60 bg-[#0f0c18] px-3 py-2 text-sm text-purple-100/85">{status}</p>
      </div>
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
