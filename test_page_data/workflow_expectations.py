"""CRM-derived workflow constants for automation verification.

Source of truth:
- apps/honojs/src/router/leads/leads.service.ts (NEXT_STATUS_MAP)
- apps/nextjs/src/lib/utils/stage-utils.ts (NEXT_STATUS_TO_LAST_STEP)
- apps/nextjs/src/features/lead-detail/utils/sales-stage-status.ts
- apps/nextjs/src/types/lead.ts (SALES_FRONTEND_STEPS, SALES_BACKEND_STEPS, …)
- apps/nextjs/src/types/sidebar.ts (kanban bucket titles and paths)
- apps/nextjs/src/features/sales/components/SaleLeadInfo.tsx (tab filtering)
- apps/nextjs/src/features/leads/components/MoveToSalesButton.tsx (move-to-sales transition)
"""

from __future__ import annotations

from typing import Literal

Pipeline = Literal["fe", "be"]
StageTabMoment = Literal["entry", "post"]

# ---------------------------------------------------------------------------
# Status IDs — apps/nextjs/src/features/lead-detail/utils/sales-stage-status.ts
# ---------------------------------------------------------------------------

APPLICATION_RECEIVED_STATUS_ID = 8
NOVA_WORKSHEET_STATUS_ID = 59
MORTGAGE_SNAPSHOT_STATUS_ID = 13
NURTURE_STATUS_ID = 57
APPRAISAL_ORDER_STATUS_ID = 14
SUBMITTED_STATUS_ID = 10
APPROVED_STATUS_ID = 48
SIGNED_STATUS_ID = 11
NOT_SIGNED_STATUS_ID = 16

RENEWAL_APPLICATION_RECEIVED_STATUS_ID = 29
RENEWAL_MORTGAGE_SNAPSHOT_STATUS_ID = 30
RENEWAL_APPRAISAL_ORDER_STATUS_ID = 31
RENEWAL_SUBMITTED_STATUS_ID = 32
RENEWAL_APPROVED_STATUS_ID = 49
RENEWAL_SIGNED_STATUS_ID = 34
RENEWAL_NOT_SIGNED_STATUS_ID = 35

# Display names — sales-stage-status.ts / lead.ts
NOVA_WORKSHEET_TAB_NAME = "Nova Worksheet"
APPLICATION_RECEIVED_STATUS_NAME = "Application Received"

# ---------------------------------------------------------------------------
# nextStatus map — apps/honojs/src/router/leads/leads.service.ts
# ---------------------------------------------------------------------------

NEXT_STATUS_MAP: dict[int, int | None] = {
    8: 59,
    59: 13,
    13: 14,
    14: 10,
    10: 48,
    48: 11,
    11: None,
    16: None,
    29: 30,
    30: 31,
    31: 32,
    32: 49,
    49: 34,
    34: None,
    35: None,
}

# ---------------------------------------------------------------------------
# Tab unlock — apps/nextjs/src/lib/utils/stage-utils.ts
# ---------------------------------------------------------------------------

NEXT_STATUS_TO_LAST_STEP: dict[int, str] = {
    59: "nova-worksheet",
    13: "mortgage-snapshot",
    57: "nurture",
    14: "appraisal-order",
    10: "submitted",
    48: "approved",
    11: "signed",
    16: "signed",
    29: "profile",
    30: "mortgage-snapshot",
    31: "appraisal-order",
    32: "submitted",
    49: "approved",
    34: "signed",
    35: "signed",
}

# SaleLeadInfo.tsx — tabs that stay visible regardless of nextStatus cutoff
ALWAYS_VISIBLE_STEP_VALUES = frozenset({"nurture"})

# lead-access/index.ts — restricted agent view when hasFullAccess is false
SALES_RESTRICTED_TAB_VALUES = frozenset({"profile", "notes"})

# ---------------------------------------------------------------------------
# Lead-detail tab definitions — apps/nextjs/src/types/lead.ts
# Nova Worksheet tab is included (isNovaWorksheetVisible() is true on dev CRM).
# ---------------------------------------------------------------------------

