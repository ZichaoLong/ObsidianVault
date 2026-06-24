---
type: memo
status: active
date: 2026-06-17
tags:
  - control-feedback
  - local-state-access
  - active-access
  - tapewalker
---

# Active Foveated Workspace Access

> [!summary] 本页定位
> 本页是控制反馈线 B 分支的机制备忘。它讨论 TapeWalker 式 `move / zoom / load / store / mark` 仿存扫描接口是否有独立研究价值。结论不是“它替代 grep / SQL / LSP / RAG”，而是：它可能只在部分有序、噪声有序、需要智能判断方向的灰色地带有增量。

## 一页版结论

`active foveated workspace access` 的核心是：

> 系统不直接暴露全局状态，而是暴露一个带位置、视野和局部读写能力的 workspace；模型必须通过移动、缩放、读取、标记和局部写入来主动选择反馈信源。

它的根本前提是 `序关系`。

- 如果待查看数据完全没有序关系，这种方法没有特殊优势。
- 如果存在确定性、可形式化、可程序化的序关系，临时生成查找代码、二分、索引、SQL、LSP、tree-sitter 或专用 resolver 会成为强对手。
- 它真正可能发挥作用的地方，是中间灰色地带：状态空间有某种局部或全局序关系，但这种序关系不够干净，不能直接写成确定性查找程序，需要模型基于局部观察做方向判断。

因此，本机制的最稳定位是：

> B 分支下的一个候选接口：`B2: active foveated workspace access`。它检验模型是否能在固定观察预算下，学习一种低成本、可回放、可训练的主动观察策略。

## 与 B 分支 Access Mode 的分层关系

当前讨论中，`active foveated workspace access` 不应被写成 B 分支的总定义。更稳的分层是：

| 层级 | 名称 | 作用 |
| --- | --- | --- |
| B 分支总问题 | 局部状态访问是否有价值 | 检验不把全局状态一次性塞进上下文时，控制、学习、纠偏和成本是否改善。 |
| B0 基础 access mode | `addressed local cell/window access` | 抽象机制层：模型通过 address、cell、window、relation、view 访问局部状态。 |
| 第一实验 substrate | `agent trace / state-transition log` | 实验落点层：把局部访问先落到 agent 轨迹和状态转移日志上。 |
| 第一任务族 | `trace first-error localization / dynamic recovery` | 给定 trace step、局部窗口、导航关系和观察预算，定位首次错误、恢复进度或做局部纠偏。 |
| TapeWalker / active foveated | access policy / view | 在 trace-local 或其他 workspace 上使用 `pos / fov / move / zoom / mark` 做主动视野控制。 |

因此，两种前期建议可以统一：

> 抽象上，B 选择 `addressed local cell/window access`；实验上，第一阶段优先选择 trace substrate 上的 first-error localization / dynamic recovery；TapeWalker 暂时作为 trace-local setting 中的一个顺序 / 视野导航 policy。

这个分层避免两个误解。

第一，trace-local 不是 B 的全部，也不是 B 的 access mode 定义。B 还可以落到代码对象、长文档、JSON、ledger、UI、proof state、dynamic workspace 等 substrate。

第二，TapeWalker 不是 B 的第一定义。TapeWalker 的独特赌注是 `active foveated policy`：在有序、半有序或可导航结构里，模型是否能通过移动视野、缩放、标记和局部判断获得比强 retrieval / resolver 更低成本的访问轨迹。

## Trace-Local 作为第一实验入口

> [!decision] 暂存判断
> 当前判断是：`trace-local first-error localization / dynamic recovery` 应升级为 A/B 主线的候选第一任务族，但暂不直接改写主线文档。更稳的安排是把它作为 primary candidate task family，把 JSON / AST / ledger 保留为 sanity check 和低风险工程验证。

若要推进 B，第一阶段更适合选择：

> 在 `agent trace / state-transition log` 这个 substrate 上，用 B0 的 `addressed local cell/window access` 定位首次错误、恢复进度、做局部纠偏。

理由是：

