---
type: note
status: active
tags:
  - tide
  - prefill-decode
  - step-transition
  - implementation
---

# StepTransition Implementation Specification

> [!summary] 本页定位
> 本页只处理 `StepTransition` 的规范性实现抽象、Event IR、LH 映射、phase/read/write/commit 约束、kernel 替换路线与工程检查项。数学定义与证明见 [[step-transition-mathematical-specification]]；`~/llm/tide` 当前完成度见 [[current-architecture-state]]。

本页不是代码状态日志。这里的 `Graph / State / Workspace / Schedule / Kernel` 是稳定接口词汇；某个接口是否已经由当前 CPU、packed 或 Ascend backend 实现，应以 [[current-architecture-state]] 为准。

## 为什么需要实现规范

LH 带来了许多实现概念：

- `iacts / oacts`
- `ichs / ochs`
- `iselector / oselector`
- `internal tick`
- bridge phase
- readout cache
- pronounce memory
- selector count
- hidden / KV cache

这些对象对复刻 LH 很重要，但如果直接用它们做 `prefill / decode` 等价性证明，人类理解成本会很高，也容易被具体实现细节绑住。

实现规范的作用是把 LH 这类复杂系统压成几个稳定接口：

```text
StepTransition(Graph, Schedule, State, input_token)
  -> output_logits, State'
```

数学层只证明这些接口的语义。实现层负责说明如何把 LH、Tide kernel、packed/crossbatch 和 backend lowering 放入这些接口。

## 五个工程对象

### 1. Graph

`Graph` 描述系统中有哪些节点、边、角色和 anchor。

它不应只是普通无类型图，而应是 role-aware graph：

- node 有 role。
- edge 有 role。
- 有 input anchor。
- 有 readout anchor。
- 可以有 input-side / output-side / bridge 等结构性标签。

### 2. State

`State` 是跨 external token 持久存在的运行时状态。

它可包含：

- node activation。
- node memory。
- selector / controller state。
- pronounce memory。
- local hidden / KV cache。

关键点是：`State` 是持久的。token `t+1` 只能读取 token `t` 完整 commit 后的 `State`。

### 3. Workspace

`Workspace` 是当前 token 内的临时状态。

它可包含：

- 当前 internal tick 的 staged messages / extra inputs。
- 当前 token 的 readout cache。
- phase artifact。
- debug / golden-test artifact。

关键点是：`Workspace` 不等于持久 `State`。它的生命周期由 step 和 phase 规则决定。

### 4. Schedule

`Schedule` 是一个 token 内按顺序执行的 phase 列表。

每个 phase 必须声明：

- 读什么。
- 写什么。
- 是否修改持久 state。
- 什么时候 commit。
- 哪些结果只在 workspace 中可见。

phase 的核心不是 enum 名称，而是：

```text
barrier + visibility + commit order
```

固定 schedule 是最简单实例。未来 dynamic runtime 可以在线选择 phase-local events，但生成策略仍必须服从同一个 visibility、commit 与 logical-rank contract。

### 5. Kernel

`Kernel` 是局部计算函数。

它只负责当前 phase 的局部 transition，例如：

- edge emit。
- message gather。
- node update。
- selector。
- readout。
- pronounce。

kernel 不应偷偷改变 phase 顺序、可见性或 commit timing。

## StepTransition 伪代码

一个 external token step 可写成：

```text
Step(input_token, State):
  Workspace = init_workspace(input_token, State)

  for internal_round in rounds:
    for phase in Schedule:
      view = read(State, Workspace, phase.read_scope)
      delta = Kernel_phase(view, phase.params)
      commit(State, Workspace, delta, phase.write_scope)

  logits, State = finalize(State, Workspace)
  return logits, State
```

实现时必须保证：

- `read` 不隐式扩大可见范围。
- `Kernel_phase` 不直接写全局状态。
- `commit` 是唯一改变持久 state 的入口。
- `Workspace` 的生命周期默认不跨 token。

上面的伪代码描述 fixed-round reference family。若 round 数或 active events 由 selector 动态决定，还必须给出终止条件、event budget 或良基 rank，不能把无限循环隐藏在 `rounds` 中。

## Dynamic Event Contract

dynamic Tide 不要求从 input 到 output 的路径在运行前固定。规范对象应从“静态路径”提升为“运行时产生的有限 logical events”。

建议最小 Event IR 为：

```text
EventId {
  external_token
  internal_round
  phase
  microstep
  node_or_edge
  role
}

Event {
  id
  read_set
  write_set
  predecessors
  state_version
  visibility_scope
  commit_target
  kernel_kind
}
```

### Logical rank

定义：

