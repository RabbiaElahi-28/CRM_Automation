"""Cross-stage prefilled data verification helpers."""

from __future__ import annotations

import re

from pages.approved_page import ApprovedPage
from pages.mortgage_snapshot_page import MortgageSnapshotPage
from pages.profile_page import ProfilePage
from pages.submitted_page import SubmittedPage
from test_page_data.addcoborrower_data import test_data as coborrower_data
from test_page_data.approved_data import (
    APPROVED_APPLICANTS_PREFILL,
    ApprovedSnapshotPrefill,
)
from utils.form_persistence import normalize_numeric


def _concat_points(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _co_applicant_name() -> str:
    co = coborrower_data["co_borrower"]
    return f"{co['first_name']} {co['last_name']}".strip()


class FormPrefillVerification:
    """Reusable Profile / Snapshot → stage form prefill checks."""

    def __init__(self, page):
        self.page = page

    def verify_submitted_loan_amount_from_profile(
        self,
        deal_name: str,
        *,
        bucket: str,
        option_number: int = 1,
    ) -> None:
        profile = ProfilePage(self.page)
        submitted = SubmittedPage(self.page)

        profile.open_lead_profile(deal_name, bucket=bucket)
        profile_loan = profile.read_mortgage_loan_amount()
        assert profile_loan, "Profile loan amount must be populated before Submitted prefill check"

        submitted.open_submitted(deal_name, bucket=bucket)
        submitted_loan = submitted.read_option_loan_amount(option_number)

        assert normalize_numeric(submitted_loan) == normalize_numeric(profile_loan), (
            "Submitted loan amount must match Profile → Mortgage Information → Loan amount: "
            f"profile={profile_loan!r}, submitted={submitted_loan!r}"
        )

    def read_snapshot_prefill(self) -> ApprovedSnapshotPrefill:
        snapshot = MortgageSnapshotPage(self.page)
        option4_type = snapshot.read_combobox_text(snapshot.option4_dropdown)
        option5_type = snapshot.read_combobox_text(snapshot.option5_dropdown)
        return ApprovedSnapshotPrefill(
            credit_score=snapshot.credit_score.input_value(),
            tds_ratio=snapshot.tds_score.input_value(),
            co_applicant_name=_co_applicant_name(),
            co_applicant_credit_score=snapshot.co_credit_score.input_value(),
            co_applicant_credit_utilization=snapshot.co_credit_utilization.input_value(),
            average_interest_rate=snapshot.current_rate.input_value(),
            min_monthly_payments=snapshot.monthly_payment.input_value(),
            time_to_pay=snapshot.years_to_pay.input_value(),
            total_interest_paid=snapshot.total_interest.input_value(),
            **APPROVED_APPLICANTS_PREFILL,
            new_option_one=option4_type,
            why_this_option_works=_concat_points(
                snapshot.option4_point1.input_value(),
                snapshot.option4_point2.input_value(),
                snapshot.option4_point3.input_value(),
            ),
            new_option_two=option5_type,
            why_this_option_works_best=_concat_points(
                snapshot.option5_point1.input_value(),
                snapshot.option5_point2.input_value(),
                snapshot.option5_point3.input_value(),
            ),
        )

    def verify_approved_prefilled_from_profile_and_snapshot(
        self,
        deal_name: str,
        *,
        bucket: str,
        snapshot_prefill: ApprovedSnapshotPrefill | None = None,
    ) -> None:
        profile = ProfilePage(self.page)
        approved = ApprovedPage(self.page)

        profile.open_lead_profile(deal_name, bucket=bucket)
        profile_name = profile.read_lead_name()
        if snapshot_prefill is None:
            snapshot_prefill = self.read_snapshot_prefill()

        approved.open_approved(deal_name, bucket=bucket)
        approved.verify_approved_form_tab_active()
        approved.verify_mortgage_option_prefilled()

        expected = ApprovedSnapshotPrefill(
            name=profile_name,
            **{
                key: value
                for key, value in snapshot_prefill.__dict__.items()
                if key != "name"
            },
        )
        approved.verify_prefilled_from_snapshot(expected)


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())
