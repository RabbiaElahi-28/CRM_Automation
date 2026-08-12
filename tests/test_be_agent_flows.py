"""Backend Agent full-flow orchestrators."""

import pytest

from tests.be_stage_test_helpers import skip_if_be_agent_unauthenticated
from utils.reporting import register_test_data
from utils.sales_flow_helpers import setup_admin_be_lead
from utils.sales_flow_orchestration import (
    run_be_agent_compliance_to_client_care_flow,
    run_be_agent_marketing_flow,
    run_backend_full_flow_reported,
)
from utils.workflow_verification import BE_SIGNED_TRANSITION, WorkflowVerification


@pytest.mark.be_agent
@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_be_agent_compliance_to_client_care(admin_page, be_agent_page, request):
    """Admin setup → BE pipeline → Admin Compliance → Client Care."""
    skip_if_be_agent_unauthenticated(be_agent_page)
    deal_name = run_be_agent_compliance_to_client_care_flow(
        admin_page, be_agent_page, request
    )
    register_test_data(
        request.node, flow="be_agent_compliance_to_client_care", deal_name=deal_name
    )


@pytest.mark.be_agent
@pytest.mark.smoke
@pytest.mark.flow_orchestrator
def test_be_agent_marketing_flow(admin_page, be_agent_page, request):
    """Admin setup → BE pipeline → Admin Marketing."""
    skip_if_be_agent_unauthenticated(be_agent_page)
    deal_name = run_be_agent_marketing_flow(admin_page, be_agent_page, request)
    register_test_data(request.node, flow="be_agent_signed_marketing", deal_name=deal_name)


@pytest.mark.be_agent
def test_be_agent_backend_stages_only(admin_page, be_agent_page, request):
    """BE agent runs backend stages through Signed (with pre-stage)."""
    skip_if_be_agent_unauthenticated(be_agent_page)
    lead_name = setup_admin_be_lead(admin_page)
    register_test_data(request.node, flow="be_agent_stages", lead_name=lead_name)
    deal_name = run_backend_full_flow_reported(
        be_agent_page,
        request,
        flow="be_agent_stages",
        deal_name=lead_name,
        include_pre_stage=True,
        signed_role="agent",
    )
    verifier = WorkflowVerification(be_agent_page)
    verifier.verify_be_agent_has_full_access(BE_SIGNED_TRANSITION.visible_tabs)
    verifier.verify_transition(
        BE_SIGNED_TRANSITION,
        record_name=deal_name,
        skip_toast=True,
        skip_bucket=True,
    )
