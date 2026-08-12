# PROJECT_STRUCTURE.md

Complete reference for the Nuborrow Agent Dashboard repository, written to support accurate Playwright automation. Everything documented here exists in the source code.

---

## 1. Repository Architecture

```
nuborrow-agent-dashboard/          ← pnpm + Turborepo monorepo root
├── apps/
│   ├── nextjs/                    ← CRM frontend (Next.js 16, React 19)
│   ├── honojs/                    ← API backend (Hono + oRPC)
│   ├── ai-underwriter/            ← AI underwriting chat app (Next.js)
│   ├── auth-service/              ← Authentication service (better-auth)
│   └── migrator/                  ← Kafka-based lead/data migration service
├── packages/
│   ├── db/                        ← Drizzle ORM schema + migrations
│   ├── orpc-contract/             ← Shared typed API contract (oRPC)
│   ├── redis/                     ← Redis client wrapper
│   ├── ui/                        ← Shared shadcn/ui component library
│   ├── underwriter/               ← ChatBot widget package
│   └── validators/                ← Zod schemas + PERMISSIONS constants
├── tooling/                       ← ESLint, TypeScript, Prettier configs
├── infra/                         ← SST (AWS) infrastructure
├── automation/                    ← Playwright test suite (Python)
└── docs/                          ← Project documentation
```

---

## 2. Frontend — `apps/nextjs/`

### 2.1 Technology

| Concern        | Library                                    |
| -------------- | ------------------------------------------ |
| Framework      | Next.js 16 (App Router)                    |
| UI             | React 19 + Tailwind CSS                    |
| Components     | `@nuborrow/ui` (shadcn/ui)                 |
| API client     | oRPC (`@orpc/client`, `@orpc/react-query`) |
| Server state   | TanStack Query (`useQuery`, `useMutation`) |
| Forms          | React Hook Form + Zod (`zodResolver`)      |
| Auth           | Server Actions + `auth_token` cookie       |
| RBAC           | Custom `RbacProvider` / `useRbac`          |
| Toasts         | `sonner`                                   |
| Error tracking | Sentry                                     |

### 2.2 Source folder map

```
apps/nextjs/src/
├── app/                           ← Next.js App Router pages
│   ├── (auth)/                    ← Unauthenticated routes (no sidebar)
│   │   ├── login/page.tsx
│   │   ├── otp/page.tsx
│   │   ├── forget-password/page.tsx
│   │   └── reset-password/page.tsx
│   ├── (dashboard)/               ← Authenticated routes (sidebar + header)
│   │   ├── layout.tsx             ← Root dashboard layout
│   │   ├── page.tsx               ← / — Dashboard home
│   │   ├── lead-bucket/
│   │   │   ├── page.tsx           ← /lead-bucket
│   │   │   └── [id]/page.tsx      ← /lead-bucket/:id
│   │   ├── my-leads/
│   │   │   ├── page.tsx           ← /my-leads
│   │   │   └── [id]/page.tsx      ← /my-leads/:id
│   │   ├── sales/
│   │   │   ├── page.tsx           ← /sales ("My Deals" — Sales Frontend)
│   │   │   └── [id]/page.tsx      ← /sales/:id
│   │   ├── sales-backend/
│   │   │   ├── page.tsx           ← /sales-backend
│   │   │   └── [id]/page.tsx      ← /sales-backend/:id
│   │   ├── compliance/
│   │   │   ├── page.tsx           ← /compliance
│   │   │   └── [id]/page.tsx      ← /compliance/:id
│   │   ├── create-lead/page.tsx   ← /create-lead
│   │   ├── edit-lead/[id]/page.tsx← /edit-lead/:id
│   │   ├── merge-leads/page.tsx   ← /merge-leads
│   │   ├── tasks/page.tsx
│   │   ├── communication/page.tsx
│   │   ├── achievements/page.tsx
│   │   ├── products/
│   │   ├── settings/page.tsx
│   │   └── vendor-management/
│   │       ├── law-firms/
│   │       └── lawyers/
│   └── api/                       ← Next.js route handlers (thin wrappers)
│       ├── home-appraised/invite-user/route.ts
│       ├── opta/estimated-value-range/route.ts
│       └── old-crm/               ← Legacy CRM bridge endpoints
├── features/                      ← Business feature modules
├── components/                    ← Shared UI components
├── lib/                           ← Utilities and services
├── hooks/                         ← Custom React hooks
├── orpc/                          ← oRPC client setup
└── types/                         ← Shared TypeScript types
```

