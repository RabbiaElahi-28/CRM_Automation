import pytest



from pages.appraisal_order_page import AppraisalOrderPage

from test_page_data.appraisal_order_data import AppraisalOrderData

from test_page_data import test_entities

from test_page_data.validation_cases import (

    APPRAISAL_EMPTY_INITIAL,

    APPRAISAL_EMPTY_NO,

    APPRAISAL_EMPTY_YES,

    APPRAISAL_EMPTY_YES_NO_AVM,

    APPRAISAL_INVALID,

)

from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields

from utils.lead_context import get_active_deal_name
from utils.reporting import register_test_data
from utils.sales_flow_helpers import run_appraisal_order_smoke

from utils.validations import Validations





def test_appraisal_order_empty(authenticated_page, request):

    """Verify all required-field validations across appraisal order flows."""

    appraisal = AppraisalOrderPage(authenticated_page)

    validator = Validations(authenticated_page)



    appraisal.open()

    appraisal.open_appraisal_order(test_entities.MY_DEALS_DEAL_NAME)



    register_test_data(request.node, scenario="empty_form", deal_name=test_entities.MY_DEALS_DEAL_NAME)



    appraisal.save_appraisal_order()
    verify_required_fields(validator, APPRAISAL_EMPTY_YES, item=request.node)

    appraisal.reset_appraisal_form()
    appraisal.select_yes_with_avm()
    appraisal.save_appraisal_order()
    verify_required_fields(validator, APPRAISAL_EMPTY_YES, item=request.node)

    appraisal.reset_appraisal_form()
    appraisal.select_no_with_avm()

    appraisal.save_appraisal_order()

    verify_required_fields(validator, APPRAISAL_EMPTY_NO, item=request.node)





def test_appraisal_order_invalid(authenticated_page, request):

    """Save appraisal order YES flow with every invalid LTV value."""

    appraisal = AppraisalOrderPage(authenticated_page)

    validator = Validations(authenticated_page)



    appraisal.open()

    appraisal.open_appraisal_order(test_entities.MY_DEALS_DEAL_NAME)

    appraisal.prepare_yes_flow_for_invalid_ltv()



    register_test_data(

        request.node, scenario="all_invalid_fields", deal_name=test_entities.MY_DEALS_DEAL_NAME

    )



    verify_invalid_fields(

        validator,

        APPRAISAL_INVALID,

        appraisal.set_field,

        appraisal.clear_field,

        appraisal.save_appraisal_order,

        item=request.node,

        reset=appraisal.prepare_yes_flow_for_invalid_ltv,

    )





@pytest.mark.module_smoke
def test_appraisal_order(authenticated_page, request):
    deal_name = get_active_deal_name()
    data = AppraisalOrderData()

    register_test_data(request.node, deal_name=deal_name, data=data)
    run_appraisal_order_smoke(authenticated_page, deal_name)


