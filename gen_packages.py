#!/usr/bin/env python3
"""Generate GitHub Pages data from support_list.md.

Usage: python3 gen_packages.py
"""

import json
import re
import shutil
from collections import defaultdict
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_FILE = ROOT / "support_list.md"
DATA_DIR = ROOT / "data"
PAGE_SIZE = 50
BROWSE_CHUNK_SIZE = 250
ROW_PATTERN = re.compile(r"^\|\s*(\d+)\s*\|")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

CATEGORIES = (
    {
        "id": "ai-ml",
        "label": "AI 与机器学习",
        "tokens": {"ai", "ml", "llm", "nlp", "agent", "agents", "agentic", "mcp"},
        "fragments": (
            "tensorflow", "torch", "keras", "scikit-learn", "sklearn",
            "xgboost", "lightgbm", "catboost", "huggingface", "transformer",
            "sentencepiece", "safetensor", "onnx", "openvino", "langchain",
            "llama-index", "machine-learning", "deep-learning", "neural",
            "embedding", "diffuser", "ultralytics", "mlflow", "spacy",
            "gensim", "computer-vision",
        ),
    },
    {
        "id": "database",
        "label": "数据库与存储",
        "tokens": {"db", "sql", "orm"},
        "fragments": (
            "database", "sqlalchemy", "sqlite", "postgres", "psycopg",
            "mysql", "mariadb", "oracle", "mongodb", "pymongo", "redis",
            "cassandra", "clickhouse", "elasticsearch", "opensearch", "neo4j",
            "influxdb", "dynamodb", "firestore", "couchdb", "duckdb", "lmdb",
            "leveldb", "rocksdb", "alembic", "peewee", "sqlmodel", "asyncpg",
            "odbc", "vector-db", "chromadb", "milvus", "qdrant", "weaviate",
        ),
    },
    {
        "id": "data-science",
        "label": "数据科学与计算",
        "tokens": {"math", "stats", "plot", "data", "dataset", "etl", "warehouse", "airbyte"},
        "fragments": (
            "numpy", "scipy", "pandas", "polars", "pyarrow", "matplotlib",
            "seaborn", "plotly", "bokeh", "altair", "sympy", "statsmodels",
            "scikit-image", "jupyter", "notebook", "ipython", "dask", "ray",
            "spark", "parquet", "hdf5", "h5py", "netcdf", "xarray", "geopandas",
            "shapely", "pyproj", "geospatial", "scientific", "analytics",
            "visualization", "dataframe", "timeseries", "time-series", "airbyte",
        ),
    },
    {
        "id": "web-network",
        "label": "Web 与网络",
        "tokens": {"api", "http", "web", "rpc", "oauth", "jwt"},
        "fragments": (
            "django", "flask", "fastapi", "starlette", "aiohttp", "httpx",
            "requests", "urllib3", "tornado", "sanic", "bottle", "falcon",
            "quart", "uvicorn", "gunicorn", "hypercorn", "websocket", "grpc",
            "graphql", "restful", "socketio", "network", "dns", "ssh", "ftp",
            "smtp", "imap", "scrapy", "beautifulsoup",
        ),
    },
    {
        "id": "dev-test",
        "label": "开发工具与测试",
        "tokens": {
            "test", "testing", "lint", "debug", "build", "docs", "types",
            "stub", "stubs",
        },
        "fragments": (
            "pytest", "unittest", "coverage", "hypothesis", "tox", "nox",
            "robotframework", "behave", "mock", "faker", "benchmark", "ruff",
            "flake8", "pylint", "mypy", "pyright", "black", "isort", "pre-commit",
            "sphinx", "mkdocs", "setuptools", "poetry", "pipenv", "virtualenv",
            "cookiecutter", "cibuildwheel", "profiler", "debugger", "type-stubs",
            "tree-sitter",
        ),
    },
    {
        "id": "system-cloud",
        "label": "基础设施与云服务",
        "tokens": {
            "cloud", "docker", "kubernetes", "linux", "windows", "macos",
            "alibabacloud", "kafka", "rabbitmq", "mqtt", "queue", "iot",
            "hardware", "sensor", "serial", "gpio", "adafruit", "circuitpython",
            "image", "images", "audio", "video", "media", "gui", "qt", "game",
            "graphics", "pygame",
        },
        "fragments": (
            "boto", "aws", "azure", "google-cloud", "openstack", "aliyun",
            "alibabacloud",
            "tencentcloud", "huaweicloud", "kubernetes", "docker", "podman",
            "ansible", "terraform", "prometheus", "grafana", "opentelemetry",
            "sentry", "datadog", "psutil", "systemd", "filesystem", "watchdog",
            "cron", "scheduler", "celery", "airflow", "saltstack", "supervisor",
            "cryptography", "openssl", "bcrypt", "argon2", "keyring", "security",
            "kafka", "rabbitmq", "mqtt", "adafruit", "circuitpython", "opencv",
            "pillow", "imageio", "ffmpeg", "gstreamer", "pyqt", "pyside",
            "tkinter", "wxpython", "pygame", "pyaudio", "soundfile", "librosa",
            "moviepy",
        ),
    },
    {
        "id": "office",
        "label": "通用办公",
        "tokens": {
            "browser", "pdf", "ppt", "pptx", "docx", "excel", "xls", "xlsx",
            "office", "spreadsheet",
        },
        "fragments": (
            "selenium", "playwright", "browser", "pdf", "powerpoint", "pptx",
            "openpyxl", "pyexcel", "xlsx", "spreadsheet", "libreoffice", "docx",
            "wordprocessing", "document-convert", "document-parser",
        ),
    },
    {
        "id": "other",
        "label": "其他",
        "tokens": set(),
        "fragments": (),
    },
)
CATEGORY_PRIORITY = (
    "dev-test", "database", "data-science", "system-cloud", "office", "ai-ml",
    "web-network"
)
CATEGORIES_BY_ID = {category["id"]: category for category in CATEGORIES}
CATEGORY_LABELS = {category["id"]: category["label"] for category in CATEGORIES}

