# HB 连接、公式与时间交互面板

打开[离线面板](generated/index.html)。页面内嵌图数据、交互代码、MathML 与阶梯图；无需网络。源码和定义入库，HTML、SVG、PNG 及数据报告由统一构建生成。

面板展示全位置 hub、group 分区、每位置 16+4 个节点的七种深度配置，包括额外连线的 5-dd4。区域图筛选边族，单节点图完整列出一跳上下游，20×20 矩阵逐边显示端点，公式侧栏随当前选择代入参数。时间对照面板保持同一空间图，比较单位时延、T=4 的跨度时延、D=M+1 的严格 Settle；上方图和深度阶梯保持 Timed 的含义。潜在路径不等于实际选择或物理延迟。

正式语义入口：

- [共同拓扑、全部尺寸、分区与 hub 放置](../../topologies/hb-multiscale.md)。其他配置已有构造定义，暂不都提供界面切换。
- [K／S／X 三组主局部绑定](../../instances/hb-multiscale-weighted-message.md)。显示筛选不会隐式切换模型。
- [角色上下界](../../local-semantics/weighted-message/role-bounded-allocation.md)、[设计问题与取舍](../../memos/design/hb-timed-and-lh.md)。
- [逐候选核对数据](generated/checks.json)、[9 层区域图](generated/regions-9.svg)、[节点矩阵](generated/node-pair-matrix.svg)、[层数阶梯](generated/depth-ladder.svg)。

从仓库根目录生成：

```bash
python3 tools/check_artifacts.py --affected 20-tide-decentralized-neural-network/explorers/hb-timed
python3 tools/build.py --group hb-topology-atlas
python3 tools/check_artifacts.py --require-built --group hb-topology-atlas
python3 20-tide-decentralized-neural-network/examples/hb_lh_checks.py
python3 20-tide-decentralized-neural-network/examples/role_bounded_allocation_checks.py
python3 20-tide-decentralized-neural-network/explorers/hb-timed/check_browser.py
```

构建使用 Python 标准库及系统 librsvg、Cairo、GObject，字体采用 Noto Sans CJK 或本机已有的 Droid Sans Fallback；不依赖 Python 的 Pillow／CairoSVG。Debian／Ubuntu 可安装 `librsvg2-2 libcairo2 fonts-noto-cjk`，GObject 由依赖带入。浏览器核对另需 Firefox，通过隔离 profile 验证区域跳转、全部公式映射、时间对照及布局；报告和截图默认写入仓库外临时目录，不进入日常 Git 产物。

`topology.py` 是连接与潜在传播的共同维护源，不保存全局可变尺寸；`build_atlas.py` 绘制图与生成数据；`page.html`、`style.css`、`explore.js`、`formulas.js` 维护展示。先核对定义、数值例子、图示与界面，再生成；详见[维护地图](../../../ARTIFACTS.md)。构建不覆盖本 README。
