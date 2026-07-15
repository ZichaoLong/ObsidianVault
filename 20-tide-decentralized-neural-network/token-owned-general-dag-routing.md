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

> [!note] 非形式化的四层阅读图
> 下表只帮助区分直观对象，不定义任何集合或函数；正式阅读从定义 0.1 开始。
> | 层级 | 对象 | 不应混同的对象 |
> | --- | --- | --- |
> | 外部序列 | `token` 位置 $t$、输入值 $x_t$、一次 `token` 出现 $(t,x_t)$ | 消息、事件、计算轨迹 |
> | 静态空间结构 | 空间节点 $v$、空间边 $(u,v)$、输入/输出锚点 | 某次执行中的节点事件、事件依赖边 |
> | 动态参考语义 | 事件实例、消息实例、已提交状态值、局部输出记录、已选空间边集合 | 物理线程、设备计算核调用顺序 |
> | 来源与执行 | 消息产生/消费关系、事件依赖边、逻辑次序、物理调度 | `owner`、因果前沿或墙钟先后 |
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
5. `timestamp` 在英文对照或接口中始终写成一个单词，不使用 `time stamp`。下面的表格只规定语言写法，不引入数学对象。

#### 直接保留英文的 AI 术语

| 本文写法 | 不作为默认写法 | 原因 |
| --- | --- | --- |
| `token` | 令牌、词元 | 本文同时讨论文本与一般模型输入；需要区分位置 $t$、值 $x_t$ 和一次出现 $(t,x_t)$，“词元”会过度强调语言学含义 |
| `prefill` / `decode` | 预填充 / 解码 | 二者是本文要比较的标准执行模式，英文在 AI 系统领域更直接 |
| `logits` | 输出逻辑值 | 固定模型接口名；需要解释时称为“归一化或采样前的输出分数” |
| Transformer / Mamba / SSM / FFN / KV cache / QKV | 人工翻译名 | 模型名、计算核族与固定缩写不翻译 |
| DAG / ISA / SSA / C++ | 展开的中文全称 | 首次需要数学定义时可补中文，后续使用固定缩写 |

#### 形式化阅读规则

本页开头的摘要、直观模型和对象层级表只用于说明研究意图，不承担数学定义。需要严格阅读时，可以从定义 0.1 开始。

从定义 0.1 起，本文遵守以下规则：

1. 一个概念首次进入正式定义、命题、定理或证明前，必须说明它所属的集合，或把它声明为集合、集合元素、函数、部分函数、关系、有限序列、多重集、有限元组，或由这些对象定义的性质。
2. 上一条也约束定义正文中的概念，而不只约束证明中的符号。一个定义不能用未声明的“键”“凭证”“谱系”“阶段内位置”等词代替真正的数学对象；若这些词有必要，就先把它们定义成集合、坐标、函数或关系。
3. 一个函数必须给出定义域和值域；一个关系必须说明它是哪两个集合笛卡尔积的子集；一个有限元组必须给出每个坐标所属的集合。
4. 同一个符号不同时承担事件身份、逻辑时间、消息归属和来源关系等不同职责。若同名投影在多个不交类型上重载，每个分支仍须单独给出定义域和值域，并且实参类型必须唯一确定分支。
5. 全文复用的正式对象必须由编号定义赋予数学类型；只在一个命题或证明内使用的局部对象，也必须在当地明确写出其类型。两者都没有做到的词只能是普通语言说明，不能作为后续推理前提。
6. 若一个概念只在单个证明中使用，就在该证明内直接定义相应集合、关系或函数，不额外提升为全文术语。
7. 直观说明可以不形式化，但必须同时满足两点：其含义无需一串新术语即可直接理解；正文明确它不承担定义或证明前提。若一段文字为了显得准确而引入多个未定义抽象词，就必须改写成数学定义，而不是继续增加解释性同义词。
8. 本页不从其他文档导入正式定义或定理。外部文档只能提供研究关系、历史或参考；本页使用的数学对象、前提与结论必须在本页重新声明。

因此，本文的开发检查不只是“符号是否先定义”，而是逐句询问：句中的每个概念到底是哪个集合、哪个元素、哪个函数、哪个关系或哪个有限记录。若无法回答，就应删除该概念、把它改成直白说明，或先补正式定义。

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

对任意集合 $A$ 与 $n\in\mathbb N$，$A^n$ 表示所有长度为 $n$、元素属于 $A$ 的有限序列组成的集合，并约定：

$$
A^0=\{()\}.
$$

定义 $A$ 上的有限序列集合：

$$
A^\star
=
\bigcup_{n\in\mathbb N}A^n.
$$

本文用圆括号表示有限序列。序列保留顺序和重复元素。

定义有限序列中的出现次数函数：

$$
\operatorname{occ}_A:A^\star\times A\to\mathbb N.
$$

若 $\mathbf a=(a_0,\ldots,a_{n-1})\in A^n$ 且 $a\in A$，规定：

$$
\operatorname{occ}_A(\mathbf a,a)
=
\left|\{i\in[n]\mid a_i=a\}\right|.
$$

下标 $A$ 可由序列类型唯一确定时，简写为 $\operatorname{occ}(\mathbf a,a)$。

定义 $A$ 上的有限多重集集合：

$$
\mathcal M_{\mathrm{fin}}(A)
=
\left\{
\mu:A\to\mathbb N
\ \middle|
\{a\in A\mid \mu(a)\neq 0\}
\text{ 是有限集}
\right\}.
$$

其中 $\mu(a)$ 是元素 $a$ 的重数。因此有限多重集保留重复元素，不因两个元素的载荷相等而把两个实例合并。

定义支撑集函数：

$$
\operatorname{supp}_A:
\mathcal M_{\mathrm{fin}}(A)
\to 2^A,
$$

$$
\operatorname{supp}_A(\mu)
=
\{a\in A\mid\mu(a)>0\}.
$$

下标 $A$ 可由实参所属的多重集空间唯一确定时，简写为 $\operatorname{supp}(\mu)$。

零函数 $0_A:A\to\mathbb N$ 称为空多重集。给定有限指标集合 $I$ 和多重集 $\mu_i\in\mathcal M_{\mathrm{fin}}(A)$，定义多重集并：

$$
\biguplus_{i\in I}\mu_i
\in\mathcal M_{\mathrm{fin}}(A),
$$

$$
\left(\biguplus_{i\in I}\mu_i\right)(a)
=
\sum_{i\in I}\mu_i(a),
\qquad a\in A.
$$

对任意集合 $A$，定义其幂集：

$$
2^A=\{B\mid B\subseteq A\}.
$$

对任意集合 $A,B$，定义带类型标签的不交并：

$$
A\sqcup B
=
(\{0\}\times A)\cup(\{1\}\times B).
$$

对指标集合 $I$ 与集合族 $(A_i)_{i\in I}$，定义：

$$
\bigsqcup_{i\in I}A_i
=
\{(i,a)\mid i\in I,\ a\in A_i\}.
$$

若对每个 $i\in I$ 都有函数 $f_i:A_i\to B$，则可在带标签不交并上定义函数：

$$
f:\bigsqcup_{i\in I}A_i\to B,
\qquad
f((i,a))=f_i(a).
$$

本文对同名字段投影采用带类型重载。一般地，给定指标集合 $I$、集合族 $(A_i)_{i\in I}$ 和函数族 $(f_i:A_i\to B_i)_{i\in I}$，本文不假设不同 $A_i$ 天然不交；同时使用多个分支时，正式定义域和值域分别取 $\bigsqcup_{i\in I}A_i$ 与 $\bigsqcup_{i\in I}B_i$，并定义带标签函数 $(i,a)\mapsto(i,f_i(a))$。正文只在指标 $i$ 已由当前量词或另一个已声明坐标唯一确定时省略标签和函数下标。每个公式中的实参及其已声明索引必须唯一确定所用分支。

固定一个特殊符号 $\bot$。除非某个定义显式把 $\bot$ 加入集合，否则约定 $\bot$ 不属于该集合。

若 $A,B$ 是集合，记：

$$
f:A\rightharpoonup B
$$

表示 $f$ 是一个部分函数：存在子集 $D\subseteq A$，使 $f:D\to B$ 是函数；此时定义 $\operatorname{dom}(f)=D$。

对函数 $f:A\to B$，定义其值域像集：

$$
\operatorname{ran}(f)
=
\{f(a)\mid a\in A\}
\subseteq B.
$$

本文把二元关系 $R$ 明确定义为某个笛卡尔积的子集。例如，$R\subseteq A\times A$ 是 $A$ 上的二元关系。若对任意 $x,y,z\in A$，关系 $<\ \subseteq A\times A$ 满足：

$$
x<y,\ y<z\Longrightarrow x<z,
$$

$$
\neg(x<x),
$$

以及：

$$
x\neq y
\Longrightarrow
(x<y\text{ 或 }y<x),
$$

则称 $<$ 是 $A$ 上的严格全序。

本文是自足文档：后文使用的输入序列、事件 DAG、前缀因果性、工作量与并行跨度均在本文首次使用前定义。一般自适应 routing 的下界属于独立的反向研究问题，不作为本文任何定义、命题或定理的证明前提。

### 定义 0.2：输入序列与固定周期

给定两个非空集合 $X$ 与 $Y$，分别称为输入值集合和读出值集合。再给定输入块长度 $L\in\mathbb N$ 与固定周期：

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

定义绝对注入轮次函数：

$$
\operatorname{InTime}_{R,L}:[L]\to\mathbb N,
$$

$$
\operatorname{InTime}_{R,L}(t)=Rt.
\tag{GD-0.1}
$$
^eq-fixed-injection-time

定义读出轮次函数：

$$
\operatorname{OutTime}_{R,L}:[L]\to\mathbb N,
$$

$$
\operatorname{OutTime}_{R,L}(t)=R(t+1).
\tag{GD-0.2}
$$
^eq-fixed-readout-time

$R$ 是参考语义的常数，不依赖输入值、节点状态、任何模型内部决策或当前运行时活动。内部计算不能推迟或提前式 GD-0.1 与 GD-0.2 规定的边界。

这里 $R$ 首先是逻辑周期。若还要求真实设备每隔固定墙钟周期输出一个 `token`，则另取 $T_{\mathrm{ext}}\in\mathbb R$ 且 $T_{\mathrm{ext}}>0$，并要求实现证明第 $t$ 个读出在墙钟截止时间 $(t+1)T_{\mathrm{ext}}$ 前完成。该实时吞吐量条件属于性能见证，不由后文的调度等价定理自动推出。

### 定义 0.3：阶段与完整逻辑时间戳

取阶段数：

$$
N_{\mathrm{phase}}\in\mathbb N_{>0},
\qquad
N_{\mathrm{phase}}\geq 6,
$$

定义阶段索引集合：

$$
\Phi
=
\{0,\ldots,N_{\mathrm{phase}}-1\}.
$$

定义完整逻辑时间戳集合：

$$
\Theta
=
\mathbb N\times\Phi.
$$

定义两个坐标投影：

$$
\operatorname{round}:\Theta\to\mathbb N,
\qquad
\operatorname{round}((\tau,i))=\tau,
$$

$$
\operatorname{phase}:\Theta\to
\Phi,
\qquad
\operatorname{phase}((\tau,i))=i.
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

定义由 $<_{\Theta}$ 得到的非严格次序关系：

$$
\leq_{\Theta}
\subseteq
\Theta\times\Theta.
$$

对任意 $\theta,\theta'\in\Theta$，规定：

