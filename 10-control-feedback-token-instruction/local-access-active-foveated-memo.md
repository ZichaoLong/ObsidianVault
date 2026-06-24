---
type: memo
status: draft
date: 2026-06-24
tags:
  - control-feedback
  - local-state-access
  - active-access
  - tapewalker
  - trace-local
  - memo
---

# Local Access and Active Foveated Memo

> [!summary] 本页定位
> 本页是控制反馈线 B 分支的非主线总备忘，收敛此前关于 `trace-local`、TapeWalker / active foveated access、peripheral-like overview、computer use、可导航结构与 learned noisy directional access 的独立讨论。它暂不改写主线，只作为后续合并主线前的设计池。

## 一页版结论

B 分支的总问题不是 TapeWalker，也不是某一种具体 `load()` 形态，而是：

> 在不把全局状态一次性暴露给模型的前提下，局部状态访问接口是否让控制、学习、纠偏和成本更好。

当前较稳的分层是：

| 层级 | 名称 | 当前判断 |
| --- | --- | --- |
| B 总问题 | 局部状态访问是否有价值 | 检验局部可见、主动选择反馈信源，是否比全局上下文、强 retrieval 或强 runtime 更可控。 |
| B0 基础 access mode | `addressed local cell/window access` | 最小局部访问层：address、cell、window、relation、view、budget。 |
| 第一实验 substrate | `agent trace / state-transition log` | 优先把局部访问落到 agent 自己的运行轨迹上。 |
| 第一任务族 | `trace-local first-error localization / dynamic recovery` | 在局部观察预算下定位首次错误、恢复进度或做局部纠偏。 |
| Access policy | linear scan / retrieval jump / topology-aware / TapeWalker | 比较不同访问策略，不把 B 的成败绑定到 TapeWalker。 |
| B2 | active foveated workspace access | 高风险、高辨识度候选：`pos / fov / move / zoom / load / mark / store`。 |
| Peripheral-like overview | B2 消融项 | 不进入 B0。只在 TapeWalker / B2 中测试低保真方向信号。 |
| Future sensor | learned sensor / encoder | 远期路线：用任务无关感知层替代纯 token/cell overview。 |

因此，当前更稳的推进口径是：

> 抽象上，B 选择 `addressed local cell/window access`；实验上，第一阶段优先选择 trace substrate 上的 first-error localization / dynamic recovery；TapeWalker 暂时作为 trace-local setting 中的一个顺序 / 视野导航 policy。

## B 分支的分层

### B 不是 TapeWalker

TapeWalker 是 B 分支下的候选 access policy，不是 B 分支本身。

如果把 B 定义成 TapeWalker，那么实验风险会过早集中到一维 tape、`move/zoom/load`、下采样策略和具体实现细节上。一旦 TapeWalker 输给 BM25、vector、LSP、SQL、RLM 或 generated analyzer，就容易误判为“局部状态访问整体失败”。

更稳的定义是：

```text
B:
  hidden global state
  local observation budget
  model chooses what to inspect next
  model can mark / verify / repair / rollback when allowed
```

在这个定义下，TapeWalker 只是其中一种策略：

```text
Policy:
  current position + field of view
  move / zoom / load / mark
  use local observations to decide next fixation
```

### B0 的最小接口

B0 应保持干净，不引入过强 overview 或 analyzer。

```text
read_budget()
read_window(address, radius)
navigate(address, relation, budget)
zoom(range, level)
mark(address, label)
```

第一版 `relation` 应收缩到最小：

```text
prev / next
```

第二阶段可以加入弱层级关系：

```text
parent / child
```

`cause_candidate / effect_candidate` 不应进入第一版 B-only。它们很容易包含诊断、归因或强 resolver 信号，应作为 `topology-aware / A+B / generated analyzer` 条件单独测试。

### B-Only 与 A+B 的拆分

trace-local setting 很容易和 A 分支的显式状态语义混在一起，因此第一版应强制拆分：

```text
B-only:
  trace event 只有 step_id / timestamp / bounded raw action / bounded raw observation / bounded raw output
  reader 只能返回受 token/cell budget 限制的 event window
  接口只有 read_budget / read_window / navigate(prev,next) / zoom / mark

A+B:
  trace event 额外有 typed event / state delta / invariant / verify result / diagnose label / rollback scope
  接口允许 diagnose / verify / repair / commit
```

