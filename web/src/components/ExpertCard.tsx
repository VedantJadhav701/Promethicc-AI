"use client";

import { useRouter } from "next/navigation";
import type { ExpertId, RiskTier } from "@/types";

/** Visual metadata for each expert, keyed by id. */
export const EXPERT_META: Record<
  ExpertId,
  { icon: string; color: string; gradient: string; label: string; description: string }
> = {
  code: {
    icon: "💻",
    color: "#3b82f6",
    gradient: "from-blue-600/20 to-blue-400/5",
    label: "Code",
    description: "Write, debug, and review code across any language or framework.",
  },
  eng: {
    icon: "⚙️",
    color: "#f97316",
    gradient: "from-orange-600/20 to-orange-400/5",
    label: "Engineering",
    description: "Mechanical, civil, electrical — solve engineering problems end to end.",
  },
  agri: {
    icon: "🌾",
    color: "#22c55e",
    gradient: "from-green-600/20 to-green-400/5",
    label: "Agriculture",
    description: "Crop science, soil health, livestock, and sustainable farming advice.",
  },
  med: {
    icon: "🩺",
    color: "#ef4444",
    gradient: "from-red-600/20 to-red-400/5",
    label: "Medicine",
    description: "General health information — never a substitute for a licensed physician.",
  },
  law: {
    icon: "⚖️",
    color: "#8b5cf6",
    gradient: "from-purple-600/20 to-purple-400/5",
    label: "Law",
    description: "Legal information by jurisdiction — not a substitute for a licensed attorney.",
  },
};

interface ExpertCardProps {
  id: ExpertId;
  riskTier: RiskTier;
  onClick?: (id: ExpertId) => void;
  selected?: boolean;
  compact?: boolean;
}

/**
 * Glassmorphism expert card with hover glow, risk badge, and navigation.
 *
 * Args:
 *   id:       Expert identifier.
 *   riskTier: standard or high_stakes — shows badge for the latter.
 *   onClick:  Optional click handler, defaults to router push.
 *   selected: Highlights the card when true.
 *   compact:  Renders a smaller variant for sidebar/pickers.
 */
export default function ExpertCard({
  id,
  riskTier,
  onClick,
  selected = false,
  compact = false,
}: ExpertCardProps) {
  const router = useRouter();
  const meta = EXPERT_META[id];

  const handleClick = () => {
    if (onClick) {
      onClick(id);
    } else {
      router.push(`/dashboard?expert=${id}`);
    }
  };

  if (compact) {
    return (
      <button
        onClick={handleClick}
        className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all duration-200 ${
          selected
            ? "bg-white/10 shadow-lg"
            : "hover:bg-white/5"
        }`}
        style={selected ? { boxShadow: `0 0 20px ${meta.color}20` } : undefined}
      >
        <span className="text-xl">{meta.icon}</span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-white">{meta.label}</p>
          {riskTier === "high_stakes" && (
            <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">
              High-stakes
            </span>
          )}
        </div>
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      className={`glass group relative flex flex-col items-start gap-4 overflow-hidden rounded-2xl border border-white/[0.06] p-6 text-left transition-all duration-300 hover:scale-[1.03] hover:border-white/[0.12] ${
        selected ? "ring-2" : ""
      }`}
      style={{
        ...(selected ? { ringColor: meta.color } : {}),
        boxShadow: `0 0 0 0 ${meta.color}00`,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget.style.boxShadow = `0 8px 40px ${meta.color}25`);
      }}
      onMouseLeave={(e) => {
        (e.currentTarget.style.boxShadow = `0 0 0 0 ${meta.color}00`);
      }}
    >
      {/* Gradient bg */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${meta.gradient} opacity-0 transition-opacity duration-300 group-hover:opacity-100`}
      />

      {/* Content */}
      <div className="relative z-10 flex w-full items-center justify-between">
        <span className="text-4xl transition-transform duration-300 group-hover:scale-110">
          {meta.icon}
        </span>
        {riskTier === "high_stakes" && (
          <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-400">
            High-stakes
          </span>
        )}
      </div>

      <div className="relative z-10">
        <h3 className="text-lg font-semibold text-white">{meta.label}</h3>
        <p className="mt-1 text-sm leading-relaxed text-gray-400">
          {meta.description}
        </p>
      </div>

      {/* Bottom accent line */}
      <div
        className="absolute bottom-0 left-0 h-[2px] w-0 transition-all duration-500 group-hover:w-full"
        style={{ backgroundColor: meta.color }}
      />
    </button>
  );
}