---

## 3. Authentication Flow

### Routes

- `GET /login` — email/password form
- `GET /otp` — two-factor OTP entry
- `GET /forget-password` — request reset link
- `GET /reset-password` — set new password

### Login sequence

1. `LoginForm` (`features/auth/components/LoginForm.tsx`) submits via `loginAction` (Next.js Server Action in `lib/auth/actions.ts`).
2. Server Action calls `POST {AUTH_URL}/api/auth/sign-in/email` (the `auth-service` app).
3. If 2FA is required: `auth-service` sets `better-auth.two_factor` cookie → Next.js redirects to `/otp`.
4. OTP form calls `verifyOtpAction` → `POST {AUTH_URL}/api/auth/two-factor/verify-otp`.
5. On success: `auth_token` cookie is set (httpOnly: false, 1 day expiry).
6. Router pushes to `/` (dashboard home).

### Auth cookie

- Cookie name: `auth_token`
- Used by the oRPC client as `Authorization: Bearer <token>` on every API call.

### Logout

- `logoutAction` (Server Action): calls `GET {AUTH_URL}/api/logout`, clears all auth cookies, redirects to `/login`.

### Key files

| File                                     | Purpose                                                             |
| ---------------------------------------- | ------------------------------------------------------------------- |
| `lib/auth/actions.ts`                    | `loginAction`, `verifyOtpAction`, `resendOtpAction`, `logoutAction` |
| `lib/auth/cookies.ts`                    | `AUTH_COOKIE_NAMES` constant                                        |
| `features/auth/components/LoginForm.tsx` | Login UI + form logic                                               |
| `features/auth/components/OtpForm.tsx`   | OTP UI + form logic                                                 |

---

## 4. Dashboard Layout

File: `app/(dashboard)/layout.tsx`

```
RbacProvider
  └── SidebarProvider
        ├── AppSidebar         ← Left sidebar (collapsible icon mode)
        │   └── SidebarButtons ← Navigation links, RBAC filtered
        └── SidebarInset
              ├── Header       ← Top bar
              ├── ImpersonationBanner  ← Shown when impersonating
              └── MainLayout
                    └── {children}   ← Page content
```

### Impersonation

`ImpersonationBanner` is rendered for all authenticated pages. Allows admins to act as another user.

---

## 5. Navigation & Sidebar

### File: `src/types/sidebar.ts`

The entire sidebar structure is defined statically:

**Agent sidebar items** (`AGENT_SIDEBAR_ITEMS`):

| Title               | Route                  | Notes                              |
| ------------------- | ---------------------- | ---------------------------------- |
| Dashboard           | `/`                    |                                    |
| Lead Bucket         | `/lead-bucket`         | LEAD_BUCKET stages/steps           |
| My Leads            | `/my-leads`            | MY_LEADS_FRONTEND stages           |
| My Deals            | `/sales`               | SALES_FRONTEND stages/steps        |
| Sales Backend       | `/sales-backend`       | SALES_BACKEND stages/steps         |
| Compliance          | `/compliance`          | COMPLIANCE stages/steps            |
| Tasks               | `/tasks`               |                                    |
| Communication       | `/communication`       |                                    |
| Achievements        | `/achievements`        |                                    |
| Products            | `/products`            |                                    |
| Vendor Management   | (group)                | Children: Law Firms, Lawyers       |
| Analytics Dashboard | `/analytics-dashboard` | Opens in new tab                   |
| Settings            | `/settings`            | PERMISSIONS.SETTINGS.READ required |

