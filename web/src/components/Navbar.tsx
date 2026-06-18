"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

/**
 * Fixed top navigation bar with glassmorphism styling.
 *
 * Shows sign-in CTA or user avatar + sign-out depending on auth state.
 */
export default function Navbar() {
  const { user, signInWithGoogle, signOut, loading } = useAuth();

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
                  onClick={signInWithGoogle}
                  className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-1.5 text-sm font-medium text-white shadow-lg shadow-blue-500/20 transition-all hover:shadow-blue-500/40"
                >
                  Sign in
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