SALES_FRONTEND_STEPS: list[tuple[str, str]] = [
    ("Profile", "profile"),
    ("Co-borrowers", "co-borrowers"),
    ("Notes", "notes"),
    ("RC Call Details", "rc-call-details"),
    ("Documents", "documents"),
    ("Activity logs", "activity-logs"),
    ("Marketing", "marketing"),
    ("Lead History", "lead-history"),
    ("Nova Worksheet", "nova-worksheet"),
    ("Mortgage Snapshot", "mortgage-snapshot"),
    ("DLO", "dlo"),
    ("Nurture", "nurture"),
    ("Appraisal Order", "appraisal-order"),
    ("Submitted", "submitted"),
    ("Approved", "approved"),
    ("Signed", "signed"),
]

SALES_BACKEND_STEPS: list[tuple[str, str]] = [
    ("Profile", "profile"),
    ("Notes", "notes"),
    ("RC Call Details", "rc-call-details"),
    ("Documents", "documents"),
    ("Activity logs", "activity-logs"),
    ("Marketing", "marketing"),
    ("Co-borrowers", "co-borrowers"),
    ("Lead History", "lead-history"),
    ("Mortgage Snapshot", "mortgage-snapshot"),
    ("DLO", "dlo"),
    ("Appraisal Order", "appraisal-order"),
    ("Submitted", "submitted"),
    ("Approved", "approved"),
    ("Signed", "signed"),
]

# SaleBackendLeadInfo.tsx — BE tab unlock (distinct from stage-utils FE map).
SALES_BACKEND_NEXT_STATUS_TO_LAST_STEP: dict[int, str] = {
    30: "dlo",
    31: "appraisal-order",
    32: "submitted",
    49: "approved",
    34: "signed",
    35: "signed",
}

# Shared stage tab names — identical in FE and BE (lead.ts SALES_*_STEPS).
SHARED_STAGE_TAB_NAMES: tuple[str, ...] = (
    "Mortgage Snapshot",
    "Appraisal Order",
    "Submitted",
    "Approved",
    "Signed",
)

# Stage-only tab sets for inline workflow verification (Phase A).
# Non-stage tabs (Profile, Notes, Activity logs, etc.) are intentionally excluded.
FE_STAGE_TAB_NAMES: frozenset[str] = frozenset(
    {NOVA_WORKSHEET_TAB_NAME, *SHARED_STAGE_TAB_NAMES, "Nurture"}
)
BE_STAGE_TAB_NAMES: frozenset[str] = frozenset(SHARED_STAGE_TAB_NAMES)

LEAD_BUCKET_STEPS: list[tuple[str, str]] = [
    ("Profile", "profile"),
    ("Co-borrowers", "co-borrowers"),
    ("Notes", "notes"),
    ("RC Call Details", "rc-call-details"),
    ("Documents", "documents"),
    ("Activity logs", "activity-logs"),
    ("Marketing", "marketing"),
]

# ---------------------------------------------------------------------------
# URL patterns — sidebar.ts hrefs + LeadGeneralInfoForm / MoveToSalesButton routing
# ---------------------------------------------------------------------------

URL_PATTERNS: dict[str, str] = {
    "lead_bucket_list": r"/lead-bucket(?:\?|$)",
    "lead_bucket_detail": r"/lead-bucket/[^/?]+",
    "my_leads_list": r"/my-leads(?:\?|$)",
    "my_leads_detail": r"/my-leads/[^/?]+",
    "sales_frontend_list": r"/sales(?:\?|$)",
    "sales_frontend_detail": r"/sales/[^/?]+",
    "sales_backend_list": r"/sales-backend(?:\?|$)",
    "sales_backend_detail": r"/sales-backend/[^/?]+",
}

# ---------------------------------------------------------------------------
# Kanban bucket names — sidebar.ts + automation/utils/entity_navigation.py
# ---------------------------------------------------------------------------

KANBAN_BUCKETS: dict[str, str] = {
    "lead_bucket": "Lead Bucket",
    "my_leads": "My Leads",
    "my_deals": "My Deals",
    "sales_backend": "Sales Backend",
}

# Admin sidebar renames My Deals → Sales Frontend (SidebarButtons.tsx); list path stays /sales.

