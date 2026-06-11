from __future__ import annotations

import argparse
import gzip
import json
import re
import ssl
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


DEFAULT_SOURCE_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/"
    "review_categories/Electronics.jsonl.gz"
)
DEFAULT_CATALOG_PATH = Path("../data/catalog/products.json")
DEFAULT_REVIEWS_PATH = Path("../data/reviews/product_reviews.json")
DEFAULT_RAW_SAMPLE_PATH = Path("../data/raw/electronics_review_sample.jsonl")


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^\x09\x0a\x0d\x20-\x7e]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def get_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def iter_jsonl_gz(source_url: str, insecure_source: bool = False):
    request = Request(source_url, headers={"User-Agent": "csagent-review-builder/0.1"})
    context = ssl._create_unverified_context() if insecure_source else None
    with urlopen(request, timeout=60, context=context) as response:
        with gzip.GzipFile(fileobj=response) as gz_file:
            for raw_line in gz_file:
                yield json.loads(raw_line.decode("utf-8"))


def normalize_review(review: dict[str, Any]) -> dict[str, Any] | None:
    title = clean_text(review.get("title"))
    text = clean_text(review.get("text"))
    rating = get_number(review.get("rating"))

    if not text or len(text) < 40:
        return None
    if rating is None or not 1 <= rating <= 5:
        return None

    return {
        "reviewId": clean_text(review.get("user_id")) or clean_text(review.get("asin")),
        "asin": clean_text(review.get("asin")),
        "rating": round(rating, 1),
        "title": title,
        "text": text[:1200],
        "helpfulVotes": int(get_number(review.get("helpful_vote")) or 0),
        "verifiedPurchase": bool(review.get("verified_purchase")),
        "timestamp": int(get_number(review.get("timestamp")) or 0),
    }


def build_reviews(
    catalog_path: Path,
    source_url: str,
    reviews_per_product: int,
    insecure_source: bool,
    scan_limit: int,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], int]:
    products = read_json(catalog_path)
    product_ids = {product["id"] for product in products}
    reviews_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    raw_sample: list[dict[str, Any]] = []
    scanned = 0

    for raw_review in iter_jsonl_gz(source_url, insecure_source=insecure_source):
        scanned += 1
        parent_asin = clean_text(raw_review.get("parent_asin"))
        if parent_asin not in product_ids:
            if scanned >= scan_limit:
                break
            continue

        if len(reviews_by_product[parent_asin]) >= reviews_per_product:
            if scanned >= scan_limit:
                break
            continue

        review = normalize_review(raw_review)
        if review is None:
            if scanned >= scan_limit:
                break
            continue

        reviews_by_product[parent_asin].append(review)
        raw_sample.append(raw_review)

        if all(len(reviews_by_product[product_id]) >= reviews_per_product for product_id in product_ids):
            break
        if scanned >= scan_limit:
            break

    return dict(reviews_by_product), raw_sample, scanned


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build review samples for selected catalog products.")
    parser.add_argument("--catalog-path", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--reviews-path", type=Path, default=DEFAULT_REVIEWS_PATH)
    parser.add_argument("--raw-sample-path", type=Path, default=DEFAULT_RAW_SAMPLE_PATH)
    parser.add_argument("--reviews-per-product", type=int, default=6)
    parser.add_argument("--scan-limit", type=int, default=1_500_000)
    parser.add_argument(
        "--insecure-source",
        action="store_true",
        help="Disable TLS verification for local environments with intercepted certificates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reviews_by_product, raw_sample, scanned = build_reviews(
        args.catalog_path,
        args.source_url,
        args.reviews_per_product,
        args.insecure_source,
        args.scan_limit,
    )

    write_json(args.reviews_path, reviews_by_product)
    write_jsonl(args.raw_sample_path, raw_sample)

    products = read_json(args.catalog_path)
    counts = {product["id"]: len(reviews_by_product.get(product["id"], [])) for product in products}
    covered = sum(1 for count in counts.values() if count > 0)
    complete = sum(1 for count in counts.values() if count >= args.reviews_per_product)

    print(f"Scanned {scanned} review records.")
    print(f"Products with reviews: {covered}/{len(products)}")
    print(f"Products with {args.reviews_per_product}+ reviews: {complete}/{len(products)}")
    print(f"Reviews: {args.reviews_path}")
    print(f"Raw sample: {args.raw_sample_path}")

    if covered == 0:
        print("No matching reviews found.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
