from __future__ import annotations

import argparse
import gzip
import json
import re
import ssl
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


DEFAULT_SOURCE_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/"
    "meta_categories/meta_Electronics.jsonl.gz"
)

EXCLUDED_CATEGORY_TERMS = (
    "background",
    "carpet",
    "decal",
    "floor cord cover",
    "messenger",
    "sticker",
    "vinyl",
)

CATEGORY_GROUPS = [
    {
        "id": "computers-storage",
        "name": "Computers & Storage",
        "description": "Laptops, computer components, keyboards, memory cards, and storage devices.",
        "subcategories": [
            "Data Storage",
            "DVI",
            "External Hard Drives",
            "Graphics Cards",
            "Keyboards",
            "Micro SD Cards",
            "Network Cards",
            "Traditional Laptops",
        ],
    },
    {
        "id": "audio-car",
        "name": "Audio & Car",
        "description": "Speakers, headphones accessories, car audio, and vehicle installation parts.",
        "subcategories": [
            "Car Dash Mounting Kits",
            "Coaxial Speakers",
            "Component Subwoofers",
            "Earpads",
            "Portable Bluetooth Speakers",
            "Radio Wiring Harnesses",
            "Speaker",
            "Vehicle Audio & Video Installation",
        ],
    },
    {
        "id": "cameras-optics",
        "name": "Cameras & Optics",
        "description": "Cameras, lenses, filters, batteries, optics, and mounting accessories.",
        "subcategories": [
            "Camera & Photo",
            "Camera Batteries",
            "Eyepieces",
            "Film Cameras",
            "Filter Sets",
            "Fish Finders & Depth Finders",
            "Neutral Density Filters",
            "SLR Camera Lenses",
            "Surveillance Housing & Mounting Brackets",
        ],
    },
    {
        "id": "mobile-accessories",
        "name": "Mobile Accessories",
        "description": "Cases, covers, wearable bands, stands, keyboard cases, and replacement screens.",
        "subcategories": [
            "Arm & Wristband Accessories",
            "Cases",
            "Covers",
            "Hard Shell Cases",
            "Keyboard Cases",
            "Replacement Screens",
            "Stands",
        ],
    },
    {
        "id": "cables-parts",
        "name": "Cables & Parts",
        "description": "Cables, remote controls, and small replacement electronics parts.",
        "subcategories": [
            "Remote Controls",
            "USB Cables",
        ],
    },
]

CATEGORY_LOOKUP = {
    subcategory: group["name"]
    for group in CATEGORY_GROUPS
    for subcategory in group["subcategories"]
}


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = fix_mojibake(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^\x09\x0a\x0d\x20-\x7e]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fix_mojibake(value: str) -> str:
    if "â" not in value and "Ã" not in value:
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return value


