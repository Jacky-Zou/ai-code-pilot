"use client";

/* eslint-disable @next/next/no-img-element */

import {
  Bot,
  Copy,
  FolderOpen,
  GitBranch,
  Loader2,
  MessagesSquare,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Pin,
  Send,
} from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { getHealth } from "@/lib/api";
import { CodeReference } from "@/components/CodeReference";
import { type ProviderSelection } from "@/components/ProviderSelector";
import { ToolCallTimeline } from "@/components/ToolCallTimeline";
import { MarkdownMessage, ModelCenterIcon } from "@/components/WorkspaceHelpers";
import { AuthModal } from "@/components/AuthModal";
import { TopBar } from "@/components/TopBar";
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
  const [selection, setSelection] = useState<ProviderSelection>({ provider: "deepseek", model: "" });
  const [isLeftRailCollapsed, setIsLeftRailCollapsed] = useState(false);
  const [isRightRailCollapsed, setIsRightRailCollapsed] = useState(false);
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
      apiKey: selection.apiKey || null,
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
      <TopBar
        backendReady={backendReady}
        theme={theme}
        onToggleTheme={toggleTheme}
        authUser={authUser}
        isUserMenuOpen={isUserMenuOpen}
        setIsUserMenuOpen={setIsUserMenuOpen}
        openAuthMode={openAuthMode}
        onSignOut={handleSignOut}
      />

      {/* ── 3-column workspace ────────────────────────────────────── */}
      <section className={`workspace-grid ${isLeftRailCollapsed ? "left-collapsed" : ""} ${isRightRailCollapsed ? "right-collapsed" : ""}`}>

        {/* Left rail */}
        <aside className="workspace-column left-rail">
          <div className="sidebar-brand-row">
            <button aria-label={isLeftRailCollapsed ? "Expand sidebar" : "AICodePilot home"}
              className="sidebar-logo-button app-tooltip"
              data-tooltip="Expand sidebar"
              onClick={() => { if (isLeftRailCollapsed) setIsLeftRailCollapsed(false); }}
              type="button">
              <Bot className="sidebar-brand-icon h-5 w-5" aria-hidden="true" />
              <PanelLeftOpen className="sidebar-expand-icon h-4 w-4" aria-hidden="true" />
            </button>
            <button aria-label="Collapse sidebar" className="rail-toggle-button app-tooltip"
              data-tooltip="Collapse sidebar"
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
              <div className="section-icon"><MessagesSquare className="h-5 w-5" /></div>
              <div>
                <h2>AI Assistant</h2>
                <p className="panel-description">{selection.provider} · {selection.model || "default"}</p>
              </div>
            </div>
            {!authUser && (
              <span className="demo-badge" title="Sign in to start chatting">Demo mode</span>
            )}
          </div>

          <div className="message-list" ref={scrollRef}>
            {messages.length === 0 && (
              <section className="chat-welcome">
                <p className="welcome-label">Quick actions</p>
                <div className="quick-action-grid">
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
                <div className={`message-bubble ${item.muted ? "muted" : ""} ${item.role === "assistant" && !item.content && isSending ? "thinking" : ""}`}>
                  {item.role === "assistant" && !item.content && isSending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                      {activeToolCalls.length > 0
                        ? `Calling ${activeToolCalls.filter((t) => !t.done).at(-1)?.tool ?? "tool"}…`
                        : "Thinking…"}
                    </>
                  ) : (
                    <>
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
                      <button
                        className="message-copy-btn"
                        onClick={() => navigator.clipboard?.writeText(item.content)}
                        title="Copy message"
                        type="button"
                        aria-label="Copy message"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                    </>
                  )}
                </div>
                {item.role === "user" && (
                  <img alt="" className="user-avatar" src={authUser?.avatarUrl ?? DEFAULT_AVATAR} />
                )}
              </article>
            ))}

            {error && <div className="error-box mx-4 mb-3">{error}</div>}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            {composerNudge && <div className="composer-empty-hint">Please enter a message.</div>}
            <textarea
              aria-invalid={composerNudge}
              className={[
                composerNudge ? "needs-input" : "",
                message.length > 30000 ? "near-limit-red" : message.length > 24000 ? "near-limit-orange" : message.length > 16000 ? "near-limit-yellow" : "",
              ].filter(Boolean).join(" ")}
              disabled={isSending}
              maxLength={32000}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleComposerKeyDown}
              placeholder="Ask about your codebase… (Enter to send, Shift+Enter for newline)"
              value={message}
            />
            {message.length > 30000 && (
              <div className="composer-limit-warn">Character limit almost reached ({message.length}/32000)</div>
            )}
            <div className="composer-footer">
              <button aria-label="Send message" className="send-button" disabled={isSending} type="submit">
                {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-4 w-4" /> Send</>}
              </button>
            </div>
          </form>
        </section>

        {/* Right rail */}
        <aside className={`workspace-column right-rail ${isRightRailCollapsed ? "right-collapsed" : ""}`}>
          <div className="right-rail-brand-row">
            <button
              aria-label={isRightRailCollapsed ? "Expand right panel" : "Collapse right panel"}
              className="rail-toggle-button app-tooltip"
              data-tooltip={isRightRailCollapsed ? "Expand Agent panel" : "Collapse Agent panel"}
              onClick={() => setIsRightRailCollapsed((v) => !v)}
              type="button"
            >
              {isRightRailCollapsed ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
            </button>
          </div>

          {/* Collapsed icons */}
          <nav className="right-rail-actions" aria-label="Collapsed right panel shortcuts">
            <button aria-label="Expand Agent Trace" className="collapsed-rail-button app-tooltip"
              data-tooltip="Agent Trace" onClick={() => setIsRightRailCollapsed(false)} type="button">
              <GitBranch className="h-4 w-4" aria-hidden="true" />
            </button>
            <button aria-label="Expand Code Evidence" className="collapsed-rail-button app-tooltip"
              data-tooltip="Code Evidence" onClick={() => setIsRightRailCollapsed(false)} type="button">
              <Pin className="h-4 w-4" aria-hidden="true" />
            </button>
          </nav>

          <div className="right-rail-body">
            <ToolCallTimeline toolCalls={latestResponse?.tool_calls ?? []} />
            <CodeReference references={latestResponse?.references ?? []} />
          </div>
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
          onNavigate={openAuthMode}
          onSubmit={handleAuthSubmit}
          onAvatarUpload={handleAvatarUpload}
        />
      )}
    </main>
  );
}
