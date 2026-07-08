---
type: note
status: active
tags:
  - tide
  - prefill-decode
  - step-transition
---

# StepTransition 规范模型

> [!summary] 本页定位
> 本页尝试把 `prefill / decode` 等价性讨论从 LH 的实现细节中抽出来，先定义一个人类可理解的规范模型。它既可作为承载 LH 的上层语义，也可作为后续更简单、更通用大 graph 执行模型的起点。

## 为什么需要这个抽象

当前讨论中，LH 带来了许多实现概念：

- `iacts / oacts`
- `ichs / ochs`
- `iselector / oselector`
- `internal tick`
- bridge phase
- readout cache
- pronounce memory
- selector count
- hidden / KV cache

这些概念对复刻 LH 很重要，但如果直接以它们作为 `prefill / decode` 等价性的证明对象，人类理解成本会很高，也容易被具体实现细节绑住。

因此，需要先定义一个更高层的规范模型：

```text
StepTransition(Graph, Schedule, State, input_token)
  -> output_logits, State'
```

证明与设计应优先落在这个规范模型上，再把 LH 映射进来。

## 人类可理解的五个概念

### 1. Graph

`Graph` 描述系统中有哪些节点、边、角色和 anchor。

它不只是普通无类型图，而是 typed graph：

- node 有 role。
- edge 有 role。
- 有 input anchor。
- 有 readout anchor。
- 可以有 input-side / output-side / bridge 等结构性标签。

### 2. State

`State` 是跨 external token 持久存在的运行时状态。

它至少可包含：

- node activation。
- node memory。
- selector / controller state。
- pronounce / readout memory。

关键点是：`State` 是持久的。token `t+1` 只能读取 token `t` 完整 commit 后的 `State`。

### 3. Workspace

`Workspace` 是当前 token 内的临时状态。

它可包含：

- 当前 internal tick 的 staged messages / extra inputs。
- 当前 token 的 readout cache。

关键点是：`Workspace` 不等于持久 `State`。它的生命周期由 step 和 phase 规则决定。

### 4. Schedule

`Schedule` 是一个 token 内按顺序执行的 phase 列表。

每个 phase 必须声明：

- 读什么。
- 写什么。
- 是否修改持久 state。
- 什么时候 commit。
- 哪些结果只在 workspace 中可见。

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

## StepTransition

一个 external token step 可写成：

```text
Step(input_token, State):
  Workspace = empty

  for internal_round in rounds:
    for phase in Schedule:
      view = read(State, Workspace, phase.read_scope)
      delta = Kernel_phase(view, phase.params)
      commit(State, Workspace, delta, phase.write_scope)

  logits, State = ReadoutOrPronounce(State, Workspace)
  return logits, State
```

这就是后续 `prefill / decode` 等价性的核心对象。

人类只需理解：

- 持久 `State`。
- 当前 token 临时 `Workspace`。
- 有序 phase 读写规则。
- 局部 `Kernel`。

## LH 如何纳入

LH 的实现概念可以映射到这个规范模型，而不需要直接成为证明语言。

| LH 内容 | 规范模型中的位置 |
| --- | --- |
| `iacts / oacts` | `State.activation[node_id]`，node 带 input/output role。 |
| `ichs / ochs` | `State.memory[node_id]`。 |
| `iselector / oselector` | `State.controller[selector_scope]`。 |
| `input_extra / output_extra` | `Workspace.mailbox[node_id]`。 |
| `internal tick` | `internal_round`。 |
| `OiBridge / IoBridge` | edge-message phase，读一组 role nodes，写另一组 mailbox。 |
| `ExternalInput` | input injection phase，只在 round 0 写 input anchor mailbox。 |
| `InputUpdate / OutputUpdate` | node-update phase，读 activation + mailbox，写 activation / memory / selector。 |
| `ReadoutCache` | 当前 token 的 workspace accumulator。 |
| `Pronounce` | final readout kernel，读 workspace output cache，改 pronounce memory，输出 logits。 |

