# Nuborrow CRM -- UI Test Automation

> **End-to-end UI automation** for the Nuborrow Agent Dashboard (CRM),
> built with **Python**, **Playwright**, and **pytest** using the **Page
> Object Model (POM)** design pattern.

This automation framework validates the complete CRM agent journey,
including authentication, lead management, sales workflows, compliance
workflows, and supporting applications such as Mortgage Snapshot and
NTP.

---

# AI Documentation Index

The `AI` folder serves as the knowledge base for this automation
framework.

## Repository Boundaries

- The application source code exists to help understand business
  logic, routing, APIs, React components, and workflows.
- You may read the entire repository when implementing automation.
- **Only the `Automation/` directory is writable.**
- Never modify application source code unless explicitly instructed.

## AI Documentation

---

File Purpose

---

README.md Entry point, setup guide, execution
instructions, and AI context loading
strategy.

STANDARDS.md Coding standards, Page Object Model
guidelines, locator strategy, testing
standards, and implementation rules.

PROJECT_STRUCTURE.md Repository architecture, routing, APIs,
React components, backend modules, and
application structure.

AUTOMATION_MAP.md Business workflows, CRM stages, external
applications, automation mapping, and
validation strategy.

PROJECT_CONTEXT.md Automation framework architecture,
reusable utilities, fixtures, helper
classes, naming conventions, and existing
implementation details.

PROMPTS.md Reusable Cursor prompts, templates, and
implementation examples.
-----------------------------------------------------------------------

## Documentation Loading Strategy

### Always Read

1.  README.md
2.  STANDARDS.md

### Load When Required

Task Additional Documentation

---

Understand application architecture PROJECT_STRUCTURE.md
Work on CRM workflows AUTOMATION_MAP.md
Extend the automation framework PROJECT_CONTEXT.md
Use reusable prompt templates PROMPTS.md

Only load documentation relevant to the current task.

---

## Tech Stack

- Python 3.13
- Playwright
- pytest
- pytest-html
- pytest-xdist
- Page Object Model (POM)

---

<!-- ## Folder Structure

``` text
automation/
├── pages/
├── tests/
├── utils/
├── test_data/
├── test_page_data/
├── reports/
├── logs/
└── AI/
``` -->

---

## AI Development Workflow

Before implementing any task:

1.  Read the required AI documentation.
2.  Search existing Page Objects.
3.  Search existing helper methods.
4.  Search existing fixtures.
5.  Search existing utilities.
6.  Search existing tests.
7.  Reuse existing code before creating new code.

### Never

- Duplicate code.
- Hardcode test values.
- Invent project behaviour.
- Modify application source code.

---

## Running Tests

```bash
pytest
```

Run smoke tests:

```bash
pytest -m smoke
```

Run module smoke tests (single CRM modules; require bootstrap deal):

```bash
pytest -m module_smoke
```

Run regression tests:

```bash
pytest -m regression
```

Run Frontend Agent tests:

```bash
pytest -m fe_agent
```

Run Backend Agent tests:

```bash
pytest -m be_agent
```

Run flow orchestrators (serial recommended — shared dev CRM state):

```bash
pytest -m flow_orchestrator
```

Run in parallel:

```bash
pytest -n auto
```

---

## Reports

Generated automatically:

- HTML Report
- Screenshots
- Videos
- Playwright Traces
- Logs

---

<!-- ## Troubleshooting

-   Run tests from the `automation/` directory.
-   Install Playwright browsers using `playwright install`.
-   Verify credentials before execution.
-   Use Playwright traces for debugging failures. -->

---

This README intentionally serves as an entry point.

Detailed technical, architectural, workflow, and automation guidance
lives inside the AI documentation files.