$$
\theta\leq_{\Theta}\theta'
\quad\Longleftrightarrow\quad
\bigl(\theta<_{\Theta}\theta'\bigr)
\text{ 或 }
\theta=\theta'.
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
\Phi,
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

给定一个有限非空集合 $V$ 和一个二元关系：

$$
E\subseteq V\times V.
$$

定义有向图：

$$
G=(V,E).
$$

称 $G$ 无有向环，当且仅当不存在 $k\in\mathbb N_{>0}$ 和节点序列：

$$
(v_0,v_1,\ldots,v_k)\in V^{k+1},
$$

同时满足：

$$
v_0=v_k
$$

以及：

$$
(v_i,v_{i+1})\in E,
\qquad i\in[k].
$$

有限且无有向环的有向图称为有限有向无环图，简称 DAG。

给定 $u,v\in V$ 与 $k\in\mathbb N$。从 $u$ 到 $v$ 的一条长度为 $k$ 的有向路径是节点序列：

$$
p=(v_0,v_1,\ldots,v_k)\in V^{k+1},
$$

满足：

$$
v_0=u,
\qquad
v_k=v,
$$

并且：

$$
(v_i,v_{i+1})\in E,
\qquad i\in[k].
$$

定义该路径的长度为 $|p|=k$。当 $k=0$ 时，序列 $(u)$ 是从 $u$ 到自身的零长度路径。

定义长度为 $k$ 的路径集合：

$$
\mathsf{Path}_G^k(u,v)
=
\left\{
p\in V^{k+1}
\ \middle|
p\text{ 满足上述从 }u\text{ 到 }v\text{ 的路径条件}
\right\}.
$$

定义全部有限路径集合：

$$
\mathsf{Path}_G(u,v)
=
\bigcup_{k\in\mathbb N}\mathsf{Path}_G^k(u,v),
$$

定义全图有限路径集合：

$$
\mathsf{Path}_G(\cdot,\cdot)
=
\bigcup_{u,v\in V}\mathsf{Path}_G(u,v),
$$

以及从输入节点出发的全部有限路径集合：

$$
\mathsf{Path}_G(s,\cdot)
=
\bigcup_{v\in V}\mathsf{Path}_G(s,v).
$$

路径长度投影是函数：

$$
|\cdot|:
\mathsf{Path}_G(\cdot,\cdot)
\to\mathbb N,
$$

其中若 $p\in\mathsf{Path}_G^k(s,v)$，则 $|p|=k$。

一个带输入输出的空间 DAG 是三元组：

$$
(G,s,z),
$$

其中 $G=(V,E)$ 是上述有限 DAG，并且：

- $s\in V$ 是指定输入节点。
- $z\in V$ 是指定输出节点。
- $s\neq z$。
- 每个 $v\in V$ 都位于至少一条从 $s$ 到 $z$ 的有向路径上。

另外固定空间边集合上的严格全序关系：

$$
<_{E}\ \subseteq E\times E.
$$

它只用于规范排列同一局部输出所选的多条边，不表示额外计算依赖。由“每个节点都位于某条从 $s$ 到 $z$ 的路径上”和无环性可推出：$s$ 没有入边、$z$ 没有出边，且其他节点至少各有一个直接空间前驱和直接空间后继。因此 $s$ 与 $z$ 分别是唯一的入度零节点与出度零节点；这里不把“唯一”留作未定义的额外条件。

对边 $(u,v)\in E$，$u$ 称为 $v$ 的直接空间前驱，$v$ 称为 $u$ 的直接空间后继。

### 定义 1.2：路径长度集合与全图深度

定义可达路径长度集合函数：

$$
\Lambda:V\to 2^{\mathbb N},
$$

$$
\Lambda(v)
=
\{|p|\mid p\in\mathsf{Path}_G(s,v)\}.
$$

因为 $G$ 有限且无环，$\Lambda(v)$ 是有限非空集合。

定义空间 DAG 的最大路径长度 $D\in\mathbb N$：

$$
D
=
\max_{v\in V}\max\Lambda(v).
$$

由于有向路径不能重复经过同一个节点：

$$
D\leq |V|-1.
$$

定义输入到输出的最短路径长度 $d_{\min}\in\mathbb N_{>0}$：

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

定义参考传播时延函数：

$$
\operatorname{delay}:E\to\mathbb N_{>0},
$$

并规定每条边的参考传播时延恰好为一个全局内部轮次：

$$
\operatorname{delay}((u,v))=1,
\qquad (u,v)\in E.
$$

这是一条语义约束，不是硬件传输延迟。物理运行时可以融合传输、使用缓冲区或异步执行，但必须保持逻辑到达时间。

> [!note] 一般 DAG 与等层 DAG
> 若对任意节点 $v$，集合 $\Lambda(v)$ 只有一个元素，则所有从 $s$ 到 $v$ 的路径等长，旧文档中的等层 DAG 是本页模型的特殊情形。本文不再把这一性质作为前提，也不通过中继节点改变原边的单位时延。

## 2. 前缀因果性与固定周期路径时间

### 定义 2.1：前缀因果函数与因果前沿

定义因果前沿索引空间：

$$
\mathbb F_L
=
\{-1\}\cup[L].
$$

给定任意集合 $\mathcal Q$、函数：

$$
f:X^L\to\mathcal Q,
$$

以及 $c\in\mathbb F_L$。称函数 $f$ 是 $c$-前缀因果的，当且仅当对任意两个输入序列 $x_{0:L},\bar x_{0:L}\in X^L$，只要：

$$
x_j=\bar x_j,
\qquad
\text{对每个满足 }j\leq c\text{ 的 }j\in[L],
$$

就有：

$$
f(x_{0:L})=f(\bar x_{0:L}).
$$

若 $c=-1$，前提中没有需要比较的输入坐标，因此该条件表示 $f$ 是常函数。

若研究一个可能不存在的记录，则使用函数：

$$
f:X^L\to\mathcal Q_\bot,
$$

其中定义加入缺失值后的扩充集合：

$$
\mathcal Q_\bot
=
\mathcal Q\cup\{\bot\},
$$

其中 $\bot\notin\mathcal Q$，并用 $\bot$ 表示该记录不存在。因此函数值相等同时要求两次执行中的存在性相同，并且在存在时记录值相同。$f(x_{0:L})=\bot$ 不表示发生了一次带空值的计算事件。

若 $f$ 是 $c$-前缀因果的，则称 $c$ 是函数 $f$ 的一个有效因果前沿。一个函数可以具有多个有效因果前沿；本文允许使用保守上界，不要求选择最小者。

例如，对每个 $t\in[L]$，定义坐标函数：

$$
\Xi_t:X^L\to[L]\times X,
\qquad
\Xi_t(x_{0:L})=(t,x_t).
$$

则 $\Xi_t$ 是 $t$-前缀因果的，所以 $t$ 是 $\Xi_t$ 的一个有效因果前沿。

在固定输入序列 $x_{0:L}$ 上，$\Xi_t(x_{0:L})=\xi_t$。这里不能只写成“值 $x_t$ 的因果前沿”：若两个位置恰好具有相同输入值，它们仍是不同的输入出现，并具有不同的位置索引。

> [!example] 如何读取因果前沿
> 声明“$3$ 是 $f$ 的有效因果前沿”只断言：只要两个输入序列的 $x_0,x_1,x_2,x_3$ 相同，函数 $f$ 的输出就必须相同。它不断言 $f$ 一定读取了这四个坐标，也不记录一次执行中具体经过了哪些事件或消息；后者要由定义 4.2a 的产生/消费函数和定义 7.2 的事件依赖关系表示。

### 定义 2.1a：抽象逻辑事件头与事件值

给定有限非空事件种类集合 $\mathcal K$ 与非空事件标识符集合 $\mathsf{EID}$。

取一个不属于 $V$ 的符号 $\mathtt{external}$，并定义事件位置集合：

$$
\mathsf{Loc}
=
V\cup\{\mathtt{external}\}.
$$

定义事件头集合：

$$
\mathfrak H_L(\mathcal K)
=
\mathsf{EID}
\times\mathcal K
\times\mathsf{Loc}
\times\Theta
\times 2^{[L]}
\times\mathbb F_L.
$$

一个逻辑事件头是该集合中的六元组：

$$
h_e
=
(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e),
\tag{GD-2.0}
$$
^eq-logical-event-header

六个坐标依次满足：

- $\eta_e\in\mathsf{EID}$ 是事件标识符。
- $\kappa_e\in\mathcal K$ 是事件种类。
- $\ell_e\in\mathsf{Loc}$ 是事件位置。
- $\theta_e\in\Theta$ 是事件值对后继可见的逻辑提交时间戳。
- $\Omega_e\subseteq[L]$ 是该事件直接联合处理或在外部接口上显式标识的归属支持集，即一组位置索引。它不是实际因果依赖集合，也不应写成“从 $0$ 到因果前沿的全部位置”来代替 $c_e$。
- $c_e\in\mathbb F_L$ 是事件值的有效因果前沿。

对常规节点事件，$\Omega_e$ 记录当前收件箱中被该事件直接消费的 `owner` 桶；它不包含仅通过节点前状态间接影响本事件的历史位置。配置 F 还可能产生一个不属于当前 $\Omega_e$ 的提升后输出 `owner=c_e`，因此 `support` 也不是“事件值中出现过的全部归属标签”。

给定事件值全集 $\mathsf{EVal}$，以及事件值空间函数：

$$
\mathcal V:
\mathfrak H_L(\mathcal K)
\to 2^{\mathsf{EVal}}.
$$

对每个 $h\in\mathfrak H_L(\mathcal K)$，简写：

$$
\mathcal V_h=\mathcal V(h),
$$

并称其为头 $h$ 对应的事件值集合。定义逻辑事件实例集合：

$$
\mathfrak E_L(\mathcal K)
=
\left\{
(h,\nu)
\ \middle|
h\in\mathfrak H_L(\mathcal K),
\ \nu\in\mathcal V_h
\right\}.
$$

一个逻辑事件实例是元素：

$$
e=(h_e,\nu_e),
$$

满足：

$$
e\in\mathfrak E_L(\mathcal K),
\qquad
\nu_e\in\mathcal V_{h_e}.
$$

定义事件头和值投影函数：

$$
h:
\mathfrak E_L(\mathcal K)
\to
\mathfrak H_L(\mathcal K),
$$

$$
h(e)=h_e,
$$

$$
\nu:
\mathfrak E_L(\mathcal K)
\to
\mathsf{EVal},
$$

$$
\nu(e)=\nu_e.
$$

定义实际事件的字段投影函数：

$$
\operatorname{id}:
\mathfrak E_L(\mathcal K)\to\mathsf{EID},
\qquad
\operatorname{kind}:
\mathfrak E_L(\mathcal K)\to\mathcal K,
$$

$$
\operatorname{loc}:
\mathfrak E_L(\mathcal K)\to\mathsf{Loc},
\qquad
\operatorname{time}:
\mathfrak E_L(\mathcal K)\to\Theta,
$$

$$
\operatorname{support}:
\mathfrak E_L(\mathcal K)\to 2^{[L]},
\qquad
\operatorname{frontier}:
\mathfrak E_L(\mathcal K)\to\mathbb F_L.
$$

它们在 $e=(h_e,\nu_e)$ 且 $h_e=(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e)$ 上取值为：

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

符号 $e$ 始终表示完整事件实例，$\eta_e$ 只表示六元事件头的第一个坐标，二者不能互换。事件标识符的形式性质由定义 2.1b 的单射条件给出；“由哪些字段确定生成”属于实现约束，不参与本文的事件依赖证明，也不能用某种编号大小或字典序代替依赖关系。

实际事件集合只包含真正发生的事件。动态事件不存在时，该事件不属于实际事件集合；不通过加入一个值为 $\bot$ 的假事件表示。一个已经发生的事件可以在其已定义值元组中含有 $\bot$ 分量；这只表示该分量为空，不表示事件本身不存在。

这里的事件不是沿边传输的数据包。事件表示“一次计算已经发生”；消息是事件产生、随后沿空间边传播的产物。一个事件可以消费多条消息、更新一次节点状态，并产生零条或多条新消息。

### 定义 2.1b：抽象事件图与依赖边

给定一次有限执行的实际事件集合：

$$
\mathcal E
\subseteq
\mathfrak E_L(\mathcal K),
$$

要求事件标识符投影在 $\mathcal E$ 上是单射，即对任意 $e,e'\in\mathcal E$：

$$
\operatorname{id}(e)=\operatorname{id}(e')
\quad\Longrightarrow\quad
e=e'.
$$

再给定二元关系：

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

称 $D$ 无有向环，当且仅当不存在 $k\in\mathbb N_{>0}$ 与事件序列：

$$
(e_0,e_1,\ldots,e_k)\in\mathcal E^{k+1},
$$

同时满足：

$$
e_0=e_k,
$$

以及：

$$
(e_i,e_{i+1})\in\mathcal A,
\qquad i\in[k].
$$

若 $D$ 无有向环，则称其为逻辑事件 DAG。这里尚未规定哪些参考依赖必须进入 $\mathcal A$；第 7 节将为固定周期 Tide 执行实例化消息、状态、读出与边界依赖关系，并定义事件值依赖完备性。

### 定义 2.1c：固定边界事件头

定义边界事件种类集合：

$$
\mathcal K_{\mathrm{bdry}}
=
\{\mathtt{inject},\mathtt{readout},\mathtt{sample}\}.
$$

先选择三个事件标识符函数：

$$
\eta^{\mathrm{in}},
\eta^{\mathrm{out}},
\eta^{\mathrm{sample}}:
[L]\to\mathsf{EID}.
$$

对 $t\in[L]$，分别简写 $\eta^{\mathrm{in}}(t)=\eta_t^{\mathrm{in}}$、$\eta^{\mathrm{out}}(t)=\eta_t^{\mathrm{out}}$ 与 $\eta^{\mathrm{sample}}(t)=\eta_t^{\mathrm{sample}}$。

要求三个函数都是单射，并且 $\operatorname{ran}(\eta^{\mathrm{in}})$、$\operatorname{ran}(\eta^{\mathrm{out}})$ 与 $\operatorname{ran}(\eta^{\mathrm{sample}})$ 两两不交。等价地，所有实际使用的 $\eta_t^{\mathrm{in}}$、$\eta_t^{\mathrm{out}}$ 和 $\eta_t^{\mathrm{sample}}$ 两两不同。

在给定序列执行中不使用 $\eta_t^{\mathrm{sample}}$。对每个 $t\in[L]$，定义输入事件头：

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

定义周期索引函数：

$$
q_R:\mathbb N\to\mathbb N,
$$

$$
q_R(\tau)
=
\left\lfloor\frac{\tau}{R}\right\rfloor,
$$

以及周期内轮次偏移函数：

$$
r_R:\mathbb N\to\{0,\ldots,R-1\},
$$

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

给定 `token` 索引 $t\in[L]$、空间节点 $v\in V$ 与路径 $p\in\mathsf{Path}_G(s,v)$。称有序对 $(t,p)$ 为路径计时见证：它描述“位置 $t$ 的输入若沿 $p$ 实际派发消息，这些消息何时到达”，但它本身不是消息实例、消息分支或实际发生的事件。

定义路径年龄函数：

$$
k_G:
\mathsf{Path}_G(s,\cdot)
\to\mathbb N,
$$

$$
k_G(p)=|p|,
$$

定义绝对到达轮次函数：

$$
A_R:
[L]\times\mathsf{Path}_G(s,\cdot)
\to\mathbb N,
$$

$$
A_R(t,p)
=
Rt+|p|,
\tag{GD-2.1}
$$
^eq-fixed-arrival-round

以及到达时间戳函数：

$$
\theta_R^{\mathrm{arr}}:
[L]\times\mathsf{Path}_G(s,\cdot)
\to\Theta,
$$

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(A_R(t,p),i_{\mathrm{arrive}}).
\tag{GD-2.2}
$$
^eq-fixed-arrival-timestamp

路径年龄可以大于 $R$。此时，若该路径对应的消息分支实际存在，它会在 `token` $t+1$ 的注入边界之后才到达；固定周期本身不截断它。

### 推论 2.3a：最短路径到达时间戳早于固定读出

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

因此，最短路径见证的到达阶段严格早于同一绝对轮次的提交阶段，而提交阶段又严格早于第 $t$ 个固定读出。第 7.5 节定义状态提交与读出后，会把这个纯时间戳不等式用于确定读出可见性。

**证明。**

由 $|p|=R$ 与式 GD-2.1，到达轮次为 $Rt+R=R(t+1)$；阶段不等式直接来自式 GD-0.3。

<div class="qed" aria-label="证毕">∎</div>

### 定义 2.4：时间戳处可用的输入前缀

定义时间戳可见输入前缀函数：

$$
a_{R,L}:\Theta\to\mathbb F_L.
$$

对任意 $\theta\in\Theta$，规定：

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

其中 $\leq_{\Theta}$ 已在定义 0.3 中给出。

给定任意集合 $\mathcal Q$、函数 $f:X^L\to\mathcal Q_\bot$、时间戳 $\theta\in\Theta$ 与 $c\in\mathbb F_L$。称四元组：

$$
(\mathcal Q,f,\theta,c)
$$

是一个有效的带时间戳前缀因果量，当且仅当 $f$ 在定义 2.1 的意义下是 $c$-前缀因果的，并且：

$$
c
\leq
a_{R,L}(\theta)
\tag{GD-2.4}
$$
^eq-timestamp-frontier-bound

后文每当为某个随输入序列变化的正式对象声明产生时间戳与因果前沿时，都必须同时给出或隐含一个相应的函数 $f$，并满足上述有效四元组条件。也就是说，因果前沿既必须是定义 2.1 的函数依赖上界，也不能超过该逻辑时间戳已经注入的最大输入位置。

特别地，对每个可能使用的事件标识符 $\eta\in\mathsf{EID}$，用函数：

$$
f_\eta:
X^L\to
\mathfrak E_L(\mathcal K)\cup\{\bot\}
$$

表示该标识符在不同输入序列上对应的实际事件，或用 $\bot$ 表示事件不存在；当 $f_\eta(x_{0:L})\neq\bot$ 时，要求其事件标识符等于 $\eta$。若当前输入上 $e=f_\eta(x_{0:L})$，则事件头必须满足：

$$
\operatorname{frontier}(e)
\leq
a_{R,L}(\operatorname{time}(e)),
$$

并且 $f_\eta$ 必须是 $\operatorname{frontier}(e)$-前缀因果的。函数值包含完整事件头和事件值，因此该条件同时约束事件存在性、头字段与值；动态事件存在性不是由某次已经发生的事件头自行推出。

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

因此，两个路径计时见证具有相同目标空间节点 $z$ 与相同到达时间戳 $(4,i_{\mathrm{arrive}})$。第 4 节把路径传播实例化为消息后，这正是可能发生同刻汇聚的最小几何条件；这里尚未使用消息或路由的定义。

### 命题 2.6：空间节点与到达时间不能唯一恢复输入位置

对固定节点 $v\in V$，定义路径计时见证集合：

$$
\mathcal W_v
=
[L]\times\mathsf{Path}_G(s,v),
$$

以及函数：

$$
\Psi_v:\mathcal W_v\to\{v\}\times\mathbb N,
$$

$$
\Psi_v(t,p)=(v,A_R(t,p)).
$$

取两个不同输入位置 $t_A,t_B\in[L]$，以及两条从 $s$ 到同一节点 $v$ 的路径 $p_A,p_B$。若：

$$
Rt_A+|p_A|
=
Rt_B+|p_B|,
$$

则有两个不同的路径计时见证 $(t_A,p_A)$ 与 $(t_B,p_B)$ 满足：

$$
\Psi_v(t_A,p_A)
=
\Psi_v(t_B,p_B).
$$

因此 $\Psi_v$ 不是单射，从目标空间节点与到达轮次不能唯一恢复路径计时见证中的输入位置坐标。

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

但两个见证的输入位置坐标分别是不同的 $t_A$ 与 $t_B$，所以 $(v,\tau)$ 不能唯一确定这个坐标。

<div class="qed" aria-label="证毕">∎</div>

命题 2.6 目前只是路径计时映射不单射的结论。定义 4.1 引入消息的 `owner` 坐标后，它会直接说明：如果运行语义希望保留当前归属索引，就不能只存目标节点和到达时间。

### 命题 2.7：前序输入位置的长路径晚到条件

取 $t_A<t_B$，并令两条路径 $p_A,p_B$ 都从 $s$ 到达同一空间节点 $v$。则路径计时见证 $(t_B,p_B)$ 的到达轮次小于 $(t_A,p_A)$ 的到达轮次，当且仅当：

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

这个命题表明：即使输入/输出时钟固定，只要路径长度差超过输入位置的注入轮次差，一般 DAG 仍会出现较晚输入位置的短路径见证先到。它只比较定义 2.3 的到达轮次，不涉及尚未定义的消息归属或选择器。

## 3. 可选的双皮层空间结构

### 定义 3.1：输入/输出双皮层 DAG

设输入皮层是有限 DAG：

$$
G_I=(V_I,E_I),
$$

并给定两个节点：

$$
s,b_I\in V_I.
$$

要求每个 $v\in V_I$ 都位于至少一条从 $s$ 到 $b_I$ 的有向路径上。

设输出皮层是有限 DAG：

$$
G_O=(V_O,E_O),
$$

并给定两个节点：

$$
b_O,z\in V_O.
$$

要求每个 $v\in V_O$ 都位于至少一条从 $b_O$ 到 $z$ 的有向路径上。

假设：

$$
V_I\cap V_O=\varnothing.
$$

定义单向桥接边：

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

工程设计可以另行选择一个节点一一对应关系，使两侧空间边在该对应下方向相反；这个额外选择不属于定义 3.1，也不增加从输出皮层返回输入皮层的执行边。

### 引理 3.2：单向桥接保持 DAG 性质

若 $G_I$ 与 $G_O$ 都是 DAG，且不存在从 $V_O$ 指向 $V_I$ 的边，则定义 3.1 的组合图 $G$ 是 DAG。

**证明。**

假设 $G$ 中存在有向环。若该环完全位于 $V_I$ 或 $V_O$，分别与 $G_I$ 或 $G_O$ 是 DAG 矛盾。

若该环同时经过两侧，则它必须通过桥接 $(b_I,b_O)$ 从 $V_I$ 进入 $V_O$。要回到 $V_I$，环中必须存在一条从 $V_O$ 指向 $V_I$ 的边，但前提排除了这种边，矛盾。

所以 $G$ 无有向环。

<div class="qed" aria-label="证毕">∎</div>

## 4. 消息、收件箱与有限事件性

### 定义 4.1：带因果标签和时间戳的消息

给定三个非空集合：逻辑消息标识符集合 $\mathsf{MID}$、元数据集合 $\mathcal U$ 与载荷集合 $\mathsf{Payload}$。另外给定严格全序关系：

$$
<_{\mathsf{MID}}
\ \subseteq
\mathsf{MID}\times\mathsf{MID}.
$$

若不同空间边使用不同载荷类型，可以把 $\mathsf{Payload}$ 定义为带边标签或类型标签的不交并。本文的证明不读取 $\mathcal U$ 的内部结构；若实现希望在元数据中保存某个额外字段，就必须把该字段作为 $\mathcal U$ 元素的明确坐标定义，而不能只靠字段名称赋予数学含义。

定义候选消息记录集合：

$$
\mathfrak R_L
=
\mathsf{MID}
\times[L]
\times\mathbb F_L
\times\Theta
\times V\times V
\times\mathcal U
\times\mathsf{Payload}.
$$

一个候选消息记录是元组：

$$
m=(\iota,t,c,\theta,u,v,\mu,p),
$$

并属于 $\mathfrak R_L$。它的八个坐标依次满足：

- $\iota$ 是逻辑消息标识符；$m$ 是消息实例，$\iota$ 是它的标识符，二者不能互换。唯一性由定义 4.2a 对实际消息集合施加的单射条件给出。
- $t\in[L]$ 是消息的归属 `token` 索引，即 $\operatorname{owner}(m)=t$。
- $c\in\mathbb F_L$ 是满足定义 2.1 的因果前沿。
- $t\leq c$。当前语义把“是否存在一条标为 `owner=t` 的消息”也视为输入相关语义，因此其因果上界不能早于位置 $t$。即使数值载荷恰好忽略 $x_t$，这条带归属记录的存在性仍至少与位置 $t$ 对齐；若未来允许与输入无关的合成 owner 记录，必须另行修改这一契约。
- $\theta=(\tau,i_{\mathrm{arrive}})\in\Theta$ 是到达时间戳。
- $u\in V$ 是源节点。
- $v\in V$ 是目标节点。
- $(u,v)\in E$。
- $\mu\in\mathcal U$ 是元数据；不需要元数据时可令 $\mathcal U$ 为单元素集合。
- $p\in\mathsf{Payload}$ 是载荷。

定义字段读取函数：

$$
\operatorname{id}:\mathfrak R_L\to\mathsf{MID},
\qquad
\operatorname{owner}:\mathfrak R_L\to[L],
$$

$$
\operatorname{frontier}:\mathfrak R_L\to\mathbb F_L,
\qquad
\operatorname{arrival}:\mathfrak R_L\to\Theta,
$$

$$
\operatorname{src}:\mathfrak R_L\to V,
\qquad
\operatorname{dst}:\mathfrak R_L\to V,
$$

$$
\operatorname{meta}:\mathfrak R_L\to\mathcal U,
\qquad
\operatorname{payload}:\mathfrak R_L\to\mathsf{Payload}.
$$

它们在 $m=(\iota,t,c,\theta,u,v,\mu,p)$ 上取值为：

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

$$
\operatorname{meta}(m)=\mu,
\qquad
\operatorname{payload}(m)=p.
$$

定义部分到达轮次函数：

$$
\operatorname{arrivalRound}:\mathfrak R_L\rightharpoonup\mathbb N,
$$

其定义域为：

$$
\operatorname{dom}(\operatorname{arrivalRound})
=
\{m\in\mathfrak R_L\mid
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})
\text{ 对某个 }\tau\in\mathbb N\}.
$$

对定义域中的 $m$，若 $\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})$，规定：

$$
\operatorname{arrivalRound}(m)=\tau.
$$

定义有效消息集合为候选记录中满足上述边、时间戳与因果标签约束的子集：

$$
\mathcal R
=
\left\{
m\in\mathfrak R_L
\ \middle|
\begin{array}{l}
\operatorname{owner}(m)\leq\operatorname{frontier}(m),\\
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})
\text{ 对某个 }\tau\in\mathbb N,\\
(\operatorname{src}(m),\operatorname{dst}(m))\in E
\end{array}
\right\}.
$$

对每个可能使用的消息标识符 $\iota\in\mathsf{MID}$，把不同输入序列上的消息实例或“不存在”写成可选函数：

$$
f_\iota^{\mathrm{msg}}:
X^L\to\mathcal R\cup\{\bot\}.
$$

若当前输入上 $m=f_\iota^{\mathrm{msg}}(x_{0:L})\neq\bot$，则要求 $\operatorname{id}(m)=\iota$，并要求 $\operatorname{frontier}(m)$ 是 $f_\iota^{\mathrm{msg}}$ 的有效因果前沿。因而消息前沿约束完整消息的存在性和全部八个坐标，不只约束载荷数值。

对节点 $v$，定义其入站消息记录集合：

$$
\mathcal R_v
=
\{m\in\mathcal R\mid\operatorname{dst}(m)=v\}.
$$

> [!important] 这是标题所说的“消息携带 `token` 归属信息”
> `owner(m)` 是消息记录的一部分，并随消息沿边传播。节点收到消息后可以按 `owner` 分桶、逐归属处理或联合处理；无论采用哪种方式，都不能在未定义新语义的情况下丢掉该字段。

每个边消息从派发时起就携带 `owner`，而不是等到发生汇聚时才临时补上。原因是一般 DAG 中未来是否会发生路径碰撞不能由当前局部消息预先排除。`owner` 只提供归属索引；要识别具体实例必须读取 `message_id`，要确定消息由哪个事件产生、被哪个事件消费，则必须读取定义 4.2a 的 $\operatorname{producer}$ 与 $\operatorname{consumer}$。

消息标识符使重复载荷仍可以保持为不同消息。其形式要求是：定义 4.2a 中实际消息集合上的 $\operatorname{id}$ 投影必须为单射。标识符如何由源事件和局部输出位置确定生成，稍后由定义 6.3 的派发函数表达；它不能依赖物理线程竞争顺序。参考语义也不读取物理线程首先写入收件箱的顺序。

对每个输入位置 $t\in[L]$，定义不属于边消息集合的边界注入记录：

$$
b_t^{\mathrm{in}}
=
(t,\theta_t^{\mathrm{in}},s,x_t).
$$

它属于边界注入记录集合：

$$
\mathcal B_{\mathrm{in}}
=
[L]\times\Theta\times V\times X.
$$

该记录在第 7 节实例化为输入逻辑事件。它的归属索引与因果前沿都是 $t$，但它不是从某条空间边到达的消息。

### 定义 4.2：单位时延派发

给定：

$$
\tau\in\mathbb N,
\qquad
t'\in[L],
\qquad
c'\in\mathbb F_L,
\qquad
t'\leq c',
$$

以及空间边 $(v,w)\in E$。称消息 $m'\in\mathcal R$ 是这些数据的一次单位时延派发，当且仅当：

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

第 6 节会给出产生此类消息的具体函数。当前定义只规定结果消息必须满足的五个字段等式，不预先使用后文的节点输出或选边对象。

### 定义 4.2a：消息产生、消费与跨边界延续

给定有限实际事件集合 $\mathcal E$ 与有限消息集合：

$$
\mathcal M\subseteq\mathcal R.
$$

要求消息标识符投影在 $\mathcal M$ 上是单射，即对任意 $m,m'\in\mathcal M$：

