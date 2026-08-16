---
name: classify-ohos-python-packages
description: Maintain and apply this repository's OpenHarmony/HarmonyOS Python package classification rules. Use when changing category names, meanings, keywords, precedence, package labels, category statistics, generated data, or tag filtering in gen_packages.py, README.md, data files, or index.html.
---

# Classify OpenHarmony Python Packages

Maintain the repository's deterministic, name-based package taxonomy and keep generated data, documentation, and the query page consistent.

## Locate The Repository

Work from the repository root containing `gen_packages.py`, `support_list.md`, `README.md`, `index.html`, and `data/`. When invoked from this skill directory, the root is `../../..`.

Treat these files according to ownership:

- `gen_packages.py`: executable source of truth for IDs, labels, keyword rules, precedence, and generation.
- `README.md`: human-readable source of truth for category meaning and limitations.
- `support_list.md`: package support source data; do not edit it for classification-only work.
- `data/*.jsonl`, `data/*.md`, `data/index.json`, `data/stats.md`: generated outputs; never hand-edit them.
- `index.html`: query UI, category badge styles, and tag filtering.

## Preserve The Taxonomy

Assign exactly one of these eight categories to every package:

| ID | Label | Boundary |
| --- | --- | --- |
| `ai-ml` | AI 与机器学习 | Models, NLP, Agent/MCP, vector and LLM ecosystems when no more specific domain wins. |
| `database` | 数据库与存储 | Databases, ORM, caches, search engines, and vector stores. |
| `data-science` | 数据科学与计算 | Scientific computing, dataframes, ETL/datasets, visualization, notebooks, and geospatial data. |
| `web-network` | Web 与网络 | Web frameworks, HTTP/API, RPC, protocols, crawlers, and servers. |
| `dev-test` | 开发工具与测试 | Tests, quality tools, type stubs, language tooling, builds, docs, and debugging. |
| `system-cloud` | 基础设施与云服务 | Cloud, containers, OS/processes, messaging, hardware/IoT, image/audio/video/GUI, observability, and security. |
| `office` | 通用办公 | Browser automation, PDF, PPT, Word, Excel, spreadsheets, and document conversion. |
| `other` | 其他 | Fallback for names without a reliable signal for the first seven categories. |

Apply these policy constraints:

1. Normalize names as implemented by `classify_package`; match explicit complete tokens or distinctive fragments.
2. Keep generic `sdk`, `client`, `cli`, parser, and utility names in `other` unless another domain signal is present.
3. Prefer specific tool or domain signals in this order: `dev-test`, `database`, `data-science`, `system-cloud`, `office`, `ai-ml`, `web-network`; use `other` only as fallback.
4. Keep Agent/MCP in AI unless an explicit database, data, infrastructure/media, office, or development signal wins.
5. Keep browser automation and document operations in office. Keep image/audio/video/GUI libraries in infrastructure according to this project's taxonomy.
6. Do not rebalance counts by weakening keyword precision. The source lacks package descriptions and PyPI classifiers, so ambiguous names must remain in `other`.

## Change Workflow

1. Inspect `git status --short` and relevant diffs. Preserve all existing user changes.
2. Read the complete `CATEGORIES`, `CATEGORY_PRIORITY`, and `classify_package` definitions in `gen_packages.py`, plus the README category section.
3. Analyze affected package names with structured JSON parsing. Measure proposed matches and inspect representative names before changing broad tokens or fragments.
4. Update `gen_packages.py`. If IDs, labels, meanings, or precedence change, update the README table and rules in the same change.
5. When adding or renaming an ID, update the matching `.category-<id>` style and fallback label in `index.html`.
6. Regenerate all static outputs from the repository root:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 gen_packages.py
   ```

7. Run deterministic validation:

   ```bash
   python3 .agents/skills/classify-ohos-python-packages/scripts/validate_categories.py
   git diff --check
   ```

8. Review the new distribution in `data/stats.md` and sample packages that moved between categories. Confirm that generic SDK/CLI names still remain in `other`.
9. If labels, counts, generated data, or UI behavior changed, refresh the local HTTP preview and verify category options, representative exact searches, combined status filtering, and console errors. Check a 320px viewport when labels or table layout changed.

## Validation Rules

Do not finish unless all of these hold:

- There are exactly eight unique category IDs.
- Every generated package has one valid category and matches `classify_package(name)`.
- JSONL group counts, total/adapted counts, and category counts match `data/index.json`.
- Package IDs remain unique and every package is in its correct first-character group.
- README and `data/stats.md` mention every current category label.
- Representative packages verify the intended moves, and ambiguous packages remain in `other`.

The bundled validator is read-only and prints the current category distribution after checking these invariants.
