---
type: index
status: active
tags:
  - tide
  - mathematics
  - semantic-anchor
---

# TIDE：数学教材与语义总览

TIDE 研究固定消息图上的有状态计算：节点接收输入、更新私有状态，区域共同选择完整计算，结果沿带正时延的边传播。本目录给出这些对象的定义、实例、嵌入与精确求值理论。

教材面向第一次接触 TIDE 的数学读者，按定义、例子、命题与证明展开。计算系统术语及实现对应集中在附录。

## 从哪里开始

- [SettleGraph：单次结算图](settlegraph-learning-note.md)：从一次输入出发，理解候选、选择、记忆、输出及有状态序列。前九节自包含。
- [带区域选择的 TimedDAG](timed-dag-region-selector-learning-note.md)：定义统一逻辑时间、消息纤维、规范作用、输入关闭与切面继续。
- [正时延 Graph 的有限切面语义](positive-delay-graph-finite-cut-learning-note.md)：研究空间有环的消息图、有限切面、强连通分量与联合求值。
- [TimedDAG 的分块预填充](timed-dag-chunk-prefill-learning-note.md)：研究因果状态块、完整输出时间批和契约相对的求值阶段。

SettleGraph 可以作为入门，也可以直接从 TimedDAG 开始。后两篇都以前置 TimedDAG 教材为基础，可按研究问题选择续篇。

## 三类图与共同语义

| 对象 | 条件与研究范围 |
|---|---|
| PositiveDelayGraph | 有限固定消息图，边时延为正整数；允许有向环，每个有限逻辑时间切面具有唯一记录 |
| TimedDAG | 消息图无环、输入有限；允许多端口、不等长路径与一般区域划分 |
| SettleGraph | 区域严格有序，时间按输入位置对齐；每位置单次结算，具有单输入与单输出边界 |

SettleGraph 经明确的时间和边界编码嵌入 TimedDAG，TimedDAG 是 PositiveDelayGraph 的受限实例。分块教材研究同一规范记录的精确联合求值。

共同语义区分候选新状态、本次计算快照与下一持久状态，也区分激活集合、局部控制与区域选择历史。完整输出读取快照；下一状态与选择历史在完整输出以前确定。

[语义锚点](semantics-anchor.md) 汇总共同边界与定义分工；[符号与函数对应索引](semantic-interface-index.md) 给出各层级的名称、类型和数学对应。

## 局部函数实例

[[weighted-kv-sparse-activation-example|接收驱动的带权 KV 与稀疏 Full]] 给出具体的模块与分层架构：带来源信息的聚合、有界私有 KV、多尺度记忆评分、允许弃权的预算选择，以及 Attention／前馈残差。文中定义训练目标与成本边界，并证明零消息删除、有限切面连续性、条件化硬化和联合求值关系。

可在读完 SettleGraph 第 5 节后阅读该例的局部公式，再结合分块教材研究时间批。不同局部模块通过各自的状态空间与函数选择进入共同框架。

## 数学研究与实现对应

本目录承担数学与语义上游职责：定义架构、具体模块与训练机制的函数形式，证明一般关系，并给出可核对的实例。公共执行基座承接局部函数、切面继续和精确求值；实验平台选择尺寸与训练配置、实现模块并验证训练与性能。

每项实现对应均需说明所采用的对象、函数与比较关系。完整记录相等、指定投影相等和反向规则相等分别具有各自的条件。教材附录给出系统用语与这些数学对象的对应。

- [版本差异与下游采用说明](semantic-versions.md)
- [研究备忘索引](memos/README.md)
- [学习资源](resources/learning-resources.md)
- [正时延 Graph 教学参考程序](examples/positive_delay_graph_reference.py)

## 架构与成本问题

固定拓扑、局部连接与可达容量增长构成 TIDE 的架构研究问题。有关扩容成本的结论须明确约束状态、参数、区域宽度、入度出度、入口终端宽度与每次处理量。

联合求值的外层块数、块内工作量与并行深度，以及具体设备上的性能分别分析。相应条件和结果见分块教材及各局部函数实例。