def clean_text_list(value: Any, limit: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [clean_text(item) for item in value if clean_text(item)]
    return cleaned[:limit] if limit else cleaned


def get_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
        try:
            return float(value)
        except ValueError:
            return None
    return None


def pick_brand(item: dict[str, Any]) -> str:
    details = item.get("details")
    details = details if isinstance(details, dict) else {}
    for key in ("Brand", "Manufacturer"):
        brand = clean_text(details.get(key))
        if brand:
            return brand
    return clean_text(item.get("store"))


def pick_category(item: dict[str, Any]) -> str:
    categories = clean_text_list(item.get("categories"))
    if categories:
        return categories[-1]
    return clean_text(item.get("main_category")) or "Electronics"


def group_category(subcategory: str) -> str:
    return CATEGORY_LOOKUP.get(subcategory, "Other Electronics")


def pick_image(item: dict[str, Any]) -> str:
    images = item.get("images")
    if not isinstance(images, list):
        return ""

    def image_url(image: Any) -> str:
        if not isinstance(image, dict):
            return ""
        for key in ("hi_res", "large", "thumb"):
            url = clean_text(image.get(key))
            if url:
                return url
        return ""

    for image in images:
        if isinstance(image, dict) and image.get("variant") == "MAIN":
            url = image_url(image)
            if url:
                return url

    for image in images:
        url = image_url(image)
        if url:
            return url
    return ""


def normalize_product(item: dict[str, Any]) -> dict[str, Any] | None:
    product_id = clean_text(item.get("parent_asin"))
    title = clean_text(item.get("title"))
    brand = pick_brand(item)
    price = get_number(item.get("price"))
    rating = get_number(item.get("average_rating"))
    review_count = get_number(item.get("rating_number"))
    image = pick_image(item)
    description_parts = clean_text_list(item.get("description"), limit=3)
    features = clean_text_list(item.get("features"), limit=6)

    subcategory = pick_category(item)
    category = group_category(subcategory)
    searchable_category = subcategory.lower()
    if any(term in searchable_category for term in EXCLUDED_CATEGORY_TERMS):
        return None

    if not all((product_id, title, brand, image, description_parts, features)):
        return None
    if price is None or price <= 0:
        return None
    if rating is None or rating < 1 or rating > 5:
        return None
    if review_count is None or review_count < 10:
        return None

    return {
        "id": product_id,
        "title": title,
        "brand": brand,
        "category": category,
        "subcategory": subcategory,
        "price": round(price, 2),
        "rating": round(rating, 1),
        "reviewCount": int(review_count),
        "image": image,
        "description": " ".join(description_parts),
        "features": features,
    }


def iter_jsonl_gz(source_url: str, insecure_source: bool = False):
    request = Request(source_url, headers={"User-Agent": "csagent-data-builder/0.1"})
    context = ssl._create_unverified_context() if insecure_source else None
    with urlopen(request, timeout=60, context=context) as response:
        with gzip.GzipFile(fileobj=response) as gz_file:
            for raw_line in gz_file:
                yield json.loads(raw_line.decode("utf-8"))


def iter_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def build_catalog(
    source_url: str,
    limit: int,
    insecure_source: bool = False,
    source_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    products: list[dict[str, Any]] = []
    raw_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    scanned = 0

    source_items = iter_jsonl(source_path) if source_path else iter_jsonl_gz(
        source_url,
        insecure_source=insecure_source,
    )

    for item in source_items:
        scanned += 1
        product = normalize_product(item)
        if product is None or product["id"] in seen_ids:
            continue

        seen_ids.add(product["id"])
        products.append(product)
        raw_records.append(item)

        if len(products) >= limit:
            break

    return products, raw_records, scanned


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local 50-product Electronics catalog.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument(
        "--source-path",
        type=Path,
        help="Read local JSONL source records instead of streaming the remote metadata file.",
    )
    parser.add_argument(
        "--insecure-source",
        action="store_true",
        help="Disable TLS verification for local environments with intercepted certificates.",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--catalog-path",
        type=Path,
        default=Path("../data/catalog/products.json"),
    )
    parser.add_argument(
        "--raw-sample-path",
        type=Path,
        default=Path("../data/raw/electronics_sample.jsonl"),
    )
    parser.add_argument(
        "--categories-path",
        type=Path,
        default=Path("../data/catalog/categories.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    products, raw_records, scanned = build_catalog(
        args.source_url,
        args.limit,
        insecure_source=args.insecure_source,
        source_path=args.source_path,
    )

    if len(products) < args.limit:
        print(f"Only found {len(products)} clean products after scanning {scanned} records.", file=sys.stderr)
        return 1

    write_json(args.catalog_path, products)
    write_json(args.categories_path, CATEGORY_GROUPS)
    write_jsonl(args.raw_sample_path, raw_records)
    print(f"Wrote {len(products)} products after scanning {scanned} metadata records.")
    print(f"Catalog: {args.catalog_path}")
    print(f"Categories: {args.categories_path}")
    print(f"Raw sample: {args.raw_sample_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
