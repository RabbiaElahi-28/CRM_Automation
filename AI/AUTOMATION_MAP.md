# AUTOMATION_MAP.md

Bridge between application code and the Playwright automation framework.

For architecture, routing, and component details see `PROJECT_STRUCTURE.md`.
For framework standards see `STANDARDS.md`.
For automation framework internals see `PROJECT_CONTEXT.md`.

This document focuses exclusively on: where to find source code for each module, which automation artifacts already exist, and how to build or extend tests.

---

## Stage Gating — Core Business Rule

**Verified from:** `apps/nextjs/src/lib/utils/stage-utils.ts`, `SaleLeadInfo.tsx`

The lead's `nextStatus` field controls which tabs are visible in the lead detail page. The mapping is:

| `nextStatus` value | Last visible tab    | Meaning                                                      |
| ------------------ | ------------------- | ------------------------------------------------------------ |
| 13                 | `mortgage-snapshot` | Lead in Application Received — only Snapshot accessible next |
| 57                 | `nurture`           | Lead moved to Nurture                                        |
| 14                 | `appraisal-order`   | Snapshot complete — Appraisal next                           |
| 10                 | `submitted`         | Appraisal complete — Submitted next                          |
| 7                  | `approved`          | Legacy approved mapping                                      |
| 11                 | `signed`            | Approved complete — Signed next                              |
| 16                 | `signed`            | Not Signed (same tab)                                        |
| 29                 | `profile`           | Backend: Application Received                                |
| 30                 | `mortgage-snapshot` | Backend: Snapshot next                                       |
| 31                 | `appraisal-order`   | Backend: Appraisal next                                      |
| 32                 | `submitted`         | Backend: Submitted next                                      |
| 49                 | `approved`          | Backend: Approved next                                       |
| 34                 | `signed`            | Backend: Signed next                                         |
| 35                 | `signed`            | Backend: Not Signed                                          |

`Nurture` is always visible regardless of `nextStatus` (defined in `ALWAYS_VISIBLE_STEP_VALUES`).

**Stage transition mechanism:** `StageUpdateDialog` (`features/lead-detail/components/StageUpdateDialog.tsx`) — calls `orpc.lead.updateLeads` with `{ id: leadId, generalInfo: { status: nextStageStatus } }`. On success, URL navigates to `?tab=<nextStageName>`.

**Automation implication:** To test a specific stage tab, the test lead must have the correct `nextStatus`. Use a known lead or set up test data accordingly. Navigate directly via URL `?tab=<value>` to reach a specific tab reliably.

---

## Stage Status ID Reference

**Sales Frontend** (`sales-stage-status.ts`):

| Stage                | Status ID |
| -------------------- | --------- |
| Application Received | 8         |
| Mortgage Snapshot    | 13        |
| Nurture              | 57        |
| Appraisal Order      | 14        |
| Submitted            | 10        |
| Approved             | 48        |
| Signed               | 11        |
| Not Signed           | 16        |

**Sales Backend** (`sales-stage-status.ts`):

| Stage                | Status ID |
| -------------------- | --------- |
| Application Received | 29        |
| Mortgage Snapshot    | 30        |
| Appraisal Ordered    | 31        |
| Submitted            | 32        |
| Approved             | 49        |
| Signed               | 34        |
| Not Signed           | 35        |

---

## 1. Authentication

**Application Route:** `/login`, `/otp`, `/forget-password`, `/reset-password`

**Frontend Page:** `apps/nextjs/src/app/(auth)/login/page.tsx`

**Main Component:** `features/auth/components/LoginForm.tsx`

**Business Logic:**

- Form validation: Zod schema (`loginSchema`) — email required + valid format, password required
- Submit: calls `loginAction` (Server Action, `lib/auth/actions.ts`)
- Auth service: `POST {AUTH_URL}/api/auth/sign-in/email`
- On success: sets `auth_token` cookie (httpOnly: false, 1 day)
- On 2FA required: redirects to `/otp`, sets `better-auth.two_factor` cookie
- Error display: `<div role="alert">` containing the error message text

**API:** `lib/auth/actions.ts` — `loginAction`, `verifyOtpAction`, `logoutAction`

**Backend:** `apps/auth-service/src/auth.ts`

**Automation Page Object:** `pages/login_page.py` — `LoginPage`

**Existing Methods:**

- `open()` — navigates to `Config.BASE_URL + "/login"`
- `valid_login(username, password)` — fills email + password, clicks show-password
- `click_signup_btn()` — clicks Sign in button

**Automation Tests:** `tests/test_login_page.py` — `test_valid_login_page` (parametrized valid + invalid from `test_data/login.json`)

**Related Helpers:**

- `auth_state` fixture (conftest) — session-scoped login + storage state capture
- `authenticated_page` fixture (conftest) — reuses `auth_state` to avoid re-login

**Automation Notes:**

- Do not re-implement login in any test. Always use `auth_state` / `authenticated_page` fixtures.
- Error message locator: `page.get_by_role("alert")` or `page.get_by_text("Invalid email or password")`
- After successful login, URL must not contain `/login`: `page.wait_for_url(lambda url: "/login" not in url)`
- Password field has a show/hide toggle button — `LoginPage.valid_login` already handles this.
- Missing test: OTP verification flow (`/otp`). Requires `OtpForm` component interaction.

---

## 2. Lead Bucket

**Application Route:** `/lead-bucket`, `/lead-bucket/:id`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/lead-bucket/page.tsx`

**Main Component:** `features/lead-bucket/components/` — list and kanban views

**Business Logic:**

- Kanban + List toggle (`?view=kanban|list`)
- Stage statuses: New(2), Remark Lead(22), ... Sent Application(47) — see `LEAD_BUCKET_STAGES` in `types/lead.ts`
- Action buttons visible in lead header: `SentApplicationButton`, `MoveToSalesButton`, `NotProceedingButton`

**API:** `orpc.lead.getFilteredLeads` with `statusType = "lead"`

**Backend:** `apps/honojs/src/router/leads/`

**Automation Page Object:** No dedicated page object. Navigation via `utils/entity_navigation.py` — `open_bucket_record(page, LEAD_BUCKET, lead_name)`.

**Automation Tests:** Used by orchestrators and `lead_assignment.py` (Admin assigns FE/BE from Lead Bucket).

**Related Helpers:** `admin_page`, `LeadAssignmentHelper`, `entity_navigation`

**Automation Notes:**

- Leads are cards in Kanban or rows in List view.
- Lead card link: `get_by_role("link", name="<lead_name>")`
- View toggle: `get_by_role("button", name="Kanban")` / `get_by_role("button", name="List")`
- Search: `get_by_placeholder("Search leads by name, email, phone...")`

---

## 3. My Leads

**Application Route:** `/my-leads`, `/my-leads/:id`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/my-leads/page.tsx`

**Main Component:** `features/my-leads/components/`

**Business Logic:**

- Stages: New Leads(2), Expiring Lead(3), Sent Application(47), Unconverted apps(55), Unconverted DLOs(58)
- Action buttons: `SentApplicationButton`, `MoveToSalesButton`, `NotProceedingButton`
- Tab steps: `LEAD_BUCKET_STEPS` (Profile, Co-borrowers, Notes, Documents, Marketing)

**API:** `orpc.lead.getFilteredLeads`

**Backend:** `apps/honojs/src/router/leads/`

