import pytest

from pages.approved_page import ApprovedPage
from pages.signed_page import SignedPage
from test_page_data.approved_data import ApprovedData
from test_page_data.signed_data import SignedData
from test_page_data import test_entities
from test_page_data.validation_cases import (
    SIGNED_EMPTY_NOT_SIGNED,
    SIGNED_EMPTY_YES_FINAL,
    SIGNED_INVALID,
)
from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields
from utils.reporting import register_test_data
from utils.validations import Validations


def test_signed_empty(authenticated_page, request):
    """Verify all required-field validations across signed form flows."""
    signed = SignedPage(authenticated_page)
    validator = Validations(authenticated_page)

    signed.open()
    signed.open_signed(test_entities.MY_DEALS_DEAL_NAME)

    register_test_data(request.node, scenario="empty_form", deal_name=test_entities.MY_DEALS_DEAL_NAME)

    signed.select_client_signed_no()
    signed.save_signed_form()
    verify_required_fields(validator, SIGNED_EMPTY_NOT_SIGNED, item=request.node)

    signed.select_client_signed_yes()
    signed.select_final_product_yes()
    signed.verify_deal_tracking_sections_visible()
    signed.save_signed_form()
    verify_required_fields(validator, SIGNED_EMPTY_YES_FINAL, item=request.node)


def test_signed_invalid(authenticated_page, request):
    """Save signed form with every schema-invalid field value."""
    signed = SignedPage(authenticated_page)
    validator = Validations(authenticated_page)

    signed.open()
    signed.open_signed(test_entities.MY_DEALS_DEAL_NAME)

    register_test_data(request.node, scenario="all_invalid_fields", deal_name=test_entities.MY_DEALS_DEAL_NAME)

    for case in SIGNED_INVALID:
        if case.field == "outstandingConditions":
            signed.prepare_yes_final_product_for_invalid()
        else:
            signed.select_client_signed_yes()
        signed.set_field(case.field, case.value)
        signed.save_signed_form()
        validator.assert_field_error(case.message, item=request.node)
        signed.clear_field(case.field)


@pytest.mark.module_smoke
def test_signed(authenticated_page, request):
    deal_name = test_entities.MY_DEALS_DEAL_NAME
    signed = SignedPage(authenticated_page)
    approved = ApprovedPage(authenticated_page)
    signed.open()

    data = SignedData()
    approved_data = ApprovedData()

    register_test_data(
        request.node,
        deal_name=deal_name,
        data=data
    )

    # --- Open Signed tab ---
    signed.open_signed(deal_name)

    # --- Not Signed flow ---
    signed.select_client_signed_no()
    signed.verify_not_signed_reason_visible()
    signed.verify_final_product_section_hidden()
    signed.fill_not_signed_reason(data.no_flow.not_signed_reason)
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.move_to_next_stage()
    signed.verify_moved_to_not_signed()

    # --- Switch back to Yes ---
    signed.select_client_signed_yes()
    signed.verify_not_signed_reason_hidden()
    signed.verify_final_product_section_visible()
    signed.verify_signed_details_prefilled()
    signed.verify_lender_name_prefilled()

    # --- Flow 1: Final Product No → Resigning back to Submitted ---
    signed.select_final_product_no()
    signed.verify_deal_tracking_sections_hidden()
    signed.select_resigning_back_to_submitted()
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.verify_moved_to_approved()

    # --- Re-complete Approved stage ---
    signed.click(approved.approved_tab)
    signed.verify_signed_tab_hidden()
    approved.verify_approved_form_tab_active()
    approved.verify_mortgage_option_prefilled()
    approved.fill_approved_form(approved_data.form)
    approved.save_approved_form()
    approved.verify_form_saved()
    approved.verify_approved_completed_tab_active()
    approved.fill_approved_completed(approved_data.approved_completed)
    approved.complete_stage()
    approved.verify_form_saved()
    approved.move_to_next_stage()
    approved.verify_moved_to_signed()

    # --- Flow 2: Final Product Yes ---
    signed.select_client_signed_yes()
    signed.select_final_product_yes()
    signed.verify_deal_tracking_sections_visible()

    # Outstanding Conditions visibility + validation
    signed.select_outstanding_condition_yes()
    signed.verify_outstanding_conditions_details_visible()
    signed.fill_outstanding_conditions_details(
        data.final_yes.short_outstanding_conditions
    )
    signed.save_signed_form()
    signed.verify_outstanding_conditions_min_length_error()

    signed.fill_outstanding_conditions_details(
        data.final_yes.outstanding_conditions_details
    )
    signed.select_outstanding_condition_no()
    signed.verify_outstanding_conditions_details_hidden()

    signed.fill_final_product_yes_sections(data.final_yes)
    signed.save_signed_form()
    signed.verify_signed_saved()
    signed.move_to_next_stage()
    signed.verify_moved_to_signed_stage()

    # --- Google Review ---
    signed.verify_google_review_visible()
    signed.select_good_for_google_review_yes()
    signed.set_closed_checked(False)
    signed.save_google_review()
    signed.verify_google_review_saved()
    signed.verify_still_on_signed_tab()

    signed.set_closed_checked(True)

    signed.save_google_review(expect_compliance_move=True, role="admin")
    signed.complete_google_review_compliance_move(role="admin")


    # # --- Compliance verification ---
    signed.open_compliance_and_search_deal(deal_name)
    signed.verify_deal_in_compliance(deal_name)