```text
LogicalRank = (external_token, internal_round, phase_ordinal, microstep)
```

rank 使用良基字典序。runtime 每次创建 dependency 时都必须满足：

```text
rank(predecessor) < rank(successor)
```

selector 可以在线决定是否创建 event、激活哪些 node / edge，或选择哪些 predecessor；但它不能在 strict core 中创建同 rank 的未声明 cycle。

### Dependency completeness

Event IR 至少需要显式表达：

- consumed value 的 producer。
- state read 对应的 version。
- write/write 与 read/write conflict order。
- phase visibility 与 barrier。
- selector decision 对 future routing 的影响。
- output 与 persistent-state commit event。

若 implementation 删除一条 dependency，必须提供 independence、commutativity、non-aliasing 或 semantics-preserving quotient 证明。

### Finite execution

有限 token 输入不自动保证有限执行。dynamic runtime 还必须满足至少一种：

- internal round 有静态上界。
- event budget 有运行时上界。
- event generation 有终止性证明。
- rank 除单调增加外还被有限 chunk domain 有界。

### Zero-delay SCC policy

对同一 logical rank 的 dependency subgraph 做 SCC 检查：

1. singleton 且无 self-loop：普通 event。
2. cycle 跨越显式 token / round / state-version / delay boundary：在 dynamic unfolding 中属于不同 rank。
3. 同 rank zero-delay SCC：strict core 拒绝。

若未来确实需要 equilibrium / implicit computation，应把整个 SCC 显式声明为 `FixedPointKernel` 或 `RootSolveKernel`，并单独规定 fixed-point selection、termination、cost 与 differentiation contract。它不能作为普通 graph cycle 自动获得语义。

### Kernel metadata lowering

logical time 是语义要求，但底层 kernel 不一定接收原始整数 tuple。合法 lowering 包括：

- causal mask。
- segment offset。
- packed row index。
- CSR / block-sparse layout。
- batch descriptor。
- 已验证的固定 schedule。

这些表示必须保留 kernel 所需的 logical partition、visibility 和 commit provenance。data pack 是物理布局优化，不是删除时间语义。

## LH 如何纳入

LH 的实现概念可以映射到这个规范模型，而不需要直接成为证明语言。

| LH 内容 | 实现规范中的位置 |
| --- | --- |
| `iacts / oacts` | `State.activation[node_id, namespace]`，node 带 input/output role。 |
| `ichs / ochs` | `State.memory[node_id, namespace]`。 |
| `iselector / oselector` | `State.controller[selector_scope]`。 |
| `input_extra / output_extra` | `Workspace.mailbox[node_id, namespace]`。 |
| `internal tick` | `internal_round`。 |
| `OiBridge / IoBridge` | edge-message phase，读一组 role nodes，写另一组 mailbox。 |
| `ExternalInput` | input injection phase，只在指定 round 写 input anchor mailbox。 |
| `InputUpdate / OutputUpdate` | node-update phase，读 activation + mailbox + memory + selector，写 activation / memory / selector。 |
| `ReadoutCache` | 当前 token 的 workspace accumulator。 |
| `Pronounce` | final readout kernel，读 workspace output cache，改 pronounce memory，输出 logits。 |

因此，LH 可被理解为一个较复杂的 `StepTransition` 实例，而不是 `StepTransition` 本身。

## LH-like phase schedule

当前 LH-like external token step 可拆成：

```text
for tick in internal_ticks:
  oibridge
  external_input  # only selected tick, usually tick 0
  iobridge
  input_cortex_update
  output_cortex_update
  readout_cache
pronounce
```

更明确的 read/write/commit 约束是：

```text
phase oibridge:
  read:
    - state.oacts@tick_start
  write:
    - workspace.input_extra@staged
  commit:
    - visible_to.input_cortex_update

phase external_input:
  condition:
    - only selected internal tick of the external token step
  read:
    - token embedding
  write:
    - workspace.input_extra[input_anchor]@staged
  commit:
    - visible_to.input_cortex_update

phase iobridge:
  read:
    - state.iacts@tick_start
  write:
    - workspace.output_extra@staged
  commit:
    - visible_to.output_cortex_update

phase input_cortex_update:
  read:
    - state.iacts@tick_start
    - workspace.input_extra@committed
    - state.ichs
    - state.iselector
  write:
    - state.iacts@next
    - state.ichs@updated
    - state.iselector@updated
  side_effects:
    - hidden decay / update
    - selector affectcount / selectcount update
    - optional hidden clear after selected activation
  commit:
    - end_of_phase

phase output_cortex_update:
  read:
    - state.oacts@tick_start
    - workspace.output_extra@committed
    - state.ochs
    - state.oselector
  write:
    - state.oacts@next
    - state.ochs@updated
    - state.oselector@updated
  side_effects:
    - hidden decay / update
    - selector affectcount / selectcount update
    - optional hidden clear after selected activation
  commit:
    - end_of_phase

phase readout_cache:
  read:
    - state.oacts@next[readout_anchor]
  write:
    - workspace.output_cache.append
  commit:
    - token-local only

phase pronounce:
  read:
    - workspace.output_cache
    - state.pronounce_memory
  write:
    - logits
    - state.pronounce_memory@updated
```

