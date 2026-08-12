# from datetime import datetime
from test_page_data.random_gen_data import RandomGenerator as RG


def _birth_date_parts():
    return RG.birthday_form_parts()


_last_valid_lead_data: dict | None = None


def get_last_valid_lead_data() -> dict | None:
    """Return the most recently generated valid lead payload (for reporting)."""
    return _last_valid_lead_data


def update_lead_email(email: str) -> None:
    """Sync persisted lead payload email after CRM profile edits."""
    global _last_valid_lead_data
    if _last_valid_lead_data is not None:
        _last_valid_lead_data["enter_email"] = email.strip()


def update_lead_property_address(property_partial: str) -> None:
    """Sync persisted property address after CRM mortgage profile edits."""
    global _last_valid_lead_data
    if _last_valid_lead_data is not None:
        _last_valid_lead_data["enter_property_address_street_number"] = (
            property_partial.strip()
        )


def valid_lead_data():
    """Return a dict of valid values for every CreateLeadPage field (unique per call)."""
    global _last_valid_lead_data
   
    identity = RG.lead_identity()
    month, year, day = _birth_date_parts()

    data = {
        
        **identity,
        "enter_phone": "4165550123",
        "select_gender": "Male",
        "select_marital_status": "Common-law",
        "enter_address_street_number": RG.street_number(),
        "enter_postal_code": RG.canadian_postal_code(),
        "enter_property_address_street_number": RG.street_number(),
        "select_month": month,
        "select_year": year,
        "select_day": day,
        "maturity_month": "2",
        "maturity_year": "2028",
        "maturity_day": "18",
        "enter_loan_amount": RG.loan_amount(),
        "enter_mortgage_rate": RG.interest_rate(),
        "enter_credit_score": str(min(int(RG.credit_score()), 999)),
        "select_property_type": "Owner occupied",
        "enter_property_value": RG.property_value(),
        "enter_monthly_payment": RG.monthly_payment(),
        "enter_balance_owing": RG.balance_owing(),
        "enter_working_situation": RG.random_choice(["Working", "Self-employed", "Retired"]),
        "enter_working_location": f"{RG.city()}, {RG.province()}",
        "enter_income": RG.annual_income(),
        "enter_employer_name": RG.employer(),
        "select_whats_important": "Lower my mortgage rate",
    }
    _last_valid_lead_data = data
    return data


def get_lead_cases():
    """Return parametrized create-lead cases for the positive smoke test."""
    return [
        ("valid_all_fields", valid_lead_data(), True, "Lead created successfully"),
    ]