因此，LH 可被理解为一个较复杂的 `StepTransition` 实例，而不是 `StepTransition` 本身。

## Prefill / Decode 等价性

在规范模型中，decode 是一步 transition：

```text
Decode(x_t, S_t) = StepTransition(x_t, S_t)
```

prefill 的最基本定义是 decode fold：

```text
Prefill(x_0:T, S_0):
  S = S_0
  for t in 0..T-1:
    y_t, S = Decode(x_t, S)
  return y_0:T, S
```

如果 `prefill` 第一版就是这个 fold，那么模型级等价性由定义成立。

后续优化的证明目标是：

```text
OptimizedKernel(view, state_slice)
==
ReferenceKernel(view, state_slice)
```

同时保持：

- phase 顺序不变。
- read scope 不变。
- write scope 不变。
- commit timing 不变。
- workspace 生命周期不变。
- external token 顺序不变。

如果每个 kernel 替换都满足上述条件，则整个 `StepTransition` 不变；如果每个 step 的 `StepTransition` 不变，则 `prefill` 与 decode fold 等价。

## 为什么完整涵盖 LH 可能很难

完整涵盖 LH 并自动得到严格 `prefill / decode` 等价性，大概率需要对 `Graph` 与 `Schedule` 施加强约束。

原因是 LH 具有许多会影响等价性的状态机制：

- selector 的历史依赖。
- hidden / KV cache 的 append 顺序。
- internal tick 内的 read / write 可见性。
- readout cache 只在当前 token 内跨 internal tick 累积。
- pronounce memory 跨 token 持久存在。
- external input 只在 tick 0 可见。

如果这些机制没有被显式约束，`prefill` 很容易在实现中无意改变语义，例如：

- token `t` 读到 token `t+1` 的 state。
- chunk 内 selector 基于未来 token 做联合决策。
- KV cache 一次性 append 整段 chunk，导致早期 token 看到未来 token。
- readout cache 或 workspace 生命周期被拉长到跨 token。

因此，`StepTransition` 抽象不是为了证明任意 graph 都天然等价，而是为了找出哪些约束会保持或破坏等价性。

## 两条研究分支

### 分支 A：涵盖 LH

目标：

```text
Typed Graph + StateStore + Workspace + PhaseSchedule + KernelRegistry
```

这条路线保留 LH 的 phase、selector、readout、pronounce 和 memory 语义。

优势：

- 可复刻 LH。
- 可对齐 native LH。
- 可用现有工程作为 golden reference。

代价：

- 抽象较复杂。
- 需要显式 state scope、selector scope、workspace lifetime。
- 证明不可能只靠普通 graph，需要依赖 phase schedule 与 state contract。

### 分支 B：不强行涵盖 LH

目标：

```text
for round:
  messages = EdgeKernel(Graph, State)
  State.nodes = NodeUpdate(messages, State.nodes)
logits = Readout(State)
```

这条路线选择更简单的通用 graph recurrent runtime。

优势：

- 更容易解释。
- 更容易定义严格 `prefill = decode fold`。
- 更可能成为后续可训练性实验的最小核心。

代价：

- 不一定能完整复刻 LH。
- 可能丢掉 LH 中某些为局部通信、超稀疏、selector 历史设计的机制。
- 需要重新验证其表达力、训练稳定性与性能价值。

## 从分支 B 逐层逼近 LH

后续推进可以从分支 B 出发，逐步引入 LH 中的要素。这样做的目的不是预设 LH 一定正确，而是让每个新增机制都被单独审视：它到底新增了什么状态、什么临时工作区、什么调度约束，以及它对 `prefill = decode fold` 和高性能并行 prefill 有何影响。

### B0：activation-only graph recurrent step

最小模型：

```text
State:
  activation[node]

Workspace:
  messages

Step(input_token, State):
  State.activation[input_node] = Embed(input_token)

  for round in 0..R-1:
    Workspace.messages = EdgeKernel(Graph, State.activation)
    next_activation = NodeKernel(Graph, State.activation, Workspace.messages)
    State.activation = next_activation

  logits = Readout(State.activation[output_node])
  return logits, State
```

