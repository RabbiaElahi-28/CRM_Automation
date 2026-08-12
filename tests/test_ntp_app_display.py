import pytest

from utils.ms_app_auth import cross_role_pipeline
from utils.ntp_app_auth import open_ntp_app_rbac_page
from utils.mortgage_snapshot_app_helpers import close_ms_app_tab
from utils.ntp_app_helpers import (
    logout_and_close_ntp_app_tab,
    open_ntp_from_crm_after_approved_save,
    prepare_lead_with_saved_approved,
    verify_ntp_app_presentation,
)
from utils.ntp_app_rbac import capture_ntp_presentation_url, verify_ntp_app_non_assigned_access_denied
from utils.reporting import register_test_data


def _run_admin_ntp_app_display_test(
    page,
    browser,
    request,
    *,
    with_co_borrower: bool,
    scenario: str,
) -> None:
    (
        lead_name,
        captured_approved,
        captured_snapshot,
        expectations,
        approved,
    ) = prepare_lead_with_saved_approved(page, with_co_borrower=with_co_borrower)

    register_test_data(
        request.node,
        deal_name=lead_name,
        captured_approved=captured_approved,
        captured_snapshot=captured_snapshot,
        scenario=scenario,
    )

    app_page = open_ntp_from_crm_after_approved_save(page, approved)

    try:
        verify_ntp_app_presentation(
            app_page,
            lead_name,
            expectations,
            with_co_borrower=with_co_borrower,
        )
        presentation_url = capture_ntp_presentation_url(app_page)
        logout_and_close_ntp_app_tab(app_page)

        cross_pipeline = cross_role_pipeline("admin")
        rbac_page = open_ntp_app_rbac_page(page.context, cross_pipeline)
        try:
            verify_ntp_app_non_assigned_access_denied(
                rbac_page,
                assigned_pipeline="admin",
                lead_name=lead_name,
                expectations=expectations,
                presentation_url=presentation_url,
            )
        finally:
            close_ms_app_tab(rbac_page)
    finally:
        if app_page is not None and not app_page.is_closed():
            close_ms_app_tab(app_page)


@pytest.mark.smoke
def test_ntp_app_display_without_co_borrower(authenticated_page, browser, request):
    """CRM saved Approved values match NTP App presentation (no co-borrower)."""
    _run_admin_ntp_app_display_test(
        authenticated_page,
        browser,
        request,
        with_co_borrower=False,
        scenario="ntp_app_display_no_co_borrower",
    )


@pytest.mark.smoke
def test_ntp_app_display_with_co_borrower(authenticated_page, browser, request):
    """CRM saved Approved values match NTP App presentation (with co-borrower)."""
    _run_admin_ntp_app_display_test(
        authenticated_page,
        browser,
        request,
        with_co_borrower=True,
        scenario="ntp_app_display_with_co_borrower",
    )
