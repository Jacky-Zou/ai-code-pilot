"use client";

/* eslint-disable @next/next/no-img-element */

import {
  AlertCircle,
  Bot,
  CheckCircle2,
  ChevronDown,
  KeyRound,
  LogIn,
  Moon,
  Settings,
  Sun,
  User,
} from "lucide-react";
import type { AuthMode, AuthUser } from "@/hooks/useAuth";

interface TopBarProps {
  backendReady: boolean;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  authUser: AuthUser | null;
  isUserMenuOpen: boolean;
  setIsUserMenuOpen: (updater: (open: boolean) => boolean) => void;
  openAuthMode: (mode: AuthMode) => void;
  onSignOut: () => void;
}

/**
 * Application top bar: branding, backend status, theme toggle, and the
 * sign-in / user menu. Extracted from ChatWorkspace to keep that component
 * focused on chat orchestration and under the 300-line ceiling.
 */
export function TopBar({
  backendReady,
  theme,
  onToggleTheme,
  authUser,
  isUserMenuOpen,
  setIsUserMenuOpen,
  openAuthMode,
  onSignOut,
}: TopBarProps) {
  return (
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
          onClick={onToggleTheme} type="button">
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
                <button onClick={onSignOut} type="button">
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
  );
}
