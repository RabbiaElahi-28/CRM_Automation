import pytest

from pages.signed_marketing_page import SignedMarketingPage
from test_page_data import test_entities
from utils.reporting import register_test_data


@pytest.mark.module_smoke
def test_signed_marketing(authenticated_page, request):
    """Signed tab: verify Approved prefills, then move lead to Marketing."""
    deal_name = test_entities.MY_DEALS_DEAL_NAME
    signed_marketing = SignedMarketingPage(authenticated_page)

    register_test_data(request.node, deal_name=deal_name)

    signed_marketing.signed.open()
    signed_marketing.open_signed(deal_name)
    signed_marketing.verify_signed_marketing_prefill()
    signed_marketing.select_final_product_no()
    signed_marketing.select_dead_move_to_marketing()
    signed_marketing.save_and_verify_marketing_disposition()