# ---------------------------------------------------------------------------
# Transition toasts — CRM components
# ---------------------------------------------------------------------------

MOVE_TO_SALES_SUCCESS_TOAST = "Lead updated successfully"
GENERAL_INFO_UPDATED_TOAST = "Lead details updated successfully"

# MoveToSalesButton.tsx sets status APPLICATION_RECEIVED_STATUS_ID (8).
MOVE_TO_SALES_STATUS_ID = APPLICATION_RECEIVED_STATUS_ID
MOVE_TO_SALES_NEXT_STATUS_ID = NEXT_STATUS_MAP[APPLICATION_RECEIVED_STATUS_ID]
MOVE_TO_SALES_URL_PATTERN = URL_PATTERNS["sales_frontend_detail"]
MOVE_TO_SALES_STATUS_CONTAINS = APPLICATION_RECEIVED_STATUS_NAME

# ---------------------------------------------------------------------------
# Nova / Scarlett — SaleLeadInfo.tsx, ScarlettPushRequiredDialog.tsx
# ---------------------------------------------------------------------------

SCARLETT_REQUIRED_DIALOG_TITLE = "Scarlett Data Required"
SCARLETT_REQUIRED_DIALOG_ACTION = "Got it"
NOVA_WORKSHEET_DIALOG_TITLE = "NOVA Worksheet"

NOVA_WORKSHEET_DIALOG_TABS: list[str] = [
    "Home Equity Ad-On",
    "Mortgage Refinance",
    "Home Purchase",
]

NOVA_WORKSHEET_DIALOG_ACTIONS: list[str] = [
    "Refresh from Scarlett",
    "Save Worksheet",
]

# Status 59 (Nova Worksheet) → nextStatus 13 unlocks Mortgage Snapshot tab.
NOVA_BYPASS_NEXT_STATUS_ID = NEXT_STATUS_MAP[NOVA_WORKSHEET_STATUS_ID]
NOVA_BYPASS_STATUS_CONTAINS = NOVA_WORKSHEET_TAB_NAME

# ---------------------------------------------------------------------------
# Tab visibility helpers (mirror SaleLeadInfo.filterStepsByNextStatus)
# ---------------------------------------------------------------------------


def _filter_steps_by_next_status(
    steps: list[tuple[str, str]],
    next_status: int | None,
) -> list[tuple[str, str]]:
    if next_status is None:
        return list(steps)
    last_step_value = NEXT_STATUS_TO_LAST_STEP.get(next_status)
    if not last_step_value:
        return list(steps)
    last_index = next(
        (index for index, (_, value) in enumerate(steps) if value == last_step_value),
        -1,
    )
    if last_index == -1:
        return list(steps)
    return [
        step
        for index, step in enumerate(steps)
        if index <= last_index or step[1] in ALWAYS_VISIBLE_STEP_VALUES
    ]


def sales_frontend_visible_tab_names(
    next_status: int | None,
    *,
    is_admin: bool = True,
    has_full_access: bool = True,
    include_dlo: bool = False,
) -> list[str]:
    """Return tab display names visible on /sales lead detail for a nextStatus."""
    steps = _filter_steps_by_next_status(SALES_FRONTEND_STEPS, next_status)
    if not include_dlo:
        steps = [step for step in steps if step[1] != "dlo"]
    if not has_full_access:
        steps = [step for step in steps if step[1] in SALES_RESTRICTED_TAB_VALUES]
    elif not is_admin:
        steps = [step for step in steps if step[1] != "activity-logs"]
    return [name for name, _ in steps]


def sales_frontend_hidden_tab_names(
    next_status: int | None,
    *,
    is_admin: bool = True,
    has_full_access: bool = True,
    include_dlo: bool = False,
) -> list[str]:
    """Return tab display names that must not render for the given nextStatus."""
    visible_values = {
        value
        for _, value in _filter_steps_by_next_status(SALES_FRONTEND_STEPS, next_status)
    }
    visible_values.update(ALWAYS_VISIBLE_STEP_VALUES)

    hidden: list[str] = []
    for name, value in SALES_FRONTEND_STEPS:
        if value in visible_values:
            continue
        if value == "dlo" and not include_dlo:
            hidden.append(name)
            continue
        if not has_full_access:
            continue
        if value == "activity-logs" and not is_admin:
            continue
        hidden.append(name)
    return hidden


