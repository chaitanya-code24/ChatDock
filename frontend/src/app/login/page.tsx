"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { getToken, login, setSession } from "../../services/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      router.replace("/dashboard");
    }
  }, [router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) {
      return;
    }

    setError("");
    setLoading(true);
    try {
      const result = await login(email.trim(), password);
      setSession(result.access_token, result.email);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <Link
        href="/"
        className="fixed top-6 left-6 z-20 inline-flex items-center gap-2 rounded-full border border-[#cfd8e4] bg-white/92 px-4 py-2 text-sm font-semibold text-[#0c214b] shadow-[0_10px_24px_rgba(26,42,74,0.08)] transition hover:bg-white"
      >
        <span aria-hidden="true">←</span>
        <span>Back to home</span>
      </Link>

      <div className="auth-shell">
        <aside className="auth-brand">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/25 px-3 py-1 text-xs font-semibold">
            ChatDock
          </span>
          <h2>Welcome back</h2>
          <p>Sign in to manage bots, upload documents, and monitor analytics.</p>
          <ul className="auth-feature-list">
            <li>• Build document-aware AI bots</li>
            <li>• Embed widgets and API integrations</li>
            <li>• Track usage and cache performance</li>
          </ul>
        </aside>

        <section className="auth-card">
          <h1>Login</h1>
          <p>Continue to your ChatDock workspace.</p>

          <form onSubmit={onSubmit}>
            <label className="auth-label">
              <span className="auth-label-text">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="auth-input"
                autoComplete="email"
                required
              />
            </label>

            <label className="auth-label">
              <span className="auth-label-text">Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="auth-input"
                autoComplete="current-password"
                required
              />
            </label>

            {error ? <p className="auth-error">{error}</p> : null}

            <button type="submit" className="auth-primary" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="auth-footer">
            New to ChatDock? <Link href="/register">Create account</Link>
          </p>
        </section>
      </div>
    </div>
  );
}
