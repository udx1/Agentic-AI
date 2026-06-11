# Catalog Schema

The normalized product catalog lives at `data/catalog/products.json`.

The shopper-facing category list lives at `data/catalog/categories.json`.

Each product has these fields:

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Product parent ASIN from the Amazon metadata. |
| `title` | string | Product display name. |
| `brand` | string | Brand or manufacturer, usually from product details or store. |
| `category` | string | Shopper-facing grouped category from `categories.json`. |
| `subcategory` | string | Original most specific category from the Amazon metadata. |
| `price` | number | Product price in US dollars at crawl time. |
| `rating` | number | Average product rating from 1.0 to 5.0. |
| `reviewCount` | integer | Number of ratings/reviews shown in metadata. |
| `image` | string | Primary product image URL. |
| `description` | string | Short cleaned description text. |
| `features` | string array | Bullet-point product features. |

## Selection Rules

The Phase 1 catalog builder keeps products that have:

- a unique parent ASIN
- title, brand, category, subcategory, image, description, and feature text
- price greater than zero
- rating between 1 and 5
- at least 10 ratings

The builder skips a few weak storefront categories, such as decals and generic floor cord covers, to keep the first UI catalog focused on recognizable electronics and accessories.

## Category Schema

Each category in `data/catalog/categories.json` has these fields:

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable slug for the grouped category. |
| `name` | string | Shopper-facing category name used in navigation. |
| `description` | string | Short explanation of the category. |
| `subcategories` | string array | Source metadata categories mapped into this group. |
