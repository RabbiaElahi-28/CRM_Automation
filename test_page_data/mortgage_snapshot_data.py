from dataclasses import dataclass, field
import datetime

from test_page_data.random_gen_data import RandomGenerator as RG

from faker import Faker
import random

fake = Faker("en_CA")


@dataclass
class MortgageSnapshotData:

    # =====================================================
    # Deal
    # =====================================================

    # deal_name: str = "Ben Fluter dell"

    # =====================================================
    # Video
    # =====================================================

    vfli_number: str = field(default_factory=RG.vfli_number)

    introduction_script: str = field(
        default_factory=lambda: RG.sentence(12)[:150]
    )

    # =====================================================
    # Client Needs
    # =====================================================

    first_need: str = field(
        default_factory=lambda: RG.sentence(6)
    )

    ok_got_it: str = field(
        default_factory=lambda: RG.sentence(5)
    )

    second_need: str = field(
        default_factory=lambda: RG.sentence(6)
    )

    lets_get_to_work: str = field(
        default_factory=lambda: RG.sentence(5)
    )

    # =====================================================
    # Primary Credit
    # =====================================================

    credit_score: str = field(
        default_factory=RG.credit_score
    )

    tds_score: str = field(
        default_factory=RG.tds_score
    )

    credit_utilization: str = field(
        default_factory=RG.credit_utilization
    )

    primary_warnings: list = field(
        default_factory=lambda: [

            "High utilization warning",

            "Negative credit reported",

            "Collections reported"
        ]
    )

    # =====================================================
    # Co Applicant
    # =====================================================

    co_credit_score: str = field(
        default_factory=RG.credit_score
    )

    co_tds_score: str = field(
        default_factory=RG.tds_score
    )

    co_credit_utilization: str = field(
        default_factory=RG.credit_utilization
    )

    co_warnings: list = field(
        default_factory=lambda: [

            "Proposal reported",

            "Bankruptcy reported"
        ]
    )

    # =====================================================
    # Cost Of Doing Nothing
    # =====================================================

    current_balance: str = field(
        default_factory=RG.loan_amount
    )

    current_rate: str = field(
        default_factory=RG.interest_rate
    )

    years_to_pay: str = field(
        default_factory=RG.mortgage_years
    )

    total_interest: str = field(
        default_factory=RG.loan_amount
    )

    total_cost: str = field(
        default_factory=RG.loan_amount
    )

    monthly_payment: str = field(
        default_factory=RG.monthly_payment
    )

    # =====================================================
    # Mortgage Option 4
    # =====================================================

    option4_type: str = "Equity Line"

    option4_loan: str = field(
        default_factory=RG.loan_amount
    )

    option4_payment: str = field(
        default_factory=RG.monthly_payment
    )

    option4_savings: str = field(
        default_factory=RG.monthly_savings
    )

    option4_point1: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    option4_point2: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    option4_point3: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    # =====================================================
    # Mortgage Option 5
    # =====================================================

    option5_type: str = "Refinancing"

    option5_loan: str = field(
        default_factory=RG.loan_amount
    )

    option5_payment: str = field(
        default_factory=RG.monthly_payment
    )

    option5_savings: str = field(
        default_factory=RG.monthly_savings
    )

    option5_point1: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    option5_point2: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    option5_point3: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    # =====================================================
    # Home Appraised
    # =====================================================
    max_value: str = field(
        default_factory=RG.max_value
    )
    min_value: str = field(
        default_factory=RG.min_value
    )
    less_all_mortgages: str = field(
        default_factory=RG.loan_amount
    )

    value_used: str = field(
        default_factory=RG.property_value
    )

    loan_required: str = field(
        default_factory=RG.loan_amount
    )

    ltv: str = field(
        default_factory=lambda: RG.decimal(20, 85)
    )

    plan_type: str = "HELOC Renovation"

    # =====================================================
    # Final Prompt
    # =====================================================

    benefit_one: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    benefit_two: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    benefit_three: str = field(
        default_factory=lambda: RG.sentence(8)[:200]
    )

    final_prompt: str = field(
        default_factory=lambda: RG.sentence(10)[:200]
    )

    
    start_dt, end_dt,start_datetime, end_datetime = RG.meeting_datetimes()

    meeting_room: str = field(default_factory=lambda: random.choice(["JazzBerry Jam", "Purple Mountain Majesty", "Harold & the Purple Crayon", "Purple Pizzazz", "You Look Mauv'elous", "Peace, Love + Purple", "Giv'em the Razzmatazz"]))

    recipient: str = field(default_factory=lambda: random.choice(["Client", "Agent", "Client & Agent"]))

    description: str = field(
        default_factory=lambda: f"Mortgage Meeting - {fake.catch_phrase()}"
    )
    meeting_link: str = field(
        default_factory=lambda: f"https://example.com/meeting-{fake.uuid4()[:8]}"
    )

    
  
    