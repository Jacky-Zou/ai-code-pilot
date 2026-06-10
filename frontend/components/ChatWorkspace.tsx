"use client";

/* eslint-disable @next/next/no-img-element */

import {
  AlertCircle,
  Bot,
  Boxes,
  CheckCircle2,
  ChevronDown,
  Code2,
  Database,
  FileCode2,
  FolderOpen,
  KeyRound,
  Loader2,
  LogIn,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Send,
  Settings,
  Sun,
  User,
  UserPlus,
  X
} from "lucide-react";
import { ChangeEvent, FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import {
  ApiClientError,
  type ChatResponse,
  type ProjectIndexResponse,
  getHealth,
  indexProject,
  sendChat
} from "@/lib/api";
import { CodeReference } from "@/components/CodeReference";
import { ProviderSelector, type ProviderSelection } from "@/components/ProviderSelector";
import { ToolCallTimeline } from "@/components/ToolCallTimeline";

type Theme = "light" | "dark";
type AuthMode = "login" | "register" | "profile" | "forgot";
type ImportKind = "folder" | "file";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  muted?: boolean;
  response?: ChatResponse;
};

type AuthUser = {
  avatarUrl: string;
  name: string;
};

type WorkspaceNode = {
  children?: WorkspaceNode[];
  name: string;
  path: string;
  type: "file" | "folder";
};

type ProjectSummary = {
  architecture: string[];
  chunks: number;
  description: string;
  files: number;
  kind: ImportKind;
  languages: Array<{ label: string; percent: number; value: number }>;
  lineCount: number;
  name: string;
  path?: string;
  purpose: string;
  sizeBytes: number;
  structure: string[];
  techStack: string[];
};

const DEFAULT_PROJECT_PATH = process.env.NEXT_PUBLIC_DEFAULT_PROJECT_PATH ?? ".";
const DEFAULT_AVATAR =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%232563eb'/%3E%3Ccircle cx='32' cy='24' r='11' fill='white' opacity='.95'/%3E%3Cpath d='M14 54c3.6-11 12.2-16 18-16s14.4 5 18 16' fill='white' opacity='.95'/%3E%3C/svg%3E";

// Keep browser imports scoped to source-like text assets. The backend has its
// own file safety layer; this frontend whitelist prevents unsupported binary or
// office formats from entering the Workspace preview flow in the first place.
const SUPPORTED_EXTENSIONS = new Set([
  ".c",
  ".cpp",
  ".css",
  ".go",
  ".html",
  ".java",
  ".js",
  ".json",
  ".jsx",
  ".md",
  ".py",
  ".rs",
  ".scss",
  ".sh",
  ".ts",
  ".tsx",
  ".txt",
  ".yaml",
  ".yml"
]);
const FILE_ACCEPT = Array.from(SUPPORTED_EXTENSIONS).join(",");

