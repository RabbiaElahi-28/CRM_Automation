from playwright.sync_api import  expect
import re
from datetime import datetime

from utils.wait_helpers import wait_for_page_ready


class BasePage:

    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------
    # Click
    # ---------------------------------------------------

    def click(self, locator):
        locator.wait_for(state="visible")
        locator.click()

    # ---------------------------------------------------
    # Fill
    # ---------------------------------------------------

    def fill(self, locator, value):
        locator.wait_for(state="visible")
        # locator.fill(str(value))
        locator.fill("" if value is None else str(value))

    # ---------------------------------------------------
    # Clear
    # ---------------------------------------------------

    def clear(self, locator):
        locator.wait_for()
        locator.fill("")

    # ---------------------------------------------------
    # Press
    # ---------------------------------------------------

    def press(self, locator, key):
        locator.press(key)

    # ---------------------------------------------------
    # Select Dropdown
    # ---------------------------------------------------

    def select_option(self, locator, value):
        locator.wait_for()
        locator.select_option(str(value))

    # ---------------------------------------------------
    # Checkbox
    # ---------------------------------------------------

    def check(self, locator):

        if not locator.is_checked():
            locator.check()

    def uncheck(self, locator):

        if locator.is_checked():
            locator.uncheck()

    # ---------------------------------------------------
    # Visibility
    # ---------------------------------------------------

    def is_visible(self, locator):

        return locator.is_visible()

    # ---------------------------------------------------
    # Wait
    # ---------------------------------------------------

    def wait_visible(self, locator):

        locator.wait_for(state="visible")

    def wait_hidden(self, locator):

        locator.wait_for(state="hidden")

    # ---------------------------------------------------
    # Text
    # ---------------------------------------------------

    def get_text(self, locator):

        return locator.text_content()

    # ---------------------------------------------------
    # Assertions
    # ---------------------------------------------------

    def verify_text(self, locator, expected):

        expect(locator).to_have_text(expected)

    def verify_contains_text(self, locator, expected):

        expect(locator).to_contain_text(expected)

    def verify_visible(self, locator):

        expect(locator).to_be_visible()

    def verify_hidden(self, locator):

        expect(locator).to_be_hidden()

    def verify_enabled(self, locator):

        expect(locator).to_be_enabled()

    def verify_disabled(self, locator):

        expect(locator).to_be_disabled()

    def verify_equal(self, locator, expected):
        expect(locator).to_have_text( re.compile(f"^{re.escape(str(expected))}$", re.IGNORECASE))


    def verify_datetime_equal(self, actual_locator, expected):
        self.actual = actual_locator.text_content().strip()

        self.actual_dt = datetime.strptime(self.actual, "%b %d, %Y, %I:%M %p")

        if isinstance(expected, str):
            self.expected_dt = datetime.strptime(expected, "%b %d, %Y, %I:%M %p")
        else:
            self.expected_dt = expected

        assert self.actual_dt == self.expected_dt, (
        f"\nExpected: {self.expected_dt}"
        f"\nActual:   {self.actual_dt}")
    # ---------------------------------------------------
    # Scroll
    # ---------------------------------------------------

    def scroll_into_view(self, locator):

        locator.scroll_into_view_if_needed()

    # ---------------------------------------------------
    # Screenshot
    # ---------------------------------------------------

    def screenshot(self, path):

        self.page.screenshot(path=path, full_page=True)

    # ---------------------------------------------------
    # Navigation
    # ---------------------------------------------------

    def goto(self, url):

        self.page.goto(url)

    def refresh(self):

        self.page.reload()

    # ---------------------------------------------------
    # Wait Loading
    # ---------------------------------------------------

    def wait_network(self):
        wait_for_page_ready(self.page)

    # ---------------------------------------------------
    # JS Click
    # ---------------------------------------------------

    def js_click(self, locator):

        locator.evaluate("element => element.click()")

    # ---------------------------------------------------
    # Hover
    # ---------------------------------------------------

    def hover(self, locator):

        locator.hover()

    # ---------------------------------------------------
    # Double Click
    # ---------------------------------------------------

    def double_click(self, locator):

        locator.dblclick()