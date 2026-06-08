---
type: experiment-protocol
status: active
tags:
  - control-feedback
  - experiment
  - explicit-state-semantics
  - local-state-access
  - trainability
---

# 控制反馈：实验协议

这份文档只回答怎么实验，不承担历史叙事。

当前实验目标：

> 检验 instruction token 是否能通过显式状态事件获得可训练数据飞轮，以及局部状态访问是否能在强检索/索引基线下改善地址生成、访问成本、长度泛化和局部修复。

## 总体设计

A/B 分支必须用 2x2 设计拆开。

| 局部访问 / 显式语义 | 无显式状态语义 | 有显式状态语义 |
| --- | --- | --- |
| 无局部访问 | typed tools 强基线 | A：显式状态语义 |
| 有局部访问 | retrieval/index 强基线 | A+B：完整候选接口 |

实验不是证明某个名字正确，而是切出：

- A 的训练、回放、归因、纠偏贡献。
- B 的寻址、局部访问、长度泛化、成本贡献。
- A+B 的交互贡献。

## 预备层：协议中立轨迹

所有任务先写成协议中立的 semantic transition，不能先写成 `Load/Store` 专家轨迹。

示例：

```text
locate violated constraint
inspect relevant object
modify state element
check invariant
make change visible
recover previous consistent state
```

然后分别渲染到：

- append-only answer。
- standard tools。
- typed tools + trace id + logging + transaction。
- explicit state semantics。
- local state access。
- explicit state semantics + local state access。

如果底层专家 IR 直接写成 `ADDRESS/READ/WRITE/VERIFY`，A/B 组会天然占便宜。

## A 分支：显式状态语义与训练可行性

A 的实验问题：

> 显式状态事件是否让 instruction token 获得比低效探索/RL 更自然的训练入口？

### A 的最小阈值

一个系统至少满足以下条件，才算进入 A：

- 事件类型统一：不同底层工具调用能映射到 `address/read/write/verify/commit/rollback/diagnose`。
- 事件生命周期清楚：事件有创建、执行、返回、失败、提交或可见性变化。
- 状态对象清楚：事件作用于明确 state object、address、scope 或 delta。
- 因果链可回放：给定事件轨迹，可以重放或半重放状态变化。
- 事件进入后续决策：后续动作能引用 event id、delta、diagnostic result 或 commit state。

如果只满足前四条，但后续决策不用这些事件对象，只能算 trace/logging protocol。

### A 的强版本

A 的强版本还要满足：

- 可诊断：错误能被归因到事件类型或事件位置。
- 可纠偏：诊断结果能触发局部修复动作。
- 可反事实：可以构造“同一轨迹，只改某个事件”的样本。
- 可监督：事件级标签可用于 imitation、error attribution 或 repair policy 学习。

### A 的强基线

A 的强对手不是普通 tools，而是：

```text
grep(query, trace_id)
read_file(path, range, trace_id)
edit_file(path, range, patch, tx_id)
sql(query, trace_id)
run_check(target, trace_id)
commit(tx_id)
rollback(tx_id)
```

这个 baseline 已经有：

- typed schema。
- trace id。
- logging。
- transaction。
- typed arguments。

A 必须回答：

> 在工具能力相近甚至相同的情况下，统一状态事件接口是否让轨迹更可训练、更可归因、更可纠偏？

### A 的训练阶段

A 不应一开始诉诸大规模 RL。建议按四层推进。

第一层：轨迹生成。

- 从协议中立 semantic transition 渲染出不同接口轨迹。
- 记录状态前后变化、事件 id、错误点、验证结果。
- 生成正轨迹、单点污染轨迹和局部修复轨迹。

第二层：模仿学习。

- 训练或评估 next action prediction。
- 比较 action accuracy、parse-valid rate、样本效率。
- NLL 只作为辅助指标，必须控制 action entropy、schema 长度和输出格式复杂度。

第三层：归因与纠偏学习。