这里最容易出错的点是：`iobridge` 在当前 LH 语义中读取 tick start 时的旧 `iacts`，不是 `input_cortex_update` 后的新 `iacts`。如果统一 graph runtime 没有这个 read view 约束，就会改变 LH 语义。

## 两条实现路线

这两条路线不是同等地位的最终竞争架构：

- LH compatibility 路线负责提取复杂机制、提供 golden oracle、暴露 state/phase/selector 问题。
- strict prefill 路线负责建立最小、可理解、可证明、可高性能实现的数学与 runtime 主线。

总体目标是“局部通信 + 超稀疏”，不是逐行复刻 LH。若某个 LH 机制无法满足或严重阻碍 model-level prefill、序列并行与 non-degenerate chunk certificate，可以简化、替换或留在 non-strict compatibility family。

### 路线 A：LH 机制提取与 compatibility

目标：

```text
Typed Graph
+ StateStore
+ Workspace
+ PhaseSchedule
+ KernelRegistry
```

这条路线保留 LH 的 phase、selector、readout、pronounce 和 memory 语义。

优势：

- 可复刻 LH。
- 可对齐 native LH。
- 可用现有工程作为 golden reference。

代价：

- 抽象较复杂。
- 需要显式 state scope、selector scope、workspace lifetime。
- 证明不能只靠普通 graph，需要依赖 phase schedule 与 state contract。

### 路线 B：strict prefill core

目标：

```text
for round:
  messages = EdgeKernel(Graph, State)
  State.nodes = NodeUpdate(messages, State.nodes)
logits = Readout(State)
```

这条路线选择更简单的通用 graph recurrent runtime，并承担当前数学与 model-level prefill 主线。

优势：

- 更容易解释。
- 更容易定义严格的顺序 fold 语义。
- 更可能成为后续可训练性实验的最小核心。

代价：

- 不一定能完整复刻 LH。
- 可能丢掉 LH 中某些为局部通信、超稀疏、selector 历史设计的机制。
- 需要重新验证其表达力、训练稳定性与性能价值。

## B0-B6 工程推进梯度

`EventId / LogicalRank / Dependency / StateVersion / CommitEvent` 是贯穿 B0-B6 的 cross-cutting execution contract，不是额外的 B7 机制。static executor 可以预先生成 events；dynamic executor 在线生成同一种 Event IR。

当前 B0 已经吸收旧版 B1 的 factorized node state：visible activation 与 private memory/cache/state 从基线开始就同时存在。因此 Transformer KV cache、Mamba/SSM recurrent state、Linear Attention accumulator 都属于 B0 的正常表达能力，不应被当作后续层级的新增机制。

B0 的工程门槛也要随之提高：不能只实现一个能容纳这些模型的 graph runtime，还要先给主力 kernel family 建立 chunk prefill proof gate。最低限度包括：

第一层是一般 correctness gate：把 decode fold 展开成 logical event DAG，确认 chunk implementation 计算的是同一个 DAG、同一组 kernel equation、同一个 output/final-state extraction。这个 gate 只证明 `C_L = Fold_T^L`，不自动给出高性能。

对 LH-like graph runtime，event id 至少应能表达：

```text
(external_token, internal_round, phase, node_or_edge)
```

物理执行可以乱序，late-token signal 也可以先到达某个 node；但 message 必须带 token / round / phase 等 logical metadata，node kernel 必须按 logical timestamp 做分桶、排序、mask 或 buffer。若 node 内把不同 token / round 的信号做不可逆、无时间戳聚合，token influence relation 会被折叠，通常无法证明 chunk prefill correctness。

第二层才是 kernel family 的高性能见证：

| Kernel family | Reference transition | Chunk implementation | 高性能见证 |
| --- | --- | --- | --- |
| FFN / norm / residual | token-wise update | batched map over sequence | vectorized / fused elementwise kernel |
| Causal attention | append KV cache, read causal prefix | batched QKV + causal mask / prefix read | matmul / FlashAttention-style fused attention |
| Linear attention | prefix accumulator update | prefix sum / associative scan | scan / fused scan |
| Mamba / SSM | affine recurrent state update | parallel prefix / chunk scan | scan / chunk scan kernel |

