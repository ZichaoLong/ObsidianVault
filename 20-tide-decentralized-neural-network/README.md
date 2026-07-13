---
type: index
status: active
tags:
  - tide
  - decentralized-nn
---

# TIDE / 去中心化神经网络

> [!summary] 本页定位
> 本页是 TIDE 线的唯一入口，负责给出当前命题、研究方法、文档职责与阅读顺序。数学定义与证明以 [[step-transition-mathematical-specification]] 为准；代码完成度以 [[current-architecture-state]] 为准。

## 一页版结论

TIDE 是 `Token Inference Decentralized Engine`。

- TIDE 的核心目标是构建前向隐藏态只做有界度局部通信的自回归神经动力系统。
- 当前第一主线不是继续扩张 runtime surface，而是严格研究 `prefill / decode` 等价性：先固定 reference semantic contract，再证明 chunk implementation 保持该 contract。
- Tide static graph 可以有环、路径也可以动态生成；当前更强的候选约束是：每次对有限 chunk 的终止 execution 应能展开为 dependency-complete logical event DAG。
- dynamic selector 不需要预先枚举完整 DAG，但每条依赖都应推进 token / round / phase / microstep 等 logical rank；同一 logical rank 内的 zero-delay SCC 默认不进入 strict core。
- `~/llm/tide` 的 CPU 路径已经不只是 LH phase runtime 骨架；独立 Tide kernels 已在当前覆盖配置和 hidden/cache mode 上与 native LH 对齐，并已有 phase artifact 与压力测试入口。
- 当前仍没有得到 strict model-level `prefill()`、一般 graph 的高性能 chunk prefill 定理或 Ascend backend。
- 对允许任意黑盒自适应 routing 的模型类别，[[adaptive-routing-prefill-impossibility]] 已证明：若 prefill 保持 exact、工作量接近实际 route chain 且不枚举整个 routing state space，则 adaptive depth 至少随 token 数线性增长。该结论尚未自动覆盖每个具体 LH selector 配置。
- 正向候选 [[token-owned-general-dag-routing]] 已把 leveled-only 约束放宽为一般 finite unit-delay DAG，并用严格递增注入时钟 $\sigma(t)$ 分离 external token step、global internal round、trajectory path age 与 phase。它证明：若每个 node 对 owner/frontier-labelled timestamped event stream 提供 exact chunk transducer，则 absolute-time streaming schedule 与 node-topological chunk schedule 等价；固定/可变的多 internal-round step 与长路径 carry-over 都被覆盖。文档同时区分 exact chunk correctness、node-local chunk throughput 与 sequence-axis low span，后两者不能由 correctness theorem 自动推出。
- 数学上以 `transition -> fold -> semantic contract -> logical event DAG -> quotient -> simulation` 为主路径；CPU/编译器/数据流谱系只提供可借鉴的成熟方法，不替代证明。
- 稀疏性、动态 selector、异步执行与 NPU lowering 后置，避免在 reference semantics 尚未稳定时混入新的不可辨识变量。

## 研究推进与写作约定

后续主数学线按数学教科书方式推进：

- 所有符号先定义后使用；定义、例子、引理、定理、证明和边界按依赖顺序出现。
- 抽象定义优先配简单例子与反例，再进入 Transformer、Mamba 或 LH-like graph。
- 明确区分定义性等价、充分条件、必要条件、充要条件、工程验证与历史类比。
- CPU ISA、编译器、SSA、memory model、translation validation 等概念首次出现时，先给出自足解释，不假设读者具备体系结构或编译器背景。
- 外部谱系负责回答“是什么、解决什么、不解决什么、在 Tide 中对应什么”；正式结论仍落在 transition、DAG、quotient、simulation 与 fold 上。
- 如果一个证明必须依赖尚未定义的工程对象，先补最小先修小节，而不是把实现术语直接带入数学证明。

数学主文档采用以下固定模板：

```text
动机问题
-> 最小例子
-> 数学定义
-> 正例与反例
-> 引理 / 定理
-> 完整证明
-> 适用边界
-> 对实现与实验的约束
```

## 文档结构

文档按“规范、状态、研究、历史”分层。只有规范层定义当前语义；状态层只报告代码事实；研究与历史层不能反向覆盖规范。

| 层级 | 文档 | 职责 |
| --- | --- | --- |
| 入口 | 本页 | 当前命题、阅读顺序、主张边界与历史动机 |
| 规范 | [[step-transition-mathematical-specification]] | transition、fold、semantic contract、DAG、quotient、simulation 与主力 kernel 定理 |
| 规范 | [[step-transition-implementation-specification]] | graph/state/workspace/schedule/kernel/Event IR 接口与验证约束 |
| 状态 | [[current-architecture-state]] | `~/llm/tide` 当前代码、测试、完成度与目标架构缺口 |
| 研究 | [[adaptive-routing-prefill-impossibility]] | Exact、work-efficient 自适应 routing 的 parallel-query 下界及 Tide Graph 嵌入 |
| 研究 | [[token-owned-general-dag-routing]] | 一般 unit-delay DAG、owner/frontier-labelled event、三种同刻/融合语义、稀疏 routing 与 node-topological chunk 证明 |
| 研究 | [[selector-and-chunk-prefill-performance-memo]] | Selector、reference/execution DAG、capability contraction 与 work/span 设计备忘 |
| 研究 | [[finite-event-dag-and-zero-delay-loops-memo]] | dynamic execution、finite logical event DAG、zero-delay SCC 与后续定理候选 |
| 参考 | [[logical-event-dag-related-theories]] | ISA、编译器、SSA/MemorySSA、数据流、provenance、scan 与 fixed-point 谱系 |
| 历史 | [[prefill-decode-equivalence-context]] | 从 LH、`tide.old` 到当前抽象的早期探索过程 |

