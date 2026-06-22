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
    BASE_URL     = "https://www.kingcole.com/product-category/yarn/"

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
        print("Getting page count...")
        driver.get(self.BASE_URL)
        self._accept_cookies(driver)
        time.sleep(5)

        # WooCommerce pagination - look for page numbers
        try:
            # Try common WooCommerce selectors
            pagination_items = driver.find_elements(By.CSS_SELECTOR,
                "a.page-numbers, .woocommerce-pagination a")
            page_numbers = []
            for el in pagination_items:
                text = el.text.strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                result = max(page_numbers)
                print(f"Found {result} pages")
                return result
        except Exception as e:
            print(f"Error finding pagination: {e}")

        print("Defaulting to 1 page")
        return 1

    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        seen = set()
        links = []

        for i in range(1, page_count + 1):
            print(f"Scanning page {i}/{page_count}")
            try:
                time.sleep(2)

                # Use the selector that worked: a[href*="/product/"]
                product_links = driver.execute_script("""
                return Array.from(document.querySelectorAll('a[href*="/product/"]'))
                    .map(a => a.href)
                    .filter((h, idx, arr) => arr.indexOf(h) === idx && h.includes('/product/'))
                    .slice(0, 50);
                """)

                for href in product_links:
                    if href not in seen and "/product/" in href:
                        seen.add(href)
                        links.append(href)

                print(f"  Found {len(product_links)} items on page {i}")

                # Click next page button if not on last page
                if i < page_count:
                    driver.execute_script("""
                    var nextLink = document.querySelector('a.next');
                    if (nextLink) nextLink.click();
                    """)
                    time.sleep(2)
            except Exception as e:
                print(f"Page {i} error: {e}")
                break

        print(f"Found {len(links)} yarn links total")
        return links

    def _get_yarn_details(self, driver, links: list[str]):
        idx = 0
        while idx < len(links):
            url = links[idx]
            print("Checking yarn link: {}".format(url))
            try:
                driver.get(url)
                time.sleep(1.5)
            except Exception as e:
                if "tab crashed" in str(e).lower():
                    print(f"  Tab crashed, restarting driver...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = self._make_driver_with_images()
                    continue
                print(f"  Skipping (load error): {e}")
                idx += 1
                continue

            try:
                # Get product name quickly
                try:
                    base_name = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
                except Exception:
                    base_name = "Unknown Yarn"

                if not base_name or base_name == "Unknown Yarn":
                    print(f"  No product title found")
                    idx += 1
                    continue

                print(f"  {base_name}")

                # Yield main product
                result = self._scrape_colour(driver, url, base_name, None, [])
                if result:
                    yield result
            except Exception as e:
                print(f"  Error: {e}")
            idx += 1

    @staticmethod
    def _scrape_colour(driver, url, base_name, variant, all_variants):
        if variant is not None:
            driver.execute_script("arguments[0].click();", variant)
            time.sleep(0.5)

        try:
            # Get main product image
            image_url = None
            try:
                img = driver.find_element(By.CSS_SELECTOR, ".wp-post-image, img.woocommerce-product-gallery__image img")
                image_url = img.get_attribute("src") or img.get_attribute("data-src")
            except Exception:
                pass

            # Get fiber/blend info
            fiber = ""
            try:
                fiber_el = driver.find_element(By.XPATH, "//th[contains(text(), 'Blend')]/../td | //td[contains(text(), 'Blend')]/../td")
                fiber = fiber_el.text.strip()
            except Exception:
                pass

            # Get yarn weight/type
            yarn_type = ""
            try:
                weight_el = driver.find_element(By.XPATH, "//th[contains(text(), 'Weight')]/../td | //th[contains(text(), 'Yarn Weight')]/../td")
                yarn_type = weight_el.text.strip()
            except Exception:
                pass

            # Get color from variant or page
            color_text = base_name
            try:
                color_el = driver.find_element(By.CSS_SELECTOR, ".variable-item-color, .product-attribute, [data-attribute_name*=color]")
                color_text = color_el.text.strip() or base_name
            except Exception:
                pass

            name = f"{base_name}: {color_text}" if color_text != base_name else base_name
            colour_slug = color_text.lower().replace(" ", "-").replace("/", "-")

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
