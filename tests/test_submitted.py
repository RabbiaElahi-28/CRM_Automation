import pytest



from pages.submitted_page import SubmittedPage

from test_page_data.submitted_data import SubmittedData

from test_page_data import test_entities

from test_page_data.validation_cases import SUBMITTED_EMPTY, SUBMITTED_INVALID

from utils.negative_test_helpers import verify_invalid_fields, verify_required_fields

from utils.lead_context import get_active_deal_name
from utils.reporting import register_test_data
from utils.sales_flow_helpers import run_submitted_smoke

from utils.validations import Validations



OPTION = 1





def test_submitted_empty(authenticated_page, request):

    """Save submitted option with all required fields cleared."""

    submitted = SubmittedPage(authenticated_page)

    validator = Validations(authenticated_page)



    submitted.open()

    submitted.open_submitted(test_entities.MY_DEALS_DEAL_NAME)

    submitted.clear_option_fields(OPTION)
    
    # submitted.save_option(OPTION)
    submitted.save_option(OPTION, expect_success=False)



    register_test_data(

        request.node, scenario="empty_option_1", deal_name=test_entities.MY_DEALS_DEAL_NAME

    )

    verify_required_fields(validator, SUBMITTED_EMPTY, item=request.node)





def test_submitted_invalid(authenticated_page, request):

    """Save submitted option with every schema-invalid field value."""

    submitted = SubmittedPage(authenticated_page)

    validator = Validations(authenticated_page)



    submitted.open()

    submitted.open_submitted(test_entities.MY_DEALS_DEAL_NAME)

    submitted.prepare_option_for_invalid_tests(OPTION)



    register_test_data(

        request.node,

        scenario="all_invalid_fields",

        deal_name=test_entities.MY_DEALS_DEAL_NAME,

        option=OPTION,

    )



    def set_field(field, value):

        submitted.set_option_field(OPTION, field, value)



    def clear_field(field):

        submitted.clear_option_field(OPTION, field)



    verify_invalid_fields(

        validator,

        SUBMITTED_INVALID,

        set_field,

        clear_field,
        lambda: submitted.save_option(OPTION, expect_success=False),

        item=request.node,

        reset=lambda: submitted.prepare_option_for_invalid_tests(OPTION),

    )





@pytest.mark.module_smoke
def test_submitted(authenticated_page, request):
    deal_name = get_active_deal_name()
    data = SubmittedData()
    register_test_data(request.node, deal_name=deal_name, data=data)
    run_submitted_smoke(authenticated_page, deal_name)
