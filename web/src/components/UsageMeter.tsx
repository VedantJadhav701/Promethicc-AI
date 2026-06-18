"use client";

import type { UsageData } from "@/types";

interface UsageMeterProps {
  usage: UsageData | null;
}

/**
 * Circular-style usage meter showing daily consumption vs cap.
 *
 * Displays tier badge and upgrade CTA for free users.
 */
export default function UsageMeter({ usage }: UsageMeterProps) {
  if (!usage) {
    return (
      <div className="glass animate-pulse rounded-xl border border-white/[0.06] p-4">
        <div className="h-4 w-24 rounded bg-white/10" />
        <div className="mt-3 h-2 w-full rounded-full bg-white/10" />
      </div>
    );
  }

  const pct = Math.min((usage.used / usage.cap) * 100, 100);
  const isFree = usage.tier === "free";

  /** Color shifts from green → amber → red as usage increases. */
  const barColor =
    pct < 50
      ? "from-green-500 to-emerald-400"
      : pct < 80
        ? "from-amber-500 to-yellow-400"
        : "from-red-500 to-rose-400";

  return (
    <div className="glass rounded-xl border border-white/[0.06] p-4">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
          Daily Usage
        </p>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
            isFree
              ? "bg-gray-500/20 text-gray-400"
              : "bg-blue-500/20 text-blue-400"
          }`}
        >
          {usage.tier}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Stats */}
      <div className="mt-2 flex items-center justify-between">
        <p className="text-xs text-gray-500">
          <span className="font-semibold text-white">{usage.used}</span> /{" "}
          {usage.cap} requests
        </p>
        <p className="text-[10px] text-gray-600">
          Resets{" "}
          {new Date(usage.resets_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>

      {/* Upgrade CTA */}
      {isFree && (
        <button className="mt-3 w-full rounded-lg border border-amber-500/30 bg-gradient-to-r from-amber-500/10 to-amber-600/10 py-2 text-xs font-semibold text-amber-400 transition-all hover:from-amber-500/20 hover:to-amber-600/20">
          ✨ Upgrade to Pro
        </button>
      )}
    </div>
  );
}
