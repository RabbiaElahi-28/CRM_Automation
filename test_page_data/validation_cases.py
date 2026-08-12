"""Validation case definitions sourced from application schemas."""

from utils.negative_test_helpers import InvalidFieldCase
from test_page_data import negative_messages as msg

CHAR_151 = "x" * 151
CHAR_201 = "x" * 201
CHAR_276 = "x" * 276


# ---------------------------------------------------------------------------
# Create Lead (updateLeadSchema + async phone)
# ---------------------------------------------------------------------------

CREATE_LEAD_EMPTY = [
    msg.CREATE_LEAD_EMAIL_REQUIRED,
    msg.CREATE_LEAD_BIRTHDAY_REQUIRED,
]

CREATE_LEAD_INVALID = [
    InvalidFieldCase("enter_email", "abc", msg.CREATE_LEAD_INVALID_EMAIL),
    InvalidFieldCase("enter_postal_code", "A1A1A1", msg.CREATE_LEAD_POSTAL_INVALID),
    InvalidFieldCase("enter_credit_score", "1000", msg.CREATE_LEAD_CREDIT_SCORE_RANGE),
    InvalidFieldCase("enter_mortgage_rate", "150", msg.CREATE_LEAD_MORTGAGE_RATE_RANGE),
    InvalidFieldCase("enter_phone", "0000000000", msg.CREATE_LEAD_PHONE_INVALID),
]

# ---------------------------------------------------------------------------
# Lead Edit (LeadOwnerForm + MortgageInfoForm)
# ---------------------------------------------------------------------------

LEAD_EDIT_EMPTY = []  # No required fields on empty contact clear

LEAD_EDIT_INVALID = [
    InvalidFieldCase("email", "abc", msg.CREATE_LEAD_INVALID_EMAIL),
    InvalidFieldCase("phone", "0000000000", msg.CREATE_LEAD_PHONE_INVALID),
    InvalidFieldCase("postal_code", "A1A1A1", msg.CREATE_LEAD_POSTAL_INVALID),
    InvalidFieldCase("credit_score", "1000", msg.CREATE_LEAD_CREDIT_SCORE_RANGE),
    InvalidFieldCase("mortgage_rate", "150", msg.CREATE_LEAD_MORTGAGE_RATE_RANGE),
]

# ---------------------------------------------------------------------------
# Co-Borrower (coBorrowerSchema)
# ---------------------------------------------------------------------------

COBORROWER_EMPTY = [
    msg.COBORROWER_FIRST_NAME,
    msg.COBORROWER_LAST_NAME,
    msg.COBORROWER_EMAIL,
    msg.COBORROWER_PHONE,
    msg.COBORROWER_DOB,
    msg.COBORROWER_EMPLOYER,
    msg.COBORROWER_INCOME,
]

COBORROWER_INVALID = [
    InvalidFieldCase("email", "abc", msg.COBORROWER_EMAIL_INVALID),
    InvalidFieldCase("first_name", "A", msg.COBORROWER_FIRST_NAME),
    InvalidFieldCase("last_name", "A", msg.COBORROWER_LAST_NAME),
    InvalidFieldCase("phone", "123456", msg.COBORROWER_PHONE),
    InvalidFieldCase("employer", "A", msg.COBORROWER_EMPLOYER),
]

# ---------------------------------------------------------------------------
# Mortgage Snapshot (mortgageSnapshotSchema)
# ---------------------------------------------------------------------------

SNAPSHOT_EMPTY = [
    msg.SNAPSHOT_VFLI_REQUIRED,
    msg.SNAPSHOT_CREDIT_SCORE_REQUIRED,
    msg.SNAPSHOT_TDS_REQUIRED,
    msg.SNAPSHOT_CREDIT_UTIL_REQUIRED,
    msg.SNAPSHOT_CO_CREDIT_SCORE_REQUIRED,
    msg.SNAPSHOT_CO_TDS_REQUIRED,
    msg.SNAPSHOT_CO_CREDIT_UTIL_REQUIRED,
    msg.SNAPSHOT_CURRENT_DEBT_REQUIRED,
    msg.SNAPSHOT_AVG_INTEREST_REQUIRED,
    msg.SNAPSHOT_AVG_TIME_REQUIRED,
    msg.SNAPSHOT_INTEREST_PAID_REQUIRED,
    msg.SNAPSHOT_TRUE_COST_REQUIRED,
    msg.SNAPSHOT_MIN_PAYMENT_REQUIRED,
    msg.SNAPSHOT_OPT1_LOAN_REQUIRED,
    msg.SNAPSHOT_OPT1_PAYMENT_REQUIRED,
    msg.SNAPSHOT_OPT1_SAVINGS_REQUIRED,
    msg.SNAPSHOT_OPT2_LOAN_REQUIRED,
    msg.SNAPSHOT_OPT2_PAYMENT_REQUIRED,
    msg.SNAPSHOT_OPT2_SAVINGS_REQUIRED,
    msg.SNAPSHOT_MIN_VALUE_REQUIRED,
    msg.SNAPSHOT_MAX_VALUE_REQUIRED,
    msg.SNAPSHOT_VALUE_USED_REQUIRED,
    msg.SNAPSHOT_LESS_MORTGAGES_REQUIRED,
    msg.SNAPSHOT_EST_LTV_REQUIRED,
]