只有这些 B0 kernel family 的 `C_L = Fold_T^L` 先成立，后续 B1-B6 的推进才是在可靠基线之上检查新增机制是否保持或破坏等价性。

数学文档中已把 correctness 与 performance proof gate 收束为以下结果和证书：

- `Unified Contract-DAG-Quotient Theorem`：统一 reference contract abstraction、logical event DAG 与 event-level quotient。
- `B0 Logical Event DAG Theorem`：若 chunk implementation 保持同一个 logical event DAG，则 correctness 成立。
- `Aggregation Quotient Theorem`：若聚合丢失 provenance，则必须证明该聚合是所有后续 kernel 与 final-state extraction 的 semantics-preserving quotient。
- `Non-Degenerate Chunk Certificate`：排除单节点 oracle，要求 uniform primitives、explicit lowering 与完整 cost ledger。
- `B0-Transformer Theorem`：由 token-wise kernels、causal attention、有限 layer-wise chain 组合得到 Transformer chunk prefill correctness。
- `B0-Mamba / SSM Theorem`：由 token-wise kernels、causal convolution 的 shift-register recurrence、selective SSM 的 affine scan recurrence、有限 layer-wise chain 组合得到 Mamba / SSM chunk prefill correctness。

| 层级 | 新增机制 | 实现重点 | prefill 风险 |
| --- | --- | --- | --- |
| B0 | standard factorized graph runtime | visible activation + private memory/cache/state；覆盖 Transformer KV cache、Mamba/SSM state、linear-attention accumulator；chain graph + rounds 表达标准 block stack | 只定义顺序 fold，不自动得到 chunk prefill；cache append / recurrent update 仍需 chunk 等价证明。 |
| B1 | typed edge / mailbox | edge role + token-local mailbox | mailbox 必须 step-local / round-local。 |
| B2 | runtime phase schedule | input/output/bridge/readout 等大范围阶段的 read/write/commit contract | 不可跨 phase 改 role / direction / barrier / visibility。 |
| B3 | selector / controller state | selector 作为控制面状态 | selector 不能基于未来 token 联合决策。 |
| B4 | readout cache | token-local cache lifecycle | readout cache 不能跨 token 泄漏。 |
| B5 | pronounce memory | final readout recurrence | 可能需要 scan / checkpoint / sequential update。 |
| B6 | LH-like input/output roles and bridges | role-aware graph + state namespace | 必须保留 role、scope、phase read-write contract。 |

## Kernel 替换规则

优化 kernel、packed kernel、crossbatch kernel 或 backend lowering 时，必须逐 phase 保持：

- read scope。
- write target。
- commit timing。
- workspace lifetime。
- persistent state equivalence。
- output equivalence。

建议替换顺序：

1. bridge kernel。
2. message gather / mailbox layout。
3. node candidate activation。
4. selector。
5. local hidden / KV cache update。
6. readout cache。
7. pronounce。
8. packed / crossbatch fusion。
9. backend lowering。

每替换一层，都应做 phase artifact 对齐，而不是只看最终 logits。

## Golden Test 要求

最低限度应有三类测试：

```text
same initial state
same input tokens
same parameters
```

比较：

- final logits。
- final persistent state。
- phase event order。
- per-phase read artifact。
- per-phase delta artifact。
- per-phase committed state。
- workspace lifecycle。

如果浮点执行顺序不同，logits 可用预声明容差；但 state artifact 的语义等价必须明确。

## 当前建议

短期应保持四层协同：

1. 用数学规范定义 transition、fold、chunk correctness 与 simulation。
2. 用 Event IR 与实现规范约束 logical rank、dependency、graph/state/workspace/phase/kernel 边界。
3. 工程上保留 native LH golden path，并用独立 Tide CPU path 做 translation-validation-style 对齐。
4. 用更简单的 strict B-family 建立 model-level prefill，再把结果逐层推广到 LH-like mechanisms。

四层都由 `prefill / decode` 等价性反过来裁决 graph、state、schedule 与 kernel 设计。

第一批最小可检查对象：

```text
StepTransition Math Spec
Event IR / LogicalRank Spec
StateStore Spec
Workspace Lifetime Spec
Phase Read/Write Scope Spec
Kernel Equivalence Spec
Prefill = Decode Fold Test
Chunk Prefill Correctness Test
```

只有这些对象被明确下来，后续讨论“是否支持 prefill”、“是否可 sequence-parallel”、“是否可 packed / crossbatch fusion”才不会被 LH 的具体实现细节淹没。
