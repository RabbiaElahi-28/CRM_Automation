from utils.config import Config
# import utils.test_data_factory as data
from utils.wait_helpers import wait_for_page_ready


class LoginPage():
    def __init__(self, page):
        self.page = page

        self.login_email = page.get_by_role("textbox", name="Enter an email")
        self.login_password = page.get_by_role("textbox", name="Enter a password")
        self.show_password = page.get_by_role("button", name="Show password")
        self.signup_btn = page.get_by_role("button", name="Sign in")

    def open(self):
        self.page.goto(Config.BASE_URL + "/login")
        wait_for_page_ready(self.page)

    def valid_login(self, username, password):
        self.login_email.click()
        self.login_email.fill(username)
        self.login_password.fill(password)
        self.show_password.click()

    def click_signup_btn(self):
        self.signup_btn.click()
