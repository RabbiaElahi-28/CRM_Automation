"""MS App RBAC: non-assigned agents must not see synced leads."""

from __future__ import annotations

import pytest

from pages.mortgage_snapshot_app.leads_page import MortgageSnapshotAppLeadsPage
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from test_page_data.mortgage_snapshot_data import MortgageSnapshotData
from test_page_data.test_entities import MY_DEALS_DEAL_NAME
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, SALES_BACKEND_BUCKET
from utils.lead_assignment import LeadAssignmentHelper
from utils.mortgage_snapshot_app_helpers import (
    _search_kwargs,
    expectations_from_captured,
    logout_and_close_ms_app_tab,
    open_ms_app_for_assigned_user,
)
from utils.ms_app_auth import (
    MsAppPipeline,
    cross_role_pipeline,
    ensure_ms_app_lead_assignee,
    open_ms_app_rbac_page,
    pipeline_label,
)
from utils.ms_app_rbac import capture_presentation_url, verify_ms_app_non_assigned_access_denied
from utils.sales_flow_helpers import ensure_fe_mortgage_snapshot_unlocked


def _prepare_bucket(page, deal_name: str, assigned_pipeline: MsAppPipeline) -> str:
    bucket = MY_DEALS_BUCKET
    if assigned_pipeline == "be":
        LeadAssignmentHelper(page).assign_be_backend(deal_name)
        bucket = SALES_BACKEND_BUCKET
    else:
        ensure_fe_mortgage_snapshot_unlocked(page, deal_name, bucket=bucket)
    return bucket


def _bootstrap_ms_app_lead(
    page,
    *,
    deal_name: str,
    assigned_pipeline: MsAppPipeline,
):
    bucket = _prepare_bucket(page, deal_name, assigned_pipeline)
    ensure_ms_app_lead_assignee(page, deal_name, assigned_pipeline, bucket=bucket)

    data = MortgageSnapshotData()
    snapshot = MortgageSnapshotPage(page)
    snapshot.click(snapshot.snapshot_tab)
    snapshot.click(snapshot.snapshot_form_tab)
    snapshot.fill_valid_baseline(data)
    snapshot.save()
    snapshot.verify_saved()
    snapshot.reopen_snapshot_form_tab()
    captured = snapshot.capture_snapshot_form_values()
    expectations = expectations_from_captured(
        deal_name, captured, with_co_borrower=False
    )
    return snapshot, expectations, bucket


@pytest.mark.smoke
@pytest.mark.parametrize(
    "assigned_pipeline",
    ["admin", "fe", "be"],
    ids=["admin", "fe", "be"],
)
def test_ms_app_rbac_non_assigned_denied(
    authenticated_page,
    browser,
    assigned_pipeline: MsAppPipeline,
):
    """Assigned user sees lead; cross-role CRM user cannot search or open it."""
    page = authenticated_page
    deal_name = MY_DEALS_DEAL_NAME
    cross_pipeline = cross_role_pipeline(assigned_pipeline)

    snapshot, expectations, bucket = _bootstrap_ms_app_lead(
        page,
        deal_name=deal_name,
        assigned_pipeline=assigned_pipeline,
    )

    app_page = open_ms_app_for_assigned_user(
        page,
        snapshot,
        assigned_pipeline=assigned_pipeline,
        browser=browser,
        prefer_crm_button=assigned_pipeline == "admin",
    )
    leads = MortgageSnapshotAppLeadsPage(app_page)
    leads.search_lead(
        deal_name,
        **_search_kwargs(expectations),
        wait_timeout_ms=Config.MS_APP_LEAD_SYNC_TIMEOUT_MS,
    )
    leads.verify_lead_search_all_identifiers(
        deal_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.applicant_first_name,
    )
    leads.search_by_deal_name(deal_name, email=expectations.lead_email or None)
    leads.open_lead_presentation(deal_name)
    presentation_url = capture_presentation_url(app_page)
    logout_and_close_ms_app_tab(app_page)

    rbac_page = open_ms_app_rbac_page(page.context, cross_pipeline)
    try:
        verify_ms_app_non_assigned_access_denied(
            rbac_page,
            assigned_pipeline=assigned_pipeline,
            lead_name=deal_name,
            expectations=expectations,
            presentation_url=presentation_url,
        )
    finally:
        rbac_page.close()

    assigned_label = pipeline_label(assigned_pipeline)
    cross_label = pipeline_label(cross_pipeline)
    assert assigned_label and cross_label
