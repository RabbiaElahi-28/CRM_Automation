import pytest

from pages.note_page import NotesPage
from test_page_data import test_entities
from utils.entity_navigation import MY_DEALS_BUCKET
from utils.lead_context import get_active_deal_name, get_lead_context
from utils.reporting import register_test_data
from utils.workflow_verification import MOVE_TO_SALES_TRANSITION, WorkflowVerification

@pytest.mark.module_smoke
def test_move_to_sales_flow(authenticated_page, request):
    # """Official CRM Move to Sales: create → assign → Move to Sales → /sales redirect."""
    """Verify bootstrap lead reached My Deals after notes move-to-sales.

    Does not create a new lead — reuses the session bootstrap lead so
    downstream stage tests always operate on the same record.
    """
    page = authenticated_page
    deal_name = get_active_deal_name()
    register_test_data(request.node, flow="move_to_sales_verify", lead_name=deal_name)

    notes = NotesPage(page)
    notes.open()
    notes.open_lead(deal_name, bucket=MY_DEALS_BUCKET)
    WorkflowVerification(page).verify_transition(
        MOVE_TO_SALES_TRANSITION,
        record_name=deal_name,
        skip_toast=True,
    )
    assert get_lead_context().is_bootstrapped or deal_name == test_entities.MY_DEALS_DEAL_NAME
