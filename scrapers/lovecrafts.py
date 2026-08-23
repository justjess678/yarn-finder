import math
import re

from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoveCraftsScraper(BaseScraper):
    source_id    = "lovecrafts"
    display_name = "LoveCrafts"
    site_url     = "https://www.lovecrafts.com/?a_aid=81052868"
    BASE_URL     = "https://www.lovecrafts.com/en-gb/l/yarns?page={}"

    def scrape(self):
        driver = self._make_driver()
        try:
            page_count = self._get_page_count(driver)
            print("Found {} pages".format(page_count))
            driver.quit()
            driver = self._make_driver()
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
        driver.get(self.BASE_URL.format(1))
        self._accept_cookies(driver)
        counter = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "navbar__counter__label"))
        )
        text = counter.text
        total = int(re.search(r'of (\d+)', text).group(1))
        per_page = int(re.search(r'\d+[-–-](\d+)', text).group(1))
        return math.ceil(total / per_page)

    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        seen = set()
        links = []

        i = 1
        while i <= page_count:
            url = self.BASE_URL.format(i)
            print(f"Scanning page {i}/{page_count}")

            try:
                driver.get(url)

                ul = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "products__grid")
                    )
                )

                for a in ul.find_elements(By.XPATH, ".//li//div//a"):
                    href = a.get_attribute("href")
                    if href and href not in seen:
                        seen.add(href)
                        links.append(href)

                # Success - move on to the next page
                i += 1

            except Exception as e:
                msg = str(e).lower()

                if (
                        "tab crashed" in msg
                        or "connection refused" in msg
                        or "max retries exceeded" in msg
                        or "failed to establish a new connection" in msg
                ):
                    print(f"Driver crashed on page {i}, restarting and retrying...")

                    try:
                        driver.quit()
                    except Exception:
                        pass

                    driver = self._make_driver()

                    # Retry the SAME page
                    continue

                print(f"Skipping page {i}: {e}")

                # Non-fatal error, move to the next page
                i += 1

        print(links)
        return links

    def _get_yarn_details(self, driver, links: list[str]):
        idx = 0

        while idx < len(links):
            url = links[idx]
            print(f"Checking yarn link: {url}")

            try:
                driver.get(url)

            except Exception as e:
                msg = str(e).lower()

                if (
                        "tab crashed" in msg
                        or "connection refused" in msg
                        or "max retries exceeded" in msg
                        or "failed to establish a new connection" in msg
                ):
                    print(f"Driver crashed on {url}, restarting and retrying...")

                    try:
                        driver.quit()
                    except Exception:
                        pass

                    driver = self._make_driver()

                    # Retry the SAME URL
                    continue

                print(f"Skipping {url}: {e}")
                idx += 1
                continue

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "variant-name")
                    )
                )

                base_name = driver.find_element(
                    By.XPATH,
                    "//h1[contains(@class,'sf-heading__title')]"
                ).text

                print(base_name)

                variants = driver.find_elements(
                    By.CLASS_NAME,
                    "grid-variants__variant"
                )

                seen_colours = set()

                for variant in [None] + list(variants):
                    result = self._scrape_colour(
                        driver,
                        url,
                        base_name,
                        variant,
                        variants,
                    )

                    if result and result["name"] not in seen_colours:
                        seen_colours.add(result["name"])
                        yield result

                # Success - move to the next yarn
                idx += 1

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

            fiber = driver.find_element(By.XPATH, '//*[@data-testid="Blend"]//dd').text
            yarn_type = driver.find_element(By.XPATH, '//*[@data-testid="Yarn Weight"]//dd').text
            colour_slug = color_el.text.lower().replace(" ", "-").replace("/", "-")
            return {
                "name": name,
                "url": f"{url}?utm_medium=affiliate&a_aid=81052868#color-{colour_slug}",
                "image_url": image_url,
                "fiber": fiber,
                "yarn_type": yarn_type
            }
        except Exception as e:
            print(f"  Colour error ({url}): {e}")
            return None
