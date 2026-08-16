#!/usr/bin/env python3
"""Validate generated package categories against the repository rules."""

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path


EXPECTED_PACKAGE_KEYS = {
    "id", "name", "version", "adapted", "completed_at", "category"
}


def load_generator(repo_root):
    module_path = repo_root / "gen_packages.py"
    spec = importlib.util.spec_from_file_location("ohos_package_generator", module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(repo_root):
    generator = load_generator(repo_root)
    data_dir = repo_root / "data"
    index = json.loads((data_dir / "index.json").read_text(encoding="utf-8"))

    categories = list(generator.CATEGORIES)
    category_ids = [category["id"] for category in categories]
    category_labels = {category["id"]: category["label"] for category in categories}
    require(len(categories) == 8, f"Expected 8 categories, found {len(categories)}")
    require(len(set(category_ids)) == 8, "Category IDs must be unique")

    index_categories = index.get("categories", [])
    require(
        [(item["id"], item["label"]) for item in index_categories]
        == [(item["id"], item["label"]) for item in categories],
        "data/index.json category IDs, labels, or order do not match gen_packages.py",
    )

    packages = []
    group_counts = {}
    for filename, expected_count in index["files"].items():
        path = data_dir / filename
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        group = filename.removesuffix(".jsonl")
        require(len(rows) == expected_count, f"{filename} count does not match index")
        for row in rows:
            require(set(row) == EXPECTED_PACKAGE_KEYS, f"Invalid schema for {row.get('name')}")
            require(row["category"] in category_ids, f"Unknown category for {row['name']}")
            require(
                row["category"] == generator.classify_package(row["name"]),
                f"Stale category for {row['name']}",
            )
            require(
                generator.first_group(row["name"]) == group,
                f"Wrong data group for {row['name']}",
            )
        packages.extend(rows)
        group_counts[filename] = len(rows)

    require(group_counts == index["files"], "Generated file counts do not match index")
    require(len(packages) == index["total"], "Total package count does not match index")
    require(len({row["id"] for row in packages}) == len(packages), "Package IDs are not unique")
    require(sum(row["adapted"] for row in packages) == index["adapted"], "Adapted count mismatch")
    require(
        sum(not row["adapted"] for row in packages) == index["not_adapted"],
        "Not-adapted count mismatch",
    )

    actual_counts = Counter(row["category"] for row in packages)
    indexed_counts = {item["id"]: item["count"] for item in index_categories}
    require(dict(actual_counts) == indexed_counts, "Category counts do not match index")

    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    stats = (data_dir / "stats.md").read_text(encoding="utf-8")
    for category_id in category_ids:
        label = category_labels[category_id]
        require(label in readme, f"README is missing category label {label}")
        require(label in stats, f"data/stats.md is missing category label {label}")

    print(f"Validated {len(packages):,} packages across {len(categories)} categories:")
    for category in categories:
        count = actual_counts[category["id"]]
        print(f"- {category['label']}: {count:,} ({count / len(packages):.1%})")


def main():
    default_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_root)
    args = parser.parse_args()
    validate(args.repo_root.resolve())


if __name__ == "__main__":
    main()
