"""Normalize CRM snapshot values and derive MS App display expectations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CREDIT_SCORE_RANGE_ROWS = (
    (750, float("inf"), "Above average"),
    (720, 749, "Average"),
    (680, 719, "Strong, but below average"),
    (620, 679, "Good, needs work"),
    (550, 619, "Needs improvement, but we can help"),
    (0, 549, "Lower than average, but we can help increase your score"),
)


def credit_rating_for_score(score: str | int) -> str:
    value = int(re.sub(r"[^\d]", "", str(score)) or "0")
    for low, high, description in CREDIT_SCORE_RANGE_ROWS:
        if low <= value <= high:
            return description
    return CREDIT_SCORE_RANGE_ROWS[-1][2]


def ms_app_credit_rating_matches(expected: str, displayed: str) -> bool:
    """
    MS App shows a short credit-rating label; CRM derives the full phrase.

    Example: expected ``Lower than average, but we can help increase your score``
    vs displayed ``Lower than average``.
    """
    expected = normalize_whitespace(expected)
    displayed = normalize_whitespace(displayed)
    if not expected or not displayed:
        return expected == displayed
    if expected in displayed or displayed in expected:
        return True
    expected_short = expected.split(",", maxsplit=1)[0].strip()
    displayed_short = displayed.split(",", maxsplit=1)[0].strip()
    return (
        expected_short == displayed_short
        or expected_short in displayed
        or displayed_short in expected
    )


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text or "").split())


def normalize_currency(value: str) -> str:
    digits = re.sub(r"[^\d.]", "", str(value or ""))
    if not digits:
        return ""
    if "." in digits:
        whole, frac = digits.split(".", 1)
        return f"{int(whole)}.{frac[:2].ljust(2, '0')[:2]}"
    return str(int(digits))


def format_currency_display(value: str) -> str:
    normalized = normalize_currency(value)
    if not normalized:
        return ""
    if "." in normalized:
        whole, frac = normalized.split(".")
        return f"${int(whole):,}.{frac}"
    return f"${int(normalized):,}"


def normalize_percent(value: str) -> str:
    cleaned = re.sub(r"[^\d.]", "", str(value or ""))
    if not cleaned:
        return ""
    number = float(cleaned)
    if number.is_integer():
        return str(int(number))
    return str(number).rstrip("0").rstrip(".")


def normalize_years(value: str) -> str:
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return digits


def checked_credit_warnings(captured: dict[str, str], prefix: str) -> list[str]:
    warnings: list[str] = []
    for key, state in captured.items():
        if not key.startswith(prefix):
            continue
        if state != "checked":
            continue
        warnings.append(key.split(":", 1)[1])
    return warnings


def first_name_from_deal_name(deal_name: str) -> str:
    return deal_name.split()[0] if deal_name.split() else deal_name


@dataclass
class MortgageSnapshotDisplayExpectations:
    """Expected values shown in the MS App presentation (from CRM save)."""

    deal_name: str
    applicant_first_name: str
    co_applicant_display_name: str
    property_address_contains: str

    introduction_script: str
    first_need: str
    first_client_response: str
    second_need: str
    second_client_response: str

    credit_score: str
    credit_rating: str
    tds_score: str
    credit_utilization: str
    primary_warning_flags: list[str] = field(default_factory=list)

    co_credit_score: str = ""
    co_credit_rating: str = ""
    co_tds_score: str = ""
    co_credit_utilization: str = ""
    co_warning_flags: list[str] = field(default_factory=list)

    current_balance: str = ""
    current_rate: str = ""
    years_to_pay: str = ""
    total_interest: str = ""
    total_cost: str = ""
    monthly_payment: str = ""

    option4_type: str = ""
    option4_loan: str = ""
    option4_payment: str = ""
    option4_savings: str = ""
    option4_points: list[str] = field(default_factory=list)

    option5_type: str = ""
    option5_loan: str = ""
    option5_payment: str = ""
    option5_savings: str = ""
    option5_points: list[str] = field(default_factory=list)

    min_value: str = ""
    max_value: str = ""
    value_used: str = ""
    less_all_mortgages: str = ""
    ltv: str = ""
    vfli_number: str = ""
    lead_email: str = ""

    final_prompt: str = ""
    final_point_one: str = ""
    final_point_two: str = ""
    final_point_three: str = ""


def build_display_expectations(
    *,
    deal_name: str,
    applicant_first_name: str,
    co_applicant_display_name: str,
    property_address_contains: str,
    captured: dict[str, str],
    data,
    lead_email: str = "",
) -> MortgageSnapshotDisplayExpectations:
    credit_score = captured.get("creditScore") or data.credit_score
    co_credit_score = captured.get("coApplicantCreditScore") or data.co_credit_score

    return MortgageSnapshotDisplayExpectations(
        deal_name=deal_name,
        applicant_first_name=applicant_first_name,
        co_applicant_display_name=co_applicant_display_name,
        property_address_contains=property_address_contains,
        vfli_number=captured.get("vfliNo") or data.vfli_number,
        lead_email=lead_email,
        introduction_script=captured.get("introScript") or data.introduction_script,
        first_need=captured.get("firstNeed") or data.first_need,
        first_client_response=captured.get("firstClientResponse") or data.ok_got_it,
        second_need=captured.get("secondNeed") or data.second_need,
        second_client_response=captured.get("secondClientResponse") or data.lets_get_to_work,
        credit_score=credit_score,
        credit_rating=credit_rating_for_score(credit_score),
        tds_score=captured.get("tdsScore") or data.tds_score,
        credit_utilization=captured.get("creditUtilization") or data.credit_utilization,
        primary_warning_flags=checked_credit_warnings(
            captured, "primaryCreditWarning:"
        ),
        co_credit_score=co_credit_score,
        co_credit_rating=credit_rating_for_score(co_credit_score),
        co_tds_score=captured.get("coApplicantTdsScore") or data.co_tds_score,
        co_credit_utilization=captured.get("coApplicantCreditUtilization")
        or data.co_credit_utilization,
        co_warning_flags=checked_credit_warnings(captured, "coCreditWarning:"),
        current_balance=captured.get("debtProfileCurrentTotalDebt") or data.current_balance,
        current_rate=captured.get("debtProfileAverageInterestRate") or data.current_rate,
        years_to_pay=captured.get("debtProfileAverageTimeToPayOff") or data.years_to_pay,
        total_interest=captured.get("debtProfileInterestPaidOverTime") or data.total_interest,
        total_cost=captured.get("debtProfileTrueCostOfDebt") or data.total_cost,
        monthly_payment=captured.get("debtProfileMinimumPaymentNeeded") or data.monthly_payment,
        option4_type=captured.get("mortgageOption4Type") or data.option4_type,
        option4_loan=captured.get("mortgageOption4LoanAmount") or data.option4_loan,
        option4_payment=captured.get("mortgageOption4MonthlyPayment") or data.option4_payment,
        option4_savings=captured.get("mortgageOption4MonthlySavings") or data.option4_savings,
        option4_points=[
            captured.get("mortgageOption4PointOne") or data.option4_point1,
            captured.get("mortgageOption4PointTwo") or data.option4_point2,
            captured.get("mortgageOption4PointThree") or data.option4_point3,
        ],
        option5_type=captured.get("mortgageOption5Type") or data.option5_type,
        option5_loan=captured.get("mortgageOption5LoanAmount") or data.option5_loan,
        option5_payment=captured.get("mortgageOption5MonthlyPayment") or data.option5_payment,
        option5_savings=captured.get("mortgageOption5MonthlySavings") or data.option5_savings,
        option5_points=[
            captured.get("mortgageOption5PointOne") or data.option5_point1,
            captured.get("mortgageOption5PointTwo") or data.option5_point2,
            captured.get("mortgageOption5PointThree") or data.option5_point3,
        ],
        min_value=captured.get("mortgageAppraisedMinimumValue") or data.min_value,
        max_value=captured.get("mortgageAppraisedMaximumValue") or data.max_value,
        value_used=captured.get("mortgageAppraisedValueUsed") or data.value_used,
        less_all_mortgages=captured.get("mortgageAppraisedLessAllMortgages")
        or data.less_all_mortgages,
        ltv=captured.get("mortgageAppraisedEstimatedLoanToValue") or data.ltv,
        final_prompt=captured.get("finalPrompt") or data.final_prompt,
        final_point_one=captured.get("finalClientSlidePointOne") or data.benefit_one,
        final_point_two=captured.get("finalClientSlidePointTwo") or data.benefit_two,
        final_point_three=captured.get("finalClientSlidePointThree") or data.benefit_three,
    )


def build_display_expectations_from_captured(
    *,
    deal_name: str,
    applicant_first_name: str,
    co_applicant_display_name: str,
    property_address_contains: str,
    captured: dict[str, str],
    lead_email: str = "",
) -> MortgageSnapshotDisplayExpectations:
    """Build MS App expectations from CRM persisted values only."""
    credit_score = captured.get("creditScore", "")
    co_credit_score = captured.get("coApplicantCreditScore", "")

    return MortgageSnapshotDisplayExpectations(
        deal_name=deal_name,
        applicant_first_name=applicant_first_name,
        co_applicant_display_name=co_applicant_display_name,
        property_address_contains=property_address_contains,
        vfli_number=captured.get("vfliNo", ""),
        lead_email=lead_email,
        introduction_script=captured.get("introScript", ""),
        first_need=captured.get("firstNeed", ""),
        first_client_response=captured.get("firstClientResponse", ""),
        second_need=captured.get("secondNeed", ""),
        second_client_response=captured.get("secondClientResponse", ""),
        credit_score=credit_score,
        credit_rating=credit_rating_for_score(credit_score),
        tds_score=captured.get("tdsScore", ""),
        credit_utilization=captured.get("creditUtilization", ""),
        primary_warning_flags=checked_credit_warnings(captured, "primaryCreditWarning:"),
        co_credit_score=co_credit_score,
        co_credit_rating=credit_rating_for_score(co_credit_score),
        co_tds_score=captured.get("coApplicantTdsScore", ""),
        co_credit_utilization=captured.get("coApplicantCreditUtilization", ""),
        co_warning_flags=checked_credit_warnings(captured, "coCreditWarning:"),
        current_balance=captured.get("debtProfileCurrentTotalDebt", ""),
        current_rate=captured.get("debtProfileAverageInterestRate", ""),
        years_to_pay=captured.get("debtProfileAverageTimeToPayOff", ""),
        total_interest=captured.get("debtProfileInterestPaidOverTime", ""),
        total_cost=captured.get("debtProfileTrueCostOfDebt", ""),
        monthly_payment=captured.get("debtProfileMinimumPaymentNeeded", ""),
        option4_type=captured.get("mortgageOption4Type", ""),
        option4_loan=captured.get("mortgageOption4LoanAmount", ""),
        option4_payment=captured.get("mortgageOption4MonthlyPayment", ""),
        option4_savings=captured.get("mortgageOption4MonthlySavings", ""),
        option4_points=[
            captured.get("mortgageOption4PointOne", ""),
            captured.get("mortgageOption4PointTwo", ""),
            captured.get("mortgageOption4PointThree", ""),
        ],
        option5_type=captured.get("mortgageOption5Type", ""),
        option5_loan=captured.get("mortgageOption5LoanAmount", ""),
        option5_payment=captured.get("mortgageOption5MonthlyPayment", ""),
        option5_savings=captured.get("mortgageOption5MonthlySavings", ""),
        option5_points=[
            captured.get("mortgageOption5PointOne", ""),
            captured.get("mortgageOption5PointTwo", ""),
            captured.get("mortgageOption5PointThree", ""),
        ],
        min_value=captured.get("mortgageAppraisedMinimumValue", ""),
        max_value=captured.get("mortgageAppraisedMaximumValue", ""),
        value_used=captured.get("mortgageAppraisedValueUsed", ""),
        less_all_mortgages=captured.get("mortgageAppraisedLessAllMortgages", ""),
        ltv=captured.get("mortgageAppraisedEstimatedLoanToValue", ""),
        final_prompt=captured.get("finalPrompt", ""),
        final_point_one=captured.get("finalClientSlidePointOne", ""),
        final_point_two=captured.get("finalClientSlidePointTwo", ""),
        final_point_three=captured.get("finalClientSlidePointThree", ""),
    )
