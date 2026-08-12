# PROJECT_CONTEXT.md

Documents only what actually exists in the repository. Nothing is invented.

---

## 1. High-Level Project Overview

**Project:** Nuborrow Agent Dashboard CRM — UI Test Automation
**Framework:** Python + Playwright (sync API) + pytest
**Design Pattern:** Page Object Model (POM)
**Target Application:** `https://dev.crm.vibecircuit.ca` (configured in `utils/config.py`)
**Browser:** Chromium (launched via Playwright)
**Cursor AI Rule:** `automation/.cursor/rules/automation.mdc` — `alwaysApply: true` — enforces POM, minimal diffs, no duplication, no hardcoded values, reuse-first policy.

The suite drives a deployed Next.js CRM used by mortgage agents. It validates end-to-end workflows including authentication (Admin, Frontend Agent, Backend Agent), lead creation and editing, co-borrower management, notes, the full Sales Frontend pipeline, Sales Backend renewal pipeline, compliance, client care, marketing, RBAC, and workflow orchestration smoke tests.

**Current scale:** 65 collected tests, 25 page-object modules, multi-role session fixtures, workflow verification layer, external MS App / NTP App verification, and full-flow orchestrators for Admin, FE, and BE.

---

## 2. Folder Structure

```
automation/
├── .cursor/rules/automation.mdc     # Cursor AI coding rules (alwaysApply)
├── AI/                              # Documentation (this folder)
├── pages/                           # Page Object Model classes (25 modules)
├── tests/                           # Test cases (65 collected)
├── test_data/                       # JSON static fixtures (login.json)
├── test_page_data/                  # Per-feature Python data + workflow_expectations.py
├── utils/                           # Shared helpers (navigation, workflow, reporting, waits)
├── reports/                         # HTML reports, screenshots, videos, traces
├── logs/                            # test.log
├── conftest.py                      # Multi-role fixtures and pytest hooks
├── pytest.ini                       # Markers and default report options
└── requirements.txt
```

Key `utils/` modules (automation framework):

| Module                             | Purpose                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `entity_navigation.py`             | Bucket constants + `open_bucket_record()` / `verify_bucket_record_visible()`                                        |
| `lead_assignment.py`               | `LeadAssignmentHelper` — assign FE/BE agents and statuses from Lead Bucket                                          |
| `lead_context.py`                  | Session-scoped bootstrap lead/deal names (`get_lead_context()`, `persist_*` helpers)                                |
| `workflow_verification.py`         | `WorkflowVerification` + transition constants (FE/BE)                                                               |
| `stage_transition_verification.py` | Stage-move URL/tab checks and toast verification helpers                                                            |
| `sales_flow_helpers.py`            | Stage smoke runners + `setup_be_assigned_lead()` + `run_backend_full_flow()`                                        |
| `sales_flow_orchestration.py`      | Reporting-aware full-flow orchestrators (`run_compliance_to_client_care_flow`, `run_backend_full_flow_reported`, …) |
| `sales_flow_regression_helpers.py` | Empty/invalid/smoke regression runners for all-cases E2E                                                            |
| `mortgage_snapshot_app_helpers.py` | MS App open/verify cycle from CRM Approved / Mortgage Snapshot save                                                 |
| `ntp_app_helpers.py`               | NTP App open/verify cycle from CRM Approved save                                                                    |
| `wait_helpers.py`                  | `select_google_places_suggestion()`, `ensure_complete_postal_code()`, `wait_for_url_pattern()`                      |
| `toast.py`                         | Sonner toast assertions (`[data-sonner-toast]`)                                                                     |
| `reporting.py`                     | HTML extras, screenshots, traces, test data capture                                                                 |
| `flow_step_reporting.py`           | Virtual per-module rows for `@flow_orchestrator` tests                                                              |
| `html_report_history.py`           | Unique HTML report paths and browsable run history                                                                  |

---

## 3. Automation Framework Architecture

