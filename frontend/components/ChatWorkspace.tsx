"use client";

/* eslint-disable @next/next/no-img-element */

import {
  AlertCircle,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Code2,
  Database,
  FileCode2,
  FolderOpen,
  KeyRound,
  Languages,
  Loader2,
  LogIn,
  Moon,
  Send,
  Settings,
  ShieldCheck,
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
import { ProviderSelector, type Language, type ProviderSelection } from "@/components/ProviderSelector";
import { CodeReference } from "@/components/CodeReference";
import { ToolCallTimeline } from "@/components/ToolCallTimeline";

type Theme = "light" | "dark";
type AuthMode = "login" | "register" | "profile" | "forgot";

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

type ProjectSummary = {
  architecture: string[];
  chunks: number;
  description: string;
  files: number;
  languages: Array<{ label: string; percent: number; value: number }>;
  name: string;
  purpose: string;
  stack: string[];
  structure: string[];
};

const DEFAULT_PROJECT_PATH = process.env.NEXT_PUBLIC_DEFAULT_PROJECT_PATH ?? "/workspace";
const DEFAULT_AVATAR =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%232563eb'/%3E%3Ccircle cx='32' cy='24' r='11' fill='white' opacity='.95'/%3E%3Cpath d='M14 54c3.6-11 12.2-16 18-16s14.4 5 18 16' fill='white' opacity='.95'/%3E%3C/svg%3E";

const demoResponse: ChatResponse = {
  answer:
    "The FastAPI backend is wired in `backend/app/main.py`.\n\n| Area | File |\n| --- | --- |\n| App entry | `backend/app/main.py` |\n| Chat route | `backend/app/api/routes_chat.py` |\n\n```python\napplication.include_router(chat_router)\napplication.include_router(project_router)\n```",
  provider: "openai",
  model: "gpt-5.2",
  tool_calls: [
    {
      name: "search_text",
      arguments: { keyword: "APIRouter" },
      result: { count: 2 },
      error: null
    },
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

const COPY = {
  zh: {
    apiReady: "Backend API 就绪",
    apiUnavailable: "Backend API 不可用",
    appSubtitle: "专业代码库理解与开发辅助工作台",
    askPlaceholder: "询问这个代码库，Shift + Enter 换行...",
    codebase: "代码库导入",
    codebaseHint: "Docker 环境建议配置 D:/code/my_projects -> /workspace，也可直接输入容器内路径。",
    contextWarning: "输入较长，请确认模型上下文足够。",
    dockerPath: "后端可访问路径",
    forgot: "忘记密码",
    index: "索引代码库",
    indexing: "索引中",
    loadExample: "加载示例对话",
    login: "登录",
    logout: "退出登录",
    profile: "个人信息设置",
    register: "注册",
    send: "发送",
    summary: "项目摘要",
    theme: "主题",
    tools: "能力入口",
    uploadFolder: "打开本地文件夹"
  },
  en: {
    apiReady: "Backend API ready",
    apiUnavailable: "Backend API unavailable",
    appSubtitle: "Professional codebase Agent workspace",
    askPlaceholder: "Ask about this codebase, Shift + Enter for newline...",
    codebase: "Codebase Import",
    codebaseHint: "In Docker, map D:/code/my_projects -> /workspace or use a container-visible path.",
    contextWarning: "Long input. Make sure the selected model context is sufficient.",
    dockerPath: "Backend-visible path",
    forgot: "Forgot password",
    index: "Index codebase",
    indexing: "Indexing",
    loadExample: "Load example",
    login: "Sign in",
    logout: "Sign out",
    profile: "Profile settings",
    register: "Create account",
    send: "Send",
    summary: "Project Summary",
    theme: "Theme",
    tools: "Capabilities",
    uploadFolder: "Open local folder"
  }
};

const CAPABILITIES = {
  zh: [
    "代码生成 / 重构",
    "架构分析与建议",
    "自动化测试生成",
    "Bug 定位与修复",
    "依赖与安全扫描",
    "文档自动生成",
    "多文件上下文理解",
    "Git 操作辅助"
  ],
  en: [
    "Code generation/refactor",
    "Architecture review",
    "Test generation",
    "Bug diagnosis",
    "Dependency/security scan",
    "Docs generation",
    "Multi-file context",
    "Git assistance"
  ]
};

const initialMessages: ChatMessage[] = [
  {
    id: "demo-user",
    role: "user",
    content: "Where is the FastAPI router implemented?",
    muted: true
  },
  {
    id: "demo-assistant",
    role: "assistant",
    content: demoResponse.answer,
    muted: true,
    response: demoResponse
  }
];

function formatApiError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (typeof error.body?.detail === "string") {
      return error.body.detail;
    }
    return error.body?.detail ? JSON.stringify(error.body.detail) : error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Chat request failed.";
}

function randomCaptcha(): string {
  return Math.random().toString(36).slice(2, 6).toUpperCase();
}

function inferLanguage(fileName: string): string {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (extension === "py") return "Python";
  if (["ts", "tsx", "js", "jsx"].includes(extension ?? "")) return "TypeScript";
  if (["css", "scss"].includes(extension ?? "")) return "CSS";
  if (["md", "mdx"].includes(extension ?? "")) return "Markdown";
  if (["yml", "yaml", "toml", "json"].includes(extension ?? "")) return "Config";
  return "Other";
}

function buildProjectSummary(
  projectPath: string,
  stats: ProjectIndexResponse | null,
  folderFiles: File[]
): ProjectSummary {
  const pathParts = projectPath.replace(/\\/g, "/").split("/").filter(Boolean);
  const name = pathParts.at(-1) || "AICodePilot";
  const files = folderFiles.length || stats?.indexed_files || 0;
  const chunks = stats?.chunks ?? 0;
  const languageCounts = new Map<string, number>();
  const structure = new Set<string>();

  for (const file of folderFiles.slice(0, 800)) {
    const relativePath = file.webkitRelativePath || file.name;
    languageCounts.set(inferLanguage(relativePath), (languageCounts.get(inferLanguage(relativePath)) ?? 0) + 1);
    const parts = relativePath.split("/").filter(Boolean);
    if (parts.length > 1) {
      structure.add(parts.slice(0, Math.min(parts.length, 3)).join("/"));
    }
  }

  if (languageCounts.size === 0) {
    languageCounts.set("Python", 42);
    languageCounts.set("TypeScript", 28);
    languageCounts.set("Markdown", 16);
    languageCounts.set("Config", 14);
  }

  const total = Array.from(languageCounts.values()).reduce((sum, value) => sum + value, 0) || 1;
  const languages = Array.from(languageCounts.entries())
    .map(([label, value]) => ({
      label,
      percent: Math.round((value / total) * 100),
      value
    }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 6);

  return {
    architecture: ["FastAPI backend", "Next.js frontend", "Hand-written Agent loop", "RAG retrieval", "Docker Compose"],
    chunks,
    description: "AI codebase understanding and development assistant with Agent tool calling and RAG retrieval.",
    files,
    languages,
    name,
    purpose: "Help developers inspect unfamiliar projects, locate logic, analyze issues, and generate engineering guidance.",
    stack: ["Python", "FastAPI", "React", "Next.js", "Tailwind CSS", "LLM API", "RAG", "Docker"],
    structure:
      structure.size > 0
        ? Array.from(structure).slice(0, 12)
        : ["backend/app/agent", "backend/app/tools", "backend/app/rag", "frontend/components", "docs"]
  };
}

function MarkdownMessage({ content }: { content: string }) {
  return (
    <ReactMarkdown
      rehypePlugins={[rehypeHighlight]}
      remarkPlugins={[remarkGfm]}
      components={{
        code({ className, children, ...props }) {
          return (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
        table({ children }) {
          return <div className="markdown-table-wrap"><table>{children}</table></div>;
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

export function ChatWorkspace() {
  const [selection, setSelection] = useState<ProviderSelection>({
    provider: "deepseek",
    model: "deepseek-v4-pro"
  });
  const [language, setLanguage] = useState<Language>("zh");
  const [theme, setTheme] = useState<Theme>("light");
  const [projectPath, setProjectPath] = useState(DEFAULT_PROJECT_PATH);
  const [folderFiles, setFolderFiles] = useState<File[]>([]);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isSending, setIsSending] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStats, setIndexStats] = useState<ProjectIndexResponse | null>(null);
  const [projectSummary, setProjectSummary] = useState<ProjectSummary | null>(null);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);
  const [backendReady, setBackendReady] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const [captchaCode, setCaptchaCode] = useState(randomCaptcha);
  const [captchaInput, setCaptchaInput] = useState("");
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const folderInputRef = useRef<HTMLInputElement | null>(null);

  const labels = COPY[language];
  const latestResponse = useMemo(
    () => [...messages].reverse().find((item) => item.response)?.response ?? null,
    [messages]
  );
  const reasoningItems = latestResponse?.tool_calls.map((toolCall) => toolCall.name) ?? [];

  useEffect(() => {
    const storedLanguage = window.localStorage.getItem("aicodepilot-language") as Language | null;
    const storedTheme = window.localStorage.getItem("aicodepilot-theme") as Theme | null;
    const storedUser = window.localStorage.getItem("aicodepilot-user");
    if (storedLanguage === "zh" || storedLanguage === "en") {
      setLanguage(storedLanguage);
    }
    if (storedTheme === "light" || storedTheme === "dark") {
      setTheme(storedTheme);
    }
    if (storedUser) {
      setAuthUser(JSON.parse(storedUser) as AuthUser);
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("aicodepilot-theme", theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem("aicodepilot-language", language);
  }, [language]);

  useEffect(() => {
    getHealth()
      .then(() => setBackendReady(true))
      .catch(() => setBackendReady(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages, isSending, error]);

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) {
      return;
    }
    if (!authUser) {
      setAuthMode("login");
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmedMessage
    };

    // Optimistic UI keeps the chat responsive while the backend Agent performs
    // potentially multi-step tool planning, RAG lookup, and final synthesis.
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

    setIsIndexing(true);
    setIndexError(null);
    setIndexStats(null);

    try {
      const stats = await indexProject({ project_path: trimmedProjectPath });
      const summary = buildProjectSummary(trimmedProjectPath, stats, folderFiles);
      setIndexStats(stats);
      setProjectSummary(summary);
      setIsSummaryOpen(true);
    } catch (requestError) {
      setIndexError(formatApiError(requestError));
    } finally {
      setIsIndexing(false);
    }
  }

  function handleFolderChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    setFolderFiles(selectedFiles);
    if (selectedFiles[0]?.webkitRelativePath) {
      const rootFolder = selectedFiles[0].webkitRelativePath.split("/")[0];
      setProjectSummary(buildProjectSummary(rootFolder, indexStats, selectedFiles));
      setIsSummaryOpen(true);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  }

  function handleAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (captchaInput.trim().toUpperCase() !== captchaCode) {
      setCaptchaCode(randomCaptcha());
      setCaptchaInput("");
      return;
    }
    const form = new FormData(event.currentTarget);
    const nextUser = {
      avatarUrl: authUser?.avatarUrl ?? DEFAULT_AVATAR,
      name: String(form.get("username") || form.get("email") || "Jacky")
    };
    setAuthUser(nextUser);
    window.localStorage.setItem("aicodepilot-user", JSON.stringify(nextUser));
    setCaptchaInput("");
    setAuthMode(null);
  }

  function handleAvatarUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !authUser) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const nextUser = { ...authUser, avatarUrl: String(reader.result) };
      setAuthUser(nextUser);
      window.localStorage.setItem("aicodepilot-user", JSON.stringify(nextUser));
    };
    reader.readAsDataURL(file);
  }

  function loadDemo() {
    setMessages(initialMessages);
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
            <p>{labels.appSubtitle}</p>
          </div>
        </div>

        <div className="top-actions">
          <div className={`status-chip ${backendReady ? "ready" : "warning"}`}>
            {backendReady ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
            {backendReady ? labels.apiReady : labels.apiUnavailable}
          </div>
          <button
            className="icon-button"
            onClick={() => setLanguage((current) => (current === "zh" ? "en" : "zh"))}
            title="Language"
            type="button"
          >
            <Languages className="h-4 w-4" />
            <span>{language === "zh" ? "中文" : "EN"}</span>
          </button>
          <button
            className="icon-button"
            onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
            title={labels.theme}
            type="button"
          >
            {theme === "light" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          {authUser ? (
            <div className="relative">
              <button className="user-button" onClick={() => setIsUserMenuOpen((open) => !open)} type="button">
                <img alt="" src={authUser.avatarUrl} />
                <span>{authUser.name}</span>
                <ChevronDown className="h-4 w-4" />
              </button>
              {isUserMenuOpen ? (
                <div className="user-menu">
                  <button onClick={() => setAuthMode("profile")} type="button">
                    <Settings className="h-4 w-4" />
                    {labels.profile}
                  </button>
                  <button onClick={() => setAuthMode("forgot")} type="button">
                    <KeyRound className="h-4 w-4" />
                    {labels.forgot}
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
                    {labels.logout}
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <button className="primary-soft-button" onClick={() => setAuthMode("login")} type="button">
              <User className="h-4 w-4" />
              {labels.login}
            </button>
          )}
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="workspace-column left-rail">
          <ProviderSelector language={language} onChange={setSelection} value={selection} />

          <section className="panel-card">
            <div className="panel-heading">
              <div>
                <p className="panel-kicker">Repository</p>
                <h2>{labels.codebase}</h2>
              </div>
              <FolderOpen className="h-5 w-5 text-accent" aria-hidden="true" />
            </div>

            <input className="hidden" multiple onChange={handleFolderChange} ref={folderInputRef} type="file" />
            <button
              className="secondary-button mb-3 w-full"
              onClick={() => {
                folderInputRef.current?.setAttribute("webkitdirectory", "");
                folderInputRef.current?.click();
              }}
              type="button"
            >
              <FolderOpen className="h-4 w-4" />
              {labels.uploadFolder}
            </button>

            <label className="field-label" htmlFor="project-path">
              {labels.dockerPath}
            </label>
            <input
              className="field-input mb-3"
              id="project-path"
              onChange={(event) => setProjectPath(event.target.value)}
              value={projectPath}
            />
            <p className="mb-3 text-xs leading-5 text-muted">{labels.codebaseHint}</p>

            <button
              className="accent-button w-full"
              disabled={isIndexing || !projectPath.trim()}
              onClick={handleIndexProject}
              type="button"
            >
              {isIndexing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
              {isIndexing ? labels.indexing : labels.index}
            </button>

            {indexStats ? (
              <div className="metric-strip mt-3">
                <span>{indexStats.indexed_files} files</span>
                <span>{indexStats.chunks} chunks</span>
              </div>
            ) : null}
            {indexError ? <div className="error-box mt-3">{indexError}</div> : null}
          </section>

          <section className="panel-card flex-1">
            <div className="panel-heading">
              <div>
                <p className="panel-kicker">Roadmap</p>
                <h2>{labels.tools}</h2>
              </div>
              <BrainCircuit className="h-5 w-5 text-primary" />
            </div>
            <div className="capability-grid">
              {CAPABILITIES[language].map((capability) => (
                <button className="capability-chip" key={capability} type="button">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  {capability}
                </button>
              ))}
            </div>
          </section>
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
              {labels.loadExample}
            </button>
          </div>

          <div className="message-list" ref={scrollRef}>
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
                      <summary>{language === "zh" ? "执行摘要" : "Reasoning summary"}</summary>
                      <ul>
                        {reasoningItems.map((toolName, index) => (
                          <li key={`${toolName}-${index}`}>{toolName}</li>
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
                  {language === "zh" ? "Agent 正在分析代码库..." : "Agent is analyzing the codebase..."}
                </div>
              </article>
            ) : null}
            {error ? <div className="error-box">{error}</div> : null}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              disabled={isSending}
              maxLength={32000}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={handleComposerKeyDown}
              placeholder={labels.askPlaceholder}
              value={message}
            />
            <div className="composer-footer">
              <span className={message.length > 12000 ? "text-warning" : ""}>
                {message.length > 12000 ? labels.contextWarning : `${message.length.toLocaleString()} chars`}
              </span>
              <button className="send-button" disabled={isSending || !message.trim()} type="submit">
                {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                <span>{labels.send}</span>
              </button>
            </div>
          </form>
        </section>

        <aside className="workspace-column right-rail">
          <ToolCallTimeline
            isRunning={isSending}
            language={language}
            toolCalls={latestResponse?.tool_calls ?? []}
          />
          <CodeReference language={language} references={latestResponse?.references ?? []} />
        </aside>
      </section>

      {isSummaryOpen && projectSummary ? (
        <ProjectSummaryModal language={language} onClose={() => setIsSummaryOpen(false)} summary={projectSummary} />
      ) : null}

      {authMode ? (
        <AuthModal
          authMode={authMode}
          captchaCode={captchaCode}
          captchaInput={captchaInput}
          language={language}
          onAvatarUpload={handleAvatarUpload}
          onCaptchaChange={setCaptchaInput}
          onClose={() => setAuthMode(null)}
          onModeChange={setAuthMode}
          onRefreshCaptcha={() => setCaptchaCode(randomCaptcha())}
          onSubmit={handleAuthSubmit}
          user={authUser}
        />
      ) : null}
    </main>
  );
}

function ProjectSummaryModal({
  language,
  onClose,
  summary
}: {
  language: Language;
  onClose: () => void;
  summary: ProjectSummary;
}) {
  return (
    <div className="modal-backdrop">
      <section className="project-modal">
        <div className="modal-header">
          <div>
            <p className="panel-kicker">{language === "zh" ? "项目摘要" : "Project Summary"}</p>
            <h2>{summary.name}</h2>
            <p>{summary.description}</p>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="summary-grid">
          <div className="summary-card">
            <h3>{language === "zh" ? "用途" : "Purpose"}</h3>
            <p>{summary.purpose}</p>
          </div>
          <div className="summary-card">
            <h3>{language === "zh" ? "规模" : "Size"}</h3>
            <div className="metric-strip">
              <span>{summary.files} files</span>
              <span>{summary.chunks} chunks</span>
            </div>
          </div>
        </div>

        <div className="summary-card">
          <h3>{language === "zh" ? "技术栈" : "Tech Stack"}</h3>
          <div className="tag-row">
            {summary.stack.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <div className="summary-grid">
          <div className="summary-card">
            <h3>{language === "zh" ? "主要架构" : "Architecture"}</h3>
            <ul className="compact-list">
              {summary.architecture.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="summary-card">
            <h3>{language === "zh" ? "结构概览" : "Structure"}</h3>
            <ul className="compact-list structure-list">
              {summary.structure.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="summary-card">
          <h3>{language === "zh" ? "语言比例" : "Language Mix"}</h3>
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
        </div>
      </section>
    </div>
  );
}

function AuthModal({
  authMode,
  captchaCode,
  captchaInput,
  language,
  onAvatarUpload,
  onCaptchaChange,
  onClose,
  onModeChange,
  onRefreshCaptcha,
  onSubmit,
  user
}: {
  authMode: AuthMode;
  captchaCode: string;
  captchaInput: string;
  language: Language;
  onAvatarUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onCaptchaChange: (value: string) => void;
  onClose: () => void;
  onModeChange: (mode: AuthMode) => void;
  onRefreshCaptcha: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  user: AuthUser | null;
}) {
  const isProfile = authMode === "profile";
  const title =
    language === "zh"
      ? authMode === "login"
        ? "登录 AICodePilot"
        : authMode === "register"
          ? "创建账号"
          : authMode === "forgot"
            ? "找回密码"
            : "个人信息设置"
      : authMode === "login"
        ? "Sign in"
        : authMode === "register"
          ? "Create account"
          : authMode === "forgot"
            ? "Reset password"
            : "Profile settings";

  return (
    <div className="modal-backdrop">
      <form className="auth-modal" onSubmit={onSubmit}>
        <div className="modal-header">
          <div>
            <p className="panel-kicker">Account</p>
            <h2>{title}</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X className="h-4 w-4" />
          </button>
        </div>

        {isProfile ? (
          <div className="profile-avatar">
            <img alt="" src={user?.avatarUrl ?? DEFAULT_AVATAR} />
            <label className="secondary-button">
              {language === "zh" ? "上传头像" : "Upload avatar"}
              <input accept="image/*" className="hidden" onChange={onAvatarUpload} type="file" />
            </label>
          </div>
        ) : null}

        <label className="field-label">{language === "zh" ? "邮箱 / 用户名" : "Email / username"}</label>
        <input className="field-input" name={authMode === "login" ? "email" : "username"} required />

        {authMode !== "forgot" ? (
          <>
            <label className="field-label">{language === "zh" ? "密码" : "Password"}</label>
            <input className="field-input" minLength={6} name="password" required type="password" />
          </>
        ) : null}

        <label className="field-label">{language === "zh" ? "验证码" : "Captcha"}</label>
        <div className="captcha-row">
          <input
            className="field-input"
            onChange={(event) => onCaptchaChange(event.target.value)}
            required
            value={captchaInput}
          />
          <button className="captcha-code" onClick={onRefreshCaptcha} type="button">
            {captchaCode}
          </button>
        </div>

        <button className="primary-button w-full" type="submit">
          {authMode === "register" ? <UserPlus className="h-4 w-4" /> : <LogIn className="h-4 w-4" />}
          {title}
        </button>

        <div className="auth-links">
          <button onClick={() => onModeChange("login")} type="button">
            {language === "zh" ? "登录" : "Sign in"}
          </button>
          <button onClick={() => onModeChange("register")} type="button">
            {language === "zh" ? "注册" : "Register"}
          </button>
          <button onClick={() => onModeChange("forgot")} type="button">
            {language === "zh" ? "忘记密码" : "Forgot password"}
          </button>
        </div>
      </form>
    </div>
  );
}
