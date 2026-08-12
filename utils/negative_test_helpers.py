"""Shared helpers for negative (empty / invalid) validation tests."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class InvalidFieldCase:
    field: str
    value: str
    message: str


def verify_invalid_fields(
    validator,
    cases: list[InvalidFieldCase],
    set_field: Callable[[str, str], None],
    clear_field: Callable[[str], None],
    save: Callable[[], None],
    item=None,
    reset: Callable[[], None] | None = None,
):
    """Fill each invalid value, save, assert error, then clear the field."""
    for case in cases:
        if reset:
            reset()
        set_field(case.field, case.value)
        save()
        validator.assert_field_error(case.message, item=item)
        clear_field(case.field)


def verify_required_fields(validator, messages: list[str], item=None, require_all=False):
    """Assert required-field messages are visible after an empty submit."""
    if require_all:
        validator.assert_field_errors(messages, item=item)
    else:
        validator.assert_messages_subset(messages, item=item)