如果 B-only 已经有效，说明局部访问本身有价值。

如果只有 A+B 有效，说明收益可能主要来自显式事件语义，而不是局部访问本身；这仍有价值，但应归入 A+B 合流，不应归入纯 B 或 TapeWalker。

## Trace-Local First-Error Localization

### 任务定义

`trace-local first-error localization` 的最小任务是：

> 给定一条已经失败的 agent trace，在有限局部观察预算下，定位第一次把任务推进到错误轨道上的决策、假设、工具调用、状态更新或 patch。

输出可以先收缩为：

```text
mark(first_bad_step)
```

可选输出：

```text
confidence
short_reason
suggested_rollback_scope
```

它不是找第一次显式报错的位置。

普通 log debugging 可能找：

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

### 为什么优先选择 Trace

`trace-local first-error localization / dynamic recovery` 比 JSON、AST、ledger 更适合作为第一类有主线说服力的任务。

| 任务类型 | 优点 | 缺点 | 对主线意义 |
| --- | --- | --- | --- |
| JSON / ledger / AST 局部修改 | 易构造、易验证、ground truth 清楚 | 太结构化，容易被 parser / query / DSL 吃掉 | 适合 sanity check，不足以支撑强叙事。 |
| 代码符号定位 / 修复 | 现实性强，有工程价值 | LSP、tree-sitter、grep、测试、debugger 很强 | 适合后期强基线，不适合作第一信号。 |
| 长文档转折点定位 | 接近阅读和研究任务，有自然顺序 | 标注主观，ground truth 难稳定 | 适合 B2 / TapeWalker 后续扩展。 |
| UI / 视觉导航 | 接近 peripheral vision 类比 | computer use 是强基线，实验噪声大 | 适合对标，不适合第一步。 |
| trace first-error localization | 贴近 agent 控制、归因、rollback、纠偏 | 构造和标注要谨慎 | 最适合连接 A、B、TapeWalker 和 peripheral-like overview。 |

选择 trace 的理由不是它最容易，而是它最贴近控制反馈线要填补的裂缝：

> 如果系统不能在自己的运行轨迹中定位“第一次走错的地方”，就很难谈可归因、可回放、局部纠偏、rollback 和训练数据飞轮。

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

第一版主指标：

- 是否命中 first bad step。
- 与 first bad step 的距离。
- observation tokens。
- `read_window` 次数。
- navigation steps。
- false negative rate。
- 是否被后续显性报错误导。
- 走错方向后是否能恢复。

### 攻击面

这类任务不是免费胜场。

- first error 有时不可唯一标注。
- 后续失败可能来自多个错误叠加。
- 半合成 trace 可能太干净。
- 真实 agent trace 标注成本高。
- 如果 overview 给出太强的失败密度、异常分数或 likely-error region，就会退化成 analyzer。
- 如果任务只是在 trace 中找显式 error keyword，就会被 grep / BM25 吃掉。

因此第一阶段要避免两种极端：

- 不要只做显式报错定位。
- 不要让 overview / analyzer 直接告诉模型目标位置。

## TapeWalker / Active Foveated Workspace Access

### 核心命题

`active foveated workspace access` 的核心是：

> 系统不直接暴露全局状态，而是暴露一个带位置、视野和局部读写能力的 workspace；模型必须通过移动、缩放、读取、标记和局部写入来主动选择反馈信源。

它的根本前提是 `序关系`，但更准确的说法是 `可导航结构`。

- 如果待查看数据完全没有序关系，这种方法没有特殊优势。
- 如果存在确定性、可形式化、可程序化的序关系，临时生成查找代码、二分、索引、SQL、LSP、tree-sitter 或专用 resolver 会成为强对手。
- 它真正可能发挥作用的地方，是中间灰色地带：状态空间有某种局部或全局序关系，但这种序关系不够干净，不能直接写成确定性查找程序，需要模型基于局部观察做方向判断。

因此，本机制的最稳定位是：

