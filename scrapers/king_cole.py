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

    def scrape(self):
        driver = self._make_driver()
        try:
            page_count = self._get_page_count(driver)
            print("Found {} pages".format(page_count))
            yield from self._scrape_all_pages(driver, page_count)
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

        try:
            pagination_items = driver.find_elements(By.CSS_SELECTOR, ".pagination a.page-link")
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

    def _scrape_all_pages(self, driver, page_count: int):
        seen = set()

        for i in range(1, page_count + 1):
            print(f"Scanning page {i}/{page_count}")
            try:
                time.sleep(2)

                product_links = driver.execute_script("""
                return Array.from(document.querySelectorAll('a[href*="/product/"]'))
                    .map(a => a.href)
                    .filter((h, idx, arr) => arr.indexOf(h) === idx && h.includes('/product/'));
                """)

                print(f"  Found {len(product_links)} items on page {i}")

                # Process each link immediately without storing
                for href in product_links:
                    if href not in seen and "/product/" in href:
                        seen.add(href)
                        result = self._get_yarn_details(driver, href)
                        if result:
                            yield result

                # Navigate to next page
                if i < page_count:
                    try:
                        driver.execute_script("""
                        var modals = document.querySelectorAll('.modal-container, .modal, [role="dialog"]');
                        for (var m of modals) {
                            var closeBtn = m.querySelector('[aria-label*="close"], [aria-label*="Close"], .close, button[type="button"]');
                            if (closeBtn) closeBtn.click();
                            else m.style.display = 'none';
                        }
                        """)
                        time.sleep(0.5)

                        pagination_links = driver.find_elements(By.CSS_SELECTOR, ".pagination a.page-link")
                        if len(pagination_links) > i:
                            pagination_links[i].click()
                            time.sleep(2)
                    except Exception as e:
                        print(f"  Error clicking page {i+1}: {e}")
                        break
            except Exception as e:
                print(f"Page {i} error: {e}")
                break

    def _get_yarn_details(self, driver, url: str):
        print("Checking yarn link: {}".format(url))
        try:
            driver.execute_script("window.stop();")
            driver.get(url)
            time.sleep(0.8)
        except Exception as e:
            if "tab crashed" in str(e).lower():
                print(f"  Tab crashed, skipping")
            else:
                print(f"  Skipping (load error): {e}")
            return None

        try:
            try:
                base_name = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
            except Exception:
                base_name = "Unknown Yarn"

            if not base_name or base_name == "Unknown Yarn":
                print(f"  No product title found")
                return None

            # Check if it's actually a yarn product (has fiber info)
            try:
                driver.find_element(By.XPATH, "//h3[contains(text(), 'Contains')]/following-sibling::p")
            except Exception:
                # If no fiber info, it's likely a pattern/book, skip it
                print(f"  Not a yarn product (no fiber info), skipping")
                return None

            print(f"  {base_name}")

            result = self._scrape_colour(driver, url, base_name, None, [])
            # Aggressively clean up memory
            driver.execute_script("document.body.innerHTML=''; window.gc && window.gc();")
            return result
        except Exception as e:
            print(f"  Error: {e}")
            return None

    @staticmethod
    def _scrape_colour(driver, url, base_name, variant, all_variants):
        if variant is not None:
            driver.execute_script("arguments[0].click();", variant)
            time.sleep(0.5)

        try:
            image_url = None
            try:
                img = driver.find_element(By.CSS_SELECTOR, ".wp-post-image, img.woocommerce-product-gallery__image img")
                image_url = img.get_attribute("src") or img.get_attribute("data-src")
            except Exception:
                pass

            fiber = ""
            try:
                fiber_el = driver.find_element(By.XPATH, "//h3[contains(text(), 'Contains')]/following-sibling::p")
                fiber = fiber_el.text.strip()
            except Exception:
                pass

            yarn_type = ""
            try:
                weight_el = driver.find_element(By.XPATH, "//h3[contains(text(), 'Ball Weight')]/following-sibling::p")
                yarn_type = weight_el.text.strip()
            except Exception:
                pass

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
