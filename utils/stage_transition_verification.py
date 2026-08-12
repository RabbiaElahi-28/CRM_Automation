"""Full post-stage transition verification — kanban, status, URL, persistence."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page, expect

from test_page_data import workflow_expectations as we
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, SALES_BACKEND_BUCKET
from utils.form_persistence import verify_form_persistence
from utils.kanban_verification import open_record_in_kanban_column
from utils.lead_context import get_active_deal_name
from utils.toast import Toast
from utils.workflow_verification import WorkflowVerification

STAGE_URL_TAB: dict[str, str] = {
    "mortgage_snapshot": "mortgage-snapshot",
    "appraisal_order": "appraisal-order",
    "submitted": "submitted",
    "approved": "approved",
    "signed": "signed",
}


@dataclass(frozen=True)
class StageFormHandlers:
    """Capture/read/reopen hooks for a stage form."""

    capture: Callable[[], dict[str, Any]]
    reopen: Callable[[], None]
    read: Callable[[], dict[str, Any]]
    normalize: Callable[[Any], str] | None = None
    label: str = "form"


def _bucket_is_backend(bucket: str) -> bool:
    return bucket == SALES_BACKEND_BUCKET


def _status_label(stage_key: str, bucket: str) -> str:
    if _bucket_is_backend(bucket):
        return we.BE_STAGE_STATUS_LABEL[stage_key]
    return we.FE_STAGE_STATUS_LABEL[stage_key]


def _kanban_column(stage_key: str, bucket: str) -> str:
    if _bucket_is_backend(bucket):
        return we.BE_STAGE_KANBAN_COLUMN[stage_key]
    return we.FE_STAGE_KANBAN_COLUMN[stage_key]


def verify_immediate_stage_move(
    page: Page,
    *,
    success_toast: str | None,
    url_tab: str,
    active_tab,
) -> None:
    """
    After Move to Next Stage: confirm via URL + active tab (durable), toast optional.

    Sonner toasts auto-dismiss quickly; the tab/URL transition is the source of truth.
    """
    expect(page).to_have_url(
        re.compile(rf"tab={re.escape(url_tab)}"),
        timeout=Config.TIMEOUT,
    )
    expect(active_tab).to_have_attribute("data-state", "active", timeout=Config.TIMEOUT)

    if success_toast:
        try:
            Toast(page).assert_message(success_toast, timeout=5000)
        except Exception:
            pass


def wait_for_stage_transition(
    page: Page,
    *,
    success_toast: str | None = None,
) -> None:
    """Wait for CRM to finish a stage transition (dialog closed, toast, idle)."""
    if success_toast:
        try:
            Toast(page).assert_message(success_toast, timeout=5000)
        except Exception:
            pass

    dialog = page.get_by_role("alertdialog", name="Move to Next Stage?")
    if dialog.count() > 0:
        expect(dialog).to_be_hidden(timeout=Config.TIMEOUT)

    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass


def _pipeline_for_bucket(bucket: str) -> we.Pipeline:
    return we.pipeline_for_bucket(bucket)


def verify_stage_entry_tabs(
    page: Page,
    *,
    bucket: str,
    stage_key: str,
    is_admin: bool = True,
    has_full_access: bool = True,
) -> None:
    """Assert stage tabs on entry match CRM nextStatus for the pipeline stage."""
    pipeline = _pipeline_for_bucket(bucket)
    visible, hidden = we.stage_tab_expectations_for_stage(
        stage_key,
        pipeline=pipeline,
        moment="entry",
        is_admin=is_admin,
        has_full_access=has_full_access,
    )
    verifier = WorkflowVerification(page)
    verifier.verify_tabs_visible(visible)
    verifier.verify_tabs_hidden(hidden)


def _verify_post_transition_tabs(
    page: Page,
    *,
    bucket: str,
    stage_key: str,
    is_admin: bool = True,
    has_full_access: bool = True,
) -> None:
    pipeline = _pipeline_for_bucket(bucket)
    next_status_id = we.STAGE_POST_TRANSITION_NEXT_STATUS[(pipeline, stage_key)]
    if next_status_id is None:
        return
    
    visible, hidden = we.stage_tab_expectations_for_stage(
        stage_key,
        pipeline=pipeline,
        moment="post",
        is_admin=is_admin,
        has_full_access=has_full_access,
    )
    verifier = WorkflowVerification(page)
    verifier.verify_tabs_visible(visible)
    verifier.verify_tabs_hidden(hidden)


def verify_post_stage_completion(
    page: Page,
    deal_name: str,
    *,
    bucket: str,
    stage_key: str,
    captured_values: dict[str, Any],
    handlers: StageFormHandlers,
    success_toast: str | None = None,
    is_admin: bool = True,
    has_full_access: bool = True,
) -> None:
    """
    Verify full CRM workflow after Complete Stage / Move To Next Stage.

    1. Wait for transition
    2. Status badge on LeadInfoHeader
    3. Kanban column placement (with bucket search) and re-open lead
    4. Post-transition tab visibility
    5. Stage tab URL
    6. Saved data persistence (captured pre-transition values)
    """
    deal_name = deal_name or get_active_deal_name()
    status_label = _status_label(stage_key, bucket)
    kanban_column = _kanban_column(stage_key, bucket)
    url_tab = STAGE_URL_TAB[stage_key]

    wait_for_stage_transition(page, success_toast=success_toast)

    verifier = WorkflowVerification(page)
    verifier.verify_status_badge(contains=status_label)

    open_record_in_kanban_column(page, bucket, deal_name, kanban_column)

    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass


    _verify_post_transition_tabs(
        page,
        bucket=bucket,
        stage_key=stage_key,
        is_admin=is_admin,
        has_full_access=has_full_access,
    )

    handlers.reopen()
    expect(page).to_have_url(re.compile(rf"tab={re.escape(url_tab)}"), timeout=Config.TIMEOUT)

    verify_form_persistence(
        read_values=handlers.read,
        reopen=handlers.reopen,
        expected=captured_values,
        normalize=handlers.normalize,
        label=handlers.label,
    )


def verify_fe_stage_completion(
    page: Page,
    deal_name: str,
    stage_key: str,
    captured_values: dict[str, Any],
    handlers: StageFormHandlers,
    *,
    success_toast: str | None = None,
) -> None:
    verify_post_stage_completion(
        page,
        deal_name,
        bucket=MY_DEALS_BUCKET,
        stage_key=stage_key,
        captured_values=captured_values,
        handlers=handlers,
        success_toast=success_toast,
    )


def verify_be_stage_completion(
    page: Page,
    deal_name: str,
    stage_key: str,
    captured_values: dict[str, Any],
    handlers: StageFormHandlers,
    *,
    success_toast: str | None = None,
) -> None:
    verify_post_stage_completion(
        page,
        deal_name,
        bucket=SALES_BACKEND_BUCKET,
        stage_key=stage_key,
        captured_values=captured_values,
        handlers=handlers,
        success_toast=success_toast,
    )