### Layer separation

```
conftest.py  ──►  Fixtures (browser, page, auth)
     │
     ▼
tests/       ──►  Scenarios + Assertions
     │
     ▼
pages/       ──►  Locators + Business Actions
     │
     ▼
utils/       ──►  Config, Logger, Helpers, Assertions
     │
     ▼
test_page_data/ / test_data/  ──►  Input Data
```

### Key principles (enforced by `automation.mdc`)

- Always reuse existing fixtures, page methods, helpers, and config.
- Never duplicate locators or methods.
- Assertions belong only in tests, never in pages.
- Pages contain locators and actions only.
- No hardcoded URLs, credentials, timeouts, or environment values.
- Prefer `get_by_role()` and `get_by_label()` over CSS/XPath selectors.
- Avoid `sleep()` and `wait_for_timeout()` unless strictly necessary.
- Generate minimal diffs — never rewrite working code.

---

## 4. Page Object Structure

All page classes follow one of two patterns:

### Pattern A — Standalone POM

Locators defined in `__init__`, methods encapsulate single actions. Does **not** inherit `BasePage`.

Examples: `LoginPage`, `CreateLeadPage`, `LeadEditPage`, `CoBorrowerPage`, `NotesPage`.

### Pattern B — BasePage inheritance

Locators defined in `__init__`, actions delegated through `BasePage` wrappers.

Examples: `MortgageSnapshotPage`, `AppraisalOrderPage`, `SubmittedPage`, `ApprovedPage`, `SignedPage`, `CompliancePage`, `ClientCarePage`, `MarketingPage`, `ProfilePage`, and external-app pages under `mortgage_snapshot_app/` and `ntp_app/`.

Shared stage page objects accept an optional `bucket=` argument on `open_*` methods (defaults to `MY_DEALS_BUCKET` / Sales Frontend). Pass `SALES_BACKEND_BUCKET` for Sales Backend tests.

### BasePage (`pages/base_page.py`)

BasePage provides reusable Playwright wrapper methods for:

- click
- fill
- select
- waits
- assertions
- screenshots
- navigation

<!-- Wraps Playwright actions into named, explicit-wait methods: -->

<!-- | Method | Action |
|--------|--------|
| `click(locator)` | Wait for visible, then click |
| `fill(locator, value)` | Wait for visible, fill string |
| `clear(locator)` | Fill with empty string |
| `press(locator, key)` | Key press |
| `select_option(locator, value)` | Dropdown selection |
| `check(locator)` | Check if unchecked |
| `uncheck(locator)` | Uncheck if checked |
| `is_visible(locator)` | Boolean visibility |
| `wait_visible(locator)` | Wait for visible state |
| `wait_hidden(locator)` | Wait for hidden state |
| `get_text(locator)` | Return text content |
| `verify_text(locator, expected)` | Assert exact text |
| `verify_contains_text(locator, expected)` | Assert contains text |
| `verify_visible(locator)` | Assert visible |
| `verify_hidden(locator)` | Assert hidden |
| `verify_enabled(locator)` | Assert enabled |
| `verify_disabled(locator)` | Assert disabled |
| `scroll_into_view(locator)` | Scroll element into view |
| `screenshot(path)` | Full-page screenshot |
| `goto(url)` | Navigate to URL |
| `refresh()` | Reload page |
| `wait_network()` | Wait for `networkidle` |
| `js_click(locator)` | JavaScript element click |
| `hover(locator)` | Mouse hover |
| `double_click(locator)` | Double click | -->

---

## 5. Fixtures

All fixtures are defined in `conftest.py`.

