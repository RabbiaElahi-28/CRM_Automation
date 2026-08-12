import re
from urllib.parse import urlparse

from pages.base_page import BasePage
from playwright.sync_api import Page, expect

from utils.config import Config

_NTP_APP_ROOT = Config.ntp_app_login_url()
_LEADS_URL = re.compile(r".*/leads(?:\?.*)?$", re.I)
_LOGIN_URL = re.compile(r"ntp\.[^/]+/?(?:\?.*)?$", re.I)
_STAFF_URL = re.compile(r".*/staff(?:\?.*)?$", re.I)


def _ntp_app_host() -> str:
    return urlparse(Config.NTP_APP_URL).hostname or ""


def _is_ntp_app_cookie(cookie: dict) -> bool:
    domain = cookie.get("domain", "")
    host = _ntp_app_host()
    if "ntp" in domain.lower() and "vibecircuit" in domain.lower():
        return True
    return bool(host and host in domain)


def _clear_ntp_app_storage(page: Page) -> None:
    """Clear NTP App auth/storage only — never wipe CRM cookies in the shared context."""
    try:
        for cookie in page.context.cookies():
            if not _is_ntp_app_cookie(cookie):
                continue
            page.context.clear_cookies(
                name=cookie["name"],
                domain=cookie["domain"],
                path=cookie.get("path", "/"),
            )
    except Exception:
        pass
    try:
        if "ntp" in page.url.lower():
            page.evaluate(
                "() => { localStorage.clear(); sessionStorage.clear(); }"
            )
    except Exception:
        pass


class NtpAppLoginPage(BasePage):
    """NTP App login fallback at Config.NTP_APP_URL."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.email_input = page.get_by_role("textbox", name=re.compile(r"email", re.I))
        self.password_input = page.get_by_role(
            "textbox", name=re.compile(r"password", re.I)
        )
        self.login_button = page.get_by_role("button", name="Login")

    def open(self, *, clear_storage: bool = False) -> None:
        if clear_storage:
            _clear_ntp_app_storage(self.page)
        self.page.goto(_NTP_APP_ROOT)
        self.page.wait_for_load_state("domcontentloaded")

    def wait_for_login_form(self) -> None:
        expect(self.page).to_have_url(_LOGIN_URL, timeout=Config.TIMEOUT)
        expect(self.email_input).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.password_input).to_be_visible(timeout=Config.TIMEOUT)
        expect(self.login_button).to_be_visible(timeout=Config.TIMEOUT)

    def login(self, email: str, password: str, *, force: bool = False) -> None:
        if not force and _LEADS_URL.search(self.page.url):
            return

        self.open(clear_storage=force)
        self.wait_for_login_form()
        self.email_input.fill("")
        self.fill(self.email_input, email)
        self.password_input.fill("")
        self.fill(self.password_input, password)

        login_btn = self.page.get_by_role("button", name="Login")
        expect(login_btn).to_be_enabled(timeout=Config.TIMEOUT)

        with self.page.expect_navigation(url=_LEADS_URL, timeout=60000):
            login_btn.click()
