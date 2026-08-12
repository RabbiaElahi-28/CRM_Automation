import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.config import Config
from utils.logger import get_logger
from utils.reporting import append_report_extras, format_summary_html
from pages.login_page import LoginPage

logger = get_logger()

TRACES_DIR = Path("reports/traces")


def _create_auth_state(browser, username: str, password: str) -> dict:
    """Log in once and capture Playwright storage state for session reuse."""
    context = browser.new_context(viewport=None, record_video_dir="reports/videos/")
    page = context.new_page()
    page.set_default_timeout(Config.TIMEOUT)

    login = LoginPage(page)
    login.open()
    login.valid_login(username, password)
    login.click_signup_btn()
    page.wait_for_url(lambda url: "/login" not in url, timeout=Config.TIMEOUT)

    state = context.storage_state()
    context.close()
    return state


def _open_authenticated_page(browser, storage_state: dict, request):
    """Create a traced browser context and page from cached storage state."""
    context = browser.new_context(storage_state=storage_state, viewport=None)
    _start_tracing(context)
    page = context.new_page()
    page.set_default_timeout(Config.TIMEOUT)

    from utils.flow_artifacts import ConsoleLogBuffer, ensure_artifact_dirs

    ensure_artifact_dirs()
    ConsoleLogBuffer().attach(page)
    return context, page


def _start_tracing(context) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)


def _stop_tracing(context, request) -> None:
    rep = getattr(request.node, "rep_call", None)
    trace_path = TRACES_DIR / f"{request.node.name}.zip"
    try:
        if rep and rep.failed:
            from utils.flow_step_reporting import FlowStepRegistry

            if (
                request.node.get_closest_marker("flow_orchestrator")
                and FlowStepRegistry.has_failure_artifacts(request.node.nodeid)
            ):
                context.tracing.stop()
            elif not trace_path.is_file():
                context.tracing.stop(path=str(trace_path))
            else:
                context.tracing.stop()
        else:
            context.tracing.stop()
    except Exception as exc:
        logger.error("Failed to stop Playwright trace for %s: %s", request.node.name, exc)


@pytest.fixture(autouse=True)
def _flow_step_registry(request):
    if request.node.get_closest_marker("flow_orchestrator"):
        from utils.flow_step_reporting import FlowStepRegistry

        FlowStepRegistry.begin(request.node.nodeid)
    yield


@pytest.fixture(autouse=True)
def _capture_report_test_data(request):
    from utils.reporting import TestDataCapture
    import sys

    capture = TestDataCapture(request.node)
    previous_trace = sys.gettrace()
    sys.settrace(capture.tracefunc)
    yield
    sys.settrace(previous_trace)


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=Config.HEADLESS)

    yield browser
    browser.close()

@pytest.fixture()
def browser_context(browser, request):

    context = browser.new_context(record_video_dir="reports/videos/"
    )

    _start_tracing(context)

    yield context

    
    rep = getattr(request.node, "rep_call", None)

    
    if rep and rep.failed:
        context.video.save_as(f"reports/videos/{request.node.name}.webm")
    _stop_tracing(context, request)

    context.close()

    


@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    page.set_default_timeout(Config.TIMEOUT)

    yield page

   


@pytest.fixture(scope="session")
def admin_auth_state(browser):
    """Log in once per session as Admin and capture storage state for reuse."""
    return _create_auth_state(browser, Config.USERNAME, Config.PASSWORD)


@pytest.fixture(scope="session")
def auth_state(admin_auth_state):
    """Log in once per session and capture the storage state for reuse."""
    return admin_auth_state


@pytest.fixture(scope="session")
def fe_agent_auth_state(browser):
    """Log in once per session as Sales Frontend Agent and capture storage state."""
    return _create_auth_state(browser, Config.FE_USERNAME, Config.FE_PASSWORD)


@pytest.fixture(scope="session")
def be_agent_auth_state(browser):
    """Log in once per session as Sales Backend Agent and capture storage state."""
    return _create_auth_state(browser, Config.BE_USERNAME, Config.BE_PASSWORD)


@pytest.fixture
def authenticated_page(browser, auth_state, request):
    """Fresh page already authenticated via the cached session storage state."""
    context, page = _open_authenticated_page(browser, auth_state, request)
    yield page
    _stop_tracing(context, request)
    context.close()


