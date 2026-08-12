import pytest

from utils.reporting import register_test_data
from utils.sales_flow_orchestration import (
    run_compliance_path_all_cases_reported,
    run_compliance_to_client_care_flow,
    run_marketing_flow,
    run_marketing_path_all_cases_reported,
)


@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_full_flow_create_lead_to_client_care(authenticated_page, request):
    """Full positive flow: Create Lead through Client Care (Compliance path)."""
    deal_name = run_compliance_to_client_care_flow(authenticated_page, request)
    register_test_data(request.node, flow="compliance_to_client_care", deal_name=deal_name)


@pytest.mark.regression
@pytest.mark.flow_orchestrator
def test_full_flow_create_lead_to_client_care_all_cases(authenticated_page, request):
    """Full regression: every stage empty, invalid, and smoke case through Client Care."""
    deal_name = run_compliance_path_all_cases_reported(authenticated_page, request)
    register_test_data(request.node, flow="compliance_all_cases", deal_name=deal_name)


@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_full_flow_create_lead_to_marketing(authenticated_page, request):
    """Full positive flow: Create Lead through Marketing (Signed Marketing path)."""
    deal_name = run_marketing_flow(authenticated_page, request)
    register_test_data(request.node, flow="signed_marketing", deal_name=deal_name)


def test_full_flow_marketing_all_cases(authenticated_page, request):
    """Full regression: every stage empty, invalid, and smoke through Marketing."""
    deal_name = run_marketing_path_all_cases_reported(authenticated_page, request)
    register_test_data(request.node, flow="marketing_all_cases", deal_name=deal_name)
