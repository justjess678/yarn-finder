from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time


class LionBrandScraper(BaseScraper):
    source_id    = "lion_brand"
    display_name = "Lion Brand"
    site_url     = "https://www.lionbrand.com"
    BASE_URL     = "https://www.lionbrand.com/collections/all-knitting-crochet-yarn"

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
        page = 1
        variant_count = 0

        while True:
            if page == 1:
                url = self.BASE_URL
            else:
                url = f"{self.BASE_URL}?page={page}"

            try:
                driver.get(url)
                print(f"Scanning page {page}")
            except Exception as e:
                print(f"Page load error: {str(e)[:50]}")
                break

            # Wait for products to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ss__results .ss__result"))
                )
            except Exception:
                print("Timeout waiting for products")
                break

            # Get products on this page
            product_items = driver.find_elements(By.CSS_SELECTOR, ".ss__results .ss__result")
            if not product_items:
                print("No products found, pagination complete")
                break

            print(f"  Found {len(product_items)} products on page {page}")

            for idx, item in enumerate(product_items, 1):
                try:
                    # Extract product link
                    try:
                        link_elem = item.find_element(By.CSS_SELECTOR, ".ProductItem__Wrapper")
                        product_url = link_elem.get_attribute("href")
                        if not product_url:
                            continue
                    except Exception:
                        continue

                    # Extract base product name
                    try:
                        name_elem = item.find_element(By.CSS_SELECTOR, ".ProductItem__Title")
                        base_name = name_elem.text.strip()
                    except Exception:
                        continue

                    # Extract image URL
                    image_url = "https://via.placeholder.com/150"
                    try:
                        img = item.find_element(By.CSS_SELECTOR, ".ss__result__image img")
                        img_src = img.get_attribute("src") or img.get_attribute("data-src")
                        if img_src:
                            image_url = img_src
                    except Exception:
                        pass

                    # Visit product page to get variants
                    try:
                        driver.execute_script("window.stop();")
                        driver.get(product_url)
                        time.sleep(0.5)

                        # Wait for color swatches
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#Item__Color .ColorSwatch__Radio"))
                            )
                        except Exception:
                            pass

                        # Get all color variants
                        swatches = driver.find_elements(By.CSS_SELECTOR, "#Item__Color .ColorSwatch__Radio")

                        if swatches:
                            print(f"    {base_name} ({len(swatches)} colors)")
                            for swatch in swatches:
                                variant_data = self._extract_variant(swatch, product_url, base_name, image_url)
                                if variant_data:
                                    yield variant_data
                                    variant_count += 1
                        else:
                            # No variants, yield base product
                            print(f"    {base_name}")
                            yield {
                                "name": base_name,
                                "url": product_url,
                                "image_url": image_url,
                                "fiber": "",
                                "yarn_type": ""
                            }
                            variant_count += 1

                    except Exception as e:
                        print(f"    Error visiting product: {str(e)[:40]}")
                        continue

                    finally:
                        # Memory cleanup
                        try:
                            driver.execute_script("document.body.innerHTML=''; window.gc && window.gc();")
                        except Exception:
                            pass

                except Exception as e:
                    print(f"    Error: {str(e)[:50]}")
                    continue

            page += 1
            time.sleep(1)

        print(f"Total: {variant_count} variants scraped")

    @staticmethod
    def _extract_variant(swatch, product_url, base_name, base_image):
        try:
            # Get color name from value attribute
            color_name = swatch.get_attribute("value")
            if not color_name:
                return None

            # Get full label from data-value-label (e.g., "Sponge [2216-S001]")
            full_label = swatch.get_attribute("data-value-label")

            # Get image URL from the swatch label's background-image
            image_url = base_image
            try:
                label = swatch.find_element(By.XPATH, "following-sibling::label")
                img_elem = label.find_element(By.CSS_SELECTOR, ".ColorSwatch__Image")
                style = img_elem.get_attribute("style")
                if style and "url(" in style:
                    match = re.search(r'url\(([^)]+)\)', style)
                    if match:
                        img_src = match.group(1).strip("'\"")
                        if img_src:
                            image_url = img_src
            except Exception:
                pass

            # Create variant name with color code if available
            if full_label and "[" in full_label:
                variant_name = f"{base_name} {full_label}"
            else:
                variant_name = f"{base_name} {color_name}"

            return {
                "name": variant_name,
                "url": f"{product_url}#color-{color_name.lower().replace(' ', '-')}",
                "image_url": image_url,
                "fiber": "",
                "yarn_type": ""
            }
        except Exception:
            return None