**Role-based sidebar filtering** (`SidebarButtons.tsx`):

- `frontend-agent` — only sees: `/`, `/my-leads`, `/sales`, `/settings`, `/analytics-dashboard`
- `backend-agent` — only sees: `/`, `/sales-backend`, `/settings`, `/analytics-dashboard`
- Other roles — all items, permission-gated

**Roles** (from `types/auth.ts`): `admin`, `manager`, `agent`, `backend`, `renewal`

---

## 6. Lead Pipeline & Status Flow

### Stage constants (from `src/types/lead.ts`)

#### Lead Bucket stages (statusType: `"lead"`)

New → Remark Lead → 2nd Remark Lead → 3rd Remark Lead → 21 Day Old → 41 Day Old Lead → 60 Day Old Lead → Frozen → Fake Lead → Sent Application → Make Over 30 → Debt Free

#### Sales Frontend stages — "My Deals" (statusType: `"sales"`)

Application Received (8) → Mortgage Snapshot (13) → Nurture (57) → Appraisal Order (14) → Submitted (10) → Approved (48) → Signed (11) → Not Signed (16)

#### Sales Backend stages (statusType: `"sales-backend"`)

Expired Renewal Lead (28) → 6 Month Renewal Lead (56) → 9 Month Maturity (54) → Application Received (29) → Mortgage Snapshot (30) → Appraisal Ordered (31) → Submitted (32) → Approved (49) → Signed (34) → Not Signed (35)

#### Compliance stages (statusType: `"closed"`)

Single stage: Compliance

### Lead progression path

```
Lead Bucket ──► My Leads ──► Sales Frontend (/sales) ──► Sales Backend (/sales-backend) ──► Compliance (/compliance)
```

After a lead completes Signed in either Sales pipeline, it moves into Compliance (statusType `"closed"`).

---

## 7. Lead Detail — Tab System

Each section (lead-bucket, my-leads, sales, sales-backend, compliance) renders a lead detail page with a tabbed interface. Tabs are driven by `Step[]` arrays in `src/types/lead.ts`.

### How tabs work

1. `useLeadDetailStagesAndSteps(role)` reads `pathname` → finds the matching sidebar item → returns its `steps[]`.
2. `SaleLeadInfo` / `ComplianceLeadInfo` filter those steps by: RBAC access, lead's `nextStatus`, DLO data presence.
3. Tab URLs use `?tab=<value>` query parameter. Active tab is synced with URL.

### Sales Frontend tab steps (`SALES_FRONTEND_STEPS`)

| Tab name          | `value`             | Component                                 |
| ----------------- | ------------------- | ----------------------------------------- |
| Profile           | `profile`           | `ProfileTab`                              |
| Co-borrowers      | `co-borrowers`      | `CoBorrower`                              |
| Notes             | `notes`             | `NotesTab`                                |
| Documents         | `documents`         | `AttachmentsSection` (lazy, client-only)  |
| Activity logs     | `activity-logs`     | `ActivityTab` (admin only)                |
| Marketing         | `marketing`         | `CommunicationCard`                       |
| Lead History      | `lead-history`      | `LeadHistory`                             |
| Mortgage Snapshot | `mortgage-snapshot` | `MortgageSnapshot`                        |
| DLO               | `dlo`               | `DLO` (shown only if `dlo.vfliNo` exists) |
| Nurture           | `nurture`           | `Nurture` (always visible)                |
| Appraisal Order   | `appraisal-order`   | `AppraisalOrder`                          |
| Submitted         | `submitted`         | `Submitted`                               |
| Approved          | `approved`          | `Approved`                                |
| Signed            | `signed`            | `Signed`                                  |

### Profile tab — sub-tabs

Profile has 3 internal sub-tabs:

