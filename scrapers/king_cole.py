import math
import re
import time

from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class KingColeScraper(BaseScraper):
    source_id    = "king_cole"
    display_name = "King Cole"
    site_url     = "https://www.kingcole.com/"
    BASE_URL     = "https://www.kingcole.com/yarns"

    def _make_driver_with_images(self):
        from selenium.webdriver.chrome.options import Options
        from selenium import webdriver
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        # Don't disable images - King Cole might need them for routing
        options.add_argument("--js-flags=--max-old-space-size=256")
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
        driver.set_page_load_timeout(300)
        return driver

    def scrape(self):
        driver = self._make_driver_with_images()
        try:
            page_count = self._get_page_count(driver)
            print("Found {} pages".format(page_count))
            links = self._get_yarn_links(driver, page_count)
            print("Found {} yarn links".format(len(links)))
            yield from self._get_yarn_details(driver, links)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    def _get_page_count(self, driver) -> int:
        import time
        print("Getting page count...")
        driver.get(self.BASE_URL)
        self._accept_cookies(driver)

        # Wait for any content to load, check multiple times
        for wait_time in [3, 5, 10]:
            time.sleep(wait_time - (wait_time - 3))
            page_source = driver.page_source
            if "pageNotFound" not in page_source and "wooFilterItems" in page_source:
                print(f"Page loaded after {wait_time}s")
                break
            if wait_time == 10:
                print(f"Still showing 404 after {wait_time}s")

        # Check for pagination
        try:
            pagination_items = driver.find_elements(By.CSS_SELECTOR, "li.page-numbers a.page-link")
            page_numbers = []
            for el in pagination_items:
                text = el.text.strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                return max(page_numbers)
        except Exception:
            pass

        print("Defaulting to 7 pages")
        return 7

    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        seen = set()
        links = []

        for i in range(1, page_count + 1):
            print(f"Scanning page {i}/{page_count}")
            try:
                time.sleep(3)

                # Use JavaScript to find product links since DOM rendering is failing
                js_code = """
                return Array.from(document.querySelectorAll('a[href*="/product/"]')).map(a => a.href).filter(h => h);
                """
                product_links = driver.execute_script(js_code)

                if not product_links:
                    print(f"  No product links found via JS, trying CSS selector...")
                    grid = driver.find_element(By.CSS_SELECTOR, "div.wooFilterItems")
                    for a in grid.find_elements(By.CSS_SELECTOR, ".itemSmall a"):
                        href = a.get_attribute("href")
                        if href and "/product/" in href:
                            product_links.append(href)

                for href in product_links:
                    if href not in seen:
                        seen.add(href)
                        links.append(href)

                print(f"  Found {len(product_links)} items on page {i}")

                # Click next page button if not on last page
                if i < page_count:
                    next_page_num = i + 1
                    driver.execute_script(f"""
                    var links = Array.from(document.querySelectorAll('a'));
                    var nextLink = links.find(a => a.textContent.trim() === '{next_page_num}');
                    if (nextLink) nextLink.click();
                    """)
                    time.sleep(3)
            except Exception as e:
                print(f"Page {i} error: {e}")
                break

        print(f"Found {len(links)} yarn links total")
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
                    continue  # retry same url
                print(f"Skipping {url}: {e}")
                idx += 1
                continue
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "variant-name"))
                )
                base_name = driver.find_element(
                    By.XPATH, "//h1[contains(@class,'sf-heading__title')]"
                ).text
                print(base_name)
                variants = driver.find_elements(By.CLASS_NAME, "grid-variants__variant")
                seen_colours = set()
                for variant in [None] + list(variants):
                    result = self._scrape_colour(driver, url, base_name, variant, variants)
                    if result and result["name"] not in seen_colours:
                        seen_colours.add(result["name"])
                        yield result
            except Exception as e:
                print(f"Detail error for {url}: {e}")
            idx += 1

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

            fiber = driver.find_element(By.XPATH, '//*[@data-testid="Blend"]//dd').text()
            yarn_type = driver.find_element(By.XPATH, '//*[@data-testid="Yarn Weight"]//dd').text()
            colour_slug = color_el.text.lower().replace(" ", "-").replace("/", "-")
            return {
                "name": name,
                "url": f"{url}#color-{colour_slug}",
                "image_url": image_url,
                "fiber": fiber,
                "yarn_type": yarn_type
            }
        except Exception as e:
            print(f"  Colour error ({url}): {e}")
            return None
