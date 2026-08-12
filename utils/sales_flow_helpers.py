"""Reusable happy-path stage runners for full-flow and smoke E2E tests."""

from __future__ import annotations

import re
from typing import Literal

from playwright.sync_api import Page, expect

from pages.add_coBorrower_page import CoBorrowerPage
from pages.appraisal_order_page import AppraisalOrderPage
from pages.approved_page import ApprovedPage
from pages.client_care_page import ClientCarePage
from pages.compliance_page import CompliancePage
from pages.create_lead import CreateLeadPage
from pages.lead_edit_page import LeadEditPage
from pages.marketing_page import MarketingPage
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from pages.note_page import NotesPage
from pages.profile_page import ProfilePage
from pages.signed_marketing_page import SignedMarketingPage
from pages.signed_page import SignedPage
from pages.submitted_page import SubmittedPage
from test_page_data.addcoborrower_data import test_data as coborrower_data
from test_page_data.appraisal_order_data import AppraisalOrderData
from test_page_data.approved_data import ApprovedData
from test_page_data.compliance_data import ComplianceData
from test_page_data.lead_edit_data import lead_edit_data
from test_page_data.mortgage_snapshot_data import MortgageSnapshotData
from test_page_data.note_data import notes_test_data
from test_page_data.signed_data import SignedData
from test_page_data.signed_form_baseline import save as save_signed_form_baseline
from test_page_data.submitted_data import SubmittedData
from test_page_data.test_entities import persist_my_deals_deal_name, persist_my_leads_deal_name
from utils.lead_assignment import LeadAssignmentHelper, assign_agent_after_create
from utils.lead_context import sync_lead_email, sync_lead_property_address
from utils.entity_navigation import MY_DEALS_BUCKET, SALES_BACKEND_BUCKET, LEAD_BUCKET
from utils.logger import get_logger
from utils.form_persistence import normalize_numeric, verify_form_persistence
from utils.form_prefill_verification import FormPrefillVerification
from utils.stage_transition_verification import (
    StageFormHandlers,
    verify_be_stage_completion,
    verify_fe_stage_completion,
    verify_stage_entry_tabs,
)
from utils.test_data_factory import valid_lead_data
from utils.toast import Toast
from utils.workflow_verification import MOVE_TO_SALES_TRANSITION, WorkflowVerification
from test_page_data import workflow_expectations as we

logger = get_logger()



def _complete_stage_verification(
    page: Page,
    deal_name: str,
    *,
    bucket: str,
    stage_key: str,
    captured_values: dict,
    handlers: StageFormHandlers,
    success_toast: str | None = None,
) -> None:
    if bucket == SALES_BACKEND_BUCKET:
        verify_be_stage_completion(
            page,
            deal_name,
            stage_key,
            captured_values,
            handlers,
            success_toast=success_toast,
        )
    else:
        verify_fe_stage_completion(
            page,
            deal_name,
            stage_key,
            captured_values,
            handlers,
            success_toast=success_toast,
        )


def create_lead_smoke(page: Page) -> str:
    lead_data = valid_lead_data()
    create = CreateLeadPage(page)
    create.open()
    create.fill_form(lead_data)
    create.submit_lead_and_wait_success()
    deal_name = lead_data["enter_name"]
    persist_my_leads_deal_name(deal_name)
    sync_lead_email(lead_data["enter_email"])
    sync_lead_property_address(lead_data["enter_property_address_street_number"])
    assign_agent_after_create(page, deal_name)
    return deal_name


def _resolve_profile_email(deal_name: str) -> str:
    """Profile email from session/create payload, else stamp derived from deal name."""
    from test_page_data.random_gen_data import RandomGenerator as RG
    from utils.lead_context import get_lead_context
    from utils.test_data_factory import get_last_valid_lead_data

    ctx = get_lead_context()
    if ctx.lead_email:
        return ctx.lead_email.strip()
    lead_data = get_last_valid_lead_data() or {}
    email = str(lead_data.get("enter_email", "")).strip()
    if email:
        return email
    stamp_email = RG.email_from_deal_stamp(deal_name)
    if stamp_email:
        return stamp_email
    return str(lead_edit_data["contact"]["email"]).strip()