| Fixture               | Scope    | Description                                                     |
| --------------------- | -------- | --------------------------------------------------------------- |
| `playwright_instance` | session  | Starts `sync_playwright` context manager                        |
| `browser`             | session  | Launches Chromium with `Config.HEADLESS`                        |
| `browser_context`     | function | New browser context with video recording and Playwright tracing |
| `page`                | function | New page from `browser_context`; applies `Config.TIMEOUT`       |
| `admin_auth_state`    | session  | Admin login once via `LoginPage`; captures `storage_state()`    |
| `auth_state`          | session  | Alias for `admin_auth_state` (backward compatible)              |
| `fe_agent_auth_state` | session  | Frontend Agent login once; captures `storage_state()`           |
| `be_agent_auth_state` | session  | Backend Agent login once; captures `storage_state()`            |
| `authenticated_page`  | function | Fresh Admin page restored from `auth_state`                     |
| `admin_page`          | function | Fresh Admin page (explicit alias)                               |
| `fe_agent_page`       | function | Fresh Frontend Agent page from `fe_agent_auth_state`            |
| `be_agent_page`       | function | Fresh Backend Agent page from `be_agent_auth_state`             |
| `lead_context`        | session  | Session-scoped bootstrap lead/deal store (`utils/lead_context.py`) |
| `active_lead_name`    | function | Lead Bucket name from current run bootstrap                     |
| `active_deal_name`    | function | My Deals name after move-to-sales in the current run            |

Role credentials come from `Config.USERNAME`/`PASSWORD` (Admin), `Config.FE_USERNAME`/`FE_PASSWORD`, and `Config.BE_USERNAME`/`BE_PASSWORD` (overridable via `AUTOMATION_FE_*` / `AUTOMATION_BE_*` env vars).

### Hooks

| Hook                            | Trigger               | Action                                                            |
| ------------------------------- | --------------------- | ----------------------------------------------------------------- |
| `pytest_runtest_makereport`     | After each test phase | Appends HTML report extras via `reporting.append_report_extras()` |
| `pytest_html_results_summary`   | Report generation     | Prepends formatted summary HTML                                   |
| `pytest_sessionstart`           | Session start           | Records session timing for report summaries                       |
| `pytest_sessionfinish`          | Session end           | Injects virtual flow-step rows for `@flow_orchestrator` tests     |
| `pytest_configure`              | Startup               | Clears stale `AUTOMATION_MY_*_DEAL_NAME` env overrides            |
| `pytest_collection_modifyitems` | Collection            | Sorts negative/empty cases before valid cases per module          |

On failure, authenticated role fixtures (`admin_page`, `fe_agent_page`, `be_agent_page`) capture screenshots and Playwright traces via `reporting.py` and `_stop_tracing()`.

---

## 6. Utilities

### `utils/config.py` — `Config` class

Central runtime configuration.

| Attribute                                | Value / Source                                                          |
| ---------------------------------------- | ----------------------------------------------------------------------- |
| `BASE_URL`                               | `https://dev.crm.vibecircuit.ca`                                        |
| `MORTGAGE_SNAPSHOT_APP_URL`              | MS App base URL (env: `MORTGAGE_SNAPSHOT_APP_URL`)                      |
| `NTP_APP_URL`                            | NTP App base URL (env: `NTP_APP_URL`)                                   |
| `MS_APP_LEAD_SYNC_TIMEOUT_MS`            | Lead sync wait for MS/NTP App after CRM save                            |
| `BROWSER`                                | `chromium`                                                              |
| `TIMEOUT`                                | `30000` ms                                                              |
| `HEADLESS`                               | `False`                                                                 |
| `SLOW_MO`                                | `1000` ms                                                               |
| `VIEWPORT_WIDTH` / `VIEWPORT_HEIGHT`     | `1920` / `1080`                                                         |
| `USERNAME` / `PASSWORD`                  | Admin credentials                                                       |
| `FE_USERNAME` / `FE_PASSWORD`            | Frontend Agent — env `AUTOMATION_FE_USERNAME`, `AUTOMATION_FE_PASSWORD` |
| `BE_USERNAME` / `BE_PASSWORD`            | Backend Agent — env `AUTOMATION_BE_USERNAME`, `AUTOMATION_BE_PASSWORD`  |
| `FE_AGENT_LABEL`, `BE_AGENT_LABEL`, etc. | Imported from `test_page_data/test_entities.py`                         |

