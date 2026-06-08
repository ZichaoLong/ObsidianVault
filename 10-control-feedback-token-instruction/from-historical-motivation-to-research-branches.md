---
type: synthesis
status: active
tags:
  - control-feedback
  - token-instruction
  - research-direction
---

# 控制反馈：从历史动机到研究分支

这份文档重新整理控制反馈线从历史动机到当前可推进研究分支的逻辑。它不预设 `Load/Store` 一定是答案，而是把它降级为一个候选低层控制原语，并要求它在强对照下证明不可被普通 Agent 工程完全吸收的增量。

当前最可守的一句话是：

> 本研究不证明 AI 能不能用工具，而是检验：显式状态语义与局部状态访问这两类接口，是否能在强 typed tools、logging、retrieval、indexing 对手下，形成更可学习、更可归因、更可纠偏、更低成本的高频控制闭环；只有当二者合流后仍有增量，`Load/Store` 才有资格被称为候选低层控制原语。

## 一页版结论

当前研究线应拆成两个正交分支。

分支 A：显式状态语义。

- 研究对象是 `address/read/write/commit/verify/replay/diagnose` 是否能成为稳定运行时事件对象。
- 它不要求模型只能看局部状态。
- 它主要检验可归因、可纠偏、可回放、可监督、轨迹是否更适合训练。
- 它的强对手不是普通工具，而是 `standard tools + typed schema + trace id + logging + transaction`。

分支 B：局部状态访问。

- 研究对象是模型是否只能通过受约束寻址访问隐藏全局状态的局部片段。
- 它不自动要求完整显式状态语义。
- 它主要检验寻址、访问成本、长度泛化、全局扫描频率、局部修复成本。
- 它的强对手不是普通工具，而是 BM25、vector search、tree-sitter/LSP、SQL/index、learned retriever 等强检索与索引系统。

二者的合流条件是：

- A 在强 typed-tools/logging/transaction 基线上仍改善归因、纠偏或训练数据质量。
- B 在强 retrieval/indexing 基线上仍改善成本曲线、长度泛化或局部修复范围。
- A+B 的组合产生交互收益，而不是两个可独立吸收的小技巧。
- 计入 workspace 构造、cell 切分、address schema、index build、runtime/scaffold 成本后，仍形成 Pareto 优势或清晰非支配点。

如果 A 成功、B 失败，研究应降格为 `agent trace / schema engineering`。如果 B 成功、A 失败，研究应降格为 `active retrieval / memory system`。如果 A、B 都成功但组合无额外收益，`Load/Store` 作为统一低层原语仍未站住。

## 历史动机的保留部分

控制反馈线最初不是从普通 agent engineering 出发，而是从更抽象的计算模型和智能工作方式出发。

历史动机里有三个重要起点。

第一，AI 需要自主控制反馈信源。系统若只能被动接收一次输入并输出答案，它的能力边界会受到限制；系统若能主动决定下一步观察什么、操作什么、验证什么，它就进入了控制反馈系统。

第二，现代 `LLM + Agent + Tools` 已经是真正的自主控制反馈信源。LLM 生成动作，工具返回观察，LLM 根据反馈继续行动。这个意义上，当前 Agent 已经不是纯 append-only 问答系统。

第三，历史动机真正想推进的不是“有没有工具”，而是“智能与世界之间的交界面应该长什么样”。如果交界面是所有异质 tools，那么接口很厚；如果交界面是统一状态访问接口，那么接口更薄。

历史动机中曾提出一种定义或假设：

> 通用智能 = 可生成指令的可学习通用程序。

如果暂时不讨论可学习性，当前 LLM+Agent 已经非常接近这个定义。因此，真正的争论不再是“系统是否自主控制反馈信源”，而是：

> 什么样的指令接口更适合作为可学习通用程序的低层动作空间？

## 历史理论动机的作用和边界