def _filter_backend_steps_by_next_status(
    steps: list[tuple[str, str]],
    next_status: int | None,
) -> list[tuple[str, str]]:
    if next_status is None:
        return list(steps)
    last_step_value = SALES_BACKEND_NEXT_STATUS_TO_LAST_STEP.get(next_status)
    if not last_step_value:
        return list(steps)
    step_values = {value for _, value in steps}
    if last_step_value not in step_values:
        # DLO is often excluded from automation steps but still gates BE unlock maps.
        if last_step_value == "dlo" and "mortgage-snapshot" in step_values:
            last_step_value = "mortgage-snapshot"
        else:
            return list(steps)
    last_index = next(
        (index for index, (_, value) in enumerate(steps) if value == last_step_value),
        -1,
    )
    if last_index == -1:
        return list(steps)
    return [step for index, step in enumerate(steps) if index <= last_index]


def sales_backend_visible_tab_names(
    next_status: int | None,
    *,
    is_admin: bool = True,
    has_full_access: bool = True,
    include_dlo: bool = False,
) -> list[str]:
    """Return tab display names visible on /sales-backend lead detail."""
    steps = list(SALES_BACKEND_STEPS)
    if not include_dlo:
        steps = [step for step in steps if step[1] != "dlo"]
    steps = _filter_backend_steps_by_next_status(steps, next_status)
    if not has_full_access:
        steps = [step for step in steps if step[1] in SALES_RESTRICTED_TAB_VALUES]
    elif not is_admin:
        steps = [step for step in steps if step[1] != "activity-logs"]
    return [name for name, _ in steps]


def sales_backend_hidden_tab_names(
    next_status: int | None,
    *,
    is_admin: bool = True,
    has_full_access: bool = True,
    include_dlo: bool = False,
) -> list[str]:
    """Return tab display names that must not render on /sales-backend."""
    visible_steps = list(SALES_BACKEND_STEPS)
    if not include_dlo:
        visible_steps = [step for step in visible_steps if step[1] != "dlo"]
    visible_steps = _filter_backend_steps_by_next_status(visible_steps, next_status)
    visible_values = {value for _, value in visible_steps}

    hidden: list[str] = []
    for name, value in SALES_BACKEND_STEPS:
        if value in visible_values:
            continue
        if value == "dlo" and not include_dlo:
            hidden.append(name)
            continue
        if not has_full_access:
            continue
        if value == "activity-logs" and not is_admin:
            hidden.append(name)
            continue
        hidden.append(name)
    return hidden


# Precomputed for Move to Sales smoke (status 8 → nextStatus 59, admin, no DLO data).
MOVE_TO_SALES_VISIBLE_TABS = sales_frontend_visible_tab_names(
    MOVE_TO_SALES_NEXT_STATUS_ID,
    is_admin=True,
    has_full_access=True,
    include_dlo=False,
)
MOVE_TO_SALES_HIDDEN_TABS = sales_frontend_hidden_tab_names(
    MOVE_TO_SALES_NEXT_STATUS_ID,
    is_admin=True,
    has_full_access=True,
    include_dlo=False,
)

# FE agent assigned to the lead has hasFullAccess (useLeadFullAccess.ts).
FE_NOVA_BYPASS_VISIBLE_TABS = sales_frontend_visible_tab_names(
    NOVA_BYPASS_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
)
FE_NOVA_BYPASS_HIDDEN_TABS = sales_frontend_hidden_tab_names(
    NOVA_BYPASS_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
)

# assign_be_backend sets status 29 → nextStatus 30 (Mortgage Snapshot stage).
BE_APPLICATION_RECEIVED_STATUS_ID = RENEWAL_APPLICATION_RECEIVED_STATUS_ID
BE_APPLICATION_NEXT_STATUS_ID = NEXT_STATUS_MAP[BE_APPLICATION_RECEIVED_STATUS_ID]
BE_STATUS_CONTAINS = "Application Received"