- **Personal Information** → `PersonalInformationSubTab` (Edit link: `/edit-lead/:id?tab=client-info`)
- **General Information** → `GeneralInformationSubTab`
- **Mortgage Information** → `MortgageInformationSubTab` (Edit link: `/edit-lead/:id?tab=mortgage-info`)

### Compliance Lead Detail tab steps (`COMPLIANCE_STEPS`)

Same tabs as Sales Frontend, plus:

- **Signed Closed** (`signed-closed`) → `Compliance` component (only in compliance detail)

---

## 8. Sales Module

### Sales Frontend (My Deals) — `/sales`

**List page:** `app/(dashboard)/sales/page.tsx`

- Renders `SaleLeadInfo` via `features/sales/components/SaleLeadInfo.tsx`.

**Detail page:** `app/(dashboard)/sales/[id]/page.tsx`

- Renders `SaleLeadInfo` component.
- Component: `features/sales/components/SaleLeadInfo.tsx` (295 lines)

**Data fetching:** `orpc.lead.getLeadDetail` (TanStack Query)

**API filter:** `statusType = "sales"` (via `orpc.lead.getFilteredLeads`)

**Key UI components inside SaleLeadInfo:**

- `LeadInfoHeader` — Back, Prev/Next navigation, action buttons
- `Tabs` + `TabsList` + `TabsTrigger` (shadcn/ui)
- All `SALES_FRONTEND_STEPS` tabs rendered

**Action buttons in header (role-gated):**

- `PendingRequirementsButton` — pending doc requirements
- `NotProceedingButton` — mark lead as not proceeding
- `SentApplicationButton` — (Lead Bucket / My Leads only)
- `MoveToSalesButton` — (Lead Bucket / My Leads only)
- `Push to Scarlett` / `PullToScarlettButton` — Scarlett CRM sync
- `HomeAppraisedButton` / `HomeAppraisedImages`
- `NovaWorksheetTrigger` — Nova worksheet (non-prod only)
- `ChatBotWidget` — AI underwriter (shown on DLO status only)
- `FakeLeadButton` — (in dropdown)

### Sales Backend — `/sales-backend`

**Components:** `features/sales-backend/components/`
**API filter:** `statusType = "sales-backend"`
**Steps:** `SALES_BACKEND_STEPS` — similar to Sales Frontend, no Nurture tab.

---

## 9. Compliance Module

### List page — `/compliance`

**File:** `app/(dashboard)/compliance/page.tsx`
**Component:** `features/compliance/components/UnifiedView.tsx` → `ComplianceUnifiedView`

**Key behavior:**

- Uses `GenericUnifiedView` (shared Kanban/List toggle component).
- `statusType = "closed"` passed to `orpc.lead.getFilteredLeads`.
- Supports Kanban and List views (`?view=kanban|list`).
- Filter state managed by `useBackendFilters` hook.
- Kanban columns built dynamically from `orpc.leadStatus.listLeadStatus`.
- Clicking a lead navigates to `/compliance/:id`.

### Detail page — `/compliance/:id`

**File:** `app/(dashboard)/compliance/[id]/page.tsx`
**Component:** `features/compliance/components/ComplianceLeadInfo.tsx`

**Difference from Sales detail:**

- Imports `Compliance` component and renders it on `signed-closed` tab.
- `COMPLIANCE_NEXT_STATUS_TO_LAST_STEP` controls which tabs are visible based on `nextStatus`.
- Additional valid tab: `signed-closed`.

### `Compliance` component

**File:** `features/lead-detail/components/compliance/Compliance.tsx`

Contains two internal tabs:

1. **Compliance Form** tab:
   - `ClosingComplianceSection` — Closing compliance checklist
   - `ClientCareChecksSection` — Checks to move into Client Care
2. **Signed Form** tab:
   - `SignedFormReadOnlyView` — Read-only view of the signed form

---

## 10. API Layer

### How API calls work

The frontend does **not** call REST endpoints directly. It uses **oRPC** — a fully-typed RPC layer over HTTP.

**Client setup:** `src/orpc/orpc-client.ts`

