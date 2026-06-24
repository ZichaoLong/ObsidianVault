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

实验推进应分三层。

Stage 0：工具结构化 sanity check。

- 比较 freeform tools 与 typed tools。
- 作用是校准任务和实现，不是 A 分支主贡献。
- 若 typed tools 都不能稳定优于 freeform tools，说明任务、prompt、工具定义或评估协议可能有问题。
- 若 typed tools 胜出，只能说明任务捕捉到了现代 Agent 工程已知收益。

Stage 1：A 分支核心对照。

- 比较 `typed tools + trace/logging/approval/checkpoint/replay/diff/transaction` 与 decision-active explicit state semantics。
- 这里才检验 A 的剩余特殊点。

Stage 2：A/B 2x2。

- 检验 A、B 各自贡献，以及 A+B 是否形成弱合流或强合流。

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
- freeform tools。
- typed tools。
- typed tools + trace id + logging + approval + checkpoint/replay + diff/transaction。
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
- tool call lifecycle / call id。
- trace id。
- logging。
- approval / guardrail。
- checkpoint / replay / fork。
- patch / diff。
- transaction。
- typed arguments。

这不是为了否认 typed tools 的价值。相反，frontier / provider-level / serious agent runtime 已经在相当程度上采用 typed tool calling、schema、trace/call id、approval、checkpoint/replay、patch/diff、trace grading 或 eval loop。A 不能再把“工具调用结构化”当作新贡献。证据表见 [[10-control-feedback-token-instruction/reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]]。

Stage 0 可以验证 typed tools 相对 freeform tools 的收益，但那只是任务校准。A 剩下的特殊点是：

> typed tool traces 能否升级成 decision-active explicit state semantics，也就是事件不只是工具调用记录，而是可回放、可诊断、可局部修复、可构造反事实、可用于继续训练的状态转移对象。

这里要区分三层：

- `semantic transition` 是协议中立的底层轨迹 IR，用于公平生成对照轨迹。
- `address/read/write/verify/commit/rollback/diagnose` 是 A 的候选可见事件语言。
- A 的真正研究对象是这些可见事件是否形成进入后续决策的显式状态语义。

如果 strong typed tools baseline 也实现了同等显式状态语义，那它其实已经吸收 A。此时结论应降级为：

> A 不是 TapeWalker 独有机制，而是优秀 Agent runtime 可能自然收敛到的状态事件层。

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

## B 分支：局部状态访问

B 的实验问题：

> 在隐藏全局状态、固定观察预算下，模型主动选择局部反馈信源，是否能改善控制成本、长度泛化、错误归因、rollback / repair 范围和训练样本质量？

### B 的最小阈值

一个系统至少满足以下条件，才算进入 B：

- global state 默认隐藏。
- 每步 observation budget 固定。
- 访问由模型控制。
- runtime 返回受限局部观察。
- 任务推进依赖多轮局部访问。

如果模型仍可随时读取完整状态，只能算支持局部读取的 full-context system。

### B0 Access Mode

B0 不应选择 TapeWalker 作为总入口。

第一版 B0 采用：

```text
addressed local cell/window access
```

最小接口：

```text
read_budget()
read_window(address, radius)
navigate(address, relation, budget)
zoom(range, level)
mark(address, label)
```

第一版 `relation` 只保留：

```text
prev / next
```

第二阶段再考虑：

```text
parent / child
```

`cause_candidate / effect_candidate / likely_error_region` 不进入 B0。它们很容易把诊断、归因或 resolver 信号偷渡进接口，应放入 A+B、topology-aware 条件或 generated analyzer baseline。

### 实验矩阵

B 实验必须拆开以下变量，否则结果无法归因。

| 变量 | 可选值 | 目的 |
| --- | --- | --- |
| substrate | trace / JSON / AST / ledger / long document / code repo / UI | 状态空间是什么。 |
| access mode | full-context / large chunk / B0 cell-window / topology view / TapeWalker | 模型能看到什么。 |
| selector | model-generated query / address / next move / oracle selector | 决定下一步看哪里。 |
| resolver | oracle / BM25 / vector / SQL / LSP / learned / generated analyzer | 把意图映射到位置。 |
| reader | exact cell / window / range / summarized bin / screenshot crop | 返回多少信息。 |
| policy | random / linear scan / retrieval jump / topology-aware / active foveated | 多步访问策略。 |
| overview | none / sparse / generic feature bins / learned feature / semantic summary | 是否提供低保真方向信号。 |
| A variable | none / typed trace / explicit state event / verify-diagnose-rollback | 是否引入显式状态语义。 |

第一阶段 B0 固定为：

