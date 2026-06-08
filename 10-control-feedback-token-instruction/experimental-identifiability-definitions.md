---
type: definition-note
status: active
tags:
  - control-feedback
  - experimental-identifiability
  - explicit-state-semantics
  - local-state-access
---

# 控制反馈实验可辨识性：六个定义

这份笔记补充控制反馈线当前最缺的实验可辨识性定义。目标不是证明方向成立，而是防止实验结果被 baseline 定义、workspace 粒度、resolver、runtime/scaffold 或任务偏置偷渡解释掉。

核心原则：

> A/B 分支不是天然二元变量，而是连续谱。实验必须先给出操作性阈值、变量拆分和裁决规则，否则结果不可解释。

六个需要先固定的定义：

- A 的操作性阈值。
- B 的操作性阈值。
- selector / resolver / reader 分解。
- workspace 粒度消融。
- 成本账本。
- A+B 交互指标。

## 1. A 的操作性阈值

A 是“显式状态语义”。它不是简单地出现 `read`、`write` 或 typed tool call，而是要看状态事件是否形成稳定运行时对象。

### 1.1 A 不是什么

以下都不足以单独算作 A：

- 工具名里有 `read` 或 `write`。
- 工具有 typed schema。
- 日志里记录了工具调用。
- 工具有 trace id。
- 工具有 transaction id。
- 工具调用可以被事后人工解释。

这些是 A 的组成材料，但不等于 A。

### 1.2 A 的最小阈值

一个系统至少满足以下条件，才算进入 A：

- 事件类型统一：不同底层工具调用能映射到统一事件类型，如 `address/read/write/verify/commit/rollback/diagnose`。
- 事件生命周期清楚：事件有创建、执行、返回、可见性变化、失败或提交状态。
- 状态对象清楚：事件作用于明确 state object、address、scope 或 delta。
- 因果链可回放：给定事件轨迹，可以重放或半重放状态变化。
- 事件能进入后续决策：后续动作能引用 event id、delta、diagnostic result 或 commit state，而不是只把它们当日志。

如果只满足前四条，但后续决策不使用这些事件对象，则只能算 `trace/logging protocol`，不能算完整 A。

### 1.3 A 的强版本

A 的强版本还应满足：

- 可诊断：错误能被归因到事件类型或事件位置。
- 可纠偏：诊断结果能触发局部修复动作。
- 可反事实：可以构造 “同一轨迹，只改某个事件” 的训练样本。
- 可监督：事件级标签可用于 imitation、error attribution 或 repair policy 学习。

### 1.4 A 的操作性分级

| 等级 | 名称 | 判定 |
| --- | --- | --- |
| A0 | 无显式状态语义 | 异质工具调用，无统一事件对象。 |
| A1 | typed trace | 有 typed schema、trace id、logging，但事件主要用于记录。 |
| A2 | unified event protocol | 有统一事件类型、状态对象、生命周期和回放。 |
| A3 | decision-active state semantics | 事件对象进入后续决策，支持诊断、纠偏和训练。 |

实验中若声称 “有 A”，至少应达到 A2。若声称 A 对学习和纠偏有价值，应达到 A3。

## 2. B 的操作性阈值

B 是“局部状态访问”。它不是简单地返回一个 range 或 chunk，而是要看模型每一步是否被限制在局部可见状态内，并且必须主动控制访问。

### 2.1 B 不是什么

以下都不足以单独算作 B：

- 工具支持 `read_file(path, range)`。
- RAG 返回 top-k chunks。
- SQL 返回若干行。
- LSP 跳到一个 symbol。
- 模型偶尔只看了一小段上下文。

这些都可能有局部读取行为，但不一定构成 B。

### 2.2 B 的最小阈值

一个系统至少满足以下条件，才算进入 B：

- global state 默认隐藏：模型每一步不能直接看到完整状态或任意大块状态。
- observation budget 固定：每步可见状态量有明确预算，如 token 数、cell 数或 byte 数。
- 访问由模型控制：模型必须生成 query、intent、address 或 selector 来获取下一批局部状态。
- 返回粒度受限：runtime 返回的不是任意大上下文，而是受限 cell、chunk、field 或 object。
- 任务推进依赖多步访问：模型需要通过多轮局部读取、更新和验证完成任务。

如果模型仍可随时读取完整状态，则不算 B，只能算 “支持局部读取的 full-context system”。

### 2.3 B 的强版本

B 的强版本还应满足：

- 可扩展：状态规模增大时，每步 observation 不随全局状态线性增长。
- 可寻址：模型能稳定生成或选择有效访问目标。
- 可局部修复：错误修复只需访问较小局部范围。
- 可控制全局回退：系统记录何时触发全局扫描、全局重解释或 large-context fallback。

