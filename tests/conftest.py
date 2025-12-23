import re
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from src.config.settings import Settings, get_settings
from src.core.logger import get_logger, log_json
from src.ui.pages.home_page import HomePage


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def _ensure_run_artifacts(base: Path, run_id: str) -> Path:
    run_dir = base / run_id
    for folder in ("screenshots", "video", "traces"):
        (run_dir / folder).mkdir(parents=True, exist_ok=True)
    return run_dir


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def run_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{uuid.uuid4().hex[:6]}"


@pytest.fixture(scope="session")
def logger(run_id: str, settings: Settings):
    return get_logger(run_id, settings.logs_dir)


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance, settings: Settings) -> Generator[Browser, None, None]:
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage"],
    )
    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser, settings: Settings, run_id: str, request, logger) -> Generator[BrowserContext, None, None]:
    run_artifacts = _ensure_run_artifacts(settings.playwright_dir, run_id)
    context = browser.new_context(
        base_url=settings.base_url,
        record_video_dir=run_artifacts / "video",
        viewport={"width": 1366, "height": 768},
        accept_downloads=True,
    )
    context.set_default_timeout(settings.ui_timeout)
    request.node._trace_started = False
    request.node._trace_stopped = False
    log_json(logger, "Context created", test=request.node.name, base_url=settings.base_url)

    yield context

    if getattr(request.node, "_trace_started", False) and not getattr(request.node, "_trace_stopped", False):
        with suppress(Exception):
            context.tracing.stop()
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def home_page(page: Page, settings: Settings) -> HomePage:
    return HomePage(page, settings.base_url, settings.ui_timeout)


def pytest_configure(config):
    settings = get_settings()
    if not getattr(config.option, "numprocesses", None):
        if settings.workers == "auto":
            config.option.numprocesses = "auto"
        else:
            with suppress(ValueError):
                config.option.numprocesses = int(settings.workers)
    if getattr(config.option, "reruns", None) is None:
        config.option.reruns = settings.reruns
    if getattr(config.option, "reruns_delay", None) is None:
        config.option.reruns_delay = settings.rerun_delay


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return

    page: Optional[Page] = item.funcargs.get("page")
    context: Optional[BrowserContext] = item.funcargs.get("context")
    settings: Optional[Settings] = item.funcargs.get("settings")
    run_id: Optional[str] = item.funcargs.get("run_id")
    logger = item.funcargs.get("logger")

    if rep.failed:
        test_name = _safe_name(item.name)
        if logger:
            log_json(logger, "Test failed", test=item.name, nodeid=item.nodeid)
        if page and settings and run_id:
            screenshot_path = settings.playwright_dir / run_id / "screenshots" / f"{test_name}.png"
            with suppress(Exception):
                page.screenshot(path=screenshot_path, full_page=True)
                allure.attach.file(
                    str(screenshot_path),
                    name=f"{item.name}-screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
        if context and settings and run_id:
            trace_path = settings.playwright_dir / run_id / "traces" / f"{test_name}-trace.zip"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            with suppress(Exception):
                context.tracing.stop(path=trace_path)
                item._trace_stopped = True
                allure.attach(
                    str(trace_path),
                    name=f"{item.name}-trace-path",
                    attachment_type=allure.attachment_type.TEXT,
                )
                allure.attach.file(
                    str(trace_path),
                    name=f"{item.name}-trace",
                    attachment_type=allure.attachment_type.ZIP,
                )
    else:
        if context and getattr(item, "_trace_started", False) and not getattr(item, "_trace_stopped", False):
            with suppress(Exception):
                context.tracing.stop()
                item._trace_stopped = True


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    context: Optional[BrowserContext] = item.funcargs.get("context")
    if context and not getattr(item, "_trace_started", False):
        with suppress(Exception):
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            item._trace_started = True
