from __future__ import annotations

import re
from typing import Literal

from playwright.sync_api import expect

from pages.base_page import BasePage
from test_page_data.approved_data import ApprovedMortgageOptionPrefill
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record
from utils.wait_helpers import wait_for_page_ready



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


class SignedPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        # ===============================
        # Navigation
        # ===============================

        self.my_deals = page.get_by_role("link", name="My Deals")
        self.compliance_link = page.get_by_role("link", name="Compliance")
        self.signed_tab = page.get_by_role("tab", name="Signed")
        self.approved_tab = page.get_by_role("tab", name="Approved", exact=True)
        self.submitted_tab = page.get_by_role("tab", name="Submitted")
        self.not_signed_tab = page.get_by_role("tab", name="Not Signed")
        self.global_search = page.get_by_role(
            "textbox", name=re.compile("Search leads", re.I)
        )

        # ===============================
        # Section headings
        # ===============================

        self.signed_documents_title = page.get_by_text(
            "Signed Documents & Loan Details", exact=True
        )
        self.client_signed_heading = page.get_by_role(
            "heading", name="Did Your Client Sign?"
        )
        self.final_product_heading = page.get_by_role(
            "heading", name="Is this the final product?"
        )
        self.deal_tracking_heading = page.get_by_role(
            "heading", name="Deal Tracking"
        )
        self.financial_profile_heading = page.get_by_role(
            "heading", name="Client Financial Profile"
        )
        self.important_notes_heading = page.get_by_role(
            "heading", name="Important Client Notes"
        )
        self.google_review_title = page.get_by_text("Google Review", exact=True)

        # ===============================
        # Did Your Client Sign?
        # ===============================

        self.client_signed_yes = page.locator("#clientSigned-yes")
        self.client_signed_no = page.locator("#clientSigned-no")
        self.not_signed_reason = page.locator("#notSignedReason")

        # ===============================
        # Signed Details (prefilled)
        # ===============================

        self.loan_amount_approved = page.locator("#loanAmountApproved")
        self.signed_mortgage_type_combobox = (
            page.locator("label")
            .filter(has_text="Mortgage Type")
            .first.locator("..")
            .get_by_role("combobox")
        )
        self.other_mortgage_type = page.locator("#otherMortgageTypeApproved")
        self.approved_term = page.locator("#approvedTerm")
        self.approved_ltv = page.locator("#approvedLTV")
        self.approved_rate = page.locator("#approvedRate")
        self.lender_name = page.locator("#lenderName")

        # ===============================
        # Final Product
        # ===============================

        self.final_product_yes = page.locator("#finalProduct-yes")
        self.final_product_no = page.locator("#finalProduct-no")
        self.deal_disposition_dead_marketing = page.locator(
            "#dealDisposition-dead_marketing"
        )
        self.deal_disposition_resigning = page.locator(
            "#dealDisposition-resigning_submitted"
        )

        # ===============================
        # Deal Tracking
        # ===============================

        #  self.signed_date_btn = (
        #     page.locator("label:text-is('Signed Date')")
        #     .locator("..")
        #     .get_by_role("button")
        # )
        # self.date_signs_back_btn = (
        #     page.locator("label:text-is('Date Signs Back to Lender')")
        #     .locator("..")
        #     .get_by_role("button")
        # )
        # self.closing_email_btn = (
        #     page.locator("label:text-is('Closing Email Sent to Lender')")
        #     .locator("..")
        #     .get_by_role("button")

        self.signed_date_btn = self._date_picker_button("Signed Date")
        self.date_signs_back_btn = self._date_picker_button("Date Signs Back to Lender")
        self.closing_email_btn = self._date_picker_button(
            "Closing Email Sent to Lender"
        )
        self.client_lawyer_combobox = (
            page.locator("label")
            .filter(has_text="Client Lawyer")
            .locator("..")
            .get_by_role("combobox")
        )
        self.important_notes_client_care = page.locator(
            "#importantNotesForClientCare"
        )
        self.home_appraisal_yes = page.locator("#homeAppraisal-yes")
        self.home_appraisal_no = page.locator("#homeAppraisal-no")
        self.credit_card_statement_yes = page.locator("#creditCardStatement-yes")
        self.credit_card_statement_no = page.locator("#creditCardStatement-no")
        self.valid_photo_id_yes = page.locator("#validPhotoId-yes")
        self.valid_photo_id_no = page.locator("#validPhotoId-no")
        self.conditioned_documents_yes = page.locator("#conditionedDocuments-yes")
        self.conditioned_documents_no = page.locator("#conditionedDocuments-no")
        self.secondary_id_yes = page.locator("#secondaryId-yes")
        self.secondary_id_no = page.locator("#secondaryId-no")
        self.retainer_fees_yes = page.locator("#retainerFees-yes")
        self.retainer_fees_no = page.locator("#retainerFees-no")
        self.home_inspection_yes = page.locator("#homeInspection-yes")
        self.home_inspection_no = page.locator("#homeInspection-no")
        self.outstanding_condition_yes = page.locator("#outstandingCondition-yes")
        self.outstanding_condition_no = page.locator("#outstandingCondition-no")
        self.outstanding_conditions_details = page.locator("#outstandingConditions")


        self.date_instructed_lender_lawyer_btn = self._date_picker_button(
            "Date Instructed to Lenders Lawyer"
        )

        self.ilr_meeting_btn = self._date_picker_button("ILR Meeting Appointment")
        self.date_instructed_borrower_lawyer_btn = self._date_picker_button(
            "Date Instructed to Borrower's Lawyer"
        )

        self.anticipated_closing_btn = self._date_picker_button(
            "Anticipated Deal Closing Date"
        )

        # ===============================
        # Client Financial Profile
        # ===============================

        self.lender_fee = page.locator("#lenderFee")
        self.lender_bps = page.locator("#lenderBps")
        self.broker_fee = page.locator("#brokerFee")
        self.admin_fee = page.locator("#adminFee")
        self.appraisal_rebate = page.locator("#appraisalRebate")
        self.lawyer_fee = page.locator("#lawyerFee")

        # ===============================
        # Important Client Notes
        # ===============================

        self.trust_ledger_review_yes = page.locator("#trustLedgerReview-yes")
        self.trust_ledger_review_no = page.locator("#trustLedgerReview-no")
        self.additional_notes = page.locator("#additionalNotes")

        # ===============================
        # Google Review
        # ===============================

        self.good_for_google_review_yes = page.locator("#goodForGoogleReview-yes")
        self.good_for_google_review_no = page.locator("#goodForGoogleReview-no")
        self.reason_no_google_review = page.locator("#reasonForNoGoogleReview")
        self.is_closed_checkbox = page.locator("#is-closed")
        self.is_closed_label = page.locator('label[for="is-closed"]')

        # ===============================
        # Buttons
        # ===============================

        self.signed_save_btn = (
            page.locator("form")
            .filter(has=self.signed_documents_title)
            .get_by_role("button", name="Save")
        )
        self.google_review_save_btn = (
            page.locator("form")
            .filter(has=self.google_review_title)
            .get_by_role("button", name="Save")
        )

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
        self.signed_create_toast = self.toast_container.get_by_text(
            "Signed data saved successfully"
        ).first
        self.signed_update_toast = self.toast_container.get_by_text(
            "Signed data updated successfully"
        ).first
        self.moved_to_signed_toast = self.toast_container.get_by_text(
            "Lead moved to Signed successfully"
        ).first
        self.moved_to_not_signed_toast = self.toast_container.get_by_text(
            "Lead moved to Not Signed successfully"
        ).first
        self.moved_to_submitted_toast = self.toast_container.get_by_text(
            "Lead moved to Submitted successfully"
        ).first
        self.moved_to_marketing_toast = self.toast_container.get_by_text(
            "Lead moved to Marketing successfully"
        ).first
        self.google_review_saved_toast = self.toast_container.get_by_text(
            "Google review saved successfully"
        ).first
        self.google_review_error_toast = self.toast_container.get_by_text(
            re.compile(r"Failed to save Google review", re.I)
        ).first

        #===================
        # compliance dialog
        #===================
        self.compliance_dialog = self.page.get_by_role("alertdialog").filter(has_text="Lead moved to Compliance")
        self.compliance_dialog_ok_btn = self.compliance_dialog.get_by_role("button", name="OK")

        #=====================
        #Lead Signed
        #=====================
        self.lead_note_heading = page.get_by_role("heading", name="Lead Notes")
        self.profile_tab = page.get_by_role("tab", name="Profile", exact=True)
        self.notes_tab = page.get_by_role("tab", name="Notes", exact=True)

    def deal(self, deal_name: str):
        return self.page.get_by_role("link", name=deal_name)

    def _date_picker_button(self, label: str):
        """Locate a date-picker trigger by field label (safe for apostrophes)."""
        return (
            self.page.locator("label")
            .filter(has_text=re.compile(rf"^{re.escape(label)}\b", re.I))
            .locator("..")
            .get_by_role("button")
        )

    def open(self):
        self.page.goto(
            Config.BASE_URL,
            wait_until="domcontentloaded",
            timeout=Config.TIMEOUT,
        )
        try:
            self.page.wait_for_load_state("networkidle", timeout=Config.TIMEOUT)
        except Exception:
            # SPA pages may never reach networkidle; domcontentloaded is sufficient.
            wait_for_page_ready(self.page)
            # pass

    def open_signed(self, deal_name: str, bucket=MY_DEALS_BUCKET):
        open_bucket_record(self.page, bucket, deal_name)
        self.ensure_signed_form()

    def ensure_signed_form(self) -> None:
        """Activate Signed tab and wait until client-signed controls are ready."""
        if "tab=signed" not in self.page.url:
            self.click(self.signed_tab)
        expect(self.signed_tab).to_have_attribute("data-state", "active", timeout=30000)
        expect(self.page).to_have_url(re.compile(r"tab=signed"), timeout=30000)
        self.wait_visible(self.signed_documents_title)
        loading = self.page.get_by_text(re.compile(r"Loading signed data", re.I))
        if loading.count() > 0:
            expect(loading.first).to_be_hidden(timeout=30000)
        expect(self.client_signed_no).to_be_visible(timeout=30000)

    def open_deal(self, deal_name: str, bucket=MY_DEALS_BUCKET):
        open_bucket_record(self.page, bucket, deal_name)

    @staticmethod
    def _normalize_numeric(value: str) -> str:
        return value.replace(",", "").strip()

    def _fill_locator(self, locator, value: str):
        locator.scroll_into_view_if_needed()
        self.fill(locator, value)

    def _click_radio(self, locator):
        locator.scroll_into_view_if_needed()
        self.click(locator)

    def select_date(self, trigger, month, year, day):
        self.click(trigger)
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

    def _fill_all_dates(self, data):
        date_fields = [
            self.signed_date_btn,
            self.date_signs_back_btn,
            self.closing_email_btn,
            self.date_instructed_lender_lawyer_btn,
            self.ilr_meeting_btn,
            self.date_instructed_borrower_lawyer_btn,
            self.anticipated_closing_btn,
        ]
        for trigger in date_fields:
            self.select_date(trigger, data.month, data.year, data.day)

    def _select_first_lawyer(self):
        self.click(self.client_lawyer_combobox)
        first = self.page.get_by_role("option").first
        first.wait_for(state="visible")
        self.click(first)

    def _select_yes_for_deal_tracking_radios(self):
        radios = [
            self.home_appraisal_yes,
            self.credit_card_statement_yes,
            self.valid_photo_id_yes,
            self.conditioned_documents_yes,
            self.secondary_id_yes,
            self.retainer_fees_yes,
            self.home_inspection_yes,
        ]
        for radio in radios:
            self._click_radio(radio)

    # ===============================
    # Verifications — visibility
    # ===============================

    def verify_client_signed_yes_selected(self):
        expect(self.client_signed_yes).to_be_checked()

    def verify_final_product_section_visible(self):
        self.verify_visible(self.final_product_heading)

    def verify_final_product_section_hidden(self):
        expect(self.final_product_heading).to_be_hidden()

    def verify_deal_tracking_sections_visible(self):
        self.verify_visible(self.deal_tracking_heading)
        self.verify_visible(self.financial_profile_heading)
        self.verify_visible(self.important_notes_heading)

    def verify_deal_tracking_sections_hidden(self):
        expect(self.deal_tracking_heading).to_be_hidden()
        expect(self.financial_profile_heading).to_be_hidden()
        expect(self.important_notes_heading).to_be_hidden()

    def verify_not_signed_reason_visible(self):
        self.verify_visible(self.not_signed_reason)

    def verify_not_signed_reason_hidden(self):
        expect(self.not_signed_reason).to_be_hidden()

    def verify_outstanding_conditions_details_visible(self):
        self.verify_visible(self.outstanding_conditions_details)

    def verify_outstanding_conditions_details_hidden(self):
        expect(self.outstanding_conditions_details).to_be_hidden()

    def verify_signed_tab_hidden(self):
        expect(self.signed_tab).to_be_hidden()

    def verify_signed_tab_visible(self):
        expect(self.signed_tab).to_be_visible()

    def verify_google_review_visible(self):
        self.verify_visible(self.google_review_title)

    def verify_on_my_deals(self):
        expect(self.page).to_have_url(re.compile(r"/sales/?$"))

    # ===============================
    # Verifications — prefilled data
    # ===============================

    def verify_signed_details_prefilled(self, prefill=None):
        self.wait_visible(self.loan_amount_approved)
        expect(self.loan_amount_approved).not_to_have_value("")
        expect(self.approved_ltv).not_to_have_value("")
        expect(self.approved_term).not_to_have_value("")
        expect(self.approved_rate).not_to_have_value("")
        expect(self.signed_mortgage_type_combobox).not_to_have_text(
            "Select an option...", use_inner_text=True
        )

        if prefill is None:
            return

        if hasattr(prefill, "mortgage_loan_amount"):
            prefill = ApprovedMortgageOptionPrefill.from_submitted_option(prefill)

        assert self._normalize_numeric(
            self.loan_amount_approved.input_value()
        ) == self._normalize_numeric(prefill.approved_loan_amount)
        expect(self.signed_mortgage_type_combobox).to_contain_text(
            prefill.mortgage_type
        )
        assert self._normalize_numeric(
            self.approved_ltv.input_value()
        ) == self._normalize_numeric(prefill.approved_ltv)
        assert self._normalize_numeric(
            self.approved_term.input_value()
        ) == self._normalize_numeric(prefill.approved_term)
        assert self._normalize_numeric(
            self.approved_rate.input_value()
        ) == self._normalize_numeric(prefill.approved_rate)

    def verify_lender_name_prefilled(self):
        expect(self.lender_name).not_to_have_value("")

    # ===============================
    # Client Signed actions
    # ===============================

    def select_client_signed_yes(self):
        self._click_radio(self.client_signed_yes)

    def select_client_signed_no(self):
        self._click_radio(self.client_signed_no)

    def fill_not_signed_reason(self, reason: str):
        self._fill_locator(self.not_signed_reason, reason)

    # ===============================
    # Final Product actions
    # ===============================

    def select_final_product_yes(self):
        self._click_radio(self.final_product_yes)

    def select_final_product_no(self):
        self._click_radio(self.final_product_no)

    def select_resigning_back_to_submitted(self):
        self._click_radio(self.deal_disposition_resigning)

    def select_dead_move_to_marketing(self):
        self._click_radio(self.deal_disposition_dead_marketing)

    # ===============================
    # Deal Tracking actions
    # ===============================

    def select_outstanding_condition_yes(self):
        self._click_radio(self.outstanding_condition_yes)

    def select_outstanding_condition_no(self):
        self._click_radio(self.outstanding_condition_no)

    def fill_outstanding_conditions_details(self, text: str):
        self._fill_locator(self.outstanding_conditions_details, text)

    _SIGNED_FIELD_LOCATORS = {
        "approvedLTV": "approved_ltv",
        "approvedTerm": "approved_term",
        "approvedRate": "approved_rate",
        "outstandingConditions": "outstanding_conditions_details",
    }

    def set_field(self, field: str, value: str):
        locator = getattr(self, self._SIGNED_FIELD_LOCATORS[field])
        self._fill_locator(locator, value)

    def clear_field(self, field: str):
        self.set_field(field, "")

    def prepare_yes_final_product_for_invalid(self):
        self.select_client_signed_yes()
        self.select_final_product_yes()
        self.select_outstanding_condition_yes()
        self.set_field(
            "outstandingConditions",
            "Valid baseline outstanding conditions text.",
        )

    def fill_final_product_yes_sections(self, data):
        self._fill_all_dates(data)
        self._select_first_lawyer()
        self._fill_locator(self.important_notes_client_care, data.important_notes)
        self._select_yes_for_deal_tracking_radios()
        self._click_radio(self.outstanding_condition_no)
        self._fill_locator(self.lender_fee, data.lender_fee)
        self._fill_locator(self.lender_bps, data.lender_bps)
        self._fill_locator(self.broker_fee, data.broker_fee)
        self._fill_locator(self.admin_fee, data.admin_fee)
        self._fill_locator(self.appraisal_rebate, data.appraisal_rebate)
        self._fill_locator(self.lawyer_fee, data.lawyer_fee)
        self._click_radio(self.trust_ledger_review_yes)
        self._fill_locator(self.additional_notes, data.additional_notes)

    # ===============================
    # Save / stage / toasts
    # ===============================

    def capture_signed_yes_values(self) -> dict[str, str]:
        """Read signed final-product-yes fields for persistence verification."""
        values = {
            "importantNotesClientCare": self.important_notes_client_care.input_value(),
            "lenderFee": self.lender_fee.input_value(),
            "lenderBps": self.lender_bps.input_value(),
            "brokerFee": self.broker_fee.input_value(),
            "adminFee": self.admin_fee.input_value(),
            "appraisalRebate": self.appraisal_rebate.input_value(),
            "lawyerFee": self.lawyer_fee.input_value(),
            "additionalNotes": self.additional_notes.input_value(),
        }
        for label, key in (
            ("Signed Date", "signedDate"),
            ("Date Signs Back to Lender", "dateSignsBackToLender"),
            ("Closing Email Sent to Lender", "closingEmailSentToLender"),
            ("Date Instructed to Lenders Lawyer", "dateInstructedLenderLawyer"),
            ("ILR Meeting Appointment", "ilrMeetingAppointment"),
            ("Date Instructed to Borrower's Lawyer", "dateInstructedBorrowerLawyer"),
            ("Anticipated Deal Closing Date", "anticipatedDealClosingDate"),
        ):

            button = self._date_picker_button(label)
            if button.count() > 0 and button.is_visible():
                values[key] = " ".join(button.inner_text().split())
        return values

    def reopen_signed_tab(self) -> None:
        self.click(self.signed_tab)
        expect(self.signed_tab).to_have_attribute("data-state", "active", timeout=30000)
        expect(self.page).to_have_url(re.compile(r"tab=signed"), timeout=30000)

    def save_signed_form(self):
        self.click(self.signed_save_btn)

    def save_google_review(
        self,
        *,
        expect_compliance_move: bool = False,
        role: Literal["admin", "agent"] = "admin",
    ) -> None:
        self.wait_for_google_review_form_idle()
        self.click(self.google_review_save_btn)

        if not expect_compliance_move:
            outcome = self.google_review_saved_toast.or_(self.google_review_error_toast)
            expect(outcome.first).to_be_visible(timeout=Config.TIMEOUT)
            return

        outcome = self.compliance_dialog.or_(self.google_review_error_toast)
        expect(outcome.first).to_be_visible(timeout=Config.TIMEOUT)

    def verify_signed_saved(self):
        success = self.signed_create_toast.or_(self.signed_update_toast)
        self.wait_visible(success.first)
        self.verify_visible(success.first)

    def verify_google_review_saved(self):
        """After isClosed=false save — toast and form ready for a second edit."""
        self.wait_visible(self.google_review_saved_toast)
        self.verify_visible(self.google_review_saved_toast)


        self.wait_for_google_review_form_idle()
        expect(self.page).to_have_url(re.compile(r"tab=signed"))
        expect(self.signed_tab).to_have_attribute("data-state", "active")


    def wait_for_google_review_form_idle(self, timeout: int | None = None) -> None:
        """Wait until Google Review mutation finished and the form is interactive."""
        timeout = timeout or Config.TIMEOUT
        if self.compliance_dialog.is_visible():
            return
        save_btn = self.google_review_save_btn
        if save_btn.count() == 0:
            return
        expect(save_btn).to_be_visible(timeout=timeout)
        expect(save_btn).to_be_enabled(timeout=timeout)
        expect(save_btn).not_to_have_text(re.compile(r"Saving", re.I), timeout=timeout)

    def move_to_next_stage(self): 
        self.wait_visible(self.stage_dialog)
        self.click(self.move_next_btn)

    def verify_moved_to_not_signed(self): 
        self.wait_visible(self.moved_to_not_signed_toast)
        self.verify_visible(self.moved_to_not_signed_toast)


    def verify_moved_to_signed_stage(self):
        self.wait_visible(self.moved_to_signed_toast)
        self.verify_visible(self.moved_to_signed_toast)
        expect(self.signed_tab).to_have_attribute("data-state", "active")

    def verify_moved_to_approved(self): 
        self.wait_visible(self.moved_to_submitted_toast)
        self.verify_visible(self.moved_to_submitted_toast)

        self.wait_visible(self.approved_tab)
        expect(self.page).to_have_url(re.compile(r"tab=approved"), timeout=Config.TIMEOUT)

    def verify_moved_to_marketing(self): 
        try:
            expect(self.moved_to_marketing_toast).to_be_visible(timeout=20000)
            return
        except AssertionError:
            pass
        expect(self.page).to_have_url(
            self._sales_bucket_list_url_pattern(),
            timeout=Config.TIMEOUT,
        )

    def verify_outstanding_conditions_min_length_error(self):
        expect(
            self.page.get_by_text(
                "Outstanding conditions must be at least 30 characters"
            )
        ).to_be_visible()

    # ===============================
    # Google Review
    # ===============================

    def select_good_for_google_review_yes(self):
        self._click_radio(self.good_for_google_review_yes)

    def _is_closed_checked(self) -> bool:
        checkbox = self.is_closed_checkbox
        aria = checkbox.get_attribute("aria-checked")
        if aria in ("true", "false"):
            return aria == "true"
        return checkbox.get_attribute("data-state") == "checked"

    def set_closed_checked(self, checked: bool = True):
        """Toggle the Radix isClosed checkbox in the Google Review form."""
        self.wait_for_google_review_form_idle()
        checkbox = self.is_closed_checkbox
        label = self.is_closed_label
        expect(checkbox).to_be_visible(timeout=Config.TIMEOUT)
        expect(checkbox).to_be_enabled(timeout=Config.TIMEOUT)
        checkbox.scroll_into_view_if_needed()

        desired = "true" if checked else "false"
        if self._is_closed_checked() != checked:
            label.click()
        if self._is_closed_checked() != checked:
            checkbox.click(force=True)
        expect(checkbox).to_have_attribute("aria-checked", desired, timeout=Config.TIMEOUT)

    def verify_still_on_signed_tab(self):
        expect(self.page).to_have_url(re.compile(r"tab=signed"))
        expect(self.signed_tab).to_have_attribute("data-state", "active")

    def verify_not_on_signed_tab(self):
        expect(self.signed_tab).not_to_have_attribute("data-state", "active")

    # ===============================
    # Compliance
    # ===============================

    def _raise_google_review_error_if_visible(self) -> None:
        if not self.google_review_error_toast.is_visible():
            return
        message = re.sub(r"\s+", " ", self.google_review_error_toast.inner_text()).strip()
        raise AssertionError(f"Google review save failed: {message}")

    def wait_for_agent_compliance_move(self) -> None:
        """Agent isClosed=true save — stay on lead detail with Profile/Notes only."""
        self._raise_google_review_error_if_visible()
        if self.compliance_dialog.is_visible():
            self.compliance_dialog_ok_btn.click()
            expect(self.compliance_dialog).to_be_hidden(timeout=Config.TIMEOUT)
        expect(self.profile_tab).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.notes_tab).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.signed_tab).to_have_count(0, timeout=Config.TIMEOUT)
        expect(self.page).to_have_url(
            re.compile(r"/(sales|sales-backend)/[A-Za-z0-9]+"),
            timeout=Config.TIMEOUT,
        )

    def verify_agent_compliance_move_view(self) -> None:
        """Agent session: dismiss Compliance dialog, then Profile/Notes only."""
        self.wait_for_agent_compliance_move()

    def _sales_bucket_list_url_pattern(self) -> re.Pattern[str]:
        """List URL after ComplianceMoveDialog OK (FE → /sales, BE → /sales-backend)."""
        if "/sales-backend" in self.page.url:
            return re.compile(r"/sales-backend(?:/)?(?:\?[^/]*)?$")
        return re.compile(r"/sales(?:/)?(?:\?[^/]*)?$")


    def complete_admin_compliance_move(self) -> None:
        """Admin isClosed=true save — Compliance dialog then kanban list redirect."""
        self._raise_google_review_error_if_visible()
        expect(self.compliance_dialog).to_be_visible(timeout=Config.TIMEOUT)
        self.compliance_dialog_ok_btn.click()
        expect(self.compliance_dialog).to_be_hidden(timeout=Config.TIMEOUT)
        expect(self.page).to_have_url(
            self._sales_bucket_list_url_pattern(),
            timeout=Config.TIMEOUT,
        )

    def complete_agent_compliance_move(self) -> None:
        """Agent isClosed=true save — OK on Compliance dialog, then Profile/Notes view."""
        self._raise_google_review_error_if_visible()
        expect(self.compliance_dialog).to_be_visible(timeout=Config.TIMEOUT)
        self.compliance_dialog_ok_btn.click()
        expect(self.compliance_dialog).to_be_hidden(timeout=Config.TIMEOUT)
        self.wait_for_agent_compliance_move()

    def complete_google_review_compliance_move(
        self,
        *,
        role: Literal["admin", "agent"] = "admin",
    ) -> None:
        if role == "admin":
            self.complete_admin_compliance_move()
        else:
            self.complete_agent_compliance_move()

    def compliance_dialog_ok(self) -> None:
        """Backward-compatible alias for admin compliance move."""
        self.complete_admin_compliance_move()

    def verify_lead_note_heading_visible(self):
        self.verify_visible(self.lead_note_heading)

    def open_compliance_and_search_deal(self, deal_name: str):
        self.click(self.compliance_link)
        self.page.wait_for_load_state("networkidle")
        self.fill(self.global_search, deal_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.get_by_text(deal_name).first).to_be_visible()

    def verify_deal_in_compliance(self, deal_name: str):
        expect(self.page.get_by_text(deal_name).first).to_be_visible()