SNAPSHOT_INVALID = [
    InvalidFieldCase("vfliNo", "abc", msg.SNAPSHOT_VFLI_INVALID),
    InvalidFieldCase("vfliNo", "123", msg.SNAPSHOT_VFLI_LENGTH),
    InvalidFieldCase("introScript", CHAR_151, msg.SNAPSHOT_MAX_150),
    InvalidFieldCase("creditScore", "abc", msg.SNAPSHOT_CREDIT_SCORE_INVALID),
    InvalidFieldCase("creditScore", "100", msg.SNAPSHOT_CREDIT_SCORE_RANGE),
    InvalidFieldCase("tdsScore", "abc", msg.SNAPSHOT_TDS_INVALID),
    InvalidFieldCase("tdsScore", "101", msg.SNAPSHOT_TDS_RANGE),
    InvalidFieldCase("creditUtilization", "abc", msg.SNAPSHOT_CREDIT_UTIL_INVALID),
    InvalidFieldCase("creditUtilization", "101", msg.SNAPSHOT_CREDIT_UTIL_RANGE),
    InvalidFieldCase("coApplicantCreditScore", "abc", msg.SNAPSHOT_CO_CREDIT_SCORE_INVALID),
    InvalidFieldCase("coApplicantCreditScore", "100", msg.SNAPSHOT_CO_CREDIT_SCORE_RANGE),
    InvalidFieldCase("coApplicantTdsScore", "abc", msg.SNAPSHOT_CO_TDS_INVALID),
    InvalidFieldCase("coApplicantTdsScore", "101", msg.SNAPSHOT_CO_TDS_RANGE),
    InvalidFieldCase("coApplicantCreditUtilization", "abc", msg.SNAPSHOT_CO_CREDIT_UTIL_INVALID),
    InvalidFieldCase("coApplicantCreditUtilization", "101", msg.SNAPSHOT_CO_CREDIT_UTIL_RANGE),
    InvalidFieldCase("debtProfileCurrentTotalDebt", "abc", msg.SNAPSHOT_CURRENT_DEBT_INVALID),
    InvalidFieldCase("debtProfileCurrentTotalDebt", "-1", msg.SNAPSHOT_CURRENT_DEBT_MIN),
    InvalidFieldCase("debtProfileAverageInterestRate", "abc", msg.SNAPSHOT_AVG_INTEREST_INVALID),
    InvalidFieldCase("debtProfileAverageInterestRate", "101", msg.SNAPSHOT_AVG_INTEREST_RANGE),
    InvalidFieldCase("debtProfileAverageTimeToPayOff", "abc", msg.SNAPSHOT_AVG_TIME_INVALID),
    InvalidFieldCase("debtProfileAverageTimeToPayOff", "51", msg.SNAPSHOT_AVG_TIME_RANGE),
    InvalidFieldCase("debtProfileInterestPaidOverTime", "abc", msg.SNAPSHOT_INTEREST_PAID_INVALID),
    InvalidFieldCase("debtProfileInterestPaidOverTime", "-1", msg.SNAPSHOT_INTEREST_PAID_MIN),
    InvalidFieldCase("debtProfileTrueCostOfDebt", "abc", msg.SNAPSHOT_TRUE_COST_INVALID),
    InvalidFieldCase("debtProfileTrueCostOfDebt", "-1", msg.SNAPSHOT_TRUE_COST_MIN),
    InvalidFieldCase("debtProfileMinimumPaymentNeeded", "abc", msg.SNAPSHOT_MIN_PAYMENT_INVALID),
    InvalidFieldCase("debtProfileMinimumPaymentNeeded", "-1", msg.SNAPSHOT_MIN_PAYMENT_MIN),
    InvalidFieldCase("mortgageOption4LoanAmount", "abc", msg.SNAPSHOT_OPT1_LOAN_INVALID),
    InvalidFieldCase("mortgageOption4LoanAmount", "-1", msg.SNAPSHOT_OPT1_LOAN_MIN),
    InvalidFieldCase("mortgageOption4MonthlyPayment", "abc", msg.SNAPSHOT_OPT1_PAYMENT_INVALID),
    InvalidFieldCase("mortgageOption4MonthlyPayment", "-1", msg.SNAPSHOT_OPT1_PAYMENT_MIN),
    InvalidFieldCase("mortgageOption4MonthlySavings", "abc", msg.SNAPSHOT_OPT1_SAVINGS_INVALID),
    InvalidFieldCase("mortgageOption4MonthlySavings", "-1", msg.SNAPSHOT_OPT1_SAVINGS_MIN),
    InvalidFieldCase("mortgageOption5LoanAmount", "abc", msg.SNAPSHOT_OPT2_LOAN_INVALID),
    InvalidFieldCase("mortgageOption5LoanAmount", "-1", msg.SNAPSHOT_OPT2_LOAN_MIN),
    InvalidFieldCase("mortgageOption5MonthlyPayment", "abc", msg.SNAPSHOT_OPT2_PAYMENT_INVALID),
    InvalidFieldCase("mortgageOption5MonthlyPayment", "-1", msg.SNAPSHOT_OPT2_PAYMENT_MIN),
    InvalidFieldCase("mortgageOption5MonthlySavings", "abc", msg.SNAPSHOT_OPT2_SAVINGS_INVALID),
    InvalidFieldCase("mortgageOption5MonthlySavings", "-1", msg.SNAPSHOT_OPT2_SAVINGS_MIN),
    InvalidFieldCase("mortgageAppraisedMinimumValue", "abc", msg.SNAPSHOT_MIN_VALUE_INVALID),
    InvalidFieldCase("mortgageAppraisedMinimumValue", "-1", msg.SNAPSHOT_MIN_VALUE_MIN),
    InvalidFieldCase("mortgageAppraisedMaximumValue", "abc", msg.SNAPSHOT_MAX_VALUE_INVALID),
    InvalidFieldCase("mortgageAppraisedMaximumValue", "-1", msg.SNAPSHOT_MAX_VALUE_MIN),
    InvalidFieldCase("mortgageAppraisedValueUsed", "abc", msg.SNAPSHOT_VALUE_USED_INVALID),
    InvalidFieldCase("mortgageAppraisedValueUsed", "-1", msg.SNAPSHOT_VALUE_USED_MIN),
    InvalidFieldCase("mortgageAppraisedLessAllMortgages", "abc", msg.SNAPSHOT_LESS_MORTGAGES_INVALID),
    InvalidFieldCase("mortgageAppraisedLessAllMortgages", "-1", msg.SNAPSHOT_LESS_MORTGAGES_MIN),
    InvalidFieldCase("mortgageAppraisedEstimatedLoanToValue", "abc", msg.SNAPSHOT_EST_LTV_INVALID),
    InvalidFieldCase("mortgageAppraisedEstimatedLoanToValue", "101", msg.SNAPSHOT_EST_LTV_RANGE),
]