> B 分支下的一个候选接口：`B2: active foveated workspace access`。它检验模型是否能在固定观察预算下，学习一种低成本、可回放、可训练的主动观察策略。

### TapeWalker 的接口形态

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

### 与 B 的独立成败关系

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

### 复杂度边界

`log(n)` 访问复杂度不是自动成立的。

它依赖几个条件：

- 状态空间有顺序、层级或可比较结构。
- 每次局部观察能给出方向性信号。
- 模型对方向信号的判断足够可靠。
- 接口允许跳步、缩放或层级访问。
- 目标不是完全无结构的 needle。

如果目标谓词是单调的，或状态空间有明确比较关系，可以接近二分、指数搜索、跳表、B-tree 这类复杂度直觉。

但如果目标是任意自然语言片段、任意错误、任意语义关系，而且没有 key、没有 schema、没有索引，那么最坏情况仍接近线性扫描。此时所谓“主动扫描”只能是 heuristic search，而不是理论 `O(log n)`。

## 可导航结构与 Workspace 拓扑

### 工作形式化

可以把可导航 workspace 写成：

```text
Navigable Workspace = (S, N, A, O, V, C, H)
```

其中：

- `S`：状态单元，例如 workspace cell、proof state、code object、trace step。
- `N`：邻接关系或可达关系，也就是拓扑。
- `A`：可执行动作，例如 move、zoom、jump、read、write、verify。
- `O`：局部观察函数，决定当前位置和当前视野能看到什么。
- `V`：验证器，例如 test、type check、proof check、invariant。
- `C`：访问成本，例如 token、tool call、wall time、setup cost。
- `H`：层级、摘要或 coarse-to-fine 结构。

对主动访问真正有用的是 `N + O + V + H`。

- 只有图，没有局部观察信号，不够。
- 只有局部观察，没有验证，容易走错。
- 只有验证，没有导航，可能退化成穷举。
- 只有层级摘要，没有回到原状态的引用，也会变成不可纠偏的总结。

因此，实验不能只报告“有 workspace”。它应报告：

- `N` 是什么拓扑。
- `O` 返回什么局部信号。
- `V` 是否能验证局部结论。
- `H` 是否由人工构造，还是模型 / 系统生成。
- `C` 是否计入构造和维护成本。

### 结构的常见形式

| 结构形式 | 例子 | 对主动访问的意义 |
| --- | --- | --- |
| 顺序结构 | 时间线、文本段落、trace step、数组 | 可前进、后退、二分、定位转折点 |
| 空间 / 度量结构 | 2D UI、地图、图像、人眼视野 | 可移动、缩放、局部扫描 |
| 层级结构 | 文件树、模块、章节、证明分层、OS 层次 | 可 coarse-to-fine 搜索 |
| 图结构 | 调用图、依赖图、概念图、证明依赖图、数据流图 | 可沿边扩展、回溯、找邻域 |
| 状态转移结构 | 程序执行、agent trace、proof state、workflow | 可定位首次错误、局部回滚 |
| 逻辑 / 验证结构 | 定理、引理、类型、测试、invariant | 可局部验证、局部纠偏 |
| 抽象-细化结构 | 摘要到原文、spec 到代码、lemma 到 proof | 可先看粗粒度，再放大细节 |

这些结构可以天然存在，也可以由系统主动构造。

天然结构：

- 文本段落顺序。
- 文件系统层级。
- 代码 AST。
- 函数调用图。
- 程序执行 trace。
- 数学证明依赖。
- UI 空间布局。

构造结构：

- bookmark。
- 摘要节点。
- 分段索引。
- 验证点。
- checkpoint。
- subgoal tree。
- error attribution graph。
- trace compaction hierarchy。

因此，更准确的牵引不是“结构普遍存在”，而是：

> 现实任务中存在大量可导航结构；有些是天然的，有些需要系统通过标记、摘要、分层、验证点主动构造出来。

### Tape 作为通用 substrate 的边界

只要支持 `Load/Store + 间接寻址`，tape 理论上可以编码任何有限结构。

图、树、AST、proof graph、调用图、堆对象、文件系统、状态机，都可以放在线性地址空间上。真实计算机也常是这样：底层是线性地址空间，上层实现链表、树、图、对象系统、文件系统、数据库和虚拟内存。

