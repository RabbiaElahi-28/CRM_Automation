"""Normalize CRM Approved/Snapshot/Profile values for NTP display expectations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from utils.mortgage_snapshot_display import (
    credit_rating_for_score,
    first_name_from_deal_name,
    format_currency_display,
    normalize_currency,
    normalize_percent,
    normalize_whitespace,
    normalize_years,
)


def normalize_date_to_mmddyyyy(value: str) -> str:
    """Convert profile 'Form filled at' text to NTP header date (MM/DD/YYYY)."""
    cleaned = normalize_whitespace(value)
    if not cleaned or cleaned in {"-", "N/A", "_ _"}:
        return ""

    formats = (
        "%m/%d/%Y",
        "%m/%d/%Y %I:%M %p",
        "%B %d, %Y at %I:%M %p",
        "%B %d, %Y %I:%M %p",
        "%d %B, %Y %I:%M %p",
        "%d %B, %Y",
        "%B %d, %Y",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned.split(" UTC")[0].strip(), fmt)
            return parsed.strftime("%m/%d/%Y")
        except ValueError:
            continue

    month_match = re.search(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        cleaned,
    )
    if month_match:
        month_name, day, year = month_match.groups()
        for fmt in ("%B %d %Y", "%b %d %Y"):
            try:
                parsed = datetime.strptime(f"{month_name} {day} {year}", fmt)
                return parsed.strftime("%m/%d/%Y")
            except ValueError:
                continue
    return ""


def co_applicant_note_display(raw: str) -> str:
    cleaned = normalize_whitespace(raw)
    return cleaned if cleaned else "N/A"


@dataclass
class NtpDisplayExpectations:
    deal_name: str
    header_first_name: str
    profile_full_name: str
    vfli_number: str
    header_time: str
    lead_email: str = ""

    applicant_credit_score: str = ""
    applicant_credit_rating: str = ""
    applicant_tds: str = ""
    applicant_credit_utilization: str = ""
    applicant_credit_notes: str = ""
    high_interest_debt: str = ""

    co_applicant_name: str = ""
    co_applicant_credit_score: str = ""
    co_applicant_credit_rating: str = ""
    co_applicant_tds: str = ""
    co_applicant_credit_utilization: str = ""
    co_applicant_credit_notes: str = "N/A"

    average_interest_rate: str = ""
    min_monthly_payments: str = ""
    total_yearly_payment: str = ""
    time_to_pay: str = ""
    total_interest_paid: str = ""
    total_cost_of_debt: str = ""

    applicants_needs: list[str] = field(default_factory=list)
    applicants_goals: str = ""

    plan_year_one: dict[str, str] = field(default_factory=dict)
    plan_year_two: dict[str, str] = field(default_factory=dict)
    plan_year_three: dict[str, str] = field(default_factory=dict)

    new_option_one: str = ""
    why_option_one: str = ""
    new_option_two: str = ""
    why_option_two: str = ""

    monthly_mortgage_payment: str = ""
    new_solution_payment: str = ""
    estimated_monthly_saving: str = ""
    current_total_debt: str = ""
    new_debt_payments: str = ""
    yearly_savings_estimate: str = ""
    combined_payments: str = ""
    new_monthly_payments: str = ""

    appraised_value: str = ""
    total_mortgages: str = ""
    remaining_equity: str = ""


def build_ntp_display_expectations(
    *,
    deal_name: str,
    profile_full_name: str,
    form_filled_at: str,
    captured_approved: dict[str, str],
    captured_snapshot: dict[str, str],
    lead_email: str = "",
    co_applicant_display_name: str = "N/A",
) -> NtpDisplayExpectations:
    credit_score = captured_approved.get("creditScore", "")
    co_credit_score = captured_approved.get("coApplicantCreditScore", "")
    co_name = normalize_whitespace(
        captured_approved.get("coApplicantName", "") or co_applicant_display_name
    )
    tds = captured_approved.get("tdsRatio", "")

    needs = [
        captured_approved.get("applicantsNeedsOne", ""),
        captured_approved.get("applicantsNeedsTwo", ""),
        captured_approved.get("applicantsNeedsThree", ""),
    ]
    needs = [normalize_whitespace(n) for n in needs if normalize_whitespace(n)]

    return NtpDisplayExpectations(
        deal_name=deal_name,
        header_first_name=first_name_from_deal_name(deal_name),
        profile_full_name=normalize_whitespace(profile_full_name),
        vfli_number=captured_snapshot.get("vfliNo", ""),
        header_time=normalize_date_to_mmddyyyy(form_filled_at),
        lead_email=lead_email,
        applicant_credit_score=credit_score,
        applicant_credit_rating=credit_rating_for_score(credit_score),
        applicant_tds=tds,
        applicant_credit_utilization=captured_snapshot.get("creditUtilization", ""),
        applicant_credit_notes=captured_approved.get("creditNotes", ""),
        high_interest_debt=captured_approved.get("currentMortgageDebtPayment", ""),
        co_applicant_name=co_name,
        co_applicant_credit_score=co_credit_score,
        co_applicant_credit_rating=credit_rating_for_score(co_credit_score),
        co_applicant_tds=tds,
        co_applicant_credit_utilization=captured_snapshot.get(
            "coApplicantCreditUtilization", ""
        ),
        co_applicant_credit_notes=co_applicant_note_display(
            captured_approved.get("coApplicantCreditNotes", "")
        ),
        average_interest_rate=captured_approved.get("averageInterestRate", ""),
        min_monthly_payments=captured_approved.get("minMonthlyPayments", ""),
        total_yearly_payment=captured_approved.get("totalYearlyPayment", ""),
        time_to_pay=captured_approved.get("timeToPay", ""),
        total_interest_paid=captured_approved.get("totalInterestPaid", ""),
        total_cost_of_debt=captured_approved.get("totalCostOfDebt", ""),
        applicants_needs=needs,
        applicants_goals=captured_approved.get("applicantsGoals", ""),
        plan_year_one={
            "action_one": captured_approved.get("planYearOneActionOne", ""),
            "action_two": captured_approved.get("planYearOneActionTwo", ""),
            "goals": captured_approved.get("planYearOneGoals", ""),
        },
        plan_year_two={
            "action_one": captured_approved.get("planYearTwoActionOne", ""),
            "action_two": captured_approved.get("planYearTwoActionTwo", ""),
            "goals": captured_approved.get("planYearTwoGoals", ""),
        },
        plan_year_three={
            "action_one": captured_approved.get("planYearThreeActionOne", ""),
            "action_two": captured_approved.get("planYearThreeActionTwo", ""),
            "goals": captured_approved.get("planYearThreeGoals", ""),
        },
        new_option_one=captured_approved.get("newOptionOne", ""),
        why_option_one=captured_approved.get("whyThisOptionWorks", ""),
        new_option_two=captured_approved.get("newOptionTwo", ""),
        why_option_two=captured_approved.get("whyThisOptionWorksBest", ""),
        monthly_mortgage_payment=captured_approved.get(
            "monthlyMortgagePaymentApproved", ""
        ),
        new_solution_payment=captured_approved.get("newSolutionPayment", ""),
        estimated_monthly_saving=captured_approved.get("estimatedMonthlySaving", ""),
        current_total_debt=captured_approved.get("currentTotalDebt", ""),
        new_debt_payments=captured_approved.get("newDebtPayments", ""),
        yearly_savings_estimate=captured_approved.get("yearlySavingsEstimate", ""),
        combined_payments=captured_approved.get("combinedPayments", ""),
        new_monthly_payments=captured_approved.get("newMonthlyPayments", ""),
        appraised_value=captured_approved.get("appraisedValue", ""),
        total_mortgages=captured_approved.get("totalMortgages", ""),
        remaining_equity=captured_approved.get("remainingEquity", ""),
    )


def expectations_from_captured(
    deal_name: str,
    captured_approved: dict[str, str],
    captured_snapshot: dict[str, str],
    *,
    profile_full_name: str,
    form_filled_at: str,
    with_co_borrower: bool,
) -> NtpDisplayExpectations:
    from utils.mortgage_snapshot_app_helpers import resolve_ms_app_lead_context

    _, co_applicant, _, lead_email = resolve_ms_app_lead_context(
        deal_name, with_co_borrower=with_co_borrower
    )
    return build_ntp_display_expectations(
        deal_name=deal_name,
        profile_full_name=profile_full_name,
        form_filled_at=form_filled_at,
        captured_approved=captured_approved,
        captured_snapshot=captured_snapshot,
        lead_email=lead_email,
        co_applicant_display_name=co_applicant,
    )