```
oRPC client  →  POST {NEXT_PUBLIC_API_URL}/rpc
               Authorization: Bearer <auth_token cookie>
```

**TanStack Query integration:**

```tsx
const result = useQuery(orpc.lead.getLeadDetail.queryOptions({ input: { id } }))
const mutation = useMutation(orpc.lead.updateLead.mutationOptions({ onSuccess: ... }))
```

**Contract:** `packages/orpc-contract/` — defines all available routes. The frontend imports `contract` from `@nuborrow/orpc-contract`.

### Key oRPC namespaces used in frontend

| Namespace               | Example usage                                                   |
| ----------------------- | --------------------------------------------------------------- |
| `orpc.lead`             | `getLeadDetail`, `getFilteredLeads`, `updateLead`, `createLead` |
| `orpc.leadStatus`       | `listLeadStatus`                                                |
| `orpc.scarlett`         | `pushToScarlett`                                                |
| `orpc.notes`            | Lead notes CRUD                                                 |
| `orpc.coBorrower`       | Co-borrower CRUD                                                |
| `orpc.mortgageSnapshot` | Snapshot form save/update                                       |
| `orpc.appraisalOrder`   | Appraisal form                                                  |
| `orpc.compliance`       | Compliance form save                                            |
| `orpc.signed`           | Signed form save                                                |
| `orpc.submitted`        | Submitted form                                                  |
| `orpc.approved`         | Approved section                                                |
| `orpc.dlo`              | DLO section                                                     |

### Auth service endpoints (called from Server Actions only)

| Endpoint                               | Purpose          |
| -------------------------------------- | ---------------- |
| `POST /api/auth/sign-in/email`         | Login            |
| `POST /api/auth/two-factor/verify-otp` | OTP verification |
| `POST /api/auth/two-factor/send-otp`   | Resend OTP       |
| `GET /api/logout`                      | Logout           |

---

## 11. Backend — `apps/honojs/`

### Framework

Hono (TypeScript) — mounted at `NEXT_PUBLIC_API_URL`. Exposes oRPC handlers at `/rpc`.

### Router modules (`apps/honojs/src/router/`)

| Router folder                 | Domain                      |
| ----------------------------- | --------------------------- |
| `leads/`                      | Lead CRUD, import, webhook  |
| `lead-status/`                | Lead status management      |
| `lead-notes/`                 | Notes CRUD                  |
| `lead-history/`               | Lead history                |
| `lead-signed/`                | Signed form                 |
| `co-applicants/`              | Co-borrower CRUD            |
| `mortgage-snapshot/`          | Snapshot form               |
| `mortgage-snapshot-meetings/` | Snapshot meeting reminders  |
| `mortgage-history/`           | Mortgage history            |
| `dlo-headlines/`              | DLO headlines               |
| `dlo-meetings/`               | DLO meeting reminders       |
| `appraisal-orders/`           | Appraisal order management  |
| `home-appraised/`             | Home appraisal value        |
| `approved/`                   | Approved stage data         |
| `submitted/`                  | Submitted stage data        |
| `compliance/`                 | Compliance form             |
| `doc-requests/`               | Document request management |
| `doc-request-items/`          | Document request line items |
| `doc-upload/`                 | S3 file uploads             |
| `emails/`                     | Email sending               |
| `sms/`                        | SMS sending                 |
| `lenders/`                    | Lender profiles             |
| `users/`                      | User management             |
| `roles/`                      | Role management             |
| `permissions/`                | Permission management       |
| `staff-permissions/`          | Staff-level permissions     |
| `settings/`                   | Settings                    |
| `rbac/`                       | RBAC setup                  |
| `dashboard/`                  | Dashboard metrics           |
| `scarlett/`                   | Scarlett CRM integration    |
| `search/`                     | Full-text search            |
| `activity-logs/`              | Activity log                |
| `system-audit/`               | System audit trail          |
| `lead-limits/`                | Lead limits per agent       |
| `dynamic-fields/`             | Dynamic form fields         |
| `products/`                   | Product catalog             |
| `plan-type/`                  | Mortgage plan types         |
| `property-type/`              | Property types              |
| `law-firms/`                  | Law firm management         |
| `lawyers/`                    | Lawyer management           |
| `relations/`                  | Co-borrower relations       |
| `source/`                     | Lead source tracking        |
| `cron-config/`                | Scheduled job config        |
| `cache/`                      | Cache management            |
| `migration/`                  | Data migration utilities    |