如果 `Prefill` 定义为逐 token 调用 `Step`，则 `prefill = decode fold` 由定义成立。

这一层的价值是给出最干净的正确性基准，但它尚未提供真正 sequence-parallel prefill；高性能 prefill 仍需证明 `forward_chunk == Step fold`。

### B1：加入 node memory

新增：

```text
State:
  activation[node]
  memory[node]
```

`NodeKernel` 变成：

```text
NodeKernel(messages, activation, memory_before)
  -> activation_delta, memory_after
```

只要 memory 按 token 顺序更新，`prefill = decode fold` 仍然直接成立。

风险是高性能 chunk prefill：如果一次性处理多个 token，必须保证 token `t` 的 node update 不能读到 token `t+1` 写入的 memory。

### B2：加入 typed edge 与 mailbox

新增：

```text
Graph:
  typed edge roles

Workspace:
  mailbox[node]
```

edge kernel 从“直接生成 messages”变成：

```text
EdgeKernel(source_activation, edge_role)
  -> mailbox[target_node]
```

这一层仍然容易保持 `prefill = decode fold`，前提是 mailbox 是当前 step / 当前 round 的临时对象，不能跨 token 持久存在。

### B3：加入 internal rounds 和 phase schedule

新增：

```text
Schedule:
  ordered phases
  read_scope
  write_scope
  commit timing
```

这是从普通 graph recurrent step 走向 LH-like runtime 的关键一步。

`Step` 不再只是：

```text
messages -> node_update
```

而是：

```text
for internal_round:
  for phase in Schedule:
    view = read(State, Workspace, phase.read_scope)
    delta = Kernel(view)
    commit(delta, phase.write_scope)
```

只要 phase schedule 在 prefill 和 decode 中完全一致，`prefill = decode fold` 仍可由 step 等价推出。

高性能并行 prefill 的风险在于跨 phase 或跨 token 重排。允许的优化应主要发生在同一 phase 内，而不是改变 phase barrier。

### B4：加入 selector / controller state

新增：

```text
State:
  controller[scope]
```

selector 不应被藏进普通 node kernel 的内部细节，因为它有历史依赖，并会影响后续 active path。

等价性要求：

```text
SelectorKernel(candidates, controller_before)
  -> selected, controller_after
```

prefill 与 decode 的 selector 更新顺序必须一致。chunk prefill 如果想并行处理多个 token，不能让早期 token 的 selector 决策依赖未来 token 的 candidates 或 controller state。

### B5：加入 readout cache

新增：

```text
Workspace:
  readout_cache
```

readout cache 是当前 token 内跨 internal rounds 累积的临时对象。

这一点非常关键：

- 它不是跨 token 的持久 `State`。
- 它也不是每个 phase 都可见的普通 message。
- 它在 token step 结束后被 pronounce 使用，然后应结束生命周期。

如果 readout cache 被错误地跨 token 保留，`prefill = decode fold` 会被破坏。

### B6：加入 pronounce memory

新增：

```text
State:
  pronounce_memory
```

pronounce kernel 变成：

```text
Pronounce(readout_cache, pronounce_memory_before)
  -> logits, pronounce_memory_after
```

它是跨 token 持久状态，因此必须按 token 顺序更新。

这会让高性能 prefill 更难，因为即使 node graph 的一部分可并行，最终 pronounce memory 仍然是 step recurrence 的一部分，除非额外证明它可以 associative scan 或其他等价并行化。

### B7：加入 LH-like input/output roles and bridges

新增：

```text
Graph:
  input-role nodes
  output-role nodes
  io bridge edges
  oi bridge edges

State:
  activation[node_id]
  memory[node_id]
  controller[selector_scope]
```

这一步可以用统一大 graph 表达 input/output 两套 cortex，但仍需要 role、scope 和 phase schedule。

