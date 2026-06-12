"use client";

import type { AuthMode } from "@/hooks/useAuth";

interface Props {
  authMode: AuthMode;
  authError: string | null;
  captchaCode: string;
  captchaInput: string;
  setCaptchaInput: (v: string) => void;
  userName?: string;
  onClose: () => void;
  onNavigate: (mode: AuthMode) => void;
  onSubmit: (data: { name?: string; captchaInput: string }) => void;
  onAvatarUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const TITLES: Record<AuthMode, string> = {
  login: "Sign in",
  register: "Create account",
  profile: "Edit profile",
  forgot: "Reset password",
};

export function AuthModal({
  authMode, authError, captchaCode, captchaInput, setCaptchaInput,
  userName, onClose, onNavigate, onSubmit, onAvatarUpload,
}: Props) {
  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={TITLES[authMode]}
    >
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="modal-header">
          <div>
            <h2>{TITLES[authMode]}</h2>
            <p style={{ margin: "4px 0 0", color: "var(--muted)", fontSize: "12px" }}>
              Demo mode — stored in browser only, not secure.
            </p>
          </div>
          <button
            aria-label="Close"
            className="icon-button compact"
            onClick={onClose}
            type="button"
            style={{ flexShrink: 0 }}
          >
            ✕
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            onSubmit({ name: (fd.get("name") as string) || undefined, captchaInput });
          }}
        >
          {/* Display name (register + profile) */}
          {(authMode === "register" || authMode === "profile") && (
            <div style={{ marginBottom: "12px" }}>
              <label className="field-label" htmlFor="auth-name">Display name</label>
              <input
                className="field-input"
                defaultValue={userName}
                id="auth-name"
                name="name"
                required
                type="text"
                placeholder="Your name"
              />
            </div>
          )}

          {/* Avatar upload (profile only) */}
          {authMode === "profile" && (
            <div style={{ marginBottom: "12px" }}>
              <label className="field-label">Avatar image</label>
              <input accept="image/*" className="field-input" onChange={onAvatarUpload} type="file" />
            </div>
          )}

          {/* Captcha (login / register / forgot) */}
          {authMode !== "profile" && (
            <div style={{ marginBottom: "12px" }}>
              <label className="field-label">Verification code</label>
              <div className="captcha-row">
                <input
                  className="field-input"
                  onChange={(e) => setCaptchaInput(e.target.value)}
                  placeholder="Enter code shown"
                  required
                  type="text"
                  value={captchaInput}
                />
                <span className="captcha-code">{captchaCode}</span>
              </div>
              {authError && (
                <p style={{ margin: "6px 0 0", color: "var(--danger)", fontSize: "13px" }}>
                  {authError}
                </p>
              )}
            </div>
          )}

          <button
            className="primary-button"
            style={{ width: "100%", marginTop: "8px" }}
            type="submit"
          >
            {authMode === "login" ? "Sign in"
              : authMode === "register" ? "Create account"
              : authMode === "forgot" ? "Reset password"
              : "Save changes"}
          </button>
        </form>

        {/* Navigation links */}
        {(authMode === "login" || authMode === "register") && (
          <div className="auth-links">
            {authMode === "login" ? (
              <>
                <span style={{ color: "var(--muted)", fontSize: "12px" }}>No account?</span>
                <button
                  type="button"
                  className="auth-links button"
                  style={{ border: 0, background: "transparent", color: "var(--primary)", fontSize: "12px", fontWeight: 800, cursor: "pointer" }}
                  onClick={() => onNavigate("register")}
                >
                  Create one
                </button>
              </>
            ) : (
              <>
                <span style={{ color: "var(--muted)", fontSize: "12px" }}>Already have an account?</span>
                <button
                  type="button"
                  style={{ border: 0, background: "transparent", color: "var(--primary)", fontSize: "12px", fontWeight: 800, cursor: "pointer" }}
                  onClick={() => onNavigate("login")}
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
