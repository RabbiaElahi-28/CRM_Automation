import re

from playwright.sync_api import expect

from pages.base_page import BasePage
from utils.config import Config
from utils.entity_navigation import MARKETING_BUCKET, verify_bucket_record_visible

_MARKETING_PATH = "/marketing"


class MarketingPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        self.marketing_link = page.get_by_role("link", name="Marketing")


    def open(self):
        self.page.goto(
            Config.BASE_URL,
            wait_until="domcontentloaded",
            timeout=Config.TIMEOUT,
        )

        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

    def verify_lead_searchable(self, deal_name: str):
        verify_bucket_record_visible(self.page, MARKETING_BUCKET, deal_name)

    def verify_lead_in_marketing(self, deal_name: str):
        verify_bucket_record_visible(self.page, MARKETING_BUCKET, deal_name)

    def verify_on_marketing_list(self):
        expect(self.page).to_have_url(re.compile(rf"{_MARKETING_PATH}(?:\?.*)?$"))
