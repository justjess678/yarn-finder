from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SandnesScraper(BaseScraper):
    source_id    = "sandnes"
    display_name = "Sandnes"
    site_url     = "https://www.sandnes-garn.com"
    BASE_URL     = "https://www.sandnes-garn.com/yarn"

    def scrape(self):
        driver = self._make_driver()
        try:
            yield from self._scrape_listing(driver)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    def _scrape_listing(self, driver):
        driver.get(self.BASE_URL)
        print("Scanning listing page")
        try:
            # Wait for products to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "products"))
            )

            # Get all product items
            products = driver.find_elements(By.CSS_SELECTOR, "li.item.product")
            print(f"Found {len(products)} products")

            for product in products:
                try:
                    # Get product link
                    link = product.find_element(By.CSS_SELECTOR, "a.product-item-info")
                    url = link.get_attribute("href")

                    # Get product name
                    name = product.find_element(By.CSS_SELECTOR, ".product-item-name").text.strip()

                    # Get fiber/attributes
                    fiber = ""
                    try:
                        fiber = product.find_element(By.CSS_SELECTOR, ".product-item-attribute").text.strip()
                    except Exception:
                        pass

                    # Get image
                    image_url = None
                    try:
                        img = product.find_element(By.CSS_SELECTOR, ".product-item-photo img")
                        image_url = img.get_attribute("src")
                    except Exception:
                        pass

                    print(f"  {name}")

                    yield {
                        "name": name,
                        "url": url,
                        "image_url": image_url,
                        "fiber": fiber,
                        "yarn_type": ""
                    }
                except Exception as e:
                    print(f"  Error processing product: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping listing: {e}")