```text
substrate = trace
access mode = addressed local cell/window
relation = prev / next
overview = none
A variable = none
```

这样先检验最小局部访问，而不把 TapeWalker、overview、diagnose 或 semantic event 混入 B 的基本判断。

### Selector Resolver Reader

B 必须拆开三个组件。

| 组件 | 输入 | 输出 | 责任 |
| --- | --- | --- | --- |
| selector | goal、当前观察、scratchpad | query、intent、symbolic address 或选择目标 | 决定要找什么 |
| resolver | query/address/intent、索引、workspace | candidate addresses 或 ranked candidates | 把选择意图映射到候选位置 |
| reader | candidate address、access policy | returned observation | 决定返回多少、什么粒度、什么格式的状态 |

如果不拆开，B 的结果可能被 resolver、reader、cell 粒度或 address schema 偷渡解释掉。

### 第一候选任务：Trace-Local First-Error Localization

第一候选任务族是：

> 给定一条已经失败的 agent trace，在有限局部观察预算下，定位第一次把任务推进到错误轨道上的决策、假设、工具调用、状态更新或 patch。

最小输入：

```text
task_spec
failed_trace_id
trace_length
initial_observation_budget
local_access_interface
```

模型不能直接读取完整 trace。它只能通过 B0 接口逐步观察。

最小输出：

```text
mark(first_bad_step)
```

可选输出：

```text
confidence
short_reason
suggested_rollback_scope
```

该任务不是找第一次显式报错位置。它要找错误链条的起点：

```text
step 083: wrote invalid state
step 157: exception is downstream symptom
```

它优先于 JSON / AST / ledger 的原因是：

- 它直接连接 agent 控制、错误归因、rollback、repair 和数据飞轮。
- trace 天然有时间 / 状态转移结构，适合局部访问。
- first error 往往没有稳定关键词，不能总被 grep 或 BM25 吃掉。
- 它能同时区分 B-only、A+B、TapeWalker policy 和 strong analyzer baseline。

### First-Error 标签协议

first-error 标注必须防止实验变成标注争议。

每条失败 trace 至少记录：

```text
first_bad_step
acceptable_interval
downstream_symptom_steps
error_type
rollback_scope
label_confidence
label_source
```

标签规则：

- `first_bad_step` 是最早使任务进入错误轨道的步骤，不是最早出现报错的步骤。
- 如果存在多因一果，使用 `acceptable_interval` 或 `first_bad_set`，不要强行单点。
- `downstream_symptom_steps` 单独记录，避免模型因命中最终报错而被误判为成功。
- 如果错误不可唯一归因，该样本进入 ambiguous bucket，只用于定性分析或鲁棒性测试。
- semi-synthetic trace 必须说明错误注入点和人工校验方式。
- real agent trace 必须允许多标注者分歧，并报告 agreement。

第一版主指标：

- first bad step hit rate。
- acceptable interval hit rate。
- distance to first bad step。
- downstream symptom confusion rate。
- observation tokens。
- `read_window` 次数。
- navigation steps。
- false negative rate。
- wrong-direction recovery。

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

- full trace / full context。
- BM25。
- vector search。
- SQL / index。
- tree-sitter / LSP。
- 代码索引。
- 编辑器跳转。
- learned retriever。
- 任务专用 resolver。
- generated analyzer / generated search code。
- RLM / recursive context management。

`retriever/index/resolver` 可以是 address resolver 的实现。B 不能假装替代这些系统。

B 的强基线设计应参考 [[10-control-feedback-token-instruction/reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]]，把 search、index、local read/write、resource discovery、tool discovery、patch/diff 和 checkpoint/replay 纳入 baseline，而不是纳入待证明的新机制。

B 要证明的是：

> 在 resolver 能力相近时，统一局部状态访问接口是否让控制、纠偏、学习或成本结构更好。

### B2 / TapeWalker 位置

TapeWalker 不进入 B0 定义。

它作为 B2 access policy：

```text
pos / fov / move / zoom / load / mark / store
```

要比较：

- random / linear scan。
- retrieval jump。
- topology-aware trace access。
- pure TapeWalker scan。
- TapeWalker + generic overview。

peripheral-like overview 只作为 B2 消融，不进入 B0。第一版 B0 的 `read_window` 不依赖 overview、summary、anomaly score 或 likely-error region。

如果 TapeWalker 赢，只能说明 active foveated policy 在某些可导航 workspace 上有价值；不能自动证明 B 的全部主张。

如果 TapeWalker 输，也不能直接判定 B 失败；B 可能由 topology-aware trace access、retrieval jump、LSP、SQL 或其他 resolver 承载。

