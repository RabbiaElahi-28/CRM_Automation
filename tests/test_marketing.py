import pytest

from pages.marketing_page import MarketingPage
from test_page_data import test_entities
from utils.reporting import register_test_data


@pytest.mark.module_smoke
def test_marketing(authenticated_page, request):
    """Verify the lead appears on the Marketing board after Signed Marketing flow."""
    deal_name = test_entities.MY_DEALS_DEAL_NAME
    marketing = MarketingPage(authenticated_page)

    register_test_data(request.node, deal_name=deal_name)

    marketing.open()
    marketing.verify_lead_searchable(deal_name)
    marketing.verify_lead_in_marketing(deal_name)
    marketing.verify_on_marketing_list()
