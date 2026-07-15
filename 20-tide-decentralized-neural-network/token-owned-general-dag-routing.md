---
type: note
status: draft
cssclasses:
  - textbook-math
tags:
  - tide
  - prefill-decode
  - sparse-routing
  - load-balancing
  - math
---

# 一般 DAG 中携带 `token` 归属信息的消息路由

> [!summary] 本页定位
> 本页研究一个固定周期 Tide 参考模型。位置 $t$ 的外部输入值 $x_t$ 在绝对内部轮次 $Rt$ 注入；模型在 $R(t+1)$ 的固定边界产生第 $t$ 个读出。空间结构是任意有限的单位时延 DAG，长路径消息可以跨边界继续传播。本文定义边上消息携带的 `token` 归属信息、节点持久状态、类型化逻辑事件、事件依赖 DAG、三种同刻转移语义，以及绝对时间流式调度与节点拓扑序分块调度。

> [!important] 核心结论
> 等层 DAG 不是封闭有限精确分块执行的必要条件。对于本文固定周期、空间无环的严格语义，只要每条消息保留归属字段 `owner`、因果前沿 `frontier` 和到达时间戳，每个可变状态只由一个节点持有，路由只沿空间 DAG 前进，并且每个节点的分块实现与其逐事件参考转移完全相同，就可以把绝对时间流式调度等价重排为节点拓扑序分块调度。该结论包含固定周期读出产物，但不自动给出低并行跨度，也尚未构造可直接接续 `decode` 的边界状态。

> [!warning] 正确性不自动推出高性能
> 本页主定理只证明流式调度与分块调度计算同一参考语义。它允许一个节点在一次调用中处理完整输入块，并消除逐 `token` 的全局主机编排；但若节点局部转移本身含有顺序状态链或控制链，其内部并行跨度仍可随事件数线性增长。要达到 Transformer/Mamba 意义上的低 `token` 轴并行跨度，还需要因果注意力、扫描、分段批量处理、紧凑打包稀疏计算核等额外结构，并要求总事件数受控。

> [!note] 标题中的“`token` 归属”具体指什么
> “携带 `token` 归属信息”只修饰沿空间边传播的消息。每条消息都有字段 `owner(m)=t`，表示这条消息当前使用输入位置 $t$ 作为归属索引。它不把 `token` 定义成计算轨迹，也不表示空间节点、空间边或持久状态属于 $x_t$，更不表示消息数值只依赖 $x_t$。
>
> 例如 `owner(m)=2`、`frontier(m)=5` 表示：该消息当前归入索引 $2$，但其载荷可能已经读取了依赖 $x_0,\ldots,x_5$ 的节点状态。`owner` 回答“当前用哪个输入位置标记这条消息”，`frontier` 回答“数值最多依赖到哪个输入前缀”；二者不能合并为一个字段。不同消息可以具有相同 `owner`，同一来源关系中的后继消息也可以在配置 F 下改变 `owner`，所以 `owner` 既不是消息标识符，也不是不可变来源标识符。

> [!example] 一页直观模型
> ```text
> 外部 token 出现 (位置 t, 值 x_t)
>   -> 输入事件
>   -> 一条或多条边上消息 (message_id, owner=t, frontier=t, arrival=...)
>   -> 下游节点在相应逻辑到达时刻产生节点事件
>   -> 节点转移产生带归属标签的局部输出记录和状态更新
>   -> 选择器为局部输出记录选择空间出边
>   -> 派发新的消息实例；消息可以分叉，节点事件也可以汇聚多条消息
>   -> 输出节点状态
>   -> 固定边界读出 y_t
> ```
> 空间 DAG、空间节点和空间边是静态结构；事件是一次实际发生的计算；消息是一个事件产生并沿一条空间边传给后继事件的记录；状态是空间节点持有的长期上下文；调度只是满足依赖关系的一种物理执行安排。本文证明的是两种调度对同一批事件、消息和状态产物等价，而不是仅比较最终输出。

> [!important] 本页的四个对象层级
> | 层级 | 对象 | 不应混同的对象 |
> | --- | --- | --- |
> | 外部序列 | `token` 位置 $t$、输入值 $x_t$、一次 `token` 出现 $(t,x_t)$ | 消息、事件、计算轨迹 |
> | 静态空间结构 | 空间节点 $v$、空间边 $(u,v)$、输入/输出锚点 | 某次执行中的节点事件、事件依赖边 |
> | 动态参考语义 | 事件实例、消息实例、状态版本、局部输出记录、路由记录 | 物理线程、设备计算核调用顺序 |
> | 来源与执行 | 消息分支、消息来源图、完整来源信息、逻辑次序、物理调度 | `owner`、因果前沿或墙钟先后 |
>
> 同一个词若跨越这些层级，正文必须加限定语。例如“节点”默认指空间节点；逻辑事件 DAG 中的顶点称为“事件顶点”；“边”必须写成空间边、消息来源边或事件依赖边；“激活”必须区分隐藏激活值与节点事件实例化。

^tide-object-layers

## 0. 术语、记号与固定周期外部接口

### 术语约定与中英文对照

本文不追求机械的全中文或全英文，而按术语是否已经形成稳定的 AI/工程直觉来选择写法：

1. `token`、`prefill`、`decode`、`logits` 直接保留英文。本文中的 `token` 是外部序列元素；$t$ 是位置索引，$x_t$ 是该位置的输入值，$(t,x_t)$ 是一次具体的 `token` 出现。`token` 不表示消息、事件或计算轨迹，因此不默认译为“令牌”或“词元”。
2. Transformer、Mamba、SSM、FFN、KV cache、QKV、DAG、ISA、SSA、C++ 等模型名或固定缩写保留原写法。
3. 节点、边、消息、状态、事件、调度、转移、路由、读出、采样、工作量、并行跨度等结构与数学对象使用中文。
4. Tide 新概念在正文中写成“归属 `token`”“归属字段”“因果前沿”“归属支持集”，公式和接口字段保留 `owner`、`frontier`、`support`。
5. `timestamp` 在英文对照或接口中始终写成一个单词，不使用 `time stamp`。下表中的说明不是新的数学对象；严格含义仍由后续定义给出。

#### 直接保留英文的 AI 术语

| 本文写法 | 不作为默认写法 | 原因 |
| --- | --- | --- |
| `token` | 令牌、词元 | 本文同时讨论文本与一般模型输入；需要区分位置 $t$、值 $x_t$ 和一次出现 $(t,x_t)$，“词元”会过度强调语言学含义 |
| `prefill` / `decode` | 预填充 / 解码 | 二者是本文要比较的标准执行模式，英文在 AI 系统领域更直接 |
| `logits` | 输出逻辑值 | 固定模型接口名；需要解释时称为“归一化或采样前的输出分数” |
| Transformer / Mamba / SSM / FFN / KV cache / QKV | 人工翻译名 | 模型名、计算核族与固定缩写不翻译 |
| DAG / ISA / SSA / C++ | 展开的中文全称 | 首次需要数学定义时可补中文，后续使用固定缩写 |

#### 时间与边界

| 中文 | 英文 | 本文简写或说明 |
| --- | --- | --- |
| 固定周期 | fixed period | 周期长度记为 $R$ |
| 内部轮次 | internal round | 指图内部推进一次的离散逻辑轮次 |
| 绝对内部轮次 | absolute internal round | 不随 `token` 重新从零计数 |
| 阶段 | phase | 同一内部轮次内按屏障、可见性和提交次序划分的分段 |
| 微步 | microstep | 仅在一个阶段内部仍需显式区分多个有序子事件时使用的离散次序坐标；不是默认必需字段 |
| 逻辑时间戳 | logical timestamp | 后文可简称时间戳；本文不用 `time stamp` |
| 逻辑秩 | logical rank | 用于证明每条事件依赖严格向前推进的良基次序键；“良基”表示不存在无限严格下降链。它可以由逻辑时间戳、语义并列键和微步组成，但不是事件标识符 |
| 同一逻辑到达时刻 | same logical arrival time | 指相同的 $(\tau,i_{\mathrm{arrive}})$；不表示同一墙钟时刻 |
| 注入 | injection / inject | `token` 进入输入节点的固定边界事件 |
| 读出 | readout | 从输出节点状态提取 $y_t$，不同于采样 |
| 采样 | sampling / sample | 根据读出选择下一个自回归 `token` |
| 边界 | boundary | 相邻固定周期之间的逻辑分界 |
| 执行切面 | execution cut | 把已经发生的事件与尚未发生的事件分开的参考观察位置；切面上可以存在在途消息 |
| 墙钟时间 | wall-clock time | 真实设备时间，不等于逻辑时间 |
| 截止时间 | deadline | 墙钟性能约束，不属于参考语义本身 |

#### 事件、消息与状态

| 中文 | 英文 | 本文简写或说明 |
| --- | --- | --- |
| 逻辑事件 | logical event | 表示一次已经实例化的逻辑计算记录 |
| 事件顶点 | event vertex | 逻辑事件 DAG 中代表一个事件实例的顶点；不同于空间节点 |
| 事件头 | event header | 事件标识符、种类、位置、时间戳、支持集和因果前沿组成的元组 |
| 事件值 | event value | 记为 $\nu(e)$ |
| 事件依赖图 | event dependency graph | 若无环，则称为逻辑事件 DAG |
| 事件依赖边 | event dependency edge | 表示事件实例之间直接的数据、状态或控制依赖；不同于空间边 |
| 消息实例 | message instance | 一个事件产生、沿一条空间边传播并具有独立消息标识符的记录 |
| 消息分支 | message branch | 消息来源图中的一条线性有向路径；分叉或汇聚后的完整结构不是一条分支 |
| 消息来源图 | message-lineage graph | 以事件实例和消息实例为顶点、以产生/消费关系为边的二部图 |
| 收件箱 | inbox | 按节点、时间戳和归属 `token` 分桶的消息多重集 |
| 逻辑到达批次 | logical arrival cohort | 同一空间节点、同一逻辑到达时间戳的完整消息多重集 $I_{v,\tau}$ |
| `token` 归属 / 归属 `token` | token ownership / owner token | 消息字段 `owner=t` 表示当前消息使用位置 $t$ 作为归属索引；它不是消息身份、不可变来源或完整依赖集合 |
| 归属支持集 | owner support | 一个事件直接联合处理或标识的 `owner` 索引集合，记为 `support`；它不是实际因果依赖集合 |
| 因果前沿 | causal frontier | 语义对象最多依赖到哪个 `token` 前缀；若对象可选，则同时约束其存在性 |
| 状态 | state | 节点持有的持久数值状态 |
| 状态版本 | state version | 一次提交后形成、可由后继事件读取的确定状态快照 |
| 增广状态 | augmented state | 数值状态与因果前沿组成的有序对 |
| 提交 | commit | 使状态或输出对后继逻辑事件可见 |
| 提交轨迹 | commit trace | 按规范提交次序排列的状态版本 |
| 在途消息 | in-flight message | 已派发、但在当前边界尚未到达或消费的消息 |
| 来源信息 | provenance | 用于说明一个产物由哪些具体事件、消息和路径产生；比归属字段和因果前沿更完整 |
| 分支谱系标识 | branch-lineage identifier | 标识一条消息分支的确定性路径信息；不能代替包含分叉、汇聚和状态依赖的完整来源信息 |
| 局部输出记录 | local output record | 节点转移产生、供选择器读取并可能派发为消息的带标签记录；不同于外部读出 $y_t$ |
| 产物 | artifact | 正确性契约中必须比较的隐藏表示、状态、路由、消息和读出等结果 |
| 来源槽位 | birth slot | 可选严格稀疏配置中由某个输入位置创建、随后至多承载一条活跃消息分支的守恒槽位 |
| `logits` | logits | 归一化或采样之前的模型输出分数 |

#### 六种容易混淆的身份、归属与来源信息

| 字段 | 回答的问题 | 示例 |
| --- | --- | --- |
| `message_id` / 消息标识符 | 这是哪一个具体消息实例？ | 两条载荷相同的消息仍有不同标识符 |
| `birth_token` / 来源位置 | 可选来源槽位最初由哪个输入位置创建？ | `birth_token=2` 在严格槽位配置中终生不变 |
| `owner` / 归属 `token` | 当前消息使用哪个输入位置作为归属索引？ | `owner=2`；配置 F 可以把后继消息改标为更大的因果前沿 |
| `support` / 归属支持集 | 当前事件直接联合处理了哪些 `owner` 索引？ | `support={2,4}`；不表示只依赖 $x_2,x_4$ |
| `frontier` / 因果前沿 | 当前数值或存在性最多依赖到哪个输入前缀？ | `frontier=5` 表示最多依赖 $x_0,\ldots,x_5$ |
| `provenance` / 来源信息 | 具体经过了哪些事件、边、槽位和路由？ | 用于精确回放与归因 |

`owner` 不能唯一确定消息分支：同一个事件可以向多条空间边派发多个具有相同 `owner` 的消息。`frontier` 也不能恢复真实依赖集合：它只是一个前缀上界。只有消息标识符与显式来源关系共同给出可回放的实例级结构。

`owner` 的操作性作用由参考语义明确规定：它用于收件箱分桶、配置 O 的同刻并列次序、配置 O/J 的逐归属局部输出记录，以及路由/损失/回放中的归属对齐。它是否进入数值计算取决于具体节点转移或选择器签名，不能仅因字段存在就假设计算核读取了它。

本文不再使用没有限定语的“`token` 轨迹”或“消息轨迹”。“轨迹”只保留在具有规范顺序的记录对象中，例如状态提交轨迹或完整执行记录；线性传播称为消息分支，包含分叉和汇聚的结构称为消息来源图。

#### 执行、调度与性能

| 中文 | 英文 | 本文简写或说明 |
| --- | --- | --- |
| 参考语义 | reference semantics | 被不同实现或调度共同保持的规范语义 |
| 转移 | transition | 一次有明确输入、输出与状态更新的确定函数 |
| 转导器 | transducer | 对一条有序输入序列执行转移并产生有序输出序列和状态的对象；不要求物理逐项流式执行 |
| 节点转移 | node transition | 消费收件箱与前状态，产生局部输出记录和状态更新；不负责物化边消息 |
| 选择器 | selector | 根据局部输出记录选择空间出边的确定函数；可变状态必须显式纳入契约 |
| 路由 | routing | 选择器产生的出边选择结果；不决定局部输出记录的 `owner` 语义 |
| 路由记录 | routing record | 把一个局部输出记录与其已选空间出边集合、必要的选择器审计字段关联起来的记录；它先于消息实例物化 |
| 派发 | dispatch | 根据局部输出记录和路由结果物化新的消息实例 |
| 事件实例化 | event instantiation | 参考语义中建立一个实际事件；“节点激活”若无额外说明只可作为它的非正式简称 |
| 隐藏激活值 | activation value | 神经网络数值张量或表示；不同于事件实例化 |
| 逻辑次序 | logical order | 参考语义规定的可见性、提交与依赖先后 |
| 语义并列键 | semantic tie | 仅当参考语义要求区分同一逻辑时间戳内的多个事件时使用的确定性次序键；配置 O 可取归属索引，配置 J/F 的联合事件不按归属拆分 |
| 调度 | schedule | 在不违反逻辑依赖的前提下安排物理执行的方式 |
| 稳定序列化键 | serialization key | 为日志、比较或存储提供确定的全序；可在逻辑秩后追加事件标识符，但其大小本身不产生因果依赖 |
| 绝对时间流式调度 | absolute-time streaming schedule | 按绝对轮次与阶段推进 |
| 节点拓扑序分块调度 | node-topological chunk schedule | 按空间 DAG 的拓扑序逐节点处理完整规范事件序列 |
| 封闭有限执行 | closed finite execution | 最后一个读出后继续冲刷当前有限输入产生的消息 |
| 延续状态 | continuation state | 可直接接续下一周期的节点状态与在途消息 |
| 水位标记 | progress watermark | 异步实现用于证明“不再会补来时间戳不超过某个界的消息”的进度凭证；默认不是模型事件或数值状态 |
| 精确分块正确性 | exact chunk correctness | 分块执行与参考产物严格相等 |
| 语义商 | semantic quotient | 主动把多个可区分输入或输出记录映射为统一表示；它改变表示语义，不只是调度优化 |
| 工作量 | work | 总原语操作数或其上界 |
| 并行跨度 | span | 无限处理器理想化下的关键路径长度 |
| 关键路径 | critical path | 由依赖关系决定、无法并行缩短的最长路径 |
| 性能见证 | performance witness | 正确性之外，对工作量、并行跨度和吞吐量的独立证明或测量 |
| DAG | directed acyclic graph | 首次定义时可写“有向无环图（DAG）”，后文直接使用 DAG |
| 计算核 | kernel | 节点内部承担数值计算或局部控制计算的实现单元 |
| 运行时 | runtime | 承担事件组织、调度、消息传递和状态提交的执行系统 |
| 事件中间表示 | Event IR | 实现层用于显式保存逻辑事件、字段与依赖关系的中间表示 |
| `prefill` / `decode` | prefill / decode | 给定 `token` 块的并行处理 / 逐步自回归处理 |
| 语义配置 | semantic profile | 固定转移、状态可见性、提交和路由含义的一组约定 |
| 类型化 | typed | 对事件种类、字段和依赖关系给出显式类型约束 |

### 定义 0.1：基础集合记号

定义自然数与正整数：

$$
\mathbb N=\{0,1,2,\ldots\},
$$

$$
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $L\in\mathbb N$，定义：

$$
[L]=\{0,1,\ldots,L-1\}.
$$

若 $L=0$，则 $[L]=\varnothing$。

有限序列使用圆括号表示。有限多重集保留重复元素，不因载荷相等而去重。

本文是自足文档：后文使用的输入序列、事件 DAG、前缀因果性、工作量与并行跨度均在本文首次使用前定义。一般自适应 routing 的下界属于独立的反向研究问题，不作为本文任何定义、命题或定理的证明前提。

### 定义 0.2：输入序列与固定周期

给定输入值空间 $X$、读出空间 $Y$、输入块长度 $L\in\mathbb N$、固定周期：

$$
R\in\mathbb N_{>0},
$$

以及输入序列：

$$
x_{0:L}=(x_0,\ldots,x_{L-1})\in X^L.
$$

对每个 $t\in[L]$：

- $t$ 称为 `token` 位置或 `token` 索引。
- $x_t\in X$ 称为位置 $t$ 的 `token` 值。
- 有序对

$$
\xi_t=(t,x_t)
$$

称为输入序列中的一次 `token` 出现，其中 $\xi_t\in[L]\times X$。

