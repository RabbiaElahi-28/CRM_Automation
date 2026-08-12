from dataclasses import dataclass, field

from faker import Faker

from test_page_data.random_gen_data import RandomGenerator as RG

fake = Faker("en_CA")


@dataclass
class ClosingComplianceData:
    credit_score: str = field(default_factory=RG.credit_score)
    total_debt_ratio: str = field(default_factory=RG.tds_score)
    loan_to_value: str = field(default_factory=RG.percentage)
    finder_fee_percent: str = field(default_factory=RG.percentage)
    volume_bonus: str = field(default_factory=RG.monthly_payment)
    broker_fee: str = field(default_factory=RG.monthly_payment)
    underwriting_fee: str = field(default_factory=RG.monthly_payment)
    net_fee: str = field(default_factory=RG.monthly_payment)
    expense_deducted: str = field(default_factory=RG.monthly_payment)
    other_expenses: str = field(default_factory=RG.monthly_payment)
    referral_fee: str = field(default_factory=RG.monthly_savings)
    appraisal_expense: str = field(default_factory=RG.monthly_payment)
    uw_fee: str = field(default_factory=RG.monthly_payment)
    internal_agent_fee_a: str = field(default_factory=RG.monthly_savings)
    internal_agent_fee_b: str = field(default_factory=RG.monthly_savings)
    af: str = field(default_factory=RG.monthly_savings)
    ff: str = field(default_factory=RG.monthly_savings)
    insurer: str = field(default_factory=lambda: fake.company())
    mpp: bool = True
    high_ratio: bool = True
    conventional: bool = True
    cmhc: bool = True
    new_or_existing: str = "New Deal"
    mortgage_position: str = "First"
    out_of_province: str = "No"
    lender_type: str = "Bank"
    lender_class: str = "Bank"
    month: str = ""
    year: str = ""
    day: str = ""

    def __post_init__(self):
        if not self.month:
            month, year, day = RG.calendar_date_parts()
            self.month = month
            self.year = str(year)
            self.day = str(day)


@dataclass
class ClientCareChecksData:
    payment_request_sent: bool = True
    final_closing_notes: str = field(
        default_factory=lambda: fake.sentence(nb_words=12)
    )
    month: str = ""
    year: str = ""
    day: str = ""

    def __post_init__(self):
        if not self.month:
            month, year, day = RG.calendar_date_parts()
            self.month = month
            self.year = str(year)
            self.day = str(day)


@dataclass
class SignedFormSnapshot:
    """Values captured from the editable Signed tab or read-only Signed Form."""

    loan_amount: str = ""
    mortgage_type: str = ""
    other_mortgage_type: str = ""
    approved_ltv: str = ""
    approved_term: str = ""
    approved_rate: str = ""
    estimated_closing_date: str = ""
    client_lawyer: str = ""
    closing_email_sent: str = ""
    lender_fee: str = ""
    lender_bps: str = ""
    broker_fee: str = ""
    admin_fee: str = ""
    appraisal_rebate: str = ""
    lawyer_fee: str = ""
    trust_ledger_review: str = ""
    outstanding_conditions: str = ""
    meeting_notes: str = ""
    client_care_needs: str = ""
    google_review_status: str = ""


@dataclass
class ComplianceData:
    closing: ClosingComplianceData = field(default_factory=ClosingComplianceData)
    client_care: ClientCareChecksData = field(default_factory=ClientCareChecksData)