$$
\operatorname{id}(m)=\operatorname{id}(m')
\quad\Longrightarrow\quad
m=m'.
$$

一个消息生命周期结构是二元组：

$$
(\operatorname{producer},\operatorname{consumer}),
$$

其中产生函数为：

$$
\operatorname{producer}:\mathcal M\to\mathcal E,
$$

并要求对每个 $m\in\mathcal M$：

$$
\operatorname{loc}(\operatorname{producer}(m))
=
\operatorname{src}(m),
$$

$$
\operatorname{time}(\operatorname{producer}(m))
<_{\Theta}
\operatorname{arrival}(m).
$$

定义部分消费函数：

$$
\operatorname{consumer}:\mathcal M\rightharpoonup\mathcal E.
$$

其中 $\rightharpoonup$ 表示部分函数。定义它的定义域：

$$
\operatorname{dom}(\operatorname{consumer})
=
\{m\in\mathcal M\mid
\operatorname{consumer}(m)\text{ 有定义}\}.
$$

若 $m\in\operatorname{dom}(\operatorname{consumer})$，要求：

$$
\operatorname{loc}(\operatorname{consumer}(m))
=
\operatorname{dst}(m),
$$

$$
\operatorname{arrival}(m)
<_{\Theta}
\operatorname{time}(\operatorname{consumer}(m)).
$$

因为 $\operatorname{consumer}$ 是函数，一个消息实例不能被两个不同事件重复消费。定义 7.1 会进一步要求：产生事件值显式包含出站消息，消费事件值显式包含入站消息。

定义在途消息集合：

$$
\mathcal M_{\mathrm{flight}}
=
\mathcal M
\setminus
\operatorname{dom}(\operatorname{consumer}).
$$

若 $\mathcal M_{\mathrm{flight}}=\varnothing$，则称该消息生命周期结构是封闭的。第 8 节的封闭有限冲刷执行结束后，$\operatorname{consumer}$ 是 $\mathcal M$ 上的全函数。只有讨论中间边界和可接续 `decode` 的延续状态时，才需要保留 $\mathcal M_{\mathrm{flight}}$。

消息实例的生命周期从产生事件派发它开始，到唯一消费事件消费它为止。消费事件可以产生零条、一条或多条后继消息，但这些后继都是新的消息实例；“没有后继消息”表示相应消息分支在消费事件处终止，不是原消息未被消费。

对任意边界索引 $k\in[L]$，考虑绝对轮次 $R(k+1)$ 的全部阶段执行完毕后得到的有限事件集合、消息集合和消息生命周期结构。若：

$$
m\in\mathcal M_{\mathrm{flight}}
\quad\text{且}\quad
\operatorname{arrivalRound}(m)>R(k+1),
$$

则 $m$ 在边界 $R(k+1)$ 之后仍保持为在途消息，并在其原定逻辑到达时间戳到达。读出、采样与下一输入位置的注入不执行隐式清除。

### 定义 4.2b：消息来源图、消息分支、分叉与汇聚

把事件实例和消息实例视为不同类型的顶点，取不交并。符号 $A\sqcup B$ 表示带来源标签的不交并，即使 $A$ 与 $B$ 作为普通集合恰有相同元素，它们在不交并中仍属于不同类型：

$$
\mathcal V_{\mathrm{msg}}
=
\mathcal E\sqcup\mathcal M.
$$

定义两个自然注入函数：

$$
\iota_{\mathcal E}:\mathcal E\to\mathcal V_{\mathrm{msg}},
\qquad
\iota_{\mathcal E}(e)=(0,e),
$$

$$
\iota_{\mathcal M}:\mathcal M\to\mathcal V_{\mathrm{msg}},
\qquad
\iota_{\mathcal M}(m)=(1,m).
$$

定义消息产生/消费边集合：

$$
\mathcal A_{\mathrm{msg}}
=
\{(\iota_{\mathcal E}(\operatorname{producer}(m)),
\iota_{\mathcal M}(m))\mid m\in\mathcal M\}
\cup
\{(\iota_{\mathcal M}(m),
\iota_{\mathcal E}(\operatorname{consumer}(m)))\mid
m\in\operatorname{dom}(\operatorname{consumer})\}.
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

消息实例级的传播结构就是二元组 $(\operatorname{producer},\operatorname{consumer})$，等价地也可写成边关系 $\mathcal A_{\mathrm{msg}}$。若另定义任意集合 $J$ 和摘要函数 $\ell:\mathcal M\to J$，则 $\ell(m)$ 只是每条消息的附加值；除非另行证明 $\ell$ 唯一决定上述两个函数，否则不能用 $\ell$ 代替产生/消费关系。

由定义 4.2a，每条产生边 $\operatorname{producer}(m)\to m$ 都满足产生事件时间戳严格早于 $\operatorname{arrival}(m)$，每条消费边 $m\to\operatorname{consumer}(m)$ 都满足 $\operatorname{arrival}(m)$ 严格早于消费事件时间戳。沿 $P_{\mathrm{msg}}$ 的任意有向路径，事件时间戳与消息到达时间戳因此严格递增，所以 $P_{\mathrm{msg}}$ 无有向环。

第 7.2 节还会定义事件之间的状态依赖边和控制依赖边；这些边属于关系 $\mathcal A_L^P$，不属于 $\mathcal A_{\mathrm{msg}}$，也不能由 `owner` 或 `frontier` 两个投影恢复。

### 定义 4.3：按空间节点、逻辑到达时间和 `owner` 分桶的收件箱

固定定义 4.2a 的实际消息集合 $\mathcal M\subseteq\mathcal R$。对空间节点 $v$、绝对轮次 $\tau$ 与归属 `token` 索引 $t$，定义函数：

$$
I_{v,\tau,t}:\mathcal R_v\to\mathbb N,
$$

$$
I_{v,\tau,t}(m)
=
\begin{cases}
1,
&m\in\mathcal M,\quad
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}}),\quad
\operatorname{owner}(m)=t,\\
0,
&\text{其他情形}.
\end{cases}
\tag{GD-4}
$$
^eq-general-owner-inbox

因为 $\mathcal M$ 有限，$I_{v,\tau,t}\in\mathcal M_{\mathrm{fin}}(\mathcal R_v)$。这里即使两个消息载荷相等，只要消息实例不同，它们仍是 $\mathcal R_v$ 中的不同元素，并各自具有重数 $1$。

定义同刻到达 $v$ 的归属 `token` 索引集合：

$$
\mathcal O_{v,\tau}
=
\{t\in[L]\mid I_{v,\tau,t}\neq 0_{\mathcal R_v}\}.
$$

定义不按 `owner` 分桶的完整同刻收件箱：

$$
I_{v,\tau}
=
\biguplus_{t\in\mathcal O_{v,\tau}}
I_{v,\tau,t},
$$

其中 $\biguplus$ 使用定义 0.1 的多重集加法。称 $I_{v,\tau}$ 为空间节点 $v$ 在绝对轮次 $\tau$ 的逻辑到达批次。

$I_{v,\tau,t}$ 可以包含来自消息来源图中多条不同分支的消息。它们因为目标空间节点、完整逻辑到达时间戳和 `owner` 都相同而进入同一桶，但仍由各自的 `message_id` 保持为不同实例。

令 $m=|\mathcal O_{v,\tau}|$。定义 $O_{v,\tau}^{\uparrow}$ 为 $\mathcal O_{v,\tau}$ 的唯一严格递增枚举：

$$
O_{v,\tau}^{\uparrow}=(t_1,t_2,\ldots,t_m),
\qquad t_1<t_2<\cdots<t_m.
$$

当 $m=0$ 时，$O_{v,\tau}^{\uparrow}=()$。

### 定义 4.4：同一归属 `token`、同刻聚合

对每个节点 $v$，给定非空数值聚合集合 $X_v^{\mathrm{num}}$，并定义带因果前沿的节点输入集合：

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

对每个 $t\in\mathcal O_{v,\tau}$，定义数值聚合结果：

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
\max_{m\in\operatorname{supp}(I_{v,\tau,t})}
\operatorname{frontier}(m).
$$

本文固定使用上述最大值作为聚合输入的因果前沿。未来若改用更小值，必须把新值重新定义为相应聚合结果函数在定义 2.1 意义下的有效因果前沿；这种替换不属于当前定义。定义节点转移实际接收的带标签输入：

$$
x_{v,\tau,t}
=
(\bar x_{v,\tau,t},c_{v,\tau,t}^{X})
\in X_v.
$$

定义节点输入的两个坐标投影函数：

$$
\operatorname{payload}:X_v\to X_v^{\mathrm{num}},
\qquad
\operatorname{frontier}:X_v\to\mathbb F_L.
$$

它们在 $x_{v,\tau,t}=(\bar x_{v,\tau,t},c_{v,\tau,t}^{X})$ 上取值为：

$$
\operatorname{payload}(x_{v,\tau,t})
=
\bar x_{v,\tau,t},
\qquad
\operatorname{frontier}(x_{v,\tau,t})
=
c_{v,\tau,t}^{X}.
$$

如果聚合器与顺序无关，它直接作用于多重集。若数值语义要求先把消息排成序列，则使用 $<_{\mathsf{MID}}$ 对消息标识符排序；由于 $\operatorname{id}$ 在实际消息集合上是单射，这给出唯一顺序。不能使用物理到达竞争作为隐式顺序。

下面三点只是对第 5 节后续定义的阅读预告，不参与本节形式化。这里的“聚合”只处理同一个 $(v,\tau,t)$ 桶内的消息，不处理不同 `owner` 之间的关系：

- 配置 O 对不同 `owner` 的桶按规定次序分别执行节点转移。
- 配置 J 联合读取多个 `owner` 桶，但仍分别产生带归属标签的局部输出记录。
- 配置 F 对多个 `owner` 桶做显式语义融合，只产生统一局部输出记录。

若后续计算需要对定义域中的任意收件箱区分每个消息实例，则必须要求 $\operatorname{Aggregate}_v$ 在 $\mathcal M_{\mathrm{fin}}(\mathcal R_v)$ 上为单射，或显式给出解码函数 $D_v:X_v^{\mathrm{num}}\to\mathcal M_{\mathrm{fin}}(\mathcal R_v)$，使对每个 $I\in\mathcal M_{\mathrm{fin}}(\mathcal R_v)$ 都有：

$$
D_v(\operatorname{Aggregate}_v(I))=I.
$$

若它只返回不可逆求和等压缩值，且不存在上述单射性或解码函数，则分支级数值区别在这个节点转移输入处已经被参考语义丢弃；消息来源图仍能记录“哪些消息被消费”，但不能从聚合值中恢复各消息的数值贡献。

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

从边界注入记录产生的第一条消息使用从 $s$ 开始的相应单边路径。若入站消息的见证路径为：

$$
p=(v_0,\ldots,v_k),
\qquad v_k=v,
$$

并且节点事件沿边 $(v,w)$ 发出新消息，则定义延长路径：

$$
p\cdot w
=
(v_0,\ldots,v_k,w).
$$

它的长度为 $|p|+1$，可作为新消息的时序见证。若一个事件消费多条同刻消息，可以任选其中一条入站消息的见证进行延长，因为它们具有相同到达轮次。改变新消息的归属索引或因果前沿不改变绝对时间，也不影响这个存在性论证。

这里的 $t$ 不是新消息的 `owner`，也不是要求写入运行时的不可变字段；同一消息可能有多个可用时序见证。该辅助量只证明时间上界，不能决定消息标识符、$\operatorname{producer}$、$\operatorname{consumer}$ 或事件依赖关系。

因为默认语义配置不在空时间戳自主发射消息，所有已派发的消息都可由上述归纳得到见证。又因为 $t\leq L-1$ 且 $|p|\leq D$：

$$
\tau=Rt+|p|
\leq
R(L-1)+D.
$$

<div class="qed" aria-label="证毕">∎</div>

### 引理 4.6：有限消息与有限常规事件性

假设每次节点调用只发出有限条消息。对任意有限输入分块，一次执行产生的消息集合与常规节点事件集合都有限。

**证明。**

有限 DAG 中的有向路径数量有限。每个消息实例只对应一条空间边；消息来源图中的任意消息分支沿空间边方向前进，不能返回已经经过的空间节点。初始注入数有限，每个事件的扇出有限，所以对有限路径集合做有限深度的分支展开后，总消息数有限。

每个常规节点事件都消费至少一条实际消息。若一个到达批次被拆成多个事件，则这些事件消费的消息集合仍两两不交，因为定义 4.2a 的 $\operatorname{consumer}$ 是函数，同一消息不能被两个事件重复消费。因此常规节点事件数不超过消息消费记录数，故也有限。

<div class="qed" aria-label="证毕">∎</div>

有限不等于高效。一般 DAG 的路径数量可以随 $|V|$ 指数增长，因此后文仍需单独加入稀疏事件预算。

## 5. 节点持有状态与三种同刻/融合语义

### 定义 5.1：节点持有的持久上下文

对每个节点 $v\in V$，给定非空状态集合：

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

对任意 $\widetilde S=(S,c^S)\in\widetilde{\mathcal S}_v$，定义投影函数：

$$
\operatorname{num}:\widetilde{\mathcal S}_v\to\mathcal S_v,
\qquad
\operatorname{frontier}:\widetilde{\mathcal S}_v\to\mathbb F_L.
$$

它们的取值为：

$$
\operatorname{num}(\widetilde S)=S,
\qquad
\operatorname{frontier}(\widetilde S)=c^S.
$$

#### 定义 5.1a：状态提交记录与状态版本

给定非空提交标识符集合 $\mathsf{CID}$。定义提交次序键集合：

$$
\mathsf{CKey}
=
\Theta\times\mathbb N.
$$

对 $(\theta,j),(\theta',j')\in\mathsf{CKey}$，定义严格字典序关系 $<_{\mathsf{CKey}}\subseteq\mathsf{CKey}\times\mathsf{CKey}$：

$$
(\theta,j)<_{\mathsf{CKey}}(\theta',j')
$$

当且仅当 $\theta<_{\Theta}\theta'$，或者 $\theta=\theta'$ 且 $j<j'$。

定义相应的非严格次序关系：

$$
\leq_{\mathsf{CKey}}
\subseteq
\mathsf{CKey}\times\mathsf{CKey},
$$

并规定：

$$
\chi\leq_{\mathsf{CKey}}\chi'
\quad\Longleftrightarrow\quad
\bigl(\chi<_{\mathsf{CKey}}\chi'\bigr)
\text{ 或 }
\chi=\chi'.
$$

对节点 $v$，定义状态提交记录集合：

$$
\mathcal Q_v
=
\mathsf{CID}
\times\mathsf{CKey}
\times\widetilde{\mathcal S}_v.
$$

一个状态提交记录是三元组：

$$
q=(\gamma_q,\chi_q,\widetilde S_q)\in\mathcal Q_v.
$$

定义三个投影函数：

$$
\operatorname{cid}:\mathcal Q_v\to\mathsf{CID},
\qquad
\operatorname{ckey}:\mathcal Q_v\to\mathsf{CKey},
$$

$$
\operatorname{version}:\mathcal Q_v\to\widetilde{\mathcal S}_v.
$$

它们在 $q=(\gamma_q,\chi_q,\widetilde S_q)$ 上取值为：

$$
\operatorname{cid}(q)=\gamma_q,
\qquad
\operatorname{ckey}(q)=\chi_q,
\qquad
\operatorname{version}(q)=\widetilde S_q.
$$

定义提交时间戳投影函数：

$$
\operatorname{ctime}:\mathcal Q_v\to\Theta.
$$

若 $\chi_q=(\theta_q,j_q)$，规定：

$$
\operatorname{ctime}(q)=\theta_q\in\Theta.
$$

称 $\operatorname{version}(q)\in\widetilde{\mathcal S}_v$ 为提交记录 $q$ 所携带的状态版本。状态版本不是新的状态类型；它就是增广状态集合中的一个元素，但通过提交记录与产生它的逻辑位置关联。

对每个可能使用的提交标识符 $\gamma\in\mathsf{CID}$，把不同输入序列上的提交记录或“不存在”写成可选函数：

$$
f_{v,\gamma}^{\mathrm{commit}}:
X^L\to\mathcal Q_v\cup\{\bot\}.
$$

若当前输入上 $q=f_{v,\gamma}^{\mathrm{commit}}(x_{0:L})\neq\bot$，则要求 $\operatorname{cid}(q)=\gamma$，并要求 $\operatorname{frontier}(\operatorname{version}(q))$ 是 $f_{v,\gamma}^{\mathrm{commit}}$ 的有效因果前沿。该条件同时约束提交是否存在、提交键和状态版本，而不只约束数值状态。

节点 $v$ 的一个状态提交轨迹是有限序列：

$$
\mathbf Q=(q_0,\ldots,q_{n-1})\in\mathcal Q_v^\star,
$$

满足提交标识符两两不同，并且：

$$
\operatorname{ckey}(q_i)
<_{\mathsf{CKey}}
\operatorname{ckey}(q_{i+1}),
\qquad i\in\mathbb N,\ i+1<n.
$$

本页由此严格区分：节点持久状态是 $\widetilde{\mathcal S}_v$ 的当前元素；状态版本是某个提交记录的第三个坐标；提交轨迹是 $\mathcal Q_v^\star$ 中满足上述次序条件的序列；收件箱和临时聚合值是当前转移输入；在途消息属于定义 4.2a 的集合 $\mathcal M_{\mathrm{flight}}$。后文若讨论可接续 `decode` 的整体边界状态，必须明确写出节点状态乘积与在途消息集合，而不使用未限定的“模型状态”。

从本定义之后，所有参考转移的状态参数和值域都使用增广状态空间 $\widetilde{\mathcal S}_v$；数值计算核只需读取 $\operatorname{num}(\widetilde S)$，但运行时必须同时传播并提交因果前沿投影。配置 O/J 可以只把该标签用于审计，配置 F 则会用它决定新消息的 `owner` 归属索引。

下面给出本文使用的安全前沿合成约定。取 $n\in\mathbb N_{>0}$、集合 $\mathcal Q_1,\ldots,\mathcal Q_n,\mathcal Q$、函数：

$$
f_i:X^L\to\mathcal Q_i,
\qquad i=1,\ldots,n,
$$

以及确定函数：

$$
g:\mathcal Q_1\times\cdots\times\mathcal Q_n\to\mathcal Q.
$$

若每个 $f_i$ 都是 $c_i$-前缀因果的，其中：

$$
c_1,\ldots,c_n,
$$

都属于 $\mathbb F_L$，则复合函数 $x_{0:L}\mapsto g(f_1(x_{0:L}),\ldots,f_n(x_{0:L}))$ 使用以下安全因果前沿：

$$
c_{\mathrm{out}}
=
\max_{1\leq i\leq n}c_i.
$$

该最大值有效，因为两个输入序列在前缀 $0{:}c_{\mathrm{out}}$ 上相同时，所有 $f_i$ 的函数值都相同，确定函数 $g$ 的结果也相同。输出也可以选择某个更小的 $c\in\mathbb F_L$，但此时必须同时满足：$c$ 是该完整可选输出函数在定义 2.1 意义下的有效因果前沿，并且 $c$ 不小于输出记录的 `owner`。按归属排序或原子联合语义会保留局部输出记录的原 `owner`，即使 $c_{\mathrm{out}}>\operatorname{owner}$；这个不等式明确表示“记录仍标为较早输入位置，但数值已经依赖更晚输入前缀”的归属与因果依赖错位。

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

定义按归属索引划分的节点事件键集合：

$$
\mathsf{NodeKey}_L
=
\mathbb N\times[L].
$$

定义二元关系：

$$
\prec_v
\ \subseteq
\mathsf{NodeKey}_L\times\mathsf{NodeKey}_L.
$$

对两个键：

$$
k=(\tau,t),
\qquad
k'=(\tau',t')
\in\mathsf{NodeKey}_L,
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
> O 与 J 只有在节点转移满足式 GD-10、选择器同时满足后文式 GD-10S 时，才成为同一语义的不同实现；F 主动改变输出记录的区分方式和归属标签，是语义商，不只是执行优化。

### 5.3 配置 O：同一时间戳内按归属 `token` 顺序执行

#### 定义 5.3：单一归属 `token` 的事件转移

给定非空数值隐藏表示集合 $H_v$。定义路由可见的带标签隐藏表示集合：

$$
\mathcal Z_v
=
\{\bot\}
\cup
(H_v\times\mathbb F_L),
$$

若 $z=(h,c)\in H_v\times\mathbb F_L$，定义：

$$
\operatorname{payload}:
\mathcal Z_v\rightharpoonup H_v,
\qquad
\operatorname{frontier}:
\mathcal Z_v\rightharpoonup\mathbb F_L,
$$

其中两个部分函数的定义域都是 $H_v\times\mathbb F_L$。在该定义域上：

$$
\operatorname{payload}(z)=h,
\qquad
\operatorname{frontier}(z)=c.
$$

定义节点 $v$ 的局部输出记录集合：

$$
\mathcal L_v
=
[L]\times\mathcal Z_v.
$$

定义归属投影函数：

$$
\operatorname{owner}:\mathcal L_v\to[L],
\qquad
\operatorname{owner}((t,z))=t.
$$

再定义局部输出前沿部分函数：

$$
\operatorname{frontier}:\mathcal L_v\rightharpoonup\mathbb F_L,
$$

其定义域为 $[L]\times(H_v\times\mathbb F_L)$，并规定：

$$
\operatorname{frontier}((t,z))=\operatorname{frontier}(z).
$$

一个带归属标签的局部输出记录是有序对 $\ell=(t,z)\in\mathcal L_v$。当 $z\neq\bot$ 时，要求：

$$
\operatorname{owner}(\ell)
\leq
\operatorname{frontier}(\ell).
$$

$\bot$ 表示该事件已执行，但不产生路由可见的隐藏表示。

对每个可能的源事件标识符 $\eta\in\mathsf{EID}$ 与局部槽位 $j\in\mathbb N$，把不同输入序列上的局部输出值或“不存在”写成可选函数：

$$
z_{v,\eta,j}:
X^L\to\mathcal Z_v\cup\{\mathtt{absent}\},
$$

其中 $\mathtt{absent}$ 是另一个不属于 $\mathcal Z_v$ 的符号，用来区分“事件或槽位不存在”和“槽位存在但输出值为 $\bot$”。若当前输入上 $z_{v,\eta,j}(x_{0:L})=(h,c)\in H_v\times\mathbb F_L$，则要求 $c$ 是该可选函数的有效因果前沿。

节点 $v$ 的单事件转移是确定函数：

$$
\mathcal T_v:
[L]\times\mathbb N\times X_v\times\widetilde{\mathcal S}_v
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

定义 $\mathcal B_v$ 为满足下列条件的有限序列集合：

$$
\mathcal B_v
=
\left\{
((t_1,x_1),\ldots,(t_m,x_m))
\ \middle|
\begin{array}{l}
m\in\mathbb N_{>0},\\
t_i\in[L],\ x_i\in X_v
\quad(i=1,\ldots,m),\\
t_1<\cdots<t_m
\end{array}
\right\}.
$$

其任意元素具有形式：

$$
B
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad
t_1<\cdots<t_m.
$$

其中 $m\in\mathbb N_{>0}$，并且对 $i=1,\ldots,m$ 有 $t_i\in[L]$、$x_i\in X_v$。

定义输入元组键集合函数：

$$
\operatorname{keys}:\mathcal B_v\to 2^{[L]},
$$

$$
\operatorname{keys}
(((t_1,x_1),\ldots,(t_m,x_m)))
=
\{t_1,\ldots,t_m\}.
$$

定义 $\mathcal L_v^{\uparrow}$ 为所有按严格递增归属索引组织的非空有限局部输出记录序列：

$$
\mathcal L_v^{\uparrow}
=
\left\{
((t_1,z_1),\ldots,(t_m,z_m))
\ \middle|
\begin{array}{l}
m\in\mathbb N_{>0},\\
(t_i,z_i)\in\mathcal L_v
\quad(i=1,\ldots,m),\\
t_1<\cdots<t_m
\end{array}
\right\}.
$$

其任意元素具有形式：

$$
Z
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr).
$$

