PROMPTS.md

1. Repository Analysis
2. Feature Planning
3. New Automation
4. Existing Feature Enhancement
5. Bug Fixing
6. Locator Management
7. Page Object
8. Test Generation
9. Test Data
10. Assertions
11. Refactoring
12. Code Review
13. Performance
14. Framework Maintenance
15. Documentation
16. Git / PR Review
17. Learning / Explanation
18. Emergency Prompts
19. AI Collaboration
20. Daily Quick Prompts

# AI Prompt Library

These prompts assume:

- Cursor Rules are enabled.
- `STANDARDS.md` has been loaded.
- `PROJECT_CONTEXT.md` exists.
- Context loading order from `README.md` has been followed.

Do not repeat project rules in prompts.

---

# 1. Repository Analysis

## Analyze Repository

Analyze the repository before responding.

Understand:

- project architecture
- page objects
- tests
- fixtures
- helpers
- utilities
- configuration
- reusable components

Do not modify code.

Return only your findings.

---

## Analyze Feature

Analyze the implementation of <feature>.

Identify:

- related page objects
- related tests
- reusable methods
- reusable locators
- fixtures
- helpers
- dependencies

Do not modify code.

---

## Explain Workflow

Explain how <feature> works.

Focus only on:

- business flow
- page objects
- fixtures
- reusable components

Keep the explanation concise.

---

## Find Existing Implementation

Search the repository for existing implementation related to <feature>.

Return:

- matching files
- reusable methods
- reusable helpers
- reusable locators

Do not generate code.

---

## Architecture Review

Review the automation architecture.

Identify:

- duplicated logic
- inconsistent patterns
- reusable opportunities
- maintainability issues

Do not modify code.

---

# 2. Feature Planning

## Create Implementation Plan

Create an implementation plan for <feature>.

Include:

- files to modify
- methods to create
- reusable methods
- reusable fixtures
- reusable helpers

Do not generate code.

---

## Automation Strategy

Create the automation strategy for <feature>.

Include:

- page object updates
- test updates
- validation points
- reusable components

Do not write code.

---

## Test Coverage Plan

Create test scenarios for <feature>.

Include:

- happy path
- negative cases
- edge cases
- validation cases

Do not implement tests.

---

## Risk Analysis

Analyze implementation risks for <feature>.

Highlight:

- fragile locators
- duplicated logic
- synchronization risks
- reusable opportunities

Do not modify code.

---

# 3. New Automation

## Standard

Implement automation for <feature>.

Requirements:

- Analyze repository first.
- Reuse existing page objects.
- Reuse existing fixtures.
- Reuse helper methods.
- Search before creating anything.
- Generate minimal changes.

Output:

Only modified code.

---

## Page Objects Only

Implement only the Page Object changes required for <feature>.

Requirements:

- Do not write tests.
- Reuse existing methods.
- Keep methods reusable.
- Do not modify unrelated code.

Output:

Only modified page objects.

---

## Tests Only

Generate pytest tests for <feature>.

Requirements:

- Reuse authenticated_page.
- Reuse fixtures.
- Keep assertions inside tests.
- Follow existing project style.

Output:

Only test code.

---

## Locators Only

Generate only the required locators for <feature>.

Requirements:

- Search existing locators first.
- Reuse locator chains.
- Prefer accessibility locators.

Output:

Locator changes only.

---

## Continue Existing Feature

Continue implementing <feature>.

Do not restart implementation.

Reuse existing work.

Implement only missing functionality.

---

## Minimal Implementation

Implement only what is necessary for <feature>.

Do not refactor.

Do not optimize.

Do not modify unrelated files.

---

## Extend Existing Feature

Extend the existing implementation of <feature>.

Preserve current behaviour.

Generate minimal changes.

---

# 4. Existing Feature Enhancement

## Add Validation

Add validation for <feature>.

Reuse existing validation methods.

Keep assertions inside tests.

---

## Add Negative Tests

Generate negative test cases for <feature>.

Reuse existing setup.

Generate tests only.

---

## Improve Existing Implementation

Improve <feature>.

Focus on:

- readability
- reuse
- maintainability

Preserve behaviour.

---

## Split Large Method

Split large methods into reusable page methods.

Do not change functionality.

---

## Reuse Existing Methods

Refactor <feature> to maximize reuse.

Avoid duplicate business logic.

