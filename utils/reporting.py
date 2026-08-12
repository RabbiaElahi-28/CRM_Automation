"""Helpers for pytest-html reporting: test data capture, serialization, and extras."""

from __future__ import annotations

import base64
import dataclasses
import enum
import html
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_html

SKIP_LOCAL_NAMES = frozenset(
    {
        "page",
        "authenticated_page",
        "browser",
        "browser_context",
        "playwright_instance",
        "auth_state",
        "request",
        "pytestconfig",
        "extra",
        "extras",
        "_capture_report_test_data",
    }
)

SKIP_TYPE_NAMES = frozenset({"Page", "BrowserContext", "Browser", "Playwright"})

SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passwd|token|secret|api[_-]?key|session[_-]?id|authorization|credential)",
    re.IGNORECASE,
)

FIELD_LABELS = {
    "deal_name": "Lead Name",
    "lead_name": "Lead Name",
    "data": "Test Data",
    "form_data": "Create Lead Form",
    "borrower_name": "Borrower Name",
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Email",
    "phone_number": "Phone Number",
    "enter_email": "Email",
    "enter_phone": "Phone Number",
    "property_address": "Property Address",
    "client_address": "Client Address",
    "province": "Province",
    "mortgage_amount": "Mortgage Amount",
    "mortgage_loan_amount": "Mortgage Amount",
    "loan_type": "Loan Type",
    "mortgage_type": "Mortgage Type",
    "lender": "Lender",
    "lender_fee": "Lender Fee",
    "property_value": "Property Value",
    "co_borrower": "Co-Borrower Information",
    "contact": "Contact Information",
    "mortgage": "Mortgage Information",
    "property": "Property Information",
    "employment": "Employment Information",
    "note": "Note",
    "mortgage_snapshot": "Mortgage Snapshot",
    "appraisal_order": "Appraisal Order",
    "submitted_deal": "Submitted Deal",
    "approved_deal": "Approved Deal",
    "signed_deal": "Signed Deal",
    "compliance": "Compliance",
    "signed_form_baseline": "Signed Form Baseline",
    "flow": "Flow",
    "stage": "Stage",
    "scenarios": "Scenarios Run",
    "username": "Username",
}


def _is_sensitive_key(key: str) -> bool:
    return bool(SENSITIVE_KEY_PATTERN.search(str(key)))


def _humanize_key(key: str) -> str:
    return str(key).replace("_", " ").strip().title()


def _format_label(prefix: str, key: str) -> str:
    mapped = FIELD_LABELS.get(key, _humanize_key(key))
    return f"{prefix} / {mapped}" if prefix else mapped


def _serialize_value(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return str(value)

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _serialize_value(getattr(value, field.name), depth + 1)
            for field in dataclasses.fields(value)
        }

    if isinstance(value, dict):
        return {
            key: _serialize_value(item, depth + 1)
            for key, item in value.items()
            if not _is_sensitive_key(str(key))
        }

    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(item, depth + 1) for item in value]

    if isinstance(value, enum.Enum):
        return value.value

    type_name = value.__class__.__name__
    if type_name in SKIP_TYPE_NAMES or type_name.endswith("Page"):
        return None

    return str(value)


def _format_cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    return str(value)


def _flatten_serialized(prefix: str, value: Any, rows: list[tuple[str, str]]) -> None:
    if value is None:
        return

    if isinstance(value, dict):
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                rows.append((_format_label(prefix, str(key)), "***REDACTED***"))
                continue
            child_prefix = _format_label(prefix, str(key)) if prefix else FIELD_LABELS.get(
                str(key), _humanize_key(str(key))
            )
            if isinstance(item, dict):
                _flatten_serialized(child_prefix, item, rows)
            else:
                rows.append((child_prefix, _format_cell(item)))
        return

    label = prefix or "Value"
    rows.append((label, _format_cell(value)))


def build_test_data_rows(item, captured: dict | None = None) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Test Name", item.nodeid)]
    captured = captured or getattr(item, "_report_test_data", {}) or {}

    for name in sorted(captured):
        if name.startswith("_") or name in SKIP_LOCAL_NAMES:
            continue

        value = captured[name]
        serialized = _serialize_value(value)
        if serialized is None:
            continue

        prefix = FIELD_LABELS.get(name, _humanize_key(name))
        if isinstance(serialized, dict):
            _flatten_serialized(prefix, serialized, rows)
        else:
            rows.append((prefix, _format_cell(serialized)))

    return rows


