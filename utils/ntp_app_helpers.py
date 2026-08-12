from __future__ import annotations

import re

from playwright.sync_api import Browser, Page, expect

from pages.approved_page import ApprovedPage
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from pages.ntp_app.leads_page import NtpAppLeadsPage
from pages.ntp_app.presentation_page import NtpAppPresentationPage
from pages.profile_page import ProfilePage
from test_page_data.approved_data import ApprovedData
from test_page_data.mortgage_snapshot_data import MortgageSnapshotData
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET
from utils.mortgage_snapshot_app_helpers import (
    MsAppWorkflowResult,
    _run_ms_step,
    close_ms_app_tab,
    finalize_ms_app_workflow_result,
)
from utils.ms_app_auth import (
    MsAppPipeline,
    cross_role_pipeline,
    resolve_ms_app_pipeline,
)
from utils.ntp_app_auth import (
    ensure_ntp_app_lead_assignee,
    open_ntp_app_as_pipeline_user,
    open_ntp_app_rbac_page,
)
from utils.ntp_app_rbac import (
    capture_ntp_presentation_url,
    verify_ntp_app_non_assigned_access_denied,
)
from utils.ntp_display import NtpDisplayExpectations, expectations_from_captured
from utils.logger import get_logger
from utils.sales_flow_helpers import (
    create_lead_smoke,
    ensure_fe_mortgage_snapshot_unlocked,
    run_appraisal_order_smoke,
    run_co_borrower_smoke,
    run_notes_smoke,
    run_nova_worksheet_unlock_smoke,
    run_submitted_smoke,
)

GROUP_NTP_APP = "NTP Application"
GROUP_CRM_RETURN = "CRM Return"

logger = get_logger()


def open_ntp_app_from_crm(
    crm_page: Page,
    approved: ApprovedPage,
    *,
    browser: Browser | None = None,
    pipeline: MsAppPipeline | None = None,
) -> Page:
    """Click CRM NTP Application button and return the NTP App tab on /leads."""
    app_page = approved.open_ntp_application(
        crm_page.context,
        browser=browser or crm_page.context.browser,
        pipeline=pipeline,
    )
    leads = NtpAppLeadsPage(app_page)
    leads.wait_for_leads()
    return app_page


def open_ntp_from_crm_after_approved_save(
    crm_page: Page,
    approved: ApprovedPage,
    *,
    browser: Browser | None = None,
    pipeline: MsAppPipeline | None = None,
) -> Page:
    """
    Post-save CRM flow (same idea as MS App after snapshot save):

    The CRM app auto-opens Appraisal Completed after Approved Form save —
    automation does not click that tab here. We switch back to Approved Form
    and open NTP Application (CRM button or staff URL fallback).
    """
    return open_ntp_app_from_crm(
        crm_page, approved, browser=browser, pipeline=pipeline
    )


def open_ntp_app_for_assigned_user(
    crm_page: Page,
    approved: ApprovedPage,
    *,
    assigned_pipeline: MsAppPipeline,
    browser: Browser,
    prefer_crm_button: bool = True,
) -> Page:
    """
    Open NTP from the CRM NTP Application button when possible.

    Uses the active CRM session (admin, FE, or BE) so NTP opens as that user.
    Native NTP login is used only when prefer_crm_button=False.
    """
    if prefer_crm_button:
        return open_ntp_from_crm_after_approved_save(
            crm_page, approved, browser=browser, pipeline=assigned_pipeline
        )

    logger.info(
        "Opening NTP App via native login for pipeline %s (prefer_crm_button=False)",
        assigned_pipeline,
    )
    return open_ntp_app_as_pipeline_user(crm_page.context, browser, assigned_pipeline)


def _search_kwargs(expectations: NtpDisplayExpectations) -> dict[str, str | None]:
    return {
        "vfli": expectations.vfli_number or None,
        "email": expectations.lead_email or None,
    }


def _reopen_lead_presentation(
    leads: NtpAppLeadsPage,
    lead_name: str,
    expectations: NtpDisplayExpectations,
    *,
    after_reload: bool = False,
) -> None:
    kwargs = {
        "lead_name": lead_name,
        "email": expectations.lead_email or None,
        "vfli": expectations.vfli_number or None,
    }
    leads.wait_for_leads_ready(timeout_ms=90000)
    if after_reload:
        leads.search_by_deal_name(
            **kwargs,
            wait_for_sync=True,
            wait_timeout_ms=min(Config.NTP_APP_LEAD_SYNC_TIMEOUT_MS, 90000),
        )
    else:
        leads.search_by_deal_name(**kwargs)
    leads.open_lead_presentation(lead_name)


