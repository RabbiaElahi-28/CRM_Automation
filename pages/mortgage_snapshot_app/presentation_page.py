from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pages.base_page import BasePage
from playwright.sync_api import Page, expect

from utils.config import Config
from utils.mortgage_snapshot_display import (
    MortgageSnapshotDisplayExpectations,
    format_currency_display,
    ms_app_credit_rating_matches,
    normalize_currency,
    normalize_percent,
    normalize_whitespace,
    normalize_years,
)


@dataclass
class SlideDiscoveryEntry:
    index: int
    slide_type: str
    fingerprint: str
    sample_text: str


@dataclass
class PresentationDiscoveryReport:
    slide_count: int
    slides: list[SlideDiscoveryEntry] = field(default_factory=list)
    click_zone: dict[str, float | int] = field(default_factory=dict)
    final_client_slide: dict[str, object] = field(default_factory=dict)
    flag_display: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "slide_count": self.slide_count,
            "slides": [asdict(s) for s in self.slides],
            "click_zone": self.click_zone,
            "final_client_slide": self.final_client_slide,
            "flag_display": self.flag_display,
        }


class MortgageSnapshotAppPresentationPage(BasePage):
    """Read-only slide presentation in the Mortgage Snapshot App."""

    NEXT_X_RATIO = 0.95
    PREV_X_RATIO = 0.05
    Y_RATIO = 0.5

    SLIDE_MARKERS = (
        ("welcome", re.compile(r"Welcome.*Mortgage Snapshot", re.I | re.S)),
        ("what_you_told_us", re.compile(r"what you told us", re.I)),
        ("credit_profile", re.compile(r"credit-score-number|Reported Flags", re.I)),
        ("debt_calculator", re.compile(r"Your debt calculator|landscape-debt-label", re.I)),
        ("mortgage_options", re.compile(r"opt-product-type|stars-row|Nuborrow Rating", re.I)),
        ("home_appraised", re.compile(r"ha-label|Minimum Value|Maximum Value", re.I)),
        ("final_client", re.compile(r"Here's how we move things forward|mp-prompt", re.I)),
    )

    def _is_locator_visible(self, locator) -> bool:
        if locator.count() == 0:
            return False
        try:
            return locator.first.is_visible()
        except Exception:
            return False

    def _is_final_client_slide(self) -> bool:
        return self._is_locator_visible(
            self.page.locator(".mp-prompt")
        ) and self._is_locator_visible(self.page.locator(".mp-point"))

    def _is_home_appraised_slide(self) -> bool:
        return self._is_locator_visible(self.page.locator(".ha-label"))

    def _is_mortgage_options_slide(self) -> bool:
        return self._is_locator_visible(self.page.locator("h3.opt-product-type"))

    def _is_debt_calculator_slide(self) -> bool:
        return self._is_locator_visible(self.page.locator(".landscape-debt-label"))

    def _is_credit_profile_slide(self) -> bool:
        return self._is_locator_visible(self.page.locator(".credit-score-number"))

    def go_to_welcome_slide(self, *, max_back: int = 8) -> None:
        """Rewind to the welcome slide from any position in the deck."""
        if self.detect_slide_type() == "welcome":
            return
        for _ in range(max_back):
            self.go_to_previous_slide()
            if self.detect_slide_type() == "welcome":
                return
        raise AssertionError(
            f"Welcome slide not reached after {max_back} back navigation(s); "
            f"detected {self.detect_slide_type()!r}, "
            f"sample: {self._slide_text()[:400]!r}"
        )

    def go_to_final_client_slide(self, *, max_advances: int = 3) -> None:
        """Advance until the final client slide is visible."""
        if self._is_final_client_slide():
            return
        for _ in range(max_advances):
            self.go_to_next_slide()
            if self._is_final_client_slide():
                return
        raise AssertionError(
            f"Final client slide not reached after {max_advances} advance(s); "
            f"detected {self.detect_slide_type()!r}, "
            f"sample: {self._slide_text()[:400]!r}"
        )

    def __init__(self, page: Page):
        super().__init__(page)
        self.presentation_root = page.locator(".font-ubuntu.h-full.w-full").first

    def wait_for_presentation(self) -> None:
        expect(self.presentation_root).to_be_visible(timeout=Config.TIMEOUT)
        self._wait_for_slide_stable()

    def _presentation_box(self) -> dict[str, float]:
        box = self.presentation_root.bounding_box()
        if not box:
            raise AssertionError("Presentation container has no bounding box")
        return box

    def go_to_next_slide(self) -> None:
        previous = self.detect_slide_type()
        box = self._presentation_box()
        self.page.mouse.click(
            box["x"] + box["width"] * self.NEXT_X_RATIO,
            box["y"] + box["height"] * self.Y_RATIO,
        )
        changed = self._wait_for_slide_change(previous)
        if changed == previous:
            self.presentation_root.focus()
            self.page.keyboard.press("ArrowRight")
            self._wait_for_slide_change(previous)

    def go_to_previous_slide(self) -> None:
        previous = self.detect_slide_type()
        box = self._presentation_box()
        self.page.mouse.click(
            box["x"] + box["width"] * self.PREV_X_RATIO,
            box["y"] + box["height"] * self.Y_RATIO,
        )
        changed = self._wait_for_slide_change(previous)
        if changed == previous:
            self.presentation_root.focus()
            self.page.keyboard.press("ArrowLeft")
            self._wait_for_slide_change(previous)

    def _wait_for_slide_stable(self, timeout_ms: int = 5000) -> None:
        self.page.wait_for_timeout(350)
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            pass

    def _wait_for_slide_change(self, previous: str, *, timeout_s: float = 6) -> str:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self._wait_for_slide_stable()
            current = self.detect_slide_type()
            if current != previous and current != "unknown":
                return current
            self.page.wait_for_timeout(250)
        return self.detect_slide_type()

    def _slide_text(self) -> str:
        if self.presentation_root.count() > 0:
            return normalize_whitespace(self.presentation_root.inner_text())
        return normalize_whitespace(self.page.locator("body").inner_text())

    def detect_slide_type(self) -> str:
        """Prefer visible slide markers — full inner_text retains prior slide copy."""
        if self._is_final_client_slide():
            return "final_client"
        if self._is_home_appraised_slide():
            return "home_appraised"
        if self._is_mortgage_options_slide():
            return "mortgage_options"
        if self._is_debt_calculator_slide():
            return "debt_calculator"
        if self._is_credit_profile_slide():
            return "credit_profile"
        text = self._slide_text()
        for slide_type, pattern in self.SLIDE_MARKERS:
            if slide_type in {
                "final_client",
                "home_appraised",
                "mortgage_options",
                "debt_calculator",
                "credit_profile",
            }:
                continue
            if pattern.search(text):
                return slide_type
        return "unknown"

    def discover_slides(self, *, max_slides: int = 10) -> PresentationDiscoveryReport:
        """Walk slides via edge clicks and record structure for tuning locators."""
        self.wait_for_presentation()
        box = self._presentation_box()
        report = PresentationDiscoveryReport(
            slide_count=0,
            click_zone={
                "container_x": box["x"],
                "container_y": box["y"],
                "container_width": box["width"],
                "container_height": box["height"],
                "next_click_x": box["x"] + box["width"] * self.NEXT_X_RATIO,
                "next_click_y": box["y"] + box["height"] * self.Y_RATIO,
                "prev_click_x": box["x"] + box["width"] * self.PREV_X_RATIO,
                "prev_click_y": box["y"] + box["height"] * self.Y_RATIO,
                "next_x_ratio": self.NEXT_X_RATIO,
                "prev_x_ratio": self.PREV_X_RATIO,
            },
        )

        seen: list[str] = []
        for index in range(max_slides):
            fingerprint = self.detect_slide_type()
            sample = self._slide_text()[:500]
            if fingerprint in seen:
                break
            seen.append(fingerprint)
            report.slides.append(
                SlideDiscoveryEntry(
                    index=index + 1,
                    slide_type=fingerprint,
                    fingerprint=fingerprint,
                    sample_text=sample,
                )
            )
            if fingerprint == "credit_profile" and not report.flag_display:
                report.flag_display = self._capture_flag_display()
            if fingerprint == "final_client":
                report.final_client_slide = self._capture_final_client_slide()
                report.slide_count = len(report.slides)
                return report
            self.go_to_next_slide()

        report.slide_count = len(report.slides)
        return report

    def _capture_flag_display(self) -> dict[str, list[str]]:
        flags = self.page.locator('p[style*="font-size: 17px"]')
        all_flags = [
            normalize_whitespace(flags.nth(i).inner_text()) for i in range(flags.count())
        ]
        if len(self._credit_columns()) > 1 and all_flags:
            split = len(all_flags) // 2
            return {"primary": all_flags[:split], "co_applicant": all_flags[split:]}
        return {"primary": all_flags, "co_applicant": []}

    def _capture_final_client_slide(self) -> dict[str, object]:
        label = self.page.locator(".mp-label").first
        points = self.page.locator(".mp-point")
        prompt = self.page.locator(".mp-prompt").first
        ctas = self.page.locator(".mp-cta")
        return {
            "label_visible": label.count() > 0 and label.is_visible(),
            "label_text": label.inner_text().strip() if label.count() else "",
            "point_count": points.count(),
            "point_texts": [normalize_whitespace(points.nth(i).inner_text()) for i in range(points.count())],
            "prompt_text": prompt.inner_text().strip() if prompt.count() else "",
            "cta_count": ctas.count(),
            "cta_texts": [normalize_whitespace(ctas.nth(i).inner_text()) for i in range(ctas.count())],
        }

    @staticmethod
    def write_discovery_report(report: PresentationDiscoveryReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    def _credit_columns(self) -> list[str]:
        """Split credit slide copy into primary / co-applicant columns."""
        parts = re.split(r"(?=Welcome,\s)", self._slide_text(), flags=re.I)
        return [part for part in parts if re.match(r"Welcome,\s", part.strip(), re.I)]

    def _credit_column_text(self, panel_index: int) -> str:
        columns = self._credit_columns()
        if panel_index >= len(columns):
            raise AssertionError(
                f"Credit column {panel_index} not found; saw {len(columns)} column(s)"
            )
        return columns[panel_index]

    def _panel_welcome_name_from_index(self, panel_index: int) -> str:
        column = self._credit_column_text(panel_index)
        match = re.search(r"Welcome,\s*(.+?)(?:\s+\d{3}\s|\s+Reported Flags)", column, re.I | re.S)
        if not match:
            match = re.search(r"Welcome,\s*(.+)", column, re.I)
        return normalize_whitespace(match.group(1)) if match else ""

    def _credit_panel_metrics(self, panel_index: int) -> tuple[str, str]:
        text = self._credit_column_text(panel_index)
        tds_match = re.search(r"(\d+)\s*%\s*TDS", text, re.I)
        util_match = re.search(r"(\d+)\s*%\s*Utilization", text, re.I)
        return (
            f"{tds_match.group(1)}%" if tds_match else "",
            f"{util_match.group(1)}%" if util_match else "",
        )

    def _credit_panel_flags(self, start: int, count: int) -> list[str]:
        flags = self.page.locator('p[style*="font-size: 17px"]')
        return [
            normalize_whitespace(flags.nth(i).inner_text())
            for i in range(start, start + count)
        ]

    def _panel_welcome_name(self, panel) -> str:
        welcome = panel.get_by_text(re.compile(r"Welcome,\s*", re.I)).first
        if welcome.count() == 0:
            return ""
        text = normalize_whitespace(welcome.inner_text())
        return text.replace("Welcome,", "").strip()

    def assert_welcome_slide(self, expectations: MortgageSnapshotDisplayExpectations) -> None:
        expect(self.page.get_by_text("Welcome", exact=False).first).to_be_visible()
        expect(self.page.get_by_text("Mortgage Snapshot", exact=False).first).to_be_visible()
        body = self._slide_text()
        assert expectations.introduction_script in body, (
            f"Introduction script not found in welcome slide: {expectations.introduction_script!r}"
        )

    def assert_welcome_slide_stale_removed(
        self,
        *,
        old_intro_script: str,
        new_intro_script: str,
    ) -> None:
        """Regression: confirm updated intro replaced the prior value in the app."""
        self.wait_for_presentation()
        assert self.detect_slide_type() == "welcome"
        body = self._slide_text()
        assert new_intro_script in body, (
            f"Updated intro {new_intro_script!r} not found in welcome slide"
        )
        if old_intro_script and old_intro_script != new_intro_script:
            assert old_intro_script not in body, (
                f"Stale intro {old_intro_script!r} still visible after save"
            )

    def assert_what_you_told_us_slide(
        self, expectations: MortgageSnapshotDisplayExpectations
    ) -> None:
        expect(self.page.get_by_text(re.compile(r"what you told us", re.I)).first).to_be_visible()
        expect(
            self.page.get_by_text(
                re.compile(rf"{re.escape(expectations.applicant_first_name)}, here's", re.I)
            ).first
        ).to_be_visible()
        bubbles = self.page.locator(".chat-bubble .messages-text, .chat-bubble p")
        texts = [normalize_whitespace(bubbles.nth(i).inner_text()) for i in range(bubbles.count())]
        joined = " | ".join(texts)
        for expected in (
            expectations.first_need,
            expectations.first_client_response,
            expectations.second_need,
            expectations.second_client_response,
        ):
            assert expected in joined, f"Expected {expected!r} in chat bubbles, got: {joined!r}"

    def _assert_credit_panel(
        self,
        panel_index: int,
        *,
        welcome_name: str,
        credit_score: str,
        credit_rating: str,
        tds_score: str,
        credit_utilization: str,
        warning_flags: list[str],
        flag_start: int = 0,
    ) -> None:
        if welcome_name.upper() == "N/A":
            name_text = self._panel_welcome_name_from_index(panel_index)
            assert "N/A" in name_text.upper(), f"Expected co-applicant N/A, got {name_text!r}"
        else:
            name_text = self._panel_welcome_name_from_index(panel_index)
            assert welcome_name.split()[0] in name_text, (
                f"Expected {welcome_name.split()[0]!r} in panel welcome line, got {name_text!r}"
            )
        score_el = self.page.locator(".credit-score-number").nth(panel_index)
        expect(score_el).to_have_text(re.compile(rf"^{re.escape(str(credit_score))}$"))
        rating_el = self.page.locator(".credit-score-rating").nth(panel_index)
        rating_text = normalize_whitespace(rating_el.inner_text())
        assert ms_app_credit_rating_matches(credit_rating, rating_text), (
            f"Rating mismatch: expected {credit_rating!r}, MS App shows {rating_text!r}"
        )
        tds_text, util_text = self._credit_panel_metrics(panel_index)
        assert normalize_percent(tds_text) == normalize_percent(tds_score), (
            f"TDS mismatch: expected {tds_score!r}, got {tds_text!r}"
        )
        assert normalize_percent(util_text) == normalize_percent(credit_utilization), (
            f"Utilization mismatch: expected {credit_utilization!r}, got {util_text!r}"
        )
        displayed_flags = self._credit_panel_flags(flag_start, len(warning_flags))
        for flag in warning_flags:
            assert flag in displayed_flags, (
                f"Flag {flag!r} not in displayed flags {displayed_flags!r}"
            )
        assert len(displayed_flags) == len(warning_flags), (
            f"Expected {len(warning_flags)} flags, saw {displayed_flags!r}"
        )

    def assert_credit_slides(
        self,
        expectations: MortgageSnapshotDisplayExpectations,
        *,
        with_co_borrower: bool,
    ) -> None:
        primary_flag_count = len(expectations.primary_warning_flags)
        self._assert_credit_panel(
            0,
            welcome_name=expectations.applicant_first_name,
            credit_score=expectations.credit_score,
            credit_rating=expectations.credit_rating,
            tds_score=expectations.tds_score,
            credit_utilization=expectations.credit_utilization,
            warning_flags=expectations.primary_warning_flags,
            flag_start=0,
        )
        if with_co_borrower:
            self._assert_credit_panel(
                1,
                welcome_name=expectations.co_applicant_display_name,
                credit_score=expectations.co_credit_score,
                credit_rating=expectations.co_credit_rating,
                tds_score=expectations.co_tds_score,
                credit_utilization=expectations.co_credit_utilization,
                warning_flags=expectations.co_warning_flags,
                flag_start=primary_flag_count,
            )
        else:
            name_text = self._panel_welcome_name_from_index(1)
            assert "N/A" in name_text.upper(), f"Expected co-applicant N/A, got {name_text!r}"

    def _debt_row_value(self, label_pattern: str) -> str:
        row = self.page.locator(".landscape-debt-row", has_text=re.compile(label_pattern, re.I)).first
        value = row.locator("span").last
        return normalize_whitespace(value.inner_text())

    def _minimum_payment_on_slide(self, expected: str) -> str:
        slide = self._slide_text()
        expected_norm = normalize_currency(expected)
        banner = re.search(
            r"\$\s*([\d,]+)\s+minimum payments needed",
            slide,
            re.I,
        )
        if banner:
            return normalize_currency(banner.group(1))
        formatted = format_currency_display(expected)
        if formatted and formatted in slide:
            return expected_norm
        expected_digits = re.sub(r"[^\d]", "", expected)
        slide_digits = re.sub(r"[^\d]", "", slide)
        if (
            expected_digits
            and slide_digits == expected_digits
        ):
            return expected_norm
        return ""

    def _read_minimum_payment(self, expected: str) -> str:
        """Read minimum payment from banner or debt row (may be mid-animation)."""
        payment = self._minimum_payment_on_slide(expected)
        if payment:
            return payment
        try:
            row_val = self._debt_row_value(r"Minimum payment needed")
            return normalize_currency(row_val)
        except Exception:
            return ""

    def _wait_for_minimum_payment_stable(self, expected: str) -> str:
        """
        Wait for the debt-slide count-up animation to reach the CRM value.

        The banner animates from $0 upward; reading too early causes false mismatches.
        """
        timeout_ms = Config.MS_APP_MIN_PAYMENT_ANIMATION_TIMEOUT_MS
        poll_ms = 250
        deadline = time.time() + (timeout_ms / 1000)
        last_payment = ""

        while time.time() < deadline:
            payment = self._read_minimum_payment(expected)
            if payment and self._currency_matches(payment, expected):
                return payment
            last_payment = payment
            self.page.wait_for_timeout(poll_ms)

        return last_payment

    @staticmethod
    def _currency_matches(actual: str, expected: str) -> bool:
        left = normalize_currency(actual)
        right = normalize_currency(expected)
        if left == right:
            return True
        if not left or not right:
            return False
        try:
            return float(left) == float(right)
        except ValueError:
            return False

    def assert_debt_slide(self, expectations: MortgageSnapshotDisplayExpectations) -> None:
        expect(self.page.locator(".landscape-debt-label").first).to_contain_text("Your debt calculator")
        assert normalize_currency(self._debt_row_value(r"Current high-interest debt")) == normalize_currency(
            expectations.current_balance
        )
        assert normalize_percent(self._debt_row_value(r"Average interest rate")) == normalize_percent(
            expectations.current_rate
        )
        years_display = self._debt_row_value(r"Average time to pay off")
        assert normalize_years(years_display) == normalize_years(expectations.years_to_pay)
        assert normalize_currency(self._debt_row_value(r"Interest paid over time")) == normalize_currency(
            expectations.total_interest
        )
        assert normalize_currency(self._debt_row_value(r"true cost of debt")) == normalize_currency(
            expectations.total_cost
        )
        payment = self._wait_for_minimum_payment_stable(expectations.monthly_payment)
        if not (payment and self._currency_matches(payment, expectations.monthly_payment)):
            raise AssertionError(
                f"Minimum payment mismatch: expected {expectations.monthly_payment!r}, "
                f"resolved {payment!r} after animation wait, "
                f"slide excerpt: {self._slide_text()[:500]!r}"
            )

    def _option_blocks(self):
        """
        Each mortgage-option column has one ``h3.opt-product-type`` heading.

        Prefer stars-row scoping when present; otherwise isolate cards via the
        product-type heading (MS App may not render ``.stars-row`` in the DOM).
        """
        stars_based = self.page.locator(
            "xpath=//div[contains(@class,'stars-row')]/ancestor::*"
            "[count(.//div[contains(@class,'stars-row')])=1]"
            "[.//h3[contains(@class,'opt-product-type')]][1]"
        )
        if stars_based.count() > 0:
            return stars_based
        return self.page.locator(
            "xpath=//h3[contains(@class,'opt-product-type')]/ancestor::*"
            "[count(.//h3[contains(@class,'opt-product-type')])=1][1]"
        )

    def _option_block(self, star_count: int, product_type: str | None = None):
        blocks = self._option_blocks()
        expect(blocks.first).to_be_visible(timeout=Config.TIMEOUT)
        block_count = blocks.count()
        if block_count == 0:
            raise AssertionError("No mortgage option blocks found on slide")

        if product_type:
            for index in range(block_count):
                block = blocks.nth(index)
                product_text = normalize_whitespace(
                    block.locator(".opt-product-type").first.inner_text()
                )
                if product_type in product_text:
                    return block

        for index in range(block_count):
            block = blocks.nth(index)
            block_stars = block.locator(
                f'.stars-row[aria-label="{star_count} star rating"]'
            )
            if block_stars.count() > 0:
                return block

        for index in range(block_count):
            block = blocks.nth(index)
            stars = block.locator(".stars-row")
            if stars.count() == 0:
                continue
            aria = stars.first.get_attribute("aria-label") or ""
            if f"{star_count} star" in aria:
                return block

        fallback_index = 0 if star_count == 4 else min(1, block_count - 1)
        return blocks.nth(fallback_index)

    def _option_block_values(self, block) -> set[str]:
        rows = block.locator(".opt-row")
        return {
            normalize_whitespace(rows.nth(i).locator("span").last.inner_text())
            for i in range(rows.count())
        }

    @staticmethod
    def _currency_in_values(value: str, values: set[str]) -> bool:
        formatted = format_currency_display(value)
        normalized = normalize_currency(value)
        normalized_values = {normalize_currency(v) for v in values}
        return formatted in values or normalized in normalized_values

    def _wait_for_option_block_values(
        self,
        block,
        *,
        loan: str,
        payment: str,
        savings: str,
        timeout_ms: int | None = None,
    ) -> set[str]:
        """Wait for animated currency values on the mortgage-options slide."""
        timeout_ms = timeout_ms or Config.MS_APP_MIN_PAYMENT_ANIMATION_TIMEOUT_MS
        deadline = time.time() + (timeout_ms / 1000)
        last_values: set[str] = set()

        while time.time() < deadline:
            values = self._option_block_values(block)
            if (
                self._currency_in_values(loan, values)
                and self._currency_in_values(payment, values)
                and self._currency_in_values(savings, values)
            ):
                return values
            last_values = values
            self.page.wait_for_timeout(250)

        return last_values

    def _assert_option_block(
        self,
        star_count: int,
        *,
        product_type: str,
        loan: str,
        payment: str,
        savings: str,
        points: list[str],
    ) -> None:
        block = self._option_block(star_count, product_type)
        product_el = block.locator(".opt-product-type").first
        expect(product_el).to_be_visible(timeout=Config.TIMEOUT)
        product_text = normalize_whitespace(product_el.inner_text())
        if product_type not in product_text:
            stars = block.locator(".stars-row")
            stars_label = (
                stars.first.get_attribute("aria-label") if stars.count() > 0 else None
            )
            raise AssertionError(
                f"Option {star_count}-star product type mismatch: expected {product_type!r}, "
                f"got {product_text!r} (block stars: {stars_label!r})"
            )
        values = self._wait_for_option_block_values(
            block, loan=loan, payment=payment, savings=savings
        )
        if not self._currency_in_values(loan, values):
            raise AssertionError(
                f"Option {star_count}-star loan mismatch: expected {loan!r} "
                f"({format_currency_display(loan)!r}), slide values: {sorted(values)!r}"
            )
        if not self._currency_in_values(payment, values):
            raise AssertionError(
                f"Option {star_count}-star payment mismatch: expected {payment!r} "
                f"({format_currency_display(payment)!r}), slide values: {sorted(values)!r}"
            )
        if not self._currency_in_values(savings, values):
            raise AssertionError(
                f"Option {star_count}-star savings mismatch: expected {savings!r} "
                f"({format_currency_display(savings)!r}), slide values: {sorted(values)!r}"
            )
        point_els = block.locator(".opt-point")
        point_text = " ".join(
            normalize_whitespace(point_els.nth(i).inner_text()) for i in range(point_els.count())
        )
        for point in points:
            assert point in point_text, f"Point {point!r} not in {point_text!r}"

    def assert_mortgage_options_slide(
        self, expectations: MortgageSnapshotDisplayExpectations
    ) -> None:
        self._assert_option_block(
            4,
            product_type=expectations.option4_type,
            loan=expectations.option4_loan,
            payment=expectations.option4_payment,
            savings=expectations.option4_savings,
            points=expectations.option4_points,
        )
        self._assert_option_block(
            5,
            product_type=expectations.option5_type,
            loan=expectations.option5_loan,
            payment=expectations.option5_payment,
            savings=expectations.option5_savings,
            points=expectations.option5_points,
        )

    def _read_home_appraised_values(self) -> dict[str, object]:
        min_val = self.page.locator(".ha-card-value").nth(0).inner_text()
        max_val = self.page.locator(".ha-card-value").nth(1).inner_text()
        detail_values = self.page.locator(
            ".ha-detail-label.tabular-nums, .ha-detail-label .tabular-nums"
        )
        texts = [
            normalize_whitespace(detail_values.nth(i).inner_text())
            for i in range(detail_values.count())
        ]
        ltv = self.page.locator(".ha-ltv-value").first.inner_text()
        return {
            "min_val": min_val,
            "max_val": max_val,
            "detail_texts": texts,
            "ltv": ltv,
        }

    def _home_appraised_values_match(
        self,
        readings: dict[str, object],
        expectations: MortgageSnapshotDisplayExpectations,
    ) -> bool:
        min_val = str(readings["min_val"])
        max_val = str(readings["max_val"])
        texts = list(readings["detail_texts"])
        ltv = str(readings["ltv"])
        normalized_texts = {normalize_currency(t) for t in texts}

        if not self._currency_matches(min_val, expectations.min_value):
            return False
        if not self._currency_matches(max_val, expectations.max_value):
            return False
        value_used = normalize_currency(expectations.value_used)
        if value_used and value_used not in normalized_texts:
            joined = normalize_currency(" ".join(texts))
            if value_used not in joined:
                return False
        less_mortgages = normalize_currency(expectations.less_all_mortgages)
        if less_mortgages and less_mortgages not in normalized_texts:
            return False
        if normalize_percent(ltv) != normalize_percent(expectations.ltv):
            return False
        return True

    def _wait_for_home_appraised_stable(
        self,
        expectations: MortgageSnapshotDisplayExpectations,
    ) -> dict[str, object]:
        """Wait for home-appraised slide currency count-up animations to finish."""
        timeout_ms = Config.MS_APP_MIN_PAYMENT_ANIMATION_TIMEOUT_MS
        poll_ms = 250
        deadline = time.time() + (timeout_ms / 1000)
        last_readings: dict[str, object] = {}

        while time.time() < deadline:
            readings = self._read_home_appraised_values()
            if self._home_appraised_values_match(readings, expectations):
                return readings
            last_readings = readings
            self.page.wait_for_timeout(poll_ms)

        return last_readings

    def assert_home_appraised_slide(
        self, expectations: MortgageSnapshotDisplayExpectations
    ) -> None:
        address = self.page.locator(".ha-label").first
        expect(address).to_be_visible()
        address_text = normalize_whitespace(address.inner_text())
        needle = expectations.property_address_contains.strip().lower()
        if needle and needle not in address_text.lower():
            raise AssertionError(
                f"Home appraised address mismatch: expected street fragment {needle!r} "
                f"from CRM profile, MS App shows {address_text!r}"
            )

        readings = self._wait_for_home_appraised_stable(expectations)
        min_val = str(readings.get("min_val", ""))
        max_val = str(readings.get("max_val", ""))
        texts = list(readings.get("detail_texts") or [])
        ltv = str(readings.get("ltv", ""))
        normalized_texts = {normalize_currency(t) for t in texts}

        if not self._currency_matches(min_val, expectations.min_value):
            raise AssertionError(
                f"Home appraised min value mismatch: expected {expectations.min_value!r}, "
                f"got {min_val!r} after animation wait"
            )
        if not self._currency_matches(max_val, expectations.max_value):
            raise AssertionError(
                f"Home appraised max value mismatch: expected {expectations.max_value!r}, "
                f"got {max_val!r} after animation wait"
            )
        value_used = normalize_currency(expectations.value_used)
        if value_used and value_used not in normalized_texts:
            raise AssertionError(
                f"Home appraised value-used mismatch: expected {expectations.value_used!r}, "
                f"detail values: {texts!r} after animation wait"
            )
        less_mortgages = normalize_currency(expectations.less_all_mortgages)
        if less_mortgages and less_mortgages not in normalized_texts:
            raise AssertionError(
                f"Home appraised less-all-mortgages mismatch: expected "
                f"{expectations.less_all_mortgages!r}, detail values: {texts!r} after animation wait"
            )
        if normalize_percent(ltv) != normalize_percent(expectations.ltv):
            raise AssertionError(
                f"Home appraised LTV mismatch: expected {expectations.ltv!r}, "
                f"got {ltv!r} after animation wait"
            )

    def _final_client_point_texts(self) -> list[str]:
        points = self.page.locator(".mp-point")
        return [
            normalize_whitespace(points.nth(i).inner_text())
            for i in range(points.count())
        ]

    def assert_final_client_slide(
        self, expectations: MortgageSnapshotDisplayExpectations
    ) -> None:
        expect(self.page.locator(".mp-label").first).to_be_visible(timeout=Config.TIMEOUT)

        prompt_el = self.page.locator(".mp-prompt").first
        expect(prompt_el).to_be_visible(timeout=Config.TIMEOUT)
        prompt_text = normalize_whitespace(prompt_el.inner_text())
        if expectations.final_prompt:
            if expectations.final_prompt not in prompt_text:
                raise AssertionError(
                    f"Final prompt mismatch: expected {expectations.final_prompt!r}, "
                    f"MS App .mp-prompt shows {prompt_text!r}"
                )

        points = self.page.locator(".mp-point")
        expect(points.first).to_be_visible(timeout=Config.TIMEOUT)
        point_texts = self._final_client_point_texts()
        joined_points = " | ".join(point_texts)

        for label, expected in (
            ("one", expectations.final_point_one),
            ("two", expectations.final_point_two),
            ("three", expectations.final_point_three),
        ):
            if not expected:
                continue
            if expected not in joined_points and not any(
                expected in text for text in point_texts
            ):
                raise AssertionError(
                    f"Final client point {label} mismatch: expected {expected!r}, "
                    f"MS App .mp-point values: {point_texts!r}"
                )

    def assert_final_client_slide_visible(self) -> None:
        """Backward-compatible alias when expectations are unavailable."""
        expect(self.page.locator(".mp-label").first).to_be_visible()
        expect(self.page.locator(".mp-prompt").first).to_be_visible()
        expect(self.page.locator(".mp-point").first).to_be_visible()

    def assert_full_presentation(
        self,
        expectations: MortgageSnapshotDisplayExpectations,
        *,
        with_co_borrower: bool,
    ) -> None:
        self.wait_for_presentation()
        assert self.detect_slide_type() == "welcome", (
            f"Expected welcome slide, got {self.detect_slide_type()}"
        )
        self.assert_welcome_slide(expectations)
        self.go_to_next_slide()
        slide2 = self.detect_slide_type()
        assert slide2 == "what_you_told_us", (
            f"Expected what_you_told_us slide, got {slide2!r}; "
            f"sample: {self._slide_text()[:400]!r}"
        )
        self.assert_what_you_told_us_slide(expectations)
        self.go_to_next_slide()
        assert self.detect_slide_type() == "credit_profile"
        self.assert_credit_slides(expectations, with_co_borrower=with_co_borrower)
        self.go_to_next_slide()
        assert self.detect_slide_type() == "debt_calculator"
        self.assert_debt_slide(expectations)
        self.go_to_next_slide()
        assert self.detect_slide_type() == "mortgage_options"
        self.assert_mortgage_options_slide(expectations)
        self.go_to_next_slide()
        assert self.detect_slide_type() == "home_appraised"
        self.assert_home_appraised_slide(expectations)
        self.go_to_next_slide()
        self.go_to_final_client_slide()
        self.assert_final_client_slide(expectations)

    def assert_slide_navigation_persistence(
        self,
        expectations: MortgageSnapshotDisplayExpectations,
        *,
        with_co_borrower: bool,
    ) -> None:
        """Single rewind to welcome and forward to final — data checked at both ends."""
        self.go_to_welcome_slide()
        self.assert_welcome_slide(expectations)
        self.go_to_final_client_slide(max_advances=8)
        self.assert_final_client_slide(expectations)
