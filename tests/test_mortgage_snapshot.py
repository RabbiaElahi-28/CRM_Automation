from playwright.sync_api import expect

import pytest



from pages.mortgage_snapshot_page import MortgageSnapshotPage

from test_page_data.mortgage_snapshot_data import MortgageSnapshotData

from test_page_data import test_entities

from test_page_data.validation_cases import SNAPSHOT_EMPTY, SNAPSHOT_INVALID

from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields

from utils.lead_context import get_active_deal_name
from utils.reporting import register_test_data
from utils.sales_flow_helpers import run_mortgage_snapshot_smoke
from utils.validations import Validations





def test_mortgage_snapshot_empty(authenticated_page, request):

    """Save mortgage snapshot form with all fields cleared."""

    snapshot = MortgageSnapshotPage(authenticated_page)

    validator = Validations(authenticated_page)



    snapshot.open()

    snapshot.open_snapshot(test_entities.MY_DEALS_DEAL_NAME)

    snapshot.clear_all_snapshot_fields()

    snapshot.save()



    register_test_data(request.node, scenario="empty_form", deal_name=test_entities.MY_DEALS_DEAL_NAME)

    verify_required_fields(validator, SNAPSHOT_EMPTY, item=request.node)





def test_mortgage_snapshot_invalid(authenticated_page, request):

    """Save mortgage snapshot with every schema-invalid field value."""

    snapshot = MortgageSnapshotPage(authenticated_page)

    validator = Validations(authenticated_page)

    data = MortgageSnapshotData()



    snapshot.open()

    snapshot.open_snapshot(test_entities.MY_DEALS_DEAL_NAME)

    snapshot.fill_valid_baseline(data)



    register_test_data(

        request.node, scenario="all_invalid_fields", deal_name=test_entities.MY_DEALS_DEAL_NAME

    )



    verify_invalid_fields(

        validator,

        SNAPSHOT_INVALID,

        snapshot.set_snapshot_field,

        snapshot.clear_snapshot_field,

        snapshot.save,

        item=request.node,

        reset=lambda: snapshot.fill_valid_baseline(data),

    )



@pytest.mark.module_smoke
def test_create_mortgage_snapshot(authenticated_page, request):
    deal_name = get_active_deal_name()
    data = MortgageSnapshotData()
    register_test_data(request.node, deal_name=deal_name, data=data)
    run_mortgage_snapshot_smoke(authenticated_page, deal_name, request_or_item=request)


@pytest.mark.module_smoke
def test_blocked_mortgage_snapshot_stage_without_save(authenticated_page, request):
    """Meeting tab → Complete Stage must not advance lead when snapshot form was never saved."""
    from utils.workflow_verification import WorkflowVerification

    deal_name = test_entities.MY_DEALS_DEAL_NAME
    snapshot = MortgageSnapshotPage(authenticated_page)
    snapshot.open()
    snapshot.open_snapshot(deal_name)
    register_test_data(request.node, scenario="complete_blocked_without_save", deal_name=deal_name)
    WorkflowVerification(authenticated_page).verify_mortgage_snapshot_complete_blocked(
        expected_status="Mortgage Snapshot",
    )

