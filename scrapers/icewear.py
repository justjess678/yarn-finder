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


    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        seen = set()
        links = []
        driver.get(self.BASE_URL)
        print("Scanning page")
        try:
            ul = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".grid.gap-4.grid-cols-2"))
            )
            for a in ul.find_elements(By.XPATH, ".//div//div//div//a"):
                href = a.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    links.append(href)
        except Exception as e:
            print(f"Page error: {e}")
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
            except WebDriverException as e:
                if "tab crashed" in str(e).lower():
                    print(f"Tab crashed on {url}, restarting driver and retrying...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = self._make_driver()
                    continue
                print(f"Detail error for {url}: {e}")
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
