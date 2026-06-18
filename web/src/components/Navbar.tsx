"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

/**
 * Fixed top navigation bar with glassmorphism styling.
 *
 * Shows sign-in CTA or user avatar + sign-out depending on auth state.
 */
export default function Navbar() {
  const { user, signInWithEmail, signUpWithEmail, signOut, loading } = useAuth();
  const router = useRouter();

  // Auth Modal state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authTab, setAuthTab] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);

    const action = authTab === "signin" ? signInWithEmail : signUpWithEmail;
    const { error } = await action(email, password);

    setAuthLoading(false);

    if (error) {
      setAuthError(error.message || "Authentication failed.");
    } else {
      setShowAuthModal(false);
      setEmail("");
      setPassword("");
      router.push("/dashboard");
    }
  };

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/5 bg-[#0a0a1a]/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* ── Logo ──────────────────────────────────────── */}
        <Link href="/" className="group flex items-center gap-2">
          <span className="text-2xl" aria-hidden>
            🔥
          </span>
          <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-amber-400 bg-clip-text text-xl font-bold tracking-tight text-transparent transition-all group-hover:tracking-wide">
            Promethicc AI
          </span>
        </Link>

        {/* ── Links ─────────────────────────────────────── */}
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="text-sm text-gray-400 transition-colors hover:text-white"
          >
            Home
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-gray-400 transition-colors hover:text-white"
          >
            Dashboard
          </Link>

          {/* ── Auth ─────────────────────────────────────── */}
          {!loading && (
            <>
              {user ? (
                <div className="flex items-center gap-3">
                  {/* Avatar */}
                  <div className="relative h-8 w-8 overflow-hidden rounded-full ring-2 ring-blue-500/40">
                    {user.user_metadata?.avatar_url ? (
                      <img
                        src={user.user_metadata.avatar_url as string}
                        alt="avatar"
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-blue-600 text-xs font-bold text-white">
                        {(user.email?.[0] ?? "U").toUpperCase()}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={signOut}
                    className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-gray-400 transition-all hover:border-red-500/40 hover:text-red-400"
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-1.5 text-sm font-medium text-white shadow-lg shadow-blue-500/20 transition-all hover:shadow-blue-500/40"
                >
                  Sign in
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Auth Modal ────────────────────────────────────── */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="glass w-full max-w-md overflow-hidden rounded-3xl border border-white/10 bg-[#0f0f23]/95 shadow-2xl animate-scale-up">
            
            {/* Header Tabs */}
            <div className="flex border-b border-white/5 bg-black/20">
              <button
                type="button"
                onClick={() => {
                  setAuthTab("signin");
                  setAuthError(null);
                }}
                className={`w-1/2 py-4.5 text-center text-sm font-semibold transition-all ${
                  authTab === "signin"
                    ? "border-b-2 border-blue-500 text-white bg-white/5"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setAuthTab("signup");
                  setAuthError(null);
                }}
                className={`w-1/2 py-4.5 text-center text-sm font-semibold transition-all ${
                  authTab === "signup"
                    ? "border-b-2 border-blue-500 text-white bg-white/5"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleAuthSubmit} className="p-8 text-left">
              <h3 className="text-xl font-bold text-white mb-6">
                {authTab === "signin" ? "Welcome back" : "Create your account"}
              </h3>

              {authError && (
                <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-xs leading-relaxed text-red-400">
                  {authError}
                </div>
              )}

              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mt-8 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAuthModal(false);
                    setAuthError(null);
                  }}
                  className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-gray-300 hover:bg-white/5 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={authLoading}
                  className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-blue-500/25 hover:bg-blue-500 disabled:opacity-50"
                >
                  {authLoading && (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  )}
                  {authTab === "signin" ? "Sign In" : "Sign Up"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </nav>
  );
}
