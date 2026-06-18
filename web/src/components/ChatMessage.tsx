"use client";

import ReactMarkdown from "react-markdown";
import type { Message } from "@/types";

interface ChatMessageProps {
  message: Message;
}

/**
 * Single chat bubble — right-aligned for user, left-aligned for assistant.
 *
 * AI messages render Markdown and display source citations underneath.
 */
export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex animate-slide-up ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`relative max-w-[80%] rounded-2xl px-4 py-3 sm:max-w-[70%] ${
          isUser
            ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white"
            : "glass border border-white/[0.06] text-gray-200"
        }`}
      >
        {/* Message body */}
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none prose-p:leading-relaxed prose-code:rounded prose-code:bg-white/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-blue-300 prose-pre:bg-black/40 prose-pre:backdrop-blur">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {/* Source citations */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 border-t border-white/10 pt-2">
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              Sources
            </p>
            <ul className="space-y-1">
              {message.sources.map((src, i) => (
                <li key={i} className="text-xs text-gray-400">
                  {src.url ? (
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 underline decoration-blue-400/30 transition-colors hover:text-blue-300"
                    >
                      {src.title}
                    </a>
                  ) : (
                    <span>{src.title}</span>
                  )}
                  {src.snippet && (
                    <span className="ml-1 text-gray-500">— {src.snippet}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Timestamp */}
        <p
          className={`mt-1.5 text-[10px] ${
            isUser ? "text-blue-200/60" : "text-gray-600"
          }`}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

/**
 * Animated typing indicator — three bouncing dots.
 */
export function TypingIndicator() {
  return (
    <div className="flex justify-start animate-slide-up">
      <div className="glass flex items-center gap-1.5 rounded-2xl border border-white/[0.06] px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-blue-400 [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-blue-400 [animation-delay:150ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-blue-400 [animation-delay:300ms]" />
      </div>
    </div>
  );
}