- 训练 error attribution classifier 或让模型直接诊断事件错误。
- 训练 repair policy：给定失败事件和局部状态，生成局部修复动作。
- 比较局部修复成功率、平均恢复步数、同类错误复发率。

第四层：数据飞轮。

- 用失败轨迹自动构造反事实样本。
- 用回放机制验证修复样本。
- 用局部事件替代整段失败标签，减少负样本污染。
- 检验继续训练后是否降低同类错误复发。

### A 的主指标

主指标应落在执行语义和训练可用性，而不是只看日志漂亮。

- repair success。
- cost-normalized repair success。
- 平均恢复步数。
- 同类错误复发率。
- replay reproducibility。
- event-level attribution accuracy。
- student model sample efficiency。
- counterfactual sample validity。

辅助指标：

- next action NLL。
- action accuracy。
- parse-valid rate。
- trajectory compression ratio。

如果使用 NLL，必须控制：

- token budget。
- schema 信息。
- action entropy。
- 输出格式复杂度。
- 可见状态量。

### A 的失败条件

A 失败或不足以扩展叙事的情况：

- 事件对象只是日志标签，不能影响后续决策。
- 可回放只是展示层，不能支撑局部修复。
- 归因高度依赖人工解释。
- 纠偏成功率不改善。
- 训练收益来自更短格式或更强 schema，而不是状态语义。
- strong typed tools baseline 达到同等训练和纠偏效果。

## B 分支：局部状态访问与地址生成

B 的实验问题：

> 在 resolver 能力相近时，局部状态访问接口是否改善地址生成、访问成本、长度泛化和局部修复范围？

### B 的最小阈值

一个系统至少满足以下条件，才算进入 B：

- global state 默认隐藏。
- 每步 observation budget 固定。
- 访问由模型控制。
- 返回粒度受限。
- 任务推进依赖多轮局部访问。

如果模型仍可随时读取完整状态，只能算支持局部读取的 full-context system。

### Selector Resolver Reader

B 必须拆开三个组件。

| 组件 | 输入 | 输出 | 责任 |
| --- | --- | --- | --- |
| selector | goal、当前观察、scratchpad | query、intent、symbolic address 或选择目标 | 决定要找什么 |
| resolver | query/address/intent、索引、workspace | candidate addresses 或 ranked candidates | 把选择意图映射到候选位置 |
| reader | candidate address、access policy | returned observation | 决定返回多少、什么粒度、什么格式的状态 |

如果不拆开，B 的结果可能被 resolver、reader、cell 粒度或 address schema 偷渡解释掉。

### B 的两层实验

第一层：固定 resolver，比 access interface。

```text
same oracle/LSP/SQL resolver ->
  return large chunk
  return local cell
  return local cell + writable address
  return local cell + commit/rollback metadata
```

这一层回答：

> 局部访问接口本身是否有价值？

第二层：固定 access interface，比 resolver。

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

### B 的强基线

B 的强对手包括：

- BM25。
- vector search。
- SQL / index。
- tree-sitter / LSP。
- 代码索引。
- 编辑器跳转。
- learned retriever。
- 任务专用 resolver。

`retriever/index/resolver` 可以是 address resolver 的实现。B 不能假装替代这些系统。

B 要证明的是：

> 在 resolver 能力相近时，统一局部状态访问接口是否让控制、纠偏、学习或成本结构更好。

### B 的主指标

- selector accuracy。
- resolver top-k hit rate。
- returned token cost。
- accessed cell count。
- unnecessary read rate。
- global fallback count。
- length generalization。
- repair read range。
- false-local-repair rate。
- total cost Pareto。

### B 的失败条件

B 失败或不足以扩展叙事的情况：

- 只证明主动检索有用。
- 结果主要来自更强 resolver。
- meaningful address 偷渡语义。
- local cell 粒度由人工任务设计贡献全部收益。
- 状态变长后访问步数或全局回退爆炸。
- strong retrieval/indexing baseline 达到同等效果。

## Workspace 粒度消融

