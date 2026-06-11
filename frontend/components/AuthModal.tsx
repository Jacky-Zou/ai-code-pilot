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
  onSubmit: (data: { name?: string; captchaInput: string }) => void;
  onAvatarUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const TITLES: Record<AuthMode, string> = {
  login: "Sign in",
  register: "Create account",
  profile: "Profile",
  forgot: "Reset password",
};

export function AuthModal({
  authMode, authError, captchaCode, captchaInput, setCaptchaInput,
  userName, onClose, onSubmit, onAvatarUpload,
}: Props) {
  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <button aria-label="Close" className="modal-close" onClick={onClose} type="button">✕</button>
        <h2>{TITLES[authMode]}</h2>
        <p className="demo-notice">⚠ Demo mode — authentication is browser-only and not secure.</p>
        <form onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          onSubmit({ name: (fd.get("name") as string) || undefined, captchaInput });
        }}>
          {(authMode === "register" || authMode === "profile") && (
            <div className="field-group">
              <label htmlFor="auth-name">Display name</label>
              <input defaultValue={userName} id="auth-name" name="name" required type="text" />
            </div>
          )}
          {authMode !== "profile" && (
            <>
              <div className="captcha-row">
                <span className="captcha-display">{captchaCode}</span>
                <input onChange={(e) => setCaptchaInput(e.target.value)}
                  placeholder="Enter code" required type="text" value={captchaInput} />
              </div>
              {authError && <p className="field-error">{authError}</p>}
            </>
          )}
          {authMode === "profile" && (
            <div className="field-group">
              <label>Avatar</label>
              <input accept="image/*" onChange={onAvatarUpload} type="file" />
            </div>
          )}
          <button className="primary-button w-full mt-4" type="submit">
            {authMode === "login" ? "Sign in" : authMode === "register" ? "Create account" : "Save"}
          </button>
        </form>
      </div>
    </div>
  );
}