BE_ASSIGNMENT_VISIBLE_TABS = sales_backend_visible_tab_names(
    BE_APPLICATION_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
)
BE_ASSIGNMENT_HIDDEN_TABS = sales_backend_hidden_tab_names(
    BE_APPLICATION_NEXT_STATUS_ID,
    is_admin=False,
    has_full_access=True,
    include_dlo=False,
)

# ---------------------------------------------------------------------------
# Backend stage display names — apps/nextjs/src/types/lead.ts SALES_BACKEND_STAGES
# ---------------------------------------------------------------------------

RENEWAL_MORTGAGE_SNAPSHOT_STATUS_NAME = "Mortgage Snapshot"
RENEWAL_APPRAISAL_ORDERED_STATUS_NAME = "Appraisal Ordered"
RENEWAL_SUBMITTED_STATUS_NAME = "Submitted"
RENEWAL_APPROVED_STATUS_NAME = "Approved"
RENEWAL_SIGNED_STATUS_NAME = "Signed"

# StageUpdateDialog toasts — shared stage components (MortgageSnapshot, AppraisalOrder, …)
BE_MORTGAGE_SNAPSHOT_SUCCESS_TOAST = "Lead moved to Appraisal Ordered successfully"
BE_APPRAISAL_ORDER_SUCCESS_TOAST = "Lead moved to Submitted successfully"
BE_SUBMITTED_SUCCESS_TOAST = "Lead moved to Approved successfully"
BE_APPROVED_SUCCESS_TOAST = "Lead moved to Signed successfully"
BE_SIGNED_SUCCESS_TOAST = "Lead moved to Signed successfully"

# nextStatus after each stage completion — NEXT_STATUS_MAP on the post-transition status id
BE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID = NEXT_STATUS_MAP[RENEWAL_MORTGAGE_SNAPSHOT_STATUS_ID]
BE_APPRAISAL_ORDER_NEXT_STATUS_ID = NEXT_STATUS_MAP[RENEWAL_APPRAISAL_ORDER_STATUS_ID]
BE_SUBMITTED_NEXT_STATUS_ID = NEXT_STATUS_MAP[RENEWAL_SUBMITTED_STATUS_ID]
BE_APPROVED_NEXT_STATUS_ID = NEXT_STATUS_MAP[RENEWAL_APPROVED_STATUS_ID]

_BE_STAGE_AGENT = dict(is_admin=False, has_full_access=True, include_dlo=False)

BE_MORTGAGE_SNAPSHOT_VISIBLE_TABS = sales_backend_visible_tab_names(
    BE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)
BE_MORTGAGE_SNAPSHOT_HIDDEN_TABS = sales_backend_hidden_tab_names(
    BE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)

BE_APPRAISAL_ORDER_VISIBLE_TABS = sales_backend_visible_tab_names(
    BE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)
BE_APPRAISAL_ORDER_HIDDEN_TABS = sales_backend_hidden_tab_names(
    BE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)

BE_SUBMITTED_VISIBLE_TABS = sales_backend_visible_tab_names(
    BE_SUBMITTED_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)
BE_SUBMITTED_HIDDEN_TABS = sales_backend_hidden_tab_names(
    BE_SUBMITTED_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)

BE_APPROVED_VISIBLE_TABS = sales_backend_visible_tab_names(
    BE_APPROVED_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)
BE_APPROVED_HIDDEN_TABS = sales_backend_hidden_tab_names(
    BE_APPROVED_NEXT_STATUS_ID,
    **_BE_STAGE_AGENT,
)

BE_SIGNED_VISIBLE_TABS = sales_backend_visible_tab_names(
    None,
    **_BE_STAGE_AGENT,
)
BE_SIGNED_HIDDEN_TABS = sales_backend_hidden_tab_names(
    None,
    **_BE_STAGE_AGENT,
)

# Non-assigned agent view (hasFullAccess=false) — lead-access/index.ts
FE_NON_ASSIGNED_VISIBLE_TABS = ["Profile", "Notes"]
FE_NON_ASSIGNED_HIDDEN_TABS = [
    name for name, _ in SALES_FRONTEND_STEPS if name not in FE_NON_ASSIGNED_VISIBLE_TABS
]