### Workflow & orchestration (Phases 5–12)

| Module                                    | Purpose                                                                                             |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `entity_navigation.py`                    | `LEAD_BUCKET`, `MY_LEADS_BUCKET`, `MY_DEALS_BUCKET`, `SALES_BACKEND_BUCKET`; `open_bucket_record()` |
| `lead_assignment.py`                      | `LeadAssignmentHelper.assign_fe_nova_bypass()`, `assign_be_backend()`                               |
| `workflow_verification.py`                | `WorkflowVerification` — tab visibility, stage transitions, FE/BE transition constants              |
| `test_page_data/workflow_expectations.py` | CRM-derived status IDs, tab names, toast messages, RBAC expectations                                |
| `sales_flow_helpers.py`                   | Stage smoke runners, `setup_be_assigned_lead()`, `run_backend_full_flow()`                          |
| `sales_flow_orchestration.py`             | Reporting-aware orchestrators                                                                       |
| `sales_flow_regression_helpers.py`        | All-cases regression runners                                                                        |
| `wait_helpers.py`                         | `select_google_places_suggestion()`, `ensure_complete_postal_code()`, `wait_for_url_pattern()` |
| `mortgage_snapshot_app_helpers.py`        | MS App workflow orchestration from CRM                                                                  |
| `ntp_app_helpers.py`                      | NTP App workflow orchestration from CRM Approved                                                        |
| `flow_step_reporting.py`                  | Virtual per-module HTML rows for `@flow_orchestrator` tests                                             |
| `html_report_history.py`                  | Unique report filenames and run index                                                                   |
| `reporting.py`                            | Screenshots, traces, test data capture, HTML extras                                                     |

### Other utilities

| Module                                       | Purpose                                                        |
| -------------------------------------------- | -------------------------------------------------------------- |
| `utils/logger.py` → `get_logger()`           | File logger → `logs/test.log`                                  |
| `utils/screenshots.py` → `take_screenshot()` | Timestamped failure screenshots                                |
| `utils/test_data_factory.py`                 | `valid_lead_data()`, `get_lead_cases()`, `get_last_valid_lead_data()` |
| `utils/toast.py` → `Toast`                   | Sonner toast assertions (`[data-sonner-toast]`)                |
| `utils/validations.py` → `Validations`       | Inline field-error assertions (`div.text-red-500`)             |

---

## 7. Configuration

| File                           | Purpose                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| `utils/config.py`              | Runtime config — browser, URL, credentials, timeouts, viewport |
| `pytest.ini`                   | Test runner config — options, `testpaths`, markers             |
| `test_data/login.json`         | JSON credential store for login parametrization                |
| `.cursor/rules/automation.mdc` | Cursor AI coding standards — `alwaysApply: true`               |

**`pytest.ini` markers:**

```ini
markers =
    smoke: quick tests
    module_smoke: single-module happy-path tests (require pre-existing deal state)
    regression: full test suites
    flow_orchestrator: single-run E2E flow with virtual per-module HTML reporting
    fe_agent: frontend agent role tests
    be_agent: backend agent role tests
```

Run by marker:

```bash
pytest -m smoke
pytest -m module_smoke
pytest -m regression
pytest -m fe_agent
pytest -m be_agent
pytest -m flow_orchestrator
```

---

## 8. Logging

| Aspect        | Detail                                                                                    |
| ------------- | ----------------------------------------------------------------------------------------- |
| Library       | Python `logging` (stdlib)                                                                 |
| Logger name   | `automation_logger`                                                                       |
| Level         | `INFO`                                                                                    |
| Handler       | `FileHandler` → `logs/test.log`                                                           |
| Format        | `%(asctime)s - %(levelname)s - %(message)s`                                               |
| Invocation    | `logger = get_logger()` at the top of each test file                                      |
| Usage pattern | `logger.info(...)` in tests before major actions; `logger.error(...)` in the failure hook |