def format_test_data_html(rows: list[tuple[str, str]]) -> str:
    if len(rows) <= 1:
        return "<h4>Test Data</h4><p>No test data captured.</p>"

    body = "".join(
        "<tr>"
        f"<th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>{html.escape(label)}</th>"
        f"<td style='padding:4px 8px;border:1px solid #ddd;white-space:pre-wrap;'>{html.escape(value)}</td>"
        "</tr>"
        for label, value in rows
    )
    return (
        "<h4>Test Data</h4>"
        "<table style='border-collapse:collapse;margin:8px 0;min-width:480px;'>"
        f"<tbody>{body}</tbody></table>"
    )


def test_data_extra(item) -> dict:
    rows = build_test_data_rows(item)
    return pytest_html.extras.html(format_test_data_html(rows))



def image_extra(path: str, name: str = "Screenshot") -> dict:
    path_obj = Path(path)
    if not path_obj.is_file():
        return pytest_html.extras.text(f"{name}: {path} (not found)")

    extension = path_obj.suffix.lstrip(".") or "png"
    mime_type = "image/png" if extension == "png" else f"image/{extension}"
    data = base64.b64encode(path_obj.read_bytes()).decode("ascii")
    return pytest_html.extras.image(data, name=name, mime_type=mime_type, extension=extension)


def video_extra(path: str, name: str = "Video") -> dict:
    path_obj = Path(path)
    if not path_obj.is_file():
        return pytest_html.extras.text(f"{name}: {path} (not found)")

    extension = path_obj.suffix.lstrip(".") or "webm"
    mime_type = "video/webm" if extension == "webm" else f"video/{extension}"
    data = base64.b64encode(path_obj.read_bytes()).decode("ascii")
    return pytest_html.extras.video(data, name=name, mime_type=mime_type, extension=extension)


def file_link_extra(path: str, name: str) -> dict:
    path_obj = Path(path)
    if path_obj.is_file():
        return pytest_html.extras.url(str(path_obj.resolve()), name=name)
    return pytest_html.extras.text(f"{name}: {path} (not found)")


def trace_instruction_extra(trace_path: Path | str) -> dict:
    """HTML instructions for opening a saved Playwright trace."""
    path_obj = Path(trace_path)
    filename = path_obj.name
    relative = path_obj.as_posix()
    command = f"playwright show-trace {relative}"
    content = (
        "<h4>Debug Information</h4>"
        "<div style='margin:8px 0;font-size:13px;line-height:1.5;'>"
        f"<strong>Trace file:</strong> {html.escape(relative)}<br><br>"
        "<strong>Run this command to inspect the failure:</strong><br>"
        f"<code style='background:#f6f6f6;padding:2px 6px;border-radius:3px;display:inline-block;margin-top:4px;'>"
        f"{html.escape(command)}</code>"
        "</div>"
    )
    return pytest_html.extras.html(content)


def failure_reason_extra(error_text: str) -> dict:
    content = (
        "<h4>Failure Reason</h4>"
        f"<pre style='white-space:pre-wrap;background:#fff5f5;border:1px solid #f5c2c2;"
        f"padding:8px;border-radius:4px;'>{html.escape(error_text)}</pre>"
    )
    return pytest_html.extras.html(content)


def console_logs_extra(logs: list[str]) -> dict:
    if not logs:
        return pytest_html.extras.text("No browser console output captured for this step.")
    body = html.escape("\n".join(logs))
    content = (
        "<h4>Browser Console Logs</h4>"
        f"<pre style='white-space:pre-wrap;background:#f6f8fa;border:1px solid #ddd;"
        f"padding:8px;border-radius:4px;max-height:320px;overflow:auto;'>{body}</pre>"
    )
    return pytest_html.extras.html(content)


