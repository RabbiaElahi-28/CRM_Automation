"""Admin Sales Backend full-flow orchestrators."""

import pytest

from utils.reporting import register_test_data
from utils.sales_flow_orchestration import (
    run_backend_compliance_all_cases_reported,
    run_backend_compliance_to_client_care_flow,
    run_backend_marketing_flow,
)


@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_admin_backend_compliance_to_client_care(authenticated_page, request):
    """Admin Backend Compliance path through Client Care."""
    deal_name = run_backend_compliance_to_client_care_flow(authenticated_page, request)
    register_test_data(request.node, flow="admin_backend_compliance", deal_name=deal_name)


@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_admin_backend_marketing_flow(authenticated_page, request):
    """Admin Backend Marketing path."""
    deal_name = run_backend_marketing_flow(authenticated_page, request)
    register_test_data(request.node, flow="admin_backend_marketing", deal_name=deal_name)


@pytest.mark.regression
@pytest.mark.flow_orchestrator
def test_admin_backend_compliance_all_cases(authenticated_page, request):
    """Full backend regression through Client Care."""
    deal_name = run_backend_compliance_all_cases_reported(authenticated_page, request)
    register_test_data(request.node, flow="backend_compliance_all_cases", deal_name=deal_name)
