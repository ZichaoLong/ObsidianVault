---
type: plan
status: draft
tags:
  - recursive-decomposition
  - memory
  - lean
  - verified-lemma-memory
  - theorem-proving
---

# Lean Verified Lemma Memory 计划

这份计划把 `verified subproblem memory` 收缩到一个更硬的问题：

> 给定一批已形式化任务，系统能否从解决过程里提取出可复用的 verified lemma / subproblem，并在 heldout 任务中通过检索、实例化、组合这些 lemma，降低证明搜索成本或提高证明成功率？

如果以 Lean 为基础设施，verification 已经由 proof checker 解决；retrieval 也已有 LeanSearch / LeanDojo / ReProver / Lean Copilot / Pantograph 等强对手。因此贡献不能写成“可验证”或“能检索 theorem”，而应落在：

> 自动形成、证明、抽象、索引、复用新的中间引理。

## 研究对象

`verified subproblem memory` 的目标不是存更多上下文，而是把已验证的局部推理结果变成后续任务可复用、可组合、可检索、可更新的中间对象。

一个 memory item 至少应包含：

```text
subproblem:
  statement
  proof
  assumptions
  dependencies
  verifier
  validity_scope
  source_tasks
  reuse_history
```

在 Lean 语境下，最自然的实例是：

- verified lemma。
- proof-state -> useful lemma / tactic。
- proof fragment。
- lemma dependency subgraph。
- generalized lemma 从多个具体实例抽象而来。

## 与普通 Retrieval 的区别

| 机制 | 存在对象 | 关键问题 |
| --- | --- | --- |
| theorem retrieval / LeanSearch | mathlib 已有 theorem | 能否找到已有定理 |
| raw trace memory | 过去 proof trace | 能否提示当前证明 |
| verified lemma memory | 新生成并已证明的 lemma / proof fragment | 能否抽象、复用、组合 |
| recursive subproblem graph | lemma 之间形成依赖图 | 能否局部展开、局部修复、跨任务积累 |

最危险的退化：

> 只是把 LeanSearch / RAG 接上，然后说 memory 有用。

这当然可能有工程价值，但会被已有 theorem retrieval / premise selection 吸收。Lean 方向真正要检验的是：系统能否增长一批新 memory，并让这些 memory 在 heldout task 上产生增量。

## 候选方向

### 方向 A：Verified Lemma Discovery

问题：

> 系统能否从多个 solved tasks 或 failed proof attempts 中，自动提出一个更一般的 lemma，并用 Lean 证明它？

价值最高，因为它不是检索已有 theorem，而是在增长 memory。

最小裁决：

- 生成的 lemma 必须通过 Lean。
- lemma 不能只是原题重命名。
- lemma 必须在 heldout tasks 中被复用。
- 复用后要降低 proof search cost 或提高 proof success。

### 方向 B：Proof-State Memory / Case-Based Proving

问题：

> 给定当前 proof state，检索过去相似 proof state 及其 closing tactic / local proof fragment，是否比普通 theorem retrieval 更有用？

这是更稳的 sanity check 方向。

它回答：

- memory 是否比 raw theorem retrieval 多带来信息。
- 过去证明状态是否有可迁移结构。
- harmful retrieval 是否可控。

### 方向 C：Lemma Usefulness Prediction

问题：

> 给定 proof state 和 candidate lemma，能否预测这个 lemma 是否真的有用？

这适合小规模训练。训练对象不是“会数学的大模型”，而是 reranker / usefulness classifier。

输入：

```text
proof_state
candidate_lemma
local_context
```

输出：

```text
useful / not useful
expected tactic
expected cost reduction
```

### 方向 D：Continual Verified Memory

问题：

> 任务按时间流进入，系统解决一批任务后把 verified subproblem 写入 memory，后续 heldout tasks 是否越来越容易？

关键指标不是单点准确率，而是 marginal improvement curve：

- memory 增长后 proof success 是否上升。
- proof search cost 是否下降。
- harmful retrieval 是否随 memory 增大而失控。

### 方向 E：Recursive Subproblem DAG

问题：

