import re
from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool

_LOG_LEVEL_PATTERN = re.compile(r"\b(CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|TRACE)\b", re.IGNORECASE)
_EXCEPTION_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b")
_STACK_FRAME_PATTERN = re.compile(r'^\s*File "([^"]+)", line (\d+), in (.+)$')
_TRACEBACK_START = "traceback (most recent call last):"
_NOISY_LINE_LIMIT = 2000


class AnalyzeLogArgs(BaseModel):
    log_text: str = Field(min_length=1)
    max_issues: int = Field(default=10, ge=1, le=50)


class AnalyzeLogTool(BaseTool):
    name = "analyze_log"
    description = "Analyze application logs and return severity counts, exception hints, stack traces, and debugging suggestions."
    args_schema = AnalyzeLogArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, AnalyzeLogArgs)

        lines = args.log_text.splitlines()
        level_counts = self._count_levels(lines)
        issue_lines = self._collect_issue_lines(lines, max_issues=args.max_issues)
        exceptions = self._collect_exceptions(lines, max_issues=args.max_issues)
        stack_traces = self._collect_stack_traces(lines, max_issues=args.max_issues)
        recommendations = self._build_recommendations(level_counts, exceptions, stack_traces)

        return {
            "line_count": len(lines),
            "level_counts": dict(level_counts),
            "issue_count": len(issue_lines),
            "issues": issue_lines,
            "exceptions": exceptions,
            "stack_traces": stack_traces,
            "recommendations": recommendations,
            "summary": self._build_summary(level_counts, exceptions, stack_traces),
        }

    def _count_levels(self, lines: list[str]) -> Counter[str]:
        counts: Counter[str] = Counter()
        for line in lines:
            match = _LOG_LEVEL_PATTERN.search(line)
            if not match:
                continue
            level = match.group(1).upper()
            # Normalize the common WARN alias so consumers get one stable key.
            counts["WARNING" if level == "WARN" else level] += 1
        return counts

    def _collect_issue_lines(self, lines: list[str], max_issues: int) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            level_match = _LOG_LEVEL_PATTERN.search(line)
            exception_match = _EXCEPTION_PATTERN.search(line)
            has_traceback = _TRACEBACK_START in line.lower()
            is_issue_level = bool(level_match and level_match.group(1).upper() in {"CRITICAL", "FATAL", "ERROR", "WARN", "WARNING"})

            if not (is_issue_level or exception_match or has_traceback):
                continue

            issues.append(
                {
                    "line_number": line_number,
                    "level": self._normalized_level(level_match.group(1)) if level_match else None,
                    "exception": exception_match.group(1) if exception_match else None,
                    "message": self._compact_line(line),
                }
            )
            if len(issues) >= max_issues:
                break
        return issues

    def _collect_exceptions(self, lines: list[str], max_issues: int) -> list[dict[str, Any]]:
        exceptions: list[dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        for line_number, line in enumerate(lines, start=1):
            for match in _EXCEPTION_PATTERN.finditer(line):
                key = (match.group(1), line_number)
                if key in seen:
                    continue
                seen.add(key)
                exceptions.append(
                    {
                        "type": match.group(1),
                        "line_number": line_number,
                        "message": self._compact_line(line),
                    }
                )
                if len(exceptions) >= max_issues:
                    return exceptions
        return exceptions

    def _collect_stack_traces(self, lines: list[str], max_issues: int) -> list[dict[str, Any]]:
        traces: list[dict[str, Any]] = []
        index = 0
        while index < len(lines) and len(traces) < max_issues:
            if _TRACEBACK_START not in lines[index].lower():
                index += 1
                continue

            start_line = index + 1
            frames: list[dict[str, Any]] = []
            exception_type: str | None = None
            exception_message: str | None = None
            index += 1

            # A Python traceback alternates stack frames and source lines until
            # the final exception line. We walk that block once and keep only the
            # structured frame metadata the Agent can safely summarize.
            while index < len(lines):
                current = lines[index]
                frame_match = _STACK_FRAME_PATTERN.match(current)
                if frame_match:
                    frames.append(
                        {
                            "file_path": frame_match.group(1),
                            "line_number": int(frame_match.group(2)),
                            "function": frame_match.group(3).strip(),
                        }
                    )
                    index += 1
                    continue

                exception_match = _EXCEPTION_PATTERN.search(current)
                if exception_match:
                    exception_type = exception_match.group(1)
                    exception_message = self._compact_line(current)
                    index += 1
                    break

                # Blank lines normally terminate the traceback block in mixed
                # application logs. Non-frame source-code lines are skipped so
                # they do not break extraction before the exception line appears.
                if not current.strip():
                    index += 1
                    break
                index += 1

            traces.append(
                {
                    "start_line": start_line,
                    "exception_type": exception_type,
                    "exception_message": exception_message,
                    "frames": frames[-5:],
                }
            )
        return traces

    def _build_recommendations(
        self,
        level_counts: Counter[str],
        exceptions: list[dict[str, Any]],
        stack_traces: list[dict[str, Any]],
    ) -> list[str]:
        recommendations: list[str] = []
        if level_counts.get("CRITICAL", 0) or level_counts.get("FATAL", 0):
            recommendations.append("Prioritize CRITICAL/FATAL entries first; they usually indicate service-impacting failures.")
        if level_counts.get("ERROR", 0):
            recommendations.append("Inspect the first ERROR and the nearest stack trace before later cascading errors.")
        if stack_traces:
            recommendations.append("Use the deepest stack frame from the latest traceback as the first code location to inspect.")
        if any(item["type"] in {"KeyError", "IndexError", "TypeError", "ValueError"} for item in exceptions):
            recommendations.append("Validate input shape and boundary checks around the reported exception line.")
        if not recommendations:
            recommendations.append("No obvious error pattern was found; review timestamps and surrounding INFO/WARNING lines for context.")
        return recommendations

    def _build_summary(
        self,
        level_counts: Counter[str],
        exceptions: list[dict[str, Any]],
        stack_traces: list[dict[str, Any]],
    ) -> str:
        highest = self._highest_level(level_counts)
        exception_names = sorted({str(item["type"]) for item in exceptions})
        parts = [f"Highest severity: {highest}"]
        if exception_names:
            parts.append("Exceptions: " + ", ".join(exception_names[:5]))
        if stack_traces:
            parts.append(f"Stack traces: {len(stack_traces)}")
        return "; ".join(parts)

    def _highest_level(self, level_counts: Counter[str]) -> str:
        for level in ("FATAL", "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"):
            if level_counts.get(level, 0):
                return level
        return "UNKNOWN"

    def _normalized_level(self, level: str) -> str:
        normalized = level.upper()
        return "WARNING" if normalized == "WARN" else normalized

    def _compact_line(self, line: str) -> str:
        stripped = line.strip()
        if len(stripped) <= _NOISY_LINE_LIMIT:
            return stripped
        return stripped[:_NOISY_LINE_LIMIT] + "...[truncated]"
