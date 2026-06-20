"use client";

import { useCallback, useState } from "react";
import { chat as apiChat, ApiError } from "@/lib/api";
import type { ExpertId, ExpertMode, Message } from "@/types";

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  errorCode: string | null;
  sendMessage: (text: string) => Promise<void>;
  clearError: () => void;
  clearMessages: () => void;
}

/**
 * Manages chat state for a single expert session.
 *
 * Args:
 *   expert:       Which expert to talk to.
 *   mode:         offline or online.
 *   jurisdiction: Required for Law expert.
 *
 * Returns:
 *   Object with messages, loading/error state, and send/clear helpers.
 */
export function useChat(
  expert: ExpertId,
  mode: ExpertMode,
  jurisdiction?: string
): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
    setErrorCode(null);
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setError(null);
      setErrorCode(null);

      try {
        const response = await apiChat(expert, mode, text, jurisdiction);

        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.response,
          sources: response.sources?.map((url) => {
            let title = url;
            try {
              const parsed = new URL(url);
              title = parsed.hostname.replace("www.", "");
            } catch {
              // Ignore
            }
            return { title, url };
          }) || [],
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
          setErrorCode(err.code);
        } else {
          setError("An unexpected error occurred. Please try again.");
          setErrorCode("UNKNOWN");
        }
      } finally {
        setIsLoading(false);
      }
    },
    [expert, mode, jurisdiction]
  );

  return {
    messages,
    isLoading,
    error,
    errorCode,
    sendMessage,
    clearError,
    clearMessages,
  };
}
