"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { getToken, register, setSession } from "../../services/auth";

export default function RegisterPage() {
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
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setError("");
    setLoading(true);
    try {
      const result = await register(email.trim(), password);
      setSession(result.access_token, result.email);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <aside className="auth-brand">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/25 px-3 py-1 text-xs font-semibold">
            ChatDock
          </span>
          <h2>Create your workspace</h2>
          <p>Launch document-trained chatbots for support, internal ops, and product FAQs.</p>
          <ul className="auth-feature-list">
            <li>• Upload PDF, DOCX, TXT, and MD files</li>
            <li>• RAG answers grounded in your knowledge base</li>
            <li>• Website widget and API deployment ready</li>
          </ul>
        </aside>

        <section className="auth-card">
          <h1>Create Account</h1>
          <p>Set up your ChatDock account in less than a minute.</p>

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
                placeholder="Minimum 8 characters"
                className="auth-input"
                autoComplete="new-password"
                minLength={8}
                required
              />
            </label>

            {error ? <p className="auth-error">{error}</p> : null}

            <button type="submit" className="auth-primary" disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="auth-footer">
            Already have an account? <Link href="/login">Login</Link>
          </p>
        </section>
      </div>
    </div>
  );
}