### Dynamic Workspace Recovery

`dynamic workspace recovery` 暂不与 first-error localization 并列作为第一任务。

若要升级为主线任务，必须先补齐：

- 输入：当前 workspace、失败 trace、可访问局部状态、可用 checkpoint。
- 输出：恢复到哪个状态、丢弃哪些变更、保留哪些变更、下一步 repair plan。
- 评价：恢复成功率、保留有效工作量、恢复读取范围、恢复成本、后续 repair success。
- 强基线：full replay、checkpoint rollback、global compact / summarize、RLM、generated recovery analyzer。

在这些定义完成前，它只作为 trace-local first-error localization 的后续扩展。

### B 的主指标

- first bad step hit rate。
- acceptable interval hit rate。
- distance to first bad step。
- downstream symptom confusion rate。
- returned token cost。
- accessed cell count。
- `read_window` 次数。
- navigation steps。
- unnecessary read rate。
- global fallback count。
- length generalization。
- repair read range。
- false-local-repair rate。
- selector accuracy。
- resolver top-k hit rate。
- wrong-direction recovery。
- total cost Pareto。

### B 的失败条件

B 失败或不足以扩展叙事的情况：

- 只证明主动检索有用。
- 结果主要来自更强 resolver。
- meaningful address 偷渡语义。
- local cell 粒度由人工任务设计贡献全部收益。
- first-error 标签不可稳定判定。
- 模型只命中下游 symptom，而非 first error。
- overview / analyzer 直接给出目标区域。
- 状态变长后访问步数或全局回退爆炸。
- strong full-context / retrieval / indexing / RLM / generated-analyzer baseline 达到同等效果。

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

注意：

- `Interaction` 只应用于预注册主收益指标。
- 成本、恢复步数、错误率等越小越好的指标，应先转成收益指标再计算。
- `Interaction <= 0` 不必然表示 A+B 互相干扰，也可能只是收益饱和。

强合流：

- `Y11` 显著优于 `Y10` 和 `Y01`。
- `Interaction > delta`，且超过预注册效应量阈值。
- 在主要任务族和长度外推上都成立。
- 计入成本账本后仍成立。
- 可以继续讨论统一状态访问接口或候选低层原语。

弱合流：

- `Y11` 是主指标最大，但 `Interaction <= 0`。
- 或 `Y11` 同时继承 A 的归因/训练优势和 B 的成本优势，但没有明显超加性。
- 可作为工程路线继续推进，但不能强称统一低层原语已经站住。

Pareto 弱合流：

- `Y11` 不是单一主指标最大，但在多指标上非支配。
- 例如成功率略低，但成本、恢复步数或全局回退显著更低。
- 可以继续工程推进，但不能支撑强机制叙事。

失败：

- `Y11` 被 `Y10` 或 `Y01` 支配。
- `Y11` 被 strong typed tools 或 strong retrieval/indexing 追平。
- `Y11` 的优势来自 setup/scaffold、meaningful address 或人工粒度设计。

## 任务选择

第一候选任务族：

- trace-local first-error localization。

它作为第一候选，不是因为它最容易，而是因为它最贴近控制反馈线的核心：

- agent 自己的运行轨迹。
- 错误归因。
- rollback point。
- repair scope。
- trace replay。
- 局部纠偏。
- selector / diagnoser / repair policy 训练样本。

结构化 sanity check：

- JSON。
- AST。
- ledger。
- dependency graph。

这些任务偏结构化，天然有利于状态访问接口。它们适合校准工具、验证实现、切分变量和自动判定，但不应承担 B 分支第一叙事。

这些任务上的正结果只能写成：

> 在强结构局部状态任务上，某种状态访问接口可能更可训练、更可归因或更可纠偏。

半结构后续任务：

- 长文档局部修订。
- 代码仓局部修复。
- 多文件一致性维护。
- 实验日志与分析状态维护。
- 研究笔记状态更新。

如果 trace-local 与结构化 sanity check 都没有稳定信号，不应直接跳到开放世界任务。

`dynamic workspace recovery` 只有在定义补齐后才进入候选任务族。否则它先作为 first-error localization 后续扩展，而不是并列第一任务。

## 当前交付物

下一步实验至少产出：

- 一个协议中立任务定义。
- 一份 A/B 阈值定义。
- 一份 2x2 对照协议。
- 一份实验矩阵，明确 substrate / access mode / resolver / reader / policy / overview / A variable。
- 一份 selector / resolver / reader 拆分说明。
- 一份 trace-local first-error 标签协议。
- 一份 dynamic workspace recovery 是否进入主线的定义草案。
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
