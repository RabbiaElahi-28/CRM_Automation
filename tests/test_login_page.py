import re
import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from utils.logger import get_logger

logger = get_logger()


def get_login_json_data():
    import json

    with open("test_data/login.json", "r") as file:
        data = json.load(file)

    cases = []

    # valid user
    valid = data["valid_user"]
    cases.append((valid["email"], valid["password"], True))

    # invalid user
    invalid = data["invalid_user"]
    cases.append((invalid["email"], invalid["password"], False))

    return cases

@pytest.mark.parametrize("email, password, is_valid", get_login_json_data())
def test_valid_login_page(page, email, password, is_valid):

    page.on(
        "console",
        lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}")
    )

    login_page = LoginPage(page)
    login_page.open()
    expect(page.get_by_role("button", name="Sign in")).to_be_visible(timeout=30000)
    login_page.valid_login(email, password)
    login_page.click_signup_btn()

    if is_valid:
        page.wait_for_url(lambda url: "/login" not in url, timeout=30000)
        expect(page).not_to_have_url(re.compile(r"/login"))

    else:
        expect(
            page.get_by_text("Invalid email or password")
        ).to_be_visible()





