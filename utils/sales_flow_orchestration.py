"""Reporting-aware orchestration for single-run full-flow E2E tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any

from playwright.sync_api import Page

from utils.flow_step_reporting import record_login_step, run_flow_step
from utils.flow_test_data import (
    STAGE_CAPTURE_CLASSES,
    STAGE_STATIC_BUILDERS,
    client_care_stage_data,
    login_stage_data,
)
from utils.entity_navigation import MY_DEALS_BUCKET, SALES_BACKEND_BUCKET
from utils.sales_flow_helpers import (
    create_lead_smoke,
    run_appraisal_order_smoke,
    run_approved_smoke,
    run_backend_appraisal_order_smoke,
    run_backend_approved_smoke,
    run_backend_mortgage_snapshot_smoke,
    run_backend_pre_stage_smoke,
    run_backend_signed_compliance_smoke,
    run_backend_signed_smoke,
    run_backend_submitted_smoke,
    run_client_care_smoke,
    run_co_borrower_smoke,
    run_compliance_smoke,
    run_fe_pre_stage_smoke,
    run_fe_sales_stages_smoke,
    run_lead_edit_smoke,
    run_marketing_smoke,
    run_mortgage_snapshot_smoke,
    run_notes_smoke,
    run_nova_bypass_smoke,
    run_nova_worksheet_unlock_smoke,
    run_signed_compliance_smoke,
    run_signed_marketing_smoke,
    run_submitted_smoke,
    setup_admin_be_lead,
    setup_admin_fe_lead,
)
from utils.lead_assignment import LeadAssignmentHelper
from utils.sales_flow_regression_helpers import (
    run_appraisal_order_empty,
    run_appraisal_order_invalid,
    run_approved_empty,
    run_approved_invalid,
    run_client_care_full,
    run_co_borrower_empty,
    run_co_borrower_invalid,
    run_create_lead_empty,
    run_create_lead_invalid,
    run_lead_edit_empty,
    run_lead_edit_invalid,
    run_mortgage_snapshot_empty,
    run_mortgage_snapshot_invalid,
    run_note_empty,
    run_note_invalid,
    run_pre_stage_all_cases,
    run_signed_empty,
    run_signed_invalid,
    run_signed_marketing_regression,
    run_submitted_empty,
    run_submitted_invalid,
)


@dataclass
class _FlowState:
    flow: str
    lead_name: str | None = None
    deal_name: str | None = None
    signed_baseline: Any | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def base_metadata(self, stage: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "flow": self.flow,
            "stage": stage,
        }
        if self.deal_name:
            metadata["deal_name"] = self.deal_name
            metadata["lead_name"] = self.deal_name
        elif self.lead_name:
            metadata["lead_name"] = self.lead_name
        metadata.update(self.extra)
        return metadata


def _attach_static_stage_data(step_key: str, metadata: dict[str, Any], _result, _captured) -> None:
    builder = STAGE_STATIC_BUILDERS.get(step_key)
    if builder is not None:
        metadata.update(builder())


def _run_step(
    item,
    page: Page,
    state: _FlowState,
    step_key: str,
    label: str,
    func,
    *,
    enrich_metadata=None,
) -> Any:
    capture_classes = STAGE_CAPTURE_CLASSES.get(step_key, ())

    def _default_enrich(metadata, result, captured):
        _attach_static_stage_data(step_key, metadata, result, captured)
        if enrich_metadata is not None:
            enrich_metadata(metadata, result, captured)

    return run_flow_step(
        item,
        page,
        step_key=step_key,
        label=label,
        func=func,
        metadata=state.base_metadata(label),
        capture_classes=capture_classes,
        enrich_metadata=_default_enrich,
    )


def run_through_approved_reported(page: Page, item, *, flow: str) -> str:
    """Shared Admin FE prefix: Create → Assign FE → Edit → Co-Borrower → Notes → stages through Approved."""
    state = _FlowState(flow=flow)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    state.lead_name = _run_step(
        item,
        page,
        state,
        "create_lead",
        "Create Lead",
        lambda: create_lead_smoke(page),
    )
    state.deal_name = state.lead_name

    state.deal_name = _run_step(
        item,
        page,
        state,
        "nova_bypass",
        "Nova Worksheet Unlock",
        lambda: run_nova_worksheet_unlock_smoke(page, state.deal_name),
    )

    _run_step(
        item,
        page,
        state,
        "edit_lead",
        "Edit Lead",
        lambda: run_lead_edit_smoke(page, state.lead_name, bucket=MY_DEALS_BUCKET),
    )
    _run_step(
        item,
        page,
        state,
        "add_co_borrower",
        "Add Co-Borrower",
        lambda: run_co_borrower_smoke(page, state.lead_name, bucket=MY_DEALS_BUCKET),
    )
    _run_step(
        item,
        page,
        state,
        "add_note",
        "Add Note",
        lambda: run_notes_smoke(
            page, state.lead_name, move_to_sales=False, bucket=MY_DEALS_BUCKET
        ),
    )
    _run_step(
        item,
        page,
        state,
        "mortgage_snapshot",
        "Mortgage Snapshot",
        lambda: run_mortgage_snapshot_smoke(
            page,
            state.deal_name,
            bucket=MY_DEALS_BUCKET,
            request_or_item=item,
            ms_app_assigned_pipeline="admin",
            ms_app_open_via_crm=True,
        ),
    )
    _run_step(
        item,
        page,
        state,
        "appraisal_order",
        "Appraisal Order",
        lambda: run_appraisal_order_smoke(page, state.deal_name, bucket=MY_DEALS_BUCKET),
    )
    _run_step(
        item,
        page,
        state,
        "submit_deal",
        "Submit Deal",
        lambda: run_submitted_smoke(page, state.deal_name, bucket=MY_DEALS_BUCKET),
    )
    _run_step(
        item,
        page,
        state,
        "approve_deal",
        "Approve Deal",
        lambda: run_approved_smoke(page, state.deal_name, bucket=MY_DEALS_BUCKET),
    )
    return state.deal_name


def run_compliance_to_client_care_flow(page: Page, item) -> str:
    """Single-run Compliance path with virtual per-module pytest-html rows."""
    flow = "compliance_to_client_care"
    state = _FlowState(flow=flow)
    deal_name = run_through_approved_reported(page, item, flow=flow)
    state.deal_name = deal_name
    state.lead_name = deal_name

    _run_step(
        item,
        page,
        state,
        "signed",
        "Signed",
        lambda: run_signed_compliance_smoke(page, deal_name),
    )
    state.signed_baseline = _run_step(
        item,
        page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(page, deal_name),
    )
    _run_step(
        item,
        page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_smoke(page, deal_name, state.signed_baseline),
        enrich_metadata=lambda md, _result, _captured: md.update(
            client_care_stage_data(state.signed_baseline)
        ),
    )
    return deal_name


def _scenarios_metadata(scenarios: list[str]):
    def enrich(metadata: dict[str, Any], _result, _captured) -> None:
        metadata["scenarios"] = scenarios

    return enrich


def _run_agent_pre_stage_all_cases_reported(
    item,
    agent_page: Page,
    state: _FlowState,
    deal_name: str,
    *,
    bucket: str,
) -> None:
    """Edit Lead, Co-Borrower, Notes — empty, invalid, smoke on agent page."""

    def _edit_lead_module() -> None:
        run_lead_edit_empty(agent_page, item, deal_name, bucket=bucket)
        run_lead_edit_invalid(agent_page, item, deal_name, bucket=bucket)
        run_lead_edit_smoke(agent_page, deal_name, bucket=bucket)

    _run_step(
        item,
        agent_page,
        state,
        "edit_lead",
        "Edit Lead",
        _edit_lead_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _co_borrower_module() -> None:
        run_co_borrower_empty(agent_page, item, deal_name, bucket=bucket)
        run_co_borrower_invalid(agent_page, item, deal_name, bucket=bucket)
        run_co_borrower_smoke(agent_page, deal_name, bucket=bucket)

    _run_step(
        item,
        agent_page,
        state,
        "add_co_borrower",
        "Add Co-Borrower",
        _co_borrower_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _note_module() -> None:
        run_note_empty(agent_page, item, deal_name, bucket=bucket)
        run_note_invalid(agent_page, item, deal_name, bucket=bucket)
        run_notes_smoke(agent_page, deal_name, move_to_sales=False, bucket=bucket)

    _run_step(
        item,
        agent_page,
        state,
        "add_note",
        "Add Note",
        _note_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )


def _run_agent_stages_all_cases_reported(
    item,
    agent_page: Page,
    state: _FlowState,
    deal_name: str,
    *,
    bucket: str,
    signed_smoke,
) -> None:
    """Mortgage Snapshot through Signed — empty, invalid, smoke on agent page."""
    if bucket == SALES_BACKEND_BUCKET:
        stage_runners = [
            (
                "mortgage_snapshot",
                "Mortgage Snapshot",
                run_mortgage_snapshot_empty,
                run_mortgage_snapshot_invalid,
                run_backend_mortgage_snapshot_smoke,
            ),
            (
                "appraisal_order",
                "Appraisal Order",
                run_appraisal_order_empty,
                run_appraisal_order_invalid,
                run_backend_appraisal_order_smoke,
            ),
            (
                "submit_deal",
                "Submit Deal",
                run_submitted_empty,
                run_submitted_invalid,
                run_backend_submitted_smoke,
            ),
            (
                "approve_deal",
                "Approve Deal",
                run_approved_empty,
                run_approved_invalid,
                run_backend_approved_smoke,
            ),
        ]
    else:
        stage_runners = [
            (
                "mortgage_snapshot",
                "Mortgage Snapshot",
                run_mortgage_snapshot_empty,
                run_mortgage_snapshot_invalid,
                run_mortgage_snapshot_smoke,
            ),
            (
                "appraisal_order",
                "Appraisal Order",
                run_appraisal_order_empty,
                run_appraisal_order_invalid,
                run_appraisal_order_smoke,
            ),
            (
                "submit_deal",
                "Submit Deal",
                run_submitted_empty,
                run_submitted_invalid,
                run_submitted_smoke,
            ),
            (
                "approve_deal",
                "Approve Deal",
                run_approved_empty,
                run_approved_invalid,
                run_approved_smoke,
            ),
        ]

    for key, label, empty_fn, invalid_fn, smoke_fn in stage_runners:
        def _mod(
            e=empty_fn,
            i=invalid_fn,
            s=smoke_fn,
            d=deal_name,
            b=bucket,
            p=agent_page,
        ) -> None:
            e(p, item, d, bucket=b)
            i(p, item, d, bucket=b)
            if s is run_mortgage_snapshot_smoke:
                s(
                    p,
                    d,
                    bucket=b,
                    request_or_item=item,
                    ms_app_assigned_pipeline=(
                        "be" if b == SALES_BACKEND_BUCKET else "fe"
                    ),
                )
            elif s is run_backend_mortgage_snapshot_smoke:
                s(p, d, request_or_item=item)
            else:
                s(p, d)

        _run_step(
            item,
            agent_page,
            state,
            key,
            label,
            _mod,
            enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
        )

    def _signed_mod() -> None:
        run_signed_empty(agent_page, item, deal_name, bucket=bucket)
        run_signed_invalid(agent_page, item, deal_name, bucket=bucket)
        signed_smoke(agent_page, deal_name)

    _run_step(
        item,
        agent_page,
        state,
        "signed",
        "Signed",
        _signed_mod,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )


def run_compliance_path_all_cases_reported(page: Page, request) -> str:
    """
    Full regression (empty, invalid, smoke per stage) with virtual per-module
    pytest-html rows. Reuses existing stage runners without changing their logic.
    """
    flow = "compliance_all_cases"
    state = _FlowState(flow=flow)
    node = request.node

    record_login_step(request, flow=flow, metadata=login_stage_data())

    def _create_lead_module() -> str:
        run_create_lead_empty(page, node)
        run_create_lead_invalid(page, node)
        return create_lead_smoke(page)

    state.lead_name = _run_step(
        request,
        page,
        state,
        "create_lead",
        "Create Lead",
        _create_lead_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )
    state.deal_name = state.lead_name

    def _note_module() -> None:
        run_note_empty(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_note_invalid(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_notes_smoke(
            page, state.lead_name, move_to_sales=False, bucket=MY_DEALS_BUCKET
        )

    state.deal_name = _run_step(
        request,
        page,
        state,
        "nova_bypass",
        "Nova Worksheet Unlock",
        lambda: run_nova_worksheet_unlock_smoke(page, state.lead_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )

    def _edit_lead_module() -> None:
        run_lead_edit_empty(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_lead_edit_invalid(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_lead_edit_smoke(page, state.lead_name, bucket=MY_DEALS_BUCKET)

    _run_step(
        request,
        page,
        state,
        "edit_lead",
        "Edit Lead",
        _edit_lead_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _co_borrower_module() -> None:
        run_co_borrower_empty(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_co_borrower_invalid(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_co_borrower_smoke(page, state.lead_name, bucket=MY_DEALS_BUCKET)

    _run_step(
        request,
        page,
        state,
        "add_co_borrower",
        "Add Co-Borrower",
        _co_borrower_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    _run_step(
        request,
        page,
        state,
        "add_note",
        "Add Note",
        _note_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _mortgage_snapshot_module() -> None:
        run_mortgage_snapshot_empty(page, node, state.deal_name)
        run_mortgage_snapshot_invalid(page, node, state.deal_name)
        run_mortgage_snapshot_smoke(
            page,
            state.deal_name,
            request_or_item=node,
            regression_ms_app=True,
            ms_app_assigned_pipeline="admin",
            ms_app_open_via_crm=True,
        )

    _run_step(
        request,
        page,
        state,
        "mortgage_snapshot",
        "Mortgage Snapshot",
        _mortgage_snapshot_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _appraisal_order_module() -> None:
        run_appraisal_order_empty(page, node, state.deal_name)
        run_appraisal_order_invalid(page, node, state.deal_name)
        run_appraisal_order_smoke(page, state.deal_name)

    _run_step(
        request,
        page,
        state,
        "appraisal_order",
        "Appraisal Order",
        _appraisal_order_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _submit_deal_module() -> None:
        run_submitted_empty(page, node, state.deal_name)
        run_submitted_invalid(page, node, state.deal_name)
        run_submitted_smoke(page, state.deal_name)

    _run_step(
        request,
        page,
        state,
        "submit_deal",
        "Submit Deal",
        _submit_deal_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _approve_deal_module() -> None:
        run_approved_empty(page, node, state.deal_name)
        run_approved_invalid(page, node, state.deal_name)
        run_approved_smoke(page, state.deal_name)

    _run_step(
        request,
        page,
        state,
        "approve_deal",
        "Approve Deal",
        _approve_deal_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    def _signed_module() -> None:
        run_signed_empty(page, node, state.deal_name)
        run_signed_invalid(page, node, state.deal_name)
        run_signed_compliance_smoke(page, state.deal_name)

    _run_step(
        request,
        page,
        state,
        "signed",
        "Signed",
        _signed_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )

    state.signed_baseline = _run_step(
        request,
        page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(page, state.deal_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )

    def _client_care_enrich(metadata, _result, _captured) -> None:
        metadata["scenarios"] = ["smoke", "readonly_verification"]
        metadata.update(client_care_stage_data(state.signed_baseline))

    _run_step(
        request,
        page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_full(
            page, node, state.deal_name, state.signed_baseline
        ),
        enrich_metadata=_client_care_enrich,
    )
    return state.deal_name


def run_marketing_flow(page: Page, item) -> str:
    """Single-run Marketing path with virtual per-module pytest-html rows."""
    flow = "signed_marketing"
    state = _FlowState(flow=flow)
    deal_name = run_through_approved_reported(page, item, flow=flow)
    state.deal_name = deal_name
    state.lead_name = deal_name

    _run_step(
        item,
        page,
        state,
        "signed",
        "Signed",
        lambda: run_signed_marketing_smoke(page, deal_name),
    )
    _run_step(
        item,
        page,
        state,
        "marketing",
        "Marketing",
        lambda: run_marketing_smoke(page, deal_name),
    )
    return deal_name


def run_backend_full_flow_reported(
    page: Page,
    item,
    *,
    flow: str,
    deal_name: str,
    include_pre_stage: bool = True,
    signed_step=None,
    signed_role: str = "admin",
    assignee_sync_page: Page | None = None,
) -> str:
    """Single-run Sales Backend pipeline with virtual per-module pytest-html rows."""
    state = _FlowState(flow=flow, deal_name=deal_name, lead_name=deal_name)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    if include_pre_stage:
        _run_step(
            item,
            page,
            state,
            "edit_lead",
            "Edit Lead",
            lambda: run_lead_edit_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET),
        )
        _run_step(
            item,
            page,
            state,
            "add_co_borrower",
            "Add Co-Borrower",
            lambda: run_co_borrower_smoke(page, deal_name, bucket=SALES_BACKEND_BUCKET),
        )
        _run_step(
            item,
            page,
            state,
            "add_note",
            "Add Note",
            lambda: run_notes_smoke(
                page, deal_name, move_to_sales=False, bucket=SALES_BACKEND_BUCKET
            ),
        )

    _run_step(
        item,
        page,
        state,
        "mortgage_snapshot",
        "Mortgage Snapshot",
        lambda: run_backend_mortgage_snapshot_smoke(
            page,
            deal_name,
            request_or_item=item,
            assignee_sync_page=assignee_sync_page or page,
        ),
    )
    _run_step(
        item,
        page,
        state,
        "appraisal_order",
        "Appraisal Order",
        lambda: run_backend_appraisal_order_smoke(page, deal_name),
    )
    _run_step(
        item,
        page,
        state,
        "submit_deal",
        "Submit Deal",
        lambda: run_backend_submitted_smoke(page, deal_name),
    )
    _run_step(
        item,
        page,
        state,
        "approve_deal",
        "Approve Deal",
        lambda: run_backend_approved_smoke(
            page,
            deal_name,
            request_or_item=item,
            browser=page.context.browser,
            assignee_sync_page=assignee_sync_page,
        ),
    )
    signed_runner = signed_step or (
        lambda: run_backend_signed_smoke(page, deal_name, role=signed_role)
    )
    _run_step(
        item,
        page,
        state,
        "signed",
        "Signed",
        signed_runner,
    )
    return deal_name


def run_through_approved_backend_reported(
    admin_page: Page,
    item,
    *,
    flow: str,
) -> str:
    """Admin BE prefix: Create → Assign BE → pre-stage → stages through Approved."""
    state = _FlowState(flow=flow)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    state.lead_name = _run_step(
        item,
        admin_page,
        state,
        "create_lead",
        "Create Lead",
        lambda: create_lead_smoke(admin_page),
    )
    state.deal_name = state.lead_name

    state.deal_name = _run_step(
        item,
        admin_page,
        state,
        "assign_backend",
        "Assign Backend Agent",
        lambda: LeadAssignmentHelper(admin_page).assign_be_backend(state.lead_name),
    )

    _run_step(
        item,
        admin_page,
        state,
        "edit_lead",
        "Edit Lead",
        lambda: run_lead_edit_smoke(
            admin_page, state.deal_name, bucket=SALES_BACKEND_BUCKET
        ),
    )
    _run_step(
        item,
        admin_page,
        state,
        "add_co_borrower",
        "Add Co-Borrower",
        lambda: run_co_borrower_smoke(
            admin_page, state.deal_name, bucket=SALES_BACKEND_BUCKET
        ),
    )
    _run_step(
        item,
        admin_page,
        state,
        "add_note",
        "Add Note",
        lambda: run_notes_smoke(
            admin_page,
            state.deal_name,
            move_to_sales=False,
            bucket=SALES_BACKEND_BUCKET,
        ),
    )
    _run_step(
        item,
        admin_page,
        state,
        "mortgage_snapshot",
        "Mortgage Snapshot",
        lambda: run_backend_mortgage_snapshot_smoke(
            admin_page, state.deal_name, request_or_item=item
        ),
    )
    _run_step(
        item,
        admin_page,
        state,
        "appraisal_order",
        "Appraisal Order",
        lambda: run_backend_appraisal_order_smoke(admin_page, state.deal_name),
    )
    _run_step(
        item,
        admin_page,
        state,
        "submit_deal",
        "Submit Deal",
        lambda: run_backend_submitted_smoke(admin_page, state.deal_name),
    )
    _run_step(
        item,
        admin_page,
        state,
        "approve_deal",
        "Approve Deal",
        lambda: run_backend_approved_smoke(admin_page, state.deal_name),
    )
    return state.deal_name


def run_backend_compliance_to_client_care_flow(admin_page: Page, item) -> str:
    """Admin Backend Compliance path through Client Care."""
    flow = "backend_compliance_to_client_care"
    state = _FlowState(flow=flow)
    deal_name = run_through_approved_backend_reported(admin_page, item, flow=flow)
    state.deal_name = deal_name

    _run_step(
        item,
        admin_page,
        state,
        "signed",
        "Signed",
        lambda: run_backend_signed_compliance_smoke(admin_page, deal_name),
    )
    state.signed_baseline = _run_step(
        item,
        admin_page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(admin_page, deal_name),
    )
    _run_step(
        item,
        admin_page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_smoke(admin_page, deal_name, state.signed_baseline),
        enrich_metadata=lambda md, _r, _c: md.update(
            client_care_stage_data(state.signed_baseline)
        ),
    )
    return deal_name


def run_backend_marketing_flow(admin_page: Page, item) -> str:
    """Admin Backend Marketing path."""
    flow = "backend_signed_marketing"
    state = _FlowState(flow=flow)
    deal_name = run_through_approved_backend_reported(admin_page, item, flow=flow)
    state.deal_name = deal_name

    _run_step(
        item,
        admin_page,
        state,
        "signed",
        "Signed",
        lambda: run_signed_marketing_smoke(admin_page, deal_name, bucket=SALES_BACKEND_BUCKET),
    )
    _run_step(
        item,
        admin_page,
        state,
        "marketing",
        "Marketing",
        lambda: run_marketing_smoke(admin_page, deal_name),
    )
    return deal_name


def run_fe_compliance_to_client_care_flow(
    admin_page: Page,
    fe_agent_page: Page,
    item,
) -> str:
    """Admin setup → FE agent pipeline → Admin Compliance → Client Care."""
    flow = "fe_compliance_to_client_care"
    state = _FlowState(flow=flow)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_fe_lead(admin_page),
    )
    state.deal_name = deal_name

    _run_step(
        item,
        fe_agent_page,
        state,
        "edit_lead",
        "Edit Lead",
        lambda: run_fe_pre_stage_smoke(fe_agent_page, deal_name),
    )
    _run_step(
        item,
        fe_agent_page,
        state,
        "sales_stages",
        "Sales Stages",
        lambda: run_fe_sales_stages_smoke(
            fe_agent_page,
            deal_name,
            request_or_item=item,
            assignee_sync_page=admin_page,
        ),
    )
    _run_step(
        item,
        fe_agent_page,
        state,
        "signed",
        "Signed",
        # lambda: run_signed_compliance_smoke(fe_agent_page, deal_name),
        lambda: run_signed_compliance_smoke(fe_agent_page, deal_name, role="agent"),
    )

    state.signed_baseline = _run_step(
        item,
        admin_page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(admin_page, deal_name),
    )
    _run_step(
        item,
        admin_page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_smoke(admin_page, deal_name, state.signed_baseline),
        enrich_metadata=lambda md, _r, _c: md.update(
            client_care_stage_data(state.signed_baseline)
        ),
    )
    return deal_name


def run_fe_marketing_flow(
    admin_page: Page,
    fe_agent_page: Page,
    item,
) -> str:
    """Admin setup → FE agent pipeline → Admin Marketing."""
    flow = "fe_signed_marketing"
    state = _FlowState(flow=flow)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_fe_lead(admin_page),
    )
    state.deal_name = deal_name

    _run_step(
        item,
        fe_agent_page,
        state,
        "edit_lead",
        "Edit Lead",
        lambda: run_fe_pre_stage_smoke(fe_agent_page, deal_name),
    )
    _run_step(
        item,
        fe_agent_page,
        state,
        "sales_stages",
        "Sales Stages",
        lambda: run_fe_sales_stages_smoke(
            fe_agent_page,
            deal_name,
            request_or_item=item,
            assignee_sync_page=admin_page,
        ),
    )
    _run_step(
        item,
        fe_agent_page,
        state,
        "signed",
        "Signed",
        lambda: run_signed_marketing_smoke(fe_agent_page, deal_name),
    )
    _run_step(
        item,
        admin_page,
        state,
        "marketing",
        "Marketing",
        lambda: run_marketing_smoke(admin_page, deal_name),
    )
    return deal_name


def run_be_agent_compliance_to_client_care_flow(
    admin_page: Page,
    be_agent_page: Page,
    item,
) -> str:
    """Admin setup → BE agent pipeline → Admin Compliance → Client Care."""
    flow = "be_agent_compliance_to_client_care"
    state = _FlowState(flow=flow)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_be_lead(admin_page),
    )
    state.deal_name = deal_name

    run_backend_full_flow_reported(
        be_agent_page,
        item,
        flow=flow,
        deal_name=deal_name,
        include_pre_stage=True,
        assignee_sync_page=admin_page,
       
        signed_step=lambda: run_backend_signed_compliance_smoke(
            be_agent_page, deal_name, role="agent"
        ),
    )

    state.signed_baseline = _run_step(
        item,
        admin_page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(admin_page, deal_name),
    )
    _run_step(
        item,
        admin_page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_smoke(admin_page, deal_name, state.signed_baseline),
        enrich_metadata=lambda md, _r, _c: md.update(
            client_care_stage_data(state.signed_baseline)
        ),
    )
    return deal_name


def run_be_agent_marketing_flow(
    admin_page: Page,
    be_agent_page: Page,
    item,
) -> str:
    """Admin setup → BE agent pipeline → Admin Marketing."""
    flow = "be_agent_signed_marketing"
    state = _FlowState(flow=flow)
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_be_lead(admin_page),
    )
    state.deal_name = deal_name

    run_backend_full_flow_reported(
        be_agent_page,
        item,
        flow=flow,
        deal_name=deal_name,
        include_pre_stage=True,
        assignee_sync_page=admin_page,
        signed_step=lambda: run_signed_marketing_smoke(
            be_agent_page, deal_name, bucket=SALES_BACKEND_BUCKET
        ),
    )
    _run_step(
        item,
        admin_page,
        state,
        "marketing",
        "Marketing",
        lambda: run_marketing_smoke(admin_page, deal_name),
    )
    return deal_name


def run_fe_agent_compliance_all_cases_reported(
    admin_page: Page,
    fe_agent_page: Page,
    item,
) -> str:
    """Admin setup → FE agent full regression → Admin Compliance → Client Care."""
    flow = "fe_agent_compliance_all_cases"
    state = _FlowState(flow=flow)
    bucket = MY_DEALS_BUCKET
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_fe_lead(admin_page),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )
    state.deal_name = deal_name

    _run_agent_pre_stage_all_cases_reported(
        item, fe_agent_page, state, deal_name, bucket=bucket
    )
    _run_agent_stages_all_cases_reported(
        item,
        fe_agent_page,
        state,
        deal_name,
        bucket=bucket,
        # signed_smoke=run_signed_compliance_smoke,
        signed_smoke=partial(run_signed_compliance_smoke, role="agent"),
    )

    state.signed_baseline = _run_step(
        item,
        admin_page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(admin_page, deal_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )

    def _client_care_enrich(metadata, _result, _captured) -> None:
        metadata["scenarios"] = ["smoke", "readonly_verification"]
        metadata.update(client_care_stage_data(state.signed_baseline))

    _run_step(
        item,
        admin_page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_full(
            admin_page, item, deal_name, state.signed_baseline
        ),
        enrich_metadata=_client_care_enrich,
    )
    return deal_name


def run_fe_agent_pre_stage_all_cases_reported(
    admin_page: Page,
    fe_agent_page: Page,
    item,
) -> str:
    """Admin setup → FE agent runs Edit Lead / Co-Borrower / Notes regression."""
    flow = "fe_agent_pre_stage_all_cases"
    state = _FlowState(flow=flow)
    bucket = MY_DEALS_BUCKET
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_fe_lead(admin_page),
    )
    state.deal_name = deal_name

    _run_agent_pre_stage_all_cases_reported(
        item, fe_agent_page, state, deal_name, bucket=bucket
    )
    return deal_name


def run_be_agent_compliance_all_cases_reported(
    admin_page: Page,
    be_agent_page: Page,
    item,
) -> str:
    """Admin setup → BE agent full regression → Admin Compliance → Client Care."""
    flow = "be_agent_compliance_all_cases"
    state = _FlowState(flow=flow)
    bucket = SALES_BACKEND_BUCKET
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_be_lead(admin_page),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )
    state.deal_name = deal_name

    _run_agent_pre_stage_all_cases_reported(
        item, be_agent_page, state, deal_name, bucket=bucket
    )
    _run_agent_stages_all_cases_reported(
        item,
        be_agent_page,
        state,
        deal_name,
        bucket=bucket,
        # signed_smoke=run_backend_signed_compliance_smoke,
        signed_smoke=partial(run_backend_signed_compliance_smoke, role="agent"),
    )

    state.signed_baseline = _run_step(
        item,
        admin_page,
        state,
        "compliance",
        "Compliance",
        lambda: run_compliance_smoke(admin_page, deal_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )
    _run_step(
        item,
        admin_page,
        state,
        "client_care",
        "Client Care",
        lambda: run_client_care_full(
            admin_page, item, deal_name, state.signed_baseline
        ),
        enrich_metadata=_scenarios_metadata(["smoke", "readonly_verification"]),
    )
    return deal_name


def run_be_agent_pre_stage_all_cases_reported(
    admin_page: Page,
    be_agent_page: Page,
    item,
) -> str:
    """Admin setup → BE agent runs Edit Lead / Co-Borrower / Notes regression."""
    flow = "be_agent_pre_stage_all_cases"
    state = _FlowState(flow=flow)
    bucket = SALES_BACKEND_BUCKET
    record_login_step(item, flow=flow, metadata=login_stage_data())

    deal_name = _run_step(
        item,
        admin_page,
        state,
        "admin_setup",
        "Admin Setup",
        lambda: setup_admin_be_lead(admin_page),
    )
    state.deal_name = deal_name

    _run_agent_pre_stage_all_cases_reported(
        item, be_agent_page, state, deal_name, bucket=bucket
    )
    return deal_name


def run_marketing_path_all_cases_reported(page: Page, request) -> str:
    """Full regression through Marketing (empty/invalid/smoke per stage)."""
    flow = "marketing_all_cases"
    state = _FlowState(flow=flow)
    node = request.node
    record_login_step(request, flow=flow, metadata=login_stage_data())

    def _create_lead_module() -> str:
        run_create_lead_empty(page, node)
        run_create_lead_invalid(page, node)
        return create_lead_smoke(page)

    state.lead_name = _run_step(
        request, page, state, "create_lead", "Create Lead", _create_lead_module,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )
    state.deal_name = _run_step(
        request, page, state, "nova_bypass", "Nova Worksheet Unlock",
        lambda: run_nova_worksheet_unlock_smoke(page, state.lead_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )

    def _edit_module() -> None:
        run_lead_edit_empty(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_lead_edit_invalid(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_lead_edit_smoke(page, state.lead_name, bucket=MY_DEALS_BUCKET)

    _run_step(request, page, state, "edit_lead", "Edit Lead", _edit_module,
              enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    def _co_module() -> None:
        run_co_borrower_empty(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_co_borrower_invalid(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_co_borrower_smoke(page, state.lead_name, bucket=MY_DEALS_BUCKET)

    _run_step(request, page, state, "add_co_borrower", "Add Co-Borrower", _co_module,
              enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    def _note_module() -> None:
        run_note_empty(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_note_invalid(page, node, state.lead_name, bucket=MY_DEALS_BUCKET)
        run_notes_smoke(page, state.lead_name, move_to_sales=False, bucket=MY_DEALS_BUCKET)

    _run_step(request, page, state, "add_note", "Add Note", _note_module,
              enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    for key, label, mod in [
        ("mortgage_snapshot", "Mortgage Snapshot", lambda: (
            run_mortgage_snapshot_empty(page, node, state.deal_name),
            run_mortgage_snapshot_invalid(page, node, state.deal_name),
            run_mortgage_snapshot_smoke(
            page,
            state.deal_name,
            request_or_item=node,
            regression_ms_app=True,
            ms_app_assigned_pipeline="admin",
            ms_app_open_via_crm=True,
        ),
        )),
        ("appraisal_order", "Appraisal Order", lambda: (
            run_appraisal_order_empty(page, node, state.deal_name),
            run_appraisal_order_invalid(page, node, state.deal_name),
            run_appraisal_order_smoke(page, state.deal_name),
        )),
        ("submit_deal", "Submit Deal", lambda: (
            run_submitted_empty(page, node, state.deal_name),
            run_submitted_invalid(page, node, state.deal_name),
            run_submitted_smoke(page, state.deal_name),
        )),
        ("approve_deal", "Approve Deal", lambda: (
            run_approved_empty(page, node, state.deal_name),
            run_approved_invalid(page, node, state.deal_name),
            run_approved_smoke(page, state.deal_name),
        )),
    ]:
        def _stage_runner(run=mod):
            run()

        _run_step(request, page, state, key, label, _stage_runner,
                  enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    def _signed_module() -> None:
        run_signed_empty(page, node, state.deal_name)
        run_signed_invalid(page, node, state.deal_name)
        run_signed_marketing_regression(page, node, state.deal_name)

    _run_step(request, page, state, "signed", "Signed", _signed_module,
              enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    _run_step(request, page, state, "marketing", "Marketing",
              lambda: run_marketing_smoke(page, state.deal_name),
              enrich_metadata=_scenarios_metadata(["smoke"]))
    return state.deal_name


def run_backend_compliance_all_cases_reported(admin_page: Page, request) -> str:
    """Full backend regression through Client Care."""
    flow = "backend_compliance_all_cases"
    state = _FlowState(flow=flow)
    node = request.node
    bucket = SALES_BACKEND_BUCKET
    record_login_step(request, flow=flow, metadata=login_stage_data())

    def _create() -> str:
        run_create_lead_empty(admin_page, node)
        run_create_lead_invalid(admin_page, node)
        return create_lead_smoke(admin_page)

    state.lead_name = _run_step(
        request, admin_page, state, "create_lead", "Create Lead", _create,
        enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]),
    )
    state.deal_name = _run_step(
        request, admin_page, state, "assign_backend", "Assign Backend Agent",
        lambda: LeadAssignmentHelper(admin_page).assign_be_backend(state.lead_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )

    def _pre_stage() -> None:
        run_pre_stage_all_cases(admin_page, node, state.deal_name, bucket=bucket)

    _run_step(request, admin_page, state, "pre_stage", "Pre-Stage", _pre_stage,
              enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    stage_runners = [
        ("mortgage_snapshot", "Mortgage Snapshot", run_mortgage_snapshot_empty,
         run_mortgage_snapshot_invalid, run_backend_mortgage_snapshot_smoke),
        ("appraisal_order", "Appraisal Order", run_appraisal_order_empty,
         run_appraisal_order_invalid, run_backend_appraisal_order_smoke),
        ("submit_deal", "Submit Deal", run_submitted_empty,
         run_submitted_invalid, run_backend_submitted_smoke),
        ("approve_deal", "Approve Deal", run_approved_empty,
         run_approved_invalid, run_backend_approved_smoke),
    ]
    for key, label, empty_fn, invalid_fn, smoke_fn in stage_runners:
        def _mod(
            e=empty_fn,
            i=invalid_fn,
            s=smoke_fn,
            d=state.deal_name,
            stage_key=key,
        ):
            e(admin_page, node, d, bucket=bucket)
            i(admin_page, node, d, bucket=bucket)
            if stage_key == "mortgage_snapshot":
                s(
                    admin_page,
                    d,
                    request_or_item=node,
                    regression_ms_app=True,
                )
            else:
                s(admin_page, d)

        _run_step(request, admin_page, state, key, label, _mod,
                  enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    def _signed_mod() -> None:
        run_signed_empty(admin_page, node, state.deal_name, bucket=bucket)
        run_signed_invalid(admin_page, node, state.deal_name, bucket=bucket)
        run_backend_signed_compliance_smoke(admin_page, state.deal_name)

    _run_step(request, admin_page, state, "signed", "Signed", _signed_mod,
              enrich_metadata=_scenarios_metadata(["empty", "invalid", "smoke"]))

    state.signed_baseline = _run_step(
        request, admin_page, state, "compliance", "Compliance",
        lambda: run_compliance_smoke(admin_page, state.deal_name),
        enrich_metadata=_scenarios_metadata(["smoke"]),
    )
    _run_step(
        request, admin_page, state, "client_care", "Client Care",
        lambda: run_client_care_full(
            admin_page, node, state.deal_name, state.signed_baseline
        ),
        enrich_metadata=_scenarios_metadata(["smoke", "readonly_verification"]),
    )
    return state.deal_name