def run_lead_edit_smoke(page: Page, lead_name: str, *, bucket: str = LEAD_BUCKET) -> None:
    lead = LeadEditPage(page)
    lead.open()
    lead.open_lead_for_edit(lead_name, bucket=bucket)
    profile_email = _resolve_profile_email(lead_name)
    lead.update_contact_email(profile_email)
    sync_lead_email(profile_email)
    lead.select_gender(lead_edit_data["gender"])
    lead.select_marital_status(lead_edit_data["marital_status"])
    lead.update_address(
        lead_edit_data["address"]["partial"],
        expected_postal_code=lead_edit_data["contact"].get("postal_code"),
    )
    lead.select_dob(
        lead_edit_data["dob"]["month"],
        lead_edit_data["dob"]["year"],
        lead_edit_data["dob"]["day"],
    )
    lead.save_client_info()
    Toast(page).assert_message("Client information updated successfully")

    lead.open_mortgage_tab()
    lead.select_mortgage_type(lead_edit_data["mortgage"]["type"])
    lead.fill_mortgage_details(
        lead_edit_data["mortgage"]["loan_amount"],
        lead_edit_data["mortgage"]["rate"],
        lead_edit_data["mortgage"]["maturity_month"],
        lead_edit_data["mortgage"]["maturity_year"],
        lead_edit_data["mortgage"]["maturity_day"],
        lead_edit_data["mortgage"]["credit_score"],
    )
    lead.fill_property_info(
        lead_edit_data["property"]["partial"],
        lead_edit_data["property"]["type"],
        lead_edit_data["property"]["value"],
        lead_edit_data["property"]["monthly_payment"],
        lead_edit_data["property"]["balance"],
    )
    sync_lead_property_address(lead_edit_data["property"]["partial"])
    lead.fill_employment(
        lead_edit_data["employment"]["work_situation"],
        lead_edit_data["employment"]["work_location_partial"],
        lead_edit_data["employment"]["income"],
        lead_edit_data["employment"]["employer"],
        lead_edit_data["employment"]["important_choice"],
    )
    lead.save_mortgage_changes()
    Toast(page).assert_message("Mortgage information updated successfully")


def run_notes_smoke(
    page: Page,
    lead_name: str,
    *,
    move_to_sales: bool = True,
    bucket: str = LEAD_BUCKET,
) -> str:
    notes = NotesPage(page)
    notes.open()
    notes.open_lead(lead_name, bucket=bucket)
    notes.open_notes_tab()
    notes.click_add_note()
    notes.enter_note(notes_test_data["note"]["text"])
    notes.apply_formatting()
    notes.select_heading(notes_test_data["note"]["heading"])
    notes.select_note_status(notes_test_data["note"]["status"])
    notes.save_note_successfully()
    notes.edit_note(
        notes_test_data["note"]["text"],
        notes_test_data["note"]["updated_text"],
    )
    notes.delete_note(notes_test_data["note"]["updated_text"])
    if move_to_sales:
        notes.move_to_sales()
        WorkflowVerification(page).verify_transition(
            MOVE_TO_SALES_TRANSITION,
            record_name=lead_name,
        )
        persist_my_deals_deal_name(lead_name)
    return lead_name


def run_nova_worksheet_unlock_smoke(
    page: Page,
    lead_name: str,
    *,
    bucket: str = LEAD_BUCKET,
) -> str:
    """Set Nova Worksheet status only — keeps current assignee (admin paths)."""
    LeadAssignmentHelper(page).assign_nova_worksheet_status_only(lead_name, bucket=bucket)
    persist_my_deals_deal_name(lead_name)
    return lead_name


def run_nova_bypass_smoke(
    page: Page,
    lead_name: str,
    *,
    bucket: str = LEAD_BUCKET,
) -> str:
    """Assign FE agent + Nova Worksheet status so Mortgage Snapshot is unlocked."""
    LeadAssignmentHelper(page).assign_fe_nova_bypass(lead_name, bucket=bucket)
    persist_my_deals_deal_name(lead_name)
    return lead_name


def ensure_fe_mortgage_snapshot_unlocked(
    page: Page,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
    assign_fe_agent: bool = False,
) -> None:
    """Unlock Mortgage Snapshot via Nova Worksheet when the tab is not visible."""
    tab = page.get_by_role("tab", name="Mortgage Snapshot", exact=True)
    if tab.count() > 0:
        try:
            if tab.is_visible():
                return
        except Exception:
            pass
    if assign_fe_agent:
        run_nova_bypass_smoke(page, deal_name, bucket=bucket)
    else:
        run_nova_worksheet_unlock_smoke(page, deal_name, bucket=bucket)


def run_co_borrower_smoke(page: Page, lead_name: str, *, bucket: str = LEAD_BUCKET) -> None:
    cb = CoBorrowerPage(page)
    cb.open()
    cb.open_lead(lead_name, bucket=bucket)
    cb.open_co_borrowers_tab()
    cb.click_add_co_borrower()
    cb.fill_basic_info(coborrower_data["co_borrower"])
    cb.select_dob(coborrower_data["co_borrower"])
    cb.select_marital_status(coborrower_data["co_borrower"]["marital_status"])
    cb.fill_employment(
        coborrower_data["co_borrower"]["employer"],
        coborrower_data["co_borrower"]["relation"],
        coborrower_data["co_borrower"]["income"],
    )
    cb.save()


