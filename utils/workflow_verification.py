"""Reusable workflow transition verification helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect

from test_page_data import workflow_expectations as we
from utils.config import Config
from utils.entity_navigation import verify_bucket_record_visible
from utils.toast import Toast


@dataclass
class TransitionExpectation:
    """Expected UI state after a workflow transition."""

    expected_url_pattern: str | None = None
    success_toast: str | None = None
    expected_status_label: str | None = None
    expected_status_contains: str | None = None
    visible_tabs: list[str] | None = None
    hidden_tabs: list[str] | None = None
    next_status_id: int | None = None
    is_admin: bool = True
    has_full_access: bool = True
    include_dlo: bool = False
    expected_agent_label: str | None = None
    bucket_name: str | None = None
    record_name: str | None = None
    expected_kanban_column: str | None = None


MOVE_TO_SALES_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.MOVE_TO_SALES_URL_PATTERN,
    success_toast=we.MOVE_TO_SALES_SUCCESS_TOAST,
    expected_status_contains=we.MOVE_TO_SALES_STATUS_CONTAINS,
    visible_tabs=we.MOVE_TO_SALES_VISIBLE_TABS,
    hidden_tabs=we.MOVE_TO_SALES_HIDDEN_TABS,
    next_status_id=we.MOVE_TO_SALES_NEXT_STATUS_ID,
    bucket_name=we.KANBAN_BUCKETS["my_deals"],
)

FE_NOVA_BYPASS_SALES_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_frontend_detail"],
    expected_status_contains=we.NOVA_BYPASS_STATUS_CONTAINS,
    visible_tabs=we.FE_NOVA_BYPASS_VISIBLE_TABS,
    hidden_tabs=we.FE_NOVA_BYPASS_HIDDEN_TABS,
    next_status_id=we.NOVA_BYPASS_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["my_deals"],
)

BE_ASSIGNMENT_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_backend_detail"],
    expected_status_contains=we.BE_STATUS_CONTAINS,
    visible_tabs=we.BE_ASSIGNMENT_VISIBLE_TABS,
    hidden_tabs=we.BE_ASSIGNMENT_HIDDEN_TABS,
    next_status_id=we.BE_APPLICATION_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["sales_backend"],
)

BE_MORTGAGE_SNAPSHOT_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_backend_detail"],
    success_toast=we.BE_MORTGAGE_SNAPSHOT_SUCCESS_TOAST,
    expected_status_contains=we.RENEWAL_MORTGAGE_SNAPSHOT_STATUS_NAME,
    
    visible_tabs=we.BE_MORTGAGE_SNAPSHOT_VISIBLE_TABS,
    hidden_tabs=we.BE_MORTGAGE_SNAPSHOT_HIDDEN_TABS,
    next_status_id=we.BE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["sales_backend"],
    expected_kanban_column=we.RENEWAL_MORTGAGE_SNAPSHOT_STATUS_NAME,
   
)

BE_APPRAISAL_ORDER_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_backend_detail"],
    success_toast=we.BE_APPRAISAL_ORDER_SUCCESS_TOAST,
    expected_status_contains=we.RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
    
    hidden_tabs=we.BE_APPRAISAL_ORDER_HIDDEN_TABS,
    next_status_id=we.BE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["sales_backend"],
    expected_kanban_column=we.RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
)

BE_SUBMITTED_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_backend_detail"],
    success_toast=we.BE_SUBMITTED_SUCCESS_TOAST,
    expected_status_contains=we.RENEWAL_SUBMITTED_STATUS_NAME,
   
    visible_tabs=we.BE_SUBMITTED_VISIBLE_TABS,
    hidden_tabs=we.BE_SUBMITTED_HIDDEN_TABS,
    next_status_id=we.BE_SUBMITTED_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["sales_backend"],
    expected_kanban_column=we.RENEWAL_SUBMITTED_STATUS_NAME,
    
)

BE_APPROVED_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_backend_detail"],
    success_toast=we.BE_APPROVED_SUCCESS_TOAST,
    expected_status_contains=we.RENEWAL_APPROVED_STATUS_NAME,
    
    visible_tabs=we.BE_APPROVED_VISIBLE_TABS,
    hidden_tabs=we.BE_APPROVED_HIDDEN_TABS,
    next_status_id=we.BE_APPROVED_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["sales_backend"],
    expected_kanban_column=we.RENEWAL_APPROVED_STATUS_NAME,
   
)

BE_SIGNED_TRANSITION = TransitionExpectation(
    expected_url_pattern=we.URL_PATTERNS["sales_backend_detail"],
    success_toast=we.BE_SIGNED_SUCCESS_TOAST,
    expected_status_contains=we.RENEWAL_SIGNED_STATUS_NAME,
    visible_tabs=we.BE_SIGNED_VISIBLE_TABS,
    hidden_tabs=we.BE_SIGNED_HIDDEN_TABS,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
    bucket_name=we.KANBAN_BUCKETS["sales_backend"],
)

FE_NON_ASSIGNED_RESTRICTED = TransitionExpectation(
    visible_tabs=we.FE_NON_ASSIGNED_VISIBLE_TABS,
    hidden_tabs=we.FE_NON_ASSIGNED_HIDDEN_TABS,
    is_admin=False,
    has_full_access=False,
)

BE_NON_ASSIGNED_RESTRICTED = TransitionExpectation(
    visible_tabs=we.BE_NON_ASSIGNED_VISIBLE_TABS,
    hidden_tabs=we.BE_NON_ASSIGNED_HIDDEN_TABS,
    is_admin=False,
    has_full_access=False,
)


class WorkflowVerification:
    """Assert post-transition UI state on lead detail and kanban views."""

    def __init__(self, page: Page):
        self.page = page

    def verify_url(self, pattern: str) -> None:
        expect(self.page).to_have_url(
            re.compile(pattern),
            timeout=Config.TIMEOUT,
        )

    def verify_status_badge(
        self,
        *,
        label: str | None = None,
        contains: str | None = None,
    ) -> None:
        """LeadInfoHeader status badge beside Push to Scarlett / action buttons."""
        badge = self._status_badge_locator()
        if label is not None:
            expect(badge.filter(has_text=label).first).to_be_visible(
                timeout=Config.TIMEOUT,
            )
            return
        if contains is not None:
            expect(badge.filter(has_text=re.compile(re.escape(contains))).first).to_be_visible(
                timeout=Config.TIMEOUT,
            )
            return
        raise ValueError("verify_status_badge requires label or contains")

    def wait_for_status_badge_contains(self, text: str) -> None:
        """Poll until profile status badge reflects post-transition CRM state."""
        expect(self._status_badge_locator()).to_contain_text(text, timeout=Config.TIMEOUT)

    def _status_badge_locator(self):
        return self.page.locator("main").locator(
            "div.flex.h-9.items-center.justify-center.rounded-md.border.px-2.text-sm.font-medium"
        ).first

    def verify_kanban_columns(self, bucket_name: str, expected_columns: list[str]) -> None:
        from utils.kanban_verification import verify_kanban_columns

        verify_kanban_columns(self.page, bucket_name, expected_columns)

    def verify_record_in_kanban_column(
        self,
        bucket_name: str,
        record_name: str,
        column_title: str,
    ) -> None:
        from utils.kanban_verification import verify_record_in_kanban_column

        verify_record_in_kanban_column(
            self.page, bucket_name, record_name, column_title
        )

    def verify_mortgage_snapshot_complete_blocked(
        self,
        *,
        expected_status: str,
    ) -> None:
        """Complete Stage from meeting tab without saved snapshot must not advance lead."""
        from pages.mortgage_snapshot_page import MortgageSnapshotPage
        from utils.toast import Toast

        snapshot = MortgageSnapshotPage(self.page)
        url_before = self.page.url
        snapshot.open_meeting_tab()
        snapshot.click(snapshot.stage_complete_btn)
        dialog = self.page.get_by_role("alertdialog", name="Move to Next Stage?")
        if dialog.count() > 0 and dialog.is_visible():
            snapshot.click(dialog.get_by_role("button", name="Move to Next Stage"))
        toast = Toast(self.page)
        toast.assert_not_message("Lead moved to Appraisal Order successfully")
        toast.assert_not_message("Lead moved to Appraisal Ordered successfully")
        expect(self.page).to_have_url(re.compile(r"tab=mortgage-snapshot"))
        self.verify_status_badge(label=expected_status)

    def verify_tabs_visible(self, tab_names: list[str]) -> None:
        for name in tab_names:
            expect(self.page.get_by_role("tab", name=name, exact=True)).to_be_visible(
                timeout=Config.TIMEOUT,
            )

    def verify_tabs_hidden(self, tab_names: list[str]) -> None:
        for name in tab_names:
            expect(self.page.get_by_role("tab", name=name, exact=True)).to_have_count(0)

    def verify_assignment(self, expected_agent_label: str) -> None:
        """Requires the Lead Bucket general-info edit form to be open."""
        from utils.lead_assignment import LeadAssignmentHelper, _agent_label_matches

        helper = LeadAssignmentHelper(self.page)
        actual = helper.get_assigned_agent_label()
        assert _agent_label_matches(actual, expected_agent_label), (
            f"Expected agent {expected_agent_label!r}, got {actual!r}"
        )

    def verify_fe_agent_assignment(self, deal_name: str) -> None:
        """CRM sales UnifiedView filters assignedTo to the authenticated agent."""
        verify_bucket_record_visible(
            self.page,
            we.KANBAN_BUCKETS["my_deals"],
            deal_name,
        )

    def verify_fe_agent_has_full_access(self, visible_tabs: list[str]) -> None:
        """Assigned FE agents get hasFullAccess — tabs beyond Profile/Notes render."""
        restricted = {name for name, value in we.SALES_FRONTEND_STEPS if value in we.SALES_RESTRICTED_TAB_VALUES}
        unlocked = [tab for tab in visible_tabs if tab not in restricted]
        assert unlocked, "Expected at least one non-restricted tab for assigned FE agent"
        self.verify_tabs_visible([unlocked[0]])

    def verify_be_agent_assignment(self, deal_name: str) -> None:
        """CRM sales-backend UnifiedView filters assignedTo to the authenticated agent."""
        verify_bucket_record_visible(
            self.page,
            we.KANBAN_BUCKETS["sales_backend"],
            deal_name,
        )

    def verify_be_agent_has_full_access(self, visible_tabs: list[str]) -> None:
        """Assigned BE agents get hasFullAccess — tabs beyond Profile/Notes render."""
        restricted = {name for name, value in we.SALES_BACKEND_STEPS if value in we.SALES_RESTRICTED_TAB_VALUES}
        unlocked = [tab for tab in visible_tabs if tab not in restricted]
        assert unlocked, "Expected at least one non-restricted tab for assigned BE agent"
        self.verify_tabs_visible([unlocked[0]])

    def verify_agent_restricted_access(
        self,
        expectation: TransitionExpectation,
    ) -> None:
        """Non-assigned agent on a lead opened via header global search."""
        if expectation.visible_tabs:
            self.verify_tabs_visible(expectation.visible_tabs)
        if expectation.hidden_tabs:
            self.verify_tabs_hidden(expectation.hidden_tabs)

    def open_lead_via_header_search(self, lead_name: str) -> None:
        """RBAC non-assigned: open lead using #header-lead-search only."""
        from utils.entity_navigation import open_lead_via_header_search

        open_lead_via_header_search(self.page, lead_name)

    def verify_non_assigned_rbac_via_header_search(
        self,
        lead_name: str,
        expectation: TransitionExpectation,
    ) -> None:
        """Search via #header-lead-search and assert restricted tab visibility."""
        self.open_lead_via_header_search(lead_name)
        self.verify_agent_restricted_access(expectation)

    def verify_tabs_for_next_status(
        self,
        next_status_id: int | None,
        *,
        pipeline: we.Pipeline,
        is_admin: bool = True,
        has_full_access: bool = True,
    ) -> None:
        """Assert tab visibility matches CRM nextStatus for FE or BE pipeline."""
        if next_status_id is None:
            return
        visible, hidden = we.tab_expectations_for_next_status(
            next_status_id,
            pipeline=pipeline,
            is_admin=is_admin,
            has_full_access=has_full_access,
        )
        self.verify_tabs_visible(visible)
        self.verify_tabs_hidden(hidden)

    def _pipeline_for_expectation(
        self,
        expectation: TransitionExpectation,
    ) -> we.Pipeline:
        if expectation.bucket_name == we.KANBAN_BUCKETS["sales_backend"]:
            return "be"
        return "fe"

    def verify_transition(
        self,
        expectation: TransitionExpectation,
        *,
        record_name: str | None = None,
        skip_toast: bool = False,
        skip_bucket: bool = False,
    ) -> None:
        """Run modular checks for a workflow transition."""
        if expectation.success_toast and not skip_toast:
            Toast(self.page).assert_message(expectation.success_toast)

        if expectation.expected_url_pattern:
            self.verify_url(expectation.expected_url_pattern)

        if expectation.expected_status_label:
            self.verify_status_badge(label=expectation.expected_status_label)
        elif expectation.expected_status_contains:
            self.verify_status_badge(contains=expectation.expected_status_contains)

        visible_tabs = expectation.visible_tabs
        hidden_tabs = expectation.hidden_tabs

       
        if expectation.next_status_id is not None and (
            visible_tabs is None or hidden_tabs is None
        ):
            pipeline = self._pipeline_for_expectation(expectation)
            resolved_visible, resolved_hidden = we.tab_expectations_for_next_status(
                expectation.next_status_id,
                pipeline=pipeline,
                is_admin=expectation.is_admin,
                has_full_access=expectation.has_full_access,
    
            )

            if visible_tabs is None:
                visible_tabs = resolved_visible
            if hidden_tabs is None:
                hidden_tabs = resolved_hidden

        if visible_tabs:
            self.verify_tabs_visible(visible_tabs)
        if hidden_tabs:
            self.verify_tabs_hidden(hidden_tabs)

        if expectation.expected_agent_label:
            self.verify_assignment(expectation.expected_agent_label)

        bucket_record = record_name or expectation.record_name
        if expectation.bucket_name and bucket_record and not skip_bucket:
            if expectation.expected_kanban_column:
                self.verify_record_in_kanban_column(
                    expectation.bucket_name,
                    bucket_record,
                    expectation.expected_kanban_column,
                )
            else:
                verify_bucket_record_visible(
                    self.page,
                    expectation.bucket_name,
                    bucket_record,
                )
