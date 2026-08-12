"""Mortgage Snapshot App staff authentication helpers."""

from __future__ import annotations

import os
from typing import Literal
from urllib.parse import quote

from playwright.sync_api import Browser, BrowserContext, Page

from utils.config import Config
from utils.logger import get_logger

logger = get_logger()

MsAppPipeline = Literal["fe", "be", "admin"]

_AUTH_STATE_CACHE: dict[str, dict] = {}


def auth_token_from_storage_state(storage_state: dict) -> str:
    for cookie in storage_state.get("cookies", []):
        if cookie.get("name") == "auth_token" and cookie.get("value"):
            return str(cookie["value"])
    raise ValueError("auth_token cookie not found in storage state")


def auth_validate_url() -> str:
    base = Config.AUTH_VALIDATE_URL.rstrip("/")
    return f"{base}/validate-session"


def credentials_for_pipeline(pipeline: MsAppPipeline) -> tuple[str, str]:
    if pipeline == "fe":
        return Config.FE_USERNAME, Config.FE_PASSWORD
    if pipeline == "be":
        return Config.BE_USERNAME, Config.BE_PASSWORD
    return Config.USERNAME, Config.PASSWORD


def storage_state_for_pipeline(browser: Browser, pipeline: MsAppPipeline) -> dict:
    username, password = credentials_for_pipeline(pipeline)
    cache_key = f"{pipeline}:{username}"
    if cache_key not in _AUTH_STATE_CACHE:
        _AUTH_STATE_CACHE[cache_key] = _login_storage_state(browser, username, password)
    return _AUTH_STATE_CACHE[cache_key]


def _login_storage_state(browser: Browser, username: str, password: str) -> dict:
    from pages.login_page import LoginPage

    context = browser.new_context(viewport=None)
    page = context.new_page()
    page.set_default_timeout(Config.TIMEOUT)
    login = LoginPage(page)
    login.open()
    login.valid_login(username, password)
    login.click_signup_btn()
    page.wait_for_url(lambda url: "/login" not in url, timeout=Config.TIMEOUT)
    state = context.storage_state()
    context.close()
    return state


def fetch_user_id_from_context(context: BrowserContext) -> str:
    """Resolve user id using the live browser context (includes current cookies)."""
    storage_state = context.storage_state()
    token = auth_token_from_storage_state(storage_state)
    response = context.request.get(
        auth_validate_url(),
        headers={
            "authorization": token,
            "Content-Type": "application/json",
        },
    )
    if not response.ok:
        raise RuntimeError(
            f"validate-session failed ({response.status}): {response.text()}"
        )
    payload = response.json()
    user_id = payload.get("user", {}).get("id")
    if not user_id:
        raise RuntimeError("validate-session response missing user.id")
    return str(user_id)


def fetch_user_id(browser: Browser, storage_state: dict) -> str:
    token = auth_token_from_storage_state(storage_state)
    context = browser.new_context(storage_state=storage_state)
    try:
        response = context.request.get(
            auth_validate_url(),
            headers={
                "authorization": token,
                "Content-Type": "application/json",
            },
        )
        if not response.ok:
            raise RuntimeError(
                f"validate-session failed ({response.status}): {response.text()}"
            )
        payload = response.json()
        user_id = payload.get("user", {}).get("id")
        if not user_id:
            raise RuntimeError("validate-session response missing user.id")
        return str(user_id)
    finally:
        context.close()


def build_ms_app_staff_url(browser: Browser, storage_state: dict) -> str:
    token = auth_token_from_storage_state(storage_state)
    user_id = fetch_user_id(browser, storage_state)
    return (
        f"{Config.MORTGAGE_SNAPSHOT_APP_URL}/staff"
        f"?id={quote(user_id)}&token={quote(token)}"
    )


