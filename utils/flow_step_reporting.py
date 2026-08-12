"""Virtual per-module pytest-html rows for single-run E2E flow orchestrators."""

from __future__ import annotations

import inspect
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

import pytest_html

from utils.flow_artifacts import ConsoleLogBuffer, save_step_failure_artifacts
from utils.flow_data_capture import capture_constructed_instances
from utils.flow_test_data import merge_captured_instances
from utils.reporting import (
    _get_html_report_plugin,
    build_failure_artifact_extras,
    build_test_data_rows,
    format_test_data_html,
    image_extra,
    test_data_extra,
)


@dataclass
class FlowStepResult:
    step_key: str
    label: str
    outcome: str
    duration: float
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    screenshot_path: str | None = None
    trace_path: str | None = None
    video_path: str | None = None
    console_log_path: str | None = None
    console_logs: list[str] = field(default_factory=list)


class _SyntheticReport:
    """Minimal stand-in for pytest.TestReport consumed by pytest-html."""

    def __init__(
        self,
        nodeid: str,
        outcome: str,
        duration: float,
        *,
        longreprtext: str = "",
        extras: list | None = None,
    ) -> None:
        self.nodeid = nodeid
        self.when = "call"
        self.outcome = outcome
        self.duration = duration
        self.longreprtext = longreprtext
        self.sections: list[tuple[str, str]] = []
        self.extras = extras or []


class _StepItem:
    """Lightweight item stand-in for test-data HTML generation."""

    def __init__(self, nodeid: str, metadata: dict[str, Any]) -> None:
        self.nodeid = nodeid
        self._report_test_data = dict(metadata)


def _resolve_item(request_or_item):
    """Accept pytest request fixture or test item."""
    return getattr(request_or_item, "node", request_or_item)


class FlowStepRegistry:
    _steps: dict[str, list[FlowStepResult]] = {}

    @classmethod
    def clear(cls, parent_nodeid: str) -> None:
        cls._steps.pop(parent_nodeid, None)

    @classmethod
    def begin(cls, parent_nodeid: str) -> None:
        cls.clear(parent_nodeid)
        cls._steps[parent_nodeid] = []

    @classmethod
    def record(cls, parent_nodeid: str, step: FlowStepResult) -> None:
        cls._steps.setdefault(parent_nodeid, []).append(step)

    @classmethod
    def get(cls, parent_nodeid: str) -> list[FlowStepResult]:
        return list(cls._steps.get(parent_nodeid, []))

    @classmethod
    def has_failure_artifacts(cls, parent_nodeid: str) -> bool:
        return any(
            step.trace_path or step.video_path or step.screenshot_path
            for step in cls.get(parent_nodeid)
            if step.outcome == "failed"
        )


def record_flow_step(
    parent_nodeid: str,
    *,
    step_key: str,
    label: str,
    outcome: str,
    duration: float,
    metadata: dict[str, Any] | None = None,
    error: str | None = None,
    screenshot_path: str | None = None,
    trace_path: str | None = None,
    video_path: str | None = None,
    console_log_path: str | None = None,
    console_logs: list[str] | None = None,
) -> None:
    FlowStepRegistry.record(
        parent_nodeid,
        FlowStepResult(
            step_key=step_key,
            label=label,
            outcome=outcome,
            duration=duration,
            metadata=metadata or {},
            error=error,
            screenshot_path=screenshot_path,
            trace_path=trace_path,
            video_path=video_path,
            console_log_path=console_log_path,
            console_logs=list(console_logs or []),
        ),
    )


def run_flow_step(
    request_or_item,
    page,
    *,
    step_key: str,
    label: str,
    func: Callable[[], Any],
    metadata: dict[str, Any] | None = None,
    capture_classes: tuple[type, ...] = (),
    enrich_metadata: Callable[[dict[str, Any], Any | None, dict[str, Any]], None] | None = None,
) -> Any:
    """Execute one logical module once and record a virtual pytest-html row."""
    item = _resolve_item(request_or_item)
    parent_nodeid = item.nodeid
    step_metadata = dict(metadata or {})
    step_metadata.setdefault("stage", label)

    started = time.perf_counter()
    screenshot_path = None
    trace_path = None
    video_path = None
    console_log_path = None
    console_logs: list[str] = []
    error_text = None
    outcome = "passed"
    result = None

    console_buffer = ConsoleLogBuffer.for_page(page) if page is not None else None
    console_start = console_buffer.mark() if console_buffer else 0
    artifact_slug = f"{item.name}_{step_key}"

    try:
        with capture_constructed_instances(*capture_classes) as captured:
            result = func()
            merge_captured_instances(step_metadata, captured)
            if enrich_metadata is not None:
                enrich_metadata(step_metadata, result, captured)
    except Exception:
        outcome = "failed"
        error_text = traceback.format_exc()
        if console_buffer is not None:
            console_logs = console_buffer.slice(console_start)
        if page is not None:
            from utils.screenshots import take_screenshot

            screenshot_path = take_screenshot(page, artifact_slug)
            artifacts = save_step_failure_artifacts(page, artifact_slug, console_logs)
            trace_path = artifacts.trace_path
            video_path = artifacts.video_path
            console_log_path = artifacts.console_log_path
            if not console_logs:
                console_logs = artifacts.console_logs
        raise
    else:
        if console_buffer is not None:
            console_logs = console_buffer.slice(console_start)
    finally:
        duration = time.perf_counter() - started
        record_flow_step(
            parent_nodeid,
            step_key=step_key,
            label=label,
            outcome=outcome,
            duration=duration,
            metadata=step_metadata,
            error=error_text,
            screenshot_path=screenshot_path,
            trace_path=trace_path,
            video_path=video_path,
            console_log_path=console_log_path,
            console_logs=console_logs,
        )

    return result


