"use client";

import { useEffect, useSyncExternalStore, useState } from "react";
import { useRouter } from "next/navigation";

import { clearSession, getToken, getUserEmail } from "../../services/auth";
import { createBot, getAnalytics, listBots, type AnalyticsOverview, type Bot } from "../../services/bot";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [bots, setBots] = useState<Bot[]>([]);
  const [error, setError] = useState("");
  const [newBotName, setNewBotName] = useState("");
  const [newBotDescription, setNewBotDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [showCreateCard, setShowCreateCard] = useState(false);
  const router = useRouter();
  const userEmail = useSyncExternalStore(
    () => () => {},
    () => getUserEmail(),
    () => null,
  );

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    async function load() {
      try {
        const [overview, botList] = await Promise.all([getAnalytics(token), listBots(token)]);
        setAnalytics(overview);
        setBots(botList);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      }
    }
    load();
  }, [router]);

  function logout() {
    clearSession();
    router.push("/login");
  }

  async function onCreateBot() {
    const token = getToken();
    if (!token || creating) {
      return;
    }
    const name = newBotName.trim();
    const description = newBotDescription.trim();
    if (name.length < 2 || name.length > 80) {
      setError("Bot name must be between 2 and 80 characters.");
      return;
    }
    if (description.length > 400) {
      setError("Description must be 400 characters or less.");
      return;
    }

    setCreating(true);
    setError("");
    try {
      const created = await createBot(token, name, description || undefined);
      const [overview, botList] = await Promise.all([getAnalytics(token), listBots(token)]);
      setAnalytics(overview);
      setBots(botList);
      setNewBotName("");
      setNewBotDescription("");
      router.push(`/dashboard/bots?botId=${created.id}&section=manage`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create bot");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#09070f] via-[#120b1f] to-[#09070f] p-6">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-purple-200">Dashboard</h1>
            <p className="text-sm text-purple-100/80">{userEmail || "Authenticated user"}</p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setShowCreateCard((prev) => !prev)}
              className="btn-primary rounded-md px-4 py-2 text-sm font-semibold"
            >
              {showCreateCard ? "Close Create" : "Create Bot"}
            </button>
            <button onClick={logout} className="btn-primary rounded-md px-4 py-2 text-sm font-semibold">
              Logout
            </button>
          </div>
        </div>

        {error ? <p className="mt-4 text-sm text-red-400">{error}</p> : null}

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard label="Bots" value={analytics?.total_bots ?? 0} />
          <StatCard label="Documents" value={analytics?.total_documents ?? 0} />
          <StatCard label="Chunks" value={analytics?.total_chunks ?? 0} />
          <StatCard label="Queries" value={analytics?.total_queries ?? 0} />
          <StatCard label="Cached" value={analytics?.cached_queries ?? 0} />
        </div>

        {showCreateCard ? (
          <div className="panel mt-8 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-purple-200">Create Bot</h2>
            <p className="mt-1 text-sm text-purple-100/75">Create first, then continue in Manage Bot for uploads, chat testing, and integrations.</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <input
                value={newBotName}
                onChange={(e) => setNewBotName(e.target.value)}
                placeholder="Bot name"
                className="input-dark rounded-md px-3 py-2"
                minLength={2}
                maxLength={80}
                required
              />
              <input
                value={newBotDescription}
                onChange={(e) => setNewBotDescription(e.target.value)}
                placeholder="Short description"
                className="input-dark rounded-md px-3 py-2"
                maxLength={400}
              />
            </div>
            <button
              type="button"
              onClick={onCreateBot}
              disabled={creating}
              className="btn-primary mt-4 rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-50"
            >
              {creating ? "Creating..." : "Create and Open Manage"}
            </button>
          </div>
        ) : null}

        <div className="panel mt-8 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-purple-200">Your Bots</h2>
          <div className="mt-4 space-y-3">
            {bots.length === 0 ? <p className="text-sm text-purple-100/80">No bots yet. Create one from the Create Bot button.</p> : null}
            {bots.map((bot) => (
              <div key={bot.id} className="rounded-lg border border-purple-900/60 bg-[#0f0c18] p-4">
                <p className="font-medium text-purple-100">{bot.bot_name}</p>
                <p className="mt-1 text-sm text-purple-100/80">{bot.description || "No description"}</p>
                <p className="mt-1 text-xs text-purple-300/70">
                  Documents: {bot.document_count} | Chunks: {bot.chunk_count}
                </p>
                <a
                  href={`/dashboard/bots?botId=${bot.id}&section=manage`}
                  className="btn-secondary mt-3 inline-block rounded-md px-3 py-1.5 text-xs font-semibold"
                >
                  Manage
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel rounded-lg p-4">
      <p className="text-xs uppercase tracking-wide text-purple-200/70">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-purple-100">{value}</p>
    </div>
  );
}
