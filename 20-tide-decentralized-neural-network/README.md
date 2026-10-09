---
type: index
status: active
as-of: 2026-10-09
tags:
  - tide
  - mathematics
  - semantic-anchor
---

# TIDE：数学教材与语义总览

20-tide 是 TIDE 各层级的数学与语义上游。这里回答“对象是什么、怎样计算、哪些结论在什么条件下成立”；实验平台选择具体构型与节点算法，实现这些语义，并验证训练、推理、等价性与性能。

初次阅读可从 [[settlegraph-learning-note|SettleGraph：单次结算图]] 开始，也可以直接读 [[timed-dag-region-selector-learning-note|TimedDAG 数学教材]]。教材面向第一次接触对象的数学读者，按定义、例子、命题与证明展开；计算机系统用语只在附录对照。

## 当前语义与层级

[[semantics-anchor|语义锚点与仓库分工]] 固定共同边界、版本、教材关系及下游引用规则。详细定义与证明由教材承担，备忘不反向改变教材。

| 层级 | 当前定义 | 教材 |
|---|---|---|
| Graph | 有限固定消息图，可有环；边时延为正整数；每个有限逻辑时间切面具有确定记录 | [正时延 Graph 的有限切面语义](positive-delay-graph-finite-cut-learning-note.md) |
| TimedDAG | 固定消息图进一步要求无环；保留多端口、不等长路径与一般区域划分 | [带区域选择的 TimedDAG](timed-dag-region-selector-learning-note.md) |
| SettleGraph | 区域依赖严格有序，每个输入位置单次结算，具有单输入与单输出；通过明确时间与边界编码嵌入 TimedDAG | [单次结算图 SettleGraph](settlegraph-learning-note.md) |

“Graph”在当前框架中指 PositiveDelayGraph，不表示任意带副作用程序。零时延边不在设计范围内。

[[timed-dag-chunk-prefill-learning-note|TimedDAG 分块预填充教材]] 是执行专题。它从 $P/S/U/F$ 作用 DAG 出发，分别定义因果状态块、完整输出时间批、联合节点块与最大前沿递归，并把外层块数、块内并行性和硬件效果分开。[静态分量窗口算法](timed-dag-chunk-prefill-learning-note.md#65-保留完整区域的静态分量) 适用于一般区域划分，在严格分层时自动采用每区域整窗口、每节点至多一个 Full 时间批的形状；[PDG 的默认分量递归](positive-delay-graph-finite-cut-learning-note.md#95-默认静态分量的窗口调度) 给出正时延有环图上的对应。

## 阅读路线

~~~text
SettleGraph：一次输入、共同选择、记忆与单次结算
    ↓ 明确的嵌入
TimedDAG：统一逻辑时间、消息纤维、关闭与继续
    ├─→ 分块预填充：哪些结构允许节点级时间批
    └─→ 正时延 Graph：空间环与有限切面
~~~

SettleGraph 是可选入门层级。分块预填充教材与正时延 Graph 教材都以 TimedDAG 教材为基础，二者之间没有先后依赖。学习者可按当前问题选择其中一条续篇。

当前共同接口区分候选新状态、本次计算快照与下一持久状态；也区分区域激活集合、各节点局部控制量与区域选择历史。状态可按统一逻辑时间衰减，或依激活结果清理。下一状态不读取完整计算结果；没有输入的时刻不自主激活或发送。时间衰减可由“保存值＋时间戳”在下一次读取时解码。

## 数学特例与语义锚点

[接收驱动的带权 KV 与稀疏 Full](weighted-kv-sparse-activation-example.md) 是该特例的上游语义锚点，定义一个三层共同的局部函数族：按接收强度写入并保留 KV，selector 根据候选记忆分配带上界的发送门控，Full 的精确零分支可省去昂贵 Attention／前馈计算。文档先定义内容、强度、预算和正式激活，再给出局部手算、零权重删除与硬化连续性的条件、三类图的时间批能力及下游继承约定。

这个特例沿用 `tide-core-3`，不改变核心定义。可在读完 SettleGraph 第 5 节后阅读局部公式，再结合分块教材阅读时间批部分；训练日程与待验证假设另见 [学习风险与诊断](memos/learning-systems/learning-risks-and-diagnostics.md#61-带权-kv-特例的退火实验)。

## 上游与实验平台

Graph 理论研究与 checkpoint 生长已在 SettleGraph 核心前向语义处发生弱汇合：从已有模型接入、单次结算的构型，可以作为总框架中的受限实例。这不表示所有实验扩展、特殊梯度或实现结果已经被统一证明。

fractal-latcarf 是 SettleGraph 的实验平台。它维护实际模块公式与选择空间、模型接入位置、初始化、训练设置、实现、测试和实测结果；上游维护抽象契约、教材与一般证明。当前对应与待下游单独对齐的接口见 [[semantics-anchor#下游如何引用|下游如何引用]]。

[graph-execution-foundation](https://github.com/ZichaoLong/tide/tree/graph-execution-foundation) 是三类图的公共执行与等价性验证基座，提供局部模块接口、continuation、通用调度与执行器对照。它与具体训练实验分别维护；采用某个上游特例时，由下游记录所引用的语义版本、具体配置及验证结果。

一般等价性定理可以留在上游，具体实现是否满足其前提由下游验证。旧 LH 的实现快照不代表 fractal-latcarf 当前状态，本仓库也不持续镜像下游“最新通过状态”。

## 进一步阅读

[[memos/README|研究备忘索引]] 按问题组织数学补充、机制与学习风险、外部背景及 LH 历史。[[resources/learning-resources|学习资源]] 提供按需书目。旧内容迁移索引仅供维护时追溯，不列入主要阅读路线。

[正时延 Graph 教学 reference](examples/positive_delay_graph_reference.py) 验证有限切面、控制量、状态快照及继续等式。它属于教材附件，不承担完整神经模型或硬件平台职责。LH 仅作为历史设计来源保留。

## 架构目标与数学约束

TIDE 的历史全称为 Topology-Invariant Degree-bounded Expansion Architecture for Autoregressive Token Inference。固定拓扑、局部连接与可达容量增长仍是架构目标；各具体架构族必须另外检查成本。

一个图有限，不等于扩容时所有节点成本具有统一上界。要主张有界成本扩容，必须同时约束状态、参数、区域宽度、入度出度、入口终端宽度与每次处理量。增加一个平铺区域的候选数不能单独完成这个目标；逻辑局部连接也不自动证明物理通信便宜。

目录名保留用于已有仓库链接。“去中心化”是历史动机和可研究的系统性质，不替代当前数学定义。