历史动机中引用复杂度理论、RAM/RASP、write-once、append-only、CoT 和时间 scaling law，这些理论并不能直接证明今天的 `Load/Store` 应该成为一等公民，但它们保留了一个重要直觉：

> 复杂任务的推进，本质上是有限状态下的连续决策、状态管理与外界交互。

这个直觉包含几层含义。

第一，单次决策可见状态越大，理论上可能解决更多问题，但处理这些状态本身也有成本。

第二，许多小决策并不需要全局状态。把所有信息都塞进上下文，可能带来冗余解释、注意力浪费和错误扩散。

第三，分而治之是降低单次决策状态需求的重要方式。问题分解减少每步处理的信息量，但引入分解、验证、回滚和重新分解成本。

第四，状态管理本身可以理解为问题分治。把大任务推进成一系列局部状态更新，就是把问题结构化成局部约束与中间对象。

第五，问题分治也可以理解为状态管理。递归分解、引理分解、模块化代码修改、账本修复、依赖图传播，本质上都在管理中间状态。

因此，历史理论动机提供的是方向牵引，而不是现实系统结论。它说明高频小颗粒闭环、局部状态更新、可验证推进是自然研究对象，但没有证明某种具体 `Load/Store` 形态应当胜出。

## 当前核心裂缝

核心裂缝是：

> 凭什么某种形态的 `Load/Store` 应该成为一等公民？

这个问题不能通过以下论证回答：

- 不能只说 RAM 比图灵机高效。
- 不能只说 append-only 有限制。
- 不能只说人类有眼耳手脚。
- 不能只说 LLM 需要 memory。
- 不能只说工具协议太乱。

现实 challenge 是：

- 当前 LLM+Agent 已经能调用工具。
- 当前 LLM+Agent 已经能读写文件。
- 当前 LLM+Agent 已经能用 regex、SQL、路径、索引精确寻址。
- 当前 LLM+Agent 已经能 compact、summarize、重新规划。
- 当前 LLM+Agent 已经能在短上下文循环里做局部修复。
- 当前 LLM+Agent 理论上可以模拟很多 `Load/Store` 机制。

所以核心问题必须换成：

> 这种模拟是否代价过高、轨迹过乱、错误边界过粗、训练信号过弱、局部纠偏不稳定？

更精确地说，当前要检验的不是 `Load/Store` 这个名字，而是：

> 统一状态访问接口是否在强工具、强检索、强日志、强事务基线下，仍然有不可被吸收的学习、纠偏或成本优势？

## 智能与世界的三种交界面

### 厚界面：Agent + Tools

如果把所有 tools 都看作智能与世界的交界面，那么界面很厚。系统需要学习和管理大量异质协议：

- 文件读写。
- regex。
- shell。
- 浏览器。
- 数据库。
- 代码解释器。
- 搜索工具。
- 专用 API。

这种路线非常强，也最接近现实前沿系统。它的问题不是不能工作，而是接口语义复杂、事件边界不统一、错误类型混杂、训练轨迹不一定清洁。

### Word Token 界面

也可以说，真正交界面仍然是 word token。模型输出 token，runtime 解释 token，工具执行 token 指令。

这说明 `Token = Instruction` 与普通 token 没有天然断裂。很多所谓指令最终仍是 token 序列，只是被 runtime 解释成行动。

因此，`Token = Instruction` 不能仅靠“token 可以表示指令”站住。它必须说明：某些 token 语义被压成稳定控制原语后，是否带来更好的学习、纠偏或成本结构。

### 薄状态界面：Load/Store

`Load/Store` 设想的是更薄的状态接口：

- 智能侧主要面对 workspace。
- workspace 内部是中间状态系统。
- workspace 外部是更复杂的世界和 tools。
- 高频小闭环尽量发生在统一状态接口内。

这不意味着其他 tools 不存在。更准确地说，外部 tools 可能退到 runtime 或 scaffold，智能体高频操作的是 workspace。

