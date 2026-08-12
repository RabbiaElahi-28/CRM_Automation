import pytest

from pages.create_lead import CreateLeadPage
from test_page_data import test_entities
from test_page_data.validation_cases import CREATE_LEAD_EMPTY, CREATE_LEAD_INVALID
from utils.lead_assignment import assign_agent_after_create
from utils.logger import get_logger
import utils.test_data_factory as data
from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields
from utils.toast import Toast
from utils.reporting import register_test_data
from utils.test_data_factory import valid_lead_data
from test_page_data.test_entities import persist_my_leads_deal_name
from utils.validations import Validations

logger = get_logger()

cases = data.get_lead_cases()


def test_create_lead_empty(authenticated_page, request):
    """Submit create-lead form with all editable fields cleared."""
    page = CreateLeadPage(authenticated_page)
    validator = Validations(authenticated_page)

    page.open()
    page.clear_all_fields()
    page.submit_lead()

    register_test_data(request.node, scenario="empty_form")
    verify_required_fields(validator, CREATE_LEAD_EMPTY, item=request.node)


def test_create_lead_invalid(authenticated_page, request):
    """Submit create-lead form with every schema-invalid field value."""
    page = CreateLeadPage(authenticated_page)
    validator = Validations(authenticated_page)
    baseline = valid_lead_data()

    page.open()
    page.fill_form(baseline)

    register_test_data(request.node, scenario="all_invalid_fields", data=baseline)

    verify_invalid_fields(
        validator,
        CREATE_LEAD_INVALID,
        page.set_field,
        page.clear_field,
        page.submit_lead,
        item=request.node,
        reset=lambda: page.restore_baseline_for_invalid_tests(baseline),
    )


@pytest.mark.parametrize(
    "lead_data, is_valid, expected_message",
    [(case[1], case[2], case[3]) for case in cases],
    ids=[case[0] for case in cases],
)
def test_valid_create_lead(authenticated_page, lead_data, is_valid, expected_message):
    logger.info(f"Creating lead (expected valid={is_valid}) with data: {lead_data}")

    create_lead_page = CreateLeadPage(authenticated_page)
    create_lead_page.open()
    create_lead_page.fill_form(lead_data)
    create_lead_page.submit_lead()
    toast = Toast(authenticated_page)

    toast.assert_visible()
    toast.assert_message(expected_message)

    if is_valid:
        persist_my_leads_deal_name(lead_data["enter_name"])
        assign_agent_after_create(authenticated_page, test_entities.MY_LEADS_DEAL_NAME)
