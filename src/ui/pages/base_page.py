from typing import Optional

from playwright.sync_api import Page, Response


class BasePage:
    def __init__(self, page: Page, base_url: str, timeout_ms: int) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = timeout_ms
        self.page.set_default_timeout(timeout_ms)

    def goto(self, path: str = "/") -> Optional[Response]:
        url = self._build_url(path)
        return self.page.goto(url, wait_until="domcontentloaded")

    def assert_response_ok(self, response: Optional[Response]) -> None:
        if response is None:
            raise AssertionError("Navigation did not return a response object.")
        status = response.status
        if not 200 <= status < 400:
            raise AssertionError(f"Unexpected response status: {status}")

    def _build_url(self, path: str) -> str:
        trimmed = path.lstrip("/")
        if not trimmed:
            return self.base_url
        return f"{self.base_url}/{trimmed}"
