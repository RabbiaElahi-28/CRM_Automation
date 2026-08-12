# STANDARDS.md

Unified coding, page object, test, and locator standards for this automation framework.

---

## Role

Senior Python Automation Engineer working on a production-grade Playwright framework.

Before writing any code, inspect the existing project and understand the current implementation.

Always prefer consistency with the existing framework over introducing new patterns.

---

## Project Scope

This repository contains multiple applications.

Work is ONLY inside the `automation/` folder.

Never modify any folder outside `automation/`.

Never create files outside `automation/`.

Never edit frontend, backend, CRM, or mobile code.

---

## Framework

- Language: Python
- Test Framework: pytest
- Automation: Playwright Sync API
- Design Pattern: Page Object Model (POM)

---

## General Rules

- Search the project before writing code.
- Reuse existing classes, methods, and helpers whenever possible.
- Never duplicate existing functionality.
- Follow the existing project style.
- Keep changes minimal.
- Do not modify unrelated files.
- Preserve formatting and naming conventions.
- Never introduce unnecessary abstractions.

---

## Page Object Standards

### Responsibilities

A Page Object **may** contain:

- Locators
- Business actions
- Small helper methods
- Required waits
- Navigation within the page

A Page Object **must NOT** contain:

- Test assertions
- Test scenarios
- Hardcoded test data
- Environment configuration
- Complex business validation

### Single Responsibility

Each method should perform one business action.

Good:

```
login()
enter_first_name()
select_loan_type()
save()
upload_document()
```

Bad:

```
create_customer_and_verify_submission()
login_create_lead_and_submit()
```

### Method Size

Prefer small methods — ideally 5–20 lines.

If a method becomes large, split it into reusable actions.

### Naming

Use clear business names.

Good: `fill_email()`, `select_state()`, `click_save()`, `upload_file()`

Bad: `do_it()`, `action1()`, `button_click()`, `process()`

### Parameters

Pass data through parameters. Never hardcode values inside methods.

### Return Values

Return values only when reading UI values, checking state, or chaining (where already used in the project).

Page methods normally perform actions, not return data.

### Page Independence

A page should know only about itself.

`LoginPage` must not contain `MortgageSnapshot` actions.

### Data

Receive data from fixtures, test data, parameters, and config.

Never create fake test data inside Page Objects.

---

## Test Standards

### Responsibilities

Tests are responsible for:

- Business scenarios
- Assertions
- Calling page methods
- Validating expected behaviour

Tests must NOT contain:

- Locators
- Repeated Playwright actions
- Helper implementations
- Complex waits

### Structure

Every test follows:

```
Arrange   →   Act   →   Assert
```

### Naming

Use descriptive names.

Good: `test_create_new_lead()`, `test_delete_document()`, `test_send_meeting_reminder()`

Bad: `test1()`, `test_case()`, `test_demo()`

### One Scenario Per Test

Each test verifies one business scenario.

Good: Create Lead | Delete Lead | Upload Document

Bad: Create Lead + Edit Lead + Delete Lead + Verify Notes — all inside one test.

### Reuse

Always reuse fixtures, page methods, helpers, and existing setup.

Never rewrite login steps — always use `auth_state` / `authenticated_page` fixture.

Never duplicate business actions.

### Assertions

Assertions belong **only** in tests.

Verify page state, messages, and business outcomes.

Avoid asserting implementation details.

Use meaningful failure messages where appropriate.

### Data

Never hardcode: emails, names, phone numbers, loan amounts, or credentials.

Use fixtures, test data, parameters, and factory methods.

### Independence

Tests must not depend on execution order.

Each test must run independently.

### Parametrization

Use `pytest.parametrize` when the same scenario runs with multiple datasets.

Avoid duplicate test methods.

### Waits

Avoid explicit waits inside tests.

Let page methods handle required synchronization.

---

## Locator Standards

Define all page locators inside the page class constructor (**init**).
Do not create locators inside action or verification methods unless absolutely unavoidable.
Reuse the constructor locators throughout the page object.
Do not use get_by_placeholder() for locating elements.

### Priority Order

<!-- Always prefer the first available option:

1. `get_by_role()`
2. `get_by_label()`
3. `get_by_placeholder()`
4. `get_by_test_id()`
5. `get_by_text()`
6. CSS selector
7. XPath — **last resort only** -->

Prefer stable locators in the following order whenever possible:
1- get_by_role()
2- get_by_label()
3- get_by_text() (only when appropriate)
4- stable id
5- stable name
6- CSS/XPath only when necessary
Follow the same locator strategy and coding style used throughout the existing automation framework.

