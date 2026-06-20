from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from .base import BaseScraper


class IceYarnsScraper(BaseScraper):
    source_id = "ice_yarns"
    display_name = "Ice Yarns"
    site_url = "https://www.iceyarns.net"
    BASE_URL = "https://www.iceyarns.net/yarn/page/{}"

    def scrape(self) -> list[dict]:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        try:
            page_count = self._get_page_count(driver)
            links = self._get_yarn_links(driver, page_count)
            return self._get_yarn_details(driver, links)
        finally:
            driver.quit()

    def _get_page_count(self, driver) -> int:
        print("Getting page count...")
        driver.get(self.BASE_URL.format(1))
        count = 1
        while self._page_has_yarns(driver) and count < 500:
            count += 1
            driver.get(self.BASE_URL.format(count))
        page_count = count - 1
        print(f"{page_count} pages found")
        return page_count

    def _page_has_yarns(self, driver) -> bool:
        try:
            ul = driver.find_element(By.ID, "innerlist")
            return len(ul.find_elements(By.TAG_NAME, "li")) > 0
        except Exception:
            return False

    def _get_yarn_links(self, driver, page_count: int) -> list[str]:
        links = []
        for i in range(1, page_count + 1):
            driver.get(self.BASE_URL.format(i))
            print(f"Scanning page {i}/{page_count}")
            try:
                ul = driver.find_element(By.ID, "innerlist")
                for a in ul.find_elements(By.XPATH, ".//li//a"):
                    if not _is_lot(a.text):
                        links.append(a.get_attribute("href"))
            except Exception as e:
                print(f"Page {i} error: {e}")
        return links

    def _get_yarn_details(self, driver, links: list[str]) -> list[dict]:
        results = []
        for url in links:
            driver.get(url)
            try:
                img = driver.find_element(
                    By.XPATH,
                    '/html/body/div[4]/div[5]/div[1]/div[1]/div[1]/div[1]/ul[@class="cloud_small"]/li[2]/a/img',
                )
                name_el = driver.find_element(
                    By.XPATH,
                    '//*[@id="pdm"]/div[2]/div[@class="product-detail-title"]/span',
                )
                name = name_el.text
                if not _is_lot(name):
                    print(f"Got: {name}")
                    results.append({
                        "name": name,
                        "url": url,
                        "image_url": img.get_attribute("src"),
                    })
            except Exception as e:
                print(f"Detail error for {url}: {e}")
        return results


def _is_lot(name: str) -> bool:
    return any(word in name for word in ("Lot", "Shades", "Mixed", "Leftover", "Needle", "Hook"))
