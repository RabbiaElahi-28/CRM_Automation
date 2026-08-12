from playwright.sync_api import expect
import re

from pages.base_page import BasePage
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record


class SubmittedPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        self.my_deals = page.get_by_role("link", name="My Deals")
        self.submitted_tab = page.get_by_role("tab", name="Submitted")
        self.approved_tab = page.get_by_role("tab", name="Approved").first

        self.save_btn = page.get_by_role("button", name="Save")
        self.stage_dialog = page.get_by_role("alertdialog", name="Move to Next Stage?")
        self.stage_cancel_btn = self.stage_dialog.get_by_role("button", name="Cancel")
        self.move_next_btn = self.stage_dialog.get_by_role(
            "button", name="Move to Next Stage"
        )

        self.toast_container = page.locator(
            'section[aria-label="Notifications alt+T"]'
        )
        self.create_success_toast = self.toast_container.get_by_text(
            "Submitted saved successfully"
        )
        self.update_success_toast = self.toast_container.get_by_text(
            "Submitted updated successfully"
        )
        self.next_stage_toast = self.toast_container.get_by_text(
            "Lead moved to Approved successfully").first

    def deal(self, deal_name: str):
        return self.page.get_by_role("link", name=deal_name).first

    def option_tab(self, option_number: int):
        return self.page.get_by_role("tab", name=f"Mortgage Option {option_number}")

    def open(self):
        self.page.goto(
            Config.BASE_URL,
            wait_until="domcontentloaded",
            timeout=Config.TIMEOUT,
        )
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

    def open_submitted(self, deal_name, bucket=MY_DEALS_BUCKET):
        open_bucket_record(self.page, bucket, deal_name)
        self.click(self.submitted_tab)

    def select_option_tab(self, option_number: int):
        tab = self.option_tab(option_number)
        expect(tab).to_be_enabled(timeout=30000)
        tab.click()

    def _select_panel_radio(self, panel, name: str, value: str) -> None:
        """Select a Radix radio option scoped to an option tabpanel."""
        radio = panel.locator(f"#{name}-{value}")
        expect(radio).to_be_visible(timeout=30000)
        if radio.get_attribute("data-state") == "checked":
            return
        radio.click(force=True)

    @staticmethod
    def _read_panel_radio_value(panel, name: str) -> str:
        for value in ("yes", "no"):
            radio = panel.locator(f"#{name}-{value}")
            if radio.count() == 0:
                continue
            state = radio.get_attribute("data-state")
            if state == "checked" or radio.get_attribute("aria-checked") == "true":
                return value
        return ""

    def active_tab_panel(self):
        return self.page.locator("[role='tab'][data-state='active']")


    _COMBOBOX_INDEX = {
        "Lender Name": 0,
        "Mortgage Type": 1,
    }



    def _panel_combobox(self, panel, label_text: str):
        index = self._COMBOBOX_INDEX.get(label_text, 0)
        return panel.get_by_role("combobox").nth(index)

    def _combobox_is_empty(self, combobox) -> bool:
        """Radix SelectTrigger exposes data-placeholder while no value is chosen."""
        return combobox.get_attribute("data-placeholder") is not None

    def _combobox_has_selection(self, combobox) -> bool:
        return not self._combobox_is_empty(combobox)

    def _wait_for_combobox_ready(self, combobox) -> None:
        expect(combobox).to_be_visible(timeout=Config.TIMEOUT)
        expect(combobox).to_be_enabled(timeout=Config.TIMEOUT)

    def _active_listbox(self):
        listbox = self.page.locator("[role='listbox']").last
        expect(listbox).to_be_visible(timeout=Config.TIMEOUT)
        return listbox

    def _wait_for_listbox_closed(self) -> None:
        listbox = self.page.locator("[role='listbox']")
        if listbox.count() == 0:
            return
        expect(listbox.last).to_be_hidden(timeout=Config.TIMEOUT)

    def _pick_combobox_option(
        self,
        panel,
        label_text: str,
        *,
        option_label: str | None = None,
    ) -> str:
        """Select a Radix combobox value inside a mortgage-option tabpanel."""
        for attempt in range(3):
            combobox = self._panel_combobox(panel, label_text)
            self._wait_for_combobox_ready(combobox)

            if option_label:
                current = " ".join(combobox.inner_text().split())
                if self._combobox_has_selection(combobox) and current == option_label:
                    return current
            elif self._combobox_has_selection(combobox):
                return " ".join(combobox.inner_text().split())

            combobox.scroll_into_view_if_needed()
            combobox.click()
            listbox = self._active_listbox()

            if option_label:
                option = listbox.get_by_role("option", name=option_label, exact=True)
                expect(option).to_be_visible(timeout=Config.TIMEOUT)
                label = " ".join(option.inner_text().split())
                option.click()
            else:
                option = listbox.get_by_role("option").first
                expect(option).to_be_visible(timeout=Config.TIMEOUT)
                label = " ".join(option.inner_text().split())
                option.click()

            self._wait_for_listbox_closed()

            combobox = self._panel_combobox(panel, label_text)
            if self._combobox_has_selection(combobox):
                return label

            if attempt < 2:
                # Keyboard fallback when pointer click did not register.
                combobox.click()
                listbox = self._active_listbox()
                if option_label:
                    listbox.get_by_role("option", name=option_label, exact=True).focus()
                else:
                    listbox.get_by_role("option").first.focus()
                self.page.keyboard.press("Enter")
                self._wait_for_listbox_closed()
                combobox = self._panel_combobox(panel, label_text)
                if self._combobox_has_selection(combobox):
                    return label

        combobox = self._panel_combobox(panel, label_text)
        raise AssertionError(
            f"Failed to select {label_text!r} "
            f"{f'option {option_label!r}' if option_label else 'first option'} "
            f"after 3 attempts (data-placeholder still present="
            f"{combobox.get_attribute('data-placeholder')!r})"
        )




    def _select_first_combobox_option(self, panel, label_text: str) -> str:
        return self._pick_combobox_option(panel, label_text)

    def _select_combobox_option(self, panel, label_text: str, option_label: str) -> None:
        self._pick_combobox_option(panel, label_text, option_label=option_label)

    def _ensure_lender_selected(self, panel) -> None:
        self._select_first_combobox_option(panel, "Lender Name")

    def _submitted_stage_panel(self):
        return self.page.get_by_role("tabpanel", name="Submitted")

    def _active_option_panel(self):
        """Mortgage option form panel — scoped inside Submitted to avoid outer tabpanel match."""
        return self._submitted_stage_panel().locator(
            "[role='tabpanel'][data-state='active']"
        )


    def _option_panel(self, option_number: int):
        tab = self.option_tab(option_number)
        expect(tab).to_be_enabled(timeout=Config.TIMEOUT)
        if tab.get_attribute("data-state") != "active":
            tab.click()
            expect(tab).to_have_attribute("data-state", "active", timeout=Config.TIMEOUT)
        panel = self._active_option_panel()
        self.wait_visible(panel)
        expect(panel.get_by_role("button", name="Save")).to_be_visible(timeout=Config.TIMEOUT)
        expect(panel.get_by_role("button", name="Save")).to_be_enabled(timeout=Config.TIMEOUT)
        return panel
        


    def _wait_for_lenders_ready(self, panel) -> None:
        lender = self._panel_combobox(panel, "Lender Name")
        expect(lender).not_to_contain_text("Loading lenders", timeout=Config.TIMEOUT)

    def _fill_number_field(self, locator, value: str) -> None:
        """Fill RHF number inputs that format display values (e.g. currency)."""
        expect(locator).to_be_visible(timeout=Config.TIMEOUT)
        locator.click()
        locator.fill("")
        locator.fill(str(value))
        locator.press("Tab")

    def _fill_option_amounts(self, panel, data) -> None:
        self._fill_number_field(panel.locator("#mortgageLoanAmount"), data.mortgage_loan_amount)
        self._fill_number_field(panel.locator("#requestedLTV"), data.requested_ltv)
        self._fill_number_field(panel.locator("#termRequested"), data.term_requested)
        self._fill_number_field(panel.locator("#rateRequested"), data.rate_requested)

    def _fill_option_radios(self, panel, data) -> None:
        self._select_panel_radio(panel, "powerOfAttorneyNeeded", data.power_of_attorney)
        self._select_panel_radio(panel, "approved", data.approved)
        if data.approved == "no":
            self.fill(panel.locator("#submittedRejectedReason"), data.rejected_reason)

    def _assert_combobox_selected(self, combobox) -> None:
        # Radix SelectTrigger keeps data-placeholder="" while empty; attribute is removed when selected.
        expect(combobox).not_to_have_attribute(
            "data-placeholder", "", timeout=Config.TIMEOUT
        )

    def _assert_option_fields_ready(self, panel, data) -> None:
        lender = self._panel_combobox(panel, "Lender Name")
        self._assert_combobox_selected(lender)

        mortgage_type = self._panel_combobox(panel, "Mortgage Type")
        self._assert_combobox_selected(mortgage_type)
        current_type = " ".join(mortgage_type.inner_text().split())
        assert current_type == data.mortgage_type, (
            f"Expected mortgage type {data.mortgage_type!r}, got {current_type!r}"
        )

        expect(panel.locator("#mortgageLoanAmount")).not_to_have_value("", timeout=Config.TIMEOUT)
        expect(panel.locator("#requestedLTV")).not_to_have_value("", timeout=Config.TIMEOUT)
        expect(panel.locator("#termRequested")).not_to_have_value("", timeout=Config.TIMEOUT)
        expect(panel.locator("#rateRequested")).not_to_have_value("", timeout=Config.TIMEOUT)

        self._assert_no_validation_errors(panel)

    def _assert_no_validation_errors(self, panel) -> None:
        errors = panel.locator("div.text-red-500, div.text-red-400, p.text-red-500")
        expect(errors).to_have_count(0, timeout=Config.TIMEOUT)

    def _ensure_option_ready_for_save(self, panel, data) -> None:
        """Ensure required Submitted option fields are populated before Save."""
        self._wait_for_lenders_ready(panel)
        self._ensure_lender_selected(panel)
        self._select_combobox_option(panel, "Mortgage Type", data.mortgage_type)
        self._fill_option_amounts(panel, data)
        self._fill_option_radios(panel, data)
        self._assert_option_fields_ready(panel, data)

    def verify_option_fields_filled(self, option_number: int, data) -> None:
        panel = self._option_panel(option_number)
        self._assert_option_fields_ready(panel, data)

    def fill_option(self, option_number: int, data):
        panel = self._option_panel(option_number)
        self._ensure_option_ready_for_save(panel, data)

    def clear_option_fields(self, option_number: int):
        panel = self._option_panel(option_number)
        for field_id in (
            "mortgageLoanAmount",
            "requestedLTV",
            "termRequested",
            "rateRequested",
        ):
            self.fill(panel.locator(f"#{field_id}"), "")

        reason = panel.locator("#submittedRejectedReason")
        if reason.count() > 0 and reason.is_visible():
            self.fill(reason, "")

        for radio_name in ("powerOfAttorneyNeeded", "approved"):
            panel.locator(f'input[name="{radio_name}"]').evaluate_all(
                "inputs => inputs.forEach(input => {"
                " input.checked = false;"
                " input.dispatchEvent(new Event('change', { bubbles: true }));"
                "})"
            )

        for label_text in ("Lender Name", "Mortgage Type"):
            combobox = (
                panel.locator("label")
                .filter(has_text=label_text)
                .locator("..")
                .get_by_role("combobox")
            )
            if combobox.count() > 0:
                combobox.scroll_into_view_if_needed()
                combobox.click()
                self.page.keyboard.press("Escape")
    


    def set_option_field(self, option_number: int, field: str, value: str):
        panel = self._option_panel(option_number)
        self.fill(panel.locator(f"#{field}"), value)

    def clear_option_field(self, option_number: int, field: str):
        self.set_option_field(option_number, field, "")

    def prepare_option_for_invalid_tests(self, option_number: int):
        """Fill minimum valid context so isolated invalid-field tests can run."""
        panel = self._option_panel(option_number)



        self._ensure_lender_selected(panel)
        self._select_combobox_option(panel, "Mortgage Type", "HELOC")
        self.fill(panel.locator("#mortgageLoanAmount"), "250000")
        self.fill(panel.locator("#requestedLTV"), "80")
        self.fill(panel.locator("#termRequested"), "25")
        self.fill(panel.locator("#rateRequested"), "5")


        self._select_panel_radio(panel, "powerOfAttorneyNeeded", "no")
        self._select_panel_radio(panel, "approved", "no")

    def fill_option_invalid_ltv(self, option_number: int, ltv: str):
        self.prepare_option_for_invalid_tests(option_number)
        self.fill(self._option_panel(option_number).locator("#requestedLTV"), ltv)
    

    def _wait_for_save_button_idle(self, panel) -> None:
        save_btn = panel.get_by_role("button", name="Save")
        expect(save_btn).to_be_visible(timeout=Config.TIMEOUT)
        expect(save_btn).to_be_enabled(timeout=Config.TIMEOUT)
        expect(save_btn).not_to_have_text(re.compile(r"Saving", re.I), timeout=Config.TIMEOUT)

    def wait_for_option_save_idle(self, panel, *, expect_success: bool = True) -> None:
        if expect_success:
            success = self.create_success_toast.or_(self.update_success_toast)
            expect(success.or_(self.stage_dialog).first).to_be_visible(
                timeout=Config.TIMEOUT
            )
            if self.stage_dialog.is_visible() or success.first.is_visible():
                return
        self._wait_for_save_button_idle(panel)

    def save_option(
        self, option_number: int, *, data=None, expect_success: bool = True
    ):
        panel = self._option_panel(option_number)
        if data is not None:
            self._ensure_option_ready_for_save(panel, data)
        else:
            self._ensure_lender_selected(panel)
        self.click(panel.get_by_role("button", name="Save"))
        self.wait_for_option_save_idle(panel, expect_success=expect_success)

    def verify_saved(self):
        panel = self._active_option_panel()
        if panel.count() > 0 and not self.stage_dialog.is_visible():
            self._assert_no_validation_errors(panel)
        success = self.create_success_toast.or_(self.update_success_toast)
        expect(success.first).to_be_visible(timeout=Config.TIMEOUT)
        self.verify_visible(success.first)

    def cancel_move_to_next_stage(self):
        self.wait_visible(self.stage_dialog)
        self.click(self.stage_cancel_btn)

    def move_to_next_stage(self):
        self.wait_visible(self.stage_dialog)
        self.click(self.move_next_btn)

    def verify_option_tab_enabled(self, option_number: int):
        tab = self.option_tab(option_number)
        expect(tab).to_be_enabled(timeout=30000)
        if option_number >= 2:
            panel = self._option_panel(option_number)
            self._wait_for_lenders_ready(panel)

    def capture_option_values_if_enabled(
        self, option_number: int, *, fallback: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Read option values when the tab is still accessible after stage moves."""
        tab = self.option_tab(option_number)
        try:
            expect(tab).to_be_enabled(timeout=5000)
            return self.capture_option_values(option_number)
        except Exception:
            if fallback is not None:
                return fallback
            raise

    def verify_option_tab_disabled(self, option_number: int):
        expect(self.option_tab(option_number)).to_be_disabled()

    def verify_moved_to_approved(self):
        from utils.stage_transition_verification import verify_immediate_stage_move

        verify_immediate_stage_move(
            self.page,
            success_toast="Lead moved to Approved successfully",
            url_tab="approved",
            active_tab=self.approved_tab,
        )

    def read_option_loan_amount(self, option_number: int) -> str:
        panel = self._option_panel(option_number)
        return panel.locator("#mortgageLoanAmount").input_value()

    def capture_option_values(self, option_number: int) -> dict[str, str]:
        """Read submitted option fields for persistence verification."""
        panel = self._option_panel(option_number)
        values = {
            "mortgageLoanAmount": panel.locator("#mortgageLoanAmount").input_value(),
            "requestedLTV": panel.locator("#requestedLTV").input_value(),
            "termRequested": panel.locator("#termRequested").input_value(),
            "rateRequested": panel.locator("#rateRequested").input_value(),
        }
        reason = panel.locator("#submittedRejectedReason")
        if reason.count() > 0 and reason.is_visible():
            values["submittedRejectedReason"] = reason.input_value()



        mortgage_type = self._panel_combobox(panel, "Mortgage Type")
        if mortgage_type.count() > 0:
            values["mortgageType"] = " ".join(mortgage_type.inner_text().split())



        lender = self._panel_combobox(panel, "Lender Name")
        if lender.count() > 0:
            values["lenderName"] = " ".join(lender.inner_text().split())

        for radio_name, key in (
            ("powerOfAttorneyNeeded", "powerOfAttorneyNeeded"),
            ("approved", "approved"),
        ):
            selected = self._read_panel_radio_value(panel, radio_name)
            if selected:
                values[key] = selected
        return values

    def reopen_submitted_tab(self) -> None:
        self.click(self.submitted_tab)
        expect(self.submitted_tab).to_have_attribute("data-state", "active", timeout=30000)
        expect(self.page).to_have_url(re.compile(r"tab=submitted"), timeout=30000)
