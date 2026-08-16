# OpenHarmony Python 包支持列表

本项目展示已在 OpenHarmony/HarmonyOS 平台验证的 Python 包，可通过 GitHub Pages 按包名精确或模糊搜索、按首字符浏览，并按类别标签及“已适配 / 无需适配”筛选。

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

## 数据概览

<!-- 运行 gen_packages.py 后，详细统计位于 data/stats.md。 -->

- 支持包总数：14,588
- 已进行适配：2,509
- 无需适配：12,079
- 数据更新日期：2026-08-13

## 项目结构

```text
├── .agents/skills/     # 仓库级 Codex Skill
│   └── classify-ohos-python-packages/
├── index.html          # GitHub Pages 查询页面
├── support_list.md     # 基础数据源（人工维护）
├── gen_packages.py     # 静态数据生成脚本
├── .nojekyll           # 禁用 Jekyll 处理
└── data/
    ├── index.json      # 总数、适配状态、类别和分组索引
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
