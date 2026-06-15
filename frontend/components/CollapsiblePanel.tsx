"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  icon: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
}

/**
 * 可折叠面板。logo 既是图标也是折叠/展开控件：
 * 鼠标移入 logo 时图标淡出、折叠/展开箭头淡入；移出恢复为 logo。
 * 不再有右侧独立的 chevron（避免冗余）。
 */
export function CollapsiblePanel({ title, description, icon, defaultOpen = false, children }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="collapsible-panel">
      <button
        className="collapsible-panel-header"
        onClick={() => setOpen((o) => !o)}
        type="button"
        aria-expanded={open}
      >
        <span className="collapsible-panel-logo" aria-hidden="true">
          <span className="logo-icon">{icon}</span>
          <span className="toggle-icon">
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </span>
        </span>
        <span className="collapsible-panel-titles">
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </span>
      </button>
      {open && <div className="collapsible-panel-body">{children}</div>}
    </section>
  );
}