def build_failure_artifact_extras(
    *,
    error_text: str | None = None,
    screenshot_path: str | None = None,
    trace_path: str | None = None,
    video_path: str | None = None,
    console_log_path: str | None = None,
    console_logs: list[str] | None = None,
) -> list[dict]:
    """Build pytest-html extras for failed steps including links and debug info."""
    extras: list[dict] = []

    if error_text:
        extras.append(failure_reason_extra(error_text))

    if screenshot_path:
        extras.append(image_extra(screenshot_path, name="Screenshot"))
        extras.append(file_link_extra(screenshot_path, name="Screenshot File"))

    if trace_path:
        extras.append(file_link_extra(trace_path, name="Playwright Trace"))
        extras.append(trace_instruction_extra(trace_path))

    if video_path:
        extras.append(video_extra(video_path, name="Video"))
        extras.append(file_link_extra(video_path, name="Video File"))

    if console_log_path:
        extras.append(file_link_extra(console_log_path, name="Console Log File"))

    test_log = Path("logs/test.log")
    if test_log.is_file():
        extras.append(file_link_extra(str(test_log), name="Execution Log"))

    if console_logs:
        extras.append(console_logs_extra(console_logs))

    return extras


def register_test_data(item, **kwargs) -> None:
    """Optional helper for tests to add extra report fields at runtime."""
    store = getattr(item, "_report_test_data", None)
    if store is None:
        store = {}
        item._report_test_data = store
    store.update(kwargs)


def append_report_extras(item, rep) -> None:
    """Attach pytest-html extras for the current report phase."""
    from utils.logger import get_logger
    from utils.screenshots import take_screenshot

    logger = get_logger()
    extras_before = list(getattr(rep, "extras", []))
    extras = list(extras_before)

    logger.info(
        "[REPORT DEBUG] pytest_runtest_makereport executed | when=%s outcome=%s extras_before=%s",
        rep.when,
        rep.outcome,
        len(extras_before),
    )

    if rep.when == "call" and rep.outcome in {"passed", "failed", "skipped"}:
        test_data = test_data_extra(item)
        logger.info("[REPORT DEBUG] test_data_extra=%s", test_data)
        extras.append(test_data)

    if rep.when == "call" and rep.failed:
        page = None
        for fixture_name in (
            "page",
            "authenticated_page",
            "admin_page",
            "fe_agent_page",
            "be_agent_page",
        ):
            page = item.funcargs.get(fixture_name)
            if page is not None:
                break
        if page:
            logger.error(f"Test failed: {item.name}")
            screenshot_path = take_screenshot(page, item.name)
            console_logs: list[str] = []
            try:
                from utils.flow_artifacts import ConsoleLogBuffer

                buffer = ConsoleLogBuffer.for_page(page)
                if buffer is not None:
                    console_logs = buffer.slice(0)
            except Exception:
                pass

            extras.extend(
                build_failure_artifact_extras(
                    error_text=getattr(rep, "longreprtext", "") or str(rep.longrepr),
                    screenshot_path=screenshot_path,
                    console_logs=console_logs,
                )
            )
        else:
            logger.info("[REPORT DEBUG] screenshot skipped: no page fixture")

    if rep.when == "teardown":
        rep_call = getattr(item, "rep_call", None)
        if rep_call and rep_call.failed:
            video_path = Path(f"reports/videos/{item.name}.webm")
            trace_path = Path(f"reports/traces/{item.name}.zip")
            extras.extend(
                build_failure_artifact_extras(
                    trace_path=str(trace_path) if trace_path.is_file() else None,
                    video_path=str(video_path) if video_path.is_file() else None,
                )
            )

    rep.extras = extras
    logger.info(
        "[REPORT DEBUG] rep.extras after append=%s items=%s",
        len(rep.extras),
        [extra.get("format_type") for extra in rep.extras],
    )


class TestDataCapture:
    def __init__(self, item):
        self.item = item
        self.captured: dict[str, Any] = {}
        self._test_module = item.module.__name__
        self._test_name = item.originalname

    def _should_capture(self, name: str, value: Any) -> bool:
        if name.startswith("_") or name in SKIP_LOCAL_NAMES:
            return False
        if callable(value):
            return False

        type_name = value.__class__.__name__
        if type_name in SKIP_TYPE_NAMES or type_name.endswith("Page"):
            return False

        return dataclasses.is_dataclass(value) or isinstance(value, (dict, list, tuple, str, int, float, bool))

    def tracefunc(self, frame, event, arg):
        if event != "return":
            return self.tracefunc

        if frame.f_globals.get("__name__") != self._test_module:
            return self.tracefunc

        if frame.f_code.co_name != self._test_name:
            return self.tracefunc

        for name, value in frame.f_locals.items():
            if self._should_capture(name, value):
                self.captured[name] = value

        if self.captured:
            existing = getattr(self.item, "_report_test_data", {})
            if existing:
                existing.update(self.captured)
            else:
                self.item._report_test_data = dict(self.captured)

        return self.tracefunc