因此，Tape 的强点是 `可表达性` 和 `统一性`。

但这只是“能表达”，不等于“好导航”。

Tape 的缺点：

- 自然邻接关系可能被编码破坏。例如 graph 邻居在 tape 上可能相隔很远。
- `left / right` 方向太弱，不能自然表达 `caller / callee`、`parent / child`、`definition / reference`、`producer / consumer`。
- 如果依赖 resolver 找地址，复杂性被转移到 resolver。
- 如果依赖 hand-crafted layout，收益可能来自人工布局，而不是模型访问策略。
- meaningful address / typed address 可能偷渡大量语义。
- 对真实任务可能不如原生结构视图高效。

因此，Tape 不是错误的，但不能把它当成天然最优 topology。

更准确的表述是：

> Tape 是通用 substrate，不是必然最优 topology。

### 稳定 opcode 与 topology-aware operands

如果把结构从一维 tape 推广到图、树、层级、UI 空间、proof state、代码对象，那么“方向”也必须一般化。

但动作集不能无限一般化。否则会牺牲 `Token = Instruction` 最重要的东西：

- 稳定事件语义。
- 可训练性。
- 可回放性。
- 可归因性。

更稳的设计不是“为每种结构发明一套方向”，而是：

> 保持少量稳定控制原语，把结构差异放进 typed operands、topology metadata、resolver 或 view 里。

例如：

```text
read(address, view)
write(address, delta)
navigate(address, relation, budget)
zoom(address, level)
mark(address, label)
verify(scope, invariant)
commit(tx)
rollback(tx)
```

这有一个清楚的取舍：

- 少量 opcode + typed operands：更统一、更可训练、更可回放，但需要 resolver / runtime 解释 relation。
- 大量结构专用 opcode：更贴近原生结构、更短路径，但训练分散、语义碎片化、工程复杂。

因此，控制反馈线若要保持可训练性和显式状态语义，应优先押注：

> stable small opcode set + topology-aware operands。

而不是：

> unbounded topology-specific action set。

### Hybrid：Tape Log + Topology Views

一个较稳的 hybrid 方案是：

> canonical state / event log 保持 tape-like；模型访问时暴露受控 topology view。

也就是底层保留统一事件语义，上层允许不同结构视图：

```text
linear view
hierarchical view
graph neighborhood view
trace view
proof-state view
code-AST view
UI-spatial view
```

这种方案避免两种极端：

- 纯 Tape：统一但不自然，很多结构导航低效。
- 纯原生结构：高效但碎片化，动作语义和训练接口容易失控。

但 hybrid 方案也不能免费使用。它必须回答：

- view 是谁构造的？
- view 是否可回放？
- view 和 canonical state 是否一致？
- view 构造成本是否计入 `C`？
- 模型收益来自 topology view，还是来自 resolver 偷渡答案？
- 训练数据能否跨 view 对齐？

## Learned Noisy Directional Access

### 核心抽象

`learned noisy directional access` 是 TapeWalker / active foveated access 背后更硬的抽象：

> 模型能否从局部观察中学习一个带噪的方向判别器，并用它把全局搜索变成逐步缩小候选空间的主动搜索？

它不是 `Load/Store` 的证明，也不是 `O(log n)` 的无条件证明。它是 B 分支下一个候选理论桥：把“人眼扫描 / 移动视野 / 放大缩小 / 局部判断”的直觉，压成可实验、可失败的问题。

直接牵引 TapeWalker 的命题不是“序关系普遍存在”，而是：

> 自然任务分布中广泛存在或可被构造出可导航结构；模型可能学习到带噪方向判断策略，在局部观察预算下逐步逼近目标。

### 方向判别器与复杂度

一个更精确的问题是：

> 每次观察一个局部窗口后，模型能否以高于随机的稳定准确率判断目标在左 / 右、上 / 下、内 / 外、前 / 后？

如果答案为是，且满足若干条件，就会接近 `noisy binary search` / `probabilistic bisection` / `generalized binary search`：

- 每次查询能把候选空间大致均分。
- 方向回答正确率稳定为 `p = 1/2 + gamma`。
- 错误不是系统性偏向。
- 系统有验证、回退、重复采样或贝叶斯更新机制，避免一次错判毁掉整条路径。

