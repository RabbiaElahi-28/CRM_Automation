"""Shared Playwright wait helpers for flaky UI patterns."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect

from utils.config import Config

CANADIAN_POSTAL_CODE_PATTERN = re.compile(r"^[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d$")

RELIABLE_PLACES_QUERIES = (
    "100 King Street West, Toronto",
    "5677 Avenue, Edmonton",
)


def wait_for_page_ready(page: Page, *, networkidle_timeout_ms: int = 8000) -> None:
    """Wait for DOM ready; optionally try networkidle without failing the step."""
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=networkidle_timeout_ms)
    except Exception:
        pass


def _places_suggestions(page: Page) -> Locator:
    return page.locator(".pac-container .pac-item")


def _trigger_places_autocomplete(input_locator: Locator) -> None:
    """Nudge Google Places to refresh suggestions after typing."""
    try:
        input_locator.press(" ")
        input_locator.press("Backspace")
    except Exception:
        pass


def _click_or_keyboard_select(page: Page, suggestion: Locator) -> bool:
    try:
        expect(suggestion).to_be_visible(timeout=3000)
        suggestion.scroll_into_view_if_needed()
        suggestion.click()
        page.wait_for_timeout(300)
        return True
    except AssertionError:
        pass

    try:
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        return True
    except Exception:
        return False


def _try_select_places_query(
    page: Page,
    input_locator: Locator,
    query: str,
    *,
    type_delay: int,
) -> bool:
    input_locator.click()
    input_locator.fill("")
    input_locator.press_sequentially(str(query), delay=type_delay)
    _trigger_places_autocomplete(input_locator)

    suggestion = _places_suggestions(page).first
    for wait_ms in (800, 1200, 2000, 3000, 4000):
        page.wait_for_timeout(wait_ms)
        if suggestion.count() == 0:
            _trigger_places_autocomplete(input_locator)
            continue
        if _click_or_keyboard_select(page, suggestion):
            return True

    return False


def select_google_places_suggestion(
    page: Page,
    input_locator: Locator,
    query: str,
    *,
    type_delay: int = 50,
    fallback_fill: bool = True,
) -> None:
    """Type into a Google Places field and select the first visible suggestion."""
    queries: list[str] = [str(query)]
    if fallback_fill and str(query) not in RELIABLE_PLACES_QUERIES:
        queries.extend(RELIABLE_PLACES_QUERIES)

    seen: set[str] = set()
    for candidate in queries:
        if candidate in seen:
            continue
        seen.add(candidate)
        if _try_select_places_query(
            page, input_locator, candidate, type_delay=type_delay
        ):
            return

    if fallback_fill:
        for candidate in RELIABLE_PLACES_QUERIES:
            if candidate in seen:
                continue
            seen.add(candidate)
            if _try_select_places_query(
                page, input_locator, candidate, type_delay=type_delay
            ):
                return

    raise AssertionError(
        f"Google Places suggestion not selected for query {query!r}. "
        "Address autocomplete did not return a selectable suggestion."
    )


def wait_for_url_pattern(page: Page, pattern: str | re.Pattern[str]) -> None:
    """Wait until the page URL matches a regex pattern."""
    expect(page).to_have_url(re.compile(pattern), timeout=Config.TIMEOUT)


def is_complete_canadian_postal_code(value: str | None) -> bool:
    """Return True when value matches Canadian postal format (e.g. K1A 0B1)."""
    if not value:
        return False
    return bool(CANADIAN_POSTAL_CODE_PATTERN.match(value.strip()))


def normalize_canadian_postal_code(value: str) -> str:
    """Normalize to uppercase `K1A 0B1` formatting."""
    cleaned = re.sub(r"\s+", "", value.strip()).upper()
    if len(cleaned) == 6:
        return f"{cleaned[:3]} {cleaned[3:]}"
    return value.strip().upper()


def ensure_complete_postal_code(
    postal_locator: Locator,
    expected_postal_code: str,
) -> None:
    """Re-enter postal code when Google Places leaves an incomplete value."""
    if not expected_postal_code:
        return
    postal_locator.wait_for(state="visible", timeout=10000)
    current = postal_locator.input_value().strip()
    if is_complete_canadian_postal_code(current):
        return
    postal_locator.fill(normalize_canadian_postal_code(expected_postal_code))
