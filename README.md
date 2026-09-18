# OpenHarmony Python 包支持列表

[通过 GitHub Pages 在线查看支持列表](https://ohos-python.github.io/ohos-python-support-list/)

本项目汇总 OpenHarmony/HarmonyOS Python 包及版本，可通过 GitHub Pages 按包名精确或模糊搜索、按首字符浏览，并按类别标签及“是否需要适配”筛选。

## 适配状态规则

`support_list.md` 保留原有“是否需要迁移”列，网页统一展示为“是否需要适配”。按本项目约定，两者均根据 **CNB 中是否存在对应库名和版本号** 判定：已收录为“是”，未收录为“否”。库名忽略大小写，并统一连字符、下划线和点号；版本号精确匹配，同库不同版本分别判定。

网页展示此次 CNB 核验时间。该状态表示制品仓收录情况，不直接判断库的技术适配需求或安装兼容性。已有成功日期沿用源清单；仅来自 CNB 且未提供成功日期的新版本以 `-` 表示。

## 类别标签

生成脚本根据包名关键词为每个包分配一个类别标签。每个包只有一个标签，共 8 类：

| 类别 | 适用范围 | 典型关键词或包 |
| --- | --- | --- |
| AI 与机器学习 | 模型训练与推理、自然语言处理、Agent/MCP 生态、向量与大模型应用 | `torch`、`tensorflow`、`onnx`、`transformers`、`huggingface`、`agent`、`mcp` |
| 数据库与存储 | 关系型与非关系型数据库、ORM、缓存、搜索和向量数据库客户端 | `sqlalchemy`、`sqlite`、`postgres`、`mysql`、`redis`、`clickhouse`、`chromadb` |
| 数据科学与计算 | 数值与科学计算、数据框、统计分析、数据集与 ETL、可视化、Notebook 和地理数据 | `numpy`、`scipy`、`pandas`、`airbyte`、`dataset`、`etl`、`jupyter`、`pyproj` |
| Web 与网络 | Web 框架、HTTP/API、RPC、网络协议、爬虫和服务端运行组件 | `django`、`flask`、`fastapi`、`requests`、`aiohttp`、`grpc`、`scrapy` |
| 开发工具与测试 | 测试、覆盖率、代码检查与格式化、类型存根、语言工具、构建发布、文档和调试 | `pytest`、`coverage`、`ruff`、`types`、`stubs`、`tree-sitter`、`setuptools` |
| 基础设施与云服务 | 云平台、容器、系统进程、消息中间件、硬件/IoT、图像音视频与 GUI、可观测性和安全 | `alibabacloud`、`docker`、`kafka`、`mqtt`、`adafruit`、`opencv`、`ffmpeg`、`pyqt` |
| 通用办公 | 浏览器自动化，以及 PDF、PPT、Word、Excel、电子表格和文档转换 | `selenium`、`playwright`、`pdf`、`pptx`、`docx`、`openpyxl`、`libreoffice` |
| 其他 | 无法仅根据包名可靠判断为上述七类的包，作为分类兜底 | 未命中明确类别关键词的包 |

### 判定规则

1. 包名会先统一为小写，并将点号和下划线按连字符处理，再匹配完整词或具有明确含义的名称片段。
2. 同时命中多个类别时，优先采用更明确的工具或领域信号，顺序为：开发工具与测试、数据库与存储、数据科学与计算、基础设施与云服务、通用办公、AI 与机器学习、Web 与网络。
3. CLI 只是交互方式，不会单独决定类别。例如带有云平台关键词的 CLI 归入基础设施与云服务；只有同时命中浏览器或文档办公关键词时才归入通用办公。
4. 未命中前七类规则的包统一归入“其他”。具体关键词和优先级以 `gen_packages.py` 中的 `CATEGORIES`、`CATEGORY_PRIORITY` 为准。

### 分类限制

基础数据只有包名、版本、适配状态和日期，不包含包描述或 PyPI Classifier，因此类别是基于包名的启发式推断，不代表包的官方分类。名称含义不明确或跨多个领域的包可能需要后续补充关键词规则。各类别的当前数量和占比见 `data/stats.md`。

## 项目结构

```text
├── .agents/skills/     # 仓库级 Codex Skill
│   └── classify-ohos-python-packages/
├── index.html          # GitHub Pages 查询页面
├── support_list.md     # 基础数据源（人工维护）
├── import_excel.py     # Excel/CSV → 在线核验 CNB → 合并清单 → 生成网页数据
├── requirements.txt    # Excel 导入依赖
├── sync_cnb.py         # 按已完整核验的 CNB 快照校正状态、合并重复并补入版本
├── cnb_verification.json # CNB 核验时间及源文件校验信息
├── gen_packages.py     # 静态数据生成脚本
├── .nojekyll           # 禁用 Jekyll 处理
└── data/
    ├── index.json      # 总数、适配状态、类别、分组索引及 CNB 核验时间
    ├── all.json        # 模糊搜索使用的聚合数据
    ├── pages/          # 首字符浏览与状态筛选的分页数据
    ├── search/         # 精确搜索使用的包名前缀分片
    ├── categories/     # 类别筛选使用的独立数据
    ├── *.jsonl         # 按首字符保存的完整分组数据
    ├── *.md            # GitHub 上直接浏览的分组表格
    └── stats.md        # 统计摘要
```

## 更新数据

### 从 Excel / CSV 一键更新

脚本文件名为 `import_excel.py`。它会联网核验 CNB，更新 `support_list.md`、`cnb_verification.json` 和网页 `data/` 数据，不修改输入文件，也不会自动提交或推送 Git。

#### 安装与正式更新

使用 Python 3.10 或以上版本，在包含脚本的项目根目录打开终端。导入 Excel 前安装依赖（仅导入 CSV 可跳过安装）：

```bash
python -m pip install -r requirements.txt
```

将输入文件放到项目目录，然后按实际文件格式执行其中一条命令。**不加 `--dry-run` 即为正式更新，无须先执行预览。**

```bash
python import_excel.py "final_output_20260917.csv"
python import_excel.py "三方库清单.xlsx"
```

也可以直接传入带引号的完整文件路径，无需复制输入文件：

```powershell
python import_excel.py "D:\download\三方库清单.xlsx"
```

注意：正式更新会核验全部 CNB 库及版本，校正现有清单的状态，并补入 CNB 中清单尚未收录的版本，**不只处理输入表格中的记录**。如果只需让网页与现有 `support_list.md` 一致、不查询 CNB，执行 `python gen_packages.py` 即可；此命令不导入 Excel/CSV，也不重新核验适配状态。

#### 输入格式

脚本读取 `.xlsx` / `.xlsm` 的全部数据工作表，自动在前 30 行查找“库名 / 三方库名称 / 包名”和“版本号 / 版本”等表头。成功日期为可选列；Excel 原有适配标记会按在线 CNB 数据重新判定。**版本号应以文本保存**，避免 Excel 将 `1.10` 变成 `1.1`；脚本默认拒绝数值型版本、公式和不完整数据行，并在报告中给出文件、工作表及行号。

也支持逗号分隔的 `.csv` 文件，兼容 UTF-8（含 BOM）及 GB18030/GBK 编码，版本号直接按文本读取。以下“级别、包名、版本”格式可以直接导入，无需转为 Excel：

```csv
级别,包名,版本
L0,aes-gcm-rsa-oaep,0.1.0
L1,aiokafka,0.13.0
```

“级别”列不参与适配状态或网页类别标签判定，仍按 CNB 的库名和版本核验状态，并沿用现有八类标签规则。缺少成功日期时保留清单已有日期，新记录填 `-`。CSV 导入不需要 openpyxl，也不支持 `--sheet`。

#### 可选预览与常用参数

需要检查结果但暂不修改正式数据时才加 `--dry-run`。该参数仍然联网查询 CNB。也可以一次导入多个文件、指定 Excel 工作表或自定义列名：

```bash
python import_excel.py "三方库清单.xlsx" --dry-run
python import_excel.py "final_output_20260917.csv" --dry-run
python import_excel.py "清单一.xlsx" "清单二.xlsx"
python import_excel.py "三方库清单.xlsx" --sheet "适配清单"
python import_excel.py "三方库清单.xlsx" --name-column "组件名称" --version-column "组件版本"
```

| 参数 | 用途 |
| --- | --- |
| `--dry-run` | 在线核验并保存预览报告，不修改正式清单和网页数据 |
| `--sheet "工作表名"` | 仅 Excel，可重复指定；默认读取全部可识别的数据工作表 |
| `--name-column "列名"` | 指定库名列标题 |
| `--version-column "列名"` | 指定版本号列标题 |
| `--date-column "列名"` | 指定成功日期列标题，指定后该列必须存在 |
| `--skip-invalid` | 明确跳过异常数据行并写入报告；默认有异常行就停止 |
| `--workers 6` | CNB 请求并发数，范围 1–12，默认 6 |
| `--timeout 30` | 每次请求的超时秒数，必须大于 0，默认 30 |
| `--retries 3` | 每次请求的最大尝试次数，范围 1–5，默认 3 |
| `--repo-root "项目路径"` | 指定要更新的完整项目，默认脚本所在目录 |

#### 更新流程与结果

完整流程如下：

1. 按规范化库名和精确版本去重，保留已有记录及最晚的已知成功日期。
2. 在线读取 CNB 全部库和全部版本分页，校验总数、唯一性及读取前后的列表一致性。读取失败或结果不完整时停止，避免将错误标记为“否”。
3. 合并 Excel/CSV、现有清单和 CNB 新增版本；CNB 中存在的标“是”，不存在的标“否”。没有成功日期的新增版本记为 `-`，不把推送日期当作成功日期。
4. 在临时目录调用现有生成脚本和八类标签校验，检查网页分页、搜索、分类数据后，再替换正式文件。替换失败时恢复原文件。

通过启动检查后，每次运行在 `outputs/excel_import/时间戳/` 中保存 `report.json`；CNB 抓取成功后另存完整的 `cnb_snapshot.json`。正式更新还会将原 `support_list.md`、已有核验信息及整个 `data/` 目录保存到 `backup/`。`--dry-run` 只保存核验结果和预览报告，不生成正式更新的备份。

终端输出报告路径及汇总数字。`report.json` 中 `status` 为 `updated` 表示已更新，`previewed` 表示仅预览，`failed` 表示失败。`summary` 中的常用字段如下（CSV 也沿用 `excel_` 字段名）：

| 字段 | 含义 |
| --- | --- |
| `excel_rows` / `excel_unique_versions` | 输入有效行数 / 按库名和版本去重后的数量 |
| `excel_duplicate_rows` | 输入记录中的重复数量 |
| `excel_added_versions` | 相对运行前清单，由输入文件新补入的版本数 |
| `cnb_added_versions` | 合并输入文件后，额外从 CNB 补入的版本数 |
| `existing_status_changes` | 现有清单中适配状态发生变化的记录数 |
| `total` / `yes` / `no` | 合并后总数 / 需要迁移“是” / 需要迁移“否” |

本次运行补入的版本数为 `excel_added_versions + cnb_added_versions`，不包含已有记录的状态修正；去重可能影响清单净增行数。该数字以运行前清单为基准，不等同于“0909 之后累计新增”。历史累计新增需另外与对应历史版本按库名和版本号对比。

如果遇到无效行，先根据报告中的文件、工作表和行号修正输入；确认要忽略这些行时再使用 `--skip-invalid`。网络失败、分页不完整或 CNB 数据持续变化时，脚本会停止，不会把读取失败判为“未收录”，也不会覆盖正式数据。正式文件替换失败时会尝试恢复备份；若恢复也失败，保留运行目录并根据报错检查 `backup/`，不要直接删除备份重跑。

本地更新完成后刷新页面即可；GitHub Pages 需提交并推送项目后发布。运行 `python import_excel.py --help` 查看全部参数。

### 使用已核验的 CNB 快照

取得完整 CNB 核验快照后，先预览校正结果，再应用并生成网页数据：

```bash
python3 sync_cnb.py <CNB核验快照.json>
python3 sync_cnb.py <CNB核验快照.json> --apply
python3 gen_packages.py
```

脚本只使用 Python 标准库。校正时先验证快照完整性，备份原始支持列表，再按“库名＋版本”更新全部状态；同名同版本的重复记录保留首条名称和最晚已有成功日期，并连续编号。原表中未被 CNB 收录的记录仍保留，只将状态改为“否”。

生成脚本同步全部分页、搜索及分类数据。只有源文件与校正记录一致时，网页才显示该次 CNB 核验时间；后续手动修改源表后需重新校正。生成完成后同步 `support_list.md`、`cnb_verification.json`、`data/` 和相关页面文件。