Workspace 粒度是核心变量，不能藏在接口里。

至少比较地址语义：

| 类型 | 示例 | 含义 |
| --- | --- | --- |
| meaningful address | `users[17].transactions` | 地址直接携带对象语义 |
| typed address | `table=users,row=17,field=transactions` | 地址携带类型结构 |
| hierarchical address | `root/users/17/transactions` | 地址携带层级结构 |
| opaque address | `cell_83921` | 地址不携带可读语义 |
| learned/generated address | model/system generated key | 地址由模型或系统生成 |

至少比较 cell 粒度：

- field-level cell。
- object-level cell。
- chunk-level cell。
- file-level cell。
- hierarchical cell。
- dynamically split cell。

必须记录：

- cell schema 是否人工设计。
- address schema 是否人工设计。
- 切分规则是否任务专用。
- 是否需要人工标注。
- 是否可跨任务复用。

## 成本账本

必须计入 setup、runtime、失败恢复和人工成本。

一次性成本：

- workspace 构造成本。
- cell 切分成本。
- address schema 设计成本。
- index build 成本。
- runtime/scaffold 实现成本。
- validator / transaction / rollback 实现成本。

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

至少报告三种口径：

- no-setup。
- amortized setup。
- full cost。

如果只在 no-setup 口径赢，在 full cost 口径输，结论应收缩为“高工程投入下可用”。

## A+B 交互指标

A+B 的合流不能靠事后解释。

建议主指标：

> cost-normalized repair success under length generalization

可写成：

```text
CNRS = repair_success / total_cost
```

交互项定义：

```text
Interaction = Y11 - Y10 - Y01 + Y00
```

其中：

- `Y00` = 无 A、无 B。
- `Y10` = 有 A、无 B。
- `Y01` = 无 A、有 B。
- `Y11` = 有 A、有 B。

强合流：

- `Y11` 显著优于 `Y10` 和 `Y01`。
- 交互项为正，且超过预注册效应量阈值。
- 在主要任务族和长度外推上都成立。
- 计入成本账本后仍成立。

弱合流：

- `Y11` 同时继承 A 的归因/训练优势和 B 的成本优势。
- 没有明显超加性，但形成 Pareto 非支配点。
- 可作为工程路线继续推进，但不能强称统一低层原语已经站住。

失败：

- `Y11` 只是 A+B 的简单拼接。
- `Y11` 被 strong typed tools 或 strong retrieval/indexing 追平。
- `Y11` 的优势来自 setup/scaffold、meaningful address 或人工粒度设计。

## 任务选择

第一阶段任务：

- JSON。
- AST。
- ledger。
- dependency graph。

这些任务偏结构化，天然有利于状态访问接口。第一阶段允许这样做，因为目标是切变量、降低噪声、自动判定。

第一阶段结论只能写成：

> 在强结构局部状态任务上，某种状态访问接口可能更可训练、更可归因或更可纠偏。

第二阶段任务：

- 长文档局部修订。
- 代码仓局部修复。
- 多文件一致性维护。
- 实验日志与分析状态维护。
- 研究笔记状态更新。

如果第一阶段都没有稳定信号，不应直接跳到开放世界任务。

## 当前交付物

下一步实验至少产出：

- 一个协议中立任务定义。
- 一份 A/B 阈值定义。
- 一份 2x2 对照协议。
- 一份 selector / resolver / reader 拆分说明。
- 一份 workspace 粒度消融表。
- 一份成本账本模板。
- 一份训练数据生成方案。
- 一份失败判定模板。

## 结论边界

第一批实验只回答是否值得继续推进独立切面，不回答终局价值。

能说：

- A 是否给 instruction token 提供更自然的训练入口。
- B 是否提供更清楚的局部反馈信源控制变量。
- A+B 是否有初步交互收益。

不能说：

- `Token = Instruction` 已被证明。
- `Load/Store` 已经成为基础模型接口。
- 控制反馈理论已经成立。
- 它已经全面优于最强 agent。
