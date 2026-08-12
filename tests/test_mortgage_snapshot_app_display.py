import json

from pathlib import Path



import pytest



from pages.mortgage_snapshot_app.presentation_page import MortgageSnapshotAppPresentationPage

from utils.config import Config

from utils.mortgage_snapshot_app_helpers import (
    expectations_from_captured,
    logout_and_close_ms_app_tab,
    open_ms_app_for_assigned_user,
    prepare_lead_with_saved_snapshot,
    run_ms_app_discovery,
    verify_ms_app_presentation,
)
from utils.ms_app_auth import cross_role_pipeline, open_ms_app_rbac_page

from utils.mortgage_snapshot_field_audit import format_verification_table

from utils.ms_app_rbac import capture_presentation_url, verify_ms_app_non_assigned_access_denied

from utils.reporting import register_test_data



DISCOVERY_REPORT_DIR = Path("reports/ms_app_discovery")

FIELD_AUDIT_REPORT = Path("reports/ms_app_field_verification.md")





def _log_discovery(report, test_name: str) -> None:

    payload = report.to_dict()

    DISCOVERY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = DISCOVERY_REPORT_DIR / f"{test_name}.json"

    MortgageSnapshotAppPresentationPage.write_discovery_report(report, report_path)

    print(f"\n=== MS App discovery ({test_name}) ===")

    print(json.dumps(payload, indent=2))





def _write_field_audit_report(test_name: str, passed: bool) -> None:

    report = format_verification_table(run_passed=passed, test_name=test_name)

    FIELD_AUDIT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    FIELD_AUDIT_REPORT.write_text(report, encoding="utf-8")

    print(f"\n=== MS App field verification ({test_name}) ===")

    print(report)





def _run_admin_ms_app_display_test(

    page,

    browser,

    request,

    *,

    with_co_borrower: bool,

    scenario: str,

) -> None:

    passed = False

    try:

        lead_name, data, _expectations, snapshot = prepare_lead_with_saved_snapshot(

            page, with_co_borrower=with_co_borrower

        )

        captured = snapshot.capture_snapshot_form_values()

        expectations = expectations_from_captured(

            lead_name, captured, with_co_borrower=with_co_borrower

        )

        register_test_data(

            request.node,

            deal_name=lead_name,

            data=data,

            scenario=scenario,

        )



        app_page = open_ms_app_for_assigned_user(
            page,
            snapshot,
            assigned_pipeline="admin",
            browser=browser,
            prefer_crm_button=True,
        )

        discovery = run_ms_app_discovery(app_page, lead_name, expectations)

        _log_discovery(discovery, request.node.name)



        app_page.goto(f"{Config.MORTGAGE_SNAPSHOT_APP_URL}/leads")

        verify_ms_app_presentation(

            app_page,

            lead_name,

            expectations,

            with_co_borrower=with_co_borrower,

        )

        presentation_url = capture_presentation_url(app_page)
        logout_and_close_ms_app_tab(app_page)

        cross_pipeline = cross_role_pipeline("admin")
        rbac_page = open_ms_app_rbac_page(page.context, cross_pipeline)
        try:
            verify_ms_app_non_assigned_access_denied(
                rbac_page,
                assigned_pipeline="admin",
                lead_name=lead_name,
                expectations=expectations,
                presentation_url=presentation_url,
            )
        finally:
            rbac_page.close()

        passed = True

    finally:

        _write_field_audit_report(request.node.name, passed=passed)





@pytest.mark.smoke

def test_mortgage_snapshot_app_display_without_co_borrower(

    authenticated_page, browser, request

):

    """CRM saved snapshot values match MS App presentation (no co-borrower)."""

    _run_admin_ms_app_display_test(

        authenticated_page,

        browser,

        request,

        with_co_borrower=False,

        scenario="ms_app_display_no_co_borrower",

    )





@pytest.mark.smoke

def test_mortgage_snapshot_app_display_with_co_borrower(

    authenticated_page, browser, request

):

    """CRM saved snapshot values match MS App presentation (with co-borrower)."""

    _run_admin_ms_app_display_test(

        authenticated_page,

        browser,

        request,

        with_co_borrower=True,

        scenario="ms_app_display_with_co_borrower",

    )

