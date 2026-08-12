"""Frontend Agent full-flow orchestrators."""

import pytest

from utils.config import Config
from utils.reporting import register_test_data
from utils.sales_flow_orchestration import (
    run_fe_compliance_to_client_care_flow,
    run_fe_marketing_flow,
)


def _skip_if_fe_agent_unauthenticated(page) -> None:
    page.goto(Config.BASE_URL)
    page.wait_for_load_state("domcontentloaded")
    if "/login" in page.url:
        pytest.skip(
            "FE agent credentials unavailable on dev CRM — cannot run FE orchestrator."
        )


@pytest.mark.fe_agent
@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_fe_agent_compliance_to_client_care(admin_page, fe_agent_page, request):
    """Admin setup → FE pipeline → Admin Compliance → Client Care."""
    _skip_if_fe_agent_unauthenticated(fe_agent_page)
    deal_name = run_fe_compliance_to_client_care_flow(
        admin_page, fe_agent_page, request
    )
    register_test_data(request.node, flow="fe_compliance_to_client_care", deal_name=deal_name)


@pytest.mark.fe_agent
@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_fe_agent_marketing_flow(admin_page, fe_agent_page, request):
    """Admin setup → FE pipeline → Admin Marketing."""
    _skip_if_fe_agent_unauthenticated(fe_agent_page)
    deal_name = run_fe_marketing_flow(admin_page, fe_agent_page, request)
    register_test_data(request.node, flow="fe_signed_marketing", deal_name=deal_name)
