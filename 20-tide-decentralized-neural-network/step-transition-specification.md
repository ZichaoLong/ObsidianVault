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