这个设想的风险是明显的：

> 薄界面可能只是把复杂性转嫁给 runtime/scaffold。

因此，所有实验必须计入 scaffold 成本。否则胜利是虚假的。

## 分支 A：显式状态语义

显式状态语义关心的是：

> 状态、读、写、提交、可见性、回放、诊断，是否能成为稳定运行时事件对象。

它不要求模型每一步只能看到局部状态。即使模型能看到较大上下文，也可以研究显式状态语义。

它的核心不是局部可见性，而是事件边界和状态语义是否清楚。

典型动作包括：

- address。
- read。
- write。
- patch。
- commit。
- rollback。
- verify。
- replay。
- diagnose。

主要研究问题：

- 错误是否能切成 address/read/write/commit/verify/infer 等类别。
- 事件是否可回放。
- 事件是否影响后续决策，而不只是日志。
- 局部修复是否因此更稳定。
- 轨迹是否更适合训练和数据清洗。

这个分支的第一风险是协议格式偏置。如果底层专家 IR 已经写成 `ADDRESS/READ/WRITE/VERIFY`，显式状态协议天然占便宜。因此底层专家轨迹必须写成协议中立的 semantic transition。

协议中立轨迹应描述语义变化，而不是预设接口形态。例如：

```text
locate violated constraint
inspect relevant object
modify state element
check invariant
make change visible
recover previous consistent state
```

然后再分别渲染到不同协议：

- append-only answer。
- standard tools。
- standard tools + typed schema + trace id + logging + transaction。
- explicit state semantics。
- full state semantics。

A 分支的强对手必须是：

> `standard tools + typed schema + trace id + logging + transaction`

如果显式状态语义只赢普通 tools，不赢这个强基线，它不能证明 `Load/Store` 有独立增量。

## 分支 B：局部状态访问

局部状态访问关心的是：

> 模型是否只能通过受约束的地址访问隐藏全局状态的局部片段，而不能每一步直接看到完整全局状态。

这里必须把 global state 藏在环境中。模型每一步只看到：

- 当前目标。
- 最近事件。
- 已加载的局部 cell。
- 小 scratchpad。
- 工具返回的局部观察。

模型必须主动生成地址，选择 load 什么、store 什么、verify 什么。

这个分支的关键不是事件语义是否漂亮，而是信息边界：

- 每步可见 token 数。
- 访问 cell 数。
- 地址生成准确率。
- 不必要读取率。
- 全局扫描触发率。
- 长度泛化曲线。
- 局部修复需要读取的范围。

B 分支的第一风险是退化为 active retrieval / POMDP。这个风险需要正面承认。它的强对手不是普通 tools，而是：

- BM25。
- vector search。
- tree-sitter/LSP。
- SQL/index。
- 编辑器跳转。
- learned retriever。
- 任务专用 resolver。

因此，`Load/Store` 不应假装替代这些 resolver。更合理的说法是：

> retriever/index/resolver 可以是 address resolver 的实现；研究问题是，在 resolver 能力相近时，统一状态访问接口是否让控制、纠偏、学习或成本结构更好。

如果 B 分支只证明“主动检索有用”，它应归入 memory/retrieval 研究，而不是控制反馈主线的完整胜利。

## 两个分支的 2x2 实验结构

显式状态语义和局部状态访问应以 2x2 factorial 设计拆开。

| | 无显式状态语义 | 有显式状态语义 |
| --- | --- | --- |
| 无局部访问 | typed tools 强基线 | A：显式状态语义 |
| 有局部访问 | retrieval/index 强基线 | A+B：完整统一状态访问接口 |

这个设计的目的不是证明某个名称正确，而是切出三个贡献：

- 显式状态语义的贡献。
- 局部状态访问的贡献。
- 二者组合后的交互贡献。

