import pytest

from pages.client_care_page import ClientCarePage
from pages.compliance_page import CompliancePage
from pages.signed_page import SignedPage
from test_page_data import test_entities
from test_page_data.signed_form_baseline import load as load_signed_form_baseline
from utils.reporting import register_test_data


@pytest.mark.module_smoke
def test_client_care(authenticated_page, request):
    """Verify Client Care Just Closed read-only data matches the Signed stage."""
    deal_name = test_entities.MY_DEALS_DEAL_NAME
    client_care = ClientCarePage(authenticated_page)
    signed = SignedPage(authenticated_page)
    compliance = CompliancePage(authenticated_page)

    register_test_data(request.node, deal_name=deal_name)

    signed_baseline = load_signed_form_baseline()
    if signed_baseline is None:
        signed.open()
        try:
            signed.open_signed(deal_name)
            signed_baseline = compliance.capture_signed_tab_values(signed)
        except Exception:
            signed_baseline = None

    client_care.open()
    client_care.verify_lead_searchable(deal_name)
    client_care.open_client_care_deal(deal_name)

    client_care.open_just_closed_tab()
    client_care.verify_just_closed_sections_visible()
    client_care.verify_just_closed_readonly()
    client_care.verify_just_closed_has_no_save_action()

    just_closed_snapshot = client_care.read_just_closed_values()
    client_care.verify_just_closed_has_data(just_closed_snapshot)

    assert signed_baseline, (
        "No Signed Form baseline available. Run test_compliance (or test_signed smoke) "
        "first so signed-stage values can be compared in Client Care Just Closed."
    )
    client_care.verify_just_closed_matches(signed_baseline)

    client_care.open_profile_tab()
    client_care.open_just_closed_tab()
    client_care.verify_just_closed_matches(just_closed_snapshot)

    client_care.refresh()
    client_care.open_just_closed_tab()
    client_care.verify_just_closed_matches(just_closed_snapshot)
