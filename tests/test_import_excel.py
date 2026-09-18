"""Offline regression tests for Excel parsing, reconciliation and safe publication."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("import_excel", ROOT / "import_excel.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def make_book(path, sheets):
    book = openpyxl.Workbook()
    book.remove(book.active)
    for name, rows in sheets.items():
        sheet = book.create_sheet(name)
        for row in rows:
            sheet.append(row)
    book.save(path)
    book.close()


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_multisheet_title_rows_dates_invalid_numeric_and_formula(self):
        path = self.root / "sample.xlsx"
        make_book(path, {
            "数据一": [["标题"], [], ["三方库名称", "版本号", "完成日期"],
                     ["Num_Py", "1.10", "2026/9/18"], ["numeric", 1.1, None], ["formula", '=A1', None]],
            "数据二": [["package_name", "version"], ["num-py", "1.10"], ["empty", None]],
            "来源统计": [["指标", "数量"], ["总数", 4]],
        })
        rows, errors, sheets = app.read_excel([path])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["version"], "1.10")
        self.assertEqual(rows[0]["completed_at"], "2026-09-18")
        self.assertEqual(len(errors), 3)
        self.assertFalse(sheets[-1]["data_sheet"])
        selected, _, _ = app.read_excel([path], ["数据二"])
        self.assertEqual(len(selected), 1)
        with self.assertRaisesRegex(ValueError, "不存在工作表"):
            app.read_excel([path], ["missing"])

    def test_exact_versions_dedup_and_ignore_excel_status(self):
        original = ("# 清单\n\n| 序号 | 库名 | 版本号 | 是否需要迁移 | 最终成功日期 |\n"
                    "| --- | --- | --- | --- | --- |\n"
                    "| 1 | Some_Pkg | 1.0 | 是 | 2026-09-10 |\n"
                    "| 2 | some-pkg | 1.0 | 是 | 2026-09-12 |\n").encode()
        imported = [{"name": "some.pkg", "version": "1.0", "completed_at": "2026-09-11"},
                    {"name": "some-pkg", "version": "1.10", "completed_at": "-"},
                    {"name": "SOME_PKG", "version": "1.10", "completed_at": "-"}]
        cnb = {("some-pkg", "1.10"): {"name": "some-pkg", "version": "1.10"},
               ("remote-only", "2.0"): {"name": "remote-only", "version": "2.0"}}
        result, report = app.merge_source(original, imported, cnb)
        self.assertIn("Some_Pkg | 1.0 | 否 | 2026-09-12", result.decode())
        self.assertIn("some-pkg | 1.10 | 是 | -", result.decode())
        self.assertIn("remote-only | 2.0 | 是 | -", result.decode())
        self.assertEqual(report["summary"]["existing_duplicates_merged"], 1)
        self.assertEqual(report["summary"]["excel_duplicate_rows"], 1)
        repeated, _ = app.merge_source(result, imported, cnb)
        self.assertEqual(result, repeated)

    def test_csv_level_name_version_encodings_and_text_versions(self):
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            with self.subTest(encoding=encoding):
                path = self.root / "input.csv"
                path.write_bytes(('级别,包名,版本\r\nL0,"Some_Pkg","1.10"\r\n'
                                  'L1,other,01.0\r\n,,\r\n\r\nL0,bad,\r\n').encode(encoding))
                rows, errors, tables = app.read_excel([path])
                self.assertEqual([r["version"] for r in rows], ["1.10", "01.0"])
                self.assertTrue(all(r["completed_at"] == "-" for r in rows))
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0]["row"], 6)
                self.assertEqual(tables[0]["valid_rows"], 2)
                self.assertEqual(tables[0]["encoding"], "gb18030" if encoding == "gb18030" else "utf-8-sig")
                source = "| 序号 | 库名 | 版本号 | 是否需要迁移 | 最终成功日期 |\n| 1 | base | 1 | 否 | - |\n"
                merged, _ = app.merge_source(source.encode(), rows, {("other", "01.0"): rows[1]})
                self.assertIn("Some_Pkg | 1.10 | 否 | -", merged.decode())
                self.assertIn("other | 01.0 | 是 | -", merged.decode())

    def test_csv_missing_header_sheet_option_and_malformed_quotes_fail(self):
        path = self.root / "bad.csv"
        path.write_text("级别,未知列,版本\nL0,a,1.0\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "未找到"):
            app.read_excel([path])
        with self.assertRaisesRegex(ValueError, "不支持 --sheet"):
            app.read_excel([path], ["数据"])
        path.write_text('级别,包名,版本\nL0,a,"1.0\n', encoding="utf-8")
        with self.assertRaises(app.csv.Error):
            app.read_excel([path])

    def test_inventory_rejects_duplicate_pages_and_checks_end(self):
        client = app.CnbClient(workers=1)
        calls = []
        def request(path, **params):
            page = params["page"]
            calls.append(page)
            data = [{"name": "a" if page == 1 else "b", "count": 1,
                     "last_artifact_name": "1.0"}] if page < 3 else []
            return data, {"x-cnb-total": "2", "x-cnb-page-size": "1", "x-cnb-page": str(page)}
        with patch.object(client, "request", side_effect=request):
            packages, info = client.inventory()
        self.assertEqual(len(packages), 2)
        self.assertEqual(set(calls), {1, 2, 3})
        self.assertTrue(info["empty_end_page_checked"])
        def duplicate(path, **params):
            data, headers = request(path, **params)
            if data:
                data[0]["name"] = "a"
            return data, headers
        with patch.object(client, "request", side_effect=duplicate), self.assertRaisesRegex(ValueError, "重复或漏页"):
            client.inventory()

    def test_all_version_pages_and_incomplete_page_error(self):
        client = app.CnbClient()
        package = {"name": "test", "version_count": 3, "latest_version": "3", "last_push_at": ""}
        def request(path, **params):
            page = params["page"]
            tags = [{"name": v} for v in (["1", "2"] if page == 1 else ["3"])]
            return {"pypi": tags}, {"x-cnb-total": "3", "x-cnb-page-size": "2", "x-cnb-page": str(page)}
        with patch.object(client, "request", side_effect=request):
            self.assertEqual([r["version"] for r in client.versions(package)], ["1", "2", "3"])
        with patch.object(client, "request", return_value=({"pypi": []}, {"x-cnb-total": "3", "x-cnb-page-size": "2", "x-cnb-page": "1"})), self.assertRaisesRegex(ValueError, "提前结束"):
            client.versions(package)

    def test_changing_snapshot_never_succeeds(self):
        client = app.CnbClient()
        first = [{"name": "a", "version_count": 1, "latest_version": "1", "last_push_at": "old"}]
        second = copy.deepcopy(first)
        second[0]["last_push_at"] = "new"
        inventory = [(first, {}), (second, {}), (first, {}), (second, {})]
        with patch.object(client, "inventory", side_effect=inventory), self.assertRaisesRegex(ValueError, "有更新"):
            client.snapshot()

    def test_publication_rolls_back_on_midway_error(self):
        repo, stage, run = [self.root / name for name in ("repo", "stage", "run")]
        for path in (repo, stage, run):
            path.mkdir()
        for folder, value in ((repo, "old"), (stage, "new")):
            (folder / "data").mkdir()
            (folder / "data/file.json").write_text(value)
            (folder / "support_list.md").write_text(value)
            (folder / "cnb_verification.json").write_text(value)
        rename = Path.rename
        def fail_once(path, target):
            if path == stage / "support_list.md":
                raise OSError("simulated locked source file")
            return rename(path, target)
        with patch.object(Path, "rename", fail_once), self.assertRaises(OSError):
            app.publish_local(repo, stage, run, b"old")
        self.assertEqual((repo / "support_list.md").read_text(), "old")
        self.assertEqual((repo / "data/file.json").read_text(), "old")
        self.assertEqual((repo / "cnb_verification.json").read_text(), "old")

    def test_generation_and_apply_in_isolated_project(self):
        repo = self.root / "project"
        repo.mkdir()
        for name in ("gen_packages.py", "README.md"):
            shutil.copy2(ROOT / name, repo / name)
        validator = Path(".agents/skills/classify-ohos-python-packages/scripts/validate_categories.py")
        (repo / validator).parent.mkdir(parents=True)
        shutil.copy2(ROOT / validator, repo / validator)
        names = ["torch", "redis", "numpy", "requests", "pytest", "docker", "openpyxl", "plain-tool"]
        original = "# 清单\n\n| 序号 | 库名 | 版本号 | 是否需要迁移 | 最终成功日期 |\n| --- | --- | --- | --- | --- |\n"
        original += "".join(f"| {i} | {name} | 1.0 | 否 | - |\n" for i, name in enumerate(names, 1))
        (repo / "support_list.md").write_bytes(original.encode())
        (repo / "data").mkdir()
        (repo / "data/old.txt").write_text("preserve this in backup")
        workbook = self.root / "input.csv"
        workbook.write_text("级别,包名,版本\nL0,some-new-package,1.0\n", encoding="utf-8-sig")
        snapshot = {"metadata": {"source": app.CNB_URL, "finished_at": "2026-09-18T16:21:12+08:00",
                    "failures": [], "inventory_stable_across_two_full_passes": True,
                    "pagination": {"empty_end_page_checked": True}, "expected_versions": 1, "versions": 1, "packages": 1},
                    "packages": [{"name": "numpy", "version_count": 1}], "versions": [{"name": "numpy", "version": "1.0"}]}
        args = app.parser().parse_args([str(workbook), "--repo-root", str(repo)])
        with patch.object(app.CnbClient, "snapshot", return_value=snapshot):
            run, report = app.run_import(args)
        self.assertEqual(report["status"], "updated")
        self.assertEqual(report["summary"]["excel_added_versions"], 1)
        self.assertEqual((run / "backup/support_list.md").read_text(), original)
        self.assertTrue((run / "backup/data/old.txt").exists())
        self.assertIn("some-new-package | 1.0 | 否 | -", (repo / "support_list.md").read_text())
        index = json.loads((repo / "data/index.json").read_text())
        self.assertEqual((index["total"], index["adapted"]), (9, 1))
        before = (repo / "support_list.md").read_bytes()
        args.dry_run = True
        with patch.object(app.CnbClient, "snapshot", return_value=snapshot):
            _, preview = app.run_import(args)
        self.assertEqual(preview["status"], "previewed")
        self.assertEqual((repo / "support_list.md").read_bytes(), before)
        with patch.object(app.CnbClient, "snapshot", side_effect=RuntimeError("network failed")), self.assertRaises(RuntimeError):
            app.run_import(args)
        self.assertEqual((repo / "support_list.md").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
