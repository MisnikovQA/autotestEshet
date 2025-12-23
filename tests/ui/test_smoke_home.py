import allure
import pytest


@allure.title("Главная страница Eshet открывается (HTTP 200-399)")
@pytest.mark.ui
@pytest.mark.smoke
def test_home_page_is_reachable(home_page):
    response = home_page.open()
    home_page.assert_response_ok(response)
