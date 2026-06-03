import { Braces, Copy, Search } from "lucide-react";
import type { CodeReference as CodeReferenceItem } from "@/lib/api";
import type { Language } from "@/components/ProviderSelector";

export interface CodeReferenceProps {
  language?: Language;
  references: CodeReferenceItem[];
}

const LABELS = {
  zh: {
    title: "代码证据",
    subtitle: "Agent 回答所依据的核心文件、行号和片段。",
    empty: "还没有代码证据。",
    referenced: "Agent 引用片段",
    score: "相关度"
  },
  en: {
    title: "Code Evidence",
    subtitle: "Files, line numbers, and snippets used by the Agent.",
    empty: "No code evidence yet.",
    referenced: "Referenced by Agent",
    score: "score"
  }
};

function formatLocation(reference: CodeReferenceItem): string {
  if (reference.line_number === null || reference.line_number === undefined) {
    return reference.file_path;
  }
  return `${reference.file_path}:${reference.line_number}`;
}

function formatScore(score: number | null): string | null {
  if (score === null) {
    return null;
  }
  return score.toFixed(2);
}

function excerptSnippet(snippet: string | null): string {
  if (!snippet) {
    return "";
  }
  const lines = snippet.split(/\r?\n/).filter(Boolean);
  return lines.slice(0, 8).join("\n");
}

export function CodeReference({ language = "zh", references }: CodeReferenceProps) {
  const labels = LABELS[language];

  return (
    <section className="panel-card insight-panel">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">Evidence</p>
          <h2>{labels.title}</h2>
        </div>
        <Search className="h-5 w-5 text-accent" aria-hidden="true" />
      </div>

      <p className="mb-4 text-xs leading-5 text-muted">{labels.subtitle}</p>

      {references.length === 0 ? (
        <div className="empty-state">
          <Braces className="h-4 w-4" aria-hidden="true" />
          {labels.empty}
        </div>
      ) : null}

      <div className="code-evidence-list">
        {references.map((reference, index) => {
          const score = formatScore(reference.score);
          const snippet = excerptSnippet(reference.snippet) || labels.referenced;

          return (
            <article className="code-evidence-card" key={`${reference.file_path}-${index}`}>
              <div className="mb-2 flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Braces className="h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
                    <span className="min-w-0 truncate font-mono text-xs font-semibold">
                      {formatLocation(reference)}
                    </span>
                  </div>
                  {score ? (
                    <div className="mt-1 text-xs text-muted">
                      {labels.score} {score}
                    </div>
                  ) : null}
                </div>
                <button
                  className="icon-button h-7 w-7"
                  onClick={() => navigator.clipboard?.writeText(formatLocation(reference))}
                  title="Copy path"
                  type="button"
                >
                  <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </div>

              <pre className="code-snippet">
                <code>{snippet}</code>
              </pre>
            </article>
          );
        })}
      </div>
    </section>
  );
}
