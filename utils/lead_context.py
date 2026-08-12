"""Session-scoped lead context for bootstrap and stage tests.

Provides a single in-memory source of truth for the lead created in the
current pytest run. ``test_entities.MY_*`` globals remain for backward
compatibility; ``persist_*`` helpers sync both stores.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LeadContext:
    """Active lead/deal names for the current test session."""

    lead_name: str | None = None
    deal_name: str | None = None
    lead_email: str | None = None
    lead_property_address: str | None = None
    _bootstrapped: bool = field(default=False, repr=False)

    def set_lead_name(self, name: str) -> None:
        self.lead_name = name

    def set_deal_name(self, name: str) -> None:
        self.deal_name = name
        if self.lead_name is None:
            self.lead_name = name

    def mark_bootstrapped(self) -> None:
        self._bootstrapped = True

    @property
    def is_bootstrapped(self) -> bool:
        return self._bootstrapped

    def get_lead_name(self) -> str:
        if self.lead_name:
            return self.lead_name
        from test_page_data import test_entities

        return test_entities.MY_LEADS_DEAL_NAME

    def get_deal_name(self) -> str:
        if self.deal_name:
            return self.deal_name
        from test_page_data import test_entities

        return test_entities.MY_DEALS_DEAL_NAME

    def require_lead_name(self) -> str:
        name = self.get_lead_name()
        if not name:
            raise RuntimeError("Bootstrap lead not created — run create-lead tests first")
        return name

    def require_deal_name(self) -> str:
        name = self.get_deal_name()
        if not name:
            raise RuntimeError(
                "Bootstrap deal not on sales — run move-to-sales bootstrap first"
            )
        return name


_SESSION = LeadContext()


def get_lead_context() -> LeadContext:
    return _SESSION


def get_active_lead_name() -> str:
    return get_lead_context().get_lead_name()


def get_active_deal_name() -> str:
    return get_lead_context().get_deal_name()


def sync_lead_name(deal_name: str) -> None:
    """Update session context and test_entities after lead creation."""
    from test_page_data.test_entities import persist_my_leads_deal_name

    get_lead_context().set_lead_name(deal_name)
    persist_my_leads_deal_name(deal_name)


def sync_lead_email(email: str) -> None:
    """Keep MS App search email aligned with the CRM profile."""
    from utils.test_data_factory import update_lead_email

    get_lead_context().lead_email = email.strip()
    update_lead_email(email)


def sync_lead_property_address(property_partial: str) -> None:
    """Keep MS App home-appraised address aligned with CRM mortgage property."""
    from utils.test_data_factory import update_lead_property_address

    get_lead_context().lead_property_address = property_partial.strip()
    update_lead_property_address(property_partial)


def sync_deal_name(deal_name: str) -> None:
    """Update session context and test_entities after move to sales."""
    from test_page_data.test_entities import persist_my_deals_deal_name

    ctx = get_lead_context()
    ctx.set_deal_name(deal_name)
    ctx.mark_bootstrapped()
    persist_my_deals_deal_name(deal_name)
