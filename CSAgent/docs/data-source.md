# Data Source

Phase 1 uses the Electronics item metadata from the Amazon Reviews 2023 dataset by McAuley Lab at UCSD.

Official dataset page:

```text
https://amazon-reviews-2023.github.io/
```

Metadata source used by the catalog builder:

```text
https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_Electronics.jsonl.gz
```

The full metadata file is large, so this project streams records and stops once it finds 50 clean products. The raw records behind the chosen catalog are saved to:

```text
data/raw/electronics_sample.jsonl
```

The normalized catalog is saved to:

```text
data/catalog/products.json
```

On this machine, Python TLS validation failed against the dataset host certificate chain. The data builder therefore supports `--insecure-source` for local development. Keep the default verified path unless your environment has the same certificate issue.
