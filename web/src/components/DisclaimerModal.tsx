"use client";

import { useState } from "react";
import { acceptDisclaimer, ApiError } from "@/lib/api";
import type { ExpertId } from "@/types";

const DISCLAIMER_TEXT: Record<string, { title: string; body: string }> = {
  med: {
    title: "Medical Information Disclaimer",
    body: `The Medical expert provides GENERAL HEALTH INFORMATION ONLY.

• It is NOT a substitute for a licensed physician.
• It will NEVER provide specific medication dosing, instruct you to start/stop/change medications, or attempt a diagnosis.
• Always consult a qualified healthcare professional for decisions about your health.

By continuing, you acknowledge that you understand these limitations and will not rely on this tool for medical decisions.`,
  },
  law: {
    title: "Legal Information Disclaimer",
    body: `The Law expert provides GENERAL LEGAL INFORMATION ONLY.

• It is NOT a substitute for a licensed attorney.
• Legal advice is jurisdiction-specific — you must select your jurisdiction before asking questions.
• The information provided should not be relied upon for making legal decisions without consulting a qualified legal professional.

By continuing, you acknowledge that you understand these limitations and will not rely on this tool for legal decisions.`,
  },
};

interface DisclaimerModalProps {
  expert: ExpertId;
  onAccepted: () => void;
}

/**
 * Full-screen modal requiring explicit disclaimer acceptance for
 * high-stakes experts (Med, Law).
 *
 * Cannot be dismissed — the user must accept to proceed.
 * Calls POST /v1/disclaimers/{expert}/accept on confirmation.
 */
export default function DisclaimerModal({
  expert,
  onAccepted,
}: DisclaimerModalProps) {
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const content = DISCLAIMER_TEXT[expert];
  if (!content) return null;

  const handleAccept = async () => {
    setAccepting(true);
    setError(null);
    try {
      await acceptDisclaimer(expert);
      onAccepted();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to record acceptance. Please try again."
      );
    } finally {
      setAccepting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="glass mx-4 w-full max-w-lg rounded-2xl border border-white/10 p-6 shadow-2xl animate-slide-up sm:p-8">
        {/* Icon */}
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-500/10">
          <span className="text-3xl">⚠️</span>
        </div>

        {/* Title */}
        <h2 className="text-center text-xl font-bold text-white">
          {content.title}
        </h2>

        {/* Body */}
        <div className="my-6 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
          <p className="whitespace-pre-line text-sm leading-relaxed text-gray-300">
            {content.body}
          </p>
        </div>

        {/* Error */}
        {error && (
          <p className="mb-4 text-center text-sm text-red-400">{error}</p>
        )}

        {/* Accept button */}
        <button
          onClick={handleAccept}
          disabled={accepting}
          className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 px-6 py-3 font-semibold text-black shadow-lg shadow-amber-500/20 transition-all hover:shadow-amber-500/40 disabled:opacity-50"
        >
          {accepting ? "Recording acceptance…" : "I understand and accept"}
        </button>
      </div>
    </div>
  );
}
