"use client";

import { Database, FileCode2, FolderOpen, Loader2 } from "lucide-react";
import type { ProjectIndexResponse } from "@/lib/api";
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
  // Using unknown ref type to be compatible across React 18/19 ref shapes
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
      <ProviderSelector onChange={onSelectionChange} value={selection} />
      <section className="panel-card workspace-panel">
        <div className="panel-heading">
          <div>
            <h2>Workspace</h2>
            <p className="panel-description">Import code and index a backend-visible path.</p>
          </div>
          <FolderOpen className="h-5 w-5 text-folder" aria-hidden="true" />
        </div>
        <p className="field-label">Local Import</p>
        <div className="workspace-actions">
          <label className="secondary-button file-picker-button">
            <FolderOpen className="h-4 w-4" /> Open folder
            <input multiple onChange={onFolderChange} ref={folderInputRef} type="file"
              {...({ directory: "", webkitdirectory: "" } as Record<string, string>)} />
          </label>
          <label className="secondary-button file-picker-button">
            <FileCode2 className="h-4 w-4" /> Open file
            <input accept={fileAccept} onChange={onFileChange} ref={fileInputRef} type="file" />
          </label>
        </div>
        <label className="field-label" htmlFor="project-path">Backend Path</label>
        <input className="field-input" id="project-path"
          onChange={(e) => onProjectPathChange(e.target.value)} value={projectPath} />
        <p className="workspace-hint">
          Browser imports power local preview only. RAG indexing requires a path visible to the backend.
        </p>
        <button className="primary-button w-full"
          disabled={isIndexing || !projectPath.trim()} onClick={onIndexProject} type="button">
          {isIndexing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
          {isIndexing ? "Indexing…" : "Index Workspace"}
        </button>
        {indexStats && (
          <div className="metric-strip mt-3">
            <span>{indexStats.indexed_files} files</span>
            <span>{indexStats.chunks} chunks</span>
          </div>
        )}
        {indexError && <div className="error-box mt-3">{indexError}</div>}
        {importError && <div className="error-box mt-3">{importError}</div>}
        <WorkspaceTree nodes={workspaceTree} />
      </section>
    </>
  );
}