它不能把 LH 简化成普通无类型 graph traversal，因为：

- `ExternalInput` 只写 input anchor。
- `OiBridge` 与 `IoBridge` 有方向和可见性规则。
- `InputUpdate` 与 `OutputUpdate` 写不同 role 的 node state。
- `Readout` 只读 output readout anchor。
- selector scope 仍然需要区分。

到这一层，已经接近 LH 的 StepTransition 形态。

## 每一层必须回答的问题

逐层推进时，每一层都应回答同一组问题：

1. `State` 新增了什么？
2. `Workspace` 新增了什么？
3. `Schedule` 新增了什么？
4. `Kernel` 的输入输出变成什么？
5. `prefill = decode fold` 是否仍然由 step 定义成立？
6. 如果做高性能并行 prefill，能否实现 `forward_chunk == Step fold`？
7. 为了实现高性能并行 prefill，需要什么 mask、ordering、state materialization、checkpoint 或 scan 结构？
8. 哪些优化只能在同一 phase 内做，哪些优化会跨 phase 或跨 token 改变语义？
9. 新增机制是否是局部通信目标下的必要机制，还是 LH 的实现选择？

这组问题本身就是后续文档推进模板。

## 逐层判断

| 层级 | 新增机制 | `prefill = decode fold` | 高性能并行 prefill 风险 |
| --- | --- | --- | --- |
| B0 | activation-only graph step | 由定义成立 | 需要证明 chunk 等价于逐 step。 |
| B1 | node memory | 仍成立 | 不能让 token `t` 读未来 memory。 |
| B2 | typed edge / mailbox | 仍成立 | mailbox 必须 step-local / round-local。 |
| B3 | internal rounds / phase schedule | 仍成立 | 不可跨 phase 改 barrier / visibility。 |
| B4 | selector / controller state | 仍成立但更脆弱 | selector 不能基于未来 token 联合决策。 |
| B5 | readout cache | 仍成立 | readout cache 必须 token-local。 |
| B6 | pronounce memory | 仍成立但有 recurrence | 可能需要 scan / checkpoint / sequential update。 |
| B7 | LH-like input/output roles and bridges | 可成立 | 必须保留 role、scope、phase read-write contract。 |

当前判断：最小分支 B 满足 `prefill = decode fold`，但不自动支持高性能并行 prefill。它的价值是提供一个干净、可理解的正确性基准。真正的研究价值在于逐层引入 LH 机制时，找出哪些机制仍容易保持等价，哪些机制让高性能 prefill 变难。

## 当前建议

建议先走中间路线：

1. 用 `StepTransition` 作为规范层。
2. 让规范层先能解释 LH，但不把 LH 细节变成唯一正确答案。
3. 在工程上继续保留 LH 对齐路径，作为复杂 reference family。
4. 在理论和实验上另行探索更简单的 strict family。
5. 以 `prefill / decode` 等价性为裁决标准，反过来约束 graph、state、schedule、kernel 的设计。

第一步可以不是完整证明，而是建立最小可检查对象：

```text
StepTransition Spec
StateStore Spec
Workspace Lifetime Spec
Phase Read/Write Scope Spec
Kernel Equivalence Spec
Prefill = Decode Fold Test
```

只有这些对象被明确下来，后续讨论“是否支持 prefill”、“是否可 sequence-parallel”、“是否可 packed / crossbatch fusion”才不会被 LH 的具体实现细节淹没。

## 开放问题

- 哪些 graph 约束足以保证 `prefill = decode fold`？
- selector 是否必须被视为 controller state，而不是 node kernel 内部细节？
- workspace 是否必须严格 token-local？
- internal tick 是否是必要概念，还是 LH-specific 复杂度？
- readout cache 与 pronounce memory 是否应进入通用模型？
- `forward_chunk` 能否在不破坏 step semantics 的情况下提供真正 sequence-parallel prefill？
- 哪些 LH 机制是局部通信目标下必要的，哪些只是当前实现选择？
