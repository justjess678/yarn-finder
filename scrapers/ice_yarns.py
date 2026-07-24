import re
import requests

from .base import BaseScraper


class IceYarnsScraper(BaseScraper):
    source_id    = "ice_yarns"
    display_name = "Ice Yarns"
    site_url     = "https://www.iceyarns.com?dt_id=2686179"
    _PRODUCTS_URL = "https://www.iceyarns.com/collections/yarn/products.json"

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
        if _is_lot(base_name):
            return

        # find which option index is the color (0-based → option1/option2/option3)
        color_idx = next(
            (i for i, o in enumerate(product["options"]) if o["name"].lower() == "color"),
            None,
        )
        opt_key = f"option{color_idx + 1}" if color_idx is not None else None

        # map variant id → image src
        image_by_variant = {}
        for img in product["images"]:
            for vid in img.get("variant_ids", []):
                image_by_variant[vid] = img["src"]

        fiber = _parse_fiber(product.get("body_html", ""))
        seen_colours = set()
        for variant in product["variants"]:
            color = variant.get(opt_key) if opt_key else None
            colour_label = color or variant["title"]
            if colour_label in seen_colours:
                continue
            seen_colours.add(colour_label)

            image_url = image_by_variant.get(variant["id"]) or (
                product["images"][0]["src"] if product["images"] else None
            )
            name = f"{base_name}: {colour_label}" if color else base_name
            print(f"  {name}")
            yield {
                "name": name,
                "url": f"https://www.iceyarns.com/products/{product['handle']}?variant={variant['id']}&dt_id=2686179",
                "image_url": image_url,
                "fiber": fiber,
                "yarn_type": product.get("product_type", ""),
            }


def _is_lot(name: str) -> bool:
    return any(word in name for word in ("Lot", "Shades", "Mixed", "Leftover", "Needle", "Hook"))


def _parse_fiber(body_html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", body_html)
    m = re.search(r"Fiber Content:\s*(.+?)\s*Yarn Type:", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""