Console logging: Not Found (no `StreamHandler` configured).

---

## 9. Test Organization

All tests live in `tests/`. **65 tests** collected.

| Category                | Example files                                                                                                                    | Fixture / marker                                |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Authentication          | `test_login_page.py`                                                                                                             | `page`                                          |
| Lead CRUD               | `test_create_lead.py`, `test_lead_edit.py`, `test_add_coborrower.py`, `test_note.py`                                             | `authenticated_page` / `admin_page`             |
| Sales Frontend stages   | `test_mortgage_snapshot.py`, `test_appraisal_order.py`, `test_submitted.py`, `test_approved.py`, `test_signed.py`                | `admin_page`, `@module_smoke`                   |
| Sales Backend stages    | `test_be_mortgage_snapshot.py`, `test_be_appraisal_order.py`, `test_be_submitted.py`, `test_be_approved.py`, `test_be_signed.py` | `be_agent_page`, `@be_agent`, `@module_smoke`   |
| RBAC                    | `test_fe_agent_rbac.py`, `test_be_agent_rbac.py`, `test_ms_app_rbac.py`                                                          | `fe_agent_page` / `be_agent_page` / `admin_page` |
| External apps           | `test_mortgage_snapshot_app_display.py`, `test_ntp_app_display.py`                                                                | `authenticated_page`, `@smoke`                  |
| Post-sales              | `test_compliance.py`, `test_client_care.py`, `test_marketing.py`, `test_signed_marketing.py`                                       | `admin_page`, `@module_smoke`                   |
| Flow orchestrators      | `test_move_to_sales_flow.py`, `test_full_sales_frontend_flow.py`, `test_admin_backend_flows.py`, `test_fe_agent_flows.py`, `test_be_agent_flows.py` | `@flow_orchestrator`, `@smoke` or `@regression` |
| Agent regression        | `test_fe_agent_regression.py`, `test_be_agent_regression.py`                                                                     | `@fe_agent` / `@be_agent`, `@regression`        |
| Helpers (not collected) | `be_stage_test_helpers.py`                                                                                                       | —                                               |

Stage smokes and orchestrators delegate to `sales_flow_helpers.py` and `sales_flow_orchestration.py` rather than duplicating navigation logic in tests.

---

## 10. Data Management

### Static JSON

- `test_data/login.json` — valid and invalid user credentials for login tests.

### Static Python dicts

- `test_page_data/addcoborrower_data.py` — `test_data` dict (lead name, co-borrower personal/employment info).
- `test_page_data/lead_edit_data.py` — `lead_edit_data` dict (contact, gender, address, DOB, mortgage, property, employment).
- `test_page_data/note_data.py` — `notes_test_data` dict (lead name, note text, heading, status, updated text).

### Dynamic Python dataclass with random generation

- `test_page_data/mortgage_snapshot_data.py` — `MortgageSnapshotData` dataclass. Uses `RandomGenerator` via `field(default_factory=...)` for all numeric and text fields. Static fields: `deal_name`, `option4_type`, `option5_type`, `plan_type`.

### Random data generator

- `test_page_data/random_gen_data.py` — `RandomGenerator` class. Uses `faker` library (locale `en_CA`) and Python `random`.

