"""Sales Frontend Agent RBAC validation after Admin Nova bypass setup."""

import pytest
from playwright.sync_api import expect

from pages.create_lead import CreateLeadPage
from pages.note_page import NotesPage
from test_page_data import test_entities
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record
from utils.lead_assignment import LeadAssignmentHelper
from utils.reporting import register_test_data
from utils.sales_flow_helpers import create_lead_smoke
from utils.test_data_factory import valid_lead_data
from utils.toast import Toast
from utils.workflow_verification import (
    FE_NOVA_BYPASS_SALES_TRANSITION,
    FE_NON_ASSIGNED_RESTRICTED,
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


def _skip_if_fe_agent_unauthenticated(page) -> None:
    page.goto(Config.BASE_URL)
    page.wait_for_load_state("domcontentloaded")
    if "/login" in page.url:
        pytest.skip(
            "FE agent credentials unavailable on dev CRM — cannot validate RBAC."
        )


@pytest.mark.fe_agent
@pytest.mark.module_smoke
def test_fe_agent_rbac_assigned_after_nova_bypass(admin_page, fe_agent_page, request):
    """
    Admin creates a lead and Nova-bypasses to FE agent; FE agent validates RBAC on /sales.

    CRM note: post-nova-bypass leads live in the My Deals kanban (/sales), not My Leads
    (My Leads filters statusType=lead). Bucket check uses MY_DEALS_BUCKET for FE.
    """
    _skip_if_fe_agent_unauthenticated(fe_agent_page)

    lead_name = create_lead_smoke(admin_page)
    LeadAssignmentHelper(admin_page).assign_fe_nova_bypass(lead_name)
    register_test_data(
        request.node,
        flow="fe_agent_rbac",
        lead_name=lead_name,
        fe_agent=test_entities.FE_AGENT_LABEL,
    )

    verifier = WorkflowVerification(fe_agent_page)

    verifier.verify_kanban_columns(
        MY_DEALS_BUCKET, list(we.FE_MY_DEALS_KANBAN_COLUMNS)
    )
    verifier.verify_fe_agent_assignment(lead_name)
    open_bucket_record(fe_agent_page, MY_DEALS_BUCKET, lead_name)

    verifier.verify_url(FE_NOVA_BYPASS_SALES_TRANSITION.expected_url_pattern)
    verifier.verify_status_badge(
        contains=FE_NOVA_BYPASS_SALES_TRANSITION.expected_status_contains,
    )
    verifier.verify_fe_agent_has_full_access(FE_NOVA_BYPASS_SALES_TRANSITION.visible_tabs)
    verifier.verify_tabs_visible(FE_NOVA_BYPASS_SALES_TRANSITION.visible_tabs)
    verifier.verify_tabs_hidden(FE_NOVA_BYPASS_SALES_TRANSITION.hidden_tabs)

    mortgage_tab = fe_agent_page.get_by_role("tab", name="Mortgage Snapshot")
    expect(mortgage_tab).to_be_visible(timeout=Config.TIMEOUT)
    mortgage_tab.click()
    expect(mortgage_tab).to_have_attribute("data-state", "active", timeout=Config.TIMEOUT)
    expect(fe_agent_page.get_by_role("tab", name="Mortgage Snapshot Form")).to_be_visible(
        timeout=Config.TIMEOUT,
    )


@pytest.mark.fe_agent
@pytest.mark.module_smoke
def test_fe_agent_rbac_non_assigned_via_header_search(
    admin_page, fe_agent_page, request
):
    """Non-assigned FE agent opens another user's lead via header global search."""
    _skip_if_fe_agent_unauthenticated(fe_agent_page)

    lead_name = _create_lead_without_assignment(admin_page)
    notes = NotesPage(admin_page)
    notes.open()
    notes.open_lead(lead_name)
    notes.move_to_sales()
    register_test_data(
        request.node,
        flow="fe_agent_rbac_non_assigned",
        lead_name=lead_name,
    )

    verifier = WorkflowVerification(fe_agent_page)
    verifier.verify_non_assigned_rbac_via_header_search(
        lead_name, FE_NON_ASSIGNED_RESTRICTED
    )