**Automation Page Object:** No dedicated page object. Navigation via `utils/entity_navigation.py` — `open_bucket_record(page, MY_LEADS_BUCKET, lead_name)`.

**Automation Tests:** Used by Sales Frontend smokes and orchestrators.

**Related Helpers:** `entity_navigation`, `test_page_data/test_entities.py` (`MY_LEADS_DEAL_NAME`)

**Automation Notes:**

- Navigate to a lead: `get_by_role("link", name="My Leads")` then `get_by_role("link", name="<lead_name>")`
- `LeadInfoHeader` shows "Move to Sales" button — clicking triggers `orpc.lead.updateLeads`

---

## 4. Create Lead

**Application Route:** `/create-lead`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/create-lead/page.tsx`

**Main Component:** `features/lead-create/components/CreateLeadForm.tsx`

**Business Logic:** Full lead creation form — personal info, DOB picker (calendar widget), credit, property, employment, priorities.

**API:** `orpc.lead.createLead`

**Backend:** `apps/honojs/src/router/leads/leads.router.ts`

**Automation Page Object:** `pages/create_lead.py` — `CreateLeadPage`

**Existing Methods:**

- `open()`, `fill_form(lead_data)`, `refill_form(lead_data)`
- Personal: `enter_lead_first_name()`, `enter_lead_last_name()`, `enter_lead_email()`, `enter_lead_phone()`, `select_lead_gender()`, `select_lead_marital_status()`, `enter_lead_address()`, `enter_lead_address_with_autocomplete()`, `enter_lead_postal_code()`, `select_lead_birthday()`, `select_lead_maturity_date()`
- Mortgage/property: `select_lead_product_type()`, `enter_lead_loan_amount()`, `enter_lead_credit_score()`, `enter_lead_mortgage_rate()`, `select_lead_property_type()`, `enter_lead_property_address()`, `enter_lead_property_address_with_autocomplete()`, `enter_lead_property_value()`, `enter_lead_monthly_payment()`, `enter_lead_balance_owing()`, `enter_lead_working_situation()`, `enter_lead_working_location()`, `enter_lead_income()`, `enter_lead_employer_name()`, `select_lead_whats_important()`
- Submit: `submit_lead()`, `submit_lead_and_wait_success()`
- Validation helpers: `set_field()`, `clear_field()`, `clear_all_fields()`, `restore_baseline_for_invalid_tests()`

**Automation Tests:** `tests/test_create_lead.py` — `test_valid_create_lead` (parametrized via `get_lead_cases()`)

**Related Helpers:**

- `utils/test_data_factory.py` — `valid_lead_data()`, `get_lead_cases()`, `get_last_valid_lead_data()`
- `utils/wait_helpers.py` — `select_google_places_suggestion()`, `ensure_complete_postal_code()`
- `utils/negative_test_helpers.py` — `verify_required_fields()`, `verify_invalid_fields()`
- `test_page_data/validation_cases.py` — `CREATE_LEAD_EMPTY`, `CREATE_LEAD_INVALID`
- `utils/toast.py` — `Toast.assert_message()`
- `utils/validations.py` — `Validations.assert_field_error()`
- `authenticated_page` fixture

**Automation Notes:**

- DOB picker is a calendar widget — `select_lead_birthday()` uses ordinal day (e.g. "4th") via `_ordinal_day()` helper.
- Address autocomplete uses `select_google_places_suggestion()`; if Google Places leaves an incomplete Canadian postal code, `ensure_complete_postal_code()` re-enters the expected value.
- Toast notification: `[data-sonner-toast]` (from `Toast` class).
- Field errors: `div.text-red-500` containing the error text.

---

## 5. Edit Lead

**Application Route:** `/edit-lead/:id?tab=client-info` or `?tab=mortgage-info`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/edit-lead/[id]/page.tsx`

**Main Component:** `features/lead-edit/components/EditLeadForm.tsx`, `EditLeadContent.tsx`

**Business Logic:** Two edit contexts linked from Profile tab: client-info (personal) and mortgage-info.

**API:** `orpc.lead.updateLead`

**Backend:** `apps/honojs/src/router/leads/leads.router.ts`

**Automation Page Object:** `pages/lead_edit_page.py` — `LeadEditPage`

**Existing Methods:**

- `open()`, `open_lead_for_edit(lead_name, bucket=...)`
- `update_contact_info(email, phone)`, `select_gender(gender)`, `select_marital_status(status)`
- `update_address(partial, expected_postal_code=...)` — Google Places autocomplete + postal recovery
- `select_dob(month, year, day)`, `save_client_info()` (alias: `sava_client_info()`)
- `open_mortgage_tab()`, `select_mortgage_type(mtype)`, `fill_mortgage_details(...)`
- `fill_property_info(...)`, `fill_employment(...)`, `save_changes()`

**Automation Tests:** `tests/test_lead_edit.py` — `test_edit_lead`

**Related Helpers:**

- `test_page_data/lead_edit_data.py` — `lead_edit_data` dict
- `authenticated_page` fixture

**Automation Notes:**

- Gender/marital status dropdowns use label-anchored combobox resolution inside the Client Information tabpanel.
- Address fields use `select_google_places_suggestion()`; incomplete postal codes are corrected via `ensure_complete_postal_code()`.
- Save button uses `.last` to handle multiple Save buttons on page

---

## 6. Sales Frontend (My Deals)

**Application Route:** `/sales`, `/sales/:id`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/sales/[id]/page.tsx`

**Main Component:** `features/sales/components/SaleLeadInfo.tsx`

**Business Logic:**

- Tabs driven by `SALES_FRONTEND_STEPS` (see `types/lead.ts`)
- Tab visibility controlled by `nextStatus` field via `NEXT_STATUS_TO_LAST_STEP` (`lib/utils/stage-utils.ts`)
- Stage status IDs: Application Received(8), Snapshot(13), Nurture(57), Appraisal(14), Submitted(10), Approved(48), Signed(11), Not Signed(16)
- `StageUpdateDialog` advances the lead to next stage via `orpc.lead.updateLeads`

**Stage Visibility Rules (verified from source):**

```
Lead arrives at /sales with nextStatus = 13 (Application Received)
  → Only visible tabs: profile, co-borrowers, notes, documents, marketing, lead-history, mortgage-snapshot, nurture
  → appraisal-order, submitted, approved, signed are HIDDEN

Agent completes Mortgage Snapshot → nextStatus becomes 14
  → appraisal-order becomes visible

Agent completes Appraisal Order → nextStatus becomes 10
  → submitted becomes visible

Agent marks one Submitted option as approved → nextStatus becomes 7 or 48
  → approved becomes visible

Agent completes Approved → nextStatus becomes 11
  → signed becomes visible