BE_NON_ASSIGNED_VISIBLE_TABS = ["Profile", "Notes"]
BE_NON_ASSIGNED_HIDDEN_TABS = [
    name for name, _ in SALES_BACKEND_STEPS if name not in BE_NON_ASSIGNED_VISIBLE_TABS
]

# ---------------------------------------------------------------------------
# Kanban column inventories — apps/nextjs/src/types/lead.ts SALES_*_STAGES
# Admin Sales Frontend = My Deals bucket (/sales) with admin sidebar label.
# ---------------------------------------------------------------------------

ADMIN_SALES_FRONTEND_KANBAN_COLUMNS: tuple[str, ...] = (
    "Application Received",
    NOVA_WORKSHEET_TAB_NAME,
    "Mortgage Snapshot",
    "Nurture",
    RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
    "Submitted",
    "Approved",
    "Signed",
    "Not Signed",
)

FE_MY_DEALS_KANBAN_COLUMNS: tuple[str, ...] = ADMIN_SALES_FRONTEND_KANBAN_COLUMNS

ADMIN_SALES_BACKEND_KANBAN_COLUMNS: tuple[str, ...] = (
    "Expired Renewal Lead",
    "6 Month Renewal Lead",
    "9 Month Maturity",
    "Application Received",
    "Mortgage Snapshot",
    RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
    "Submitted",
    "Approved",
    "Signed",
    "Not Signed",
)

BE_SALES_BACKEND_KANBAN_COLUMNS: tuple[str, ...] = ADMIN_SALES_BACKEND_KANBAN_COLUMNS

# Stage completion → kanban column title (post-transition placement)
FE_STAGE_KANBAN_COLUMN: dict[str, str] = {
    "mortgage_snapshot": "Mortgage Snapshot",
    "appraisal_order": RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
    "submitted": "Submitted",
    "approved": "Approved",
    "signed": "Signed",
}

BE_STAGE_KANBAN_COLUMN: dict[str, str] = {
    "mortgage_snapshot": "Mortgage Snapshot",
    "appraisal_order": RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
    "submitted": "Submitted",
    "approved": "Approved",
    "signed": "Signed",
}

FE_STAGE_STATUS_LABEL: dict[str, str] = {
    "mortgage_snapshot": "Mortgage Snapshot",
    "appraisal_order": "Appraisal Order",
    "submitted": "Submitted",
    "approved": "Approved",
    "signed": "Signed",
}

BE_STAGE_STATUS_LABEL: dict[str, str] = {
    "mortgage_snapshot": "Mortgage Snapshot",
    "appraisal_order": RENEWAL_APPRAISAL_ORDERED_STATUS_NAME,
    "submitted": "Submitted",
    "approved": "Approved",
    "signed": "Signed",
}

# ---------------------------------------------------------------------------
# Stage tab visibility — CRM nextStatus drives SaleLeadInfo / SaleBackendLeadInfo
# DLO is ignored (include_dlo=False). Sales Backend has no Nurture tab.
# ---------------------------------------------------------------------------

FE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID = NEXT_STATUS_MAP[MORTGAGE_SNAPSHOT_STATUS_ID]
FE_APPRAISAL_ORDER_NEXT_STATUS_ID = NEXT_STATUS_MAP[APPRAISAL_ORDER_STATUS_ID]
FE_SUBMITTED_NEXT_STATUS_ID = NEXT_STATUS_MAP[SUBMITTED_STATUS_ID]
FE_APPROVED_NEXT_STATUS_ID = NEXT_STATUS_MAP[APPROVED_STATUS_ID]

STAGE_ENTRY_NEXT_STATUS: dict[tuple[Pipeline, str], int | None] = {
    ("fe", "mortgage_snapshot"): NOVA_BYPASS_NEXT_STATUS_ID,
    ("fe", "appraisal_order"): FE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    ("fe", "submitted"): FE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    ("fe", "approved"): FE_SUBMITTED_NEXT_STATUS_ID,
    ("fe", "signed"): FE_APPROVED_NEXT_STATUS_ID,
    ("be", "mortgage_snapshot"): BE_APPLICATION_NEXT_STATUS_ID,
    ("be", "appraisal_order"): BE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    ("be", "submitted"): BE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    ("be", "approved"): BE_SUBMITTED_NEXT_STATUS_ID,
    ("be", "signed"): BE_APPROVED_NEXT_STATUS_ID,
}

