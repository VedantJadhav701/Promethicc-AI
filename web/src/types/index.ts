/** Risk classification for experts. */
export type RiskTier = "standard" | "high_stakes";

/** Mode of operation — offline (free) or online (paid). */
export type ExpertMode = "offline" | "online";

/** Canonical expert identifiers. */
export type ExpertId = "code" | "eng" | "agri" | "med" | "law";

/** Error codes returned by the backend. */
export type ErrorCode =
  | "DISCLAIMER_REQUIRED"
  | "JURISDICTION_REQUIRED"
  | "UPGRADE_REQUIRED"
  | "RATE_LIMITED"
  | "EMERGENCY_DETECTED"
  | "UNAUTHORIZED";

/** Expert definition as returned from /v1/experts. */
export interface Expert {
  id: ExpertId;
  name: string;
  label: string;
  description: string;
  risk_tier: RiskTier;
  icon: string;
  color: string;
}

/** Outgoing chat request body. */
export interface ChatRequest {
  expert: ExpertId;
  mode: ExpertMode;
  message: string;
  jurisdiction?: string;
}

/** Source citation attached to an AI response. */
export interface Source {
  title: string;
  url?: string;
  snippet?: string;
}

/** Backend chat response. */
export interface ChatResponse {
  expert: ExpertId;
  mode: ExpertMode;
  reply: string;
  sources?: Source[];
  usage?: UsageData;
}

/** Structured error from the backend. */
export interface ErrorResponse {
  detail: string;
  code: ErrorCode;
}

/** Daily usage snapshot. */
export interface UsageData {
  used: number;
  cap: number;
  tier: "free" | "pro";
  resets_at: string;
}

/** Single chat message rendered in the UI. */
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

/** Disclaimer acceptance record. */
export interface DisclaimerAcceptance {
  user_id: string;
  expert: ExpertId;
  accepted_at: string;
}
