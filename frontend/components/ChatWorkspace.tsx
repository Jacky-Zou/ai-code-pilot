"use client";

import {
  AlertCircle,
  Bot,
  Braces,
  CheckCircle2,
  Code2,
  Database,
  FolderSearch,
  GitBranch,
  Loader2,
  Play,
  Search,
  Send
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { ApiClientError, type ChatResponse, sendChat } from "@/lib/api";
import { ProviderSelector, type ProviderSelection } from "@/components/ProviderSelector";

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
  const [projectPath, setProjectPath] = useState("D:/code/my_project");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-white"
              type="button"
            >
              <Database className="h-4 w-4" aria-hidden="true" />
              Index Project
            </button>
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
          <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <GitBranch className="h-4 w-4 text-primary" aria-hidden="true" />
              Tool Calls
            </div>
            <div className="space-y-2">
              {(latestResponse?.tool_calls ?? []).map((toolCall, index) => (
                <div
                  className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2 text-sm"
                  key={`${toolCall.name}-${index}`}
                >
                  <span className="min-w-0 truncate">{toolCall.name}</span>
                  <CheckCircle2
                    className={`h-4 w-4 shrink-0 ${toolCall.error ? "text-warning" : "text-accent"}`}
                    aria-hidden="true"
                  />
                </div>
              ))}
              {!latestResponse?.tool_calls.length ? (
                <p className="text-sm text-muted">No tool calls yet.</p>
              ) : null}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Search className="h-4 w-4 text-accent" aria-hidden="true" />
              Code References
            </div>
            <div className="space-y-3">
              {(latestResponse?.references ?? []).map((reference, index) => (
                <div className="rounded-md border border-border p-3" key={`${reference.file_path}-${index}`}>
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                    <Braces className="h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
                    <span className="min-w-0 truncate">
                      {reference.file_path}
                      {reference.line_number ? `:${reference.line_number}` : ""}
                    </span>
                  </div>
                  <p className="text-sm text-muted">{reference.snippet ?? "Referenced by Agent"}</p>
                </div>
              ))}
              {!latestResponse?.references.length ? (
                <p className="text-sm text-muted">No references yet.</p>
              ) : null}
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}
