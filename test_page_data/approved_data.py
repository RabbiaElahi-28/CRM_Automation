from dataclasses import dataclass, field

from faker import Faker

from test_page_data.random_gen_data import RandomGenerator as RG
from test_page_data.submitted_data import SubmittedOptionData

fake = Faker("en_CA")

MORTGAGE_TYPES = [
    "Home Equity Loan",
    "HELOC",
    "Refinance",
    "Purchase",
    "Second Position",
    "Third Position",
]


@dataclass
class ApprovedMortgageOptionPrefill:
    """
    Expected Your Mortgage Option values prefilled from the Submitted stage
    approved option (the option where approved=yes).

    Frontend mapping (transformFromSubmittedAndDlo):
      approvedLoanAmount  <- submitted.approvedLoanAmount
      mortgageTypeApproved <- submitted.mortgageType
      approvedLtv         <- submitted.approvedLtv
      approvedTerm        <- submitted.term
      approvedRate        <- submitted.approvedRate
    """

    approved_loan_amount: str
    mortgage_type: str
    approved_ltv: str
    approved_term: str
    approved_rate: str

    @classmethod
    def from_submitted_option(cls, option: SubmittedOptionData):
        return cls(
            approved_loan_amount=option.mortgage_loan_amount,
            mortgage_type=option.mortgage_type,
            approved_ltv=option.requested_ltv,
            approved_term=option.term_requested,
            approved_rate=option.rate_requested,
        )


@dataclass
class ApprovedSnapshotPrefill:
    """Expected Approved form values verified against Profile + Mortgage Snapshot."""

    name: str = ""
    credit_score: str = ""
    tds_ratio: str = ""
    co_applicant_name: str = ""
    co_applicant_credit_score: str = ""
    co_applicant_credit_utilization: str = ""
    average_interest_rate: str = ""
    min_monthly_payments: str = ""
    time_to_pay: str = ""
    total_interest_paid: str = ""
    applicants_needs_one: str = ""
    applicants_needs_two: str = ""
    applicants_needs_three: str = ""
    applicants_goals: str = ""
    new_option_one: str = ""
    why_this_option_works: str = ""
    new_option_two: str = ""
    why_this_option_works_best: str = ""


APPROVED_APPLICANTS_PREFILL = {
    "applicants_needs_one": "Leverage the equity to refinance credit card debt",
    "applicants_needs_two": "Complete renovations, improve property",
    "applicants_needs_three": "Seek Suitable employment, track income for renewal",
    "applicants_goals": (
        "Use improved credit score, income and property improvements to obtain a new mortgage"
    ),
}


@dataclass
class ApprovedFormData:
    name: str = field(default_factory=RG.full_name)
    credit_score: str = field(default_factory=RG.credit_score)
    tds_ratio: str = field(default_factory=RG.tds_score)
    credit_notes: str = field(default_factory=lambda: fake.sentence(nb_words=10))
    current_mortgage_debt_payment: str = field(default_factory=RG.monthly_payment)
    average_interest_rate: str = field(default_factory=RG.interest_rate)
    min_monthly_payments: str = field(default_factory=RG.monthly_payment)
    total_yearly_payment: str = field(default_factory=RG.annual_income)
    time_to_pay: str = field(default_factory=RG.mortgage_years)
    total_interest_paid: str = field(default_factory=RG.loan_amount)
    total_cost_of_debt: str = field(default_factory=RG.loan_amount)
    applicants_needs_one: str = field(
        default_factory=lambda: fake.sentence(nb_words=6)
    )
    applicants_needs_two: str = field(
        default_factory=lambda: fake.sentence(nb_words=6)
    )
    applicants_needs_three: str = field(
        default_factory=lambda: fake.sentence(nb_words=6)
    )
    applicants_goals: str = field(default_factory=lambda: fake.sentence(nb_words=8))
    plan_year_one_action_one: str = field(
        default_factory=lambda: fake.sentence(nb_words=5)
    )
    plan_year_one_action_two: str = field(
        default_factory=lambda: fake.sentence(nb_words=5)
    )
    plan_year_one_goals: str = field(
        default_factory=lambda: fake.sentence(nb_words=6)
    )
    plan_year_two_action_one: str = field(
        default_factory=lambda: fake.sentence(nb_words=5)
    )
    plan_year_two_action_two: str = field(
        default_factory=lambda: fake.sentence(nb_words=5)
    )
    plan_year_two_goals: str = field(
        default_factory=lambda: fake.sentence(nb_words=6)
    )
    plan_year_three_action_one: str = field(
        default_factory=lambda: fake.sentence(nb_words=5)
    )
    plan_year_three_action_two: str = field(
        default_factory=lambda: fake.sentence(nb_words=5)
    )
    plan_year_three_goals: str = field(
        default_factory=lambda: fake.sentence(nb_words=6)
    )
    new_option_one: str = field(default_factory=lambda: fake.sentence(nb_words=6))
    why_this_option_works: str = field(
        default_factory=lambda: fake.sentence(nb_words=8)
    )
    new_option_two: str = field(default_factory=lambda: fake.sentence(nb_words=6))
    why_this_option_works_best: str = field(
        default_factory=lambda: fake.sentence(nb_words=8)
    )
    monthly_mortgage_payment: str = field(default_factory=RG.monthly_payment)
    new_solution_payment: str = field(default_factory=RG.monthly_payment)
    estimated_monthly_saving: str = field(default_factory=RG.monthly_savings)
    current_total_debt: str = field(default_factory=RG.balance_owing)
    new_debt_payments: str = field(default_factory=RG.monthly_payment)
    yearly_savings_estimate: str = field(default_factory=RG.monthly_savings)
    combined_payments: str = field(default_factory=RG.monthly_payment)
    new_monthly_payments: str = field(default_factory=RG.monthly_payment)
    
    appraised_value: int = field(default_factory=lambda: fake.random_int(700000, 1200000))
    total_mortgages: int = field(default_factory=lambda: fake.random_int(50000, 600000))
    saving_note_section: str = field(default_factory=lambda: fake.sentence(nb_words=10))


@dataclass
class ApprovedCompletedData:
    month: str
    year: str
    day: str

    @classmethod
    def random(cls):
        month, year, day = RG.calendar_date_parts()
        return cls(month=month, year=str(year), day=str(day))


@dataclass
class ApprovedData:
    form: ApprovedFormData = field(default_factory=ApprovedFormData)
    approved_completed: ApprovedCompletedData = field(
        default_factory=ApprovedCompletedData.random
    )
