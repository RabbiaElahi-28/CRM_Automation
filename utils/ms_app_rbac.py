"""Mortgage Snapshot App user-specific RBAC validation."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.mortgage_snapshot_app.leads_page import MortgageSnapshotAppLeadsPage
from utils.logger import get_logger
from utils.mortgage_snapshot_display import MortgageSnapshotDisplayExpectations
from utils.ms_app_auth import (
    MsAppPipeline,
    pipeline_label,
)

logger = get_logger()


class MsAppRbacViolation(AssertionError):
    """Lead data was visible to a non-assigned MS App user."""


def verify_ms_app_non_assigned_access_denied(
    rbac_page: Page,
    *,
    assigned_pipeline: MsAppPipeline,
    lead_name: str,
    expectations: MortgageSnapshotDisplayExpectations,
    presentation_url: str | None = None,
) -> None:
    """
    Confirm a cross-role MS App user cannot find or open the lead.

    Expects rbac_page to already be logged in as the cross-role user
    (via open_ms_app_rbac_page on a dedicated tab).
    """
    from utils.ms_app_auth import cross_role_pipeline

    cross_pipeline = cross_role_pipeline(assigned_pipeline)
    assigned_label = pipeline_label(assigned_pipeline)
    cross_label = pipeline_label(cross_pipeline)

    leads = MortgageSnapshotAppLeadsPage(rbac_page)
    leads.wait_for_leads()
    leads.wait_for_leads_ready(timeout_ms=60000)

    logger.info(
        "MS App RBAC: lead %r assigned to %s — verifying hidden from %s",
        lead_name,
        assigned_label,
        cross_label,
    )

    leads.assert_lead_not_accessible(
        lead_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.applicant_first_name,
        presentation_url=presentation_url,
    )


def capture_presentation_url(app_page: Page) -> str | None:
    url = app_page.url
    if "/leads" in url:
        return None
    if "mortgagesnapshot" in url.lower():
        return url
    return None