const demoResponse: ChatResponse = {
  answer:
    "The FastAPI backend is wired in `backend/app/main.py`.\n\n| Area | File |\n| --- | --- |\n| App entry | `backend/app/main.py` |\n| Chat route | `backend/app/api/routes_chat.py` |\n\n```python\napplication.include_router(chat_router)\napplication.include_router(project_router)\n```",
  provider: "openai",
  model: "gpt-5.2",
  tool_calls: [
    { name: "search_text", arguments: { keyword: "APIRouter" }, result: { count: 2 }, error: null },
    {
      name: "retrieve_code",
      arguments: { query: "FastAPI router" },
      result: { matches: [{ file_path: "backend/app/main.py" }, { file_path: "backend/app/api/routes_chat.py" }] },
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

const QUICK_ACTIONS = [
  "Explain the Agent execution flow",
  "Find the FastAPI route definitions",
  "Review the tool registry design",
  "Generate unit tests for the executor",
  "Analyze a bug from an error log",
  "Suggest a refactor plan"
];

function formatApiError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (typeof error.body?.detail === "string") return error.body.detail;
    return error.body?.detail ? JSON.stringify(error.body.detail) : error.message;
  }
  if (error instanceof Error) return error.message;
  return "Request failed.";
}

function randomCaptcha(): string {
  return Math.random().toString(36).slice(2, 6).toUpperCase();
}

function fileExtension(fileName: string): string {
  const dotIndex = fileName.lastIndexOf(".");
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : "";
}

function isSupportedCodeFile(file: File): boolean {
  return SUPPORTED_EXTENSIONS.has(fileExtension(file.name));
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function inferLanguage(fileName: string): string {
  const extension = fileExtension(fileName);
  if (extension === ".py") return "Python";
  if ([".ts", ".tsx", ".js", ".jsx"].includes(extension)) return "TypeScript";
  if ([".css", ".scss", ".html"].includes(extension)) return "Web";
  if ([".c", ".cpp", ".java", ".go", ".rs"].includes(extension)) return "Compiled";
  if ([".json", ".yaml", ".yml"].includes(extension)) return "Config";
  if (extension === ".md") return "Markdown";
  return "Other";
}

function detectTechStack(fileNames: string[]): string[] {
  const normalized = fileNames.map((fileName) => fileName.replace(/\\/g, "/").toLowerCase());
  const names = new Set(normalized.map((fileName) => fileName.split("/").at(-1) ?? fileName));
  const stack: string[] = [];
  if (names.has("requirements.txt") || names.has("pyproject.toml")) stack.push("Python");
  if (names.has("package.json")) stack.push("Node.js");
  if (normalized.some((fileName) => fileName.endsWith(".tsx") || fileName.endsWith(".jsx"))) stack.push("React");
  if (normalized.some((fileName) => fileName.includes("next.config") || fileName.startsWith("app/"))) stack.push("Next.js");
  if (normalized.some((fileName) => fileName.includes("tailwind"))) stack.push("Tailwind CSS");
  if (names.has("docker-compose.yml") || names.has("dockerfile")) stack.push("Docker");
  if (normalized.some((fileName) => fileName.includes("/agent/") || fileName.startsWith("agent/"))) stack.push("LLM Agent");
  if (normalized.some((fileName) => fileName.includes("/rag/") || fileName.startsWith("rag/"))) stack.push("RAG");
  return Array.from(new Set(stack)).slice(0, 10);
}

function detectArchitecture(fileNames: string[]): string[] {
  const normalized = fileNames.map((fileName) => fileName.replace(/\\/g, "/").toLowerCase());
  const roots = new Set(normalized.map((fileName) => fileName.split("/")[0]));
  const architecture: string[] = [];
  if (roots.has("backend")) architecture.push("Backend service layer");
  if (roots.has("frontend")) architecture.push("Frontend workspace application");
  if (normalized.some((fileName) => fileName.includes("/agent/"))) architecture.push("Agent planner/executor core");
  if (normalized.some((fileName) => fileName.includes("/tools/"))) architecture.push("Tool calling layer");
  if (normalized.some((fileName) => fileName.includes("/rag/"))) architecture.push("RAG indexing and retrieval layer");
  if (roots.has("docs")) architecture.push("Documentation package");
  if (normalized.some((fileName) => fileName.includes("/tests/") || fileName.startsWith("tests/"))) architecture.push("Automated test suite");
  return architecture.slice(0, 8);
}

function buildWorkspaceTree(files: File[]): WorkspaceNode[] {
  type MutableNode = WorkspaceNode & { childMap?: Map<string, MutableNode> };
  const root = new Map<string, MutableNode>();

  // The browser exposes selected folders as a flat FileList. Rebuilding a small
  // tree here gives users a VS Code-like project preview without asking the
  // backend to inspect arbitrary local paths.
  for (const file of files) {
    const relativePath = file.webkitRelativePath || file.name;
    const parts = relativePath.split("/").filter(Boolean);
    let current = root;
    let path = "";

    parts.forEach((part, index) => {
      path = path ? `${path}/${part}` : part;
      const isFile = index === parts.length - 1;
      if (!current.has(part)) {
        current.set(part, {
          childMap: isFile ? undefined : new Map<string, MutableNode>(),
          name: part,
          path,
          type: isFile ? "file" : "folder"
        });
      }
      const node = current.get(part);
      if (!node || isFile) return;
      node.childMap ??= new Map<string, MutableNode>();
      current = node.childMap;
    });
  }

  function materialize(nodes: Iterable<MutableNode>): WorkspaceNode[] {
    return Array.from(nodes)
      .map((node) => ({
        name: node.name,
        path: node.path,
        type: node.type,
        children: node.childMap ? materialize(node.childMap.values()) : undefined
      }))
      .sort((left, right) => {
        if (left.type !== right.type) return left.type === "folder" ? -1 : 1;
        return left.name.localeCompare(right.name);
      });
  }

  return materialize(root.values());
}

async function buildImportSummary(
  kind: ImportKind,
  files: File[],
  stats: ProjectIndexResponse | null = null
): Promise<ProjectSummary> {
  const firstFile = files[0];
  const rootName =
    kind === "folder" && firstFile?.webkitRelativePath
      ? firstFile.webkitRelativePath.split("/")[0]
      : firstFile?.name || "Workspace";
  const languageCounts = new Map<string, number>();
  const structure = new Set<string>();
  const relativePaths = files.map((file) => file.webkitRelativePath || file.name);
  let lineCount = 0;
  let sizeBytes = 0;

  // The summary is intentionally computed in the browser for instant feedback:
  // project/file name, rough language mix, total bytes, and line counts. The
  // backend indexing response is merged later when a real RAG index is created.
  for (const file of files) {
    const relativePath = file.webkitRelativePath || file.name;
    const language = inferLanguage(relativePath);
    sizeBytes += file.size;
    languageCounts.set(language, (languageCounts.get(language) ?? 0) + 1);
    const parts = relativePath.split("/").filter(Boolean);
    if (parts.length > 1) structure.add(parts.slice(0, Math.min(parts.length, 3)).join("/"));

    // Browser imports are only used for local preview metadata. The backend
    // still needs a backend-visible path before it can perform real RAG indexing.
    if (file.size <= 1024 * 1024) {
      const text = await file.text().catch(() => "");
      lineCount += text ? text.split(/\r?\n/).length : 0;
    }
  }

  const total = Array.from(languageCounts.values()).reduce((sum, value) => sum + value, 0) || 1;
  const languages = Array.from(languageCounts.entries())
    .map(([label, value]) => ({ label, percent: Math.round((value / total) * 100), value }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 6);

  return {
    chunks: stats?.chunks ?? 0,
    description:
      kind === "folder"
        ? "Project or folder imported successfully. The overview below is generated from the selected source files."
        : "Code file imported successfully. The overview below is generated from the selected file.",
    files: files.length,
    kind,
    languages,
    lineCount,
    name: rootName,
    purpose:
      "This workspace can now be inspected by AICodePilot for codebase understanding, implementation lookup, debugging support, and documentation workflows.",
    sizeBytes,
    structure: structure.size > 0 ? Array.from(structure).slice(0, 14) : files.map((file) => file.name).slice(0, 14),
    techStack: detectTechStack(relativePaths),
    architecture: detectArchitecture(relativePaths)
  };
}

function MarkdownMessage({ content }: { content: string }) {
  return (
    <ReactMarkdown
      rehypePlugins={[rehypeHighlight]}
      remarkPlugins={[remarkGfm]}
      components={{
        table({ children }) {
          return (
            <div className="markdown-table-wrap">
              <table>{children}</table>
            </div>
          );
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function WorkspaceTree({ nodes }: { nodes: WorkspaceNode[] }) {
  if (nodes.length === 0) return null;

  return (
    <ul className="workspace-tree">
      {nodes.map((node) => (
        <li key={node.path}>
          <span className={`workspace-tree-row ${node.type}`}>
            {node.type === "folder" ? <FolderOpen className="h-3.5 w-3.5" /> : <FileCode2 className="h-3.5 w-3.5" />}
            <span>{node.name}</span>
          </span>
          {node.children?.length ? <WorkspaceTree nodes={node.children} /> : null}
        </li>
      ))}
    </ul>
  );
}

function ModelCenterIcon({ className = "h-4 w-4" }: { className?: string }) {
  return <Boxes className={className} aria-hidden="true" />;
}

export function ChatWorkspace() {
  const [selection, setSelection] = useState<ProviderSelection>({ provider: "deepseek", model: "deepseek-v4-pro" });
  const [theme, setTheme] = useState<Theme>("light");
  const [isLeftRailCollapsed, setIsLeftRailCollapsed] = useState(false);
  const [projectPath, setProjectPath] = useState(DEFAULT_PROJECT_PATH);
  const [workspaceTree, setWorkspaceTree] = useState<WorkspaceNode[]>([]);
  const [message, setMessage] = useState("");
  const [composerNudge, setComposerNudge] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStats, setIndexStats] = useState<ProjectIndexResponse | null>(null);
  const [projectSummary, setProjectSummary] = useState<ProjectSummary | null>(null);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);
  const [backendReady, setBackendReady] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const [captchaCode, setCaptchaCode] = useState(randomCaptcha);
  const [captchaInput, setCaptchaInput] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const folderInputRef = useRef<HTMLInputElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const latestResponse = useMemo(
    () => [...messages].reverse().find((item) => item.response)?.response ?? null,
    [messages]
  );

  useEffect(() => {
    const storedTheme = window.localStorage.getItem("aicodepilot-theme") as Theme | null;
    const storedUser = window.localStorage.getItem("aicodepilot-user");
    if (storedTheme === "light" || storedTheme === "dark") setTheme(storedTheme);
    if (storedUser) {
      try {
        setAuthUser(JSON.parse(storedUser) as AuthUser);
      } catch {
        window.localStorage.removeItem("aicodepilot-user");
      }
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("aicodepilot-theme", theme);
  }, [theme]);

  useEffect(() => {
    getHealth()
      .then(() => setBackendReady(true))
      .catch(() => setBackendReady(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isSending, error]);

  useEffect(() => {
    if (!composerNudge) return;
    const timeoutId = window.setTimeout(() => setComposerNudge(false), 2200);
    return () => window.clearTimeout(timeoutId);
  }, [composerNudge]);

  async function handleFolderChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (selectedFiles.length === 0) return;
    if (selectedFiles.some((file) => !isSupportedCodeFile(file))) {
      setImportError("Unsupported file format. Please select a code file or a project folder.");
      return;
    }

    setWorkspaceTree(buildWorkspaceTree(selectedFiles));
    const summary = await buildImportSummary("folder", selectedFiles, indexStats);
    setProjectSummary(summary);
    setIsSummaryOpen(true);
  }

  async function handleSingleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0];
    event.target.value = "";
    if (!selectedFile) return;
    if (!isSupportedCodeFile(selectedFile)) {
      setImportError("Unsupported file format. Please select a code file or a project folder.");
      return;
    }

    setWorkspaceTree(buildWorkspaceTree([selectedFile]));
    const summary = await buildImportSummary("file", [selectedFile], null);
    setProjectSummary(summary);
    setIsSummaryOpen(true);
  }

  async function handleIndexProject() {
    const trimmedProjectPath = projectPath.trim();
    if (!trimmedProjectPath || isIndexing) return;

    setIsIndexing(true);
    setIndexError(null);
    setIndexStats(null);

    try {
      const stats = await indexProject({ project_path: trimmedProjectPath });
      setIndexStats(stats);
      setProjectSummary({
        architecture: stats.architecture,
        chunks: stats.chunks,
        description: stats.summary || "Backend-visible workspace indexed for semantic retrieval.",
        files: stats.indexed_files,
        kind: "folder",
        languages: stats.languages.map((item) => ({ label: item.label, percent: item.percent, value: item.files })),
        lineCount: stats.line_count,
        name: stats.project_name || trimmedProjectPath.replace(/\\/g, "/").split("/").filter(Boolean).at(-1) || "Workspace",
        path: stats.project_path || trimmedProjectPath,
        purpose: stats.likely_purpose,
        sizeBytes: stats.size_bytes,
        structure: stats.structure,
        techStack: stats.tech_stack
      });
      setIsSummaryOpen(true);
    } catch (requestError) {
      setIndexError(formatApiError(requestError));
    } finally {
      setIsIndexing(false);
    }
  }

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmedMessage = message.trim();
    if (isSending) return;
    if (!trimmedMessage) {
      setComposerNudge(true);
      composerRef.current?.focus();
      return;
    }
    if (!authUser) {
      openAuthMode("login");
      return;
    }

    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content: trimmedMessage }]);
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
        { id: `assistant-${Date.now()}`, role: "assistant", content: response.answer, response }
      ]);
    } catch (requestError) {
      setError(formatApiError(requestError));
    } finally {
      setIsSending(false);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  }

  function openAuthMode(nextMode: AuthMode) {
    setAuthError(null);
    setCaptchaInput("");
    setCaptchaCode(randomCaptcha());
    setAuthMode(nextMode);
    setIsUserMenuOpen(false);
  }

  function handleAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthError(null);

    if (authMode !== "profile" && captchaInput.trim().toUpperCase() !== captchaCode) {
      setAuthError("Captcha is incorrect. Please try again.");
      setCaptchaCode(randomCaptcha());
      setCaptchaInput("");
      return;
    }

    const form = new FormData(event.currentTarget);
    const fallbackName = authUser?.name || "Developer";
    const nextName = String(form.get("username") || form.get("email") || fallbackName).trim() || fallbackName;
    const nextUser = { avatarUrl: authUser?.avatarUrl ?? DEFAULT_AVATAR, name: nextName };
    setAuthUser(nextUser);
    window.localStorage.setItem("aicodepilot-user", JSON.stringify(nextUser));
    setCaptchaInput("");
    setAuthMode(null);
  }

  function handleAvatarUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const nextUser = { avatarUrl: String(reader.result), name: authUser?.name ?? "Developer" };
      setAuthUser(nextUser);
      window.localStorage.setItem("aicodepilot-user", JSON.stringify(nextUser));
    };
    reader.readAsDataURL(file);
  }

  function loadDemo() {
    setMessages([
      { id: "demo-user", role: "user", content: "Where is the FastAPI router implemented?", muted: true },
      { id: "demo-assistant", role: "assistant", content: demoResponse.answer, muted: true, response: demoResponse }
    ]);
    setError(null);
  }

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div className="flex items-center gap-3">
          <div className="brand-mark">
            <Bot className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h1>AICodePilot</h1>
            <p>AI codebase understanding and development workspace</p>
          </div>
        </div>

        <div className="top-actions">
          <div
            aria-label={backendReady ? "Backend API ready" : "Backend API unavailable"}
            className={`status-chip app-tooltip ${backendReady ? "ready" : "warning"}`}
            data-tooltip={backendReady ? "Backend API ready" : "Backend API unavailable"}
            role="status"
          >
            {backendReady ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          </div>
          <button
            aria-label="Toggle theme"
            className="icon-button app-tooltip"
            data-tooltip={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
            onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
            type="button"
          >
            {theme === "light" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          {authUser ? (
            <div className="relative">
              <button
                aria-label="Open user menu"
                className="user-button app-tooltip"
                data-tooltip="Account menu"
                onClick={() => setIsUserMenuOpen((open) => !open)}
                type="button"
              >
                <img alt="" src={authUser.avatarUrl} />
                <span>{authUser.name}</span>
                <ChevronDown className="h-4 w-4" />
              </button>
              {isUserMenuOpen ? (
                <div className="user-menu">
                  <button onClick={() => openAuthMode("profile")} type="button">
                    <Settings className="h-4 w-4" />
                    Profile settings
                  </button>
                  <button onClick={() => openAuthMode("forgot")} type="button">
                    <KeyRound className="h-4 w-4" />
                    Reset password
                  </button>
                  <button
                    onClick={() => {
                      setAuthUser(null);
                      window.localStorage.removeItem("aicodepilot-user");
                      setIsUserMenuOpen(false);
                    }}
                    type="button"
                  >
                    <LogIn className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <button className="primary-soft-button" onClick={() => openAuthMode("login")} type="button">
              <User className="h-4 w-4" />
              Sign in
            </button>
          )}
        </div>
      </header>

      <section className={`workspace-grid ${isLeftRailCollapsed ? "left-collapsed" : ""}`}>
        <aside className="workspace-column left-rail">
          <div className="sidebar-brand-row">
            <button
              aria-label={isLeftRailCollapsed ? "Expand sidebar" : "AICodePilot home"}
              className="sidebar-logo-button app-tooltip"
              data-tooltip={isLeftRailCollapsed ? "Open sidebar" : ""}
              onClick={() => {
                if (isLeftRailCollapsed) setIsLeftRailCollapsed(false);
              }}
              type="button"
            >
              <Bot className="sidebar-brand-icon h-5 w-5" aria-hidden="true" />
              <PanelLeftOpen className="sidebar-expand-icon h-4 w-4" aria-hidden="true" />
            </button>
            <button
              aria-label="Collapse sidebar"
              className="rail-toggle-button app-tooltip"
              data-tooltip="Collapse sidebar"
              onClick={() => setIsLeftRailCollapsed(true)}
              type="button"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>

          <nav className="collapsed-rail-actions" aria-label="Collapsed sidebar shortcuts">
            <button
              aria-label="Open model center"
              className="collapsed-rail-button app-tooltip"
              data-tooltip="Model Center"
              onClick={() => setIsLeftRailCollapsed(false)}
              type="button"
            >
              <ModelCenterIcon />
            </button>
            <button
              aria-label="Open workspace"
              className="collapsed-rail-button workspace-shortcut app-tooltip"
              data-tooltip="Workspace"
              onClick={() => setIsLeftRailCollapsed(false)}
              type="button"
            >
              <FolderOpen className="h-4 w-4" aria-hidden="true" />
            </button>
          </nav>

          <div className="left-rail-body">
            <ProviderSelector onChange={setSelection} value={selection} />

            <section className="panel-card workspace-panel">
            <div className="panel-heading">
              <div>
                <h2>Workspace</h2>
                <p className="panel-description">Import code and index a backend-visible path.</p>
              </div>
              <FolderOpen className="h-5 w-5 text-folder" aria-hidden="true" />
            </div>

            <p className="field-label">Local Import</p>
            <div className="workspace-actions">
              <label className="secondary-button file-picker-button">
                <FolderOpen className="h-4 w-4" />
                Open folder
                <input
                  multiple
                  onChange={handleFolderChange}
                  ref={folderInputRef}
                  type="file"
                  {...({ directory: "", webkitdirectory: "" } as Record<string, string>)}
                />
              </label>
              <label className="secondary-button file-picker-button">
                <FileCode2 className="h-4 w-4" />
                Open file
                <input accept={FILE_ACCEPT} onChange={handleSingleFileChange} ref={fileInputRef} type="file" />
              </label>
            </div>

            <label className="field-label" htmlFor="project-path">
              Backend Path
            </label>
            <input
              className="field-input"
              id="project-path"
              onChange={(event) => setProjectPath(event.target.value)}
              value={projectPath}
            />
            <p className="workspace-hint">
              Browser imports power local preview only. RAG indexing requires a path visible to the backend or Docker
              container.
            </p>

            <button
              className="primary-button w-full"
              disabled={isIndexing || !projectPath.trim()}
              onClick={handleIndexProject}
              type="button"
            >
              {isIndexing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
              {isIndexing ? "Indexing" : "Index Workspace"}
            </button>

            {indexStats ? (
              <div className="metric-strip mt-3">
                <span>{indexStats.indexed_files} files</span>
                <span>{indexStats.chunks} chunks</span>
              </div>
            ) : null}
            {indexError ? <div className="error-box mt-3">{indexError}</div> : null}
            <WorkspaceTree nodes={workspaceTree} />
            </section>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-header">
            <div className="flex items-center gap-3">
              <div className="section-icon">
                <Code2 className="h-5 w-5" />
              </div>
              <div>
                <h2>Agent Chat</h2>
                <p>
                  {selection.provider} / {selection.model}
                </p>
              </div>
            </div>
            <button className="secondary-button" onClick={loadDemo} type="button">
              Load example
            </button>
          </div>

          <div className="message-list" ref={scrollRef}>
            {messages.length === 0 ? (
              <section className="chat-welcome">
                <h3>Start with a codebase question</h3>
                <p>Select a workspace, index it, then ask the Agent to inspect files, search code, or explain behavior.</p>
                <div className="quick-action-grid">
                  {QUICK_ACTIONS.map((action) => (
                    <button key={action} onClick={() => setMessage(action)} type="button">
                      {action}
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {messages.map((item) => (
              <article
                className={`message-row ${item.role === "user" ? "user" : "assistant"} ${item.muted ? "muted-demo" : ""}`}
                key={item.id}
              >
                {item.role === "assistant" ? (
                  <div className="agent-avatar">
                    <Bot className="h-4 w-4" />
                  </div>
                ) : null}
                <div className="message-bubble">
                  <MarkdownMessage content={item.content} />
                  {item.response ? (
                    <details className="reasoning-panel">
                      <summary>Execution summary</summary>
                      <ul>
                        {item.response.tool_calls.map((toolCall, index) => (
                          <li key={`${toolCall.name}-${index}`}>{toolCall.name}</li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </div>
                {item.role === "user" ? (
                  <img alt="" className="user-avatar" src={authUser?.avatarUrl ?? DEFAULT_AVATAR} />
                ) : null}
              </article>
            ))}

            {isSending ? (
              <article className="message-row assistant">
                <div className="agent-avatar">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="message-bubble loading">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Thinking through the codebase...
                </div>
              </article>
            ) : null}
            {error ? <div className="error-box">{error}</div> : null}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            {composerNudge ? <div className="composer-empty-hint">Type a message before sending.</div> : null}
            <textarea
              aria-invalid={composerNudge}
              className={composerNudge ? "needs-input" : ""}
              disabled={isSending}
              maxLength={32000}
              onBlur={() => setComposerNudge(false)}
              onChange={(event) => {
                setMessage(event.target.value);
                if (event.target.value.trim()) setComposerNudge(false);
              }}
              onFocus={() => {
                if (message.trim()) setComposerNudge(false);
              }}
              onKeyDown={handleComposerKeyDown}
              placeholder="Ask about this codebase. Shift + Enter for a new line..."
              ref={composerRef}
              value={message}
            />
            <div className="composer-footer">
              <span className={message.length > 12000 ? "text-warning" : ""}>
                {message.length > 12000 ? "Long prompt. Check the selected model context window." : `${message.length.toLocaleString()} chars`}
              </span>
              <button className="send-button" disabled={isSending} type="submit">
                {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                <span>Send</span>
              </button>
            </div>
          </form>
        </section>

        <aside className="workspace-column right-rail">
          <ToolCallTimeline isRunning={isSending} language="en" toolCalls={latestResponse?.tool_calls ?? []} />
          <CodeReference language="en" references={latestResponse?.references ?? []} />
        </aside>
      </section>

      {isSummaryOpen && projectSummary ? (
        <ProjectSummaryModal onClose={() => setIsSummaryOpen(false)} summary={projectSummary} />
      ) : null}
      {importError ? <ImportErrorModal message={importError} onClose={() => setImportError(null)} /> : null}
      {authMode ? (
        <AuthModal
          authError={authError}
          authMode={authMode}
          captchaCode={captchaCode}
          captchaInput={captchaInput}
          onAvatarUpload={handleAvatarUpload}
          onCaptchaChange={setCaptchaInput}
          onClose={() => setAuthMode(null)}
          onModeChange={openAuthMode}
          onRefreshCaptcha={() => setCaptchaCode(randomCaptcha())}
          onSubmit={handleAuthSubmit}
          user={authUser}
        />
      ) : null}
    </main>
  );
}

function ProjectSummaryModal({ onClose, summary }: { onClose: () => void; summary: ProjectSummary }) {
  return (
    <div className="modal-backdrop">
      <section className="project-modal">
        <header className="modal-header">
          <div>
            <p className="panel-kicker">{summary.kind === "folder" ? "Project imported successfully" : "File imported successfully"}</p>
            <h2>{summary.name}</h2>
            <p>{summary.description}</p>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="summary-metrics">
          <span>{summary.files} files</span>
          <span>{formatBytes(summary.sizeBytes)}</span>
          <span>{summary.lineCount.toLocaleString()} lines</span>
          <span>{summary.chunks.toLocaleString()} chunks</span>
        </div>

        <section className="summary-card summary-overview-card">
          <h3>Project overview</h3>
          {summary.path ? <p className="summary-path">{summary.path}</p> : null}
          <p>{summary.purpose}</p>
        </section>

        <div className="summary-grid">
          <section className="summary-card">
            <h3>Technology stack</h3>
            <div className="tag-row">
              {(summary.techStack.length ? summary.techStack : ["Source code"]).map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </section>
          <section className="summary-card">
            <h3>Architecture</h3>
            <ul className="compact-list">
              {(summary.architecture.length ? summary.architecture : ["General software workspace"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="summary-card">
            <h3>Programming languages</h3>
            <div className="language-chart">
              {summary.languages.map((item) => (
                <div className="language-row" key={item.label}>
                  <span>{item.label}</span>
                  <div>
                    <i style={{ width: `${item.percent}%` }} />
                  </div>
                  <strong>{item.percent}%</strong>
                </div>
              ))}
            </div>
          </section>
          <section className="summary-card">
            <h3>Top-level structure</h3>
            <ul className="compact-list structure-list">
              {(summary.structure.length ? summary.structure : ["No folder structure available"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </div>

        <footer className="modal-footer">
          <button className="primary-button" onClick={onClose} type="button">
            Done
          </button>
        </footer>
      </section>
    </div>
  );
}

function ImportErrorModal({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className="modal-backdrop">
      <section className="alert-modal">
        <header className="modal-header">
          <div>
            <p className="panel-kicker">Import blocked</p>
            <h2>Unsupported file format</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X className="h-4 w-4" />
          </button>
        </header>
        <p>{message}</p>
        <footer className="modal-footer">
          <button className="primary-button" onClick={onClose} type="button">
            Choose again
          </button>
        </footer>
      </section>
    </div>
  );
}

function AuthModal({
  authError,
  authMode,
  captchaCode,
  captchaInput,
  onAvatarUpload,
  onCaptchaChange,
  onClose,
  onModeChange,
  onRefreshCaptcha,
  onSubmit,
  user
}: {
  authError: string | null;
  authMode: AuthMode;
  captchaCode: string;
  captchaInput: string;
  onAvatarUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onCaptchaChange: (value: string) => void;
  onClose: () => void;
  onModeChange: (mode: AuthMode) => void;
  onRefreshCaptcha: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  user: AuthUser | null;
}) {
  const isProfile = authMode === "profile";
  const isForgot = authMode === "forgot";
  const title =
    authMode === "login"
      ? "Sign in"
      : authMode === "register"
        ? "Create account"
        : authMode === "forgot"
          ? "Reset password"
          : "Profile settings";

  return (
    <div className="modal-backdrop">
      <form className="auth-modal" onSubmit={onSubmit}>
        <header className="modal-header">
          <div>
            <p className="panel-kicker">Account</p>
            <h2>{title}</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X className="h-4 w-4" />
          </button>
        </header>

        {isProfile ? (
          <div className="profile-avatar">
            <img alt="" src={user?.avatarUrl ?? DEFAULT_AVATAR} />
            <label className="secondary-button">
              Upload avatar
              <input accept="image/*" className="hidden" onChange={onAvatarUpload} type="file" />
            </label>
          </div>
        ) : null}

        <label className="field-label">{isProfile ? "Username" : "Email or username"}</label>
        <input
          className="field-input"
          defaultValue={isProfile ? user?.name : ""}
          name={isProfile || authMode === "register" ? "username" : "email"}
          required
        />

        {!isForgot ? (
          <>
            <label className="field-label">{isProfile ? "Current password" : "Password"}</label>
            <input className="field-input" minLength={isProfile ? undefined : 6} name="password" required={!isProfile} type="password" />
          </>
        ) : null}

        {isProfile || isForgot ? (
          <>
            <label className="field-label">New password</label>
            <input className="field-input" minLength={6} name="newPassword" required={isForgot} type="password" />
          </>
        ) : null}

        {!isProfile ? (
          <>
            <label className="field-label">Captcha</label>
            <div className="captcha-row">
              <input className="field-input" onChange={(event) => onCaptchaChange(event.target.value)} required value={captchaInput} />
              <button className="captcha-code" onClick={onRefreshCaptcha} type="button">
                {captchaCode}
              </button>
            </div>
          </>
        ) : null}

        {authError ? <div className="error-box mb-3">{authError}</div> : null}

        <button className="primary-button w-full" type="submit">
          {authMode === "register" ? <UserPlus className="h-4 w-4" /> : <LogIn className="h-4 w-4" />}
          {isProfile ? "Save profile" : title}
        </button>

        <div className="auth-links">
          <button onClick={() => onModeChange("login")} type="button">
            Sign in
          </button>
          <button onClick={() => onModeChange("register")} type="button">
            Register
          </button>
          <button onClick={() => onModeChange("forgot")} type="button">
            Forgot password
          </button>
        </div>
      </form>
    </div>
  );
}
