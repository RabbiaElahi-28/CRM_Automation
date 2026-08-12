"""Sales Backend Submitted stage progression."""

import pytest

from tests.be_stage_test_helpers import skip_if_be_agent_unauthenticated
from utils.reporting import register_test_data
from utils.sales_flow_helpers import (
    run_backend_appraisal_order_smoke,
    run_backend_mortgage_snapshot_smoke,
    run_backend_submitted_smoke,
    setup_be_assigned_lead,
)

@pytest.mark.module_smoke
def test_be_submitted_stage(admin_page, be_agent_page, request):
    skip_if_be_agent_unauthenticated(be_agent_page)

    lead_name = setup_be_assigned_lead(admin_page)
    register_test_data(request.node, flow="be_submitted", lead_name=lead_name)

    run_backend_mortgage_snapshot_smoke(be_agent_page, lead_name)
    run_backend_appraisal_order_smoke(be_agent_page, lead_name)
    run_backend_submitted_smoke(be_agent_page, lead_name)

