import { Braces, Copy, Search } from "lucide-react";
import type { CodeReference as CodeReferenceItem } from "@/lib/api";
import type { Language } from "@/components/ProviderSelector";

export interface CodeReferenceProps {
  language?: Language;
  references: CodeReferenceItem[];
}

function formatLocation(reference: CodeReferenceItem): string {
  if (reference.line_number === null || reference.line_number === undefined) return reference.file_path;
  return `${reference.file_path}:${reference.line_number}`;
}

function formatScore(score: number | null): string | null {
  if (score === null) return null;
  return score.toFixed(2);
}

function excerptSnippet(snippet: string | null): string {
  if (!snippet) return "Referenced by Agent";
  const lines = snippet.split(/\r?\n/).filter(Boolean);
  return lines.slice(0, 8).join("\n");
}

export function CodeReference({ references }: CodeReferenceProps) {
  return (
    <section className="panel-card insight-panel">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">Evidence</p>
          <h2>Code Evidence</h2>
        </div>
        <Search className="h-5 w-5 text-accent" aria-hidden="true" />
      </div>

      <p className="panel-subtitle">Files, line numbers, and snippets used by the Agent.</p>

      {references.length === 0 ? (
        <div className="timeline-skeleton">
          <Braces className="h-4 w-4" aria-hidden="true" />
          <span>No code evidence yet.</span>
        </div>
      ) : null}

      <div className="code-evidence-list">
        {references.map((reference, index) => {
          const score = formatScore(reference.score);
          const snippet = excerptSnippet(reference.snippet);
          const location = formatLocation(reference);

          return (
            <article className="code-evidence-card" key={`${reference.file_path}-${index}`}>
              <div className="evidence-header">
                <div className="min-w-0 flex-1">
                  <div className="evidence-path">
                    <Braces className="h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
                    <span>{location}</span>
                  </div>
                  {score ? <div className="mt-1 text-xs text-muted">score {score}</div> : null}
                </div>
                <button
                  className="icon-button compact"
                  onClick={() => navigator.clipboard?.writeText(location)}
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
