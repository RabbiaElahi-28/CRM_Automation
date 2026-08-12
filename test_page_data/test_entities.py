"""Centralized test entity names for automation.



Update deal/lead names here when test data changes — tests should never

hardcode these values.



Optional environment overrides (no code changes required):

  AUTOMATION_MY_LEADS_DEAL_NAME

  AUTOMATION_MY_DEALS_DEAL_NAME

  AUTOMATION_ASSIGNED_AGENT

  AUTOMATION_FE_AGENT_LABEL

  AUTOMATION_BE_AGENT_LABEL

  AUTOMATION_BE_STATUS_LABEL

  AUTOMATION_NOVA_BYPASS_STATUS_LABEL

"""



import os

import re

from pathlib import Path



_ENTITIES_FILE = Path(__file__).resolve()



MY_LEADS_DEAL_NAME = os.environ.get("AUTOMATION_MY_LEADS_DEAL_NAME", "Michael Friedman Automation Deal")

MY_DEALS_DEAL_NAME = os.environ.get("AUTOMATION_MY_DEALS_DEAL_NAME", "Michael Friedman Automation Deal")

ASSIGNED_AGENT = os.environ.get(
    "AUTOMATION_ASSIGNED_AGENT", "Hammad Ali (Admin)"
    # "AUTOMATION_ASSIGNED_AGENT", "Aleena shahid (Frontend Agent)"
)

FE_AGENT_LABEL = os.environ.get(
    "AUTOMATION_FE_AGENT_LABEL", "Rabbia Frontend (Frontend Agent)"
)

BE_AGENT_LABEL = os.environ.get(
    "AUTOMATION_BE_AGENT_LABEL", "Rabbia Backend (Backend Agent)"
)

BE_STATUS_LABEL = os.environ.get(
    "AUTOMATION_BE_STATUS_LABEL", "Application Received (Sales Backend)"
)

NOVA_BYPASS_STATUS_LABEL = os.environ.get(
    "AUTOMATION_NOVA_BYPASS_STATUS_LABEL", "Nova Worksheet (Sales Frontend)"
)





def _persist_entity_default(variable: str, deal_name: str) -> None:

    env_key = f"AUTOMATION_{variable}"

    safe_name = deal_name.replace("\\", "\\\\").replace('"', '\\"')

    content = _ENTITIES_FILE.read_text(encoding="utf-8")

    pattern = (

        rf'({variable} = os\.environ\.get\("{env_key}", ")[^"]*("\))'

    )

    updated, count = re.subn(pattern, rf'\1{safe_name}\2', content, count=1)

    if count != 1:

        raise RuntimeError(f"Failed to update {variable} in test_entities.py")

    _ENTITIES_FILE.write_text(updated, encoding="utf-8")





def persist_my_leads_deal_name(deal_name: str) -> None:

    """Write the latest My Leads name to disk and refresh this module."""

    global MY_LEADS_DEAL_NAME

    _persist_entity_default("MY_LEADS_DEAL_NAME", deal_name)

    MY_LEADS_DEAL_NAME = deal_name

    from utils.lead_context import get_lead_context

    get_lead_context().set_lead_name(deal_name)





def persist_my_deals_deal_name(deal_name: str) -> None:

    """Write the latest My Deals name to disk and refresh this module."""

    global MY_DEALS_DEAL_NAME

    _persist_entity_default("MY_DEALS_DEAL_NAME", deal_name)

    MY_DEALS_DEAL_NAME = deal_name

    from utils.lead_context import get_lead_context

    ctx = get_lead_context()
    ctx.set_deal_name(deal_name)
    ctx.mark_bootstrapped()