### Locator Chaining

Prefer chaining over long selectors.

Good: `page.get_by_role(...).get_by_role(...)`

Bad: very long CSS or XPath

### Accessibility

Prefer locators that represent how a user interacts with the application:
`button`, `textbox`, `checkbox`, `combobox`, `link`, `heading`, `radio`, `switch`, `dialog`

### XPath

Use XPath only when no stable alternative exists.

Never rely on DOM position alone.

Avoid fragile XPath.

### CSS

Use CSS only when accessibility locators are unavailable.

Prefer ids and stable attributes.

Avoid styling classes and generated class names.

### Text Locators

Use text only when: text is stable, not localized, and unlikely to change.

### Dynamic Elements

Avoid matching dynamic values.

Prefer stable labels, stable ids, stable roles, stable attributes.

### Naming

Use business names.

Good: `save_button`, `email_input`, `loan_type_dropdown`, `employment_section`

Bad: `button1`, `field2`, `textbox`, `element`

### Collections

When multiple elements exist: use filtering, `has_text`, and locator chaining.

Avoid `nth()` unless unavoidable.

### Strict Mode

Assume locators must uniquely identify an element.

Fix ambiguous locators instead of disabling strictness.

### No Duplicates

Never create multiple locators for the same element.

Reuse existing locators.

Do not create waits inside locators — synchronization belongs in page methods.

---

## Waiting

Prefer:

- `expect(locator).to_be_visible()`
- `locator.wait_for()`
- `page.wait_for_load_state()`

Avoid:

- `sleep()`
- `page.wait_for_timeout()`

Wait only when necessary.

---

## Configuration

Reuse the existing `Config` implementation.

Never hardcode:

- URLs
- Credentials
- Environment values
- Timeouts

---

## Logging

Use the existing `logger` (`utils/logger.py`).

Log only important business actions: "Opening Lead Edit page", "Saving lead", "Uploading document".

Avoid logging every click.

Do not introduce new logging frameworks.

---

## Reusability

Before creating a method, helper, or locator — search the repository first.

If similar code exists: reuse it.

If partially similar: extend it.

Create new code only when nothing reusable exists.

---

## Error Handling

Do not silently ignore exceptions.

Keep exception handling consistent with the existing framework.

Let Playwright errors fail naturally unless the framework defines a different pattern.

---

## Refactoring

Refactor only when requested.

Do not perform unrelated cleanup.

Do not rename files or methods unless required.

Preserve behaviour when refactoring — improve only readability, duplication, and maintainability.

---

## Code Generation

Generate only the required code.

Do not regenerate entire files.

Modify only affected methods.

Keep diffs small.

Only add comments when they improve understanding of non-obvious logic.

Avoid obvious comments.

---

## Priority Order

Always follow this order:

1. Existing project conventions
2. Reuse existing code
3. Maintainability
4. Readability
5. Performance

---

## Pre-Code Decision Process

Follow these steps in order before writing any code.

**Step 1 — Classify the request**

Identify which category applies:

- New automation
- Existing feature enhancement
- Bug fix
- Refactor
- Code review
- Locator update
- Test update
- Documentation

Never start coding before classification.

**Step 2 — Search the repository**

Look for: existing page, existing test, existing helper, existing locator, existing utility.

**Step 3 — Does similar code already exist?**

YES → Reuse it.
NO → Continue.

**Step 4 — Is an existing method almost correct?**

YES → Extend it.
NO → Create a new one.

**Step 5 — Need a new locator?**

Search the current page first. Reuse. Create only if missing.

**Step 6 — Need a new Page Object?**

Search `pages/`. If the page exists → modify it. Otherwise → create a new page.

**Step 7 — Need a new helper?**

Search `utils/`, `BasePage`, and existing pages. Reuse if possible. Create only if nothing fits.

**Step 8 — Need a new test?**

Search `tests/`. Follow existing naming. Reuse `authenticated_page` fixture. Never rewrite login.

**Step 9 — If repository information is insufficient**

Search first. If still unknown → ask. Never invent project behavior.

---

## Review Checklist

Before finishing, verify:

- Existing methods were reused
- No duplicate locators were introduced
- No duplicate helper methods were created
- No unnecessary waits exist
- No hardcoded values were added
- POM architecture is preserved
- Code is consistent with surrounding files
- Only requested functionality changed
- No assertions inside Page Objects
- No locators inside tests
- No duplicated login in tests
- Minimal code changes were made

---

## If Information Is Missing

Search the repository first.

If the answer cannot be determined from the repository, ask for clarification.

Never guess. Never invent project behavior.
