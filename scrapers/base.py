from abc import ABC, abstractmethod


class BaseScraper(ABC):
    source_id: str = ""
    display_name: str = ""
    site_url: str = ""

    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        Scrape yarn data from the source.
        Returns a list of dicts with keys: name, url, image_url
        """
        pass
