from __future__ import annotations

import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, expect

from pages.mortgage_snapshot_app.leads_page import (
    MortgageSnapshotAppLeadsPage,
    PersistentNetworkError,
)
from pages.mortgage_snapshot_app.presentation_page import (
    MortgageSnapshotAppPresentationPage,
    PresentationDiscoveryReport,
)
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from test_page_data.addcoborrower_data import test_data as coborrower_data
from test_page_data.mortgage_snapshot_data import MortgageSnapshotData
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET
from utils.flow_step_reporting import record_flow_step
from utils.logger import get_logger
from utils.mortgage_snapshot_display import (
    MortgageSnapshotDisplayExpectations,
    build_display_expectations,
    build_display_expectations_from_captured,
    first_name_from_deal_name,
)
from utils.ms_app_auth import (
    MsAppPipeline,
    cross_role_pipeline,
    ensure_ms_app_lead_assignee,
    open_ms_app_as_pipeline_user,
    open_ms_app_rbac_page,
)
from utils.ms_app_rbac import (
    capture_presentation_url,
    verify_ms_app_non_assigned_access_denied,
)
from utils.sales_flow_helpers import (
    create_lead_smoke,
    ensure_fe_mortgage_snapshot_unlocked,
    run_co_borrower_smoke,
    run_notes_smoke,
    run_nova_worksheet_unlock_smoke,
)
from utils.screenshots import take_screenshot
from utils.test_data_factory import get_last_valid_lead_data

logger = get_logger()

# Report groups (virtual flow-step labels)
GROUP_MORTGAGE_SNAPSHOT = "Mortgage Snapshot"
GROUP_MS_APP = "Mortgage Snapshot App"
GROUP_CRM_RETURN = "CRM Return"
GROUP_STAGE = "Stage Complete"


def grouped_step_label(group: str, step: str) -> str:
    return f"{group} › {step}"


