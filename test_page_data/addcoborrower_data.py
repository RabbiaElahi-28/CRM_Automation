def _resolve_lead_name() -> str:
    from utils.lead_context import get_active_lead_name

    return get_active_lead_name()


test_data = {
    "login": {
        "email": "hammad.ali@fantechlabs.io",
        "password": "Test1234@"
    },

    "co_borrower": {
        "first_name": "Josh",
        "last_name": "Abraham",
        "email": "joshabraham1234@gmail.com",
        "phone": "(614) 876-2837",

        "dob_day": "Thursday, April 6th,",
        "dob_month": 3,
        "dob_year": 1995,

        "marital_status": "Married",

        "employer": "Fantech",
        "relation": "Spouse",
        "income": "71626"
    }
}


def get_coborrower_test_data() -> dict:
    """Return co-borrower payload with the active bootstrap lead name."""
    return {**test_data, "lead_name": _resolve_lead_name()}
