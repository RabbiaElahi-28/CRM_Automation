from pages.lead_edit_page import LeadEditPage
from test_page_data.lead_edit_data import lead_edit_data
from test_page_data.validation_cases import LEAD_EDIT_INVALID
from utils.logger import get_logger
from utils.negative_test_helpers import verify_invalid_fields
from utils.reporting import register_test_data
from utils.toast import Toast
from utils.validations import Validations

logger = get_logger()

_CLIENT_FIELDS = frozenset({"email", "postal_code", "phone"})
_CLIENT_INVALID = [case for case in LEAD_EDIT_INVALID if case.field in _CLIENT_FIELDS]
_MORTGAGE_INVALID = [
    case for case in LEAD_EDIT_INVALID if case.field not in _CLIENT_FIELDS
]


def _lead_name() -> str:
    from utils.lead_context import get_active_lead_name

    return get_active_lead_name()


def test_lead_edit_empty(authenticated_page, request):
    """Clear mortgage credit score and save — empty coerces below minimum range."""
    lead = LeadEditPage(authenticated_page)
    validator = Validations(authenticated_page)

    lead.open()
    lead.open_lead_for_edit(_lead_name())
    lead.open_mortgage_tab()
    lead.set_mortgage_field("credit_score", "")
    lead.save_mortgage_changes()

    register_test_data(
        request.node,
        scenario="empty_credit_score",
        lead_name=_lead_name(),
    )
    validator.assert_field_error(
        "Current credit score must be between 300 and 999",
        item=request.node,
    )


def test_lead_edit_invalid(authenticated_page, request):
    """Save lead edit with every schema-invalid field value."""
    lead = LeadEditPage(authenticated_page)
    validator = Validations(authenticated_page)

    lead.open()
    lead.open_lead_for_edit(_lead_name())

    register_test_data(
        request.node,
        scenario="all_invalid_fields",
        lead_name=_lead_name(),
    )

    verify_invalid_fields(
        validator,
        _CLIENT_INVALID,
        lead.set_client_field,
        lead.clear_client_field,
        lead.save_client_info,
        item=request.node,
        reset=lambda: lead.restore_baseline_for_invalid_tests(lead_edit_data),
    )

    verify_invalid_fields(
        validator,
        _MORTGAGE_INVALID,
        lead.set_mortgage_field,
        lead.clear_mortgage_field,
        lead.save_mortgage_changes,
        item=request.node,
        reset=lambda: lead.restore_baseline_for_invalid_tests(lead_edit_data),
    )


def test_edit_lead(authenticated_page):
    lead = LeadEditPage(authenticated_page)
    logger.info("Editing lead %s with data: %s", _lead_name(), lead_edit_data)

    lead.open()
    lead.open_lead_for_edit(_lead_name())

    lead.update_contact_email(lead_edit_data["contact"]["email"])
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

    toast = Toast(authenticated_page)
    toast.assert_message("Client information updated successfully")

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
    lead.fill_employment(
        lead_edit_data["employment"]["work_situation"],
        lead_edit_data["employment"]["work_location_partial"],
        lead_edit_data["employment"]["income"],
        lead_edit_data["employment"]["employer"],
        lead_edit_data["employment"]["important_choice"],
    )
    lead.save_mortgage_changes()
    toast.assert_message("Mortgage information updated successfully")
