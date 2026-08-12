"""Stage empty/invalid/smoke runners for full regression E2E flows."""

from playwright.sync_api import Page

from pages.add_coBorrower_page import CoBorrowerPage
from pages.appraisal_order_page import AppraisalOrderPage
from pages.approved_page import ApprovedPage
from pages.client_care_page import ClientCarePage
from pages.create_lead import CreateLeadPage
from pages.lead_edit_page import LeadEditPage
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from pages.note_page import NotesPage
from pages.signed_page import SignedPage
from pages.submitted_page import SubmittedPage
from test_page_data import negative_messages as msg
from test_page_data.addcoborrower_data import test_data as coborrower_data
from test_page_data.appraisal_order_data import AppraisalOrderData
from test_page_data.lead_edit_data import lead_edit_data
from test_page_data.mortgage_snapshot_data import MortgageSnapshotData
from test_page_data.validation_cases import (
    APPRAISAL_EMPTY_NO,
    APPRAISAL_EMPTY_YES,
    APPRAISAL_INVALID,
    APPROVED_EMPTY,
    APPROVED_INVALID,
    COBORROWER_EMPTY,
    COBORROWER_INVALID,
    CREATE_LEAD_EMPTY,
    CREATE_LEAD_INVALID,
    LEAD_EDIT_INVALID,
    SIGNED_EMPTY_NOT_SIGNED,
    SIGNED_EMPTY_YES_FINAL,
    SIGNED_INVALID,
    SNAPSHOT_EMPTY,
    SNAPSHOT_INVALID,
    SUBMITTED_EMPTY,
    SUBMITTED_INVALID,
)
from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields
from utils.reporting import register_test_data
from utils.entity_navigation import MY_DEALS_BUCKET, SALES_BACKEND_BUCKET
from utils.sales_flow_helpers import (
    create_lead_smoke,
    run_appraisal_order_smoke,
    run_approved_smoke,
    run_client_care_smoke,
    run_co_borrower_smoke,
    run_compliance_smoke,
    run_lead_edit_smoke,
    run_mortgage_snapshot_smoke,
    run_notes_smoke,
    run_signed_compliance_smoke,
    run_signed_marketing_smoke,
    run_submitted_smoke,
)
from utils.test_data_factory import valid_lead_data
from utils.validations import Validations

_SUBMITTED_OPTION = 1

_CLIENT_FIELDS = frozenset({"email", "postal_code", "phone"})
_CLIENT_INVALID = [case for case in LEAD_EDIT_INVALID if case.field in _CLIENT_FIELDS]
_MORTGAGE_INVALID = [
    case for case in LEAD_EDIT_INVALID if case.field not in _CLIENT_FIELDS
]


def run_create_lead_empty(page: Page, item) -> None:
    create = CreateLeadPage(page)
    validator = Validations(page)
    create.open()
    create.clear_all_fields()
    create.submit_lead()
    register_test_data(item, stage="create_lead", scenario="empty_form")
    verify_required_fields(validator, CREATE_LEAD_EMPTY, item=item)


def run_create_lead_invalid(page: Page, item) -> None:
    create = CreateLeadPage(page)
    validator = Validations(page)
    baseline = valid_lead_data()
    create.open()
    create.fill_form(baseline)
    register_test_data(item, stage="create_lead", scenario="all_invalid_fields")
    verify_invalid_fields(
        validator,
        CREATE_LEAD_INVALID,
        create.set_field,
        create.clear_field,
        create.submit_lead,
        item=item,
        reset=lambda: create.restore_baseline_for_invalid_tests(baseline),
    )