### Middlewares (`apps/honojs/src/middlewares/`)

- `auth.ts` — JWT token validation
- `rbac.ts` — Permission enforcement
- `audit.ts` — Audit logging
- `db.ts` — Database connection
- `pino-logger.ts` — Structured logging
- `global-error-handler.ts` — Centralized error handling
- `retry.ts` — Retry logic

### Background jobs (`apps/honojs/src/cron/`)

- `emails.ts` — Email scheduling
- `audit-retention.ts` — Audit log retention

### Lead assignment cron (`apps/honojs/src/lead-assignment-cron/`)

Scheduler that assigns leads to agents and sends email notifications.

---

## 12. RBAC System

### Roles

`admin`, `manager`, `agent`, `backend`, `renewal`

### Role-slug variants (for sidebar)

`frontend-agent`, `backend-agent` — drive sidebar item visibility.

### Key files

| File                            | Purpose                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------- |
| `lib/rbac/rbac-provider.tsx`    | `RbacProvider` context, `useRbac()` hook (`can()`, `roleSlug`, `permissions`) |
| `lib/rbac/route-permissions.ts` | `ROUTE_PERMISSIONS`, `SETTINGS_TAB_PERMISSIONS`, `SIDEBAR_PERMISSIONS`        |
| `lib/rbac/lead-access/index.ts` | `filterStepsForLeadAccess`, `isStaffAdmin`, `resolveListAssignedTo`           |
| `lib/rbac/useLeadFullAccess.ts` | `useLeadFullAccess(assignedToId)` → `hasFullAccess` boolean                   |
| `packages/validators/`          | `PERMISSIONS` constants (source of truth for permission strings)              |

### Lead access pattern

`hasFullAccess` controls whether the full tab set is shown in lead detail. Agents only see a reduced tab set if the lead is not assigned to them. Admins always see all tabs.

---

## 13. Shared Components

### `src/components/layout/`

| Component             | Purpose                               |
| --------------------- | ------------------------------------- |
| `AppSidebar`          | Left navigation sidebar               |
| `SidebarButtons`      | Renders nav items with RBAC filtering |
| `Header`              | Top bar                               |
| `HeaderClient`        | Client-side part of header            |
| `ImpersonationBanner` | Shows when admin is impersonating     |
| `MainLayout`          | Wraps page content                    |

### `src/components/shared/`

| Component                       | Purpose                        |
| ------------------------------- | ------------------------------ |
| `forms/FormInputField`          | Controlled text input          |
| `forms/FormSelectField`         | Controlled select              |
| `forms/FormDatePickerField`     | Date picker                    |
| `forms/FormPhoneInputField`     | Phone number input             |
| `forms/FormRichTextEditorField` | Rich text editor (Tiptap)      |
| `forms/PasswordInput`           | Password with show/hide toggle |
| `filters/FilterAndSearch`       | Search + filter bar            |
| `filters/BackendFilterPanel`    | Advanced backend filters       |
| `data-display/DataTable`        | TanStack Table                 |
| `dialogs/ConfirmDialog`         | Generic confirm dialog         |
| `dialogs/EditLeadModal`         | Edit lead modal                |
| `CollapsibleSection`            | Expand/collapse section card   |

### `src/features/kanban/`

| Component             | Purpose                                                   |
| --------------------- | --------------------------------------------------------- |
| `GenericUnifiedView`  | Kanban/List toggle container (used by all pipeline pages) |
| `GenericKanbanBoard`  | Kanban board                                              |
| `GenericKanbanCard`   | Individual card                                           |
| `GenericKanbanColumn` | Kanban column                                             |

