"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  icon: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
}

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
            <ChevronDown className={`h-3.5 w-3.5 ${open ? "rotate-180" : ""}`} style={{ transition: "transform 200ms ease" }} />
          </span>
        </span>
        <span className="collapsible-panel-titles">
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </span>
        <ChevronDown className={`collapsible-panel-chevron ${open ? "open" : ""}`} style={{ height: 14, width: 14 }} aria-hidden="true" />
      </button>
      {open && <div className="collapsible-panel-body">{children}</div>}
    </section>
  );
}
