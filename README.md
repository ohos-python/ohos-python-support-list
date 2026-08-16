# OpenHarmony Python 包支持列表

本项目展示已在 OpenHarmony/HarmonyOS 平台验证的 Python 包，可通过 GitHub Pages 按包名搜索、按首字符浏览，并按“已适配 / 无需适配”筛选。

## 数据概览

<!-- 运行 gen_packages.py 后，详细统计位于 data/stats.md。 -->

- 支持包总数：14,588
- 已进行适配：2,509
- 无需适配：12,079
- 数据更新日期：2026-08-13

## 项目结构

```text
├── index.html          # GitHub Pages 查询页面
├── support_list.md     # 基础数据源（人工维护）
├── gen_packages.py     # 静态数据生成脚本
├── .nojekyll           # 禁用 Jekyll 处理
└── data/
    ├── index.json      # 总数、适配状态和分组索引
    ├── *.jsonl         # 页面查询使用的分组数据
    ├── *.md            # GitHub 上直接浏览的分组表格
    └── stats.md        # 统计摘要
```

## 更新数据

编辑 `support_list.md` 后执行：

```bash
python3 gen_packages.py
```

生成脚本只使用 Python 标准库。它会校验数据行，将源表中的“是否需要迁移”转换为页面上的适配标签：`是`表示“已适配”，`否`表示“无需适配”。生成完成后提交 `support_list.md`、`data/` 和 README 中更新后的统计数字。

## 启用 GitHub Pages

1. 将本目录作为 GitHub 仓库根目录推送。
2. 在仓库 **Settings > Pages** 中选择 **Deploy from a branch**。
3. 选择默认分支和根目录 `/ (root)`，保存后等待部署完成。

本地预览需要通过 HTTP 服务访问，以便页面读取 `data/`：

```bash
python3 -m http.server 8000
```

然后访问 `http://localhost:8000/`。