- 它最贴近控制反馈主线，对象就是 agent 的运行过程，而不是任意结构化数据。
- 它天然连接 `first-error localization / rollback / repair / verify`。
- 它比代码符号定位更不容易被 LSP、tree-sitter、grep 完全吸收。
- 它比普通长文档语义搜索更容易构造验证信号和失败标签。
- 它能同时测试 TapeWalker 式顺序视野访问，但不把 B 绑定死在一维 tape 上。

这意味着主线若后续调整，可以从原先的“结构化状态任务优先”改成：

```text
Primary candidate task family:
  trace-local first-error localization / dynamic recovery

Sanity check task family:
  JSON / AST / ledger local edit

Later expansion:
  long document turning point
  code/debug trace
  UI / foveated navigation
```

这里不是否定 JSON / AST / ledger。它们仍然有价值，但价值更像 sanity check：验证局部 cell/window access、显式状态事件、回放和 commit/rollback 机制能否跑通。它们不应承担最强叙事，因为任务结构太容易被 parser、query、DSL 或专用工具吸收。

### 任务定义：Trace-Local First-Error Localization

`trace-local first-error localization` 的最小任务是：

> 给定一条已经失败的 agent trace，在有限局部观察预算下，定位第一次把任务推进到错误轨道上的决策、假设、工具调用、状态更新或 patch。

它不是让模型重新完成原任务，而是让模型读一个已经发生过的运行轨迹，并回答：

```text
first_bad_step = ?
```

这里的 `first_bad_step` 不一定是第一次显式报错的位置。

普通 log debugging 往往找：

```text
step 157: exception occurred
```

first-error localization 要找：

```text
step 083: wrote invalid state
step 157: exception is only a downstream symptom
```

因此它更贴近控制反馈线的核心对象：

- 错误归因。
- rollback point。
- repair scope。
- trace replay。
- 局部纠偏。
- selector / diagnoser / repair policy 的训练样本。

### 为什么优先做 Trace

做 trace-local first-error localization 的理由不是它最容易，而是它最贴近控制反馈线要填补的裂缝：

> 如果系统不能在自己的运行轨迹中定位“第一次走错的地方”，就很难谈可归因、可回放、局部纠偏、rollback 和训练数据飞轮。

它的说服力来自三点。

第一，对象就是 agent 的运行过程。

JSON、AST、ledger 是外部结构化对象。trace 是 agent 自己的控制过程、反馈过程和状态转移过程。若目标是研究控制反馈，trace 比一般结构化数据更贴近主线。

第二，它天然连接 A / B / TapeWalker / peripheral-like overview。

| 方向 | trace first-error localization 的作用 |
| --- | --- |
| A 分支 | 若 trace 有显式状态事件，是否更容易定位 first error。 |
| B 分支 | 若只能局部读 trace，局部访问接口是否降低观察成本。 |
| TapeWalker | 顺序 / 视野 / zoom / mark 是否帮助在 trace 中导航。 |
| Peripheral-like overview | 低语义 bucket features 是否提供方向信号。 |
| 纠偏 | first error 是否能导出更好的 rollback point 和 repair scope。 |
| 训练 | first-error trace 是否能转成 selector / diagnoser / repair policy 样本。 |

第三，它有自然顺序和局部因果结构，但不总能被关键词或确定性索引吃掉。

JSON 查询、AST 定位、SQL 查询、代码符号跳转常常有强 parser / query / LSP / tree-sitter 对手。trace first error 可能没有稳定关键词，且第一次错误通常早于最终显性失败。这给局部访问、顺序导航和 overview 留出更真实的实验空间。

### 与其他任务的对比

| 任务类型 | 优点 | 缺点 | 对主线意义 |
| --- | --- | --- | --- |
| JSON / ledger / AST 局部修改 | 易构造、易验证、ground truth 清楚 | 太结构化，容易被 parser / query / DSL 吃掉 | 适合 sanity check，不足以支撑强叙事。 |
| 代码符号定位 / 修复 | 现实性强，有工程价值 | LSP、tree-sitter、grep、测试、debugger 很强 | 适合后期强基线，不适合作第一信号。 |
| 长文档转折点定位 | 接近阅读和研究任务，有自然顺序 | 标注主观，ground truth 难稳定 | 适合 B2 / TapeWalker 后续扩展。 |
| UI / 视觉导航 | 接近 peripheral vision 类比 | computer use 是强基线，实验噪声大 | 适合对标，不适合第一步。 |
| trace first-error localization | 贴近 agent 控制、归因、rollback、纠偏 | 构造和标注要谨慎 | 最适合连接 A、B、TapeWalker 和 peripheral-like overview。 |