| Category   | Methods                                                                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Person     | `first_name`, `last_name`, `full_name`, `email`, `phone`, `company_name`, `job_title`, `lead_identity()` |
| Address    | `street`, `city`, `province`, `postal_code`, `canadian_postal_code()`, `full_address`, `street_number()` |
| Numbers    | `number`, `decimal`, `percentage`                                                                                                          |
| Mortgage   | `loan_amount`, `property_value`, `balance_owing`, `monthly_payment`, `monthly_savings`, `annual_income`, `interest_rate`, `mortgage_years` |
| Credit     | `credit_score`, `tds_score`, `credit_utilization`                                                                                          |
| Dates      | `birth_date`, `future_date`                                                                                                                |
| Text       | `word`, `sentence`, `paragraph`, `short_note`                                                                                              |
| IDs        | `vfli_number`, `random_string`                                                                                                             |
| Employment | `employer` (picks from fixed list)                                                                                                         |
| Utility    | `random_bool`, `random_choice`                                                                                                             |

### Factory functions

- `utils/test_data_factory.py` — `valid_lead_data()`, `get_lead_cases()`, `get_last_valid_lead_data()` — builds payloads via `RandomGenerator`; persists last valid payload for reporting and downstream flows.

---

## 11. Business Modules

Modules exercised by the automation suite:

| Module                                     | Tested                                                        |
| ------------------------------------------ | ------------------------------------------------------------- |
| Authentication                             | Yes — Admin, FE, BE session fixtures                          |
| Lead Creation / Edit / Co-Borrower / Notes | Yes                                                           |
| Lead Bucket / My Leads navigation          | Yes — via `entity_navigation.py` + `lead_assignment.py`       |
| Sales Frontend pipeline                    | Yes — stage smokes + full-flow orchestrators                  |
| Sales Backend pipeline                     | Yes — BE stage smokes + `test_admin_backend_flows.py`, `test_be_agent_flows.py` |
| RBAC (FE / BE / MS App tab visibility)     | Yes — `test_fe_agent_rbac.py`, `test_be_agent_rbac.py`, `test_ms_app_rbac.py`   |
| Compliance / Client Care / Marketing       | Yes                                                           |
| Nova Worksheet bypass                      | Yes — status 59 via orchestrators/helpers; dedicated `test_nova_worksheet.py` is skipped |
| Mortgage Snapshot                          | Yes — FE and BE stage tests                                   |
| Mortgage Snapshot App (external)           | Yes — `test_mortgage_snapshot_app_display.py`, `test_ms_app_rbac.py` |
| NTP Application (external)                 | Yes — `test_ntp_app_display.py`                               |
| Workflow Verification                      | Yes — `workflow_verification.py` + `workflow_expectations.py` |

Modules present in the application but not yet covered: DLO, Documents, Communication, Dashboard, Settings, Vendor Management, AI Underwriting, Tasks, Lead Merge, Search.

---

## 12. Existing Reusable Components

| Component                          | Location                                  | Reuse scope                                                              |
| ---------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------ |
| `BasePage`                         | `pages/base_page.py`                      | All stage page objects                                                   |
| `Config`                           | `utils/config.py`                         | All pages and conftest                                                   |
| `entity_navigation`                | `utils/entity_navigation.py`              | Bucket navigation (Lead Bucket, My Leads, Sales Frontend, Sales Backend) |
| `LeadAssignmentHelper`             | `utils/lead_assignment.py`                | Admin assignment from Lead Bucket                                        |
| `WorkflowVerification`             | `utils/workflow_verification.py`          | Stage transitions, tab visibility, RBAC                                  |
| `workflow_expectations`            | `test_page_data/workflow_expectations.py` | CRM-derived constants for verification                                   |
| Sales Flow Helpers / Orchestration | `utils/sales_flow_*.py`                   | Stage smokes and full-flow E2E                                           |
| `Toast`                            | `utils/toast.py`                          | Sonner toast assertions                                                  |
| `select_google_places_suggestion`  | `utils/wait_helpers.py`                   | Address autocomplete in lead forms                                       |
| `ensure_complete_postal_code`      | `utils/wait_helpers.py`                   | Re-fill Canadian postal code when Places autofill is incomplete          |
| `ProfilePage`                      | `pages/profile_page.py`                   | Read Profile tab fields for form-prefill verification                    |
| MS / NTP App helpers               | `utils/mortgage_snapshot_app_helpers.py`, `utils/ntp_app_helpers.py` | External-app open, presentation verify, RBAC, cleanup         |
| Multi-role fixtures                | `conftest.py`                             | `admin_page`, `fe_agent_page`, `be_agent_page`, `authenticated_page`     |

