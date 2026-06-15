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
  // CPU/芯片风格图标，契合"模型引擎"主题
  return (
    <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24" width="16">
      <rect x="6" y="6" width="12" height="12" rx="2" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="9.5" y="9.5" width="5" height="5" rx="1" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