即使 $x_t=x_{t'}$，只要 $t\neq t'$，$\xi_t$ 与 $\xi_{t'}$ 仍是两次不同的出现。后文写“`token` $t$”时只是在无歧义处简称“位置 $t$ 的 `token` 出现”，不把 $t$、$x_t$、消息实例或事件实例视为同一个对象。消息字段 `owner=t` 存储的是索引 $t$，不是值 $x_t$。

本文所说的长度为 $L$ 的 `chunk` 就是有限输入序列 $x_{0:L}$。物理 `prefill` 可以一次持有整个 `chunk`，但这不表示所有 `token` 出现在同一个逻辑时间；它们仍按式 GD-0.1 的固定逻辑周期依次注入。

对每个 $t\in[L]$，定义 `token` $x_t$ 的绝对注入轮次：

$$
\operatorname{InTime}(t)=Rt.
\tag{GD-0.1}
$$
^eq-fixed-injection-time

定义第 $t$ 个读出的绝对轮次：

$$
\operatorname{OutTime}(t)=R(t+1).
\tag{GD-0.2}
$$
^eq-fixed-readout-time

$R$ 是参考语义的常数，不依赖输入值、节点状态、任何模型内部决策或当前运行时活动。内部计算不能推迟或提前式 GD-0.1 与 GD-0.2 规定的边界。

这里 $R$ 首先是逻辑周期。若还要求真实设备每隔固定墙钟周期 $T_{\mathrm{ext}}>0$ 输出一个 `token`，则实现必须证明第 $t$ 个读出在墙钟截止时间 $(t+1)T_{\mathrm{ext}}$ 前完成。该实时吞吐量条件属于性能见证，不由后文的调度等价定理自动推出。

### 定义 0.3：阶段与完整逻辑时间戳

取阶段数：

$$
N_{\mathrm{phase}}\in\mathbb N_{>0},
\qquad
N_{\mathrm{phase}}\geq 6,
$$

以及按执行先后排列的阶段元组：

$$
\mathcal P
=
(\varphi_0,\ldots,\varphi_{N_{\mathrm{phase}}-1}).
$$

定义完整逻辑时间戳集合：

$$
\Theta
=
\mathbb N\times\{0,\ldots,N_{\mathrm{phase}}-1\}.
$$

对 $(\tau,i),(\tau',j)\in\Theta$，定义字典序严格次序 $<_{\Theta}$：

$$
(\tau,i)<_{\Theta}(\tau',j)
$$

当且仅当：

$$
\tau<\tau',
$$

或：

$$
\tau=\tau'
\quad\text{且}\quad
i<j.
$$

指定六个不同阶段索引：

$$
i_{\mathrm{arrive}},
i_{\mathrm{step}},
i_{\mathrm{commit}},
i_{\mathrm{read}},
i_{\mathrm{sample}},
i_{\mathrm{inject}}
\in
\{0,\ldots,N_{\mathrm{phase}}-1\},
$$

满足：

$$
i_{\mathrm{arrive}}
<
i_{\mathrm{step}}
<
i_{\mathrm{commit}}
<
i_{\mathrm{read}}
<
i_{\mathrm{sample}}
<
i_{\mathrm{inject}}.
\tag{GD-0.3}
$$
^eq-boundary-phase-order

定义第 $t$ 个 `token` 的注入时间戳：

$$
\theta_t^{\mathrm{in}}
=
(Rt,i_{\mathrm{inject}}),
$$

以及第 $t$ 个读出与采样时间戳：

$$
\theta_t^{\mathrm{out}}
=
(R(t+1),i_{\mathrm{read}}),
$$

$$
\theta_t^{\mathrm{sample}}
=
(R(t+1),i_{\mathrm{sample}}).
$$

因此当 $t+1\in[L]$ 时：

$$
\theta_t^{\mathrm{out}}
<_{\Theta}
\theta_t^{\mathrm{sample}}
<_{\Theta}
\theta_{t+1}^{\mathrm{in}}.
\tag{GD-0.4}
$$
^eq-read-sample-inject-order

本文后续使用以下严格约定：

- “同一完整逻辑时间戳”指两个对象具有相同的 $(\tau,i)\in\Theta$。
- “同一绝对轮次”只要求绝对轮次 $\tau$ 相同，阶段可以不同。
- 第 4-6 节简称“同刻到达”时，专指相同的到达时间戳 $(\tau,i_{\mathrm{arrive}})$。
- 同一逻辑时间戳不要求对象在同一墙钟时刻执行；反之，物理上同时执行也不能使两个不同逻辑时间戳变成同刻。

### 定义 0.4：给定序列（teacher forcing）与自回归外部接口

在用于验证 `prefill` 的给定序列参考中，$x_{0:L}$ 是边界数据；虽然物理实现可以一次持有整个张量，位置 $t$ 的输入值 $x_t$ 在逻辑上只能从 $\theta_t^{\mathrm{in}}$ 开始可见。

在自回归 `decode` 参考中，给定确定性 `token` 选择函数：

$$
\operatorname{SelectToken}:Y\to X,
$$

并要求第 $t$ 个固定周期读出 $y_t\in Y$ 产生后：

$$
x_{t+1}
=
\operatorname{SelectToken}(y_t),
\qquad t+1\in[L].
\tag{GD-0.5}
$$
^eq-autoregressive-token-selection

到达、节点转移与状态提交均在读出之前完成，因此绝对轮次 $R(t+1)$ 到达输出节点的最短路径消息可以影响 $y_t$。式 GD-0.4 保证随后先选择 `token`，最后注入下一 `token`。后文的分块正确性定理以给定输入序列的参考执行为比较对象；式 GD-0.5 额外定义自回归 `decode` 如何把连续两个固定周期连接起来。

> [!example] $R=2$ 时的一段时间线
> - 绝对轮次 $0$：注入 $x_0$。
> - 绝对轮次 $1$：图内消息继续传播。
> - 绝对轮次 $2$：先提交本轮节点状态，再读出 $y_0$；自回归执行随后采样 $x_1$，最后注入 $x_1$。
> - 比最短路径更长的消息可以在轮次 $3,4,\ldots$ 才到达，并影响更晚的读出。
>
> 这里的轮次是逻辑时间，不是设备墙钟时间；`prefill` 可以并行计算多个逻辑轮次，但不能改变上述可见性顺序。

## 1. 一般单位时延空间 DAG

### 定义 1.1：带输入输出的空间 DAG

一个带输入输出的空间 DAG 是三元组：

$$
(G,s,z),
$$

其中：

- $G=(V,E)$ 是有限 DAG。
- $s\in V$ 是唯一输入节点。
- $z\in V$ 是唯一输出节点。
- $s\neq z$。
- 每个 $v\in V$ 都位于至少一条从 $s$ 到 $z$ 的有向路径上。

另外固定节点集合 $V$ 与边集合 $E$ 的静态全序 $<_{V}$、$<_{E}$，只用于规范序列化与确定性并列消解；它们不表示额外计算依赖。

对边 $(u,v)\in E$，$u$ 称为 $v$ 的直接空间前驱，$v$ 称为 $u$ 的直接空间后继。

### 定义 1.2：有向路径与路径长度

从节点 $u$ 到节点 $v$ 的一条有向路径是节点元组：

$$
p=(v_0,v_1,\ldots,v_k),
$$

满足：

$$
v_0=u,\qquad v_k=v,
$$

并且对每个 $i\in\{0,\ldots,k-1\}$：

$$
(v_i,v_{i+1})\in E.
$$

路径 $p$ 的边数称为路径长度，记为：

$$
|p|=k.
$$

定义从输入节点到 $v$ 的可达路径长度集合：

$$
\Lambda(v)
=
\{|p|\mid p\text{ 是从 }s\text{ 到 }v\text{ 的有向路径}\}.
$$

因为 $G$ 有限且无环，$\Lambda(v)$ 是有限非空集合。

定义空间 DAG 的最大路径长度：

$$
D
=
\max_{v\in V}\max\Lambda(v).
$$

由于有向路径不能重复经过同一个节点：

$$
D\leq |V|-1.
$$

定义输入到输出的最短路径长度：

$$
d_{\min}
=
\min\Lambda(z).
$$

本文固定周期严格语义配置取：

$$
R=d_{\min}.
\tag{GD-1.1}
$$
^eq-period-shortest-path

由 $s\neq z$，有 $d_{\min}\geq 1$，所以式 GD-1.1 与定义 0.2 的 $R\in\mathbb N_{>0}$ 一致。因此，若位置 $t$ 的输入沿一条最短输入输出路径实际派发消息，则相应消息在绝对轮次 $R(t+1)$ 到达输出边界。式 [[#^eq-read-sample-inject-order|GD-0.4]] 进一步规定同一边界上先读出，再采样，最后注入。当 $D>R$ 时，更长路径上的消息仍会跨越该边界，并只能影响逻辑时间更晚的状态或读出。

> [!note] 为什么取 $R=d_{\min}$
> 这使“最短空间路径走完一次”与“外部接口推进一个 `token` 周期”对齐：$x_t$ 在 $Rt$ 注入，沿最短路径实际派发的消息在 $R(t+1)$ 到达输出节点，并在同一边界的读出阶段之前提交。长路径消息不被截断，只是把影响推迟到后续读出。

### 定义 1.3：单位时延边

本文假设每条边的参考传播时延恰好为一个全局内部轮次：

$$
\operatorname{delay}(u,v)=1,
\qquad (u,v)\in E.
$$

这是一条语义约束，不是硬件传输延迟。物理运行时可以融合传输、使用缓冲区或异步执行，但必须保持逻辑到达时间。

> [!note] 一般 DAG 与等层 DAG
> 若对任意节点 $v$，集合 $\Lambda(v)$ 只有一个元素，则所有从 $s$ 到 $v$ 的路径等长，旧文档中的等层 DAG 是本页模型的特殊情形。本文不再把这一性质作为前提，也不通过中继节点改变原边的单位时延。

## 2. 前缀因果性与固定周期路径时间

### 定义 2.1：前缀因果对象与因果前沿

定义因果前沿索引空间：

$$
\mathbb F_L
=
\{-1\}\cup[L].
$$

给定由输入序列 $x_{0:L}$ 决定的任意语义对象 $q$，以及 $c\in\mathbb F_L$。称 $q$ 是 $c$-前缀因果的，当且仅当对任意两个输入序列 $x_{0:L}$ 与 $\bar x_{0:L}$：

$$
x_j=\bar x_j,
\qquad
0\leq j\leq c,
$$

都蕴含两次执行中的 $q$ 相同。若 $c=-1$，该条件表示 $q$ 与整个输入序列无关。

若 $q$ 是一个动态产生的可选记录，则把它的值域扩展为：

$$
\mathcal Q_\bot
=
\mathcal Q\cup\{\bot\},
$$

其中 $\bot$ 表示该记录不存在。因此“$q$ 相同”同时要求两次执行中存在性与存在时的数值都相同。这里的 $q$ 仍只是可选语义对象；$q=\bot$ 不表示发生了一次带空值的计算记录。

若运行时为 $q$ 声明：

$$
\operatorname{frontier}(q)=c,
$$

则要求 $q$ 至少是 $c$-前缀因果的。因果前沿可以是保守上界，不要求一定是最小依赖 `token` 索引。定义 0.2 的一次 `token` 出现满足：

$$
\operatorname{frontier}(\xi_t)=t.
$$

这里不能只写成“值 $x_t$ 的因果前沿”：若两个位置恰好具有相同输入值，它们仍是不同的输入出现，并具有不同的位置索引。

> [!example] 如何读取因果前沿
> `frontier(q)=3` 只断言：只要两个输入序列的 $x_0,x_1,x_2,x_3$ 相同，$q$ 就必须相同。它不断言 $q$ 一定使用了这四个 `token`，也不记录具体经过了哪些路径；后者属于来源信息。

### 定义 2.1a：抽象逻辑事件头与事件值

给定有限事件种类集合 $\mathcal K$ 与带静态全序的事件标识符空间 $\mathsf{EID}$。一个合法逻辑事件头是六元组：

$$
h_e
=
(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e),
\tag{GD-2.0}
$$
^eq-logical-event-header

其中：

- $\eta_e\in\mathsf{EID}$ 是全局唯一且确定生成的逻辑事件标识符。它可以由事件种类、位置、时间戳、语义并列键和规范前驱标识符构造，但不能来自线程竞争顺序；标识符大小只用于稳定序列化，不能自行创造因果依赖。语义并列键的含义由所选语义配置固定；它不是事件标识符的别名。
- $\kappa_e\in\mathcal K$ 是事件种类。
- $\ell_e\in V\cup\{\mathtt{external}\}$ 是事件位置。
- $\theta_e\in\Theta$ 是事件值对后继可见的逻辑提交时间戳。
- $\Omega_e\subseteq[L]$ 是该事件直接联合处理或在外部接口上显式标识的归属支持集，即一组位置索引。它不是实际因果依赖集合，也不应写成“从 $0$ 到因果前沿的全部位置”来代替 $c_e$。
- $c_e\in\mathbb F_L$ 是事件值的有效因果前沿。

对常规节点事件，$\Omega_e$ 记录当前收件箱中被该事件直接消费的 `owner` 桶；它不包含仅通过节点前状态间接影响本事件的历史位置。配置 F 还可能产生一个不属于当前 $\Omega_e$ 的提升后输出 `owner=c_e`，因此 `support` 也不是“事件值中出现过的全部归属标签”。

对每个合法事件头 $h_e$，声明值空间 $\mathcal V_e$。一个逻辑事件实例是有序对：

$$
e=(h_e,\nu_e),
$$

其中：

$$
\nu_e\in\mathcal V_e.
$$

定义事件头和值投影：

$$
h(e)=h_e,
\qquad
\nu(e)=\nu_e.
$$

定义实际事件的字段投影：

$$
\operatorname{id}(e)=\eta_e,
\quad
\operatorname{kind}(e)=\kappa_e,
\quad
\operatorname{loc}(e)=\ell_e,
$$

$$
\operatorname{time}(e)=\theta_e,
\quad
\operatorname{support}(e)=\Omega_e,
\quad
\operatorname{frontier}(e)=c_e.
$$

符号 $e$ 始终表示完整事件实例，$\eta_e$ 只表示它的事件标识符，二者不能互换。实际事件集合只包含真正发生的事件。动态存在性不通过“值为 $\bot$ 的假事件”表达，而通过源事件值中的可选路由/消息记录表达。一个已经发生的节点事件仍可以把“无路由可见的隐藏表示”作为其结构化值的某个 $\bot$ 分量；这不表示该事件未发生。

这里的事件不是沿边传输的数据包。事件表示“一次计算已经发生”；消息是事件产生、随后沿空间边传播的产物。一个事件可以消费多条消息、更新一次节点状态，并产生零条或多条新消息。

### 定义 2.1b：抽象事件图与依赖边

给定一次有限执行的实际事件集合 $\mathcal E$，以及二元关系：

$$
\mathcal A\subseteq\mathcal E\times\mathcal E.
$$

定义事件图：

$$
D=(\mathcal E,\mathcal A).
$$

要求 $\mathcal A$ 中每个有序对都表示参考语义中的直接数据、状态或控制依赖：$e'$ 的事件头、存在性或值读取了 $e$ 产生的某个产物。该关系此处可以不完备，但不能加入没有语义依赖的任意次序边。

若 $(e,e')\in\mathcal A$，称 $e$ 是 $e'$ 的直接依赖，并记为：

$$
e\longrightarrow e'.
$$

若 $D$ 无有向环，则称其为逻辑事件 DAG。这里尚未规定哪些参考依赖必须进入 $\mathcal A$；第 7 节将为固定周期 Tide 执行实例化关系 $\mathcal A_L^P$，并定义依赖完备性。

### 定义 2.1c：固定边界事件头

定义边界事件种类集合：

$$
\mathcal K_{\mathrm{bdry}}
=
\{\mathtt{inject},\mathtt{readout},\mathtt{sample}\}.
$$

对每个 $t\in[L]$，定义必定发生的输入事件头：

$$
h_{e_t^{\mathrm{in}}}
=
(\eta_t^{\mathrm{in}},\mathtt{inject},s,
\theta_t^{\mathrm{in}},\{t\},t),
$$

以及必定发生的固定读出事件头：

$$
h_{e_t^{\mathrm{out}}}
=
(\eta_t^{\mathrm{out}},\mathtt{readout},z,
\theta_t^{\mathrm{out}},\{t\},t).
$$

自回归执行还定义采样事件头：

$$
h_{e_t^{\mathrm{sample}}}
=
(\eta_t^{\mathrm{sample}},\mathtt{sample},\mathtt{external},
\theta_t^{\mathrm{sample}},\{t\},t).
$$

给定序列执行不实例化采样事件。读出和采样事件的支持集 $\{t\}$ 表示它们显式对应第 $t$ 个外部读出位置；因果前沿 $t$ 才表示其值最多依赖输入前缀 $x_{0:t+1}$。边界事件的值空间与值在定义 7.1 中登记；本定义只固定事件恒等、种类、位置、时间戳、支持集与因果前沿。

### 定义 2.2：所在周期与周期内轮次偏移

对绝对轮次 $\tau\in\mathbb N$，定义其所处周期的索引：

$$
q_R(\tau)
=
\left\lfloor\frac{\tau}{R}\right\rfloor,
$$

以及周期内轮次偏移：

$$
r_R(\tau)
=
\tau-Rq_R(\tau).
$$

由欧几里得除法：

$$
0\leq r_R(\tau)<R.
$$

$q_R(\tau)$ 是全局时钟已经进入的周期编号，不是任意消息的归属 `token`。

### 定义 2.3：路径年龄与固定周期到达时间

给定 `token` 索引 $t\in[L]$、空间节点 $v\in V$ 与一条从 $s$ 到 $v$ 的空间路径 $p$。称有序对 $(t,p)$ 为路径计时见证：它描述“位置 $t$ 的输入若沿 $p$ 实际派发消息，这些消息何时到达”，但它本身不是消息实例、消息分支或实际发生的事件。

定义该路径计时见证的路径年龄：

$$
k(p)=|p|,
$$

绝对到达轮次：

$$
A_R(t,p)
=
Rt+|p|,
\tag{GD-2.1}
$$
^eq-fixed-arrival-round

以及到达时间戳：

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(A_R(t,p),i_{\mathrm{arrive}}).
\tag{GD-2.2}
$$
^eq-fixed-arrival-timestamp

路径年龄可以大于 $R$。此时，若该路径对应的消息分支实际存在，它会在 `token` $t+1$ 的注入边界之后才到达；固定周期本身不截断它。

### 推论 2.3a：最短路径在固定读出前提交

若 $p$ 是从 $s$ 到 $z$ 的最短路径，则 $|p|=R$，并且：

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(R(t+1),i_{\mathrm{arrive}}).
$$

由式 GD-0.3：

$$
(R(t+1),i_{\mathrm{arrive}})
<_{\Theta}
(R(t+1),i_{\mathrm{commit}})
<_{\Theta}
\theta_t^{\mathrm{out}}.
$$

因此，只要最短路径到达所触发的输出节点转移在本轮次正常执行，其已提交的状态可以被第 $t$ 个固定读出读取。

**证明。**

由 $|p|=R$ 与式 GD-2.1，到达轮次为 $Rt+R=R(t+1)$；阶段不等式直接来自式 GD-0.3。

<div class="qed" aria-label="证毕">∎</div>

### 定义 2.4：时间戳处可用的输入前缀

若 $L>0$，对任意 $\theta\in\Theta$，定义在 $\theta$ 之前已经完成注入的最大 `token` 索引：

$$
a_{R,L}(\theta)
=
\max
\left(
\{-1\}
\cup
\{t\in[L]\mid \theta_t^{\mathrm{in}}\leq_{\Theta}\theta\}
\right),
\tag{GD-2.3}
$$
^eq-available-prefix

其中 $\leq_{\Theta}$ 是由 $<_{\Theta}$ 诱导的非严格次序。

本文要求每个计算核只读取在其时间戳已经可见的输入位置和值。任意在时间戳 $\theta$ 产生并声明因果前沿的良构语义对象 $q$ 必须具有有效因果前沿，并满足：

$$
\operatorname{frontier}(q)
\leq
a_{R,L}(\theta)
\tag{GD-2.4}
$$
^eq-timestamp-frontier-bound

特别地，每个逻辑事件实例 $e$ 必须满足：

$$
\operatorname{frontier}(e)
\leq
a_{R,L}(\operatorname{time}(e)),
$$

并且 $\nu(e)$ 是定义 2.1 意义下的 $\operatorname{frontier}(e)$-前缀因果对象。动态事件存在性的前缀因果性必须在产生该事件的可选路由/消息记录上单独登记，不能由实际事件头自行推出。

特别地，在边界轮次 $R(t+1)$ 的读出阶段，下一次注入尚未发生，因此对每个 $t\in[L]$：

$$
a_{R,L}(\theta_t^{\mathrm{out}})=t.
\tag{GD-2.5}
$$
^eq-readout-prefix

**证明。**

输入值 $x_0,\ldots,x_t$ 的注入时间戳都不晚于 $\theta_t^{\mathrm{out}}$。若 $j>t$ 且 $j\in[L]$，则 $\theta_j^{\mathrm{in}}\geq_{\Theta}\theta_{t+1}^{\mathrm{in}}>_{\Theta}\theta_t^{\mathrm{out}}$；当 $t=L-1$ 时不存在这样的 $j$。代入式 [[#^eq-available-prefix|GD-2.3]] 即得式 GD-2.5。

<div class="qed" aria-label="证毕">∎</div>

### 例 2.5：不同输入位置的路径计时见证发生同刻碰撞

令汇聚节点就是输出节点 $z$，并考虑：

```text
s -> a -> b -> c -> z
s -> d ------------> z
```

记长路径为 $p_A=(s,a,b,c,z)$，短路径为 $p_B=(s,d,z)$。它们的长度分别为 $4$ 与 $2$。假设不存在更短的输入输出路径，则：

$$
R=d_{\min}=2.
$$

- 输入位置 A 的索引为 $0$，沿长路径到达 $z$ 的轮次为 $A_R(0,p_A)=0+4=4$。
- 输入位置 B 的索引为 $1$，沿短路径到达 $z$ 的轮次为 $A_R(1,p_B)=2+2=4$。

因此，若这两条路由都实际发生，它们产生的消息会在同一空间节点 $z$、同一逻辑到达时间戳 $(4,i_{\mathrm{arrive}})$ 汇聚。这里相等的是逻辑时间戳，不要求两条消息在物理实现中同时完成计算或写入缓冲区。

### 命题 2.6：归属保持分支中不能由空间节点与时间恢复消息的 `owner`

考虑配置 O/J 中两条从输入事件产生、此前未经过归属改标的消息分支。若它们分别保留 `owner=t_A` 与 `owner=t_B`，其中 $t_A,t_B\in[L]$ 且 $t_A\neq t_B$，并沿两条从 $s$ 到同一节点 $v$ 的路径 $p_A,p_B$ 传播，满足：

$$
Rt_A+|p_A|
=
Rt_B+|p_B|,
$$

则 $(v,A_R(t_A,p_A))$ 不能唯一确定到达消息当前带有哪个 `owner` 索引。因此，归属保持配置不能从空间节点与到达时间恢复 `owner`；后文定义消息时必须显式保留该字段。

**证明。**

两个路径计时见证给出的到达轮次分别为：

$$
\tau_A=Rt_A+|p_A|,
$$

$$
\tau_B=Rt_B+|p_B|.
$$

由题设：

$$
\tau_B
=
Rt_B+|p_B|
=
Rt_A+|p_A|
=
\tau_A.
$$

但两条消息分别保留不同的 `owner=t_A` 与 `owner=t_B`，所以 $(v,\tau)$ 不能唯一确定消息当前归属于哪个 `token`。

<div class="qed" aria-label="证毕">∎</div>

这个命题说明归属标签在 O/J 的归属保持分支中不是冗余字段。配置 F 还可能依据融合事件把后继消息的 `owner` 改为因果前沿；此时当前 `owner` 更不可能仅由原始输入位置、空间节点与到达时间恢复，而必须读取消息字段或重放完整产生关系。若把同刻到达、但当前归属不同的消息无标签合并，后续输出对齐、路由、损失、回放与归因都会失去明确语义。

### 命题 2.7：归属保持分支中的前序 `token` 晚到条件

取 $t_A<t_B$，并令两条路径 $p_A,p_B$ 都从 $s$ 到达同一空间节点 $v$。若配置 O/J 中两条实际消息分支分别保留 `owner=t_A` 与 `owner=t_B`，则位置 B 的消息先于位置 A 的消息到达，当且仅当：

$$
|p_A|-|p_B|
>
R(t_B-t_A).
$$

二者同刻到达，当且仅当上式中的 $>$ 改为 $=$。

**证明。**

由式 [[#^eq-fixed-arrival-round|GD-2.1]]：

$$
\tau_A=Rt_A+|p_A|,
\qquad
\tau_B=Rt_B+|p_B|.
$$

因此：

$$
\tau_B<\tau_A
$$

当且仅当：

$$
Rt_B+|p_B|
<
Rt_A+|p_A|,
$$

移项即得结论。同刻条件同理。

<div class="qed" aria-label="证毕">∎</div>

这个命题表明：即使输入/输出时钟固定，只要路径长度差超过输入位置的注入轮次差，一般 DAG 的归属保持分支仍会出现较晚输入位置的消息先到。这里的“归属逆序”只指消息到达同一空间节点的逻辑时间次序与 `owner` 索引次序相反；它不表示外部 `token` 的生成次序被改写。该事实由拓扑结构与固定 $R$ 共同决定，不由选择器改写时间戳。

## 3. 可选的双皮层空间结构

### 定义 3.1：输入/输出双皮层 DAG

设输入皮层为：

$$
G_I=(V_I,E_I),
$$

其执行方向从输入节点 $s$ 指向输入桥接节点 $b_I$。

设输出皮层为：

$$
G_O=(V_O,E_O),
$$

其执行方向从输出桥接节点 $b_O$ 指向输出节点 $z$。

假设：

$$
V_I\cap V_O=\varnothing.
$$

增加唯一单向桥接：

$$
(b_I,b_O).
$$

组合图定义为：

$$
G
=
\left(
V_I\cup V_O,\,
E_I\cup E_O\cup\{(b_I,b_O)\}
\right).
$$

$G_O$ 可以与 $G_I$ 反向同构，但反向同构只描述结构对应关系，不增加从输出皮层返回输入皮层的执行边。

### 引理 3.2：单向桥接保持 DAG 性质

若 $G_I$ 与 $G_O$ 都是 DAG，且不存在从 $V_O$ 指向 $V_I$ 的边，则定义 3.1 的组合图 $G$ 是 DAG。

**证明。**

假设 $G$ 中存在有向环。若该环完全位于 $V_I$ 或 $V_O$，分别与 $G_I$ 或 $G_O$ 是 DAG 矛盾。

若该环同时经过两侧，则它必须通过桥接 $(b_I,b_O)$ 从 $V_I$ 进入 $V_O$。要回到 $V_I$，环中必须存在一条从 $V_O$ 指向 $V_I$ 的边，但前提排除了这种边，矛盾。

所以 $G$ 无有向环。

<div class="qed" aria-label="证毕">∎</div>

## 4. 消息、收件箱与有限事件性

### 定义 4.1：带因果标签和时间戳的消息

给定带静态全序的逻辑消息标识符空间 $\mathsf{MID}$、元数据空间 $\mathcal U$ 与载荷空间 $\mathcal P$。若不同边使用不同载荷类型，可把 $\mathcal P$ 取为带边或类型标签的不交并。

一个消息实例是元组：

$$
m=(\iota,t,c,\theta,u,v,\mu,p),
$$

属于：

$$
\mathsf{MID}
\times[L]
\times\mathbb F_L
\times\Theta
\times V\times V
\times\mathcal U
\times\mathcal P,
$$

其中：

- $\iota$ 是全局唯一逻辑消息标识符；$m$ 是消息实例，$\iota$ 是它的标识符，二者不能互换。
- $t\in[L]$ 是消息的归属 `token` 索引，即 $\operatorname{owner}(m)=t$。
- $c\in\mathbb F_L$ 是满足定义 2.1 的因果前沿。
- $t\leq c$。当前语义把“是否存在一条标为 `owner=t` 的消息”也视为输入相关语义，因此其因果上界不能早于位置 $t$。即使数值载荷恰好忽略 $x_t$，这条带归属记录的存在性仍至少与位置 $t$ 对齐；若未来允许与输入无关的合成 owner 记录，必须另行修改这一契约。
- $\theta=(\tau,i_{\mathrm{arrive}})\in\Theta$ 是到达时间戳。
- $u\in V$ 是源节点。
- $v\in V$ 是目标节点。
- $(u,v)\in E$。
- $\mu\in\mathcal U$ 是元数据，例如来源槽位、源端口、路由标识符或分支谱系标识符；不需要元数据时可令 $\mathcal U$ 为单元素集合。
- $p\in\mathcal P$ 是载荷。

定义字段读取函数：

$$
\operatorname{id}(m)=\iota,
\qquad
\operatorname{owner}(m)=t,
$$

$$
\operatorname{frontier}(m)=c,
\qquad
\operatorname{arrival}(m)=\theta,
\qquad
\operatorname{src}(m)=u,
\qquad
\operatorname{dst}(m)=v.
$$

若 $\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})$，定义：

$$
\operatorname{arrivalRound}(m)=\tau.
$$

记所有满足上述约束的有效消息的集合为 $\mathcal R$。对节点 $v$，定义其入站消息记录空间：

$$
\mathcal R_v
=
\{m\in\mathcal R\mid\operatorname{dst}(m)=v\}.
$$

> [!important] 这是标题所说的“消息携带 `token` 归属信息”
> `owner(m)` 是消息记录的一部分，并随消息沿边传播。节点收到消息后可以按 `owner` 分桶、逐归属处理或联合处理；无论采用哪种方式，都不能在未定义新语义的情况下丢掉该字段。

每个边消息从派发时起就携带 `owner`，而不是等到发生汇聚时才临时补上。原因是一般 DAG 中未来是否会发生路径碰撞不能由当前局部消息预先排除。`owner` 只提供归属索引；要识别具体实例必须读取 `message_id`，要恢复完整来源必须读取显式产生/消费关系。

消息标识符使重复载荷仍保持为不同消息。逻辑消息标识符必须由产生事件标识符、局部输出槽位、已选空间边、`owner`、`frontier`、时间戳、来源槽位或其他已声明语义字段确定性生成；同一产生事件若能沿同一边派发多条消息，还必须包含规范消息序号。它不能来自依赖线程竞争顺序的全局自增计数。参考语义不依赖物理线程首先写入收件箱的顺序。

对每个输入位置 $t\in[L]$，定义不属于边消息集合的边界注入记录：

$$
b_t^{\mathrm{in}}
=
(t,\theta_t^{\mathrm{in}},s,x_t).
$$

该记录在第 7 节实例化为输入逻辑事件。它的归属索引与因果前沿都是 $t$，但它不是从某条空间边到达的消息。

### 定义 4.2：单位时延派发

若常规节点事件在绝对轮次 $\tau$ 的提交阶段，或输入事件在 $(\tau,i_{\mathrm{inject}})$，产生归属 `token` 索引为 $t'\in[L]$、因果前沿为 $c'\in\mathbb F_L$ 的输出记录，其中 $t'\leq c'$，并沿已选边 $(v,w)\in E$ 派发，则新消息必须满足：

$$
\operatorname{owner}(m')=t',
\qquad
\operatorname{frontier}(m')=c',
$$

$$
\operatorname{arrival}(m')
=
(\tau+1,i_{\mathrm{arrive}}),
\tag{GD-3}
$$
^eq-unit-delay-dispatch

$$
\operatorname{src}(m')=v,
\qquad
\operatorname{dst}(m')=w.
$$

派发步骤可以根据局部输出记录与已选空间边构造载荷、新消息标识符和其他元数据，但选择器与派发步骤都不能独立改写节点输出已声明的归属索引或因果前沿，也不能改写式 GD-3 决定的逻辑到达时间戳。

一个局部输出记录可以选择零条、一条或多条空间出边。若选择多条出边，每条边都产生一个具有独立 `message_id` 的消息实例；这些消息可以继承相同的 `owner` 和 `frontier`，但它们不是同一个消息。局部输出记录的数量与归属标签由节点转移语义决定，出边集合由选择器决定，消息实例由派发步骤物化；三者是不同操作。

### 定义 4.2a：消息产生、消费与跨边界延续

给定一次执行前缀或边界切面；令 $\mathcal E$ 是该前缀中已经发生的事件实例集合，$\mathcal M$ 是已经产生的消息实例集合。定义产生函数：

$$
\operatorname{producer}:\mathcal M\to\mathcal E,
$$

并要求对每个 $m\in\mathcal M$，事件 $\operatorname{producer}(m)$ 的事件值中包含派发 $m$ 的记录。定义部分消费函数：

$$
\operatorname{consumer}:\mathcal M\rightharpoonup\mathcal E.
$$

其中符号 $\rightharpoonup$ 表示部分函数。若消息已经到达并被节点事件消费，则 $\operatorname{consumer}(m)$ 有定义；若消息在该执行切面仍处于在途状态，则它尚未定义。因为这是函数，一个消息实例不能被两个不同事件重复消费。

在第 8 节的封闭有限冲刷执行结束后，所有已派发消息都已经到达并被消费，此时 $\operatorname{consumer}$ 在该执行的 $\mathcal M$ 上成为全函数。只有讨论中间边界切面和可接续 `decode` 的延续状态时，才需要保留尚未定义消费事件的在途消息。

消息实例的生命周期从产生事件派发它开始，到唯一消费事件消费它为止。消费事件可以产生零条、一条或多条后继消息，但这些后继都是新的消息实例；“没有后继消息”表示相应消息分支在消费事件处终止，不是原消息未被消费。

固定周期边界本身不删除、吸收或重写任何已经存在的消息。更精确地，对任意边界索引 $k\in[L]$，若消息 $m$ 在边界 $R(k+1)$ 的执行切面上已经产生但尚未被消费，且：

$$
\operatorname{arrivalRound}(m)>R(k+1),
$$

则 $m$ 在边界 $R(k+1)$ 之后仍保持为在途消息，并在其原定逻辑到达时间戳到达。读出、采样与下一输入位置的注入不执行隐式清除。

这里的边界切面取绝对轮次 $R(k+1)$ 的全部已定义阶段执行完毕之后；它是观察执行前缀的位置，不是额外的逻辑事件。

### 定义 4.2b：消息来源图、消息分支、分叉与汇聚

把事件实例和消息实例视为不同类型的顶点，取不交并。符号 $A\sqcup B$ 表示带来源标签的不交并，即使 $A$ 与 $B$ 作为普通集合恰有相同元素，它们在不交并中仍属于不同类型：

$$
\mathcal V_{\mathrm{msg}}
=
\mathcal E\sqcup\mathcal M.
$$

定义消息产生/消费边集合：

$$
\mathcal A_{\mathrm{msg}}
=
\{(\operatorname{producer}(m),m)\mid m\in\mathcal M\}
\cup
\{(m,\operatorname{consumer}(m))\mid
\operatorname{consumer}(m)\text{ 已定义}\}.
$$

称二部有向图：

$$
P_{\mathrm{msg}}
=
(\mathcal V_{\mathrm{msg}},\mathcal A_{\mathrm{msg}})
$$

为该执行的消息来源图。一条消息分支是 $P_{\mathrm{msg}}$ 中的一条有限有向路径。消息分支本身是线性的；完整消息来源图可以出现：

- **分叉**：一个事件产生两条或更多消息。
- **汇聚**：一个事件消费两条或更多消息。
- **终止**：一个消费事件不再产生相应后继消息。

因此不能把一个可能分叉、汇聚的完整传播过程定义成单一消息序列。多个消息分支可以具有相同 `owner`；一次汇聚也可以消费相同或不同 `owner` 的消息。`owner` 不标识消息分支，配置 F 对后继消息重新赋予 `owner` 也不会删除已经发生的产生/消费关系。

“分支谱系标识”只适合标识一条线性路径或作为规范化摘要。汇聚事件产生的后继消息具有多个父消息，若需要完整回放，必须在账本中记录排序后的父消息标识符集合或显式产生/消费边；单个标量 lineage 即使由父集合确定性哈希得到，也不能单独恢复完整来源 DAG。

在本文单位时延空间 DAG 中，每条消息从产生事件指向下一绝对轮次的消费事件，所以 $P_{\mathrm{msg}}$ 无环。完整来源信息还可以包含状态版本和控制依赖；这些关系由第 7 节的逻辑事件 DAG 表示，不能仅由 $P_{\mathrm{msg}}$、`owner` 或 `frontier` 恢复。

### 定义 4.3：按空间节点、逻辑到达时间和 `owner` 分桶的收件箱

对空间节点 $v$、绝对轮次 $\tau$ 与归属 `token` 索引 $t$，定义有限消息多重集：

$$
I_{v,\tau,t}
=
\left\{
m\ \middle|\
\operatorname{dst}(m)=v,\,
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}}),\,
\operatorname{owner}(m)=t
\right\}_{\mathrm{multi}}.
\tag{GD-4}
$$
^eq-general-owner-inbox

定义同刻到达 $v$ 的归属 `token` 索引集合：

$$
\mathcal O_{v,\tau}
=
\{t\in[L]\mid I_{v,\tau,t}\neq\varnothing\}.
$$

定义不按 `owner` 分桶的完整同刻收件箱：

$$
I_{v,\tau}
=
\biguplus_{t\in\mathcal O_{v,\tau}}
I_{v,\tau,t},
$$

其中 $\biguplus$ 表示保留重复消息的多重集并。称 $I_{v,\tau}$ 为空间节点 $v$ 在绝对轮次 $\tau$ 的逻辑到达批次。

$I_{v,\tau,t}$ 可以包含来自消息来源图中多条不同分支的消息。它们因为目标空间节点、完整逻辑到达时间戳和 `owner` 都相同而进入同一桶，但仍由各自的 `message_id` 保持为不同实例。

把它按 `token` 索引递增排列：

$$
O_{v,\tau}^{\uparrow}=(t_1,t_2,\ldots,t_m),
\qquad t_1<t_2<\cdots<t_m.
$$

### 定义 4.4：同一归属 `token`、同刻聚合

对每个节点 $v$，给定数值聚合空间 $X_v^{\mathrm{num}}$，并定义带因果前沿的节点输入空间：

$$
X_v
=
X_v^{\mathrm{num}}\times\mathbb F_L.
$$

给定确定性数值聚合器：

$$
\operatorname{Aggregate}_v:
\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\to X_v^{\mathrm{num}},
$$

其中 $\mathcal R_v$ 是到达 $v$ 的消息记录空间，$\mathcal M_{\mathrm{fin}}(\mathcal R_v)$ 表示其有限多重集。

先定义数值聚合结果：

$$
\bar x_{v,\tau,t}
=
\operatorname{Aggregate}_v(I_{v,\tau,t}).
\tag{GD-5}
$$
^eq-general-owner-aggregate

默认因果前沿为：

$$
c_{v,\tau,t}^{X}
=
\max_{m\in I_{v,\tau,t}}
\operatorname{frontier}(m).
$$

若聚合器能够证明忽略了某些因果前沿较高的消息，可以把 $c_{v,\tau,t}^{X}$ 取为更小但仍有效的因果前沿；不能在没有证明时降低标签。定义节点转移实际接收的带标签输入：

$$
x_{v,\tau,t}
=
(\bar x_{v,\tau,t},c_{v,\tau,t}^{X})
\in X_v.
$$

并定义投影：

$$
\operatorname{payload}(x_{v,\tau,t})
=
\bar x_{v,\tau,t},
\qquad
\operatorname{frontier}(x_{v,\tau,t})
=
c_{v,\tau,t}^{X}.
$$

如果聚合器与顺序无关，它直接作用于多重集。若业务语义要求顺序，必须先按固定字段，例如 `(source spatial node id, message id)`，做规范排序；不能使用物理到达竞争作为隐式顺序。

这里的“聚合”只处理同一个 $(v,\tau,t)$ 桶内的消息，不处理不同 `owner` 之间的关系。它与第 5 节的三种操作不同：

- 配置 O 对不同 `owner` 的桶按规定次序分别执行节点转移。
- 配置 J 联合读取多个 `owner` 桶，但仍分别产生带归属标签的局部输出记录。
- 配置 F 对多个 `owner` 桶做显式语义融合，只产生统一局部输出记录。

若后续计算需要区分桶内各消息分支，$\operatorname{Aggregate}_v$ 的输出必须保留带 `message_id` 的序列、多重集或等价的充分统计量。若它只返回不可逆求和等压缩值，则分支级数值区别在这个节点转移输入处已经被语义性丢弃；消息来源图仍能记录“哪些消息被消费”，但不能从聚合值中恢复各消息的数值贡献。

不同绝对轮次的消息不在本步骤聚合。同一个归属索引可以因不同路径长度在同一空间节点触发多个不同时间的节点事件：

$$
x_{v,\tau_1,t},
\qquad
x_{v,\tau_2,t},
\qquad
\tau_1\neq\tau_2.
$$

> [!important] 到达汇聚不自动等于一次统一节点事件
> 定义 4.3 的 $I_{v,\tau}$ 是一个逻辑到达批次。配置 O 会把这个批次按 `owner` 拆成多个有序节点事件；配置 J/F 才各自把整个批次作为一次联合或融合节点事件。因此，“多条消息同刻到达同一节点”描述收件箱事实，“节点一次统一处理它们”则是额外的转移语义选择。

> [!example] 分叉、同刻汇聚、归属语义与再次派发
> 假设位置 $2$ 的输入产生两个消息分支，消息 $m_1,m_2$ 都满足 `owner=2`，并经两条等长空间路径在 $(v,\tau,i_{\mathrm{arrive}})$ 到达。它们都是 $I_{v,\tau,2}$ 中的独立消息实例，先形成 $x_{v,\tau,2}$。若同刻还有 `owner=4` 的消息 $m_3$，则配置 O 分别处理归属桶 $2,4$，配置 J 联合计算但分别产生归属 $2,4$ 的局部输出记录，配置 F 则只产生一个统一归属记录。随后选择器才决定每个局部输出记录是否沿 $(v,w_1)$、$(v,w_2)$ 等空间边派发；每条已选边产生一个在 $\tau+1$ 到达的新消息实例。

### 引理 4.5：有限时间范围

若输入块长度为 $L>0$，则所有由这些输入出现触发并沿 $G$ 传播的消息都满足：

$$
0\leq\tau\leq R(L-1)+D.
\tag{GD-6}
$$
^eq-finite-horizon

**证明。**

对每条消息选择一个只用于存在性证明的时序见证 $(t,p)$：$t\in[L]$ 是某个通过入站消息触发当前产生事件的输入位置，$p$ 是从 $s$ 到当前目标的有向路径，并满足：

$$
\tau=Rt+|p|.
$$

从边界注入记录产生的第一条消息使用从 $s$ 开始的相应单边路径。若节点事件消费一条带见证 $(t,p)$ 的入站消息，则沿边 $(v,w)$ 发出的任意消息可以取延长路径 $p\mathbin{\|}(v,w)$ 作为见证。若联合或融合事件消费多条同刻消息，可以任选其中一条入站消息的见证进行延长，因为它们具有相同到达轮次。归属提升或因果前沿提升不改变绝对时间，也不影响这个存在性论证。

这里的 $t$ 不是新消息的 `owner`，也不是要求写入运行时的不可变来源字段；同一消息可能有多个可用时序见证。该辅助量只证明时间上界，不能用于恢复消息身份、分支或完整来源关系。

因为默认语义配置不在空时间戳自主发射消息，所有已派发的消息都可由上述归纳得到见证。又因为 $t\leq L-1$ 且 $|p|\leq D$：

$$
\tau=Rt+|p|
\leq
R(L-1)+D.
$$

<div class="qed" aria-label="证毕">∎</div>

### 引理 4.6：有限事件性

假设每次节点调用只沿有限出边集合发出有限条消息。对任意有限输入分块，一次执行产生的消息集合有限。

**证明。**

有限 DAG 中的有向路径数量有限。每个消息实例只对应一条空间边；消息来源图中的任意消息分支沿空间边方向前进，不能返回已经经过的空间节点。初始注入数有限，每个事件的扇出有限，所以对有限路径集合做分支展开后，总消息数有限。

<div class="qed" aria-label="证毕">∎</div>

有限不等于高效。一般 DAG 的路径数量可以随 $|V|$ 指数增长，因此后文仍需单独加入稀疏事件预算。

## 5. 节点持有状态与三种同刻/融合语义

### 定义 5.1：节点持有的持久上下文

每个节点 $v$ 有状态空间：

$$
\mathcal S_v,
$$

以及初始状态：

$$
S_v^0\in\mathcal S_v.
$$

其具体实现可以是：

- KV cache。
- Mamba/SSM 递归状态。
- 线性注意力累加器。
- 显式节点记忆。
- 其他具有分块正确性契约的状态。

严格语义配置要求每个可变状态位置只有一个持有节点。这里讨论的是“谁可以写这份状态”，不是消息的 `owner` 归属索引。若多个节点必须联合修改同一状态，应把它们封装为一个具有独立事件序列契约的超级节点或子图算子。

持久状态属于节点，不属于某个 `token`。为进行因果审计，把实际数值状态与其因果前沿写成增广状态：

$$
\widetilde S_v=(S_v,c_v^S),
\qquad
c_v^S\in\mathbb F_L.
$$

定义增广状态空间：

$$
\widetilde{\mathcal S}_v
=
\mathcal S_v\times\mathbb F_L.
$$

初始状态不依赖输入，声明：

$$
c_v^{S,0}=-1.
$$

因此增广初始状态为：

$$
\widetilde S_v^0=(S_v^0,-1).
$$

本页严格区分以下对象：

- **节点持久状态**：跨固定周期继续存在，并由后继节点事件读取。
- **状态版本**：某次提交后形成的一个确定快照；同一节点在执行中可以产生许多版本。
- **局部输出记录或隐藏表示**：当前节点转移的产物，只有经显式提交才成为持久状态，或经派发才成为消息载荷。
- **收件箱与临时聚合值**：当前事件输入，不因被读取就自动进入下一周期。
- **在途消息**：跨边界延续时属于全局延续状态的一部分，但不是任何节点的持久数值状态。

因此“模型状态”若不加限定可能同时指节点状态乘积与“节点状态加在途消息”的边界延续状态；后文涉及 `prefill`/`decode` 交接时必须明确写出所指状态空间。

对任意 $\widetilde S=(S,c^S)\in\widetilde{\mathcal S}_v$，定义投影：

$$
\operatorname{num}(\widetilde S)=S,
\qquad
\operatorname{frontier}(\widetilde S)=c^S.
$$

从本定义之后，所有参考转移的状态参数和值域都使用增广状态空间 $\widetilde{\mathcal S}_v$；数值计算核只需读取 $\operatorname{num}(\widetilde S)$，但运行时必须同时传播并提交因果前沿投影。配置 O/J 可以只把该标签用于审计，配置 F 则会用它决定新消息的 `owner` 归属索引。

对任意节点转移，若它读取 $n\in\mathbb N_{>0}$ 个语义对象，其因果前沿为：

$$
c_1,\ldots,c_n,
$$

则输出隐藏表示与后状态默认声明：

$$
c_{\mathrm{out}}
=
\max_{1\leq i\leq n}c_i.
$$

计算核若通过因果掩码、带版本的状态或独立证明得到更紧的依赖上界，可以声明更小的有效因果前沿；但带归属标签的路由或消息记录还必须覆盖其归属 `token`，因此不得把因果前沿降到 `owner` 索引以下。按归属排序或原子联合语义会保留局部输出记录的原 `owner`，即使 $c_{\mathrm{out}}>\operatorname{owner}$；这个不等式明确表示“记录仍标为较早输入位置，但数值已经依赖更晚输入前缀”的归属与因果依赖错位。

因此：

```text
消息 / 隐藏表示 / 路由记录 -> 归属索引 + 因果前沿
持久上下文                -> 持有节点 + 因果前沿
```

### 定义 5.2：同刻归属 `token` 元组

对非空归属 `token` 索引集合：

$$
O_{v,\tau}^{\uparrow}=(t_1,\ldots,t_m),
$$

定义节点 $v$ 在时间 $\tau$ 的按归属 `token` 索引组织的输入元组：

$$
B_{v,\tau}
=
\bigl(
(t_1,x_{v,\tau,t_1}),
\ldots,
(t_m,x_{v,\tau,t_m})
\bigr).
$$

该元组的顺序由 `token` 索引唯一决定，不依赖运行时调度。

定义 4.3 已给出完整同刻收件箱 $I_{v,\tau}$。配置 F 直接对该逻辑到达批次做一次联合计算。

默认严格语义配置中，没有收件箱事件的节点状态保持不变。若模型需要在空时间戳执行衰减，应另行定义：

$$
\operatorname{Idle}_v:
\mathbb N\times\widetilde{\mathcal S}_v
\to
\widetilde{\mathcal S}_v,
$$

并把所有空时间戳更新纳入第 7 节定义的节点参考与分块产物。本文后续公式取 $\operatorname{Idle}_v(\tau,\widetilde S)=\widetilde S$；非平凡空闲/衰减是相同证明框架下的扩展，不是免费省略项。

#### 定义 5.2a：节点的绝对时间事件次序

对同一节点的两个“按归属 `token` 划分的事件”次序键：

$$
k=(\tau,t),
\qquad
k'=(\tau',t'),
$$

定义：

$$
k\prec_v k'
$$

当且仅当：

$$
\tau<\tau',
$$

或：

$$
\tau=\tau'
\quad\text{且}\quad
t<t'.
$$

因此节点状态首先按绝对时间演进；只有绝对时间相同，才使用归属 `token` 的索引打破并列。

#### 例 5.2b：跨时间的归属 `token` 逆序

取固定周期 $R=2$。设 $v$ 是一个具有出边 $(v,z)$ 的中间空间节点，且全图最短输入输出路径为 $(s,v,z)$，所以 $R=d_{\min}=2$。消息 A 的归属 `token` 索引为 $0$，沿长度 $4$ 的路径到达 $v$；消息 B 的归属 `token` 索引为 $1$，沿直接边 $(s,v)$ 到达 $v$。二者到达轮次为：

$$
\tau_A=R\cdot 0+4=4,
\qquad
\tau_B=R\cdot 1+1=3.
$$

虽然 $t_A<t_B$，但在绝对时间事件次序中：

$$
(\tau_B,t_B)\prec_v(\tau_A,t_A).
$$

所以 B 的短路径事件会先更新节点状态，A 的晚到事件可能读取 B 的影响。后文的“按归属排序”只规定同一 $\tau$ 内的顺序，不消除这种跨时间归属逆序。

> [!summary] 三种同刻语义先看直观区别
> | 配置 | 同一节点、同一时间戳收到 A/B 时怎么计算 | 发出的消息归属 |
> | --- | --- | --- |
> | O：按归属排序 | 先处理 A 并提交状态，再处理 B；B 可以读取 A 的更新 | 分别保留 A、B |
> | J：原子联合 | A/B 一次联合计算，只提交一次状态，但仍分别产生 A、B 的输出记录 | 分别保留 A、B |
> | F：因果前沿融合 | A/B 与前状态一次融合，只产生一个统一输出 | 不再产生分别标为 A/B 的后继记录；统一记录的 `owner` 提升为本次因果前沿 |
>
> O 与 J 可以在满足式 GD-10 时成为同一语义的不同实现；F 主动改变输出记录的区分方式和归属标签，是语义商，不只是执行优化。

### 5.3 配置 O：同一时间戳内按归属 `token` 顺序执行

#### 定义 5.3：单一归属 `token` 的事件转移

给定数值隐藏表示空间 $H_v$。定义路由可见的带标签隐藏表示空间：

$$
\mathcal Z_v
=
\{\bot\}
\uplus
(H_v\times\mathbb F_L),
$$

其中 $\uplus$ 表示不交并。若 $z=(h,c)\in H_v\times\mathbb F_L$，定义：

$$
\operatorname{payload}(z)=h,
\qquad
\operatorname{frontier}(z)=c.
$$

一个带归属标签的输出记录是有序对 $r=(t,z)\in[L]\times\mathcal Z_v$。其中 $t$ 是归属 `token` 索引，定义 $\operatorname{owner}(r)=t$；当 $z\neq\bot$ 时，定义 $\operatorname{frontier}(r)=\operatorname{frontier}(z)$，并要求：

$$
\operatorname{owner}(r)
\leq
\operatorname{frontier}(r).
$$

$\bot$ 表示该事件已执行，但不产生路由可见的隐藏表示。节点 $v$ 的单事件转移是确定函数：

$$
\mathcal T_v:
\mathbb N\times\mathbb N\times X_v\times\widetilde{\mathcal S}_v
\to
\mathcal Z_v\times\widetilde{\mathcal S}_v.
$$

输入的两个自然数依次是归属 `token` 索引 $t$ 与绝对时间 $\tau$。返回的带标签隐藏表示与后状态必须满足定义 5.1 的因果前沿传播规则。

#### 定义 5.4：按归属 `token` 排序的同刻转移

给定：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad t_1<\cdots<t_m,
$$

以及进入该时间戳前的增广状态 $\widetilde S^{(0)}\in\widetilde{\mathcal S}_v$。递归定义：

$$
(z_i,\widetilde S^{(i)})
=
\mathcal T_v(t_i,\tau,x_i,\widetilde S^{(i-1)}),
\qquad i=1,\ldots,m.
\tag{GD-7}
$$
^eq-owner-ordered-group

该时间戳按归属 `token` 划分的输出与提交后状态分别为：

$$
Z_{v,\tau}^{\mathrm{ord}}
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr),
$$

其中每个非 $\bot$ 的 $z_i$ 都显式包含因果前沿，不再省略该字段。

$$
\widetilde S^+
=
\widetilde S^{(m)}.
$$

若 A、B 同刻到达且 $t_A<t_B$，则 B 的转移读取 A 已经更新后的状态。因果方向是：

$$
A\longrightarrow B.
$$

“按归属排序”是同一时间戳内的参考语义；同一空间节点的完整事件序列仍按定义 5.2a 的 $(\tau,t)$ 字典序次序演进。它不要求物理实现真的逐个归属 `token` 循环。若能证明一个因果掩码、扫描或其他批量计算核等于式 [[#^eq-owner-ordered-group|GD-7]]，则可以联合执行。

### 5.4 配置 J：同刻联合计算但保留各自归属

#### 定义 5.5：联合转移与整体状态增量

定义 $\mathcal B_v$ 为所有有限的、按归属 `token` 索引组织的输入元组的集合。其任意元素具有形式：

$$
B
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad
t_1<\cdots<t_m.
$$

其中 $m\in\mathbb N_{>0}$、$t_i\in[L]$ 且 $x_i\in X_v$。

定义 $\mathcal Z_v^\star$ 为所有具有相同归属 `token` 键形式的有限带标签隐藏表示元组的集合：

$$
Z
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr).
$$

其中 $z_i\in\mathcal Z_v$。

调用 $\mathcal J_v$ 时，输出元组必须与输入元组使用完全相同的归属 `token` 键序列；若某个归属 `token` 不产生隐藏表示，则相应位置写为 $\bot$。

对节点 $v$，给定增量空间 $\Delta_v$、提交函数：

$$
\operatorname{Commit}_v:
\widetilde{\mathcal S}_v\times\Delta_v
\to\widetilde{\mathcal S}_v,
$$

并要求 $\operatorname{Commit}_v$ 是确定函数，且其返回状态的因果前沿投影满足定义 5.1 的有效因果前沿规则；$\Delta_v$ 可以携带数值增量与计算该标签所需的审计信息。

以及原子联合转移：

$$
\mathcal J_v:
\mathbb N\times\mathcal B_v\times\widetilde{\mathcal S}_v
\to
\mathcal Z_v^\star\times\Delta_v.
$$

对任意时间戳 $\tau$、归属 `token` 元组 $B_{v,\tau}$ 与进入该时间戳前的增广状态 $\widetilde S$，定义：

$$
\mathcal J_v(\tau,B_{v,\tau},\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{joint}},
\Delta_{v,\tau}
\right),
\tag{GD-8}
$$
^eq-atomic-joint-transition

其中：

$$
Z_{v,\tau}^{\mathrm{joint}}
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr)
$$

仍为按归属 `token` 索引组织的输出；每个非 $\bot$ 的 $z_i$ 显式包含经过证明或按默认最大值规则得到的因果前沿。状态只在联合计算结束后提交一次：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau}).
\tag{GD-9}
$$
^eq-atomic-joint-commit

定义联合转移与提交的组合：

$$
\operatorname{Atomic}_v(\tau,B_{v,\tau},\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{joint}},
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau})
\right).
\tag{GD-9a}
$$
^eq-atomic-joint-composed

$\Delta_{v,\tau}$ 属于节点的整体状态更新，不要求归属于某个单独 `token`。为了回放与归因，可以额外保留按归属 `token` 划分的增量分解，但它不是数学正确性的必要字段。

原子联合允许：

- 所有归属 `token` 读取同一个前状态。
- 联合计算核比较多个归属 `token` 的输入。
- 每个归属 `token` 的输出可以依赖同刻其他归属 `token`。
- 联合计算核使用归属 `token` 索引构造三角掩码。

它不允许把多个归属 `token` 变成一个永久无归属的在途消息。出站记录仍必须按归属 `token` 分开。

#### 定义 5.6：同刻按归属 `token` 保持因果的联合算子

对 $t\in\mathcal O_{v,\tau}$，定义归属 `token` 前缀：

若：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
$$

并且 $t=t_j$，则：

$$
B_{v,\tau}^{\leq t}
=
\bigl((t_1,x_1),\ldots,(t_j,x_j)\bigr).
$$

若归属 `token` $t$ 的隐藏表示与路由决策只依赖：

$$
(\widetilde S,\tau,B_{v,\tau}^{\leq t}),
$$

而不依赖归属 `token` 索引大于 $t$ 的输入，则称联合算子在该时间戳内满足按归属 `token` 的因果性。

这是比任意联合更强的约束。任意联合只保证绝对时间语义；它不自动保证按 `token` 归属划分的前缀因果性。

### 定义 5.7：联合算子与有序折叠等价

把定义 5.4 的递归结果记为：

$$
\operatorname{GroupFold}_{\mathcal T_v}(\tau,B,\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{ord}},
\widetilde S^{(m)}
\right).
\tag{GD-9b}
$$
^eq-owner-group-fold

若对任意 $\tau$、任意归属 `token` 元组 $B\in\mathcal B_v$ 和任意增广状态 $\widetilde S\in\widetilde{\mathcal S}_v$：

$$
\operatorname{Atomic}_v(\tau,B,\widetilde S)
=
\operatorname{GroupFold}_{\mathcal T_v}(\tau,B,\widetilde S),
\tag{GD-10}
$$
^eq-joint-ordered-equivalence

则称原子联合算子与按归属 `token` 排序的分组折叠等价。这里要求相等的是：

- 每个归属 `token` 的隐藏表示。
- 每个归属 `token` 的路由可见记录。
- 时间戳结束后的状态。

只比较整体增量或最终状态不足以建立等价。

### 命题 5.8：折叠等价的联合执行不改变语义

若式 [[#^eq-joint-ordered-equivalence|GD-10]] 对节点 $v$ 成立，则在该节点上用 $\mathcal J_v$ 一次执行整个时间戳分组，与按归属 `token` 顺序执行 $\mathcal T_v$ 得到相同的可观察产物。

**证明。**

这是式 [[#^eq-joint-ordered-equivalence|GD-10]] 的直接展开：定义已经要求按归属 `token` 划分的输出、路由可见记录与最终状态全部相等。

<div class="qed" aria-label="证毕">∎</div>

### 例 5.9：最终状态相同但语义不同

本例只写数值载荷，并假设两种实现使用相同的合法因果前沿标签；因此省略式中的增广状态与带标签隐藏表示外壳。

令：

$$
S\in\mathbb R,
$$

单事件转移为：

$$
\mathcal T(x,S)=(S+x,S+x).
$$

取：

$$
S=0,\qquad x_A=1,\qquad x_B=2.
$$

按归属 `token` 排序的折叠得到：

$$
h_A=1,\qquad h_B=3,\qquad S^+=3.
$$

若快照联合分别从旧状态计算，再把增量相加，则可能得到：

$$
h_A=1,\qquad h_B=2,\qquad S^+=3.
$$

两者最终状态都是 $3$，但 B 的隐藏表示不同，所以后续路由与输出也可能不同。

### 5.10 配置 F：同刻融合并把输出归属提升到因果前沿

#### 定义 5.10：融合因果前沿

给定节点 $v$ 在时间 $\tau$ 的非空完整收件箱 $I_{v,\tau}$ 与增广前状态 $\widetilde S$，记：

$$
c_v^{S,-}
=
\operatorname{frontier}(\widetilde S).
$$

定义本次融合的因果前沿：

$$
c_{v,\tau}^{\star}
=
\max
\left(
\{c_v^{S,-}\}
\cup
\{\operatorname{frontier}(m)\mid m\in I_{v,\tau}\}
\right).
\tag{GD-F1}
$$
^eq-frontier-fusion-max

因为 $I_{v,\tau}$ 非空，且每条消息都满足 $0\leq\operatorname{owner}(m)\leq\operatorname{frontier}(m)$，所以 $c_{v,\tau}^{\star}\in[L]$；它不会在融合事件中取值 $-1$。

这个定义必须读取前状态的因果前沿。若当前输入只有 A、B，但前状态已经受 C 影响且 $C>B$，则：

$$
c_{v,\tau}^{\star}=C,
$$

不能把新输出错误标记为 B。

#### 定义 5.11：原子融合转移

因果前沿融合计算核是确定函数：

$$
\mathcal F_v:
\mathbb N
\times
\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\times
\widetilde{\mathcal S}_v
\to
(H_v\cup\{\bot\})
\times
\Delta_v.
$$

它对完整同刻收件箱与增广前状态做一次联合计算：

$$
\mathcal F_v(\tau,I_{v,\tau},\widetilde S)
=
(h^\star,\Delta^\star).
\tag{GD-F2}
$$
^eq-frontier-fusion-transition

增广状态仍通过 $\operatorname{Commit}_v$ 一次提交：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta^\star),
$$

并要求其因果前沿投影满足：

$$
\operatorname{frontier}(\widetilde S^+)
=
c_{v,\tau}^{\star}.
$$

若 $h^\star\neq\bot$，该时间戳只产生一个统一输出记录，其归属 `token` 索引取为 $c_{v,\tau}^{\star}$：

$$
Z_{v,\tau}^{\mathrm{front}}
=
\bigl((c_{v,\tau}^{\star},z^\star)\bigr),
\tag{GD-F3}
$$
^eq-frontier-owned-output

其中：

$$
z^\star
=
(h^\star,c_{v,\tau}^{\star})
\in
\mathcal Z_v,
$$

且该记录满足：

$$
\operatorname{owner}(c_{v,\tau}^{\star},z^\star)
=
\operatorname{frontier}(z^\star)
=
c_{v,\tau}^{\star}.
$$

所有出站消息都继承这个归属索引和因果前沿。原始 A/B 消息分支及其汇聚关系可以保存在消息来源图或元数据中，但 A/B 不再各自产生独立的后继局部输出记录。也就是说，F 在该融合事件之后只建立一类统一归属的后继消息；它不会抹去已经发生的来源关系，但会改变后继输出的可区分语义。该操作是明确的语义商，而不是对 O 或 J 的免费重排。

#### 例 5.11a：A/B 统一发射与前状态污染

令 A、B 的 `token` 索引分别为：

$$
A=0,
\qquad
B=1.
$$

若同刻收件箱只含 A/B，且前状态因果前沿不超过 B，则：

$$
c^\star
=
\max(c_v^{S,-},0,1)
=
1,
$$

所以联合计算可以只发射一个 `owner=B`、`frontier=B` 的输出。

若前状态已经受 `token` C 影响，且：

$$
C=2>B,
\qquad
c_v^{S,-}=2,
$$

则：

$$
c^\star
=
\max(2,0,1)
=
2.
$$

此时数值计算即使当前只混合 A/B，也不能把输出标记为 B；必须标记为 C，或改用不含 C 的带版本的/带掩码的状态。

#### 定义 5.11b：因果前沿融合路由原语

定义节点 $v$ 的出边集合：

$$
\operatorname{Out}(v)
=
\{(v,u)\in E\}.
$$

因果前沿融合路由原语是确定函数：

$$
\operatorname{Route}_v^{\mathrm{front}}:
\mathbb N\times([L]\times\mathcal Z_v)
\to
2^{\operatorname{Out}(v)}.
$$

它只能读取绝对时间、统一输出记录与静态参数；对 $z=\bot$ 返回空集。沿任一已选边生成的消息必须保留该输出的归属索引和因果前沿，且消息标识符、元数据与载荷构造都必须是确定函数。第 6 节将在此原语上增加候选分数，并定义另外两种语义配置的选择器。

#### 引理 5.12：前缀因果组合

给定 $n\in\mathbb N_{>0}$。设语义对象：

$$
q_1,\ldots,q_n
$$

分别具有有效因果前沿：

$$
c_1,\ldots,c_n.
$$

若 $f$ 是不读取其他输入 `token` 数据的确定函数，令：

$$
q=f(q_1,\ldots,q_n)
$$

并定义：

$$
c^\star
=
\max_{1\leq i\leq n}c_i,
$$

则 $q$ 是 $c^\star$-前缀因果的。

**证明。**

取任意两个在前缀 $0{:}c^\star$ 上相同的输入序列。因为每个 $c_i\leq c^\star$，两次执行中所有 $q_i$ 都相同。$f$ 是确定函数且不读取其他输入 `token` 数据，所以两次得到的 $q$ 相同。

<div class="qed" aria-label="证毕">∎</div>

#### 定理 5.13：因果前沿融合的 `token` 前缀不变量

假设：

1. 初始状态因果前沿为 $-1$。
2. 定义 2.1c 的输入事件 $e_t^{\mathrm{in}}$ 的归属支持集为 $\{t\}$，因果前沿为 $t$。
3. 每个数值计算核只读取其显式收件箱、前状态、静态参数与逻辑元数据；路由使用定义 5.11b 的纯函数。
4. 每次融合按式 [[#^eq-frontier-fusion-max|GD-F1]] 更新状态因果前沿，并按式 [[#^eq-frontier-owned-output|GD-F3]] 标记统一输出。

则任意因果前沿融合状态或消息，若其因果前沿与归属索引均为 $c$，其数值内容只依赖：

$$
x_0,\ldots,x_c.
$$

特别地，不会出现一个 `owner=A` 的晚到消息在融合中读取 B 后，其统一后继消息仍标记为 `owner=A`；统一记录的归属至少被提升到当前因果前沿。

**证明。**

沿绝对时间流式执行归纳。初始状态与输入序列无关，所以因果前沿 $-1$ 有效；输入出现 $\xi_t=(t,x_t)$ 的因果前沿 $t$ 有效。

假设某次融合的前状态与全部收件箱消息都具有有效因果前沿。式 [[#^eq-frontier-fusion-max|GD-F1]] 取这些因果前沿的最大值 $c^\star$。由引理 5.12，$\mathcal F_v$ 产生的 $h^\star$、$\Delta^\star$ 与提交后的数值状态都是 $c^\star$-前缀因果的。式 [[#^eq-frontier-owned-output|GD-F3]] 又把输出的 `owner` 与 `frontier` 都设为 $c^\star$，所以不变量被保持。

定义 5.11b 的路由原语是这些前缀因果输出、绝对时间与静态参数的确定函数，所以已选路由的存在性也保持同一个因果前沿上界。单位时延空间派发只复制已经有效的归属索引和因果前沿，不读取新的 `token` 数据。对所有绝对时间及其中的节点事件重复上述论证，结论成立。

<div class="qed" aria-label="证毕">∎</div>

#### 推论 5.13a：依赖边上的因果前沿单调性

对因果前沿融合逻辑事件 $e$，使用定义 2.1a 的事件级因果前沿。输入事件取 `token` 索引；节点融合事件取式 GD-F1 的 $c_{v,\tau}^{\star}$；读出/采样事件取对应固定周期前缀索引。

在定理 5.13 的前提下，对因果前沿融合执行的任意逻辑依赖边：

$$
e\longrightarrow e',
$$

都有：

$$
\operatorname{frontier}(e)
\leq
\operatorname{frontier}(e').
$$

因此有限逻辑事件 DAG 可以先按因果前沿递增分组，再在同一因果前沿内取拓扑序；不存在从较大因果前沿指向较小因果前沿的依赖边。

**证明。**

空间派发保持归属索引和因果前沿不变，所以空间依赖边上因果前沿相等。局部状态或融合依赖的输出因果前沿由式 [[#^eq-frontier-fusion-max|GD-F1]] 取所有输入与前状态因果前沿的最大值，所以不小于任一前驱的因果前沿。

对边界依赖，第 $t$ 个读出/采样事件的因果前沿都是 $t$；由式 GD-2.4，任何在 $\theta_t^{\mathrm{out}}$ 前可见的状态前驱，其因果前沿都不超过 $t$。自回归采样到下一输入的边从因果前沿 $t$ 指向 $t+1$。输入事件没有更早的 `token` 数据前驱。

因此每条事件依赖边上因果前沿单调不减。把有限事件顶点按因果前沿分组后，跨组边只会从较小组指向较大组；每个同因果前沿诱导子图仍是 DAG，所以可在组内取拓扑序。

<div class="qed" aria-label="证毕">∎</div>

这个推论使有限逻辑事件 DAG 可以先按因果前沿分组：因果前沿是事件值输入前缀依赖的上界。但它仍不推出每个因果前沿或 `token` 恰好产生一个输出读出。

#### 命题 5.14：提升因果前沿不自动带来高性能 `prefill`

式 [[#^eq-frontier-fusion-max|GD-F1]] 中的 $\max$ 是满足结合律的归约，可以低成本批量计算。但数值状态若按时间戳分组 $G_0,\ldots,G_{q-1}$ 满足：

$$
S_{j+1}=\Phi_{G_j}(S_j),
$$

则任意 $\Phi_{G_j}$ 仍形成：

$$
S_0\to S_1\to\cdots\to S_q
$$

的顺序依赖链。要获得 Transformer/Mamba 意义上的高性能 chunk prefill，还需要至少一种额外结构：

- $\Phi_{G_j}$ 有紧凑表示，并在函数组合下闭合，可用并行/分块扫描。
- 全部输出可由因果掩码、分段注意力或其他因果批量计算核联合计算。
- 节点转移是 `token` 局部或分组局部，不读取前序可变状态。

例如仿射递推：

$$
S_{j+1}=A_jS_j+b_j
$$

可以通过满足结合律的有序对组合做扫描；Mamba/SSM 属于这一方向。因果注意力则通过带掩码的批量计算核获得 `prefill`。因果前沿融合解决的是归属与因果标记问题，不替代这些数值收缩。

### 5.15 三种语义配置的边界

| 语义配置 | 同刻计算 | 出站消息的归属 | `owner` 与 `frontier` 的关系 | 高性能前提 |
| --- | --- | --- | --- | --- |
| O：按归属排序 | A 提交后 B 读取 | 分别保留 A、B | `frontier` 可大于 `owner`；必须显式记录 | 因果批量/扫描 |
| J：原子联合 | A/B 与前状态一次联合计算，保留按归属输出 | 分别保留 A、B | 任意联合不自动保证按归属前缀因果；需分别登记 | 联合分块契约 |
| F：因果前沿融合 | A/B 与前状态一次联合计算，只发射统一输出 | 提升为全部依赖的最大因果前沿 | `owner=frontier`，并由定理 5.13 给出前缀上界 | 仍需扫描、因果批量或无状态分组计算核 |

### 5.16 节点转移、归属语义、路由与派发的边界

对任意配置，一次节点处理都必须按以下概念顺序解释：

1. 收件箱按 $(v,\tau,t)$ 分桶，并在桶内形成 $x_{v,\tau,t}$。
2. O/J/F 节点转移读取这些输入和节点前状态，决定产生多少个局部输出记录、每个记录的数值、`owner`、`frontier` 以及状态更新。
3. 选择器逐个或联合读取已经形成的局部输出记录，决定每个记录选择哪些空间出边。
4. 派发步骤对每个“局部输出记录、已选空间边”组合创建一个新的消息实例，并把到达时间戳设为下一绝对轮次。

因此，“出口 `owner` 规则”和“向哪里路由”不是同一个规则。前者属于节点转移参考语义，后者属于选择器。选择出边也不等于下游空间节点已经执行；它只产生下一轮次到达的消息，消息到达并形成非空收件箱后，下游节点事件才会实例化。

## 6. 一般 DAG 上的路由

### 定义 6.1：局部候选分数

对空间节点 $v$ 在绝对轮次 $\tau$ 产生的非空带标签局部输出记录：

$$
(t,z),
\qquad
z=(h,c)\in H_v\times\mathbb F_L,
$$

以及每条出边 $(v,u)\in E$，定义：

$$
s_{v,\tau,t\to u}
=
g_{v\to u}(h)
+b_{v\to u}
+d_{v\to u}(t,\tau).
\tag{GD-11}
$$
^eq-general-routing-score

其中：

- $g_{v\to u}:H_v\to\mathbb R$ 是学习得到的内容分数。
- $b_{v\to u}\in\mathbb R$ 是静态的学习或配置偏置。
- $d_{v\to u}:[L]\times\mathbb N\to\mathbb R$ 是只读取归属 `token` 索引、绝对时间与边/节点静态配置的确定性先验。

三项都不读取此前 `token` 的实际硬路由计数。

### 定义 6.2：保持标签的纯选择器

配置 O 给定确定函数：

$$
\rho_v^{\mathrm{ord}}:
\mathbb N\times[L]\times\mathcal Z_v
\to
2^{\operatorname{Out}(v)},
$$

其中 $2^{\operatorname{Out}(v)}$ 表示 $\operatorname{Out}(v)$ 的幂集。

并定义：

$$
A_{v,\tau,t}
=
\rho_v^{\mathrm{ord}}(\tau,t,z)
\subseteq
\operatorname{Out}(v).
$$

要求 $\rho_v^{\mathrm{ord}}(\tau,t,\bot)=\varnothing$。

配置 O 中，$A_{v,\tau,t}$ 只能读取归属 `token` $t$ 对应的 $z$ 与静态配置。需要由节点状态影响路由的信息，必须先由 $\mathcal T_v$ 显式写入 $z$ 的载荷；选择器不再隐式选择读取提交前还是提交后的状态视图。

令 $\mathcal A_v^\star$ 为所有有限的、按归属 `token` 索引组织的已选边集合元组：

$$
\bigl((t_1,A_1),\ldots,(t_m,A_m)\bigr),
\qquad
m\in\mathbb N_{>0},
\qquad
t_i\in[L],
\qquad
t_1<\cdots<t_m,
\qquad
A_i\subseteq\operatorname{Out}(v).
$$

配置 J 给定确定函数：

$$
\rho_v^{\mathrm{joint}}:
\mathbb N\times\mathcal Z_v^\star
\to
\mathcal A_v^\star.
$$

它读取 $\tau$ 与整个 $Z_{v,\tau}^{\mathrm{joint}}$，并返回具有完全相同归属 `token` 键序列的已选边集合元组：

$$
\bigl((t,A_{v,\tau,t})\bigr)_{t\in O_{v,\tau}^{\uparrow}}
=
\rho_v^{\mathrm{joint}}
\left(
\tau,Z_{v,\tau}^{\mathrm{joint}}
\right).
$$

因此联合选择器可以比较同刻多个带归属标签的隐藏表示，但联合转移的前状态和后状态可见性已经在 $Z_{v,\tau}^{\mathrm{joint}}$ 的定义中固定，不由选择器临时决定。

配置 F 只有一个统一记录：

$$
(t,z)
=
\left(
c_{v,\tau}^{\star},
z^\star
\right),
$$

配置 F 使用定义 5.11b 的路由原语，并只对该统一记录选择：

$$
A_{v,\tau,t}
=
\operatorname{Route}_v^{\mathrm{front}}(\tau,(t,z)).
$$

无论使用哪种语义配置，选择器都必须：

- 确定性处理并列消解。
- 只选择 $v$ 的出站边。
- 对每个出站消息保留节点输出已声明的 `owner` 与 `frontier`；归属提升只能发生在定义 5.11 的融合转移内。
- 不根据路由结果追溯修改已经提交的同刻节点状态，除非这种修改已写入节点转移契约。

若选择器具有可变状态，该状态必须由唯一节点持有，并纳入 $\widetilde{\mathcal S}_v$ 以及第 7 节定义的节点参考/分块契约。这足以定义正确性，但不自动提供高性能。严格高性能语义进一步要求：`affectcount/selectcount` 一类跨事件反馈要么删除，要么给出独立的扫描或批量收缩证明。

### 定义 6.3：已选载荷派发

若带标签输出为 $(t,z)$、$z=(h,c)$，且 $(v,u)\in A_{v,\tau,t}$，给定载荷子类型 $\mathcal P_{v\to u}\subseteq\mathcal P$ 与投影 $P_{v\to u}:H_v\to\mathcal P_{v\to u}$，定义：

$$
p'
=
P_{v\to u}(h),
$$

并发出满足式 [[#^eq-unit-delay-dispatch|GD-3]] 的消息：

$$
m'
=
(\iota',t,c,(\tau+1,i_{\mathrm{arrive}}),v,u,\mu',p').
$$

其中 $\iota'\in\mathsf{MID}$ 与 $\mu'\in\mathcal U$ 必须由源事件标识符、已选边、归属索引、因果前沿、来源槽位与分支谱系等已声明字段确定性生成，不能依赖物理线程竞争顺序。

不同归属 `token` 可以选择同一边。即使源、目标、时间戳和载荷相同，它们仍是 `owner` 不同的两条消息。

### 备注 6.4：A 影响后续路由的三条语义路径

配置 O 中，A 可以先更新节点持有的状态，B 再读取该状态：

$$
x_A
\to
S_A
\to
h_B
\to
A_{v,\tau,B}.
$$

配置 J 中，A 的当前输入可以通过联合算子直接影响 B 的隐藏表示或路由：

$$
(x_A,x_B,S)
\to
\mathcal J_v
\to
h_B
\to
A_{v,\tau,B}.
$$

前两条路径语义不同，实验时不能只看最终状态后把它们视为同一个模型。

配置 F 不再分别产生标为 A/B 的出站记录，而是：

$$
(I_A,I_B,S)
\to
\mathcal F_v
\to
(h^\star,c^\star)
\to
A_{v,\tau,c^\star}.
$$

若 $c^\star=B$，则统一消息取 `owner=B`；若前状态已受 C 影响且 $C>B$，则统一消息必须取 `owner=C`。

## 7. 类型化逻辑事件、空间节点输入序列与分块契约

本节同时使用三种图，必须保持顶点和边的类型分离：

| 图 | 顶点 | 边 |
| --- | --- | --- |
| 空间 DAG $G=(V,E)$ | 可复用的空间节点 $v$ | 允许消息传播的空间边 |
| 消息来源图 $P_{\mathrm{msg}}$ | 事件实例与消息实例 | 消息的产生边与消费边 |
| 逻辑事件 DAG $D_L^P$ | 一次有限执行中的事件实例 $e$ | 数据、状态或控制的直接事件依赖边 |

一个空间节点可以在不同逻辑时间对应许多节点事件；一个事件顶点也不是一个永久神经网络节点。后文若只写“节点”，默认仍指空间节点；逻辑事件 DAG 的元素始终称为“事件”或“事件顶点”。

### 定义 7.1：语义配置专属的逻辑事件

取语义配置：

$$
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\}.
$$

定义事件种类集合：

$$
\mathcal K^P
=
\mathcal K_{\mathrm{bdry}}
\cup
\{\mathtt{node}_P\}.
$$

语义配置 $P$ 的事件是定义 2.1a 的逻辑事件实例，并取 $\mathcal K=\mathcal K^P$。为便于阅读，后文把它的事件头继续写成：

$$
h_e
=
(\eta,\kappa,\ell,\theta,\Omega,c),
\tag{GD-E1}
$$
^eq-logical-event-instance

该事件头是定义 2.1a 在固定周期 Tide 参考语义中的具体使用：$\theta$ 是逻辑时间戳，$\Omega$ 是归属支持集，$c$ 是因果前沿。每个事件的值 $\nu(e)$ 与事件头一起满足定义 2.1a 和式 GD-2.4。事件级因果前沿 $c$ 是整个事件值的有效保守上界；值内的单个隐藏表示、状态或消息产物可以登记不大于 $c$ 的更紧因果前沿。

实际事件集合只登记真正发生的事件。选择器不选择某条边时，相应节点事件的路由集合中没有该边，也不会产生该出站消息；不会为“未发生的下游事件”伪造一个值为 $\bot$ 的事件。另一方面，已经发生的节点事件可以包含 $\bot$ 隐藏表示分量，表示该转移已执行但没有产生路由可见的隐藏表示。

本文使用以下事件实例：

1. 对每个 $t\in[L]$，使用定义 2.1c 的输入事件头 $h_{e_t^{\mathrm{in}}}$。

2. 对非空常规收件箱分组：配置 O 为每个 $(v,\tau,t)$ 建立一个事件，其提交时间戳为 $(\tau,i_{\mathrm{commit}})$、归属支持集为 $\{t\}$；配置 J/F 为每个 $(v,\tau)$ 建立一个事件，归属支持集为 $\mathcal O_{v,\tau}$。其事件级因果前沿必须是该事件值的有效上界；配置 F 取式 GD-F1 的 $c_{v,\tau}^{\star}$。

3. 对每个 $t\in[L]$，使用定义 2.1c 的固定读出事件头 $h_{e_t^{\mathrm{out}}}$。

读出事件对每个 $t$ 必定存在，不能被选择器取消、推迟或改写时间戳。

4. 自回归执行额外包含定义 2.1c 的采样事件头 $h_{e_t^{\mathrm{sample}}}$。

给定序列分块定理不需要采样事件；它把 $x_{0:L}$ 作为边界数据。

事件值空间必须按种类显式登记：输入事件值包含边界注入记录 $b_t^{\mathrm{in}}$；输入/节点事件值还至少包含带标签隐藏表示、已提交的状态版本、路由记录与已派发的消息；$\nu(e_t^{\mathrm{out}})=y_t\in Y$；$\nu(e_t^{\mathrm{sample}})=\operatorname{SelectToken}(y_t)\in X$。实现不能把这些参考语义可见的产物隐藏为未比较的副作用。

### 定义 7.2：直接依赖与依赖完备性

给定一次已经实例化的有限参考执行，其事件集合记为：

$$
\mathcal E_L^P.
$$

定义直接依赖关系：

$$
\mathcal A_L^P
\subseteq
\mathcal E_L^P\times\mathcal E_L^P,
$$

为包含下列边的最小关系：

1. **消息边**：若事件 $e$ 派发的消息被事件 $e'$ 的收件箱消费，则 $(e,e')\in\mathcal A_L^P$。输入事件产生的第一跳消息也使用该规则。
2. **状态边**：若同一节点的事件 $e'$ 读取事件 $e$ 提交后的状态版本，且中间没有其他覆盖该版本的提交，则 $(e,e')\in\mathcal A_L^P$。
3. **读出边**：若 $e$ 是输出节点 $z$ 在 $\theta_t^{\mathrm{out}}$ 之前的最后一个状态提交事件，则 $(e,e_t^{\mathrm{out}})\in\mathcal A_L^P$；若不存在这样的事件，读出使用边界初始状态。
4. **自回归边界边**：在纯推理中，$(e_t^{\mathrm{out}},e_t^{\mathrm{sample}})\in\mathcal A_L^P$，并且当 $t+1\in[L]$ 时，$(e_t^{\mathrm{sample}},e_{t+1}^{\mathrm{in}})\in\mathcal A_L^P$。

若选择器被细化为独立事件，则选择器值到路由或消息产生事件的控制边也必须加入 $\mathcal A_L^P$。本文默认选择器是相应节点事件的内部原语；已选路由集合与每条可选出站消息都属于该节点事件值，不能依赖未声明的全局状态。某个下游常规事件是否实例化，由其收件箱是否非空决定；该收件箱中每条消息都必须通过消息边追溯到源事件。

定义事件图：

$$
D_L^P
=
(\mathcal E_L^P,\mathcal A_L^P).
$$

称 $D_L^P$ 依赖完备，当且仅当任何被实际执行读取、且可能改变事件头、事件值、状态版本、路由、消息或读出的参考依赖，都由 $\mathcal A_L^P$ 中的一条事件依赖边、显式边界数据参数，或事件局部原语内部已声明的顺序表示。未选择的路由/消息以源事件值中的空集合或缺失可选记录表示，不额外建立值为 $\bot$ 的事件顶点。

对 $e\in\mathcal E_L^P$，定义：

$$
\operatorname{Pred}(e)
=
\{e'\in\mathcal E_L^P\mid(e',e)\in\mathcal A_L^P\}.
$$

对每个事件 $e$，给定显式声明的边界数据空间 $\mathcal B_e$。它只能包含该事件允许读取的输入 `token` 前缀、其位置的初始状态投影、静态参数与逻辑元数据。给定确定性事件函数：

$$
F_e:
\{h_e\}
\times
\left(
\prod_{e'\in\operatorname{Pred}(e)}\mathcal V_{e'}
\right)
\times\mathcal B_e
\to
\mathcal V_e,
$$

并要求 $F_e$ 只读取式 GD-E1 的事件头 $h_e$、直接前驱与已声明边界数据。事件头不是额外的 `token` 数据通道：其中任何会随执行改变的支持集、因果前沿或标识符字段，都必须由直接前驱记录与静态规范化规则唯一导出；不能把未声明的数值信息编码进事件标识符或元数据。较粗事件若在物理实现中展开为多个操作，必须先细化为依赖完备的逻辑子事件 DAG，或给出融合原语保持语义的证明。

对本文严格 Tide 语义，只有 $e_t^{\mathrm{in}}$ 可以从 $X^L$ 直接读取 $x_t$。常规节点事件只能通过入站消息、局部状态前驱、静态参数与逻辑元数据获得依赖 `token` 的信息；读出事件只能读取式 GD-E3 指定的输出节点状态快照；采样事件只能读取对应读出值与静态选择参数。

### 定义 7.3：空间节点的完整规范输入序列

对每个非空常规时间戳分组，定义：

$$
E_{v,\tau}
=
\left(
q_R(\tau),
r_R(\tau),
I_{v,\tau},
B_{v,\tau}
\right).
$$

定义常规分组记录的执行时间戳：

$$
\theta_{v,\tau}^{\mathrm{step}}
=
(\tau,i_{\mathrm{step}}).
$$

对空间节点 $v$，把全部常规分组记录与仅在 $v=s$ 时存在的注入记录合并，并按 $<_{\Theta}$ 及所选配置的规范并列次序排列，得到完整规范输入序列：

$$
\mathbf U_v.
$$

更明确地，$\mathbf U_v$ 的记录集合为：

$$
\left\{
(\theta_{v,\tau}^{\mathrm{step}},E_{v,\tau})
\mid I_{v,\tau}\neq\varnothing
\right\}
$$

与：

$$
\left\{
(\theta_t^{\mathrm{in}},b_t^{\mathrm{in}})
\mid t\in[L],\ v=s
\right\}
$$

的不交并。由引理 4.5 与引理 4.6，$\mathbf U_v$ 是有限序列。

这里的“序列”是为了使参考转导器具有确定输入次序，不表示物理运行时必须按流式逐项到达或执行。物理实现可以先收集、分段、排序和打包，只要产生相同的规范序列语义。

### 定义 7.4：空间节点参考转导器与状态提交轨迹

给定输入节点的注入转移：

$$
\mathcal I_s:
[L]\times X\times\widetilde{\mathcal S}_s
\to
\mathcal Z_s\times\widetilde{\mathcal S}_s.
$$

若 $\mathcal I_s$ 对 `token` $t$ 返回非空带标签隐藏表示 $z$，则输入事件的输出记录为 $(t,z)$，其 `owner=t`，并必须满足 $t\leq\operatorname{frontier}(z)$。

节点参考转导器 $\operatorname{Ref}_v^P$ 按 $\mathbf U_v$ 的时间戳顺序处理记录：

- 注入记录使用 $\mathcal I_s$。
- 若 $P=\mathrm{ord}$，常规分组使用式 [[#^eq-owner-ordered-group|GD-7]]。
- 若 $P=\mathrm{joint}$，常规分组使用式 [[#^eq-atomic-joint-transition|GD-8]] 与式 [[#^eq-atomic-joint-commit|GD-9]]。
- 若 $P=\mathrm{front}$，常规分组使用式 [[#^eq-frontier-fusion-transition|GD-F2]] 与式 [[#^eq-frontier-owned-output|GD-F3]]。
- 每个带标签输出经过第 6 节选择器与单位时延派发。

每次状态更新都产生一个提交记录：

$$
q=(\eta_q,\chi_q,\widetilde S_v^q),
$$

其中 $\eta_q$ 是全局唯一且确定生成的提交记录标识符，$\widetilde S_v^q$ 称为这次提交产生的状态版本，$\chi_q\in\mathbb N\times\{0,\ldots,N_{\mathrm{phase}}-1\}\times\mathbb N$ 是完整提交次序键。定义：

$$
\operatorname{version}(q)=\widetilde S_v^q.
$$

配置 O 的常规事件使用 $\chi_q=(\tau,i_{\mathrm{commit}},t)$；配置 J/F 的事件使用 $\chi_q=(\tau,i_{\mathrm{commit}},0)$；注入转移使用 $\chi_q=(Rt,i_{\mathrm{inject}},t)$。第三个坐标只用于同一绝对轮次、同一阶段内的规范并列消解，不是新的物理时间单位。若 $\chi_q=(\tau_q,i_q,j_q)$，定义提交时间戳投影：

$$
\operatorname{ctime}(q)=(\tau_q,i_q)\in\Theta.
$$

按 $\chi_q$ 的字典序次序排列全部提交记录，得到状态提交轨迹 $\mathbf Q_v^P$。

定义：

$$
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0)
=
\left(
\mathbf H_v^P,
\mathbf Q_v^P,
\mathbf R_v^P,
\mathbf M_{v,\mathrm{out}}^P,
\widetilde S_v^{P,\mathrm{final}}
\right).
\tag{GD-E2}
$$
^eq-node-reference-artifacts

五项依次是带标签隐藏表示记录序列、完整状态提交轨迹、路由记录序列、出站消息记录序列与最终增广状态。

上述四类记录序列都必须使用规范逻辑次序：先按源事件的提交键，再按归属 `token` 索引、边标识符与确定性记录或消息标识符排序。它们不能按物理线程完成或缓冲区追加的先后顺序排列；否则式 GD-E2 与 GD-12 中的序列相等没有确定含义。

### 定义 7.5：固定周期读出

给定读出函数：

$$
\rho_z:
[L]\times\widetilde{\mathcal S}_z
\to Y.
$$

任何读出所需的隐藏表示/输出寄存器都必须是 $\mathcal S_z$ 的显式组件，不能作为 $\rho_z$ 的隐藏全局输入。

对任意时间戳 $\theta$，定义：

$$
\mathbf Q_z^{P,<\theta}
=
\{q\in\mathbf Q_z^P\mid\operatorname{ctime}(q)<_{\Theta}\theta\}.
$$

若该集合非空，在其中按完整 $\chi_q$ 次序取最后一个提交记录，并把其增广状态定义为 $\widetilde S_z^{<\theta}$；若集合为空，则定义 $\widetilde S_z^{<\theta}=\widetilde S_z^0$。

第 $t$ 个固定周期读出定义为：

$$
y_t
=
\rho_z
\left(
t,
\widetilde S_z^{<\theta_t^{\mathrm{out}}}
\right).
\tag{GD-E3}
$$
^eq-fixed-period-readout

定义读出序列：

$$
y_{0:L}=(y_0,\ldots,y_{L-1})\in Y^L.
$$

式 GD-E3 对每个 $t\in[L]$ 必须执行一次。长路径消息若在 $\theta_t^{\mathrm{out}}$ 之后才提交，只能影响后续读出，不能追溯修改 $y_t$。

### 定义 7.6：空间节点事件序列分块算子

节点 $v$ 在语义配置 $P$ 下的分块算子是函数：

$$
\mathcal C_v^P:
(\mathbf U_v,\widetilde S_v^0)
\mapsto
\left(
\widehat{\mathbf H}_v^P,
\widehat{\mathbf Q}_v^P,
\widehat{\mathbf R}_v^P,
\widehat{\mathbf M}_{v,\mathrm{out}}^P,
\widehat{\widetilde S}_v^{P,\mathrm{final}}
\right).
$$

称它满足精确节点分块契约，当且仅当对任意有限合法空间节点规范输入序列：

$$
\mathcal C_v^P(\mathbf U_v,\widetilde S_v^0)
=
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0).
\tag{GD-12}
$$
^eq-node-event-stream-contract

等式比较式 GD-E2 的全部五类产物。特别地，只比较最终状态或最终 `logits` 不足以证明该契约。

> [!warning] GD-12 是节点级前提，不是自动得到的实现
> 定理 8.4 把全图调度等价归约到每个节点的 GD-12 契约，但没有证明任意节点计算都能高效满足它。顺序循环也可以满足正确性；是否具有高性能 `prefill`，还要为具体注意力、SSM、FFN、选择器或路由计算分别证明。

### 引理 7.7：有限参考执行的事件 DAG

在引理 4.6 的条件下，给定任意语义配置 $P$，给定序列参考的事件图 $D_L^P$ 是有限 DAG。若再加入定义 7.1 的采样事件与自回归边界边，有限前缀的自回归事件图仍是 DAG。

**证明。**

由引理 4.6，消息与常规节点事件数有限；输入、读出与采样事件各至多 $L$ 个，所以事件集合有限。

给每个事件定义字典序等级。注入、读出与采样事件使用其 $\Theta$ 时间戳，并追加并列消解坐标 $0$。配置 O 的节点事件使用：

$$
\operatorname{rank}(e_{v,\tau,t})
=
(\tau,i_{\mathrm{commit}},t).
$$

联合/因果前沿节点事件使用：

$$
\operatorname{rank}(e_{v,\tau})
=
(\tau,i_{\mathrm{commit}},0).
$$

消息边把轮次从 $\tau$ 推进到 $\tau+1$。局部状态边按节点参考次序指向更大的时间戳，或在配置 O 的同刻分组内指向更大的归属 `token` 索引。读出边由式 GD-0.3 从提交阶段指向读出阶段。自回归边界边由式 GD-0.4 从读出指向采样，再指向下一注入。每类边都严格增加等级，所以不存在有向环。

<div class="qed" aria-label="证毕">∎</div>

### 例 7.8：计算核族与分块实现映射

| 节点计算核 | 逻辑事件语义 | 可能的分块实现 |
| --- | --- | --- |
| 逐 `token` 映射 / FFN | 事件独立读取各自输入 | 批量化矩阵乘 / 融合的逐元素计算 |
| 因果注意力 | 事件值只读取允许的因果前缀 | 紧凑打包 QKV + 因果掩码 / 融合的注意力 |
| Mamba/SSM | 状态边形成仿射/选择性递推 | 并行/分块扫描或选择性扫描计算核 |
| 线性注意力 | 前缀累加器状态边 | 满足结合律的扫描 / 分块累加器 |
| 同轮次集合交互 | 原子联合节点事件 | 分段集合计算核 / 分组注意力 |
| 配置 F 的状态融合 | 同刻多重集与前状态产生一个统一事件值 | 分段归约 + 扫描/因果批量计算核 |
| 任意黑盒转移 | 按依赖完备的事件次序 | 顺序回退；只证明正确性 |

分块实现映射可以按 $(\tau,q_R(\tau),r_R(\tau),t,c,\mu)$ 排序与打包，但必须保持式 GD-12 和全部直接依赖。

### 7.9 收件箱完备性与节点内等待

在同步绝对时间参考中，每个内部轮次的阶段屏障直接保证收件箱分组完整，不需要水位标记作为模型语义。

异步物理运行时若要在没有全局屏障的情况下执行同一参考，可以使用水位标记、前驱完成通知或分块结束标记，证明不会再补来时间戳不超过某界的消息。水位标记是物理进度凭证，不是逻辑事件；只有当模型行为显式读取水位标记时，它才必须提升为控制事件。

即使完整 $\mathbf U_v$ 已一次性交给节点，状态边仍可能形成顺序依赖。分块算子可以使用批量化映射、扫描、带掩码的批量计算核，或在没有收缩时使用节点局部顺序循环。后者仍可满足 GD-12，但节点局部并行跨度可以是 $\Theta(M_v)$。

如果生成 $\mathbf U_v$ 必须先读取 $v$ 自己尚未产生的输出、沿空间环返回的消息，或未纳入事件图的共享可变选择器状态，则节点拓扑序分解失败。本页的空间 DAG、状态唯一持有与仅向前路由正是用于排除这类循环就绪依赖。

## 8. 流式调度与节点拓扑序分块调度

### 定义 8.1：绝对时间流式调度

定义封闭执行 horizon：

$$
H_L
=
\begin{cases}
0,&L=0,\\
R(L-1)+D,&L>0.
\end{cases}
\tag{GD-8.1}
$$
^eq-streaming-horizon

若 $L=0$，执行没有输入注入，也不执行任何内部轮次，所有节点保持初始状态。若 $L>0$，流式参考按：

$$
\tau=0,1,\ldots,H_L
$$

推进。

当 $L>0$ 时，由 $R=d_{\min}\leq D$，有 $RL\leq H_L$，所以最后一个固定读出轮次 $RL$ 已包含在该时间范围内。

本定义采用 **封闭有限执行**：在第 $L-1$ 个读出后不再注入新 `token`，但继续执行到 $H_L$，使这 $L$ 个注入已经产生的所有空间消息都被消费或显式终止。因此本节得到的最终节点状态是冲刷后状态，不是假想的下一注入边界 $RL$ 上、仍保留在途消息的延续状态。后者必须把边界状态快照与在途消息多重集一起定义，属于风险九所述的下一步嵌入定理。

在每个绝对轮次 $\tau$，严格按定义 0.3 的阶段次序执行：

1. 在 $i_{\mathrm{arrive}}$ 收集到达时间戳为 $(\tau,i_{\mathrm{arrive}})$ 的消息，构造 $I_{v,\tau,t}$、$I_{v,\tau}$ 与 $B_{v,\tau}$。
2. 在 $i_{\mathrm{step}}$ 执行全部非空常规节点分组，并在 $i_{\mathrm{commit}}$ 提交状态、路由与出站消息记录。
3. 若存在 $t\in[L]$ 满足 $\tau=R(t+1)$，在 $i_{\mathrm{read}}$ 执行固定读出事件 $e_t^{\mathrm{out}}$；自回归执行随后在 $i_{\mathrm{sample}}$ 执行 $e_t^{\mathrm{sample}}$。
4. 若存在 $t\in[L]$ 满足 $\tau=Rt$，在 $i_{\mathrm{inject}}$ 执行输入事件 $e_t^{\mathrm{in}}$。给定序列参考读取边界数据 $x_t$；自回归参考对 $t>0$ 读取前一采样事件的值。
5. 本轮次派发的空间消息按式 GD-3 在 $(\tau+1,i_{\mathrm{arrive}})$ 到达。

每个固定读出都按式 GD-E3 读取提交轨迹快照。因为每条边时延为 $1$，同一个轮次内不存在从一个空间节点到另一个空间节点的零时延消息依赖。

### 定义 8.2：空间拓扑序

空间 DAG 的拓扑序是元组：

$$
\pi=(v_1,v_2,\ldots,v_N),
\qquad N=|V|,
$$

满足每个节点恰好出现一次，并且：

$$
(v_i,v_j)\in E
\quad\Longrightarrow\quad
i<j.
$$

有限 DAG 至少存在一个拓扑序。

### 定义 8.3：节点拓扑序分块调度

给定边界序列 $x_{0:L}$ 与拓扑序 $\pi$。分块调度依次处理：

$$
v_1,v_2,\ldots,v_N.
$$

处理节点 $v_i$ 时：

1. 它的所有空间前驱已经完成。
2. 从所有前驱出站消息记录序列合并常规收件箱分组；若 $v_i=s$，再加入固定注入记录，得到完整 $\mathbf U_{v_i}$。
3. 调用 $\mathcal C_{v_i}^P$ 一次处理整条空间节点规范输入序列。
4. 把得到的出站消息加入空间后继的待处理收件箱。

> [!note] 为什么这不是让未来 `token` 提前可见
> 物理 `prefill` 可以一次持有 $x_{0:L}$，但每个事件仍携带原来的逻辑时间戳，且定义 2.4 禁止它读取尚未在该时间戳注入的 `token`。节点拓扑序调度只是把已经定义好的事件计算重新分组，不改变任何事件允许读取的数据。

全部节点完成后，使用 $\widehat{\mathbf Q}_z^P$ 按式 GD-E3 计算固定读出序列。互不依赖的节点可以并行执行；元组 $\pi$ 只用于定义一种合法顺序。

### 定理 8.4：固定周期一般 DAG 调度等价定理

给定任意有限输入分块、任意语义配置：

$$
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\},
$$

并假设：

1. 空间图 $G$ 满足定义 1.1，不要求 $\Lambda(v)$ 为单元素集合。
2. 固定周期满足 $R=d_{\min}$，注入/读出/采样阶段满足式 GD-0.3 与 GD-0.4。
3. 每条边满足单位时延派发，边界满足定义 4.2a 的跨边界延续语义。
4. 每条消息保留归属 `token` 索引、因果前沿、到达时间戳与消息标识符。
5. 收件箱聚合满足定义 4.4。
6. 每个可变状态位置只有一个持有节点。
7. 路由只沿 $E$ 前进且是确定函数；任何可变路由状态都由唯一节点持有，并包含在该节点事件/值与分块契约中。
8. 事件图满足定义 7.2 的依赖完备性。
9. 每个节点的分块算子满足式 GD-12，并比较完整提交轨迹。
10. 执行满足引理 4.6 的有限事件条件。

则节点拓扑序分块调度与绝对时间流式调度产生完全相同的：

- 每个节点的带时间戳的收件箱。
- 每条带 `owner` 与 `frontier` 的隐藏表示记录。
- 每个节点的完整状态提交轨迹。
- 已选路由。
- 全部已派发的消息。
- 每个节点在封闭时间范围 $H_L$ 后的冲刷后最终上下文状态与状态因果前沿。
- 固定时间戳 $\theta_t^{\mathrm{out}}$ 上的读出序列 $y_{0:L}$。

因此，给定序列的流式执行与分块执行计算同一个封闭有限固定周期参考语义。

**证明。**

取空间 DAG 的任意拓扑序：

$$
\pi=(v_1,\ldots,v_N).
$$

由前提 6-8，每个节点的可变依赖都由该节点的增广状态、入站消息、静态参数与已声明边界数据给出；不存在跨节点的隐藏共享状态依赖。因此，一旦 $\mathbf U_v$ 与 $\widetilde S_v^0$ 相同，$\operatorname{Ref}_v^P$ 的全部产物就唯一确定。

对 $i=1,\ldots,N$ 做数学归纳，证明节点 $v_i$ 在两种调度中得到相同完整 $\mathbf U_{v_i}$，并产生式 GD-E2 的相同产物。

当 $i=1$ 时，$v_1=s$。定义 1.1 要求每个 $v\neq s$ 都位于一条从 $s$ 出发的非零长度路径上，所以它至少有一个空间前驱。另一方面，$s$ 不可能有入边：若 $(u,s)\in E$，则 $u$ 可从 $s$ 到达，进而形成从 $s$ 到 $u$ 再回到 $s$ 的有向环。因此 $s$ 是唯一入度为零的节点，任意拓扑序都以 $s$ 开始。输入节点的 $\mathbf U_s$ 在两种调度中都由同一组固定记录 $b_t^{\mathrm{in}}$ 构成。由式 GD-12，分块算子与流式参考转导器产生相同隐藏表示记录、提交轨迹、路由、出站消息与最终增广状态。

假设结论对 $v_1,\ldots,v_{i-1}$ 成立。考虑 $v_i$。由拓扑序的定义，$v_i$ 的每个直接前驱都位于：

$$
\{v_1,\ldots,v_{i-1}\}.
$$

由归纳假设，每个前驱在两种调度中产生完全相同的出站消息记录序列。因此，把所有目标为 $v_i$ 的消息按 $(\tau,t)$ 分桶后，得到相同的：

$$
I_{v_i,\tau,t},
$$

相同的原始多重集 $I_{v_i,\tau}$、归属 `token` 元组 $B_{v_i,\tau}$，以及相同的空间节点完整规范输入序列 $\mathbf U_{v_i}$。

在流式调度中，节点 $v_i$ 按参考事件次序对 $\mathbf U_{v_i}$ 执行 $\operatorname{Ref}_{v_i}^P$。在分块调度中，它执行 $\mathcal C_{v_i}^P$。由式 GD-12，两者产生式 GD-E2 的全部相同产物。

所以结论对 $v_i$ 成立。由数学归纳法，结论对所有节点成立，特别地 $\mathbf Q_z^P=\widehat{\mathbf Q}_z^P$。对每个 $t\in[L]$ 应用同一个式 GD-E3，得到相同 $y_t$。

证明中没有使用“所有到达同一节点的路径等长”，所以一般 DAG 中的路径长度碰撞被完整保留，而不是通过中继节点消除。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.4a：固定周期读出不被长路径追溯修改

在定理 8.4 的条件下，任意到达/提交时间戳晚于 $\theta_t^{\mathrm{out}}$ 的事件都不会改变 $y_t$，但可以通过后续状态边影响 $y_{t+1},y_{t+2},\ldots$。

**证明。**

由式 GD-E3，$y_t$ 只读取 $\theta_t^{\mathrm{out}}$ 之前的最后已提交的状态。更晚事件不属于该快照；后续读出使用更晚快照，因而仍可读取其影响。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.5：配置 O 的正确性

若每个节点的分块算子精确实现按归属 `token` 排序的事件序列折叠，则节点拓扑序分块执行与配置 O 的绝对时间流式参考等价。

**证明。**

在定理 8.4 中取 $P=\mathrm{ord}$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.6：原子联合配置的正确性

若每个节点的分块算子精确实现原子联合时间戳转移，则节点拓扑序分块执行与配置 J 的绝对时间流式参考等价。

**证明。**

在定理 8.4 中取 $P=\mathrm{joint}$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.6a：因果前沿融合配置的正确性

若每个节点的分块算子精确实现配置 F 的原子融合事件序列转移，则节点拓扑序分块执行与配置 F 的绝对时间流式参考等价，并在定理 5.13 的前提下保持 `token` 前缀因果前沿不变量。

**证明。**

在定理 8.4 中取 $P=\mathrm{front}$，得到调度等价；再应用定理 5.13，得到因果前沿不变量。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.7：折叠等价的联合实现映射

若每个节点的联合算子还满足式 [[#^eq-joint-ordered-equivalence|GD-10]]，则配置 J 的分块执行、配置 O 的分块执行与配置 O 的流式参考三者等价。

**证明。**

由命题 5.8，每个时间戳分组上联合与有序产物相同。对每个节点的时间戳流归纳，可得两种节点参考转导器相同。再分别应用推论 8.5 与推论 8.6。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.8：等长路径模型是本定理的特殊情形

若对每个节点 $v$，存在唯一 $d(v)$ 使：

$$
\Lambda(v)=\{d(v)\},
$$

则任何由位置 $t$ 注入、并实际到达空间节点 $v$ 的消息，其到达轮次唯一为 $Rt+d(v)$；`owner` 不同的消息不会在同一 $v$、同一到达轮次汇聚。定理 8.4 仍然成立，并在配置 O/J 中退化为等层 DAG 的调度等价结论；配置 F 仍可因持久状态依赖发生归属提升。

**证明。**

由式 GD-2.1，任意从输入位置 $t$ 出发并实际到达 $v$ 的消息分支，其空间路径都有 $\tau=Rt+d(v)$。若 $t\neq t'$：

$$
Rt+d(v)
\neq
Rt'+d(v),
$$

所以不存在 `owner` 不同的消息在同一空间节点同刻汇聚。其余结论直接由定理 8.4 得到。

<div class="qed" aria-label="证毕">∎</div>

## 9. 正确性之外：工作量、并行跨度与超稀疏约束

### 9.0 三层性能目标

本文把“支持 chunk prefill”拆成三个不能混用的层级：

| 层级 | 要求 | 允许的节点内实现 | 本页状态 |
| --- | --- | --- | --- |
| 封闭有限精确分块正确性 | 一次分块调用与封闭有限逐时间戳参考产物完全相同 | 包括顺序回退 | 由定理 8.4 归约到节点契约 |
| 节点局部分块吞吐量 | 一个节点一次或少量调用处理多个输入位置、多个逻辑轮次的完整事件序列；本地打包，批量收发边消息，无逐位置全局编排 | 普通 C++/设备循环、分支、取分数最高的若干项、聚集/分散、局部矩阵计算核均可 | Tide 当前首要性能目标 |
| `token` 轴低并行跨度 | 跨 `token` / 事件依赖可被收缩，不保留长度随输入块线性增长的关键路径 | `token` 局部映射、因果注意力、扫描、分段批量等 | 更强的可选目标，需逐计算核证明 |

在默认恒等空闲语义下，固定周期 $R$ 不会自动破坏前两层；它只决定注入/读出的截止时间与每个节点的带时间戳事件序列。若空时间戳也执行非平凡衰减/更新，其工作量/并行跨度必须另行计入。真正阻止第三层的是节点局部状态/控制转移缺少可组合结构，而不是“一个外部周期含 $R$ 个内部轮次”这一事实本身。

因此，若每个节点映射到独立设备，合理的第一阶段实现是：空间前驱批量生成完整或分块事件记录序列，节点在本设备内对这些记录做排序、分段和打包后一次处理，再批量派发。节点内某些选择器或路由代码即使只能顺序执行，也不要求运行时回到逐 `token` 的跨设备控制循环；但它的实际并行跨度与吞吐必须诚实计入性能报告。

### 定义 9.1：节点事件数

定义封闭执行的轮次索引集合：

$$
\mathbb T_L
=
\begin{cases}
\varnothing,&L=0,\\
\{0,\ldots,H_L\},&L>0.
\end{cases}
$$

定义节点 $v$ 按归属 `token` 划分的事件数：

$$
M_v
=
\sum_{\tau\in\mathbb T_L}|\mathcal O_{v,\tau}|.
$$

定义全图按归属 `token` 划分的事件总数：

$$
M
=
\sum_{v\in V}M_v.
$$

令 $\mathcal M_{\mathrm{dispatch}}$ 为执行中全部已派发的消息的集合，定义其消息总数：

$$
N_{\mathrm{msg}}
=
\left|\mathcal M_{\mathrm{dispatch}}\right|.
$$

配置 J/F 的时间戳分组数可能小于 $M_v$，但联合或融合计算核的工作量必须计入它读取的全部原始消息与带归属字段记录。

定义实际常规节点事件数：

$$
M_{\mathrm{node}}^P
=
\begin{cases}
M,&P=\mathrm{ord},\\
\displaystyle\sum_{v\in V}
\left|\{\tau\in\mathbb T_L\mid I_{v,\tau}\neq\varnothing\}\right|,
&P\in\{\mathrm{joint},\mathrm{front}\}.
\end{cases}
$$

给定序列执行还固定包含 $L$ 个注入事件与 $L$ 个读出事件。因此若把全部逻辑事件计入，定义：

$$
M_{\mathrm{all}}^{\mathrm{TF}}
=
M_{\mathrm{node}}^P+2L,
$$

其中 $M_{\mathrm{node}}^P$ 是按所选语义配置实际建立的常规节点事件数。自回归有限前缀另增加 $L$ 个采样事件。性能报告不能把这些边界事件、提交轨迹或读出成本视为免费。

### 定义 9.2：节点分块工作量与并行跨度

记节点 $v$ 的分块算子工作量上界与并行跨度上界分别为：

$$
W_v,
\qquad
P_v.
$$

工作量是总原语操作数的抽象；并行跨度是在依赖关系与无限处理器理想化下的关键路径长度。二者都是性能见证，不属于定理 8.4 的正确性结论。

### 命题 9.3：粗粒度节点拓扑序工作量/并行跨度上界

令 $W_{\mathrm{transport}}$ 表示全部已派发消息的序列化、传输、合并与物化工作量。节点拓扑序调度的总工作量满足：

$$
W_{\mathrm{graph}}
\leq
\sum_{v\in V}W_v
+W_{\mathrm{transport}}
+W_{\mathrm{out}}.
\tag{GD-13}
$$
^eq-general-dag-work

其中 $W_{\mathrm{out}}$ 是从输出节点提交轨迹计算并记录全部 $L$ 个固定读出的工作量。对每个节点 $v$，令 $C_v^{\mathrm{sched}}\geq 0$ 表示未包含在 $P_v$ 中的节点间记录序列合并、传输与调度器并行跨度；令 $P_{\mathrm{out}}$ 表示同一读出阶段的并行跨度。若无依赖节点可并行，则粗粒度并行跨度满足：

$$
P_{\mathrm{graph}}
\leq
\max_{p}
\sum_{v\in p}
\bigl(P_v+C_v^{\mathrm{sched}}\bigr)
+P_{\mathrm{out}},
\tag{GD-14}
$$
^eq-general-dag-span

其中最大值遍历空间 DAG 的所有有向路径。

**证明。**

这里 $W_v$ 已包含节点局部收件箱聚合、转移、路由，以及输入节点对注入记录的处理。消息载荷大小、跨设备通信、全局排序或非线性索引构建的成本全部计入 $W_{\mathrm{transport}}$；固定读出函数 $\rho_z$ 与输出物化的全部成本计入 $W_{\mathrm{out}}$。把三类互不重叠的工作量相加即得式 GD-13。

分块调度的节点级依赖图就是空间 DAG。任意节点计算关键路径对应其中一条有向路径；沿该路径累加每个节点的分块并行跨度与调度开销，再加入输出读出提取的并行跨度，得到式 GD-14。

<div class="qed" aria-label="证毕">∎</div>

这个命题解释了“一般 DAG 仍可能支持高性能 chunk prefill”的准确含义：

- 图级顺序深度由空间关键路径决定，而不是由 `token` 数直接决定。
- 但若某个 $P_v=\Theta(M_v)$ 且没有扫描或批量收缩，`token` 轴顺序链只是被封装进节点计算核，并没有消失。
- 若 $M$ 本身因扇出指数增长，即使并行跨度较小，总工作量与内存占用仍不可接受。

### 定义 9.4：固定来源消息槽位

给定常数：

$$
K\in\mathbb N_{>0}.
$$

每个输入位置 $b\in[L]$ 在注入时最多创建 $K$ 个不可变来源槽位：

$$
(b,q),
\qquad
q\in[K].
$$

这里 $b$ 是来源位置索引，不随后续 `owner` 或 `frontier` 提升而改变。槽位标识符 $(b,q)$ 写入消息元数据。严格槽位语义要求：

> [!note] 来源位置、`owner` 与 `frontier` 仍是三个对象
> 来源位置 $b$ 记录槽位最初由哪个输入位置创建，终生不变；`owner` 记录当前消息使用哪个输入位置作为归属索引，配置 F 可以提升它；`frontier` 记录当前数值依赖的输入前缀上界。三者相等是常见初始状态，但不是一般不变量。

- 每个槽位在任一时刻最多对应一条活跃传播中的消息。
- 一个槽位到达节点后，最多选择一条出边。
- 槽位可以终止或与其他槽位在节点内联合计算，但不能复制为两个同时活跃的同标识符槽位。
- 每个来源槽位在注入/分裂时至多初始化一次；终止后不能重新初始化或复用。已初始化槽位可以沿一条空间路径依次访问多个节点。
- 若需要分裂，只能从同一来源位置尚未启用的固定槽位池中分配；新槽位从分裂节点开始承载一条新的单路径消息分支。
- 因果前沿融合可以消费多个入站来源槽位，并保留其中一个或若干已有槽位继续传播；不能因为归属提升到更大的因果前沿而获得新的槽位池。

在该语义配置中，路由记录不再只是边集合，而是槽位到边的指派：

$$
A_{v,\tau}^{\mathrm{slot}}
\subseteq
([L]\times[K])
\times
\{(v,u)\in E\}.
$$

同一个来源槽位标识符在 $A_{v,\tau}^{\mathrm{slot}}$ 中至多出现一次。若多个槽位在同一事件分组中聚合，节点计算核必须显式给出哪些槽位合并、终止与继续传播；不能在丢失槽位恒等后仍声称满足槽位守恒。

### 命题 9.5：固定槽位的事件上界

在严格槽位语义中，每个来源位置的全部槽位节点访问次数不超过：

$$
K|V|.
$$

长度为 $L$ 的输入块中，按归属 `token` 划分的事件总数满足：

$$
M\leq LK|V|.
\tag{GD-15}
$$
^eq-owner-slot-event-bound

**证明。**

每个来源槽位至多初始化一次，并且初始化后不复制，只沿一条路由路径前进。空间图无环，所以该路径最多访问每个节点一次，节点访问次数不超过 $|V|$。每个来源位置最多有 $K$ 个槽位，因此其全部槽位访问次数不超过 $K|V|$。因果前沿提升只改变消息的 `owner` 标签，不创建来源槽位。每个按归属 `token` 划分的事件至少消费一次槽位访问，所以事件数不超过槽位访问次数；对 $L$ 个来源位置求和得到式 GD-15。

<div class="qed" aria-label="证毕">∎</div>

固定来源槽位不是唯一的稀疏设计，但它给出一个不依赖空间层级或归属提升、也不需要跨 `token` 在线计数器的明确上界。若改为“每个事件独立选择分数最高的 $K$ 条出边”，最坏事件数可能随 DAG 深度指数增长，不能称为超稀疏保证。

## 10. 空间/时间均衡与选择器配置

### 定义 10.1：空间节点访问负载

在固定槽位语义配置中，定义：

$$
a_{b,q,v}
=
\begin{cases}
1,&\text{来源位置 }b\text{ 的槽位 }q\text{ 访问节点 }v,\\
0,&\text{否则}.
\end{cases}
$$

定义长度为 $L$ 的节点负载：

$$
n_v^{(L)}
=
\sum_{b\in[L]}\sum_{q\in[K]}a_{b,q,v}.
\tag{GD-16}
$$
^eq-general-node-load

若不采用槽位语义，可以把 $n_v^{(L)}$ 改为到达 $v$ 的、按归属 `token` 划分的事件数，但必须同时报告事件复制数量。

### 10.2 当前 LH 在线计数选择器

给定隐藏表示摘要空间 $\mathcal H$、控制状态空间 $\mathcal Q$ 与硬路由空间 $\mathcal R_{\mathrm{route}}$，以及确定函数：

$$
\rho:
\mathcal H\times\mathcal Q
\to
\mathcal R_{\mathrm{route}},
$$

$$
U:
\mathcal Q\times\mathcal R_{\mathrm{route}}
\to
\mathcal Q.
$$

给定有限事件数 $J\in\mathbb N_{>0}$。对按参考次序排列的 $j\in[J]$，当前 LH 风格的选择器可以抽象为：

$$
R_j=\rho(H_j,Q_j),
$$

$$
Q_{j+1}=U(Q_j,R_j),
$$

其中第二式只对 $j+1\in[J]$ 使用；$H_j\in\mathcal H$、$Q_j\in\mathcal Q$、$R_j\in\mathcal R_{\mathrm{route}}$，且 $Q_j$ 包含 `affectcount/selectcount`。这可以直接惩罚近期热点，但形成：

$$
Q_0\to R_0\to Q_1\to R_1\to\cdots.
$$

若 $j$ 沿 `token` 轴或事件轴增长，且组合转移不具有已证明的扫描或批量结构，就形成逐步揭示的自适应控制链。命题 10.3 只证明该链的直接依赖代价；本文不在这里额外主张一般 oracle 模型下的复杂度下界。

### 命题 10.3：强在线反馈的依赖代价

如果后一个路由必须读取由前一个实际硬路由更新的控制状态，且该更新/路由组合没有额外已证明的收缩，则精确执行存在相应长度的顺序控制链。

**证明。**

后一个路由需要更新后的 $Q_{j+1}$；$Q_{j+1}$ 需要前一个硬路由 $R_j$；$R_j$ 又读取 $Q_j$。因此每一步都依赖前一步，得到上述控制链。

<div class="qed" aria-label="证毕">∎</div>

### 10.4 与 `prefill` 兼容的均衡层

在严格语义配置中，均衡拆成以下互不替代的层：

| 层 | 方法 | 是否进入逐事件前向状态 |
| --- | --- | --- |
| 结构上界 | 固定来源槽位、有限出度、静态可用性 | 否 |
| 静态容量 | 边/节点偏置、设备容量权重、拓扑分区 | 否 |
| 确定性时间分散 | $d_{v\to u}(t,\tau)$ | 否 |
| 训练期均衡 | 节点负载 / 时间窗口损失 | 只影响梯度 |
| 在线硬均衡 | 持久路由计数器 | 是；通常形成控制链 |

给定目标节点容量权重：

$$
\pi_v>0,
\qquad
\sum_{v\in V}\pi_v=1,
$$

定义归一化实际负载：

$$
\widehat p_v
=
\frac{n_v^{(L)}}{\sum_{u\in V}n_u^{(L)}}.
$$

分母为 $0$ 时把损失定义为 $0$。空间均衡目标可以写为：

$$
\mathcal L_{\mathrm{space}}
=
\sum_{v\in V}
(\widehat p_v-\pi_v)^2.
\tag{GD-17}
$$
^eq-general-space-balance-loss

给定窗口宽度 $B\in\mathbb N_{>0}$。对每个 $j\in\mathbb N$，定义绝对时间窗口：

$$
W_j
=
\{jB,\ldots,(j+1)B-1\},
$$

可以统计到达时间落入 $W_j$ 的节点事件，构造 $\mathcal L_{\mathrm{time}}$。它约束真实流水线时间上的热点，而不是把外部 `token` 索引误当作唯一到达时间。

### 命题 10.5：跨 `token` 硬容量约束的三种基本选择

给定硬容量 $C\in\mathbb N$。若要求任意输入上、任意时间窗口内节点 $v$ 的硬准入不超过 $C$，而多个归属 `token` 都可能选择 $v$，则精确选择器至少采用以下一种机制：

1. 用静态资格约束或配额预先限制可选归属 `token` / 槽位。
2. 联合观察一个已知的归属 `token` / 事件集合后做指派。
3. 在线维护已使用容量，让后续决策读取此前的准入结果。

第二种机制是否允许取决于参考语义：配置 J/F 可以在同一时间戳分组内使用它，但不能免费跨越尚未形成的未来分组。第三种机制形成在线控制链。第一种最容易保持原生兼容严格 `prefill`，但会限制内容路由的自由度。

**证明。**

若资格未预先限制，当超过 $C$ 个候选同时或先后希望进入 $v$ 时，选择器必须依据其他候选拒绝其中一部分。若同时观察一个已知集合后联合决定，属于第二类；若按到达顺序读取已用容量，属于第三类；剩余情形只能提前限制资格，属于第一类。

<div class="qed" aria-label="证毕">∎</div>

### 10.6 三种选择器配置

| 语义配置 | 状态与均衡 | chunk prefill 中的位置 |
| --- | --- | --- |
| `LH-exact streaming` | 每次硬路由后更新持久计数 | 保留原行为，但通常含长自适应链 |
| `General-DAG strict` | 固定来源槽位、静态偏置/先验、训练损失 | 满足定理 8.4 封闭有限正确性的候选 |
| `Block-lagged` | 分块内冻结计数器，分块后更新 | 分块内可批量，分块间仍顺序 |

## 11. 三种同刻/融合语义的实验设计

配置 O、J、F 不应混成一个实验条件。O/J 为每个输入归属桶分别保留局部输出记录的 `owner`；F 主动做语义商，并改变统一出站消息的 `owner`。

### 11.1 必做正确性门槛

| 检查项 | 参考 | 分块候选 | 判定 |
| --- | --- | --- | --- |
| 有序标量 | 按 $(\tau,t)$ 顺序执行 | 紧凑打包/扫描/因果批量 | 全部产物相等 |
| 联合标量 | 按 $\tau$ 调用 $\mathcal J_v$ | 分组化/分段批量 | 全部产物相等 |
| 因果前沿融合标量 | 按 $\tau$ 调用 $\mathcal F_v$，统一发射 | 分段融合 + 扫描/因果批量 | 全部产物相等 |
| 因果前沿不变量 | 式 GD-F1 的标量传播 | 批量化最大值/因果前沿传播 | 所有输出/状态满足定理 5.13 |
| 联合对比有序 | 两套参考 | 直接比较 | 只在式 GD-10 成立时期待相等 |
| F 对比 O/J | 三套参考 | 直接比较 | 默认不期待相等；评估语义商的质量/效率 |
| 流式对比拓扑序 | 封闭有限绝对时间调度 | 节点拓扑序调度 | 定理 8.4 所列产物 |

产物相等至少包括：

- 带 `owner` / `frontier` 的隐藏表示。
- 完整状态提交轨迹与每次提交的次序键。
- 状态因果前沿。
- 已选边。
- 消息标识符、`owner`、`frontier`、来源槽位、到达时间戳、目标与载荷。
- 最终节点状态。
- 每个固定 $\theta_t^{\mathrm{out}}$ 的读出 $y_t$。

### 11.2 最小诊断任务

1. **不等长路径碰撞**：直接边与两跳/三跳路径使归属不同 `token` 的消息在同一节点、同一 $\tau$ 相遇。
2. **跨时间归属逆序**：让 B 的短路径事件先于 A 的长路径事件到达，检查绝对时间状态可见性。
3. **状态因果前沿污染**：当前输入只有 A/B，但前状态因果前沿为 C>B；验证统一发射必须取 `owner=C` 而不是 `owner=B`。
4. **因果前沿融合**：A/B 同刻联合计算，只发射一个 `owner=B` 的消息，并与 O/J 分别标记 A/B 的输出记录比较。
5. **累加器反例**：复现实例 5.9，确保测试能发现“最终状态相同但按归属 `token` 划分的输出不同”。
6. **因果注意力节点**：分别验证事件次序掩码与归属 `token` 次序掩码的标量/批量等价。
7. **SSM/线性注意力节点**：验证不规则事件序列的紧凑打包扫描。
8. **联合交互节点**：让路由 B 显式依赖同刻 A 的特征，检查联合语义。
9. **稀疏来源槽位路由**：检查事件上界、槽位守恒、融合时的槽位消耗与输出可达性。
10. **双皮层 DAG**：验证多路径输入皮层、单向桥接与输出皮层的完整拓扑执行。

### 11.3 性能与质量指标

- 输出与产物是否正确且相等。
- 按归属 `token` 划分的事件总数 $M$。
- 节点分块工作量与实测延迟。
- 图关键路径并行跨度。
- 打包利用率与填充浪费。
- 节点/边负载分布。
- 碰撞密度：同一 $(v,\tau)$ 中归属 `token` 数量的分布。
- 因果前沿提升距离与提升频率。
- 融合压缩比：融合前分别带归属标签的记录数 / 统一输出数。
- 路由稳定性与训练质量。
- 配置 O、J、F 的任务质量差异。

## 12. 对当前 LH/Tide 机制的迁移

| 当前机制 | 一般 DAG 严格语义的处理 |
| --- | --- |
| 输入/输出皮层 + 桥接 | 保留为定义 3.1 的可选空间结构 |
| 每条边的单位时延 | 直接保留 |
| 消息载荷与元数据 | 增加消息标识符、`owner`、`frontier`、到达时间戳、来源槽位 |
| 外部 `token` 时钟 | 固定为 $Rt$ 注入与 $R(t+1)$ 读出，不由选择器或路由改写 |
| 同绝对内部轮次多源聚合 | 同时保留原始收件箱与按 `owner` 分组的视图；选择 O、J 或 F 契约 |
| 局部隐藏表示/KV | 归入节点持有的状态与节点转导器 |
| `signal norm` | 解释为局部隐藏表示或局部输出记录载荷的范数，并作为式 GD-11 的内容特征；不是轨迹或消息身份 |
| `affectcount/selectcount` | 流式语义配置保留；严格语义配置改为日志、训练统计或静态偏置来源 |
| 持久公平次序 | 不进入严格精确前向路由 |
| `clear_after_activation` | 明确解释为“选择器接受当前节点更新候选后清理哪一状态槽”，并成为节点转移的显式状态更新；不能依赖含糊的“激活”一词或隐藏为选择器副作用 |
| 紧凑打包/CROSSBATCH | 作为 $\mathcal C_v^P$ 的物理实现映射，不改变参考语义 |
| 阶段屏障 | 可封装在节点/子图转导器；不得产生未声明的零时延共享状态环 |

当前原生 LH 可以继续作为黄金参考实现，但本页不主张它自动满足任一严格语义配置。特别需要逐项检查：

- 现有聚合是否保留消息的 `owner`、逻辑时间戳与所需的显式来源关系。
- 现有状态/消息是否能增加因果前沿审计标签。
- 选择器计数器是否跨归属 `token` 或事件形成自适应链。
- 同一绝对内部轮次的节点更新是有序、联合、因果前沿融合，还是依赖线程顺序。
- 记忆清除/衰减的可见性与提交时序。
- 输出状态是否显式包含式 GD-E3 所需的读出寄存器。

## 13. 全面设计审视

### 13.1 已经解决的结构问题

1. **不再修改路径时延**：跳跃边保持单位时延，不通过中继分层改写参考语义。
2. **外部时钟固定**：`token` $t$ 在 $Rt$ 注入，第 $t$ 个读出在 $R(t+1)$ 发生；选择器/路由不能修改时钟。
3. **完整逻辑时间明确**：绝对轮次、阶段、路径年龄、消息 `owner` 与因果前沿是不同字段；同一边界的提交、读出、采样和注入顺序由式 GD-0.3 固定。
4. **逻辑事件已类型化**：输入、节点、读出与采样事件都有事件标识符、种类、位置、时间戳、归属支持集与因果前沿。
5. **依赖完备性已成为前提**：消息、状态、读出与自回归边界依赖均显式进入事件 DAG。
6. **固定读出已进入正确性契约**：节点分块必须对齐完整提交轨迹，定理 8.4 直接推出每个 $y_t$ 相同。
7. **一般 DAG 有直接证明**：证明按空间拓扑序归纳，不要求等长路径。
8. **长期上下文位置明确**：长期历史进入节点持有的 KV cache、SSM 状态或累加器，不藏在没有明确生命周期与归属字段的游走消息中。
9. **正确性与性能分层**：定理 8.4 证明调度等价；第 9 节再区分节点局部分块吞吐量、`token` 轴低并行跨度、工作量与事件上界。
10. **稀疏性不再依赖空间层级**：固定来源槽位给出适用于一般 DAG 与归属提升的 $LK|V|$ 上界。

这里“已经解决”只指流式与分块调度相对同一个绝对时间参考的等价性，不表示已经解决该参考与标准 `token` 前缀自回归语义的关系。

### 13.2 仍然存在的主要风险

#### 风险一：节点分块契约可能只是把顺序链藏进计算核

式 GD-12 是正确性契约，不是性能结论。若选择器或状态转移是任意黑盒，$\mathcal C_v^P$ 可能只能顺序执行整条事件序列。

研究上必须为每类节点声明：

- `token` 局部。
- 因果注意力/批量。
- 可由扫描组合。
- 同刻联合。
- 顺序回退。

并分别给出工作量/并行跨度见证。

#### 风险二：一般 DAG 的绝对时间次序不自动等于 `token` 次序

即使选择配置 O，一般 DAG 仍允许例 5.2b 的归属逆序：由命题 2.7，当路径长度差超过固定值 $R(t_B-t_A)$ 时，较晚 `token` 的短路径事件会先于较早 `token` 的长路径事件修改同一节点状态。该行为由固定 $R$ 与拓扑结构决定，运行时选择器不能改写其时间戳。配置 J 还允许较早归属 `token` 的同刻输出读取较晚归属 `token` 的输入。

这些行为属于本文绝对时间参考；它们不要求 `owner` 索引小的事件永远先于索引大的事件。本文能由完整时间戳可见性与因果前沿上界保证的是**输入前缀因果性**：式 GD-2.5 要求第 $t$ 个读出发生时尚不可见 $x_{t+1}$，式 GD-2.4 要求事件值的因果前沿不超过其时间戳可见前缀。这不等于证明该绝对时间参考与任意 GPT 顺序 transition 语义相同；后者仍需要单独的 transition-level 等价证明。

因此仍需要分别验证：

- 流式绝对时间因果性。
- 每个事件函数是否满足式 GD-2.4。
- 输出读出是否满足因果前沿 $\leq t$。
- 是否允许跨时间归属逆序。
- 是否要求定义 5.6 的按归属 `token` 因果条件。
- 是否实际满足式 GD-10。
- 是否采用定理 5.13 的因果前沿提升不变量。

#### 风险三：`owner` / `frontier` 不能代替完整来源信息

相同的 `owner` / `frontier` 组合可以经不同路径、不同来源槽位、不同绝对时间多次到达同一节点。因果前沿只给出依赖上界，不说明具体依赖了哪些 `token`；仅保留这两个字段仍不足以回放。逻辑事件标识符、消息标识符、到达时间戳、源、来源槽位、分支谱系和显式产生/消费关系都应进入执行记录。

#### 风险四：固定槽位可能限制表达力

$K$ 条来源槽位所承载的消息分支给出清晰上界，但禁止无界分裂。需要实验判断：

- 小 $K$ 是否足以覆盖有用的局部通信。
- 合并/融合后如何保留、消费或释放来源槽位。
- 训练是否出现槽位坍缩。
- 是否需要静态分层槽位池，而不是自由复制。

如果放松槽位守恒，必须提供新的事件数上界。

#### 风险五：全局负载均衡仍未被免费解决

静态偏置、先验和训练损失只保证分布意义上的均衡，不保证任意输入的即时硬均衡。配置 J/F 只能联合处理已经形成的时间戳分组，不能自动解决跨全部未来事件的容量分配。

#### 风险六：固定读出已定义，但其表示能力尚未验证

式 GD-E3 已固定“一周期一读出”，并要求读出寄存器是 $\mathcal S_z$ 的显式组件。剩余风险不再是读出是否存在，而是：

- 固定截止时间前的事件祖先是否足以产生有训练价值的 $y_t$。
- 长路径只影响未来读出的归纳偏置是否合理。
- 配置 F 是否过早丢失分别带归属标签的输出信息。
- 读出状态的训练目标、损失对齐与梯度路径是否明确。

#### 风险七：本页不覆盖图环

空间图无环是主定理前提。特殊递归子图可以：

- 按有限轮次展开为事件 DAG。
- 增加时延/状态边界。
- 封装为有独立分块契约的超级节点。

同一逻辑时间的零时延代数环不在本页范围内；若需要支持，必须另行定义同时方程或定点语义，并证明解的存在性、唯一性、求解终止性与成本。

#### 风险八：训练与后端实现映射仍需独立验证

调度正确性不自动证明：

- 反向图与梯度累积等价。
- 稀疏紧凑打包计算核在 Ascend 上高效。
- 动态形状、分段排序与通信成本可接受。
- 数值重排只产生声明范围内的浮点误差。

#### 风险九：固定周期事件参考语义尚未嵌入统一 StepTransition

本页把固定周期事件语义作为主要参考语义，并证明其两种封闭有限调度等价。定义 8.1 在最后一个读出后继续冲刷到 $H_L$，所以式 GD-E2 的最终状态是冲刷后状态；它们不等于下一注入边界上“节点状态 + 尚未到达消息”组成的延续状态。

要得到可接续 `decode` 的 `prefill` 交接状态，尚需构造单周期转移：

$$
\mathcal T_R:
X\times\mathcal S_R
\to
Y\times\mathcal S_R
$$

使 $\mathcal S_R$ 显式包含全部节点状态与跨边界在途消息；定义每个边界切面的状态快照；再证明连续 $L$ 个周期的事件执行正好是 $\operatorname{Fold}_{\mathcal T_R}^L$ 的展开。该嵌入定理是把本页结果提升为统一模型级 `prefill == decode` 定理的下一步。

### 13.3 当前推荐的最小实现顺序

1. 实现固定 $R$、六阶段边界次序与每周期强制读出。
2. 分离稳定 `event_id`、语义事件头、语义并列键与逻辑秩：事件头包含 `(kind, location, timestamp, owner_support, frontier)`；`semantic_tie` 只在所选语义配置要求同刻有序时进入逻辑秩；`event_id` 只用于身份和稳定序列化，不能用单个 `token`、物理创建次序或任意编号大小代替因果次序。
3. 实现消息键：`(message_id, owner, frontier, arrival_timestamp, src, dst, birth_slot, branch_lineage)`，并显式记录 `producer(message_id)` 与 `consumer(message_id)`。
4. 实现一般 DAG 绝对时间标量参考，并输出完整的事件、消息来源图和状态提交账本。
5. 实现配置 O 的节点拓扑序分块执行器，并对齐式 GD-E2 的五类产物与全部 $y_t$。
6. 定义边界切面、在途消息多重集与统一 $\mathcal T_R$，证明延续状态的折叠嵌入。
7. 为逐 `token` 映射、注意力、SSM/线性注意力增加紧凑打包节点计算核；其他局部逻辑先允许顺序回退。
8. 实现配置 J/F 的标量与分块语义。
9. 用不等长路径碰撞、归属逆序、跨边界延续、固定读出与状态因果前沿污染比较 O/J/F。
10. 加入固定来源槽位、工作量/并行跨度与负载指标。
11. 最后再引入训练期均衡和更复杂选择器。

### 13.4 当前可主张与不可主张

当前可以主张：

- 一般有限单位时延 DAG 在本文条件下具有封闭有限精确节点拓扑序分块调度。
- 固定周期注入/读出与跨边界延续消息可以同时纳入该调度等价。
- 每个有限给定序列执行在本文条件下具有类型化、依赖完备的事件 DAG。
- 消息的 `owner` 在非等长路径中是必要的归属消歧字段，但它不是完整来源信息。
- 配置 O、J、F 都可以分别建立调度等价定理。
- 折叠等价的联合计算核可以批量实现配置 O 的语义。
- 配置 F 在定理 5.13 的条件下保持显式 `token` 前缀依赖上界。
- 固定来源槽位给出一个兼容归属提升的超稀疏事件上界。

当前不能主张：

- 任意一般 DAG、任意节点计算核都有高性能 `prefill`。
- 配置 J 与配置 O 在未证明式 GD-10 时语义相同。
- 配置 F 的数值状态转移自动具有扫描或批量高性能实现。
- 当前计算核或选择器族已经给出低并行跨度的并行 `prefill` 见证。
- 当前 LH 选择器已满足严格语义配置。
- 静态/训练均衡能提供任意输入上的硬容量。
- 封闭执行的冲刷后最终状态可以直接作为下一 `token` 边界的 `decode` 延续状态。
- 本页调度定理已经等同于统一 $\mathcal T_R$ 上的完整模型级 `prefill == decode` 定理。
- 本页已经解决图环、反向或 Ascend 实现映射。

## 14. 研究结论

一般 DAG 下，消息的 `owner` 与 `frontier` 都不应被删除，但二者职责不同。绝对时间决定事件何时发生；`owner` 是当前消息的归属索引；`frontier` 给出数值内容最多依赖到哪个 `token` 前缀；节点持有的状态决定历史如何影响当前计算；消息来源图记录实例级分叉与汇聚。配置 F 不再分别产生旧 `owner` 的后继输出，而把统一输出的 `owner` 提升为因果前沿。

最小正向命题是：

> 对任意满足 $R=d_{\min}$ 的有限单位时延空间 DAG，只要固定注入/读出阶段次序、跨边界延续语义、类型化事件依赖、状态唯一持有与精确节点分块契约均成立，就可以把针对有限给定序列的封闭绝对时间流式执行重排为节点拓扑序分块执行，并保持全部隐藏表示、提交、路由、消息、冲刷后最终状态与固定周期读出产物。

这个命题保留了 Tide 所需的一般空间 DAG，也把真正的性能问题准确地下推到：

- 节点事件序列计算核是否至少具有可接受的局部分块吞吐量，以及是否进一步具有因果批量、扫描或联合执行所需的低并行跨度结构。
- 事件数是否有超稀疏上界。
- 选择器是否避免不可收缩的跨 `token` 控制链。
- O、J、F 中哪一种更有训练价值、任务价值与可实现的数值收缩。
