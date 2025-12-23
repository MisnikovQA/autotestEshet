from typing import Optional

from playwright.sync_api import Page, Response

from src.ui.pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page, base_url: str, timeout_ms: int) -> None:
        super().__init__(page, base_url, timeout_ms)

    def open(self) -> Optional[Response]:
        return self.goto("/")