def login_ms_app(page: Page, pipeline: MsAppPipeline, *, force: bool = False) -> None:
    """Authenticate at dev.mortgagesnapshot.vibecircuit.ca using CRM role credentials."""
    from pages.mortgage_snapshot_app.leads_page import MortgageSnapshotAppLeadsPage
    from pages.mortgage_snapshot_app.login_page import (
        MortgageSnapshotAppLoginPage,
        _clear_ms_app_storage,
    )

    username, password = credentials_for_pipeline(pipeline)
    login = MortgageSnapshotAppLoginPage(page)
    if force:
        _clear_ms_app_storage(page)
        login.open(clear_storage=False)
    login.login(username, password, force=force)
    MortgageSnapshotAppLeadsPage(page).wait_for_leads()


def ensure_ms_app_lead_assignee(
    page: Page,
    deal_name: str,
    pipeline: MsAppPipeline,
    *,
    bucket: str,
    assignee_page: Page | None = None,
) -> None:
    """Align CRM assignee with the MS App user before sync/RBAC checks."""
    from utils.entity_navigation import open_bucket_record
    from utils.lead_assignment import LeadAssignmentHelper, reassign_lead_agent

    sync_page = assignee_page or page
    expected_label = pipeline_label(pipeline)
    reassign_lead_agent(
        sync_page, deal_name, expected_label, bucket=bucket
    )
    open_bucket_record(sync_page, bucket, deal_name)
    helper = LeadAssignmentHelper(sync_page)
    helper.open_edit_lead_from_menu()
    actual = helper.get_assigned_agent_label()
    from utils.lead_assignment import _agent_label_matches

    assert _agent_label_matches(actual, expected_label), (
        f"CRM assignee mismatch for {deal_name!r}: expected {expected_label!r}, got {actual!r}"
    )
    helper.page.keyboard.press("Escape")
    open_bucket_record(page, bucket, deal_name)


def open_ms_app_as_pipeline_user(
    context: BrowserContext,
    browser: Browser,
    pipeline: MsAppPipeline,
) -> Page:
    """Open MS App /leads authenticated as the assigned pipeline user."""
    app_page = context.new_page()
    app_page.set_default_timeout(Config.TIMEOUT)
    login_ms_app(app_page, pipeline)
    return app_page


def open_ms_app_rbac_page(
    context: BrowserContext,
    pipeline: MsAppPipeline,
) -> Page:
    """
    Open a fresh MS App tab for RBAC checks at the native login URL.

    Does not clear CRM cookies — only navigates to Config.ms_app_login_url().
    """
    from pages.mortgage_snapshot_app.leads_page import MortgageSnapshotAppLeadsPage
    from pages.mortgage_snapshot_app.login_page import MortgageSnapshotAppLoginPage

    rbac_page = context.new_page()
    rbac_page.set_default_timeout(Config.TIMEOUT)
    login = MortgageSnapshotAppLoginPage(rbac_page)
    login.open()
    username, password = credentials_for_pipeline(pipeline)
    login.login(username, password, force=False)
    MortgageSnapshotAppLeadsPage(rbac_page).wait_for_leads()
    return rbac_page


def resolve_ms_app_pipeline(
    bucket: str,
    assigned_pipeline: MsAppPipeline | None = None,
) -> MsAppPipeline:
    """Default MS App user per CRM bucket when pipeline is not explicitly set."""
    from utils.entity_navigation import MY_DEALS_BUCKET, SALES_BACKEND_BUCKET

    if assigned_pipeline is not None:
        return assigned_pipeline
    if bucket == SALES_BACKEND_BUCKET:
        return "be"
    if bucket == MY_DEALS_BUCKET:
        return "admin"
    return "fe"


def cross_role_pipeline(assigned_pipeline: MsAppPipeline) -> MsAppPipeline:
    """Return the cross-role agent used for non-assigned MS App RBAC checks."""
    if assigned_pipeline == "fe":
        return "be"
    if assigned_pipeline == "be":
        return "fe"
    override = os.environ.get("MS_APP_RBAC_ADMIN_CROSS_ROLE", "fe").lower()
    if override == "be":
        return "be"
    return "fe"


def pipeline_label(pipeline: MsAppPipeline) -> str:
    from test_page_data import test_entities

    if pipeline == "fe":
        return Config.FE_AGENT_LABEL
    if pipeline == "be":
        return Config.BE_AGENT_LABEL
    return test_entities.ASSIGNED_AGENT
