from app.tools.log_tools import AnalyzeLogTool


def test_analyze_log_counts_levels_and_issue_lines() -> None:
    log_text = "\n".join(
        [
            "2026-05-29 10:00:00 INFO server started",
            "2026-05-29 10:00:01 WARN slow request",
            "2026-05-29 10:00:02 ERROR request failed: ValueError invalid id",
        ]
    )

    result = AnalyzeLogTool().run(log_text=log_text)

    assert result["line_count"] == 3
    assert result["level_counts"] == {"INFO": 1, "WARNING": 1, "ERROR": 1}
    assert result["issue_count"] == 2
    assert result["issues"][0]["level"] == "WARNING"
    assert result["exceptions"][0]["type"] == "ValueError"
    assert "Highest severity: ERROR" in result["summary"]


def test_analyze_log_extracts_python_traceback_frames() -> None:
    log_text = "\n".join(
        [
            "ERROR worker crashed",
            "Traceback (most recent call last):",
            '  File "backend/app/main.py", line 12, in run',
            "    raise RuntimeError('boom')",
            "RuntimeError: boom",
        ]
    )

    result = AnalyzeLogTool().run(log_text=log_text)

    assert result["stack_traces"][0]["start_line"] == 2
    assert result["stack_traces"][0]["exception_type"] == "RuntimeError"
    assert result["stack_traces"][0]["frames"] == [
        {"file_path": "backend/app/main.py", "line_number": 12, "function": "run"}
    ]
    assert any("deepest stack frame" in item for item in result["recommendations"])


def test_analyze_log_limits_issue_results() -> None:
    log_text = "\n".join(f"ERROR failure {index}" for index in range(20))

    result = AnalyzeLogTool().run(log_text=log_text, max_issues=3)

    assert result["level_counts"] == {"ERROR": 20}
    assert len(result["issues"]) == 3


def test_analyze_log_requires_non_empty_text() -> None:
    try:
        AnalyzeLogTool().run(log_text="")
    except Exception as exc:
        assert "log_text" in str(exc)
    else:
        raise AssertionError("AnalyzeLogTool should reject empty log text")
