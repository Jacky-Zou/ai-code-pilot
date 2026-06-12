"use client";

import { Database, FileCode2, FolderOpen } from "lucide-react";
import type { ProjectIndexResponse } from "@/lib/api";
import { CollapsiblePanel } from "@/components/CollapsiblePanel";
import { ProviderSelector, type ProviderSelection } from "@/components/ProviderSelector";
import { WorkspaceTree } from "@/components/WorkspaceHelpers";
import type { WorkspaceNode } from "@/hooks/useWorkspaceImport";

interface Props {
  selection: ProviderSelection;
  onSelectionChange: (s: ProviderSelection) => void;
  projectPath: string;
  onProjectPathChange: (p: string) => void;
  onIndexProject: () => void;
  isIndexing: boolean;
  indexStats: ProjectIndexResponse | null;
  indexError: string | null;
  importError: string | null;
  workspaceTree: WorkspaceNode[];
  folderInputRef: { current: HTMLInputElement | null };
  fileInputRef: { current: HTMLInputElement | null };
  onFolderChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  fileAccept: string;
}

export function WorkspacePanel({
  selection, onSelectionChange, projectPath, onProjectPathChange,
  onIndexProject, isIndexing, indexStats, indexError, importError,
  workspaceTree, folderInputRef, fileInputRef, onFolderChange, onFileChange, fileAccept,
}: Props) {
  return (
    <>
      <CollapsiblePanel
        title="Model Center"
        description="Provider, API key, model."
        icon={<ModelCenterSvg />}
      >
        <ProviderSelector onChange={onSelectionChange} value={selection} />
      </CollapsiblePanel>

      <CollapsiblePanel
        title="Workspace"
        description="Open folder or file to set context."
        icon={<FolderOpen className="h-4 w-4" />}
      >
        {/* Open folder / file — IDE-like workspace selection */}
        <div className="workspace-actions" style={{ marginBottom: 8 }}>
          <label className="secondary-button file-picker-button" title="Open folder as workspace">
            <FolderOpen className="h-4 w-4" /> Open Folder
            <input multiple onChange={onFolderChange} ref={folderInputRef} type="file"
              {...({ directory: "", webkitdirectory: "" } as Record<string, string>)} />
          </label>
          <label className="secondary-button file-picker-button" title="Open single file">
            <FileCode2 className="h-4 w-4" /> Open File
            <input accept={fileAccept} onChange={onFileChange} ref={fileInputRef} type="file" />
          </label>
        </div>

        {/* Current workspace path (auto-filled or manual) */}
        <label className="field-label" htmlFor="project-path">Workspace Path</label>
        <input
          className="field-input"
          id="project-path"
          onChange={(e) => onProjectPathChange(e.target.value)}
          placeholder="e.g. D:\code\my_project"
          value={projectPath}
        />
        <p className="workspace-hint" style={{ marginTop: 4 }}>
          Path used by the AI to index and search your code. Must be visible to the backend server.
        </p>

        <button
          className="primary-button w-full"
          disabled={isIndexing || !projectPath.trim()}
          onClick={onIndexProject}
          style={{ marginTop: 8, width: "100%" }}
          type="button"
        >
          <Database className="h-4 w-4" />
          {isIndexing ? "Indexing…" : "Index Workspace"}
        </button>

        {indexStats && (
          <div className="metric-strip" style={{ marginTop: 8 }}>
            <span>{indexStats.indexed_files} files</span>
            <span>{indexStats.chunks} chunks</span>
          </div>
        )}
        {indexError && <div className="error-box" style={{ marginTop: 8 }}>{indexError}</div>}
        {importError && <div className="error-box" style={{ marginTop: 8 }}>{importError}</div>}
        {workspaceTree.length > 0 && <WorkspaceTree nodes={workspaceTree} />}
      </CollapsiblePanel>
    </>
  );
}

function ModelCenterSvg() {
  return (
    <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="16">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