若只做 A，不能声称验证局部访问。若只做 B，不能声称验证显式状态语义。若 A 和 B 都有收益但组合没有额外收益，说明二者可以被现有机制分开吸收，`Load/Store` 作为统一低层原语仍未站住。

## 更可学习的严格含义

“更可学习”不能定义成“人类看起来更清楚”。它应定义成：

> 在同一任务分布、同一模型能力、同等信息预算下，某种交互协议产生的轨迹更容易让模型从数据中学成可复用策略，并在执行语义上获得更好结果。

更可学习至少包括四层。

第一，模仿学习更容易。

- next action NLL 更低。
- exact action accuracy 更高。
- parse-valid rate 更高。
- 用更少训练样本达到同等执行成功率。
- 对更长状态、更深结构、更大图泛化更好。

第二，credit assignment 更局部。

- 错误能定位到事件。
- 错误能分类到 address/read/write/commit/verify/infer。
- 负样本不会污染整段轨迹。
- 反事实样本更容易构造。

第三，纠偏策略更容易学习。

- 局部修复成功率更高。
- 平均恢复步数更少。
- 同类错误复发率更低。
- 失败后更少退回全局扫描或全局重解释。

第四，轨迹数据质量更高。

- 事件边界清楚。
- 状态变化可回放。
- 输入输出语义稳定。
- 正负样本可自动生成。
- 更适合 imitation、RL、数据清洗和反事实训练。

但必须注意：`next action NLL` 不能作为主裁决指标。它容易被短语法、低熵动作空间、强类型标签污染。

更稳的主指标应是执行语义结果：

- semantic success。
- repair success。
- 平均恢复步数。
- 同类错误复发率。
- 长度泛化。
- 总成本 Pareto。

若使用 NLL 或 action accuracy，必须控制：

- token budget。
- schema 信息。
- action entropy。
- 输出格式复杂度。
- 可见状态量。

## Workspace 粒度是核心难题

`Load/Store` 的核心难点不是写出几个动作名，而是 workspace 粒度。

必须回答：

- 谁定义 cell？
- 谁定义 address schema？
- 谁定义 scope？
- 谁定义 transaction？
- 谁决定状态边界？
- 谁维护 workspace 与外部世界的一致性？

如果这些完全由研究者手工设计，实验可能只是 DSL/task engineering。如果让模型学习，难度会明显上升。

因此，workspace 粒度应作为显式研究变量，而不是隐藏假设。

建议分三步：

第一步，人工固定粒度。

- 目的是验证机制是否可能成立。
- 不能据此声称通用性。
- 必须记录人工设计成本。

第二步，粒度消融。

- coarse cell。
- fine cell。
- hierarchical cell。
- typed address。
- untyped address。
- static schema。
- dynamic schema。

第三步，模型辅助或自动粒度生成。

- 让模型提出 cell 切分。
- 让模型提出 address schema。
- 让系统根据错误率和访问成本调整粒度。
- 检验自动粒度是否接近人工粒度效果。

如果粒度问题不处理，`Load/Store` 的低层原语地位站不稳。

## 成本模型必须计入 scaffold

薄界面可能把复杂性转嫁给 runtime。必须建立成本账本。

至少计入：

- workspace 构造成本。
- cell 切分成本。
- address schema 设计成本。
- index build 成本。
- resolver 调用成本。
- runtime/scaffold 代码复杂度。
- 每步可见 token 数。
- 每步生成 token 数。
- tool call 数。
- action 步数。
- 失败恢复步数。
- rollback/retry 次数。
- 人工工程量。

如果 `Load/Store` 赢，是因为 scaffold 做了大量隐性工作，那么不能算低层原语胜利。最多说明某种工程 scaffold 有用。

成本裁决不应只看单一指标，而应看 Pareto。

可能的主坐标：

- semantic success。
- total token cost。
- action/tool-call cost。
- repair cost。
- global reinterpretation count。
- setup/scaffold cost。