---

## 14. Feature Modules (`src/features/`)

| Feature folder    | Pages it powers                                  |
| ----------------- | ------------------------------------------------ |
| `auth/`           | Login, OTP                                       |
| `dashboard/`      | `/` home                                         |
| `lead-bucket/`    | `/lead-bucket`                                   |
| `my-leads/`       | `/my-leads`                                      |
| `leads/`          | Shared lead action buttons                       |
| `lead-create/`    | `/create-lead`                                   |
| `lead-edit/`      | `/edit-lead/:id`                                 |
| `lead-merge/`     | `/merge-leads`                                   |
| `lead-detail/`    | All lead detail tabs (shared across pipeline)    |
| `sales/`          | `/sales` list + detail                           |
| `sales-backend/`  | `/sales-backend` list + detail                   |
| `compliance/`     | `/compliance` list + detail                      |
| `nova-worksheet/` | Nova Worksheet modal (equity/refinance/purchase) |
| `law-firms/`      | `/vendor-management/law-firms`                   |
| `lawyers/`        | `/vendor-management/lawyers`                     |
| `products/`       | `/products`                                      |
| `settings/`       | `/settings`                                      |
| `tasks/`          | `/tasks`                                         |
| `achievements/`   | `/achievements`                                  |
| `chat/`           | `/communication`                                 |
| `kanban/`         | Shared Kanban infrastructure                     |

---

## 15. State Management

- **Server/async state:** TanStack Query (`useQuery`, `useMutation`, `useQueryClient`).
- **UI/local state:** React `useState`.
- **URL state:** `useSearchParams`, `router.push` — tab active state is in `?tab=` query param, view mode in `?view=kanban|list`.
- **Session storage:** Kanban column pagination is persisted to `sessionStorage` via `useKanbanPersistence`.
- **No global state library** (no Redux, Zustand, or MobX).

---

## 16. Business Logic Locations

| Logic                         | Location                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------- |
| Auth token handling           | `lib/auth/actions.ts` (Server Actions)                                          |
| RBAC permission checks        | `lib/rbac/rbac-provider.tsx`, `lib/rbac/lead-access/`                           |
| Lead pipeline step visibility | `features/lead-detail/useLeadDetailStagesAndSteps.tsx`                          |
| Lead navigation (prev/next)   | `features/lead-detail/components/leadNavigation/`                               |
| Tab/step filtering by status  | `SaleLeadInfo.tsx`, `ComplianceLeadInfo.tsx` (inline `filterStepsByNextStatus`) |
| Stage/status constants        | `src/types/lead.ts`                                                             |
| Sidebar item definitions      | `src/types/sidebar.ts`                                                          |
| Kanban column building        | `features/leads/status-type-mapping.ts`                                         |
| Filter state                  | `hooks/useBackendFilters.ts`                                                    |
| Google Places autocomplete    | `lib/services/google-places.ts`                                                 |
| Nova worksheet calculations   | `features/nova-worksheet/lib/`                                                  |

---

## 17. Playwright Automation — Key Locator Reference

### Login page (`/login`)

- Email field: `get_by_role("textbox", name="Enter an email")`
- Password field: `get_by_role("textbox", name="Enter a password")`
- Show password: `get_by_role("button", name="Show password")`
- Sign in button: `get_by_role("button", name="Sign in")`
- Error message: `page.get_by_role("alert")` or `div[role='alert']`

### OTP page (`/otp`)

- OTP form: `features/auth/components/OtpForm.tsx`

### Dashboard sidebar links

- `get_by_role("link", name="Lead Bucket")`
- `get_by_role("link", name="My Leads")`
- `get_by_role("link", name="My Deals")` — Sales Frontend
- `get_by_role("link", name="Sales Backend")`
- `get_by_role("link", name="Compliance")`

### Lead detail tabs

