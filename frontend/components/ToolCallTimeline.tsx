import { AlertCircle, CheckCircle2, Clock3, Loader2 } from "lucide-react";
import type { ToolResult } from "@/lib/api";
import type { Language } from "@/components/ProviderSelector";

export interface ToolCallTimelineProps {
  isRunning?: boolean;
  language?: Language;
  toolCalls: ToolResult[];
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function formatArguments(toolCall: ToolResult): string {
  const args = asRecord(toolCall.arguments);
  if (toolCall.name === "read_file") return `Read ${String(args.file_path ?? "selected file")}`;
  if (toolCall.name === "search_text") return `Search "${String(args.keyword ?? "")}"`;
  if (toolCall.name === "retrieve_code") return `Retrieve semantic context for "${String(args.query ?? "")}"`;
  if (toolCall.name === "project_tree") return `Build project tree to depth ${String(args.max_depth ?? 3)}`;
  if (toolCall.name === "find_files") return `Find files matching "${String(args.pattern ?? "")}"`;
  if (toolCall.name === "list_files") return "List project files";
  return "Run development tool";
}

function formatResult(toolCall: ToolResult): string {
  if (toolCall.error) return toolCall.error;
  const result = asRecord(toolCall.result);

  if (toolCall.name === "read_file") return `Loaded ${String(result.relative_path ?? result.file_path ?? "file")}`;
  if (toolCall.name === "search_text") return `${String(result.count ?? 0)} matches`;
  if (toolCall.name === "retrieve_code") {
    const matches = Array.isArray(result.matches) ? result.matches.length : 0;
    return `${matches} semantic snippets`;
  }
  if (toolCall.name === "project_tree") return `${String(result.count ?? 0)} tree entries`;
  if (toolCall.name === "find_files") return `${String(result.count ?? 0)} files found`;
  if (toolCall.name === "list_files") return `${String(result.count ?? 0)} files`;
  return "Completed";
}

export function ToolCallTimeline({ isRunning = false, toolCalls }: ToolCallTimelineProps) {
  const displayCalls = isRunning
    ? [
        ...toolCalls,
        {
          name: "agent_thinking",
          arguments: {},
          result: null,
          error: null
        } satisfies ToolResult
      ]
    : toolCalls;

  return (
    <div className="insight-panel-body">
      {displayCalls.length === 0 ? (
        <div className="timeline-skeleton">
          <Clock3 className="h-4 w-4" aria-hidden="true" />
          <span>Waiting for Agent activity.</span>
        </div>
      ) : null}

      <div className="agent-step-list">
        {displayCalls.map((toolCall, index) => {
          const isPending = isRunning && index === displayCalls.length - 1 && toolCall.name === "agent_thinking";
          const hasError = Boolean(toolCall.error);
          const statusLabel = isPending ? "Thinking..." : hasError ? "Error" : "Done";

          return (
            <details className="agent-step" key={`${toolCall.name}-${index}`} open={isPending || !hasError}>
              <summary>
                <span className={`step-dot ${hasError ? "error" : isPending ? "running" : "done"}`}>
                  {hasError ? (
                    <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                  ) : isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                </span>
                <span className="step-summary-title">
                  {isPending ? "Thinking through tool results" : `Tool call: ${toolCall.name}`}
                </span>
                <span className={`status-pill ${hasError ? "danger" : isPending ? "running" : "ready"}`}>
                  {statusLabel}
                </span>
              </summary>

              <dl className="step-meta">
                <div>
                  <dt>Action</dt>
                  <dd>{isPending ? "Preparing the final answer from available context." : formatArguments(toolCall)}</dd>
                </div>
                <div>
                  <dt>{hasError ? "Problem" : "Outcome"}</dt>
                  <dd>{isPending ? "Waiting for model response." : formatResult(toolCall)}</dd>
                </div>
              </dl>
            </details>
          );
        })}
      </div>
    </div>
  );
}
