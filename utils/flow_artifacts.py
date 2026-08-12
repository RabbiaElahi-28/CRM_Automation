"""Artifact capture for flow-step HTML reporting (screenshots, traces, video, logs)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

TRACES_DIR = Path("reports/traces")
VIDEOS_DIR = Path("reports/videos")
LOGS_DIR = Path("reports/logs")
SCREENSHOTS_DIR = Path("reports/screenshots")


def ensure_artifact_dirs() -> None:
    for directory in (TRACES_DIR, VIDEOS_DIR, LOGS_DIR, SCREENSHOTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


@dataclass
class StepArtifacts:
    screenshot_path: str | None = None
    trace_path: str | None = None
    video_path: str | None = None
    console_log_path: str | None = None
    console_logs: list[str] = field(default_factory=list)


class ConsoleLogBuffer:
    """Collect browser console messages for the active Playwright page."""

    def __init__(self) -> None:
        self._entries: list[str] = []

    def attach(self, page) -> None:
        def _on_console(message) -> None:
            location = ""
            if message.location:
                location = (
                    f" ({message.location.get('url', '')}:"
                    f"{message.location.get('lineNumber', '')})"
                )
            self._entries.append(f"[{message.type}]{location} {message.text}")

        page.on("console", _on_console)
        page._flow_console_buffer = self  # noqa: SLF001 — reporting hook

    @classmethod
    def for_page(cls, page) -> ConsoleLogBuffer | None:
        return getattr(page, "_flow_console_buffer", None)

    def mark(self) -> int:
        return len(self._entries)

    def slice(self, start: int) -> list[str]:
        return list(self._entries[start:])


def save_step_failure_artifacts(page, artifact_slug: str, console_logs: list[str]) -> StepArtifacts:
    """Persist failure artifacts for a virtual flow step."""
    ensure_artifact_dirs()
    artifacts = StepArtifacts(console_logs=list(console_logs))

    if console_logs:
        log_path = LOGS_DIR / f"{artifact_slug}.log"
        log_path.write_text("\n".join(console_logs), encoding="utf-8")
        artifacts.console_log_path = str(log_path)

    if page is None:
        return artifacts

    context = page.context

    trace_path = TRACES_DIR / f"{artifact_slug}.zip"
    try:
        context.tracing.stop(path=str(trace_path))
        if trace_path.is_file():
            artifacts.trace_path = str(trace_path)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception:
        pass

    video = page.video
    if video is not None:
        video_path = VIDEOS_DIR / f"{artifact_slug}.webm"
        try:
            video.save_as(str(video_path))
            if video_path.is_file():
                artifacts.video_path = str(video_path)
        except Exception:
            pass

    return artifacts
