import requests
from urllib.parse import quote

from .base import BaseScraper

CJ_BASE = "https://www.anrdoezrs.net/click-101816610-13759646"

def affiliate_link(url, sku):
    return (
        f"{CJ_BASE}"
        f"?url={quote(url, safe='')}"
        f"&cjsku={sku}"
    )


def trim_string_with_suffix(text, max_len=200):
    # If the string is already short enough, return it as is
    if len(text) <= max_len:
        return text

    # Split the string at the first colon
    if ":" in text:
        prefix, suffix = text.split(":", 1)
        suffix = ":" + suffix  # Keep the colon as part of the preserved end
    else:
        prefix = text
        suffix = ""

    # Calculate how many characters are allowed for the prefix
    # Account for the 3 characters used by "..."
    allowed_prefix_len = max_len - len(suffix) - len("...")

    # Fallback if the suffix + "..." is already longer than max_len
    if allowed_prefix_len < 0:
        return text[:max_len - 3] + "..."

    # Trim the prefix from the end working backwards
    trimmed_prefix = prefix[:allowed_prefix_len]

    return trimmed_prefix + "..." + suffix


class YarnspirationsScraper(BaseScraper):
    source_id    = "yarnspirations"
    display_name = "Yarnspirations"
    _site_url    = "https://www.yarnspirations.com/"
    site_url     = "https://www.tkqlhce.com/click-101816609-13781249"
    _PRODUCTS_URL = "https://www.yarnspirations.com/collections/yarn/products.json"

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

        color_idx = next(
            (i for i, o in enumerate(product["options"]) if o["name"].lower() == "color"),
            None,
        )
        opt_key = f"option{color_idx + 1}" if color_idx is not None else None

        image_by_variant = {}
        for img in product["images"]:
            for vid in img.get("variant_ids", []):
                image_by_variant[vid] = img["src"]

        seen_colours = set()
        for variant in product["variants"]:
            colour_label = variant.get(opt_key) if opt_key else variant["title"]
            if colour_label in seen_colours:
                continue
            seen_colours.add(colour_label)

            image_url = image_by_variant.get(variant["id"]) or (
                product["images"][0]["src"] if product["images"] else None
            )
            name = f"{base_name}: {colour_label}"
            print(f"  {name}")
            url = f"https://www.yarnspirations.com/products/{product['handle']}?variant={variant['id']}"
            aff_url = affiliate_link(url=url, sku=variant["sku"])
            yield {
                "name": trim_string_with_suffix(name),
                "url": aff_url,
                "image_url": image_url,
                "fiber": "",
                "yarn_type": product.get("product_type", ""),
            }
