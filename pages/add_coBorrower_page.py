import re

from playwright.sync_api import expect

from utils.config import Config
from utils.entity_navigation import LEAD_BUCKET, open_bucket_record
from utils.wait_helpers import wait_for_page_ready

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


class CoBorrowerPage:

    def __init__(self, page):
        self.page = page

    def _dialog(self):
        return self.page.get_by_role("alertdialog")

    # ---------- NAVIGATION ----------
    def open(self):
        self.page.goto(Config.BASE_URL)
        wait_for_page_ready(self.page)

    def open_lead(self, lead_name: str, bucket=LEAD_BUCKET):
        open_bucket_record(self.page, bucket, lead_name)

    def open_co_borrowers_tab(self):
        self.page.get_by_role("tab", name="Co-borrowers").click()

    def click_add_co_borrower(self):
        self.page.get_by_role("button", name="Add Co-Borrower").click()
        expect(self._dialog()).to_be_visible(timeout=15000)

    # ---------- FORM ----------
    def fill_basic_info(self, data):
        dialog = self._dialog()
        dialog.locator("#firstName").fill(data["first_name"])
        dialog.locator("#lastName").fill(data["last_name"])
        dialog.locator("#email").fill(data["email"])
        dialog.get_by_role("textbox", name="(XXX) XXX-XXXX").fill(data["phone"])

    def _dob_picker_button(self):
        return (
            self._dialog()
            .locator("label")
            .filter(has_text="Date of Birth")
            .locator("..")
            .get_by_role("button")
        )

    def select_dob(self, data):
        self._dob_picker_button().click()
        calendar = self.page.locator("[data-slot='calendar']")
        expect(calendar).to_be_visible(timeout=10000)

        dob_day = str(data["dob_day"]).strip().rstrip(",")
        if not dob_day.isdigit():
            self.page.get_by_role("combobox", name="month").select_option(
                str(data["dob_month"])
            )
            self.page.get_by_role("combobox", name="year").select_option(
                str(data["dob_year"])
            )
            self.page.get_by_role("button", name=dob_day).click()
            return

        month_index = int(data["dob_month"])
        year = str(data["dob_year"])
        calendar.locator("select").nth(0).select_option(index=month_index)
        calendar.locator("select").nth(1).select_option(value=year)
        month_name = _MONTHS_FULL[month_index]
        calendar.get_by_role(
            "button",
            name=re.compile(
                rf"{month_name}\s+{_ordinal_day(dob_day)},\s*{year}",
                re.I,
            ),
        ).click()

    def _combobox_for_label(self, label: str):
        return (
            self._dialog()
            .locator("label")
            .filter(has_text=label)
            .locator("..")
            .get_by_role("combobox")
        )

    def select_marital_status(self, status: str):
        trigger = self._combobox_for_label("Marital Status")
        expect(trigger).to_be_enabled(timeout=15000)
        trigger.click()
        self.page.get_by_role("option", name=status).click()

    def select_relation(self, relation: str):
        trigger = self._combobox_for_label("Relation")
        expect(trigger).to_be_enabled(timeout=15000)
        trigger.click()
        self.page.get_by_role("option", name=relation).click()

    def fill_employment(self, employer: str, relation: str, income: str):
        self._dialog().get_by_role("textbox", name="Employer").fill(employer)
        self.select_relation(relation)
        self.fill_income(income)

    def fill_income(self, income: str):
        self._dialog().get_by_role("textbox", name="Income").fill(income)

    def clear_basic_info(self):
        self.page.locator("#firstName").fill("")
        self.page.locator("#lastName").fill("")
        self.page.locator("#email").fill("")
        self.page.get_by_role("textbox", name="(XXX) XXX-XXXX").fill("")

    def clear_employment(self):
        self.page.get_by_role("textbox", name="Employer").fill("")
        self.fill_income("")

    def set_field(self, field: str, value: str):
        dialog = self._dialog()
        field_map = {
            "first_name": dialog.locator("#firstName"),
            "last_name": dialog.locator("#lastName"),
            "email": dialog.locator("#email"),
            "phone": dialog.get_by_role("textbox", name="(XXX) XXX-XXXX"),
            "employer": dialog.get_by_role("textbox", name="Employer"),
            "income": dialog.get_by_role("textbox", name="Income"),
        }
        field_map[field].fill(value)

    def clear_field(self, field: str):
        self.set_field(field, "")

    def fill_valid_baseline(self):
        """Minimum valid co-borrower data for isolated invalid-field tests."""
        self.fill_basic_info(
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "test.user@example.com",
                "phone": "1234567890",
            }
        )
        self.select_dob({"dob_month": 0, "dob_year": 1990, "dob_day": "15"})
        self.select_marital_status("Married")
        self.fill_employment("Acme Corp", "Parent", "75000")

    def save(self):
        self._dialog().get_by_role("button", name="Save").click()