# ---------------------------------------------------------------------------
# Appraisal Order (appraisalOrderSchema)
# ---------------------------------------------------------------------------

APPRAISAL_EMPTY_INITIAL = [
    msg.APPRAISAL_ORDERED_REQUIRED,
    msg.APPRAISAL_AVM_REQUIRED,
]

APPRAISAL_EMPTY_YES_NO_AVM = [msg.APPRAISAL_AVM_REQUIRED]

APPRAISAL_EMPTY_YES = [
    msg.APPRAISAL_COMPANY_REQUIRED,
    msg.APPRAISAL_LOCATION_REQUIRED,
    msg.APPRAISAL_LTV_REQUIRED,
    msg.APPRAISAL_DATE_ORDER_REQUIRED,
    msg.APPRAISAL_APPOINTMENT_REQUIRED,
    msg.APPRAISAL_CITY_REQUIRED,
]

APPRAISAL_EMPTY_NO = [msg.APPRAISAL_REASON_REQUIRED]

APPRAISAL_INVALID = [
    InvalidFieldCase("ltv", "150", msg.APPRAISAL_LTV_MAX),
    InvalidFieldCase("ltv", "0", msg.APPRAISAL_LTV_MIN),
]

# ---------------------------------------------------------------------------
# Submitted (submittedSchema)
# ---------------------------------------------------------------------------

SUBMITTED_EMPTY = [
    msg.SUBMITTED_LOAN_AMOUNT_REQUIRED,
    msg.SUBMITTED_LTV_REQUIRED,
    msg.SUBMITTED_TERM_REQUIRED,
    msg.SUBMITTED_RATE_REQUIRED,
]

