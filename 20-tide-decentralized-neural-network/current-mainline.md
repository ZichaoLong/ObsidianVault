---
type: current-mainline
status: active
as-of: 2026-09-10
tags:
  - tide
  - current-mainline
  - settlegraph
  - timed-dag
  - delayed-graph
---

# TIDE 当前主线：从正时延有环 Graph 到 structural SCC lowering

> [!summary] 本页只回答三个问题
> 1. TimedDAG 当前已经得到什么？
> 2. 正时延有环 Graph 的 finite-cut 语义已经得到什么？
> 3. Graph 线下一步研究哪类 SCC，而不加入什么？
>
> 本页是当前学习与开发入口。既有数学、架构、runtime 和 SCC 长文是按需查阅的研究资料库，不是继续推进前必须从头读完的教材。

## 一句话主线

```text
Graph 收缩线：TimedDAG（固定空间 DAG）
→ 正时延有环图的 finite-cut 语义【当前已闭合】
→ structural SCC 的低-span chunk lowering【当前下一台阶】

checkpoint 生长线：SettleGraph
→ 训练、推理与性能验证
```

两条路线可以共享概念和实现接口，但不预设最终得到同一个结构族。

## 当前已闭合的数学教材层

当前正典由三份文档组成：

1. [[timed-dag-region-selector-learning-note|《带区域选择的 TimedDAG：从零开始的数学定义》]]：定义多输入、多输出、正时延空间 DAG、时间纤维、节点状态、region selector、selector-history、seal、合法阶段轨迹、事件 DAG 与 continuation，并证明有限唯一性、关闭、次序无关和切面继续。
2. [[timed-dag-chunk-prefill-learning-note|《TimedDAG 的分块预填充：支持集、时间切面与分层区域》]]：区分语义存在性、大块外层调度、低 span 与硬件性能；给出 graded DAG 的节点级 token 对齐切面，以及严格分层 region 的 exact chunk-prefill 外层算法。
3. [[positive-delay-graph-finite-cut-learning-note|《正时延有向图的有限切面语义：从 TimedDAG 到有环 Graph》]]：允许固定消息图含环，证明 finite-cut 存在唯一性与定量有限性、finite-cut 事件 DAG、seal 推进、continuation sufficiency 和 cut composition；并给出 SCC-local region 条件下的 exact message-SCC 外层调度及跨 SCC selector 反例。

旧的 TimedDAG-v0 学习笔记已由第一份教材的一般定义取代。旧笔记中的实现细节仍可从 Git 历史查阅，但不再作为当前定义入口。

这三份教材已经把一般空间 DAG 的 correctness、若干 DAG 高性能 prefill 充分条件，以及正时延有环图的 finite-cut correctness 分开。它们尚未证明：任意 TimedDAG 或 structural SCC 都有低-span prefill、SettleGraph 已形式嵌入，或任意 selector-history 都能并行扫描。

## 独立的 checkpoint 生长线：SettleGraph

SettleGraph 的权威来源在 `fractal-latcarf`：

- [随分支更新的 SettleGraph 语义](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/experiment-semantics-and-naming.md)
- [实现与等价性验证计划](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/settlegraph-implementation-plan.md)

这条线从存在预训练 checkpoint、可训练且已有高性能 prefill 的架构出发，主要承担可重复实验、配对归因、训练稳定性验证和实际推广。

SettleGraph 的主体结构看起来可以落在 TimedDAG 严格分层类的更窄 profile 中，但正式结论仍需给出全部坐标的编码、投影与 trace 等式。两边出现同名的 selector-history 或参数字段，不自动构成嵌入证明。

## 已闭合台阶：正时延有环图

这个已经完成的台阶只删除“固定空间图无环”这一条限制，仍要求每条边满足严格正时延：

```text
静态图：允许有向环
动态事件：逻辑时间 θ 的消息只能影响 θ+d，且 d ≥ 1
```

[[positive-delay-graph-finite-cut-learning-note]] 已按以下顺序闭合这一层：

