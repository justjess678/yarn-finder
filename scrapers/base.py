from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from abc import ABC, abstractmethod
from typing import Iterator


class BaseScraper(ABC):
    source_id: str = ""
    display_name: str = ""
    site_url: str = ""

    @abstractmethod
    def scrape(self) -> Iterator[dict]:
        """Yields dicts with keys: name, url, image_url (and optionally fiber, yarn_type)."""
        pass

    @staticmethod
    def _make_driver():
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Chrome(options=options)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        driver.set_page_load_timeout(30)
        return driver

    @staticmethod
    def _accept_cookies(driver):
        try:
            driver.find_element(By.XPATH, "//button[contains(., 'Accept All')]").click()
        except Exception:
            pass
