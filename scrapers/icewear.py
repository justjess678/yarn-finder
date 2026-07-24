import math
import re

from .base import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class IcewearScraper(BaseScraper):
    source_id    = "icewear"
    display_name = "Icewear Garn"
    site_url     = "https://icewear.is"
    BASE_URL     = "https://icewear.is/is-IS/prjonavorur/dokkur"

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
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("Scanning page")
        try:
            print(driver.current_url)
            print(driver.title)
            print(driver.page_source[:500])
            ul = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".grid.gap-4.grid-cols-2"))
            )
            for a in ul.find_elements(By.XPATH, ".//div//div//div//a"):
                href = a.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    links.append(href)
        except Exception as e:
            import traceback
            print(f"Page error: {type(e).__name__}: {repr(e)}")
            traceback.print_exc()
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
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
                h1 = driver.find_element(By.TAG_NAME, "h1")
                spans = h1.find_elements(By.TAG_NAME, "span")
                base_name = spans[0].text.strip() if spans else h1.text.strip()
                fiber = spans[1].text.strip() if len(spans) > 1 else ""
                print(base_name)
                variants = driver.find_elements(
                    By.XPATH, "/html/body/main/div/div[2]/div[2]/div[2]/div/div/div/a"
                )
                seen_colours = set()
                for variant in variants:
                    try:
                        driver.execute_script("arguments[0].click();", variant)
                        colour_p = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "p.mb-4.font-medium.leading-6.w-fit")
                            )
                        )
                        colour_name = colour_p.text.replace("Litur: ", "").strip()
                        image_url = driver.find_element(
                            By.CSS_SELECTOR, "img[fetchpriority='high']"
                        ).get_attribute("src")
                        name = f"{base_name}: {colour_name}"
                        if name in seen_colours:
                            continue
                        seen_colours.add(name)
                        colour_slug = colour_name.lower().replace(" ", "-").replace("/", "-")
                        variant_url = driver.current_url.split("#")[0] + f"#color-{colour_slug}"
                        print(f"  {name}")
                        yield {
                            "name": name,
                            "url": variant_url,
                            "image_url": image_url,
                            "fiber": fiber,
                            "yarn_type": "",
                        }
                    except Exception as e:
                        print(f"  Colour error: {e}")
            except Exception as e:
                print(f"Detail error for {url}: {e}")
            idx += 1
