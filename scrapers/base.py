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
