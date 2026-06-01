import { AlertCircle, CheckCircle2, GitBranch } from "lucide-react";
import type { ToolResult } from "@/lib/api";

export interface ToolCallTimelineProps {
  toolCalls: ToolResult[];
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function formatArguments(toolCall: ToolResult): string {
  const args = asRecord(toolCall.arguments);
  if (toolCall.name === "read_file") {
    return `Read ${String(args.file_path ?? "selected file")}`;
  }
  if (toolCall.name === "search_text") {
    return `Search "${String(args.keyword ?? "")}"`;
  }
  if (toolCall.name === "retrieve_code") {
    return `Retrieve "${String(args.query ?? "")}"`;
  }
  if (toolCall.name === "project_tree") {
    return `Show tree depth ${String(args.max_depth ?? 3)}`;
  }
  if (toolCall.name === "find_files") {
    return `Find files matching "${String(args.pattern ?? "")}"`;
  }
  if (toolCall.name === "list_files") {
    return "List project files";
  }
  return "Run development tool";
}

function formatResult(toolCall: ToolResult): string {
  if (toolCall.error) {
    return toolCall.error;
  }

  const result = asRecord(toolCall.result);
  if (toolCall.name === "read_file") {
    return `Loaded ${String(result.relative_path ?? result.file_path ?? "file")}`;
  }
  if (toolCall.name === "search_text") {
    return `${String(result.count ?? 0)} matches`;
  }
  if (toolCall.name === "retrieve_code") {
    const matches = Array.isArray(result.matches) ? result.matches.length : 0;
    return `${matches} semantic snippets`;
  }
  if (toolCall.name === "project_tree") {
    return `${String(result.count ?? 0)} tree entries`;
  }
  if (toolCall.name === "find_files") {
    return `${String(result.count ?? 0)} files found`;
  }
  if (toolCall.name === "list_files") {
    return `${String(result.count ?? 0)} files`;
  }
  return "Completed";
}

export function ToolCallTimeline({ toolCalls }: ToolCallTimelineProps) {
  return (
    <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <GitBranch className="h-4 w-4 text-primary" aria-hidden="true" />
        Agent Steps
      </div>

      <p className="mb-3 text-xs leading-5 text-muted">
        Tools the Agent used to inspect files, search code, or retrieve semantic context.
      </p>

      {toolCalls.length === 0 ? <p className="text-sm text-muted">No tool activity yet.</p> : null}

      <div className="space-y-3">
        {toolCalls.map((toolCall, index) => {
          const hasError = Boolean(toolCall.error);
          const statusLabel = hasError ? "Error" : "Done";

          return (
            <div className="relative pl-7" key={`${toolCall.name}-${index}`}>
              {index < toolCalls.length - 1 ? (
                <span className="absolute left-[7px] top-7 h-[calc(100%-8px)] w-px bg-border" />
              ) : null}
              <span
                className={`absolute left-0 top-1 flex h-4 w-4 items-center justify-center rounded-full ${
                  hasError ? "bg-[#fff4f4] text-warning" : "bg-[#effaf8] text-accent"
                }`}
              >
                {hasError ? (
                  <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                )}
              </span>

              <div className="rounded-md border border-border p-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="min-w-0 truncate text-sm font-medium">{toolCall.name}</span>
                  <span
                    className={`shrink-0 rounded-md px-2 py-1 text-xs ${
                      hasError ? "bg-[#fff4f4] text-warning" : "bg-[#effaf8] text-accent"
                    }`}
                  >
                    {statusLabel}
                  </span>
                </div>

                {/* Keep the detailed values compact: the right rail is for scanning,
                    while full tool/result expansion can be added later if needed. */}
                <dl className="space-y-2 text-xs text-muted">
                  <div>
                    <dt className="font-medium text-foreground">Action</dt>
                    <dd className="mt-1">{formatArguments(toolCall)}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">{hasError ? "Problem" : "Outcome"}</dt>
                    <dd className="mt-1">{formatResult(toolCall)}</dd>
                  </div>
                </dl>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
