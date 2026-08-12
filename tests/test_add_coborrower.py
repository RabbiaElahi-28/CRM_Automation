import pytest

from pages.add_coBorrower_page import CoBorrowerPage
from test_page_data.addcoborrower_data import test_data
from test_page_data.validation_cases import COBORROWER_EMPTY, COBORROWER_INVALID
from utils.logger import get_logger
from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields
from utils.reporting import register_test_data
from utils.validations import Validations

logger = get_logger()


def _lead_name() -> str:
    from utils.lead_context import get_active_lead_name

    return get_active_lead_name()


def test_add_co_borrower_empty(authenticated_page, request):
    """Submit co-borrower form without filling required fields."""
    cb = CoBorrowerPage(authenticated_page)
    validator = Validations(authenticated_page)
    lead_name = _lead_name()

    cb.open()
    cb.open_lead(lead_name)
    cb.open_co_borrowers_tab()
    cb.click_add_co_borrower()
    cb.save()

    register_test_data(request.node, scenario="empty_form", lead_name=lead_name)
    verify_required_fields(validator, COBORROWER_EMPTY, item=request.node)


def test_add_co_borrower_invalid(authenticated_page, request):
    """Submit co-borrower form with every schema-invalid field value."""
    cb = CoBorrowerPage(authenticated_page)
    validator = Validations(authenticated_page)
    lead_name = _lead_name()

    cb.open()
    cb.open_lead(lead_name)
    cb.open_co_borrowers_tab()
    cb.click_add_co_borrower()
    cb.fill_valid_baseline()

    register_test_data(request.node, scenario="all_invalid_fields", lead_name=lead_name)

    verify_invalid_fields(
        validator,
        COBORROWER_INVALID,
        cb.set_field,
        cb.clear_field,
        cb.save,
        item=request.node,
        reset=cb.fill_valid_baseline,
    )


def test_add_co_borrower(authenticated_page):
    logger.info(f"Adding co-borrower with data: {test_data}")
    lead_name = _lead_name()

    cb = CoBorrowerPage(authenticated_page)

    cb.open()

    cb.open_lead(lead_name)
    cb.open_co_borrowers_tab()
    cb.click_add_co_borrower()

    cb.fill_basic_info(test_data["co_borrower"])
    cb.select_dob(test_data["co_borrower"])
    cb.select_marital_status(test_data["co_borrower"]["marital_status"])
    cb.fill_employment(
        test_data["co_borrower"]["employer"],
        test_data["co_borrower"]["relation"],
        test_data["co_borrower"]["income"]
    )

    cb.save()
