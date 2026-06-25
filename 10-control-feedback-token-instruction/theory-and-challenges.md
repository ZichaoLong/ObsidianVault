---
type: theory-challenges
status: active
tags:
  - control-feedback
  - theory
  - challenge
  - defense
---

# 控制反馈：理论与挑战

这份文档保存当前主线背后的理论支撑、现实对手和主要攻击面。它不是执行入口；执行入口见 [[10-control-feedback-token-instruction/current-mainline|当前主线]] 与 [[10-control-feedback-token-instruction/experiment-protocol|实验协议]]。

## 理论层级

当前理论内容分三层。

| 层级 | 作用 | 当前位置 |
| --- | --- | --- |
| 信仰牵引 | 解释为什么 `Token = Instruction` 值得想 | 历史动机、RAM/RASP、write-once、time scaling |
| 机制支撑 | 解释 A/B 为什么不是随意拆分 | [instruction 可训练性](<experiment-protocol.md#A 分支：显式状态语义与训练可行性>)、局部状态更新闭包、全局重解释 |
| 裁决层 | 判断现实价值是否站住 | 强基线、[成本账本](<experiment-protocol.md#成本账本>)、[A+B 交互](<experiment-protocol.md#A+B 交互指标>)、任务迁移 |

历史理论动机不能直接证明今天的 `Load/Store` 应成为一等公民，但保留了重要直觉：

> 复杂任务的推进，本质上是有限状态下的连续决策、状态管理与外界交互。

## 历史动机留下的三个问题

历史动机最后沉淀出三个问题。

第一，instruction 怎么训练？

- word token 的训练数据天然丰富。
- instruction token 若依赖探索，会面对低效 RL 攻击。
- 这要求 instruction 事件可回放、可监督、可归因、可构造反事实。
- 这支撑 A 分支。

第二，反馈信源怎么选择？

- AI 不应只被动 append。
- 系统应能主动选择观察什么、读取什么、修改什么、验证什么。
- 这支撑 B 分支。

第三，什么控制原语值得稳定下来？

- 不是所有 tool call 都应进入底层词表。
- 也不是 `Load/Store` 名称天然正确。
- 只有在训练、成本、纠偏和生态压力下稳定下来的事件，才有资格成为候选控制原语语言。

## 对标机制谱系

当前路线真正的对手不是某一个 agent，而是当前最强 `LLM + Agent + Tools` 已吸收的机制族。

主要对手包括：

- ReAct：交替推理与行动。
- Plan-Then-Execute：先规划，再执行。
- Reflection / Self-Correction：失败后反思再修。
- Search / Deliberate Inference：多分支探索。
- Program / Tool Delegation：外包给程序或工具。
- Recursive Context Management：递归管理上下文。
- Skill / Memory Accumulation：技能与经验沉淀。
- Recursive Decomposition：递归分解与问题分解。
- Recursive Self-Call / Prompt-as-Environment：把长上下文或任务状态外部化为可 inspect / decompose / recursively call 的环境，代表是 RLM。
- Internal Recurrent / Latent Control Loop：把递归和局部闭环内化到模型隐状态，代表是 HRM / TRM。

这些机制已经能部分模拟 `Load/Store`：

- 调用工具。
- 读写文件。
- 使用数据库。
- 使用 regex、SQL、LSP、索引。
- compact、summarize、重新规划。
- 短上下文循环中做局部修复。

因此当前问题不是“能不能模拟”，而是：

> 这种模拟是否代价过高、轨迹过乱、错误边界过粗、训练信号过弱、局部纠偏不稳定？

HRM / TRM 和 RLM 的位置需要分开：

- HRM / TRM 是内部隐状态递归，不是显式 workspace，也不是 `address/read/write/commit` 证据。它们挑战的是“局部闭环必须外显为状态事件”的假设。
- RLM 是外部环境化上下文上的递归 self-call，比 HRM 更接近 B 分支，因为它显式涉及 inspect、decompose、局部读取和递归调用。
- 因此控制反馈线可以引用 HRM / TRM / RLM 作为相邻对手，但不能用 HRM / TRM 支撑 `Load/Store`，也不能把 RLM 的成功直接等同于显式状态语义成立。

## 局部访问的理论对象

B 分支不应直接等同于 TapeWalker。更原始的对象是：

> hidden global state + constrained local observation + model-controlled feedback source selection。

可以把可导航 workspace 写成：

```text
Navigable Workspace = (S, N, A, O, V, C, H)
```

其中：

- `S`：状态单元，例如 trace step、cell、proof state、code object。
- `N`：邻接或可达关系，例如 prev/next、parent/child、caller/callee。
- `A`：动作，例如 read、navigate、zoom、mark、write、verify。
- `O`：局部观察函数。
- `V`：验证器，例如 test、type check、invariant、proof checker。
- `C`：成本，例如 token、tool call、wall time、setup cost。
- `H`：层级、coarse-to-fine view、summary 或 feature bins。

这个形式化的作用不是证明 TapeWalker 必然有效，而是约束实验必须说明：

- workspace 拓扑是什么。
- 局部观察返回什么信号。
- 验证器如何约束错误。
- 层级或 overview 是否由人工、runtime 或模型构造。
- 成本是否计入。

### 性能与通用性桥

当前对齐后的核心判断是：

> 通用性来自小而稳定的局部状态指令集；可行性与基础性能首先依赖任务状态是否具有可导航结构；resolver / cache / index 是现实任务中的工程加速层；verifier / rollback / replay 是独立的控制可靠性与训练数据层。

对应到 `Navigable Workspace = (S, N, A, O, V, C, H)`：

- 稳定小指令集对应 `A` 与模型可见控制事件语言，例如 read、navigate、write、verify、commit、rollback、mark。A 负责稳定事件语义，B 负责局部访问、寻址与 relation/view 压力。
- 可导航结构主要对应 `N + O + H`，即拓扑、局部观察和层级 / coarse-to-fine view。
- resolver / cache / index 不是 `Navigable Workspace` 元组里的基础项，但在实验中必须作为单独变量记录；它们会影响 `O + H + C`，即局部观察、层级视图和成本。
- verifier / rollback / replay 主要对应 `V` 与 commit/rollback/replay 语义。
- 性能裁决必须落到 `C`，即 token、tool call、wall time、setup、维护和失败恢复成本。

这给出一个更稳的研究图谱：

| 组件 | 贡献 | 如果缺失 |
| --- | --- | --- |
| 稳定小指令集 | 跨任务复用、可训练、可回放、可归因。 | 退化成任务专用工具或 prompt protocol。 |
| 可导航结构 | 支持局部搜索、方向判断、长度泛化和访问成本下降。 | 局部访问只能靠盲扫、全局重读或任务专用 oracle。 |
| resolver / cache / index | 利用现实任务结构提供工程加速。 | 可行但可能太慢，或完全依赖模型盲搜。 |
| verifier / rollback / replay | 允许局部试探、局部修改、失败隔离和训练样本构造。 | 错误污染全局状态，系统频繁退回全局重解释。 |

resolver / cache / index 很重要，但它们不应替代核心假设的检验。核心假设仍是：

> 小而稳定的局部状态指令集 + 可导航结构，是否足以构成通用 AI runtime 的可接受性能 fallback？

`verifier / rollback / replay` 的意义不是额外工程装饰，而是把局部启发式动作变成可控机制。模型可以提出局部修改，runtime 或验证器检查其影响；成功则 commit，失败则 rollback 并把失败事件转化为训练样本。这样，局部操作既不会要求模型一次全局正确，也不会让错误无限传播。

这也是 A+B 合流比单独 A 或单独 B 更强的原因：

- A 提供稳定事件语义、回放、诊断和训练接口。
- B 提供受限观察下的局部定位和访问策略。
- A+B 才能形成“局部访问 -> 局部修改 -> 验证 -> commit/rollback -> 继续推进”的闭环。

### 计算模型类比

RAM/RASP、Load/Store、ISA、cache、GPU/NPU 和 DSA/ASIC 的类比，不用于证明 `Load/Store` 或 TapeWalker 必然正确。它的作用是帮助理解本研究的意图：

> 当系统面对开放任务分布时，通常会出现“通用稳定接口 + 任务结构利用 + 专用加速层”的分工压力。

在经典计算机中，通用 CPU / ISA 提供相对稳定的控制核心，专用加速器、SIMD/SIMT、GPU/NPU、DSA/ASIC 则利用特定任务结构换取性能。cache、index 和 memory hierarchy 不是新的计算语义，而是让常见访问模式更快的工程层。

映射到控制反馈线：

- 小而稳定的局部状态指令集，对应通用接口压力。
- workspace topology 和可导航结构，对应任务状态中的可利用结构。
- resolver / cache / index / overview / learned sensor，对应工程加速层。
- verifier / rollback / replay，对应控制可靠性、失败隔离和训练数据生成层。

这组类比的边界同样重要：

- 它不能推出 AI 必须采用 `Load/Store`。
- 它不能推出 TapeWalker 的序关系是唯一或最终 topology。
- 它不能替代强基线实验。

它只说明：如果 AI runtime 想面对开放任务分布，又不为每个任务单独设计完整专用系统，那么它可能需要某种“可接受性能下的通用 fallback”。TapeWalker 是线性 / 层级 topology 上的一个候选 fallback，而不是终局答案。

### TapeWalker 的准确位置

TapeWalker 不应被写成 B 分支本身，也不应被写成唯一通用 topology。

更稳的表述是：

> TapeWalker 是线性 / 层级可导航 workspace 的最小 ISA 候选。

它押注：

- `prev / next` 是最低成本、最通用、可退化的 relation。
- 局部窗口、移动视野、缩放、标记和局部写入可以覆盖大量文本、trace、日志、时间线和局部扫描任务。
- 如果局部观察能提供带噪方向信号，则 active foveated policy 可能在成本上优于全局重读或线性扫描。

但序关系不是唯一可导航结构：

| topology | 更自然的任务 |
| --- | --- |
| 线性 / 时间顺序 | 文本、trace、日志、时间线。 |
| 层级 | 文件树、章节、模块、proof/subgoal tree。 |
| 图结构 | 调用图、依赖图、概念图、proof graph。 |
| 空间结构 | UI、图像、地图、二维表格。 |
| schema / key | 数据库、字典、资源表、符号表。 |

因此，TapeWalker 的胜利条件应收缩为：

> 在线性、层级或可线性化的 workspace 上，稳定小指令集加 active foveated policy 是否能相对强 retrieval、index、generated analyzer 或 full-context 基线形成成本、训练或纠偏优势。

若要走向更通用的 AI runtime，后续应保持 opcode 稳定，把 topology 差异放进 relation、view、resolver 或 workspace metadata，而不是为每个任务发明完全不同的动作语言。

这里需要区分几个层级，避免 TapeWalker 概念膨胀：

| 层级 | 含义 |
| --- | --- |
| 狭义 TapeWalker | 线性 / 层级 workspace 上的 `pos / fov / move / zoom / load / mark`。 |
| 广义可导航 workspace | graph / spatial / proof / code / trace topology 上的局部观察、移动、标记、读写和验证。 |
| resolver 路线 | 把可导航性预编码进 embedding、schema、AST、index、递归分解树或 generated analyzer。 |
| world model / verifier / rollback | 支持导航可靠性的状态估计、预测、验证、回退和训练数据层。 |

因此，“一切都是导航”这个说法只有在广义控制意义下成立；研究上仍应保留层级边界。狭义 TapeWalker 只负责最小线性 / 层级导航假设，不能把物理世界模型、复杂因果推理、智能度量和 verifier 全部并入自己的胜利条件。

### Resolver 谱系与可导航性假设

Resolver 的角色是：

> 把 query / intent / symbolic address 映射到 workspace 中的候选位置。

因此，resolver 不是 TapeWalker 的反面。它们都依赖某种可导航性，只是可导航结构被放在不同地方：

- resolver 路线把导航结构预编码到词项空间、embedding space、schema、AST、trace topology、递归分解树或任务专用 analyzer 中。
- TapeWalker 路线尝试把导航结构保留在 workspace 层，让模型通过稳定局部指令在线观察、移动、缩放、标记和逼近目标地址。

| 机制 | 可导航性在哪里 | 核心假设 | 困难主要放在哪里 |
| --- | --- | --- | --- |
| grep / regex | 字符串位置与模式空间 | 目标有稳定字面 key 或可写成正则模式。 | query 构造、模式覆盖、同义表达缺失。 |
| BM25 / lexical search | 词项空间与倒排索引 | 相关对象与 query 有足够 lexical signal。 | 词项重合、query expansion、倒排索引和 rerank。 |
| vector / ANN / HNSW | embedding space 的近邻几何和可导航索引图 | embedding model 能把语义相关性投影成可近邻化结构，ANN 图能在目标分布上快速近似导航，近似错误可被下游容忍。 | embedding model、数据分布、近似召回、索引结构、reranker / LLM 补救。 |
| SQL / DB index | schema、key、predicate、表关系 | 目标可表达成结构化查询，schema 足以承载任务语义。 | schema 设计、predicate 生成、索引选择、查询优化。 |
| LSP / tree-sitter | AST、符号表、定义引用图、类型关系 | 代码任务的关键导航结构可由语言语法和静态语义暴露。 | parser、语言服务器、静态分析、跨语言/动态行为缺口。 |
| trace topology | 时间顺序、层级、checkpoint、可能的因果边 | 错误传播在 trace 中留下可定位结构。 | 事件粒度、trace 设计、因果标签、symptom 与 first error 区分。 |
| RLM / recursive context | 递归分解树和局部上下文 | 任务可通过 inspect / decompose / recursive call 逐步局部化。 | 递归协议、上下文管理、子问题边界、合并错误。 |
| generated analyzer | 临时任务专用程序或诊断器 | 模型能为当前任务生成有效导航器或分析器。 | 程序生成、验证、运行成本、过拟合当前任务。 |
| TapeWalker / active foveated access | workspace topology 与在线局部观察轨迹 | 无可靠专用 resolver 时，仍可用稳定局部指令和可导航结构逐步逼近目标。 | 起点、方向信号、错误恢复、观察预算、长度外推。 |

Vector resolver 的关键不是“高维 ANN 不可能”，而是它押注一组很强的联动条件：

> 语义可被投影成可近邻化几何；点集或索引图在目标分布上具有可导航性；近似召回错误可由 rerank、LLM、多轮检索、fallback 或下游任务容忍。

这里有一个重要攻击：

> 如果使用 cosine、L2、inner product 这类 cheap metric 作为低成本导航力场，语义相关性可能不足以被稳定表达，尤其在高维、距离集中、hubness 或任务语义细粒度变化时；如果改用 cross-encoder、LLM judge、任务专用 scoring function 这类智能度量，每次比较本身就接近一次复杂智能计算，vector resolver 的低成本优势会被削弱，并退向 semantic analyzer / reranker / agentic search。

换句话说，vector retrieval 的困难没有消失，而是在 cheap metric、embedding model、ANN index、reranker 和下游容错之间被重新分摊。若 cheap metric 足够好，它是强 resolver；若 cheap metric 不够好，就必须引入更智能、更昂贵的比较或多轮修正，此时它已经接近广义在线导航系统，而不是单纯低成本检索。

HNSW 这类系统不是“无导航”的检索。相反，它通过分层可导航小世界图在 embedding space 中进行近似导航。这与 TapeWalker 的区别是：

- HNSW 把可导航结构压进 embedding metric 与离线索引图。
- TapeWalker 把可导航结构留在 workspace / trace / text / topology view 中，并让模型在线导航。

因此，控制反馈线不应写成 “TapeWalker vs resolver”，而应写成：

> 导航结构应该被预编码进专用 resolver，还是显式暴露成可学习、可回放、可纠偏的 workspace interaction？

### 人类可导航性类比

人类的强处不只是“序关系”。空间连续性、物体恒常性、因果 / 物理先验、周边视觉、运动控制闭环和长期世界模型，都在广义上为导航提供结构。

可以把这些能力分层理解：

| 机制 | 对导航的贡献 | 边界 |
| --- | --- | --- |
| 空间连续性 | 让位置、方向、距离和局部移动有稳定意义。 | 是 topology / geometry，不等于完整智能。 |
| 周边视觉 | 在低带宽下提供方向信号，指导下一次 fixation / zoom / move。 | 是 observation layer，不应被直接等同于 resolver。 |
| 物体恒常性 | 让不可见对象仍可被追踪和重新定位。 | 是状态估计 / memory，不是移动动作本身。 |
| 因果 / 物理先验 | 预测动作后果、错误传播和可恢复路径。 | 是 transition model，会显著改变导航策略。 |
| 运动控制闭环 | 把观察、行动和反馈连成稳定循环。 | 是执行与控制层，不是单纯寻址。 |
| 长期 world model | 维护跨时间的地图、对象、目标和信念状态。 | 是内部模型层，可能替代部分外部 workspace 导航。 |

因此，更稳的类比是：

> 人类利用现实世界赠与的大量可导航结构，使局部观察和局部行动变得高效；但这些赠与不应全部压成“序关系”，也不应全部并入狭义 TapeWalker。它们更像广义可导航 workspace 的结构、传感、状态估计和转移模型。

这对控制反馈线的启发是：TapeWalker 的序关系只是最小 topology prior。若要走向更强通用性，研究对象应扩展为“稳定局部状态指令集如何作用在多种可导航 workspace 上”，而不是把人的全部智能机制都解释成线性扫描。

### Noisy Directional Access

TapeWalker / active foveated access 背后的较硬命题是：

> 模型能否从局部观察中学习带噪方向判断，并用多步观察逐渐缩小候选区域？

若每次局部观察能以 `p = 1/2 + gamma` 的概率给出方向信号，并且错误可通过重复、验证或回退控制，那么查询次数可能保持对规模 `n` 的对数依赖，但常数会随噪声快速恶化：

```text
queries ~= O((log n + log(1/delta)) / gamma^2)
```

这不是无条件 `O(log n)`。如果局部窗口没有方向信号，或者 `gamma` 随长度外推迅速下降，最坏情况仍接近线性扫描。

`IP = PSPACE` 不应作为 TapeWalker 的直接理论支撑。它最多作为远层背景：复杂结构有时能通过交互协议和局部检查暴露给较弱 verifier，但这不能推出现实 workspace 可由模型主动导航。

### Peripheral-Like Overview 风险

peripheral-like overview 的价值不是单纯少读 token，而是在受限带宽下提供方向信号。

但在文本、trace、workspace 上，它通常不是免费传感器，而是派生 observation layer：

- sparse sample。
- generic feature bins。
- learned feature。
- semantic summary。
- anomaly score。
- generated analyzer。

越往后越容易偷走智能。主线边界应是：

- B0 不引入 overview。
- B2 / TapeWalker 才测试 overview 消融。
- generic feature bins 可以作为较干净 proxy。
- semantic summary、anomaly score、likely-error region 更接近 analyzer baseline。

### Computer Use 对标

`computer use` 与 active foveated access 都是观察、行动、再观察的主动闭环。

区别是：

- computer use 的状态空间是 GUI / browser / app UI。
- active foveated access 的状态空间是受控 workspace，例如 trace、文本、表、代码对象。
- computer use 通过 scroll、click、focus、zoom 间接控制视野。
- TapeWalker 把 `pos / fov / move / zoom / load / mark` 显式变成 workspace 指令。

因此，UI / 视觉任务必须把 computer use 当强基线；trace-local first-error localization 则不需要把它作为核心基线，因为 substrate 不同。

## 局部状态更新闭包

局部状态更新闭包仍有价值，但它不再是唯一主线。

当前位置：

> 它是 B 分支和效率桥的理论支撑，解释为什么局部访问与局部修复可能是自然机制，而不是单纯工程偏好。

### 直观问题

> 对某类任务，求解与纠错是否可以主要通过有限组局部状态更新原语完成，而不必频繁退回全局重解释？

### 最小对象

状态空间 `S`：

- 某个工作区。
- 某个结构化对象。
- 某个可被局部读写的中间表示。

局部更新原语 `U`：

```text
ui : S -> S
```

直观要求：

- `ui` 只改动状态的有限局部部分。
- 其余大部分状态保持不变。

任务空间 `T`：

- 初始状态 `s0(tau)`。
- 目标条件 `Goal(tau, s)`。

全局重解释算子 `G`：

> 当系统不足以仅凭当前局部状态对象继续推进时，触发一次对更大范围任务状态的重新组织、重新摘要、重新检索、重新规划或重新解释。

`G` 不是：

- 是否重新 prefill。
- 是否重算 KV cache。
- 是否重跑模型。

`G` 是工作方式层概念：

- 下一步是否重新依赖更大范围语义理解。

### 当前缺口

局部状态更新闭包还必须补：

- 对“局部性”的任务内定义。
- 对 `G` 的行为判据。
- “近似闭包”的容许边界。
- 至少一个现实任务族到 `S/U/G` 的映射。

不能先追求一般定义，应 task-first。

## 确定性层与智能层

纯确定性路线不够。

- 它可能只是算法复杂度或抽象状态机。
- 即使形式上成立，也未必对应现实 LLM/Agent 工作方式。

纯智能实验路线也不够。

- 它可能只是 prompt、tooling、agent engineering。
- 没有钉住机制对象。

正确结构是：

- 确定性层负责变量隔离和机制对象生成。
- 智能层负责验证机制对象是否能被现实预测型控制系统承载。

这也是为什么实验先从强结构任务开始，但不能永远停在强结构任务。

## Test-Time 状态层次

test-time 状态至少有三层：

- `token / context` 层。
- 中间状态系统层，包括 KV cache、RNN state、node memory、workspace。
- 参数层，即 test-time 更新后的权重。

当前阶段先冻结参数。

原因：

- 参数更新变量过多。
- 工程复杂且难复现。
- 容易掩盖显式状态语义与局部访问本身的作用。

长期可以继续问：

- session adapter 是否承载事件压缩。
- 临时 LoRA 是否吸收局部修复策略。
- 参数层是否减少全局重解释。

但这不是第一击。

### HRM / TRM / RLM 的位置

HRM / TRM 属于 `model-internal latent recursion`：

- 递归发生在模型隐状态或 recurrent computation 中。
- 状态不是外部可寻址 workspace。
- 事件不可直接回放成 `address/read/write/commit`。
- 它们更像是“内部控制循环”路线，而不是控制反馈线当前 A/B 接口的证据。

这对控制反馈线是挑战而不是支撑：

> 如果内部 recurrent refinement 已能在某些任务上高效解决问题，显式 workspace / control event 路线就必须证明自己在可诊断性、可训练数据、可复用 memory、工程可控性或复杂任务组织上有额外收益。

RLM 属于 `external recursive self-call / prompt-as-environment`：

- 它把长上下文或任务状态当成外部环境。
- 模型通过 inspect / decompose / recursive call 控制下一步读取和处理范围。
- 它更接近 B 分支的强基线，而不是 A 分支的显式状态语义。

因此：

- 若 B 只做长上下文局部访问，RLM / recursive context management 必须进入强对照。
- 若 A 要证明显式状态语义，HRM / RLM 都不是直接对照；A 的强对照仍是 typed tools + trace/logging/approval/checkpoint/replay/diff/transaction。
- 若 A+B 要重新讨论候选低层控制原语，必须说明外部显式事件相比内部 recurrent refinement 和外部 recursive self-call 的不可替代增量。

## 主要攻击面

### 攻击 1：A 的低阶部分已被 Agent 工程吸收

现代 Agent + Tools 已经在很大程度上吸收了 A 的低阶收益，尤其是在 frontier / provider-level / serious agent runtime 中。详细证据表见 [[10-control-feedback-token-instruction/reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]]。

已被强工程基线部分吸收的内容包括：

- typed action schema。
- 稳定 tool call 生命周期。
- trace / logging / call correlation。
- replay-ready history / resume / fork。
- 显式状态变更 / diff / commit-ish 事件。
- approval / safety / guardrail 状态。
- trace grading / eval loop。

因此，A 不能再主张“第一次让工具调用结构化”。A 剩下的特殊点必须收缩为：

> typed tool traces 能否升级成 decision-active explicit state semantics，使事件不只是工具调用记录，而是可回放、可诊断、可局部修复、可构造反事实、可用于继续训练的状态转移对象。

防守边界：

- `tools vs typed tools` 只作为 Stage 0 sanity check。
- A 的核心对照必须是 `typed tools + trace/logging/approval/checkpoint/replay/diff/transaction` vs decision-active explicit state semantics。
- 如果强 typed tools baseline 实现了同等显式状态语义，A 已被 baseline 吸收。

### 攻击 2：A 只是 schema engineering

A 的显式状态事件可能只是把 typed tools 包装成更规整的 schema。

若 strong typed tools + logging + transaction 达到同等训练、归因和纠偏效果，A 没有独立增量。

防守边界：

- A 必须证明事件进入后续决策。
- A 必须证明轨迹更可训练，而不是只更好看。
- A 必须证明局部修复和反事实样本构造更稳定。

### 攻击 3：A 的训练收益来自低熵动作空间

如果 action vocabulary 更短、更固定，NLL 下降可能只是格式收益。

防守边界：

- NLL 只能作为辅助指标。
- 主指标应是 repair success、sample efficiency、同类错误复发率、counterfactual validity。
- 必须控制 action entropy、schema 信息和输出格式复杂度。

### 攻击 4：B 只是 active retrieval

B 可能退化成 retrieval、memory system 或 POMDP。

现代 Agent 工程已经吸收了 B 的大量弱版本收益，包括 search、index、local read/write、resource discovery、tool discovery、patch/diff 和 history。详细证据表见 [[10-control-feedback-token-instruction/reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]]。

防守边界：

- 固定 resolver，比 access interface。
- 固定 access interface，比 resolver。
- 预先定义 selector/resolver/reader。
- B0 先用 `addressed local cell/window access`，不把 TapeWalker 当总定义。
- 强基线必须包括 full-context、BM25/vector、SQL/LSP、generated analyzer 和 RLM / recursive context management。
- 若只证明检索有用，不算控制反馈主线胜利。

### 攻击 5：B 与 TapeWalker / overview 混淆

TapeWalker 是 B2 access policy，不是 B 的定义。peripheral-like overview 是 B2 消融，不是 B0 默认能力。

如果把 TapeWalker 直接写成 B，实验会被一维 tape、移动/缩放策略、下采样、overview 设计和具体 runtime 细节绑架。

如果把 overview 写进 B0，收益可能来自 summary、feature bins、anomaly score 或 likely-error region，而不是局部访问本身。

防守边界：

- B 总定义保持为 hidden global state + fixed observation budget + model-controlled feedback source。
- B0 使用无 overview 的 local cell/window access。
- TapeWalker 只作为 B2，与 linear scan、retrieval jump、topology-aware access 对照。
- overview 只作为 B2 消融，并按 generic features、learned features、semantic summary、generated analyzer 分级。
- UI / 视觉任务必须对标 computer use；trace-local 任务则不把 computer use 当核心基线。

### 攻击 6：meaningful address 偷渡语义

`users[17].transactions` 已经携带大量语义，模型可能不是学会局部访问，而是吃到了地址标签。

防守边界：

- 做 meaningful / typed / hierarchical / opaque / learned address 消融。
- 若只在 meaningful address 下有效，结论必须收缩。

### 攻击 7：workspace 粒度由人工设计贡献全部收益

如果 cell/schema/scope 全由研究者手工定制，实验可能只是 DSL/task engineering。

防守边界：

- 记录人工设计成本。
- 做 [[10-control-feedback-token-instruction/experiment-protocol#Workspace 粒度消融|cell 粒度消融]]。
- 后续引入模型辅助或自动粒度生成。

### 攻击 8：scaffold 偷走全部困难

薄接口可能只是把复杂性转嫁给 runtime。

防守边界：

- 计入 [[10-control-feedback-token-instruction/experiment-protocol#成本账本|setup、runtime、人工成本]]。
- 区分 model-only proposal quality、runtime-corrected success、rollback-assisted success。
- 如果胜利来自 validator 自动拒错，不能说模型学会了状态管理。

### 攻击 9：任务选择偏置

JSON、AST、ledger、dependency graph 天然适合状态访问接口。

防守边界：

- trace-local first-error localization 升为第一候选任务族。
- 强结构任务只作为 sanity check 和变量隔离。
- 强结构任务结论必须收缩。
- 第二阶段必须进入半结构任务。
- dynamic workspace recovery 先补齐定义，再决定是否并列进入主线。

### 攻击 10：A+B 无交互

A 和 B 可能都是有用小技巧，但组合没有统一原语意义。

防守边界：

- 预注册 [[10-control-feedback-token-instruction/experiment-protocol#A+B 交互指标|交互指标]]。
- 强合流要求 `Y11` 优于 `Y10/Y01`，且 `Interaction > delta`。
- `Y11` 最大但 `Interaction <= 0` 只是弱合流，说明组合工程上有用，但不能强称统一低层原语站住。
- `Y11` 单指标不是最大但 Pareto 非支配时，只能算 Pareto 弱合流。
- 若 `Y11` 被 `Y10` 或 `Y01` 支配，则组合接口失败，但 A 或 B 单分支仍可能保留。

### 攻击 11：历史动机与实验指标之间仍有裂缝

RAM/RASP、write-once、time scaling 不能直接推出当前实验指标。

防守边界：

- 历史动机只提供“为什么值得想”。
- A 提供“instruction 是否可训练”的第一桥。
- B 提供“反馈信源是否可主动控制”的第二桥。
- A+B 交互和成本账本才提供“是否值得继续做”的裁决。

### 攻击 12：Agent+Tools 可以无限吸收

现有 Agent+Tools 可以吸收 typed schema、logging、transaction、retrieval、indexing，甚至局部访问形态。

防守边界：

- 不证明 Agent+Tools 不能做。
- 只检验某套状态访问接口是否在训练、纠偏、成本上形成更稳定非支配点。
- 若被强基线吸收，说明方向可能成为工程实践，而不是独立底层原语。

## 结果解释表

| 结果 | 解释 |
| --- | --- |
| A 成功，B 失败 | 更像 agent trace / schema engineering。 |
| B 成功，A 失败 | 更像 active retrieval / memory system。 |
| A 成功，B 成功，`Y11` 最大但无正交互 | 弱合流，工程组合有用，但统一原语未站住。 |
| `Y11` Pareto 非支配但主指标不最大 | Pareto 弱合流，可以继续工程推进。 |
| `Y11` 被 `Y10` 或 `Y01` 支配 | A+B 组合失败，单分支仍可保留。 |
| A 和 B 都只赢弱基线 | 不能说明独立增量。 |
| A 和 B 在强基线下都失败 | 当前形态应放弃或大幅转向。 |
| A+B 在强基线和成本账本下形成 `Interaction > delta` | 可以重新讨论统一状态访问接口或候选低层原语。 |

这张表的目的不是悲观，而是避免任何结果都能解释成胜利。

## 当前 Defense

当前 defense 不是“控制反馈已经成立”，而是：

- 历史动机足够严肃，值得提出问题。
- A 把 `Token = Instruction` 最大训练裂缝压成可实验问题，但必须承认其低阶部分已被现代 Agent 工程部分吸收。
- B 把“自主控制反馈信源”压成隐藏全局状态、固定观察预算下的局部反馈信源选择问题。
- A/B 2x2 让结果可分解、可输、可降级。
- 强基线与成本账本避免自我奖励。

如果 A/B 都站不住，就不应继续扩张叙事。

如果 A 站住但 B 不站住，仍可保留为 instruction trace / data flywheel 工程方向。

如果 B 站住但 A 不站住，仍可保留为 active retrieval / memory system 方向。

只有 A+B 在强基线下形成交互收益，才值得重新讨论 `Load/Store` 或更底层控制原语语言。
