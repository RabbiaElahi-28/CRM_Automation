"""Build per-stage test-data payloads for flow HTML reporting from real data sources."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from test_page_data.addcoborrower_data import test_data as coborrower_data
from test_page_data.compliance_data import ComplianceData
from test_page_data.lead_edit_data import lead_edit_data
from test_page_data.note_data import notes_test_data
from test_page_data.signed_data import SignedData
from test_page_data.submitted_data import SubmittedData
from test_page_data.appraisal_order_data import AppraisalOrderData
from test_page_data.approved_data import ApprovedData
from test_page_data.mortgage_snapshot_data import MortgageSnapshotData
from utils.config import Config
from utils.test_data_factory import get_last_valid_lead_data


def _object_to_dict(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return {
            key: val
            for key, val in vars(value).items()
            if not key.startswith("_")
        }
    return value


def normalize_create_lead_data(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not raw:
        return {}
    return {
        "lead_name": raw.get("enter_name") or raw.get("deal_name"),
        "first_name": raw.get("first_name"),
        "last_name": raw.get("last_name"),
        "email": raw.get("enter_email"),
        "phone_number": raw.get("enter_phone"),
        "gender": raw.get("select_gender"),
        "marital_status": raw.get("select_marital_status"),
        "property_address": raw.get("enter_property_address_street_number"),
        "client_address": raw.get("enter_address_street_number"),
        "mortgage_type": raw.get("select_property_type"),
        "mortgage_amount": raw.get("enter_loan_amount"),
        "mortgage_rate": raw.get("enter_mortgage_rate"),
        "credit_score": raw.get("enter_credit_score"),
        "property_value": raw.get("enter_property_value"),
        "monthly_payment": raw.get("enter_monthly_payment"),
        "balance_owing": raw.get("enter_balance_owing"),
        "working_situation": raw.get("enter_working_situation"),
        "working_location": raw.get("enter_working_location"),
        "income": raw.get("enter_income"),
        "employer_name": raw.get("enter_employer_name"),
        "whats_important": raw.get("select_whats_important"),
        "date_of_birth": {
            "month": raw.get("select_month"),
            "day": raw.get("select_day"),
            "year": raw.get("select_year"),
        },
    }


def login_stage_data() -> dict[str, Any]:
    return {
        "username": Config.USERNAME,
        "auth_method": "session_fixture",
    }


def edit_lead_stage_data() -> dict[str, Any]:
    return {
        "contact": lead_edit_data["contact"],
        "gender": lead_edit_data["gender"],
        "marital_status": lead_edit_data["marital_status"],
        "address": lead_edit_data["address"],
        "date_of_birth": lead_edit_data["dob"],
        "mortgage": lead_edit_data["mortgage"],
        "property": lead_edit_data["property"],
        "employment": lead_edit_data["employment"],
    }


def co_borrower_stage_data() -> dict[str, Any]:
    return {"co_borrower": coborrower_data["co_borrower"]}


def note_stage_data() -> dict[str, Any]:
    return {"note": notes_test_data["note"]}


def create_lead_stage_data() -> dict[str, Any]:
    return {"form_data": normalize_create_lead_data(get_last_valid_lead_data())}


def merge_captured_instances(metadata: dict[str, Any], captured: dict[str, Any]) -> None:
    """Attach instances constructed during the step under readable keys."""
    key_map = {
        "MortgageSnapshotData": "mortgage_snapshot",
        "AppraisalOrderData": "appraisal_order",
        "SubmittedData": "submitted_deal",
        "ApprovedData": "approved_deal",
        "SignedData": "signed_deal",
        "ComplianceData": "compliance",
    }
    for class_name, instance in captured.items():
        key = key_map.get(class_name, class_name)
        metadata[key] = _object_to_dict(instance)


def client_care_stage_data(signed_baseline: Any | None) -> dict[str, Any]:
    if signed_baseline is None:
        return {}
    return {"signed_form_baseline": _object_to_dict(signed_baseline)}


# Stage metadata builders used by orchestration (reporting layer only).
STAGE_STATIC_BUILDERS = {
    "login": login_stage_data,
    "edit_lead": edit_lead_stage_data,
    "add_co_borrower": co_borrower_stage_data,
    "add_note": note_stage_data,
    "create_lead": create_lead_stage_data,
}

STAGE_CAPTURE_CLASSES = {
    "mortgage_snapshot": (MortgageSnapshotData,),
    "appraisal_order": (AppraisalOrderData,),
    "submit_deal": (SubmittedData,),
    "approve_deal": (ApprovedData,),
    "signed": (SignedData,),
    "compliance": (ComplianceData,),
}