建议阅读顺序：

1. 研究语义：本页 -> [[step-transition-mathematical-specification]] 第 1-3 节 -> [[adaptive-routing-prefill-impossibility]] -> [[token-owned-general-dag-routing]] -> [[finite-event-dag-and-zero-delay-loops-memo]]。
2. 工程实现：[[step-transition-implementation-specification]] -> [[current-architecture-state]]。
3. 外部先修：遇到 ISA、SSA、MemorySSA、dataflow、fixed-point 等概念时查 [[logical-event-dag-related-theories]]。
4. 历史追溯：只有需要理解 LH、`tide.old` 与 StepTransition 的来源时才读 [[prefill-decode-equivalence-context]]。

## 当前研究主线

### LH 在研究中的位置

LH 提供的是一组围绕“局部通信 + 超稀疏”形成的复杂机制候选：分层局部图、双 cortex、bridge phase、selector、local hidden/KV、multi-tick readout 与 pronounce。这些机制具有三种价值：

- 提供早期研究动机与可运行的复杂样本。
- 暴露跨 node/edge 并行、node/edge 稀疏与状态生命周期需要面对的问题。
- 作为 native golden oracle，帮助检查 Tide 的 graph/phase/state 抽象是否足以表达真实复杂计算。

但 LH 不是唯一机制集合，也不是数学主线必须完整复刻的终点。既有 LH 把多种机制混合在同一个 transition 中，不能因此预设它自然满足 chunk prefill correctness。当前裁决原则是：

> 总体目标保持“局部通信 + 超稀疏”；当前优先约束保持 `prefill / decode` 等价性，以获得 model-level prefill 与序列并行；若某个 LH 机制破坏这一目标，可以在不违背总体目标的前提下简化、替代或暂时放弃，而不是无限复杂化理论和 runtime 去迁就它。

### 已完成的工程基座

- 从 LH C++ 中提取 role-aware graph、phase、state namespace、selector、local hidden 与 pronounce 语义。
- 建立 native LH golden path 和独立 Tide CPU path。
- 对齐当前覆盖配置下的 end-to-end logits、phase schedule、signal artifacts、selector count artifacts 与主要 hidden/cache mode。
- 建立 CPU stress benchmark；其结果是性能测量入口，不是 chunk prefill correctness 证明。

### 当前数学任务

1. 固定 reference semantic contract，明确输出、持久状态、workspace 与允许的 abstraction。
2. 用 B0 覆盖 GPT-style Transformer、Mamba/SSM 与主力 kernel family。
3. 在已有 Unified Contract-DAG-Quotient Theorem 上，补 finite dynamic execution 到 logical event DAG 的 representation lemma。
4. 证明 dependency completeness + local refinement / quotient 足以推出 chunk correctness，并明确这只是工程可用的充分条件体系。
5. 给出 zero-delay cycle dichotomy：增加 delay/state boundary、封装为 fixed-point kernel，或判定非法。
6. 用 non-degenerate chunk certificate 排除单节点 oracle 与隐藏恢复计算，并把 correctness 与 work/span performance witness 分开。
7. 把 mailbox、phase、selector、readout、pronounce 与 LH-like roles 视为候选机制，逐个检查、简化或替代，而不是默认全部加入 strict family。
8. 在 [[adaptive-routing-prefill-impossibility]] 的模型类别下，继续证明具体 LH selector 是否能够嵌入 pointer chasing；对不能嵌入的受限子类，寻找 token-local、scan、causal-bulk 或有限 chunk-wide frontier 结构。
9. 对一般 DAG 明确选择 absolute-time event order 与 token-prefix order 的关系；分别研究 owner-ordered、atomic-joint 与 frontier-owned fusion，并把 output readout 的 autoregressive causality 写入 contract。

### 下一工程阶段

1. 定义 `EventId / LogicalRank / Dependency / StateVersion / CommitEvent`，使 static executor 与未来 dynamic executor 共用一个 event contract。
2. 增加 memory-state 级 per-phase artifact equality。
3. 依据数学 contract 设计第一版 model-level `prefill()`，而不是仅在调用端循环 `think()`。
4. 先证明并实现 token-wise、causal attention、affine scan 等 kernel-level chunk paths。
5. 再做 dynamic event generation、并行 executor、packed/crossbatch fusion 与 layout 优化。
6. CPU semantic gate 稳定后，再推进 Ascend lowering、device placement 与 graph-node affinity。

## 当前主张边界