> 不只存单个 lemma，而是存一组有依赖关系的 verified nodes；失败时只展开某个节点，成功节点缓存复用。

这最接近“递归分解”，但工程复杂，不应作为第一击。

## 最小实验

输入：

```text
一批 Lean theorem proving tasks
```

输出：

```text
系统自动生成的 verified lemma memory
```

目标：

```text
在 heldout tasks 上提升 proof success 或降低 proof search cost
```

基本对照：

| 组 | 含义 |
| --- | --- |
| no memory | 直接证明 |
| mathlib retrieval | LeanSearch / Loogle / premise retrieval |
| raw trace memory | 检索过去 proof traces |
| final theorem memory | 近邻 theorem / answer，作为污染风险对照 |
| verified lemma memory | 只存已由 Lean 验证的中间 lemma |
| generalized lemma memory | 从多个实例抽象出更一般 lemma，再验证并复用 |

主指标：

- proof success rate。
- proof search nodes / tactics / time。
- retrieved lemma usefulness。
- harmful retrieval rate。
- verified lemma reuse rate。
- heldout family transfer。
- proof length reduction。
- memory construction cost。

关键裁决：

> 如果 verified lemma memory 只在同模板近邻上有效，那就是 retrieval / cache；如果它能从训练任务中生成更抽象的 lemma，并在表面不同、参数不同、组合结构不同的 heldout theorem 中复用，才接近高价值 memory。

## 小规模训练路线

几台 8 卡服务器不适合从零训练大模型。更现实的训练目标是 retrieval / reranking / proof policy / lemma proposal。

### Stage 0：不训练，先做审计

- 建立 Lean task families。
- 划分 family-heldout / template-heldout。
- 定义 memory schema。
- 跑 no-memory / theorem retrieval / raw trace memory / verified lemma memory baseline。

目标：

> 先确认这个问题是否真的有 memory 增量。

### Stage 1：训练 reranker

任务：

> `proof state + candidate lemma -> useful / not useful`

数据：

- 从 mathlib / LeanDojo-style traces 提取 proof states。
- 使用实际 proof dependencies 构造正样本。
- 使用相似但未被使用的 theorem 构造 hard negatives。

目标：

- 降低 harmful retrieval。
- 提高 useful lemma 命中率。
- 在固定 top-k 下提升 proof search success。

### Stage 2：训练 tactic / proof-step policy

任务：

> condition on retrieved verified memory，预测下一步 tactic 或 proof fragment。

目标：

- memory-conditioned prover 优于普通 retrieval prover。
- proof search nodes / time 下降。
- heldout family 上仍有效。

### Stage 3：训练 lemma proposer

任务：

> 从 solved tasks / failed goals / similar proof states 中提出 candidate lemma statement 和 proof sketch，经 Lean checker 过滤。

闭环：

```text
propose lemma -> Lean verifies -> add to memory -> heldout tasks reuse -> successful reuse becomes training signal
```

这是高风险高价值阶段，不应在 Stage 0/1 失败时继续扩张。

## 失败条件

这条线应承认失败的情况：

- verified lemma memory 不优于 mathlib retrieval / LeanSearch-like baseline。
- 生成 lemma 只是原题或近邻模板的重命名。
- family-heldout / template-heldout 上没有复用收益。
- harmful retrieval rate 随 memory 增长快速上升。
- reranker 只能学习 theorem popularity，不能学习 proof-state usefulness。
- lemma proposal 成功率过低，memory construction cost 吞掉收益。
- proof checker 通过但 lemma 太专用，不能降低后续 proof search cost。

## 当前建议

Lean 方向适合作为 `verified subproblem memory` 的 sanity check 和高价值候选分支。

更稳的第一步不是“训练大模型做数学”，而是：

> Lean-based verified lemma memory sanity check + proof-state retriever / reranker training。

如果这个方向站住，再推进 lemma proposer 和 recursive subproblem DAG。

如果这个方向站不住，`verified subproblem memory` 至少在形式化数学证明场景中缺少独立增量，应回退到其他非 Lean 验证场景或承认为 retrieval engineering。
