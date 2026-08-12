"""Profile tab read actions on lead detail pages."""

import re

from playwright.sync_api import expect

from pages.base_page import BasePage
from utils.entity_navigation import open_bucket_record


class ProfilePage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.profile_tab = page.get_by_role("tab", name="Profile", exact=True)
        self.personal_information_tab = page.get_by_role(
            "tab", name="Personal Information"
        )
        self.mortgage_information_tab = page.get_by_role(
            "tab", name="Mortgage Information"
        )

    def open_lead_profile(self, deal_name: str, *, bucket: str) -> None:
        open_bucket_record(self.page, bucket, deal_name)
        self.click(self.profile_tab)
        expect(self.personal_information_tab).to_be_visible(timeout=30000)

    def _profile_field_value(self, label: str) -> str:
        """Read a Profile sub-tab label/value pair.

        CRM renders values as ``div.text-base``, clickable ``button.text-base``,
        or ``a`` links (email/phone) — not always a plain div.
        """
        label_cell = (
            self.page.locator("div.text-sm.text-slate-700")
            .filter(has_text=re.compile(rf"^{re.escape(label)}\b", re.I))
            .first
        )
        expect(label_cell).to_be_visible(timeout=30000)
        value_cell = label_cell.locator("xpath=following-sibling::*[1]")
        expect(value_cell).to_be_visible(timeout=30000)
        return value_cell.inner_text()

    def read_lead_name(self) -> str:
        self.click(self.profile_tab)
        self.click(self.personal_information_tab)
        expect(self.personal_information_tab).to_have_attribute(
            "data-state", "active", timeout=30000
        )
        return self._normalize_text(self._profile_field_value("Name"))

    def read_form_filled_at(self) -> str:
        self.click(self.profile_tab)
        self.click(self.personal_information_tab)
        expect(self.personal_information_tab).to_have_attribute(
            "data-state", "active", timeout=30000
        )
        return self._normalize_text(self._profile_field_value("Form filled at"))

    def read_mortgage_loan_amount(self) -> str:
        self.click(self.mortgage_information_tab)
        expect(self.mortgage_information_tab).to_have_attribute(
            "data-state", "active", timeout=30000
        )
        return self._normalize_currency(self._profile_field_value("Loan amount"))

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _normalize_currency(value: str) -> str:
        cleaned = (value or "").replace("$", "").replace(",", "").strip()
        if cleaned in {"_ _", "-", ""}:
            return ""
        if "." in cleaned:
            cleaned = cleaned.split(".", maxsplit=1)[0]
        return cleaned
