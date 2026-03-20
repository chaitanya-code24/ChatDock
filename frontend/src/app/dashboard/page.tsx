"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../components/dashboard/app-shell";
import { getToken } from "../../services/auth";
import { createBot, deleteBot, listBots, type Bot } from "../../services/bot";

export default function DashboardPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [status, setStatus] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newBotName, setNewBotName] = useState("");
  const [newBotDescription, setNewBotDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingBotId, setDeletingBotId] = useState("");
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    void refreshBots(token);
  }, [router]);

  async function refreshBots(token: string) {
    try {
      const list = await listBots(token);
      setBots(list);
    } catch (err) {
      setStatus(readError(err, "Failed to load bots."));
    }
  }

  async function onCreateBot() {
    const token = getToken();
    if (!token || creating) {
      return;
    }
    const botName = newBotName.trim();
    if (botName.length < 2) {
      setStatus("Bot name should be at least 2 characters.");
      return;
    }

    setCreating(true);
    setStatus("");
    try {
      const created = await createBot(token, botName, newBotDescription.trim() || undefined);
      setShowCreateModal(false);
      setNewBotName("");
      setNewBotDescription("");
      await refreshBots(token);
      router.push(`/dashboard/bots?botId=${created.id}&section=manage`);
    } catch (err) {
      setStatus(readError(err, "Could not create bot."));
    } finally {
      setCreating(false);
    }
  }

  async function onDeleteBot(bot: Bot) {
    const token = getToken();
    if (!token || deletingBotId) {
      return;
    }
    if (!window.confirm(`Delete "${bot.bot_name}"?`)) {
      return;
    }
    setDeletingBotId(bot.id);
    setStatus("");
    try {
      await deleteBot(token, bot.id);
      await refreshBots(token);
      setStatus("Bot deleted.");
    } catch (err) {
      setStatus(readError(err, "Delete failed."));
    } finally {
      setDeletingBotId("");
    }
  }

  return (
    <AppShell>
      <section className="cd-page-head">
        <div>
          <h1 className="cd-page-title">Your Bots</h1>
          <p className="cd-page-subtitle">Manage your document-aware chatbots</p>
        </div>
        <button type="button" className="cd-btn-dark" onClick={() => setShowCreateModal(true)}>
          <span aria-hidden="true">+</span>
          Create Bot
        </button>
      </section>

      <section className="cd-grid-bots">
        {bots.map((bot) => (
          <article key={bot.id} className="cd-bot-card cd-shadow">
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <h3 className="cd-bot-title m-0 text-lg font-semibold text-[#03143a]">
                  {bot.bot_name}
                </h3>
              </div>
              {bot.archived ? (
                <span className="cd-pill-inactive">archived</span>
              ) : bot.document_count > 0 ? (
                <span className="cd-pill-dark">active</span>
              ) : (
                <span className="cd-pill-inactive">inactive</span>
              )}
            </div>

            <p className="mt-2 text-sm text-[#4d6180] line-clamp-2">
              {bot.description || "Handles common customer inquiries and support tickets"}
            </p>

            <div className="mt-3 flex items-center gap-2 text-[#3d5578]">
              <svg viewBox="0 0 24 24" fill="none" className="cd-icon-sm stroke-current">
                <path d="M7 3.8h7.6L20 9.2V20a1 1 0 01-1 1H7a1 1 0 01-1-1V4.8a1 1 0 011-1z" strokeWidth="1.6" />
                <path d="M14.6 3.8V9.2H20M9 13h7M9 16h5" strokeWidth="1.6" />
              </svg>
              <span className="text-base">
                {bot.document_count} documents
              </span>
            </div>
            <p className="mt-1 text-sm text-[#4f6586]">
              Created {new Date(bot.created_at).toLocaleDateString()}
            </p>

            <div className="cd-bot-actions">
              <a href={`/dashboard/bots?botId=${bot.id}&section=manage`} className="cd-btn-dark cd-bot-manage-btn">
                Manage
              </a>
              <a href={`/dashboard/bots?botId=${bot.id}&section=chat`} className="cd-btn-light h-[42px]">
                <svg viewBox="0 0 24 24" fill="none" className="cd-icon-sm stroke-current">
                  <path d="M4 6.5A2.5 2.5 0 016.5 4h11A2.5 2.5 0 0120 6.5v6A2.5 2.5 0 0117.5 15H9l-3.5 3v-3.6A2.5 2.5 0 014 12V6.5z" strokeWidth="1.6" />
                </svg>
                Test
              </a>
              <button
                type="button"
                className="cd-delete-btn text-[#ff2435] disabled:opacity-40"
                disabled={deletingBotId === bot.id}
                onClick={() => void onDeleteBot(bot)}
                aria-label={`Delete ${bot.bot_name}`}
              >
                <img src="/delete.svg" alt="Delete" className="cd-icon-sm" />
              </button>
            </div>
          </article>
        ))}
      </section>

      {status ? <p className="cd-status mt-4">{status}</p> : null}

      {showCreateModal ? (
        <div className="cd-modal-overlay">
          <div className="cd-modal cd-shadow">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="m-0 text-[25px] font-semibold text-[#06163a] scale-[0.62] origin-left -mb-2">
                  Create New Bot
                </h3>
                <p className="m-0 text-[28px] text-[#5d7091] scale-[0.5] origin-left -mb-2">
                  Set up a new document-aware chatbot for your use case
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="rounded-md p-1 text-[#6f7f9b] hover:bg-[#eef2f7]"
              >
                <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5 stroke-current">
                  <path d="M6 6l12 12M18 6L6 18" strokeWidth="1.7" />
                </svg>
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <label className="block">
                <span className="block text-[26px] font-medium text-[#0a1b42] scale-[0.5] origin-left -mb-2">Bot Name</span>
                <input
                  value={newBotName}
                  onChange={(e) => setNewBotName(e.target.value)}
                  className="cd-input"
                  placeholder="e.g., Customer Support Bot"
                />
              </label>
              <label className="block">
                <span className="block text-[26px] font-medium text-[#0a1b42] scale-[0.5] origin-left -mb-2">Description</span>
                <textarea
                  value={newBotDescription}
                  onChange={(e) => setNewBotDescription(e.target.value)}
                  className="cd-textarea"
                  placeholder="What will this bot help with?"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="cd-btn-light h-10 px-4" onClick={() => setShowCreateModal(false)}>
                Cancel
              </button>
              <button type="button" className="cd-btn-dark h-10 px-4" onClick={() => void onCreateBot()} disabled={creating}>
                {creating ? "Creating..." : "Create Bot"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
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