def run_flow_step_soft(
    request_or_item,
    page,
    *,
    step_key: str,
    label: str,
    func: Callable[[], Any],
    metadata: dict[str, Any] | None = None,
) -> tuple[Any | None, bool]:
    """Execute a flow step, record outcome, but do not re-raise on failure."""
    item = _resolve_item(request_or_item)
    started = time.perf_counter()
    outcome = "passed"
    error_text = None
    screenshot_path = None
    result = None

    try:
        result = func()
    except Exception:
        outcome = "failed"
        error_text = traceback.format_exc()
        if page is not None:
            from utils.screenshots import take_screenshot

            screenshot_path = take_screenshot(page, f"{item.name}_{step_key}")
    finally:
        duration = time.perf_counter() - started
        record_flow_step(
            item.nodeid,
            step_key=step_key,
            label=label,
            outcome=outcome,
            duration=duration,
            metadata=dict(metadata or {}),
            error=error_text,
            screenshot_path=screenshot_path,
        )

    return result, outcome == "passed"


def record_login_step(
    request_or_item,
    *,
    flow: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Login runs in the session auth fixture; record it as a passed virtual step."""
    item = _resolve_item(request_or_item)
    step_metadata = {"flow": flow, "stage": "Login", "auth": "session_fixture"}
    if metadata:
        step_metadata.update(metadata)
    record_flow_step(
        item.nodeid,
        step_key="login",
        label="Login",
        outcome="passed",
        duration=0.0,
        metadata=step_metadata,
    )


def _step_test_data_extra(nodeid: str, metadata: dict[str, Any]) -> dict:
    fake_item = _StepItem(nodeid, metadata)
    rows = build_test_data_rows(fake_item)
    return pytest_html.extras.html(format_test_data_html(rows))


def build_flow_step_extras(step: FlowStepResult, nodeid: str) -> list[dict]:
    """Compose all pytest-html extras for one virtual flow step."""
    extras = [_step_test_data_extra(nodeid, step.metadata)]

    if step.outcome == "failed":
        extras.extend(
            build_failure_artifact_extras(
                error_text=step.error,
                screenshot_path=step.screenshot_path,
                trace_path=step.trace_path,
                video_path=step.video_path,
                console_log_path=step.console_log_path,
                console_logs=step.console_logs,
            )
        )
    elif step.screenshot_path:
        extras.append(image_extra(step.screenshot_path, name=f"{step.label} Screenshot"))

    return extras


def _adjust_outcome(report_data, outcome: str, delta: int) -> None:
    key = outcome.lower()
    if key not in report_data.outcomes:
        return
    report_data.outcomes[key]["value"] = max(0, report_data.outcomes[key]["value"] + delta)


def _add_synthetic_report_row(html_plugin, synthetic, duration: float) -> None:
    """Insert one virtual row, compatible with pytest-html 4.1.x and 4.2.x."""
    processed_extras = html_plugin._process_extras(synthetic, synthetic.nodeid)
    if "processed_extras" in inspect.signature(html_plugin._process_report).parameters:
        html_plugin._process_report(synthetic, duration, processed_extras)
    else:
        html_plugin._process_report(synthetic, duration)


def inject_flow_steps_into_html_report(session) -> None:
    """Replace orchestrator parent rows with one pytest-html row per flow step."""
    html_plugin = _get_html_report_plugin(session)
    if html_plugin is None:
        return

    report_data = html_plugin._report

    for item in session.items:
        if not item.get_closest_marker("flow_orchestrator"):
            continue

        steps = FlowStepRegistry.get(item.nodeid)
        if not steps:
            continue

        parent_nodeid = item.nodeid
        if parent_nodeid in report_data.data["tests"]:
            report_data.data["tests"].pop(parent_nodeid)
            rep_call = getattr(item, "rep_call", None)
            if rep_call is not None:
                _adjust_outcome(report_data, rep_call.outcome, -1)

        for step in steps:
            step_nodeid = f"{parent_nodeid}::{step.label}"
            extras = build_flow_step_extras(step, step_nodeid)

            synthetic = _SyntheticReport(
                step_nodeid,
                step.outcome,
                step.duration,
                longreprtext=step.error or "",
                extras=extras,
            )
            _add_synthetic_report_row(html_plugin, synthetic, step.duration)
            _adjust_outcome(report_data, step.outcome, 1)
