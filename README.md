# CRM_Automation
# Automation Framework

This repository contains an automated end-to-end testing framework for a **CRM (Customer Relationship Management)** system, built using **Python**, **Playwright**, and **Pytest**. The project follows the **Page Object Model (POM)** design pattern to ensure scalability, maintainability, and reusability of test components.

---

## 🛠️ Tech Stack & Tools

- **Programming Language:** Python
- **Automation Tool:** Playwright (Python)
- **Test Runner:** Pytest
- **Design Pattern:** Page Object Model (POM)
- **Reporting:** Pytest HTML / Allure Reports
- **Configuration:** Custom pytest/env configuration setup

---

## 🏗️ Project Architecture & Features

- **Page Object Model (POM):** Clean separation between page elements/actions and test logic for easier maintenance.
- **Reusable Utilities:** Common functions for actions, assertions, and handling dynamic UI elements.
- **Test Data Management:** Parameterized and structured test data handling for dynamic scenarios.
- **Detailed Reporting:** Generates comprehensive test execution reports with execution status and failure logs.
- **Flexible Configuration:** Environment-based configurations for smooth setup across different test environments.

---

## 📂 Directory Structure

```text
├── config/              # Environment configurations & setup
├── pages/               # Page Object classes (POM structure)
├── tests/               # Test cases & suites
├── utils/               # Helper methods & custom utility functions
├── test_data/           # Static/dynamic test data files
├── reports/             # Generated execution reports
├── pytest.ini           # Pytest configuration settings
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
