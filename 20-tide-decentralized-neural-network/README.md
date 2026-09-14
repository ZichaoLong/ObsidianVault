---
type: index
status: active
as-of: 2026-09-14
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
| Graph | 有限固定消息图，可有环；边时延为正整数；每个有限逻辑时间切面具有确定记录 | [[positive-delay-graph-finite-cut-learning-note|正时延 Graph 的有限切面语义]] |
| TimedDAG | 固定消息图进一步要求无环；保留多端口、不等长路径与一般区域划分 | [[timed-dag-region-selector-learning-note|带区域选择的 TimedDAG]] |
| SettleGraph | 区域依赖严格有序，每个输入位置单次结算，具有单输入与单输出；通过明确时间与边界编码嵌入 TimedDAG | [[settlegraph-learning-note|单次结算图 SettleGraph]] |

“Graph”在当前框架中指 PositiveDelayGraph，不表示任意带副作用程序。零时延边不在设计范围内。

[[timed-dag-chunk-prefill-learning-note|TimedDAG 分块预填充教材]] 是执行专题，不是第四种架构。它区分正确继续、节点级时间批、节点内部并行性与硬件效果。

## 阅读路线

~~~text
SettleGraph：一次输入、共同选择、记忆与单次结算
    ↓ 明确的嵌入
TimedDAG：统一逻辑时间、消息纤维、关闭与继续
    ├─→ 分块预填充：哪些结构允许节点级时间批
    └─→ 正时延 Graph：空间环与有限切面
~~~

SettleGraph 是可选入门层级，不是 TimedDAG 的强制前置。后两篇均以前置 TimedDAG 教材为基础；学习者不必先读旧研究材料或完成系统课程。

当前共同接口区分候选新状态、本次计算快照与下一持久状态；也区分区域激活集合、各节点局部控制量与区域选择历史。状态可按统一逻辑时间衰减，或依激活结果清理。下一状态不读取完整计算结果；没有输入的时刻不自主激活或发送。时间衰减可由“保存值＋时间戳”在下一次读取时解码。

## 上游与实验平台

Graph 理论研究与 checkpoint 生长已在 SettleGraph 核心前向语义处发生弱汇合：从已有模型接入、单次结算的构型，可以作为总框架中的受限实例。这不表示所有实验扩展、特殊梯度或实现结果已经被统一证明。

fractal-latcarf 是 SettleGraph 的实验平台。它维护实际模块公式与选择空间、模型接入位置、初始化、训练设置、实现、测试和实测结果；上游维护抽象契约、教材与一般证明。当前对应与待下游单独对齐的接口见 [[semantics-anchor#下游如何引用|下游如何引用]]。

一般等价性定理可以留在上游，具体实现是否满足其前提由下游验证。旧 LH 的实现快照不代表 fractal-latcarf 当前状态，本仓库也不持续镜像下游“最新通过状态”。

## 进一步阅读

[[memos/README|研究备忘索引]] 按问题组织数学专题、构型候选、学习风险、执行成本及外部背景。[[memos/research-questions|研究问题]] 保存剩余问题，不要求各层级服从同一条强制开发阶梯。[[resources/learning-resources|学习资源]] 提供按需书目。[[memos/history/migration-map|旧内容迁移索引]] 记录重写来源与 Git 追溯方法；旧长文不再构成第二套核心。

[正时延 Graph 教学 reference](examples/positive_delay_graph_reference.py) 验证有限切面、控制量、状态快照及继续等式。它属于教材附件，不承担完整神经模型或硬件平台职责。旧 HB 示例归入历史附件。

## 架构目标与数学约束

TIDE 的历史全称为 Topology-Invariant Degree-bounded Expansion Architecture for Autoregressive Token Inference。固定拓扑、局部连接与可达容量增长仍是架构目标；各具体架构族必须另外检查成本。

一个图有限，不等于扩容时所有节点成本具有统一上界。要主张有界成本扩容，必须同时约束状态、参数、区域宽度、入度出度、入口终端宽度与每次处理量。增加一个平铺区域的候选数不能单独完成这个目标；逻辑局部连接也不自动证明物理通信便宜。

目录名保留用于已有仓库链接。“去中心化”是历史动机和可研究的系统性质，不替代当前数学定义。
