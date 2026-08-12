from playwright.sync_api import expect

from utils.config import Config


class Toast:

    def __init__(self, page):
        self.page = page

    def assert_visible(self):
        expect(self.page.locator("[data-sonner-toast]").first).to_be_visible(
            timeout=Config.TIMEOUT,
        )

    def assert_message(self, message: str, *, timeout: int | None = None):
        """Wait for a Sonner toast containing ``message``."""
        wait_ms = timeout or Config.TIMEOUT
        toast = self.page.locator("[data-sonner-toast]").filter(has_text=message).first
        expect(toast).to_be_visible(timeout=wait_ms)

    def assert_not_message(self, message: str, *, timeout: int = 3000):
        toast = self.page.locator("[data-sonner-toast]").filter(has_text=message)
        expect(toast).to_have_count(0, timeout=timeout)