---

# 5. Bug Fixing

## Standard Bug Fix

Fix the following issue.

<describe issue>

Requirements:

- Find root cause first.
- Preserve architecture.
- Generate smallest possible fix.
- Avoid workarounds.

Output:

Modified code only.

---

## Failed Test

The following test is failing.

<paste error>

Find:

- root cause
- affected implementation

Fix only the required code.

---

## Root Cause Only

Analyze this failure.

Explain:

- why it happens
- affected files
- possible solutions

Do not write code.

---

## Flaky Test

Fix the flaky behaviour.

Focus on:

- synchronization
- waits
- unstable locators

Avoid unnecessary delays.

---

## Timeout Issue

Fix timeout failures.

Reuse existing waits.

Avoid wait_for_timeout().

---

## Locator Failure

Fix the failing locator.

Prefer accessibility locators.

Reuse existing locator chains.

---

## Regression Bug

Fix the regression without changing existing behaviour.

Generate minimal changes.

---

## Verify Bug Fix

Review the proposed fix.

Verify:

- root cause addressed
- no duplicated code
- no architecture violations
- no unnecessary changes

Do not rewrite code.

---

# 6. Locator Management

## Generate New Locators

Generate locators for <feature>.

Requirements

- Search existing locators first.
- Reuse existing locator chains.
- Prefer:
  1. get_by_role()
  2. get_by_label()
  3. get_by_placeholder()
  4. get_by_test_id()
  5. get_by_text()
- Use CSS only if necessary.
- XPath only as a last resort.

Output

Only locator code.

---

## Improve Existing Locators

Improve locator reliability for <feature>.

Requirements

- Replace unstable locators.
- Preserve existing behaviour.
- Keep locators readable.
- Do not modify unrelated code.

Output

Only modified locator code.

---

## Review Locators

Review the locators in the selected file.

Identify

- duplicate locators
- fragile selectors
- XPath that can be removed
- better accessibility locators
- opportunities for locator reuse

Do not modify code.

---

## Convert Locators

Convert the selected locators to the preferred locator strategy.

Preserve behaviour.

Do not modify unrelated code.

---

## Remove Duplicate Locators

Find duplicate locators.

Merge them into reusable locators.

Generate minimal changes.

---

# 7. Page Object

## Create Page Methods

Create reusable page methods for <feature>.

Requirements

- One business action per method.
- Keep methods small.
- Reuse existing methods.
- No assertions.
- No hardcoded data.

Output

Only page object code.

---

## Extend Existing Page

Extend the existing Page Object.

Do not rewrite the page.

Generate only the required methods.

---

## Review Page Object

Review this Page Object.

Check for

- duplicated methods
- long methods
- assertions
- hardcoded values
- poor naming
- missing reuse

Do not modify code.

---

## Refactor Page Object

Improve this Page Object.

Goals

- improve readability
- improve reuse
- reduce duplication

Preserve behaviour.

---

## Split Large Methods

Split large page methods into reusable methods.

Do not change behaviour.

---

## Extract Reusable Methods

Find duplicated business actions.

Extract reusable page methods.

Generate minimal changes.

---

## Convert to Existing Pattern

Update this page so it matches the project's existing Page Object style.

Do not change functionality.

---

# 8. Test Generation

## Generate Tests

Generate pytest tests for <feature>.

Requirements

- Reuse authenticated_page.
- Reuse fixtures.
- Keep assertions inside tests.
- Follow project naming.
- One scenario per test.

Output

Only tests.

---

## Happy Path

Generate happy path tests for <feature>.

Reuse existing setup.

---

## Negative Tests

Generate negative test cases for <feature>.

Reuse existing fixtures.

---

## Edge Cases

Generate edge case tests for <feature>.

Focus on business validation.

---

## Parametrize Tests

Convert repetitive tests into pytest.parametrize.

Reuse existing data.

---

## Improve Tests

Review and improve the selected tests.

Focus on

- readability
- reuse
- maintainability

Do not change behaviour.

---

## Remove Duplicate Test Logic

Extract duplicated business actions into reusable page methods.

Generate minimal changes.

---

# 9. Test Data

## Generate Test Data

Generate test data for <feature>.

Requirements

- Reuse RandomGenerator.
- Reuse existing data modules.
- Avoid hardcoded values.

Output

Only test data.

---

## Generate Valid Cases

