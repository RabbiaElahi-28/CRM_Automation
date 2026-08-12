import re

from playwright.sync_api import expect

from utils.config import Config
from utils.wait_helpers import ensure_complete_postal_code, select_google_places_suggestion

_MONTHS_FULL = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _ordinal_day(day):
    """Turn a day number (e.g. '4') into its ordinal form (e.g. '4th')."""
    n = int(day)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


class CreateLeadPage:
    def __init__(self, page):
        self.page = page

        self.enter_first_name = page.get_by_role("textbox", name="Enter first name")
        self.enter_last_name = page.get_by_role("textbox", name="Enter last name")
        self.enter_email = page.locator('[id="personalInfo.email"]')
        self.enter_phone = page.locator('[id="personalInfo.phone"]')
        self.enter_address = page.locator('[id="personalInfo.address"]')
        self.enter_city = page.locator('[id="personalInfo.city"]')
        self.enter_state = page.locator('[id="personalInfo.state"]')
        self.enter_postal_code = page.locator('[id="personalInfo.postalCode"]')
        self.birthday_picker = (
            page.locator("label")
            .filter(has_text=re.compile(r"^Birthday\b", re.I))
            .locator("..")
            .get_by_role("button")
        )
        self.maturity_picker = (
            page.locator("label")
            .filter(has_text=re.compile(r"^Maturity Date\b", re.I))
            .locator("..")
            .get_by_role("button")
        )
        self.enter_loan_amount = page.locator('[id="MortgageInfo.loanAmount"]')
        self.enter_credit_score = page.locator('[id="MortgageInfo.currentCreditScore"]')
        self.enter_mortgage_rate = page.locator('[id="MortgageInfo.mortgageRatePercent"]')
        self.enter_property_address = page.locator('[id="MortgageInfo.propertyAddress"]')
        self.enter_property_value = page.locator('[id="MortgageInfo.propertyValue"]')
        self.enter_monthly_payment = page.locator('[id="MortgageInfo.monthlyMortgagePayment"]')
        self.enter_balance_owing = page.locator('[id="MortgageInfo.mortgageBalanceOwing"]')
        self.enter_working_situation = page.locator('[id="MortgageInfo.workingSituation"]')
        self.enter_working_location = page.locator('[id="MortgageInfo.workingLocation"]')
        self.enter_income = page.locator('[id="MortgageInfo.income"]')
        self.enter_employer_name = page.locator('[id="MortgageInfo.employerName"]')
        self.create_lead_button = page.get_by_role("button", name="Create Lead")

    def open(self):
        self.page.goto(Config.BASE_URL + "/create-lead")
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        expect(self.page.get_by_role("heading", name="Create New Lead")).to_be_visible(
            timeout=30000
        )

    def _select_labeled_combobox(self, label: str, option_name: str):
        trigger = (
            self.page.locator("label")
            .filter(has_text=label)
            .locator("..")
            .get_by_role("combobox")
        )
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        self.page.get_by_role("option", name=option_name, exact=True).click()

    def _select_first_combobox_option(self, label: str):
        trigger = (
            self.page.locator("label")
            .filter(has_text=label)
            .locator("..")
            .get_by_role("combobox")
        )
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        self.page.get_by_role("option").first.click()

    def enter_lead_first_name(self, first_name: str):
        self.enter_first_name.fill(first_name)

    def enter_lead_last_name(self, last_name: str):
        self.enter_last_name.fill(last_name)

    def enter_lead_name(self, enter_name: str):
        """Fill first/last name from a combined deal label when split fields are unavailable."""
        parts = enter_name.split()
        if not parts:
            return
        self.enter_lead_first_name(parts[0])
        if len(parts) > 1:
            if " Automation Deal " in enter_name:
                last_name = enter_name.split(" Automation Deal ", 1)[0].split(None, 1)[1]
            else:
                last_name = parts[1]
            self.enter_lead_last_name(last_name)

    def enter_lead_email(self, enter_email):
        self.enter_email.fill(enter_email)

    def enter_lead_phone(self, enter_phone):
        self.enter_phone.fill(enter_phone)

    def select_lead_gender(self, select_gender):
        self._select_labeled_combobox("Gender", select_gender)

    def select_lead_marital_status(self, select_marital_status):
        self._select_labeled_combobox("Marital Status", select_marital_status)

    def enter_lead_address(self, enter_address):
        self.enter_address.fill(enter_address)

    def _select_first_google_places_suggestion(self, input_locator, street_number: str):
        select_google_places_suggestion(
            self.page, input_locator, street_number, type_delay=50
        )

    def enter_lead_address_with_autocomplete(
        self, street_number: str, *, expected_postal_code: str | None = None
    ):
        self._select_first_google_places_suggestion(self.enter_address, street_number)
        if expected_postal_code:
            ensure_complete_postal_code(self.enter_postal_code, expected_postal_code)

    def enter_lead_property_address_with_autocomplete(self, street_number: str):
        self._select_first_google_places_suggestion(
            self.enter_property_address, street_number
        )

    def enter_lead_city(self, city: str):
        self.enter_city.fill(city)

    def enter_lead_state(self, state: str):
        self.enter_state.fill(state)

    def enter_lead_postal_code(self, postal_code: str):
        self.enter_postal_code.fill(postal_code)

    def select_lead_birthday(self, select_month, select_year, select_day):
        self._pick_calendar_date(
            self.birthday_picker, select_month, select_year, select_day
        )

    def select_lead_maturity_date(self, select_month, select_year, select_day):
        self._pick_calendar_date(
            self.maturity_picker, select_month, select_year, select_day
        )

    def _pick_calendar_date(self, picker, select_month, select_year, select_day):
        picker.click()
        calendar = self.page.locator("[data-slot='calendar']")
        calendar.wait_for(state="visible", timeout=10000)
        calendar.locator("select").nth(1).select_option(value=str(select_year))
        calendar.locator("select").nth(0).select_option(index=int(select_month) - 1)
        month_name = _MONTHS_FULL[int(select_month) - 1]
        calendar.get_by_role(
            "button",
            name=re.compile(
                rf"{month_name}\s+{_ordinal_day(select_day)},\s*{select_year}",
                re.I,
            ),
        ).click()

    def select_lead_product_type(self, product_type: str):
        self._select_labeled_combobox("Product Type", product_type)

    def select_first_product_type(self):
        self._select_first_combobox_option("Product Type")

    def enter_lead_loan_amount(self, loan_amount: str):
        self.enter_loan_amount.fill(loan_amount)

    def enter_lead_credit_score(self, enter_credit_score):
        self.enter_credit_score.fill(enter_credit_score)

    def enter_lead_mortgage_rate(self, mortgage_rate: str):
        self.enter_mortgage_rate.fill(mortgage_rate)

    def select_lead_property_type(self, select_property_type):
        self._select_labeled_combobox("Property Type", select_property_type)

    def enter_lead_property_address(self, enter_property_address):
        self.enter_property_address.fill(enter_property_address)

    def enter_lead_property_value(self, enter_property_value):
        self.enter_property_value.fill(enter_property_value)

    def enter_lead_monthly_payment(self, enter_monthly_payment):
        self.enter_monthly_payment.fill(enter_monthly_payment)

    def enter_lead_balance_owing(self, enter_balance_owing):
        self.enter_balance_owing.fill(enter_balance_owing)

    def enter_lead_working_situation(self, enter_working_situation):
        self.enter_working_situation.fill(enter_working_situation)

    def enter_lead_working_location(self, enter_working_location):
        self.enter_working_location.fill(enter_working_location)

    def enter_lead_income(self, enter_income):
        self.enter_income.fill(enter_income)

    def enter_lead_employer_name(self, enter_employer_name):
        self.enter_employer_name.fill(enter_employer_name)

    def select_lead_whats_important(self, select_whats_important):
        self._select_labeled_combobox("What's Important to You", select_whats_important)

    def submit_lead(self):
        expect(self.create_lead_button).to_be_enabled(timeout=Config.TIMEOUT)
        self.create_lead_button.click()

    def submit_lead_and_wait_success(self) -> None:
        """Submit and wait for lead-bucket redirect; surface CRM validation errors."""
        expect(self.create_lead_button).to_be_enabled(timeout=Config.TIMEOUT)

        last_exc: Exception | None = None
        for attempt in range(2):
            self.create_lead_button.click()
            try:
                self.page.wait_for_url(
                    re.compile(r"/lead-bucket"), timeout=Config.TIMEOUT
                )
                return
            except Exception as exc:
                last_exc = exc
                if attempt == 0 and "/create-lead" in self.page.url:
                    expect(self.create_lead_button).to_be_enabled(
                        timeout=Config.TIMEOUT
                    )
                    continue
                break
        exc = last_exc
        assert exc is not None
        toast = self.page.locator("[data-sonner-toast]").first
        if toast.count() > 0:
            try:
                message = toast.inner_text(timeout=2000).strip()
                if message:
                    raise AssertionError(f"Create lead failed: {message}") from exc
            except AssertionError:
                raise
            except Exception:
                pass
        phone_error = self.page.locator(
            '[id="personalInfo.phone"]'
        ).locator("xpath=ancestor::div[contains(@class,'space-y-2')]//div[contains(@class,'text-red-500')]")
        if phone_error.count() > 0:
            try:
                message = phone_error.first.inner_text(timeout=2000).strip()
                if message:
                    raise AssertionError(
                        f"Create lead phone validation failed: {message}"
                    ) from exc
            except AssertionError:
                raise
            except Exception:
                pass
        raise AssertionError(
            f"Create lead did not redirect to lead bucket (still on {self.page.url})"
        ) from exc

    def open_new_lead_form(self):
        if "/create-lead" not in self.page.url:
            self.open()

    _FIELD_LOCATORS = {
        "enter_first_name": "enter_first_name",
        "enter_last_name": "enter_last_name",
        "enter_email": "enter_email",
        "enter_phone": "enter_phone",
        "enter_postal_code": "enter_postal_code",
        "enter_address": "enter_address",
        "enter_city": "enter_city",
        "enter_state": "enter_state",
        "enter_credit_score": "enter_credit_score",
        "enter_mortgage_rate": "enter_mortgage_rate",
        "enter_property_address": "enter_property_address",
        "enter_property_value": "enter_property_value",
        "enter_monthly_payment": "enter_monthly_payment",
        "enter_balance_owing": "enter_balance_owing",
        "enter_working_situation": "enter_working_situation",
        "enter_working_location": "enter_working_location",
        "enter_income": "enter_income",
        "enter_employer_name": "enter_employer_name",
        "enter_loan_amount": "enter_loan_amount",
    }

    def set_field(self, field: str, value: str):
        locator = getattr(self, self._FIELD_LOCATORS[field])
        locator.fill(value)

    def clear_field(self, field: str):
        self.set_field(field, "")

    def clear_all_fields(self):
        for field_name in self._FIELD_LOCATORS:
            self.clear_field(field_name)

    def refill_form(self, lead_data):
        """Fill fields without re-navigating (for validation test resets)."""
        self.enter_lead_first_name(lead_data["first_name"])
        self.enter_lead_last_name(lead_data["last_name"])
        self.enter_lead_email(lead_data["enter_email"])
        self.enter_lead_phone(lead_data["enter_phone"])
        self.select_lead_gender(lead_data["select_gender"])
        self.select_lead_marital_status(lead_data["select_marital_status"])
        used_address_autocomplete = bool(lead_data.get("enter_address_street_number"))
        if used_address_autocomplete:
            self.enter_lead_address_with_autocomplete(
                lead_data["enter_address_street_number"],
                expected_postal_code=lead_data.get("enter_postal_code"),
            )
        elif lead_data.get("enter_address"):
            self.enter_lead_address(lead_data["enter_address"])
        if lead_data.get("enter_city"):
            self.enter_lead_city(lead_data["enter_city"])
        if lead_data.get("enter_state"):
            self.enter_lead_state(lead_data["enter_state"])
        if lead_data.get("enter_postal_code") and not used_address_autocomplete:
            self.enter_lead_postal_code(lead_data["enter_postal_code"])
        self.select_lead_birthday(
            lead_data["select_month"], lead_data["select_year"], lead_data["select_day"]
        )
        self.select_lead_maturity_date(
            lead_data["maturity_month"],
            lead_data["maturity_year"],
            lead_data["maturity_day"],
        )
        if lead_data.get("select_product_type"):
            self.select_lead_product_type(lead_data["select_product_type"])
        else:
            self.select_first_product_type()
        if lead_data.get("enter_loan_amount"):
            self.enter_lead_loan_amount(lead_data["enter_loan_amount"])
        if lead_data.get("enter_mortgage_rate"):
            self.enter_lead_mortgage_rate(lead_data["enter_mortgage_rate"])
        self.enter_lead_credit_score(lead_data["enter_credit_score"])
        self.select_lead_property_type(lead_data["select_property_type"])
        if lead_data.get("enter_property_address_street_number"):
            self.enter_lead_property_address_with_autocomplete(
                lead_data["enter_property_address_street_number"]
            )
        elif lead_data.get("enter_property_address"):
            self.enter_lead_property_address(lead_data["enter_property_address"])
        self.enter_lead_property_value(lead_data["enter_property_value"])
        self.enter_lead_monthly_payment(lead_data["enter_monthly_payment"])
        self.enter_lead_balance_owing(lead_data["enter_balance_owing"])
        self.enter_lead_working_situation(lead_data["enter_working_situation"])
        self.enter_lead_working_location(lead_data["enter_working_location"])
        self.enter_lead_income(lead_data["enter_income"])
        self.enter_lead_employer_name(lead_data["enter_employer_name"])
        self.select_lead_whats_important(lead_data["select_whats_important"])

    def fill_form(self, lead_data):
        """Open the new-lead form and fill every field from a data dict."""
        self.open_new_lead_form()
        self.refill_form(lead_data)

    _INVALID_RESET_FIELDS = (
        "enter_email",
        "enter_postal_code",
        "enter_credit_score",
        "enter_mortgage_rate",
        "enter_phone",
    )

    def restore_baseline_for_invalid_tests(self, baseline: dict):
        """Restore text fields touched by invalid-validation cases."""
        for key in self._INVALID_RESET_FIELDS:
            if key in baseline:
                self.set_field(key, str(baseline[key]))
