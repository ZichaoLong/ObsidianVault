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
> 本页只处理 `StepTransition` 的实现抽象、LH 映射、phase/read/write/commit 约束、kernel 替换路线与工程检查项。数学定义与证明见 [[step-transition-mathematical-specification]]。

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

### 路线 A：涵盖 LH

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

### 路线 B：不强行涵盖 LH

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
- 更容易定义严格的顺序 fold 语义。
- 更可能成为后续可训练性实验的最小核心。

代价：

- 不一定能完整复刻 LH。
- 可能丢掉 LH 中某些为局部通信、超稀疏、selector 历史设计的机制。
- 需要重新验证其表达力、训练稳定性与性能价值。

## B0-B7 工程推进梯度

| 层级 | 新增机制 | 实现重点 | prefill 风险 |
| --- | --- | --- | --- |
| B0 | activation-only graph step | edge emit + node update + readout | 只定义顺序 fold，不自动得到 chunk prefill。 |
| B1 | node memory | memory read/write namespace | token `t` 不能读未来 memory。 |
| B2 | typed edge / mailbox | edge role + token-local mailbox | mailbox 必须 step-local / round-local。 |
| B3 | internal rounds / phase schedule | read/write/commit contract | 不可跨 phase 改 barrier / visibility。 |
| B4 | selector / controller state | selector 作为控制面状态 | selector 不能基于未来 token 联合决策。 |
| B5 | readout cache | token-local cache lifecycle | readout cache 不能跨 token 泄漏。 |
| B6 | pronounce memory | final readout recurrence | 可能需要 scan / checkpoint / sequential update。 |
| B7 | LH-like input/output roles and bridges | role-aware graph + state namespace | 必须保留 role、scope、phase read-write contract。 |

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

短期应保持两条线并行：

1. 用数学规范定义 transition、fold、chunk correctness 与 simulation。
2. 用实现规范约束 LH-like runtime 的 graph/state/workspace/phase/kernel 边界。
3. 工程上继续保留 native LH 对齐路径，作为复杂 reference family。
4. 理论和实验上另行探索更简单的 strict B-family。
5. 用 `prefill / decode` 等价性反过来裁决 graph、state、schedule、kernel 的设计。

第一批最小可检查对象：

```text
StepTransition Math Spec
StateStore Spec
Workspace Lifetime Spec
Phase Read/Write Scope Spec
Kernel Equivalence Spec
Prefill = Decode Fold Test
Chunk Prefill Correctness Test
```

只有这些对象被明确下来，后续讨论“是否支持 prefill”、“是否可 sequence-parallel”、“是否可 packed / crossbatch fusion”才不会被 LH 的具体实现细节淹没。

