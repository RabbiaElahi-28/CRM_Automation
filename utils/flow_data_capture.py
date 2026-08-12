"""Capture form data object instances during a flow step without changing test helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


@contextmanager
def capture_constructed_instances(*classes: type) -> Iterator[dict[str, Any]]:
    """
    Temporarily wrap class constructors so the last constructed instance
    per class is available to the reporting layer.
    """
    captured: dict[str, Any] = {}
    originals: dict[type, Any] = {}

    for cls in classes:
        original_init = cls.__init__

        def patched_init(self, *args, __orig=original_init, __name=cls.__name__, **kwargs):
            __orig(self, *args, **kwargs)
            captured[__name] = self

        cls.__init__ = patched_init
        originals[cls] = original_init

    try:
        yield captured
    finally:
        for cls, original_init in originals.items():
            cls.__init__ = original_init