def _get_html_report_plugin(session):
    for plugin in session.config.pluginmanager.get_plugins():
        if hasattr(plugin, "_process_report") and hasattr(plugin, "_report"):
            return plugin
    return None


def resolve_session_duration_seconds(session) -> float:
    """Prefer pytest-html total_duration; fall back to summed test durations or perf counter."""
    html_plugin = _get_html_report_plugin(session)
    if html_plugin is not None:
        report = getattr(html_plugin, "_report", None)
        total = getattr(report, "total_duration", None)
        if total:
            return float(total)

    terminal = session.config.pluginmanager.getplugin("terminalreporter")
    if terminal is not None:
        summed = 0.0
        for reports in getattr(terminal, "stats", {}).values():
            for rep in reports:
                summed += getattr(rep, "duration", 0.0) or 0.0
        if summed > 0:
            return summed

    from utils.session_timing import resolve_session_duration_seconds as perf_duration

    return perf_duration(session)


def format_summary_html(session) -> str:
    html_plugin = _get_html_report_plugin(session)
    if html_plugin is not None:
        outcomes = html_plugin._report.outcomes
        passed = outcomes["passed"]["value"]
        failed = outcomes["failed"]["value"] + outcomes["error"]["value"]
        skipped = outcomes["skipped"]["value"] + outcomes["xfailed"]["value"]
        xpassed = outcomes["xpassed"]["value"]
        total = passed + failed + skipped + xpassed
        completed = passed + failed + xpassed
        pass_denominator = passed + failed + xpassed
    else:
        terminal = session.config.pluginmanager.getplugin("terminalreporter")
        stats = getattr(terminal, "stats", {}) if terminal else {}

        passed = len(stats.get("passed", []))
        failed = len(stats.get("failed", [])) + len(stats.get("error", []))
        skipped = len(stats.get("skipped", [])) + len(stats.get("xfailed", []))
        xpassed = len(stats.get("xpassed", []))
        total = passed + failed + skipped + xpassed
        completed = passed + failed + xpassed
        pass_denominator = passed + failed + xpassed

    pass_percentage = (passed / pass_denominator * 100) if pass_denominator else 0.0

    duration_seconds = resolve_session_duration_seconds(session)
    minutes, seconds = divmod(int(duration_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    duration_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return (
        "<h3>Execution Summary</h3>"
        "<table style='border-collapse:collapse;margin:8px 0;min-width:420px;'>"
        "<tbody>"
        f"<tr><th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>Total Tests</th><td style='padding:4px 8px;border:1px solid #ddd;'>{total}</td></tr>"
        f"<tr><th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>Passed</th><td style='padding:4px 8px;border:1px solid #ddd;'>{passed}</td></tr>"
        f"<tr><th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>Failed</th><td style='padding:4px 8px;border:1px solid #ddd;'>{failed}</td></tr>"
        f"<tr><th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>Skipped</th><td style='padding:4px 8px;border:1px solid #ddd;'>{skipped}</td></tr>"
        f"<tr><th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>Execution Duration</th><td style='padding:4px 8px;border:1px solid #ddd;'>{duration_text}</td></tr>"
        f"<tr><th style='text-align:left;padding:4px 8px;background:#f6f6f6;border:1px solid #ddd;'>Pass Percentage</th><td style='padding:4px 8px;border:1px solid #ddd;'>{pass_percentage:.1f}% ({passed}/{completed} completed)</td></tr>"
        "</tbody></table>"
        "<script>"
        "document.addEventListener('DOMContentLoaded', function () {"
        "  const url = new URL(window.location.href);"
        "  if (url.searchParams.has('visible')) {"
        "    url.searchParams.delete('visible');"
        "    window.history.replaceState({}, '', url.href);"
        "  }"
        "});"
        "</script>"
    )
