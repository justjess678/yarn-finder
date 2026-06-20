import requests

from .base import BaseScraper


class HobbiiScraper(BaseScraper):
    source_id    = "hobbii"
    display_name = "Hobbii"
    site_url     = "https://www.hobbii.com/"
    _PRODUCTS_URL = "https://hobbii.com/collections/yarn/products.json"

    def scrape(self):
        page = 1
        while True:
            resp = requests.get(self._PRODUCTS_URL, params={"limit": 250, "page": page}, timeout=15)
            resp.raise_for_status()
            products = resp.json()["products"]
            if not products:
                break
            print(f"Page {page}: {len(products)} products")
            for product in products:
                yield from self._extract_colours(product)
            page += 1

    @staticmethod
    def _extract_colours(product: dict):
        base_name = product["title"]

        image_by_variant = {}
        for img in product["images"]:
            for vid in img.get("variant_ids", []):
                image_by_variant[vid] = img["src"]

        seen_colours = set()
        for variant in product["variants"]:
            colour_label = variant.get("option1") or variant["title"]
            if colour_label in seen_colours:
                continue
            seen_colours.add(colour_label)

            image_url = image_by_variant.get(variant["id"]) or (
                product["images"][0]["src"] if product["images"] else None
            )
            name = f"{base_name}: {colour_label}"
            print(f"  {name}")
            yield {
                "name": name,
                "url": f"https://hobbii.com/products/{product['handle']}?variant={variant['id']}",
                "image_url": image_url,
                "fiber": "",
                "yarn_type": product.get("product_type", ""),
            }
