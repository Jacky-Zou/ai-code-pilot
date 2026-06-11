"use client";

import { useCallback, useRef, useState } from "react";
import { type ChatResponse, type ToolResult, type CodeReference } from "@/lib/api";
import { consumeSse, type SseEvent } from "@/lib/sse";

export type StreamingToolCall = {
  tool: string;
  done: boolean;
  error?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  muted?: boolean;
  response?: ChatResponse;
};

type SendOptions = {
  message: string;
  projectPath?: string | null;
  provider?: string | null;
  model?: string | null;
  baseUrl?: string;
};

const API_BASE_URL =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

/**
 * Manages chat session state and SSE stream consumption.
 *
 * Connects to /api/chat/stream and updates messages incrementally as each
 * SSE event arrives. The conversationId is persisted across sends so the
 * backend can maintain multi-turn memory for the session.
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeToolCalls, setActiveToolCalls] = useState<StreamingToolCall[]>([]);
  const conversationIdRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(async (opts: SendOptions) => {
    const { message, projectPath, provider, model, baseUrl } = opts;

    // Abort any in-flight stream before starting a new one
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);
    setError(null);
    setActiveToolCalls([]);

    // Placeholder for streaming assistant message
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "" },
    ]);

    try {
      const url = `${(baseUrl ?? API_BASE_URL).replace(/\/+$/, "")}/api/chat/stream`;
      const body = {
        message,
        project_path: projectPath ?? null,
        provider: provider ?? null,
        model: model ?? null,
        conversation_id: conversationIdRef.current ?? undefined,
      };

      await consumeSse(
        url,
        body,
        (event: SseEvent) => {
          if (event.type === "tool_start") {
            setActiveToolCalls((prev) => [
              ...prev,
              { tool: event.data.tool as string, done: false },
            ]);
          } else if (event.type === "tool_end") {
            const toolName = event.data.tool as string;
            setActiveToolCalls((prev) =>
              prev.map((tc) =>
                tc.tool === toolName && !tc.done
                  ? { ...tc, done: true, error: (event.data.error as string | null) ?? null }
                  : tc
              )
            );
          } else if (event.type === "answer_delta") {
            const text = event.data.text as string;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + text } : m
              )
            );
          } else if (event.type === "done") {
            const data = event.data;

            // Persist conversation_id for follow-up messages
            if (data.conversation_id) {
              conversationIdRef.current = data.conversation_id as string;
            }

            const chatResponse: ChatResponse = {
              answer: data.answer as string,
              provider: data.provider as string,
              model: data.model as string,
              tool_calls: (data.tool_calls as ToolResult[]) ?? [],
              references: (data.references as CodeReference[]) ?? [],
              conversation_id: data.conversation_id as string,
            };

            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: data.answer as string, response: chatResponse }
                  : m
              )
            );
          } else if (event.type === "error") {
            setError((event.data.detail as string) ?? "Stream error");
          }
        },
        controller.signal
      );
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      const msg = err instanceof Error ? err.message : "Unknown streaming error";
      setError(msg);
      // Remove the empty placeholder on failure
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setIsSending(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setActiveToolCalls([]);
    conversationIdRef.current = null;
  }, []);

  return {
    messages,
    isSending,
    error,
    activeToolCalls,
    send,
    clearMessages,
    conversationId: conversationIdRef.current,
  };
}