---

## 13. Naming Conventions

| Entity            | Convention                        | Example                                                            |
| ----------------- | --------------------------------- | ------------------------------------------------------------------ |
| Test files        | `test_<feature>.py`               | `test_create_lead.py`                                              |
| Test functions    | `test_<action>_<subject>`         | `test_add_edit_delete_note`                                        |
| Page classes      | `PascalCase`, suffix varies       | `CreateLeadPage`, `NotesPage`, `CoBorrowerPage`                    |
| Page files        | `snake_case`, no suffix           | `create_lead.py`, `note_page.py`                                   |
| Page methods      | `snake_case`, verb-first          | `open_lead()`, `fill_basic_info()`, `save_note()`                  |
| Utility classes   | `PascalCase`                      | `Config`, `Toast`, `Validations`, `RandomGenerator`                |
| Utility functions | `snake_case`                      | `get_logger()`, `take_screenshot()`, `valid_lead_data()`           |
| Data dicts        | `snake_case`                      | `test_data`, `lead_edit_data`, `notes_test_data`                   |
| Data dataclasses  | `PascalCase`                      | `MortgageSnapshotData`                                             |
| Fixtures          | `snake_case`                      | `authenticated_page`, `browser_context`                            |
| Markers           | lowercase                         | `smoke`, `module_smoke`, `regression`, `flow_orchestrator`, `fe_agent`, `be_agent` |
| Screenshot files  | `<test_name>_YYYYMMDD_HHMMSS.png` | `test_edit_lead_20260622_134609.png`                               |

---

## 14. Current Automation Coverage

**65 collected tests** covering authentication, lead management, Sales Frontend and Sales Backend pipelines, RBAC, compliance/post-sales flows, external MS App / NTP App verification, and full-flow orchestrators.

### Modules with no dedicated test coverage

DLO, Documents, Communication (email/SMS/chat), Dashboard, Settings, Vendor Management, AI Underwriting, Tasks, Lead Merge, Search, Lender Management, Activity Logs (standalone).

---

## 15. Known Architectural Patterns

### Multi-role session auth reuse

`admin_auth_state`, `fe_agent_auth_state`, and `be_agent_auth_state` each log in once per session. Role-specific page fixtures (`admin_page`, `fe_agent_page`, `be_agent_page`) restore cached `storage_state` — no repeated login per test.

### Workflow Verification layer

Stage transitions and tab visibility are verified through `WorkflowVerification` using constants from `workflow_expectations.py` (CRM-derived). Assertions live in helpers/tests, not page objects.

### Sales Flow Helpers / Orchestration

Stage smokes (`run_*_smoke()`) and full pipelines (`run_backend_full_flow()`, `run_compliance_to_client_care_flow()`) centralize navigation and verification. Orchestrator tests use `@flow_orchestrator` for virtual per-module HTML reporting.

### Failure artifact capture via hook

`pytest_runtest_makereport` appends HTML extras. On failure, role fixtures capture screenshots and Playwright trace zips under `reports/traces/`. Videos saved to `reports/videos/` on failure.

### Google Places address interaction

Use `select_google_places_suggestion()` from `wait_helpers.py` for address fields. After autocomplete, call `ensure_complete_postal_code()` when the postal field may be partially filled (Canadian format `K1A 0B1`).

### Locator chaining pattern (edit page dropdowns)

`LeadEditPage` resolves custom dropdown components by chaining: `page.locator("text=<Label>").locator("..").locator("button[role='combobox']")` — anchors the lookup to a visible label, then traverses to the sibling trigger button.

Future automation should always reuse existing page objects before introducing new ones.
