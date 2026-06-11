"use client";

/* eslint-disable @next/next/no-img-element */

import {
  AlertCircle,
  Bot,
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
} from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { getHealth } from "@/lib/api";
import { CodeReference } from "@/components/CodeReference";
import { ProviderSelector, type ProviderSelection } from "@/components/ProviderSelector";
import { ToolCallTimeline } from "@/components/ToolCallTimeline";
import { MarkdownMessage, ModelCenterIcon } from "@/components/WorkspaceHelpers";
import { AuthModal } from "@/components/AuthModal";
import { WorkspacePanel } from "@/components/WorkspacePanel";
import { useChat } from "@/hooks/useChat";
import { useTheme } from "@/hooks/useTheme";
import { useAuth } from "@/hooks/useAuth";
import { useWorkspaceImport } from "@/hooks/useWorkspaceImport";

const DEFAULT_PROJECT_PATH = process.env.NEXT_PUBLIC_DEFAULT_PROJECT_PATH ?? ".";

const QUICK_ACTIONS = [
  "Explain the Agent execution flow",
  "Find the FastAPI route definitions",
  "Review the tool registry design",
  "Generate unit tests for the executor",
  "Analyze a bug from an error log",
  "Suggest a refactor plan",
];

const DEFAULT_AVATAR =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%232563eb'/%3E%3Ccircle cx='32' cy='24' r='11' fill='white' opacity='.95'/%3E%3Cpath d='M14 54c3.6-11 12.2-16 18-16s14.4 5 18 16' fill='white' opacity='.95'/%3E%3C/svg%3E";

