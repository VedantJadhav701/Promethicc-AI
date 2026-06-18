"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import ExpertCard, { EXPERT_META } from "@/components/ExpertCard";
import ChatMessage, { TypingIndicator } from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import DisclaimerModal from "@/components/DisclaimerModal";
import UsageMeter from "@/components/UsageMeter";
import { useChat } from "@/hooks/useChat";
import { getUsage } from "@/lib/api";
import type { ExpertId, ExpertMode, UsageData } from "@/types";

const EXPERT_LIST: { id: ExpertId; riskTier: "standard" | "high_stakes" }[] = [
  { id: "code", riskTier: "standard" },
  { id: "eng", riskTier: "standard" },
  { id: "agri", riskTier: "standard" },
  { id: "med", riskTier: "high_stakes" },
  { id: "law", riskTier: "high_stakes" },
];

const HIGH_STAKES: ExpertId[] = ["med", "law"];

/**
 * Dashboard page — expert picker, chat UI, usage meter, and mode toggle.
 */
export default function DashboardPage() {
  const searchParams = useSearchParams();
  const initialExpert = (searchParams.get("expert") as ExpertId) || "code";

  const [selectedExpert, setSelectedExpert] = useState<ExpertId>(initialExpert);
  const [mode, setMode] = useState<ExpertMode>("offline");
  const [jurisdiction, setJurisdiction] = useState<string>("");
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [acceptedDisclaimers, setAcceptedDisclaimers] = useState<Set<ExpertId>>(
    new Set()
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, isLoading, error, errorCode, sendMessage, clearError, clearMessages } =
    useChat(selectedExpert, mode, jurisdiction || undefined);

  /* ── Fetch usage on mount ────────────────────────────────── */
  useEffect(() => {
    getUsage()
      .then(setUsage)
      .catch(() => {
        setUsage({ used: 0, cap: 20, tier: "free", resets_at: new Date().toISOString() });
      });
  }, []);

  /* ── Auto-scroll to bottom ───────────────────────────────── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  /* ── React to DISCLAIMER_REQUIRED ────────────────────────── */
  useEffect(() => {
    if (errorCode === "DISCLAIMER_REQUIRED") {
      setShowDisclaimer(true);
      clearError();
    }
  }, [errorCode, clearError]);

  /* ── Expert selection ────────────────────────────────────── */
  const selectExpert = useCallback(
    (id: ExpertId) => {
      setSelectedExpert(id);
      clearMessages();
      clearError();
      setSidebarOpen(false);

      if (HIGH_STAKES.includes(id) && !acceptedDisclaimers.has(id)) {
        setShowDisclaimer(true);
      }
    },
    [acceptedDisclaimers, clearMessages, clearError]
  );

  const handleDisclaimerAccepted = useCallback(() => {
    setAcceptedDisclaimers((prev) => new Set(prev).add(selectedExpert));
    setShowDisclaimer(false);
  }, [selectedExpert]);

  const handleSend = useCallback(
    (text: string) => {
      if (
        HIGH_STAKES.includes(selectedExpert) &&
        !acceptedDisclaimers.has(selectedExpert)
      ) {
        setShowDisclaimer(true);
        return;
      }
      sendMessage(text);
    },
    [selectedExpert, acceptedDisclaimers, sendMessage]
  );

  const meta = EXPERT_META[selectedExpert];

  return (
    <>
      {/* ── Disclaimer modal ────────────────────────────── */}
      {showDisclaimer && HIGH_STAKES.includes(selectedExpert) && (
        <DisclaimerModal
          expert={selectedExpert}
          onAccepted={handleDisclaimerAccepted}
        />
      )}

      <div className="flex h-[calc(100vh-4rem)]">
        {/* ── Mobile sidebar toggle ─────────────────────── */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="fixed bottom-4 left-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg shadow-blue-500/30 lg:hidden"
        >
          {sidebarOpen ? "✕" : "☰"}
        </button>

        {/* ── Sidebar ───────────────────────────────────── */}
        <aside
          className={`fixed inset-y-0 left-0 z-30 w-64 border-r border-white/5 bg-[#0a0a1a]/95 pt-20 backdrop-blur-xl transition-transform duration-300 lg:relative lg:z-auto lg:translate-x-0 lg:pt-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-full flex-col p-4">
            {/* Expert list */}
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-gray-600">
              Experts
            </p>
            <div className="space-y-1">
              {EXPERT_LIST.map((e) => (
                <ExpertCard
                  key={e.id}
                  id={e.id}
                  riskTier={e.riskTier}
                  onClick={selectExpert}
                  selected={selectedExpert === e.id}
                  compact
                />
              ))}
            </div>

            {/* Usage */}
            <div className="mt-auto pt-4">
              <UsageMeter usage={usage} />
            </div>
          </div>
        </aside>

        {/* ── Overlay for mobile sidebar ────────────────── */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ── Main chat area ────────────────────────────── */}
        <div className="flex flex-1 flex-col">
          {/* Chat header */}
          <div className="flex items-center gap-3 border-b border-white/5 bg-[#0a0a1a]/80 px-4 py-3 backdrop-blur-xl lg:px-6">
            <span className="text-2xl">{meta.icon}</span>
            <div>
              <h2 className="font-semibold text-white">{meta.label}</h2>
              <p className="text-xs text-gray-500">{meta.description}</p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  mode === "offline" ? "bg-green-500" : "bg-blue-500"
                }`}
              />
              <span className="text-xs text-gray-500">
                {mode === "offline" ? "Offline" : "Online"}
              </span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-6">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center animate-fade-in">
                <span className="mb-4 text-6xl animate-float">{meta.icon}</span>
                <h3 className="text-xl font-semibold text-white">
                  Chat with {meta.label}
                </h3>
                <p className="mt-2 max-w-sm text-sm text-gray-500">
                  Ask anything in this expert&apos;s domain. Your conversation
                  is private and audited for quality.
                </p>
                {selectedExpert === "law" && (
                  <p className="mt-3 rounded-lg border border-purple-500/20 bg-purple-500/5 px-4 py-2 text-xs text-purple-400">
                    ⚖️ Please select a jurisdiction before asking legal
                    questions.
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
                {isLoading && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}

            {/* Error toast */}
            {error && errorCode !== "DISCLAIMER_REQUIRED" && (
              <div className="mt-4 animate-slide-up rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-red-400">{error}</p>
                  <button
                    onClick={clearError}
                    className="text-xs text-red-500 hover:text-red-400"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            expert={selectedExpert}
            mode={mode}
            onModeChange={setMode}
            jurisdiction={jurisdiction}
            onJurisdictionChange={setJurisdiction}
            tier={usage?.tier ?? "free"}
          />
        </div>
      </div>
    </>
  );
}
