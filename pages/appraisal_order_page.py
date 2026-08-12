from playwright.sync_api import expect
import re
from pages.base_page import BasePage
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record
from utils.wait_helpers import select_google_places_suggestion, wait_for_page_ready


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
class AppraisalOrderPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        # ===============================
        # Navigation
        # ===============================

        self.my_deals = page.get_by_role("link",name="My Deals")

        self.appraisal_tab = page.get_by_role("tab", name="Appraisal Order", exact=True)

        # ===============================
        # Form Fields
        # ===============================

        #         self.company_input = page.get_by_role("textbox",name="Enter Appraisal Company")

        # self.location_input = page.get_by_role("textbox",name="Enter Appraisal Location")

        # # self.location_option = page.getByRole('textbox',name = 'Enter Appraisal Location' )

        # self.ltv_input = page.get_by_role("textbox",name="Enter LTV")

        self.avm = page.locator("//button[@id='avm-yes']")

        self.company_input = page.locator("#appraisalCompany")
        self.location_input = page.locator("#appraisalLocation")
        self.ltv_input = page.locator("#ltv")

        self.city_input = page.locator("#city")

        self.appraisal_yes = page.locator("#appraisalOrdered-yes")

        self.appraisal_no = page.locator("#appraisalOrdered-no")

        self.reason_input = page.get_by_role("textbox",name="Enter reason for not ordering")

        # ===============================
        # Buttons
        # ===============================

        self.save_btn = self.page.get_by_role("button", name="Save")
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
            "Appraisal order created successfully"
        )
        self.update_success_toast = self.toast_container.get_by_text(
            "Appraisal order updated successfully"
        )
        # self.next_stage_toast = self.toast_container.get_by_text("Lead moved to Submitted successfully").first
        self.next_stage_toast = self.page.locator('section[aria-label="Notifications alt+T"]').get_by_text("Lead moved to Submitted successfully").first

    # ===================================================
    # Navigation
    # ===================================================

    # def open(self):

    #     self.click(self.appraisal_tab)

    def deal(self, deal_name: str):
        return self.page.get_by_role("link",name=deal_name)

    def open(self):
        self.page.goto(Config.BASE_URL)
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

    def _wait_for_appraisal_form(self) -> None:
        expect(self.appraisal_yes.or_(self.appraisal_no).first).to_be_visible(
            timeout=30000
        )

    @staticmethod
    def _is_radio_checked(radio) -> bool:
        aria = radio.get_attribute("aria-checked")
        if aria in ("true", "false"):
            return aria == "true"
        return radio.get_attribute("data-state") == "checked"

    def _select_radio(self, radio) -> None:
        radio.scroll_into_view_if_needed()
        expect(radio).to_be_visible(timeout=Config.TIMEOUT)
        if self._is_radio_checked(radio):
            return
        radio.click(force=True)
        expect(radio).to_have_attribute("aria-checked", "true", timeout=Config.TIMEOUT)

    def _select_appraisal_ordered(self, value: str) -> None:
        radio = self.appraisal_yes if value == "yes" else self.appraisal_no
        self._select_radio(radio)

    def wait_for_appraisal_form_idle(self) -> None:
        """Wait until save mutation finished and the form is interactive."""
        expect(self.save_btn).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.save_btn).to_be_enabled(timeout=Config.TIMEOUT)
        expect(self.save_btn).not_to_have_text(re.compile(r"Saving", re.I), timeout=Config.TIMEOUT)
        if self.stage_dialog.is_visible():
            return

    def verify_appraisal_ordered(self, value: str) -> None:
        radio = self.appraisal_yes if value == "yes" else self.appraisal_no
        expect(radio).to_have_attribute("aria-checked", "true", timeout=Config.TIMEOUT)

    def ensure_appraisal_yes_form_visible(self) -> None:
        """Switch to Appraisal Ordered = Yes and wait for yes-path fields."""
        self.wait_for_appraisal_form_idle()
        for _ in range(3):
            if self.company_input.is_visible():
                self.verify_appraisal_ordered("yes")
                return
            self._select_appraisal_ordered("yes")
        expect(self.company_input).to_be_visible(timeout=Config.TIMEOUT)
        self.verify_appraisal_ordered("yes")

    def _wait_for_appraisal_yes_fields(self) -> None:
        self.ensure_appraisal_yes_form_visible()

    def open_appraisal_order(self, deal_name, bucket=MY_DEALS_BUCKET):
        open_bucket_record(self.page, bucket, deal_name)
        self.reopen_appraisal_tab()

    # ===================================================
    # Scenario NO
    # ===================================================

    def fill_appraisal_no(self, data):
        self.wait_for_appraisal_form_idle()
        self._select_appraisal_ordered("no")
        self._select_radio(self.avm)

        self.fill(self.reason_input, data.reason)
        

    # ===================================================
    # Scenario YES
    # ===================================================

    def fill_appraisal_yes(self, data):

        self._wait_for_appraisal_yes_fields()

        self.fill(self.company_input,data.company)


        location = self.location_input
        location.clear()
        select_google_places_suggestion(
            self.page, location, data.location, type_delay=100
        )
        self.page.keyboard.press("Tab")
        if self.city_input.count() > 0 and self.city_input.is_visible():
            expect(self.city_input).not_to_have_value("", timeout=Config.TIMEOUT)


        self.fill(self.ltv_input,data.ltv)

        self.select_date("Date Order Placed", data.month, data.year, data.day)
        self.select_date(
            "Appraisal Appointment Confirmed", data.month, data.year, data.day
        )

    
    def _appraisal_form(self):
        return self.page.locator("form").filter(has=self.company_input).first

    def _date_picker_button(self, label_text: str):
        """Date labels include a required-marker span (e.g. 'Date Order Placed *')."""
        return (
            self._appraisal_form()
            .locator("label")
            .filter(has_text=re.compile(rf"^{re.escape(label_text)}\b", re.I))
            .locator("..")
            .get_by_role("button")
            .first
        )

    def select_date(self, label_text, month, year, day):
        trigger = self._date_picker_button(label_text)
        self.click(trigger)

        calendar = self.page.locator("[role='dialog']").last
        calendar.wait_for(state="visible")
        calendar.get_by_label("Choose the Month").select_option(str(month))
        calendar.get_by_label("Choose the Year").select_option(str(year))

        full_month = _MONTH_TO_FULL.get(str(month), str(month))
        day_button = calendar.get_by_role(
            "button",
            name=re.compile(rf"{full_month}.*{_ordinal_day(day)}", re.IGNORECASE),
        ).first
        self.click(day_button)
    def save_appraisal_order(self):
        self.click(self.save_btn)

    def clear_yes_form_fields(self):
        self.company_input.fill("")
        self.location_input.fill("")
        self.ltv_input.fill("")
        self.city_input.fill("")

    def select_yes_with_avm(self):
        self.ensure_appraisal_yes_form_visible()
        self._select_radio(self.avm)

    def select_yes_without_avm(self):
        self.ensure_appraisal_yes_form_visible()

    def reset_appraisal_form(self):
        cancel = self.page.get_by_role("button", name="Cancel")
        if cancel.count() > 0 and cancel.first.is_visible():
            self.click(cancel.first)
            wait_for_page_ready(self.page)
            self._wait_for_appraisal_form()

    def select_no_with_avm(self):
        self._select_appraisal_ordered("no")
        self._select_radio(self.avm)

    def set_field(self, field: str, value: str):
        field_map = {
            "ltv": self.ltv_input,
            "appraisalCompany": self.company_input,
            "appraisalLocation": self.location_input,
            "city": self.city_input,
            "appraisalOrderRejectedReason": self.reason_input,
        }
        self.fill(field_map[field], value)

    def clear_field(self, field: str):
        self.set_field(field, "")

    def prepare_yes_flow_for_invalid_ltv(self):
        self.select_yes_with_avm()

    def fill_invalid_ltv(self, ltv: str):
        self.prepare_yes_flow_for_invalid_ltv()
        self.fill(self.ltv_input, ltv)

    # ===================================================
    # Dates
    # ===================================================

    def select_order_date(self, date_name):

        self.click(self.date_buttons.first)

        self.click(self.page.get_by_role("button",name=date_name))

    def select_expected_date(self, date_name):

        self.click(self.date_buttons.nth(1))

        self.click(self.page.get_by_role("button",name=date_name))

    # ===================================================
    # Popup
    # ===================================================

    def verify_saved(self):
        success = self.create_success_toast.or_(self.update_success_toast)
        self.wait_visible(success.first)
        self.verify_visible(success.first)

    def cancel_move_to_next_stage(self):
        self.wait_visible(self.stage_dialog)
        self.click(self.stage_cancel_btn)
        expect(self.stage_dialog).to_be_hidden(timeout=Config.TIMEOUT)
        self.wait_for_appraisal_form_idle()

    def move_to_next_stage(self):
        self.wait_visible(self.stage_dialog)
        self.click(self.move_next_btn)

    # ===================================================
    # Verification
    # ===================================================

    def verify_next_stage_message(self):
        from utils.stage_transition_verification import verify_immediate_stage_move

        verify_immediate_stage_move(
            self.page,
            success_toast="Lead moved to Submitted successfully",
            url_tab="submitted",
            active_tab=self.page.get_by_role("tab", name="Submitted").first,
        )

    def verify_reason(self, data):

        expect(self.reason_input).to_have_value(data.reason)

    def verify_yes_details(self, data):

        expect(self.company_input).to_have_value(data.company)

        expect(self.location_input).not_to_have_value("")

        expect(self.ltv_input).to_have_value(data.ltv)

    def _read_date_button(self, label_text: str) -> str:
        button = self._date_picker_button(label_text)
        expect(button).to_be_visible(timeout=30000)
        return " ".join(button.inner_text().split())

    def capture_appraisal_yes_values(self) -> dict[str, str]:
        """Read appraisal-order yes-path fields saved in the happy path."""
        expect(self.company_input).to_be_visible(timeout=30000)
        values = {
            "appraisalCompany": self.company_input.input_value(),
            "appraisalLocation": self.location_input.input_value(),
            "ltv": self.ltv_input.input_value(),
            "dateOrderPlaced": self._read_date_button("Date Order Placed"),
            "appraisalAppointmentConfirmed": self._read_date_button(
                "Appraisal Appointment Confirmed"
            ),
        }
        if self.city_input.count() > 0 and self.city_input.is_visible():
            values["city"] = self.city_input.input_value()
        return values

    def reopen_appraisal_tab(self) -> None:
        self.click(self.appraisal_tab)
        expect(self.appraisal_tab).to_have_attribute("data-state", "active", timeout=30000)
        expect(self.page).to_have_url(re.compile(r"tab=appraisal-order"), timeout=30000)
        self._wait_for_appraisal_form()

    