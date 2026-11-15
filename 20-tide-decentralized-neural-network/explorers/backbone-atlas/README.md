# Tide 主干拓扑与规模面板

打开[离线面板](generated/index.html)。页面内嵌图数据、交互代码、MathML 与阶梯图；无需网络。源码和定义入库，HTML、SVG、PNG 及数据报告由统一构建生成。

共用一个入口，分别选择空间图、时间绑定和参数配置。连接视图覆盖三类 HB，规模筛选另包含 FC；FC 连接视图与 LH 探索图尚未接入。三类空间图分别选择：

| 空间图 | 面板尺寸 | 用途 |
|---|---|---|
| 多跨度 HB | 原 5／5-dd4／7／9／13／15／17 层宽图；窄图 5-dd4／7／9／双入口九层／15 层，每区 8／16／32，可选 4 hub | Timed、Timed 与 Settle 同周期的机制对照、Multiscale-Settle |
| 原 HB-Lattice | 5／7／9 层，16，无 hub | 原递归展开收拢，保持 $D=L+2$ |
| Settle 位交换 | 原 7／10／13 层；另有 m 与 R 分开的窄平台，每区 8／16／32，可选 4 hub | 对齐计算的逐轮合作，可切换真实 hub 增强图 |

共 58 个空间配置。含 hub 的配置在每个非末层位置设置 D 区与独立 H 区，末层只有 D。区域图可筛选边族，单节点图完整列出上下游，矩阵按两端实际节点数显示：例如 n=32 时，无 hub 为 32×32，含 hub 的内部位置为 36×36，进入末层为 36×32；公式侧栏随当前选择代入。空间选择改变模型，显示筛选只隐藏连线。

多跨度图的时间选择同步更新区域边标注、节点时延、端点矩阵与到达表：Timed 单位时延／T=4、Timed 单位时延／与 Settle 同周期、Settle 跨度时延／D=M+1。前两项是 Timed 的两种输入日程。原 HB 与位交换图固定各自 Settle 绑定。层数相位阶梯单独标明是单位时延／T=4 的固定参考，Settle 表则给出对齐时间与宽段潜在来源覆盖。潜在路径不等于实际选择、无损内容覆盖或物理低时延。

规模筛选覆盖 FC 与三类 HB，支持 n=8／16／32／64／128、d=64 至 768、K／S／X、independent／shared，以及 shared 秩 4／8／16。预算只选合法的 1、2、4、8、16、32、64 或 pool；显示总参、预算比例和活跃参数代理，超过 256M 的行也保留。规模筛选不修改上方连接图；有已绘制连线的行可点击“查看”。

正式语义入口：

- [共同拓扑、全部尺寸、分区与 hub 放置](../../topologies/hb-multiscale.md)。其他配置已有构造定义，暂不都提供界面切换。
- [位交换拓扑与覆盖证明](../../topologies/hb-exchange.md)、[Settle 三图共同绑定](../../instances/hb-settle-weighted-message.md)、[两种整体参数配置](../../local-semantics/weighted-message/parameter-profiles.md)。
- [统一主干比较绑定与计数口径](../../instances/backbone-comparison.md)、[完整 CSV](generated/capacity.csv)、[生成范围表](generated/capacity-summary.md)。
- [K／S／X 三组主局部绑定](../../instances/hb-multiscale-weighted-message.md)。显示筛选不会隐式切换模型。
- [角色上下界](../../local-semantics/weighted-message/role-bounded-allocation.md)、[设计问题与取舍](../../memos/design/hb-and-lh.md)。
- [逐候选核对数据](generated/checks.json)、[9 层区域图](generated/regions-9.svg)、[节点矩阵](generated/node-pair-matrix.svg)、[层数阶梯](generated/depth-ladder.svg)。

## 在另一台机器构建

当前构建使用 Linux 的系统图形库及字体路径；Debian／Ubuntu 或 WSL Ubuntu 可按以下步骤操作。使用 Python 3.10+，先更新仓库，再在仓库根目录运行。首次安装系统依赖：

```bash
sudo apt-get update
sudo apt-get install -y python3 librsvg2-2 libcairo2 fonts-noto-cjk
```

仅构建面板（无需构建其他图集或静态演示 PDF）：

```bash
python3 tools/build.py --group backbone-atlas
python3 tools/check_artifacts.py --require-built --group backbone-atlas
```

成功后用现代浏览器直接打开 `20-tide-decentralized-neural-network/explorers/backbone-atlas/generated/index.html`，无需启动 HTTP 服务。页面内嵌交互所需数据；CSV 下载及正文链接需要保留对应目录。产物不随 Git 同步，拉取后按维护地图检查状态并重建本组。

