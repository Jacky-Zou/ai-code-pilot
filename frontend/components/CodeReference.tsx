import { Braces, Search } from "lucide-react";
import type { CodeReference as CodeReferenceItem } from "@/lib/api";

export interface CodeReferenceProps {
  references: CodeReferenceItem[];
}

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

  // Scores may come from semantic retrieval as raw similarity values.
  // Showing two decimals keeps the UI readable while preserving ranking signal.
  return score.toFixed(2);
}

export function CodeReference({ references }: CodeReferenceProps) {
  return (
    <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <Search className="h-4 w-4 text-accent" aria-hidden="true" />
        Code Evidence
      </div>

      <p className="mb-3 text-xs leading-5 text-muted">
        Files and snippets the Agent used as evidence for the latest answer.
      </p>

      {references.length === 0 ? <p className="text-sm text-muted">No code evidence yet.</p> : null}

      <div className="space-y-3">
        {references.map((reference, index) => {
          const score = formatScore(reference.score);

          return (
            <div className="rounded-md border border-border p-3" key={`${reference.file_path}-${index}`}>
              <div className="mb-2 flex items-start gap-2 text-sm font-medium">
                <Braces className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="truncate">{formatLocation(reference)}</div>
                  {score ? <div className="mt-1 text-xs text-muted">score {score}</div> : null}
                </div>
              </div>

              {/* Snippets are optional because some tools only return a location.
                  Keep a fallback so the right rail still communicates why the item exists. */}
              <pre className="max-h-32 overflow-auto whitespace-pre-wrap rounded-md bg-background p-2 text-xs leading-5 text-muted">
                {reference.snippet ?? "Referenced by Agent"}
              </pre>
            </div>
          );
        })}
      </div>
    </section>
  );
}
