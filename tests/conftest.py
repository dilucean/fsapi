import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "base_url": "http://127.0.0.1:8000",
    }


@pytest.fixture
def page(page: Page):
    page.set_default_timeout(10000)
    return page
