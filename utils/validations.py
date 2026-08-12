from playwright.sync_api import expect


class Validations:

    _ERROR_SELECTOR = "div.text-red-500, div.text-red-400"

    def __init__(self, page):
        self.page = page

    def _error_locator(self, message: str | None = None):
        locator = self.page.locator(self._ERROR_SELECTOR)
        if message:
            return locator.filter(has_text=message)
        return locator

    def _visible_error_texts(self) -> list[str]:
        errors = self.page.locator(self._ERROR_SELECTOR)
        count = errors.count()
        return [
            errors.nth(i).inner_text().strip()
            for i in range(count)
            if errors.nth(i).is_visible()
        ]

    def _register_validation_failure(self, item, expected: str, actual: str) -> None:
        if item is None:
            return
        from utils.reporting import register_test_data

        register_test_data(
            item,
            Expected_Validation=expected,
            Actual_Validation=actual,
        )

    def assert_field_error(self, message: str, item=None):
        error = self._error_locator(message)
        try:
            expect(error.first).to_be_visible(timeout=10000)
            expect(error.first).to_have_text(message)
        except AssertionError:
            actual = self._actual_validation_summary()
            self._register_validation_failure(item, message, actual)
            raise AssertionError(
                f"Expected validation: {message!r}\nActual: {actual!r}"
            ) from None

    def assert_field_errors(self, messages: list[str], item=None):
        for message in messages:
            self.assert_field_error(message, item=item)

    def assert_messages_subset(self, messages: list[str], item=None):
        """Assert each expected message appears among visible inline errors."""
        visible = self._visible_error_texts()
        missing = [message for message in messages if message not in visible]
        if missing:
            actual = self._actual_validation_summary()
            for message in missing:
                self._register_validation_failure(item, message, actual)
            raise AssertionError(
                f"Expected validation messages not found: {missing!r}\nActual: {actual!r}"
            ) from None

    def assert_any_field_error(self, item=None):
        errors = self._error_locator()
        try:
            expect(errors.first).to_be_visible(timeout=10000)
        except AssertionError:
            self._register_validation_failure(item, "At least one field error", "No validation displayed")
            raise AssertionError(
                "Expected at least one validation message.\nActual: No validation displayed"
            ) from None

    def _actual_validation_summary(self) -> str:
        texts = self._visible_error_texts()
        if not texts:
            return "No validation displayed"
        return " | ".join(texts)