因此，JSON / AST / ledger 更适合作为低风险 sanity check；trace first-error localization 更适合作为第一类有主线说服力的任务。

### 具体例子

代码 agent 错误修复 trace：

```text
step 01: read failing test
step 02: inspect function parse_config
step 03: infer bug is missing default value
step 04: patch parse_config
step 05: run tests -> same failure
step 06: inspect config_loader
step 07: patch caller
step 08: tests now fail elsewhere
step 09: rollback partial patch
step 10: final failure
```

可能的 first error 是：

```text
step 03: 错误归因 bug 位置
```

而不是 `step 05` 的 test failure。

数据分析 agent trace：

```text
step 01: load sales table
step 02: filter region = US
step 03: join customer table
step 04: mistakenly use inner join instead of left join
step 05: aggregate revenue
step 06: result looks too low
step 07: try changing date filter
step 08: produce wrong report
```

first error 是：

```text
step 04: 错误 join 类型导致状态被破坏
```

研究 / 文档 agent trace：

```text
step 01: read problem statement
step 02: read paper abstract
step 03: misread "requires online setting" as "offline setting"
step 04: design wrong comparison
step 05: collect irrelevant references
step 06: write wrong summary
```

first error 是：

```text
step 03: 约束误读
```

这些例子都不是单纯找最终报错，而是找后续错误链条的起点。

### 最小构造方式

第一阶段可以采用半合成 trace：

> 真实 agent / task template + 程序化注入错误 + 可验证最终失败 + 少量人工校验 first-error label。

这比纯人工玩具任务更真实，也比完全真实 trace 更容易获得 ground truth。

可测输出：

```text
mark(first_bad_step)
```

可选输出：

```text
confidence
short_reason
suggested_rollback_scope
```

第一版主指标：

- 是否命中 first bad step。
- 与 first bad step 的距离。
- observation tokens。
- read_window 次数。
- navigation steps。
- false negative rate。
- 是否被后续显性报错误导。
- 走错方向后是否能恢复。

### 攻击面

这类任务也不是免费胜场。

- first error 有时不可唯一标注。
- 后续失败可能来自多个错误叠加。
- 半合成 trace 可能太干净。
- 真实 agent trace 标注成本高。
- 如果 overview 给出太强的失败密度、异常分数或 likely-error region，就会退化成 analyzer。
- 如果任务只是在 trace 中找显式 error keyword，就会被 grep / BM25 吃掉。

因此第一阶段要避免两种极端：

- 不要只做显式报错定位。
- 不要让 overview / analyzer 直接告诉模型目标位置。

第一版接口可以收缩为：

```text
read_budget()
read_window(trace_step_id, radius)
navigate(trace_step_id, relation, budget)
zoom(trace_range, level)
mark(trace_step_id, label)
```

其中 `relation` 的 MVP 应只保留最小顺序关系：

```text
prev / next
```

可以在第二个 condition 中再加入弱层级关系：

```text
parent / child
```

`cause_candidate / effect_candidate` 不应进入第一版 B-only。它们很容易包含诊断、归因或强 resolver 信号，应作为 `topology-aware / A+B / generated analyzer` 条件单独测试。

`overview()` 也不应默认进入 MVP。第一版只提供 `read_budget()`：

```text
trace_length
current_marks
remaining_budget
```

如果需要 overview，应拆成单独条件：

| 条件 | 允许内容 | 解释风险 |
| --- | --- | --- |
| no overview | 只知道长度、当前位置、预算 | 最干净，但方向信号弱 |
| generic overview | event type histogram、粗粒度 chunk 边界 | 可能已经是派生索引 |
| semantic overview | checkpoint summary、异常分数、失败密度 | 很可能偷走 selector / resolver 贡献 |

