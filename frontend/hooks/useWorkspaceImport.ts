"use client";

import { useCallback, useRef, useState } from "react";
import { indexProject, type ProjectIndexResponse } from "@/lib/api";

export type WorkspaceNode = {
  children?: WorkspaceNode[];
  name: string;
  path: string;
  type: "file" | "folder";
};

export type ProjectSummary = {
  architecture: string[];
  chunks: number;
  description: string;
  files: number;
  kind: "folder" | "file";
  languages: Array<{ label: string; percent: number; value: number }>;
  lineCount: number;
  name: string;
  path?: string;
  purpose: string;
  sizeBytes: number;
  structure: string[];
  techStack: string[];
};

const SUPPORTED_EXTENSIONS = new Set([
  ".c", ".cpp", ".css", ".go", ".html", ".java", ".js", ".json", ".jsx",
  ".md", ".py", ".rs", ".scss", ".sh", ".ts", ".tsx", ".txt", ".yaml", ".yml",
]);

const FILE_ACCEPT = Array.from(SUPPORTED_EXTENSIONS).join(",");

function isSupportedCodeFile(name: string): boolean {
  const dot = name.lastIndexOf(".");
  if (dot === -1) return false;
  return SUPPORTED_EXTENSIONS.has(name.slice(dot).toLowerCase());
}

function buildWorkspaceTree(files: FileList): WorkspaceNode[] {
  const root: WorkspaceNode[] = [];
  const dirMap = new Map<string, WorkspaceNode>();

  for (const file of Array.from(files)) {
    const parts = (file.webkitRelativePath || file.name).split("/");
    let current = root;
    let pathSoFar = "";

    for (let i = 0; i < parts.length - 1; i++) {
      pathSoFar = pathSoFar ? `${pathSoFar}/${parts[i]}` : parts[i];
      if (!dirMap.has(pathSoFar)) {
        const node: WorkspaceNode = {
          name: parts[i],
          path: pathSoFar,
          type: "folder",
          children: [],
        };
        dirMap.set(pathSoFar, node);
        current.push(node);
      }
      current = dirMap.get(pathSoFar)!.children!;
    }

    if (isSupportedCodeFile(parts[parts.length - 1])) {
      current.push({
        name: parts[parts.length - 1],
        path: file.webkitRelativePath || file.name,
        type: "file",
      });
    }
  }
  return root;
}

