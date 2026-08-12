"""Sales Backend Agent RBAC validation after Admin backend assignment."""

import re

import pytest
from playwright.sync_api import expect

from pages.create_lead import CreateLeadPage
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from pages.note_page import NotesPage
from test_page_data import test_entities
from utils.config import Config
from utils.entity_navigation import SALES_BACKEND_BUCKET, open_bucket_record
from utils.lead_assignment import LeadAssignmentHelper
from utils.reporting import register_test_data
from utils.sales_flow_helpers import create_lead_smoke
from utils.test_data_factory import valid_lead_data
from utils.toast import Toast
from utils.workflow_verification import (
    BE_ASSIGNMENT_TRANSITION,
    BE_NON_ASSIGNED_RESTRICTED,
    WorkflowVerification,
)
from test_page_data import workflow_expectations as we


def _create_lead_without_assignment(page) -> str:
    lead_data = valid_lead_data()
    create = CreateLeadPage(page)
    create.open()
    create.fill_form(lead_data)
    create.submit_lead()
    Toast(page).assert_message("Lead created successfully")
    return lead_data["enter_name"]


def _skip_if_be_agent_unauthenticated(page) -> None:
    page.goto(Config.BASE_URL)
    page.wait_for_load_state("domcontentloaded")
    if "/login" in page.url:
        pytest.skip(
            "BE agent credentials unavailable on dev CRM — cannot validate RBAC."
        )


@pytest.mark.be_agent
@pytest.mark.module_smoke
def test_be_agent_rbac_assigned_after_backend_assignment(admin_page, be_agent_page, request):
    """
    Admin creates a lead and assigns BE agent + backend status; BE agent validates RBAC.

    Shared stage page objects reuse the same DOM on /sales-backend detail pages.
    """
    _skip_if_be_agent_unauthenticated(be_agent_page)

    lead_name = create_lead_smoke(admin_page)
    LeadAssignmentHelper(admin_page).assign_be_backend(lead_name)
    register_test_data(
        request.node,
        flow="be_agent_rbac",
        lead_name=lead_name,
        be_agent=test_entities.BE_AGENT_LABEL,
    )

    verifier = WorkflowVerification(be_agent_page)

    verifier.verify_kanban_columns(
        SALES_BACKEND_BUCKET, list(we.BE_SALES_BACKEND_KANBAN_COLUMNS)
    )
    verifier.verify_be_agent_assignment(lead_name)
    open_bucket_record(be_agent_page, SALES_BACKEND_BUCKET, lead_name)

    verifier.verify_url(BE_ASSIGNMENT_TRANSITION.expected_url_pattern)
    verifier.verify_status_badge(
        contains=BE_ASSIGNMENT_TRANSITION.expected_status_contains,
    )
    verifier.verify_be_agent_has_full_access(BE_ASSIGNMENT_TRANSITION.visible_tabs)
    verifier.verify_tabs_visible(BE_ASSIGNMENT_TRANSITION.visible_tabs)
    if BE_ASSIGNMENT_TRANSITION.hidden_tabs:
        verifier.verify_tabs_hidden(BE_ASSIGNMENT_TRANSITION.hidden_tabs)

    snapshot = MortgageSnapshotPage(be_agent_page)
    snapshot.open_snapshot(lead_name, bucket=SALES_BACKEND_BUCKET)
    expect(be_agent_page).to_have_url(
        re.compile(r"/sales-backend/"),
        timeout=Config.TIMEOUT,
    )
    mortgage_tab = be_agent_page.get_by_role("tab", name="Mortgage Snapshot", exact=True)
    expect(mortgage_tab).to_have_attribute("data-state", "active", timeout=Config.TIMEOUT)
    expect(be_agent_page.get_by_role("tab", name="Mortgage Snapshot Form")).to_be_visible(
        timeout=Config.TIMEOUT,
    )


@pytest.mark.be_agent
@pytest.mark.module_smoke
def test_be_agent_rbac_non_assigned_via_header_search(
    admin_page, be_agent_page, request
):
    """Non-assigned BE agent opens another user's lead via header global search."""
    _skip_if_be_agent_unauthenticated(be_agent_page)

    lead_name = _create_lead_without_assignment(admin_page)
    notes = NotesPage(admin_page)
    notes.open()
    notes.open_lead(lead_name)
    notes.move_to_sales()
    register_test_data(
        request.node,
        flow="be_agent_rbac_non_assigned",
        lead_name=lead_name,
    )

    verifier = WorkflowVerification(be_agent_page)
    verifier.verify_non_assigned_rbac_via_header_search(
        lead_name, BE_NON_ASSIGNED_RESTRICTED
    )
