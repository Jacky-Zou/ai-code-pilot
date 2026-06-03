import { AlertCircle, CheckCircle2, Clock3, GitBranch, Loader2 } from "lucide-react";
import type { ToolResult } from "@/lib/api";
import type { Language } from "@/components/ProviderSelector";

export interface ToolCallTimelineProps {
  isRunning?: boolean;
  language?: Language;
  toolCalls: ToolResult[];
}

const LABELS = {
  zh: {
    title: "执行步骤",
    subtitle: "展示 Agent 如何搜索、读取和分析代码。",
    empty: "等待 Agent 执行任务。",
    action: "动作",
    outcome: "结果",
    problem: "问题",
    done: "Done",
    running: "Running",
    error: "Error"
  },
  en: {
    title: "Agent Steps",
    subtitle: "How the Agent searches, reads, and reasons over code.",
    empty: "Waiting for Agent activity.",
    action: "Action",
    outcome: "Outcome",
    problem: "Problem",
    done: "Done",
    running: "Running",
    error: "Error"
  }
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function formatArguments(toolCall: ToolResult, language: Language): string {
  const args = asRecord(toolCall.arguments);
  const read = language === "zh" ? "读取" : "Read";
  const search = language === "zh" ? "搜索" : "Search";
  const retrieve = language === "zh" ? "语义检索" : "Retrieve";

  if (toolCall.name === "read_file") return `${read} ${String(args.file_path ?? "selected file")}`;
  if (toolCall.name === "search_text") return `${search} "${String(args.keyword ?? "")}"`;
  if (toolCall.name === "retrieve_code") return `${retrieve} "${String(args.query ?? "")}"`;
  if (toolCall.name === "project_tree") {
    return language === "zh"
      ? `生成项目结构，深度 ${String(args.max_depth ?? 3)}`
      : `Show tree depth ${String(args.max_depth ?? 3)}`;
  }
  if (toolCall.name === "find_files") {
    return language === "zh"
      ? `查找文件 "${String(args.pattern ?? "")}"`
      : `Find files matching "${String(args.pattern ?? "")}"`;
  }
  if (toolCall.name === "list_files") return language === "zh" ? "列出项目文件" : "List project files";
  return language === "zh" ? "运行开发工具" : "Run development tool";
}

function formatResult(toolCall: ToolResult, language: Language): string {
  if (toolCall.error) return toolCall.error;

  const result = asRecord(toolCall.result);
  if (toolCall.name === "read_file") {
    return language === "zh"
      ? `已加载 ${String(result.relative_path ?? result.file_path ?? "file")}`
      : `Loaded ${String(result.relative_path ?? result.file_path ?? "file")}`;
  }
  if (toolCall.name === "search_text") {
    return language === "zh" ? `${String(result.count ?? 0)} 处匹配` : `${String(result.count ?? 0)} matches`;
  }
  if (toolCall.name === "retrieve_code") {
    const matches = Array.isArray(result.matches) ? result.matches.length : 0;
    return language === "zh" ? `${matches} 个语义片段` : `${matches} semantic snippets`;
  }
  if (toolCall.name === "project_tree") {
    return language === "zh"
      ? `${String(result.count ?? 0)} 个结构条目`
      : `${String(result.count ?? 0)} tree entries`;
  }
  if (toolCall.name === "find_files") {
    return language === "zh" ? `${String(result.count ?? 0)} 个文件` : `${String(result.count ?? 0)} files found`;
  }
  if (toolCall.name === "list_files") {
    return language === "zh" ? `${String(result.count ?? 0)} 个文件` : `${String(result.count ?? 0)} files`;
  }
  return language === "zh" ? "已完成" : "Completed";
}

export function ToolCallTimeline({ isRunning = false, language = "zh", toolCalls }: ToolCallTimelineProps) {
  const labels = LABELS[language];
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
    <section className="panel-card insight-panel">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">Trace</p>
          <h2>{labels.title}</h2>
        </div>
        <GitBranch className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      <p className="panel-subtitle">{labels.subtitle}</p>

      {displayCalls.length === 0 ? (
        <div className="empty-state">
          <Clock3 className="h-4 w-4" aria-hidden="true" />
          {labels.empty}
        </div>
      ) : null}

      <div className="agent-step-list">
        {displayCalls.map((toolCall, index) => {
          const isPending = isRunning && index === displayCalls.length - 1 && toolCall.name === "agent_thinking";
          const hasError = Boolean(toolCall.error);
          const statusLabel = isPending ? labels.running : hasError ? labels.error : labels.done;

          return (
            <article className="agent-step" key={`${toolCall.name}-${index}`}>
              <div className={`step-dot ${hasError ? "error" : isPending ? "running" : "done"}`}>
                {hasError ? (
                  <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                ) : isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                )}
              </div>
              <div className="step-card">
                <div className="step-card-header">
                  <h3>{isPending ? (language === "zh" ? "综合上下文" : "Synthesizing") : toolCall.name}</h3>
                  <span className={`status-pill ${hasError ? "danger" : isPending ? "running" : "ready"}`}>
                    {statusLabel}
                  </span>
                </div>
                <dl className="step-meta">
                  <div>
                    <dt>{labels.action}</dt>
                    <dd>
                      {isPending
                        ? language === "zh"
                          ? "整理工具结果并生成最终回答"
                          : "Preparing final answer from tool results"
                        : formatArguments(toolCall, language)}
                    </dd>
                  </div>
                  <div>
                    <dt>{hasError ? labels.problem : labels.outcome}</dt>
                    <dd>
                      {isPending
                        ? language === "zh"
                          ? "等待模型返回"
                          : "Waiting for model"
                        : formatResult(toolCall, language)}
                    </dd>
                  </div>
                </dl>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