def logout_and_close_ntp_app_tab(app_page: Page) -> None:
    if app_page.is_closed():
        return
    leads = NtpAppLeadsPage(app_page)
    if "/leads" not in app_page.url:
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
    leads: NtpAppLeadsPage,
    lead_name: str,
    expectations: NtpDisplayExpectations,
) -> NtpAppPresentationPage:
    leads.verify_identifiers_then_open_presentation(
        lead_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.header_first_name,
        wait_timeout_ms=Config.NTP_APP_LEAD_SYNC_TIMEOUT_MS,
    )
    presentation = NtpAppPresentationPage(app_page)
    presentation.wait_for_presentation()
    return presentation


def verify_crm_after_ntp_app(
    crm_page: Page,
    approved: ApprovedPage,
    deal_name: str,
) -> None:
    crm_page.bring_to_front()
    expect(crm_page.get_by_text(deal_name, exact=False).first).to_be_visible(
        timeout=Config.TIMEOUT
    )
    approved.reopen_approved_completed_tab()
    expect(crm_page).not_to_have_url(re.compile(r"ntp", re.I))
    login_button = crm_page.get_by_role(
        "button", name=re.compile(r"sign in|log in", re.I)
    )
    if login_button.count() > 0:
        expect(login_button.first).not_to_be_visible()


