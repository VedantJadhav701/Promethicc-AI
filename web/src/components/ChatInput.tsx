"use client";

import {
  type FormEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { ExpertId, ExpertMode } from "@/types";

/** Common jurisdictions for the Law expert. */
const JURISDICTIONS = [
  "United States",
  "United Kingdom",
  "European Union",
  "India",
  "Canada",
  "Australia",
  "Nigeria",
  "South Africa",
  "Other",
] as const;

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  expert: ExpertId;
  mode: ExpertMode;
  onModeChange: (mode: ExpertMode) => void;
  jurisdiction?: string;
  onJurisdictionChange?: (j: string) => void;
  tier: "free" | "pro";
}

/**
 * Chat input area with auto-resizing textarea, mode toggle, and
 * jurisdiction selector (visible only for the Law expert).
 */
export default function ChatInput({
  onSend,
  isLoading,
  expert,
  mode,
  onModeChange,
  jurisdiction,
  onJurisdictionChange,
  tier,
}: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /* ── Auto-resize ─────────────────────────────────────────── */
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [text]);

  /* ── Submit ──────────────────────────────────────────────── */
  const handleSubmit = useCallback(
    (e?: FormEvent) => {
      e?.preventDefault();
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;
      onSend(trimmed);
      setText("");
    },
    [text, isLoading, onSend]
  );

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isOnlineDisabled = tier === "free";

  return (
    <div className="border-t border-white/5 bg-[#0a0a1a]/80 px-4 py-3 backdrop-blur-xl">
      {/* ── Top controls ───────────────────────────────────── */}
      <div className="mb-2 flex flex-wrap items-center gap-3">
        {/* Mode toggle */}
        <div className="flex items-center rounded-lg border border-white/10 p-0.5">
          <button
            onClick={() => onModeChange("offline")}
            className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
              mode === "offline"
                ? "bg-green-600/20 text-green-400 shadow-sm shadow-green-500/10"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            ⚡ Offline
          </button>
          <button
            onClick={() => !isOnlineDisabled && onModeChange("online")}
            disabled={isOnlineDisabled}
            className={`relative rounded-md px-3 py-1 text-xs font-medium transition-all ${
              mode === "online"
                ? "bg-blue-600/20 text-blue-400 shadow-sm shadow-blue-500/10"
                : isOnlineDisabled
                  ? "cursor-not-allowed text-gray-600"
                  : "text-gray-500 hover:text-gray-300"
            }`}
          >
            🌐 Online
            {isOnlineDisabled && (
              <span className="ml-1.5 rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] font-bold uppercase text-amber-400">
                Upgrade
              </span>
            )}
          </button>
        </div>

        {/* Jurisdiction selector (Law only) */}
        {expert === "law" && (
          <select
            value={jurisdiction ?? ""}
            onChange={(e) => onJurisdictionChange?.(e.target.value)}
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-300 outline-none transition-colors focus:border-purple-500/50"
          >
            <option value="" disabled>
              Select jurisdiction…
            </option>
            {JURISDICTIONS.map((j) => (
              <option key={j} value={j} className="bg-gray-900">
                {j}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* ── Input row ──────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your expert…"
          rows={1}
          disabled={isLoading}
          className="flex-1 resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none transition-all focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={isLoading || !text.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/20 transition-all hover:shadow-blue-500/40 disabled:opacity-40 disabled:shadow-none"
        >
          {isLoading ? (
            <svg
              className="h-4 w-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="3"
                className="opacity-25"
              />
              <path
                d="M4 12a8 8 0 018-8"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-4 w-4"
            >
              <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
            </svg>
          )}
        </button>
      </form>
    </div>
  );
}
