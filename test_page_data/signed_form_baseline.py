"""Persist Signed Form snapshot for cross-stage verification (Compliance → Client Care)."""

import json
from dataclasses import asdict
from pathlib import Path

from test_page_data.compliance_data import SignedFormSnapshot

_BASELINE_FILE = Path(__file__).resolve().parent / ".signed_form_baseline.json"


def save(snapshot: SignedFormSnapshot) -> None:
    _BASELINE_FILE.write_text(
        json.dumps(asdict(snapshot), indent=2),
        encoding="utf-8",
    )


def load() -> SignedFormSnapshot | None:
    if not _BASELINE_FILE.exists():
        return None
    data = json.loads(_BASELINE_FILE.read_text(encoding="utf-8"))
    return SignedFormSnapshot(**data)
