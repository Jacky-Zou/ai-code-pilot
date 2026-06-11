"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

export type AuthUser = {
  avatarUrl: string;
  name: string;
};

export type AuthMode = "login" | "register" | "profile" | "forgot";

const STORAGE_KEY = "aicodepilot-user";

/**
 * Local browser-side authentication state.
 *
 * NOTE: This is a DEMO-ONLY implementation. Credentials are stored in
 * localStorage and validated entirely in the browser with no backend
 * involvement. It is clearly labelled here so the UI can display the
 * appropriate disclaimer to users.
 */
export function useAuth() {
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [captchaCode, setCaptchaCode] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  // Restore persisted demo session on mount
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setAuthUser(JSON.parse(stored) as AuthUser);
      }
    } catch {
      // Ignore malformed stored data
    }
  }, []);

  const openAuthMode = useCallback((mode: AuthMode) => {
    setAuthMode(mode);
    setAuthError(null);
    setCaptchaInput("");
    // Simple 6-character alphanumeric captcha for demo purposes
    setCaptchaCode(
      Math.random().toString(36).slice(2, 8).toUpperCase()
    );
  }, []);

  const closeAuth = useCallback(() => {
    setAuthMode(null);
    setAuthError(null);
  }, []);

  const handleAuthSubmit = useCallback(
    (formData: {
      name?: string;
      captchaInput: string;
      avatarUrl?: string;
    }) => {
      if (
        authMode === "login" ||
        authMode === "register" ||
        authMode === "forgot"
      ) {
        if (formData.captchaInput.toUpperCase() !== captchaCode) {
          setAuthError("Verification code does not match.");
          return;
        }
      }

      const nextUser: AuthUser = {
        name: formData.name ?? authUser?.name ?? "Guest",
        avatarUrl:
          formData.avatarUrl ??
          authUser?.avatarUrl ??
          `https://api.dicebear.com/7.x/bottts/svg?seed=${Date.now()}`,
      };

      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
      setAuthUser(nextUser);
      setAuthMode(null);
      setAuthError(null);
    },
    [authMode, captchaCode, authUser]
  );

  const handleSignOut = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    setAuthUser(null);
    setIsUserMenuOpen(false);
  }, []);

  const handleAvatarUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const url = e.target?.result as string;
        const updated: AuthUser = {
          name: authUser?.name ?? "User",
          avatarUrl: url,
        };
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        setAuthUser(updated);
      };
      reader.readAsDataURL(file);
    },
    [authUser]
  );

  return {
    authUser,
    authMode,
    authError,
    captchaCode,
    captchaInput,
    setCaptchaInput,
    isUserMenuOpen,
    setIsUserMenuOpen,
    openAuthMode,
    closeAuth,
    handleAuthSubmit,
    handleSignOut,
    handleAvatarUpload,
  };
}
