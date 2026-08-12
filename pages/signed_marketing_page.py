from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.signed_page import SignedPage
from utils.config import Config


class SignedMarketingPage(BasePage):
    """Signed tab actions for the Dead → Marketing disposition path."""

    def __init__(self, page):
        super().__init__(page)
        self.signed = SignedPage(page)

    def open_signed(self, deal_name: str):
        self.signed.open_signed(deal_name)

    def verify_signed_marketing_prefill(self, prefill=None):
        self.signed.verify_client_signed_yes_selected()
        self.signed.verify_final_product_section_visible()
        self.signed.verify_signed_details_prefilled(prefill)
        self.signed.verify_lender_name_prefilled()

    def select_final_product_no(self):
        self.signed.select_final_product_no()
        self.signed.verify_deal_tracking_sections_hidden()

    def select_dead_move_to_marketing(self):
        self.signed.select_dead_move_to_marketing()

    def save_and_verify_marketing_disposition(self):
        self.signed.save_signed_form()
        outcome = (
            self.signed.signed_update_toast.or_(self.signed.signed_create_toast).or_(
                self.signed.moved_to_marketing_toast
            )
        )
        expect(outcome.first).to_be_visible(timeout=Config.TIMEOUT)
        self.signed.verify_moved_to_marketing()
