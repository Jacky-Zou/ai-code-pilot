import { AlertCircle, CheckCircle2, GitBranch } from "lucide-react";
import type { ToolResult } from "@/lib/api";

export interface ToolCallTimelineProps {
  toolCalls: ToolResult[];
}

function previewValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "None";
  }
  if (typeof value === "string") {
    return value;
  }

  // Tool arguments/results may be nested dictionaries from the backend.
  // JSON.stringify gives the UI a stable, inspectable preview without coupling
  // this component to every individual tool's response schema.
  try {
    return JSON.stringify(value);
  } catch {
    return "Unserializable value";
  }
}

export function ToolCallTimeline({ toolCalls }: ToolCallTimelineProps) {
  return (
    <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <GitBranch className="h-4 w-4 text-primary" aria-hidden="true" />
        Tool Calls
      </div>

      {toolCalls.length === 0 ? <p className="text-sm text-muted">No tool calls yet.</p> : null}

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
                    <dt className="font-medium text-foreground">Arguments</dt>
                    <dd className="mt-1 truncate">{previewValue(toolCall.arguments)}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">{hasError ? "Error" : "Result"}</dt>
                    <dd className="mt-1 truncate">
                      {hasError ? toolCall.error : previewValue(toolCall.result)}
                    </dd>
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
