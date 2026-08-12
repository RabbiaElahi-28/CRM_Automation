"""Kanban column inventory and record placement verification."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from utils.config import Config
from utils.entity_navigation import _BUCKET_PATHS, _filter_bucket_record, _record_card_link


def _open_bucket_list(page: Page, bucket_name: str) -> str:
    bucket_path = _BUCKET_PATHS.get(bucket_name)
    if bucket_path:
        page.goto(f"{Config.BASE_URL}{bucket_path}")
    else:
        page.get_by_role("link", name=bucket_name).click()
    page.wait_for_load_state("domcontentloaded")
    return bucket_path or page.url.split("?")[0].replace(Config.BASE_URL, "")


def _kanban_column(page: Page, column_title: str):
    """
    Resolve a kanban column's card area.

    CRM layout (GenericKanbanBoard): column header ``h3`` and card scroll
    ``div.shadow-column`` are siblings inside the same column wrapper — the
    ``h3`` is NOT nested inside ``shadow-column``.
    """
    title = page.locator("h3").filter(has_text=column_title).first
    expect(title).to_be_visible(timeout=30000)
    return title.locator(
        "xpath=ancestor::div[contains(@class,'rounded-lg')][1]"
    ).locator("div.shadow-column")


def verify_kanban_columns(page: Page, bucket_name: str, expected_columns: list[str]) -> None:
    """Assert required kanban column headers are visible on a bucket board."""
    _open_bucket_list(page, bucket_name)
    for column_title in expected_columns:
        expect(page.locator("h3").filter(has_text=column_title).first).to_be_visible(
            timeout=30000,
        )


def verify_record_in_kanban_column(
    page: Page,
    bucket_name: str,
    record_name: str,
    column_title: str,
) -> None:
    """Search bucket, then assert the card is under a specific kanban column."""
    bucket_path = _filter_bucket_record(page, bucket_name, record_name)
    column = _kanban_column(page, column_title)
    expect(column.first).to_be_visible(timeout=30000)
    record = column.locator(f"a[href*='{bucket_path}/']").filter(has_text=record_name)
    expect(record.first).to_be_visible(timeout=30000)


def open_record_in_kanban_column(
    page: Page,
    bucket_name: str,
    record_name: str,
    column_title: str,
) -> None:
    """Search bucket, verify column placement, and open the record like a user."""
    bucket_path = _filter_bucket_record(page, bucket_name, record_name)
    column = _kanban_column(page, column_title)
    expect(column.first).to_be_visible(timeout=30000)
    link = column.locator(f"a[href*='{bucket_path}/']").filter(has_text=record_name).first
    expect(link).to_be_visible(timeout=30000)
    href = link.get_attribute("href")
    if not href:
        raise AssertionError(f"Kanban card for {record_name!r} in {column_title!r} has no href")
    target = href if href.startswith("http") else f"{Config.BASE_URL}{href}"
    page.goto(target)
    page.wait_for_load_state("domcontentloaded")
    expect(page.get_by_role("tab", name="Profile")).to_be_visible(timeout=30000)
