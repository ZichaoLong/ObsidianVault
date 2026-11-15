# HB 连接、公式与时间交互面板

打开[离线面板](generated/index.html)。页面内嵌图数据、交互代码、MathML 与阶梯图；无需网络。源码和定义入库，HTML、SVG、PNG 及数据报告由统一构建生成。

共用一个入口，保留原目录路径。三类空间图分别选择：

| 空间图 | 面板尺寸 | 用途 |
|---|---|---|
| 多跨度 HB | 5／5-dd4／7／9／13／15／17 层，16+4，group 分区 | Timed、对齐 TimedDAG、同周期机制对照、Multiscale-Settle |
| 原 HB-Lattice | 5／7／9 层，16，无 hub | 原递归展开收拢，保持 $D=L+2$ |
| Settle 位交换 | 7／10／13 层，16 或 16+4 | 对齐计算的逐轮合作，可切换真实 hub 增强图 |

共 16 个空间配置。含 hub 的配置在每个非末层位置设置 D 区与独立 H 区，末层只有 D。区域图可筛选边族，单节点图完整列出上下游，矩阵按两端实际节点数显示：普通位置为 16×16，含 hub 的内部位置为 20×20，进入末层为 20×16；公式侧栏随当前选择代入。空间选择改变模型，显示筛选只隐藏连线。

多跨度图的时间选择同步更新区域边标注、节点时延、端点矩阵与到达表：单位时延／T=4，跨度时延／T=4，单位时延／与 Settle 同周期，跨度时延／D=M+1。原 HB 与位交换图固定各自 Settle 绑定。层数相位阶梯单独标明是单位时延／T=4 的固定参考，Settle 表则给出对齐时间与宽段潜在来源覆盖。潜在路径不等于实际选择、无损内容覆盖或物理低时延。

正式语义入口：

- [共同拓扑、全部尺寸、分区与 hub 放置](../../topologies/hb-multiscale.md)。其他配置已有构造定义，暂不都提供界面切换。
- [位交换拓扑与覆盖证明](../../topologies/hb-settle-exchange.md)、[Settle 三图共同绑定](../../instances/hb-settle-weighted-message.md)、[两种整体参数配置](../../local-semantics/weighted-message/parameter-profiles.md)。
- [K／S／X 三组主局部绑定](../../instances/hb-multiscale-weighted-message.md)。显示筛选不会隐式切换模型。
- [角色上下界](../../local-semantics/weighted-message/role-bounded-allocation.md)、[设计问题与取舍](../../memos/design/hb-timed-and-lh.md)。
- [逐候选核对数据](generated/checks.json)、[9 层区域图](generated/regions-9.svg)、[节点矩阵](generated/node-pair-matrix.svg)、[层数阶梯](generated/depth-ladder.svg)。

从仓库根目录生成：

```bash
python3 tools/check_artifacts.py --affected 20-tide-decentralized-neural-network/explorers/hb-timed
python3 tools/build.py --group hb-topology-atlas
python3 tools/check_artifacts.py --require-built --group hb-topology-atlas
python3 20-tide-decentralized-neural-network/examples/hb_lh_checks.py
python3 20-tide-decentralized-neural-network/examples/hb_settle_checks.py
python3 20-tide-decentralized-neural-network/examples/role_bounded_allocation_checks.py
python3 20-tide-decentralized-neural-network/explorers/hb-timed/check_browser.py
```

构建使用 Python 标准库及系统 librsvg、Cairo、GObject，字体采用 Noto Sans CJK 或本机已有的 Droid Sans Fallback；不依赖 Python 的 Pillow／CairoSVG。Debian／Ubuntu 可安装 `librsvg2-2 libcairo2 fonts-noto-cjk`，GObject 由依赖带入。浏览器核对另需 Firefox，通过隔离 profile 验证 16 个配置、区域跳转、公式映射、矩阵端点数量、末层角色与矩形矩阵、g=1 边界、时间同步及宽窄布局；报告和截图默认写入仓库外临时目录，不进入日常 Git 产物。仓库 CI 在 push／pull request 时构建本组并执行浏览器核对。

两个带 hub 的构造器默认省去末层 H；`terminal_hubs=True` 可复现此前包含它们的图，面板展示默认图。删除对 group／singleton 保留节点与输出的影响，以及 mixed 的差异，见[共同拓扑 §1](../../topologies/hb-multiscale.md#1-节点位置与区域)。

`topology.py` 维护多跨度端点与潜在传播，`settle_topology.py` 维护原 HB 和位交换图，不保存全局可变尺寸；`build_atlas.py` 绘制图与生成数据；`page.html`、`style.css`、`explore.js`、`formulas.js` 维护展示。先核对定义、数值例子、图示与界面，再生成；详见[维护地图](../../../ARTIFACTS.md)。构建不覆盖本 README。
