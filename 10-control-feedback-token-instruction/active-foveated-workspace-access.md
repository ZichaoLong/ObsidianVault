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
