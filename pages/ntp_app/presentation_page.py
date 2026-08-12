from __future__ import annotations

import re

from pages.base_page import BasePage
from playwright.sync_api import Page, expect

from utils.config import Config
from utils.mortgage_snapshot_display import (
    format_currency_display,
    normalize_percent,
    normalize_whitespace,
    normalize_years,
)
from utils.ntp_display import NtpDisplayExpectations


class NtpAppPresentationPage(BasePage):
    """Read-only NTP presentation — single scrollable page (no slides)."""

    REVIEW_LABEL = re.compile(r"reviewed the plan in detail", re.I)

    def __init__(self, page: Page):
        super().__init__(page)
        self.presentation_root = page.locator("body")
        self.profile_cards = page.locator("#profileCard")
        self.review_label = page.get_by_text(self.REVIEW_LABEL)
        self.review_section = self.review_label.locator(
            "xpath=ancestor::div[contains(@class,'flex')][1]"
        )
        self.review_checkbox = self.review_label.locator(
            "xpath=preceding-sibling::button[1]"
        )
        self.download_pdf_btn = page.get_by_role("button", name="Download PDF")

    def wait_for_presentation(self) -> None:
        expect(
            self.page.get_by_text(
                re.compile(r"Name\s*:?\s*\w", re.I)
            ).first
        ).to_be_visible(timeout=Config.TIMEOUT)
        expect(
            self.page.get_by_text(re.compile(r"YourCredit Profile|Credit Score", re.I)).first
        ).to_be_visible(timeout=Config.TIMEOUT)

    def _assert_header_field(self, label: str, expected: str) -> None:
        if not expected:
            return
        header = self.page.get_by_text(
            re.compile(rf"{re.escape(label)}\s*:?\s*{re.escape(expected)}", re.I)
        ).first
        expect(header).to_be_visible(timeout=Config.TIMEOUT)

    def _assert_text_contains(self, expected: str) -> None:
        cleaned = normalize_whitespace(expected)
        if not cleaned:
            return
        expect(self.page.get_by_text(cleaned, exact=False).first).to_be_visible(
            timeout=Config.TIMEOUT
        )

    def _format_label_value(self, expected: str, *, kind: str) -> str:
        if kind == "currency":
            return format_currency_display(expected)
        if kind == "percent":
            return normalize_percent(expected)
        if kind == "years":
            return normalize_years(expected)
        return normalize_whitespace(str(expected))

    def _assert_split_label_value(self, label: str, value: str) -> None:
        """
        NTP often renders label, description, and value in separate paragraphs.

        Prefer the value inside the same block as the matching label.
        """
        value_pattern = re.compile(re.escape(value), re.I)
        label_pattern = re.compile(re.escape(label), re.I)
        candidates = self.page.get_by_text(label_pattern)
        for i in range(candidates.count()):
            label_loc = candidates.nth(i)
            try:
                if not label_loc.is_visible():
                    continue
            except Exception:
                continue
            section = label_loc.locator("xpath=ancestor::div[1]")
            value_loc = section.get_by_text(value_pattern)
            if value_loc.count() == 0:
                continue
            expect(value_loc.first).to_be_visible(timeout=Config.TIMEOUT)
            return

        expect(self.page.get_by_text(label_pattern).first).to_be_visible(
            timeout=Config.TIMEOUT
        )
        expect(self.page.get_by_text(value_pattern).first).to_be_visible(
            timeout=Config.TIMEOUT
        )

    def _assert_label_value(
        self,
        label: str,
        expected: str,
        *,
        kind: str = "text",
        window: int = 80,
    ) -> None:
        if not normalize_whitespace(str(expected)):
            return
        value = self._format_label_value(expected, kind=kind)
        pattern = re.compile(
            rf"{re.escape(label)}.{{0,{window}}}{re.escape(value)}",
            re.I | re.S,
        )
        inline = self.page.get_by_text(pattern).first
        try:
            expect(inline).to_be_visible(timeout=5000)
        except AssertionError:
            self._assert_split_label_value(label, value)

    def assert_header(self, expectations: NtpDisplayExpectations) -> None:
        self._assert_header_field("Name", expectations.header_first_name)
        self._assert_header_field("VFLI", expectations.vfli_number)
        if expectations.header_time:
            self._assert_header_field("Time", expectations.header_time)

    def assert_profile_cards(
        self,
        expectations: NtpDisplayExpectations,
        *,
        with_co_borrower: bool,
    ) -> None:
        self._assert_text_contains(expectations.profile_full_name)
        self._assert_label_value("Credit Score", expectations.applicant_credit_score)
        self._assert_label_value(
            "Credit Utilization",
            expectations.applicant_credit_utilization,
            kind="percent",
        )
        self._assert_label_value(
            "Total Debt Services",
            expectations.applicant_tds,
            kind="percent",
        )
        if expectations.applicant_credit_notes:
            self._assert_text_contains(expectations.applicant_credit_notes)

        if not with_co_borrower:
            return

        if expectations.co_applicant_name and expectations.co_applicant_name != "N/A":
            self._assert_text_contains(expectations.co_applicant_name)
        if expectations.co_applicant_credit_score:
            self._assert_label_value(
                "Credit Score",
                expectations.co_applicant_credit_score,
            )
        self._assert_label_value(
            "Credit Utilization",
            expectations.co_applicant_credit_utilization,
            kind="percent",
        )
        if expectations.co_applicant_credit_notes:
            self._assert_text_contains(expectations.co_applicant_credit_notes)

    def assert_true_cost_of_debt(self, expectations: NtpDisplayExpectations) -> None:
        self._assert_label_value(
            "high-interest debt",
            expectations.high_interest_debt,
            kind="currency",
        )
        self._assert_label_value(
            "high interest rate",
            expectations.average_interest_rate,
            kind="percent",
        )
        self._assert_label_value(
            "Minimum Payment",
            expectations.min_monthly_payments,
            kind="currency",
        )
        self._assert_label_value(
            "Total minimum payment for a year",
            expectations.total_yearly_payment,
            kind="currency",
        )
        self._assert_label_value(
            "pay off",
            expectations.time_to_pay,
            kind="years",
        )
        self._assert_label_value(
            "interest paid over time",
            expectations.total_interest_paid,
            kind="currency",
        )
        self._assert_label_value(
            "True cost of debt",
            expectations.total_cost_of_debt,
            kind="currency",
        )

    def assert_needs_and_goals(self, expectations: NtpDisplayExpectations) -> None:
        for need in expectations.applicants_needs:
            self._assert_text_contains(need)
        if expectations.applicants_goals:
            self._assert_text_contains(expectations.applicants_goals)

    def assert_ntp_plan(self, expectations: NtpDisplayExpectations) -> None:
        for plan in (
            expectations.plan_year_one,
            expectations.plan_year_two,
            expectations.plan_year_three,
        ):
            for value in plan.values():
                self._assert_text_contains(value)

    def assert_top_options(self, expectations: NtpDisplayExpectations) -> None:
        for value in (
            expectations.new_option_one,
            expectations.why_option_one,
            expectations.new_option_two,
            expectations.why_option_two,
        ):
            self._assert_text_contains(value)

    def _scroll_to_payment_comparison(self) -> None:
        """Bring payment comparison into view — section may lazy-render below the fold."""
        anchor = self.page.get_by_text(re.compile(r"Mortgage Payment", re.I)).first
        anchor.scroll_into_view_if_needed()
        expect(anchor).to_be_visible(timeout=Config.TIMEOUT)

    def assert_payment_comparison(self, expectations: NtpDisplayExpectations) -> None:
        self._scroll_to_payment_comparison()
        rows = (
            ("Mortgage Payment", expectations.monthly_mortgage_payment, "currency"),
            ("New Solution Payment", expectations.new_solution_payment, "currency"),
            ("Monthly Savings", expectations.estimated_monthly_saving, "currency"),
            ("Total Debt Payments", expectations.current_total_debt, "currency"),
            ("New Debt Payments", expectations.new_debt_payments, "currency"),
            ("Yearly Savings", expectations.yearly_savings_estimate, "currency"),
            ("Combined Payments", expectations.combined_payments, "currency"),
            ("New Monthly Payments", expectations.new_monthly_payments, "currency"),
        )
        for label, expected, kind in rows:
            self._assert_label_value(label, expected, kind=kind)

    def assert_how_client_saves(self, expectations: NtpDisplayExpectations) -> None:
        self._assert_label_value(
            "Appraised Value",
            expectations.appraised_value,
            kind="currency",
        )
        self._assert_label_value(
            "Total Mortgage",
            expectations.total_mortgages,
            kind="currency",
        )
        self._assert_label_value(
            "Remaining Equity",
            expectations.remaining_equity,
            kind="currency",
        )

    def assert_full_presentation(
        self,
        expectations: NtpDisplayExpectations,
        *,
        with_co_borrower: bool,
    ) -> None:
        self.wait_for_presentation()
        self.assert_header(expectations)
        self.assert_profile_cards(expectations, with_co_borrower=with_co_borrower)
        self.assert_true_cost_of_debt(expectations)
        self.assert_needs_and_goals(expectations)
        self.assert_ntp_plan(expectations)
        self.assert_top_options(expectations)
        self.assert_payment_comparison(expectations)
        self.assert_how_client_saves(expectations)

    def assert_pdf_download(self, expected_first_name: str) -> None:
        self.review_label.scroll_into_view_if_needed()
        expect(self.review_checkbox).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.download_pdf_btn).to_be_disabled(timeout=Config.TIMEOUT)
        self.click(self.review_checkbox)
        expect(self.page).not_to_have_url(re.compile(r"/login", re.I), timeout=5000)
        expect(self.download_pdf_btn).to_be_enabled(timeout=Config.TIMEOUT)
        with self.page.expect_download(timeout=60000) as download_info:
            self.click(self.download_pdf_btn)
        download = download_info.value
        filename = download.suggested_filename
        assert expected_first_name.lower() in filename.lower(), (
            f"PDF filename {filename!r} should contain first name {expected_first_name!r}"
        )
