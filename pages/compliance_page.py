import re
from dataclasses import asdict

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.signed_page import SignedPage
from test_page_data.compliance_data import SignedFormSnapshot
from utils.config import Config


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

_COMPLIANCE_PATH = "/compliance"
_CLIENT_CARE_PATH = "/client-care"
_SIGNED_FORM_SECTION_TITLES = (
    "Please Review Your Client Profile",
    "Client Financial Profile",
    "Important Client Notes",
)


class CompliancePage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        # ===============================
        # Navigation
        # ===============================

        self.compliance_link = page.get_by_role("link", name="Compliance")
        self.client_care_link = page.get_by_role("link", name="Client Care")
        self.list_search = page.locator('[name="list-global-search"]')
        self.global_search = page.get_by_role(
            "textbox", name=re.compile("Search leads", re.I)
        )

        self.signed_closed_tab = page.get_by_role("tab", name="Signed Closed")
        self.main_signed_tab = page.get_by_role("tab", name="Signed", exact=True)

        self.compliance_form_tab = page.get_by_role("tab", name="Compliance Form")
        self.signed_form_tab = page.get_by_role("tab", name="Signed Form").first

        self.compliance_card_title = page.get_by_text("Compliance", exact=True).first
        self.closing_compliance_heading = page.get_by_role(
            "heading", name="Closing - Compliance"
        )
        self.client_care_checks_heading = page.get_by_role(
            "heading", name="Important Checks to Move into Client Care"
        )
        self.signed_profile_heading = page.get_by_text(
            "Please Review Your Client Profile", exact=True
        ).first

        # ===============================
        # Closing Compliance fields
        # ===============================

        self.credit_score = page.locator("#creditScoreForMainApplicant")
        self.total_debt_ratio = page.locator("#totalDebtRatio")
        self.loan_to_value = page.locator("#loanToValuePercent")
        self.finder_fee_percent = page.locator("#finderFeePercent")
        self.volume_bonus = page.locator("#volumeBonus")
        self.broker_fee = page.locator("#brokerFee")
        self.underwriting_fee = page.locator("#underwritingFee")
        self.net_fee = page.locator("#netFee")
        self.expense_deducted = page.locator("#expenseDeducted")
        self.other_expenses = page.locator("#otherExpenses")
        self.referral_fee = page.locator("#referralFee")
        self.appraisal_expense = page.locator("#appraisalExpense")
        self.uw_fee = page.locator("#uwFee")
        self.internal_agent_fee_a = page.locator("#internalAgentFeeA")
        self.internal_agent_fee_b = page.locator("#internalAgentFeeB")
        self.af = page.locator("#af")
        self.ff = page.locator("#ff")
        self.insurer = page.locator("#insurer")

        self.mpp_yes = page.locator("#mpp-true")
        self.mpp_no = page.locator("#mpp-false")
        self.high_ratio_yes = page.locator("#highRatio-true")
        self.high_ratio_no = page.locator("#highRatio-false")
        self.conventional_yes = page.locator("#conventional-true")
        self.conventional_no = page.locator("#conventional-false")
        self.cmhc_yes = page.locator("#cmhc-true")
        self.cmhc_no = page.locator("#cmhc-false")

        self.maturity_date_btn = (
            page.locator("label:text-is('Maturity Date')")
            .locator("..")
            .get_by_role("button")
        )
        self.new_or_existing_combobox = (
            page.locator("label")
            .filter(has_text="New or Existing")
            .locator("..")
            .get_by_role("combobox")
        )
        self.mortgage_position_combobox = (
            page.locator("label")
            .filter(has_text="Mortgage Position")
            .locator("..")
            .get_by_role("combobox")
        )
        self.out_of_province_combobox = (
            page.locator("label")
            .filter(has_text="Out of Province")
            .locator("..")
            .get_by_role("combobox")
        )
        self.other_lender_combobox = (
            page.locator("label")
            .filter(has_text="Other Lender")
            .locator("..")
            .get_by_role("combobox")
        )
        self.lender_type_combobox = (
            page.locator("label")
            .filter(has_text="Lender Type")
            .locator("..")
            .get_by_role("combobox")
        )
        self.lender_class_combobox = (
            page.locator("label")
            .filter(has_text="Lender Class")
            .locator("..")
            .get_by_role("combobox")
        )
        self.lawyers_combobox = (
            page.locator("label")
            .filter(has_text="Lawyers")
            .locator("..")
            .get_by_role("combobox")
        )

        self.closing_save_btn = (
            page.locator("form")
            .filter(has=self.credit_score)
            .get_by_role("button", name="Save Data")
        )

        # ===============================
        # Client Care Checks fields
        # ===============================

        self.payment_request_sent_yes = page.locator("#paymentRequestSent-true")
        self.payment_request_sent_no = page.locator("#paymentRequestSent-false")
        self.final_maturity_date_btn = (
            page.locator("label:text-is('Final Maturity Date')")
            .locator("..")
            .get_by_role("button")
        )
        self.final_closing_notes = page.locator("#finalClosingNotes")

        self.client_care_save_btn = (
            page.locator("form")
            .filter(has=self.payment_request_sent_yes)
            .get_by_role("button", name="Save Data")
        )
        self.complete_stage_btn = page.get_by_role("button", name="Complete Stage")

        # ===============================
        # Toasts
        # ===============================

        self.toast_container = page.locator(
            'section[aria-label="Notifications alt+T"]'
        )
        self.closing_saved_toast = self.toast_container.get_by_text(
            "Closing compliance data saved successfully"
        ).first
        self.client_care_saved_toast = self.toast_container.get_by_text(
            "Client care checks saved successfully"
        ).first
        self.moved_to_client_care_toast = self.toast_container.get_by_text(
            "Lead moved to Client Care successfully"
        ).first

        self._last_closing_values: dict[str, str] = {}

    # ===============================
    # Navigation
    # ===============================

    def open(self):
        self.page.goto(Config.BASE_URL)
        self.page.wait_for_load_state("networkidle")

    def _compliance_record_link(self, deal_name: str):
        link = self.page.locator(f"a[href*='/compliance/']").filter(
            has=self.page.get_by_text(deal_name, exact=True)
        )
        if link.count() > 0:
            return link.first
        return self.page.get_by_role("link", name=deal_name)

    def _client_care_record_link(self, deal_name: str):
        return self.page.locator(f"a[href*='{_CLIENT_CARE_PATH}/']").filter(
            has=self.page.get_by_text(deal_name, exact=True)
        )

    def _search_bucket(self, bucket_path: str, deal_name: str):
        self.page.goto(f"{Config.BASE_URL}{bucket_path}")
        self.page.wait_for_load_state("networkidle")
        search = self.list_search
        search.wait_for(state="visible", timeout=30000)
        search.fill(deal_name)
        self.page.wait_for_function(
            """(expected) => {
                const params = new URLSearchParams(window.location.search);
                return params.get('search') === expected;
            }""",
            arg=deal_name,
            timeout=15000,
        )
        self.page.wait_for_load_state("networkidle")

    def _search_compliance_board(self, deal_name: str):
        self.click(self.compliance_link)
        self.page.wait_for_load_state("networkidle")

        if self.list_search.count() > 0:
            try:
                self.list_search.wait_for(state="visible", timeout=5000)
                self.list_search.fill(deal_name)
                self.page.wait_for_function(
                    """(expected) => {
                        const params = new URLSearchParams(window.location.search);
                        return params.get('search') === expected;
                    }""",
                    arg=deal_name,
                    timeout=15000,
                )
                self.page.wait_for_load_state("networkidle")
                return
            except Exception:
                pass

        self.fill(self.global_search, deal_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")

    def open_compliance_deal(self, deal_name: str):
        # self._search_compliance_board(deal_name)
        # record = self._compliance_record_link(deal_name)
        # record.wait_for(state="visible", timeout=30000)
        # record.click()
        # self.page.wait_for_load_state("networkidle")
        from utils.entity_navigation import COMPLIANCE_BUCKET, open_bucket_record

        open_bucket_record(self.page, COMPLIANCE_BUCKET, deal_name)

    def open_signed_closed_tab(self):
        self.click(self.signed_closed_tab)
        self.wait_visible(self.compliance_card_title)

    def open_main_signed_tab(self):
        self.click(self.main_signed_tab)

    def open_compliance_form_tab(self):
        self.click(self.compliance_form_tab)
        self.wait_visible(self.closing_compliance_heading)

    def open_signed_form_tab(self):
        self.click(self.signed_form_tab)
        self.wait_visible(self.signed_profile_heading)
        self.wait_for_signed_form_readonly_ready()

    def open_client_care(self):
        self.click(self.client_care_link)
        self.page.wait_for_load_state("networkidle")

    # ===============================
    # Helpers
    # ===============================

    @staticmethod
    def _normalize_numeric(value: str) -> str:
        cleaned = re.sub(r"[^\d.\-]", "", str(value or ""))
        if not cleaned:
            return ""
        if "." in cleaned:
            number = float(cleaned)
            if number.is_integer():
                return str(int(number))
            return str(number)
        return cleaned

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _normalize_date(value: str) -> str:
        text = CompliancePage._normalize_text(value)
        match = re.search(r"\d{2}/\d{2}/\d{4}", text)
        return match.group(0) if match else text

    def _fill_locator(self, locator, value: str):
        locator.scroll_into_view_if_needed()
        locator.click()
        locator.fill("")
        self.fill(locator, value)

    def _wait_for_compliance_form_ready(self):
        loader = self.page.get_by_text("Loading compliance data...")
        if loader.count() > 0:
            loader.first.wait_for(state="hidden", timeout=30000)
        self.wait_visible(self.credit_score)

    def _capture_closing_compliance_values(self) -> dict[str, str]:
        self._wait_for_compliance_form_ready()
        return {
            "credit_score": self.credit_score.input_value(),
            "total_debt_ratio": self.total_debt_ratio.input_value(),
            "loan_to_value": self.loan_to_value.input_value(),
            "finder_fee_percent": self.finder_fee_percent.input_value(),
            "volume_bonus": self.volume_bonus.input_value(),
            "broker_fee": self.broker_fee.input_value(),
            "underwriting_fee": self.underwriting_fee.input_value(),
            "net_fee": self.net_fee.input_value(),
            "expense_deducted": self.expense_deducted.input_value(),
            "other_expenses": self.other_expenses.input_value(),
            "referral_fee": self.referral_fee.input_value(),
            "appraisal_expense": self.appraisal_expense.input_value(),
            "uw_fee": self.uw_fee.input_value(),
            "internal_agent_fee_a": self.internal_agent_fee_a.input_value(),
            "internal_agent_fee_b": self.internal_agent_fee_b.input_value(),
            "af": self.af.input_value(),
            "ff": self.ff.input_value(),
            "insurer": self.insurer.input_value(),
            "maturity_date": self._read_date_button(self.maturity_date_btn),
            "new_or_existing": self._read_combobox_text(self.new_or_existing_combobox),
            "mortgage_position": self._read_combobox_text(
                self.mortgage_position_combobox
            ),
            "out_of_province": self._read_combobox_text(self.out_of_province_combobox),
            "other_lender": self._read_combobox_text(self.other_lender_combobox),
            "lender_type": self._read_combobox_text(self.lender_type_combobox),
            "lender_class": self._read_combobox_text(self.lender_class_combobox),
            "lawyer": self._read_combobox_text(self.lawyers_combobox),
        }

    def _click_radio(self, locator):
        locator.scroll_into_view_if_needed()
        self.click(locator)

    def _select_combobox_option(self, combobox, option_label: str):
        combobox.scroll_into_view_if_needed()
        self.click(combobox)
        option = self.page.get_by_role("option", name=option_label, exact=True)
        option.wait_for(state="visible")
        self.click(option)

    def _select_first_combobox_option(self, combobox) -> str:
        combobox.scroll_into_view_if_needed()
        self.click(combobox)
        first = self.page.get_by_role("option").first
        first.wait_for(state="visible")
        label = self._normalize_text(first.inner_text())
        self.click(first)
        return label

    def _select_boolean_radio(self, yes_locator, no_locator, value: bool):
        self._click_radio(yes_locator if value else no_locator)

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

    def _read_date_button(self, trigger) -> str:
        trigger.scroll_into_view_if_needed()
        return self._normalize_date(trigger.inner_text())

    def _read_combobox_text(self, combobox) -> str:
        combobox.scroll_into_view_if_needed()
        return self._normalize_text(combobox.inner_text())

    def _read_readonly_field(self, label: str) -> str:

        # container = (
        #     self.page.locator("label")
        #     .filter(has_text=label)
        #     .first.locator("..")
        # )
        # field = container.locator("input, textarea").first
        # field.wait_for(state="visible")
        scope = self._signed_form_scope()
        self._ensure_signed_form_sections_expanded()
        label_locator = scope.locator("label").filter(
            has_text=re.compile(rf"^{re.escape(label)}", re.I)
        ).first
        label_locator.scroll_into_view_if_needed()
        field = label_locator.locator("..").locator("input, textarea").first
        field.wait_for(state="visible", timeout=Config.TIMEOUT)
        return self._normalize_text(field.input_value())

    def _client_care_just_closed_panel(self):
        """Client Care tabpanel for the Just Closed signed snapshot."""
        return self.page.get_by_role("tabpanel", name="Just Closed")

    def _signed_form_scope(self):
        """Read-only signed snapshot: Compliance uses 'Signed Form'; Client Care uses 'Just Closed'."""
        if _CLIENT_CARE_PATH in self.page.url:
            return self._client_care_just_closed_panel()
        return self.page.get_by_role("tabpanel", name="Signed Form")

    def _wait_for_signed_form_async_content(self, scope, timeout: int) -> None:
        """Wait for SignedFormReadOnlyView skeleton / refetch overlay to finish."""
        skeleton = scope.locator("[class*='animate-pulse']")
        loading = scope.get_by_text(re.compile(r"Loading signed data", re.I))
        empty = scope.get_by_text(
            re.compile(r"No signed form data is available", re.I)
        )

        if skeleton.count() > 0:
            expect(skeleton.first).to_be_hidden(timeout=timeout)

        if loading.count() > 0:
            expect(loading.first).to_be_hidden(timeout=timeout)

        if empty.count() > 0 and empty.first.is_visible():
            detail = self._normalize_text(empty.first.inner_text())
            raise AssertionError(
                f"Signed form has no data in Client Care Just Closed: {detail}"
            )

        error_alert = scope.get_by_text(re.compile(r"Error loading signed form", re.I))
        if error_alert.count() > 0 and error_alert.first.is_visible():
            detail = self._normalize_text(error_alert.first.inner_text())
            raise AssertionError(f"Signed form failed to load: {detail}")

    def _ensure_signed_form_sections_expanded(self) -> None:
        """Expand CollapsibleSection panels so read-only inputs are visible."""
        scope = self._signed_form_scope()
        if _CLIENT_CARE_PATH in self.page.url:
            expect(self.page.get_by_role("tabpanel", name="Profile")).to_be_hidden(
                timeout=Config.TIMEOUT
            )
        for title in _SIGNED_FORM_SECTION_TITLES:
            trigger = scope.get_by_role("button", name=title, exact=True)
            expect(trigger.first).to_be_visible(timeout=Config.TIMEOUT)
            button = trigger.first
            button.scroll_into_view_if_needed()
            if button.get_attribute("aria-expanded") == "false":
                self.click(button)
            expect(button).to_have_attribute("aria-expanded", "true", timeout=5000)

    def wait_for_signed_form_readonly_ready(self, timeout: int | None = None):
        """Wait until async SignedFormReadOnlyView content is loaded and readable."""
        timeout = timeout or Config.TIMEOUT
        if _CLIENT_CARE_PATH in self.page.url:
            expect(self.page).to_have_url(
                re.compile(r"([?&])tab=just-closed"), timeout=timeout
            )
            expect(self.page.get_by_role("tabpanel", name="Profile")).to_be_hidden(
                timeout=timeout
            )
        scope = self._signed_form_scope()
        expect(scope).to_be_visible(timeout=timeout)

        self._wait_for_signed_form_async_content(scope, timeout)
        self._ensure_signed_form_sections_expanded()

        anchor_label = scope.locator("label").filter(
            has_text=re.compile(r"^Loan Amount Approved\b", re.I)
        ).first
        expect(anchor_label).to_be_visible(timeout=timeout)
        anchor_field = anchor_label.locator("..").locator("input, textarea").first
        expect(anchor_field).to_be_visible(timeout=timeout)
        expect(anchor_field).to_be_disabled(timeout=timeout)

        if _CLIENT_CARE_PATH in self.page.url:
            for title in _SIGNED_FORM_SECTION_TITLES:
                expect(
                    scope.get_by_role("button", name=title, exact=True).first
                ).to_be_visible(timeout=timeout)

    # ===============================
    # Signed Form verification
    # ===============================

    def capture_signed_tab_values(self, signed: SignedPage) -> SignedFormSnapshot:
        signed.wait_visible(signed.signed_documents_title)

        trust_ledger = ""
        if signed.trust_ledger_review_yes.is_checked():
            trust_ledger = "yes"
        elif signed.trust_ledger_review_no.is_checked():
            trust_ledger = "no"

        google_review = ""
        if signed.good_for_google_review_yes.is_checked():
            google_review = "yes"
        elif signed.good_for_google_review_no.is_checked():
            google_review = "no"

        outstanding = ""
        if signed.outstanding_conditions_details.is_visible():
            outstanding = signed.outstanding_conditions_details.input_value()

        other_mortgage = ""
        if signed.other_mortgage_type.is_visible():
            other_mortgage = signed.other_mortgage_type.input_value()

        return SignedFormSnapshot(
            loan_amount=signed.loan_amount_approved.input_value(),
            mortgage_type=self._read_combobox_text(signed.signed_mortgage_type_combobox),
            other_mortgage_type=other_mortgage,
            approved_ltv=signed.approved_ltv.input_value(),
            approved_term=signed.approved_term.input_value(),
            approved_rate=signed.approved_rate.input_value(),
            estimated_closing_date=self._read_date_button(signed.anticipated_closing_btn),
            client_lawyer=self._read_combobox_text(signed.client_lawyer_combobox),
            closing_email_sent=self._read_date_button(signed.closing_email_btn),
            lender_fee=signed.lender_fee.input_value(),
            lender_bps=signed.lender_bps.input_value(),
            broker_fee=signed.broker_fee.input_value(),
            admin_fee=signed.admin_fee.input_value(),
            appraisal_rebate=signed.appraisal_rebate.input_value(),
            lawyer_fee=signed.lawyer_fee.input_value(),
            trust_ledger_review=trust_ledger,
            outstanding_conditions=outstanding,
            meeting_notes=signed.additional_notes.input_value(),
            client_care_needs=signed.important_notes_client_care.input_value(),
            google_review_status=google_review,
        )

    def read_signed_form_readonly_values(self) -> SignedFormSnapshot:
        self.wait_for_signed_form_readonly_ready()
        self._ensure_signed_form_sections_expanded()

        scope = self._signed_form_scope()
        trust_text = self._normalize_text(
            scope.get_by_text(re.compile(r"Trust Ledger Review:", re.I)).inner_text()
        )
        trust_ledger = ""
        if re.search(r"\bYes\b", trust_text, re.I):
            trust_ledger = "yes"
        elif re.search(r"\bNo\b", trust_text, re.I):
            trust_ledger = "no"

        google_group = scope.locator(
            "label", has_text="Google Review Status"
        ).first.locator("..")
        yes_radio = google_group.get_by_role("radio", name="Yes")
        no_radio = google_group.get_by_role("radio", name="No")
        google_review = ""
        if yes_radio.is_checked():
            google_review = "yes"
        elif no_radio.is_checked():
            google_review = "no"

        return SignedFormSnapshot(
            loan_amount=self._read_readonly_field("Loan Amount Approved"),
            mortgage_type=self._read_readonly_field("Mortgage Type"),
            other_mortgage_type=self._read_readonly_field("Other"),
            approved_ltv=self._read_readonly_field("Approved LTV - %"),
            approved_term=self._read_readonly_field("Approved Term"),
            approved_rate=self._read_readonly_field("Approved Rate"),
            estimated_closing_date=self._read_readonly_field("Estimated Closing Date"),
            client_lawyer=self._read_readonly_field("Clients Lawyer"),
            closing_email_sent=self._read_readonly_field("Closing Email Thread Sent"),
            lender_fee=self._read_readonly_field("Lender Fee"),
            lender_bps=self._read_readonly_field("Lender BPS"),
            broker_fee=self._read_readonly_field("Broker Fee"),
            admin_fee=self._read_readonly_field("Admin Fee"),
            appraisal_rebate=self._read_readonly_field("Appraisal Rebate"),
            lawyer_fee=self._read_readonly_field("Lawyer Fee"),
            trust_ledger_review=trust_ledger,
            outstanding_conditions=self._read_readonly_field("Outstanding Conditions"),
            meeting_notes=self._read_readonly_field("Meeting Notes"),
            client_care_needs=self._read_readonly_field("Client Care Needs"),
            google_review_status=google_review,
        )

    def verify_signed_form_readonly(self):
        self.wait_for_signed_form_readonly_ready()
        scope = self._signed_form_scope()
        inputs = scope.locator("input, textarea")
        count = inputs.count()
        assert count > 0, "Expected read-only Signed Form fields to be visible"
        for index in range(count):
            expect(inputs.nth(index)).to_be_disabled()

    def verify_signed_form_has_data(self, snapshot: SignedFormSnapshot):
        required = {
            "loan_amount": snapshot.loan_amount,
            "mortgage_type": snapshot.mortgage_type,
            "approved_ltv": snapshot.approved_ltv,
            "approved_term": snapshot.approved_term,
            "approved_rate": snapshot.approved_rate,
        }
        missing = [name for name, value in required.items() if not self._normalize_text(value)]
        assert not missing, f"Signed Form is missing expected signed-stage values: {missing}"

    def verify_signed_form_matches(self, baseline: SignedFormSnapshot):
        actual = self.read_signed_form_readonly_values()
        mismatches = []

        for field_name, expected in asdict(baseline).items():
            actual_value = getattr(actual, field_name)
            if field_name in {
                "loan_amount",
                "approved_ltv",
                "approved_term",
                "approved_rate",
                "lender_fee",
                "lender_bps",
                "broker_fee",
                "admin_fee",
                "appraisal_rebate",
                "lawyer_fee",
            }:
                if self._normalize_numeric(expected) != self._normalize_numeric(
                    actual_value
                ):
                    mismatches.append(
                        (field_name, expected, actual_value)
                    )
            elif field_name in {
                "estimated_closing_date",
                "closing_email_sent",
            }:
                if self._normalize_date(expected) != self._normalize_date(actual_value):
                    mismatches.append(
                        (field_name, expected, actual_value)
                    )
            elif expected and self._normalize_text(expected) != self._normalize_text(
                actual_value
            ):
                mismatches.append((field_name, expected, actual_value))

        assert not mismatches, (
            "Signed Form read-only values do not match the Signed tab:\n"
            + "\n".join(
                f"  {name}: expected {exp!r}, got {act!r}"
                for name, exp, act in mismatches
            )
        )

    # ===============================
    # Closing Compliance actions
    # ===============================

    def fill_closing_compliance(self, data):
        self.open_compliance_form_tab()
        self._fill_locator(self.credit_score, data.credit_score)
        self.select_date(
            self.maturity_date_btn, data.month, data.year, data.day
        )
        self._fill_locator(self.total_debt_ratio, data.total_debt_ratio)
        self._select_combobox_option(
            self.new_or_existing_combobox, data.new_or_existing
        )
        self._fill_locator(self.loan_to_value, data.loan_to_value)
        self._select_combobox_option(
            self.mortgage_position_combobox, data.mortgage_position
        )
        self._fill_locator(self.finder_fee_percent, data.finder_fee_percent)
        self._fill_locator(self.volume_bonus, data.volume_bonus)
        self._fill_locator(self.broker_fee, data.broker_fee)
        self._fill_locator(self.underwriting_fee, data.underwriting_fee)
        self._select_boolean_radio(self.mpp_yes, self.mpp_no, data.mpp)
        self._select_boolean_radio(
            self.high_ratio_yes, self.high_ratio_no, data.high_ratio
        )
        self._select_boolean_radio(
            self.conventional_yes, self.conventional_no, data.conventional
        )
        self._select_boolean_radio(self.cmhc_yes, self.cmhc_no, data.cmhc)
        self._select_combobox_option(
            self.out_of_province_combobox, data.out_of_province
        )
        self._fill_locator(self.net_fee, data.net_fee)
        self._fill_locator(self.expense_deducted, data.expense_deducted)
        self._fill_locator(self.other_expenses, data.other_expenses)
        self._fill_locator(self.referral_fee, data.referral_fee)
        self._fill_locator(self.appraisal_expense, data.appraisal_expense)
        self._fill_locator(self.uw_fee, data.uw_fee)
        self._fill_locator(self.internal_agent_fee_a, data.internal_agent_fee_a)
        self._fill_locator(self.internal_agent_fee_b, data.internal_agent_fee_b)
        self._fill_locator(self.af, data.af)
        self._fill_locator(self.ff, data.ff)
        self._fill_locator(self.insurer, data.insurer)
        other_lender = self._select_first_combobox_option(self.other_lender_combobox)
        self._select_combobox_option(self.lender_type_combobox, data.lender_type)
        self._select_combobox_option(self.lender_class_combobox, data.lender_class)
        lawyer = self._select_first_combobox_option(self.lawyers_combobox)

    def save_closing_compliance(self):
        self.click(self.closing_save_btn)

    def verify_closing_compliance_saved(self):
        self.wait_visible(self.closing_saved_toast)
        self.verify_visible(self.closing_saved_toast)
        self._last_closing_values = self._capture_closing_compliance_values()

    def verify_closing_compliance_persisted(self):
        self.open_compliance_form_tab()
        expected = self._last_closing_values
        assert expected, "No closing compliance values captured after save"

        self._wait_for_compliance_form_ready()
        checks = self._capture_closing_compliance_values()

        numeric_keys = {
            "credit_score",
            "total_debt_ratio",
            "loan_to_value",
            "finder_fee_percent",
            "volume_bonus",
            "broker_fee",
            "underwriting_fee",
            "net_fee",
            "expense_deducted",
            "other_expenses",
            "referral_fee",
            "appraisal_expense",
            "uw_fee",
            "internal_agent_fee_a",
            "internal_agent_fee_b",
            "af",
            "ff",
        }

        mismatches = []
        for key, exp in expected.items():
            act = checks[key]
            if key == "maturity_date":
                if self._normalize_date(exp) != self._normalize_date(act):
                    mismatches.append((key, exp, act))
            elif key in numeric_keys:
                if self._normalize_numeric(exp) != self._normalize_numeric(act):
                    mismatches.append((key, exp, act))
            elif self._normalize_text(exp) != self._normalize_text(act):
                mismatches.append((key, exp, act))

        assert not mismatches, (
            "Closing compliance data did not persist after refresh:\n"
            + "\n".join(
                f"  {name}: expected {exp!r}, got {act!r}"
                for name, exp, act in mismatches
            )
        )

    # ===============================
    # Client Care Checks actions
    # ===============================

    def fill_client_care_checks(self, data):
        self._select_boolean_radio(
            self.payment_request_sent_yes,
            self.payment_request_sent_no,
            data.payment_request_sent,
        )
        self.select_date(
            self.final_maturity_date_btn, data.month, data.year, data.day
        )
        self._fill_locator(self.final_closing_notes, data.final_closing_notes)

    def save_client_care_checks(self):
        self.click(self.client_care_save_btn)

    def verify_client_care_checks_saved(self):
        self.wait_visible(self.client_care_saved_toast)
        self.verify_visible(self.client_care_saved_toast)

    def complete_stage(self):
        self.click(self.complete_stage_btn)

    def verify_moved_to_client_care_toast(self):
        self.wait_visible(self.moved_to_client_care_toast)
        expect(self.moved_to_client_care_toast).to_have_count(1)
        self.verify_visible(self.moved_to_client_care_toast)

    def verify_on_client_care_page(self):
        expect(self.page).to_have_url(re.compile(r"/client-care/?$"))

    def _search_client_care_board(self, deal_name: str):
        if "/client-care" not in self.page.url:
            self.page.goto(f"{Config.BASE_URL}{_CLIENT_CARE_PATH}")
            self.page.wait_for_load_state("networkidle")

        if self.list_search.count() > 0:
            try:
                self.list_search.wait_for(state="visible", timeout=5000)
                self.list_search.fill(deal_name)
                self.page.wait_for_load_state("networkidle")
                return
            except Exception:
                pass

        if self.global_search.count() > 0:
            self.fill(self.global_search, deal_name)
            self.page.keyboard.press("Enter")
            self.page.wait_for_load_state("networkidle")

    def verify_lead_in_client_care(self, deal_name: str):
        candidates = [deal_name]
        stripped = deal_name.strip()
        if stripped and stripped not in candidates:
            candidates.append(stripped)

        for name in candidates:
            record = self._client_care_record_link(name)
            if record.count() > 0 and record.first.is_visible():
                expect(record.first).to_be_visible()
                return
            self._search_client_care_board(name)
            record = self._client_care_record_link(name)
            if record.count() > 0:
                expect(record.first).to_be_visible(timeout=30000)
                return

        expect(self.page.get_by_text(stripped or deal_name).first).to_be_visible(
            timeout=30000
        )