```

**API:** `orpc.lead.getLeadDetail`, `orpc.lead.getFilteredLeads`, `orpc.lead.updateLeads`

**Backend:** `apps/honojs/src/router/leads/`, each stage has its own router

**Automation Page Object:** No dedicated Sales page object. Shared stage page objects (`MortgageSnapshotPage`, `AppraisalOrderPage`, `SubmittedPage`, `ApprovedPage`, `SignedPage`) accept optional `bucket=` (default `MY_DEALS_BUCKET`).

**Automation Tests:**

- Stage smokes: `test_mortgage_snapshot.py`, `test_appraisal_order.py`, `test_submitted.py`, `test_approved.py`, `test_signed.py`
- RBAC: `test_fe_agent_rbac.py` (`@fe_agent`)
- Orchestrators: `test_move_to_sales_flow.py`, `test_full_sales_frontend_flow.py` (`@flow_orchestrator`)

**Related Helpers:** `WorkflowVerification`, `workflow_expectations`, `sales_flow_helpers.py`, `sales_flow_orchestration.py`, `admin_page` / `fe_agent_page`

**Automation Notes:**

- Tab `data-state="active"` attribute identifies the selected tab.
- Fastest navigation: `authenticated_page.goto(BASE_URL + f"/sales/{lead_id}?tab={tab_value}")`
- Stage transition dialog: `get_by_role("alertdialog")` → `get_by_role("button", name="Move to Next Stage")`
- Toast on stage move: `get_by_text("Lead moved to <StageName> successfully")`

---

## 7. Sales Backend

**Application Route:** `/sales-backend`, `/sales-backend/:id`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/sales-backend/[id]/page.tsx`

**Main Component:** `features/sales-backend/components/SaleBackendLeadInfo.tsx`

**Business Logic:**

- Same tab system as Sales Frontend, uses `SALES_BACKEND_STEPS`
- Additional early stages before Application Received: Expired Renewal Lead(28), 6 Month Renewal(56), 9 Month Maturity(54)
- Different status IDs (see Stage Status ID Reference above)
- `getSalesStageStatusMap(pathname)` returns `SALES_BACKEND_STAGE_STATUS` when path includes `/sales-backend`
- Compliance detail page also uses `SALES_BACKEND_STAGE_STATUS` (same `getSalesStageStatusMap` check)
- No `Nurture` tab in `SALES_BACKEND_STEPS`

**API:** Same oRPC namespaces as Sales Frontend

**Backend:** Same backend routers, status IDs differ

**Automation Page Object:** Shared stage page objects with `bucket=SALES_BACKEND_BUCKET`.

**Automation Tests:**

- RBAC: `test_be_agent_rbac.py` (`@be_agent`)
- Stage smokes: `test_be_mortgage_snapshot.py`, `test_be_appraisal_order.py`, `test_be_submitted.py`, `test_be_approved.py`, `test_be_signed.py`
- Full pipeline: `test_admin_backend_flows.py`, `test_be_agent_flows.py` (`@be_agent`, `@flow_orchestrator`)

**Related Helpers:** `setup_be_assigned_lead()`, `run_backend_*_smoke()`, `run_backend_full_flow()`, `be_agent_page`, `LeadAssignmentHelper.assign_be_backend()`

**Differences from Sales Frontend:**

- Status IDs are different (30, 31, 32, 49, 34, 35 instead of 13, 14, 10, 48, 11, 16)
- No Nurture tab
- Has Mortgage History tab instead
- Has additional pre-pipeline stages (Renewal, Maturity)

**Automation Notes:**

- Reuse the same tab interaction patterns as Sales Frontend
- `getSalesStageStatusMap` automatically selects the correct status map based on URL

---

## 8. Compliance

**Application Route:** `/compliance`, `/compliance/:id`

**Frontend Page:** `apps/nextjs/src/app/(dashboard)/compliance/[id]/page.tsx`

**Main Component:**

- List: `features/compliance/components/UnifiedView.tsx` — `ComplianceUnifiedView`
- Detail: `features/compliance/components/ComplianceLeadInfo.tsx`
- Compliance form: `features/lead-detail/components/compliance/Compliance.tsx`

**Business Logic:**

- Leads enter Compliance after completing Signed in Sales pipeline
- `statusType = "closed"` for all API queries
- Lead detail uses `COMPLIANCE_STEPS` + extra tab `signed-closed`
- `signed-closed` tab renders the `Compliance` component
- Compliance component has two internal tabs:
  - **Compliance Form**: `ClosingComplianceSection` + `ClientCareChecksSection`
  - **Signed Form**: `SignedFormReadOnlyView` (read-only view of signed data)
- `COMPLIANCE_NEXT_STATUS_TO_LAST_STEP` in `ComplianceLeadInfo.tsx` controls tab visibility (uses Sales Backend status IDs)
- Uses `SALES_BACKEND_STAGE_STATUS` (because `getSalesStageStatusMap` matches `/compliance` to backend map)

**API:** `orpc.lead.getFilteredLeads` (statusType: "closed"), `orpc.lead.getLeadDetail`, `orpc.compliance.*`

**Backend:** `apps/honojs/src/router/compliance/`

**Automation Page Object:** `pages/compliance_page.py` — `CompliancePage`

**Automation Tests:** `tests/test_compliance.py` — `@smoke`; included in compliance-to-client-care orchestrators

**Related Helpers:** `authenticated_page` fixture

**Tab locators (Compliance detail):**

- `get_by_role("tab", name="Signed Closed")` — navigates to compliance form
- `get_by_role("tab", name="Compliance Form")` — internal sub-tab
- `get_by_role("tab", name="Signed Form")` — internal sub-tab

**Automation Notes:**

- `Compliance` component is reached at tab value `signed-closed`, not `compliance`
- URL pattern: `/compliance/<id>?tab=signed-closed`
- `ClosingComplianceSection` and `ClientCareChecksSection` are collapsible — use `CollapsibleSection` wrapper

---

## 9. Profile Tab

**Application Route:** Any lead detail page — `?tab=profile` (default)

**Main Component:** `features/lead-detail/components/ProfileTab.tsx`

**Child Components:**

- `PersonalInformationSubTab` — sub-tab "Personal Information"
- `GeneralInformationSubTab` — sub-tab "General Information"
- `MortgageInformationSubTab` — sub-tab "Mortgage Information"
- `CommunicationCard` — shown on right side (email, SMS compose)

**Edit Links (from Profile tab):**

- Personal Information → Edit button → `/edit-lead/:id?tab=client-info`
- Mortgage Information → Edit button → `/edit-lead/:id?tab=mortgage-info`

**Business Logic:**

- Edit buttons only visible if `hasFullAccess` is true (lead assigned to logged-in user or admin)
- Sub-tabs are internal to `ProfileTab`, not URL-driven

**API:** `orpc.lead.getLeadDetail`

**Automation Page Object:** `pages/lead_edit_page.py` (edit flow); `pages/profile_page.py` — `ProfilePage` for read-only Profile tab assertions.

**Sub-tab locators:**

- `get_by_role("tab", name="Personal Information")`
- `get_by_role("tab", name="General Information")`
- `get_by_role("tab", name="Mortgage Information")`
- Edit button: `get_by_role("link", name="Edit")` (within profile card)

**Automation Notes:**

- Profile is the default tab — no `?tab=` needed in URL
- CommunicationCard renders email/SMS compose area alongside profile data

---

## 10. Notes

**Application Route:** Lead detail — `?tab=notes`

**Main Component:** `features/lead-detail/components/notes/NotesTab.tsx`

**Child Components:**

- `AddNoteForm` — form to add a note
- `EditNoteForm` — inline edit
- `DeleteNoteDialog` — confirm delete
- `NotesList` — list of notes
- `NoteItem` — individual note card

**Note Properties:** Text content (rich text via Tiptap `.tiptap` editor), heading, status

**API:** `orpc.notes.*` (CRUD)

