---
type: research-memo
status: archived
date: 2026-08-13
archived-date: 2026-08-14
tags:
  - tide
  - appendix
  - research-memo
  - scc
  - migration-index
  - deferred-open-questions
---

# SCC 宏节点：剩余研究问题与迁移索引

> [!summary] 本页定位
> 2026-08-13 的 SCC 宏节点讨论已经完成主线分流。本页不再保存讨论原稿，只记录内容迁往何处，以及尚不具备正式答案、明确延期的问题。返回 [[20-tide-decentralized-neural-network/README|Tide 主入口]]。

> [!important] 唯一事实源
> 本页不是数学、架构、runtime 或背景事实源，也不得作为证明前提或实现 contract 被引用。已经迁移的定义、例子、校正和阶段性结论均已从本页删除；其当前版本只以对应核心文档为准。若本页的迁移标签与核心文档冲突，以核心文档为准。

## 1. 迁移索引

| 主线职责 | 原讨论的迁移范围 | 当前状态与唯一落点 |
| --- | --- | --- |
| 数学与语义 | 节点窗口 reference fold、时间分块义务、static schema SCC 与 dynamic dependency 的分层、多端口边界、finite-cut 与因果证书问题 | 已主线化；正式对象、命题、反例和证明只查 [[tide-mathematical-foundations]]。与黑盒自适应执行有关的反向边界只查 [[adaptive-routing-prefill-lower-bound]]。 |
| Runtime 与验证 | macro event interface、timed I/O、seal/progress、pending/in-flight work、continuation、checkpoint/replay 与失败行为 | 已作为候选且未实现的工程 contract 分流；接口状态和测试义务只查 [[tide-runtime-validation-and-status]]。 |
| 架构与训练 | Graph 收缩、结构化空间候选、prefill/streaming 取舍、learning value、非退化成本与 compute-matched 实验 | 已分流为架构候选和实验议程；不构成数学结论，唯一落点是 [[tide-model-architecture-and-training]]。 |
| 背景与文献 | SCC/动态展开、finite-prefix productivity、logical progress、watermark 强度与 Zeno 的相邻研究谱系 | 已分流为外部背景；引用边界和一手来源只查 [[tide-background-history-and-references]]，该文档同样不承担 Tide 证明。 |

原稿中的汇总结论、具体示例、既有算子校正、research-profile 正文和已经确定的接口说明均不在这里保留副本。原稿的整合建议由上表取代；原“待形式化问题”只留下下面仍真正开放的子集。

## 2. 延期开放问题

> [!warning] 阅读边界
> 下列条目只说明问题为何尚未进入主线，以及将来若解决应落到哪里。问题名不是已定义对象，提问方式也不预设答案、可解性或研究优先级。

### O1. 偏序时间与 capability frontier

**开放问题**：是否需要把当前 profile-specific logical time 推广为真正的偏序时间；若需要，怎样用 antichain/capability 表示 cut、输入进展和跨 macro 的可继续生产能力，并定义 capability 的创建、转移与释放。

**为何延期**：当前严格 profile 尚可使用更简单的时间坐标。引入 capability 会同时改变进展证明、资源所有权、backpressure 和 checkpoint contract；在没有通用 executor 与最小反例前直接形式化，容易把 Naiad/timely 的特定机制误当成 Tide 必需语义。

**未来落点**：时间域、cut 与 progress soundness 进入 [[tide-mathematical-foundations]]；capability ledger、恢复和测试进入 [[tide-runtime-validation-and-status]]；外部机制比较只进入 [[tide-background-history-and-references]]。

### O2. Port quotient theorem

**开放问题**：在什么充分或必要条件下，可以把若干 boundary edges、内部 endpoints 或 timestamped messages 商成较少的 macro ports/aggregate messages，同时保持所有声明的输出、状态、路由、continuation 和未来可观察行为。

**为何延期**：安全商映射取决于下游 kernel、状态 alias、provenance、动态 routing 和观察等价，不能从 SCC 拓扑单独推出。当前还没有一个既非平凡 identity、又覆盖真实神经 kernel 的统一 port quotient 条件。

**未来落点**：正式 quotient 对象、定理和反例进入 [[tide-mathematical-foundations]]；具体 aggregation/fusion lowering 与 translation validation 进入 [[tide-runtime-validation-and-status]]。

### O3. Owner-free causality

**开放问题**：在何种 profile 下，仅凭 message/event identity、logical time、显式 dependency、state version 和 readout identity，就足以证明 token-prefix causality 与 artifact equality，而完全不需要 `owner` 标签。

**为何延期**：部分现有证书仍使用 `owner` 表达归属或同刻并列语义；删除它需要先区分“证明便利字段”和“不可恢复的观察信息”，再用最小反例验证不会丢失 readout、route 或 continuation 的归属关系。

