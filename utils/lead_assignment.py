"""Post-create helper: assign an agent from Lead Bucket general info only."""

import re
from urllib.parse import quote

from playwright.sync_api import Page, expect

from test_page_data import test_entities
from utils.config import Config
from utils.entity_navigation import LEAD_BUCKET, MY_DEALS_BUCKET, open_bucket_record
from utils.toast import Toast

GENERAL_INFO_UPDATED_TOAST = "Lead details updated successfully"
_SALES_DETAIL_PATH = re.compile(r"/sales/[^/?]+")
_SALES_BACKEND_DETAIL_PATH = re.compile(r"/sales-backend/[^/?]+")
_DETAIL_PATH = re.compile(
    r"/(lead-bucket|my-leads|sales-backend|sales|compliance|marketing|client-care)/[^/?#]+"
)
_STATUS_SCOPE_BY_PATH = {
    "lead-bucket": "lead_bucket",
    "my-leads": "lead",
    "sales-backend": "renewal",
    "sales": "application",
    "marketing": "marketing",
    "compliance": "closed",
    "client-care": "client",
}


def _agent_label_matches(actual: str, expected: str) -> bool:
    actual_name = actual.split("(", maxsplit=1)[0].strip().lower()
    expected_name = expected.split("(", maxsplit=1)[0].strip().lower()
    if expected_name not in actual_name and actual_name not in expected_name:
        return False
    if "(" in expected:
        role = expected.split("(", maxsplit=1)[1].rstrip(")").strip().lower()
        return role in actual.lower()
    return True


class LeadAssignmentHelper:
    """Assign-agent-only flow from Lead Bucket. Does not touch Edit Lead tests."""

    def __init__(self, page: Page):
        self.page = page

    def _edit_lead_section(self):
        return self.page.locator("main").filter(
            has=self.page.get_by_role("button", name="Back to Lead Info")
        )

    def _general_info_form(self):
        """LeadGeneralInfoForm — first form on /edit-lead (Assigned, Status, Source)."""
        section = self._edit_lead_section()
        form = section.locator("form").first
        expect(form.get_by_role("combobox").first).to_be_visible(timeout=30000)
        return form

    def _general_info_visible(self) -> bool:
        section = self._edit_lead_section()
        form = section.locator("form").first
        if form.count() == 0:
            return False
        try:
            return form.is_visible()
        except Exception:
            return False

    def _assigned_combobox(self):
        return self._general_info_form().get_by_role("combobox").nth(0)

    def _status_combobox(self):
        return self._general_info_form().get_by_role("combobox").nth(1)

    def open_lead_in_lead_bucket(self, lead_name: str):
        open_bucket_record(self.page, LEAD_BUCKET, lead_name)

    def open_edit_lead_from_menu(self):
        """Open general-info edit form — direct /edit-lead navigation (avoids header menu flake)."""
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        if "/edit-lead/" in self.page.url:
            expect(self._assigned_combobox()).to_be_visible(timeout=30000)
            return

        expect(self.page.get_by_role("tab", name="Profile")).to_be_visible(
            timeout=30000
        )

        match = _DETAIL_PATH.search(self.page.url)
        if not match:
            raise AssertionError(f"Not on lead detail page: {self.page.url}")

        path_segment = match.group(1)
        lead_id = self.page.url.split(f"/{path_segment}/", maxsplit=1)[1].split("?")[0]
        status_scope = _STATUS_SCOPE_BY_PATH.get(path_segment)
        query = f"?statusScope={quote(status_scope)}" if status_scope else ""
        self.page.goto(f"{Config.BASE_URL}/edit-lead/{lead_id}{query}")
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        expect(self._assigned_combobox()).to_be_visible(timeout=30000)

    def _select_combobox_option(self, combobox, option_label: str):
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        expect(combobox).to_be_enabled(timeout=30000)
        combobox.scroll_into_view_if_needed()
        combobox.click()

        option = self.page.get_by_role("option", name=option_label, exact=True)
        if option.count() == 0:
            name_part = option_label.split("(", maxsplit=1)[0].strip()
            role_part = (
                option_label.split("(", maxsplit=1)[1].rstrip(")").strip()
                if "(" in option_label
                else ""
            )
            option = self.page.get_by_role("option").filter(
                has_text=re.compile(re.escape(name_part), re.I)
            )
            if role_part:
                option = option.filter(
                    has_text=re.compile(re.escape(role_part), re.I)
                )
        expect(option.first).to_be_visible(timeout=10000)
        option.first.click()
        self.page.keyboard.press("Escape")

    def select_assigned_agent(self, agent_label: str):
        self._select_combobox_option(self._assigned_combobox(), agent_label)

    def select_status(self, status_label: str):
        self._select_combobox_option(self._status_combobox(), status_label)

    def save_general_info(self):
        save_button = self._general_info_form().get_by_role("button", name="Save")
        expect(save_button).to_be_enabled(timeout=10000)
        save_button.click()

    def get_assigned_agent_label(self) -> str:
        combobox = self._assigned_combobox()
        expect(combobox).to_contain_text("(", timeout=30000)
        return combobox.inner_text().strip()

    def _save_and_assert_toast(self):
        self.save_general_info()
        Toast(self.page).assert_message(GENERAL_INFO_UPDATED_TOAST)

    def _return_to_detail_after_edit(self, url_pattern: re.Pattern[str]) -> None:
        """CRM may stay on /edit-lead after save; navigate back to detail if needed."""
        try:
            expect(self.page).to_have_url(url_pattern, timeout=5000)
            return
        except AssertionError:
            pass

        edit_match = re.search(r"/edit-lead/([^/?#]+)", self.page.url)
        if not edit_match:
            raise AssertionError(
                f"Expected detail URL matching {url_pattern.pattern!r}, "
                f"got {self.page.url!r} (not edit-lead either)"
            )

        lead_id = edit_match.group(1)
        if url_pattern is _SALES_DETAIL_PATH:
            target = f"{Config.BASE_URL}/sales/{lead_id}?statusScope=application"
        elif url_pattern is _SALES_BACKEND_DETAIL_PATH:
            target = f"{Config.BASE_URL}/sales-backend/{lead_id}?statusScope=renewal"
        else:
            raise AssertionError(f"Unsupported detail redirect pattern: {url_pattern.pattern!r}")

        self.page.goto(target)
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        expect(self.page).to_have_url(url_pattern, timeout=Config.TIMEOUT)

    def assign_nova_worksheet_status_only(
        self,
        lead_name: str,
        status_label: str | None = None,
        *,
        bucket: str = LEAD_BUCKET,
    ) -> str:
        """Set Nova Worksheet status without changing the assigned agent."""
        if status_label is None:
            status_label = (
                "Nova Worksheet"
                if bucket == MY_DEALS_BUCKET
                else test_entities.NOVA_BYPASS_STATUS_LABEL
            )
        open_bucket_record(self.page, bucket, lead_name)
        self.open_edit_lead_from_menu()
        self.select_status(status_label)
        self._save_and_assert_toast()
        self._return_to_detail_after_edit(_SALES_DETAIL_PATH)
        return lead_name

    def assign_fe_nova_bypass(
        self,
        lead_name: str,
        agent_label: str | None = None,
        status_label: str | None = None,
        *,
        bucket: str = LEAD_BUCKET,
    ) -> str:
        """Assign FE agent + Nova Worksheet status and wait for /sales redirect."""
        agent_label = agent_label or test_entities.FE_AGENT_LABEL
        if status_label is None:
            status_label = (
                "Nova Worksheet"
                if bucket == MY_DEALS_BUCKET
                else test_entities.NOVA_BYPASS_STATUS_LABEL
            )
   

        open_bucket_record(self.page, bucket, lead_name)
        self.open_edit_lead_from_menu()
        self.select_assigned_agent(agent_label)
        self.select_status(status_label)
        self._save_and_assert_toast()
        self._return_to_detail_after_edit(_SALES_DETAIL_PATH)
        return lead_name

    def assign_be_backend(
        self,
        lead_name: str,
        agent_label: str | None = None,
        status_label: str | None = None,
    ) -> str:
        """Assign BE agent + Application Received (Sales Backend) from Lead Bucket and wait for redirect."""
        agent_label = agent_label or test_entities.BE_AGENT_LABEL
        status_label = status_label or test_entities.BE_STATUS_LABEL

        self.open_lead_in_lead_bucket(lead_name)
        self.open_edit_lead_from_menu()
        self.select_assigned_agent(agent_label)
        self.select_status(status_label)
        self._save_and_assert_toast()
        self._return_to_detail_after_edit(_SALES_BACKEND_DETAIL_PATH)
        return lead_name

    def assign_backend_status_only(
        self,
        lead_name: str,
        status_label: str | None = None,
    ) -> str:
        """Set Sales Backend status without changing the assigned agent."""
        status_label = status_label or test_entities.BE_STATUS_LABEL
        self.open_lead_in_lead_bucket(lead_name)
        self.open_edit_lead_from_menu()
        self.select_status(status_label)
        self._save_and_assert_toast()
        self._return_to_detail_after_edit(_SALES_BACKEND_DETAIL_PATH)
        return lead_name