**Backend:** `apps/honojs/src/router/lead-notes/`

**Automation Page Object:** `pages/note_page.py` — `NotesPage`

**Existing Methods:**

- `open()`, `open_lead(lead_name)`, `open_notes_tab()`
- `click_add_note()`, `enter_note(note_text)`, `apply_formatting()`
- `select_heading(heading)`, `select_note_status(status)`, `save_note()`
- `edit_note(note_text, updated_note)`, `delete_note(note_text)`
- `_open_note_menu(note_text)` — private helper (opens kebab menu on note card)

**Automation Tests:** `tests/test_note.py` — `test_add_edit_delete_note`

**Related Helpers:**

- `test_page_data/note_data.py` — `notes_test_data`
- `authenticated_page` fixture

**Key Locators:**

- Rich text editor: `page.locator(".tiptap")`
- Note card: `page.locator("div.p-6").filter(has_text=<note_text>).first`
- Kebab menu: `locator("button[aria-haspopup='menu']")`
- Edit menuitem: `get_by_role("menuitem", name="Edit")`
- Delete menuitem: `get_by_role("menuitem", name="Delete")`
- Save Notes: `get_by_role("button", name="Save Notes")`
- Update: `get_by_role("button", name="Update")`

**Automation Notes:**

- Heading dropdown is inside the "Notes" tabpanel: `get_by_role("tabpanel", name="Notes").get_by_role("combobox")`
- Note status is selected by text click: `page.get_by_text(status).click()`
- After delete, page is reloaded (`page.reload()`) — wait for networkidle

---

## 11. Documents

**Application Route:** Lead detail — `?tab=documents`

**Main Component:** `features/lead-detail/components/Attachments/Attachments.tsx` — `AttachmentsSection` (lazy-loaded, client-only)

**Child Components:**

- `DocumentsTab` — uploaded documents list
- `RequestedDocumentsTab` — outstanding document requests
- `RequestDocumentsDialog` — dialog to request docs
- `DirectUploadDialog` — direct file upload
- `UploadDocumentsDialog`, `UploadPortalDialog`
- `ViewDocumentDialog` — document viewer
- `DocumentSelectionToolbar`

**Business Logic:**

- Component loaded only on client side (no SSR) due to react-pdf dependency
- Loading state: `"Loading documents…"` text

**API:** `orpc.docRequests.*`, `orpc.docUpload.*`

**Backend:** `apps/honojs/src/router/doc-requests/`, `apps/honojs/src/router/doc-upload/`

**Automation Page Object:** Not yet created. Recommended: `pages/documents_page.py`

**Automation Tests:** None yet.

**Automation Notes:**

- Wait for client load: `page.wait_for_load_state("networkidle")` after tab click
- Request Documents button: `get_by_role("button", name="Request Documents")`
- Upload button: `get_by_role("button", name="Upload")`
- Files upload via dialog: use `page.set_input_files(locator, path)` for file input elements

---

## 12. Activity Logs

**Application Route:** Lead detail — `?tab=activity-logs` (admin only)

**Main Component:** `features/lead-detail/components/ActivityTab.tsx`

**Business Logic:**

- Only visible to admin users (checked in `SaleLeadInfo`/`ComplianceLeadInfo` via `isAdmin`)
- Filterable activity timeline

**API:** `orpc.activityLogs.*`

**Backend:** `apps/honojs/src/router/activity-logs/`

**Automation Page Object:** Not yet created.

**Automation Notes:**

- Tab only appears for admin role — test credentials must be admin
- Tab locator: `get_by_role("tab", name="Activity logs")`

---

## 13. Mortgage Snapshot

**Application Route:** Lead detail — `?tab=mortgage-snapshot`

**Main Component:** `features/lead-detail/components/mortgageSnapshot/MortgageSnapshot.tsx`

**Child Components:**

- `CreditProfileSection` — primary credit
- `CoApplicantCreditProfileSection` — co-applicant credit
- `MortgageOptionCard` — options 1-N
- `MortgageSnapshotSections` — sections layout
- `MortgageSnapshotMeetingScheduledSection` — meeting tab section
- `NumberFieldWithHelper`, `TextAreaWithCounter`, `SectionCard`

**Business Logic:**

- Snapshot form saves against `orpc.mortgageSnapshot.*`
- Toast on save: `"Mortgage snapshot created successfully"` or `"Mortgage snapshot updated successfully"`
- After save, active tab switches to `"Mortgage Snapshot Meeting"` tab
- Meeting reminder uses `orpc.mortgageSnapshotMeetings.*`

**API:** `orpc.mortgageSnapshot.*`, `orpc.mortgageSnapshotMeetings.*`

**Backend:**

- `apps/honojs/src/router/mortgage-snapshot/`
- `apps/honojs/src/router/mortgage-snapshot-meetings/`

**Automation Page Object:** `pages/mortgage_snapshot_page.py` — `MortgageSnapshotPage` (extends `BasePage`)

**Existing Locators (all in `__init__`):**