Generate valid test data only.

Follow existing project style.

---

## Generate Invalid Cases

Generate negative test data.

Cover business validation.

---

## Extend Existing Data

Extend the existing test data module.

Do not duplicate values.

---

## Review Test Data

Review the selected data.

Check for

- duplicates
- hardcoded values
- reuse opportunities

Do not modify code.

---

# 10. Assertions

## Generate Assertions

Generate assertions for <feature>.

Requirements

- Assertions belong only inside tests.
- Reuse existing validation helpers.
- Reuse Toast where appropriate.

Output

Only assertions.

---

## Improve Assertions

Improve the existing assertions.

Make failures easier to understand.

---

## Review Assertions

Review assertions.

Check

- unnecessary assertions
- duplicated assertions
- weak validation
- missing business verification

Do not modify code.

---

## Replace Assertions

Replace weak assertions with stronger business assertions.

Preserve behaviour.

---

## Assertion Strategy

Suggest a better assertion strategy.

Do not generate code.

---

# 11. Refactoring

## Safe Refactor

Refactor the selected implementation.

Requirements

- Preserve behaviour.
- Improve readability.
- Reduce duplication.
- Reuse existing methods.
- Generate minimal changes.

Output

Only modified code.

---

## Remove Duplicate Code

Find duplicated code.

Extract reusable methods.

Do not change functionality.

---

## Improve Reusability

Improve reuse in <feature>.

Search for similar implementations.

Merge duplicated logic where appropriate.

---

## Simplify Implementation

Simplify the selected implementation.

Keep the same behaviour.

Reduce unnecessary complexity.

---

## Modernize Page Object

Update the selected Page Object to match the current project standards.

Do not rewrite the file.

Generate only necessary changes.

---

## Reduce Technical Debt

Identify technical debt in the selected files.

Prioritize improvements.

Do not modify code.

---

## Standardize Code Style

Update the selected implementation to match the project's existing style.

Preserve behaviour.

---

## Refactor for Maintainability

Improve long-term maintainability.

Focus on

- readability
- reuse
- consistency

---

# 12. Code Review

## Full Review

Review the selected implementation.

Check for

- duplicated methods
- duplicated locators
- duplicated tests
- unnecessary waits
- flaky Playwright patterns
- poor naming
- hardcoded values
- architecture violations

Return findings ordered by priority.

Do not modify code.

---

## Architecture Review

Review the architecture.

Focus on

- POM consistency
- separation of concerns
- reusable components
- maintainability

Do not generate code.

---

## Page Review

Review the selected Page Object.

Check

- long methods
- business logic leakage
- assertions
- duplicated actions
- locator quality

Do not modify code.

---

## Test Review

Review the selected tests.

Check

- readability
- business coverage
- duplicated setup
- duplicated assertions
- flaky patterns

Do not modify code.

---

## Review AI Generated Code

Review the AI-generated implementation.

Verify

- follows project standards
- reuses existing code
- no duplicated logic
- no unnecessary changes

Suggest improvements only.

---

## Regression Review

Review the changes.

Identify possible regressions.

Do not modify code.

---

## Pre-Merge Review

Review all modified files before merge.

Check

- maintainability
- project standards
- code duplication
- architecture

Return a checklist.

---

# 13. Performance

## Improve Performance

Optimize the selected implementation.

Focus on

- execution speed
- fewer Playwright actions
- reusable methods
- unnecessary waits

Preserve behaviour.

---

## Remove Slow Operations

Identify slow operations.

Suggest improvements.

Do not modify code.

---

## Reduce Playwright Actions

Reduce unnecessary clicks, fills, waits and page interactions.

Keep behaviour unchanged.

---

## Improve Test Execution

Improve execution speed.

Reuse existing setup.

Reduce duplicate work.

---

## Performance Review

Review this implementation for performance issues.

Do not modify code.

---

# 14. Framework Maintenance

## Framework Audit

Audit the automation framework.

Check

- duplicated utilities
- duplicated helpers
- inconsistent patterns
- missing abstractions
- architecture issues

Return prioritized findings.

---

## Reuse Audit

Identify opportunities to reuse

- fixtures
- page methods
- utilities
- locators
- helpers

Do not modify code.

---

## Folder Review

Review the project structure.

Suggest improvements.

Do not move files.

---

## Naming Review

Review naming conventions.

