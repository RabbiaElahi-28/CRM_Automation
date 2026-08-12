"""Reusable save → reopen → compare persistence verification."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def normalize_numeric(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = str(value).replace(",", "").replace("%", "").strip()
    if not cleaned:
        return ""
    try:
        return format(float(cleaned), "g")
    except ValueError:
        return cleaned


def assert_field_values_match(
    actual: dict[str, Any],
    expected: dict[str, Any],
    *,
    normalize: Callable[[Any], str] | None = None,
    label: str = "form",
) -> None:
    normalize = normalize or (lambda v: str(v).strip())
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key, "")
        if normalize(actual_value) != normalize(expected_value):
            mismatches.append(
                f"{key}: expected {expected_value!r}, got {actual_value!r}"
            )
    assert not mismatches, f"{label} persistence mismatch:\n" + "\n".join(mismatches)


def verify_form_persistence(
    *,
    read_values: Callable[[], dict[str, Any]],
    reopen: Callable[[], None],
    expected: dict[str, Any],
    normalize: Callable[[Any], str] | None = None,
    label: str = "form",
) -> None:
    """Capture values, reopen the form, and assert saved values match."""
    reopen()
    actual = read_values()
    assert_field_values_match(actual, expected, normalize=normalize, label=label)