1. 把 TimedDAG 的逐逻辑时间递归推广为有限 cut 上的语义；
2. 证明每个合法有限 cut 的存在唯一性与有限抽象函数作用数；在局部函数有终止实现时再推出有限工作；
3. 定义并闭合 seal、continuation 与 cut composition；
4. 给出 SCC-local profile 的 exact message-SCC 外层调度，并把低 span 留给下一台阶。

一次开放执行可以永不全局停止；这不妨碍某个得到足够输入 seal 的有限 cut 在有限工作后完成。structural SCC 只给出图论分解，不自动给出 SCC 内部语义、终止性或并行算法。

## finite-cut 台阶的退出审计

正时延有环语义至少应完成：

- [x] 有限 cut 的对象、输入边界与输出投影均已定义；
- [x] 每个合法输入的有限 cut 结果存在且唯一；获得覆盖目标 cut 的 source seal 后可以在线有限推进；当前微节点规格还直接给出事件与在途消息的定量有限界；
- [x] continuation 保存未来所需的全部节点状态、selector-history、绝对时间与在途消息；
- [x] 相邻 cut 的分段执行等于一次执行；
- [x] seal、完成谓词与正时延传播给出不允许未来回写过去的硬进展证书；
- [x] [reference interpreter](examples/positive_delay_graph_reference.py) 已对延迟自环、两节点环、随机 cut 划分和随机 ready-event 调度比较 $B,\mathcal C,\mathcal A,q,y,M,Z,W$ 投影。

这些条件现已满足。下一台阶只对具体 SCC profile 登记 sequential fallback、packed loop、scan、固定轮展开或其他 lowering，并分别证明其 work、span、memory 与 communication。

## Graph 线下一台阶：有代数见证的 structural SCC

当前问题不再是“正时延环能否精确继续”，而是：哪些 dependency-complete structural SCC 具有真正降低序列轴 span 的区间求值器。

研究顺序固定为：

1. 从 message SCC 与跨 SCC selector 反例出发，定义包含 selector owner、history 和所有可变状态依赖的 dependency-complete SCC 边界；
2. 为每个 SCC 保留逐边 identity、时延、输入输出投影与 continuation，先与微观 reference trace 对拍 exact sequential fallback；
3. 首先研究 affine/associative scan、固定轮展开与 causal-bulk 等具有明确复合代数的子类；
4. 对每个子类分别证明 work、span、memory、communication 和 cut composition；
5. 无法给出低-span witness 的 SCC 明确登记为 sequential fallback，不因封装成一次 API 就称为高性能。

## 明确延期

当前下一台阶不加入：

- 零时延边或代数环；
- 一般 fixed point、root solver 或无限同刻迭代；
- 随机或依赖墙钟竞争的模型语义；
- 从图结构直接推出 GPU/NPU 性能；
- 来源未定义的公共 context 状态。

这些对象若以后加入，必须重新给出函数类型、事件依赖、cut 状态与证明义务，不能只沿用系统名称。

## 推荐阅读顺序

1. 先读 [[timed-dag-region-selector-learning-note]]，手算直接递归、selector-history、seal 与 continuation。
2. Graph 线随后读 [[positive-delay-graph-finite-cut-learning-note]]，理解为什么空间环不破坏 finite-cut 递归，并手算 $W_b$ 与 cut composition。
3. 研究空间 DAG 的 chunk lowering 时读 [[timed-dag-chunk-prefill-learning-note]]，区分安全时间切面、严格分层充分条件、tile witness 与低 span。
4. checkpoint 生长实验按需阅读并运行 `fractal-latcarf` 的 SettleGraph 语义与 reference。
5. 旧长文只作为材料来源，不反向改写新教材中的已定义对象。

## 本页维护规则

1. 本页保持短小，只记录当前台阶、下一台阶、延期范围和退出条件。
2. 每次只允许一个 Graph 线“下一台阶”；当前只研究正时延 structural SCC 的 lowering，不同时加入零时延、偏序时间和 solver。
3. 只有产生稳定语义、reference、证明或反例后，才把结论整合进 TIDE 长文。
4. 动态工程状态必须带日期和 commit；未提交 WIP 不进入能力声明。