def run_mortgage_snapshot_smoke(
    page: Page,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
    with_co_borrower: bool = True,
    request_or_item=None,
    regression_ms_app: bool = False,
    ms_app_assigned_pipeline: Literal["fe", "be", "admin"] | None = None,
    ms_app_open_via_crm: bool | None = None,
    fail_on_ms_app_error: bool = True,
    assignee_sync_page: Page | None = None,
) -> None:
    from utils.ms_app_auth import resolve_ms_app_pipeline

    ms_app_assigned_pipeline = resolve_ms_app_pipeline(
        bucket, ms_app_assigned_pipeline
    )
    if ms_app_open_via_crm is None:
        ms_app_open_via_crm = True
    if bucket == MY_DEALS_BUCKET:
        ensure_fe_mortgage_snapshot_unlocked(
            page,
            deal_name,
            bucket=MY_DEALS_BUCKET,
            assign_fe_agent=ms_app_assigned_pipeline == "fe",
        )

    snapshot = MortgageSnapshotPage(page)
    data = MortgageSnapshotData()
    snapshot.open()
    snapshot.open_snapshot(deal_name, bucket=bucket)
    verify_stage_entry_tabs(page, bucket=bucket, stage_key="mortgage_snapshot")
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
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    expect(snapshot.set_meeting_reminder_btn).to_be_visible()
    expect(snapshot.active_tab).to_be_visible()
    expect(snapshot.active_tab).to_have_attribute("data-state", "active")
    snapshot.reopen_snapshot_form_tab()
    captured_snapshot = snapshot.capture_snapshot_form_values()

    from utils.mortgage_snapshot_app_helpers import (
        GROUP_MORTGAGE_SNAPSHOT,
        GROUP_STAGE,
        record_grouped_flow_step,
        verify_mortgage_snapshot_app_workflow,
    )

    parent_nodeid = None
    if request_or_item is not None:
        parent_nodeid = getattr(
            getattr(request_or_item, "node", request_or_item), "nodeid", None
        )

    record_grouped_flow_step(
        parent_nodeid,
        group=GROUP_MORTGAGE_SNAPSHOT,
        step="Save",
        step_key="ms_snapshot_save",
        metadata={"deal_name": deal_name},
    )
    record_grouped_flow_step(
        parent_nodeid,
        group=GROUP_MORTGAGE_SNAPSHOT,
        step="Persistence",
        step_key="ms_snapshot_persistence",
        metadata={"deal_name": deal_name, "field_count": len(captured_snapshot)},
    )

    ms_app_result = verify_mortgage_snapshot_app_workflow(
        page,
        snapshot,
        deal_name,
        captured_snapshot,
        with_co_borrower=with_co_borrower,
        parent_nodeid=parent_nodeid,
        soft_fail=not fail_on_ms_app_error,
        include_regression_rerun=regression_ms_app,
        assigned_pipeline=ms_app_assigned_pipeline,
        browser=page.context.browser,
        enforce_ms_app_rbac=True,
        prefer_crm_button=ms_app_open_via_crm,
        sync_assignee=ms_app_assigned_pipeline != "admin",
        bucket=bucket,
        assignee_sync_page=assignee_sync_page,
    )
    if not ms_app_result.passed and fail_on_ms_app_error:
        raise AssertionError(
            ms_app_result.summary(workflow="Mortgage Snapshot App")
        )

    snapshot.reopen_snapshot_meeting_tab()
    snapshot.create_meeting(data)
    snapshot.fill_meeting_details(data)
    snapshot.verify_meeting_saved()
    snapshot.meeting_search_export(data)
    snapshot.meeting_menu_actions(data)
    snapshot.verify_meeting_updated()
    snapshot.delete_meeting(data)
    snapshot.verify_meeting_deleted()
    snapshot.complete_stage()
    snapshot.verify_stage_completed()
    record_grouped_flow_step(
        parent_nodeid,
        group=GROUP_STAGE,
        step="Mortgage Snapshot",
        step_key="ms_stage_complete",
        metadata={
            "deal_name": deal_name,
            "ms_app_passed": ms_app_result.passed,
        },
    )
 
    snapshot_handlers = StageFormHandlers(
        capture=snapshot.capture_snapshot_form_values,
        reopen=snapshot.reopen_snapshot_form_tab,
        read=snapshot.capture_snapshot_form_values,
        label="mortgage snapshot",
    )
    _complete_stage_verification(
        page,
        deal_name,
        bucket=bucket,
        stage_key="mortgage_snapshot",
        captured_values=captured_snapshot,
        handlers=snapshot_handlers,
        # success_toast=we.BE_MORTGAGE_SNAPSHOT_SUCCESS_TOAST,
    )