def _run_ntp_presentation_cycle(
    app_page: Page,
    leads: NtpAppLeadsPage,
    lead_name: str,
    expectations: NtpDisplayExpectations,
    *,
    with_co_borrower: bool,
    result: MsAppWorkflowResult,
    parent_nodeid: str | None,
) -> tuple[NtpAppPresentationPage | None, str | None]:
    presentation = _run_ms_step(
        result,
        step_key="ntp_app_search",
        label="Search",
        group=GROUP_NTP_APP,
        func=lambda: _open_and_search(app_page, leads, lead_name, expectations),
        parent_nodeid=parent_nodeid,
        page=app_page,
        metadata={"deal_name": lead_name},
    )
    if presentation is None:
        return None, None

    def _verify_presentation():
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
        return True

    if _run_ms_step(
        result,
        step_key="ntp_app_presentation",
        label="Presentation",
        group=GROUP_NTP_APP,
        func=_verify_presentation,
        parent_nodeid=parent_nodeid,
        page=app_page,
    ) is None:
        return None, None

    def _verify_pdf():
        presentation.assert_pdf_download(expectations.header_first_name)
        return True

    if _run_ms_step(
        result,
        step_key="ntp_app_pdf",
        label="PDF Download",
        group=GROUP_NTP_APP,
        func=_verify_pdf,
        parent_nodeid=parent_nodeid,
        page=app_page,
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
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
        return True

    if _run_ms_step(
        result,
        step_key="ntp_app_refresh",
        label="Refresh",
        group=GROUP_NTP_APP,
        func=_refresh_verify,
        parent_nodeid=parent_nodeid,
        page=app_page,
    ) is None:
        return None, None

    def _reopen_verify():
        leads.close_presentation()
        _reopen_lead_presentation(leads, lead_name, expectations)
        presentation.assert_full_presentation(
            expectations, with_co_borrower=with_co_borrower
        )
        return True

    if _run_ms_step(
        result,
        step_key="ntp_app_reopen",
        label="Reopen",
        group=GROUP_NTP_APP,
        func=_reopen_verify,
        parent_nodeid=parent_nodeid,
        page=app_page,
    ) is None:
        return None, None

    return presentation, capture_ntp_presentation_url(app_page)


def verify_ntp_app_workflow(
    crm_page: Page,
    approved: ApprovedPage,
    deal_name: str,
    captured_approved: dict[str, str],
    captured_snapshot: dict[str, str],
    *,
    profile_full_name: str,
    form_filled_at: str,
    with_co_borrower: bool = True,
    parent_nodeid: str | None = None,
    soft_fail: bool = True,
    assigned_pipeline: MsAppPipeline | None = None,
    browser: Browser | None = None,
    enforce_ntp_app_rbac: bool = True,
    prefer_crm_button: bool = True,
    sync_assignee: bool = True,
    bucket: str = MY_DEALS_BUCKET,
    assignee_sync_page: Page | None = None,
) -> MsAppWorkflowResult:
    result = MsAppWorkflowResult(passed=True, captured_snapshot=dict(captured_snapshot))
    assigned_pipeline = resolve_ms_app_pipeline(bucket, assigned_pipeline)
    expectations = expectations_from_captured(
        deal_name,
        captured_approved,
        captured_snapshot,
        profile_full_name=profile_full_name,
        form_filled_at=form_filled_at,
        with_co_borrower=with_co_borrower,
    )

    def _sync_assignee():
        if not sync_assignee or assigned_pipeline == "admin":
            return True
        ensure_ntp_app_lead_assignee(
            crm_page,
            deal_name,
            assigned_pipeline,
            bucket=bucket,
            assignee_page=assignee_sync_page,
        )
        approved.reopen_approved_form_tab()
        return True

    if sync_assignee and assigned_pipeline != "admin":
        _run_ms_step(
            result,
            step_key="ntp_app_assignee",
            label="Assignee Sync",
            group=GROUP_NTP_APP,
            func=_sync_assignee,
            parent_nodeid=parent_nodeid,
            page=crm_page,
            metadata={
                "assigned_pipeline": assigned_pipeline,
                "bucket": bucket,
                "note": "Reuses MS App assignee helper; skips when ntp_sync_assignee=False",
            },
        )

    app_page: Page | None = None
    ntp_tab_closed = False

    def _close_assigned_app_tab():
        nonlocal ntp_tab_closed
        if app_page is not None and not app_page.is_closed():
            logout_and_close_ntp_app_tab(app_page)
            ntp_tab_closed = True
        crm_page.bring_to_front()
        return True

    try:
        def _open_app():
            nonlocal app_page
            resolved_browser = browser or crm_page.context.browser
            if prefer_crm_button:
                app_page = open_ntp_from_crm_after_approved_save(
                    crm_page,
                    approved,
                    browser=resolved_browser,
                    pipeline=assigned_pipeline,
                )
            elif browser is not None:
                app_page = open_ntp_app_for_assigned_user(
                    crm_page,
                    approved,
                    assigned_pipeline=assigned_pipeline,
                    browser=browser,
                    prefer_crm_button=False,
                )
            else:
                app_page = open_ntp_from_crm_after_approved_save(
                    crm_page,
                    approved,
                    browser=resolved_browser,
                    pipeline=assigned_pipeline,
                )
            return app_page

        app_page = _run_ms_step(
            result,
            step_key="ntp_app_open",
            label="Open",
            group=GROUP_NTP_APP,
            func=_open_app,
            parent_nodeid=parent_nodeid,
            page=crm_page,
        )
        if app_page is None:
            return finalize_ms_app_workflow_result(
                result,
                workflow="NTP Application",
                deal_name=deal_name,
                soft_fail=soft_fail,
            )

        leads = NtpAppLeadsPage(app_page)
        cycle_result = _run_ntp_presentation_cycle(
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
                workflow="NTP Application",
                deal_name=deal_name,
                soft_fail=soft_fail,
            )
        _presentation, presentation_url = cycle_result

        _run_ms_step(
            result,
            step_key="ntp_app_close_assigned",
            label="Close Assigned Tab",
            group=GROUP_NTP_APP,
            func=_close_assigned_app_tab,
            parent_nodeid=parent_nodeid,
            page=app_page,
        )

        if enforce_ntp_app_rbac and browser is not None:
            cross_pipeline = cross_role_pipeline(assigned_pipeline)

            def _rbac_non_assigned():
                rbac_page = open_ntp_app_rbac_page(crm_page.context, cross_pipeline)
                try:
                    verify_ntp_app_non_assigned_access_denied(
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
                step_key="ntp_app_rbac_non_assigned",
                label="Non-Assigned Denied",
                group=GROUP_NTP_APP,
                func=_rbac_non_assigned,
                parent_nodeid=parent_nodeid,
                page=crm_page,
                metadata={
                    "assigned_pipeline": assigned_pipeline,
                    "cross_pipeline": cross_pipeline,
                    "login_url": Config.ntp_app_login_url(),
                },
            )
            if rbac_result is None:
                return finalize_ms_app_workflow_result(
                    result,
                    workflow="NTP Application",
                    deal_name=deal_name,
                    soft_fail=soft_fail,
                )

        def _crm_return():
            verify_crm_after_ntp_app(crm_page, approved, deal_name)
            return True

        _run_ms_step(
            result,
            step_key="crm_return_ntp",
            label="Session Preserved",
            group=GROUP_CRM_RETURN,
            func=_crm_return,
            parent_nodeid=parent_nodeid,
            page=crm_page,
        )

        return finalize_ms_app_workflow_result(
            result,
            workflow="NTP Application",
            deal_name=deal_name,
            soft_fail=soft_fail,
        )
    finally:
        if app_page is not None and not ntp_tab_closed and not app_page.is_closed():
            try:
                logout_and_close_ntp_app_tab(app_page)
                crm_page.bring_to_front()
            except Exception:
                logger.warning(
                    "Failed to close NTP App tab after partial workflow",
                    exc_info=True,
                )


def prepare_lead_with_saved_approved(
    page: Page,
    *,
    with_co_borrower: bool = False,
) -> tuple[str, dict[str, str], dict[str, str], NtpDisplayExpectations, ApprovedPage]:
    lead_name = create_lead_smoke(page)
    if with_co_borrower:
        run_co_borrower_smoke(page, lead_name)

    run_notes_smoke(page, lead_name, move_to_sales=True)
    for attempt in range(3):
        try:
            run_nova_worksheet_unlock_smoke(page, lead_name, bucket=MY_DEALS_BUCKET)
            break
        except Exception:
            if attempt == 2:
                raise
            page.wait_for_timeout(5000)
    ensure_fe_mortgage_snapshot_unlocked(
        page, lead_name, bucket=MY_DEALS_BUCKET, assign_fe_agent=False
    )

    snapshot = MortgageSnapshotPage(page)
    data = MortgageSnapshotData()
    snapshot.open()
    snapshot.open_snapshot(lead_name, bucket=MY_DEALS_BUCKET)
    snapshot.fill_video_section(data)
    snapshot.fill_client_needs(data)
    snapshot.fill_primary_credit(data)
    snapshot.fill_co_applicant_credit(data)
    snapshot.fill_cost_of_doing_nothing(data)
    snapshot.fill_option_four(data)
    snapshot.fill_option_five(data)
    snapshot.fill_home_appraised(data)
    snapshot.fill_final_prompt(data)
    snapshot.save()
    snapshot.verify_saved()
    snapshot.reopen_snapshot_form_tab()
    captured_snapshot = snapshot.capture_snapshot_form_values()
    snapshot.reopen_snapshot_meeting_tab()
    snapshot.create_meeting(data)
    snapshot.fill_meeting_details(data)
    snapshot.verify_meeting_saved()
    snapshot.delete_meeting(data)
    snapshot.verify_meeting_deleted()
    snapshot.complete_stage()

    run_appraisal_order_smoke(page, lead_name, bucket=MY_DEALS_BUCKET)
    run_submitted_smoke(page, lead_name, bucket=MY_DEALS_BUCKET)

    approved = ApprovedPage(page)
    approved.open_approved(lead_name, bucket=MY_DEALS_BUCKET)
    approved_data = ApprovedData()

    profile = ProfilePage(page)
    profile_name = profile.read_lead_name()
    form_filled_at = profile.read_form_filled_at()
    approved.reopen_approved_form_tab()

    approved.fill_approved_form(approved_data.form)
    approved.save_approved_form()
    approved.verify_form_saved()
    approved.verify_approved_completed_tab_enabled()
    approved.verify_approved_completed_tab_active()
    approved.reopen_approved_form_tab()
    captured_approved = approved.capture_approved_form_values()
    expectations = expectations_from_captured(
        lead_name,
        captured_approved,
        captured_snapshot,
        profile_full_name=profile_name,
        form_filled_at=form_filled_at,
        with_co_borrower=with_co_borrower,
    )
    return lead_name, captured_approved, captured_snapshot, expectations, approved


def verify_ntp_app_presentation(
    app_page: Page,
    lead_name: str,
    expectations: NtpDisplayExpectations,
    *,
    with_co_borrower: bool,
) -> NtpAppPresentationPage:
    leads = NtpAppLeadsPage(app_page)
    leads.wait_for_leads()
    leads.verify_identifiers_then_open_presentation(
        lead_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.header_first_name,
        wait_timeout_ms=Config.NTP_APP_LEAD_SYNC_TIMEOUT_MS,
    )
    presentation = NtpAppPresentationPage(app_page)
    presentation.assert_full_presentation(
        expectations, with_co_borrower=with_co_borrower
    )
    presentation.assert_pdf_download(expectations.header_first_name)
    return presentation
