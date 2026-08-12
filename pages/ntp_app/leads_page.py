import re

from pages.mortgage_snapshot_app.leads_page import MortgageSnapshotAppLeadsPage
from playwright.sync_api import Page, expect

from utils.config import Config


class NtpAppLeadsPage(MortgageSnapshotAppLeadsPage):
    """NTP App /leads list — reuses MS App search/sync with NTP-specific navigation."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input = page.get_by_role(
            "textbox", name=re.compile(r"Search Name, Email, or VFLI", re.I)
        )

    def wait_for_leads(self) -> None:
        if "/ntp" in self.page.url and "/leads" not in self.page.url:
            self.page.goto(f"{Config.NTP_APP_URL.rstrip('/')}/leads")
        self.page.wait_for_url(re.compile(r".*/leads(?:\?.*)?$"), timeout=Config.TIMEOUT)
        expect(self.search_input).to_be_visible(timeout=Config.TIMEOUT)
        self.wait_for_leads_ready()

    def close_presentation(self) -> None:
        if "/leads" not in self.page.url:
            self.page.goto(f"{Config.NTP_APP_URL.rstrip('/')}/leads")
            self.wait_for_leads()

    def open_lead_presentation(self, lead_name: str) -> None:
        row = self._lead_row(lead_name)
        assert row is not None, f"Lead row not found for {lead_name!r}"
        expect(row).to_be_visible(timeout=Config.TIMEOUT)
        action_btn = row.get_by_role(
            "button", name=re.compile(r"View NTP|NTP", re.I)
        ).first
        expect(action_btn).to_be_visible(timeout=Config.TIMEOUT)
        self.click(action_btn)

    def assert_lead_not_accessible(
        self,
        lead_name: str,
        *,
        vfli: str | None = None,
        email: str | None = None,
        applicant_first_name: str | None = None,
        presentation_url: str | None = None,
    ) -> None:
        from utils.ntp_app_rbac import NtpAppRbacViolation

        terms = self._search_terms(
            lead_name,
            vfli=vfli,
            email=email,
            applicant_first_name=applicant_first_name,
        )

        self.refresh_leads()

        def _raise(reason: str) -> None:
            raise NtpAppRbacViolation(
                f"NTP App RBAC violation for lead {lead_name!r}: {reason}"
            )

        def _row_is_visible() -> bool:
            row = self._lead_row(lead_name, email=email)
            return row is not None

        self.fill(self.search_input, "")
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)
        if self._scan_visible_pages_for_lead(lead_name, email=email) is not None:
            _raise("lead row visible in unfiltered leads list")

        for term in terms:
            self._apply_search_term(term)
            if _row_is_visible():
                _raise(f"lead row visible when searching {term!r}")
            if self._scan_visible_pages_for_lead(lead_name, email=email) is not None:
                _raise(f"lead row visible across pages when searching {term!r}")

        if presentation_url and "/leads" not in presentation_url:
            self.page.goto(presentation_url)
            self.page.wait_for_load_state("domcontentloaded")
            review_text = self.page.get_by_text(
                re.compile(r"reviewed the plan in detail", re.I)
            )
            if review_text.count() > 0:
                try:
                    if review_text.first.is_visible():
                        _raise(
                            f"cached/direct presentation URL still accessible: "
                            f"{presentation_url}"
                        )
                except Exception:
                    pass
            lead_heading = self.page.get_by_text(lead_name, exact=False)
            if lead_heading.count() > 0:
                try:
                    if lead_heading.first.is_visible():
                        _raise(
                            f"lead name visible via direct URL {presentation_url!r}"
                        )
                except Exception:
                    pass

        empty = self.page.get_by_text("No leads are available", exact=True)
        if empty.count() > 0:
            try:
                if empty.is_visible():
                    return
            except Exception:
                pass

        if not _row_is_visible():
            return
        _raise("lead row visible after all search checks")

    def logout(self) -> None:
        from pages.ntp_app.login_page import (
            NtpAppLoginPage,
            _LEADS_URL,
            _clear_ntp_app_storage,
        )

        login = NtpAppLoginPage(self.page)
        if self.logout_button.count() > 0 and self.logout_button.is_visible():
            self.click(self.logout_button)
            try:
                self.page.wait_for_url(
                    re.compile(r"ntp\.[^/]+/?(?:\?.*)?$", re.I),
                    timeout=15000,
                )
            except Exception:
                pass
        _clear_ntp_app_storage(self.page)
        login.open(clear_storage=False)
        if _LEADS_URL.search(self.page.url):
            _clear_ntp_app_storage(self.page)
            self.page.goto(f"{Config.NTP_APP_URL.rstrip('/')}/")
            self.page.wait_for_load_state("domcontentloaded")
        login.wait_for_login_form()
