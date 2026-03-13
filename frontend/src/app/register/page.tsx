"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { register, setSession } from "../../services/auth";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await register(email, password);
      setSession(result.access_token, result.email);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#09070f] via-[#120b1f] to-[#09070f] px-6 py-12">
      <div className="panel mx-auto max-w-md rounded-xl p-8 shadow-[0_12px_36px_rgba(0,0,0,0.4)]">
        <h1 className="text-2xl font-bold text-purple-200">Create Account</h1>
        <p className="mt-2 text-sm text-purple-100/80">Start building your first chatbot.</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-dark w-full rounded-md px-3 py-2"
            required
          />
          <input
            type="password"
            placeholder="Password (min 8 chars)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-dark w-full rounded-md px-3 py-2"
            required
          />
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full rounded-md px-4 py-2 font-semibold disabled:opacity-60"
          >
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>
        <p className="mt-4 text-sm text-purple-100/80">
          Already have an account?{" "}
          <a className="font-medium text-purple-300 hover:text-purple-200" href="/login">
            Login
          </a>
        </p>
      </div>
    </div>
  );
}
