import pytest

from pages.nova_worksheet_page import NovaWorksheetPage
from test_page_data import test_entities

_SKIP_REASON = (
    "CRM has no supported UI path to set scarlettAppNo on a fresh lead without "
    "Push to Scarlett (forbidden in E2E). SaleLeadInfo.handleOpenNovaWorksheetTab "
    "opens ScarlettPushRequiredDialog when scarlettAppNo is missing, so the Nova "
    "Worksheet dialog cannot be automated end-to-end until Scarlett data exists."
)


@pytest.mark.skip(reason=_SKIP_REASON)
def test_nova_worksheet_requires_scarlett_app_number(authenticated_page):
    """Placeholder for Nova Worksheet automation — blocked by Scarlett dependency."""
    page = NovaWorksheetPage(authenticated_page)
    page.open()
    page.open_deal(test_entities.MY_DEALS_DEAL_NAME)
    page.open_nova_tab()
