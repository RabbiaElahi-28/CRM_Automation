"""Shared navigation for opening leads/deals from bucket kanban views."""

import re

from playwright.sync_api import Page, expect

from utils.config import Config

MY_LEADS_BUCKET = "My Leads"
MY_DEALS_BUCKET = "My Deals"
LEAD_BUCKET = "Lead Bucket"
SALES_BACKEND_BUCKET = "Sales Backend"
COMPLIANCE_BUCKET = "Compliance"
CLIENT_CARE_BUCKET = "Client Care"
MARKETING_BUCKET = "Marketing"

_BUCKET_PATHS = {
    MY_LEADS_BUCKET: "/my-leads",
    MY_DEALS_BUCKET: "/sales",
    LEAD_BUCKET: "/lead-bucket",
    SALES_BACKEND_BUCKET: "/sales-backend",
    COMPLIANCE_BUCKET: "/compliance",
    CLIENT_CARE_BUCKET: "/client-care",
    MARKETING_BUCKET: "/marketing",
}

_SEARCH_DEBOUNCE_MS = 400  # apps/nextjs/src/hooks/useBackendFilters.ts


def _list_search_input(page):
    """Bucket filter search — not the header nav search (header-lead-search)."""
    return page.locator('[name="list-global-search"]')


def _record_card_link(page, bucket_path: str, record_name: str):
    """Kanban cards wrap name + timestamp in one link; match by href and deal name."""
    return page.locator(f"a[href*='{bucket_path}/']").filter(has_text=record_name)


def _wait_for_page_ready(page: Page) -> None:
    """CRM pages often never reach networkidle (analytics/CORS); prefer DOM ready."""
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass


def _wait_for_bucket_search_applied(page: Page, bucket_path: str, record_name: str) -> None:
    """Wait until debounced bucket search is applied and the target card is visible."""
    page.wait_for_timeout(_SEARCH_DEBOUNCE_MS)
    page.wait_for_function(
        """(expected) => {
            const params = new URLSearchParams(window.location.search);
            return params.get('search') === expected;
        }""",
        arg=record_name,
        timeout=15000,
    )


    link = _record_card_link(page, bucket_path, record_name).first
    for attempt in range(6):
        try:
            expect(link).to_be_visible(timeout=10000)
            return
        except AssertionError:
            if attempt == 5:
                raise
            page.wait_for_timeout(2000)
            search = _list_search_input(page)
            if search.input_value() != record_name:
                search.fill(record_name)
                page.wait_for_timeout(_SEARCH_DEBOUNCE_MS)


def open_bucket_record(page, bucket_name: str, record_name: str) -> None:
    """Filter the bucket kanban board by name and open the matching card."""
    bucket_path = _filter_bucket_record(page, bucket_name, record_name)
    link = _record_card_link(page, bucket_path, record_name).first
    expect(link).to_be_visible(timeout=30000)
    href = link.get_attribute("href")
    if not href:
        raise AssertionError(f"Kanban card for {record_name!r} has no href")
    target = href if href.startswith("http") else f"{Config.BASE_URL}{href}"
    page.goto(target)
    _wait_for_page_ready(page)
    expect(page).to_have_url(
        re.compile(rf"{re.escape(bucket_path)}/[A-Za-z0-9]+"),
        timeout=30000,
    )
    expect(page.get_by_role("tab", name="Profile")).to_be_visible(timeout=30000)


def _filter_bucket_record(page, bucket_name: str, record_name: str) -> str:
    if not record_name:
        raise ValueError(
            f"Cannot search {bucket_name!r}: record_name is empty — "
            "check flow orchestrator did not overwrite deal_name with None"
        )
    bucket_path = _BUCKET_PATHS.get(bucket_name)
    if bucket_path:
        page.goto(f"{Config.BASE_URL}{bucket_path}")
    else:
        page.get_by_role("link", name=bucket_name).click()

    _wait_for_page_ready(page)
    bucket_path = bucket_path or page.url.split("?")[0].replace(Config.BASE_URL, "")

    search = _list_search_input(page)
    expect(search).to_be_visible(timeout=30000)
    search.fill(record_name)
    _wait_for_bucket_search_applied(page, bucket_path, record_name)
    return bucket_path


def verify_bucket_record_visible(page, bucket_name: str, record_name: str) -> None:
    """Filter a bucket kanban board and verify the matching card is visible."""
    bucket_path = _filter_bucket_record(page, bucket_name, record_name)
    from playwright.sync_api import expect

    expect(_record_card_link(page, bucket_path, record_name).first).to_be_visible(timeout=30000)


def _header_search_input(page):
    """Top navigation global search — not bucket list-global-search."""
    return page.locator("#header-lead-search")


def open_lead_via_header_search(page, lead_name: str) -> None:
    """
    Open a lead via the header SearchAutocomplete (#header-lead-search only).

    Use only for non-assigned RBAC tests. Bucket list-global-search is not used here.
    """
    from playwright.sync_api import expect

    page.goto(
        Config.BASE_URL,
        wait_until="domcontentloaded",
        timeout=Config.TIMEOUT,
    )
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass

    search = page.locator("#header-lead-search")
    expect(search).to_be_visible(timeout=30000)
    search.click()
    search.fill(lead_name)

    searching = page.get_by_text("Searching...")
    if searching.count() > 0:
        searching.wait_for(state="hidden", timeout=30000)

    listbox = page.locator("[role='listbox']")
    option = listbox.get_by_role("option").filter(has_text=lead_name)
    expect(option.first).to_be_visible(timeout=30000)
    option.first.click()
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