### 2.4 B 的操作性分级

| 等级 | 名称 | 判定 |
| --- | --- | --- |
| B0 | full-context | 模型可直接看到完整状态或大块状态。 |
| B1 | optional local access | 工具支持局部读取，但模型仍可读取全局状态。 |
| B2 | budgeted local observation | 每步可见状态受预算限制，模型必须主动访问局部状态。 |
| B3 | scalable local state access | 在长状态上保持局部访问成本，并减少全局回退。 |

实验中若声称 “有 B”，至少应达到 B2。若声称 B 有扩展性价值，应达到 B3。

## 3. Selector / Resolver / Reader 分解

B 的最大混淆来自 resolver。为了避免把寻址能力、检索能力和读取粒度混在一起，必须拆成 selector、resolver、reader。

### 3.1 三个组件

| 组件 | 输入 | 输出 | 责任 |
| --- | --- | --- | --- |
| selector | goal、当前观察、scratchpad | query、intent、symbolic address 或选择目标 | 决定要找什么。 |
| resolver | query/address/intent、索引、workspace | candidate addresses 或 ranked candidates | 把选择意图映射到候选位置。 |
| reader | candidate address、access policy | returned observation | 决定返回多少、什么粒度、什么格式的状态。 |

### 3.2 为什么必须拆开

如果不拆开，B 的实验可能被以下因素主导：

- selector 更聪明。
- resolver 更强。
- reader 返回更多信息。
- cell 粒度更有利。
- address schema 偷渡语义。

结果看似是局部访问胜利，实际可能只是 resolver 或 reader 更强。

### 3.3 两层实验

第一层：固定 resolver，比 reader/access interface。

示例：

```text
same oracle/LSP resolver ->
  return large chunk
  return local cell
  return local cell + writable address
  return local cell + commit/rollback metadata
```

这一层回答：

> 局部访问接口本身是否有价值？

第二层：固定 reader/access interface，比 resolver。

示例：

```text
same local cell access <-
  oracle resolver
  BM25 resolver
  vector resolver
  SQL/index resolver
  tree-sitter/LSP resolver
  learned resolver
```

这一层回答：

> 什么 resolver 最适合承载局部状态访问？

### 3.4 Resolver parity 的弱定义

严格的 resolver parity 很难成立。可先采用弱定义：

- 在同一任务集上，resolver top-k hit rate 接近。
- 返回候选数量接近。
- 返回内容 token budget 接近。
- resolver 构建成本计入成本账本。
- selector 由同一模型或同一策略产生。

如果这些不接近，不能把结果归因到 B。

## 4. Workspace 粒度消融

Workspace 粒度可能把答案藏进接口。必须把 cell、address、scope、schema 作为核心变量。

### 4.1 为什么粒度重要

如果地址是：

```text
users[17].transactions
```

这个地址已经携带大量语义。模型看到它就知道对象类型、用户编号、字段含义。

如果地址是：

```text
cell_83921
```

模型可能不知道这个 cell 代表什么。

因此，B 的成功可能来自 meaningful address，而不是局部访问机制本身。

### 4.2 地址语义消融

至少应比较：

| 类型 | 示例 | 含义 |
| --- | --- | --- |
| meaningful address | `users[17].transactions` | 地址直接携带对象语义。 |
| typed address | `table=users,row=17,field=transactions` | 地址携带类型结构，但较少自然语言。 |
| hierarchical address | `root/users/17/transactions` | 地址携带层级结构。 |
| opaque address | `cell_83921` | 地址不携带可读语义。 |
| learned/generated address | model/system generated key | 地址由模型或系统生成。 |

若只在 meaningful address 下有效，结论必须收缩。

### 4.3 Cell 粒度消融

至少应比较：

- field-level cell。
- object-level cell。
- chunk-level cell。
- file-level cell。
- hierarchical cell。
- dynamically split cell。

指标包括：

- selector accuracy。
- resolver hit rate。
- reader token cost。
- repair success。
- false-local-repair rate。
- global fallback count。

### 4.4 粒度设计成本

必须记录：

- cell schema 是否人工设计。
- address schema 是否人工设计。
- 切分规则是否任务专用。
- 是否需要人工标注。
- 是否可跨任务复用。

如果粒度设计成本很高，薄接口可能只是把复杂性转嫁给 workspace 设计。

## 5. 成本账本

成本账本用于防止 runtime/scaffold 偷渡收益。

### 5.1 必须计入的成本

一次性成本：

- workspace 构造成本。
- cell 切分成本。
- address schema 设计成本。
- index build 成本。
- runtime/scaffold 实现成本。
- validator / transaction / rollback 机制实现成本。

每任务成本：