def run_appraisal_order_smoke(
    page: Page,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
) -> None:
    appraisal = AppraisalOrderPage(page)
    data = AppraisalOrderData()
    appraisal.open()
    appraisal.open_appraisal_order(deal_name, bucket=bucket)
    verify_stage_entry_tabs(page, bucket=bucket, stage_key="appraisal_order")
    appraisal.fill_appraisal_no(data)
    appraisal.verify_reason(data)
    appraisal.save_appraisal_order()
    appraisal.verify_saved()
    appraisal.verify_appraisal_ordered("no")
    appraisal.cancel_move_to_next_stage()
    appraisal.wait_for_appraisal_form_idle()
    appraisal.fill_appraisal_yes(data)
    appraisal.verify_yes_details(data)
    captured_appraisal = appraisal.capture_appraisal_yes_values()
    appraisal.save_appraisal_order()
    appraisal.verify_saved()
    appraisal.move_to_next_stage()
    appraisal.verify_next_stage_message()

    appraisal_handlers = StageFormHandlers(
        capture=appraisal.capture_appraisal_yes_values,
        reopen=appraisal.reopen_appraisal_tab,
        read=appraisal.capture_appraisal_yes_values,
        normalize=normalize_numeric,
        label="appraisal order",
    )
    toast = (
        we.BE_APPRAISAL_ORDER_SUCCESS_TOAST
        if bucket == SALES_BACKEND_BUCKET
        else "Lead moved to Submitted successfully"
    )
    _complete_stage_verification(
        page,
        deal_name,
        bucket=bucket,
        stage_key="appraisal_order",
        captured_values=captured_appraisal,
        handlers=appraisal_handlers,
        success_toast=toast,
    )


def run_submitted_smoke(
    page: Page,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
) -> None:
    submitted = SubmittedPage(page)
    data = SubmittedData()
    submitted.open()
    submitted.open_submitted(deal_name, bucket=bucket)
    verify_stage_entry_tabs(page, bucket=bucket, stage_key="submitted")

    submitted.fill_option(1, data.option1)
    submitted.save_option(1, data=data.option1)
    submitted.verify_saved()
    submitted.cancel_move_to_next_stage()
    submitted.verify_option_tab_enabled(2)
    submitted.fill_option(2, data.option2)
    submitted.save_option(2, data=data.option2)
    submitted.verify_saved()
    submitted.cancel_move_to_next_stage()
    submitted.verify_option_tab_enabled(3)
    submitted.fill_option(3, data.option3)
    submitted.verify_option_fields_filled(3, data.option3)
    captured_submitted = submitted.capture_option_values(3)
    submitted.save_option(3, data=data.option3)
    submitted.verify_saved()
    submitted.move_to_next_stage()
    submitted.verify_moved_to_approved()


    def _read_submitted_persist() -> dict[str, str]:
        return submitted.capture_option_values_if_enabled(
            3, fallback=captured_submitted
        )
    submitted_handlers = StageFormHandlers(
        capture=lambda: captured_submitted,
        reopen=submitted.reopen_submitted_tab,
        read=_read_submitted_persist,
        normalize=normalize_numeric,
        label="submitted option 3",
    )
    toast = (
        we.BE_SUBMITTED_SUCCESS_TOAST
        if bucket == SALES_BACKEND_BUCKET
        else "Lead moved to Approved successfully"
    )
    _complete_stage_verification(
        page,
        deal_name,
        bucket=bucket,
        stage_key="submitted",
        captured_values=captured_submitted,
        handlers=submitted_handlers,
        success_toast=toast,
    )


