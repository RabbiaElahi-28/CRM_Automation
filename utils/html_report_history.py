"""Unique per-run pytest-html report paths, history index, and terminal summary."""

from __future__ import annotations

import platform
import re
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("reports/html_reports")
LEGACY_REPORT_PATH = Path("reports/html_report/report.html")
PENDING_REPORT_PATH = Path("reports/html_reports/_automation_pending.html")
HISTORY_MD = REPORTS_DIR / "report_history.md"
HISTORY_HTML = REPORTS_DIR / "index.html"

MARKER_SUITE_NAMES: dict[str, str] = {
    "smoke": "smoke_suite",
    "regression": "regression_suite",
    "flow_orchestrator": "flow_orchestrator",
    "fe_agent": "fe_agent_suite",
    "be_agent": "be_agent_suite",
    "module_smoke": "module_smoke_suite",
}

_RUN_SUFFIX = re.compile(r"_run(\d+)\.html$", re.IGNORECASE)


def _normalize_markexpr(markexpr: str) -> str:
    return " ".join(markexpr.strip().lower().split())


def _resolve_marker_suite_name(markexpr: str) -> str | None:
    normalized = _normalize_markexpr(markexpr)
    if not normalized:
        return None

    if normalized in MARKER_SUITE_NAMES:
        return MARKER_SUITE_NAMES[normalized]

    for marker, suite_name in MARKER_SUITE_NAMES.items():
        if re.search(rf"(?:^|\s){re.escape(marker)}(?:\s|$)", normalized):
            return suite_name

    return None


def _collect_cli_targets(config) -> list[str]:
    file_or_dir = getattr(config.option, "file_or_dir", None) or []
    return [str(item) for item in file_or_dir if not str(item).startswith("-")]


def _stem_from_path(path_str: str) -> str | None:
    path = Path(path_str.replace("\\", "/"))
    if path.suffix == ".py":
        return path.stem
    return None


def _test_name_from_nodeid(nodeid: str) -> str:
    test_name = nodeid.split("::")[-1]
    return test_name.split("[", maxsplit=1)[0]


def resolve_report_base_name(config) -> str:
    """Derive a meaningful report basename from pytest invocation."""
    markexpr = getattr(config.option, "markexpr", None) or ""
    marker_suite = _resolve_marker_suite_name(markexpr)
    if marker_suite:
        return marker_suite

    targets = _collect_cli_targets(config)
    if len(targets) == 1:
        target = targets[0].replace("\\", "/")
        if "::" in target:
            file_part, node_part = target.split("::", maxsplit=1)
            file_stem = _stem_from_path(file_part)
            if node_part and not node_part.endswith(".py"):
                return _test_name_from_nodeid(target)
            if file_stem:
                return file_stem
        stem = _stem_from_path(target)
        if stem:
            return stem

    if targets:
        stems = [_stem_from_path(item) for item in targets]
        stems = [stem for stem in stems if stem]
        if len(stems) == 1:
            return stems[0]

    return "full_suite"


