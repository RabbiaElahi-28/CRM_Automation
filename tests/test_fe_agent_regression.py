"""Frontend Agent regression orchestrators."""

import pytest

from utils.config import Config
from utils.reporting import register_test_data
# from utils.sales_flow_orchestration import run_fe_agent_pre_stage_all_cases_reported
from utils.sales_flow_orchestration import run_fe_agent_compliance_all_cases_reported


def _skip_if_fe_agent_unauthenticated(page) -> None:
    page.goto(Config.BASE_URL)
    page.wait_for_load_state("domcontentloaded")
    if "/login" in page.url:
        pytest.skip(
            "FE agent credentials unavailable on dev CRM — cannot run FE regression."
        )


@pytest.mark.regression
@pytest.mark.fe_agent
@pytest.mark.flow_orchestrator
def test_fe_agent_compliance_all_cases(admin_page, fe_agent_page, request):
    """Full FE agent regression: pre-stage + stages on agent, Compliance on admin."""
    _skip_if_fe_agent_unauthenticated(fe_agent_page)
    # deal_name = run_fe_agent_pre_stage_all_cases_reported(
    deal_name = run_fe_agent_compliance_all_cases_reported(
        admin_page, fe_agent_page, request
    )
    register_test_data(
        request.node, flow="fe_agent_compliance_all_cases", deal_name=deal_name
    )
