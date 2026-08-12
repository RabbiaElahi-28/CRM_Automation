import os


class Config:
    BASE_URL = "https://dev.crm.vibecircuit.ca"
    MORTGAGE_SNAPSHOT_APP_URL = os.environ.get(
        "MORTGAGE_SNAPSHOT_APP_URL",
        "https://dev.mortgagesnapshot.vibecircuit.ca",
    )
    NTP_APP_URL = os.environ.get(
        "NTP_APP_URL",
        "https://dev.ntp.vibecircuit.ca",
    )

    @classmethod
    def ms_app_login_url(cls) -> str:
        """Native MS App login entry — RBAC and staff login (single place to change)."""
        return cls.MORTGAGE_SNAPSHOT_APP_URL.rstrip("/") + "/"

    @classmethod
    def ntp_app_login_url(cls) -> str:
        """Native NTP App login entry — RBAC fallback (single place to change)."""
        return cls.NTP_APP_URL.rstrip("/") + "/"

    MS_APP_LEAD_SYNC_TIMEOUT_MS = int(
        os.environ.get("MS_APP_LEAD_SYNC_TIMEOUT_MS", "180000")
    )
    NTP_APP_LEAD_SYNC_TIMEOUT_MS = int(
        os.environ.get(
            "NTP_APP_LEAD_SYNC_TIMEOUT_MS",
            os.environ.get("MS_APP_LEAD_SYNC_TIMEOUT_MS", "180000"),
        )
    )
    MS_APP_SEARCH_INTERVAL_MS = int(
        os.environ.get("MS_APP_SEARCH_INTERVAL_MS", "5000")
    )
    AUTH_VALIDATE_URL = os.environ.get(
        "AUTOMATION_AUTH_VALIDATE_URL",
        "https://dev.auth.crm.vibecircuit.ca",
    )
    MS_APP_NETWORK_ERROR_MAX_RETRIES = int(
        os.environ.get("MS_APP_NETWORK_ERROR_MAX_RETRIES", "3")
    )
    MS_APP_MIN_PAYMENT_ANIMATION_TIMEOUT_MS = int(
        os.environ.get("MS_APP_MIN_PAYMENT_ANIMATION_TIMEOUT_MS", "15000")
    )
    BROWSER = "chromium"
    TIMEOUT = 30000
    HEADLESS = False
    SLOW_MO = 1000
    VIEWPORT_WIDTH = 1920                  #1280
    VIEWPORT_HEIGHT = 1080                 #720

    USERNAME = "hammad.ali@fantechlabs.io"
    PASSWORD = "Test1234@"

    FE_USERNAME = os.environ.get("AUTOMATION_FE_USERNAME", "rabbia.elahi@fantechlabs.io")
    FE_PASSWORD = os.environ.get("AUTOMATION_FE_PASSWORD", "Fantechtest&1")
    BE_USERNAME = os.environ.get("AUTOMATION_BE_USERNAME", "rabbia.elahi+1@fantechlabs.io")
    BE_PASSWORD = os.environ.get("AUTOMATION_BE_PASSWORD", "Fantechtest&1")

    # Test deal/lead names and role labels — see test_page_data/test_entities.py
    from test_page_data.test_entities import (  # noqa: E402
        BE_AGENT_LABEL,
        BE_STATUS_LABEL,
        FE_AGENT_LABEL,
        MY_DEALS_DEAL_NAME,
        MY_LEADS_DEAL_NAME,
        NOVA_BYPASS_STATUS_LABEL,
    )
