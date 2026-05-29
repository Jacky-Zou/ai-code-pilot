"use client";

import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Code2,
  Database,
  FolderSearch,
  Loader2,
  Play,
  Send
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import {
  ApiClientError,
  type ChatResponse,
  type ProjectIndexResponse,
  indexProject,
  sendChat
} from "@/lib/api";
import { ProviderSelector, type ProviderSelection } from "@/components/ProviderSelector";
import { CodeReference } from "@/components/CodeReference";
import { ToolCallTimeline } from "@/components/ToolCallTimeline";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
};

const demoResponse: ChatResponse = {
  answer:
    "The FastAPI backend is wired in backend/app/main.py. Chat and project retrieval routes are split into routes_chat.py and routes_project.py.",
  provider: "openai",
  model: "gpt-5.2",
  tool_calls: [
    {
      name: "search_text",
      arguments: { keyword: "APIRouter" },
      result: { matches: 2 },
      error: null
    },
    {
      name: "retrieve_code",
      arguments: { query: "FastAPI router" },
      result: { chunks: 2 },
      error: null
    }
  ],
  references: [
    {
      file_path: "backend/app/main.py",
      line_number: 28,
      snippet: "application.include_router(chat_router)",
      score: null
    },
    {
      file_path: "backend/app/api/routes_chat.py",
      line_number: 6,
      snippet: "router = APIRouter(prefix=\"/api\", tags=[\"chat\"])",
      score: null
    }
  ]
};

const DEFAULT_PROJECT_PATH = process.env.NEXT_PUBLIC_DEFAULT_PROJECT_PATH ?? "/app/app";

const initialMessages: ChatMessage[] = [
  {
    id: "demo-user",
    role: "user",
    content: "Where is the FastAPI router implemented?"
  },
  {
    id: "demo-assistant",
    role: "assistant",
    content: demoResponse.answer,
    response: demoResponse
  }
];

function formatApiError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.body?.detail ? String(error.body.detail) : error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Chat request failed.";
}

