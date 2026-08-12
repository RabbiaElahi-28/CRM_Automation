from test_page_data.random_gen_data import RandomGenerator
from utils.wait_helpers import RELIABLE_PLACES_QUERIES

_gen = RandomGenerator()

# Short numeric queries (e.g. "3619") rarely return Places suggestions.
_RELIABLE_ADDRESS = RELIABLE_PLACES_QUERIES[0]
_RELIABLE_ADDRESS_ALT = RELIABLE_PLACES_QUERIES[1]

def _resolve_lead_name() -> str:
    from utils.lead_context import get_active_lead_name

    return get_active_lead_name()


lead_edit_data = {
    "contact": {
        "email": "",
        "phone": "4165550123",
        "postal_code": "M5H 2N2",
    },
    "gender": "Male",
    "marital_status": "Divorced",
    "address": {
        "partial": _RELIABLE_ADDRESS,
        "full": "",
    },
    "dob": {
        "month": "4",
        "year": "1995",
        "day": "10",
    },
    "mortgage": {
        "type": "Refinancing",
        "loan_amount": "350000",
        "rate": "5.25",
        "maturity_month": "2",
        "maturity_year": "2028",
        "maturity_day": "18",
        "credit_score": "720",
    },
    "property": {
        "partial": _RELIABLE_ADDRESS,
        "full": "",
        "type": "Owner occupied",
        "value": "650000",
        "monthly_payment": "2100",
        "balance": "420000",
    },
    "employment": {
        "work_situation": "Employed Full Time",
        "work_location_partial": _RELIABLE_ADDRESS_ALT,
        "work_location_full": "",
        "income": "85000",
        "employer": _gen.company_name(),
        "important_choice": "Use the equity",
    },
}


def get_lead_edit_data() -> dict:
    """Return lead edit payload with the active bootstrap lead name."""
    return {**lead_edit_data, "lead_name": _resolve_lead_name()}
