import math
import re

from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class IstexScraper(BaseScraper):
    source_id    = "istex"
    display_name = "Istex"
    site_url     = "https://istex.is"
    BASE_URL     = "https://istex.is/vorur/"

    def scrape(self):
        driver = self._make_driver()
        try:
            page_count = 1
            links = self._get_yarn_links(driver, page_count)
            print("Found {} yarn links".format(len(links)))
            yield from self._get_yarn_details(driver, links)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        seen = set()
        links = []
        driver.get(self.BASE_URL)
        print("Scanning page")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-column-clickable]"))
            )
            for el in driver.find_elements(By.CSS_SELECTOR, "[data-column-clickable]"):
                path = el.get_attribute("data-column-clickable")
                if path and "/vorur/" in path:
                    href = "https://istex.is" + path.rstrip("/")
                    if href not in seen:
                        seen.add(href)
                        links.append(href)
        except Exception as e:
            print(f"Page error: {e}")
        print(links)
        return links

    def _get_yarn_details(self, driver, links: list[str]):
        from selenium.common.exceptions import WebDriverException
        idx = 0
        while idx < len(links):
            url = links[idx]
            print("Checking yarn link: {}".format(url))
            try:
                driver.get(url)
            except Exception as e:
                if "tab crashed" in str(e).lower():
                    print(f"Tab crashed on {url}, restarting driver and retrying...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = self._make_driver()
                    continue
                print(f"Skipping {url}: {e}")
                idx += 1
                continue
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.elementor-heading-title"))
                )
                base_name = driver.find_element(By.CSS_SELECTOR, "h1.elementor-heading-title").text.strip()
                fiber = self._parse_fiber(driver)
                print(base_name)
                cards = driver.find_elements(By.CSS_SELECTOR, "article.elementor-post.elementor-grid-item")
                for card in cards:
                    try:
                        colour_name = card.find_element(By.CSS_SELECTOR, "h3.elementor-post__title a").text.strip()
                        img = card.find_element(By.CSS_SELECTOR, ".elementor-post__thumbnail img")
                        image_url = img.get_attribute("data-lazy-src") or img.get_attribute("src")
                    except Exception:
                        continue
                    if not colour_name:
                        continue
                    name = f"{base_name}: {colour_name}"
                    colour_slug = colour_name.lower().replace(" ", "-").replace("/", "-")
                    print(f"  {name}")
                    yield {
                        "name": name,
                        "url": f"{url}#color-{colour_slug}",
                        "image_url": image_url,
                        "fiber": fiber,
                        "yarn_type": "",
                    }
            except Exception as e:
                print(f"Detail error for {url}: {e}")
            idx += 1

    @staticmethod
    def _parse_fiber(driver) -> str:
        try:
            p = driver.find_element(By.CSS_SELECTOR, ".elementor-widget-container p")
            text = p.text
            if "Efni" in text:
                return text.split("Efni")[1].split(":")[1].split("\n")[0].strip().lstrip("\xa0").strip()
        except Exception:
            pass
        return ""
