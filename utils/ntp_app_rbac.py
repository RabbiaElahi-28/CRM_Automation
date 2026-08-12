"""NTP Application user-specific RBAC validation."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.ntp_app.leads_page import NtpAppLeadsPage
from utils.logger import get_logger
from utils.ms_app_auth import MsAppPipeline, cross_role_pipeline, pipeline_label
from utils.ntp_display import NtpDisplayExpectations

logger = get_logger()


class NtpAppRbacViolation(AssertionError):
    """Lead data was visible to a non-assigned NTP App user."""


def capture_ntp_presentation_url(app_page: Page) -> str | None:
    url = app_page.url
    if "/leads" in url:
        return None
    if "ntp" in url.lower():
        return url
    return None


def verify_ntp_app_non_assigned_access_denied(
    rbac_page: Page,
    *,
    assigned_pipeline: MsAppPipeline,
    lead_name: str,
    expectations: NtpDisplayExpectations,
    presentation_url: str | None = None,
) -> None:
    cross_pipeline = cross_role_pipeline(assigned_pipeline)
    assigned_label = pipeline_label(assigned_pipeline)
    cross_label = pipeline_label(cross_pipeline)

    leads = NtpAppLeadsPage(rbac_page)
    leads.wait_for_leads()
    leads.wait_for_leads_ready(timeout_ms=60000)

    logger.info(
        "NTP App RBAC: lead %r assigned to %s — verifying hidden from %s",
        lead_name,
        assigned_label,
        cross_label,
    )

    leads.assert_lead_not_accessible(
        lead_name,
        vfli=expectations.vfli_number or None,
        email=expectations.lead_email or None,
        applicant_first_name=expectations.header_first_name,
        presentation_url=presentation_url,
    )