export function ChatWorkspace() {
  const [selection, setSelection] = useState<ProviderSelection>({ provider: "openai", model: "" });
  const [isLeftRailCollapsed, setIsLeftRailCollapsed] = useState(false);
  const [projectPath, setProjectPath] = useState(DEFAULT_PROJECT_PATH);
  const [message, setMessage] = useState("");
  const [composerNudge, setComposerNudge] = useState(false);
  const [backendReady, setBackendReady] = useState(false);

  const { theme, toggle: toggleTheme } = useTheme();
  const {
    authUser, authMode, authError, captchaCode, captchaInput, setCaptchaInput,
    isUserMenuOpen, setIsUserMenuOpen, openAuthMode, closeAuth,
    handleAuthSubmit, handleSignOut, handleAvatarUpload,
  } = useAuth();
  const {
    workspaceTree, importError, isIndexing, indexStats, indexError,
    folderInputRef, fileInputRef,
    handleFolderChange, handleSingleFileChange, handleIndexProject, FILE_ACCEPT,
  } = useWorkspaceImport();
  const { messages, isSending, error, activeToolCalls, send } = useChat();

  const scrollRef = useRef<HTMLDivElement>(null);

  // Health check on mount
  useEffect(() => {
    getHealth().then(() => setBackendReady(true)).catch(() => setBackendReady(false));
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  // Composer nudge auto-clear
  useEffect(() => {
    if (composerNudge && message.trim()) setComposerNudge(false);
  }, [message, composerNudge]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!message.trim()) { setComposerNudge(true); return; }
    if (!authUser) { openAuthMode("login"); return; }
    send({
      message: message.trim(),
      projectPath: projectPath || null,
      provider: selection.provider || null,
      model: selection.model || null,
    });
    setMessage("");
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event as unknown as FormEvent);
    }
  }

  const latestResponse = messages.filter((m) => m.role === "assistant" && m.response).at(-1)?.response;

  return (
    <main className="app-shell">
      {/* ── Top bar ──────────────────────────────────────────────── */}
      <header className="top-bar">
        <div className="flex items-center gap-3">
          <div className="brand-mark"><Bot className="h-5 w-5" aria-hidden="true" /></div>
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
          <button aria-label="Toggle theme" className="icon-button app-tooltip"
            data-tooltip={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
            onClick={toggleTheme} type="button">
            {theme === "light" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          {authUser ? (
            <div className="relative">
              <button aria-label="Open user menu" className="user-button app-tooltip"
                data-tooltip="Account menu" onClick={() => setIsUserMenuOpen((o) => !o)} type="button">
                <img alt="" src={authUser.avatarUrl} />
                <span>{authUser.name}</span>
                <ChevronDown className="h-4 w-4" />
              </button>
              {isUserMenuOpen && (
                <div className="user-menu">
                  <button onClick={() => openAuthMode("profile")} type="button">
                    <Settings className="h-4 w-4" /> Profile settings
                  </button>
                  <button onClick={() => openAuthMode("forgot")} type="button">
                    <KeyRound className="h-4 w-4" /> Reset password
                  </button>
                  <button onClick={handleSignOut} type="button">
                    <LogIn className="h-4 w-4" /> Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button className="primary-soft-button" onClick={() => openAuthMode("login")} type="button">
              <User className="h-4 w-4" /> Sign in
            </button>
          )}
        </div>
      </header>

      {/* ── 3-column workspace ────────────────────────────────────── */}
      <section className={`workspace-grid ${isLeftRailCollapsed ? "left-collapsed" : ""}`}>

        {/* Left rail */}
        <aside className="workspace-column left-rail">
          <div className="sidebar-brand-row">
            <button aria-label={isLeftRailCollapsed ? "Expand sidebar" : "AICodePilot home"}
              className="sidebar-logo-button app-tooltip"
              onClick={() => { if (isLeftRailCollapsed) setIsLeftRailCollapsed(false); }}
              type="button">
              <Bot className="sidebar-brand-icon h-5 w-5" aria-hidden="true" />
              <PanelLeftOpen className="sidebar-expand-icon h-4 w-4" aria-hidden="true" />
            </button>
            <button aria-label="Collapse sidebar" className="rail-toggle-button app-tooltip"
              onClick={() => setIsLeftRailCollapsed(true)} type="button">
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>

          <nav className="collapsed-rail-actions" aria-label="Collapsed sidebar shortcuts">
            <button aria-label="Open model center" className="collapsed-rail-button app-tooltip"
              data-tooltip="Model Center" onClick={() => setIsLeftRailCollapsed(false)} type="button">
              <ModelCenterIcon />
            </button>
            <button aria-label="Open workspace" className="collapsed-rail-button workspace-shortcut app-tooltip"
              data-tooltip="Workspace" onClick={() => setIsLeftRailCollapsed(false)} type="button">
              <FolderOpen className="h-4 w-4" aria-hidden="true" />
            </button>
          </nav>

          <div className="left-rail-body">
            <WorkspacePanel
              selection={selection}
              onSelectionChange={setSelection}
              projectPath={projectPath}
              onProjectPathChange={setProjectPath}
              onIndexProject={() => handleIndexProject(projectPath)}
              isIndexing={isIndexing}
              indexStats={indexStats}
              indexError={indexError}
              importError={importError}
              workspaceTree={workspaceTree}
              folderInputRef={folderInputRef}
              fileInputRef={fileInputRef}
              onFolderChange={handleFolderChange}
              onFileChange={handleSingleFileChange}
              fileAccept={FILE_ACCEPT}
            />
          </div>
        </aside>

        {/* Chat panel */}
        <section className="chat-panel">
          <div className="chat-header">
            <div className="flex items-center gap-3">
              <div className="section-icon"><Code2 className="h-5 w-5" /></div>
              <div>
                <h2>Chat</h2>
                <p className="panel-description">{selection.provider} · {selection.model || "default"}</p>
              </div>
            </div>
            {/* Demo mode notice — authentication is browser-only */}
            {!authUser && (
              <span className="demo-badge" title="Sign in to start chatting">Demo mode — sign in required</span>
            )}
          </div>

          <div className="message-list" ref={scrollRef}>
            {messages.length === 0 && (
              <section className="chat-welcome">
                <p className="welcome-label">Quick actions</p>
                <div className="quick-actions-grid">
                  {QUICK_ACTIONS.map((action) => (
                    <button className="quick-action-chip" key={action}
                      onClick={() => setMessage(action)} type="button">
                      {action}
                    </button>
                  ))}
                </div>
              </section>
            )}

            {messages.map((item) => (
              <article className={`message-row ${item.role}`} key={item.id}>
                {item.role === "assistant" && (
                  <div className="agent-avatar" aria-hidden="true">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div className={`message-bubble ${item.muted ? "muted" : ""}`}>
                  <MarkdownMessage content={item.content} />
                  {item.response?.tool_calls?.length ? (
                    <details className="tool-summary">
                      <summary>{item.response.tool_calls.length} tool call{item.response.tool_calls.length > 1 ? "s" : ""}</summary>
                      <ul>
                        {item.response.tool_calls.map((tc, i) => (
                          <li key={i}><code>{tc.name}</code>{tc.error ? ` ✗ ${tc.error}` : " ✓"}</li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </div>
                {item.role === "user" && (
                  <img alt="" className="user-avatar" src={authUser?.avatarUrl ?? DEFAULT_AVATAR} />
                )}
              </article>
            ))}

            {isSending && (
              <article className="message-row assistant">
                <div className="agent-avatar" aria-hidden="true"><Bot className="h-4 w-4" /></div>
                <div className="message-bubble thinking">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  {activeToolCalls.length > 0
                    ? `Calling ${activeToolCalls.filter((t) => !t.done).at(-1)?.tool ?? "tool"}…`
                    : "Thinking…"}
                </div>
              </article>
            )}
            {error && <div className="error-box mx-4 mb-3">{error}</div>}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            {composerNudge && <div className="composer-empty-hint">Please enter a message.</div>}
            <textarea
              aria-invalid={composerNudge}
              className={composerNudge ? "needs-input" : ""}
              disabled={isSending}
              maxLength={32000}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleComposerKeyDown}
              placeholder="Ask about your codebase… (Enter to send, Shift+Enter for newline)"
              value={message}
            />
            <div className="composer-footer">
              <span className={message.length > 12000 ? "char-warn" : "char-count"}>
                {message.length} / 32000
              </span>
              <button aria-label="Send message" className="send-button" disabled={isSending} type="submit">
                {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </button>
            </div>
          </form>
        </section>

        {/* Right rail */}
        <aside className="workspace-column right-rail">
          <ToolCallTimeline toolCalls={latestResponse?.tool_calls ?? []} />
          <CodeReference references={latestResponse?.references ?? []} />
        </aside>
      </section>

      {/* ── Auth modal (demo-only) ───────────────────────────────── */}
      {authMode && (
        <AuthModal
          authMode={authMode}
          authError={authError}
          captchaCode={captchaCode}
          captchaInput={captchaInput}
          setCaptchaInput={setCaptchaInput}
          userName={authUser?.name}
          onClose={closeAuth}
          onSubmit={handleAuthSubmit}
          onAvatarUpload={handleAvatarUpload}
        />
      )}
    </main>
  );
}