在这种模型下，查询次数可以保持对 `n` 的对数依赖，但常数随噪声快速恶化。粗略可以理解为：

```text
queries ~= O((log n + log(1/delta)) / gamma^2)
```

其中 `delta` 是失败概率，`gamma` 是高于随机的 margin。

这给出两个边界。

第一，这不是确定性 `O(log n)`。只有方向 oracle 总是正确，或错误可以被确定性验证并纠正时，才接近确定性二分。

第二，如果 `gamma` 很小，或随着长度、任务难度、分布迁移而下降，复杂度优势会迅速消失。若局部窗口无法提供方向信号，最坏情况仍接近线性扫描。

### 与 IP = PSPACE 的关系

`IP = PSPACE` 不是 TapeWalker / `learned noisy directional access` 的直接哲学牵引。

它更适合放在远层背景：它说明复杂对象在合适协议和表示下可能存在可被较弱 verifier 局部随机检查的结构，但它不说明这些结构天然可导航，也不说明模型能通过移动视野把结构找出来。

更克制的表述是：

> `IP = PSPACE` 不意味着复杂问题容易求解；它说明在合适的交互协议和表示下，即使非常复杂的计算也可能具有可被较弱 verifier 通过局部随机检查验证的结构。这可作为“结构可能广泛存在、可通过交互暴露”的哲学牵引，但不能直接推出现实任务中存在可由模型主动扫描发现的序关系。

因此，`IP = PSPACE` 若放入历史动机，最合适的位置不是作为 `Load/Store` 或 `active foveated access` 的理论证明，而是作为更弱的旁支脚注：

> 复杂任务不一定只能靠一次性全局展开；交互、局部检查、随机抽查、状态化声明和验证协议，可能把复杂结构暴露给较弱控制器。

### 可测指标

TapeWalker 式实验不应直接声称 `log(n)`，而应测量：

- 局部窗口到方向判断的准确率。
- 每次观察带来的信息增益。
- 错误方向判断是否可恢复。
- 方向准确率是否随 workspace 长度保持。
- 方向策略能否迁移到 heldout 任务或更长长度。

如果加入 `grep / BM25 / vector / SQL / LSP / RLM / generated search code` 后优势消失，应承认它被现有 Agent 工程吸收。

如果只在人工有序玩具任务上有效，结论应限于机制 sanity check。

## Peripheral-Like Overview

### 与下采样的区别

TapeWalker 当前的 `load()` 下采样，更接近：

> sparse probe：在一个窗口中抽取少量位置，返回这些位置的相对精确内容。

人的 peripheral vision 更接近：

> low-bandwidth feature field：大范围、低分辨率、连续覆盖的传感器信号，与内部注意力和眼动控制协同工作。

二者不是同一个东西。

关键区别不是“是否少读 token”，而是：

> peripheral vision 在低成本、受限带宽下，仍保留空间 / 序关系 / 低语义显著性 / 变化信号，从而指导下一次 attention、fixation、zoom 或 move。

因此更严谨的说法是：

> peripheral-like 机制的价值不是单纯节省 token，而是在低成本周边观察中保留足够方向信号。

### 人类类比的边界

人类 peripheral vision 不是离线摘要索引。

它是：

> 低成本、受限带宽的传感器输入，加上内部高级注意力、眼动、记忆和 world model 的协同。

但 TapeWalker 在文本、trace、workspace 上没有天然传感器层。所谓 peripheral-like overview 多半只能是：

- 派生视图。
- summary layer。
- feature layer。
- index layer。
- learned sensor / encoder。

这导致一个重要边界：

> 在 workspace 上，peripheral-like overview 不是免费感知层，而是需要构造、维护、计费和防止智能泄漏的派生层。

### Overview Strength Ladder

为了避免 overview 偷走 TapeWalker 的贡献，应把 overview 按强度分级。

