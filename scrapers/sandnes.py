from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time


class SandnesScraper(BaseScraper):
    source_id    = "sandnes"
    display_name = "Sandnes"
    site_url     = "https://www.sandnes-garn.com"
    BASE_URL     = "https://www.sandnes-garn.com/yarn"

    def scrape(self):
        driver = self._make_driver()
        try:
            yield from self._scrape_all(driver)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    def _scrape_all(self, driver):
        driver.get(self.BASE_URL)
        print("Scanning listing page")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "products"))
            )

            # Get product links from listing
            product_items = driver.find_elements(By.CSS_SELECTOR, "li.item.product a.product-item-info")
            product_urls = [item.get_attribute("href") for item in product_items]
            print(f"Found {len(product_urls)} products")

            variant_count = 0
            for idx, url in enumerate(product_urls, 1):
                try:
                    driver.execute_script("window.stop();")
                    driver.get(url)
                    # Wait for swatches to render
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".swatch-option.image"))
                        )
                    except Exception:
                        pass

                    # Get product name from H1
                    try:
                        base_name = driver.find_element(By.TAG_NAME, "h1").text.strip()
                    except Exception:
                        continue

                    # Get fiber from description or attributes
                    fiber = ""
                    try:
                        attrs = driver.find_elements(By.CSS_SELECTOR, "[data-testid], .product-attribute, .description")
                        for attr in attrs:
                            text = attr.text.strip()
                            if "%" in text and len(text) < 100:
                                fiber = text
                                break
                    except Exception:
                        pass

                    # Extract variants from swatches (no clicking)
                    swatches = driver.find_elements(By.CSS_SELECTOR, ".swatch-option.image")
                    if swatches:
                        print(f"  {base_name} ({len(swatches)})")
                        for swatch in swatches:
                            variant_data = self._extract_variant(swatch, url, fiber)
                            if variant_data:
                                yield variant_data
                                variant_count += 1
                    else:
                        # No variants found
                        print(f"  {base_name}")
                        yield {
                            "name": base_name,
                            "url": url,
                            "image_url": None,
                            "fiber": fiber,
                            "yarn_type": ""
                        }
                        variant_count += 1

                except Exception as e:
                    print(f"  [{idx}] Error: {str(e)[:50]}")

                finally:
                    # Aggressive memory cleanup
                    try:
                        driver.execute_script("document.body.innerHTML=''; window.gc && window.gc();")
                    except Exception:
                        pass

            print(f"Total: {variant_count} variants")

        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    def _extract_variant(swatch, base_url, fiber):
        try:
            product_name = swatch.get_attribute("data-product-name")
            if not product_name:
                return None

            color_code = swatch.get_attribute("data-option-label")

            style = swatch.get_attribute("style")
            image_url = None
            if style:
                match = re.search(r'url\(([^)]+)\)', style)
                if match:
                    image_url = match.group(1).strip("'\"")

            return {
                "name": product_name.strip(),
                "url": f"{base_url}#{color_code.lower()}" if color_code else base_url,
                "image_url": image_url,
                "fiber": fiber,
                "yarn_type": ""
            }
        except Exception:
            return None
