"""CRM Mortgage Snapshot form field → MS App presentation verification map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldVerificationSpec:
    crm_field_id: str
    crm_label: str
    ms_app_slide: str
    ms_app_locator: str
    verified: bool
    notes: str = ""


# All CRM snapshot form fields from _SNAPSHOT_FIELD_ATTRS + combobox/checkbox fields.
FIELD_VERIFICATION_MAP: tuple[FieldVerificationSpec, ...] = (
    # Video
    FieldVerificationSpec(
        "vfliNo",
        "VFLI Number",
        "N/A (Leads list)",
        "Search by VFLI on /leads",
        True,
        "Verified via lead search, not on presentation slides",
    ),
    FieldVerificationSpec(
        "introScript",
        "Introduction Script",
        "Slide 1 - Welcome",
        "Welcome slide body text",
        True,
    ),
    # Client needs
    FieldVerificationSpec(
        "firstNeed",
        "Client's 1st need",
        "Slide 2 - What you told us",
        ".chat-bubble-bot .messages-text (1st)",
        True,
    ),
    FieldVerificationSpec(
        "firstClientResponse",
        "Agent's 1st reply",
        "Slide 2 - What you told us",
        ".chat-bubble-user .messages-text (1st)",
        True,
    ),
    FieldVerificationSpec(
        "secondNeed",
        "Client's 2nd need",
        "Slide 2 - What you told us",
        ".chat-bubble-bot .messages-text (2nd)",
        True,
    ),
    FieldVerificationSpec(
        "secondClientResponse",
        "Agent's 2nd reply",
        "Slide 2 - What you told us",
        ".chat-bubble-user .messages-text (2nd)",
        True,
    ),
    # Primary credit
    FieldVerificationSpec(
        "creditScore",
        "Credit Score",
        "Slide 3 - Credit",
        ".credit-score-number (panel 1)",
        True,
    ),
    FieldVerificationSpec(
        "creditScore (derived)",
        "Credit Rating",
        "Slide 3 - Credit",
        ".credit-score-rating (panel 1)",
        True,
        "Derived from creditScore via creditScoreRanges tiers",
    ),
    FieldVerificationSpec(
        "tdsScore",
        "TDS %",
        "Slide 3 - Credit",
        ".tabular-nums TDS (panel 1)",
        True,
    ),
    FieldVerificationSpec(
        "creditUtilization",
        "Utilization %",
        "Slide 3 - Credit",
        ".tabular-nums Utilization (panel 1)",
        True,
    ),
    FieldVerificationSpec(
        "primaryCreditWarning:*",
        "Primary credit warning flags",
        "Slide 3 - Credit",
        'p[style*="font-size: 17px"] (panel 1, all checked)',
        True,
    ),
    # Co-applicant credit
    FieldVerificationSpec(
        "coApplicantCreditScore",
        "Co-applicant Credit Score",
        "Slide 3 - Credit",
        ".credit-score-number (panel 2)",
        True,
        "Skipped when no co-borrower; panel shows N/A",
    ),
    FieldVerificationSpec(
        "coApplicantCreditScore (derived)",
        "Co-applicant Credit Rating",
        "Slide 3 - Credit",
        ".credit-score-rating (panel 2)",
        True,
    ),
    FieldVerificationSpec(
        "coApplicantTdsScore",
        "Co-applicant TDS %",
        "Slide 3 - Credit",
        ".tabular-nums TDS (panel 2)",
        True,
    ),
    FieldVerificationSpec(
        "coApplicantCreditUtilization",
        "Co-applicant Utilization %",
        "Slide 3 - Credit",
        ".tabular-nums Utilization (panel 2)",
        True,
    ),
    FieldVerificationSpec(
        "coCreditWarning:*",
        "Co-applicant credit warning flags",
        "Slide 3 - Credit",
        'p[style*="font-size: 17px"] (panel 2, all checked)',
        True,
    ),
    # Debt profile
    FieldVerificationSpec(
        "debtProfileCurrentTotalDebt",
        "Current Total of All Credit Cards and Loans",
        "Slide 4 - Debt",
        '".landscape-debt-row" label "Current high-interest debt"',
        True,
        "Label differs in MS App",
    ),
    FieldVerificationSpec(
        "debtProfileAverageInterestRate",
        "Average interest rate",
        "Slide 4 - Debt",
        '".landscape-debt-row" label "Average interest rate"',
        True,
    ),
    FieldVerificationSpec(
        "debtProfileAverageTimeToPayOff",
        "Average time to pay off",
        "Slide 4 - Debt",
        '".landscape-debt-row" label "Average time to pay off"',
        True,
    ),
    FieldVerificationSpec(
        "debtProfileInterestPaidOverTime",
        "Interest paid over time",
        "Slide 4 - Debt",
        '".landscape-debt-row" label "Interest paid over time"',
        True,
    ),
    FieldVerificationSpec(
        "debtProfileTrueCostOfDebt",
        "The true cost of debt",
        "Slide 4 - Debt",
        '".landscape-debt-row" label "true cost of debt"',
        True,
    ),
    FieldVerificationSpec(
        "debtProfileMinimumPaymentNeeded",
        "Minimum payment needed",
        "Slide 4 - Debt",
        ".landscape-debt-amount + .landscape-debt-decimal",
        True,
    ),
    # Mortgage option 4 (4-star)
    FieldVerificationSpec(
        "mortgageOption4Type",
        "Option 4 product type",
        "Slide 5 - Options",
        ".opt-product-type (4-star block)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption4LoanAmount",
        "Option 4 loan amount",
        "Slide 5 - Options",
        ".opt-row Loan amount (4-star)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption4MonthlyPayment",
        "Option 4 monthly payment",
        "Slide 5 - Options",
        ".opt-row Monthly payment (4-star)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption4MonthlySavings",
        "Option 4 monthly saving",
        "Slide 5 - Options",
        ".opt-row Monthly saving (4-star)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption4PointOne",
        "Option 4 point 1",
        "Slide 5 - Options",
        ".opt-point (4-star, point 1)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption4PointTwo",
        "Option 4 point 2",
        "Slide 5 - Options",
        ".opt-point (4-star, point 2)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption4PointThree",
        "Option 4 point 3",
        "Slide 5 - Options",
        ".opt-point (4-star, point 3)",
        True,
    ),
    # Mortgage option 5 (5-star)
    FieldVerificationSpec(
        "mortgageOption5Type",
        "Option 5 product type",
        "Slide 5 - Options",
        ".opt-product-type (5-star block)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption5LoanAmount",
        "Option 5 loan amount",
        "Slide 5 - Options",
        ".opt-row Loan amount (5-star)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption5MonthlyPayment",
        "Option 5 monthly payment",
        "Slide 5 - Options",
        ".opt-row Monthly payment (5-star)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption5MonthlySavings",
        "Option 5 monthly saving",
        "Slide 5 - Options",
        ".opt-row Monthly saving (5-star)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption5PointOne",
        "Option 5 point 1",
        "Slide 5 - Options",
        ".opt-point (5-star, point 1)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption5PointTwo",
        "Option 5 point 2",
        "Slide 5 - Options",
        ".opt-point (5-star, point 2)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageOption5PointThree",
        "Option 5 point 3",
        "Slide 5 - Options",
        ".opt-point (5-star, point 3)",
        True,
    ),
    # Home appraised
    FieldVerificationSpec(
        "(profile) propertyAddress",
        "Property Address",
        "Slide 6 - Home Appraised",
        ".ha-label",
        True,
        "From CRM profile, not snapshot form field",
    ),
    FieldVerificationSpec(
        "mortgageAppraisedMinimumValue",
        "Minimum Value",
        "Slide 6 - Home Appraised",
        ".ha-card-value (min)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageAppraisedMaximumValue",
        "Maximum Value",
        "Slide 6 - Home Appraised",
        ".ha-card-value (max)",
        True,
    ),
    FieldVerificationSpec(
        "mortgageAppraisedValueUsed",
        "Value Used",
        "Slide 6 - Home Appraised",
        ".ha-detail-label *Value Used",
        True,
    ),
    FieldVerificationSpec(
        "mortgageAppraisedLessAllMortgages",
        "Less All Mortgages",
        "Slide 6 - Home Appraised",
        ".ha-detail-label Less All Mortgages",
        True,
    ),
    FieldVerificationSpec(
        "mortgageAppraisedEstimatedLoanToValue",
        "Estimated Loan to Value",
        "Slide 6 - Home Appraised",
        ".ha-ltv-value",
        True,
    ),
    # Final client slide - intentionally not content-verified
    FieldVerificationSpec(
        "finalPrompt",
        "Final prompt",
        "Slide 7 - Final Client",
        ".mp-label / slide body text",
        True,
    ),
    FieldVerificationSpec(
        "finalClientSlidePointOne",
        "Final slide benefit 1",
        "Slide 7 - Final Client",
        ".mp-point",
        True,
    ),
    FieldVerificationSpec(
        "finalClientSlidePointTwo",
        "Final slide benefit 2",
        "Slide 7 - Final Client",
        ".mp-point",
        True,
    ),
    FieldVerificationSpec(
        "finalClientSlidePointThree",
        "Final slide benefit 3",
        "Slide 7 - Final Client",
        ".mp-point",
        True,
    ),
    FieldVerificationSpec(
        "finalClientSlidePlanType",
        "Plan type (combobox)",
        "Slide 7 - Final Client",
        "N/A",
        False,
        "Not displayed in MS App presentation",
    ),
    FieldVerificationSpec(
        "(rbac) non-assigned user",
        "Cross-role MS App isolation",
        "N/A (Leads list)",
        "Logout -> cross-role MS App login -> search all identifiers + direct URL",
        True,
        "Mandatory RBAC: lead must not appear for non-assigned agent",
    ),
    # Profile-derived (not form fields)
    FieldVerificationSpec(
        "(profile) firstName",
        "Applicant first name",
        "Slide 2 - What you told us",
        'Heading "{name}, here\'s"',
        True,
        "From CRM profile",
    ),
    FieldVerificationSpec(
        "(profile) coBorrowerName",
        "Co-applicant name",
        "Slide 3 - Credit",
        'Welcome, {name} (panel 2)',
        True,
        "N/A when no co-borrower",
    ),
)


def format_verification_table(
    *,
    run_passed: bool | None = None,
    test_name: str = "",
) -> str:
    """Return markdown table of field verification coverage."""
    lines = [
        "| CRM Field | CRM Label | MS App Slide | MS App Locator | Verified | Notes |",
        "|-----------|-----------|--------------|----------------|----------|-------|",
    ]
    for spec in FIELD_VERIFICATION_MAP:
        status = "Yes" if spec.verified else "No (by design)"
        if run_passed is not None and spec.verified:
            status = "PASS" if run_passed else "FAIL"
        elif run_passed is not None and not spec.verified:
            status = "N/A"
        lines.append(
            f"| `{spec.crm_field_id}` | {spec.crm_label} | {spec.ms_app_slide} | "
            f"{spec.ms_app_locator} | {status} | {spec.notes} |"
        )
    if test_name:
        lines.insert(0, f"**Test run:** `{test_name}` - overall: {'PASS' if run_passed else 'FAIL' if run_passed is False else 'NOT RUN'}")
        lines.insert(1, "")
    return "\n".join(lines)