<!-- ## Content

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Reports & Artifacts](#reports--artifacts)
- [Folder Structure](#Folder Structure)
- [Troubleshooting](#troubleshooting) -->

---

<!-- ## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.13 | Language runtime |
| Playwright 1.60 | Browser automation (sync API, Chromium) |
| pytest 9.1 | Test runner |
| pytest-html 4.2 | Self-contained HTML reports |
| pytest-xdist 3.8 | Parallel test execution |
| pytest-metadata | Report metadata |

Design pattern: **Page Object Model** — locators and actions live in `pages/`, test logic lives in `tests/`, and test data is externalized to `test_data/` and `test_page_data/`.

--- -->

## Prerequisites

- **Python 3.13+** installed and on `PATH`
- **pip** (bundled with Python)
- Network access to the target environment (`https://dev.crm.vibecircuit.ca`)
- Valid CRM credentials (configured in `utils/config.py`)

---

## Installation

All commands are run from the `automation/` directory.

### 1. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers

Playwright requires its browser binaries to be downloaded once:

```bash
playwright install
```

---

## Configuration

Runtime settings live in `utils/config.py`:

| Setting                              | Description                                         |
| ------------------------------------ | --------------------------------------------------- |
| `BASE_URL`                           | Target environment URL                              |
| `BROWSER`                            | Browser engine (Chromium)                           |
| `TIMEOUT`                            | Default action/navigation timeout (ms)              |
| `HEADLESS`                           | Run with or without a visible browser window        |
| `SLOW_MO`                            | Delay between actions (useful for debugging)        |
| `VIEWPORT_WIDTH` / `VIEWPORT_HEIGHT` | Browser viewport size                               |
| `USERNAME` / `PASSWORD`              | Admin login credentials                             |
| `FE_USERNAME` / `FE_PASSWORD`        | Frontend Agent credentials (env: `AUTOMATION_FE_*`) |
| `BE_USERNAME` / `BE_PASSWORD`        | Backend Agent credentials (env: `AUTOMATION_BE_*`)  |
| `MORTGAGE_SNAPSHOT_APP_URL`          | MS App base URL (env override)                      |
| `NTP_APP_URL`                        | NTP App base URL (env override)                     |
| `MS_APP_LEAD_SYNC_TIMEOUT_MS`        | Wait for MS/NTP lead sync after CRM save            |

Deal names and agent labels are in `test_page_data/test_entities.py`.

Login data is also available in `test_data/login.json` (valid and invalid users).

> Update `BASE_URL` and credentials before running against a different environment.

---

<!-- ## Running Tests

Run all commands from the `automation/` directory with the virtual environment activated.

### Run the full suite

```bash
pytest
```

### Run a specific test file

```bash
pytest tests/test_create_lead.py
```

### Run a single test by name

```bash
pytest tests/test_login_page.py::test_valid_login_page
```

### Run by marker

Markers are defined in `pytest.ini`:

```bash
pytest -m smoke
pytest -m regression
```

### Run in parallel

Powered by `pytest-xdist`:

```bash
pytest -n auto
```

### Re-run failed tests

A custom `--reruns` option is available (default `2`):

```bash
pytest --reruns 3
```

> The default options in `pytest.ini` (`-v -s --html=... --self-contained-html`) are applied automatically on every run.

--- -->

## Reports & Artifacts

After a run, artifacts are written under `reports/` and `logs/`:

| Artifact            | Location                                                | When generated                          |
| ------------------- | ------------------------------------------------------- | --------------------------------------- |
| HTML report         | `reports/html_reports/{suite}_{date}_run{NN}.html`      | Every run (unique, never overwritten)   |
| Report history      | `reports/html_reports/report_history.md` / `index.html` | Browsable run index                     |
| Failure screenshots | `reports/screenshots/`                                  | On test failure                         |
| Videos              | `reports/videos/`                                       | Recorded per session (saved on failure) |
| Playwright traces   | `reports/traces/`                                       | On test failure                         |
| Execution log       | `logs/test.log`                                         | Every run                               |

### Viewing a Playwright trace

```bash
playwright show-trace reports/traces/<test_name>.zip
```

---

## Folder Structure

```
automation/
├── conftest.py            # Multi-role fixtures (Admin, FE, BE) & failure hooks
├── pytest.ini             # Markers: smoke, module_smoke, regression, flow_orchestrator, fe_agent, be_agent
├── requirements.txt       # Python dependencies
│
├── pages/                 # Page Object Model classes (25 modules)
│   ├── base_page.py
│   ├── login_page.py, create_lead.py, lead_edit_page.py, profile_page.py
│   ├── mortgage_snapshot_page.py, appraisal_order_page.py
│   ├── submitted_page.py, approved_page.py, signed_page.py
│   ├── compliance_page.py, client_care_page.py, marketing_page.py
│   ├── nova_worksheet_page.py, signed_marketing_page.py
│   ├── mortgage_snapshot_app/ (login, leads, presentation)
│   ├── ntp_app/ (login, leads, presentation)
│   └── add_coBorrower_page.py, note_page.py, …
│
├── tests/                 # 65 collected tests
│   ├── test_login_page.py, test_create_lead.py, …
│   ├── test_fe_agent_rbac.py, test_be_agent_rbac.py
│   ├── test_fe_agent_flows.py, test_be_agent_flows.py
│   ├── test_fe_agent_regression.py, test_be_agent_regression.py
│   ├── test_be_*.py (Backend stage smokes)
│   ├── test_mortgage_snapshot_app_display.py, test_ntp_app_display.py, test_ms_app_rbac.py
│   ├── test_admin_backend_flows.py, test_full_sales_frontend_flow.py
│   └── be_stage_test_helpers.py (helper module, not collected)
│
├── test_data/             # JSON test data (login.json)
├── test_page_data/        # Python data + workflow_expectations.py, test_entities.py
│
├── utils/                 # Shared helpers
│   ├── config.py, logger.py, toast.py, validations.py
│   ├── entity_navigation.py, lead_assignment.py
│   ├── workflow_verification.py
│   ├── sales_flow_helpers.py, sales_flow_orchestration.py
│   ├── sales_flow_regression_helpers.py, wait_helpers.py
│   ├── lead_context.py, stage_transition_verification.py
│   ├── mortgage_snapshot_app_helpers.py, ntp_app_helpers.py
│   └── reporting.py, flow_step_reporting.py, html_report_history.py, …
│
├── reports/               # HTML reports, screenshots, videos, traces
├── logs/                  # test.log
└── AI/                    # Documentation (this folder)
```

### Key Fixtures (`conftest.py`)

| Fixture                             | Scope    | Purpose                                        |
| ----------------------------------- | -------- | ---------------------------------------------- |
| `playwright_instance`               | session  | Starts Playwright                              |
| `browser`                           | session  | Launches Chromium                              |
| `browser_context`                   | function | Context with video + tracing (unauthenticated) |
| `page`                              | function | Fresh unauthenticated page                     |
| `admin_auth_state` / `auth_state`   | session  | Admin login cached once                        |
| `fe_agent_auth_state`               | session  | Frontend Agent login cached once               |
| `be_agent_auth_state`               | session  | Backend Agent login cached once                |
| `authenticated_page` / `admin_page` | function | Admin-authenticated page                       |
| `fe_agent_page`                     | function | Frontend Agent page                            |
| `be_agent_page`                     | function | Backend Agent page                             |
| `lead_context`                      | session  | Bootstrap lead/deal names for the current run  |
| `active_lead_name` / `active_deal_name` | function | Names from `lead_context` after bootstrap |

On failure, role fixtures capture screenshots and Playwright traces automatically.

---

### 1. Cursor Rules

Read `.cursor/rules/` — project-level AI behaviour rules.

### 3. Framework Files

Understand before coding:

- `conftest.py` — fixtures and failure hooks
- `utils/config.py` — Config class (BASE_URL, credentials, timeouts)
- `utils/logger.py` — logger setup
- `pages/base_page.py` — shared Playwright action wrappers

### 4. Existing Pages

Before creating any page method:

- Search for an existing page.
- Search for similar methods.
- Search for reusable actions.

Never duplicate.

### 5. Existing Tests

Before writing tests:

- Understand naming style.
- Understand assertion patterns.
- Follow the existing test flow.

### 6. Utilities

Search existing helpers before creating:

- `utils/entity_navigation.py` → bucket navigation (Lead Bucket, My Leads, Sales Frontend, Sales Backend)
- `utils/lead_assignment.py` → `LeadAssignmentHelper`
- `utils/workflow_verification.py` → `WorkflowVerification`
- `test_page_data/workflow_expectations.py` → CRM-derived constants
- `utils/sales_flow_helpers.py` / `sales_flow_orchestration.py` → stage smokes and orchestrators
- `utils/wait_helpers.py` → Google Places autocomplete, Canadian postal-code recovery
- `utils/toast.py` → `Toast`
- `utils/validations.py` → `Validations`
- `utils/reporting.py` → failure artifacts and HTML extras

### 7. Test Data

Search before creating:

- `test_data/login.json`
- `test_page_data/random_gen_data.py` → `RandomGenerator`
- Feature-specific data modules in `test_page_data/`

Never hardcode. Never invent project behavior.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'faker'`

Some data modules (e.g. `test_page_data/random_gen_data.py`) use the `faker` library, which is not pinned in `requirements.txt`. Install it:

```bash
pip install faker
```

### `Executable doesn't exist` / browser not found

Playwright browser binaries were not installed. Run:

```bash
playwright install
```

### Import errors for `pages`, `utils`, or `test_data`

Tests rely on relative paths and imports rooted at the `automation/` directory. Always run `pytest` **from inside `automation/`**, not from the repository root.

### `FileNotFoundError: test_data/login.json`

The working directory is wrong. Run tests from the `automation/` folder so relative data paths resolve.

### Tests time out or elements not found

- Confirm `BASE_URL` is reachable and the environment is up.
- Increase `TIMEOUT` in `utils/config.py`.
- Set `HEADLESS = False` and increase `SLOW_MO` to watch the run and debug locally.

### Authentication failures

Verify `USERNAME` / `PASSWORD` in `utils/config.py` and the entries in `test_data/login.json` are valid for the target environment.

### Reports or screenshots not generated

Ensure the `reports/` and `logs/` directories exist (they are created on demand) and that you have write permission in the `automation/` directory.

### Viewing detailed failures

Open the latest report from `reports/html_reports/` (or browse `report_history.md`), review `reports/screenshots/`, or replay a trace:

```bash
playwright show-trace reports/traces/<test_name>.zip
```
