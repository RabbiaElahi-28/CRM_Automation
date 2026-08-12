import pytest

from pages.compliance_page import CompliancePage
from test_page_data.compliance_data import ComplianceData
from test_page_data import test_entities
from test_page_data.signed_form_baseline import save as save_signed_form_baseline
from utils.reporting import register_test_data


@pytest.mark.module_smoke
def test_compliance(authenticated_page, request):
    """Complete Compliance stage: verify Signed Form, save Compliance, complete stage."""
    deal_name = test_entities.MY_DEALS_DEAL_NAME
    compliance = CompliancePage(authenticated_page)
    data = ComplianceData()

    register_test_data(
        request.node,
        deal_name=deal_name,
        data=data,
    )

    compliance.open()
    compliance.open_compliance_deal(deal_name)

    # --- Signed Closed > Signed Form (read-only verification) ---
    compliance.open_signed_closed_tab()
    compliance.open_signed_form_tab()
    compliance.verify_signed_form_readonly()
    signed_baseline = compliance.read_signed_form_readonly_values()
    compliance.verify_signed_form_has_data(signed_baseline)

    # --- Navigation between internal tabs should not lose Signed Form data ---
    compliance.open_compliance_form_tab()
    compliance.open_signed_form_tab()
    compliance.verify_signed_form_matches(signed_baseline)

    # --- Compliance Form: Closing Compliance ---
    compliance.open_compliance_form_tab()
    compliance.fill_closing_compliance(data.closing)
    compliance.save_closing_compliance()
    compliance.verify_closing_compliance_saved()

    # --- Compliance Form: Client Care Checks ---
    compliance.fill_client_care_checks(data.client_care)
    compliance.save_client_care_checks()
    compliance.verify_client_care_checks_saved()

    # --- Persistence after refresh ---
    compliance.refresh()
    compliance.open_signed_closed_tab()
    compliance.verify_closing_compliance_persisted()
    compliance.open_signed_form_tab()
    compliance.verify_signed_form_matches(signed_baseline)

    # --- Complete stage ---
    save_signed_form_baseline(signed_baseline)
    compliance.open_compliance_form_tab()
    compliance.complete_stage()
    compliance.verify_moved_to_client_care_toast()
    compliance.verify_on_client_care_page()
    compliance.verify_lead_in_client_care(deal_name)