async function buildImportSummary(
  files: FileList,
  kind: "folder" | "file",
  indexStats?: ProjectIndexResponse | null
): Promise<ProjectSummary> {
  const LANG_MAP: Record<string, string> = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".css": "CSS", ".scss": "CSS",
    ".html": "HTML", ".md": "Markdown", ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML", ".sh": "Shell",
  };
  const TECH_PATTERNS: Array<[RegExp, string]> = [
    [/requirements\.txt|setup\.py|pyproject\.toml/, "Python"],
    [/package\.json/, "Node.js"],
    [/\.(tsx|jsx)$/, "React"],
    [/next\.config/, "Next.js"],
    [/tailwind\.config/, "Tailwind CSS"],
    [/Dockerfile|docker-compose/, "Docker"],
    [/executor|planner|agent/, "LLM Agent"],
    [/retriever|vector_store|embeddings/, "RAG"],
  ];

  const langCounts: Record<string, number> = {};
  let totalLines = 0;
  let totalBytes = 0;
  const techSet = new Set<string>();
  const structureSet = new Set<string>();
  const archSet = new Set<string>();

  await Promise.all(
    Array.from(files).map(async (file) => {
      const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
      if (LANG_MAP[ext]) langCounts[LANG_MAP[ext]] = (langCounts[LANG_MAP[ext]] ?? 0) + 1;
      totalBytes += file.size;

      const path = file.webkitRelativePath || file.name;
      for (const [pattern, tech] of TECH_PATTERNS) {
        if (pattern.test(path) || pattern.test(file.name)) techSet.add(tech);
      }

      const topDir = path.split("/")[0];
      if (path.includes("/")) structureSet.add(topDir);

      if (file.size < 200_000) {
        try {
          const text = await file.text();
          totalLines += text.split("\n").length;
          if (text.includes("FastAPI") || text.includes("@app.")) archSet.add("FastAPI backend");
          if (text.includes("React") || text.includes("useState")) archSet.add("React frontend");
          if (text.includes("SQLModel") || text.includes("sqlalchemy")) archSet.add("SQLModel ORM");
          if (text.includes("Chroma") || text.includes("chromadb")) archSet.add("ChromaDB vector store");
        } catch {
          // Skip unreadable files
        }
      }
    })
  );

  const totalFiles = Array.from(files).filter((f) => isSupportedCodeFile(f.name)).length;
  const langEntries = Object.entries(langCounts).sort((a, b) => b[1] - a[1]);
  const totalLangFiles = langEntries.reduce((s, [, c]) => s + c, 0);

  return {
    name: kind === "folder"
      ? (files[0]?.webkitRelativePath?.split("/")[0] ?? "Project")
      : files[0]?.name ?? "File",
    kind,
    files: totalFiles,
    sizeBytes: totalBytes,
    lineCount: totalLines,
    techStack: Array.from(techSet),
    architecture: Array.from(archSet),
    structure: Array.from(structureSet).slice(0, 8),
    languages: langEntries.map(([label, count]) => ({
      label,
      value: count,
      percent: totalLangFiles > 0 ? Math.round((count / totalLangFiles) * 100) : 0,
    })),
    chunks: indexStats?.chunks ?? 0,
    description: `${totalFiles} files · ${(totalBytes / 1024).toFixed(1)} KB`,
    purpose: "",
  };
}

/**
 * Manages workspace file import, tree building, and project indexing.
 */
export function useWorkspaceImport(baseUrl?: string) {
  const [workspaceTree, setWorkspaceTree] = useState<WorkspaceNode[]>([]);
  const [projectSummary, setProjectSummary] = useState<ProjectSummary | null>(null);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStats, setIndexStats] = useState<ProjectIndexResponse | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFolderChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files?.length) return;
      setImportError(null);
      try {
        const tree = buildWorkspaceTree(files);
        setWorkspaceTree(tree);
        const summary = await buildImportSummary(files, "folder", indexStats);
        setProjectSummary(summary);
        setIsSummaryOpen(true);
      } catch (err) {
        setImportError(err instanceof Error ? err.message : "Import failed");
      }
      if (event.target) event.target.value = "";
    },
    [indexStats]
  );

  const handleSingleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files?.length) return;
      setImportError(null);
      try {
        const tree = buildWorkspaceTree(files);
        setWorkspaceTree(tree);
        const summary = await buildImportSummary(files, "file", indexStats);
        setProjectSummary(summary);
        setIsSummaryOpen(true);
      } catch (err) {
        setImportError(err instanceof Error ? err.message : "Import failed");
      }
      if (event.target) event.target.value = "";
    },
    [indexStats]
  );

  const handleIndexProject = useCallback(
    async (projectPath: string) => {
      if (!projectPath.trim()) return;
      setIsIndexing(true);
      setIndexError(null);
      try {
        const stats = await indexProject({ project_path: projectPath }, { baseUrl });
        setIndexStats(stats);
        if (projectSummary) {
          setProjectSummary({ ...projectSummary, chunks: stats.chunks });
        }
      } catch (err) {
        setIndexError(err instanceof Error ? err.message : "Indexing failed");
      } finally {
        setIsIndexing(false);
      }
    },
    [baseUrl, projectSummary]
  );

  return {
    workspaceTree,
    projectSummary,
    isSummaryOpen,
    setIsSummaryOpen,
    importError,
    isIndexing,
    indexStats,
    indexError,
    folderInputRef,
    fileInputRef,
    handleFolderChange,
    handleSingleFileChange,
    handleIndexProject,
    FILE_ACCEPT,
  };
}