### 从旧目录升级

2026-11-15 起，面板从 `explorers/hb-timed/` 迁到本目录，构建组从 `hb-topology-atlas` 改为 `backbone-atlas`。Git 更新只迁移维护源；旧机器的 `hb-timed/generated/` 可能仍在。先检查旧目录内容，将旧目录整体移至仓库外保存，再使用上方新命令构建。以下命令从仓库根目录执行，只移动这个旧目录，不删除其中的手工文件或生成物：

```bash
if [ -d 20-tide-decentralized-neural-network/explorers/hb-timed ]; then
  tide_atlas_backup=$(mktemp -d ../tide-atlas-before-move.XXXXXX) &&
    mv 20-tide-decentralized-neural-network/explorers/hb-timed "$tide_atlas_backup/" &&
    printf '旧目录已保存到 %s\n' "$tide_atlas_backup"
fi
```

旧书签请改为本页的新地址；公共构图和计数源的迁移见[路径记录](../../records/history/migration-map.md#2026-11-15-主干面板与参考计算)。置换种子与配置标识保持原值，目录迁移不改变连接或参数数目。

Conda Python 可以调用统一构建器。PNG 渲染由 `tools/native_svg.py` 启动 `/usr/bin/python3 -I -S`（或 `/bin/python3`），只在该子进程中清除 LD_LIBRARY_PATH、LD_PRELOAD、LD_AUDIT、PYTHONHOME、PYTHONPATH，并使用系统 PATH。这样避免系统 Pango／Fontconfig 与 Conda 已加载库混用，调用者环境和其他构建组的 Python 选择不变。依赖预检在相同隔离环境中实际加载图形库，而非只查找库名。

若旧版本出现 `libpangoft2 ... undefined symbol: FcConfigSetDefaultSubstitute`，先更新仓库。临时也可用下面的命令绕过调用者的 Python 和库路径：

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u LD_AUDIT -u PYTHONHOME -u PYTHONPATH \
  /usr/bin/python3 tools/build.py --group backbone-atlas
```

## 维护与核对

从仓库根目录生成并核对：

```bash
python3 tools/check_artifacts.py --affected 20-tide-decentralized-neural-network/reference/backbones 20-tide-decentralized-neural-network/explorers/backbone-atlas
python3 tools/build.py --group backbone-atlas
python3 tools/check_artifacts.py --require-built --group backbone-atlas
python3 20-tide-decentralized-neural-network/examples/hb_lh_checks.py
python3 20-tide-decentralized-neural-network/examples/hb_settle_checks.py
python3 20-tide-decentralized-neural-network/examples/hb_compact_checks.py
python3 20-tide-decentralized-neural-network/examples/backbone_capacity_checks.py
python3 20-tide-decentralized-neural-network/examples/role_bounded_allocation_checks.py
python3 20-tide-decentralized-neural-network/explorers/backbone-atlas/check_browser.py
```

构建使用 Python 标准库、系统 Python 及系统 librsvg、Cairo、GObject，字体采用 Noto Sans CJK 或本机已有的 Droid Sans Fallback；不依赖 Python 的 Pillow／CairoSVG。Debian／Ubuntu 可安装 `librsvg2-2 libcairo2 fonts-noto-cjk`，GObject 由依赖带入。浏览器核对另需 Firefox，通过隔离 profile 验证 58 个配置及参数预算筛选、区域跳转、公式映射、矩阵端点数量、末层角色与矩形矩阵、g=1 边界、时间同步及宽窄布局；报告和截图默认写入仓库外临时目录，不进入日常 Git 产物。仓库 CI 在 push／pull request 时构建本组并执行浏览器核对。

两个带 hub 的构造器默认省去末层 H；`terminal_hubs=True` 可复现此前包含它们的图，面板展示默认图。删除对 group／singleton 保留节点与输出的影响，以及 mixed 的差异，见[共同拓扑 §1](../../topologies/hb-multiscale.md#1-节点位置与区域)。

[公共参考代码](../../reference/backbones/README.md)维护多跨度／Lattice／Exchange 构造、潜在传播与主干参数计数，数学核对程序和本面板共用。`build_atlas.py` 绘制图并生成页面与图数据，`capacity_reports.py` 将计数结果写为 CSV、范围表及页面数据；`capacity.js` 维护规模筛选，`page.html`、`style.css`、`explore.js`、`formulas.js` 维护展示。先核对定义、数值例子、图示与界面，再生成；详见[维护地图](../../../ARTIFACTS.md)。构建不覆盖本 README。
