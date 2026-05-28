import {
  Bot,
  Braces,
  CheckCircle2,
  Code2,
  Database,
  FolderSearch,
  GitBranch,
  Play,
  Search,
  Send,
  Settings2
} from "lucide-react";

const references = [
  {
    file: "backend/app/main.py",
    line: "28",
    text: "FastAPI app wiring and health endpoint"
  },
  {
    file: "backend/app/agent/executor.py",
    line: "42",
    text: "Agent action execution loop"
  }
];

const toolCalls = ["search_text", "retrieve_code", "read_file"];

export default function Home() {
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
          <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Settings2 className="h-4 w-4 text-primary" aria-hidden="true" />
              Model
            </div>
            <label className="mb-3 block text-xs font-medium uppercase text-muted">Provider</label>
            <select className="mb-4 h-10 w-full rounded-md border border-border bg-white px-3 text-sm">
              <option>OpenAI</option>
              <option>DeepSeek</option>
            </select>
            <label className="mb-3 block text-xs font-medium uppercase text-muted">Model</label>
            <select className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm">
              <option>gpt-5.2</option>
              <option>deepseek-v4-pro</option>
            </select>
          </section>

          <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <FolderSearch className="h-4 w-4 text-accent" aria-hidden="true" />
              Project
            </div>
            <input
              className="mb-3 h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
              defaultValue="D:/code/my_project"
              aria-label="Project path"
            />
            <button className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-white">
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
            <button className="flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm text-muted">
              <Play className="h-4 w-4" aria-hidden="true" />
              Demo
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-auto p-5">
            <div className="max-w-[78%] rounded-lg border border-border bg-background p-4">
              <p className="text-sm font-medium">Where is the FastAPI router implemented?</p>
            </div>
            <div className="ml-auto max-w-[82%] rounded-lg bg-[#edf4ff] p-4">
              <p className="text-sm leading-6">
                The FastAPI backend is wired in <strong>backend/app/main.py</strong>. Chat and
                project retrieval routes are split into <strong>routes_chat.py</strong> and{" "}
                <strong>routes_project.py</strong>.
              </p>
            </div>
          </div>

          <form className="border-t border-border p-4">
            <div className="flex gap-3">
              <input
                className="h-11 flex-1 rounded-md border border-border bg-white px-3 text-sm"
                placeholder="Ask about this codebase..."
                aria-label="Agent message"
              />
              <button className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-white">
                <Send className="h-4 w-4" aria-hidden="true" />
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
              {toolCalls.map((toolCall) => (
                <div
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
                  key={toolCall}
                >
                  <span>{toolCall}</span>
                  <CheckCircle2 className="h-4 w-4 text-accent" aria-hidden="true" />
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Search className="h-4 w-4 text-accent" aria-hidden="true" />
              Code References
            </div>
            <div className="space-y-3">
              {references.map((reference) => (
                <div className="rounded-md border border-border p-3" key={reference.file}>
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                    <Braces className="h-4 w-4 text-warning" aria-hidden="true" />
                    {reference.file}:{reference.line}
                  </div>
                  <p className="text-sm text-muted">{reference.text}</p>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}