def run_approved_smoke(
    page: Page,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
    with_co_borrower: bool = True,
    request_or_item=None,
    browser=None,
    ntp_app_assigned_pipeline: Literal["fe", "be", "admin"] | None = None,
    ntp_app_open_via_crm: bool | None = None,
    fail_on_ntp_app_error: bool = False,
    assignee_sync_page: Page | None = None,
    verify_ntp_app: bool = True,
    ntp_sync_assignee: bool = False,
) -> None:
    from utils.ms_app_auth import resolve_ms_app_pipeline
    from utils.ntp_app_helpers import verify_ntp_app_workflow

    ntp_app_assigned_pipeline = resolve_ms_app_pipeline(
        bucket, ntp_app_assigned_pipeline
    )
    if browser is None:
        browser = page.context.browser
    if ntp_app_open_via_crm is None:
        ntp_app_open_via_crm = True

    prefill = FormPrefillVerification(page)
    snapshot = MortgageSnapshotPage(page)
    snapshot.open_snapshot(deal_name, bucket=bucket)
    verify_stage_entry_tabs(page, bucket=bucket, stage_key="approved")
    snapshot_prefill = prefill.read_snapshot_prefill()
    prefill.verify_approved_prefilled_from_profile_and_snapshot(
        deal_name,
        bucket=bucket,
        snapshot_prefill=snapshot_prefill,
    )
    approved = ApprovedPage(page)
    data = ApprovedData()

    approved.verify_approved_form_tab_active() #commented out 
    approved.verify_mortgage_option_prefilled() #commented out

    # NTP expectations: capture snapshot/profile before save (no tab detour after save).
    snapshot.reopen_snapshot_form_tab()
    captured_snapshot = snapshot.capture_snapshot_form_values()
    profile = ProfilePage(page)
    profile_full_name = profile.read_lead_name()
    form_filled_at = profile.read_form_filled_at()
    approved.reopen_approved_form_tab()

    approved.fill_approved_form(data.form)
    approved.save_approved_form()
    approved.verify_form_saved()
    # CRM auto-opens Appraisal Completed — assert only, do not navigate there for NTP.
    approved.verify_approved_completed_tab_enabled()
    approved.verify_approved_completed_tab_active()
    approved.reopen_approved_form_tab()
    captured_approved = approved.capture_approved_form_values()

    if verify_ntp_app:
        parent_nodeid = None
        if request_or_item is not None:
            parent_nodeid = getattr(
                getattr(request_or_item, "node", request_or_item), "nodeid", None
            )
        ntp_result = verify_ntp_app_workflow(
            page,
            approved,
            deal_name,
            captured_approved,
            captured_snapshot,
            profile_full_name=profile_full_name,
            form_filled_at=form_filled_at,
            with_co_borrower=with_co_borrower,
            parent_nodeid=parent_nodeid,
            soft_fail=not fail_on_ntp_app_error,
            assigned_pipeline=ntp_app_assigned_pipeline,
            browser=browser,
            prefer_crm_button=ntp_app_open_via_crm,
            sync_assignee=ntp_sync_assignee,
            bucket=bucket,
            assignee_sync_page=assignee_sync_page,
        )
        if not ntp_result.passed and fail_on_ntp_app_error:
            raise AssertionError(ntp_result.summary(workflow="NTP Application"))
        approved.reopen_approved_completed_tab()

    approved.fill_approved_completed(data.approved_completed)
    approved.complete_stage()
    approved.verify_form_saved()
    approved.move_to_next_stage()
    approved.verify_moved_to_signed()

    approved_handlers = StageFormHandlers(
        capture=approved.capture_approved_form_values,
        reopen=approved.reopen_approved_form_tab,
        read=approved.capture_approved_form_values,
        normalize=normalize_numeric,
        label="approved form",
    )
    toast = (
        we.BE_APPROVED_SUCCESS_TOAST
        if bucket == SALES_BACKEND_BUCKET
        else "Lead moved to Signed successfully"
    )
    _complete_stage_verification(
        page,
        deal_name,
        bucket=bucket,
        stage_key="approved",
        captured_values=captured_approved,
        handlers=approved_handlers,
        success_toast=toast,
    )