| 强度 | 名称 | 例子 | 结论边界 |
| --- | --- | --- | --- |
| L0 | `load_sparse` | 均匀抽样，返回少量精确 cell | 只测 sparse probe，不是 peripheral-like overview。 |
| L1 | `static_generic_features` | 长度、类型分布、密度、变化量、失败计数、dirty flag、bucket 边界 | 最干净的 sensor proxy，可优先测试。 |
| L2 | `static_learned_features` | frozen embedding、task-agnostic encoder、低维 feature vector | 可能接近 learned sensor，但必须证明不是 task-specific locator。 |
| L3 | `static_semantic_summary` | LLM summary、自然语言区域摘要、疑似问题描述 | 容易偷走智能，只能作为强 scaffold 对照。 |
| L4 | `resolver / generated analyzer` | 直接返回候选目标、likely-error region、task-specific anomaly score | 不算 TapeWalker 默认能力，应作为强基线。 |

当前第一优先级应是 L1。

L2 可以作为 learned sensor 的早期版本，但必须冻结、计费并做跨任务迁移检验。

L3 / L4 即使有效，也只能说明“语义摘要 / analyzer 有用”，不能直接证明 active foveated access 有机制优势。

### 与 B0 / B2 的边界

当前更稳的安排是：

```text
B0:
  addressed local cell/window access
  read_window only
  不默认引入 peripheral-like overview
  不依赖 overview 产生方向信号

B2 / TapeWalker static:
  load_sparse vs load_overview_static
  只读 trace / long document / log localization
  测方向信号与观察成本

B2 / TapeWalker dynamic:
  只有 static overview 有信号后，再研究 overview maintenance cost
```

因此 peripheral-like overview 的位置是：

> B2 / TapeWalker 的重要消融项和远景桥，不是 B 分支的默认 access mode。

更明确地说：

> B0 的 `read_window` 不应依赖 overview；overview 只进入 B2 / TapeWalker 消融。否则会污染 B0 对 `addressed local cell/window access` 本身的判断。

### Direction Signal Metrics

“方向信号”必须从直觉落成指标。至少可以考虑这些指标：

| 指标 | 含义 |
| --- | --- |
| `direction_accuracy` | 给定当前位置和目标，模型选择 left / right / zoom / jump-bin / stay 的准确率。 |
| `information_gain` | 观察 overview 后，候选区间或候选 bin 的熵下降。 |
| `navigation_regret` | 相对 oracle policy 多走多少步、多读多少 token 或多花多少 tool call。 |
| `recovery_after_wrong_direction` | 走错方向后能否通过后续观察恢复，而不是不可逆偏离。 |
| `same_token_success` | 在相同 observation token 预算下的定位成功率。 |
| `same_success_cost` | 达到相同定位成功率时需要的 observation token、tool call 或 wall-clock。 |
| `false_negative_rate` | overview 没有给出有效方向信号导致目标区域被跳过的比例。 |

这些指标比“token 变少”更关键。

如果 overview 只降低 token，但 `direction_accuracy`、`navigation_regret`、`same_token_success` 没有改善，它更像压缩层，而不是 peripheral-like navigation layer。

### Learned Sensor 远景

从历史动机看，最远景的形态不应是纯 cell/token 型 overview，而应更接近：

```text
workspace region
  -> learned sensor / encoder
  -> compact latent or coarse feature field
  -> controller decides next fixation / zoom / move
```

这里 `Load` 不是把 token 原文搬给 LLM，而是通过一个可训练感知层，把 workspace 转成低带宽状态信号。

但这条路很重，因为它牵涉：

- sensor 的训练目标。
- workspace 表示。
- sensor 与 controller 的接口。
- controller 与 sensor 是分阶段训练还是联合训练。
- 是否仍能复用现有 LLM。
- 如何防止 sensor 退化成 retriever / resolver。
- 如何计入构造、推理和维护成本。

因此，learned sensor 适合作为远景升级路径，不适合作为第一阶段默认实验。

## Computer Use 对标

### 一句话结论

`computer use` 与 `active foveated workspace access` 在高层上相似：二者都是“观察 -> 动作 -> 再观察”的主动反馈闭环。

但二者不是同一个东西。

更精确地说：

> `computer use` 是视觉 / UI 环境中的具身工具接口；`active foveated workspace access` 是受控 workspace 上的一等公民视野访问接口。

### 核心差异