def next_run_number(reports_dir: Path, base_name: str, date_str: str) -> int:
    """Return the next run number for base_name on date_str."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    pattern = f"{base_name}_{date_str}_run*.html"
    numbers: list[int] = []
    for path in reports_dir.glob(pattern):
        match = _RUN_SUFFIX.search(path.name)
        if match:
            numbers.append(int(match.group(1)))
    return (max(numbers) if numbers else 0) + 1


def build_report_filename(config) -> str:
    base_name = resolve_report_base_name(config)
    date_str = datetime.now().strftime("%Y-%m-%d")
    run_number = next_run_number(REPORTS_DIR, base_name, date_str)
    return f"{base_name}_{date_str}_run{run_number:02d}.html"


def build_report_path(config) -> Path:
    return REPORTS_DIR / build_report_filename(config)


def _user_provided_html_path(config) -> Path | None:
    htmlpath = getattr(config.option, "htmlpath", None)
    if not htmlpath:
        return None

    path = Path(str(htmlpath))
    legacy_paths = {
        LEGACY_REPORT_PATH.as_posix(),
        PENDING_REPORT_PATH.as_posix(),
    }
    if path.as_posix() in legacy_paths:
        return None
    return path


def configure_html_report_path(config) -> Path | None:
    """Assign a unique html report path unless the user supplied a custom one."""
    if getattr(config.option, "collectonly", False):
        config.option.htmlpath = None
        config._automation_html_report_path = None
        return None

    custom_path = _user_provided_html_path(config)
    if custom_path is not None:
        custom_path.parent.mkdir(parents=True, exist_ok=True)
        config.option.htmlpath = str(custom_path)
        config._automation_html_report_path = custom_path
        return custom_path

    report_path = build_report_path(config)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    config.option.htmlpath = str(report_path)
    config._automation_html_report_path = report_path
    return report_path


def get_report_path(session) -> Path | None:
    path = getattr(session.config, "_automation_html_report_path", None)
    if path is not None:
        return Path(path)

    htmlpath = getattr(session.config.option, "htmlpath", None)
    return Path(htmlpath) if htmlpath else None


def _session_stats(session) -> dict[str, int | float]:
    from utils.reporting import _get_html_report_plugin

    html_plugin = _get_html_report_plugin(session)
    if html_plugin is not None:
        outcomes = html_plugin._report.outcomes
        passed = outcomes["passed"]["value"]
        failed = outcomes["failed"]["value"] + outcomes["error"]["value"]
        skipped = outcomes["skipped"]["value"] + outcomes["xfailed"]["value"]
        xpassed = outcomes["xpassed"]["value"]
        duration = getattr(html_plugin._report, "total_duration", 0.0)
    else:
        terminal = session.config.pluginmanager.getplugin("terminalreporter")
        stats = getattr(terminal, "stats", {}) if terminal else {}
        passed = len(stats.get("passed", []))
        failed = len(stats.get("failed", [])) + len(stats.get("error", []))
        skipped = len(stats.get("skipped", [])) + len(stats.get("xfailed", []))
        xpassed = len(stats.get("xpassed", []))
        duration = 0.0

    if not duration:
        from utils.reporting import resolve_session_duration_seconds

        duration = resolve_session_duration_seconds(session)

    total = passed + failed + skipped + xpassed
    completed = passed + failed + xpassed
    pass_rate = (passed / completed * 100) if completed else 0.0
    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "xpassed": xpassed,
        "total": total,
        "duration": duration,
        "pass_rate": pass_rate,
    }


def _result_label(stats: dict[str, int | float]) -> str:
    if stats["failed"]:
        return "FAILED"
    if stats["passed"] and stats["total"] == stats["passed"] + stats["skipped"]:
        return "PASSED"
    if stats["passed"]:
        return "PASSED"
    return "COMPLETED"


def _format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def append_report_history(session, report_path: Path) -> None:
    stats = _session_stats(session)
    suite_name = resolve_report_base_name(session.config)
    result = _result_label(stats)
    duration = _format_duration(float(stats["duration"]))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    header = "| Date | Suite | Run | Result | Duration | Report |\n| --- | --- | --- | --- | --- | --- |\n"
    row = (
        f"| {timestamp} | {suite_name} | {report_path.name} | {result} | "
        f"{duration} | [{report_path.name}]({report_path.name}) |\n"
    )

    if not HISTORY_MD.is_file():
        HISTORY_MD.write_text("# HTML Report History\n\n" + header + row, encoding="utf-8")
    else:
        existing = HISTORY_MD.read_text(encoding="utf-8")
        with HISTORY_MD.open("a", encoding="utf-8") as handle:
            if "Date | Suite" not in existing:
                handle.write("\n" + header)
            handle.write(row)

    _refresh_history_html()


def _refresh_history_html() -> None:
    if not HISTORY_MD.is_file():
        return

    body = HISTORY_MD.read_text(encoding="utf-8")
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Automation Report History</title>"
        "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;} table{border-collapse:collapse;width:100%;}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f6f6f6;}</style>"
        "</head><body>"
        + _markdown_table_to_html(body)
        + "</body></html>"
    )
    HISTORY_HTML.write_text(html, encoding="utf-8")


def _markdown_table_to_html(markdown: str) -> str:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    html_parts: list[str] = ["<h1>Automation Report History</h1>"]
    in_table = False
    for line in lines:
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(set(cell) <= {"-", " "} for cell in cells):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                html_parts.append("<table><thead><tr>")
                in_table = True
            else:
                html_parts.append("<tr>")
            html_parts.extend(f"<{tag}>{cell}</{tag}>" for cell in cells)
            html_parts.append("</tr>")
            if tag == "th":
                html_parts.append("</thead><tbody>")
        elif in_table:
            html_parts.append("</tbody></table>")
            in_table = False
            html_parts.append(f"<p>{line}</p>")
        else:
            html_parts.append(f"<p>{line}</p>")
    if in_table:
        html_parts.append("</tbody></table>")
    return "".join(html_parts)


def _collect_trace_paths(session) -> list[Path]:
    traces_dir = Path("reports/traces")
    if not traces_dir.is_dir():
        return []

    collected: list[Path] = []
    for item in session.items:
        rep_call = getattr(item, "rep_call", None)
        if rep_call is None or not rep_call.failed:
            continue
        trace_path = traces_dir / f"{item.name}.zip"
        if trace_path.is_file():
            collected.append(trace_path)
    return collected


def _collect_video_paths(session) -> list[Path]:
    videos_dir = Path("reports/videos")
    if not videos_dir.is_dir():
        return []

    collected: list[Path] = []
    for item in session.items:
        rep_call = getattr(item, "rep_call", None)
        if rep_call is None or not rep_call.failed:
            continue
        video_path = videos_dir / f"{item.name}.webm"
        if video_path.is_file():
            collected.append(video_path)
    return collected


def print_terminal_report_summary(session) -> None:
    report_path = get_report_path(session)
    if report_path is None or not report_path.is_file():
        return

    stats = _session_stats(session)
    traces = _collect_trace_paths(session)
    videos = _collect_video_paths(session)
    open_command = _open_report_command(report_path)

    print("\n" + "=" * 50)
    print("HTML Report Generated")
    print()
    print(f"Report:\n{report_path.as_posix()}")
    print()
    print("Open Report:")
    print()
    print(open_command)

    if traces:
        print()
        print("Trace:")
        for trace_path in traces:
            print(f"playwright show-trace {trace_path.as_posix()}")

    if videos:
        print()
        print("Videos:")
        for video_path in videos:
            print(video_path.as_posix())

    print()
    print(
        f"Summary: {stats['passed']} passed, {stats['failed']} failed, "
        f"{stats['skipped']} skipped, pass rate {stats['pass_rate']:.1f}%"
    )
    print(f"History: {HISTORY_MD.as_posix()}")
    print("=" * 50)


def _open_report_command(report_path: Path) -> str:
    resolved = report_path.resolve()
    if platform.system().lower().startswith("win"):
        return f'start "" "{resolved}"'
    if platform.system() == "Darwin":
        return f'open "{resolved}"'
    return f'xdg-open "{resolved}"'