只有 no overview / generic overview 能作为 B-only 的早期条件。semantic overview 必须计入构造成本，并对标 BM25、vector、generated analyzer。

## B-Only 与 A+B 的拆分

trace-local setting 很容易和 A 分支的显式状态语义混在一起。为了让结果可解释，第一版应强制拆成两层：

```text
B-only:
trace event 只有 step_id / timestamp / bounded raw action / bounded raw observation / bounded raw output
reader 只能返回受 token/cell budget 限制的 event window
接口只有 read_budget / read_window / navigate(prev,next) / zoom / mark

A+B:
trace event 额外有 typed event / state delta / invariant / verify result / diagnose label / rollback scope
接口允许 diagnose / verify / repair / commit
```

B-only 中的 `raw observation / raw output` 不是完整全局上下文，而是被 cell/window 化后的受限局部内容。否则它会退回 full-context 或大 chunk baseline。

如果 B-only 已经有效，说明局部访问本身有价值。

如果只有 A+B 有效，说明收益可能来自显式事件语义，而不是局部访问本身；这仍有价值，但应归入 A+B 合流，而不是归入 TapeWalker 或纯 B。

## 独立成败关系

B 分支、trace-local setting 与 TapeWalker 可以独立成功或失败。

| 结果 | 含义 |
| --- | --- |
| B 成功，TapeWalker 失败 | 统一局部状态访问接口有价值，但有效 resolver 可能是 BM25、vector、LSP、tree-sitter、SQL 或 topology-aware trace access，而不是 active foveated 扫描。 |
| TapeWalker 成功，B 总体信号不明显 | 某些有序 / 半有序 / 可导航任务里 active foveated policy 有价值，但不能推出局部状态访问接口普遍有优势。 |
| 两者都成功 | B 提供总框架，TapeWalker 成为其中一个高价值 access policy。 |
| 两者都失败 | 强 Agent + typed tools + indexing / retrieval / generated analyzer 可能已经吸收这部分收益，需要转向显式状态语义、训练接口或其他机制。 |

当前更稳的主张不是：

> TapeWalker 证明 B。

而是：

> TapeWalker 是 B 分支下高风险、高辨识度的 access policy 候选；如果 trace-local first-error localization 或 dynamic workspace recovery 中出现稳定信号，它才值得进入主线。

## 与 TapeWalker 的关系

TapeWalker 当前实现已经包含这类接口的雏形：

- `pos`：当前读写头位置。
- `fov`：当前视野大小。
- `move / step_forward / step_backward / jump`：移动读写头。
- `zoom`：放大或缩小视野。
- `load / load_full / load_range`：读取当前位置附近或指定范围。
- `store / insert / delete / append`：局部写入和结构修改。
- `mark / goto_mark`：书签和跳转。
- `search`：保留传统关键词搜索作为 fallback。

这不是纯 `Load/Store`，而是：

> 带读写头、可变视野、局部观察、局部写入、书签和检索 fallback 的 active workspace interface。

## 复杂度边界

`log(n)` 访问复杂度不是自动成立的。

它依赖几个条件：

- 状态空间有顺序、层级或可比较结构。
- 每次局部观察能给出方向性信号。
- 模型对方向信号的判断足够可靠。
- 接口允许跳步、缩放或层级访问。
- 目标不是完全无结构的 needle。

如果目标谓词是单调的，或状态空间有明确比较关系，可以接近二分、指数搜索、跳表、B-tree 这类复杂度直觉。

但如果目标是任意自然语言片段、任意错误、任意语义关系，而且没有 key、没有 schema、没有索引，那么最坏情况仍接近线性扫描。此时所谓“主动扫描”只能是 heuristic search，而不是理论 `O(log n)`。

## 强基线覆盖

这条线必须承认，现代强 Agent 已经覆盖了大量弱版本。不能把“支持局部读取”“支持移动视野”“支持按需查询”“支持局部 patch”当作新贡献。

