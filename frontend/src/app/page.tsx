export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0712] via-[#100a1d] to-[#1d0f35] text-purple-50">
      <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-purple-300">ChatDock</p>
        <h1 className="mt-4 max-w-2xl text-4xl font-bold leading-tight sm:text-5xl">
          Build document-trained chatbots and deploy them in minutes.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-purple-100/80">
          Upload docs, run RAG queries, and track usage analytics from one dashboard.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <a href="/register" className="btn-primary rounded-lg px-6 py-3 font-semibold">
            Create Account
          </a>
          <a href="/login" className="btn-primary rounded-lg px-6 py-3 font-semibold">
            Login
          </a>
          <a href="/dashboard" className="btn-primary rounded-lg px-6 py-3 font-semibold">
            Open Dashboard
          </a>
        </div>
      </main>
    </div>
  );
}
