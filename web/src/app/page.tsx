"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import ExpertCard from "@/components/ExpertCard";
import { useAuth } from "@/context/AuthContext";
import type { ExpertId } from "@/types";

/** Static expert list — mirrors the backend experts.yaml. */
const EXPERTS: { id: ExpertId; riskTier: "standard" | "high_stakes" }[] = [
  { id: "code", riskTier: "standard" },
  { id: "eng", riskTier: "standard" },
  { id: "agri", riskTier: "standard" },
  { id: "med", riskTier: "high_stakes" },
  { id: "law", riskTier: "high_stakes" },
];

const FEATURES = [
  {
    icon: "⚡",
    title: "Offline Mode — Free Forever",
    description:
      "Runs entirely on our servers at zero cost. No API keys, no credit card, no catch.",
    color: "text-green-400",
  },
  {
    icon: "🌐",
    title: "Online Mode — Supercharged",
    description:
      "Web search, RAG, and premium LLMs for when you need the best possible answers.",
    color: "text-blue-400",
  },
  {
    icon: "🛡️",
    title: "Safety-First Design",
    description:
      "High-stakes experts require disclaimers. Emergency queries are short-circuited to safe responses.",
    color: "text-amber-400",
  },
];

/**
 * Landing page — hero, expert cards, features, email/password auth CTA.
 */
export default function LandingPage() {
  const { signInWithEmail, signUpWithEmail, user } = useAuth();
  const router = useRouter();

  // Auth Modal state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authTab, setAuthTab] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const handleLaunchClick = () => {
    if (user) {
      router.push("/dashboard");
    } else {
      setShowAuthModal(true);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);

    try {
      const action = authTab === "signin" ? signInWithEmail : signUpWithEmail;
      const { error } = await action(email, password);

      if (error) {
        setAuthError(error.message || "Authentication failed. Please check your credentials.");
      } else {
        setShowAuthModal(false);
        setEmail("");
        setPassword("");
        router.push("/dashboard");
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setAuthError(
        errMsg || "Failed to reach Auth server. Please verify your NEXT_PUBLIC_SUPABASE_URL config."
      );
    } finally {
      setAuthLoading(false);
    }
  };

  return (
    <div className="mesh-gradient min-h-screen">
      <Navbar />

      {/* ── Hero ──────────────────────────────────────────── */}
      <section className="relative flex min-h-[90vh] flex-col items-center justify-center px-4 pt-20 text-center">
        {/* Glow orbs */}
        <div className="pointer-events-none absolute left-1/4 top-1/4 h-72 w-72 rounded-full bg-blue-600/10 blur-[120px] animate-pulse-glow" />
        <div className="pointer-events-none absolute right-1/4 bottom-1/4 h-72 w-72 rounded-full bg-purple-600/10 blur-[120px] animate-pulse-glow [animation-delay:1.5s]" />

        <div className="animate-slide-up">
          <span className="mb-4 inline-block rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-gray-400 backdrop-blur">
            🔥 5 Specialized AI Experts
          </span>
        </div>

        <h1 className="animate-slide-up text-5xl font-extrabold leading-tight tracking-tight sm:text-6xl lg:text-7xl [animation-delay:100ms]">
          Your{" "}
          <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-amber-400 bg-clip-text text-transparent animate-gradient-x">
            AI Expert
          </span>{" "}
          Panel
        </h1>

        <p className="mx-auto mt-6 max-w-2xl animate-slide-up text-lg text-gray-400 [animation-delay:200ms]">
          Code, Engineering, Agriculture, Medicine, and Law — five domain
          experts powered by AI, available instantly. Start free with offline
          mode, upgrade for premium intelligence.
        </p>

        <div className="mt-10 animate-slide-up [animation-delay:300ms]">
          <button
            onClick={handleLaunchClick}
            className="group relative inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-[length:200%_100%] px-8 py-4 text-lg font-bold text-white shadow-2xl shadow-blue-500/25 transition-all hover:shadow-blue-500/40 animate-gradient-x"
          >
            <span className="text-xl">🚀</span>
            {user ? "Go to Dashboard" : "Launch — Access Experts"}
            <span className="absolute inset-0 rounded-2xl bg-white/10 opacity-0 transition-opacity group-hover:opacity-100" />
          </button>
        </div>
      </section>

      {/* ── Expert Cards ─────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-bold text-white animate-slide-up">
            Meet Your Experts
          </h2>
          <p className="mt-3 text-gray-400 animate-slide-up [animation-delay:100ms]">
            Each expert is purpose-built with domain-specific knowledge and
            safety guardrails.
          </p>
        </div>

        <div className="stagger-children grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {EXPERTS.map((e) => (
            <ExpertCard key={e.id} id={e.id} riskTier={e.riskTier} />
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section className="mx-auto max-w-5xl px-4 pb-20">
        <div className="stagger-children grid gap-6 md:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="glass rounded-2xl border border-white/[0.06] p-6 transition-all duration-300 hover:border-white/[0.12]"
            >
              <span className="text-3xl">{f.icon}</span>
              <h3 className={`mt-3 text-lg font-semibold ${f.color}`}>
                {f.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-400">
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </section>

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
            <form onSubmit={handleAuthSubmit} className="p-8">
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

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10 text-center">
        <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
          <span className="text-lg">🔥</span>
          <span>
            Promethicc AI — Built by{" "}
            <span className="text-gray-400">Vedant</span>
          </span>
        </div>
        <div className="mt-4 flex items-center justify-center gap-6 text-xs text-gray-600">
          <a href="#" className="transition-colors hover:text-gray-400">
            GitHub
          </a>
          <a href="#" className="transition-colors hover:text-gray-400">
            Documentation
          </a>
          <a href="#" className="transition-colors hover:text-gray-400">
            Privacy
          </a>
        </div>
      </footer>
    </div>
  );
}
