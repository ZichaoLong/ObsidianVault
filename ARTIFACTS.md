# 维护源、生成物与同步

Git 保存正文、维护源、原始素材和明确留存的证据。能由源文件重建的图片、HTML、PDF、备注与日常报告默认在本地生成。AI 先读 [AGENTS.md](AGENTS.md)，再按本页定位工作线；准确路径、直接输入、人工核对来源和构建命令集中登记在 [generated-artifacts.json](generated-artifacts.json)。

## 各条工作线的维护地图

| 工作线／目录 | 编辑入口与产物 | 修改后需要同步什么 |
|---|---|---|
| [控制反馈](10-control-feedback-token-instruction/README.md) | 正文为手工 Markdown；历史动机的五张图维护于 [assets/images/](assets/images/)，SVG → PNG，属于 `editable-assets` | 图文含义变化时核对历史动机与 SVG；修改图源后重建该组。复杂拓扑 PNG 是原始素材，继续保留 |
| [递归分解与 Memory](11-recursive-decomposition-memory/README.md) | 当前主要维护 Markdown，暂无登记的机械生成物 | 同步本线入口、当前状态、证据与相互引用；新增图片／报告时先确定维护源和生成方式，再登记 |
| [Tide 正典、局部语义、拓扑与实例](20-tide-decentralized-neural-network/README.md) | 教材和实例是人工维护的语义来源；图和展示不会自动从教材解析定义 | 核对共同名称、定义、证明、实例、图形源和展示内容；查清影响后分别改源。正典修订继续遵守 Tide 的版本核验约定 |
| [Tide 原有三图](20-tide-decentralized-neural-network/figures/README.md#整体结构与一次区域作用) | [src/legacy/](20-tide-decentralized-neural-network/figures/src/legacy/) → PNG／SVG，`legacy-figures` | 改绘图源后重建；正典或接口变化时人工核对图示。来源快照不随日常构建改写 |
| [Tide 局部图集](20-tide-decentralized-neural-network/figures/README.md#带权消息与两个算例) | [figures/src/](20-tide-decentralized-neural-network/figures/src/) 中局部、记忆、控制与时间绘图源 → PNG／SVG／报告，`local-figures` | 教材或算例变化时核对图中参数、条件和公式，再生成。报告记录教材哈希，不代表已完成语义审阅 |
| [Tide 展示](20-tide-decentralized-neural-network/presentations/design-introduction/README.md) | `content.py`、`build.py`、CSS／JS 和 HB 图源 → HTML／备注／分步 SVG，`presentation-build`；其后 `presentation-export` → PDF／预览／报告 | 讲述脚本、HB 实例、定义或设计说明变化时，核对屏幕内容、图形源和备注；需要交付静态版时再导出 |
| [技术笔记](30-technical-notes/README.md)与[共享素材](assets/README.md) | Markdown 为正文；三份 PPTX → SVG／PNG／PDF，属于 `editable-assets` | PowerPoint 修改 PPTX 后重建；改变数学符号或连线含义时核对正文。所有八张可编辑图的对应关系见素材说明 |
| [总入口](00-entry/README.md)、[索引](40-index/README.md)、[归档](90-archive/README.md) | 人工维护的 Markdown，暂无机械生成物 | 移动／改名正文时同步入口和引用；归档保留历史含义，活跃版本另行维护 |

这张表说明维护职责。机器清单中，`inputs` 是生成器直接读取的维护源，`depends_on` 是构建组依赖，`review_sources` 是需要人工核对的教材、算例或叙述来源。同一文件可以同时属于前两类来源：例如报告会读取教材哈希，但绘图公式仍需人工核对。

## 修改、拉取与合并后的流程

1. 从上表和清单定位维护源。修改 Python、SVG、PPTX 或展示内容源；直接修改导出物会在下次构建时被覆盖。
2. 查影响范围。修改教材、算例或设计解释后，先完成 `REVIEW` 提示对应的图文核对，再更新受影响的维护源。文档移动／改名也要同步全仓引用。
3. 用统一入口重建所需组；静态展示交付前构建 `presentation-export`。它会先构建 HTML 依赖。普通构建之后，旧 PDF 可能被标为 `STALE`，不会被静默视为已同步。
4. 运行登记检查、全仓链接检查和适用的 Tide 检查；提交源码、清单、忽略规则及明确留存文件。提交与推送仍按当前任务授权执行。

影响查询从仓库根目录运行，支持多个文件或目录：

```bash
python3 tools/check_artifacts.py --affected assets/fig/gpt-diagram.pptx
python3 tools/check_artifacts.py --affected 20-tide-decentralized-neural-network/instances/hb-lattice-weighted-message.md
python3 tools/check_artifacts.py --changed-from HEAD~1
```

`REBUILD` 表示直接输入变化；`REVIEW` 表示需要人工核对内容；`DOWNSTREAM` 表示后续依赖组。查询给出对应构建命令，但不自动修改定义或执行生成。`--changed-from` 将指定提交与当前已跟踪的工作区文件比较，包含已暂存和未暂存修改；新增文件先暂存或用 `--affected` 显式指定。清单无法推断尚未登记的语义关系，仍需按维护地图核对正文与引用。

Git `pull`、切换分支、合并以及新建 worktree 后，先读目标版本的约定，再运行状态检查。同步前记下当前提交，完成同步后用 `--changed-from` 比较该提交，可以定位本次需要重建与审读的下游。忽略的产物和本地构建记录不会随 Git 同步；新 worktree 按新克隆处理。同一 worktree 顺序构建，并行工作使用独立 worktree。

如果检测到旧版本留下的未归类图片或报告，先确认来源：手工源应登记；需要留存的成品应登记理由；可重建的旧输出可移至仓库外后再构建。检查器只报告，不自动删除；不要用全仓 `git clean -fdx` 处理同步问题。

## 文件归类与新增产物

| 内容 | 处理方式 |
|---|---|
| 正文、绘图／展示脚本、CSS、JS、依赖说明 | 跟踪，作为维护源 |
| 手工 SVG、PPTX、原始图片、外部原件 | 跟踪；媒体文件在 `asset_sources` 标明来源身份，避免被生成器覆盖 |
| 可重建的 PNG／SVG／HTML／PDF／备注／报告 | 在组的 `outputs` 登记准确路径，并添加精确忽略规则 |
| 用户明确指定留存的成品与历史证据 | 在 `retained` 登记路径和理由，跟踪并撤销该路径的忽略规则；历史快照用独立文件名 |
| `.artifact-state.json` | 清单的 `state_file`：统一构建自动维护的本地指纹记录，精确忽略，不作为研究证据提交 |

新增／改名／移除产物时，同时更新源目录的注册信息、组的 `inputs`／`outputs`／`review_sources`／`depends_on`、精确忽略规则、维护入口和引用。`asset_directories` 列出需要检查本地残留素材的目录。媒体文件和这些目录中的 JSON，必须归入维护源、已登记输出或留存文件；新增独立产物目录时一并登记。

[素材目录](assets/catalog.json)与 PPTX／SVG 导出清单、Tide 局部绘图函数注册名与输出清单会交叉检查。检测到新媒体文件时不能仅因其扩展名判定可删除，也不能用按扩展名全局忽略来掩盖遗漏。

若将生成的 SVG 改为长期手工维护，另存到如 `figures/manual/` 的位置，登记为图源，让生成器读取它；生成器不得继续覆盖同一路径。明确留存且仍自动更新的成品可以同时登记在 `outputs` 与 `retained`，其变动需随源一起审阅提交。历史核验快照不适用这种日常覆盖方式。

## 本地生成

Python 3.10+，从仓库根目录运行：

```bash
python3 tools/build.py                       # 全部普通组：58 个输出
python3 tools/build.py --full                # 含静态展示：共 61 个输出
python3 tools/build.py --group editable-assets
python3 tools/build.py --group legacy-figures
python3 tools/build.py --group local-figures
python3 tools/build.py --group presentation-build
python3 tools/build.py --group presentation-export
```

`--group` 可重复使用，自动按依赖顺序构建；不要与 `--full` 同用。HTML 组只需 Python 标准库。其他普通组需要 Pillow、CairoSVG、Cairo 和字体；展示导出另需浏览器。当前绘图脚本使用固定字体路径，Debian／Ubuntu 安装方式如下：

```bash
python3 -m pip install -r 20-tide-decentralized-neural-network/figures/requirements.txt
sudo apt-get install libcairo2 fonts-noto-cjk fonts-dejavu-core fonts-dejavu-extra

# 完整展示导出另需 Google Chrome、Node.js 18+，以及：
sudo apt-get install fonts-noto-cjk-extra
npm install --global @playwright/cli@0.1.12
```

构建器只提示依赖，不自动安装系统软件。其他系统需提供等价字体路径和渲染环境；CI 使用 Ubuntu 24.04、Python 3.12 和 Node.js 22。PPTX 图的 PDF 由 Cairo 导出，属于普通构建；Tide 展示的 PDF 需要浏览器。

各底层生成器的单图、另存预览等命令继续可用，见[素材说明](assets/README.md)、[图集说明](20-tide-decentralized-neural-network/figures/README.md#生成与修改)和[展示说明](20-tide-decentralized-neural-network/presentations/design-introduction/README.md#内容与复现)。底层命令不更新统一构建记录；正式核验前用对应的 `--group` 完成生成。另存预览宜放在仓库外。

## 状态与核验

统一构建在执行前取消该组旧的成功记录，执行成功且所有输出存在、输入在构建期间未变化时，记录直接输入、构建配置、依赖及输出的 SHA-256。失败不会沿用旧的成功状态；不使用修改时间推断新旧。

| 状态 | 含义与处理 |
|---|---|
| `MISSING` | 至少一个输出缺失；新克隆正常，按需构建 |
| `UNVERIFIED` | 文件存在但没有成功构建记录；用统一入口重建 |
| `STALE` | 输入／构建配置／依赖／输出发生变化，或依赖组不再有效；重建对应组 |
| `CURRENT` | 与成功构建时记录的直接输入和输出一致 |

`CURRENT` 只说明机械生成关系，不证明教材、算例和展示的语义已经一致，也不承诺不同字体或运行环境下逐字节相同。`review_sources` 的变化由影响查询提示，重新构建不会替代人工审读。原有渲染报告继续记录字体、渲染环境和图形检查结果。

```bash
# 只检查归类并显示各组状态；缺失、未核验、过期不单独导致失败。
python3 tools/check_artifacts.py

# 全仓已跟踪／已暂存 Markdown，以及已经生成的备注。
python3 tools/check_links.py
python3 20-tide-decentralized-neural-network/tools/check_documents.py
python3 -m unittest discover -s tools -p 'test_*.py'

# 要求全部产物存在且为 CURRENT；也可仅严格核验一个组。
python3 tools/check_artifacts.py --require-built
python3 tools/check_artifacts.py --require-built --group editable-assets
python3 tools/check_links.py --require-built
```

全仓链接检查支持 Markdown 内联／引用式链接、Obsidian 双链与转义别名、标题／块锚点，以及 HTML 链接和图片；跳过代码示例及外部 URL，不访问网络。仅允许清单中的准确产物路径和输出目录尚未生成；未登记的失效链接报错。未暂存的私人草稿不进入全仓检查；新正文暂存后纳入检查。Tide 检查继续负责正典版本、局部公式、旧配置名等专项规则。

检查器扫描全部已跟踪媒体，以及已登记素材目录内的媒体／JSON 残留；它无法仅从任意文件内容自动判断所有生成物。新增其他格式仍须主动登记。

## GitHub Actions

[Repository checks](.github/workflows/repository.yml)在 push／pull request 时执行登记与目录交叉核对、全仓链接、Tide 专项和单元测试，轻量检查只需 Python 标准库与 Git。

在 **Actions → Repository checks → Run workflow** 手动触发完整构建，验证全部产物、指纹状态、浏览器交互与布局，以及构建不改动维护源、不留下未跟踪文件。CI 不回写生成物；所有检出都使用完整 Git 历史。

历史重写后的旧克隆处理见 [2026-10-28 治理记录](20-tide-decentralized-neural-network/records/history/2026-10-28-artifact-governance.md)。日常同步采用本页流程，无需重写历史。