- Navigation: `my_deals`, `snapshot_tab`, `snapshot_form_tab`
- Video: `vfli_number` (#vfliNo), `introduction_script`
- Client needs: `first_need` (#firstNeed), `ok_got_it`, `second_need` (#secondNeed), `lets_get_to_work`
- Primary credit: `credit_score` (#creditScore), `tds_score`, `credit_utilization`, checkboxes for 7 warning types
- Co-applicant: `co_credit_score`, `co_tds_score`, `co_credit_utilization`
- Cost of doing nothing: `current_balance`, `current_rate`, `years_to_pay`, `total_interest`, `total_cost`, `monthly_payment`
- Option 4/5: dropdowns, loan, payment, savings, 3 points each
- Home appraised: `minimum_value`, `maximum_value`, `value_used`, `less_all_mortgages`, `ltv`, `plan_type`
- Final prompt: `benefit_one`, `benefit_two`, `benefit_three`, `final_prompt`
- Buttons: `save_button`
- Toasts: `created_success_toast`, `updated_success_toast`, `meeting_*_toast`
- Meeting: `set_meeting_reminder_btn`, `meeting_room_input`, `recipient_input`, `start_date_input`, `end_date_input`, `description_input`, `meeting_link_input`, `email_notify_checkbox`

**Existing Methods:**

- `open()`, `open_snapshot(deal_name)` — navigates to My Deals → deal → Snapshot tab → Snapshot Form tab
- `fill_video_section(data)`, `fill_client_needs(data)`, `fill_primary_credit(data)`
- `fill_co_applicant_credit(data)`, `fill_cost_of_doing_nothing(data)`
- `fill_option_four(data)`, `fill_option_five(data)`, `fill_home_appraised(data)`, `fill_final_prompt(data)`
- `complete_snapshot(deal_name, data)` — full flow: navigate + fill all sections + save
- `save()`, `verify_saved()` — tries `created_success_toast`, falls back to `updated_success_toast`
- Meeting: `fill_meeting_details(data)`, `create_meeting(data)`, `verify_meeting_saved()`
- Meeting CRUD: `meeting_menu_actions(data)`, `verify_meeting_details(data)`, `verify_meeting_updated()`, `verify_meeting_deleted()`
- `meeting_search_export(data)`, `delete_meeting()`

**Automation Tests:** `tests/test_mortgage_snapshot.py` — `test_create_mortgage_snapshot`

**Related Helpers:**

- `test_page_data/mortgage_snapshot_data.py` — `MortgageSnapshotData` dataclass (uses `RandomGenerator`)
- `test_page_data/random_gen_data.py` — `RandomGenerator`
- `authenticated_page` fixture

**Critical Automation Note — Toast Timing:**
`verify_saved()` must be called **immediately** after `complete_snapshot()` / `save()`, before any other assertions. Toast is ephemeral — waiting for other elements first causes timeout. (Already fixed in current test.)

**Mortgage Snapshot External Application (MS App):**

Automation opens the external MS App from CRM after Mortgage Snapshot save (or via native login for RBAC). Implemented in:

- Page objects: `pages/mortgage_snapshot_app/` — `MortgageSnapshotAppLoginPage`, `MortgageSnapshotAppLeadsPage`, `MortgageSnapshotAppPresentationPage`
- Helpers: `utils/mortgage_snapshot_app_helpers.py`, `utils/ms_app_auth.py`, `utils/ms_app_rbac.py`, `utils/mortgage_snapshot_display.py`
- Config: `Config.MORTGAGE_SNAPSHOT_APP_URL`, `Config.MS_APP_LEAD_SYNC_TIMEOUT_MS`
- Tests: `tests/test_mortgage_snapshot_app_display.py` (`@smoke`), `tests/test_ms_app_rbac.py` (`@smoke`)

Typical cycle: CRM save → open MS App tab → search lead → verify presentation → refresh/reopen → logout → RBAC denied check for non-assigned role → close tab.

---

## 14. DLO (Debt & Loan Optimization)

**Application Route:** Lead detail — `?tab=dlo` (only visible if `leadDetail.dlo.vfliNo` exists)

**Main Component:** `features/lead-detail/components/dlo/Dlo.tsx`

**Child Components:**

- `DLOForm` — main DLO form (two internal tabs: "DLO Form", "DLO Meeting")
- `DLOMeetingScheduledSection` — meeting section within DLO

**Business Logic:**

- DLO tab only renders if `leadDetail.dlo.vfliNo` is a non-empty value
- DLO completion triggers `StageUpdateDialog` with `showDloCompletionChecks = true`
- DLO completion checks: `clientReviewedDlo` checkbox + `savedVideo` checkbox — both must be checked before moving
- DLO stage stores data in localStorage key `dlo-draft-${leadId}` (cleared on successful move)
- After DLO stage transition, lead status updates via `orpc.lead.updateLeads`

**API:** `orpc.dlo.*`

**Backend:** `apps/honojs/src/router/dlo-headlines/`, `apps/honojs/src/router/dlo-meetings/`

**Automation Page Object:** Not yet created. Recommended: `pages/dlo_page.py`

**Automation Tests:** None yet.

**DLO completion dialog locators:**

- Dialog: `get_by_role("alertdialog")`
- Client reviewed checkbox: `get_by_role("checkbox", name="Client reviewed DLO")`
  - ID: `#dlo-client-reviewed-checkbox`
- Video saved checkbox: `get_by_role("checkbox", name="Video saved")`
  - ID: `#dlo-video-saved-checkbox`
- Confirm: `get_by_role("button", name="Move to Next Stage")`

**Automation Notes:**

- Test lead must have `dlo.vfliNo` populated to see DLO tab
- DLO tab has two internal sub-tabs: `get_by_role("tab", name="DLO Form")`, `get_by_role("tab", name="DLO Meeting")`

---

## 15. Nurture

**Application Route:** Lead detail — `?tab=nurture` (always visible in SALES_FRONTEND_STEPS)

**Main Component:** `features/lead-detail/components/Nurture.tsx`

**Business Logic (verified from source):**

- Form fields: `timeToMove` (1-5 days dropdown) + `reason` (textarea, max 275 chars, required)
- Time options: 1 day, 2 days, 3 days, 4 days, 5 days
- Submit: calls `orpc.lead.updateNurture` with `{ leadId, nurtureDays, nurtureReason }`
- If lead is NOT already in Nurture status (57): `StageUpdateDialog` appears asking to move lead to Nurture
- `StageUpdateDialog` calls `orpc.lead.updateLeads` → sets `generalInfo.status = 57`
- Toast on save: `"Nurture updated successfully"`
- `NURTURE_STAGE_STATUS = 57` (hardcoded in component)

**Background Return Mechanism:**

- The CRM frontend itself does not implement the automatic return from Nurture
- Backend implementation: `apps/honojs/src/lead-assignment-cron/scheduler.ts` is the cron system
- The specific Nurture expiry scheduler has **not been confirmed** from inspected source files
- Do not assume or document the exact mechanism without reading the backend cron

**API:** `orpc.lead.updateNurture`, `orpc.lead.updateLeads`

**Backend:** `apps/honojs/src/router/leads/leads.router.ts`, `apps/honojs/src/lead-assignment-cron/`

**Automation Page Object:** Not yet created. Recommended: methods added to a `SalesPage` or dedicated `pages/nurture_page.py`

**Key Locators:**

- Time to move dropdown: `get_by_label("I Want Time to Move (In Days)")` or combobox within nurture card
- Reason textarea: `get_by_placeholder("Type reason here")`
- Save button: `get_by_role("button", name="Save")`
- Cancel: `get_by_role("button", name="Cancel")`
- Stage update dialog: `get_by_role("alertdialog")` → `get_by_role("button", name="Move to Next Stage")`

**Automation Notes:**

- Nurture tab is always visible — no `nextStatus` gating
- After `updateNurture` succeeds: if not already in Nurture, `StageUpdateDialog` opens automatically
- Toast: `"Nurture updated successfully"` (from sonner)
- Recommended test scenario: fill Nurture form → save → confirm move in dialog → assert toast

---

## 16. Appraisal Order

**Application Route:** Lead detail — `?tab=appraisal-order`

**Main Component:** `features/lead-detail/components/AppraisalOrder/AppraisalOrder.tsx`

**Child Components:** `AppraisalOrderFormFields`, `AppraisalOrderFormFooter`, `useAppraisalOrderForm` (hook)

**API:** `orpc.appraisalOrder.*`

**Backend:** `apps/honojs/src/router/appraisal-orders/`

**Automation Page Object:** `pages/appraisal_order_page.py` — `AppraisalOrderPage` (optional `bucket=`)

**Automation Tests:** `tests/test_appraisal_order.py`, `tests/test_be_appraisal_order.py` — `@smoke`

---

## 17. Submitted

**Application Route:** Lead detail — `?tab=submitted`

**Main Component:** `features/lead-detail/components/submitted/Submitted.tsx`

**Child Components:** `SubmittedForm` (renders per mortgage option), `SubmittedSkeleton`

**Business Logic (verified from source):**

- Three mortgage options (Option 1, Option 2, Option 3) as internal tabs
- Option 2 disabled if Option 1 is approved
- Option 3 disabled if Option 1 OR Option 2 is approved
- Each option stores: lender name, mortgage type, loan amount, LTV, term, rate, power of attorney, approved flag, rejected reason
- When a submitted option is marked `approved = true`, it auto-locks other options
- Data fetched via `orpc.submitted.getSubmittedByLeadId`

**API:** `orpc.submitted.*`

**Backend:** `apps/honojs/src/router/submitted/`

**Automation Page Object:** `pages/submitted_page.py` — `SubmittedPage` (optional `bucket=`)

**Automation Tests:** `tests/test_submitted.py`, `tests/test_be_submitted.py` — `@smoke`

**Key Locators:**

- Option tabs: `get_by_role("tab", name="Mortgage Option 1")`, `"Mortgage Option 2"`, `"Mortgage Option 3"`
- Disabled tab hint: `title` attribute on disabled tab trigger
- Lender name: `get_by_role("textbox", name="Lender Name")` (check actual placeholder in `SubmittedForm`)

**Automation Notes:**

- Test Option 2 disabled state by first approving Option 1
- Visible only when `nextStatus >= 10`

---

## 18. Approved

**Application Route:** Lead detail — `?tab=approved`

**Main Component:** `features/lead-detail/components/Approved/Approved.tsx`

**Child Components:**

- `MortgageOption`, `CheckPlan`, `NewTomorrowPlan`, `TopMortgageOptions`, `HowClientSaves` — in "Approved Form" tab
- `AppraisalCompletedSection` — in "Appraisal Completed" tab (gated: only accessible after Approved Form is valid)
- `StageUpdateDialog` — to move to Signed after completion

**Business Logic (verified from source):**

- Two internal tabs: "Approved Form" and "Appraisal Completed"
- "Appraisal Completed" tab is disabled until Approved Form schema validates (`tabOneReady`)
- Auto-fills from `leadDetail.submitted` (approved items) and DLO data
- `remainingEquity` auto-computed: `appraisedValue - totalMortgages`
- Save on Approved Form → navigates to Appraisal Completed tab
- "Complete Stage" button validates full `approvedCompleteSchema` → shows `StageUpdateDialog` to move to Signed
- **NTP Application button** — opens external application in a new tab

**NTP Application (verified from source):**

- Button label: `"NTP Application"` with `ExternalLink` icon
- URL: `${env.NEXT_PUBLIC_NTP_APP_URL}/staff?id=${userId}&token=${auth_token_cookie_value}`
- Opens in a new browser tab (`window.open(url, "_blank")`)
- Auth: `userId` (from auth session) + `auth_token` cookie value passed as URL params
- Shows Submitted and Approved leads; displays NTP page; allows PDF download

**API:** `orpc.approved.getApprovedByLeadId`, `orpc.approved.createApproved`, `orpc.approved.updateApproved`

**Backend:** `apps/honojs/src/router/approved/`

**Automation Page Object:** `pages/approved_page.py` — `ApprovedPage` (optional `bucket=`)

**Automation Tests:** `tests/test_approved.py`, `tests/test_be_approved.py` — `@smoke`

**Key Locators:**

- Approved Form tab: `get_by_role("tab", name="Approved Form")`
- Appraisal Completed tab: `get_by_role("tab", name="Appraisal Completed")`
- NTP Application button: `get_by_role("button", name="NTP Application")`
- Save button: `get_by_role("button", name="Save")`

**NTP Automation (implemented):**

1. Save Approved Form in CRM, then click **NTP Application** (or use `open_ntp_from_crm_after_approved_save()`)
2. Capture the new page/tab via helper orchestration in `utils/ntp_app_helpers.py`
3. Verify presentation fields via `pages/ntp_app/presentation_page.py` — `NtpAppPresentationPage`
4. Refresh, reopen, logout, RBAC check (`utils/ntp_app_rbac.py`), return to CRM tab
5. PDF download can be asserted via `page.expect_download()` where covered

**Automation Tests:** `tests/test_ntp_app_display.py` — `@smoke`, with/without co-borrower scenarios

**Automation Helpers:** `utils/ntp_app_helpers.py`, `utils/ntp_app_auth.py`, `utils/ntp_display.py`; config `Config.NTP_APP_URL`, `Config.NTP_APP_LEAD_SYNC_TIMEOUT_MS`

**Automation Notes:**

- Approved Form saves first, then Appraisal tab unlocks
- `StageUpdateDialog` appears after completing full stage — confirm to move to Signed

---

## 19. Signed

**Application Route:** Lead detail — `?tab=signed`

**Main Component:** `features/lead-detail/components/signed/Signed.tsx`

**Child Components:**

- `ClientSignedSection` — first section (always visible)
- `FinalProductSection` — visible only if `clientSigned === "yes"`
- `DealTrackingSection`, `ClientFinancialProfileSection`, `ImportantClientNotesSection` — visible only if `finalProduct === "yes"`
- `GoogleReviewSection` — visible only if lead is already in Signed stage status

**Business Logic (verified from source):**

- Conditional rendering: `ConditionalSections` reads `clientSigned` and `finalProduct` from form
- If `clientSigned !== "yes"` → only `ClientSignedSection` shown
- If `clientSigned === "yes"` + `finalProduct === "yes"` → all sections shown
- `useSignedForm` hook manages form state and submission
- On save: `pendingStageUpdate` triggers `StageUpdateDialog`
- `GoogleReviewSection` only renders when lead status matches signed stage (11 for frontend, 34 for backend)

**API:** `orpc.leadSigned.*`

**Backend:** `apps/honojs/src/router/lead-signed/`

**Automation Page Object:** `pages/signed_page.py` — `SignedPage` (optional `bucket=`)

**Automation Tests:** `tests/test_signed.py`, `tests/test_be_signed.py`, `tests/test_signed_marketing.py` — `@smoke`

**Key Locators:**

- Save: `get_by_role("button", name="Save")`
- Cancel: `get_by_role("button", name="Cancel")`

**Automation Notes:**

- Must set `clientSigned = "yes"` to reveal subsequent sections
- `GoogleReviewSection` only visible after lead is moved to Signed status

---

## 20. Co-Borrower

**Application Route:** Lead detail — `?tab=co-borrowers`

**Main Component:** `features/lead-detail/components/coBorrower/CoBorrower.tsx`

**Child Component:** `AddCoBorrowerModel` — modal dialog

**API:** `orpc.coBorrower.*`

**Backend:** `apps/honojs/src/router/co-applicants/`

**Automation Page Object:** `pages/add_coBorrower_page.py` — `CoBorrowerPage`

**Existing Methods:**

- `open()`, `open_lead(lead_name)`, `open_co_borrowers_tab()`
- `click_add_co_borrower()`, `fill_basic_info(data)`, `select_dob(data)`
- `select_marital_status(status)`, `fill_employment(employer, relation, income)`, `fill_income(income)`, `save()`

**Automation Tests:** `tests/test_add_coborrower.py` — `test_add_co_borrower`

**Related Helpers:**

- `test_page_data/addcoborrower_data.py` — `test_data`
- `authenticated_page` fixture

**Key Locators:**

- Add Co-Borrower button: `get_by_role("button", name="Add Co-Borrower")`
- Co-borrowers tab: `get_by_role("tab", name="Co-borrowers")`
- Form fields: `#firstName`, `#lastName`, `#email`, phone `(XXX) XXX-XXXX`
- DOB picker: `get_by_role("button", name="Pick a date")`
- Month/Year: `get_by_role("combobox", name="month")` / `get_by_role("combobox", name="year")`
- Marital status: `get_by_role("combobox").filter(has_text="Single")`
- Employer: `get_by_role("textbox", name="Employer")`
- Relation: `get_by_role("combobox").filter(has_text="Parent")`
- Save: `get_by_role("button", name="Save")`

---

## 21. Shared Automation Infrastructure

### conftest.py Fixtures

| Fixture                             | Use When                                                 |
| ----------------------------------- | -------------------------------------------------------- |
| `playwright_instance`               | Never import directly — used by `browser`                |
| `browser`                           | Base browser session                                     |
| `browser_context`                   | Unauthenticated tests needing video/trace (e.g. login)   |
| `page`                              | Unauthenticated page                                     |
| `admin_auth_state` / `auth_state`   | Session-scoped Admin auth — never call directly in tests |
| `fe_agent_auth_state`               | Session-scoped Frontend Agent auth                       |
| `be_agent_auth_state`               | Session-scoped Backend Agent auth                        |
| `authenticated_page` / `admin_page` | Admin tests (lead CRUD, stage smokes, orchestrators)     |
| `fe_agent_page`                     | Frontend Agent RBAC and FE-specific tests (`@fe_agent`)  |
| `be_agent_page`                     | Backend Agent RBAC and BE pipeline tests (`@be_agent`)   |

### pytest Markers

| Marker              | Purpose                                                        |
| ------------------- | -------------------------------------------------------------- |
| `smoke`             | Quick validation tests (orchestrators and external-app smokes) |
| `module_smoke`      | Single-module happy-path tests requiring bootstrap deal state  |
| `regression`        | Full all-cases regression (`test_full_sales_frontend_flow.py`, agent regression files) |
| `flow_orchestrator` | Single-run E2E with virtual per-module HTML rows               |
| `fe_agent`          | Requires Frontend Agent credentials                            |
| `be_agent`          | Requires Backend Agent credentials                             |

### Shared Utilities

| File                                                      | Use For                                                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------ |
| `utils/config.py` → `Config`                              | URLs, Admin/FE/BE credentials, timeouts, viewport                        |
| `utils/entity_navigation.py`                              | Bucket navigation — Lead Bucket, My Leads, Sales Frontend, Sales Backend |
| `utils/lead_assignment.py` → `LeadAssignmentHelper`       | Admin assigns agents/status from Lead Bucket                             |
| `utils/workflow_verification.py` → `WorkflowVerification` | Tab visibility, stage transitions, RBAC checks                           |
| `test_page_data/workflow_expectations.py`                 | CRM-derived constants (status IDs, toasts, tab names)                    |
| `utils/sales_flow_helpers.py`                             | Stage smoke runners, BE setup, `run_backend_full_flow()`                 |
| `utils/sales_flow_orchestration.py`                       | Reporting-aware full-flow orchestrators                                  |
| `utils/sales_flow_regression_helpers.py`                  | All-cases regression helpers                                             |
| `utils/wait_helpers.py`                                   | Google Places autocomplete, Canadian postal recovery, URL waits           |
| `utils/lead_context.py`                                   | Bootstrap lead/deal session store                                        |
| `utils/stage_transition_verification.py`                  | Stage-move URL/tab/toast verification                                    |
| `utils/mortgage_snapshot_app_helpers.py`                  | MS App workflow from CRM                                                 |
| `utils/ntp_app_helpers.py`                                | NTP App workflow from CRM Approved                                       |
| `utils/negative_test_helpers.py`                          | Shared empty/invalid field verification                                  |
| `utils/html_report_history.py`                            | Unique HTML report paths and run index                                   |
| `utils/toast.py` → `Toast`                                | Sonner toast assertions (`[data-sonner-toast]`)                          |
| `utils/validations.py` → `Validations`                    | Field-level error messages                                               |
| `utils/reporting.py`                                      | Failure screenshots, HTML extras, test data capture                      |
| `utils/flow_step_reporting.py`                            | Virtual module rows for `@flow_orchestrator` tests                       |
| `utils/logger.py` → `get_logger()`                        | Logging at top of every test file                                        |
| `utils/test_data_factory.py`                              | Lead creation parametrized data                                          |
| `test_page_data/test_entities.py`                         | Persistent deal names, agent labels, status labels                       |
| `test_page_data/random_gen_data.py` → `RandomGenerator`   | Random mortgage/person/address data                                      |

### Stage Transition Dialog (reusable pattern)

Any test that advances a lead stage will encounter `StageUpdateDialog`:

```python
# After triggering a stage completion:
page.get_by_role("alertdialog").wait_for(state="visible")
page.get_by_role("button", name="Move to Next Stage").click()
# Expect toast:
toast = Toast(page)
toast.assert_message("Lead moved to <NextStageName> successfully")
```

### Tab Navigation Pattern

Direct URL navigation is always more reliable than clicking tabs:

```python
page.goto(Config.BASE_URL + f"/sales/{lead_id}?tab=mortgage-snapshot")
page.wait_for_load_state("networkidle")
```

### New Tab / Popup Pattern (for NTP / external apps)

```python
with context.expect_page() as new_page_info:
    page.get_by_role("button", name="NTP Application").click()
new_page = new_page_info.value
new_page.wait_for_load_state("networkidle")
# assert URL, fields, download
```

---

## Coverage Summary

| Module              | Page Object                    | Tests                                              | Priority |
| ------------------- | ------------------------------ | -------------------------------------------------- | -------- |
| Authentication      | `LoginPage` ✓                  | `test_login_page.py` ✓                             | —        |
| Create Lead         | `CreateLeadPage` ✓             | `test_create_lead.py` ✓                            | —        |
| Edit Lead           | `LeadEditPage` ✓               | `test_lead_edit.py` ✓                              | —        |
| Notes               | `NotesPage` ✓                  | `test_note.py` ✓                                   | —        |
| Co-Borrower         | `CoBorrowerPage` ✓             | `test_add_coborrower.py` ✓                         | —        |
| Lead Bucket         | `entity_navigation` ✓          | via orchestrators / assignment ✓                   | —        |
| My Leads            | `entity_navigation` ✓          | via FE smokes / orchestrators ✓                    | —        |
| Sales Frontend      | Shared stage POs ✓             | Stage smokes + orchestrators ✓                     | —        |
| Sales Backend       | Shared stage POs (`bucket=`) ✓ | BE smokes + `test_admin_backend_flows.py`, `test_be_agent_flows.py` ✓ | —        |
| MS App              | `mortgage_snapshot_app/*` ✓    | `test_mortgage_snapshot_app_display.py`, `test_ms_app_rbac.py` ✓       | —        |
| NTP Application     | `ntp_app/*` ✓                  | `test_ntp_app_display.py` ✓                                           | —        |
| Profile viewing     | `ProfilePage` ✓                | Used by form-prefill verification helpers                               | Low      |
| Stage Gating / RBAC | `WorkflowVerification` ✓       | `test_fe_agent_rbac.py`, `test_be_agent_rbac.py`, `test_ms_app_rbac.py` ✓ | —        |
| Mortgage Snapshot   | `MortgageSnapshotPage` ✓       | FE + BE stage tests ✓                              | —        |
| Appraisal Order     | `AppraisalOrderPage` ✓         | FE + BE stage tests ✓                              | —        |
| Submitted           | `SubmittedPage` ✓              | FE + BE stage tests ✓                              | —        |
| Approved            | `ApprovedPage` ✓               | FE + BE stage tests ✓                              | —        |
| Signed              | `SignedPage` ✓                 | FE + BE + marketing tests ✓                        | —        |
| Compliance          | `CompliancePage` ✓             | `test_compliance.py` + orchestrators ✓             | —        |
| Client Care         | `ClientCarePage` ✓             | `test_client_care.py` ✓                            | —        |
| Marketing           | `MarketingPage` ✓              | `test_marketing.py` ✓                              | —        |
| Nova Worksheet      | `NovaWorksheetPage` ✓          | `test_nova_worksheet.py` skipped; Nova bypass in orchestrators ✓   | —        |
| Nurture             | ✗                              | ✗                                                  | Medium   |
| DLO                 | ✗                              | ✗                                                  | Medium   |
| Documents           | ✗                              | ✗                                                  | Low      |
| Activity Logs       | ✗                              | ✗                                                  | Low      |

---

## Unmapped Business Workflows

The following workflows exist in the application but have no automation mapping yet. They are documented here at the business level for future reference. When implementing, follow the same module mapping format used in sections 1–21 above.

---

### Dashboard & Analytics

**Business Workflows:**

- Agent Dashboard Overview — view key metrics, lead pipeline, team pipeline, active deals
- Performance & Achievements — track achievements, review analytics

**Frontend Route:** `/` or `/dashboard` (root dashboard after login)

**Automation Notes:** No page object or tests exist. Requires reading dashboard cards, counters, and chart data.

---

### Lead Qualification Actions

**Business Workflows:**

- Mark as Fake Lead — flags lead as invalid
- Mark as Not Proceeding — removes lead from active pipeline
- Move to Sales — promotes lead from Lead Bucket to Sales Frontend
- Send Application — sends application to the client

**Frontend Component:** `LeadInfoHeader.tsx` — action buttons visible per lead status

**Automation Notes:** These are buttons in the lead header. Locators: `get_by_role("button", name="Fake Lead")`, `get_by_role("button", name="Not Proceeding")`, `get_by_role("button", name="Move to Sales")`. Each triggers a confirmation dialog.

---

### Lead Status & History

**Business Workflows:**

- Update Lead Status
- Advance Pipeline Stage
- Review Lead History

**Frontend Route:** Lead detail — `?tab=lead-history`

**Main Component:** `features/lead-detail/components/LeadHistoryTab.tsx` (verify file name)

**API:** `orpc.lead.getLeadDetail` (includes history)

**Automation Notes:** History tab shows a timeline of status changes. No page object or tests yet.

---

### Merge Duplicate Leads

**Business Workflows:**

- Select leads to merge, choose primary lead, compare field values, confirm merge

**Automation Notes:** Merge UI not yet located in source. Requires source code inspection before automating.

---

### Communication — Email & SMS

**Business Workflows:**

- Compose email from lead profile, apply email template, send email
- Compose SMS, send message

**Frontend Component:** `CommunicationCard` — rendered alongside Profile tab in lead detail

**Automation Notes:** Compose area is in the Profile tab sidebar. Locators require inspection of `CommunicationCard` component. No page object or tests exist.

---

### Communication — Internal Chat

**Business Workflows:**

- Start new conversation, manage group members, share files, view profile

**Automation Notes:** Chat feature likely has its own route or drawer. Requires source code inspection.

---

### Notifications

**Business Workflows:**

- Review notifications, manage notification preferences

**Automation Notes:** Notification bell in app header. No tests exist.

---

### Mortgage History

**Business Workflows:**

- Add historical mortgage, review mortgage history

**Frontend Route:** Lead detail — `?tab=mortgage-history`

**Automation Notes:** Mortgage History tab is available in Sales Backend but not Sales Frontend. No page object or tests exist.

---

### Nova Worksheet

**Business Workflows:**

- Choose refinance / equity / purchase, prefill from source data, import credit and application documents
- Capture borrower qualifying details, debts, credit summary
- Capture existing mortgages, define mortgage terms, apply lender criteria
- Calculate fees, cash to close, net advance and savings
- Present worksheet to client, capture client signature

**Automation Page Object:** `pages/nova_worksheet_page.py` — `NovaWorksheetPage`

**Automation Tests:** `tests/test_nova_worksheet.py` — currently `@pytest.mark.skip` (Scarlett app number dependency). Nova status **59** bypass is exercised in orchestrators via `run_nova_bypass_smoke()` / `LeadAssignmentHelper.assign_fe_nova_bypass()`.

**Automation Notes:** Admin assigns FE agent with Nova bypass status via `LeadAssignmentHelper.assign_fe_nova_bypass()`. Do not use Push to Scarlett for bypass.

---

### Lender Management

**Business Workflows:**

- Manage lender profiles, define lender criteria
- Match lead to lenders, rank lender options, review lender guidelines

**Automation Notes:** Admin/settings area. No page object or tests exist.

---

### Vendor Management — Law Firms & Lawyers

**Business Workflows:**

- Add and maintain law firm details
- Add and maintain lawyer details
- Used in Compliance closing coordination (assign law firm, assign lawyer)

**Automation Notes:** Admin settings area. Referenced from Compliance closing flow. No tests exist.

---

### Product Catalog

**Business Workflows:**

- Add products, maintain product details, plan types, property types

**Automation Notes:** Admin settings area. No tests exist.

---

### AI Underwriting

**Business Workflows:**

- Review lead completeness, run underwriting assessment
- Interact via AI chat, generate lender recommendations, validate lead data

**Application:** Separate external application (likely `ai-underwriter` app in monorepo)

**Automation Notes:** External app — requires new browser context, auth flow inspection, and dedicated page objects. Not yet mapped.

---

### Tasks & Reminders

**Business Workflows:**

- Create task, track tasks
- Review headlines, track important items, manage meetings

**Automation Notes:** Likely accessible from the sidebar or a dedicated route. No tests exist.

---

### Administration & Settings

**Business Workflows:**

- Update personal information, update company information, manage localization
- Manage staff, manage roles, configure permissions
- Manage security settings, review logged-in devices
- Review audit logs, configure lead management preferences, configure notifications

**Frontend Route:** `/settings/*` (verify exact sub-routes)

**Automation Notes:** Admin-only. Requires admin credentials. Covers staff CRUD, role assignment, RBAC configuration, and audit log review. No tests exist.

---

### Integrations — Scarlett

**Business Workflows:**

- Pull lead data from Scarlett CRM into this system

**Frontend Component:** `PushToScarlettButton` in `LeadInfoHeader.tsx`

**API:** `orpc.scarlett.*` (backend: `apps/honojs/src/router/scarlett/`)

**Automation Notes:** Button in lead header. Clicking triggers a push/pull to Scarlett. Requires verifying exact API response and success toast.

---

### Integrations — Legacy CRM & Lead Migration

**Business Workflows:**

- Add lead to legacy CRM, flag lead in legacy CRM
- Import leads, migrate notes, migrate requested documents

**Automation Notes:** Admin/bulk operation features. Requires source code inspection before automating.

---

### Search

**Business Workflows:**

- Search across records (leads, notes, documents)

**Automation Notes:** Global search bar in app header. No tests exist. Locator: `get_by_placeholder("Search...")` or `get_by_role("searchbox")`.

---

### System Audit

**Business Workflows:**

- Track system activity, retain audit history (background cron)

**Automation Notes:** Admin-facing audit log. Backend cron: `apps/honojs/src/cron/audit-retention.ts`. No frontend automation needed unless verifying audit log entries.