Check

- files
- classes
- methods
- fixtures
- test names

Do not modify code.

---

## Standards Compliance

Verify that the selected implementation follows `STANDARDS.md`.

List violations only.

---

# 15. Documentation

## Update Documentation

Update documentation for <feature>.

Document only what exists.

Do not invent implementation.

---

## Update PROJECT_CONTEXT

Review PROJECT_CONTEXT.md.

Update only outdated information.

Do not modify code.

---

## Explain Feature

Explain how <feature> works.

Focus on

- business flow
- reusable methods
- test flow

Keep concise.

---

## Generate Feature Documentation

Generate documentation for <feature>.

Include

- workflow
- page objects
- tests
- reusable methods

Do not modify code.

---

## Documentation Review

Review documentation.

Identify

- outdated sections
- missing information
- inconsistencies

Do not rewrite everything.

Return recommendations only.

---

# 16. Git / Pull Request Review

## Review Current Changes

Review all modified files.

Verify:

- project standards
- duplicated code
- reusable methods
- reusable locators
- maintainability

Return findings only.

---

## Review Before Commit

Review the current changes before commit.

Check

- formatting
- naming
- duplicated code
- unnecessary changes
- missing cleanup

Do not modify code.

---

## Review Pull Request

Review this Pull Request.

Focus on

- correctness
- maintainability
- architecture
- Playwright best practices

Suggest improvements only.

---

## Generate Commit Summary

Generate a concise Git commit message for the current changes.

Follow Conventional Commits.

Return only the commit message.

---

## Generate Pull Request Description

Generate a Pull Request description.

Include

- summary
- changes
- testing performed
- risks

Do not invent information.

---

# 17. Learning / Explanation

## Explain Selected Code

Explain the selected implementation.

Focus on

- business flow
- project structure
- reusable methods
- design decisions

Keep the explanation beginner-friendly.

---

## Teach Me

Teach me how <feature> works in this project.

Use the existing implementation as the reference.

Do not explain generic Playwright concepts unless necessary.

---

## Compare Two Implementations

Compare these implementations.

Highlight

- advantages
- disadvantages
- maintainability
- readability

Recommend the better approach.

---

## Explain AI Decisions

Explain why you generated this implementation.

Reference existing project patterns where applicable.

---

## Explain Failure

Explain why this test failed.

Focus on the root cause.

Suggest the best fix.

Do not write code.

---

# 18. AI Collaboration

## Plan Before Coding

Before writing code:

Analyze the repository.

Create an implementation plan.

Wait for my approval before generating code.

---

## Implement Step by Step

Break the implementation into small steps.

Complete only the first step.

Wait for approval before continuing.

---

## Think Before Coding

Analyze first.

List possible approaches.

Recommend the best approach.

Wait for confirmation.

---

## Ask Questions First

If any requirement is unclear,

ask questions before writing code.

Never assume business behaviour.

---

## Verify Before Responding

Before generating code verify:

- existing implementation
- reusable methods
- reusable locators
- reusable helpers
- fixtures

Generate code only after verification.

---

## Self Review

After generating code,

review your own implementation.

Check

- duplication
- architecture
- maintainability
- project standards

Improve the solution before responding.

---

## Minimal Change Mode

Generate the smallest possible implementation.

Avoid refactoring.

Avoid unnecessary formatting changes.

Modify only what is required.

---

## Read Only Mode

Analyze the repository.

Do not modify code.

Return findings only.

---

# 19. Recovery Prompts

## AI Went in the Wrong Direction

The previous solution does not match the project.

Analyze the repository again.

Reuse existing implementation.

Generate a new solution with minimal changes.

---

## Too Much Code Generated

Reduce the implementation.

Keep only the required changes.

Remove unnecessary code.

---

## Too Many Modified Files

Reduce the scope.

Modify only the files required for this task.

---

## Wrong Architecture

Update the solution to follow the project's existing architecture.

Reuse existing patterns.

---

## Over-Engineered Solution

Simplify the implementation.

Use the existing project style.

Avoid unnecessary abstractions.

---

# 20. Personal Favorites

These are the prompts intended for daily use.

Implement <feature>.

---

Continue implementing <feature>.

---

Fix <bug>.

---

Review this file.

---

Generate tests for <feature>.

---

Generate page methods only.

---

Improve locator stability.

---

Analyze this module.

