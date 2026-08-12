from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Error, Page, expect
import re
import time

from pages.base_page import BasePage
from test_page_data.approved_data import ApprovedMortgageOptionPrefill
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record
from utils.logger import get_logger
from utils.ms_app_auth import MsAppPipeline
from utils.wait_helpers import wait_for_page_ready

logger = get_logger()

_EXPECT_FAILURES = (AssertionError, Error)


def _ordinal_day(day):
    n = int(day)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


_MONTH_TO_FULL = {
    "Jan": "January",
    "Feb": "February",
    "Mar": "March",
    "Apr": "April",
    "May": "May",
    "Jun": "June",
    "Jul": "July",
    "Aug": "August",
    "Sep": "September",
    "Oct": "October",
    "Nov": "November",
    "Dec": "December",
}


class ApprovedPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        # ===============================
        # Navigation
        # ===============================

        self.my_deals = page.get_by_role("link", name="My Deals")
        self.approved_tab = page.get_by_role("tab", name="Approved", exact=True)
        self.signed_tab = page.get_by_role("tab", name="Signed")

        # ===============================
        # Internal Tabs
        # ===============================

        self.approved_form_tab = page.get_by_role("tab", name="Approved Form")
        self.approved_completed_tab = page.get_by_role(
            "tab", name="Appraisal Completed"
        )

        # ===============================
        # Approved Form — Your Mortgage Option
        # ===============================

        self.approved_loan_amount = page.locator("#approvedLoanAmount")
        self.mortgage_type_combobox = (
            page.locator("label")
            .filter(has_text="Mortgage Type")
            .first.locator("..")
            .get_by_role("combobox")
        )
        self.other_mortgage_type = page.locator("#otherMortgageTypeApproved")
        self.approved_ltv = page.locator("#approvedLtv")
        self.approved_term = page.locator("#approvedTerm")
        self.approved_rate = page.locator("#approvedRate")

        # ===============================
        # Approved Form — Check Your Plan for Accuracy
        # ===============================

        self.name = page.locator("#name")
        self.credit_score = page.locator("#creditScore")
        self.tds_ratio = page.locator("#tdsRatio")
        self.credit_notes = page.locator("#creditNotes")
        self.co_applicant_name = page.locator("#coApplicantName")
        self.co_applicant_credit_score = page.locator("#coApplicantCreditScore")
        self.co_applicant_credit_utilization = page.locator(
            "#coApplicantCreditUtilization"
        )
        self.co_applicant_credit_notes = page.locator("#coApplicantCreditNotes")
        self.current_mortgage_debt_payment = page.locator(
            "#currentMortgageDebtPayment"
        )
        self.average_interest_rate = page.locator("#averageInterestRate")
        self.min_monthly_payments = page.locator("#minMonthlyPayments")
        self.total_yearly_payment = page.locator("#totalYearlyPayment")
        self.time_to_pay = page.locator("#timeToPay")
        self.total_interest_paid = page.locator("#totalInterestPaid")
        self.total_cost_of_debt = page.locator("#totalCostOfDebt")
        self.applicants_needs_one = page.locator("#applicantsNeedsOne")
        self.applicants_needs_two = page.locator("#applicantsNeedsTwo")
        self.applicants_needs_three = page.locator("#applicantsNeedsThree")
        self.applicants_goals = page.locator("#applicantsGoals")

        # ===============================
        # Approved Form — New Tomorrow Plan
        # ===============================

        self.plan_year_one_action_one = page.locator("#planYearOneActionOne")
        self.plan_year_one_action_two = page.locator("#planYearOneActionTwo")
        self.plan_year_one_goals = page.locator("#planYearOneGoals")
        self.plan_year_two_action_one = page.locator("#planYearTwoActionOne")
        self.plan_year_two_action_two = page.locator("#planYearTwoActionTwo")
        self.plan_year_two_goals = page.locator("#planYearTwoGoals")
        self.plan_year_three_action_one = page.locator("#planYearThreeActionOne")
        self.plan_year_three_action_two = page.locator("#planYearThreeActionTwo")
        self.plan_year_three_goals = page.locator("#planYearThreeGoals")

        # ===============================
        # Approved Form — Top Mortgage Options
        # ===============================

        self.new_option_one = page.locator("#newOptionOne")
        self.why_this_option_works = page.locator("#whyThisOptionWorks")
        self.new_option_two = page.locator("#newOptionTwo")
        self.why_this_option_works_best = page.locator("#whyThisOptionWorksBest")
        self.monthly_mortgage_payment = page.locator(
            "#monthlyMortgagePaymentApproved"
        )
        self.new_solution_payment = page.locator("#newSolutionPayment")
        self.estimated_monthly_saving = page.locator("#estimatedMonthlySaving")
        self.current_total_debt = page.locator("#currentTotalDebt")
        self.new_debt_payments = page.locator("#newDebtPayments")
        self.yearly_savings_estimate = page.locator("#yearlySavingsEstimate")
        self.combined_payments = page.locator("#combinedPayments")
        self.new_monthly_payments = page.locator("#newMonthlyPayments")

        # ===============================
        # Approved Form — How Your Client Saves
        # ===============================

        self.appraised_value = page.locator("#appraisedValue")
        self.total_mortgages = page.locator("#totalMortgages")
        self.remaining_equity = page.locator("#remainingEquity")
        self.saving_note_section = page.locator("#savingNoteSection")
        self.commitment_requested_yes = page.locator("#commitmentRequested-yes")
        self.commitment_requested_no = page.locator("#commitmentRequested-no")
        self.conditions_reviewed_yes = page.locator("#conditionsReviewed-yes")
        self.conditions_reviewed_no = page.locator("#conditionsReviewed-no")
        self.submitted_any_other = page.locator("#submittedAnyOther")

        # ===============================
        # Approved Completed — Appraisal Completed
        # ===============================

        self.appraisal_completed_date_btn = (
            page.locator("label:text-is('Appraisal Completed Date')")
            .locator("..")
            .get_by_role("button")
        )
        self.estimated_property_value = page.locator(
            "label:text-is('Estimated Property Value')"
        ).locator("..").locator("input")

        # ===============================
        # Approved Completed — Do You have?
        # ===============================

        self.current_mortgage_statement_checkbox = page.locator("label").filter(
            has_text="Current Mortgage Statement"
        )
        self.current_property_tax_statement_checkbox = page.locator("label").filter(
            has_text="Current Property Tax Statement"
        )
        self.income_documents_checkbox = page.locator("label").filter(
            has_text="Income Documents"
        )
        self.debt_statements_checkbox = page.locator("label").filter(
            has_text="Debt statements to be paid"
        )

        # ===============================
        # Buttons
        # ===============================

        self.ntp_application_btn = page.get_by_role("button", name="NTP Application")
        self.save_btn = page.get_by_role("button", name="Save", exact=True)
        self.close_btn = page.get_by_role("button", name="Close")
        self.complete_stage_btn = page.get_by_role("button", name="Complete Stage")

        self.stage_dialog = page.get_by_role("alertdialog", name="Move to Next Stage?")
        self.stage_cancel_btn = self.stage_dialog.get_by_role("button", name="Cancel")
        self.move_next_btn = self.stage_dialog.get_by_role(
            "button", name="Move to Next Stage"
        )

        # ===============================
        # Toasts
        # ===============================

        self.toast_container = page.locator(
            'section[aria-label="Notifications alt+T"]'
        )
        self.create_success_toast = self.toast_container.get_by_text(
            "Approved information created successfully"
        )
        self.update_success_toast = self.toast_container.get_by_text(
            "Approved information updated successfully"
        )
        self.next_stage_toast = self.toast_container.get_by_text(
            "Lead moved to Signed successfully"
        ).first

    def deal(self, deal_name: str):
        return self.page.get_by_role("link", name=deal_name)

    def open(self):
        self.page.goto(Config.BASE_URL)
        wait_for_page_ready(self.page)

    def open_approved(self, deal_name, bucket=MY_DEALS_BUCKET):
        open_bucket_record(self.page, bucket, deal_name)
        self.click(self.approved_tab)
        self.wait_visible(self.approved_form_tab)

    def verify_approved_form_tab_active(self):
        expect(self.approved_form_tab).to_have_attribute("data-state", "active")

    def verify_approved_completed_tab_disabled(self):
        expect(self.approved_completed_tab).to_be_disabled()

    def verify_approved_completed_tab_enabled(self):
        expect(self.approved_completed_tab).to_be_enabled()

    def verify_approved_completed_tab_active(self):
        """Assert CRM auto-navigated to Appraisal Completed after Approved Form save."""
        expect(self.approved_completed_tab).to_have_attribute(
            "data-state", "active"
        )

    def select_approved_completed_tab(self):
        self.click(self.approved_completed_tab)

    def _fill_locator(self, locator, value: str):
        locator.scroll_into_view_if_needed()
        self.fill(locator, value)

    def fill_credit_score(self, value: str):
        self._fill_locator(self.credit_score, value)

    _APPROVED_FIELD_LOCATORS = {
        "approvedLoanAmount": "approved_loan_amount",
        "approvedLtv": "approved_ltv",
        "approvedTerm": "approved_term",
        "approvedRate": "approved_rate",
        "creditScore": "credit_score",
        "tdsRatio": "tds_ratio",
        "averageInterestRate": "average_interest_rate",
        "coApplicantCreditScore": "co_applicant_credit_score",
        "coApplicantCreditUtilization": "co_applicant_credit_utilization",
        "currentMortgageDebtPayment": "current_mortgage_debt_payment",
    }

    def set_field(self, field: str, value: str):
        locator = getattr(self, self._APPROVED_FIELD_LOCATORS[field])
        self._fill_locator(locator, value)

    def clear_field(self, field: str):
        self.set_field(field, "")

    def clear_all_approved_form_fields(self):
        text_locators = [
            self.approved_loan_amount,
            self.approved_ltv,
            self.approved_term,
            self.approved_rate,
            self.name,
            self.credit_score,
            self.tds_ratio,
            self.credit_notes,
            self.current_mortgage_debt_payment,
            self.average_interest_rate,
            self.min_monthly_payments,
            self.total_yearly_payment,
            self.time_to_pay,
            self.total_interest_paid,
            self.total_cost_of_debt,
            self.applicants_needs_one,
            self.applicants_needs_two,
            self.applicants_needs_three,
            self.applicants_goals,
            self.plan_year_one_action_one,
            self.plan_year_one_action_two,
            self.plan_year_one_goals,
            self.plan_year_two_action_one,
            self.plan_year_two_action_two,
            self.plan_year_two_goals,
            self.plan_year_three_action_one,
            self.plan_year_three_action_two,
            self.plan_year_three_goals,
            self.new_option_one,
            self.why_this_option_works,
            self.new_option_two,
            self.why_this_option_works_best,
            self.monthly_mortgage_payment,
            self.new_solution_payment,
            self.estimated_monthly_saving,
            self.current_total_debt,
            self.new_debt_payments,
            self.yearly_savings_estimate,
            self.combined_payments,
            self.new_monthly_payments,
            self.total_mortgages,
            self.remaining_equity,
            self.saving_note_section,
        ]
        for locator in text_locators:
            locator.scroll_into_view_if_needed()
            self.fill(locator, "")

    def prepare_valid_baseline_for_invalid_tests(self):
        """Fill required approved fields so isolated invalid tests can run."""
        from test_page_data.approved_data import ApprovedFormData

        data = ApprovedFormData()
        self.fill_approved_form(data)

    @staticmethod
    def _normalize_numeric(value: str) -> str:
        return value.replace(",", "").strip()

    def verify_mortgage_option_prefilled(self, prefill=None):
        """
        Verify Your Mortgage Option is prefilled from the Submitted stage
        approved option (approved=yes).

        When prefill is provided (ApprovedMortgageOptionPrefill or
        SubmittedOptionData), values are compared exactly after normalizing
        currency/number formatting. Use the same submitted option instance
        when running Submitted then Approved in one flow.

        When prefill is omitted, verifies all mortgage option fields are
        populated (non-empty) from data saved in a prior Submitted run.
        """
        self.wait_visible(self.approved_loan_amount)

        expect(self.approved_loan_amount).not_to_have_value("")
        expect(self.approved_ltv).not_to_have_value("")
        expect(self.approved_term).not_to_have_value("")
        expect(self.approved_rate).not_to_have_value("")
        expect(self.mortgage_type_combobox).not_to_have_text(
            "Select an option...", use_inner_text=True
        )

        if prefill is None:
            return

        if hasattr(prefill, "mortgage_loan_amount"):
            prefill = ApprovedMortgageOptionPrefill.from_submitted_option(prefill)

        assert self._normalize_numeric(
            self.approved_loan_amount.input_value()
        ) == self._normalize_numeric(prefill.approved_loan_amount)
        expect(self.mortgage_type_combobox).to_contain_text(prefill.mortgage_type)
        assert self._normalize_numeric(
            self.approved_ltv.input_value()
        ) == self._normalize_numeric(prefill.approved_ltv)
        assert self._normalize_numeric(
            self.approved_term.input_value()
        ) == self._normalize_numeric(prefill.approved_term)
        assert self._normalize_numeric(
            self.approved_rate.input_value()
        ) == self._normalize_numeric(prefill.approved_rate)

    def verify_prefilled_from_snapshot(self, expected) -> None:
        """Verify Approved snapshot-driven prefills (Check Your Plan + Top Options)."""
        import re

        def _norm_text(value: str | None) -> str:
            return re.sub(r"\s+", " ", (value or "").strip())

        checks = [
            (self.name, expected.name, _norm_text),
            (self.credit_score, expected.credit_score, self._normalize_numeric),
            (self.tds_ratio, expected.tds_ratio, self._normalize_numeric),
            (self.co_applicant_name, expected.co_applicant_name, _norm_text),
            (
                self.co_applicant_credit_score,
                expected.co_applicant_credit_score,
                self._normalize_numeric,
            ),
            (
                self.co_applicant_credit_utilization,
                expected.co_applicant_credit_utilization,
                self._normalize_numeric,
            ),
            (
                self.average_interest_rate,
                expected.average_interest_rate,
                self._normalize_numeric,
            ),
            (
                self.min_monthly_payments,
                expected.min_monthly_payments,
                self._normalize_numeric,
            ),
            (self.time_to_pay, expected.time_to_pay, self._normalize_numeric),
            (
                self.total_interest_paid,
                expected.total_interest_paid,
                self._normalize_numeric,
            ),
            (self.applicants_needs_one, expected.applicants_needs_one, _norm_text),
            (self.applicants_needs_two, expected.applicants_needs_two, _norm_text),
            (self.applicants_needs_three, expected.applicants_needs_three, _norm_text),
            (self.applicants_goals, expected.applicants_goals, _norm_text),
            (self.new_option_one, expected.new_option_one, _norm_text),
            (self.why_this_option_works, expected.why_this_option_works, _norm_text),
            (self.new_option_two, expected.new_option_two, _norm_text),
            (
                self.why_this_option_works_best,
                expected.why_this_option_works_best,
                _norm_text,
            ),
        ]
        mismatches: list[str] = []
        for locator, expected_value, normalizer in checks:
            if not str(expected_value or "").strip():
                continue
            actual = normalizer(locator.input_value())
            if actual != normalizer(str(expected_value)):
                mismatches.append(
                    f"{locator}: expected {expected_value!r}, got {locator.input_value()!r}"
                )
        assert not mismatches, "Approved snapshot prefill mismatch:\n" + "\n".join(mismatches)

    def fill_approved_form(self, data):
        """
        Fill required Approved Form fields.

        Your Mortgage Option is not filled here — those fields are prefilled
        from the Submitted stage approved option via transformFromSubmittedAndDlo.
        Call verify_mortgage_option_prefilled() after opening the Approved tab.
        """
        self._fill_locator(self.name, data.name)
        self._fill_locator(self.credit_score, data.credit_score)
        self._fill_locator(self.tds_ratio, data.tds_ratio)
        self._fill_locator(self.credit_notes, data.credit_notes)
        self._fill_locator(
            self.current_mortgage_debt_payment, data.current_mortgage_debt_payment
        )
        self._fill_locator(self.average_interest_rate, data.average_interest_rate)
        self._fill_locator(self.min_monthly_payments, data.min_monthly_payments)
        self._fill_locator(self.total_yearly_payment, data.total_yearly_payment)
        self._fill_locator(self.time_to_pay, data.time_to_pay)
        self._fill_locator(self.total_interest_paid, data.total_interest_paid)
        self._fill_locator(self.total_cost_of_debt, data.total_cost_of_debt)
        self._fill_locator(self.applicants_needs_one, data.applicants_needs_one)
        self._fill_locator(self.applicants_needs_two, data.applicants_needs_two)
        self._fill_locator(self.applicants_needs_three, data.applicants_needs_three)
        self._fill_locator(self.applicants_goals, data.applicants_goals)

        self._fill_locator(
            self.plan_year_one_action_one, data.plan_year_one_action_one
        )
        self._fill_locator(
            self.plan_year_one_action_two, data.plan_year_one_action_two
        )
        self._fill_locator(self.plan_year_one_goals, data.plan_year_one_goals)
        self._fill_locator(
            self.plan_year_two_action_one, data.plan_year_two_action_one
        )
        self._fill_locator(
            self.plan_year_two_action_two, data.plan_year_two_action_two
        )
        self._fill_locator(self.plan_year_two_goals, data.plan_year_two_goals)
        self._fill_locator(
            self.plan_year_three_action_one, data.plan_year_three_action_one
        )
        self._fill_locator(
            self.plan_year_three_action_two, data.plan_year_three_action_two
        )
        self._fill_locator(self.plan_year_three_goals, data.plan_year_three_goals)

        self._fill_locator(self.new_option_one, data.new_option_one)
        self._fill_locator(self.why_this_option_works, data.why_this_option_works)
        self._fill_locator(self.new_option_two, data.new_option_two)
        self._fill_locator(
            self.why_this_option_works_best, data.why_this_option_works_best
        )
        self._fill_locator(
            self.monthly_mortgage_payment, data.monthly_mortgage_payment
        )
        self._fill_locator(self.new_solution_payment, data.new_solution_payment)
        self._fill_locator(
            self.estimated_monthly_saving, data.estimated_monthly_saving
        )
        self._fill_locator(self.current_total_debt, data.current_total_debt)
        self._fill_locator(self.new_debt_payments, data.new_debt_payments)
        self._fill_locator(
            self.yearly_savings_estimate, data.yearly_savings_estimate
        )
        self._fill_locator(self.combined_payments, data.combined_payments)
        self._fill_locator(self.new_monthly_payments, data.new_monthly_payments)

        self._fill_locator(self.appraised_value, data.appraised_value)
        self._fill_locator(self.total_mortgages, data.total_mortgages)
        self._fill_locator(self.saving_note_section, data.saving_note_section)

    def save_approved_form(self):
        self.click(self.save_btn)

    def verify_form_saved(self):
        success = self.create_success_toast.or_(self.update_success_toast)
        self.wait_visible(success.first)
        self.verify_visible(success.first)

    def select_date(self, month, year, day):
        self.click(self.appraisal_completed_date_btn)

        calendar = self.page.locator("[data-slot='calendar']")
        calendar.wait_for(state="visible")
        calendar.get_by_label("Choose the Month").select_option(str(month))
        calendar.get_by_label("Choose the Year").select_option(str(year))

        full_month = _MONTH_TO_FULL.get(str(month), str(month))
        day_button = calendar.get_by_role(
            "button",
            name=re.compile(rf"{full_month}.*{_ordinal_day(day)}", re.IGNORECASE),
        ).first
        self.click(day_button)

    def _check_document(self, checkbox_label):
        checkbox_label.scroll_into_view_if_needed()
        checkbox = checkbox_label.get_by_role("checkbox")
        if checkbox.get_attribute("aria-checked") != "true":
            self.click(checkbox)
        
        

    def fill_approved_completed(self, data):
        self.select_date(data.month, data.year, data.day)
       
        self._check_document(self.current_mortgage_statement_checkbox)
        self._check_document(self.current_property_tax_statement_checkbox)
        self._check_document(self.income_documents_checkbox)
        self._check_document(self.debt_statements_checkbox)

    def complete_stage(self):
        self.click(self.complete_stage_btn)

    def cancel_move_to_next_stage(self):
        self.wait_visible(self.stage_dialog)
        self.click(self.stage_cancel_btn)

    def move_to_next_stage(self):
        self.wait_visible(self.stage_dialog)
        self.click(self.move_next_btn)

    def verify_moved_to_signed(self):
        from utils.stage_transition_verification import verify_immediate_stage_move

        verify_immediate_stage_move(
            self.page,
            success_toast="Lead moved to Signed successfully",
            url_tab="signed",
            active_tab=self.signed_tab,
        )

    def capture_approved_form_values(self) -> dict[str, str]:
        """Read editable approved-form fields saved in the happy path."""
        capture_map = {
            "name": self.name,
            "creditScore": self.credit_score,
            "tdsRatio": self.tds_ratio,
            "creditNotes": self.credit_notes,
            "currentMortgageDebtPayment": self.current_mortgage_debt_payment,
            "averageInterestRate": self.average_interest_rate,
            "minMonthlyPayments": self.min_monthly_payments,
            "totalYearlyPayment": self.total_yearly_payment,
            "timeToPay": self.time_to_pay,
            "totalInterestPaid": self.total_interest_paid,
            "totalCostOfDebt": self.total_cost_of_debt,
            "applicantsNeedsOne": self.applicants_needs_one,
            "applicantsNeedsTwo": self.applicants_needs_two,
            "applicantsNeedsThree": self.applicants_needs_three,
            "applicantsGoals": self.applicants_goals,
            "planYearOneActionOne": self.plan_year_one_action_one,
            "planYearOneActionTwo": self.plan_year_one_action_two,
            "planYearOneGoals": self.plan_year_one_goals,
            "planYearTwoActionOne": self.plan_year_two_action_one,
            "planYearTwoActionTwo": self.plan_year_two_action_two,
            "planYearTwoGoals": self.plan_year_two_goals,
            "planYearThreeActionOne": self.plan_year_three_action_one,
            "planYearThreeActionTwo": self.plan_year_three_action_two,
            "planYearThreeGoals": self.plan_year_three_goals,
            "newOptionOne": self.new_option_one,
            "whyThisOptionWorks": self.why_this_option_works,
            "newOptionTwo": self.new_option_two,
            "whyThisOptionWorksBest": self.why_this_option_works_best,
            "monthlyMortgagePaymentApproved": self.monthly_mortgage_payment,
            "newSolutionPayment": self.new_solution_payment,
            "estimatedMonthlySaving": self.estimated_monthly_saving,
            "currentTotalDebt": self.current_total_debt,
            "newDebtPayments": self.new_debt_payments,
            "yearlySavingsEstimate": self.yearly_savings_estimate,
            "combinedPayments": self.combined_payments,
            "newMonthlyPayments": self.new_monthly_payments,
            "appraisedValue": self.appraised_value,
            "totalMortgages": self.total_mortgages,
            "remainingEquity": self.remaining_equity,
            "savingNoteSection": self.saving_note_section,
            "coApplicantName": self.co_applicant_name,
            "coApplicantCreditNotes": self.co_applicant_credit_notes,
        }
        return {
            key: locator.input_value()
            for key, locator in capture_map.items()
            if locator.count() > 0
        }

    def reopen_approved_form_tab(self) -> None:
        self.click(self.approved_tab)
        expect(self.approved_tab).to_have_attribute("data-state", "active", timeout=30000)
        self.click(self.approved_form_tab)
        expect(self.approved_form_tab).to_have_attribute("data-state", "active", timeout=30000)

    def reopen_approved_completed_tab(self) -> None:
        self.click(self.approved_tab)
        expect(self.approved_tab).to_have_attribute("data-state", "active", timeout=30000)
        self.click(self.approved_completed_tab)
        expect(self.approved_completed_tab).to_have_attribute(
            "data-state", "active", timeout=30000
        )

    def wait_for_ntp_application_enabled(
        self, *, timeout_ms: int | None = None
    ) -> None:
        """Wait for NTP Application to enable after auth session hydrates."""
        total_ms = timeout_ms or min(Config.NTP_APP_LEAD_SYNC_TIMEOUT_MS, 90000)
        deadline = time.monotonic() + total_ms / 1000
        last_error: BaseException | None = None
        while time.monotonic() < deadline:
            self.reopen_approved_form_tab()
            remaining_ms = max(2000, int((deadline - time.monotonic()) * 1000))
            try:
                expect(self.ntp_application_btn).to_be_enabled(
                    timeout=min(remaining_ms, 15000)
                )
                return
            except _EXPECT_FAILURES as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("NTP Application button did not become enabled")

    def _ntp_button_is_enabled(self, *, timeout_ms: int = 15000) -> bool:
        try:
            expect(self.ntp_application_btn).to_be_enabled(timeout=timeout_ms)
            return True
        except _EXPECT_FAILURES:
            return False

    def open_ntp_application(
        self,
        context: BrowserContext,
        *,
        browser: Browser | None = None,
        pipeline: MsAppPipeline | None = None,
    ) -> Page:
        """Open NTP App in a new tab via CRM footer button or staff URL fallback."""
        from utils.ntp_app_auth import open_ntp_app_via_staff_url

        resolved_browser = browser or context.browser
        resolved_pipeline: MsAppPipeline = pipeline or "admin"
        self.reopen_approved_form_tab()

        if self._ntp_button_is_enabled(timeout_ms=15000):
            with context.expect_page() as new_page_info:
                self.click(self.ntp_application_btn)
            app_page: Page = new_page_info.value
            app_page.set_default_timeout(Config.TIMEOUT)
            app_page.wait_for_load_state("domcontentloaded")
            app_page.wait_for_url(re.compile(r".*/leads(?:\?.*)?$"), timeout=60000)
            return app_page

        if resolved_browser is not None:
            logger.warning(
                "NTP Application button disabled; opening via staff URL fallback"
            )
            return open_ntp_app_via_staff_url(
                context, resolved_browser, pipeline=resolved_pipeline
            )

        self.wait_for_ntp_application_enabled()
        with context.expect_page() as new_page_info:
            self.click(self.ntp_application_btn)
        app_page = new_page_info.value
        app_page.set_default_timeout(Config.TIMEOUT)
        app_page.wait_for_load_state("domcontentloaded")
        app_page.wait_for_url(re.compile(r".*/leads(?:\?.*)?$"), timeout=60000)
        return app_page