def run_signed_compliance_smoke(
    page: Page,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
    role: Literal["admin", "agent"] = "admin",
) -> None:
    signed = SignedPage(page)

    data = SignedData()
    approved_data = ApprovedData()
    approved = ApprovedPage(page)

    if re.search(r"/(sales|sales-backend)/[A-Za-z0-9]+", page.url):
        signed.ensure_signed_form()
    else:
        signed.open_signed(deal_name, bucket=bucket)

    signed.select_client_signed_no()
    signed.verify_not_signed_reason_visible()
    signed.verify_final_product_section_hidden()
    signed.fill_not_signed_reason(data.no_flow.not_signed_reason)
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.move_to_next_stage()
    signed.verify_moved_to_not_signed()

    # --- Switch back to Yes ---
    signed.select_client_signed_yes()
    signed.verify_not_signed_reason_hidden()
    signed.verify_final_product_section_visible()
    signed.verify_signed_details_prefilled()
    signed.verify_lender_name_prefilled()

    # --- Flow 1: Final Product No → Resigning back to Submitted ---
    signed.select_final_product_no()
    signed.verify_deal_tracking_sections_hidden()
    signed.select_resigning_back_to_submitted()
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.verify_moved_to_approved()

    # --- Re-complete Approved stage ---
    signed.click(approved.approved_tab)
    signed.verify_signed_tab_hidden()
    approved.verify_approved_form_tab_active()
    approved.verify_mortgage_option_prefilled()
    approved.fill_approved_form(approved_data.form)
    approved.save_approved_form()
    approved.verify_form_saved()
    approved.verify_approved_completed_tab_active()
    approved.fill_approved_completed(approved_data.approved_completed)
    approved.complete_stage()
    approved.verify_form_saved()
    approved.move_to_next_stage()
    approved.verify_moved_to_signed()

    # --- Flow 2: Final Product Yes ---

    verify_stage_entry_tabs(page, bucket=bucket, stage_key="signed")
    signed.select_client_signed_yes()
    signed.select_final_product_yes()
    signed.verify_deal_tracking_sections_visible()

    signed.select_outstanding_condition_no()
    signed.verify_outstanding_conditions_details_hidden()

    signed.fill_final_product_yes_sections(data.final_yes)
    signed.save_signed_form()
    signed.verify_signed_saved()
    captured_signed = signed.capture_signed_yes_values()
    signed.move_to_next_stage()
    
    signed_handlers = StageFormHandlers(
        capture=signed.capture_signed_yes_values,
        reopen=signed.reopen_signed_tab,
        read=signed.capture_signed_yes_values,
        normalize=normalize_numeric,
        label="signed form",
    )
    _complete_stage_verification(
        page,
        deal_name,
        bucket=bucket,
        stage_key="signed",
        captured_values=captured_signed,
        handlers=signed_handlers,
        
    )

    # --- Google Review ---
    signed.verify_google_review_visible()
    signed.select_good_for_google_review_yes()
    signed.set_closed_checked(False)
    signed.save_google_review()
    signed.verify_google_review_saved()
    signed.verify_still_on_signed_tab()

    signed.set_closed_checked(True)
   
    signed.save_google_review(expect_compliance_move=True, role=role)
    signed.complete_google_review_compliance_move(role=role)
    


def run_backend_signed_compliance_smoke(
    page: Page,
    deal_name: str,
    *,
    role: Literal["admin", "agent"] = "admin",
) -> None:
    """Signed (Compliance disposition) on Sales Backend."""
    run_signed_compliance_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET, role=role)


def run_signed_marketing_smoke(page: Page, deal_name: str, *, bucket=MY_DEALS_BUCKET) -> None:
    signed_marketing = SignedMarketingPage(page)
    signed_marketing.signed.open()
    signed_marketing.signed.open_signed(deal_name, bucket=bucket)
    signed_marketing.verify_signed_marketing_prefill()
    signed_marketing.select_final_product_no()
    signed_marketing.select_dead_move_to_marketing()
    signed_marketing.save_and_verify_marketing_disposition()


def run_compliance_smoke(page: Page, deal_name: str):
    compliance = CompliancePage(page)
    data = ComplianceData()
    compliance.open()
    compliance.open_compliance_deal(deal_name)
    compliance.open_signed_closed_tab()
    compliance.open_signed_form_tab()
    compliance.verify_signed_form_readonly()
    signed_baseline = compliance.read_signed_form_readonly_values()
    compliance.verify_signed_form_has_data(signed_baseline)
    compliance.open_compliance_form_tab()
    compliance.fill_closing_compliance(data.closing)
    compliance.save_closing_compliance()
    compliance.verify_closing_compliance_saved()
    compliance.fill_client_care_checks(data.client_care)
    compliance.save_client_care_checks()
    compliance.verify_client_care_checks_saved()
    save_signed_form_baseline(signed_baseline)
    compliance.open_compliance_form_tab()
    compliance.complete_stage()
    compliance.verify_moved_to_client_care_toast()
    compliance.verify_on_client_care_page()
    compliance.verify_lead_in_client_care(deal_name)
    return signed_baseline


def run_client_care_smoke(page: Page, deal_name: str, signed_baseline) -> None:
    client_care = ClientCarePage(page)
    client_care.open()
    client_care.verify_lead_searchable(deal_name)
    client_care.open_client_care_deal(deal_name)
    client_care.open_just_closed_tab()
    client_care.verify_just_closed_sections_visible()
    client_care.verify_just_closed_readonly()
    client_care.verify_just_closed_has_no_save_action()
    just_closed_snapshot = client_care.read_just_closed_values()
    client_care.verify_just_closed_has_data(just_closed_snapshot)
    assert signed_baseline, "Signed Form baseline required for Client Care verification"
    client_care.verify_just_closed_matches(signed_baseline)


