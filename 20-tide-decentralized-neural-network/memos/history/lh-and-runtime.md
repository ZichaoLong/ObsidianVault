---
type: historical-research-record
status: historical
snapshot-date: 2026-07-10
source-vault-revision: 133d638
---

# LH、旧 runtime 与 HB 示例的历史位置

本页保存后来抽象从何而来的必要信息。工程快照对应旧文注明的 **2026-07-10**、代码基线 `79bb9ec`；本次整理没有重查 LH、tide.old 或当时 runtime 的代码。原始调查、对拍表、吞吐数字及开发计划都可在本仓库 Git `133d638` 的 `tide-runtime-validation-and-status.md` 查阅，不能据此判断今天的实验平台状态。

## 1. LH 提供了哪些问题

旧 C++ Connectome 使用两套 cortex 及状态：input cortex 与 output cortex；`inputA`、`outputA` 处理各自内部传播，`ioA`、`oiA` 连接两套 cortex。Bridge 除了方向，还参与特定执行相位。一个外部 token 输入后运行有限个 internal tick，将指定输出节点每个 tick 的值保存，再由 Pronounce 汇合读出。

单个节点的旧处理包括：接收局部输入、与 local hidden 共同计算候选激活、selector 决定保留的激活、归一化/激活，以及可选 `clear_after_activation`。其中 hidden 有加法累积和局部 KV 两类；KV 记录实际送达该节点的历史，而非全图公共历史。

这些机制提供了几个长期有用的问题：

- 收到消息与被选择是两种不同覆盖。
- 记忆的写入、读取、清理以及跨步保存需要分别定义。
- 选择历史可能影响以后路由，必须成为显式语义状态。
- 内部过程与外部读出不一定是同一时钟或同一个事件。

当前模型统一使用逻辑时间 $\theta$，并按教材定义候选、Full 与 Next。旧 `internal tick`、CHAL 和 selector 的具体顺序不能直接改名后当作当前节点契约；尤其旧候选激活可能已经包含昂贵计算，是否能在 Full 前完成选择需要重新分析。

## 2. 旧 selector 的动机

历史 `NaiveSelector` 按层级局部组选择，hub 节点只要受到影响就可能被保留，底层 point 竞争有限名额；优先级涉及 `selectcount`、`affectcount`、signal norm 与 index tie-break。

后来关于信号积累、恢复量、慢阈值和负载的公式，是在此基础上提出的控制机制设想，不是已验证的生物能量模型。当前保留的表达方式见 [Selector 与局部记忆](../architecture/selector-and-memory.md)：history 可记录选中后的恢复；时间衰减按统一逻辑时间惰性计算；神经状态清理需区分 Full 的读出快照与 Next。

## 3. Runtime 抽象留下的有用分工

旧运行时尝试把静态 GraphSpec、持久 State、临时 Workspace、执行 Schedule 与 Kernel 分开，并显式记录 phase 的读视图、写目标及 commit 策略。这些名称不进入当前数学定义，但分工仍有意义：临时 buffer 的重排可以自由度较大，未来会读取的状态和未交付消息不能静默丢失。

旧 `tide.old` 的 strict/non-strict family 标签曾同时夹带接口统一、语义等价和序列并行等含义，容易混淆。当前分别讨论数学语义、有限切面、节点批及实际性能，见 [执行与成本](../learning-systems/execution-and-cost.md)。B0—B6、P0—P6 等旧编号不再规定研究顺序。

## 4. 2026-07-10 对拍快照能说明什么

当时旧文报告三层 reference chain：native LH whole `think()`、由 Tide schedule 驱动的 native phase path、独立 Tide CPU kernels。在当时覆盖的配置上，报告了 logits、部分 phase message/hidden 与 selector count 的对拍，以及 CPU stress benchmark。

该快照不能证明一般 Graph 的完整 memory-state equality、当前教材语义、训练价值或设备后端性能。当时列出的“未完成 checkpoint growth”也不是今天 fractal-latcarf 的状态。原始数字缺少在本页重新复核的完整环境与配置，故只保留版本入口，不将历史吞吐重排成当前排行榜。

## 5. HB 两个 toy reference

| 历史程序 | 当时想演示什么 | 现在怎样使用 |
| --- | --- | --- |
| [HB-Line-v0](examples/hb_line_v0_reference.py) | 分开空间邻接、深度切片及节点内部步骤；比较 depth-major、token-major 与 chunk continuation | 阅读旧模型的方程与调度，不作为当前解释器 |
| [HB-Lattice-v0](examples/hb_lattice_v0_reference.py) | 八个宏阶段、局部分支与 deadline merge 的 toy 对拍 | 追溯旧图为何混合空间和 lowering |

两个文件保留其原始 toy 数值规则，并在文件头注明历史范围。它们只依赖 Python 标准库，运行自己的内置检查：

```bash
python 20-tide-decentralized-neural-network/memos/history/examples/hb_line_v0_reference.py
python 20-tide-decentralized-neural-network/memos/history/examples/hb_lattice_v0_reference.py
```

这些检查通过只说明旧 toy 的相应 schedules 一致，不证明 `tide-core-3`、真实 Attention/SSM、低 span 或训练收益。

## 6. 历史图的索引

- HB-Sliced：[基图](assets/hb-sliced-spatial-base-graphs.svg)、[节点步骤](assets/hb-sliced-node-transition.svg)。
- HB-Line：[空间 DAG](assets/hb-line-v0-spatial-dag.svg)、[单输入传播示意](assets/hb-line-v0-token-route.svg)。
- HB-Lattice：[八阶段图](assets/hb-lattice-v0-superblock.svg)、[平面布局](assets/hb-lattice-v0-plane.svg)、[旧节点 contract](assets/hb-lattice-v0-node-contract.svg)。

图中的步骤、参数与正文历史程序属于各自版本。新构型解释见 [拓扑与生长候选](../architecture/topology-and-growth-candidates.md)。过期的两路线汇合图、checkpoint 强制阶梯图由 Git 历史保存，不再作为当前入口图片。

## 7. 怎样追溯原文

例如在本仓库执行：

```bash
git show 133d638:20-tide-decentralized-neural-network/tide-runtime-validation-and-status.md
git show 133d638:20-tide-decentralized-neural-network/tide-model-architecture-and-training.md
```

历史版本用于回答当时提出过什么；当前数学以教材和语义版本锚点为准，具体实现完成度由各实验平台自己的 revision 与记录回答。