其中对 $i=1,\ldots,m$ 有 $z_i\in\mathcal Z_v$。

定义局部输出序列键集合函数：

$$
\operatorname{keys}:\mathcal L_v^{\uparrow}\to 2^{[L]},
$$

$$
\operatorname{keys}
(((t_1,z_1),\ldots,(t_m,z_m)))
=
\{t_1,\ldots,t_m\}.
$$

调用 $\mathcal J_v$ 时，输出元组必须与输入元组使用完全相同的归属 `token` 键集合和递增次序，即若输入 $B\in\mathcal B_v$ 对应输出 $Z\in\mathcal L_v^{\uparrow}$，则：

$$
\operatorname{keys}(Z)=\operatorname{keys}(B).
$$

两边都按严格递增索引排列，所以键集合相等已经唯一确定坐标次序。若某个归属 `token` 不产生隐藏表示，则相应位置写为 $\bot$。

对节点 $v$，给定非空增量集合 $\Delta_v$ 与提交函数：

$$
\operatorname{Commit}_v:
\widetilde{\mathcal S}_v\times\Delta_v
\to\widetilde{\mathcal S}_v,
$$

并要求 $\operatorname{Commit}_v$ 是确定函数，且其返回状态的因果前沿投影满足定义 5.1 的有效因果前沿规则。本文不读取 $\Delta_v$ 的内部坐标；它们的语义完全由 $\operatorname{Commit}_v$ 的定义决定。

以及原子联合转移：

$$
\mathcal J_v:
\mathbb N\times\mathcal B_v\times\widetilde{\mathcal S}_v
\to
\mathcal L_v^{\uparrow}\times\Delta_v.
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

仍为按归属 `token` 索引组织的输出；每个非 $\bot$ 的 $z_i$ 必须满足定义 5.3 的局部输出前沿条件及相应可选输出函数的前缀因果条件。状态只在联合计算结束后提交一次：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau}).
\tag{GD-9}
$$
^eq-atomic-joint-commit

定义联合转移与提交的组合：

$$
\operatorname{Atomic}_v:
\mathbb N\times\mathcal B_v\times\widetilde{\mathcal S}_v
\to
\mathcal L_v^{\uparrow}\times\widetilde{\mathcal S}_v,
$$

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

$\Delta_{v,\tau}\in\Delta_v$ 是本次联合调用交给 $\operatorname{Commit}_v$ 的单个增量元素，不具有本文定义的 `owner` 投影。

原子联合允许：

- 所有归属 `token` 读取同一个前状态。
- 联合计算核比较多个归属 `token` 的输入。
- 每个归属 `token` 的输出可以依赖同刻其他归属 `token`。
- 联合计算核使用归属 `token` 索引构造三角掩码。

它不允许把多个归属 `token` 变成一个永久无归属的在途消息。出站记录仍必须按归属 `token` 分开。

#### 定义 5.6：同刻按归属 `token` 保持因果的联合算子

对每个 $t\in[L]$，定义输入前缀部分函数：

$$
\operatorname{prefix}_t:
\mathcal B_v\rightharpoonup\mathcal B_v,
$$

其定义域为：

$$
\operatorname{dom}(\operatorname{prefix}_t)
=
\{B\in\mathcal B_v\mid t\in\operatorname{keys}(B)\}.
$$

若：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
$$

并且 $t=t_j$，则定义：

$$
\operatorname{prefix}_t(B_{v,\tau})
=
\bigl((t_1,x_1),\ldots,(t_j,x_j)\bigr).
$$

对每个 $t\in[L]$，定义部分函数：

$$
\operatorname{out}_t:
\mathcal L_v^{\uparrow}\rightharpoonup\mathcal Z_v.
$$

其定义域为：

$$
\operatorname{dom}(\operatorname{out}_t)
=
\{Z\in\mathcal L_v^{\uparrow}\mid t\in\operatorname{keys}(Z)\}.
$$

若 $Z=((t_1,z_1),\ldots,(t_m,z_m))\in\mathcal L_v^{\uparrow}$ 且 $t=t_j$，则定义：

$$
\operatorname{out}_t(Z)=z_j.
$$

称联合算子在同一时间戳内满足按归属 `token` 的因果性，当且仅当：对任意 $\tau\in\mathbb N$、$\widetilde S\in\widetilde{\mathcal S}_v$、$B,B'\in\mathcal B_v$ 与 $t\in\operatorname{keys}(B)\cap\operatorname{keys}(B')$，只要：