@pytest.fixture(scope="session")
def lead_context():
    """Session-scoped store for the bootstrap lead created in the current run."""
    from utils.lead_context import get_lead_context

    return get_lead_context()


@pytest.fixture
def active_lead_name(lead_context):
    """Lead Bucket name from the current run's bootstrap create."""
    return lead_context.get_lead_name()


@pytest.fixture
def active_deal_name(lead_context):
    """My Deals name after move-to-sales in the current run."""
    return lead_context.get_deal_name()


@pytest.fixture
def admin_page(browser, admin_auth_state, request):
    """Fresh Admin page authenticated via the cached Admin storage state."""
    context, page = _open_authenticated_page(browser, admin_auth_state, request)
    yield page
    _stop_tracing(context, request)
    context.close()


@pytest.fixture
def fe_agent_page(browser, fe_agent_auth_state, request):
    """Fresh Sales Frontend Agent page authenticated via cached storage state."""
    context, page = _open_authenticated_page(browser, fe_agent_auth_state, request)
    yield page
    _stop_tracing(context, request)
    context.close()


@pytest.fixture
def be_agent_page(browser, be_agent_auth_state, request):
    """Fresh Sales Backend Agent page authenticated via cached storage state."""
    context, page = _open_authenticated_page(browser, be_agent_auth_state, request)
    yield page
    _stop_tracing(context, request)
    context.close()


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    append_report_extras(item, rep)
    setattr(item, "rep_" + rep.when, rep)


def pytest_html_results_summary(prefix, summary, postfix, session):
    prefix.append(format_summary_html(session))


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    from utils.session_timing import mark_session_start

    mark_session_start(session)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    from utils.flow_step_reporting import inject_flow_steps_into_html_report
    from utils.html_report_history import append_report_history, get_report_path, print_terminal_report_summary

    inject_flow_steps_into_html_report(session)

    if getattr(session.config.option, "collectonly", False):
        return

    report_path = get_report_path(session)
    if report_path is not None and report_path.is_file():
        append_report_history(session, report_path)
    print_terminal_report_summary(session)


def pytest_configure(config):
    """Ensure full-flow runs use persisted test_entities defaults, not shell env overrides."""
    import os

    os.environ.pop("AUTOMATION_MY_LEADS_DEAL_NAME", None)
    os.environ.pop("AUTOMATION_MY_DEALS_DEAL_NAME", None)

    from utils.html_report_history import configure_html_report_path

    configure_html_report_path(config)


def _negative_test_order(item):
    name = item.name
    if "_empty" in name:
        return 0
    if "_invalid" in name:
        return 1
    return 2


_STAGE_MODULE_ORDER = (
    "test_mortgage_snapshot",
    "test_appraisal_order",
    "test_submitted",
    "test_approved",
    "test_signed",
    "test_compliance",
    "test_client_care",
    "test_marketing",
    "test_signed_marketing",
    "test_nova_worksheet",
)


_BOOTSTRAP_MODULE_ORDER = {
    "test_lead_edit": 0,
    "test_add_coborrower": 1,
    "test_note": 2,
}


def _collection_sort_key(item):
    """Order tests so bootstrap (create → move to sales) runs before dependent modules."""
    module = item.module.__name__.rsplit(".", maxsplit=1)[-1]

    if module == "test_login_page":
        return (0, _negative_test_order(item), item.name)
    if module == "test_create_lead":
        return (1, _negative_test_order(item), item.name)
    if module in _BOOTSTRAP_MODULE_ORDER:
        return (
            2,
            _BOOTSTRAP_MODULE_ORDER[module],
            _negative_test_order(item),
            item.name,
        )
    if module == "test_move_to_sales_flow":
        return (3, 0, item.name)
    if module in _STAGE_MODULE_ORDER:
        return (4 + _STAGE_MODULE_ORDER.index(module), _negative_test_order(item), item.name)
    if module.startswith("test_be_") and module not in (
        "test_be_agent_flows",
        "test_be_agent_rbac",
    ):
        return (20, _negative_test_order(item), item.name)
    if module in (
        "test_full_sales_frontend_flow",
        "test_admin_backend_flows",
        "test_fe_agent_flows",
        "test_be_agent_flows",
        "test_fe_agent_rbac",
        "test_be_agent_rbac",
    ):
        return (30, _negative_test_order(item), item.name)
    return (10, _negative_test_order(item), item.name)


def pytest_collection_modifyitems(session, config, items):
    items.sort(key=_collection_sort_key)