- selector 调用成本。
- resolver 调用成本。
- reader 返回 token 成本。
- model input token。
- model output token。
- action/tool-call 数。
- verification 次数。
- rollback/retry 次数。
- global fallback 次数。

失败恢复成本：

- 平均恢复步数。
- 恢复读取范围。
- 恢复 token 成本。
- 同类错误复发次数。

人工成本：

- schema 设计时间。
- 任务适配时间。
- 人工标注量。
- 人工调试量。

### 5.2 成本摊销

一次性成本可以在多任务上摊销，但必须明确摊销方式。

建议至少报告三种口径：

- no-setup：只看运行时成本。
- amortized setup：一次性成本按任务数或样本数摊销。
- full cost：一次性成本和运行时成本都计入。

如果一个方法只在 no-setup 口径赢，在 full cost 口径输，结论应收缩为 “高工程投入下可用”，不能说接口天然高效。

### 5.3 Runtime 约束与模型学习的区分

`semantic success` 或 `repair success` 可能被 validator、transaction、rollback 强烈影响。

必须区分：

- model-only proposal quality。
- runtime-corrected success。
- validator rejection rate。
- rollback-assisted success。
- final committed success。

如果成功率主要来自 runtime 自动拒绝错误或自动回滚，不能说模型学会了更好的状态管理策略。

## 6. A+B 交互指标

A+B 的合流不能靠事后解释，必须预先定义交互收益。

### 6.1 主指标优先级

建议预注册一个主指标：

> cost-normalized repair success under length generalization

可写成：

```text
CNRS = repair_success / total_cost
```

其中 `total_cost` 可以按实验阶段定义为：

```text
total_cost =
  input_tokens
  + output_tokens
  + tool_call_weight * tool_calls
  + verification_weight * verifications
  + rollback_weight * rollbacks
  + fallback_weight * global_fallbacks
  + setup_weight * amortized_setup_cost
```

权重必须预先固定，或报告多个权重方案下的 Pareto 结果。

### 6.2 交互项定义

设：

- `Y00` = 无 A、无 B。
- `Y10` = 有 A、无 B。
- `Y01` = 无 A、有 B。
- `Y11` = 有 A、有 B。

若指标越大越好，交互项可定义为：

```text
Interaction = (Y11 - Y10) - (Y01 - Y00)
```

等价于：

```text
Interaction = Y11 - Y10 - Y01 + Y00
```

若指标越小越好，比如恢复步数或总成本，应先转成收益指标，或反向定义。

### 6.3 什么算 A+B 合流成功

强合流：

- `Y11` 显著优于 `Y10` 和 `Y01`。
- 交互项为正，且超过预注册效应量阈值。
- 在主要任务族和长度外推上都成立。
- 计入成本账本后仍成立。

弱合流：

- `Y11` 同时继承 A 的归因优势和 B 的成本优势。
- 没有明显超加性，但形成 Pareto 非支配点。
- 可作为工程路线继续推进，但不能强称统一低层原语已经站住。

失败：

- `Y11` 只等于 A+B 的简单拼接，没有成本或纠偏优势。
- `Y11` 被 strong typed tools 或 strong retrieval/indexing 追平。
- `Y11` 的优势来自 setup/scaffold 或 meaningful address 偷渡。

### 6.4 多指标 Pareto 裁决

如果指标不止一个，至少报告：

- semantic success。
- repair success。
- total runtime cost。
- amortized setup cost。
- global fallback count。
- false-local-repair rate。
- error attribution accuracy。
- trajectory learnability。

不能只挑赢的指标解释。应预先指定：

- primary metric。
- secondary metrics。
- hard safety constraints。

例如：

- primary metric：CNRS。
- secondary metrics：error attribution accuracy、global fallback count、trajectory NLL。
- hard constraints：semantic success 不得低于 baseline，false-local-repair rate 不得高于 baseline。

## 7. 当前最小可辨识命题

补完六个定义后，当前最小命题应改写为：

> 在预先定义 A/B 阈值、selector-resolver-reader 分解、workspace 粒度消融、成本账本和交互指标的前提下，显式状态语义与局部状态访问是否分别、以及组合后，在强 typed tools/logging/transaction 和强 retrieval/indexing 基线下，形成不可被 baseline、resolver、workspace 粒度或 scaffold 成本解释掉的学习、纠偏或成本优势？

这个命题仍可输。

如果输掉，至少能知道输在哪里：

- A 阈值不成立：显式状态语义只是 logging。
- B 阈值不成立：局部访问只是 optional read range。
- resolver 主导结果：B 不可归因。
- meaningful address 主导结果：workspace 粒度偷渡。
- runtime 主导结果：模型没有学会。
- A+B 无交互：统一接口未站住。