STAGE_POST_TRANSITION_NEXT_STATUS: dict[tuple[Pipeline, str], int | None] = {
    ("fe", "mortgage_snapshot"): FE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    ("fe", "appraisal_order"): FE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    ("fe", "submitted"): FE_SUBMITTED_NEXT_STATUS_ID,
    ("fe", "approved"): FE_APPROVED_NEXT_STATUS_ID,
    ("fe", "signed"): None,
    ("be", "mortgage_snapshot"): BE_MORTGAGE_SNAPSHOT_NEXT_STATUS_ID,
    ("be", "appraisal_order"): BE_APPRAISAL_ORDER_NEXT_STATUS_ID,
    ("be", "submitted"): BE_SUBMITTED_NEXT_STATUS_ID,
    ("be", "approved"): BE_APPROVED_NEXT_STATUS_ID,
    ("be", "signed"): None,
}


def pipeline_for_bucket(bucket: str) -> Pipeline:
    """Return fe or be from entity_navigation bucket constant."""
    if bucket == "Sales Backend":
        return "be"
    return "fe"


def tab_expectations_for_next_status(
    next_status_id: int | None,
    *,
    pipeline: Pipeline,
    is_admin: bool = True,
    has_full_access: bool = True,
) -> tuple[list[str], list[str]]:
    """Visible and hidden tab names for a CRM nextStatus (DLO excluded)."""
    kwargs = dict(
        is_admin=is_admin,
        has_full_access=has_full_access,
        include_dlo=False,
    )
    if pipeline == "be":
        visible = sales_backend_visible_tab_names(next_status_id, **kwargs)
        hidden = sales_backend_hidden_tab_names(next_status_id, **kwargs)
    else:
        visible = sales_frontend_visible_tab_names(next_status_id, **kwargs)
        hidden = sales_frontend_hidden_tab_names(next_status_id, **kwargs)
    return visible, hidden


def tab_expectations_for_stage(
    stage_key: str,
    *,
    pipeline: Pipeline,
    moment: StageTabMoment,
    is_admin: bool = True,
    has_full_access: bool = True,
) -> tuple[list[str], list[str]]:
    """Resolve entry or post-transition tab expectations for a pipeline stage."""
    mapping = (
        STAGE_ENTRY_NEXT_STATUS
        if moment == "entry"
        else STAGE_POST_TRANSITION_NEXT_STATUS
    )
    next_status_id = mapping[(pipeline, stage_key)]
    return tab_expectations_for_next_status(
        next_status_id,
        pipeline=pipeline,
        is_admin=is_admin,
        has_full_access=has_full_access,
    )


def stage_tab_names_for_pipeline(pipeline: Pipeline) -> frozenset[str]:
    """Return the stage-tab name set for FE or BE pipeline."""
    return FE_STAGE_TAB_NAMES if pipeline == "fe" else BE_STAGE_TAB_NAMES


def filter_to_stage_tabs(
    visible: list[str],
    hidden: list[str],
    *,
    pipeline: Pipeline,
) -> tuple[list[str], list[str]]:
    """Keep only stage workflow tabs; drop Profile, Notes, Activity logs, etc."""
    allowed = stage_tab_names_for_pipeline(pipeline)
    return (
        [name for name in visible if name in allowed],
        [name for name in hidden if name in allowed],
    )


def stage_tab_expectations_for_stage(
    stage_key: str,
    *,
    pipeline: Pipeline,
    moment: StageTabMoment,
    is_admin: bool = True,
    has_full_access: bool = True,
) -> tuple[list[str], list[str]]:
    """Entry/post stage tab visibility — stage tabs only, not auxiliary tabs."""
    visible, hidden = tab_expectations_for_stage(
        stage_key,
        pipeline=pipeline,
        moment=moment,
        is_admin=is_admin,
        has_full_access=has_full_access,
    )
    return filter_to_stage_tabs(visible, hidden, pipeline=pipeline)
