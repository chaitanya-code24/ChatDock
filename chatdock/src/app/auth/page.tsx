"use client";

import { useState } from "react";
import { auth, googleProvider, githubProvider } from "@/firebase";
import { signInWithPopup, signInWithEmailAndPassword, sendPasswordResetEmail } from "firebase/auth";

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [success, setSuccess] = useState("");

  // Google login handler
  const handleGoogleLogin = async () => {
    setError("");
    try {
      await signInWithPopup(auth, googleProvider);
      window.location.href = "/";
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("An unknown error occurred.");
    }
  };

  // GitHub login handler
  const handleGithubLogin = async () => {
    setError("");
    try {
      await signInWithPopup(auth, githubProvider);
      window.location.href = "/";
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("An unknown error occurred.");
    }
  };

  // Email/password login handler
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const form = e.target as HTMLFormElement;
    const email = (form.elements.namedItem("email") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;
    try {
      await signInWithEmailAndPassword(auth, email, password);
      window.location.href = "/";
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("An unknown error occurred.");
    }
    setLoading(false);
  };

  // Password reset handler
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      await sendPasswordResetEmail(auth, resetEmail);
      setSuccess("Password reset email sent!");
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("An unknown error occurred.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#181826] via-[#2d1836] to-[#0a0a23] px-4">
      <div className="w-full max-w-4xl flex flex-col md:flex-row items-stretch justify-center gap-0 md:gap-8">
        {/* Branding Side */}
        <div className="hidden md:flex flex-col justify-center items-center w-1/2 bg-gradient-to-br from-pink-500/20 via-purple-500/20 to-blue-500/10 rounded-l-3xl shadow-2xl relative overflow-hidden">
          <div className="absolute -top-10 -left-10 w-56 h-56 bg-gradient-to-br from-pink-500 via-purple-500 to-blue-500 opacity-30 rounded-full blur-2xl pointer-events-none z-0" />
          <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-gradient-to-tr from-blue-500 via-purple-500 to-pink-500 opacity-20 rounded-full blur-2xl pointer-events-none z-0" />
          <div className="relative z-10 flex flex-col items-center text-center px-8">
            <div className="flex flex-col items-center gap-0">
              <img src="/logo.svg" alt="ChatDock Logo" className="w-32 h-32 mx-auto drop-shadow-lg mb-0" />
              <h2 className="mt-0 mb-0 text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 animate-gradient tracking-tight drop-shadow-lg">
                ChatDock
              </h2>
            </div>
            <p className="text-base text-gray-300 font-medium mb-4">
              Your AI-powered chat assistant for productivity, creativity, and more.
            </p>
            <span className="inline-block bg-gradient-to-r from-pink-500 to-purple-600 text-white text-xs font-semibold px-4 py-1 rounded-full shadow">
              🚀 Fast. No Code. Smart.
            </span>
          </div>
        </div>
        {/* Login Card */}
        <div className="w-full md:w-1/2 bg-gradient-to-br from-[#232347]/80 via-[#181826]/80 to-[#2d1836]/80 backdrop-blur-2xl rounded-3xl shadow-2xl border border-pink-400/30 p-8 sm:p-12 flex flex-col gap-8 relative overflow-hidden">
          {/* Decorative Blobs */}
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-gradient-to-br from-pink-500 via-purple-500 to-blue-500 opacity-30 rounded-full blur-2xl pointer-events-none z-0" />
          <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-gradient-to-tr from-blue-500 via-purple-500 to-pink-500 opacity-20 rounded-full blur-2xl pointer-events-none z-0" />

          <div className="relative z-10 text-center">
            <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 animate-gradient mb-3 tracking-tight drop-shadow-lg">
              Welcome Back
            </h1>
            <p className="text-gray-300 text-base font-medium">
              Sign in to your{" "}
              <span className="text-pink-400 font-bold">ChatDock</span> account
            </p>
          </div>

          {error && (
            <div className="relative z-10 bg-pink-900/60 text-pink-300 text-sm rounded-lg p-2 text-center border border-pink-400/30 shadow">
              {error}
            </div>
          )}
          {success && (
            <div className="relative z-10 bg-green-900/60 text-green-300 text-sm rounded-lg p-2 text-center border border-green-400/30 shadow">
              {success}
            </div>
          )}

          <form className="flex flex-col gap-5 relative z-10" onSubmit={handleSignIn}>
            <div>
              <label className="block text-sm font-semibold text-pink-300 mb-1">Email</label>
              <input
                type="email"
                name="email"
                className="w-full px-4 py-2 rounded-xl bg-[#181826] border border-pink-400/40 text-white focus:outline-none focus:ring-2 focus:ring-pink-400 transition placeholder:text-gray-400"
                placeholder="you@email.com"
                autoComplete="email"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-purple-300 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  className="w-full px-4 py-2 rounded-xl bg-[#181826] border border-purple-400/40 text-white focus:outline-none focus:ring-2 focus:ring-purple-400 transition placeholder:text-gray-400"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-pink-300 hover:text-purple-300 transition"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
            <div className="flex justify-between items-center mt-1">
              <button
                type="button"
                onClick={() => setShowReset((v) => !v)}
                className="text-xs text-pink-400 hover:underline hover:text-purple-400 transition bg-transparent border-none p-0 font-semibold"
              >
                Forgot password?
              </button>
              <a
                href="/register"
                className="text-xs text-purple-400 hover:underline hover:text-pink-400 transition font-semibold"
              >
                Create account
              </a>
            </div>
            {showReset && (
              <form className="mt-2 flex flex-col gap-2" onSubmit={handleResetPassword}>
                <input
                  type="email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="w-full px-4 py-2 rounded-xl bg-[#181826] border border-pink-400/40 text-white focus:outline-none focus:ring-2 focus:ring-pink-400 transition placeholder:text-gray-400"
                  placeholder="Enter your email"
                  required
                />
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-600 hover:from-purple-600 hover:to-pink-500 text-white font-bold py-2 rounded-xl shadow-lg transition-all hover:scale-105"
                >
                  Send Reset Link
                </button>
              </form>
            )}
            <button
              type="submit"
              className="mt-2 w-full bg-gradient-to-r from-pink-500 to-purple-600 hover:from-purple-600 hover:to-pink-500 text-white font-bold py-2.5 rounded-xl shadow-lg transition-all hover:scale-105"
              disabled={loading}
            >
              {loading ? "Signing In..." : "Sign In"}
            </button>
          </form>

          <div className="flex items-center gap-2 my-2 relative z-10">
            <div className="flex-1 h-px bg-gradient-to-r from-pink-400/30 via-purple-400/30 to-blue-400/30" />
            <span className="text-xs text-gray-400">or</span>
            <div className="flex-1 h-px bg-gradient-to-r from-pink-400/30 via-purple-400/30 to-blue-400/30" />
          </div>

          <div className="flex flex-col gap-3 relative z-10">
            <button
              type="button"
              onClick={handleGoogleLogin}
              className="flex items-center justify-center gap-3 w-full py-2.5 rounded-xl bg-[#181826] border border-pink-400/40 hover:border-pink-400 text-white font-semibold shadow transition-all hover:scale-105"
            >
              <svg className="w-5 h-5" viewBox="0 0 48 48">
                <g>
                  <path
                    fill="#FFC107"
                    d="M43.6 20.5H42V20.5H24V27.5H35.2C33.7 31.1 30.1 33.5 24 33.5C17.4 33.5 12 28.1 12 21.5C12 14.9 17.4 9.5 24 9.5C27.1 9.5 29.8 10.6 31.8 12.5L36.6 7.7C33.4 4.7 29.1 2.5 24 2.5C12.9 2.5 4 11.4 4 21.5C4 31.6 12.9 40.5 24 40.5C34.6 40.5 43.5 32.2 43.5 21.5C43.5 20.3 43.5 19.4 43.6 20.5Z"
                  />
                  <path
                    fill="#FF3D00"
                    d="M6.3 14.1L12.1 18.1C13.7 14.6 18.3 11.5 24 11.5C27.1 11.5 29.8 12.6 31.8 14.5L36.6 9.7C33.4 6.7 29.1 4.5 24 4.5C16.1 4.5 9.1 10.2 6.3 14.1Z"
                  />
                  <path
                    fill="#4CAF50"
                    d="M24 44.5C30.1 44.5 35.7 41.7 39.2 37.6L33.8 33.1C31.7 34.9 28.9 36.5 24 36.5C17.4 36.5 12 31.1 12 24.5C12 23.7 12.1 22.9 12.3 22.1L6.3 26.9C9.1 31.8 16.1 37.5 24 44.5Z"
                  />
                  <path
                    fill="#1976D2"
                    d="M43.6 20.5H42V20.5H24V27.5H35.2C34.5 29.2 33.2 30.7 31.8 32.1L36.6 36.9C39.5 34.2 41.5 30.5 43.6 20.5Z"
                  />
                </g>
              </svg>
              Continue with Google
            </button>

            <button
              type="button"
              onClick={handleGithubLogin}
              className="flex items-center justify-center gap-3 w-full py-2.5 rounded-xl bg-[#181826] border border-purple-400/40 hover:border-purple-400 text-white font-semibold shadow transition-all hover:scale-105"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.184 6.839 9.504.5.092.682-.217.682-.482 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.892 1.53 2.341 1.088 2.91.832.091-.647.35-1.088.636-1.34-2.221-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.987 1.029-2.687-.103-.254-.446-1.274.098-2.656 0 0 .84-.27 2.75 1.025A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.295 2.748-1.025 2.748-1.025.546 1.382.202 2.402.1 2.656.64.7 1.028 1.594 1.028 2.687 0 3.847-2.337 4.695-4.566 4.944.359.309.678.919.678 1.853 0 1.337-.012 2.419-.012 2.749 0 .267.18.577.688.479C19.138 20.203 22 16.447 22 12.021 22 6.484 17.523 2 12 2Z" />
              </svg>
              Continue with GitHub
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
