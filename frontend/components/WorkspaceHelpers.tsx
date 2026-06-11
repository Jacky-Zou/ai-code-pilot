"use client";

import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import type { WorkspaceNode } from "@/hooks/useWorkspaceImport";

export function MarkdownMessage({ content }: { content: string }) {
  return (
    <ReactMarkdown rehypePlugins={[rehypeHighlight]} remarkPlugins={[remarkGfm]}>
      {content}
    </ReactMarkdown>
  );
}

export function WorkspaceTree({ nodes }: { nodes: WorkspaceNode[] }) {
  if (!nodes.length) return null;
  return (
    <ul className="workspace-tree mt-3">
      {nodes.map((node) => (
        <li key={node.path}>
          <span className={`tree-node ${node.type}`}>{node.name}</span>
          {node.children ? <WorkspaceTree nodes={node.children} /> : null}
        </li>
      ))}
    </ul>
  );
}

export function ModelCenterIcon() {
  return (
    <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="16">
      <path
        d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