**未来落点**：充分条件、反例及与可选归属证书的关系进入 [[tide-mathematical-foundations]]；owner-free Event IR 的 property test 与日志对拍进入 [[tide-runtime-validation-and-status]]。

### O4. Partial semantics boundary

**开放问题**：对只在部分输入上终止、只对部分 cut productive，或可能显式失败的 macro，应采用 partial function、带 failure/divergence 的结果语义，还是将其排除出 strict family、只留在 best-effort execution 中。

**为何延期**：该选择会改变 `prefill = decode` 的比较对象、failure 的可观察性、训练时梯度路径和 runtime disposition。一般程序终止性障碍也意味着不能期待一个对开放 Graph 完备的自动判定器。

**未来落点**：partial/failure/divergence 的正式语义进入 [[tide-mathematical-foundations]]；允许哪些模型进入哪类实验进入 [[tide-model-architecture-and-training]]；超时、预算耗尽与恢复行为进入 [[tide-runtime-validation-and-status]]。

### O5. Finite-cut progress certificate composition

**开放问题**：当 macro 具有可变 delay、多输入 source、backpressure 和跨 cut continuation 时，局部 seal、progress frontier 与 hard output certificate 需要满足什么闭包条件，才能沿 condensation DAG 合成为 model-level finite-cut progress。

**为何延期**：它依赖 O1 的时间/进展表示、O2 的端口边界，以及尚未固定的 fairness、local-finiteness 和 channel-ownership 前提。现有候选 runtime 字段只能提出 proof obligation，不能替代组合定理。

**未来落点**：certificate composition 与不健全反例进入 [[tide-mathematical-foundations]]；调度、backpressure、checkpoint 和三类行为测试进入 [[tide-runtime-validation-and-status]]。

### O6. SCC macro 非退化与成本证书

**开放问题**：怎样限制 macro 粒度、内部 primitive、边界宽度和隐藏控制状态，防止把整个 sequential computation 封装成单一 SCC oracle；又怎样分别核算 work、span、memory、communication 和 hardware utilization。

**为何延期**：非退化条件必须同时参考 IR 与 machine cost model；过早给出统一常数会错误排除合法 fused kernel，过弱又会让高性能 claim 变成空话。当前尚无可用于校准的 SCC macro 实现和 benchmark。

**未来落点**：模型 capability 与实验预算进入 [[tide-model-architecture-and-training]]；可审计 cost ledger 和 profiler 证据进入 [[tide-runtime-validation-and-status]]；若出现新的黑盒自适应下界，再进入 [[adaptive-routing-prefill-lower-bound]]。

### O7. Exact restriction、approximation 与 distillation

**开放问题**：把 streaming-only Graph 收缩为 prefill-compatible family 时，哪些步骤是 exact structural restriction 或 semantics-preserving lowering，哪些是带显式误差界的 approximation，哪些只是以数据和 teacher 行为为依据的 distillation。

**为何延期**：三类主张需要完全不同的证据。exact 路径要求全输入语义等价；approximation 要先选择误差度量、输入域与组合误差界；distillation 只能给经验分布上的训练结果。当前没有理由把它们压成一个统一“转换定理”。

**未来落点**：exact 部分若可证明，进入 [[tide-mathematical-foundations]]；approximation/distillation 的假设、数据、teacher、指标和消融进入 [[tide-model-architecture-and-training]]；具体 lowering 的数值误差验证进入 [[tide-runtime-validation-and-status]]。

### O8. Learning value 与执行 profile 的受控归因

**开放问题**：反馈、持久状态、动态 routing 或开放迭代带来的 learning value，能否在参数量、训练 token、FLOPs、显存、能耗、墙钟和优化稳定性均可审计的条件下，与执行 profile 带来的训练规模差异分离。

**为何延期**：目前没有受控训练证据，也没有足够稳定的 streaming/macro runtime 用于公平计费。纯理论执行谱系既不能证明 learning value，也不能排除训练不足造成的假阴性。

**未来落点**：研究假设、baseline、compute-matched protocol 和泛化指标进入 [[tide-model-architecture-and-training]]；真实性能与资源计量进入 [[tide-runtime-validation-and-status]]。

## 3. 维护规则

1. 核心文档一旦回答某个开放问题，应直接删除本页对应条目；不要把答案复制回本页。
2. 若问题只被部分解决，只保留尚未解决的最小剩余问题，并链接唯一核心落点。
3. 新定义、定理、接口字段、架构结论、实验数字和文献综述不得首先写入本页。
4. 本页不保留讨论逐字稿、已合入例子或为了“上下文完整”而复制的主线正文。
5. `status: archived` 表示原讨论稿已归档；开放问题是否仍值得投入，由核心文档的当前研究顺序决定。

返回 [[20-tide-decentralized-neural-network/README|Tide 主入口]]。