| 维度 | Computer use | TapeWalker / active foveated workspace access |
| --- | --- | --- |
| 状态空间 | GUI / 浏览器 / 桌面 / app UI | 人工定义的 workspace，可是文本、trace、表、图、文件片段 |
| 观察方式 | screenshot / 可见窗口 / UI 状态 | `pos + fov + load_range / load_cell / zoom` |
| 地址 | 像素坐标、UI 元素、窗口位置，可能有 accessibility / DOM 辅助 | 显式 address / cell / cursor / mark |
| 视野控制 | 通过 scroll、click、window focus、browser zoom 等间接控制 | `fov` 是一等公民，可直接放大、缩小、移动 |
| 写入方式 | click / type / drag / shortcut，修改真实 UI 状态 | `store / insert / delete / patch / commit` 修改 workspace |
| 可控实验性 | 噪声大，UI 状态复杂，难严格控制信息预算 | 可强制隐藏全局状态、固定 observation budget、记录访问轨迹 |
| 研究价值 | 强现实基线，适合真实 GUI 任务 | 更适合研究 B 分支机制、selector 学习、局部访问策略 |

`computer use` 不缺主动性，但通常缺少显式、一等公民的视野控制。

它可以滚动页面、点击元素、切换窗口、聚焦区域、输入文本、调整浏览器页面状态。这些动作会间接改变下一次 observation。

但这类视野控制通常是 UI 操作的副产品，而不是类似下面这样的显式 workspace 指令：

```text
move(pos)
zoom(fov)
load(cell)
load_range(start, end)
mark(pos)
goto_mark(mark_id)
```

因此，对 UI / 视觉任务，computer use 是必须对标的强基线；对 trace-local first-error localization，它不是核心基线，因为 substrate 不是 UI。

## 强基线覆盖与胜率判断

### 已被强 Agent / 工具链覆盖的弱版本

现代强 Agent 已经覆盖了大量弱版本。不能把“支持局部读取”“支持移动视野”“支持按需查询”“支持局部 patch”当作新贡献。

| 已覆盖能力 | 现有强 Agent / 工具链形态 | 吸收程度 | 对 active foveated 的含义 |
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

### 场景胜率判断

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

## 实验裁决与优先级

### 推荐推进顺序

第一步：B0 trace-local。

```text
Task:
  trace-local first-error localization

Interface:
  read_budget
  read_window
  navigate(prev,next)
  zoom
  mark

No:
  semantic overview
  anomaly score
  cause_candidate
  likely-error region
```

第二步：强基线。

必须对标：

- full trace。
- random / linear scan。
- grep / BM25 / vector retrieval。
- generated deterministic analyzer。
- RLM / recursive context management，若任务是长上下文。

第三步：B2 / TapeWalker policy。

比较：

- linear scan。
- pure TapeWalker scan。
- topology-aware trace access。
- retrieval jump。
- TapeWalker + L1 generic overview。

第四步：A+B。

加入：

- typed event。
- state delta。
- invariant。
- verify result。
- diagnose label。
- rollback scope。

观察是否改善 first-error localization、rollback point、repair scope 和训练样本质量。

第五步：远期 learned sensor。

只有在 L1 generic overview 有信号后，再考虑：

- frozen embedding。
- task-agnostic encoder。
- direction prediction。
- information gain prediction。
- multi-task transfer。

### 主要指标

主指标应同时覆盖成功率和成本：

- first bad step hit rate。
- distance to first bad step。
- observation tokens。
- tool calls。
- navigation steps。
- false negative rate。
- recovery after wrong direction。
- same-token success。
- same-success cost。
- local repair success。
- selector imitation / training sample efficiency。
- length scaling curve。

如果只报告 token 下降，不足以支持 peripheral-like 或 active foveated 的机制价值。

如果只报告定位成功率，不计入 overview、resolver、index、runtime scaffold 成本，也不足以支持 B 的效率桥。

## 参考与对标来源

这些来源用于约束强基线，不用于证明 active foveated 一定有效。

### 强 Agent / 工具链基线

