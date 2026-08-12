import re
from urllib.parse import quote

from playwright.sync_api import expect

from utils.config import Config
from utils.entity_navigation import LEAD_BUCKET, MY_DEALS_BUCKET, open_bucket_record
from utils.wait_helpers import (
    ensure_complete_postal_code,
    select_google_places_suggestion,
    wait_for_page_ready,
)

_STATUS_SCOPE_BY_PATH = {
    "lead-bucket": "lead_bucket",
    "my-leads": "lead",
    "sales-backend": "renewal",
    "sales": "application",
    "marketing": "marketing",
    "compliance": "closed",
    "client-care": "client",
}
_DETAIL_PATH = re.compile(
    r"/(lead-bucket|my-leads|sales-backend|sales|compliance|marketing|client-care)/([^/?#]+)"
)

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
    n = int(day)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


class LeadEditPage:
    def __init__(self, page):
        self.page = page

    @staticmethod
    def _safe_fill(locator, value) -> None:
        locator.wait_for(state="visible")
        locator.fill("" if value is None else str(value))

    # ---------- NAVIGATION ----------
    def open(self):
        self.page.goto(Config.BASE_URL)
        wait_for_page_ready(self.page)

    def open_lead_for_edit(self, lead_name: str, bucket=LEAD_BUCKET):
        from utils.lead_context import get_lead_context

        ctx = get_lead_context()
        if ctx.is_bootstrapped and bucket == LEAD_BUCKET:
            bucket = MY_DEALS_BUCKET
        open_bucket_record(self.page, bucket, lead_name)
        match = _DETAIL_PATH.search(self.page.url)
        if not match:
            raise AssertionError(f"Not on lead detail page: {self.page.url}")
        path_segment, lead_id = match.group(1), match.group(2)
        status_scope = _STATUS_SCOPE_BY_PATH.get(path_segment)
        query = f"?statusScope={quote(status_scope)}" if status_scope else ""
        self.page.goto(f"{Config.BASE_URL}/edit-lead/{lead_id}{query}")
        self.page.wait_for_load_state("domcontentloaded")
        expect(self.page.locator("#email")).to_be_visible(timeout=30000)

    def _client_tabpanel(self):
        return self.page.get_by_role("tabpanel").filter(
            has=self.page.locator("#email")
        )

    def open_client_tab(self):
        self.page.get_by_role("tab", name="Client Information").click()
        expect(self._client_tabpanel()).to_be_visible(timeout=15000)
        expect(self.page.locator("#email")).to_be_visible(timeout=15000)

    def _mortgage_tabpanel(self):
        return self.page.get_by_role("tabpanel").filter(
            has=self.page.locator("#loanAmount")
        )

    def _combobox_for_label(self, scope, label: str):
        return (
            scope.locator("label")
            .filter(has_text=label)
            .locator("..")
            .get_by_role("combobox")
        )

    def _select_labeled_combobox(self, label: str, option_name: str, *, exact: bool = True):
        if label in {"Gender", "Marital Status"}:
            scope = self._client_tabpanel()
        elif label in {"Product Type", "Property Type", "What's Important to You"}:
            scope = self._mortgage_tabpanel()
        else:
            scope = self.page
        trigger = self._combobox_for_label(scope, label)
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        option = self.page.get_by_role("option", name=option_name, exact=exact)
        expect(option.first).to_be_visible(timeout=10000)
        option.first.click()

    def _select_first_combobox_option(self, label: str):
        scope = self._mortgage_tabpanel()
        trigger = self._combobox_for_label(scope, label)
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        self.page.get_by_role("option").first.click()

    def _select_first_google_places_suggestion(self, input_locator, street_number: str):
        select_google_places_suggestion(
            self.page, input_locator, street_number, type_delay=50
        )

    def _pick_calendar_date(self, label: str, month: str, year: str, day: str):
        picker = (
            self.page.locator("label")
            .filter(has_text=label)
            .locator("..")
            .get_by_role("button")
        )
        picker.click()
        calendar = self.page.locator("[data-slot='calendar']")
        expect(calendar).to_be_visible(timeout=10000)
        calendar.locator("select").nth(1).select_option(value=str(year))
        calendar.locator("select").nth(0).select_option(index=int(month) - 1)
        month_name = _MONTHS_FULL[int(month) - 1]
        calendar.get_by_role(
            "button",
            name=re.compile(
                rf"{month_name}\s+{_ordinal_day(day)},\s*{year}",
                re.I,
            ),
        ).click()

    # ---------- PERSONAL INFO ----------
    def update_contact_email(self, email: str):
        self.open_client_tab()
        self._safe_fill(self.page.locator("#email"), email)

    def update_contact_info(self, email: str, phone: str):
        self.open_client_tab()
        self.update_contact_email(email)
        self._safe_fill(self.page.locator("#phone"), phone)

    def set_client_field(self, field: str, value: str):
        self.open_client_tab()
        field_map = {
            "email": self.page.locator("#email"),
            "phone": self.page.locator("#phone"),
            "postal_code": self.page.locator("#postalCode"),
        }
        self._safe_fill(field_map[field], value)

    def clear_client_field(self, field: str):
        self.set_client_field(field, "")

    def select_gender(self, gender: str):
        self._select_labeled_combobox("Gender", gender)

    def select_marital_status(self, status: str):
        self._select_labeled_combobox("Marital Status", status)

    def update_address(
        self, street_number: str, *, expected_postal_code: str | None = None
    ):
        self._select_first_google_places_suggestion(
            self.page.locator("#address"), street_number
        )
        if expected_postal_code:
            ensure_complete_postal_code(
                self.page.locator("#postalCode"), expected_postal_code
            )

    def select_dob(self, month: str, year: str, day: str):
        self._pick_calendar_date("Birthday", month, year, day)

    def save_client_info(self):
        self.open_client_tab()
        self._client_tabpanel().get_by_role("button", name="Save").click()

    def sava_client_info(self):
        """Backward-compatible alias."""
        self.save_client_info()

    # ---------- MORTGAGE INFO ----------
    def open_mortgage_tab(self):
        self.page.get_by_role("tab", name="Mortgage Information").click()
        expect(self._mortgage_tabpanel()).to_be_visible(timeout=15000)
        expect(self.page.locator("#loanAmount")).to_be_visible(timeout=15000)

    def set_mortgage_field(self, field: str, value: str):
        self.open_mortgage_tab()
        field_map = {
            "credit_score": self.page.locator("#currentCreditScore"),
            "mortgage_rate": self.page.locator("#mortgageRatePercent"),
        }
        self._safe_fill(field_map[field], value)

    def clear_mortgage_field(self, field: str):
        self.set_mortgage_field(field, "")

    def select_mortgage_type(self, product_type: str | None = None):
        self.open_mortgage_tab()
        if not product_type:
            self._select_first_combobox_option("Product Type")
            return

        trigger = self._combobox_for_label(self._mortgage_tabpanel(), "Product Type")
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        option = self.page.get_by_role("option", name=product_type, exact=True)
        if option.count() == 0:
            self.page.keyboard.press("Escape")
            self._select_first_combobox_option("Product Type")
        else:
            option.first.click()

    def fill_mortgage_details(
        self,
        loan_amount: str,
        rate: str,
        maturity_month: str,
        maturity_year: str,
        maturity_day: str,
        credit_score: str,
    ):
        self.open_mortgage_tab()
        self._safe_fill(self.page.locator("#loanAmount"), loan_amount)
        self._safe_fill(self.page.locator("#mortgageRatePercent"), rate)
        self._pick_calendar_date("Maturity Date", maturity_month, maturity_year, maturity_day)
        self._safe_fill(self.page.locator("#currentCreditScore"), credit_score)

    def fill_property_info(
        self,
        property_partial: str,
        property_type: str,
        value: str,
        monthly_payment: str,
        balance: str,
        *,
        property_full: str | None = None,
    ):
        self.open_mortgage_tab()
        trigger = self._combobox_for_label(self._mortgage_tabpanel(), "Property Type")
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        option = self.page.get_by_role("option", name=property_type, exact=True)
        if option.count() == 0:
            self.page.keyboard.press("Escape")
            self._select_first_combobox_option("Property Type")
        else:
            option.first.click()

        self._select_first_google_places_suggestion(
            self.page.locator("#propertyAddress"), property_partial
        )
        self._safe_fill(self.page.locator("#propertyValue"), value)
        self._safe_fill(self.page.locator("#monthlyMortgagePayment"), monthly_payment)
        self._safe_fill(self.page.locator("#mortgageBalanceOwing"), balance)

    def fill_employment(
        self,
        work_situation: str,
        work_location_partial: str,
        income: str,
        employer: str,
        important_choice: str,
        *,
        work_location_full: str | None = None,
    ):
        self.open_mortgage_tab()
        self._safe_fill(self.page.locator("#workingSituation"), work_situation)
        self._select_first_google_places_suggestion(
            self.page.locator("#workingLocation"), work_location_partial
        )
        self._safe_fill(self.page.locator("#income"), income)
        self._safe_fill(self.page.locator("#employerName"), employer)
        trigger = self._combobox_for_label(
            self._mortgage_tabpanel(), "What's Important to You"
        )
        expect(trigger).to_be_enabled(timeout=30000)
        trigger.click()
        option = self.page.get_by_role("option", name=important_choice, exact=False)
        if option.count() == 0:
            self.page.keyboard.press("Escape")
            self._select_first_combobox_option("What's Important to You")
        else:
            option.first.click()

    def save_mortgage_changes(self):
        self.open_mortgage_tab()
        save_button = self._mortgage_tabpanel().get_by_role("button", name="Save")
        save_button.scroll_into_view_if_needed()
        expect(save_button).to_be_enabled(timeout=10000)
        save_button.click()

    def save_changes(self):
        self.save_mortgage_changes()

    _CLIENT_INVALID_RESET = ("email", "phone", "postal_code")
    _MORTGAGE_INVALID_RESET = ("credit_score", "mortgage_rate")

    def restore_baseline_for_invalid_tests(self, baseline: dict):
        contact = baseline.get("contact", {})
        mortgage = baseline.get("mortgage", {})
        for field in self._CLIENT_INVALID_RESET:
            if field == "email" and contact.get("email") is not None:
                self.set_client_field("email", contact["email"])
            elif field == "phone" and contact.get("phone") is not None:
                self.set_client_field("phone", contact["phone"])
            elif field == "postal_code":
                self.clear_client_field("postal_code")
        for field in self._MORTGAGE_INVALID_RESET:
            if field == "credit_score" and mortgage.get("credit_score") is not None:
                self.set_mortgage_field("credit_score", mortgage["credit_score"])
            elif field == "mortgage_rate" and mortgage.get("rate") is not None:
                self.set_mortgage_field("mortgage_rate", mortgage["rate"])
