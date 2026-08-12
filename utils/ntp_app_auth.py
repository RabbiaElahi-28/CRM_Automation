"""NTP App staff authentication helpers — mirrors MS App auth patterns."""

from __future__ import annotations

import re
from urllib.parse import quote

from playwright.sync_api import Browser, BrowserContext, Page

from utils.config import Config
from utils.logger import get_logger
from utils.ms_app_auth import (
    MsAppPipeline,
    auth_token_from_storage_state,
    credentials_for_pipeline,
    ensure_ms_app_lead_assignee,
    fetch_user_id_from_context,
    pipeline_label,
)

logger = get_logger()


def build_ntp_app_staff_url(context: BrowserContext) -> str:
    """Build the same staff URL the CRM NTP Application button opens."""
    storage_state = context.storage_state()
    token = auth_token_from_storage_state(storage_state)
    user_id = fetch_user_id_from_context(context)
    return (
        f"{Config.NTP_APP_URL.rstrip('/')}/staff"
        f"?id={quote(user_id)}&token={quote(token)}"
    )


def open_ntp_app_via_staff_url(
    context: BrowserContext,
    browser: Browser,
    *,
    pipeline: MsAppPipeline = "admin",
) -> Page:
    """Open NTP App /leads using CRM session, or native login if staff URL fails."""
    try:
        url = build_ntp_app_staff_url(context)
        app_page = context.new_page()
        app_page.set_default_timeout(Config.TIMEOUT)
        logger.info("Opening NTP App via staff URL (CRM button unavailable)")
        app_page.goto(url)
        app_page.wait_for_load_state("domcontentloaded")
        app_page.wait_for_url(re.compile(r".*/leads(?:\?.*)?$"), timeout=60000)
        return app_page
    except Exception as exc:
        logger.warning(
            "Staff URL open failed (%s); falling back to native NTP login (%s)",
            exc,
            pipeline,
        )
        return open_ntp_app_as_pipeline_user(context, browser, pipeline)


def login_ntp_app(page: Page, pipeline: MsAppPipeline, *, force: bool = False) -> None:
    from pages.ntp_app.leads_page import NtpAppLeadsPage
    from pages.ntp_app.login_page import NtpAppLoginPage, _clear_ntp_app_storage

    username, password = credentials_for_pipeline(pipeline)
    login = NtpAppLoginPage(page)
    if force:
        _clear_ntp_app_storage(page)
        login.open(clear_storage=False)
    login.login(username, password, force=force)
    NtpAppLeadsPage(page).wait_for_leads()


def open_ntp_app_as_pipeline_user(
    context: BrowserContext,
    browser: Browser,
    pipeline: MsAppPipeline,
) -> Page:
    app_page = context.new_page()
    app_page.set_default_timeout(Config.TIMEOUT)
    login_ntp_app(app_page, pipeline)
    return app_page


def open_ntp_app_rbac_page(context: BrowserContext, pipeline: MsAppPipeline) -> Page:
    from pages.ntp_app.leads_page import NtpAppLeadsPage
    from pages.ntp_app.login_page import NtpAppLoginPage

    rbac_page = context.new_page()
    rbac_page.set_default_timeout(Config.TIMEOUT)
    login = NtpAppLoginPage(rbac_page)
    login.open()
    username, password = credentials_for_pipeline(pipeline)
    login.login(username, password, force=False)
    NtpAppLeadsPage(rbac_page).wait_for_leads()
    return rbac_page


def ensure_ntp_app_lead_assignee(
    page: Page,
    deal_name: str,
    pipeline: MsAppPipeline,
    *,
    bucket: str,
    assignee_page: Page | None = None,
) -> None:
    ensure_ms_app_lead_assignee(
        page,
        deal_name,
        pipeline,
        bucket=bucket,
        assignee_page=assignee_page,
    )


__all__ = [
    "build_ntp_app_staff_url",
    "ensure_ntp_app_lead_assignee",
    "fetch_user_id_from_context",
    "login_ntp_app",
    "open_ntp_app_as_pipeline_user",
    "open_ntp_app_rbac_page",
    "open_ntp_app_via_staff_url",
    "pipeline_label",
]