def run_lead_edit_empty(
    page: Page, item, lead_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    lead = LeadEditPage(page)
    validator = Validations(page)
    lead.open()
    lead.open_lead_for_edit(lead_name, bucket=bucket)
    lead.open_mortgage_tab()
    lead.set_mortgage_field("credit_score", "")
    lead.save_mortgage_changes()
    register_test_data(item, stage="lead_edit", scenario="empty_credit_score", lead_name=lead_name)
    validator.assert_field_error(
        "Current credit score must be between 300 and 999",
        item=item,
    )


def run_lead_edit_invalid(
    page: Page, item, lead_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    lead = LeadEditPage(page)
    validator = Validations(page)
    lead.open()
    lead.open_lead_for_edit(lead_name, bucket=bucket)
    register_test_data(item, stage="lead_edit", scenario="all_invalid_fields", lead_name=lead_name)
    verify_invalid_fields(
        validator,
        _CLIENT_INVALID,
        lead.set_client_field,
        lead.clear_client_field,
        lead.save_client_info,
        item=item,
        reset=lambda: lead.restore_baseline_for_invalid_tests(lead_edit_data),
    )
    verify_invalid_fields(
        validator,
        _MORTGAGE_INVALID,
        lead.set_mortgage_field,
        lead.clear_mortgage_field,
        lead.save_mortgage_changes,
        item=item,
        reset=lambda: lead.restore_baseline_for_invalid_tests(lead_edit_data),
    )


def run_co_borrower_empty(
    page: Page, item, lead_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    cb = CoBorrowerPage(page)
    validator = Validations(page)
    cb.open()
    cb.open_lead(lead_name, bucket=bucket)
    cb.open_co_borrowers_tab()
    cb.click_add_co_borrower()
    cb.save()
    register_test_data(item, stage="co_borrower", scenario="empty_form", lead_name=lead_name)
    verify_required_fields(validator, COBORROWER_EMPTY, item=item)


def run_co_borrower_invalid(
    page: Page, item, lead_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    cb = CoBorrowerPage(page)
    validator = Validations(page)
    cb.open()
    cb.open_lead(lead_name, bucket=bucket)
    cb.open_co_borrowers_tab()
    cb.click_add_co_borrower()
    cb.fill_valid_baseline()
    register_test_data(item, stage="co_borrower", scenario="all_invalid_fields", lead_name=lead_name)
    verify_invalid_fields(
        validator,
        COBORROWER_INVALID,
        cb.set_field,
        cb.clear_field,
        cb.save,
        item=item,
        reset=cb.fill_valid_baseline,
    )


def run_note_empty(
    page: Page, item, lead_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    notes = NotesPage(page)
    validator = Validations(page)
    notes.open()
    notes.open_lead(lead_name, bucket=bucket)
    notes.open_notes_tab()
    notes.click_add_note()
    notes.clear_note()
    notes.save_note()
    register_test_data(item, stage="notes", scenario="empty_note", lead_name=lead_name)
    validator.assert_field_error(msg.NOTE_EMPTY, item=item)
    notes.dismiss_add_note_form_if_open()


def run_note_invalid(
    page: Page, item, lead_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    """Reject whitespace-only note content (contact status defaults to not contacted)."""
    notes = NotesPage(page)
    validator = Validations(page)
    notes.open()
    notes.open_lead(lead_name, bucket=bucket)
    notes.open_notes_tab()
    notes.click_add_note()
    notes.enter_whitespace_note()
    notes.save_note()

    register_test_data(item, stage="notes", scenario="whitespace_note", lead_name=lead_name)
    validator.assert_field_error(msg.NOTE_EMPTY, item=item)
    notes.dismiss_add_note_form_if_open()


def run_pre_stage_all_cases(
    page: Page,
    item,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
) -> None:
    """Edit Lead, Co-Borrower, and Notes — empty, invalid, then smoke."""
    run_lead_edit_empty(page, item, deal_name, bucket=bucket)
    run_lead_edit_invalid(page, item, deal_name, bucket=bucket)
    run_lead_edit_smoke(page, deal_name, bucket=bucket)
    run_co_borrower_empty(page, item, deal_name, bucket=bucket)
    run_co_borrower_invalid(page, item, deal_name, bucket=bucket)
    run_co_borrower_smoke(page, deal_name, bucket=bucket)
    run_note_empty(page, item, deal_name, bucket=bucket)
    run_note_invalid(page, item, deal_name, bucket=bucket)
    run_notes_smoke(page, deal_name, move_to_sales=False, bucket=bucket)


def run_mortgage_snapshot_empty(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    snapshot = MortgageSnapshotPage(page)
    validator = Validations(page)
    snapshot.open()
    snapshot.open_snapshot(deal_name, bucket=bucket)
    snapshot.clear_all_snapshot_fields()
    snapshot.save()
    register_test_data(item, stage="mortgage_snapshot", scenario="empty_form", deal_name=deal_name)
    verify_required_fields(validator, SNAPSHOT_EMPTY, item=item)


def run_mortgage_snapshot_invalid(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    snapshot = MortgageSnapshotPage(page)
    validator = Validations(page)
    data = MortgageSnapshotData()
    snapshot.open()
    snapshot.open_snapshot(deal_name, bucket=bucket)
    snapshot.fill_valid_baseline(data)
    register_test_data(
        item, stage="mortgage_snapshot", scenario="all_invalid_fields", deal_name=deal_name
    )
    verify_invalid_fields(
        validator,
        SNAPSHOT_INVALID,
        snapshot.set_snapshot_field,
        snapshot.clear_snapshot_field,
        snapshot.save,
        item=item,
        reset=lambda: snapshot.fill_valid_baseline(data),
    )


def run_appraisal_order_empty(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    appraisal = AppraisalOrderPage(page)
    validator = Validations(page)
    appraisal.open()
    appraisal.open_appraisal_order(deal_name, bucket=bucket)
    register_test_data(item, stage="appraisal_order", scenario="empty_form", deal_name=deal_name)
    appraisal.save_appraisal_order()
    verify_required_fields(validator, APPRAISAL_EMPTY_YES, item=item)
    appraisal.reset_appraisal_form()
    appraisal.select_yes_with_avm()
    appraisal.save_appraisal_order()
    verify_required_fields(validator, APPRAISAL_EMPTY_YES, item=item)
    appraisal.reset_appraisal_form()
    appraisal.select_no_with_avm()
    appraisal.save_appraisal_order()
    verify_required_fields(validator, APPRAISAL_EMPTY_NO, item=item)


def run_appraisal_order_invalid(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    appraisal = AppraisalOrderPage(page)
    validator = Validations(page)
    appraisal.open()
    appraisal.open_appraisal_order(deal_name, bucket=bucket)
    appraisal.prepare_yes_flow_for_invalid_ltv()
    register_test_data(
        item, stage="appraisal_order", scenario="all_invalid_fields", deal_name=deal_name
    )
    verify_invalid_fields(
        validator,
        APPRAISAL_INVALID,
        appraisal.set_field,
        appraisal.clear_field,
        appraisal.save_appraisal_order,
        item=item,
        reset=appraisal.prepare_yes_flow_for_invalid_ltv,
    )


def run_submitted_empty(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    submitted = SubmittedPage(page)
    validator = Validations(page)
    submitted.open()
    submitted.open_submitted(deal_name, bucket=bucket)
    submitted.clear_option_fields(_SUBMITTED_OPTION)
    submitted.save_option(_SUBMITTED_OPTION, expect_success=False)
    register_test_data(
        item, stage="submitted", scenario="empty_option_1", deal_name=deal_name
    )
    verify_required_fields(validator, SUBMITTED_EMPTY, item=item)


def run_submitted_invalid(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    submitted = SubmittedPage(page)
    validator = Validations(page)
    submitted.open()
    submitted.open_submitted(deal_name, bucket=bucket)
    submitted.prepare_option_for_invalid_tests(_SUBMITTED_OPTION)
    register_test_data(
        item, stage="submitted", scenario="all_invalid_fields", deal_name=deal_name
    )

    def set_field(field, value):
        submitted.set_option_field(_SUBMITTED_OPTION, field, value)

    def clear_field(field):
        submitted.clear_option_field(_SUBMITTED_OPTION, field)

    verify_invalid_fields(
        validator,
        SUBMITTED_INVALID,
        set_field,
        clear_field,
        lambda: submitted.save_option(_SUBMITTED_OPTION, expect_success=False),
        item=item,
        reset=lambda: submitted.prepare_option_for_invalid_tests(_SUBMITTED_OPTION),
    )


def run_approved_empty(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    approved = ApprovedPage(page)
    validator = Validations(page)
    approved.open()
    approved.open_approved(deal_name, bucket=bucket)
    approved.clear_all_approved_form_fields()
    approved.save_approved_form()
    register_test_data(item, stage="approved", scenario="empty_form", deal_name=deal_name)
    verify_required_fields(validator, APPROVED_EMPTY, item=item)


def run_approved_invalid(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    approved = ApprovedPage(page)
    validator = Validations(page)
    approved.open()
    approved.open_approved(deal_name, bucket=bucket)
    approved.prepare_valid_baseline_for_invalid_tests()
    register_test_data(
        item, stage="approved", scenario="all_invalid_fields", deal_name=deal_name
    )
    verify_invalid_fields(
        validator,
        APPROVED_INVALID,
        approved.set_field,
        approved.clear_field,
        approved.save_approved_form,
        item=item,
        reset=approved.prepare_valid_baseline_for_invalid_tests,
    )


def run_signed_empty(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    signed = SignedPage(page)
    validator = Validations(page)
    signed.open()
    signed.open_signed(deal_name, bucket=bucket)
    register_test_data(item, stage="signed", scenario="empty_form", deal_name=deal_name)
    signed.select_client_signed_no()
    signed.save_signed_form()
    verify_required_fields(validator, SIGNED_EMPTY_NOT_SIGNED, item=item)
    signed.select_client_signed_yes()
    signed.select_final_product_yes()
    signed.verify_deal_tracking_sections_visible()
    signed.save_signed_form()
    verify_required_fields(validator, SIGNED_EMPTY_YES_FINAL, item=item)


def run_signed_invalid(
    page: Page, item, deal_name: str, *, bucket: str = MY_DEALS_BUCKET
) -> None:
    signed = SignedPage(page)
    validator = Validations(page)
    signed.open()
    signed.open_signed(deal_name, bucket=bucket)
    register_test_data(
        item, stage="signed", scenario="all_invalid_fields", deal_name=deal_name
    )
    for case in SIGNED_INVALID:
        if case.field == "outstandingConditions":
            signed.prepare_yes_final_product_for_invalid()
        else:
            signed.select_client_signed_yes()
        signed.set_field(case.field, case.value)
        signed.save_signed_form()
        validator.assert_field_error(case.message, item=item)
        signed.clear_field(case.field)


def run_client_care_full(page: Page, item, deal_name: str, signed_baseline) -> None:
    client_care = ClientCarePage(page)
    client_care.open()
    client_care.verify_lead_searchable(deal_name)
    client_care.open_client_care_deal(deal_name)
    client_care.open_just_closed_tab()
    client_care.verify_just_closed_sections_visible()
    client_care.verify_just_closed_readonly()
    client_care.verify_just_closed_has_no_save_action()
    just_closed_snapshot = client_care.read_just_closed_values()
    client_care.verify_just_closed_has_data(just_closed_snapshot)
    assert signed_baseline, "Signed Form baseline required for Client Care verification"
    client_care.verify_just_closed_matches(signed_baseline)
    client_care.open_profile_tab()
    client_care.open_just_closed_tab()
    client_care.verify_just_closed_matches(just_closed_snapshot)
    client_care.refresh()
    client_care.open_just_closed_tab()
    client_care.verify_just_closed_matches(just_closed_snapshot)
    register_test_data(item, stage="client_care", deal_name=deal_name)


def run_signed_marketing_regression(
    page: Page,
    item,
    deal_name: str,
    *,
    bucket: str = MY_DEALS_BUCKET,
) -> None:
    run_signed_empty(page, item, deal_name, bucket=bucket)
    run_signed_invalid(page, item, deal_name, bucket=bucket)
    run_signed_marketing_smoke(page, deal_name, bucket=bucket)


def run_compliance_path_all_cases(page: Page, request) -> str:
    """
    Run every stage test case (empty, invalid, smoke) on one fresh lead
    through the Compliance → Client Care path.
    """
    item = request.node
    register_test_data(item, flow="compliance_all_cases")

    run_create_lead_empty(page, item)
    run_create_lead_invalid(page, item)
    lead_name = create_lead_smoke(page)
    register_test_data(item, deal_name=lead_name)

    run_lead_edit_empty(page, item, lead_name)
    run_lead_edit_invalid(page, item, lead_name)
    run_lead_edit_smoke(page, lead_name)

    run_co_borrower_empty(page, item, lead_name)
    run_co_borrower_invalid(page, item, lead_name)
    run_co_borrower_smoke(page, lead_name)

    run_note_empty(page, item, lead_name)
    deal_name = run_notes_smoke(page, lead_name)
    register_test_data(item, deal_name=deal_name)

    run_mortgage_snapshot_empty(page, item, deal_name)
    run_mortgage_snapshot_invalid(page, item, deal_name)
    run_mortgage_snapshot_smoke(
        page,
        deal_name,
        request_or_item=item,
        regression_ms_app=True,
    )

    run_appraisal_order_empty(page, item, deal_name)
    run_appraisal_order_invalid(page, item, deal_name)
    run_appraisal_order_smoke(page, deal_name)

    run_submitted_empty(page, item, deal_name)
    run_submitted_invalid(page, item, deal_name)
    run_submitted_smoke(page, deal_name)

    run_approved_empty(page, item, deal_name)
    run_approved_invalid(page, item, deal_name)
    run_approved_smoke(page, deal_name)

    run_signed_empty(page, item, deal_name)
    run_signed_invalid(page, item, deal_name)
    run_signed_compliance_smoke(page, deal_name)

    signed_baseline = run_compliance_smoke(page, deal_name)
    run_client_care_full(page, item, deal_name, signed_baseline)

    return deal_name
