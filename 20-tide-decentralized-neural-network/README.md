---
type: index
status: active
tags:
  - tide
  - mathematics
  - semantic-anchor
---

# TIDE：数学教材与语义总览

TIDE 研究固定消息图上的有状态计算：节点聚合收到的值、形成候选状态，区域共同选择完整计算，结果沿正时延边传播。节点的私有状态与区域的选择历史连接不同时间的作用。

本目录是数学与语义上游，面向第一次接触 TIDE 的数学读者，给出对象、函数、例子和证明。共同名称与返回值族也为下游实现提供直接对应；系统术语和计算表示见各篇附录。

## 阅读路线

| 教材 | 主要问题 | 前置 |
|---|---|---|
| [SettleGraph：单次结算图](settlegraph-learning-note.md) | 候选、选择、记忆与输出怎样组成一次结算和有状态序列 | 集合、函数与归纳法 |
| [带区域选择的 TimedDAG](timed-dag-region-selector-learning-note.md) | 一般到达时间下的纤维、规范作用、关闭与切面继续 | 集合、函数与归纳法 |
| [正时延图的有限切面语义](positive-delay-graph-finite-cut-learning-note.md) | 空间有环时的有限记录、继续与强连通分量 | TimedDAG |
| [TimedDAG 的分块预填充](timed-dag-chunk-prefill-learning-note.md) | 因果状态块、完整输出时间批与求值阶段 | TimedDAG |

SettleGraph 与 TimedDAG 都可独立作为起点。读完 TimedDAG 后，按问题选择有环图或分块求值续篇。

## 共同语义与层级

$$
\mathrm{SettleGraph}\subseteq\mathrm{TimedDAG}\subseteq\mathrm{PositiveDelayGraph}.
$$

SettleGraph 使用严格区域分层、对齐的边时延与输入日程，按输入位置得到单次结算。TimedDAG 允许一般有限输入日程与区域划分；PositiveDelayGraph 进一步允许空间有环和局部有限的输入流。各层使用同一套局部空间、函数参数和规范作用结果。

承载值空间 $P$ 与本地内容空间 $X_v$ 分别定义。Agg、Upd、Read、SelStep、Next、Full 依次描述聚合、候选状态、选择依据、共同选择、状态延续和完整输出。Full 返回逐边与逐端口两个值族；候选状态、计算快照和下一持久状态各有明确坐标。

[语义锚点](semantics-anchor.md) 汇总共同定义与层级条件；[符号与函数索引](semantic-interface-index.md) 提供名称、类型、记录和证明位置的查阅入口。

## 局部模块与架构实例

可复用的特化分别定义，具体实例给出它们的组合。局部计算语义固定函数与数值性质；拓扑和时间配置固定图、区域、端口及注入日程；组合实例绑定来源与读出，并核对所用结论的条件。

| 文档 | 内容 |
|---|---|
| [带权消息的有状态局部架构](local-architecture-learning-note.md) | 共同载荷、接收、状态与读取、区域控制和广播，组合条件及正典对应 |
| [区域评分与发送分配](region-allocation-learning-note.md) | 评分信息、增益依赖、稠密与稀疏发送函数、导数和局部极限 |
| [带权 KV](weighted-kv-sparse-activation-example.md) | KV 写入、描述与内容读取、位置、完整例子、联合求值及数值证明 |
| [循环记忆](recurrent-memory-learning-note.md) | 完整 affine／delta 状态模块，逻辑时间、弱输入、仿射复合与继续 |
| [全连接分层实例](weighted-kv-layered-example.md) | 相邻层全连接、对齐时间、来源和读出；配置生效条件及异构记忆组合 |
| [HB-Lattice 实例](weighted-kv-hb-lattice-example.md) | 多区域展开与收拢、稀疏邻域；候选传播、工作量及记忆组合 |

局部教材与架构实例通过同一组函数组合。定义、推论、教学例子与证明形成数学主线；研究与实现分别沿以下入口继续。

| 文档 | 主要问题 |
|---|---|
| [设计分析](memos/architecture/selector-and-memory.md) | 整体设计空间、信息与梯度依赖、成本取舍、外部证据和可修正的研究判断 |
| [可选研究问题与对照](memos/learning-systems/weighted-kv-experiment-plan.md) | 按问题取用的比较、训练目标及结果解释；具体优先级由研究者安排 |
| [实现核对](weighted-kv-implementation-checks.md) | 前向、反向、边界、继续及组合与数学定义的对应 |

记录相等、指定投影相等和指定反向规则相等分别陈述。具体训练、实现与测量由下游维护。

## 延伸阅读

- [研究备忘](memos/README.md)：数学补充、架构机制、学习风险与外部背景。
- [学习资源](resources/learning-resources.md)：按问题选读的书目和练习。
- [教学参考程序](examples/positive_delay_graph_reference.py)：正时延图的有限切面与记录比较。
- [版本差异与采用记录](semantic-versions.md)。
