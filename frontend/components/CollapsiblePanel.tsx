"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  icon: ReactNode;
  /** "left" rail → 标题在前 logo 在后；"right" rail → logo 在前标题在后（镜像）。 */
  side?: "left" | "right";
  defaultOpen?: boolean;
  children: ReactNode;
}

/**
 * 可折叠面板。logo 既是图标也是折叠/展开指示：
 * - 默认仅显示 logo 内的图标（无背景）。
 * - 鼠标移入整行 header 时，logo 浮现蓝色背景，图标淡出、折叠/展开箭头淡入。
 * 左右栏目通过 side 实现镜像对称布局，效果完全一致。
 */
export function CollapsiblePanel({
  title,
  description,
  icon,
  side = "left",
  defaultOpen = false,
  children,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);

  const logo = (
    <span className="collapsible-panel-logo" aria-hidden="true">
      <span className="logo-icon">{icon}</span>
      <span className="toggle-icon">
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </span>
    </span>
  );

  const titles = (
    <span className="collapsible-panel-titles">
      <h3>{title}</h3>
      {description && <p>{description}</p>}
    </span>
  );

  return (
    <section className={`collapsible-panel side-${side}`}>
      <button
        className="collapsible-panel-header"
        onClick={() => setOpen((o) => !o)}
        type="button"
        aria-expanded={open}
      >
        {side === "right" ? (
          <>
            {logo}
            {titles}
          </>
        ) : (
          <>
            {titles}
            {logo}
          </>
        )}
      </button>
      {open && <div className="collapsible-panel-body">{children}</div>}
    </section>
  );
}
