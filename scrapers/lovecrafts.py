import math
import re

from base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoveCraftsScraper(BaseScraper):
    source_id    = "lovecrafts"
    display_name = "LoveCrafts"
    site_url     = "https://www.lovecrafts.com/"
    BASE_URL     = "https://www.lovecrafts.com/en-gb/l/yarns?page={}"

    def scrape(self) -> list[dict]:
        driver = self._make_driver()
        try:
            page_count = self._get_page_count(driver)
            links = self._get_yarn_links(driver, page_count)
            return self._get_yarn_details(driver, links)
        finally:
            driver.quit()

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
        return driver

    @staticmethod
    def _accept_cookies(driver):
        try:
            driver.find_element(By.XPATH, "//button[contains(., 'Accept All')]").click()
        except Exception:
            pass

    def _get_page_count(self, driver) -> int:
        print("Getting page count...")
        driver.get(self.BASE_URL.format(1))
        self._accept_cookies(driver)
        counter = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "navbar__counter__label"))
        )
        text = counter.text
        total = int(re.search(r'of (\d+)', text).group(1))
        per_page = int(re.search(r'\d+[—–-](\d+)', text).group(1))
        return math.ceil(total / per_page)

    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        seen = set()
        links = []
        for i in range(1, page_count + 1):
            driver.get(self.BASE_URL.format(i))
            print(f"Scanning page {i}/{page_count}")
            try:
                ul = driver.find_element(By.CLASS_NAME, "products__grid")
                for a in ul.find_elements(By.XPATH, ".//li//div//a"):
                    href = a.get_attribute("href")
                    if href and href not in seen:
                        seen.add(href)
                        links.append(href)
            except Exception as e:
                print(f"Page {i} error: {e}")
        return links

    def _get_yarn_details(self, driver, links: list[str]) -> list[dict]:
        results = []
        for url in links:
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "variant-name"))
                )
                base_name = driver.find_element(
                    By.XPATH, "//h1[contains(@class,'sf-heading__title')]"
                ).text
                variants = driver.find_elements(By.CLASS_NAME, "grid-variants__variant")
                seen_colours = set()
                for variant in [None] + list(variants):
                    result = self._scrape_colour(driver, url, base_name, variant, variants)
                    if result and result["name"] not in seen_colours:
                        seen_colours.add(result["name"])
                        results.append(result)
            except Exception as e:
                print(f"Detail error for {url}: {e}")
        return results

    @staticmethod
    def _scrape_colour(driver, url, base_name, variant, all_variants):
        if variant is not None:
            driver.execute_script("arguments[0].click();", variant)
        try:
            color_el = driver.find_element(By.CLASS_NAME, "variant-name")
            name = f"{base_name}: {color_el.text}"

            # Image src is on the <img> inside the variant's image-wrapper span.
            # For the default run (no click), use the first variant.
            source_variant = variant or (all_variants[0] if all_variants else None)
            image_url = None
            if source_variant:
                image_url = source_variant.find_element(
                    By.XPATH, ".//span[@data-testid='image-wrapper']//img"
                ).get_attribute("src")

            return {"name": name, "url": url, "image_url": image_url}
        except Exception as e:
            print(f"  Colour error ({url}): {e}")
            return None
