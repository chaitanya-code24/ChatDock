import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#eceff3] text-[#03143a]">
      <header className="border-b border-[#d3dbe6] bg-[#f8fafc]">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-[9px] bg-[#2459ea] text-white">
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
                <rect x="3.5" y="7" width="17" height="12.5" rx="2.5" strokeWidth="1.7" />
                <path d="M8 7V5.6A1.6 1.6 0 019.6 4h4.8A1.6 1.6 0 0116 5.6V7M9 12h6M12 9v6" strokeWidth="1.7" />
              </svg>
            </span>
            <span className="text-xl font-bold">ChatDock</span>
          </Link>
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

      <main className="mx-auto w-full max-w-6xl px-6 py-12">
        <section className="grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <span className="inline-flex rounded-full border border-[#c7d1df] bg-[#f8fafc] px-3 py-1 text-xs font-semibold text-[#28436d]">
              Document-trained AI support platform
            </span>
            <h1 className="mt-4 text-5xl font-bold leading-tight tracking-tight text-[#03143a]">
              Build and launch your
              <span className="text-[#2459ea]"> custom chatbot </span>
              in minutes
            </h1>
            <p className="mt-4 max-w-xl text-lg text-[#4b6283]">
              Upload PDFs, docs, or knowledge files. ChatDock indexes them with RAG and gives you a production-ready bot
              for website embedding and API integration.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/register" className="cd-btn-dark px-5">
                Create Free Bot
              </Link>
              <Link href="/dashboard" className="cd-btn-light px-5">
                Open Dashboard
              </Link>
            </div>
            <div className="mt-6 grid max-w-xl grid-cols-3 gap-3">
              <Stat title="1-2s" subtitle="response time" />
              <Stat title="20/min" subtitle="rate limits" />
              <Stat title="RAG" subtitle="source-based answers" />
            </div>
          </div>

          <div className="cd-card cd-shadow p-5">
            <div className="rounded-xl border border-[#d0d8e3] bg-[#f8fafc] p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#4f6688]">Live Demo</p>
              <div className="mt-3 space-y-2">
                <div className="rounded-lg bg-[#e2e8f1] px-3 py-2 text-sm text-[#091b3f]">
                  What is your refund policy?
                </div>
                <div className="rounded-lg border border-[#d0d8e3] bg-[#f8fafc] px-3 py-2 text-sm text-[#18345f]">
                  Refund requests are processed within 5 business days after inspection.
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-[#eef3fa] px-3 py-2 text-xs text-[#425a7f]">
                <span className="inline-flex h-2 w-2 rounded-full bg-[#16a34a]" />
                Sources attached from indexed documents
              </div>
            </div>
          </div>
        </section>

        <section className="mt-12 grid gap-4 md:grid-cols-3">
          <Feature
            title="Upload Knowledge"
            desc="Train your bot on PDF, TXT, DOCX, and MD files with automatic chunking."
          />
          <Feature
            title="Embed Anywhere"
            desc="Ship to websites with one script tag or query directly via secure API."
          />
          <Feature
            title="Track Performance"
            desc="Monitor usage, cache hits, and query trends in your analytics dashboard."
          />
        </section>

        <section className="mt-12 cd-card p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-[#03143a]">Ready to launch your first chatbot?</h2>
              <p className="mt-1 text-[#4b6283]">Create your workspace and go live with ChatDock today.</p>
            </div>
            <Link href="/register" className="cd-btn-dark px-5">
              Start Building
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

function Stat({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="cd-card p-3">
      <p className="text-lg font-bold text-[#07193f]">{title}</p>
      <p className="text-xs text-[#5b7090]">{subtitle}</p>
    </div>
  );
}

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <article className="cd-card p-4">
      <h3 className="text-lg font-semibold text-[#06163b]">{title}</h3>
      <p className="mt-1 text-sm text-[#4d6385]">{desc}</p>
    </article>
  );
}
