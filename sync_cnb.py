#!/usr/bin/env python3
"""Correct support_list.md from a complete, independently verified CNB snapshot."""

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "support_list.md"
VERIFICATION = ROOT / "cnb_verification.json"
ROW = re.compile(r"^\|\s*\d+\s*\|")
NOTE = "> 判定规则：按库名和版本号核验 CNB 制品仓，存在标为“是”，未收录标为“否”。CNB 新增记录未提供成功日期时记为 `-`。"


def key(name, version):
    return re.sub(r"[-_.]+", "-", name.casefold()), version


def read_snapshot(path):
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    metadata = snapshot["metadata"]
    if metadata["failures"] or not metadata["inventory_stable_across_two_full_passes"]:
        raise ValueError("CNB snapshot has failed requests or changed during collection")
    if not metadata["pagination"]["empty_end_page_checked"]:
        raise ValueError("CNB pagination was not checked to the end")
    versions = snapshot["versions"]
    by_key = {key(item["name"], item["version"]): item for item in versions}
    if len(by_key) != len(versions) or len(versions) != metadata["expected_versions"]:
        raise ValueError("CNB versions are incomplete or duplicated")
    if len(versions) != metadata["versions"]:
        raise ValueError("CNB version total does not match metadata")
    package_counts = Counter(key(item["name"], item["version"])[0] for item in versions)
    expected_counts = {key(item["name"], "")[0]: item["version_count"] for item in snapshot["packages"]}
    if dict(package_counts) != expected_counts or len(expected_counts) != metadata["packages"]:
        raise ValueError("Per-package CNB version counts do not match")
    return metadata, by_key


def correct(snapshot_path, apply=False):
    metadata, cnb = read_snapshot(snapshot_path)
    original = SOURCE.read_bytes()
    lines = original.decode("utf-8").splitlines()
    retained, duplicate_rows, changes = {}, [], Counter()
    header = []
    for line in lines:
        if not ROW.match(line):
            if line != NOTE and not retained:
                header.append(line)
            continue
        fields = [value.strip() for value in line.strip().strip("|").split("|")]
        if len(fields) != 5 or fields[3] not in {"是", "否"}:
            raise ValueError(f"Invalid source row: {line}")
        pair = key(fields[1], fields[2])
        status = "是" if pair in cnb else "否"
        if status != fields[3]:
            changes[f"{fields[3]}→{status}"] += 1
        fields[3] = status
        if pair in retained:
            duplicate_rows.append({"removed": fields, "retained_original_id": retained[pair][0]})
            # Keep the first spelling and the latest recorded success date.
            if fields[4] != "-" and fields[4] > retained[pair][4]:
                retained[pair][4] = fields[4]
        else:
            retained[pair] = fields

    missing = sorted(cnb.keys() - retained.keys())
    for pair in missing:
        item = cnb[pair]
        retained[pair] = ["", item["name"], item["version"], "是", "-"]
    if {pair for pair, row in retained.items() if row[3] == "是"} != set(cnb):
        raise ValueError("Corrected positive records do not exactly equal the CNB snapshot")

    while len(header) > 1 and not header[1].strip():
        header.pop(1)
    header[1:1] = ["", NOTE, ""]
    rows = [f"| {i} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |"
            for i, row in enumerate(retained.values(), 1)]
    updated = ("\n".join(header + rows) + "\n").encode("utf-8")
    summary = {
        "checked_at": metadata["finished_at"], "source_rows_before": sum(ROW.match(x) is not None for x in lines),
        "status_changes": dict(changes), "duplicates_merged": len(duplicate_rows),
        "versions_added": len(missing), "total": len(retained),
        "yes": len(cnb), "no": len(retained) - len(cnb),
        "added": [cnb[pair] for pair in missing], "duplicate_rows": duplicate_rows,
    }
    if apply:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = snapshot_path.parent / f"support_list_校正前_{timestamp}.md"
        backup.write_bytes(original)
        SOURCE.write_bytes(updated)
        verification = {
            "source_url": metadata["source"], "checked_at": metadata["finished_at"],
            "package_count": metadata["packages"], "version_count": len(cnb),
            "rule": "normalized-name-and-exact-version",
            "source_sha256": sha256(updated).hexdigest(),
            "snapshot_sha256": sha256(snapshot_path.read_bytes()).hexdigest(),
        }
        VERIFICATION.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["backup"] = str(backup)
        (snapshot_path.parent / f"support_list_校正记录_{timestamp}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Complete CNB verification snapshot JSON")
    parser.add_argument("--apply", action="store_true", help="Back up and update the source; otherwise preview")
    args = parser.parse_args()
    correct(args.snapshot.resolve(), args.apply)