@dataclass
class MsAppStepResult:
    step_key: str
    label: str
    passed: bool
    duration_s: float
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MsAppWorkflowResult:
    passed: bool
    steps: list[MsAppStepResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    discovery: PresentationDiscoveryReport | None = None
    captured_snapshot: dict[str, str] = field(default_factory=dict)

    def summary(self, *, workflow: str = "MS App") -> str:
        failed = [s.label for s in self.steps if not s.passed]
        if failed:
            return f"{workflow} verification failed at: {', '.join(failed)}"
        return f"{workflow} verification passed"


def _short_step_error(error: str | None) -> str:
    if not error:
        return "(no error detail)"
    for line in error.splitlines():
        stripped = line.strip()
        if stripped.startswith("AssertionError:"):
            return stripped
    for line in reversed(error.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return "(no error detail)"


def emit_soft_fail_report(
    result: MsAppWorkflowResult,
    *,
    workflow: str,
    deal_name: str | None = None,
) -> None:
    """Log and print soft-fail workflow step failures to the pytest terminal."""
    failed_steps = [step for step in result.steps if not step.passed]
    if not failed_steps:
        return

    deal_note = f" (deal: {deal_name})" if deal_name else ""
    lines = [
        "",
        "=" * 72,
        f"SOFT-FAIL: {workflow} verification had failures{deal_note}",
        "=" * 72,
    ]
    for step in failed_steps:
        lines.append(f"  FAILED  {step.label} ({step.duration_s:.1f}s)")
        lines.append(f"           {_short_step_error(step.error)}")
    lines.extend(
        [
            "-" * 72,
            result.summary(workflow=workflow),
            "=" * 72,
            "",
        ]
    )
    report = "\n".join(lines)
    logger.warning(report)
    print(report, flush=True)


def finalize_ms_app_workflow_result(
    result: MsAppWorkflowResult,
    *,
    workflow: str,
    deal_name: str | None = None,
    soft_fail: bool = True,
) -> MsAppWorkflowResult:
    """Set passed flag; emit terminal report or raise when verification failed."""
    result.passed = all(step.passed for step in result.steps)
    if result.passed:
        return result
    if soft_fail:
        emit_soft_fail_report(result, workflow=workflow, deal_name=deal_name)
        return result
    raise AssertionError(result.summary(workflow=workflow))


def resolve_ms_app_lead_email(deal_name: str) -> str:
    """Resolve MS App search email: CRM profile first, deal-name stamp fallback."""
    from test_page_data.random_gen_data import RandomGenerator as RG
    from utils.lead_context import get_lead_context

    ctx = get_lead_context()
    if ctx.lead_email:
        return ctx.lead_email.strip()
    lead_data = get_last_valid_lead_data() or {}
    email = str(lead_data.get("enter_email", "")).strip()
    if email:
        return email
    stamp_email = RG.email_from_deal_stamp(deal_name)
    return stamp_email or ""


def resolve_ms_app_property_address(deal_name: str) -> str:
    """Profile property street number: post-edit CRM value first, create payload fallback."""
    from test_page_data.lead_edit_data import lead_edit_data
    from utils.lead_context import get_lead_context

    ctx = get_lead_context()
    if ctx.lead_property_address:
        return ctx.lead_property_address.strip()
    lead_data = get_last_valid_lead_data() or {}
    prop = str(lead_data.get("enter_property_address_street_number", "")).strip()
    if prop:
        return prop
    return str(lead_edit_data["property"]["partial"]).strip()


def resolve_ms_app_lead_context(
    deal_name: str,
    *,
    with_co_borrower: bool,
) -> tuple[str, str, str, str]:
    lead_data = get_last_valid_lead_data() or {}
    first_name = lead_data.get("first_name") or first_name_from_deal_name(deal_name)
    property_contains = resolve_ms_app_property_address(deal_name)
    lead_email = resolve_ms_app_lead_email(deal_name)
    if with_co_borrower:
        co_applicant = (
            f"{coborrower_data['co_borrower']['first_name']} "
            f"{coborrower_data['co_borrower']['last_name']}"
        )
    else:
        co_applicant = "N/A"
    return first_name, co_applicant, property_contains, lead_email


def expectations_from_captured(
    deal_name: str,
    captured: dict[str, str],
    *,
    with_co_borrower: bool,
) -> MortgageSnapshotDisplayExpectations:
    first_name, co_applicant, property_contains, lead_email = resolve_ms_app_lead_context(
        deal_name, with_co_borrower=with_co_borrower
    )
    return build_display_expectations_from_captured(
        deal_name=deal_name,
        applicant_first_name=first_name,
        co_applicant_display_name=co_applicant,
        property_address_contains=property_contains,
        captured=captured,
        lead_email=lead_email,
    )


def _search_kwargs(expectations: MortgageSnapshotDisplayExpectations) -> dict[str, str]:
    return {
        "vfli": expectations.vfli_number or None,
        "email": expectations.lead_email or None,
    }


def open_ms_app_from_crm(
    page: Page,
    context: BrowserContext,
    snapshot: MortgageSnapshotPage,
) -> Page:
    """Click CRM Application button and return the MS App tab on /leads."""
    app_page = snapshot.open_mortgage_snapshot_application(context)
    leads = MortgageSnapshotAppLeadsPage(app_page)
    leads.wait_for_leads()
    return app_page


def open_ms_app_for_assigned_user(
    crm_page: Page,
    snapshot: MortgageSnapshotPage,
    *,
    assigned_pipeline: MsAppPipeline,
    browser: Browser,
    prefer_crm_button: bool = True,
) -> Page:
    """
    Open MS App from the CRM Mortgage Snapshot Application button when possible.

    Uses the active CRM session (admin, FE, or BE) so MS App opens as that user.
    Falls back to native MS App login only when the CRM button is unavailable.
    """
    snapshot.reopen_snapshot_form_tab()
    if prefer_crm_button:
        try:
            expect(snapshot.mortgage_snapshot_application_btn).to_be_enabled(timeout=15000)
            return open_ms_app_from_crm(crm_page, crm_page.context, snapshot)
        except Exception:
            pass
    return open_ms_app_as_pipeline_user(crm_page.context, browser, assigned_pipeline)


def _record_ms_step(
    result: MsAppWorkflowResult,
    *,
    step_key: str,
    label: str,
    passed: bool,
    duration_s: float,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
    parent_nodeid: str | None = None,
    page: Page | None = None,
    group: str | None = None,
    screenshot_path: str | None = None,
    trace_path: str | None = None,
    video_path: str | None = None,
    console_log_path: str | None = None,
    console_logs: list[str] | None = None,
) -> None:
    display_label = grouped_step_label(group, label) if group else label
    if not passed and page is not None and screenshot_path is None:
        screenshot_path = take_screenshot(page, f"ms_app_{step_key}")
    step_meta = dict(metadata or {})
    if group:
        step_meta["report_group"] = group
    step = MsAppStepResult(
        step_key=step_key,
        label=display_label,
        passed=passed,
        duration_s=duration_s,
        error=error,
        metadata=step_meta,
    )
    result.steps.append(step)
    if not passed and error:
        result.errors.append(f"{display_label}: {error}")
    if parent_nodeid:
        record_flow_step(
            parent_nodeid,
            step_key=step_key,
            label=display_label,
            outcome="passed" if passed else "failed",
            duration=duration_s,
            metadata=step_meta,
            error=error,
            screenshot_path=screenshot_path,
            trace_path=trace_path,
            video_path=video_path,
            console_log_path=console_log_path,
            console_logs=list(console_logs or []),
        )


def _capture_ms_step_failure_artifacts(page: Page, step_key: str) -> dict[str, Any]:
    from utils.flow_artifacts import ConsoleLogBuffer, save_step_failure_artifacts

    console_buffer = ConsoleLogBuffer.for_page(page)
    console_start = console_buffer.mark() if console_buffer else 0
    console_logs = console_buffer.slice(console_start) if console_buffer else []
    screenshot_path = take_screenshot(page, f"ms_app_{step_key}")
    artifacts = save_step_failure_artifacts(page, f"ms_app_{step_key}", console_logs)
    if not console_logs:
        console_logs = artifacts.console_logs
    return {
        "screenshot_path": screenshot_path,
        "trace_path": artifacts.trace_path,
        "video_path": artifacts.video_path,
        "console_log_path": artifacts.console_log_path,
        "console_logs": console_logs,
    }


def record_grouped_flow_step(
    parent_nodeid: str | None,
    *,
    group: str,
    step: str,
    step_key: str,
    outcome: str = "passed",
    duration: float = 0.0,
    metadata: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    if not parent_nodeid:
        return
    record_flow_step(
        parent_nodeid,
        step_key=step_key,
        label=grouped_step_label(group, step),
        outcome=outcome,
        duration=duration,
        metadata={**(metadata or {}), "report_group": group},
        error=error,
    )


def _run_ms_step(
    result: MsAppWorkflowResult,
    *,
    step_key: str,
    label: str,
    func,
    parent_nodeid: str | None = None,
    page: Page | None = None,
    metadata: dict[str, Any] | None = None,
    group: str | None = None,
) -> Any:
    started = time.perf_counter()
    try:
        value = func()
        _record_ms_step(
            result,
            step_key=step_key,
            label=label,
            passed=True,
            duration_s=time.perf_counter() - started,
            metadata=metadata,
            parent_nodeid=parent_nodeid,
            page=page,
            group=group,
        )
        return value
    except PersistentNetworkError as exc:
        error = traceback.format_exc()
        artifact_kwargs: dict[str, Any] = {}
        if page is not None:
            artifact_kwargs = _capture_ms_step_failure_artifacts(page, step_key)
        _record_ms_step(
            result,
            step_key=step_key,
            label=label,
            passed=False,
            duration_s=time.perf_counter() - started,
            error=f"Persistent network error: {exc}\n{error}",
            metadata={**(metadata or {}), "network_error": "persistent"},
            parent_nodeid=parent_nodeid,
            page=page,
            group=group,
            **artifact_kwargs,
        )
        logger.error("MS App persistent network error (%s): %s", label, exc)
        return None
    except Exception as exc:
        error = traceback.format_exc()
        artifact_kwargs = {}
        if page is not None:
            artifact_kwargs = _capture_ms_step_failure_artifacts(page, step_key)
        _record_ms_step(
            result,
            step_key=step_key,
            label=label,
            passed=False,
            duration_s=time.perf_counter() - started,
            error=error,
            metadata={**(metadata or {}), "exception": str(exc)},
            parent_nodeid=parent_nodeid,
            page=page,
            group=group,
            **artifact_kwargs,
        )
        logger.error("MS App step failed (%s): %s", label, error or exc)
        return None


def _verify_presentation_pass(
    app_page: Page,
    leads: MortgageSnapshotAppLeadsPage,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
    *,
    with_co_borrower: bool,
    include_persistence: bool = True,
    include_refresh: bool = True,
    include_reload: bool = True,
) -> MortgageSnapshotAppPresentationPage:
    leads.verify_identifiers_then_open_presentation(
        lead_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.applicant_first_name,
        wait_timeout_ms=Config.MS_APP_LEAD_SYNC_TIMEOUT_MS,
    )
    presentation = MortgageSnapshotAppPresentationPage(app_page)
    presentation.assert_full_presentation(
        expectations, with_co_borrower=with_co_borrower
    )
    if include_persistence:
        presentation.assert_slide_navigation_persistence(
            expectations, with_co_borrower=with_co_borrower
        )
    if include_refresh:
        leads.close_presentation()
        app_page.reload()
        app_page.wait_for_load_state("domcontentloaded")
        leads.wait_for_leads()
        _reopen_lead_presentation(
            leads, lead_name, expectations, after_reload=True
        )
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
    if include_reload:
        leads.close_presentation()
        _reopen_lead_presentation(leads, lead_name, expectations)
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
    return presentation


def verify_crm_after_ms_app(
    crm_page: Page,
    snapshot: MortgageSnapshotPage,
    deal_name: str,
) -> None:
    """Verify CRM session survived MS App tab: same lead, tab, URL, no logout."""
    crm_page.bring_to_front()
    crm_page.reload()
    crm_page.wait_for_load_state("domcontentloaded")
    try:
        crm_page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass

    expect(crm_page).not_to_have_url(re.compile(r"mortgagesnapshot", re.I))
    expect(crm_page).not_to_have_url(re.compile(r"/login(?:\?|$)", re.I))
    auth_error = crm_page.get_by_text(
        re.compile(r"Missing authentication token", re.I)
    )
    if auth_error.count() > 0:
        expect(auth_error.first).not_to_be_visible(timeout=5000)
    expect(crm_page.get_by_text(deal_name, exact=False).first).to_be_visible(
        timeout=Config.TIMEOUT
    )
    snapshot.click(snapshot.snapshot_tab)
    expect(snapshot.snapshot_tab).to_have_attribute("data-state", "active", timeout=30000)
    expect(snapshot.snapshot_form_tab).to_be_visible(timeout=Config.TIMEOUT)
    # assert re.search(r"/sales/", crm_page.url), (
    #     f"Expected CRM sales lead URL after MS App, got {crm_page.url}"
    # )
    login_button = crm_page.get_by_role("button", name=re.compile(r"sign in|log in", re.I))
    if login_button.count() > 0:
        expect(login_button.first).not_to_be_visible()


def _reopen_lead_presentation(
    leads: MortgageSnapshotAppLeadsPage,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
    *,
    after_reload: bool = False,
) -> None:
    kwargs = {
        "lead_name": lead_name,
        "email": expectations.lead_email or None,
        "vfli": expectations.vfli_number or None,
    }
    if after_reload:
        leads.wait_for_leads_ready(timeout_ms=90000)
        leads.search_by_deal_name(
            **kwargs,
            wait_for_sync=True,
            wait_timeout_ms=min(Config.MS_APP_LEAD_SYNC_TIMEOUT_MS, 90000),
        )
    else:
        leads.search_by_deal_name(**kwargs)
    leads.open_lead_presentation(lead_name)


def close_ms_app_tab(app_page: Page) -> None:
    if not app_page.is_closed():
        app_page.close()


def logout_and_close_ms_app_tab(app_page: Page) -> None:
    """Logout from MS App on the assigned-user tab, then close it."""
    if app_page.is_closed():
        return
    leads = MortgageSnapshotAppLeadsPage(app_page)
    if "/leads" not in app_page.url and "/mortgage-snapshot" in app_page.url:
        leads.close_presentation()
    if leads.logout_button.count() > 0:
        try:
            if leads.logout_button.is_visible():
                leads.logout()
        except Exception:
            pass
    close_ms_app_tab(app_page)


def _open_and_search(
    app_page: Page,
    leads: MortgageSnapshotAppLeadsPage,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
) -> MortgageSnapshotAppPresentationPage:
    leads.verify_identifiers_then_open_presentation(
        lead_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.applicant_first_name,
        wait_timeout_ms=Config.MS_APP_LEAD_SYNC_TIMEOUT_MS,
    )
    return MortgageSnapshotAppPresentationPage(app_page)


def _run_ms_app_presentation_cycle(
    app_page: Page,
    leads: MortgageSnapshotAppLeadsPage,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
    *,
    with_co_borrower: bool,
    result: MsAppWorkflowResult,
    parent_nodeid: str | None,
    stale_check: tuple[str, str] | None = None,
    record_discovery: bool = True,
) -> tuple[MortgageSnapshotAppPresentationPage | None, str | None]:
    """Open → search → presentation → slides → refresh → reopen."""
    presentation = _run_ms_step(
        result,
        step_key="ms_app_search",
        label="Search",
        group=GROUP_MS_APP,
        func=lambda: _open_and_search(app_page, leads, lead_name, expectations),
        parent_nodeid=parent_nodeid,
        page=app_page,
        metadata={"deal_name": lead_name},
    )
    if presentation is None:
        return None, None

    def _verify_presentation():
        if stale_check:
            old_intro, new_intro = stale_check
            presentation.assert_welcome_slide_stale_removed(
                old_intro_script=old_intro,
                new_intro_script=new_intro,
            )
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
        return True

    if _run_ms_step(
        result,
        step_key="ms_app_presentation",
        label="Presentation",
        group=GROUP_MS_APP,
        func=_verify_presentation,
        parent_nodeid=parent_nodeid,
        page=app_page,
    ) is None:
        return None, None

    def _verify_slides():
        presentation.assert_slide_navigation_persistence(
            expectations, with_co_borrower=with_co_borrower
        )
        if record_discovery:
            result.discovery = presentation.discover_slides()
        return True

    if _run_ms_step(
        result,
        step_key="ms_app_slides",
        label="Slides",
        group=GROUP_MS_APP,
        func=_verify_slides,
        parent_nodeid=parent_nodeid,
        page=app_page,
        metadata={"slide_count": result.discovery.slide_count if result.discovery else None},
    ) is None:
        return None, None

    def _refresh_verify():
        leads.close_presentation()
        app_page.reload()
        app_page.wait_for_load_state("domcontentloaded")
        leads.wait_for_leads()
        _reopen_lead_presentation(
            leads, lead_name, expectations, after_reload=True
        )
        if stale_check:
            old_intro, new_intro = stale_check
            presentation.assert_welcome_slide_stale_removed(
                old_intro_script=old_intro,
                new_intro_script=new_intro,
            )
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
        return True

    if _run_ms_step(
        result,
        step_key="ms_app_refresh",
        label="Refresh",
        group=GROUP_MS_APP,
        func=_refresh_verify,
        parent_nodeid=parent_nodeid,
        page=app_page,
    ) is None:
        return None, None

    def _reopen_verify():
        leads.close_presentation()
        _reopen_lead_presentation(leads, lead_name, expectations)
        if stale_check:
            old_intro, new_intro = stale_check
            presentation.assert_welcome_slide_stale_removed(
                old_intro_script=old_intro,
                new_intro_script=new_intro,
            )
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
        return True

    if _run_ms_step(
        result,
        step_key="ms_app_reopen",
        label="Reopen",
        group=GROUP_MS_APP,
        func=_reopen_verify,
        parent_nodeid=parent_nodeid,
        page=app_page,
    ) is None:
        return None, None

    presentation_url = capture_presentation_url(app_page)
    return presentation, presentation_url


def verify_mortgage_snapshot_app_workflow(
    crm_page: Page,
    snapshot: MortgageSnapshotPage,
    deal_name: str,
    captured: dict[str, str],
    *,
    with_co_borrower: bool = True,
    parent_nodeid: str | None = None,
    soft_fail: bool = True,
    include_regression_rerun: bool = False,
    assigned_pipeline: MsAppPipeline = "admin",
    browser: Browser | None = None,
    enforce_ms_app_rbac: bool = True,
    prefer_crm_button: bool = True,
    sync_assignee: bool = True,
    bucket: str = MY_DEALS_BUCKET,
    assignee_sync_page: Page | None = None,
) -> MsAppWorkflowResult:
    """
    Full MS App verification between snapshot save and stage completion.

    Uses persisted CRM captured values only. When soft_fail=True (default),
    failures are recorded but not raised so the CRM workflow can continue.
    """
    result = MsAppWorkflowResult(passed=True, captured_snapshot=dict(captured))
    expectations = expectations_from_captured(
        deal_name, captured, with_co_borrower=with_co_borrower
    )
    availability_started = time.perf_counter()
    app_page: Page | None = None

    def _sync_assignee():
        if not sync_assignee or assigned_pipeline == "admin":
            return True
        ensure_ms_app_lead_assignee(
            crm_page,
            deal_name,
            assigned_pipeline,
            bucket=bucket,
            assignee_page=assignee_sync_page,
        )
        snapshot.click(snapshot.snapshot_tab)
        snapshot.click(snapshot.snapshot_form_tab)
        return True

    if sync_assignee and assigned_pipeline != "admin":
        _run_ms_step(
            result,
            step_key="ms_app_assignee",
            label="Assignee Sync",
            group=GROUP_MS_APP,
            func=_sync_assignee,
            parent_nodeid=parent_nodeid,
            page=crm_page,
            metadata={"assigned_pipeline": assigned_pipeline, "bucket": bucket},
        )

    def _open_app():
        nonlocal app_page
        if browser is not None:
            app_page = open_ms_app_for_assigned_user(
                crm_page,
                snapshot,
                assigned_pipeline=assigned_pipeline,
                browser=browser,
                prefer_crm_button=prefer_crm_button,
            )
        else:
            snapshot.reopen_snapshot_form_tab()
            app_page = open_ms_app_from_crm(crm_page, crm_page.context, snapshot)
        return app_page

    app_page = _run_ms_step(
        result,
        step_key="ms_app_open",
        label="Open",
        group=GROUP_MS_APP,
        func=_open_app,
        parent_nodeid=parent_nodeid,
        page=crm_page,
    )
    if app_page is None:
        return finalize_ms_app_workflow_result(
            result,
            workflow="Mortgage Snapshot App",
            deal_name=deal_name,
            soft_fail=soft_fail,
        )

    result.timings["save_to_app_open_s"] = time.perf_counter() - availability_started
    leads = MortgageSnapshotAppLeadsPage(app_page)

    load_started = time.perf_counter()
    cycle_result = _run_ms_app_presentation_cycle(
        app_page,
        leads,
        deal_name,
        expectations,
        with_co_borrower=with_co_borrower,
        result=result,
        parent_nodeid=parent_nodeid,
    )
    if cycle_result[0] is None:
        return finalize_ms_app_workflow_result(
            result,
            workflow="Mortgage Snapshot App",
            deal_name=deal_name,
            soft_fail=soft_fail,
        )
    _presentation, presentation_url = cycle_result
    result.timings["presentation_verify_s"] = time.perf_counter() - load_started

    def _close_assigned_app_tab():
        logout_and_close_ms_app_tab(app_page)
        crm_page.bring_to_front()
        return True

    _run_ms_step(
        result,
        step_key="ms_app_close_assigned",
        label="Close Assigned Tab",
        group=GROUP_MS_APP,
        func=_close_assigned_app_tab,
        parent_nodeid=parent_nodeid,
        page=app_page,
    )

    if enforce_ms_app_rbac and browser is not None:
        cross_pipeline = cross_role_pipeline(assigned_pipeline)

        def _rbac_non_assigned():
            rbac_page = open_ms_app_rbac_page(crm_page.context, cross_pipeline)
            try:
                verify_ms_app_non_assigned_access_denied(
                    rbac_page,
                    assigned_pipeline=assigned_pipeline,
                    lead_name=deal_name,
                    expectations=expectations,
                    presentation_url=presentation_url,
                )
                return True
            finally:
                close_ms_app_tab(rbac_page)
                crm_page.bring_to_front()

        rbac_result = _run_ms_step(
            result,
            step_key="ms_app_rbac_non_assigned",
            label="Non-Assigned Denied",
            group=GROUP_MS_APP,
            func=_rbac_non_assigned,
            parent_nodeid=parent_nodeid,
            page=crm_page,
            metadata={
                "assigned_pipeline": assigned_pipeline,
                "cross_pipeline": cross_pipeline,
                "login_url": Config.ms_app_login_url(),
            },
        )
        if rbac_result is None:
            return finalize_ms_app_workflow_result(
                result,
                workflow="Mortgage Snapshot App",
                deal_name=deal_name,
                soft_fail=soft_fail,
            )

    def _crm_return():
        crm_page.bring_to_front()
        verify_crm_after_ms_app(crm_page, snapshot, deal_name)
        return True

    _run_ms_step(
        result,
        step_key="crm_return",
        label="Session Preserved",
        group=GROUP_CRM_RETURN,
        func=_crm_return,
        parent_nodeid=parent_nodeid,
        page=crm_page,
        metadata={"deal_name": deal_name, "url": crm_page.url},
    )

    if include_regression_rerun:
        old_intro = captured.get("introScript", "")

        def _edit_and_save():
            snapshot.reopen_snapshot_form_tab()
            new_intro = f"{old_intro} regression-update"
            snapshot.set_snapshot_field("introScript", new_intro)
            snapshot.save()
            snapshot.verify_saved()
            snapshot.reopen_snapshot_form_tab()
            updated_captured = snapshot.capture_snapshot_form_values()
            result.captured_snapshot = updated_captured
            return new_intro, updated_captured

        edit_result = _run_ms_step(
            result,
            step_key="ms_snapshot_regression_edit",
            label="Save",
            group=GROUP_MORTGAGE_SNAPSHOT,
            func=_edit_and_save,
            parent_nodeid=parent_nodeid,
            page=crm_page,
        )
        if edit_result:
            new_intro, updated_captured = edit_result
            updated_expectations = expectations_from_captured(
                deal_name, updated_captured, with_co_borrower=with_co_borrower
            )

            def _regression_open():
                if browser is not None:
                    return open_ms_app_for_assigned_user(
                        crm_page,
                        snapshot,
                        assigned_pipeline=assigned_pipeline,
                        browser=browser,
                        prefer_crm_button=prefer_crm_button,
                    )
                snapshot.reopen_snapshot_form_tab()
                return open_ms_app_from_crm(crm_page, crm_page.context, snapshot)

            reg_app = _run_ms_step(
                result,
                step_key="ms_app_regression_open",
                label="Open",
                group=GROUP_MS_APP,
                func=_regression_open,
                parent_nodeid=parent_nodeid,
                page=crm_page,
            )
            if reg_app:
                reg_leads = MortgageSnapshotAppLeadsPage(reg_app)
                stale = (old_intro, new_intro)
                _run_ms_app_presentation_cycle(
                    reg_app,
                    reg_leads,
                    deal_name,
                    updated_expectations,
                    with_co_borrower=with_co_borrower,
                    result=result,
                    parent_nodeid=parent_nodeid,
                    stale_check=stale,
                    record_discovery=False,
                )

                def _regression_close():
                    reg_leads.close_presentation()
                    reg_leads.logout()
                    close_ms_app_tab(reg_app)
                    crm_page.bring_to_front()
                    verify_crm_after_ms_app(crm_page, snapshot, deal_name)
                    return True

                _run_ms_step(
                    result,
                    step_key="ms_app_regression_close",
                    label="Close",
                    group=GROUP_MS_APP,
                    func=_regression_close,
                    parent_nodeid=parent_nodeid,
                    page=crm_page,
                )

    return finalize_ms_app_workflow_result(
        result,
        workflow="Mortgage Snapshot App",
        deal_name=deal_name,
        soft_fail=soft_fail,
    )


# ---------------------------------------------------------------------------
# Standalone test bootstrap (test_mortgage_snapshot_app_display.py)
# ---------------------------------------------------------------------------


def prepare_lead_with_saved_snapshot(
    page: Page,
    *,
    with_co_borrower: bool = False,
) -> tuple[str, MortgageSnapshotData, MortgageSnapshotDisplayExpectations, MortgageSnapshotPage]:
    """Bootstrap lead, save snapshot form only (no stage complete), return expectations."""
    lead_name = create_lead_smoke(page)
    first_name, co_applicant, property_contains, lead_email = resolve_ms_app_lead_context(
        lead_name, with_co_borrower=with_co_borrower
    )

    if with_co_borrower:
        run_co_borrower_smoke(page, lead_name)

    run_notes_smoke(page, lead_name, move_to_sales=True)
    run_nova_worksheet_unlock_smoke(page, lead_name, bucket=MY_DEALS_BUCKET)
    ensure_fe_mortgage_snapshot_unlocked(
        page, lead_name, bucket=MY_DEALS_BUCKET, assign_fe_agent=False
    )

    data = MortgageSnapshotData()
    snapshot = MortgageSnapshotPage(page)
    snapshot.click(snapshot.snapshot_tab)
    snapshot.click(snapshot.snapshot_form_tab)
    snapshot.fill_valid_baseline(data)
    snapshot.save()
    snapshot.verify_saved()
    snapshot.reopen_snapshot_form_tab()
    captured = snapshot.capture_snapshot_form_values()
    expectations = build_display_expectations(
        deal_name=lead_name,
        applicant_first_name=first_name,
        co_applicant_display_name=co_applicant,
        property_address_contains=property_contains,
        lead_email=lead_email,
        captured=captured,
        data=data,
    )
    return lead_name, data, expectations, snapshot


def run_ms_app_discovery(
    app_page: Page,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
) -> PresentationDiscoveryReport:
    leads = MortgageSnapshotAppLeadsPage(app_page)
    leads.wait_for_leads()
    leads.search_by_deal_name(
        lead_name, email=expectations.lead_email or None
    )
    leads.open_lead_presentation(lead_name)
    presentation = MortgageSnapshotAppPresentationPage(app_page)
    return presentation.discover_slides()


def verify_ms_app_presentation(
    app_page: Page,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
    *,
    with_co_borrower: bool,
) -> MortgageSnapshotAppPresentationPage:
    leads = MortgageSnapshotAppLeadsPage(app_page)
    leads.wait_for_leads()
    return _verify_presentation_pass(
        app_page,
        leads,
        lead_name,
        expectations,
        with_co_borrower=with_co_borrower,
    )
