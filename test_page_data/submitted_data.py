from dataclasses import dataclass, field

from faker import Faker

from test_page_data.random_gen_data import RandomGenerator as RG

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
class SubmittedOptionData:
    mortgage_type: str = "HELOC"
    other_mortgage_type: str = ""
    mortgage_loan_amount: str = field(default_factory=RG.loan_amount)
    requested_ltv: str = field(default_factory=lambda: RG.percentage(40, 80))
    term_requested: str = field(default_factory=RG.term_requested)
    rate_requested: str = field(default_factory=RG.interest_rate)
    power_of_attorney: str = "no"
    approved: str = "no"
    rejected_reason: str = field(
        default_factory=lambda: fake.sentence(nb_words=8)[:275]
    )


@dataclass
class SubmittedData:
    option1: SubmittedOptionData = field(
        default_factory=lambda: SubmittedOptionData(
            approved="no",
            mortgage_type="HELOC",
        )
    )
    option2: SubmittedOptionData = field(
        default_factory=lambda: SubmittedOptionData(
            approved="no",
            mortgage_type="Refinance",
        )
    )
    option3: SubmittedOptionData = field(
        default_factory=lambda: SubmittedOptionData(
            approved="yes",
            mortgage_type="Home Equity Loan",
            power_of_attorney="yes",
        )
    )