$$
\operatorname{prefix}_t(B)
=
\operatorname{prefix}_t(B'),
$$

把 $\operatorname{Atomic}_v(\tau,B,\widetilde S)$ 与 $\operatorname{Atomic}_v(\tau,B',\widetilde S)$ 的第一个坐标分别记为 $Z,Z'$，就有：

$$
\operatorname{out}_t(Z)
=
\operatorname{out}_t(Z').
$$

这一定义只约束联合转移产生的局部输出。第 6.2 节还会分别约束选择器，不能在这里用尚未定义的“路由决策”替代一个函数条件。

这是比任意联合更强的约束。任意联合只保证绝对时间语义；它不自动保证按 `token` 归属划分的前缀因果性。

### 定义 5.7：联合算子与有序折叠等价

定义函数：

$$
\operatorname{GroupFold}_{\mathcal T_v}:
\mathbb N\times\mathcal B_v\times\widetilde{\mathcal S}_v
\to
\mathcal L_v^{\uparrow}\times\widetilde{\mathcal S}_v,
$$

其函数值是定义 5.4 的递归结果：

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
- 每个归属 `token` 的局部输出记录，包括 $\bot$ 是否出现及非空记录的因果前沿。
- 时间戳结束后的状态。

只比较整体增量或最终状态不足以建立等价。

### 命题 5.8：折叠等价的联合执行保持节点转移产物

若式 [[#^eq-joint-ordered-equivalence|GD-10]] 对节点 $v$ 成立，则在该节点上用 $\mathcal J_v$ 一次执行整个时间戳分组，与按归属 `token` 顺序执行 $\mathcal T_v$ 得到相同的局部输出记录和后状态。本命题不比较第 6 节才定义的选择器与消息派发。

**证明。**

这是式 [[#^eq-joint-ordered-equivalence|GD-10]] 的直接展开：定义已经要求按归属 `token` 划分的局部输出记录与最终状态全部相等。

<div class="qed" aria-label="证毕">∎</div>

### 例 5.9：最终状态相同但语义不同

本例只写数值载荷，并假设两种实现使用相同的合法因果前沿标签；因此省略式中的增广状态与带标签隐藏表示外壳。

令：

$$
S\in\mathbb R,
$$

定义单事件转移：

$$
\mathcal T:\mathbb R\times\mathbb R
\to\mathbb R\times\mathbb R,
$$

其函数值为：

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

给定节点 $v$、时间 $\tau$、满足 $I_{v,\tau}\neq 0_{\mathcal R_v}$ 的完整收件箱，以及增广前状态 $\widetilde S$，记：

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
\{\operatorname{frontier}(m)
\mid m\in\operatorname{supp}(I_{v,\tau})\}
\right).
\tag{GD-F1}
$$
^eq-frontier-fusion-max

因为 $I_{v,\tau}\neq 0_{\mathcal R_v}$，且每条消息都满足 $0\leq\operatorname{owner}(m)\leq\operatorname{frontier}(m)$，所以 $c_{v,\tau}^{\star}\in[L]$；它不会在融合事件中取值 $-1$。

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

若 $h^\star\neq\bot$，定义：

$$
z^\star
=
(h^\star,c_{v,\tau}^{\star})
\in
\mathcal Z_v.
$$

若 $h^\star=\bot$，定义 $z^\star=\bot$。两种情况下，该时间戳都产生一个统一局部输出记录，其归属 `token` 索引取为 $c_{v,\tau}^{\star}$：

$$
Z_{v,\tau}^{\mathrm{front}}
=
\bigl((c_{v,\tau}^{\star},z^\star)\bigr),
\tag{GD-F3}
$$
^eq-frontier-owned-output

当 $h^\star\neq\bot$ 时，该记录满足：

$$
\operatorname{owner}((c_{v,\tau}^{\star},z^\star))
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

定义出边集合函数：

$$
\operatorname{Out}:V\to 2^E,
$$

$$
\operatorname{Out}(v)
=
\{(v,u)\in E\}.
$$

因果前沿融合路由原语是确定函数：

$$
\operatorname{Route}_v^{\mathrm{front}}:
\mathbb N\times\mathcal L_v
\to
2^{\operatorname{Out}(v)}.
$$

它只能读取绝对时间、统一输出记录与已固定在函数本身中的静态参数；对形如 $(t,\bot)$ 的记录返回空集。沿任一已选边生成的消息必须保留该输出的归属索引和因果前沿。第 6.3 节会用一个具有完整定义域和值域的确定函数 $\operatorname{Dispatch}$ 构造消息标识符、元数据与载荷。

#### 引理 5.12：前缀因果组合

给定 $n\in\mathbb N_{>0}$、集合 $\mathcal Q_1,\ldots,\mathcal Q_n$，以及函数：

$$
f_i:X^L\to\mathcal Q_i,
\qquad i=1,\ldots,n.
$$

假设 $f_i$ 是 $c_i$-前缀因果的，其中：

$$
c_i\in\mathbb F_L.
$$

给定集合 $\mathcal Q$ 与确定函数：

$$
g:
\mathcal Q_1\times\cdots\times\mathcal Q_n
\to\mathcal Q.
$$

定义复合函数：

$$
F:X^L\to\mathcal Q,
$$

$$
F(x_{0:L})
=
g(f_1(x_{0:L}),\ldots,f_n(x_{0:L})),
$$

并定义：

$$
c^\star
=
\max_{1\leq i\leq n}c_i,
$$

则 $F$ 是 $c^\star$-前缀因果的。

**证明。**

取任意两个在前缀 $0{:}c^\star$ 上相同的输入序列。因为每个 $c_i\leq c^\star$，由 $f_i$ 的前缀因果性，对每个 $i$ 都有两次函数值 $f_i(x_{0:L})$ 相同。函数 $g$ 是确定函数，所以两次得到的 $F(x_{0:L})$ 相同。

<div class="qed" aria-label="证毕">∎</div>

#### 定理 5.13：因果前沿融合的 `token` 前缀不变量

假设：

1. 初始状态因果前沿为 $-1$。
2. 对每个 $t\in[L]$，输入事件 $e_t^{\mathrm{in}}$ 产生的每个首跳提交记录、局部输出记录和消息，其可选记录函数都是 $t$-前缀因果的，并且首跳消息满足 `owner=t, frontier=t`。
3. 后续计算只使用定义 4.4、5.11、5.11b 与 6.3 已给出定义域和值域的确定函数；这些函数的模型参数固定在函数本身中，不存在额外输入通道。
4. 每次融合按式 [[#^eq-frontier-fusion-max|GD-F1]] 更新状态因果前沿，并按式 [[#^eq-frontier-owned-output|GD-F3]] 标记统一输出。

则以下两条不变量成立：

1. 任意节点 $v$ 的配置 F 提交记录 $q\in\mathcal Q_v$，令 $\gamma=\operatorname{cid}(q)$ 与 $c=\operatorname{frontier}(\operatorname{version}(q))$，则定义 5.1a 的可选提交函数 $f_{v,\gamma}^{\mathrm{commit}}$ 是 $c$-前缀因果的。
2. 任意配置 F 的消息 $m$，令 $\iota=\operatorname{id}(m)$。若：

$$
\operatorname{owner}(m)
=
\operatorname{frontier}(m)
=c,
$$

则定义 4.1 的可选消息函数 $f_\iota^{\mathrm{msg}}$ 是 $c$-前缀因果的。

也就是说，上述数值内容只依赖：

$$
x_0,\ldots,x_c.
$$

特别地，不会出现一个 `owner=A` 的晚到消息在融合中读取 B 后，其统一后继消息仍标记为 `owner=A`；统一记录的归属至少被提升到当前因果前沿。

**证明。**

沿绝对时间流式执行归纳。初始状态是固定元素 $\widetilde S_v^0$，所以对应常函数是 $(-1)$-前缀因果的。假设 2 直接给出全部首跳可选记录函数的有效前沿 $t$。

假设某次融合的前状态与全部收件箱消息的可选记录函数都具有各自声明的有效因果前沿。式 [[#^eq-frontier-fusion-max|GD-F1]] 取这些因果前沿的最大值 $c^\star$。把确定函数 $\mathcal F_v$ 与 $\operatorname{Commit}_v$ 代入引理 5.12，可知融合输出、增量与提交记录的完整可选函数都是 $c^\star$-前缀因果的。式 [[#^eq-frontier-owned-output|GD-F3]] 又把输出的 `owner` 与 `frontier` 都设为 $c^\star$，所以第一条不变量被保持。

定义 5.11b 的路由原语只接收绝对时间与局部输出记录，定义 6.3 的派发函数只接收派发请求；二者都是确定函数。因此路由记录与消息完整记录的可选函数保持同一个因果前沿上界，且派发消息满足 `owner=frontier=c^\star`。对所有绝对时间及其中的节点事件重复上述论证，第二条不变量也成立。

<div class="qed" aria-label="证毕">∎</div>

#### 讨论 5.14：提升因果前沿不自动带来高性能 `prefill`

本小节是性能解释，不作为后续正确性定理的数学前提。

式 [[#^eq-frontier-fusion-max|GD-F1]] 中的 $\max$ 是满足结合律的归约，可以低成本批量计算。为准确描述剩余顺序链，给定 $q\in\mathbb N_{>0}$、非空分组集合 $\mathcal G$、非空数值状态集合 $\mathcal S$、分组序列 $(G_0,\ldots,G_{q-1})\in\mathcal G^q$，以及函数族：

$$
(\Phi_G:\mathcal S\to\mathcal S)_{G\in\mathcal G}.
$$

若状态序列 $(S_0,\ldots,S_q)\in\mathcal S^{q+1}$ 满足：

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

例如，给定维数 $d\in\mathbb N_{>0}$、矩阵 $A_j\in\mathbb R^{d\times d}$、向量 $b_j\in\mathbb R^d$ 与状态 $S_j\in\mathbb R^d$，仿射递推：

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

由三项的值域，$s_{v,\tau,t\to u}\in\mathbb R$。

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

定义 $\mathcal A_v^{\uparrow}$ 为以下按严格递增归属索引组织的非空有限选边记录序列集合：

$$
\mathcal A_v^{\uparrow}
=
\left\{
((t_1,A_1),\ldots,(t_m,A_m))
\ \middle|
\begin{array}{l}
m\in\mathbb N_{>0},\\
t_i\in[L],\ A_i\in 2^{\operatorname{Out}(v)}
\quad(i=1,\ldots,m),\\
t_1<\cdots<t_m
\end{array}
\right\}.
$$

其任意元素具有形式：

$$
\bigl((t_1,A_1),\ldots,(t_m,A_m)\bigr),
\qquad
m\in\mathbb N_{>0},
\qquad
t_i\in[L]\quad(i=1,\ldots,m),
\qquad
t_1<\cdots<t_m,
\qquad
A_i\subseteq\operatorname{Out}(v)
\quad(i=1,\ldots,m).
$$

定义选边记录序列的键集合函数：

$$
\operatorname{keys}:\mathcal A_v^{\uparrow}\to 2^{[L]},
$$

$$
\operatorname{keys}
(((t_1,A_1),\ldots,(t_m,A_m)))
=
\{t_1,\ldots,t_m\}.
$$

配置 J 给定确定函数：

$$
\rho_v^{\mathrm{joint}}:
\mathbb N\times\mathcal L_v^{\uparrow}
\to
\mathcal A_v^{\uparrow}.
$$

若：

$$
Z_{v,\tau}^{\mathrm{joint}}
=
((t_1,z_1),\ldots,(t_m,z_m)),
$$

则要求存在 $A_i\subseteq\operatorname{Out}(v)$（$i=1,\ldots,m$），使联合选择器返回具有完全相同归属 `token` 键序列的元组：

$$
\rho_v^{\mathrm{joint}}
\left(
\tau,Z_{v,\tau}^{\mathrm{joint}}
\right)
=
((t_1,A_1),\ldots,(t_m,A_m)).
$$

因此联合选择器可以比较同刻多个带归属标签的隐藏表示，但联合转移的前状态和后状态可见性已经在 $Z_{v,\tau}^{\mathrm{joint}}$ 的定义中固定，不由选择器临时决定。

等价地，上述键匹配条件可写为：

$$
\operatorname{keys}
\left(
\rho_v^{\mathrm{joint}}(\tau,Z)
\right)
=
\operatorname{keys}(Z),
\qquad
Z\in\mathcal L_v^{\uparrow}.
$$

称联合选择器与逐记录选择器兼容，当且仅当对任意 $\tau\in\mathbb N$ 和任意：

$$
Z=((t_1,z_1),\ldots,(t_m,z_m))
\in\mathcal L_v^{\uparrow},
$$

都有：

$$
\rho_v^{\mathrm{joint}}(\tau,Z)
=
\bigl(
(t_1,\rho_v^{\mathrm{ord}}(\tau,t_1,z_1)),
\ldots,
(t_m,\rho_v^{\mathrm{ord}}(\tau,t_m,z_m))
\bigr).
\tag{GD-10S}
$$
^eq-selector-fold-compatibility

式 GD-10S 禁止联合选择器利用其他归属记录改变某个 $t_i$ 的选边结果。若实验希望研究跨归属联合路由，则不应假设该式成立，也不能仅凭节点转移的式 GD-10 宣称配置 J 与配置 O 等价。

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

选择器还必须满足逐局部输出槽位的前缀因果约束。固定节点 $v$、一个可能的源事件标识符 $\eta\in\mathsf{EID}$ 与局部槽位 $j\in\mathbb N$。把不同输入序列上的选边结果写成可选函数：

$$
a_{v,\eta,j}:
X^L\to
2^{\operatorname{Out}(v)}\cup\{\bot\},
$$

其中 $\bot$ 表示该事件或该局部槽位不存在。若当前输入上该槽位的局部输出为 $z=(h,c)\neq\bot$，则要求 $c$ 是函数 $a_{v,\eta,j}$ 的有效因果前沿。换言之，只要两个输入序列在 $0{:}c$ 上相同，该槽位是否存在以及选择的空间边集合都必须相同。

这个条件对配置 O 通常由“选择器只读取 $z$ 与静态参数”直接得到。对配置 J，它不是自动成立的：若 $t_i$ 的选边结果读取了另一个具有更大因果前沿的局部输出，就必须把 $z_i$ 的因果前沿提高到足以覆盖该依赖，或者禁止这次跨记录读取。否则定义 6.3 产生的消息会把一个依赖更晚输入的存在性错误标成较小前沿。

无论使用哪种语义配置，选择器都必须：

- 确定性处理并列消解。
- 只选择 $v$ 的出站边。
- 对每个出站消息保留节点输出已声明的 `owner` 与 `frontier`；归属提升只能发生在定义 5.11 的融合转移内。
- 不根据路由结果追溯修改已经提交的同刻节点状态，除非这种修改已写入节点转移契约。

若选择器具有可变状态，该状态必须由唯一节点持有，并纳入 $\widetilde{\mathcal S}_v$ 以及第 7 节定义的节点参考/分块契约。这足以定义正确性，但不自动提供高性能。严格高性能语义进一步要求：`affectcount/selectcount` 一类跨事件反馈要么删除，要么给出独立的扫描或批量收缩证明。

#### 定义 6.2a：路由记录

对节点 $v$，定义候选路由记录集合：

$$
\mathfrak{RR}_v
=
\mathsf{EID}
\times\Theta
\times\mathbb N
\times[L]
\times\mathcal Z_v
\times 2^{\operatorname{Out}(v)}.
$$

一个候选路由记录是六元组：

$$
r=(\eta_r,\theta_r,j_r,t_r,z_r,A_r)
\in\mathfrak{RR}_v.
$$

六个坐标分别是源事件标识符、源事件时间戳、该事件局部输出序列中的槽位索引、归属 `token` 索引、局部输出值和已选空间边集合。定义投影函数：

$$
\operatorname{sourceEvent}:\mathfrak{RR}_v\to\mathsf{EID},
\qquad
\operatorname{sourceTime}:\mathfrak{RR}_v\to\Theta,
$$

$$
\operatorname{slot}:\mathfrak{RR}_v\to\mathbb N,
\qquad
\operatorname{owner}:\mathfrak{RR}_v\to[L],
$$

$$
\operatorname{output}:\mathfrak{RR}_v\to\mathcal Z_v,
\qquad
\operatorname{edges}:\mathfrak{RR}_v\to 2^{\operatorname{Out}(v)}.
$$

它们在 $r=(\eta_r,\theta_r,j_r,t_r,z_r,A_r)$ 上取值为：

$$
\operatorname{sourceEvent}(r)=\eta_r,
\qquad
\operatorname{sourceTime}(r)=\theta_r,
\qquad
\operatorname{slot}(r)=j_r,
$$

$$
\operatorname{owner}(r)=t_r,
\qquad
\operatorname{output}(r)=z_r,
\qquad
\operatorname{edges}(r)=A_r.
$$

定义有效路由记录集合：

$$
\mathcal{RR}_v
=
\{r\in\mathfrak{RR}_v
\mid
\begin{array}{l}
\operatorname{output}(r)=\bot
\Longrightarrow
\operatorname{edges}(r)=\varnothing,\\
\operatorname{output}(r)\neq\bot
\Longrightarrow
\operatorname{owner}(r)
\leq
\operatorname{frontier}(\operatorname{output}(r))
\end{array}
\}.
$$

若事件 $e$ 在节点 $v$ 产生局部输出序列：

$$
((t_0,z_0),\ldots,(t_{m-1},z_{m-1}))\in\mathcal L_v^\star,
$$

则对应路由记录序列必须是某个：

$$
(r_0,\ldots,r_{m-1})\in\mathcal{RR}_v^m.
$$

对每个 $j\in[m]$，第 $j$ 项的前三个相关坐标满足：

$$
\operatorname{sourceEvent}(r_j)=\operatorname{id}(e),
\qquad
\operatorname{sourceTime}(r_j)=\operatorname{time}(e),
\qquad
\operatorname{slot}(r_j)=j,
$$

并且：

$$
(\operatorname{owner}(r_j),\operatorname{output}(r_j))
=
(t_j,z_j).
$$

最后一个坐标 $\operatorname{edges}(r_j)$ 必须等于所选语义配置的选择器对该局部输出给出的边集合。由此，“路由记录”不再是未说明结构的工程名词，而是 $\mathcal{RR}_v$ 中的明确六元组。

### 定义 6.3：已选载荷派发

对每条空间边 $(v,u)\in E$，给定非空载荷子集：

$$
\mathsf{Payload}_{v\to u}
\subseteq
\mathsf{Payload},
$$

以及确定函数：

$$
P_{v\to u}:
H_v\to\mathsf{Payload}_{v\to u}.
$$

对节点 $v$，定义派发请求集合：

$$
\mathcal D_v
=
\left\{
(r,(v,u))
\ \middle|
\begin{array}{l}
r\in\mathcal{RR}_v,\\
\operatorname{output}(r)=(h,c)
\text{ 对某个 }(h,c)\in H_v\times\mathbb F_L,\\
(v,u)\in\operatorname{edges}(r)
\end{array}
\right\}.
$$

定义带节点标签的不交并：

$$
\mathcal D
=
\bigsqcup_{v\in V}\mathcal D_v.
$$

派发函数是确定函数：

$$
\operatorname{Dispatch}:
\mathcal D\to\mathcal R.
$$

若 $\delta=(v,d)\in\mathcal D$，其中 $d=(r,(v,u))\in\mathcal D_v$、$\operatorname{sourceTime}(r)=\theta$ 且 $\operatorname{output}(r)=(h,c)$，记：

$$
m'=\operatorname{Dispatch}(\delta).
$$

要求：

$$
\operatorname{owner}(m')=\operatorname{owner}(r),
\qquad
\operatorname{frontier}(m')=c,
$$

$$
\operatorname{arrival}(m')
=
(\operatorname{round}(\theta)+1,i_{\mathrm{arrive}}),
$$

$$
\operatorname{src}(m')=v,
\qquad
\operatorname{dst}(m')=u,
\qquad
\operatorname{payload}(m')=P_{v\to u}(h).
$$

最后要求复合函数：

$$
\operatorname{id}\circ\operatorname{Dispatch}:
\mathcal D\to\mathsf{MID}
$$

是单射。这样，每个“路由记录槽位、已选空间边”组合产生恰好一个具有唯一标识符的消息实例；消息元数据是 $\operatorname{Dispatch}$ 返回值的第七个坐标，其数学含义只来自 $\mathcal U$ 的显式定义，不来自额外的未类型化名称。

此外，$\operatorname{Dispatch}$ 在所有输入序列上的取值必须满足定义 4.1 的可选消息函数条件。确定性本身不够：若消息标识符或元数据读取了超出 $\operatorname{frontier}(m')$ 的输入信息，就必须提高消息前沿或修改构造函数。

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

对三个可能的配置分别选择符号 $\mathtt{node}_{\mathrm{ord}}$、$\mathtt{node}_{\mathrm{joint}}$ 与 $\mathtt{node}_{\mathrm{front}}$，要求三者两两不同，且都不属于 $\mathcal K_{\mathrm{bdry}}$。

给定三个节点事件标识符函数：

$$
\eta^{\mathrm{node,ord}}:
V\times\mathbb N\times[L]
\to\mathsf{EID},
$$

$$
\eta^{\mathrm{node,joint}}:
V\times\mathbb N
\to\mathsf{EID},
\qquad
\eta^{\mathrm{node,front}}:
V\times\mathbb N
\to\mathsf{EID}.
$$

要求三个函数都是单射，其像集两两不交，并且都与定义 2.1c 中三个边界标识符函数的像集不交。于是事件标识符由空间节点、绝对轮次和所选语义配置唯一确定；配置 O 还把归属索引作为第三个输入坐标。函数值的数值大小不定义事件依赖次序。

给定四个提交标识符函数：

$$
\gamma^{\mathrm{in}}:[L]\to\mathsf{CID},
$$

$$
\gamma^{\mathrm{ord}}:
V\times\mathbb N\times[L]\to\mathsf{CID},
$$

$$
\gamma^{\mathrm{joint}}:
V\times\mathbb N\to\mathsf{CID},
\qquad
\gamma^{\mathrm{front}}:
V\times\mathbb N\to\mathsf{CID}.
$$

要求四个函数都是单射且像集两两不交。它们只确定提交记录身份，不定义状态依赖次序；提交次序仍由 $\mathsf{CKey}$ 的坐标决定。

定义事件种类集合：

$$
\mathcal K^P
=
\mathcal K_{\mathrm{bdry}}
\cup
\{\mathtt{node}_P\}.
$$

取两个不同标签 $\mathtt{initialState}$ 与 $\mathtt{commitState}$。对每个节点 $v\in V$，定义状态输入记录集合：

$$
\mathcal{SI}_v
=
\bigl(\{\mathtt{initialState}\}\times\{\widetilde S_v^0\}\bigr)
\cup
\bigl(\{\mathtt{commitState}\}\times\mathcal Q_v\bigr).
$$

定义状态值投影函数：

$$
\operatorname{stateVersion}:\mathcal{SI}_v\to\widetilde{\mathcal S}_v,
$$

$$
\operatorname{stateVersion}
((\mathtt{initialState},\widetilde S_v^0))
=
\widetilde S_v^0,
$$

$$
\operatorname{stateVersion}
((\mathtt{commitState},q))
=
\operatorname{version}(q).
$$

再定义提交来源部分函数：

$$
\operatorname{stateCommit}:\mathcal{SI}_v\rightharpoonup\mathcal Q_v,
$$

其定义域是 $\{\mathtt{commitState}\}\times\mathcal Q_v$，并规定：

$$
\operatorname{stateCommit}((\mathtt{commitState},q))=q.
$$

因此，状态输入记录不仅保存被读取的状态值，还区分它是节点初始状态，还是由某个具体提交记录产生的状态版本。

对每个节点 $v\in V$，定义常规节点事件值集合：

$$
\mathcal W_v^{\mathrm{node}}
=
\mathcal{SI}_v
\times\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\times\mathcal L_v^\star
\times\mathcal Q_v^\star
\times\mathcal{RR}_v^\star
\times\mathcal R^\star.
$$

它的六个坐标依次是：该事件读取的状态输入记录、消费的入站消息多重集、产生的局部输出记录序列、产生的状态提交记录序列、产生的路由记录序列和派发的出站消息序列。

定义常规节点事件值的坐标投影函数：

$$
\operatorname{stateInput}:\mathcal W_v^{\mathrm{node}}\to\mathcal{SI}_v,
\qquad
\operatorname{inbox}:\mathcal W_v^{\mathrm{node}}
\to\mathcal M_{\mathrm{fin}}(\mathcal R_v),
$$

$$
\operatorname{local}:\mathcal W_v^{\mathrm{node}}\to\mathcal L_v^\star,
\qquad
\operatorname{commits}:\mathcal W_v^{\mathrm{node}}\to\mathcal Q_v^\star,
$$

$$
\operatorname{routes}:\mathcal W_v^{\mathrm{node}}\to\mathcal{RR}_v^\star,
\qquad
\operatorname{outbox}:\mathcal W_v^{\mathrm{node}}\to\mathcal R^\star.
$$

对 $w=(\varsigma,I,\mathbf H,\mathbf Q,\mathbf R,\mathbf M)\in\mathcal W_v^{\mathrm{node}}$，规定：

$$
\operatorname{stateInput}(w)=\varsigma,
\quad
\operatorname{inbox}(w)=I,
\quad
\operatorname{local}(w)=\mathbf H,
$$

$$
\operatorname{commits}(w)=\mathbf Q,
\operatorname{routes}(w)=\mathbf R,
\quad
\operatorname{outbox}(w)=\mathbf M.
$$

定义输入事件值集合：

$$
\mathcal W_s^{\mathrm{in}}
=
\mathcal B_{\mathrm{in}}
\times\mathcal{SI}_s
\times\mathcal L_s^\star
\times\mathcal Q_s^\star
\times\mathcal{RR}_s^\star
\times\mathcal R^\star.
$$

它的前两个坐标是边界注入记录与状态输入记录，其余四个坐标与常规节点事件值的后四个坐标相同。

定义输入事件值的坐标投影函数：

$$
\operatorname{boundary}:\mathcal W_s^{\mathrm{in}}\to\mathcal B_{\mathrm{in}},
\qquad
\operatorname{stateInput}:\mathcal W_s^{\mathrm{in}}\to\mathcal{SI}_s,
$$

$$
\operatorname{local}:\mathcal W_s^{\mathrm{in}}\to\mathcal L_s^\star,
\qquad
\operatorname{commits}:\mathcal W_s^{\mathrm{in}}\to\mathcal Q_s^\star,
$$

$$
\operatorname{routes}:\mathcal W_s^{\mathrm{in}}\to\mathcal{RR}_s^\star,
\qquad
\operatorname{outbox}:\mathcal W_s^{\mathrm{in}}\to\mathcal R^\star.
$$

对 $w=(b,\varsigma,\mathbf H,\mathbf Q,\mathbf R,\mathbf M)\in\mathcal W_s^{\mathrm{in}}$，规定：

$$
\operatorname{boundary}(w)=b,
\quad
\operatorname{stateInput}(w)=\varsigma,
\quad
\operatorname{local}(w)=\mathbf H,
$$

$$
\operatorname{commits}(w)=\mathbf Q,
\quad
\operatorname{routes}(w)=\mathbf R,
\quad
\operatorname{outbox}(w)=\mathbf M.
$$

定义该语义配置的事件值全集：

$$
\mathsf{EVal}^P
=
\mathcal W_s^{\mathrm{in}}
\cup
\bigcup_{v\in V}\mathcal W_v^{\mathrm{node}}
\cup X\cup Y.
$$

现在在定义 2.1a 中取 $\mathcal K=\mathcal K^P$ 与 $\mathsf{EVal}=\mathsf{EVal}^P$。定义事件值空间函数：

$$
\mathcal V^P:
\mathfrak H_L(\mathcal K^P)
\to
2^{\mathsf{EVal}^P}.
$$

对任意事件头：

$$
h=(\eta,\kappa,\ell,\theta,\Omega,c)
\in\mathfrak H_L(\mathcal K^P),
$$

把函数值 $\mathcal V^P(h)$，简写为 $\mathcal V_h$，定义为：

$$
\mathcal V_h
=
\begin{cases}
\mathcal W_s^{\mathrm{in}},
&\kappa=\mathtt{inject},\ \ell=s,\\
\mathcal W_v^{\mathrm{node}},
&\kappa=\mathtt{node}_P,\ \ell=v\in V,\\
Y,
&\kappa=\mathtt{readout},\ \ell=z,\\
X,
&\kappa=\mathtt{sample},\ \ell=\mathtt{external},\\
\varnothing,
&\text{其他情形}.
\end{cases}
$$

因此语义配置 $P$ 的逻辑事件实例集合是已经在定义 2.1a 中给出的：

$$
\mathfrak E_L(\mathcal K^P)
=
\{(h,\nu)\mid
h\in\mathfrak H_L(\mathcal K^P),\quad
\nu\in\mathcal V_h\}.
$$

为便于阅读，后文把事件头继续写成：

$$
h_e
=
(\eta,\kappa,\ell,\theta,\Omega,c),
\tag{GD-E1}
$$
^eq-logical-event-instance

该事件头是定义 2.1a 在固定周期 Tide 参考语义中的具体使用：$\theta$ 是逻辑时间戳，$\Omega$ 是归属支持集，$c$ 是因果前沿。定义 2.4 的完整可选事件函数 $f_\eta$ 必须满足定义 2.1 与式 GD-2.4；事件级因果前沿 $c$ 是整个事件头和值的有效保守上界，值元组内的单个局部输出、状态版本或消息可以登记不大于 $c$ 的更紧因果前沿。

实际事件集合只登记真正发生的事件。选择器不选择某条边时，相应路由记录的第六个坐标不含该边，出站消息序列中也没有由该路由槽位和该边构成的消息；不会为“未发生的下游事件”伪造一个值为 $\bot$ 的事件。另一方面，已经发生的节点事件可以在局部输出序列中包含 $z=\bot$ 的记录，表示该转移已执行但该局部输出槽位没有路由可见值。

本文使用以下事件实例：

1. 对每个 $t\in[L]$，使用定义 2.1c 的输入事件头 $h_{e_t^{\mathrm{in}}}$。

2. 对非空常规收件箱分组，节点事件头按下列公式定义。

配置 O：对每个满足 $t\in\mathcal O_{v,\tau}$ 的三元组 $(v,\tau,t)$，选择事件值的一个有效因果前沿 $c_{v,\tau,t}^{\mathrm{ord}}\in\mathbb F_L$，并定义：

$$
h_{v,\tau,t}^{\mathrm{ord}}
=
\left(
\eta^{\mathrm{node,ord}}(v,\tau,t),
\mathtt{node}_{\mathrm{ord}},
v,
(\tau,i_{\mathrm{commit}}),
\{t\},
c_{v,\tau,t}^{\mathrm{ord}}
\right).
$$

配置 J：对每个满足 $I_{v,\tau}\neq0_{\mathcal R_v}$ 的二元组 $(v,\tau)$，选择事件值的一个有效因果前沿 $c_{v,\tau}^{\mathrm{joint}}\in\mathbb F_L$，并定义：

$$
h_{v,\tau}^{\mathrm{joint}}
=
\left(
\eta^{\mathrm{node,joint}}(v,\tau),
\mathtt{node}_{\mathrm{joint}},
v,
(\tau,i_{\mathrm{commit}}),
\mathcal O_{v,\tau},
c_{v,\tau}^{\mathrm{joint}}
\right).
$$

配置 F：对每个满足 $I_{v,\tau}\neq0_{\mathcal R_v}$ 的二元组 $(v,\tau)$，定义：

$$
h_{v,\tau}^{\mathrm{front}}
=
\left(
\eta^{\mathrm{node,front}}(v,\tau),
\mathtt{node}_{\mathrm{front}},
v,
(\tau,i_{\mathrm{commit}}),
\mathcal O_{v,\tau},
c_{v,\tau}^{\star}
\right),
$$

其中 $c_{v,\tau}^{\star}$ 由式 GD-F1 定义。对与当前 $P$ 对应的那一个公式，所得事件头属于 $\mathfrak H_L(\mathcal K^P)$；实际事件是该事件头与相应事件值的有序对。

3. 对每个 $t\in[L]$，使用定义 2.1c 的固定读出事件头 $h_{e_t^{\mathrm{out}}}$。

读出事件对每个 $t$ 必定存在，不能被选择器取消、推迟或改写时间戳。

4. 自回归执行额外包含定义 2.1c 的采样事件头 $h_{e_t^{\mathrm{sample}}}$。

给定序列分块定理不需要采样事件；它把 $x_{0:L}$ 作为边界数据。

输入事件 $e_t^{\mathrm{in}}$ 的事件值第一个坐标必须等于 $b_t^{\mathrm{in}}$。读出和采样事件满足：

$$
\nu(e_t^{\mathrm{out}})=y_t\in Y,
$$

$$
\nu(e_t^{\mathrm{sample}})
=
\operatorname{SelectToken}(y_t)
\in X.
$$

对定义 4.2a 的每条实际消息 $m$，要求：

$$
\operatorname{occ}
\left(
\operatorname{outbox}(\nu(\operatorname{producer}(m))),
m
\right)
=1.
$$

若 $m\in\operatorname{dom}(\operatorname{consumer})$，则要求：

$$
\operatorname{inbox}(\nu(\operatorname{consumer}(m)))(m)>0.
$$

每个路由记录还必须满足定义 6.2a 的源事件标识符、源时间戳和局部槽位坐标约束。这样，“事件值包含哪些产物”由上述笛卡尔积、投影函数与一致性条件给出，而不是由未类型化的副作用清单给出。

更具体地，若 $e$ 是输入事件或常规节点事件，且：

$$
\operatorname{routes}(\nu(e))
=(r_0,\ldots,r_{m-1}),
$$

则要求 $\operatorname{commits}(\nu(e))$ 的长度至多为 $1$。若它非空，就存在唯一 $q\in\mathcal Q_{\operatorname{loc}(e)}$ 使：

$$
\operatorname{commits}(\nu(e))=(q).
$$

该提交记录必须满足：

$$
\operatorname{ctime}(q)=\operatorname{time}(e).
$$

提交键的第二个坐标由事件配置唯一确定。若 $e=e_t^{\mathrm{in}}$，则：

$$
\operatorname{cid}(q)=\gamma^{\mathrm{in}}(t),
\qquad
\operatorname{ckey}(q)
=
(\operatorname{time}(e),t).
$$

若 $P=\mathrm{ord}$、$\operatorname{kind}(e)=\mathtt{node}_{\mathrm{ord}}$ 且 $\operatorname{support}(e)=\{t\}$，则同样要求：

$$
\operatorname{cid}(q)=\gamma^{\mathrm{ord}}(\operatorname{loc}(e),\operatorname{round}(\operatorname{time}(e)),t),
\qquad
\operatorname{ckey}(q)
=
(\operatorname{time}(e),t).
$$

若 $P\in\{\mathrm{joint},\mathrm{front}\}$ 且 $\operatorname{kind}(e)=\mathtt{node}_P$，则要求：

$$
\operatorname{cid}(q)
=
\begin{cases}
\gamma^{\mathrm{joint}}
(\operatorname{loc}(e),\operatorname{round}(\operatorname{time}(e))),
&P=\mathrm{joint},\\
\gamma^{\mathrm{front}}
(\operatorname{loc}(e),\operatorname{round}(\operatorname{time}(e))),
&P=\mathrm{front},
\end{cases}
$$

并且：

$$
\operatorname{ckey}(q)
=
(\operatorname{time}(e),0).
$$

若提交序列为 $(q)$，则 $\operatorname{version}(q)$ 是本事件完成后对后继事件可见的节点状态；若提交序列为空，则本事件不改变节点状态。

定义 6.2a 还要求 $\operatorname{local}(\nu(e))$ 具有长度 $m$，并与路由记录逐槽位对应。对每个 $j\in[m]$ 和每条 $a\in\operatorname{edges}(r_j)$，相应带标签派发请求 $\delta\in\mathcal D$ 必须满足：

$$
\operatorname{Dispatch}(\delta)\in\mathcal M,
$$

$$
\operatorname{producer}(\operatorname{Dispatch}(\delta))=e,
$$

并且：

$$
\operatorname{occ}
\left(
\operatorname{outbox}(\nu(e)),
\operatorname{Dispatch}(\delta)
\right)
=1.
$$

反过来，出站消息序列中的每条消息必须来自且只来自一个这样的派发请求。

### 定义 7.2：直接依赖与事件值依赖完备性

给定一次已经实例化的有限参考执行，其事件集合记为：

$$
\mathcal E_L^P
\subseteq
\mathfrak E_L(\mathcal K^P).
$$

并要求 $\operatorname{id}$ 在 $\mathcal E_L^P$ 上满足定义 2.1b 的单射条件。

对每个 $t\in[L]$，要求 $\mathcal E_L^P$ 中存在唯一事件，其事件头等于定义 2.1c 的 $h_{e_t^{\mathrm{in}}}$，并把该事件记为 $e_t^{\mathrm{in}}$；同样要求存在唯一事件头为 $h_{e_t^{\mathrm{out}}}$ 的事件，并记为 $e_t^{\mathrm{out}}$。本定义中的 $\mathcal E_L^P$ 是给定序列执行的事件集合，不含种类为 $\mathtt{sample}$ 的事件。

取有限实际消息集合：

$$
\mathcal M_L^P\subseteq\mathcal R,
$$

以及定义 4.2a 的函数：

$$
\operatorname{producer}_L^P:
\mathcal M_L^P\to\mathcal E_L^P,
$$

$$
\operatorname{consumer}_L^P:
\mathcal M_L^P\rightharpoonup\mathcal E_L^P.
$$

用 $\mathcal M_L^P$ 按定义 4.3 构造 $I_{v,\tau,t}$、$I_{v,\tau}$ 与 $\mathcal O_{v,\tau}$。要求实际常规节点事件头集合恰好为：

$$
\{h(e)\mid e\in\mathcal E_L^P,
\operatorname{kind}(e)=\mathtt{node}_{\mathrm{ord}}\}
=
\{h_{v,\tau,t}^{\mathrm{ord}}
\mid v\in V,\ \tau\in\mathbb N,
t\in\mathcal O_{v,\tau}\},
$$

当 $P=\mathrm{ord}$；当 $P=\mathrm{joint}$ 时要求：

$$
\{h(e)\mid e\in\mathcal E_L^P,
\operatorname{kind}(e)=\mathtt{node}_{\mathrm{joint}}\}
=
\{h_{v,\tau}^{\mathrm{joint}}
\mid v\in V,\ \tau\in\mathbb N,
I_{v,\tau}\neq0_{\mathcal R_v}\};
$$

当 $P=\mathrm{front}$ 时要求：

$$
\{h(e)\mid e\in\mathcal E_L^P,
\operatorname{kind}(e)=\mathtt{node}_{\mathrm{front}}\}
=
\{h_{v,\tau}^{\mathrm{front}}
\mid v\in V,\ \tau\in\mathbb N,
I_{v,\tau}\neq0_{\mathcal R_v}\}.
$$

由于节点事件标识符函数是单射且 $\operatorname{id}$ 在实际事件集合上也是单射，每个右侧事件头至多对应一个实际事件；上述集合等式同时要求它确实存在。

定义具有状态输入的事件集合：

$$
\mathcal E_{L,\mathrm{state}}^P
=
\{e\in\mathcal E_L^P
\mid
\operatorname{kind}(e)\in
\{\mathtt{inject},\mathtt{node}_P\}\}.
$$

定义状态事件键函数：

$$
\operatorname{stateKey}:
\mathcal E_{L,\mathrm{state}}^P
\to\mathsf{CKey}.
$$

若 $e=e_t^{\mathrm{in}}$，规定：

$$
\operatorname{stateKey}(e)
=
(\operatorname{time}(e),t).
$$

若 $P=\mathrm{ord}$、$\operatorname{kind}(e)=\mathtt{node}_{\mathrm{ord}}$ 且 $\operatorname{support}(e)=\{t\}$，规定：

$$
\operatorname{stateKey}(e)
=
(\operatorname{time}(e),t).
$$

若 $P\in\{\mathrm{joint},\mathrm{front}\}$ 且 $\operatorname{kind}(e)=\mathtt{node}_{P}$，规定：

$$
\operatorname{stateKey}(e)
=
(\operatorname{time}(e),0).
$$

定义事件 $e'\in\mathcal E_{L,\mathrm{state}}^P$ 之前、同一空间节点已经产生的提交对集合：

$$
\mathcal C_{e'}^{\mathrm{state}}
=
\left\{
(e,q)
\ \middle|
\begin{array}{l}
e\in\mathcal E_{L,\mathrm{state}}^P,\\
\operatorname{loc}(e)=\operatorname{loc}(e'),\\
\operatorname{commits}(\nu(e))=(q_0,\ldots,q_{n-1})
\text{ 对某个 }n\in\mathbb N,\\
q=q_j\text{ 对某个 }j\in[n],\\
\operatorname{ckey}(q)<_{\mathsf{CKey}}
\operatorname{stateKey}(e')
\end{array}
\right\}.
$$

若 $\mathcal C_{e'}^{\mathrm{state}}=\varnothing$，要求：

$$
\operatorname{stateInput}(\nu(e'))
=
(\mathtt{initialState},\widetilde S_{\operatorname{loc}(e')}^0).
$$

若 $\mathcal C_{e'}^{\mathrm{state}}\neq\varnothing$，要求其中存在唯一有序对 $(e_{e'}^{\mathrm{state}},q_{e'}^{\mathrm{state}})$，满足对每个 $(e,q)\in\mathcal C_{e'}^{\mathrm{state}}$：

$$
\operatorname{ckey}(q)
\leq_{\mathsf{CKey}}
\operatorname{ckey}(q_{e'}^{\mathrm{state}}),
$$

并要求：

$$
\operatorname{stateInput}(\nu(e'))
=
(\mathtt{commitState},q_{e'}^{\mathrm{state}}).
$$

上述唯一最大提交条件定义部分函数：

$$
\operatorname{stateProducer}:
\mathcal E_{L,\mathrm{state}}^P
\rightharpoonup
\mathcal E_{L,\mathrm{state}}^P,
$$

其定义域是满足 $\mathcal C_{e'}^{\mathrm{state}}\neq\varnothing$ 的事件，并规定：

$$
\operatorname{stateProducer}(e')
=
e_{e'}^{\mathrm{state}}.
$$

定义消息依赖关系：

$$
\mathcal A_{L,\mathrm{msg}}^P
=
\left\{
(\operatorname{producer}_L^P(m),
\operatorname{consumer}_L^P(m))
\ \middle|
m\in\operatorname{dom}(\operatorname{consumer}_L^P)
\right\}.
$$

定义状态依赖关系：

$$
\mathcal A_{L,\mathrm{state}}^P
=
\{(\operatorname{stateProducer}(e'),e')
\mid
e'\in\operatorname{dom}(\operatorname{stateProducer})\}.
$$

对每个 $t\in[L]$，定义读出前提交对集合：

$$
\mathcal C_t^{\mathrm{read}}
=
\left\{
(e,q)
\ \middle|
\begin{array}{l}
e\in\mathcal E_{L,\mathrm{state}}^P,\\
\operatorname{loc}(e)=z,\\
\operatorname{commits}(\nu(e))=(q_0,\ldots,q_{n-1})
\text{ 对某个 }n\in\mathbb N,\\
q=q_j\text{ 对某个 }j\in[n],\\
\operatorname{ctime}(q)<_{\Theta}\theta_t^{\mathrm{out}}
\end{array}
\right\}.
$$

若 $\mathcal C_t^{\mathrm{read}}\neq\varnothing$，要求其中存在唯一有序对 $(e_t^{\mathrm{read}},q_t^{\mathrm{read}})$，满足对每个 $(e,q)\in\mathcal C_t^{\mathrm{read}}$：

$$
\operatorname{ckey}(q)
\leq_{\mathsf{CKey}}
\operatorname{ckey}(q_t^{\mathrm{read}}),
$$

定义读出依赖关系：

$$
\mathcal A_{L,\mathrm{read}}^P
=
\{(e_t^{\mathrm{read}},e_t^{\mathrm{out}})
\mid
t\in[L],\ \mathcal C_t^{\mathrm{read}}\neq\varnothing\}.
$$

若 $\mathcal C_t^{\mathrm{read}}=\varnothing$，则 $e_t^{\mathrm{out}}$ 读取固定初始状态 $\widetilde S_z^0$，不增加状态事件前驱。

定义给定序列执行的边界依赖关系：

$$
\mathcal A_{L,\mathrm{bdry}}^P=\varnothing.
$$

最终定义直接依赖关系：

$$
\mathcal A_L^P
=
\mathcal A_{L,\mathrm{msg}}^P
\cup
\mathcal A_{L,\mathrm{state}}^P
\cup
\mathcal A_{L,\mathrm{read}}^P
\cup
\mathcal A_{L,\mathrm{bdry}}^P
\subseteq
\mathcal E_L^P\times\mathcal E_L^P.
$$

以上四个关系分别表示当前参考语义中的消息、状态、读出和自回归边界直接依赖：

- 输入事件产生的第一跳消息与常规节点事件产生的消息使用同一个 $\mathcal A_{L,\mathrm{msg}}^P$ 定义。
- 每个带 $\mathtt{commitState}$ 标签的状态输入记录通过部分函数 $\operatorname{stateProducer}$ 唯一指向产生该提交记录的事件。
- 读出边由集合 $\mathcal C_t^{\mathrm{read}}$ 中提交键最大的唯一有序对确定。
- 本文把选择器、路由记录和消息派发保留为节点事件内部的确定原语，因此当前事件种类集合中没有独立选择器事件。若未来增加该事件种类，必须同时扩充事件值集合和直接依赖关系，不能只在文字中补一条“控制边”。

定义事件图：

$$
D_L^P
=
(\mathcal E_L^P,\mathcal A_L^P).
$$

为单独表述有限前缀自回归扩展，定义采样事件集合：

$$
\mathcal E_L^{\mathrm{sample}}
=
\{e_t^{\mathrm{sample}}\mid t\in[L]\},
$$

其中每个 $e_t^{\mathrm{sample}}$ 是事件头为定义 2.1c 中 $h_{e_t^{\mathrm{sample}}}$、事件值为 $\operatorname{SelectToken}(y_t)$ 的唯一事件；并要求当 $t+1\in[L]$ 时，输入序列满足式 GD-0.5，即 $x_{t+1}=\operatorname{SelectToken}(y_t)$。定义：

$$
\mathcal E_{L,\mathrm{AR}}^P
=
\mathcal E_L^P\cup\mathcal E_L^{\mathrm{sample}},
$$

$$
\mathcal A_{L,\mathrm{AR}}^P
=
\mathcal A_L^P
\cup
\{(e_t^{\mathrm{out}},e_t^{\mathrm{sample}})\mid t\in[L]\}
\cup
\{(e_t^{\mathrm{sample}},e_{t+1}^{\mathrm{in}})
\mid t+1\in[L]\},
\qquad
\mathcal A_{L,\mathrm{AR}}^P
\subseteq
\mathcal E_{L,\mathrm{AR}}^P
\times
\mathcal E_{L,\mathrm{AR}}^P,
$$

以及自回归有限前缀事件图：

$$
D_{L,\mathrm{AR}}^P
=
(\mathcal E_{L,\mathrm{AR}}^P,
\mathcal A_{L,\mathrm{AR}}^P).
$$

定义一次有限参考执行记录为六元组：

$$
\mathscr X_L^P
=
(x_{0:L},
\mathcal E_L^P,
\mathcal M_L^P,
\operatorname{producer}_L^P,
\operatorname{consumer}_L^P,
\mathcal A_L^P),
$$

其中 $x_{0:L}\in X^L$，并要求其输入事件值使用同一序列的 $b_t^{\mathrm{in}}$。整个六元组还必须满足定义 4.2a 的消息生命周期条件、定义 7.1 的事件值一致性条件，以及本定义的直接依赖条件。后文固定 $\mathscr X_L^P$ 后，为简化公式，可以省略 $L,P$ 上标，把其中四个消息对象写成 $\mathcal M$、$\operatorname{producer}$、$\operatorname{consumer}$ 和相应收件箱。

定义所有满足上述条件的六元组组成的集合为 $\mathfrak X_L^P$。因此：

$$
\mathscr X_L^P\in\mathfrak X_L^P.
$$

定义直接前驱集合函数：

$$
\operatorname{Pred}:\mathcal E_L^P\to 2^{\mathcal E_L^P},
$$

$$
\operatorname{Pred}(e)
=
\{e'\in\mathcal E_L^P\mid(e',e)\in\mathcal A_L^P\}.
$$

取一个不属于 $X$ 的符号 $\mathtt{unit}$，定义单元素集合：

$$
\mathbf 1=\{\mathtt{unit}\}.
$$

对每个事件 $e\in\mathcal E_L^P$，定义边界参数集合：

$$
\mathcal B_e
=
\begin{cases}
X,&\operatorname{kind}(e)=\mathtt{inject},\\
\mathbf 1,&\operatorname{kind}(e)\neq\mathtt{inject}.
\end{cases}
$$

定义该次执行中的实际边界参数 $b_e\in\mathcal B_e$：若 $e=e_t^{\mathrm{in}}$，则 $b_e=x_t$；否则 $b_e=\mathtt{unit}$。模型权重、拓扑和其他不随输入序列改变的常量固定在后述函数 $F_e$ 本身中，不额外作为未类型化参数传入。

定义前驱值赋值集合：

$$
\mathcal P_e
=
\left\{
g:\operatorname{Pred}(e)\to
\bigcup_{e'\in\operatorname{Pred}(e)}\mathcal V_{h(e')}
\ \middle|
g(e')\in\mathcal V_{h(e')}
\text{ 对每个 }e'\in\operatorname{Pred}(e)
\right\}.
$$

当 $\operatorname{Pred}(e)=\varnothing$ 时，$\mathcal P_e$ 只含空函数。称事件图 $D_L^P$ 对该参考执行是**事件值依赖完备的**，当且仅当对每个 $e\in\mathcal E_L^P$ 都存在确定性事件函数：

$$
F_e:
\{h(e)\}
\times\mathcal P_e
\times\mathcal B_e
\to
\mathcal V_{h(e)},
$$

使下面的实际执行等式成立。

对实际执行，定义实际前驱赋值 $g_e\in\mathcal P_e$：

$$
g_e(e')=\nu(e'),
\qquad e'\in\operatorname{Pred}(e).
$$

$$
\nu(e)=F_e(h(e),g_e,b_e).
$$

这个定义把事件**值**函数可读取的输入限制为三个数学对象：已经给定的事件头、直接前驱值赋值和 $b_e$。只有输入事件的 $b_e$ 属于 $X$；其他事件的边界参数都是同一个常量 $\mathtt{unit}$。未选择的路由或消息以源事件值中的空集合或缺失记录表示，不建立值为 $\bot$ 的假事件。

本定义不把“动态事件是否存在、其事件头如何跨不同输入序列生成”偷藏进依赖完备性一词。跨输入的事件存在性和完整事件记录受定义 2.4 的可选函数 $f_\eta$ 约束；若后续要证明事件头本身也能从前驱值统一重建，还必须另外给出一个跨输入序列共享的头生成函数。本页当前的调度等价定理只重排同一次已经实例化的有限参考执行，不使用尚未证明的跨输入头生成结论。

> [!note] 物理融合不改变上述定义
> $F_e$ 在本页中是一个原子参考函数。物理实现若把它展开为多个操作，必须证明这些操作的组合仍计算同一个 $F_e$；若要在逻辑层观察这些中间结果，则应把一个事件替换为新的有限事件集合和依赖关系。该说明不向当前事件图增加新的对象。

### 定义 7.3：空间节点的完整规范输入序列

先固定 $\mathscr X_L^P\in\mathfrak X_L^P$。本节中的 $I_{v,\tau}$、$B_{v,\tau}$ 与 $g_{v,\tau}$ 默认由该执行记录的消息集合和生命周期函数构造。

对节点 $v$，定义常规分组记录集合：

$$
\mathcal G_v
=
\mathbb N
\times\{0,\ldots,R-1\}
\times\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\times\mathcal B_v.
$$

对每个满足 $I_{v,\tau}\neq 0_{\mathcal R_v}$ 的绝对轮次 $\tau$，定义常规分组记录：

$$
g_{v,\tau}
=
\left(
q_R(\tau),
r_R(\tau),
I_{v,\tau},
B_{v,\tau}
\right)
\in\mathcal G_v.
$$

当需要同时量化不同参考执行时，用：

$$
I_{v,\tau}[\mathscr X_L^P],
\qquad
B_{v,\tau}[\mathscr X_L^P],
\qquad
g_{v,\tau}[\mathscr X_L^P]
$$

表示由执行记录 $\mathscr X_L^P$ 构造的相应对象。定义合法常规分组记录集合：

$$
\mathcal G_v^{\mathrm{legal}}
=
\left\{
g_{v,\tau}[\mathscr X_L^P]
\ \middle|
\begin{array}{l}
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\},\\
\mathscr X_L^P\in\mathfrak X_L^P,\\
\tau\in\mathbb N,\\
I_{v,\tau}[\mathscr X_L^P]\neq 0_{\mathcal R_v}
\end{array}
\right\}.
$$

这个集合条件同时保证：记录中的周期编号与周期内偏移来自同一个 $\tau$，消息多重集只含该节点该到达时间的实际消息，输入元组 $B_{v,\tau}$ 由同一消息多重集按定义 4.3--4.4 构造。

定义常规分组记录的执行时间戳：

$$
\theta_{v,\tau}^{\mathrm{step}}
=
(\tau,i_{\mathrm{step}}).
$$

取两个互不相同的标签 $\mathtt{group}$ 与 $\mathtt{injectRecord}$。定义：

$$
\mathcal U_{v,\mathrm{group}}^{\mathrm{rec}}
=
\left\{
(\mathtt{group},(Rq+r,i_{\mathrm{step}}),g)
\ \middle|
g=(q,r,I,B)\in\mathcal G_v^{\mathrm{legal}}
\right\}.
$$

定义合法边界注入记录集合：

$$
\mathcal B_{\mathrm{in}}^{\mathrm{legal}}
=
\{(t,\theta_t^{\mathrm{in}},s,x)
\mid t\in[L],\ x\in X\}.
$$

并定义带时间戳的注入输入记录集合：

$$
\mathcal U_{\mathrm{inject}}^{\mathrm{rec}}
=
\{(\mathtt{injectRecord},\theta_t^{\mathrm{in}},b)
\mid b=(t,\theta_t^{\mathrm{in}},s,x)
\in\mathcal B_{\mathrm{in}}^{\mathrm{legal}}\}.
$$

节点 $v$ 的带标签输入记录集合定义为：

$$
\mathcal U_v^{\mathrm{rec}}
=
\begin{cases}
\mathcal U_{v,\mathrm{group}}^{\mathrm{rec}},
&v\neq s,\\
\mathcal U_{s,\mathrm{group}}^{\mathrm{rec}}
\cup
\mathcal U_{\mathrm{inject}}^{\mathrm{rec}},
&v=s.
\end{cases}
$$

定义函数 $\operatorname{utime}:\mathcal U_v^{\mathrm{rec}}\to\Theta$：

$$
\operatorname{utime}((\mathtt{group},\theta,g))=\theta,
$$

并且在 $v=s$ 时：

$$
\operatorname{utime}((\mathtt{injectRecord},\theta,b))=\theta.
$$

定义合法规范输入序列集合 $\mathfrak U_v\subseteq(\mathcal U_v^{\mathrm{rec}})^\star$。序列 $(u_0,\ldots,u_{n-1})$ 属于 $\mathfrak U_v$，当且仅当：

$$
\operatorname{utime}(u_i)
<_{\Theta}
\operatorname{utime}(u_{i+1}),
\qquad i\in\mathbb N,\ i+1<n.
$$

并且存在 $P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\}$ 与同一个 $\mathscr X_L^P\in\mathfrak X_L^P$，使该执行记录在节点 $v$ 产生的全部常规分组记录与输入节点注入记录恰好是序列中的这些记录。这个共同执行条件排除“每一项分别合法、但来自互不相容执行”的拼接序列。

对空间节点 $v$，把全部实际常规分组记录与仅在 $v=s$ 时存在的实际注入记录按 $<_{\Theta}$ 排列，得到完整规范输入序列：

$$
\mathbf U_v\in\mathfrak U_v.
$$

更明确地，$\mathbf U_v$ 中的常规记录恰好为：

$$
\left\{
(\mathtt{group},\theta_{v,\tau}^{\mathrm{step}},g_{v,\tau})
\mid I_{v,\tau}\neq 0_{\mathcal R_v}
\right\}
$$

并且当 $v=s$ 时，其注入记录恰好为：

$$
\left\{
(\mathtt{injectRecord},\theta_t^{\mathrm{in}},b_t^{\mathrm{in}})
\mid t\in[L]
\right\}
.
$$

由引理 4.5 与引理 4.6，这些记录组成有限集。常规记录位于阶段 $i_{\mathrm{step}}$，注入记录位于阶段 $i_{\mathrm{inject}}$，所以同一节点不会出现两个具有相同 $\operatorname{utime}$ 的规范输入记录。

这里的“序列”是为了使参考转导器具有确定输入次序，不表示物理运行时必须按流式逐项到达或执行。物理实现可以先收集、分段、排序和打包，只要产生相同的规范序列语义。

### 定义 7.4：空间节点参考转导器与状态提交轨迹

给定输入节点的注入转移：

$$
\mathcal I_s:
[L]\times X\times\widetilde{\mathcal S}_s
\to
\mathcal Z_s\times\widetilde{\mathcal S}_s.
$$

若 $\mathcal I_s$ 对 `token` $t$ 返回非空带标签隐藏表示 $z$，则输入事件的输出记录为 $(t,z)$，其 `owner=t`，并必须满足 $t\leq\operatorname{frontier}(z)$。另一方面，输入事件时间戳为 $\theta_t^{\mathrm{in}}$，式 GD-2.4 给出 $\operatorname{frontier}(z)\leq t$，所以实际必有：

$$
\operatorname{frontier}(z)=t.
$$

定义节点 $v$ 的完整参考产物集合：

$$
\mathsf{Artifact}_v^P
=
\mathcal{SI}_v^\star
\times\mathcal L_v^\star
\times\mathcal Q_v^\star
\times\mathcal{RR}_v^\star
\times\mathcal R^\star
\times\widetilde{\mathcal S}_v.
$$

节点参考转导器是确定函数：

$$
\operatorname{Ref}_v^P:
\mathfrak U_v\times\widetilde{\mathcal S}_v
\to
\mathsf{Artifact}_v^P.
$$

它按 $\mathbf U_v$ 的时间戳顺序处理记录：

- 在处理每条记录前，若此前没有提交记录，则相应事件值的 $\operatorname{stateInput}$ 坐标取 $(\mathtt{initialState},\widetilde S_v^0)$；否则取 $(\mathtt{commitState},q)$，其中 $q$ 是此前提交键最大的提交记录。
- 注入记录使用 $\mathcal I_s$。
- 若 $P=\mathrm{ord}$，常规分组使用式 [[#^eq-owner-ordered-group|GD-7]]。
- 若 $P=\mathrm{joint}$，常规分组使用式 [[#^eq-atomic-joint-transition|GD-8]] 与式 [[#^eq-atomic-joint-commit|GD-9]]。
- 若 $P=\mathrm{front}$，常规分组使用式 [[#^eq-frontier-fusion-transition|GD-F2]] 与式 [[#^eq-frontier-owned-output|GD-F3]]。
- 每个带标签输出经过第 6 节选择器与单位时延派发。
- 输入事件的路由记录使用定义 2.1c 的 $\eta_t^{\mathrm{in}}$ 作为 $\operatorname{sourceEvent}$；常规节点事件分别使用 $\eta^{\mathrm{node,ord}}(v,\tau,t)$、$\eta^{\mathrm{node,joint}}(v,\tau)$ 或 $\eta^{\mathrm{node,front}}(v,\tau)$。因此路由记录中的源事件标识符由 $\mathbf U_v$ 的记录坐标和语义配置唯一确定。

每次状态更新都产生定义 5.1a 的一个提交记录：

$$
q=(\gamma_q,\chi_q,\widetilde S_v^q)
\in\mathcal Q_v.
$$

输入事件使用 $\gamma_q=\gamma^{\mathrm{in}}(t)$。配置 O 的常规事件使用 $\gamma_q=\gamma^{\mathrm{ord}}(v,\tau,t)$，以及：

$$
\chi_q=((\tau,i_{\mathrm{commit}}),t).
$$

配置 J 的常规事件使用 $\gamma_q=\gamma^{\mathrm{joint}}(v,\tau)$；配置 F 使用 $\gamma_q=\gamma^{\mathrm{front}}(v,\tau)$。二者的提交键都为：

$$
\chi_q=((\tau,i_{\mathrm{commit}}),0).
$$

注入转移使用：

$$
\chi_q=((Rt,i_{\mathrm{inject}}),t).
$$

$\chi_q$ 的第二个坐标只用于同一完整逻辑时间戳内的规范并列消解，不是新的物理时间单位。按 $<_{\mathsf{CKey}}$ 排列全部提交记录，得到定义 5.1a 意义下的状态提交轨迹 $\mathbf Q_v^P\in\mathcal Q_v^\star$。

定义：

$$
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0)
=
\left(
\mathbf \Sigma_v^P,
\mathbf H_v^P,
\mathbf Q_v^P,
\mathbf R_v^P,
\mathbf M_{v,\mathrm{out}}^P,
\widetilde S_v^{P,\mathrm{final}}
\right).
\tag{GD-E2}
$$
^eq-node-reference-artifacts

六项依次属于 $\mathcal{SI}_v^\star$、$\mathcal L_v^\star$、$\mathcal Q_v^\star$、$\mathcal{RR}_v^\star$、$\mathcal R^\star$ 与 $\widetilde{\mathcal S}_v$。序列 $\mathbf\Sigma_v^P$ 按节点事件次序记录每个输入事件或常规节点事件的 $\operatorname{stateInput}$ 坐标。

参考转导器按 $\mathbf U_v$ 的顺序追加事件产物；配置 O 在同一常规分组内按归属索引递增追加。单个事件内部先按局部输出槽位递增追加局部输出与路由记录，再按 $<_{E}$ 递增追加每个路由记录派发的消息。提交记录按 $<_{\mathsf{CKey}}$ 追加。物理线程完成或缓冲区写入先后不进入这些序列次序，因此式 GD-E2 与 GD-12 中的序列相等具有唯一含义。

### 定义 7.5：固定周期读出

给定读出函数：

$$
\rho_z:
[L]\times\widetilde{\mathcal S}_z
\to Y.
$$

任何读出所需的隐藏表示/输出寄存器都必须是 $\mathcal S_z$ 的显式组件，不能作为 $\rho_z$ 的隐藏全局输入。

把输出节点状态提交轨迹写成：

$$
\mathbf Q_z^P
=
(q_0,\ldots,q_{n-1})
\in\mathcal Q_z^\star.
$$

定义读出前提交索引集合函数：

$$
J_z^P:\Theta\to 2^{[n]},
$$

$$
J_z^P(\theta)
=
\{j\in[n]\mid
\operatorname{ctime}(q_j)<_{\Theta}\theta\}.
$$

定义最大提交索引部分函数：

$$
j^\star:\Theta\rightharpoonup[n],
$$

其定义域为 $\{\theta\in\Theta\mid J_z^P(\theta)\neq\varnothing\}$。对定义域中的 $\theta$，规定：

$$
j^\star(\theta)=\max J_z^P(\theta),
$$

并定义：

$$
\widetilde S_z^{<\theta}
=
\operatorname{version}(q_{j^\star(\theta)}).
$$

若 $J_z^P(\theta)=\varnothing$，则定义 $\widetilde S_z^{<\theta}=\widetilde S_z^0$。

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
\mathfrak U_v\times\widetilde{\mathcal S}_v
\to
\mathsf{Artifact}_v^P.
$$

对输入 $(\mathbf U_v,\widetilde S_v^0)$，把其函数值记为：

$$
\mathcal C_v^P(\mathbf U_v,\widetilde S_v^0)
=
\left(
\widehat{\mathbf \Sigma}_v^P,
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

等式比较式 GD-E2 的全部六类产物。特别地，只比较最终状态或最终 `logits` 不足以证明该契约。

> [!warning] GD-12 是节点级前提，不是自动得到的实现
> 定理 8.4 把全图调度等价归约到每个节点的 GD-12 契约，但没有证明任意节点计算都能高效满足它。顺序循环也可以满足正确性；是否具有高性能 `prefill`，还要为具体注意力、SSM、FFN、选择器或路由计算分别证明。

### 引理 7.7：有限参考执行的事件 DAG

在引理 4.6 的条件下，给定任意语义配置 $P$，给定序列参考的事件图 $D_L^P$ 是有限 DAG；定义 7.2 的自回归有限前缀事件图 $D_{L,\mathrm{AR}}^P$ 也是有限 DAG。

**证明。**

由引理 4.6，消息与常规节点事件数有限；输入、读出与采样事件各至多 $L$ 个，所以事件集合有限。

在本证明内取集合：

$$
\mathcal K_7
=
\Theta\times\mathbb N,
$$

并定义二元关系：

$$
<_{\mathcal K_7}
\ \subseteq
\mathcal K_7\times\mathcal K_7.
$$

对任意 $(\theta,a),(\theta',b)\in\mathcal K_7$，规定：

$$
(\theta,a)<_{\mathcal K_7}(\theta',b)
$$

当且仅当 $\theta<_{\Theta}\theta'$，或者 $\theta=\theta'$ 且 $a<b$。

先定义自回归扩展事件集上的函数：

$$
\lambda_{L,\mathrm{AR}}^P:
\mathcal E_{L,\mathrm{AR}}^P
\to
\mathcal K_7.
$$

对每个具有状态输入的事件 $e\in\mathcal E_{L,\mathrm{state}}^P$，定义：

$$
\lambda_{L,\mathrm{AR}}^P(e)
=
\operatorname{stateKey}(e).
$$

读出事件取：

$$
\lambda_{L,\mathrm{AR}}^P(e_t^{\mathrm{out}})
=
(\theta_t^{\mathrm{out}},0),
$$

自回归执行中的采样事件取：

$$
\lambda_{L,\mathrm{AR}}^P(e_t^{\mathrm{sample}})
=
(\theta_t^{\mathrm{sample}},0).
$$

定义给定序列事件集上的限制函数：

$$
\lambda_L^P
=
\left.\lambda_{L,\mathrm{AR}}^P\right|_{\mathcal E_L^P}:
\mathcal E_L^P\to\mathcal K_7.
$$

由定义 4.2a，消息产生事件的时间戳严格早于消息到达时间戳，而消息到达时间戳严格早于消费事件的提交时间戳，所以消息边使 $\lambda_{L,\mathrm{AR}}^P$ 的第一个坐标严格增加。对状态边 $(e,e')$，定义 7.2 选择的提交记录满足：

$$
\operatorname{ckey}(q_{e'}^{\mathrm{state}})
<_{\mathsf{CKey}}
\operatorname{stateKey}(e').
$$

定义 7.1 又要求源事件 $e$ 中该提交记录的提交键等于 $\operatorname{stateKey}(e)$，所以状态边使 $\lambda_{L,\mathrm{AR}}^P$ 严格增加。读出边的源提交时间戳严格早于读出时间戳；自回归边界边由式 GD-0.4 从读出指向采样，再指向下一注入。因此每条 $(e,e')\in\mathcal A_{L,\mathrm{AR}}^P$ 都满足：

$$
\lambda_{L,\mathrm{AR}}^P(e)
<_{\mathcal K_7}
\lambda_{L,\mathrm{AR}}^P(e').
$$

若事件图存在有向环：

$$
e_0\to e_1\to\cdots\to e_k\to e_0,
$$

沿环应用上述严格不等式与字典序的传递性，会得到：

$$
\lambda_{L,\mathrm{AR}}^P(e_0)
<_{\mathcal K_7}
\lambda_{L,\mathrm{AR}}^P(e_0),
$$

关系 $<_{\mathcal K_7}$ 由两个严格全序的字典序构造，因此具有传递性和反自反性；上式与反自反性矛盾。因此 $D_{L,\mathrm{AR}}^P$ 无环。其子图 $D_L^P$ 也无环。

<div class="qed" aria-label="证毕">∎</div>

### 命题 7.7a：配置 F 的被读取产物因果前沿单调

取 $P=\mathrm{front}$。在定理 5.13 的前提下，以下两条成立：

1. 若消息 $m$ 由事件 $e$ 产生并被配置 F 的常规节点事件 $e'$ 消费，则：

$$
\operatorname{frontier}(m)
\leq
\operatorname{frontier}(e').
$$

2. 若提交记录 $q\in\operatorname{commits}(\nu(e))$，并且 $\operatorname{version}(q)$ 是配置 F 的常规节点事件 $e'$ 实际读取的状态输入，则：

$$
\operatorname{frontier}(\operatorname{version}(q))
\leq
\operatorname{frontier}(e').
$$

**证明。**

事件 $e'$ 的配置 F 转移按式 GD-F1，把其前状态和全部入站消息的因果前沿取最大值。若 $m$ 被 $e'$ 消费，则 $m$ 属于该收件箱，所以第一条成立。若 $\operatorname{version}(q)$ 是 $e'$ 读取的前状态，则其因果前沿也是式 GD-F1 取最大值的输入之一，所以第二条成立。

<div class="qed" aria-label="证毕">∎</div>

不能在当前粗粒度事件定义下自动把上述结论加强为：

$$
\operatorname{frontier}(e)
\leq
\operatorname{frontier}(e').
$$

原因是 $\operatorname{frontier}(e)$ 是整个事件值的保守上界，而 $e$ 的某条具体出站消息或某个具体状态版本可以登记更小的因果前沿。若希望得到事件级单调性，必须额外要求每条依赖边所传递产物的因果前沿等于源事件因果前沿，或者把粗事件细化为逐产物事件。因而，当前文档只主张被实际读取产物上的单调性，不主张可以无条件按事件级因果前沿对整个事件 DAG 分层。

### 例 7.8：计算核族与分块实现映射

| 节点计算核 | 逻辑事件语义 | 可能的分块实现 |
| --- | --- | --- |
| 逐 `token` 映射 / FFN | 事件独立读取各自输入 | 批量化矩阵乘 / 融合的逐元素计算 |
| 因果注意力 | 事件值只读取允许的因果前缀 | 紧凑打包 QKV + 因果掩码 / 融合的注意力 |
| Mamba/SSM | 状态边形成仿射/选择性递推 | 并行/分块扫描或选择性扫描计算核 |
| 线性注意力 | 前缀累加器状态边 | 满足结合律的扫描 / 分块累加器 |
| 同轮次集合交互 | 原子联合节点事件 | 分段集合计算核 / 分组注意力 |
| 配置 F 的状态融合 | 同刻多重集与前状态产生一个统一事件值 | 分段归约 + 扫描/因果批量计算核 |
| 任意黑盒转移 | 按显式事件依赖次序 | 顺序回退；只证明正确性 |

分块实现映射可以按 $(\tau,q_R(\tau),r_R(\tau),t,c,\mu)$ 排序与打包，但必须保持式 GD-12 和全部直接依赖。

### 7.9 收件箱完备性与节点内等待

本小节是运行时实现说明，不向前述数学模型增加新的集合、事件种类或定理前提。

在同步绝对时间参考中，每个内部轮次的阶段屏障直接保证收件箱分组完整，不需要额外的模型字段。

异步物理运行时若不使用全局屏障，就必须维护某种实现级记录，使节点在处理到达轮次 $\tau$ 前能够证明：所有空间前驱今后都不会再发送到达轮次不超过 $\tau$ 的消息。本文不规定该记录的数据结构，也不允许模型函数读取它；因此它不属于当前参考语义。若未来模型行为要读取这种记录，就必须先为它定义集合、事件值和依赖边。

即使完整 $\mathbf U_v$ 已一次性交给节点，状态边仍可能形成顺序依赖。分块算子可以使用批量化映射、扫描、带掩码的批量计算核，或在没有收缩时使用节点局部顺序循环。后者仍可满足 GD-12，但其节点局部关键路径长度可能与 $\mathbf U_v$ 的记录数成正比。

如果生成 $\mathbf U_v$ 必须先读取 $v$ 自己尚未产生的输出、沿空间环返回的消息，或未纳入事件图的共享可变选择器状态，则节点拓扑序分解失败。本页的空间 DAG、状态唯一持有与仅向前路由正是用于排除这类循环就绪依赖。

## 8. 流式调度与节点拓扑序分块调度

### 定义 8.1：绝对时间流式调度

定义封闭执行的最后绝对轮次：

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
\qquad
N=|V|,
\qquad
\pi\in V^N,
$$

满足对每个 $v\in V$：

$$
\operatorname{occ}(\pi,v)=1,
$$

并且：

$$
(v_i,v_j)\in E
\quad\Longrightarrow\quad
i<j.
$$

### 引理 8.2a：有限 DAG 存在拓扑序

定义 1.1 的每个有限 DAG 都至少存在一个定义 8.2 意义下的拓扑序。

**证明。**

先证明任意有限非空 DAG 至少有一个入度为零的节点。反设每个节点都有入边。从任意节点 $v_0$ 开始，依次选择满足 $(v_{j+1},v_j)\in E$ 的节点 $v_{j+1}$。因为 $V$ 有限，这个无限序列中必有两个位置取到同一节点，从而在 $G$ 中得到有向环，与定义 1.1 矛盾。

对 $|V|$ 做归纳。当 $|V|=1$ 时，唯一节点组成拓扑序。设结论对节点数小于 $N$ 的有限 DAG 成立。对 $|V|=N$ 的 DAG，取一个入度为零节点 $v_1$，删除 $v_1$ 及其出边，得到节点数 $N-1$ 的有限 DAG。由归纳假设，剩余节点存在拓扑序 $(v_2,\ldots,v_N)$。因为没有边指向 $v_1$，序列 $(v_1,v_2,\ldots,v_N)$ 满足定义 8.2。

<div class="qed" aria-label="证毕">∎</div>

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
7. 路由只沿 $E$ 前进、满足定义 6.2 的逐槽位前缀因果条件且是确定函数；任何可变路由状态都由唯一节点持有，并包含在该节点事件/值与分块契约中。
8. 事件图满足定义 7.2 的事件值依赖完备性。
9. 每个节点的分块算子满足式 GD-12，并比较完整提交轨迹。
10. 执行满足引理 4.6 的有限事件条件。

则节点拓扑序分块调度与绝对时间流式调度产生完全相同的：

- 每个节点的带时间戳的收件箱。
- 每个输入事件和常规节点事件的状态输入记录。
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

若每个节点的联合算子满足式 [[#^eq-joint-ordered-equivalence|GD-10]]，并且联合选择器与逐记录选择器满足式 [[#^eq-selector-fold-compatibility|GD-10S]]，则配置 J 的分块执行、配置 O 的分块执行与配置 O 的流式参考三者等价。

**证明。**

由命题 5.8，每个时间戳分组上的联合转移与有序转移产生相同局部输出记录和后状态。由式 GD-10S，每个对应局部输出记录又选择相同空间边；定义 6.3 的派发函数因此产生相同消息。对每个节点的时间戳流归纳，可得两种节点参考转导器的式 GD-E2 六类产物全部相同。再分别应用推论 8.5 与推论 8.6。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.8：等长路径模型是本定理的特殊情形

若对每个节点 $v$，存在唯一 $d(v)$ 使：

$$
\Lambda(v)=\{d(v)\},
$$

则任意路径计时见证 $(t,p)$ 到达空间节点 $v$ 的轮次唯一为 $Rt+d(v)$。因此，不同输入位置 $t\neq t'$ 的两个路径计时见证不会在同一 $v$、同一到达轮次相遇。对配置 O/J 中从输入开始始终保留 `owner=t` 的消息分支，这进一步推出不同 `owner` 的消息不会同刻汇聚。定理 8.4 仍然成立；配置 F 的后继消息可以改标 `owner`，故不把上述 `owner` 结论外推到 F。

**证明。**

由式 GD-2.1，任意从输入位置 $t$ 出发并实际到达 $v$ 的消息分支，其空间路径都有 $\tau=Rt+d(v)$。若 $t\neq t'$：

$$
Rt+d(v)
\neq
Rt'+d(v),
$$

所以不同输入位置的路径计时见证不能在同一空间节点同刻汇聚。配置 O/J 的归属保持结论由 $\operatorname{owner}=t$ 得到；调度等价结论直接由定理 8.4 得到。

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
\left|\{\tau\in\mathbb T_L\mid I_{v,\tau}\neq 0_{\mathcal R_v}\}\right|,
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

定义非负实数集合：

$$
\mathbb R_{\geq 0}
=
\{x\in\mathbb R\mid x\geq 0\}.
$$

对固定输入和执行，以及每个节点 $v\in V$，给定：

- 有限操作集合 $\mathcal O_v$。
- 操作直接依赖关系 $\mathcal D_v^{\mathrm{op}}\subseteq\mathcal O_v\times\mathcal O_v$，并要求 $(\mathcal O_v,\mathcal D_v^{\mathrm{op}})$ 无有向环。
- 操作成本函数 $w_v:\mathcal O_v\to\mathbb R_{\geq0}$。

定义操作 DAG 中的有限有向路径集合 $\mathsf{OpPath}_v$：其元素是有限序列 $(o_0,\ldots,o_k)$，其中 $k\in\mathbb N$、$o_i\in\mathcal O_v$，并且对每个 $i\in[k]$ 都有 $(o_i,o_{i+1})\in\mathcal D_v^{\mathrm{op}}$。

定义节点工作量函数 $W:V\to\mathbb R_{\geq0}$：

$$
W(v)
=
\sum_{o\in\mathcal O_v}w_v(o).
$$

定义节点并行跨度函数 $P:V\to\mathbb R_{\geq0}$：

$$
P(v)
=
\begin{cases}
0,&\mathcal O_v=\varnothing,\\
\displaystyle
\max_{(o_0,\ldots,o_k)\in\mathsf{OpPath}_v}
\sum_{i=0}^{k}w_v(o_i),
&\mathcal O_v\neq\varnothing.
\end{cases}
$$

对 $v\in V$，简写：

$$
W_v\in\mathbb R_{\geq 0},
\qquad
P_v\in\mathbb R_{\geq 0}.
$$

因此 $W_v$ 是全部操作成本之和，$P_v$ 是操作依赖 DAG 中带权路径成本的最大值。二者都是性能见证，不属于定理 8.4 的正确性结论。

### 命题 9.3：粗粒度节点拓扑序工作量/并行跨度上界

给定：

$$
W_{\mathrm{transport}},
W_{\mathrm{out}},
W_{\mathrm{graph}}
\in\mathbb R_{\geq 0},
$$

分别表示全部已派发消息的序列化、传输、合并与物化工作量，全部固定读出的工作量，以及节点拓扑序调度的总工作量。则：

$$
W_{\mathrm{graph}}
\leq
\sum_{v\in V}W_v
+W_{\mathrm{transport}}
+W_{\mathrm{out}}.
\tag{GD-13}
$$
^eq-general-dag-work

再给定函数：

$$
C^{\mathrm{sched}}:V\to\mathbb R_{\geq0},
$$

并简写 $C^{\mathrm{sched}}(v)=C_v^{\mathrm{sched}}$；它表示未包含在 $P_v$ 中的节点间记录序列合并、传输与调度器并行跨度。给定 $P_{\mathrm{out}},P_{\mathrm{graph}}\in\mathbb R_{\geq0}$，分别表示读出阶段与全图执行的并行跨度。若无依赖节点可并行，则：

$$
P_{\mathrm{graph}}
\leq
\max_{p\in\mathsf{Path}_G(\cdot,\cdot)}
\sum_{v\in p}
\bigl(P_v+C_v^{\mathrm{sched}}\bigr)
+P_{\mathrm{out}},
\tag{GD-14}
$$
^eq-general-dag-span

其中 $v\in p$ 表示节点 $v$ 是路径序列 $p$ 的某个坐标。

**证明。**

这里 $W_v$ 已包含节点局部收件箱聚合、转移、路由，以及输入节点对注入记录的处理。消息载荷大小、跨设备通信、全局排序或非线性索引构建的成本全部计入 $W_{\mathrm{transport}}$；固定读出函数 $\rho_z$ 与输出物化的全部成本计入 $W_{\mathrm{out}}$。把三类互不重叠的工作量相加即得式 GD-13。

分块调度的节点级依赖图就是空间 DAG。任意节点计算关键路径对应其中一条有向路径；沿该路径累加每个节点的分块并行跨度与调度开销，再加入输出读出提取的并行跨度，得到式 GD-14。

<div class="qed" aria-label="证毕">∎</div>

这个命题解释了“一般 DAG 仍可能支持高性能 chunk prefill”的准确含义：

- 图级顺序深度由空间关键路径决定，而不是由 `token` 数直接决定。
- 但若在一族增长的输入块上，某个节点的 $P_v$ 与其事件数 $M_v$ 成线性比例，且没有扫描或批量收缩，`token` 轴顺序链只是被封装进节点计算核，并没有消失。
- 若 $M$ 本身因扇出指数增长，即使并行跨度较小，总工作量与内存占用仍不可接受。

### 定义 9.4：固定来源消息槽位

给定常数：

$$
K\in\mathbb N_{>0}.
$$

定义来源槽位集合：

$$
\mathsf{Slot}_{L,K}
=
[L]\times[K].
$$

其中 $a=(b,q)\in\mathsf{Slot}_{L,K}$ 的第一个坐标 $b$ 是来源位置索引，第二个坐标 $q$ 是该来源位置的槽位索引。固定一次有限执行及其实际消息集合 $\mathcal M$。一个槽位赋值是函数：

$$
\sigma:\mathcal M\to\mathsf{Slot}_{L,K}.
$$

对槽位 $a\in\mathsf{Slot}_{L,K}$，定义：

$$
\mathcal M_a
=
\{m\in\mathcal M\mid\sigma(m)=a\}.
$$

严格槽位语义由下面的序列条件定义。对每个 $a\in\mathsf{Slot}_{L,K}$：

- 若 $\mathcal M_a=\varnothing$，不增加条件。
- 若 $\mathcal M_a\neq\varnothing$，则存在唯一 $n_a\in\mathbb N_{>0}$ 和至少一个消息序列

$$
\mathbf m_a
=
(m_0,\ldots,m_{n_a-1})
\in\mathcal M_a^{n_a},
$$

满足下列三个条件：

1. 对任意不同的 $i,j\in[n_a]$，有 $m_i\neq m_j$。
2. $\mathcal M_a=\{m_i\mid i\in[n_a]\}$。
3. 对每个满足 $i+1\in[n_a]$ 的 $i$，有 $m_i\in\operatorname{dom}(\operatorname{consumer})$，并且：

$$
\operatorname{producer}(m_{i+1})
=
\operatorname{consumer}(m_i).
$$

条件 1--3 就是本文“同一槽位形成一条有限消息链”的完整数学含义。它排除同一槽位的分叉、断开后重新开始和两个互不相连的初始化链；不同槽位仍可被同一个事件共同消费。

来源位置坐标 $b$ 不随后续 `owner` 或 `frontier` 提升而改变。实现可以把 $\sigma(m)$ 编码为元数据 $\operatorname{meta}(m)$ 的一个坐标，但数学定义依赖的是函数 $\sigma$，而不是“元数据里有一个字段”这句话。

> [!note] 来源位置、`owner` 与 `frontier` 仍是三个对象
> 来源位置 $b$ 记录槽位最初由哪个输入位置创建，终生不变；`owner` 记录当前消息使用哪个输入位置作为归属索引，配置 F 可以提升它；`frontier` 记录当前数值依赖的输入前缀上界。三者相等是常见初始状态，但不是一般不变量。

对每个输入事件或常规节点事件 $e$，定义该事件的槽位派发关系：

$$
A_e^{\mathrm{slot}}
=
\left\{
(\sigma(m),(\operatorname{src}(m),\operatorname{dst}(m)))
\ \middle|
\begin{array}{l}
m\in\mathcal M,\\
\operatorname{occ}(\operatorname{outbox}(\nu(e)),m)>0
\end{array}
\right\}
\subseteq
\mathsf{Slot}_{L,K}
\times
\operatorname{Out}(\operatorname{loc}(e)).
$$

要求对任意 $a\in\mathsf{Slot}_{L,K}$，至多存在一个空间边 $d\in\operatorname{Out}(\operatorname{loc}(e))$ 使 $(a,d)\in A_e^{\mathrm{slot}}$。因此同一个事件不能把同一个槽位复制到两条空间边；逐消息的 $\sigma$ 值与事件出站消息序列已经足以重建并验证关系 $A_e^{\mathrm{slot}}$。

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

对每个非空槽位 $a$，定义 9.4 给出消息序列 $\mathbf m_a=(m_0,\ldots,m_{n_a-1})$。相邻消息满足 $\operatorname{producer}(m_{i+1})=\operatorname{consumer}(m_i)$，所以 $m_i$ 的目标空间节点就是 $m_{i+1}$ 的源空间节点。由此，这些消息的空间边首尾相接，并且只沿 DAG $G$ 前进；因此该消息链不能两次到达同一空间节点，节点访问次数不超过 $|V|$。每个来源位置 $b$ 恰有 $K$ 个可用槽位 $(b,q)$，所以这些槽位的节点访问次数总和不超过 $K|V|$。

每个按归属 `token` 划分的常规事件至少消费一条消息；给每个事件选择其消费消息集合中标识符在 $<_{\mathsf{MID}}$ 下最小的消息。由于 $\operatorname{id}$ 在实际消息集合上是单射，这个消息唯一；又由于 $\operatorname{consumer}$ 是函数，不同事件不会选择到同一个消息，所以得到一个从按归属划分的常规事件集合到 $\mathcal M$ 的单射。因果前沿提升只改变消息的 `owner` 投影，不改变 $\sigma$。因此事件数不超过全部槽位消息数，也不超过上述全部槽位节点访问次数；对 $L$ 个来源位置求和得到式 GD-15。

<div class="qed" aria-label="证毕">∎</div>

固定来源槽位不是唯一的稀疏设计，但它给出一个不依赖空间层级或归属提升、也不需要跨 `token` 在线计数器的明确上界。若改为“每个事件独立选择分数最高的 $K$ 条出边”，最坏事件数可能随 DAG 深度指数增长，不能称为超稀疏保证。

## 10. 空间/时间均衡与选择器配置

### 定义 10.1：空间节点访问负载

在固定槽位语义配置中，定义访问指示函数：

$$
a:\mathsf{Slot}_{L,K}\times V\to\{0,1\},
$$

并对 $(b,q)\in\mathsf{Slot}_{L,K}$ 与 $v\in V$ 规定：

$$
a((b,q),v)
=
\begin{cases}
1,&\text{存在 }m\in\mathcal M
\text{ 满足 }\sigma(m)=(b,q)
\text{ 且 }\operatorname{dst}(m)=v,\\
0,&\text{否则}.
\end{cases}
$$

后文把 $a((b,q),v)$ 简写为 $a_{b,q,v}$。

定义长度为 $L$ 的节点负载函数：

$$
n^{(L)}:V\to\mathbb N,
$$

$$
n^{(L)}(v)
=
\sum_{b\in[L]}\sum_{q\in[K]}a_{b,q,v}.
\tag{GD-16}
$$
^eq-general-node-load

后文把 $n^{(L)}(v)$ 简写为 $n_v^{(L)}$。

若不采用槽位语义，可以把 $n_v^{(L)}$ 改为到达 $v$ 的、按归属 `token` 划分的事件数，但必须同时报告事件复制数量。

### 定义 10.2：当前 LH 在线计数选择器的抽象递推

给定三个非空集合：隐藏表示摘要集合 $\mathcal H$、控制状态集合 $\mathcal Q$ 与硬路由结果集合 $\mathcal R_{\mathrm{route}}$，以及确定函数：

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

给定有限事件数 $J\in\mathbb N_{>0}$、隐藏摘要序列：

$$
H_{0:J}=(H_0,\ldots,H_{J-1})\in\mathcal H^J,
$$

以及初始控制状态 $Q_0\in\mathcal Q$。递归定义控制状态序列与路由结果序列：

$$
Q_{0:J+1}=(Q_0,\ldots,Q_J)\in\mathcal Q^{J+1},
$$

$$
R_{0:J}=(R_0,\ldots,R_{J-1})\in\mathcal R_{\mathrm{route}}^J,
$$

使对每个 $j\in[J]$：

$$
R_j=\rho(H_j,Q_j),
$$

$$
Q_{j+1}=U(Q_j,R_j).
$$

在当前 LH 实现的对应关系中，$Q_j$ 的具体数据结构含有 `affectcount/selectcount` 坐标；这个实现映射不参与命题 10.3。上述递推本身形成值依赖：

$$
Q_0\to R_0\to Q_1\to R_1\to\cdots.
$$

若 $j$ 沿 `token` 轴或事件轴增长，且组合转移不具有已证明的扫描或批量结构，就形成逐步揭示的自适应控制链。命题 10.3 只证明该链的直接依赖代价；本文不在这里额外主张一般 oracle 模型下的复杂度下界。

### 命题 10.3：强在线反馈的依赖代价

取两个不同符号 $\mathtt q$ 与 $\mathtt r$。

定义有限有向图：

$$
D_J^{\mathrm{ctrl}}
=
(V_J^{\mathrm{ctrl}},E_J^{\mathrm{ctrl}}),
$$

其中：

$$
V_J^{\mathrm{ctrl}}
=
\bigl(\{\mathtt q\}\times[J]\bigr)
\cup
\bigl(\{\mathtt r\}\times[J]\bigr),
$$

$$
E_J^{\mathrm{ctrl}}
=
\{((\mathtt q,j),(\mathtt r,j))\mid j\in[J]\}
\cup
\{((\mathtt r,j),(\mathtt q,j+1))
\mid j+1\in[J]\}.
$$

顶点 $(\mathtt q,j)$ 表示值 $Q_j$ 可用，顶点 $(\mathtt r,j)$ 表示值 $R_j$ 可用。则 $D_J^{\mathrm{ctrl}}$ 含有长度为 $2J-1$ 的有向路径：

$$
(\mathtt q,0)
\to(\mathtt r,0)
\to(\mathtt q,1)
\to(\mathtt r,1)
\to\cdots
\to(\mathtt q,J-1)
\to(\mathtt r,J-1).
$$

因此，若每个顶点代表一个单位时长且不可再分解的参考原语，任何保持这些直接依赖边的调度，其并行跨度至少为 $2J$；若只按边数计路径长度，则该路径长度为 $2J-1$。

**证明。**

由 $R_j=\rho(H_j,Q_j)$，值 $R_j$ 读取 $Q_j$，所以 $((\mathtt q,j),(\mathtt r,j))\in E_J^{\mathrm{ctrl}}$。由 $Q_{j+1}=U(Q_j,R_j)$，值 $Q_{j+1}$ 读取 $R_j$，所以 $((\mathtt r,j),(\mathtt q,j+1))\in E_J^{\mathrm{ctrl}}$。按 $j=0,\ldots,J-1$ 交替连接这些边，就得到所列路径。路径含 $2J$ 个单位时长顶点，任意合法调度都必须保持这些顶点的先后次序，所以并行跨度至少为 $2J$。

<div class="qed" aria-label="证毕">∎</div>

如果 $\rho$ 与 $U$ 的组合具有可扫描的紧凑表示，可以用一个新的批量原语替换上述逐事件原语图；但那需要另外证明新原语与这组递推等价，不能由命题 10.3 自动得到。

### 10.4 与 `prefill` 兼容的均衡层

在严格语义配置中，均衡拆成以下互不替代的层：

| 层 | 方法 | 是否进入逐事件前向状态 |
| --- | --- | --- |
| 结构上界 | 固定来源槽位、有限出度、静态可用性 | 否 |
| 静态容量 | 边/节点偏置、设备容量权重、拓扑分区 | 否 |
| 确定性时间分散 | $d_{v\to u}(t,\tau)$ | 否 |
| 训练期均衡 | 节点负载 / 时间窗口损失 | 只影响梯度 |
| 在线硬均衡 | 持久路由计数器 | 是；通常形成控制链 |

定义正实数集合 $\mathbb R_{>0}=\{x\in\mathbb R\mid x>0\}$。给定目标节点容量权重函数：

$$
\pi:V\to\mathbb R_{>0},
$$

并简写 $\pi(v)=\pi_v$。要求：

$$
\pi_v>0,
\qquad
\sum_{v\in V}\pi_v=1,
$$

定义总访问负载：

$$
N_L^{\mathrm{load}}
=
\sum_{u\in V}n_u^{(L)}
\in\mathbb N.
$$

当 $N_L^{\mathrm{load}}>0$ 时，定义归一化实际负载函数：

$$
\widehat p^{(L)}:V\to[0,1],
$$

并简写 $\widehat p^{(L)}(v)=\widehat p_v^{(L)}$。规定：

$$
\widehat p_v^{(L)}
=
\frac{n_v^{(L)}}{N_L^{\mathrm{load}}}.
$$

定义空间均衡损失：

$$
\mathcal L_{\mathrm{space}}
=
\begin{cases}
0,&N_L^{\mathrm{load}}=0,\\
\displaystyle
\sum_{v\in V}(\widehat p_v^{(L)}-\pi_v)^2,
&N_L^{\mathrm{load}}>0.
\end{cases}
\tag{GD-17}
$$
^eq-general-space-balance-loss

给定窗口宽度 $B\in\mathbb N_{>0}$，定义绝对时间窗口函数：

$$
\mathsf{Window}_B:\mathbb N\to 2^{\mathbb N},
$$

并对每个 $j\in\mathbb N$ 规定：

$$
\mathsf{Window}_B(j)
=
\{jB,\ldots,(j+1)B-1\},
$$

后续若要定义时间均衡损失，应先把“某节点事件的到达轮次”定义成函数，再对落入 $\mathsf{Window}_B(j)$ 的事件计数。本文在没有给出该计数函数与损失公式前，不引入额外的 $\mathcal L_{\mathrm{time}}$ 符号。

### 设计分类 10.5：跨 `token` 硬容量约束的三种基本选择

本小节给出工程设计空间的分类，不声称下面三项已经构成某个形式化选择器模型中的集合论完备分类，因此不作为后续定理前提。

给定硬容量 $C\in\mathbb N$。若要求任意输入上、任意时间窗口内节点 $v$ 的硬准入不超过 $C$，而多个归属 `token` 都可能选择 $v$，则精确选择器至少采用以下一种机制：

1. 用静态资格约束或配额预先限制可选归属 `token` / 槽位。
2. 联合观察一个已知的归属 `token` / 事件集合后做指派。
3. 在线维护已使用容量，让后续决策读取此前的准入结果。

第二种机制是否允许取决于参考语义：配置 J/F 可以在同一时间戳分组内使用它，但不能免费跨越尚未形成的未来分组。第三种机制形成在线控制链。第一种最容易保持原生兼容严格 `prefill`，但会限制内容路由的自由度。

直观理由是：若资格未预先限制，当超过 $C$ 个候选同时或先后希望进入 $v$ 时，选择器必须依据其他候选拒绝其中一部分；它可以联合观察已知集合后决定，也可以按到达顺序读取已用容量。若后续需要把这段分类提升为定理，必须先定义候选集合、信息可见性、选择器状态和“机制等价”的精确集合。

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
| 选择器前沿 | 固定槽位的 $a_{v,\eta,j}$ | 改变声明前沿之后的输入后缀 | 选边集合与槽位存在性不变 |
| 联合对比有序 | 两套参考 | 直接比较 | 只在式 GD-10 与 GD-10S 同时成立时期待全部产物相等 |
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
5. **直接依赖与事件值重建已成为前提**：消息、状态、读出与自回归边界依赖均由关系显式给出；每个事件值还必须由事件头、直接前驱值和已类型化边界参数重建。
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
- 节点转移是否满足式 GD-10，选择器是否同时满足式 GD-10S。
- 是否采用定理 5.13 的因果前沿提升不变量。

#### 风险三：`owner` / `frontier` 不能决定产生、消费与事件依赖关系

相同的 `owner` / `frontier` 组合可以经不同路径、不同定义 9.4 的来源槽位、不同绝对时间多次到达同一节点。因果前沿只给出输入前缀依赖上界，不决定定义 4.2a 的函数 $\operatorname{producer}$、$\operatorname{consumer}$，也不决定定义 7.2 的关系 $\mathcal A_L^P$。因此执行记录必须保存事件标识符、消息标识符、到达时间戳、源节点、目标节点、可选来源槽位、两个消息生命周期函数和事件依赖边；不能用 `owner` / `frontier` 两个投影替代这些对象。

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

要得到可接续 `decode` 的 `prefill` 交接状态，下一阶段必须先选择一个非空集合 $\mathcal S_R$，其元素拟表示一个周期边界上的完整延续状态，再构造单周期转移函数：

$$
\mathcal T_R:
X\times\mathcal S_R
\to
Y\times\mathcal S_R
$$

对任意初始延续状态 $S_0\in\mathcal S_R$ 与输入序列 $x_{0:L}\in X^L$，递归定义：

$$
(y_t,S_{t+1})
=
\mathcal T_R(x_t,S_t),
\qquad t\in[L].
$$

并把由该递推唯一确定的函数记为：

$$
\operatorname{Fold}_{\mathcal T_R}^L:
X^L\times\mathcal S_R
\to
Y^L\times\mathcal S_R,
$$

$$
\operatorname{Fold}_{\mathcal T_R}^L(x_{0:L},S_0)
=
(y_{0:L},S_L).
$$

未来构造必须使 $\mathcal S_R$ 显式包含全部节点状态与跨边界在途消息，定义每个边界切面的状态快照，并证明连续 $L$ 个周期的事件执行正好等于上述 $\operatorname{Fold}_{\mathcal T_R}^L$。该嵌入定理是把本页结果提升为统一模型级 `prefill == decode` 定理的下一步。

### 13.3 当前推荐的最小实现顺序

1. 实现固定 $R$、六阶段边界次序与每周期强制读出。
2. 分离稳定 `event_id`、事件头与事件依赖：事件头包含 `(kind, location, timestamp, owner_support, frontier)`；配置 O 的同刻顺序直接由 $(\tau,t)$ 定义，配置 J/F 则各自建立一个联合事件；`event_id` 只用于身份，不能用单个 `token`、物理创建次序或任意编号大小代替依赖边。
3. 实现定义 4.1 的消息八元组 `(message_id, owner, frontier, arrival_timestamp, src, dst, metadata, payload)`，并显式保存定义 4.2a 的 `producer(message_id)` 与部分函数 `consumer(message_id)`；若启用固定槽位语义，再额外实现定义 9.4 的函数 $\sigma$。
4. 实现一般 DAG 绝对时间标量参考，并输出完整的事件、消息来源图和状态提交账本。
5. 实现配置 O 的节点拓扑序分块执行器，并对齐式 GD-E2 的六类产物与全部 $y_t$。
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
- 每个有限给定序列执行在本文条件下具有类型化事件 DAG、显式消息/状态/读出依赖与事件值重建条件。
- 消息的 `owner` 在非等长路径中是必要的归属消歧字段，但它不能决定 $\operatorname{producer}$、$\operatorname{consumer}$ 或 $\mathcal A_L^P$。
- 配置 O、J、F 都可以分别建立调度等价定理。
- 满足 GD-10 的联合转移与满足 GD-10S 的联合选择器可以共同批量实现配置 O 的完整语义。
- 配置 F 在定理 5.13 的条件下保持显式 `token` 前缀依赖上界。
- 固定来源槽位给出一个兼容归属提升的超稀疏事件上界。

当前不能主张：

- 任意一般 DAG、任意节点计算核都有高性能 `prefill`。
- 配置 J 与配置 O 在未同时证明式 GD-10 和 GD-10S 时语义相同。
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
