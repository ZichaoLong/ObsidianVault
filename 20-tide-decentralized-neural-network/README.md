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

[接收驱动的带权 KV 与稀疏 Full](weighted-kv-sparse-activation-example.md) 具体定义来源聚合、有限时间窗口记忆、多尺度评分、允许弃权的预算选择，以及 Attention 与前馈残差。它在共同接口下选择 $X_v=P=\mathbb R^{1+d}$、接收驱动更新和广播 Full，并给出训练目标、数值性质及联合求值见证。

局部实例固定具体函数和附加条件，公共执行基座实现图语义、切面继续与精确联合求值，实验平台选择尺寸、训练配置并验证效果。记录相等、指定投影相等和指定反向规则相等分别陈述。

## 延伸阅读

- [研究备忘](memos/README.md)：数学补充、架构机制、学习风险与外部背景。
- [学习资源](resources/learning-resources.md)：按问题选读的书目和练习。
- [教学参考程序](examples/positive_delay_graph_reference.py)：正时延图的有限切面与记录比较。
- [版本差异与采用记录](semantic-versions.md)。
