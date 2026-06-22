from .base import *
import time


class DropsScraper(BaseScraper):
    source_id    = "drops"
    display_name = "DROPS"
    site_url     = "https://www.garnstudio.com"
    BASE_URL     = "https://www.garnstudio.com/yarns.php?cid=30"

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
        driver.set_page_load_timeout(8)
        driver.set_script_timeout(5)
        
        try:
            driver.get(self.BASE_URL)
        except Exception as e:
            print(f"Page load timed out: {str(e)[:50]}")
        
        print("Scanning listing page")
        time.sleep(3)
        
        # Get product divs from listing - don't wait, just extract
        yarn_divs = driver.find_elements(By.CSS_SELECTOR, ".yarns .yarn")
        print(f"Found {len(yarn_divs)} products")

        variant_count = 0
        for idx, yarn_div in enumerate(yarn_divs, 1):
            try:
                # Extract product name
                try:
                    name_elem = yarn_div.find_element(By.CSS_SELECTOR, ".prod_desc h3 a")
                    base_name = name_elem.text.strip()
                    url = name_elem.get_attribute("href")
                except Exception:
                    continue

                if not url:
                    continue

                # Extract fiber from extra-info
                fiber = ""
                try:
                    info_elem = yarn_div.find_element(By.CSS_SELECTOR, ".extra-info")
                    text = info_elem.text
                    lines = text.split('\n')
                    if lines:
                        fiber = lines[0].strip()
                except Exception:
                    pass

                # Extract image URL from listing
                image_url = "https://via.placeholder.com/150"
                try:
                    img = yarn_div.find_element(By.CSS_SELECTOR, ".img-cont img")
                    img_src = img.get_attribute("src")
                    if img_src:
                        image_url = img_src
                except Exception:
                    pass

                print(f"  {base_name}")
                yield {
                    "name": base_name,
                    "url": url,
                    "image_url": image_url,
                    "fiber": fiber,
                    "yarn_type": ""
                }
                variant_count += 1

            except Exception as e:
                print(f"  [{idx}] Error: {str(e)[:50]}")
                continue

        print(f"Total: {variant_count} products scraped")
