#!/usr/bin/env python3
"""Generate GitHub Pages data from support_list.md.

Usage: python3 gen_packages.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_FILE = ROOT / "support_list.md"
DATA_DIR = ROOT / "data"
ROW_PATTERN = re.compile(r"^\|\s*(\d+)\s*\|")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def first_group(name):
    first = name[0].lower() if name else ""
    return first if "a" <= first <= "z" else "0-9"


def parse_source():
    packages = []
    errors = []

    for line_number, raw_line in enumerate(
        SOURCE_FILE.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not ROW_PATTERN.match(raw_line):
            continue

        columns = [value.strip() for value in raw_line.strip().strip("|").split("|")]
        if len(columns) != 5:
            errors.append(f"line {line_number}: expected 5 columns, got {len(columns)}")
            continue

        number, name, version, migration, completed_at = columns
        if not name:
            errors.append(f"line {line_number}: package name is empty")
            continue
        if migration not in {"是", "否"}:
            errors.append(f"line {line_number}: invalid migration value {migration!r}")
            continue

        packages.append(
            {
                "id": int(number),
                "name": name,
                "version": version or "-",
                "adapted": migration == "是",
                "completed_at": completed_at,
            }
        )

    if errors:
        raise ValueError("Invalid source data:\n" + "\n".join(errors[:20]))
    if not packages:
        raise ValueError(f"No package rows found in {SOURCE_FILE}")
    return packages


def package_sort_key(package):
    return (package["name"].casefold(), package["version"].casefold(), package["id"])


def write_group(group, packages):
    jsonl_path = DATA_DIR / f"{group}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as output:
        for package in packages:
            output.write(json.dumps(package, ensure_ascii=False, separators=(",", ":")) + "\n")

    label = group.upper() if group != "0-9" else "0-9 / 其他"
    md_path = DATA_DIR / f"{group}.md"
    with md_path.open("w", encoding="utf-8") as output:
        output.write(f"# {label} 开头的 Python 包（{len(packages):,} 个）\n\n")
        output.write("> [返回项目首页](../README.md)\n\n")
        output.write("| 包名 | 版本 | 适配状态 | 最终成功日期 |\n")
        output.write("| --- | --- | --- | --- |\n")
        for package in packages:
            status = "已适配" if package["adapted"] else "无需适配"
            output.write(
                f"| `{package['name']}` | {package['version']} | {status} | "
                f"{package['completed_at']} |\n"
            )


def main():
    packages = parse_source()
    packages.sort(key=package_sort_key)

    groups = defaultdict(list)
    for package in packages:
        groups[first_group(package["name"])].append(package)

    DATA_DIR.mkdir(exist_ok=True)
    for old_file in DATA_DIR.glob("*.jsonl"):
        old_file.unlink()
    for old_file in DATA_DIR.glob("*.md"):
        old_file.unlink()

    counts = {}
    for group in sorted(groups, key=lambda value: (value == "0-9", value)):
        write_group(group, groups[group])
        counts[f"{group}.jsonl"] = len(groups[group])

    dates = [match.group() for package in packages for match in [DATE_PATTERN.search(package["completed_at"])] if match]
    adapted = sum(package["adapted"] for package in packages)
    index = {
        "total": len(packages),
        "adapted": adapted,
        "not_adapted": len(packages) - adapted,
        "last_updated": max(dates) if dates else "-",
        "files": counts,
    }
    (DATA_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    stats = (
        f"> 数据由 `gen_packages.py` 自动生成，更新日期：{index['last_updated']}\n\n"
        "| 指标 | 数量 |\n| --- | ---: |\n"
        f"| 支持包总数 | {index['total']:,} |\n"
        f"| 已进行适配 | {index['adapted']:,} |\n"
        f"| 无需适配 | {index['not_adapted']:,} |\n"
    )
    (DATA_DIR / "stats.md").write_text(stats, encoding="utf-8")
    print(
        f"Generated {index['total']} packages: "
        f"{index['adapted']} adapted, {index['not_adapted']} not adapted."
    )


if __name__ == "__main__":
    main()