SUBMITTED_INVALID = [
    InvalidFieldCase("requestedLTV", "150", msg.SUBMITTED_LTV_MAX),
    InvalidFieldCase("requestedLTV", "0", msg.SUBMITTED_LTV_REQUIRED),
    InvalidFieldCase("mortgageLoanAmount", "0", msg.SUBMITTED_LOAN_AMOUNT_REQUIRED),
    InvalidFieldCase("termRequested", "0", msg.SUBMITTED_TERM_REQUIRED),
    InvalidFieldCase("termRequested", "101", msg.SUBMITTED_TERM_MAX),
    InvalidFieldCase("rateRequested", "0", msg.SUBMITTED_RATE_REQUIRED),
    InvalidFieldCase("rateRequested", "101", msg.SUBMITTED_RATE_MAX),
    InvalidFieldCase("submittedRejectedReason", CHAR_276, msg.SUBMITTED_REASON_MAX),
]

# ---------------------------------------------------------------------------
# Notes (AddNoteForm.tsx)
# ---------------------------------------------------------------------------

NOTE_EMPTY = [
    msg.NOTE_EMPTY,
]

# ---------------------------------------------------------------------------
# Approved (approvedSchema — tab 1 save)
# ---------------------------------------------------------------------------

APPROVED_EMPTY = [
    msg.APPROVED_FIELD_REQUIRED,
    msg.APPROVED_CREDIT_SCORE_RANGE,
]

APPROVED_INVALID = [
    InvalidFieldCase("creditScore", "100", msg.APPROVED_CREDIT_SCORE_RANGE),
    InvalidFieldCase("creditScore", "1000", msg.APPROVED_CREDIT_SCORE_RANGE),
    InvalidFieldCase("approvedLtv", "101", msg.APPROVED_LTV_MAX),
    InvalidFieldCase("approvedTerm", "101", msg.APPROVED_TERM_MAX),
    InvalidFieldCase("approvedRate", "101", msg.APPROVED_RATE_MAX),
    InvalidFieldCase("tdsRatio", "101", msg.APPROVED_TDS_MAX),
    InvalidFieldCase("averageInterestRate", "101", msg.APPROVED_AVG_INTEREST_MAX),
    InvalidFieldCase("coApplicantCreditScore", "100", msg.APPROVED_CO_CREDIT_SCORE_RANGE),
    InvalidFieldCase("coApplicantCreditUtilization", "101", msg.APPROVED_CO_UTIL_MAX),
    InvalidFieldCase("currentMortgageDebtPayment", "-1", msg.APPROVED_FIELD_REQUIRED),
]

# ---------------------------------------------------------------------------
# Signed (signedFormSchema — conditional paths)
# ---------------------------------------------------------------------------

SIGNED_EMPTY_NOT_SIGNED = [msg.SIGNED_NOT_SIGNED_REASON]

# Signed details are prefilled from Approved; empty save validates Final Product Yes sections.
SIGNED_EMPTY_YES_FINAL = [
    msg.SIGNED_SIGNED_DATE_REQUIRED,
    msg.SIGNED_DATE_SIGNS_BACK_REQUIRED,
    msg.SIGNED_CLOSING_EMAIL_REQUIRED,
    msg.SIGNED_HOME_APPRAISAL_REQUIRED,
    msg.SIGNED_CREDIT_CARD_STATEMENT_REQUIRED,
    msg.SIGNED_VALID_PHOTO_ID_REQUIRED,
    msg.SIGNED_CONDITIONED_DOCUMENTS_REQUIRED,
    msg.SIGNED_SECONDARY_ID_REQUIRED,
    msg.SIGNED_RETAINER_FEES_REQUIRED,
    msg.SIGNED_HOME_INSPECTION_REQUIRED,
    msg.SIGNED_OUTSTANDING_CONDITION_REQUIRED,
    msg.SIGNED_DATE_INSTRUCTED_LENDER_LAWYER_REQUIRED,
    msg.SIGNED_ILR_MEETING_REQUIRED,
    msg.SIGNED_DATE_INSTRUCTED_BORROWER_LAWYER_REQUIRED,
    msg.SIGNED_ANTICIPATED_CLOSING_REQUIRED,
    msg.SIGNED_LENDER_BPS_REQUIRED,
    msg.SIGNED_APPRAISAL_REBATE_REQUIRED,
    msg.SIGNED_LAWYER_FEE_REQUIRED,
    msg.SIGNED_TRUST_LEDGER_REVIEWED_REQUIRED,
]

SIGNED_INVALID = [
    InvalidFieldCase("approvedLTV", "150", msg.SIGNED_APPROVED_LTV_RANGE),
    InvalidFieldCase("approvedTerm", "150", msg.SIGNED_APPROVED_TERM_RANGE),
    InvalidFieldCase("approvedRate", "150", msg.SIGNED_APPROVED_RATE_RANGE),
    InvalidFieldCase("outstandingConditions", "too short", msg.SIGNED_OUTSTANDING_MIN),
    InvalidFieldCase("outstandingConditions", CHAR_201, msg.SIGNED_OUTSTANDING_MAX),
]