def run_marketing_smoke(page: Page, deal_name: str) -> None:
    marketing = MarketingPage(page)
    marketing.open()
    marketing.verify_lead_searchable(deal_name)
    marketing.verify_lead_in_marketing(deal_name)
    marketing.verify_on_marketing_list()


def run_backend_pre_stage_smoke(page: Page, deal_name: str) -> None:
    """Edit Lead, Co-Borrower, and Notes on Sales Backend before stage progression."""
    run_lead_edit_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET)
    run_co_borrower_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET)
    run_notes_smoke(page, deal_name, move_to_sales=False, bucket=SALES_BACKEND_BUCKET)


def run_fe_pre_stage_smoke(page: Page, deal_name: str) -> None:
    """Edit Lead, Co-Borrower, and Notes on Sales Frontend (My Deals)."""
    run_lead_edit_smoke(page, deal_name, bucket=MY_DEALS_BUCKET)
    run_co_borrower_smoke(page, deal_name, bucket=MY_DEALS_BUCKET)
    run_notes_smoke(page, deal_name, move_to_sales=False, bucket=MY_DEALS_BUCKET)


def setup_admin_fe_lead(admin_page: Page) -> str:
    """Admin creates a lead and Nova-bypasses to the FE agent."""
    lead_name = create_lead_smoke(admin_page)
    run_nova_bypass_smoke(admin_page, lead_name)
    return lead_name


def setup_admin_be_lead(admin_page: Page) -> str:
    """Admin creates a lead and assigns the BE agent with Sales Backend status."""
    lead_name = create_lead_smoke(admin_page)
    LeadAssignmentHelper(admin_page).assign_be_backend(lead_name)
    return lead_name


def setup_be_assigned_lead(admin_page: Page) -> str:
    """Alias for setup_admin_be_lead — backward compatible."""
    return setup_admin_be_lead(admin_page)



def run_backend_mortgage_snapshot_smoke(
    page: Page,
    deal_name: str,
    *,
    request_or_item=None,
    regression_ms_app: bool = False,
    assignee_sync_page: Page | None = None,
) -> None:
    run_mortgage_snapshot_smoke(
        page,
        deal_name,
        bucket=SALES_BACKEND_BUCKET,
        request_or_item=request_or_item,
        regression_ms_app=regression_ms_app,
        ms_app_assigned_pipeline="be",
        assignee_sync_page=assignee_sync_page,
    )


def run_backend_appraisal_order_smoke(page: Page, deal_name: str) -> None:
    run_appraisal_order_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET)


def run_backend_submitted_smoke(page: Page, deal_name: str) -> None:
    run_submitted_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET)


def run_backend_approved_smoke(
    page: Page,
    deal_name: str,
    *,
    request_or_item=None,
    browser=None,
    assignee_sync_page: Page | None = None,
    verify_ntp_app: bool = True,
    ntp_sync_assignee: bool = False,
) -> None:
    run_approved_smoke(
        page,
        deal_name,
        bucket=SALES_BACKEND_BUCKET,
        request_or_item=request_or_item,
        browser=browser,
        ntp_app_assigned_pipeline="be",
        assignee_sync_page=assignee_sync_page,
        verify_ntp_app=verify_ntp_app,
        ntp_sync_assignee=ntp_sync_assignee,
    )


