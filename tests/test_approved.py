import pytest

from pages.approved_page import ApprovedPage
from test_page_data.approved_data import ApprovedData
from test_page_data import test_entities
from test_page_data.validation_cases import APPROVED_EMPTY, APPROVED_INVALID
from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields
from utils.lead_context import get_active_deal_name
from utils.reporting import register_test_data
from utils.sales_flow_helpers import run_approved_smoke
from utils.validations import Validations


def test_approved_empty(authenticated_page, request):
    """Save approved form with all required fields cleared."""
    approved = ApprovedPage(authenticated_page)
    validator = Validations(authenticated_page)

    approved.open()
    approved.open_approved(test_entities.MY_DEALS_DEAL_NAME)
    approved.clear_all_approved_form_fields()
    approved.save_approved_form()

    register_test_data(request.node, scenario="empty_form", deal_name=test_entities.MY_DEALS_DEAL_NAME)
    verify_required_fields(validator, APPROVED_EMPTY, item=request.node)


def test_approved_invalid(authenticated_page, request):
    """Save approved form with every schema-invalid field value."""
    approved = ApprovedPage(authenticated_page)
    validator = Validations(authenticated_page)

    approved.open()
    approved.open_approved(test_entities.MY_DEALS_DEAL_NAME)
    approved.prepare_valid_baseline_for_invalid_tests()

    register_test_data(
        request.node, scenario="all_invalid_fields", deal_name=test_entities.MY_DEALS_DEAL_NAME
    )

    verify_invalid_fields(
        validator,
        APPROVED_INVALID,
        approved.set_field,
        approved.clear_field,
        approved.save_approved_form,
        item=request.node,
        reset=approved.prepare_valid_baseline_for_invalid_tests,
    )


@pytest.mark.module_smoke
def test_approved(authenticated_page, request):
    deal_name = get_active_deal_name()
    data = ApprovedData()
    register_test_data(request.node, deal_name=deal_name, data=data)
    run_approved_smoke(authenticated_page, deal_name)

 