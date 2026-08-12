"""Nova Worksheet page object — locators and actions only (no workflow automation).

CRM sources:
- apps/nextjs/src/features/sales/components/SaleLeadInfo.tsx (Nova tab trigger)
- apps/nextjs/src/features/nova-worksheet/components/NovaWorksheetDialog.tsx
- apps/nextjs/src/features/nova-worksheet/components/ScarlettPushRequiredDialog.tsx
"""

from pages.base_page import BasePage
from test_page_data.workflow_expectations import (
    NOVA_WORKSHEET_DIALOG_ACTIONS,
    NOVA_WORKSHEET_DIALOG_TABS,
    NOVA_WORKSHEET_DIALOG_TITLE,
    NOVA_WORKSHEET_TAB_NAME,
    SCARLETT_REQUIRED_DIALOG_ACTION,
    SCARLETT_REQUIRED_DIALOG_TITLE,
)
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record


class NovaWorksheetPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        self.nova_tab = page.get_by_role("tab", name=NOVA_WORKSHEET_TAB_NAME)

        self.scarlett_required_dialog = page.get_by_role(
            "alertdialog",
            name=SCARLETT_REQUIRED_DIALOG_TITLE,
        )
        self.scarlett_got_it_button = self.scarlett_required_dialog.get_by_role(
            "button",
            name=SCARLETT_REQUIRED_DIALOG_ACTION,
        )

        self.worksheet_dialog = page.get_by_role("dialog", name=NOVA_WORKSHEET_DIALOG_TITLE)
        self.refresh_from_scarlett_button = self.worksheet_dialog.get_by_role(
            "button",
            name=NOVA_WORKSHEET_DIALOG_ACTIONS[0],
        )
        self.save_worksheet_button = self.worksheet_dialog.get_by_role(
            "button",
            name=NOVA_WORKSHEET_DIALOG_ACTIONS[1],
        )
        self.complete_stage_button = self.worksheet_dialog.get_by_role(
            "button",
            name="Complete Stage",
        )

        self.worksheet_tab_home_equity = self.worksheet_dialog.get_by_role(
            "tab",
            name=NOVA_WORKSHEET_DIALOG_TABS[0],
        )
        self.worksheet_tab_mortgage_refinance = self.worksheet_dialog.get_by_role(
            "tab",
            name=NOVA_WORKSHEET_DIALOG_TABS[1],
        )
        self.worksheet_tab_home_purchase = self.worksheet_dialog.get_by_role(
            "tab",
            name=NOVA_WORKSHEET_DIALOG_TABS[2],
        )

    def open(self):
        self.page.goto(Config.BASE_URL)
        self.page.wait_for_load_state("networkidle")

    def open_deal(self, deal_name: str):
        open_bucket_record(self.page, MY_DEALS_BUCKET, deal_name)

    def open_nova_tab(self):
        self.click(self.nova_tab)

    def dismiss_scarlett_required_dialog(self):
        self.click(self.scarlett_got_it_button)

    def select_worksheet_tab(self, tab_name: str):
        self.click(self.worksheet_dialog.get_by_role("tab", name=tab_name))

    def click_refresh_from_scarlett(self):
        self.click(self.refresh_from_scarlett_button)

    def click_save_worksheet(self):
        self.click(self.save_worksheet_button)

    def click_complete_stage(self):
        self.click(self.complete_stage_button)