| 已覆盖能力 | 现有强 Agent / 工具链形态 | 吸收程度 | 对 `active foveated` 的含义 |
| --- | --- | --- | --- |
| 精确关键词定位 | `grep` / `rg` / shell search / log search | 高 | 只要目标有稳定关键词，主动扫描几乎没有优势。 |
| 语义检索 | BM25 / vector search / hybrid retrieval / RAG | 高 | 如果任务能写成自然语言 query，语义检索是强基线。 |
| 结构化查询 | SQL / database index / structured API / resource templates | 高 | 表格、数据库、强 schema 任务不应作为主战场。 |
| 代码符号导航 | LSP / tree-sitter / code index / editor jump / call graph | 高 | 代码定位任务必须对标这些，不能只对标全文上下文。 |
| 局部读写 | `read_file(path, range)` / local patch / diff / checkpoint / rollback | 高 | 局部读写本身已经是强 Agent 正常能力。 |
| 按需暴露反馈入口 | deferred tools / MCP resources / tool search / resource discovery | 中高 | “先生成 query，再暴露候选反馈源”已被工程吸收。 |
| 长上下文递归管理 | compact / summarize / recursive context management / RLM | 中高 | 长上下文局部处理不能只对标 full-context baseline。 |
| UI / 视觉空间访问 | screenshot / crop / OCR / accessibility tree / computer-use agent | 中 | 视觉或 UI foveation 有自然类比，但 computer-use 是强对手。 |
| 确定性序关系查找 | generated search code / binary search / parser / custom resolver | 高 | 若序关系可形式化，临时生成查找程序通常更强。 |

因此，TapeWalker 式机制最稳的剩余命题不是：

> 现有 Agent 缺少局部访问。

而是：

> 在有序但不可完全程序化的灰色状态空间里，模型能否学习一种主动视野访问策略，在固定观察预算下比强 resolver / 强 retrieval / generated search code 更低成本、更可回放、更可训练，或更适合局部纠偏。

## 主要攻击面与胜率判断

这里的“胜率”是当前研究先验，不是统计结论。它只用于决定优先级：先把高胜率场景做成可输实验，再考虑是否进入主线。

| 场景 / 攻击面 | 强反方解释 | 防守条件 | 当前胜率判断 |
| --- | --- | --- | --- |
| 有精确关键词、稳定符号、稳定 key | `grep / rg / LSP / SQL` 直接解决，主动扫描只是低效替代。 | 只作为负控任务，不作为正面证据。 | 低 |
| 有确定性可比较谓词 | `binary_search(predicate)` 或 generated search code 更直接。 | 必须证明谓词不能稳定形式化，局部线索需要语义判断。 | 低 |
| 普通语义定位 | BM25 / vector / hybrid retrieval 足够强。 | 任务要让一次 query 不稳定，局部窗口能提供方向信号。 | 中低 |
| 长文档观点转折 / 定义变化 | 长上下文、RAG、RLM 可能已能处理。 | 需要无稳定关键词、跨段落语义漂移、局部观察可判断方向。 | 中低到中 |
| 长 agent trace 首次错误定位 | trace 有时间 / 因果顺序，错误点可能没有关键词，局部观察可能提供方向信号。 | 必须对标 full trace grading、RLM、检索、线性扫描和 generated analyzer。 | 中到中高 |
| dynamic workspace recovery | compact / checkpoint / replay 已很强，但恢复“当前进度”可能需要局部导航。 | 必须证明局部访问比重新 compact、全局回读或 checkpoint replay 更省。 | 中 |
| UI / 表格 / 二维空间导航 | computer-use agent、OCR、accessibility tree 是强对手。 | 适合做二维 foveation，但要限制观察预算并计入视觉工具成本。 | 中 |
| 代码仓定位 / 修复 | LSP、tree-sitter、code index、测试和编辑器跳转非常强。 | 只有在跨文件语义状态、无稳定符号、trace/debug 顺序任务上才有机会。 | 低到中 |
| 结构化 JSON / AST / ledger | 任务天然偏向结构化接口，也容易被 query / parser 吸收。 | 可用于机制 sanity check，但结论必须收缩。 | 低 |
| selector 轨迹训练 | 即使推理时不总赢，主动访问轨迹可能成为训练数据。 | 需要证明轨迹能提升 selector imitation、长度泛化或局部修复。 | 中到中高 |

