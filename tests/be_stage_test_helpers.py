"""Shared helpers for Sales Backend stage progression tests."""

import pytest

from utils.config import Config


def skip_if_be_agent_unauthenticated(page) -> None:
    page.goto(Config.BASE_URL)
    page.wait_for_load_state("domcontentloaded")
    if "/login" in page.url:
        pytest.skip(
            "BE agent credentials unavailable on dev CRM — cannot validate stage progression."
        )