当前可以主张：

- Tide 的 role-aware phase abstraction 能承载当前覆盖范围内的 LH C++ 计算过程。
- 独立 Tide CPU kernels 在当前覆盖配置上可数值复刻 native LH。
- 数学文档已经给出 Transformer/Mamba 的 B0 chunk correctness 路线，以及一般 logical event DAG / quotient correctness gate。
- 数学文档已经在明确的 black-box parallel-query 模型下，证明任意自适应路由链不存在通用 exact、work-efficient、次线性 adaptive-depth prefill。
- 正向设计已经给出一般 unit-delay 空间 DAG 的 schedule-equivalence theorem，并明确区分 owner-ordered、atomic-joint 与 frontier-owned fusion 三种语义。

当前不能主张：

- 任意一般 graph 都有高性能 chunk prefill。
- 可以不经额外 selector embedding 或不可组合性分析，就把模型类别下界直接套用于每一个具体 LH/Tide selector 实例。
- 当前完整 LH 自动满足 strict `prefill = decode fold`。
- CPU 数值对齐已经证明训练可行性、scaling 或性能优势。
- 通用高性能 packed/crossbatch lowering、异步执行或 Ascend backend 已经完成。
- finite dynamic execution 的 DAG representation、zero-delay SCC theorem 与 causality verifier 已经完成；它们当前仍是 [[finite-event-dag-and-zero-delay-loops-memo]] 中的候选扩展。

## 历史动机：从链表、星型到去中心化 Graph 神经网络

> [!summary] 核心动机
> MoE 让参数计算稀疏化，但 expert dispatch、全局路由与同步仍可能形成集中式通信压力。TIDE 想探索有界度局部通信的 Graph 神经网络，研究是否能获得不同的计算与通信扩展路径。

本节保留研究方向形成时的直觉，不承担当前 `prefill / decode` correctness 证明；规范性结论仍以上述数学与实现文档为准。

为降低 dense Transformer 每个 token 激活全部 FFN 参数的成本，MoE（Mixture of Experts）只激活少量 experts，并已在大模型中证明这种参数稀疏路线具有工程可行性。

但参数激活稀疏不等于通信天然局部。MoE 仍需要路由、dispatch/combine、负载均衡与跨设备同步；在某些部署形态中，这些操作会形成新的集中式或 all-to-all 通信压力。

具体来说：

- 标准 dense Transformer block 可以抽象成顺序链：attention -> FFN -> attention -> FFN。
- MoE block 可以抽象成带全局 router / expert dispatch 的星型阶段。
- 这只是帮助形成研究问题的概念图，不是对所有 Transformer、MoE 实现和通信后端的精确描述。
- TIDE 的问题是：能否把一部分全局 dispatch 压力替换为长期稳定的有界度局部通信，同时保持可训练性和高效序列执行。

![[assets/images/linked-list-transformer-star-moe-decentralized-graph-nn-01.png|48%]] ![[assets/images/linked-list-transformer-star-moe-decentralized-graph-nn-02.png|48%]]

自然想法是把拓扑变成去中心化 Graph，从而消除 All-to-One 通信瓶颈，接近榨干物理极限。

### 要点一：节点激活也要去中心化

如果激活选择依赖复杂模块输入输出状态，节点激活也要去中心化。

Graph 神经网络仍需保持 token 进、token 出的自回归工作方式，并具有明确的先后时序关系。

后续可以设置多个输入节点与多个输出节点；当前主流 LLM 则是单输入、单输出。

### 要点二：Graph 需要输入到输出的固定路由路径

早期假设是：Graph 至少包含一条从输入到输出的稳定可达路径，其他路径作为局部支线。它是保证信号可传播的候选充分条件，不是已经证明的必要条件。

满足这两个要点后，就可以设计 Graph 神经网络，使 token 一个接一个输入网络，一个接一个输出。

通过 LibTorch C++、gather、scatter 等实现，可以支持：

- 空间并行：不同节点并行执行。
- batch 并行：同一节点内处理 batch。
- 自动构图与梯度反传：借助 LibTorch。

原始伪代码：

```python
for token in input_tokens:
    input_signal = embed(token)
    for i in range(route_len_from_input_node_to_output_node):
        for node in graph: # C++ 中用 openmp 并行执行
            emit(node_signal)
        for node in graph: # C++ 中用 openmp 并行执行
            receive(node_signal)
    output_token = output(output_node)
```

### 要点三：时间锚点与序列并行

早期吞吐结果没有实现序列并行，这对训练不友好。

问题暴露在两层循环：

```python
for token in input_tokens:
    for i in range(route_len_from_input_node_to_output_node):
```

要实现序列并行，关键是加入时间戳：

```text
t = token_id * route_len_from_input_node_to_output_node + i
```

每个节点（attention + ffn 块）处理信息时，应感知接收到的 graph 上游节点信号的时间戳。对 FFN 这较好处理；对 attention 或 linear attention 则要尤为小心。

早期实现的原始吞吐表已经移入 [[prefill-decode-equivalence-context#原始吞吐记录（历史）]]，避免与当前 `~/llm/tide` stress benchmark 混淆。
