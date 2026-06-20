"""
Quick manual test for LoveCraftsScraper.
Run from the scrapers/ directory: python test_lovecrafts.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from lovecrafts import LoveCraftsScraper

TEST_YARN_URL = "https://www.lovecrafts.com/en-gb/p/paintbox-simply-dk"

def test_page_count():
    print("--- test_page_count ---")
    scraper = LoveCraftsScraper()
    driver = scraper._make_driver()
    try:
        count = scraper._get_page_count(driver)
        print(f"Page count: {count}")
        assert isinstance(count, int) and count > 0, "Expected a positive int"
        print("PASS")
    finally:
        driver.quit()

def test_single_yarn(url=TEST_YARN_URL):
    print(f"\n--- test_single_yarn: {url} ---")
    scraper = LoveCraftsScraper()
    driver = scraper._make_driver()
    try:
        results = scraper._get_yarn_details(driver, [url])
        if not results:
            print("FAIL — no results returned")
            return
        for r in results:
            print(f"  name:      {r['name']}")
            print(f"  image_url: {r['image_url']}")
            print()
        print(f"PASS — {len(results)} colour(s) found")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else TEST_YARN_URL
    test_page_count()
    test_single_yarn(url)