当前最值得优先试的不是代码符号定位、JSON 或 SQL 类任务，而是：

> `trace first-error localization` 与 `dynamic workspace recovery`。

原因是它们同时满足四点：

- 有自然序关系。
- 不能总是靠稳定关键词解决。
- 局部窗口可能给出方向信号。
- 结果可连接到控制反馈线的错误归因、局部修复和 selector 训练。

## 参考与对标来源

本节给出上面两张表对应的参考来源。它们不是为了证明 `active foveated` 不值得做，而是为了明确：哪些能力已经是强基线，实验必须把它们放进对照组。

### 强 Agent / 工具链基线

- 精确文本搜索：[`ripgrep`](https://github.com/BurntSushi/ripgrep) 是现代命令行全文搜索强基线。
- BM25 / 关键词检索：[Lucene BM25Similarity](https://javadoc.io/doc/org.apache.lucene/lucene-core/latest/org/apache/lucene/search/similarities/package-summary.html) 与 [Azure AI Search BM25 配置文档](https://learn.microsoft.com/en-us/azure/search/index-ranking-similarity) 可作为 BM25 工程化参考。
- 向量检索：[Faiss 官方文档](https://faiss.ai/index.html)、[Faiss paper](https://arxiv.org/abs/2401.08281) 说明高效向量相似搜索已经是成熟基础设施。
- 数据库索引：[PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html) 与 [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html) 是结构化查询 / 索引强基线。
- 代码符号导航：[Language Server Protocol specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) 与 [Tree-sitter 官方文档](https://tree-sitter.github.io/) 是代码定位、增量解析和编辑器跳转的强对手。
- Agent 工具与资源暴露：[Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-06-18)、[MCP Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources) 说明工具、资源、文件、数据库 schema 等上下文可以被标准化暴露给模型。
- Agent runtime / tracing：[OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents) 与 [OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/) 说明 typed tools、state、approvals、tool calls 和 trace 已是强 Agent runtime 的常规能力。
- UI / computer use：[OpenAI Computer Use](https://developers.openai.com/api/docs/guides/tools-computer-use)、[OpenAI Computer-Using Agent](https://openai.com/index/computer-using-agent/)、[Anthropic Computer Use Tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool) 是视觉 / UI foveation 的强对手。
- 长上下文递归管理：[Recursive Language Models](https://arxiv.org/abs/2512.24601)、[RLM project page](https://alexzhang13.github.io/blog/2025/rlm/)、[RLM GitHub](https://github.com/alexzhang13/rlm) 说明长上下文可以被外部化为可 inspect / decompose / recursive call 的环境。
- 结构化递归运行时：[λ-RLM paper](https://arxiv.org/abs/2603.20105)、[λ-RLM GitHub](https://github.com/lambda-calculus-LLM/lambda-RLM) 说明 typed functional runtime 也是长上下文局部处理的强对照。
- 本仓库内吸收表：[[10-control-feedback-token-instruction/reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]] 汇总了 Codex、OpenAI Agents SDK、MCP、LangGraph 等对 A/B 弱版本的吸收判断。

### Active / Foveated 机制背景

- [Recurrent Models of Visual Attention](https://arxiv.org/abs/1406.6247)：经典视觉注意力模型，通过自适应选择局部区域降低大图像处理成本，是 `foveated access` 的重要相邻思想来源。
- [Multiple Object Recognition with Visual Attention](https://arxiv.org/abs/1412.7755)：展示模型可学习关注输入图像中的局部区域并识别多个对象。
- [Foveation in the Era of Deep Learning](https://proceedings.bmvc2023.org/703/)：更直接讨论 deep learning 时代的 foveated sensing / active attending。

### 对本备忘的直接约束

这些参考共同给出三个约束：

- 如果任务可由 `grep / BM25 / vector / SQL / LSP / tree-sitter / generated code` 稳定解决，`active foveated` 不应声称机制优势。
- 如果任务只是长上下文局部读取，必须对标 RLM / λ-RLM / recursive context management。
- 如果任务是视觉或 UI 空间导航，必须对标 computer-use agent，而不是只对标全文上下文或随机扫描。

## 真正可能有价值的灰色地带

这类任务需要满足三个条件。

第一，存在某种序关系。

可能是时间顺序、空间顺序、论证顺序、执行顺序、状态演化顺序、trace 顺序、文档结构顺序、UI 空间顺序。

第二，序关系不是完全确定可程序化的。

如果能直接写成 `binary_search(predicate)`，那么生成代码或专用算法是强对手。这里需要的是局部线索带有噪声、需要语义判断、方向信号不稳定、不同区域结构不同。

第三，局部观察能提供方向信号。

如果看一个窗口无法判断下一步往哪里走，主动访问就退化成随机游走或线性扫描。

典型候选：

- 长 agent trace 中定位首次错误决策。
- 长篇文档中定位观点转折、定义变化、立场冲突或论证断裂点。
- 物理 / 具身环境中的空间搜索和局部导航。
- UI / 表格 / 图形界面中的视野缩放和局部定位。
- 动态 workspace 中恢复中断任务，找回当前进度和最近可用状态。
- 日志或执行轨迹中查找第一次 invariant break，但没有稳定关键词。

## 哲学价值

从务虚角度看，这个机制有两个吸引力。

第一，它是通用回退机制。

当没有现成 key、schema、index、resolver 时，系统仍能通过移动视野、局部观察、标记和逐步修正来工作。这类似人眼扫描、具身探索、调试过程和阅读长文。

第二，现实世界往往不是完全无序的。

许多任务“似乎”至少局部有序：

- 物理世界有空间连续性。
- 具身行动有时间和位置连续性。
- 长文本有段落、主题、论证推进。
- 代码执行有调用栈、控制流、依赖图。
- Agent 轨迹有决策和状态演化顺序。

这些序关系不总是足以构造确定性索引，但可能足以支持智能体通过局部观察逐步逼近目标。

## 务实裁决

最终价值不应靠哲学直觉裁决，而要靠任务强度。

- 如果只能在人工玩具任务上赢，它就是一份普通研究或实验 scaffold。
- 如果能在强 resolver 不容易覆盖的真实任务上形成稳定优势，它才可能成为控制反馈线 B 分支的重要机制。
- 如果加入 `grep / BM25 / vector / SQL / LSP / RLM / generated search code` 后优势消失，就应承认它被现有 Agent 工程吸收。
- 如果它能产生高质量 selector 轨迹，用于训练局部访问策略，那么它的价值会从“推理时工具”上升到“数据飞轮接口”。

最关键的实验问题是：

> 能否找到一类足够真实、足够有序、但又无法被确定性 resolver 轻易吃掉的任务？

## 建议实验切口

优先任务：

- `trace first-error localization`：给长 agent trace，定位首次导致最终失败的局部决策。
- `semantic turning-point search`：在长文档中定位观点、定义、目标或约束发生变化的位置。
- `dynamic workspace recovery`：任务被 compact / interrupt 后，靠局部 workspace 找回进度并继续。
- `no-good-key log debugging`：日志里没有稳定关键词，需要通过局部语义判断 invariant 是否破坏。
- `foveated UI/table navigation`：二维空间中通过缩放和移动定位目标区域。

必须包含的强基线：

- full context。
- random / linear scan。
- generated deterministic search code。
- grep / BM25 / vector retrieval。
- SQL / index / LSP / tree-sitter，若任务适用。
- RLM / recursive context management，若任务是长上下文。

主指标：

- 成功率。
- observation tokens。
- tool calls。
- wall-clock。
- false negative rate。
- 平均定位步数。
- 局部修复成功率。
- workspace 长度 scaling curve。
- selector 轨迹是否可监督训练。

## 当前判断

这条线值得保留，但应保持收缩：

> `active foveated workspace access` 是 B 分支的候选机制，不是 `Load/Store` 的最终证明。它的核心赌注是：许多现实任务处在“完全无序”和“确定性可索引”之间，存在需要智能判断的有序灰色地带；在这些任务里，主动视野访问可能比一次性 query 或强 resolver 更可控、更可训练、更适合局部纠偏。

如果找不到这类任务，它应降级为 TapeWalker 的历史动机和实验 scaffold。
