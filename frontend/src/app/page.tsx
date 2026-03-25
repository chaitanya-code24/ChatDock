import Link from "next/link";
import Image from "next/image";

const projectTags = ["FastAPI", "Next.js", "Qdrant", "Docker"];

const workflowSteps = [
  {
    index: "1",
    title: "Open your workspace",
    desc: "Create a bot, define its tone, and prepare the support experience you want customers to see.",
  },
  {
    index: "2",
    title: "Upload your knowledge",
    desc: "Train the bot on PDFs, DOCX, TXT, and markdown so answers stay grounded in your real documents.",
  },
  {
    index: "3",
    title: "Launch and monitor",
    desc: "Embed the widget, ship the API, and watch analytics to improve your highest-volume questions.",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#eceff3] text-[#03143a]">
      <header className="border-b border-[#d3dbe6] bg-[#f8fafc]/95 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center overflow-hidden">
              <Image src="/chatdock.svg" alt="ChatDocks logo" width={40} height={40} className="h-10 w-10 object-contain" />
            </span>
            <span className="text-xl font-bold">ChatDock</span>
          </Link>

          <nav className="hidden items-center gap-8 text-sm font-medium text-[#4d6385] md:flex">
            <a href="#product" className="transition hover:text-[#0b1f4f]">
              Product
            </a>
            <a href="#workflow" className="transition hover:text-[#0b1f4f]">
              Workflow
            </a>
            <a href="#launch" className="transition hover:text-[#0b1f4f]">
              Launch
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <Link href="/login" className="cd-btn-light h-10 px-4 text-sm">
              Login
            </Link>
            <Link href="/register" className="cd-btn-dark h-10 px-4 text-sm">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-6 py-8 md:py-10">
        <section className="relative overflow-hidden rounded-[34px] border border-[#d8e0ea] bg-[#f8fafc] px-8 py-10 shadow-[0_28px_80px_rgba(36,47,76,0.08)] md:px-10 lg:px-12 lg:py-14">
          <div className="absolute inset-y-0 right-0 hidden w-[42%] bg-[radial-gradient(circle_at_top_right,_rgba(36,89,234,0.12),_transparent_58%),linear-gradient(140deg,rgba(36,89,234,0.05),rgba(248,250,252,0.15)_45%,rgba(36,89,234,0.08))] lg:block" />

          <div className="relative grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <span className="inline-flex rounded-full border border-[#c7d1df] bg-white px-3 py-1 text-xs font-semibold text-[#28436d]">
                Document-trained AI support platform
              </span>
              <h1 className="mt-5 max-w-[11ch] text-5xl font-bold leading-[1.02] tracking-tight text-[#03143a] md:text-6xl">
                Turn your
                <span className="text-[#2459ea]"> documents </span>
                into a support bot that ships fast.
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-8 text-[#4b6283]">
                ChatDock gives teams a cleaner way to upload knowledge, test responses, and launch grounded chatbot
                experiences across websites and product workflows.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <Link href="/register" className="cd-btn-dark px-5">
                  Create Free Bot
                </Link>
                <Link href="/dashboard" className="cd-btn-light px-5">
                  Open Dashboard
                </Link>
              </div>

              <div className="mt-7 flex flex-wrap items-center gap-3">
                {projectTags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-[#d4dce7] bg-white px-3 py-1.5 text-sm font-semibold text-[#233e67]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="mx-auto max-w-[470px] rounded-[28px] border border-[#d7dfeb] bg-white p-5 shadow-[0_22px_70px_rgba(33,49,79,0.12)]">
                <div className="rounded-[24px] border border-[#d6dee8] bg-[#f7fafe] p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#5b7090]">Live Support Demo</p>
                      <h2 className="mt-2 text-xl font-semibold text-[#081a41]">Customer Support Bot</h2>
                      <p className="mt-1 text-sm text-[#607493]">Trained on policies, FAQs, and support procedures.</p>
                    </div>
                    <div className="rounded-2xl bg-[#2459ea] px-3 py-2 text-right text-white">
                      <p className="text-[11px] uppercase tracking-[0.12em] text-white/70">Accuracy</p>
                      <p className="text-xl font-semibold">RAG</p>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3">
                    <div className="rounded-2xl bg-[#e8eef8] px-4 py-3 text-base font-medium text-[#0d2351]">
                      What is your refund policy?
                    </div>
                    <div className="rounded-2xl border border-[#d2dbe8] bg-white px-4 py-4 text-[15px] leading-7 text-[#18345f]">
                      Refund requests are reviewed after inspection, then processed within five business days. Customers
                      can track status from the support portal or through the website widget.
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <MetricCard title="1-2s" subtitle="typical response time" />
                      <MetricCard title="Widget + API" subtitle="deployment ready" />
                    </div>
                    <div className="flex items-center gap-2 rounded-2xl bg-[#edf3fb] px-4 py-3 text-sm text-[#4a6285]">
                      <span className="inline-flex h-2.5 w-2.5 rounded-full bg-[#16a34a]" />
                      Sources attached from indexed documents
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="product" className="mt-10 rounded-[30px] border border-[#d8e0ea] bg-[#f8fafc] p-8 shadow-[0_24px_70px_rgba(30,48,76,0.06)] md:p-10">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6a7d99]">Future of support</p>
              <h2 className="mt-3 max-w-[14ch] text-4xl font-bold leading-tight text-[#03143a]">
                A document support system built to scale with your team.
              </h2>
            </div>
            <p className="max-w-md text-base leading-7 text-[#576d8e]">
              Design one grounded workflow for policies, support playbooks, onboarding docs, or product FAQs, then reuse
              it across bots, integrations, and analytics.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <Feature
              icon="⟳"
              title="Reusable knowledge"
              desc="Index the same document base once and serve it through chat, widget, and API."
            />
            <Feature
              icon="⌘"
              title="Multiple deployments"
              desc="Launch on websites, internal tools, and support workflows without rebuilding your bot."
            />
            <Feature
              icon="◌"
              title="Grounded responses"
              desc="Keep answers tied to indexed documents with retrieval, citations, and analytics feedback."
            />
          </div>
        </section>

        <section className="mt-10">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6a7d99]">Why teams choose it</p>
            <h2 className="mt-3 text-4xl font-bold text-[#03143a]">A cleaner path from messy docs to working support.</h2>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="rounded-[26px] border border-[#d8e0ea] bg-[#f8fafc] p-6 shadow-[0_18px_50px_rgba(31,48,78,0.05)]">
              <p className="text-5xl font-bold tracking-tight text-[#2459ea]">3k+</p>
              <p className="mt-4 max-w-[14ch] text-xl font-semibold leading-8 text-[#06163b]">
                Support interactions routed through trained bots.
              </p>
            </div>

            <div className="rounded-[26px] border border-[#d8e0ea] bg-[#f8fafc] p-6 shadow-[0_18px_50px_rgba(31,48,78,0.05)]">
              <h3 className="max-w-[16ch] text-2xl font-semibold leading-9 text-[#06163b]">Launch widget support on your site in a few steps.</h3>
              <div className="mt-8 flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#2459ea] text-lg font-semibold text-white">
                  W
                </span>
                <span className="text-2xl text-[#89a0c2]">↔</span>
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[#d7e0eb] bg-white text-lg font-semibold text-[#0d2351]">
                  A
                </span>
              </div>
            </div>

            <div className="md:col-span-3 grid gap-4 lg:grid-cols-[0.48fr_0.52fr]">
              <div className="rounded-[26px] border border-[#d8e0ea] bg-[#f8fafc] p-6 shadow-[0_18px_50px_rgba(31,48,78,0.05)]">
                <h3 className="text-2xl font-semibold text-[#06163b]">No answer drift</h3>
                <p className="mt-4 max-w-[22ch] text-base leading-7 text-[#556b8c]">
                  Grounded retrieval keeps your support answers anchored to uploaded policies, guides, and FAQs instead of
                  generic chatbot output.
                </p>
              </div>

              <div className="rounded-[26px] border border-[#d8e0ea] bg-[#f8fafc] p-6 shadow-[0_18px_50px_rgba(31,48,78,0.05)]">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-[#6a7d99]">Project Stack</p>
                    <p className="mt-1 text-3xl font-bold text-[#07193f]">Hybrid RAG</p>
                  </div>
                  <span className="rounded-full bg-[#ebf1fb] px-3 py-1 text-xs font-semibold text-[#31507e]">current build</span>
                </div>
                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <StackLine label="Backend" value="FastAPI + PostgreSQL + Redis" />
                  <StackLine label="Frontend" value="Next.js + TypeScript" />
                  <StackLine label="Retrieval" value="Qdrant + BM25 + reranking" />
                  <StackLine label="Runtime" value="Docker + local widget preview" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="workflow" className="mt-10 rounded-[32px] bg-[#072a4a] px-8 py-10 text-white shadow-[0_30px_80px_rgba(7,42,74,0.22)] md:px-10 md:py-12">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-white/65">Step by step</p>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
            <h2 className="max-w-[14ch] text-4xl font-bold leading-tight">Build a support engine your team can actually manage.</h2>
            <p className="max-w-md text-base leading-7 text-white/72">
              Keep the workflow simple: index documents, validate the experience, and ship the same bot wherever users need help.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {workflowSteps.map((step) => (
              <article key={step.index} className="rounded-[24px] border border-white/10 bg-white/6 p-5 backdrop-blur-sm">
                <p className="text-5xl font-bold leading-none text-white/28">{step.index}</p>
                <h3 className="mt-6 text-xl font-semibold text-white">{step.title}</h3>
                <p className="mt-2 text-sm leading-7 text-white/70">{step.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-10 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6a7d99]">Our mission</p>
          <h2 className="mt-3 text-4xl font-bold text-[#03143a]">Help teams turn internal knowledge into customer-ready support.</h2>
          <p className="mx-auto mt-3 max-w-2xl text-base leading-7 text-[#586d8e]">
            ChatDock is built for fast-moving teams that want grounded AI support without building a full custom retrieval stack from scratch.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <Milestone value="RAG" label="document-grounded responses" />
            <Milestone value="API" label="integration-ready endpoints" />
            <Milestone value="UI" label="dashboard, widget, analytics" />
          </div>
        </section>

        <section id="launch" className="mt-10 rounded-[32px] bg-[#072a4a] px-8 py-10 text-white shadow-[0_30px_80px_rgba(7,42,74,0.22)] md:px-10">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="max-w-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-white/65">Try it now</p>
              <h2 className="mt-3 text-4xl font-bold leading-tight">Ready to launch a chatbot your team can trust?</h2>
              <p className="mt-3 text-base leading-7 text-white/72">
                Start with one bot, train it on real documents, and ship support that feels fast, grounded, and production-ready.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/register" className="rounded-xl bg-[#2459ea] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1949cf]">
                Get Started Now
              </Link>
              <Link
                href="/login"
                className="rounded-xl border border-white/15 bg-white/6 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Learn More
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto mt-8 w-full max-w-6xl px-6 pb-10">
        <div className="rounded-[28px] border border-[#d7dfeb] bg-[#f8fafc] px-8 py-8">
          <div className="grid gap-8 md:grid-cols-[1.1fr_1fr]">
            <div>
              <Link href="/" className="inline-flex items-center gap-3">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-[9px] bg-[#2459ea] text-white">
                  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
                    <rect x="3.5" y="7" width="17" height="12.5" rx="2.5" strokeWidth="1.7" />
                    <path d="M8 7V5.6A1.6 1.6 0 019.6 4h4.8A1.6 1.6 0 0116 5.6V7M9 12h6M12 9v6" strokeWidth="1.7" />
                  </svg>
                </span>
                <span className="text-xl font-bold">ChatDock</span>
              </Link>
              <p className="mt-4 max-w-md text-sm leading-7 text-[#566c8d]">
                Build document-aware support bots, test them in real workflows, and launch them through widget and API.
              </p>
            </div>
            <div className="grid gap-6 sm:grid-cols-3">
              <FooterColumn title="Project" links={["Bots", "Analytics", "Integrations"]} />
              <FooterColumn title="Resources" links={["Docs", "Architecture", "Setup"]} />
              <FooterColumn title="Code" links={["GitHub", "Frontend", "Backend"]} />
            </div>
          </div>
          <p className="mt-8 border-t border-[#e0e6ef] pt-5 text-xs text-[#7387a3]">© ChatDock. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

function Feature({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <article className="rounded-2xl border border-[#d5dce6] bg-white p-5">
      <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ebf1fb] text-lg font-semibold text-[#2459ea]">
        {icon}
      </span>
      <h3 className="mt-5 text-lg font-semibold text-[#06163b]">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-[#4d6385]">{desc}</p>
    </article>
  );
}

function MetricCard({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-2xl border border-[#d7e0eb] bg-[#f8fafc] p-4">
      <p className="text-xl font-bold text-[#07193f]">{title}</p>
      <p className="mt-1 text-xs uppercase tracking-[0.1em] text-[#647896]">{subtitle}</p>
    </div>
  );
}

function Milestone({ value, label }: { value: string; label: string }) {
  return (
    <article className="rounded-[24px] border border-[#d8e0ea] bg-[#f8fafc] p-6 shadow-[0_16px_44px_rgba(31,48,78,0.04)]">
      <p className="text-5xl font-bold tracking-tight text-[#07193f]">{value}</p>
      <p className="mt-3 text-sm font-medium uppercase tracking-[0.08em] text-[#68809e]">{label}</p>
    </article>
  );
}

function StackLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#dce4ee] bg-white px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[#6a7d99]">{label}</p>
      <p className="mt-1 text-sm font-medium text-[#0f254e]">{value}</p>
    </div>
  );
}

function FooterColumn({ title, links }: { title: string; links: string[] }) {
  return (
    <div>
      <p className="text-sm font-semibold text-[#07193f]">{title}</p>
      <div className="mt-3 space-y-2">
        {links.map((link) => (
          <p key={link} className="text-sm text-[#5c7191]">
            {link}
          </p>
        ))}
      </div>
    </div>
  );
}
