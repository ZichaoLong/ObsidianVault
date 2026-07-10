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
- `~/llm/tide` 的 CPU 路径已经不只是 LH phase runtime 骨架；独立 Tide kernels 已在当前覆盖配置和 hidden/cache mode 上与 native LH 对齐，并已有 phase artifact 与压力测试入口。
- 当前仍没有得到 strict model-level `prefill()`、一般 graph 的高性能 chunk prefill 定理或 Ascend backend。
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

| 文档 | 职责 | 当前地位 |
| --- | --- | --- |
| 本页 | 入口、研究约定、当前主线、历史动机 | 当前入口 |
| [[step-transition-mathematical-specification]] | transition、fold、semantic contract、DAG、quotient、主力 kernel 定理 | 规范性数学主线 |
| [[step-transition-implementation-specification]] | graph/state/workspace/schedule/kernel 接口与验证约束 | 规范性实现主线 |
| [[current-architecture-state]] | `~/llm/tide` 当前代码、测试和未覆盖边界 | 动态工程快照 |
| [[logical-event-dag-related-theories]] | CPU、编译器、数据流、provenance、scan 等参考谱系 | 先修与参考，不是证明 |
| [[prefill-decode-equivalence-context]] | 从 LH、`tide.old` 到当前抽象的早期探索过程 | 历史材料，非当前规范 |

建议阅读顺序：

1. 本页。
2. [[step-transition-mathematical-specification]] 的第 1-3 节。
3. [[step-transition-implementation-specification]]。
4. [[current-architecture-state]]。
5. 遇到 CPU/编译器/数据流概念时，再查 [[logical-event-dag-related-theories]]。
6. 只有需要追溯设计来源时，才读 [[prefill-decode-equivalence-context]]。

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
3. 用 Unified Contract-DAG-Quotient Theorem 统一 contract resolution、logical event DAG、聚合与物理执行顺序。
4. 用 non-degenerate chunk certificate 排除单节点 oracle，并把 correctness 与 work/span performance witness 分开。
5. 把 mailbox、phase、selector、readout、pronounce 与 LH-like roles 视为候选机制，逐个检查、简化或替代，而不是默认全部加入 strict family。

### 下一工程阶段

1. 增加 memory-state 级 per-phase artifact equality。
2. 依据数学 contract 设计第一版 model-level `prefill()`，而不是仅在调用端循环 `think()`。
3. 先证明并实现 token-wise、causal attention、affine scan 等 kernel-level chunk paths。
4. 再做并行 executor、packed/crossbatch fusion 与 layout 优化。
5. CPU semantic gate 稳定后，再推进 Ascend lowering、device placement 与 graph-node affinity。

## 当前主张边界

当前可以主张：

- Tide 的 role-aware phase abstraction 能承载当前覆盖范围内的 LH C++ 计算过程。
- 独立 Tide CPU kernels 在当前覆盖配置上可数值复刻 native LH。
- 数学文档已经给出 Transformer/Mamba 的 B0 chunk correctness 路线，以及一般 logical event DAG / quotient correctness gate。

当前不能主张：

- 任意一般 graph 都有高性能 chunk prefill。
- 当前完整 LH 自动满足 strict `prefill = decode fold`。
- CPU 数值对齐已经证明训练可行性、scaling 或性能优势。
- 通用高性能 packed/crossbatch lowering、异步执行或 Ascend backend 已经完成。

## 历史动机：从链表、星型到去中心化 Graph 神经网络

> [!summary] 核心动机
> MoE 让参数计算稀疏化，但 expert dispatch、全局路由与同步仍可能形成集中式通信压力。TIDE 想探索有界度局部通信的 Graph 神经网络，研究是否能获得不同的计算与通信扩展路径。

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

### 附录：原始吞吐记录

这部分是早期实验记录，保留为历史参考。

| ms/per token/step |          |     |        | 56Core CPU |     |     |     | 7*T4 GPU 15GB / [8.5B 8*V100 32GB] |      |     |     |
| ----------------- | -------- | --- | ------ | ---------- | --- | --- | --- | ---------------------------------- | ---- | --- | --- |
| Size              | Node     | Dim | Batch  | 1          | 16  | 256 | 512 | 1                                  | 16   | 256 | 512 |
| 1B                | 7168/64  | 128 | Grad   | 140        | 50  | 27  | 24  | 350                                | 156  | 60  | 48  |
|                   |          |     | NoGrad | 130        | 34  | 5   | 2.5 | 320                                | 120  | 17  | 9   |
| 8.5B              | 57344/64 | 128 | Grad   | 1350       | 543 | 234 | 136 | 3600                               | 1200 | 273 |     |
|                   |          |     | NoGrad | 1000       | 375 | 54  | 29  | 3600                               | 906  | 109 | 57  |

| ms/per token/step |        |      |        | 56Core CPU |     |   |      | 7*T4 GPU 15GB |   |      |      |
| ----------------- | ------ | ---- | ------ | ---------- | --- | - | ---- | -------------- | - | ---- | ---- |
| Size              | Node   | Dim  | Batch  | 1          | 16  |   | 512  | 16             |   | 512  | 2048 |
| 0.58B             | 224/32 | 512  | Grad   | 15         | 2.5 |   | 0.57 | 6.9            |   | 1.4  | 1    |
|                   |        |      | NoGrad | 15         |     |   | 0.3  |                |   | 0.65 | 0.35 |
| 2.2B              | 224/32 | 1024 | Grad   | 25         | 5.6 |   | 1.17 | 8.8            |   | 1.8  | 1.2  |
|                   |        |      | NoGrad | 25         |     |   | 0.88 |                |   | 0.88 | 0.56 |
| 8.8B              | 224/32 | 2048 | Grad   | 85         |     |   | 3.6  | 9.1            |   | 2.8  |      |
|                   |        |      | NoGrad | 85         |     |   | 3.3  |                |   | 1.46 | 0.95 |

| ms/per token/step |                   |   |        | 56Core CPU |     |   |     | 7*T4 GPU 15GB |    |   |     |
| ----------------- | ----------------- | - | ------ | ---------- | --- | - | --- | -------------- | -- | - | --- |
| Qwen 7B           |                   |   | Batch  | 1          | 16  |   | 512 | 1              | 16 |   | 512 |
| 44input+56output  |                   |   | NoGrad | 210        | 56  |   | 29  | 46             | 21 |   | 6.4 |
| 34input+66output  |                   |   | NoGrad |            |     |   |     | 51             | 24 |   | 6.7 |

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
