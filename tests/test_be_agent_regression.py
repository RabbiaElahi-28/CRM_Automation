"""Backend Agent regression orchestrators."""

import pytest

from tests.be_stage_test_helpers import skip_if_be_agent_unauthenticated
from utils.reporting import register_test_data
from utils.sales_flow_orchestration import run_be_agent_compliance_all_cases_reported


@pytest.mark.regression
@pytest.mark.be_agent
@pytest.mark.flow_orchestrator
def test_be_agent_compliance_all_cases(admin_page, be_agent_page, request):
    """Full BE agent regression: pre-stage + stages on agent, Compliance on admin."""
    skip_if_be_agent_unauthenticated(be_agent_page)
    deal_name = run_be_agent_compliance_all_cases_reported(
        admin_page, be_agent_page, request
    )
    register_test_data(
        request.node, flow="be_agent_compliance_all_cases", deal_name=deal_name
    )