def reassign_lead_agent(
    page: Page,
    lead_name: str,
    agent_label: str,
    *,
    bucket: str = LEAD_BUCKET,
) -> None:
    """Reassign agent from lead detail (via bucket navigation) without changing status."""
    from utils.entity_navigation import SALES_BACKEND_BUCKET

    helper = LeadAssignmentHelper(page)
    open_bucket_record(page, bucket, lead_name)
    helper.open_edit_lead_from_menu()
    helper.select_assigned_agent(agent_label)
    helper._save_and_assert_toast()
    detail_pattern = (
        _SALES_BACKEND_DETAIL_PATH
        if bucket == SALES_BACKEND_BUCKET
        else _SALES_DETAIL_PATH
    )
    helper._return_to_detail_after_edit(detail_pattern)


def assign_agent_after_create(page: Page, lead_name: str | None = None) -> None:
    """Open Lead Bucket, assign agent, save, and verify persistence."""
    from utils.lead_context import get_active_lead_name

    lead_name = lead_name or get_active_lead_name()
    agent = test_entities.ASSIGNED_AGENT
    helper = LeadAssignmentHelper(page)

    helper.open_lead_in_lead_bucket(lead_name)
    helper.open_edit_lead_from_menu()
    helper.select_assigned_agent(agent)
    helper.save_general_info()
    Toast(page).assert_message(GENERAL_INFO_UPDATED_TOAST)

    helper.open_lead_in_lead_bucket(lead_name)
    helper.open_edit_lead_from_menu()
    actual = helper.get_assigned_agent_label()
    assert _agent_label_matches(actual, agent), actual
