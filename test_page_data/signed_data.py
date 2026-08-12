from dataclasses import dataclass, field

from faker import Faker

from test_page_data.approved_data import ApprovedMortgageOptionPrefill
from test_page_data.random_gen_data import RandomGenerator as RG
from test_page_data.submitted_data import SubmittedOptionData

fake = Faker("en_CA")


@dataclass
class SignedPrefillData:
    """
    Expected Signed form prefills from Approved + Submitted approved option.

    Approved form fields map to SignedDetailsFields; lenderName comes from
    Submitted approved option only (read-only on Signed form).
    """

    loan_amount: str
    mortgage_type: str
    approved_ltv: str
    approved_term: str
    approved_rate: str
    lender_name: str = ""

    @classmethod
    def from_submitted_option(cls, option: SubmittedOptionData):
        approved = ApprovedMortgageOptionPrefill.from_submitted_option(option)
        return cls(
            loan_amount=approved.approved_loan_amount,
            mortgage_type=approved.mortgage_type,
            approved_ltv=approved.approved_ltv,
            approved_term=approved.approved_term,
            approved_rate=approved.approved_rate,
        )


@dataclass
class SignedNoFlowData:
    not_signed_reason: str = field(
        default_factory=lambda: fake.sentence(nb_words=8)
    )


@dataclass
class SignedFinalProductYesData:
    month: str = ""
    year: str = ""
    day: str = ""
    important_notes: str = field(
        default_factory=lambda: fake.sentence(nb_words=10)
    )
    outstanding_conditions_details: str = field(
        default_factory=lambda: fake.sentence(nb_words=12)[:200]
    )
    short_outstanding_conditions: str = field(
        default_factory=lambda: fake.sentence(nb_words=4)[:25]
    )
    lender_fee: str = field(default_factory=RG.monthly_payment)
    lender_bps: str = field(default_factory=RG.percentage)
    broker_fee: str = field(default_factory=RG.monthly_payment)
    admin_fee: str = field(default_factory=RG.monthly_payment)
    appraisal_rebate: str = field(default_factory=RG.monthly_savings)
    lawyer_fee: str = field(default_factory=RG.monthly_payment)
    additional_notes: str = field(
        default_factory=lambda: fake.sentence(nb_words=8)
    )
    google_review_no_reason: str = field(
        default_factory=lambda: fake.sentence(nb_words=10)
    )

    def __post_init__(self):
        if not self.month:
            month, year, day = RG.calendar_date_parts()
            self.month = month
            self.year = str(year)
            self.day = str(day)


@dataclass
class SignedData:
    no_flow: SignedNoFlowData = field(default_factory=SignedNoFlowData)
    final_yes: SignedFinalProductYesData = field(
        default_factory=SignedFinalProductYesData
    )
