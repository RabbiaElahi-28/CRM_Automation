import re
import time

from pages.base_page import BasePage
from playwright.sync_api import Page, expect

from utils.config import Config


class PersistentNetworkError(Exception):
    """MS App network error did not recover after configured retries."""


class MortgageSnapshotAppLeadsPage(BasePage):
    """Mortgage Snapshot App /leads list."""

    NETWORK_ERROR_PATTERN = re.compile(r"Network Error", re.I)

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input = page.get_by_role(
            "textbox", name="Search client, email or VFLI"
        )
        self.logout_button = page.get_by_role("button", name="Logout")
        self.refresh_button = page.get_by_role("button", name="Refresh Data")

    def wait_for_leads(self) -> None:
        if "/mortgage-snapshot" in self.page.url:
            self.page.goto(f"{Config.MORTGAGE_SNAPSHOT_APP_URL}/leads")
        self.page.wait_for_url(re.compile(r".*/leads(?:\?.*)?$"), timeout=Config.TIMEOUT)
        expect(self.search_input).to_be_visible(timeout=Config.TIMEOUT)
        self.wait_for_leads_ready()

    def _network_error_visible(self) -> bool:
        alert = self.page.get_by_text(self.NETWORK_ERROR_PATTERN)
        if alert.count() == 0:
            return False
        try:
            return alert.first.is_visible()
        except Exception:
            return False

    def _dismiss_dialogs(self) -> bool:
        """Dismiss blocking dialogs. Returns True if a network error was dismissed."""
        dismissed_network = False
        if self._network_error_visible():
            dismissed_network = True
        for label in ("Ok", "OK", "Close"):
            button = self.page.get_by_role("button", name=label)
            if button.count() > 0:
                try:
                    if button.first.is_visible():
                        button.first.click()
                        self.page.wait_for_timeout(500)
                except Exception:
                    pass
        return dismissed_network

    def _table_has_rows(self) -> bool:
        empty = self.page.get_by_text("No leads are available", exact=True)
        if empty.count() > 0:
            try:
                if empty.is_visible():
                    return False
            except Exception:
                pass
        return self.page.locator("tbody tr").filter(has=self.page.locator("td")).count() > 0

    def wait_for_leads_ready(self, *, timeout_ms: int = 90000) -> None:
        deadline = time.time() + (timeout_ms / 1000)
        network_failures = 0
        max_network_retries = Config.MS_APP_NETWORK_ERROR_MAX_RETRIES

        while time.time() < deadline:
            had_network_error = self._dismiss_dialogs()
            if had_network_error:
                network_failures += 1
                if self.refresh_button.count() > 0 and self.refresh_button.is_visible():
                    self.click(self.refresh_button)
                self.page.wait_for_timeout(2000)
                if self._table_has_rows() and not self._network_error_visible():
                    return
                if network_failures >= max_network_retries:
                    raise PersistentNetworkError(
                        f"MS App network error persisted after {max_network_retries} retries"
                    )
                continue

            if self._table_has_rows():
                return
            if self.refresh_button.count() > 0 and self.refresh_button.is_visible():
                self.click(self.refresh_button)
            self.page.wait_for_timeout(2500)

        if self._network_error_visible():
            raise PersistentNetworkError(
                "MS App network error persisted while waiting for leads table"
            )
        expect(self.page.locator("tbody tr").first).to_be_visible(timeout=5000)

    def _lead_row(
        self,
        lead_name: str,
        *,
        email: str | None = None,
    ):
        """
        Locate the tbody row for this exact lead.

        MS App search is a loose substring filter — many unrelated leads may
        remain visible — so we match on the full deal name (and email when given).
        """
        rows = self.page.locator("tbody tr").filter(has=self.page.locator("td"))
        count = rows.count()
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
            except Exception:
                continue
            text = row.inner_text()
            if lead_name not in text:
                continue
            if email and email not in text:
                continue
            return row
        return None

    def _scan_visible_pages_for_lead(
        self,
        lead_name: str,
        *,
        email: str | None = None,
    ):
        """Walk pagination until the lead row appears or pages are exhausted."""
        for _ in range(15):
            row = self._lead_row(lead_name, email=email)
            if row is not None:
                return row
            next_btn = self.page.get_by_role("button", name="Next Page")
            if next_btn.count() == 0:
                break
            try:
                if next_btn.is_disabled():
                    break
            except Exception:
                break
            self.click(next_btn)
            self.page.wait_for_timeout(1200)
        return None

    def refresh_leads(self) -> None:
        had_network = self._dismiss_dialogs()
        if self.refresh_button.count() > 0 and self.refresh_button.is_visible():
            self.click(self.refresh_button)
            self.page.wait_for_timeout(1500)
        if had_network and self._network_error_visible():
            raise PersistentNetworkError("MS App network error after refresh")

    def _apply_search_term(self, term: str) -> None:
        self.fill(self.search_input, "")
        self.fill(self.search_input, term)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000)

    _SEARCH_STOP_WORDS = frozenset({"deal", "automation"})

    @classmethod
    def _name_search_terms(
        cls,
        lead_name: str,
        *,
        applicant_first_name: str | None = None,
    ) -> list[str]:
        """Build human-name search terms; skip Automation Deal suffix tokens."""
        terms: list[str] = [lead_name]
        parts = lead_name.split()

        if applicant_first_name:
            first = applicant_first_name.strip()
            if first:
                terms.append(first)

        automation_idx = next(
            (i for i, part in enumerate(parts) if part.lower() == "automation"),
            len(parts),
        )
        name_parts = parts[:automation_idx] if automation_idx > 0 else parts[:2]
        if len(name_parts) >= 2:
            terms.append(" ".join(name_parts[:2]))
        elif (
            len(name_parts) == 1
            and name_parts[0].lower() not in cls._SEARCH_STOP_WORDS
        ):
            terms.append(name_parts[0])

        return terms

    @classmethod
    def _search_terms(
        cls,
        lead_name: str,
        *,
        vfli: str | None = None,
        email: str | None = None,
        applicant_first_name: str | None = None,
    ) -> list[str]:
        terms = cls._name_search_terms(
            lead_name, applicant_first_name=applicant_first_name
        )
        if vfli:
            terms.append(vfli)
        if email:
            terms.append(email)
        deduped: list[str] = []
        for term in terms:
            cleaned = term.strip()
            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)
        return deduped

    def _assert_lead_row_visible(
        self,
        row,
        lead_name: str,
        *,
        search_term: str | None = None,
        email: str | None = None,
    ) -> None:
        if row is None:
            detail = f" when searching {search_term!r}" if search_term else ""
            email_note = f" (email={email!r})" if email else ""
            raise AssertionError(
                f"Lead {lead_name!r} not visible in MS App leads list{detail}{email_note}"
            )
        expect(row).to_be_visible(timeout=Config.TIMEOUT)

    def search_by_deal_name(
        self,
        lead_name: str,
        *,
        email: str | None = None,
        vfli: str | None = None,
        wait_for_sync: bool = False,
        wait_timeout_ms: int | None = None,
    ) -> None:
        """Search the leads list using the full deal name only."""
        if wait_for_sync:
            self.search_lead(
                lead_name,
                vfli=vfli,
                email=email,
                wait_timeout_ms=wait_timeout_ms or Config.MS_APP_LEAD_SYNC_TIMEOUT_MS,
            )

        self.fill(self.search_input, "")
        self._apply_search_term(lead_name)
        row = self._lead_row(lead_name, email=email)
        if row is None:
            row = self._scan_visible_pages_for_lead(lead_name, email=email)
        assert row is not None, (
            f"Lead {lead_name!r} not found in MS App when searching by deal name"
        )
        expect(row).to_be_visible(timeout=Config.TIMEOUT)

    def verify_identifiers_then_open_presentation(
        self,
        lead_name: str,
        *,
        vfli: str | None = None,
        email: str | None = None,
        applicant_first_name: str | None = None,
        wait_timeout_ms: int | None = None,
    ) -> None:
        """
        Sync/search lead, verify every identifier finds it, then search by deal
        name and open the presentation.
        """
        self.search_lead(
            lead_name,
            vfli=vfli,
            email=email,
            wait_timeout_ms=wait_timeout_ms,
        )
        self.verify_lead_search_all_identifiers(
            lead_name,
            vfli=vfli,
            email=email,
            applicant_first_name=applicant_first_name,
        )
        self.search_by_deal_name(lead_name, email=email)
        self.open_lead_presentation(lead_name)

    def search_lead(
        self,
        lead_name: str,
        *,
        vfli: str | None = None,
        email: str | None = None,
        wait_timeout_ms: int | None = None,
    ) -> None:
        wait_timeout_ms = wait_timeout_ms or Config.MS_APP_LEAD_SYNC_TIMEOUT_MS
        self.wait_for_leads_ready(timeout_ms=min(wait_timeout_ms, 90000))
        terms = self._search_terms(
            lead_name,
            vfli=vfli,
            email=email,
        )
        deadline = time.time() + (wait_timeout_ms / 1000)
        network_failures = 0

        while time.time() < deadline:
            had_network = self._dismiss_dialogs()
            if had_network:
                network_failures += 1
                if network_failures >= Config.MS_APP_NETWORK_ERROR_MAX_RETRIES:
                    raise PersistentNetworkError(
                        f"MS App network error persisted during lead search "
                        f"after {network_failures} retries"
                    )
            self.refresh_leads()
            if not self._table_has_rows():
                self.page.wait_for_timeout(Config.MS_APP_SEARCH_INTERVAL_MS)
                continue

            # Clear search and scan all pages (lead may not match filter until synced).
            self.fill(self.search_input, "")
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)
            row = self._scan_visible_pages_for_lead(lead_name, email=email)
            if row is not None:
                return

            for term in terms:
                self._apply_search_term(term)
                row = self._lead_row(lead_name, email=email)
                if row is not None:
                    return
                row = self._scan_visible_pages_for_lead(lead_name, email=email)
                if row is not None:
                    return

            self.page.wait_for_timeout(Config.MS_APP_SEARCH_INTERVAL_MS)

        if self._network_error_visible():
            raise PersistentNetworkError("MS App network error blocked lead search")
        row = self._lead_row(lead_name, email=email)
        if row is None:
            raise AssertionError(
                f"Lead {lead_name!r} not found in MS App after "
                f"{wait_timeout_ms / 1000:.0f}s (sync/search)"
            )
        expect(row).to_be_visible(timeout=5000)

    def verify_lead_search_all_identifiers(
        self,
        lead_name: str,
        *,
        vfli: str | None = None,
        email: str | None = None,
        applicant_first_name: str | None = None,
    ) -> None:
        """Confirm the lead is findable by every supported search term."""
        terms = self._search_terms(
            lead_name,
            vfli=vfli,
            email=email,
            applicant_first_name=applicant_first_name,
        )
        for term in terms:
            self.fill(self.search_input, "")
            self.fill(self.search_input, term)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(2000)
            row = self._lead_row(lead_name, email=email)
            if row is None:
                row = self._scan_visible_pages_for_lead(lead_name, email=email)
            self._assert_lead_row_visible(
                row,
                lead_name,
                search_term=term,
                email=email,
            )

    def close_presentation(self) -> None:
        """Return to the MS App leads list from an open presentation."""
        if "/leads" not in self.page.url:
            self.page.goto(f"{Config.MORTGAGE_SNAPSHOT_APP_URL}/leads")
            self.wait_for_leads()

    def open_lead_presentation(self, lead_name: str) -> None:
        row = self._lead_row(lead_name)
        assert row is not None, f"Lead row not found for {lead_name!r}"
        expect(row).to_be_visible(timeout=Config.TIMEOUT)
        action_btn = row.get_by_role(
            "button", name=re.compile(r"Mortgage Snapshot|Fill Snapshot Form", re.I)
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
        """
        Hard-fail when a non-assigned user can find or open the lead in MS App.

        Uses short, deterministic checks (no sync polling).
        """
        from utils.ms_app_rbac import MsAppRbacViolation

        terms = self._search_terms(
            lead_name,
            vfli=vfli,
            email=email,
            applicant_first_name=applicant_first_name,
        )

        self.refresh_leads()

        def _raise(reason: str) -> None:
            raise MsAppRbacViolation(
                f"MS App RBAC violation for lead {lead_name!r}: {reason}"
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
            presentation_root = self.page.locator(".font-ubuntu.h-full.w-full").first
            if presentation_root.count() > 0:
                try:
                    if presentation_root.is_visible():
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

        # No row matched any search term — expected for non-assigned users.
        if not _row_is_visible():
            return
        _raise("lead row visible after all search checks")

    def logout(self) -> None:
        from pages.mortgage_snapshot_app.login_page import (
            MortgageSnapshotAppLoginPage,
            _LEADS_URL,
            _clear_ms_app_storage,
        )

        login = MortgageSnapshotAppLoginPage(self.page)
        if self.logout_button.count() > 0 and self.logout_button.is_visible():
            self.click(self.logout_button)
            try:
                self.page.wait_for_url(
                    re.compile(r"mortgagesnapshot\.[^/]+/?(?:\?.*)?$", re.I),
                    timeout=15000,
                )
            except Exception:
                pass
        _clear_ms_app_storage(self.page)
        login.open(clear_storage=False)
        if _LEADS_URL.search(self.page.url):
            _clear_ms_app_storage(self.page)
            self.page.goto(f"{Config.MORTGAGE_SNAPSHOT_APP_URL.rstrip('/')}/")
            self.page.wait_for_load_state("domcontentloaded")
        login.wait_for_login_form()
