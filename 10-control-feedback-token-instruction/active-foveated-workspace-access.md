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

这条线必须承认，现代 Agent 工程已经覆盖了大量弱版本。

- 有精确关键词时，`grep / rg` 是强基线。
- 有语义 query 时，BM25 / vector / hybrid retrieval 是强基线。
- 有表结构时，SQL / database index 是强基线。
- 有代码符号时，LSP / tree-sitter / code index 是强基线。
- 有 UI 或视觉空间时，computer-use agent 是强基线。
- 有长上下文递归访问时，RLM / recursive context management 是强基线。
- 有确定性序关系时，临时生成查找程序本身就是强基线。

所以，TapeWalker 式机制不能把“支持局部读写”或“支持移动视野”当作独立贡献。它必须证明：

> 在这些强 resolver 都不直接适用，或成本 / 数据 / 任务分布不允许预先构造强 resolver 的场景中，主动视野访问策略仍有可测增量。

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

