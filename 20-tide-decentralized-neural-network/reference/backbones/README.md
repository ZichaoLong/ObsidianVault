# 主干构造与参数计数参考

本目录提供面板和数学核对共用的 Python 标准库代码。正式定义分别由 [topologies/](../../topologies/) 与[主干比较绑定](../../instances/backbone-comparison.md)承担；这里构造端点、计算潜在传播和参数形状，不执行整网神经计算或训练。

| 维护源 | 对应定义与职责 |
|---|---|
| [multiscale.py](multiscale.py) | [HB-Multiscale](../../topologies/hb-multiscale.md)：宽／窄轮廓、可选 hub、端点构造、时延支持与潜在来源覆盖 |
| [settle_graphs.py](settle_graphs.py) | [HB-Lattice](../../topologies/hb-lattice.md) 与 [HB-Exchange](../../topologies/hb-exchange.md)：展开、交换与收拢的端点构造 |
| [capacity.py](capacity.py) | FC 与三类 HB 的空间轮廓与时间绑定登记、节点／来源类统计、独立／区域共享／层级共享参数计数及预算活跃代理 |

入口程序将 `reference/` 加入 Python 模块搜索路径，按 `from backbones import multiscale, settle_graphs, capacity` 导入。包内使用相对导入；公共代码不依赖面板目录、HTML 或图形库，也不写生成物。`settle_graphs.py` 与多跨度图共用固定置换规则，种子 `hb-timed-discussion-20261114-v1` 保留其定义身份。

`capacity.PROFILES` 登记空间轮廓，`BOUND_PROFILES` 将其接到主时间绑定；`count` 继续接收空间标识，返回精确标量计数。多跨度 Timed／Settle 共用计数，在生成表和面板中分别列出。导出的 CSV 由面板报表代码换算成 M，内嵌 JSON 保留原始计数。

[教学与核对程序](../../examples/README.md)检查构造及公式；[主干面板](../../explorers/backbone-atlas/README.md)负责视图、CSV 和 Markdown 范围表。FC 目前通过节点和来源类统计参与计数，尚未提供用于面板绘图的逐边构造；LH 的教学构造仍在 HB／LH 核对程序中。

修改本目录后，从仓库根目录查影响并核对定义、例子和界面公式，再重建：

```bash
python3 tools/check_artifacts.py --affected 20-tide-decentralized-neural-network/reference/backbones
python3 20-tide-decentralized-neural-network/examples/hb_lh_checks.py
python3 20-tide-decentralized-neural-network/examples/hb_settle_checks.py
python3 20-tide-decentralized-neural-network/examples/hb_compact_checks.py
python3 20-tide-decentralized-neural-network/examples/backbone_capacity_checks.py
python3 tools/build.py --group backbone-atlas
python3 tools/check_artifacts.py --require-built --group backbone-atlas
```

生成登记与人工核对来源见[维护地图](../../../ARTIFACTS.md)。构图、计数与数学正文需要同步审阅，构建通过本身不能证明语义一致。