在实际判断中，如果 token 成本下降但 action 步数暴涨，不一定赢。如果局部修复更好但总体成功率下降，也不一定赢。需要预先定义主指标和 Pareto 解释规则。

## 任务选择与偏置

候选任务如 JSON、AST、ledger、dependency graph 都偏符号、偏局部、偏结构化，天然有利于状态访问接口。

这不是错误，但必须承认其边界。

第一阶段可以使用这些任务，因为它们能降低噪声、固定机制对象、自动判定正确性。但第一阶段结论只能是：

> 在天然结构化、局部状态任务上，某种状态访问接口可能更可学习或更可纠偏。

不能直接推广到开放世界任务。

第二阶段必须加入更弱结构或半结构任务：

- 长文档局部修订。
- 代码仓库局部修复。
- 多文件一致性维护。
- 实验日志与分析状态维护。
- 课程学习笔记的局部更新。
- 需要递归分解但局部状态不明显的任务。

任务应形成梯度：

- 强结构。
- 半结构。
- 弱结构。
- 开放世界近似任务。

如果只在本来就像数据库/AST 的任务上成立，结论应保持收缩。

## 错误归因不是天然唯一

错误类型可能不可唯一归因。一次失败可能同时是：

- address_error。
- infer_error。
- verify_error。
- update_error。

因此，credit assignment 的提升不能只依赖研究者事后 ontology。

需要三种约束。

第一，任务构造时注入单点错误。

- 单独污染 address。
- 单独污染 read。
- 单独污染 write。
- 单独污染 commit。
- 单独污染 verify。

第二，允许多标签归因。

- 不强迫所有错误唯一分类。
- 记录主因和副因。
- 区分机制错误与任务推理错误。

第三，用纠偏结果反证归因价值。

- 如果归因正确，局部修复应更容易。
- 如果归因只是标签，恢复步数不会下降。

因此，错误归因的价值必须由修复结果支撑，而不能只由标签准确率支撑。

## 理论侧命题的重新定位

“局部状态更新闭包”仍有价值，但它不是唯一最终答案。

更准确的理论问题是：

> 对某些现实相关任务族，是否存在自然的局部状态更新闭包，使得任务推进和纠错可以主要由有限局部原语完成，而不必频繁进行全局重解释？

这个命题支撑 Load/Store 的方式是：

- 它说明局部状态更新不是单纯工程偏好。
- 它说明某些任务结构天然适合局部推进。
- 它说明高频小闭环有独立研究价值。

但它不能单独证明 Load/Store 是一等公民。因为短上下文循环 Agent、普通工具协议、传统程序都可能实现局部状态更新。

因此，理论命题必须加强为：

> 对某些任务类，存在自然的局部状态更新闭包；用统一状态访问原语表达时，相比全局重解释或异质工具模拟，具有更低的局部修复成本、控制复杂度、错误传播范围或轨迹复杂度。

这把理论命题接到了效率桥，而不是停在“能不能做”。

## 合流条件

只有以下条件同时成立，`Load/Store` 才能重新从候选分支合流为“低层控制原语”主张。

第一，A 分支站住。

- 显式状态语义在强 typed tools/logging/transaction 基线上仍有增量。
- 增量体现为归因、纠偏、回放、训练数据质量，而不是格式更整齐。

第二，B 分支站住。

- 局部状态访问在强 retrieval/indexing 基线上仍有增量。
- 增量体现为成本曲线、长度泛化、局部修复范围，而不是弱化版检索。

第三，A+B 有交互收益。

- 更好地址选择。
- 更低恢复步数。
- 更少全局重解释。
- 更干净训练轨迹。
- 更稳定的局部修复策略。

第四，计入 scaffold 成本后仍有优势。

- 不是 runtime 偷偷承担了所有困难。
- 不是人工 workspace 设计贡献了全部收益。
- 不是强 prompt 或更长 schema 信息带来的假象。

第五，优势能跨任务粒度迁移。