Tabs use `role="tab"` with `data-state="active"` on the active one:

- `get_by_role("tab", name="Profile")`
- `get_by_role("tab", name="Notes")`
- `get_by_role("tab", name="Documents")`
- `get_by_role("tab", name="Mortgage Snapshot")`
- `get_by_role("tab", name="DLO")`
- `get_by_role("tab", name="Appraisal Order")`
- `get_by_role("tab", name="Submitted")`
- `get_by_role("tab", name="Approved")`
- `get_by_role("tab", name="Signed")`
- `get_by_role("tab", name="Signed Closed")` — Compliance only

### Profile sub-tabs

- `get_by_role("tab", name="Personal Information")`
- `get_by_role("tab", name="General Information")`
- `get_by_role("tab", name="Mortgage Information")`

### Lead header action buttons

- `get_by_role("button", name="Not Proceeding")`
- `get_by_role("button", name="Move to Sales")`
- `get_by_role("button", name="Sent Application")`
- `get_by_role("button", name="Push to Scarlett")`
- `get_by_role("button", name="Home Appraised")`

### Compliance form tabs

- `get_by_role("tab", name="Compliance Form")`
- `get_by_role("tab", name="Signed Form")`

### Toast notifications (via sonner)

Sonner renders toasts outside normal DOM flow. Use:

- `page.get_by_text("<message text>")` — for text assertions
- `page.locator('[data-sonner-toast]')` — for container

### Kanban/List toggle

- `get_by_role("button", name="Kanban")` / `get_by_role("button", name="List")`

### URL patterns for tests

| Page                     | URL                                    |
| ------------------------ | -------------------------------------- |
| Login                    | `/login`                               |
| Dashboard                | `/`                                    |
| Lead Bucket              | `/lead-bucket`                         |
| My Leads                 | `/my-leads`                            |
| Sales Frontend           | `/sales`                               |
| Sales Backend            | `/sales-backend`                       |
| Compliance               | `/compliance`                          |
| Lead detail (sales)      | `/sales/<uuid>?tab=<tab-value>`        |
| Lead detail (compliance) | `/compliance/<uuid>?tab=signed-closed` |
| Create Lead              | `/create-lead`                         |
| Edit Lead                | `/edit-lead/<uuid>?tab=client-info`    |

---

## 18. Integration Points for Automation

### Session auth pattern (already implemented in conftest.py)

Login once per session per role via `admin_auth_state`, `fe_agent_auth_state`, and `be_agent_auth_state` → reuse `storage_state` in `admin_page`, `fe_agent_page`, and `be_agent_page`. The `auth_token` cookie is captured and replayed. `authenticated_page` is an alias for Admin.

### Bucket navigation pattern

Use `utils/entity_navigation.py` — constants `LEAD_BUCKET`, `MY_LEADS_BUCKET`, `MY_DEALS_BUCKET`, `SALES_BACKEND_BUCKET` with `open_bucket_record(page, bucket, record_name)`.

### Workflow verification pattern

Stage transitions and tab visibility are verified via `WorkflowVerification` + `workflow_expectations.py` (CRM-derived). Assertions belong in helpers/tests, not page objects.

### Tab navigation pattern

Navigate to a tab using the URL: `page.goto(BASE_URL + "/sales/<id>?tab=mortgage-snapshot")` — this is more reliable than clicking tabs because the URL drives the active tab state.

### Dynamic field visibility

Tabs like `dlo` only appear if the lead has `dlo.vfliNo` set. Test data must use a lead known to have DLO data to test that tab.

### Lead ID sourcing

Lead UUIDs for test data are hardcoded in `test_page_data/` files (e.g. `"Donovan Mattis"` by name, `"Steven Wilson mark"` for notes). Navigate by name using `get_by_role("link", name=<lead_name>)`.

### RBAC tab gating

Tabs inside `{hasFullAccess && ...}` only render if the authenticated user is the assigned agent or an admin. Test credentials must be the assigned agent or an admin account.