if len(CATEGORIES) != 8 or len(CATEGORIES_BY_ID) != len(CATEGORIES):
    raise ValueError("Categories must contain exactly 8 unique IDs")


def first_group(name):
    first = name[0].lower() if name else ""
    return first if "a" <= first <= "z" else "0-9"


def classify_package(name):
    normalized = re.sub(r"[._]+", "-", name.casefold())
    tokens = set(filter(None, re.split(r"[^a-z0-9]+", normalized)))
    for category_id in CATEGORY_PRIORITY:
        category = CATEGORIES_BY_ID[category_id]
        if tokens & category["tokens"] or any(
            fragment in normalized for fragment in category["fragments"]
        ):
            return category["id"]
    return CATEGORIES[-1]["id"]


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
                "category": classify_package(name),
            }
        )

    if errors:
        raise ValueError("Invalid source data:\n" + "\n".join(errors[:20]))
    if not packages:
        raise ValueError(f"No package rows found in {SOURCE_FILE}")
    return packages


def package_sort_key(package):
    return (package["name"].casefold(), package["version"].casefold(), package["id"])


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def search_bucket(name):
    normalized = name.casefold()
    group = first_group(normalized)
    if group == "0-9":
        return group
    second = normalized[1] if len(normalized) > 1 else "_"
    if not ("a" <= second <= "z" or "0" <= second <= "9"):
        second = "_"
    return f"{group}-{second}"


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
        output.write("| 包名 | 版本 | 类别 | 是否需要通过鸿蒙源进行下载 | 最终成功日期 |\n")
        output.write("| --- | --- | --- | --- | --- |\n")
        for package in packages:
            status = "是" if package["adapted"] else "否"
            output.write(
                f"| `{package['name']}` | {package['version']} | "
                f"{CATEGORY_LABELS[package['category']]} | {status} | "
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
    for generated_dir in ("pages", "search", "categories"):
        shutil.rmtree(DATA_DIR / generated_dir, ignore_errors=True)
    (DATA_DIR / "pages").mkdir(exist_ok=True)
    (DATA_DIR / "search").mkdir(exist_ok=True)
    (DATA_DIR / "categories").mkdir(exist_ok=True)

    counts = {}
    browse_counts = {}
    for group in sorted(groups, key=lambda value: (value == "0-9", value)):
        write_group(group, groups[group])
        counts[f"{group}.jsonl"] = len(groups[group])
        browse_counts[group] = {}
        browse_sets = {
            "all": groups[group],
            "adapted": [package for package in groups[group] if package["adapted"]],
            "direct": [package for package in groups[group] if not package["adapted"]],
        }
        for status, status_packages in browse_sets.items():
            browse_counts[group][status] = len(status_packages)
            for chunk in range(ceil(len(status_packages) / BROWSE_CHUNK_SIZE)):
                start = chunk * BROWSE_CHUNK_SIZE
                write_json(
                    DATA_DIR / "pages" / f"{group}-{status}-{chunk + 1}.json",
                    status_packages[start:start + BROWSE_CHUNK_SIZE],
                )

    search_groups = defaultdict(list)
    category_groups = defaultdict(list)
    for package in packages:
        search_groups[search_bucket(package["name"])].append(package)
        category_groups[package["category"]].append(package)
    for bucket, bucket_packages in search_groups.items():
        write_json(DATA_DIR / "search" / f"{bucket}.json", bucket_packages)
    for category_id, category_packages in category_groups.items():
        write_json(DATA_DIR / "categories" / f"{category_id}.json", category_packages)
    write_json(DATA_DIR / "all.json", packages)

    dates = [match.group() for package in packages for match in [DATE_PATTERN.search(package["completed_at"])] if match]
    adapted = sum(package["adapted"] for package in packages)
    category_counts = {
        category["id"]: sum(package["category"] == category["id"] for package in packages)
        for category in CATEGORIES
    }
    index = {
        "total": len(packages),
        "adapted": adapted,
        "not_adapted": len(packages) - adapted,
        "last_updated": max(dates) if dates else "-",
        "categories": [
            {"id": category["id"], "label": category["label"], "count": category_counts[category["id"]]}
            for category in CATEGORIES
        ],
        "files": counts,
        "browse": {
            "page_size": PAGE_SIZE,
            "chunk_size": BROWSE_CHUNK_SIZE,
            "groups": browse_counts,
        },
        "search_files": sorted(search_groups),
    }
    (DATA_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    stats = (
        f"> 数据由 `gen_packages.py` 自动生成，更新日期：{index['last_updated']}\n\n"
        "| 指标 | 数量 |\n| --- | ---: |\n"
        f"| 支持包总数 | {index['total']:,} |\n"
        f"| 需要通过鸿蒙源下载 | {index['adapted']:,} |\n"
        f"| 无需通过鸿蒙源下载 | {index['not_adapted']:,} |\n"
        "\n## 类别分布\n\n"
        "> 类别由包名关键词规则自动推断；办公自动化与文档处理包归为“通用办公”，未命中前七类规则的包归为“其他”。\n\n"
        "| 类别 | 数量 | 占比 |\n| --- | ---: | ---: |\n"
        + "".join(
            f"| {category['label']} | {category_counts[category['id']]:,} | "
            f"{category_counts[category['id']] / len(packages):.1%} |\n"
            for category in CATEGORIES
        )
    )
    (DATA_DIR / "stats.md").write_text(stats, encoding="utf-8")
    print(
        f"Generated {index['total']} packages: "
        f"{index['adapted']} adapted, {index['not_adapted']} not adapted."
    )


if __name__ == "__main__":
    main()