- 精确文本搜索：[`ripgrep`](https://github.com/BurntSushi/ripgrep)。
- BM25 / 关键词检索：[Lucene BM25Similarity](https://javadoc.io/doc/org.apache.lucene/lucene-core/latest/org/apache/lucene/search/similarities/package-summary.html)、[Azure AI Search BM25 配置文档](https://learn.microsoft.com/en-us/azure/search/index-ranking-similarity)。
- 向量检索：[Faiss 官方文档](https://faiss.ai/index.html)、[Faiss paper](https://arxiv.org/abs/2401.08281)。
- 数据库索引：[PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)、[PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)。
- 代码符号导航：[Language Server Protocol specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)、[Tree-sitter 官方文档](https://tree-sitter.github.io/)。
- Agent 工具与资源暴露：[Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-06-18)、[MCP Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)。
- Agent runtime / tracing：[OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents)、[OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/)。
- UI / computer use：[OpenAI Computer Use](https://developers.openai.com/api/docs/guides/tools-computer-use)、[OpenAI Computer-Using Agent](https://openai.com/index/computer-using-agent/)、[Anthropic Computer Use Tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)。
- 长上下文递归管理：[Recursive Language Models](https://arxiv.org/abs/2512.24601)、[RLM project page](https://alexzhang13.github.io/blog/2025/rlm/)、[RLM GitHub](https://github.com/alexzhang13/rlm)。
- 结构化递归运行时：[λ-RLM paper](https://arxiv.org/abs/2603.20105)、[λ-RLM GitHub](https://github.com/lambda-calculus-LLM/lambda-RLM)。
- 本仓库内吸收表：[[10-control-feedback-token-instruction/reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]]。

### Active / Foveated 机制背景

- [Recurrent Models of Visual Attention](https://arxiv.org/abs/1406.6247)：通过自适应选择局部区域降低大图像处理成本。
- [Multiple Object Recognition with Visual Attention](https://arxiv.org/abs/1412.7755)：模型学习关注输入图像中的局部区域并识别多个对象。
- [Foveation in the Era of Deep Learning](https://proceedings.bmvc2023.org/703/)：讨论 deep learning 时代的 foveated sensing / active attending。

## 尚未决定的问题

这些问题应留待后续讨论，不应在本备忘中提前定案：

- `trace-local first-error localization` 是否正式升为主线第一任务族。
- B0 的最小 `read_window` 粒度如何定义。
- trace event 的 B-only 字段边界如何定义。
- first-error label 如何处理多因一果和不可唯一归因。
- generated analyzer 基线应强到什么程度。
- `load_overview_static` 的 L1 generic feature 字段有哪些。
- overview 的信息预算和构造成本如何计入。
- 是否需要 shuffled / corrupted overview 负控。
- TapeWalker 是否应先做纯一维 view，还是直接做 trace topology view。
- learned sensor 的训练目标是方向预测、信息增益预测、错误区间预测，还是下一步 action imitation。
- dynamic workspace recovery 是否应与 first-error localization 同步推进。

## 原 Memo 映射

本页收敛以下非主线 memo 的主要内容，但暂不删除原文。

| 原文件 | 合并后位置 |
| --- | --- |
| [[10-control-feedback-token-instruction/active-foveated-workspace-access|Active Foveated Workspace Access]] | B 分层、trace-local、TapeWalker、强基线、胜率判断。 |
| [[10-control-feedback-token-instruction/navigable-structure-topologies-memo|可导航结构与 Workspace 拓扑备忘]] | 可导航 workspace、topology、tape 边界、stable opcode + typed operands。 |
| [[10-control-feedback-token-instruction/learned-noisy-directional-access-memo|Learned Noisy Directional Access 备忘]] | 带噪方向判别、复杂度边界、IP = PSPACE 的位置。 |
| [[10-control-feedback-token-instruction/peripheral-vision-and-tapewalker-memo|Peripheral Vision and TapeWalker Memo]] | 下采样与 peripheral vision、overview strength ladder、direction signal metrics。 |
| [[10-control-feedback-token-instruction/computer-use-vs-active-foveated-access|Computer Use vs Active Foveated Access]] | computer use 对标、UI / 视觉 substrate 下的强基线。 |

后续如果本页被确认没有丢信息，原 memo 可以删除或归档；在此之前，原 memo 保留作为审计版本。
