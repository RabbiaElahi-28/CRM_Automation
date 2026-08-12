import re

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.compliance_page import CompliancePage
from test_page_data.compliance_data import SignedFormSnapshot
from utils.config import Config
from utils.entity_navigation import (
    CLIENT_CARE_BUCKET,
    open_bucket_record,
    verify_bucket_record_visible,
)

_CLIENT_CARE_PATH = "/client-care"
_JUST_CLOSED_TAB_VALUE = "just-closed"


class ClientCarePage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self._compliance = CompliancePage(page)

        # ===============================
        # Navigation
        # ===============================

        self.client_care_link = page.get_by_role("link", name="Client Care")
        self.list_search = page.locator('[name="list-global-search"]')
        self.global_search = page.get_by_role(
            "textbox", name=re.compile("Search leads", re.I)
        )

        self.profile_tab = page.get_by_role("tab", name="Profile", exact=True)

        # self.just_closed_tab = page.get_by_role("tab", name="Just Closed")
        # self.just_closed_title = page.locator("[role='tabpanel']").get_by_text(
        #     "Just Closed", exact=True
        # )
        self.profile_tab_panel = page.get_by_role("tabpanel", name="Profile")
        self.just_closed_tab = page.get_by_role("tab", name="Just Closed", exact=True)
        self.just_closed_tab_panel = page.get_by_role("tabpanel", name="Just Closed")
        self.client_profile_heading = page.get_by_text(
            "Please Review Your Client Profile", exact=True
        )
        self.financial_profile_heading = page.get_by_text(
            "Client Financial Profile", exact=True
        )
        self.important_notes_heading = page.get_by_text(
            "Important Client Notes", exact=True
        )

    # ===============================
    # Navigation
    # ===============================

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

    def verify_lead_searchable(self, deal_name: str):
        # self._compliance._search_client_care_board(deal_name)
        # record = self._compliance._client_care_record_link(deal_name)
        # expect(record.first).to_be_visible(timeout=30000)
        verify_bucket_record_visible(self.page, CLIENT_CARE_BUCKET, deal_name)

    def open_client_care_deal(self, deal_name: str):
        # self._compliance._search_client_care_board(deal_name)
        # record = self._compliance._client_care_record_link(deal_name)
        # record.first.wait_for(state="visible", timeout=30000)
        # record.first.click()
        # self.page.wait_for_load_state("networkidle")
        # expect(self.page).to_have_url(re.compile(rf"{_CLIENT_CARE_PATH}/"))
        open_bucket_record(self.page, CLIENT_CARE_BUCKET, deal_name)

    def _deal_detail_url(self) -> str:
        return self.page.url.split("?")[0]

    def _navigate_client_care_tab(self, tab: str) -> None:
        """Switch tabs via URL — Client Care syncs Radix tabs with ?tab= query param."""
        base = self._deal_detail_url()
        target = base if tab == "profile" else f"{base}?tab={tab}"
        if self.page.url != target:
            self.page.goto(
                target,
                wait_until="domcontentloaded",
                timeout=Config.TIMEOUT,
            )
            try:
                self.page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

    def _assert_just_closed_tab_active(self) -> None:
        expect(self.page).to_have_url(
            re.compile(r"([?&])tab=just-closed"), timeout=Config.TIMEOUT
        )
        expect(self.just_closed_tab).to_have_attribute(
            "data-state", "active", timeout=Config.TIMEOUT
        )
        expect(self.profile_tab_panel).to_be_hidden(timeout=Config.TIMEOUT)
        expect(self.just_closed_tab_panel).to_be_visible(timeout=Config.TIMEOUT)

    def _ensure_just_closed_tab_active(self) -> None:
        if (
            "tab=just-closed" in self.page.url
            and self.just_closed_tab.get_attribute("data-state") == "active"
            and not self.profile_tab_panel.is_visible()
        ):
            expect(self.just_closed_tab_panel).to_be_visible(timeout=5000)
            return
        self.open_just_closed_tab()

    def _just_closed_tab_panel(self):
        return self.just_closed_tab_panel

    def open_just_closed_tab(self):

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                self._navigate_client_care_tab(_JUST_CLOSED_TAB_VALUE)
                self.just_closed_tab.scroll_into_view_if_needed()
                if self.just_closed_tab.get_attribute("data-state") != "active":
                    self.click(self.just_closed_tab)
                self._assert_just_closed_tab_active()
                self._compliance.wait_for_signed_form_readonly_ready()
                return
            except Exception as exc:
                last_error = exc
                if attempt == 2:
                    raise
                self.page.wait_for_timeout(1000)
        if last_error is not None:
            raise last_error

    def open_profile_tab(self):
        self._navigate_client_care_tab("profile")
        expect(self.profile_tab).to_have_attribute(
            "data-state", "active", timeout=Config.TIMEOUT
        )
        expect(self.profile_tab_panel).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.page).not_to_have_url(re.compile(r"tab=just-closed"))

    def verify_on_client_care_list(self):
        expect(self.page).to_have_url(re.compile(rf"{_CLIENT_CARE_PATH}/?$"))

    # ===============================
    # Just Closed verification
    # ===============================

    def _just_closed_scope(self):
        return self._just_closed_tab_panel()

    def verify_just_closed_sections_visible(self):
        self._ensure_just_closed_tab_active()
        self.verify_visible(self.client_profile_heading)
        self.verify_visible(self.financial_profile_heading)
        self.verify_visible(self.important_notes_heading)

    def verify_just_closed_readonly(self):
        self._ensure_just_closed_tab_active()
        self._compliance.verify_signed_form_readonly()

    def verify_just_closed_has_no_save_action(self):
        self._ensure_just_closed_tab_active()
        scope = self._just_closed_scope()
        expect(scope.get_by_role("button", name="Save")).to_have_count(0)
        expect(scope.get_by_role("button", name="Save Data")).to_have_count(0)
        expect(scope.get_by_role("button", name="Complete Stage")).to_have_count(0)

    def read_just_closed_values(self) -> SignedFormSnapshot:
        self._ensure_just_closed_tab_active()
        return self._compliance.read_signed_form_readonly_values()

    def verify_just_closed_has_data(self, snapshot: SignedFormSnapshot):
        self._ensure_just_closed_tab_active()
        self._compliance.verify_signed_form_has_data(snapshot)

    def verify_just_closed_matches(self, baseline: SignedFormSnapshot):
        self._ensure_just_closed_tab_active()
        self._compliance.verify_signed_form_matches(baseline)