- 不只在一个手工 DSL 任务上成立。
- 至少在多个结构化任务族上成立。
- 最好能推进到半结构任务。

## 结果解释规则

需要提前定义哪些结果仍属于控制反馈主线，哪些结果意味着转向。

| 结果 | 解释 |
| --- | --- |
| A 成功，B 失败 | 更像 agent trace/schema engineering，不足以支撑局部访问原语。 |
| B 成功，A 失败 | 更像 active retrieval/memory system，不足以支撑显式状态语义。 |
| A 成功，B 成功，A+B 无交互收益 | 两个机制可被分别吸收，统一 Load/Store 原语未站住。 |
| A 和 B 都只赢弱基线 | 不能说明独立增量，需加强对照。 |
| A 和 B 在强基线下都失败 | 当前形态应放弃或大幅转向。 |
| A+B 在强基线和成本账本下仍形成 Pareto 优势 | 可以继续推进 Load/Store 作为候选低层控制原语。 |

这张表的目的不是提前悲观，而是避免任何结果都能解释成胜利。

## 当前计划

第一阶段：重写实验定义。

- 不用 Load/Store 术语写底层专家 IR。
- 改用协议中立 semantic transition。
- 明确 A/B 分支各自强基线。
- 明确 scaffold 成本账本。
- 明确 workspace 粒度变量。

第二阶段：做强结构任务的 2x2 小实验。

- JSON。
- AST。
- ledger。
- dependency graph。

第一阶段任务不追求开放世界泛化，只追求机制对象清楚、可自动判定、可注入错误。

第三阶段：引入小模型训练。

- imitation learning。
- error attribution。
- recovery/repair。
- length generalization。

注意 NLL 只能作为辅助指标，主指标应落到执行语义和成本。

第四阶段：引入强 LLM/Agent rollout。

- 使用强 LLM 作为 controller。
- 控制 prompt、上下文、工具能力、schema 信息和可见状态量。
- 对比强 typed tools 与强 retrieval/indexing。

第五阶段：推进半结构任务。

- 长文档修订。
- 代码仓局部修复。
- 多文件一致性维护。
- 研究笔记状态更新。

只有前四阶段出现稳定收益，第五阶段才有意义。

## 当前最小可输命题

新版最小可输命题不应写成 “Load/Store 有用”。

更合适的是：

> 在同等模型能力、同等信息预算、计入 scaffold 成本的前提下，显式状态语义与局部状态访问分别、以及组合后，是否相对强 typed tools/logging/transaction 和强 retrieval/indexing 基线，在学习、归因、纠偏或成本曲线上形成不可被吸收的增量？

这个命题可以输。

它输掉时的含义也清楚：

- 如果强 typed tools 足以吸收 A，则显式状态语义不是独立主线。
- 如果强 retrieval/indexing 足以吸收 B，则局部状态访问不是独立主线。
- 如果 A+B 没有交互收益，则 `Load/Store` 不是统一低层原语，只是两个工程机制的组合。
- 如果 scaffold 成本吞掉收益，则薄界面是假象。

它站住时的含义也清楚：

- 状态访问接口不只是工具别名。
- 事件语义和局部访问不是单独小技巧。
- 二者组合确实形成更适合高频小闭环的控制接口。
- 后续才值得讨论训练接口、基础模型接口、甚至更底层神经网络承载。

## 最可守的研究表述

当前最可守的表述是：

> 控制反馈线研究的不是“AI 是否会用工具”，而是“状态访问是否值得成为可学习智能系统的低层控制接口”。为避免被普通 Agent 工程吸收，必须将显式状态语义和局部状态访问拆开，在强 typed tools、logging、retrieval、indexing 对手下分别验证，再检验二者组合是否产生不可被吸收的学习、纠偏和成本优势。

更短的版本是：

> `Load/Store` 不是预设答案，而是显式状态语义与局部状态访问在强基线下合流后才有资格成立的候选低层原语。