---

Explain this implementation.

---

Create an implementation plan.

---

Review AI-generated code.

---

Find the root cause only.

---

Optimize this implementation.

---

Refactor this page.

---

Update PROJECT_CONTEXT.md.

---

Review current changes before commit.

---

Generate Pull Request description.

---

Teach me how this feature works.

---

# 21. Examples

Golden patterns for this repository. Adapt — do not copy literally.

---

## Page Object Structure

```python
class LeadEditPage:

    def __init__(self, page):
        self.page = page
        self.first_name = page.get_by_label("First Name")
        self.last_name = page.get_by_label("Last Name")
        self.save_button = page.get_by_role("button", name="Save")
```

- Store all locators in `__init__`.
- Use descriptive names.
- Prefer accessibility locators.
- No assertions. No business validation.

---

## One Business Action Per Method

```python
def fill_personal_information(self, data):
    self.first_name.fill(data["first_name"])
    self.last_name.fill(data["last_name"])
```

- One responsibility per method.
- Small methods.
- No assertions.

---

## Compose Small Methods

```python
def create_lead(self, data):
    self.fill_personal_information(data)
    self.fill_contact_information(data)
    self.fill_property_information(data)
    self.save()
```

- High-level business flow.
- Reuse smaller methods.
- No duplicated code.

---

## Tests Drive Validation

```python
def test_create_lead(authenticated_page):
    lead = CreateLeadPage(authenticated_page)
    lead.create_lead(data)
    Toast(authenticated_page).assert_message("Lead created successfully.")
```

- Assertions stay in tests.
- Page Objects perform actions.
- Tests verify results.

---

## Reuse Fixtures

```python
def test_edit_lead(authenticated_page):
    page = LeadEditPage(authenticated_page)
    page.open_lead(name)
    page.update_phone(phone)
```

- Use existing fixtures.
- Never login manually inside tests.

---

## Locator Priority

```python
page.get_by_role(...)       # 1st choice
page.get_by_label(...)      # 2nd
page.get_by_placeholder(...)# 3rd
page.get_by_test_id(...)    # 4th
page.get_by_text(...)       # 5th
# CSS only if required
# XPath only as last resort
```

---

## Google Autocomplete Pattern

```python
field.fill(partial_text)
field.press(" ")
field.press("Backspace")
field.press("ArrowDown")
field.press("Enter")
```

Do not invent a different solution.

---

## Config Usage

```python
Config.BASE_URL
Config.TIMEOUT
Config.USERNAME
Config.PASSWORD
```

Never hardcode these values.

---

## Logging

```python
logger.info("Opening Lead Edit page.")
logger.info("Saving lead.")
```

Log only important business actions. Not every click.

---

## Validation Helpers

```python
Toast(page).assert_message("Lead created successfully.")
Validations(page).assert_field_error("Email", "Invalid email address")
```

Do not duplicate validation logic.

---

## Naming Reference

Page methods: `fill_contact_information()`, `save()`, `search_lead()`, `open_lead()`, `delete_note()`

Tests: `test_create_lead()`, `test_edit_lead()`, `test_add_note()`

Locators: `save_button`, `email_input`, `phone_input`, `mortgage_type_dropdown`

---

## Waiting Strategy

```python
# Preferred
expect(locator).to_be_visible()
locator.wait_for()

# Avoid
page.wait_for_timeout(3000)
time.sleep(3)
```

Reuse `BasePage` wrappers when available.

---

## Stage Transition (New Tab / Dialog) Pattern

```python
# Stage update dialog
page.get_by_role("alertdialog").wait_for(state="visible")
page.get_by_role("button", name="Move to Next Stage").click()
Toast(page).assert_message("Lead moved to Mortgage Snapshot successfully")

# External app in new tab
with context.expect_page() as new_page_info:
    page.get_by_role("button", name="NTP Application").click()
new_page = new_page_info.value
new_page.wait_for_load_state("networkidle")
```

---

## AI Pre-Code Workflow

1. Analyze the repository.
2. Search for existing implementation.
3. Reuse existing code.
4. Modify only required files.
5. Review generated code.
6. Return the final implementation.

---

## Code Review Checklist

Before responding, verify:

- No duplicated code or locators
- No hardcoded values
- No assertions in Page Objects
- Reusable methods and fixtures
- Project naming followed
- Minimal diff generated