def run_backend_signed_smoke(
    page: Page,
    deal_name: str,
    *,
    role: Literal["admin", "agent"] = "admin",
) -> None:
    signed = SignedPage(page)

    data = SignedData()
    approved_data = ApprovedData()
    approved = ApprovedPage(page)

    if re.search(r"/(sales|sales-backend)/[A-Za-z0-9]+", page.url):
        signed.ensure_signed_form()
    else:
        signed.open_signed(deal_name, bucket=SALES_BACKEND_BUCKET)

    verify_stage_entry_tabs(page, bucket=SALES_BACKEND_BUCKET, stage_key="signed")
    signed.select_client_signed_no()
    signed.verify_not_signed_reason_visible()
    signed.verify_final_product_section_hidden()
    signed.fill_not_signed_reason(data.no_flow.not_signed_reason)
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.move_to_next_stage()
    signed.verify_moved_to_not_signed()

    # --- Switch back to Yes ---
    signed.select_client_signed_yes()
    signed.verify_not_signed_reason_hidden()
    signed.verify_final_product_section_visible()
    signed.verify_signed_details_prefilled()
    signed.verify_lender_name_prefilled()

    # --- Flow 1: Final Product No → Resigning back to Submitted ---
    signed.select_final_product_no()
    signed.verify_deal_tracking_sections_hidden()
    signed.select_resigning_back_to_submitted()
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.verify_moved_to_approved()

    # --- Re-complete Approved stage ---
    signed.click(approved.approved_tab)
    signed.verify_signed_tab_hidden()
    approved.verify_approved_form_tab_active()
    approved.verify_mortgage_option_prefilled()
    approved.fill_approved_form(approved_data.form)
    approved.save_approved_form()
    approved.verify_form_saved()
    approved.verify_approved_completed_tab_active()
    approved.fill_approved_completed(approved_data.approved_completed)
    approved.complete_stage()
    approved.verify_form_saved()
    approved.move_to_next_stage()
    approved.verify_moved_to_signed()

    # --- Flow 2: Final Product Yes ---
    verify_stage_entry_tabs(page, bucket=SALES_BACKEND_BUCKET, stage_key="signed")
    signed.select_client_signed_yes()
    signed.select_final_product_yes()
    signed.verify_deal_tracking_sections_visible()

    # Outstanding Conditions visibility + validation
    signed.select_outstanding_condition_yes()
    signed.verify_outstanding_conditions_details_visible()
    signed.fill_outstanding_conditions_details(
        data.final_yes.short_outstanding_conditions
    )
    signed.save_signed_form()
    signed.verify_outstanding_conditions_min_length_error()

    signed.fill_outstanding_conditions_details(
        data.final_yes.outstanding_conditions_details
    )
    signed.select_outstanding_condition_no()
    signed.verify_outstanding_conditions_details_hidden()

    signed.fill_final_product_yes_sections(data.final_yes)
    signed.save_signed_form()
    signed.verify_signed_saved()
    captured_signed = signed.capture_signed_yes_values()
    signed.move_to_next_stage()
    signed_handlers = StageFormHandlers(
        capture=signed.capture_signed_yes_values,
        reopen=signed.reopen_signed_tab,
        read=signed.capture_signed_yes_values,
        normalize=normalize_numeric,
        label="signed form",
    )
    _complete_stage_verification(
        page,
        deal_name,
        bucket=SALES_BACKEND_BUCKET,
        stage_key="signed",
        captured_values=captured_signed,
        handlers=signed_handlers,
        success_toast="Lead moved to Signed successfully",
    )

    # --- Google Review ---
    signed.verify_google_review_visible()
    signed.select_good_for_google_review_yes()
    signed.set_closed_checked(False)
    signed.save_google_review()
    signed.verify_google_review_saved()
    signed.verify_still_on_signed_tab()

    signed.set_closed_checked(True)
    signed.save_google_review(expect_compliance_move=True, role=role)
    signed.complete_google_review_compliance_move(role=role)


def run_backend_full_flow(page: Page, deal_name: str, *, include_pre_stage: bool = True) -> str:
    """Orchestrate the full Sales Backend pipeline through Signed."""
    if include_pre_stage:
        run_backend_pre_stage_smoke(page, deal_name)
    run_backend_mortgage_snapshot_smoke(page, deal_name)
    run_backend_appraisal_order_smoke(page, deal_name)
    run_backend_submitted_smoke(page, deal_name)
    run_backend_approved_smoke(page, deal_name)
    run_backend_signed_smoke(page, deal_name)
    return deal_name


def run_fe_sales_stages_smoke(
    page: Page,
    deal_name: str,
    *,
    request_or_item=None,
    regression_ms_app: bool = False,
    assignee_sync_page: Page | None = None,
    browser=None,
    verify_ntp_app: bool = True,
    ntp_sync_assignee: bool = False,
) -> None:
    """Mortgage Snapshot through Approved on Sales Frontend (My Deals)."""
    run_mortgage_snapshot_smoke(
        page,
        deal_name,
        bucket=MY_DEALS_BUCKET,
        request_or_item=request_or_item,
        regression_ms_app=regression_ms_app,
        ms_app_assigned_pipeline="fe",
        assignee_sync_page=assignee_sync_page,
    )
    run_appraisal_order_smoke(page, deal_name, bucket=MY_DEALS_BUCKET)
    run_submitted_smoke(page, deal_name, bucket=MY_DEALS_BUCKET)
    run_approved_smoke(
        page,
        deal_name,
        bucket=MY_DEALS_BUCKET,
        request_or_item=request_or_item,
        browser=browser,
        ntp_app_assigned_pipeline="fe",
        assignee_sync_page=assignee_sync_page,
        verify_ntp_app=verify_ntp_app,
        ntp_sync_assignee=ntp_sync_assignee,
    )


def run_through_approved_smoke(page: Page) -> str:
    lead_name = create_lead_smoke(page)
    run_nova_bypass_smoke(page, lead_name)
    run_fe_pre_stage_smoke(page, lead_name)
    run_fe_sales_stages_smoke(page, lead_name)
    return lead_name
