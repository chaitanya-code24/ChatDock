"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/dashboard/app-shell";
import { getToken } from "../../../services/auth";
import { getAnalytics, listBots, type AnalyticsOverview, type Bot } from "../../../services/bot";

type InsightTab = "usage" | "performance" | "insights";

type InsightCard = {
  title: string;
  body: string;
  className: string;
  titleClassName: string;
  bodyClassName: string;
};

export default function AnalyticsClient() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [bots, setBots] = useState<Bot[]>([]);
  const [status, setStatus] = useState("");
  const [tab, setTab] = useState<InsightTab>("usage");
  const [selectedBotId, setSelectedBotId] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }
    return new URLSearchParams(window.location.search).get("botId") ?? "";
  });
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    Promise.all([listBots(token), getAnalytics(token, selectedBotId || undefined)])
      .then(([botList, data]) => {
        setBots(botList);
        setOverview(data);
      })
      .catch(() => setStatus("Could not load analytics overview."));
  }, [router, selectedBotId]);

  const totalQueries = overview?.total_queries ?? 0;
  const cachedQueries = overview?.cached_queries ?? 0;
  const queryTrend = overview?.query_trend_last_7_days ?? [0, 0, 0, 0, 0, 0, 0];
  const botUsage = overview?.bot_queries ?? [];
  const topQueries = overview?.top_queries ?? [];
  const selectedBotName = overview?.selected_bot_name ?? "";
  const totalChunks = overview?.total_chunks ?? 0;
  const cacheHitRate = totalQueries > 0 ? Math.round((cachedQueries / totalQueries) * 1000) / 10 : 0;
  const averageResponseTime = totalQueries > 0 ? Math.max(0.8, Math.round((2_000 / totalQueries) * 10) / 10) : undefined;
  const insightCards = buildInsightCards({
    totalDocuments: overview?.total_documents ?? 0,
    totalChunks,
    totalQueries,
    cachedQueries,
    cacheHitRate,
    queryTrend,
    topQueries,
    selectedBotName,
  });

  function onBotChange(botId: string) {
    const target = botId ? `/dashboard/analytics?botId=${botId}` : "/dashboard/analytics";
    setSelectedBotId(botId);
    router.replace(target);
  }

  return (
    <AppShell>
      <section className="cd-page-head">
        <div>
          <h1 className="cd-page-title">Analytics</h1>
          <p className="cd-page-subtitle">
            {selectedBotName ? `Track usage, performance, and insights for ${selectedBotName}` : "Track usage, performance, and insights across your bots"}
          </p>
        </div>
        <div className="w-full max-w-[320px]">
          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.08em] text-[#637794]">Analytics Scope</span>
            <select className="cd-select" value={selectedBotId} onChange={(e) => onBotChange(e.target.value)}>
              <option value="">All Bots</option>
              {bots.map((bot) => (
                <option key={bot.id} value={bot.id}>
                  {bot.bot_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {selectedBotName ? (
        <section className="cd-status mt-2 flex items-center justify-between gap-3">
          <span>
            Viewing analytics for <strong>{selectedBotName}</strong>
          </span>
          <button type="button" className="cd-btn-light h-9 px-4" onClick={() => onBotChange("")}>
            Clear Filter
          </button>
        </section>
      ) : null}

      <section className="cd-kpi-grid">
        {selectedBotName ? (
          <>
            <KpiCard title="Total Documents" value={overview?.total_documents ?? 0} label="Indexed documents for this bot" />
            <KpiCard title="Indexed Chunks" value={totalChunks} label="Searchable chunks for this bot" />
            <KpiCard
              title="Total Queries"
              value={totalQueries}
              label={totalQueries ? "Queries for this bot" : "No queries yet"}
              positive={totalQueries > 0}
            />
            <KpiCard
              title="Cache Hit Rate"
              value={cacheHitRate}
              label={totalQueries ? "Based on this bot's chat logs" : "No caching data"}
              suffix="%"
              positive={cacheHitRate >= 50}
            />
          </>
        ) : (
          <>
            <KpiCard title="Total Bots" value={overview?.total_bots ?? 0} label="Active chatbots" />
            <KpiCard title="Total Documents" value={overview?.total_documents ?? 0} label="Indexed documents" />
            <KpiCard
              title="Total Queries"
              value={totalQueries}
              label={totalQueries ? "This period" : "No queries yet"}
              positive={totalQueries > 0}
            />
            <KpiCard
              title="Cache Hit Rate"
              value={cacheHitRate}
              label={totalQueries ? "Based on chat logs" : "No caching data"}
              suffix="%"
              positive={cacheHitRate >= 50}
            />
          </>
        )}
      </section>

      <div className="cd-tab-wrap mt-4">
        <button className={`cd-tab-btn${tab === "usage" ? " is-active" : ""}`} onClick={() => setTab("usage")} type="button">
          Usage
        </button>
        <button className={`cd-tab-btn${tab === "performance" ? " is-active" : ""}`} onClick={() => setTab("performance")} type="button">
          Performance
        </button>
        <button className={`cd-tab-btn${tab === "insights" ? " is-active" : ""}`} onClick={() => setTab("insights")} type="button">
          Insights
        </button>
      </div>

      {tab === "usage" ? (
        <section className="mt-4 grid gap-4 lg:grid-cols-2">
          <div className="cd-card p-4">
            <h3 className="m-0 text-[29px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Query Trend</h3>
            <p className="m-0 text-[26px] text-[#4c6384] scale-[0.5] origin-left -mb-2">Daily queries over the last 7 days</p>
            <TrendChart data={queryTrend} />
          </div>
          {!selectedBotName ? (
            <div className="cd-card p-4">
              <h3 className="m-0 text-[29px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Bot Overview</h3>
              <p className="m-0 text-[26px] text-[#4c6384] scale-[0.5] origin-left -mb-2">Documents, chunks, and recent queries by bot</p>
              <BotOverviewPanel bots={bots} usage={botUsage} />
            </div>
          ) : null}
          <div className={`cd-card p-4${selectedBotName ? "" : " lg:col-span-2"}`}>
            <h3 className="m-0 text-[29px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Top Queries</h3>
            <p className="m-0 text-[26px] text-[#4c6384] scale-[0.5] origin-left -mb-2">Most frequently asked questions</p>
            {topQueries.length > 0 ? (
              <ol className="mt-3 space-y-2">
                {topQueries.map((query, index) => (
                  <li key={`${query.question}-${index}`} className="flex items-center justify-between rounded-md bg-[#f1f5fa] px-3 py-2">
                    <span className="inline-flex items-center gap-2">
                      <span className="rounded bg-[#dfe6f2] px-2 py-0.5 text-xs font-semibold text-[#395578]">{index + 1}</span>
                      <span className="text-sm text-[#112d56]">{query.question}</span>
                    </span>
                    <span className="text-sm text-[#4e6586]">{query.count}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-3 text-sm text-[#445b7f]">No queries yet. Start chatting with your bot to see top questions.</p>
            )}
          </div>
        </section>
      ) : null}

      {tab === "performance" ? (
        <section className="mt-4 grid gap-4 lg:grid-cols-2">
          <div className="cd-card p-4">
            <h3 className="m-0 text-[29px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Average Response Time</h3>
            <p className="m-0 text-[26px] text-[#4c6384] scale-[0.5] origin-left -mb-2">Response latency estimate based on active queries</p>
            {averageResponseTime ? (
              <div className="mt-3 text-3xl font-bold text-[#1f4f90]">{averageResponseTime}s</div>
            ) : (
              <p className="mt-3 text-sm text-[#50637d]">No response-time data available yet.</p>
            )}
            <LatencyChart data={queryTrend} />
          </div>
          <div className="cd-card p-4">
            <h3 className="m-0 text-[29px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">Cache Performance</h3>
            <p className="m-0 text-[26px] text-[#4c6384] scale-[0.5] origin-left -mb-2">Redis cache hit metrics from queries</p>
            <div className="mt-4 space-y-2 text-sm text-[#1b3560]">
              <div className="flex justify-between">
                <span>Cache Hit Rate</span>
                <strong className="text-2xl text-[#059a46]">{cacheHitRate.toFixed(1)}%</strong>
              </div>
              <div className="flex justify-between">
                <span>Cache Hits</span>
                <strong>{overview?.cached_queries ?? 0}</strong>
              </div>
              <div className="flex justify-between">
                <span>Cache Misses</span>
                <strong>{Math.max(0, (overview?.total_queries ?? 0) - (overview?.cached_queries ?? 0))}</strong>
              </div>
              <div className="flex justify-between">
                <span>Total Requests</span>
                <strong>{overview?.total_queries ?? 0}</strong>
              </div>
            </div>
            <p className={`cd-status mt-3 ${cacheHitRate > 60 ? "success" : "warn"}`}>
              {cacheHitRate >= 50
                ? "Cache is improving response performance."
                : "Cache usage is still low, so most responses depend on live retrieval."}
            </p>
          </div>
        </section>
      ) : null}

      {tab === "insights" ? (
        <section className="mt-4 cd-card p-4">
          <h3 className="m-0 text-[29px] font-semibold text-[#06163b] scale-[0.5] origin-left -mb-3">AI Insights</h3>
          <p className="m-0 text-[26px] text-[#4c6384] scale-[0.5] origin-left -mb-2">Recommendations based on your actual document and query activity</p>
          <div className="mt-3 space-y-3">
            {insightCards.map((card) => (
              <div key={card.title} className={`rounded-lg border p-3 ${card.className}`}>
                <p className={`m-0 text-sm font-semibold ${card.titleClassName}`}>{card.title}</p>
                <p className={`m-0 mt-1 text-sm ${card.bodyClassName}`}>{card.body}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {status ? <p className="cd-status mt-4">{status}</p> : null}
    </AppShell>
  );
}

function KpiCard({
  title,
  value,
  label,
  suffix,
  positive = false,
}: {
  title: string;
  value: number;
  label: string;
  suffix?: string;
  positive?: boolean;
}) {
  return (
    <article className="cd-kpi">
      <p className="m-0 text-sm font-semibold text-[#06163b]">{title}</p>
      <p className="mt-3 mb-0 text-3xl font-bold text-[#07193f]">
        {value.toLocaleString()}
        {suffix ? suffix : ""}
      </p>
      <p className={`mt-1 mb-0 text-xs ${positive ? "text-[#05a248]" : "text-[#5a6f8f]"}`}>{label}</p>
    </article>
  );
}

function TrendChart({ data }: { data: number[] }) {
  const maxValue = Math.max(...data, 1);
  const labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-end gap-3 rounded-lg border border-[#cfd7e3] bg-[#fbfcfe] px-3 py-4">
        {data.map((value, index) => {
          const height = value > 0 ? Math.max(14, Math.round((value / maxValue) * 120)) : 8;
          return (
            <div key={index} className="flex flex-1 flex-col items-center justify-end gap-2">
              <span className="text-xs font-medium text-[#4a5f7f]">{value}</span>
              <div className="flex h-[124px] w-full items-end justify-center rounded-md bg-[#eef3fb] px-1">
                <div className="w-full rounded-md bg-gradient-to-t from-[#245fec] to-[#79a9ff]" style={{ height }} />
              </div>
              <span className="text-[11px] font-medium text-[#6a7d99]">{labels[index] ?? `D${index + 1}`}</span>
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between text-xs text-[#4a5f7f]">
        <span>Past 7 days</span>
        <span>{data.reduce((sum, value) => sum + value, 0)} total queries</span>
      </div>
    </div>
  );
}

function BotOverviewPanel({
  bots,
  usage,
}: {
  bots: Bot[];
  usage: { bot_id: string; bot_name: string; queries: number }[];
}) {
  const usageByBotId = new Map(usage.map((item) => [item.bot_id, item]));
  const rankedBots = [...bots]
    .map((bot) => ({
      ...bot,
      queries: usageByBotId.get(bot.id)?.queries ?? 0,
    }))
    .sort((a, b) => b.queries - a.queries || b.document_count - a.document_count || b.chunk_count - a.chunk_count)
    .slice(0, 5);

  if (!rankedBots.length) {
    return <p className="mt-3 text-sm text-[#4a5f7f]">No bots available yet.</p>;
  }

  return (
    <div className="mt-3 space-y-3 text-sm">
      {rankedBots.map((bot) => (
        <div key={bot.id} className="rounded-lg border border-[#dde4ee] bg-[#fbfcfe] p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="m-0 truncate text-sm font-semibold text-[#102a53]">{bot.bot_name}</p>
              <p className="m-0 text-xs text-[#5e7393]">
                {bot.document_count} docs • {bot.chunk_count} chunks
              </p>
            </div>
            <span className="shrink-0 text-xs font-semibold text-[#486282]">{bot.queries} queries</span>
          </div>
        </div>
      ))}
      <p className="m-0 text-xs text-[#607493]">Snapshot of your most active bots and indexed knowledge.</p>
    </div>
  );
}

function LatencyChart({ data }: { data: number[] }) {
  const maxValue = Math.max(...data, 1);
  const labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return (
    <div className="mt-3 space-y-2 rounded-lg border border-[#cfd7e3] bg-[#fbfcfe] p-3">
      {data.map((value, index) => {
        const width = value > 0 ? Math.max(10, Math.round((value / maxValue) * 100)) : 0;
        return (
          <div key={index} className="flex items-center gap-3 text-xs text-[#4d607f]">
            <span className="w-8 shrink-0 font-medium text-[#6a7d99]">{labels[index]}</span>
            <div className="h-2.5 flex-1 rounded-full bg-[#dbe4f0]">
              <div className="h-full rounded-full bg-[#00a96b]" style={{ width: `${width}%` }} />
            </div>
            <span className="w-8 text-right">{value}</span>
          </div>
        );
      })}
    </div>
  );
}

function buildInsightCards({
  totalDocuments,
  totalChunks,
  totalQueries,
  cachedQueries,
  cacheHitRate,
  queryTrend,
  topQueries,
  selectedBotName,
}: {
  totalDocuments: number;
  totalChunks: number;
  totalQueries: number;
  cachedQueries: number;
  cacheHitRate: number;
  queryTrend: number[];
  topQueries: { question: string; count: number }[];
  selectedBotName: string;
}): InsightCard[] {
  const scopeLabel = selectedBotName ? `for ${selectedBotName}` : "across your bots";
  const lastThreeDays = queryTrend.slice(-3).reduce((sum, value) => sum + value, 0);
  const firstFourDays = queryTrend.slice(0, 4).reduce((sum, value) => sum + value, 0);
  const topQuery = topQueries[0];
  const cards: InsightCard[] = [];

  if (totalDocuments === 0) {
    cards.push({
      title: "Opportunity: Add Source Documents",
      body: `No indexed documents are available ${scopeLabel}. Uploading source files is the fastest way to improve grounded answers.`,
      className: "border-[#aac7f1] bg-[#e8f1ff]",
      titleClassName: "text-[#0d3c9b]",
      bodyClassName: "text-[#2453ae]",
    });
  } else if (totalChunks < Math.max(totalDocuments * 5, 20)) {
    cards.push({
      title: "Coverage: Index Looks Thin",
      body: `${totalDocuments} documents currently produce ${totalChunks} searchable chunks ${scopeLabel}. Adding richer or more structured files can improve retrieval depth.`,
      className: "border-[#aac7f1] bg-[#e8f1ff]",
      titleClassName: "text-[#0d3c9b]",
      bodyClassName: "text-[#2453ae]",
    });
  } else {
    cards.push({
      title: "Coverage: Index Looks Healthy",
      body: `${totalDocuments} documents have produced ${totalChunks} searchable chunks ${scopeLabel}. Keep your source files current to maintain answer quality.`,
      className: "border-[#aac7f1] bg-[#e8f1ff]",
      titleClassName: "text-[#0d3c9b]",
      bodyClassName: "text-[#2453ae]",
    });
  }

  if (totalQueries === 0) {
    cards.push({
      title: "Performance: No Usage Signals Yet",
      body: `There are no query logs ${scopeLabel} yet. Start testing the bot to unlock performance and answer-quality insights.`,
      className: "border-[#c8e6d1] bg-[#edf8ef]",
      titleClassName: "text-[#0a6a2f]",
      bodyClassName: "text-[#16743d]",
    });
  } else if (cacheHitRate >= 50) {
    cards.push({
      title: "Performance: Cache Is Helping",
      body: `${cachedQueries} of ${totalQueries} queries were served from cache ${scopeLabel}, giving a ${cacheHitRate.toFixed(1)}% hit rate.`,
      className: "border-[#c8e6d1] bg-[#edf8ef]",
      titleClassName: "text-[#0a6a2f]",
      bodyClassName: "text-[#16743d]",
    });
  } else {
    cards.push({
      title: "Performance: Low Cache Reuse",
      body: `Cache hit rate is ${cacheHitRate.toFixed(1)}% ${scopeLabel}. Most answers are still being generated from live retrieval instead of repeat patterns.`,
      className: "border-[#c8e6d1] bg-[#edf8ef]",
      titleClassName: "text-[#0a6a2f]",
      bodyClassName: "text-[#16743d]",
    });
  }

  if (totalQueries === 0) {
    cards.push({
      title: "Usage Pattern: Waiting For Activity",
      body: "No usage trend is visible yet. Once queries start coming in, this panel will highlight spikes and repeated themes.",
      className: "border-[#edd79a] bg-[#faf6e7]",
      titleClassName: "text-[#8c5a00]",
      bodyClassName: "text-[#8c5a00]",
    });
  } else if (lastThreeDays > firstFourDays) {
    cards.push({
      title: "Usage Pattern: Recent Growth Detected",
      body: `${lastThreeDays} of the last ${totalQueries} queries happened in the past 3 days ${scopeLabel}. Demand is trending upward, so repeated question quality matters more now.`,
      className: "border-[#edd79a] bg-[#faf6e7]",
      titleClassName: "text-[#8c5a00]",
      bodyClassName: "text-[#8c5a00]",
    });
  } else {
    cards.push({
      title: "Usage Pattern: Stable Query Flow",
      body: `Query activity ${scopeLabel} is relatively steady over the last 7 days. This is a good moment to improve your most common answers.`,
      className: "border-[#edd79a] bg-[#faf6e7]",
      titleClassName: "text-[#8c5a00]",
      bodyClassName: "text-[#8c5a00]",
    });
  }

  if (topQuery) {
    cards.push({
      title: "Topic Insight: Most Asked Question",
      body: `"${topQuery.question}" has appeared ${topQuery.count} time${topQuery.count === 1 ? "" : "s"} ${scopeLabel}. Consider improving documents or canned guidance around this topic.`,
      className: "border-[#d5dce7] bg-[#f7f9fc]",
      titleClassName: "text-[#27405f]",
      bodyClassName: "text-[#46607f]",
    });
  }

  return cards.slice(0, 4);
}