export function ChatWorkspace() {
  const [selection, setSelection] = useState<ProviderSelection>({
    provider: "openai",
    model: "gpt-5.2"
  });
  const [projectPath, setProjectPath] = useState(DEFAULT_PROJECT_PATH);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isSending, setIsSending] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStats, setIndexStats] = useState<ProjectIndexResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);

  // The right rail should always reflect the newest Agent response, not a stale demo result.
  // Walking from the end keeps this independent from whether the user sends one or many messages.
  const latestResponse = useMemo(
    () => [...messages].reverse().find((item) => item.response)?.response ?? null,
    [messages]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmedMessage
    };

    // Optimistically append the user message before calling the API so the chat feels immediate.
    // The assistant message is appended only after the backend returns a typed ChatResponse.
    setMessages((current) => [...current, userMessage]);
    setMessage("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendChat({
        message: trimmedMessage,
        project_path: projectPath.trim() || null,
        provider: selection.provider,
        model: selection.model
      });
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.answer,
          response
        }
      ]);
    } catch (requestError) {
      setError(formatApiError(requestError));
    } finally {
      setIsSending(false);
    }
  }

  async function handleIndexProject() {
    const trimmedProjectPath = projectPath.trim();
    if (!trimmedProjectPath || isIndexing) {
      return;
    }

    // Project indexing is a separate backend workflow from chat. Keeping its status separate
    // lets users index a repository, see chunk/file counts, and continue chatting afterward.
    setIsIndexing(true);
    setIndexError(null);
    setIndexStats(null);

    try {
      const stats = await indexProject({ project_path: trimmedProjectPath });
      setIndexStats(stats);
    } catch (requestError) {
      setIndexError(formatApiError(requestError));
    } finally {
      setIsIndexing(false);
    }
  }

  function loadDemo() {
    setMessages(initialMessages);
    setError(null);
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-panel">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-white">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">AICodePilot</h1>
              <p className="text-sm text-muted">Codebase Agent workspace</p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm text-muted">
            <CheckCircle2 className="h-4 w-4 text-accent" aria-hidden="true" />
            Backend API ready
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[300px_minmax(0,1fr)_340px]">
        <aside className="space-y-4">
          <ProviderSelector onChange={setSelection} value={selection} />

          <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <FolderSearch className="h-4 w-4 text-accent" aria-hidden="true" />
              Project
            </div>
            <input
              className="mb-3 h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
              onChange={(event) => setProjectPath(event.target.value)}
              value={projectPath}
              aria-label="Project path"
            />
            <button
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-[#8ec5bd]"
              disabled={isIndexing || !projectPath.trim()}
              onClick={handleIndexProject}
              type="button"
            >
              {isIndexing ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Database className="h-4 w-4" aria-hidden="true" />
              )}
              {isIndexing ? "Indexing" : "Index Project"}
            </button>
            {indexStats ? (
              <div className="mt-3 rounded-md border border-[#b7dfd8] bg-[#effaf8] p-3 text-sm">
                <div className="flex items-center gap-2 font-medium text-accent">
                  <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  Index ready
                </div>
                <p className="mt-2 text-muted">
                  {indexStats.indexed_files} files, {indexStats.chunks} chunks
                </p>
              </div>
            ) : null}
            {indexError ? (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-[#f4c7c7] bg-[#fff4f4] p-3 text-sm text-[#9f1239]">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{indexError}</span>
              </div>
            ) : null}
          </section>
        </aside>

        <section className="flex min-h-[620px] flex-col rounded-lg border border-border bg-panel shadow-soft">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div className="flex items-center gap-2 font-semibold">
              <Code2 className="h-5 w-5 text-primary" aria-hidden="true" />
              Agent Chat
            </div>
            <button
              className="flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm text-muted"
              onClick={loadDemo}
              type="button"
            >
              <Play className="h-4 w-4" aria-hidden="true" />
              Demo
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-auto p-5">
            {messages.map((item) => (
              <div
                className={
                  item.role === "user"
                    ? "max-w-[78%] rounded-lg border border-border bg-background p-4"
                    : "ml-auto max-w-[82%] rounded-lg bg-[#edf4ff] p-4"
                }
                key={item.id}
              >
                <p className="whitespace-pre-wrap text-sm leading-6">{item.content}</p>
                {item.response ? (
                  <p className="mt-3 text-xs text-muted">
                    {item.response.provider} / {item.response.model}
                  </p>
                ) : null}
              </div>
            ))}
            {isSending ? (
              <div className="ml-auto flex max-w-[82%] items-center gap-2 rounded-lg bg-[#edf4ff] p-4 text-sm text-muted">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Thinking
              </div>
            ) : null}
            {error ? (
              <div className="flex items-start gap-2 rounded-lg border border-[#f4c7c7] bg-[#fff4f4] p-4 text-sm text-[#9f1239]">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{error}</span>
              </div>
            ) : null}
          </div>

          <form className="border-t border-border p-4" onSubmit={handleSubmit}>
            <div className="flex gap-3">
              <input
                className="h-11 flex-1 rounded-md border border-border bg-white px-3 text-sm"
                disabled={isSending}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Ask about this codebase..."
                value={message}
                aria-label="Agent message"
              />
              <button
                className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-white disabled:cursor-not-allowed disabled:bg-[#9bb7f4]"
                disabled={isSending || !message.trim()}
                type="submit"
              >
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="h-4 w-4" aria-hidden="true" />
                )}
                <span className="sr-only">Send</span>
              </button>
            </div>
          </form>
        </section>

        <aside className="space-y-4">
          <ToolCallTimeline toolCalls={latestResponse?.tool_calls ?? []} />
          <CodeReference references={latestResponse?.references ?? []} />
        </aside>
      </section>
    </main>
  );
}
