---
type: mathematical-specification
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - prefill-decode
  - event-dag
  - allocator
---

# Tide 数学基础

> [!summary] 本页定位
> 本页是 Tide 正向数学主线的唯一正式入口。它依次定义单步 transition、顺序 fold、kernel 级 chunk 正确性、有限 logical event DAG，以及显式 allocator 的一般空间 DAG。自适应路由的通用下界独立见 [[adaptive-routing-prefill-lower-bound]]。

> [!important] 证明状态
> StepTransition、B0 kernel family 与一般空间 DAG 的既有定理按原证明保留。显式 allocator 的拓扑序构造只证明空间遍历次数不随 chunk 长度增长；时间分块组合律仍是额外义务，不能由空间 DAG 自动推出。

## 第一部分：StepTransition、kernel 与 logical event DAG



> [!summary] 本页定位
> 本部分只处理 `StepTransition`、`prefill`、`decode`、chunk prefill 与 kernel 优化的数学定义。实现对象、LH 映射、phase 工程约束见 [[tide-runtime-validation-and-status#第一部分：StepTransition 实现规范|StepTransition 实现规范]]。

> [!note] 写作与证明约定
> 本页按“概念与符号先于使用、简单例子先于复杂架构、引理先于定理、证明不跳步”的顺序推进。进入定义或证明的每个对象都必须先声明为集合、集合元素、函数、部分函数、关系、有限序列、多重集或有限元组；函数给出定义域和值域，关系给出所在笛卡尔积。直观说明若不承担数学前提，必须保持直白，不能用未定义术语模拟精确性。CPU ISA、编译器、SSA、内存模型等外部概念只作为参考谱系，见 [[tide-background-history-and-references#第一部分：ISA、编译器与 dataflow 理论谱系|ISA、编译器与 dataflow 理论谱系]]；它们不替代本页的数学证明，本页也不从其他文档隐式导入正式定义或定理。

> [!note] 中英文术语
> `token`、`prefill`、`decode`、`logits` 以及数学符号、公式字段、代码接口、固定缩写和模型专名保留英文，其余解释性正文优先使用中文。本文中的 `token` 指输入序列位置上的离散输入单位，不表示消息、事件或计算轨迹；输入位置、输入值、空间节点、消息和事件是不同类型的对象。

> [!important] 对象层级约定
> 本页区分输入位置、输入值、空间节点与逻辑事件：$t$ 是输入位置，$x_t$ 是输入值，二者都不是计算轨迹；空间图的节点是可复用计算位置，逻辑事件 DAG 的顶点是一次有限执行中的事件。数学符号 $\mathcal S$ 表示在相邻 transition 调用之间传递的 **transition-state 容器**；其中只有旧值能够影响下一步语义的分量才称为**持久上下文**。B0 为统一表达而把会被 `Init` 无条件覆盖的当前步 activation slot 也放进 $\mathcal S$，但它不承载跨步历史。临时工作区、局部输出记录、消息和事件值若不属于返回的 $\mathcal S$，则不自动成为 transition state 或持久上下文。本页需要的这些区分均在本页相应定义中重新给出，不以其他文档为定义来源。

> [!roadmap] 当前形式化边界
> 第一部分定义顺序折叠、分块正确性、语义商、有限 logical event DAG、主力 kernel family 与步骤模拟；第二部分定义可从任意全局位置开始的一般空间 DAG 窗口执行；第三部分给出可选归属与因果证书；第四部分规定有限事件展开和 zero-delay 强连通分量的 strict-core 边界。一般动态事件生成、任意有环拓扑和定点 kernel 仍未形成统一的高性能 prefill 定理。

> [!important] 证否边界
> 本页以构造性 correctness 为主。任意黑盒自适应 routing 在 exact、work-efficient 前提下为何不能获得次线性 adaptive-depth prefill，见独立数学文档 [[adaptive-routing-prefill-lower-bound]]。该下界不自动等价于具体 LH selector 的不可能性结论。

阅读本页时，所有结论按以下强度区分：

- `定义`：约定数学对象的含义。
- `例`：帮助理解定义，不承担一般性证明。
- `引理 / 定理`：在明确前提下给出可证明结论。
- `高性能实现见证`：说明已有实现结构可承载该数学对象，不等于 complexity theorem。
- `工程验证`：检查具体实现，不自动提升为一般数学定理。
- 定义、引理、定理、推论与例使用标题编号；引用时优先链接到对应标题。
- 只有会被正文交叉引用的公式才编号；显示编号使用 `\tag{...}`，稳定锚点使用语义化 block ID `^eq-...`。
- 证明统一以“**证明。**”开始，并以右对齐的 `∎` 结束；不同时重复使用“证毕”。

### 0. 记号约定

#### 定义 0.1：自然数与区间

令：

$$
\mathbb{N}=\{0,1,2,\ldots\}
$$

令：

$$
\mathbb{N}_{>0}=\{1,2,3,\ldots\}
$$

对任意 $L\in\mathbb{N}$，定义半开下标集合：

$$
[L]=\{0,1,\ldots,L-1\}
$$

当 $L=0$ 时，$[L]=\varnothing$。

#### 定义 0.2：有限序列

对任意集合 $A$ 与长度 $L\in\mathbb{N}$，记：

$$
A^L=\{a:[L]\to A\}
$$

因此，$A^L$ 是一个集合：它的元素是从有序有限下标集 $[L]$ 到 $A$ 的函数。

若 $a\in A^L$，定义：

$$
a_t=a(t),\quad t\in[L]
$$

因为 $[L]$ 有自然顺序，所以可把函数 $a:[L]\to A$ 规范地写成长度为 $L$ 的 tuple：

$$
a_{0:L}=(a_0,\ldots,a_{L-1})
$$

这里没有单射约束。若 $t\neq t'$，可以有 $a_t\neq a_{t'}$，也可以有 $a_t=a_{t'}$。

空序列记作：

$$
a_{0:0}=()
$$

#### 定义 0.3：有限索引族

若 $I$ 是有限集合，记：

$$
A^I=\{f:I\to A\}
$$

因此，$A^I$ 也是一个集合：它的元素是以 $I$ 为索引的一族 $A$ 中元素。

若 $f\in A^I$，定义：

$$
f_i=f(i),\quad i\in I
$$

除非额外给 $I$ 指定顺序，否则 $A^I$ 不是 list / tuple，而只是 indexed family。这里同样没有单射约束；不同索引可以映射到同一个 $A$ 中元素。

#### 定义 0.4：有向边的 source / destination

若 $G=(V,E)$ 是有向图，且 $e=(u,v)\in E$，定义：

$$
\operatorname{src}(e)=u
$$

$$
\operatorname{dst}(e)=v
$$

对任意节点 $v\in V$，定义其入边集合：

$$
E^{-}(v)=\{e\in E\mid \operatorname{dst}(e)=v\}
$$

#### 定义 0.5：有限依赖族的乘积空间

若 $I$ 是有限集合，且对每个 $i\in I$ 给定集合 $A_i$，定义有限乘积：

$$
\prod_{i\in I}A_i
=
\{a:I\to \bigcup_{i\in I}A_i\mid a_i\in A_i,\ i\in I\}
$$

若 $I=\varnothing$，则：

$$
\prod_{i\in I}A_i=\{()\}
$$

也就是说，空依赖集合的输入是唯一的空 tuple。

### 1. Transition 与顺序 Fold

这一节先定义最基础的 transition 与 fold。后文所有 `prefill = decode fold` 都引用这里的定义。

#### 定义 1.1：单步 transition system

给定三个集合：

$$
X=\text{input value space}
$$

$$
Y=\text{output/readout space}
$$

$$
\mathcal{S}=\text{persistent state space}
$$

一个单步 transition system 是函数：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

这里 $x\in X$ 是一次单步输入值，不是输入位置、消息、事件或计算轨迹。对长度为 $L$ 的输入序列，位置索引仍记为 $t\in[L]$，位置 $t$ 的输入值记为 $x_t$；即使 $x_t=x_{t'}$，$t\neq t'$ 仍表示两次不同的输入出现。

对任意 $x\in X$，定义：

$$
\mathcal{T}_x:\mathcal{S}\to Y\times\mathcal{S}
$$

其中：

$$
\mathcal{T}_x(S)=\mathcal{T}(x,S)
$$

#### 定义 1.2：顺序 fold

给定 transition system $\mathcal{T}$、长度 $L\in\mathbb{N}$、输入序列 $x_{0:L}\in X^L$ 与初始状态 $S_0\in\mathcal{S}$。

定义状态序列：

$$
S_0,S_1,\ldots,S_L\in\mathcal{S}
$$

以及输出序列：

$$
y_{0:L}\in Y^L
$$

满足对所有 $t\in[L]$：

$$
(y_t,S_{t+1})=\mathcal{T}_{x_t}(S_t)
$$

由于 $\mathcal{T}$ 是函数，上述 $S_{0:L+1}$ 与 $y_{0:L}$ 由 $x_{0:L}$ 和 $S_0$ 唯一确定。

定义长度为 $L$ 的顺序 fold 函数：

$$
\operatorname{Fold}_{\mathcal{T}}^L:X^L\times\mathcal{S}\to Y^L\times\mathcal{S}
$$

其中：

$$
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)=(y_{0:L},S_L)
$$

当 $L=0$ 时：

$$
\operatorname{Fold}_{\mathcal{T}}^0(x_{0:0},S_0)=((),S_0)
$$

这就是后文所谓 `fold` 的严格含义。长度 $L$ 是函数类型的一部分；若上下文中长度明确，文字说明中可省略上标，但正式公式优先写成 $\operatorname{Fold}_{\mathcal{T}}^L$。

#### 定义 1.3：Decode 语义

给定 transition system $\mathcal{T}$。对每个 $L\in\mathbb{N}$，定义长度为 $L$ 的 decode 语义为：

$$
\operatorname{Decode}_{\mathcal{T}}^L(x_{0:L},S_0)
:=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

也就是说，decode 是逐 token 应用同一个单步 transition。

#### 定义 1.4：顺序 prefill 语义

给定 transition system $\mathcal{T}$。对每个 $L\in\mathbb{N}$，定义长度为 $L$ 的最保守顺序 prefill 语义为：

$$
\operatorname{Prefill}^{seq,L}_{\mathcal{T}}(x_{0:L},S_0)
:=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

这里的 `seq` 明确表示它只是顺序 fold，不代表高性能并行 prefill。

#### 定理 1.5：顺序 prefill 与 decode 等价

对任意 transition system $\mathcal{T}$、任意 $L\in\mathbb{N}$、任意 $x_{0:L}\in X^L$、任意 $S_0\in\mathcal{S}$：

$$
\operatorname{Prefill}^{seq,L}_{\mathcal{T}}(x_{0:L},S_0)
=
\operatorname{Decode}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

**证明。**

二者都被定义为：

$$
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

因此等价。

<div class="qed" aria-label="证毕">∎</div>

### 2. Correctness、Semantic Contract 与等价层次

#### 定义 2.1：chunk prefill implementation

给定 transition system $\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}$。

对任意长度 $L\in\mathbb{N}$，一个 chunk prefill implementation 是函数：

$$
\mathcal{C}_L:X^L\times\mathcal{S}\to Y^L\times\mathcal{S}
$$

#### 定义 2.2：chunk prefill 正确性

称 $\mathcal{C}_L$ 对 $\mathcal{T}$ 正确，当且仅当对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$：

$$
\mathcal{C}_L(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
\tag{2.1}
$$

^eq-chunk-prefill-correctness

#### 定义 2.3：reference semantic contract

给定 transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

称四元组：

$$
(X,Y,\mathcal{S},\mathcal{T})
$$

是一个 reference semantic contract。它规定了 chunk implementation 必须复现的输入、输出、持久状态与单步状态更新语义。

因此，定义 2.2 中的 correctness 不是绝对性质，而是相对于 reference semantic contract 的性质。若 $\mathcal{T}$ 本身只把历史压缩为某个 aggregate state，则 $\mathcal{C}_L$ 只需要复现该 aggregate state；若 $\mathcal{T}$ 明确保存输入位置、逻辑轮次、阶段标签和显式来源关系，则 $\mathcal{C}_L$ 也必须保存这些记录，或证明丢弃它们不会改变该 contract 的输出与最终状态。时间标签本身不是完整 provenance。

#### 定义 2.4：transition semantic quotient

给定 fine reference transition：

$$
\mathcal{T}^{fine}:X\times\mathcal{S}^{fine}\to Y^{fine}\times\mathcal{S}^{fine}
$$

以及 coarse reference transition：

$$
\mathcal{T}^{coarse}:X\times\mathcal{S}^{coarse}\to Y^{coarse}\times\mathcal{S}^{coarse}
$$

给定状态抽象映射：

$$
\alpha:\mathcal{S}^{fine}\to\mathcal{S}^{coarse}
$$

以及输出抽象映射：

$$
\beta:Y^{fine}\to Y^{coarse}
$$

称 $\mathcal{T}^{coarse}$ 是 $\mathcal{T}^{fine}$ 关于 $(\alpha,\beta)$ 的 semantic quotient，当且仅当对所有 $x\in X$ 与 $S\in\mathcal{S}^{fine}$，若：

$$
\mathcal{T}^{fine}(x,S)=(y,S')
$$

则：

$$
\mathcal{T}^{coarse}(x,\alpha(S))=(\beta(y),\alpha(S'))
$$

也就是说，fine transition 的一步计算先执行再抽象，与先抽象再执行 coarse transition，得到同一个 coarse output 与 coarse next state。

##### 例 2.4a：完整历史 contract 与求和 contract

令输入空间为 $X=\mathbb{R}$，输出空间为 singleton $Y=\{*\}$。定义 finite-history state space：

$$
\mathcal{S}^{fine}=\bigcup_{P\in\mathbb{N}}\mathbb{R}^{P}
$$

若 $h=(h_0,\ldots,h_{P-1})\in\mathcal{S}^{fine}$，定义 append transition：

$$
\mathcal{T}^{fine}(x,h)=(*,(h_0,\ldots,h_{P-1},x))
$$

这个 fine contract 要求最终 state 保留每个输入及其顺序。

令 coarse state space 为 $\mathcal{S}^{coarse}=\mathbb{R}$，并定义：

$$
\mathcal{T}^{coarse}(x,s)=(*,s+x)
$$

定义状态抽象与输出抽象：

$$
\alpha(h_0,\ldots,h_{P-1})=\sum_{j=0}^{P-1}h_j
$$

$$
\beta(*)=*
$$

约定空和为 $0$，因此 $\alpha(())=0$。记 $h\mathbin{\|}x$ 为在有限序列 $h$ 末尾 append 元素 $x$。对任意 $x\in\mathbb{R}$ 与历史 $h$：

$$
\alpha(h\mathbin{\|}x)=\alpha(h)+x
$$

由于：

$$
\mathcal{T}^{fine}(x,h)=(*,h\mathbin{\|}x)
$$

并且：

$$
\begin{aligned}
\mathcal{T}^{coarse}(x,\alpha(h))
&=(*,\alpha(h)+x)\\
&=(*,\alpha(h\mathbin{\|}x))\\
&=(\beta(*),\alpha(h\mathbin{\|}x)),
\end{aligned}
$$

所以先执行 $\mathcal{T}^{fine}$ 再应用 $(\alpha,\beta)$，等于先应用 $\alpha$ 再执行 $\mathcal{T}^{coarse}$。由定义 2.4，$\mathcal{T}^{coarse}$ 是 $\mathcal{T}^{fine}$ 的 semantic quotient。

在 coarse contract 下，历史 $(1,2)$ 与 $(2,1)$ 都映射到 state $3$，实现无需恢复顺序 provenance；在 fine contract 下，这两个历史必须保持可区分。这个例子说明：同一个 chunk algorithm 是否正确，取决于 reference semantic contract 要求观察什么。

#### 引理 2.5：semantic quotient 保持顺序 fold

若 $\mathcal{T}^{coarse}$ 是 $\mathcal{T}^{fine}$ 关于 $(\alpha,\beta)$ 的 semantic quotient，则对任意 $L\in\mathbb{N}$、$x_{0:L}\in X^L$ 与 $S_0^{fine}\in\mathcal{S}^{fine}$，若：

$$
\operatorname{Fold}_{\mathcal{T}^{fine}}^L(x_{0:L},S_0^{fine})=(y^{fine}_{0:L},S_L^{fine})
$$

则：

$$
\operatorname{Fold}_{\mathcal{T}^{coarse}}^L(x_{0:L},\alpha(S_0^{fine}))
=
(\beta^L(y^{fine}_{0:L}),\alpha(S_L^{fine}))
$$

其中 $\beta^L$ 是逐位置应用 $\beta$ 的序列映射：

$$
\beta^L(y^{fine}_{0:L})=(\beta(y^{fine}_0),\ldots,\beta(y^{fine}_{L-1}))
$$

当 $L=0$ 时，$\beta^0(())=()$。

**证明。**

对 $L$ 归纳。$L=0$ 时，两个 fold 都返回空输出；coarse 初始状态是 $\alpha(S_0^{fine})$，结论成立。

假设长度 $L$ 成立。考虑长度 $L+1$。由归纳假设，前 $L$ 个 token 后 coarse state 等于 $\alpha(S_L^{fine})$，coarse 输出等于 $\beta^L(y^{fine}_{0:L})$。对第 $L$ 个 token，若：

$$
\mathcal{T}^{fine}(x_L,S_L^{fine})=(y_L^{fine},S_{L+1}^{fine})
$$

则由 semantic quotient 定义：

$$
\mathcal{T}^{coarse}(x_L,\alpha(S_L^{fine}))
=
(\beta(y_L^{fine}),\alpha(S_{L+1}^{fine}))
$$

因此长度 $L+1$ 的输出序列与最终状态也满足结论。

<div class="qed" aria-label="证毕">∎</div>

这个引理给出一个重要边界：对 fine contract 正确通常可推出对其 coarse quotient 正确；但只对 coarse contract 正确，不能推出对 fine contract 正确。若原 reference transition 已经是高度压缩的 coarse semantics，chunk prefill correctness 会更容易证明，但证明结论也只覆盖这个较弱 contract。

#### 定义 2.6：三个层次

本页区分三个层次：

1. 顺序 fold 等价：对每个 $L$，$\operatorname{Prefill}^{seq,L}_{\mathcal{T}}=\operatorname{Decode}_{\mathcal{T}}^L$。这是定义性等价。
2. chunk forward 等价：证明某个 $\mathcal{C}_L$ 满足定义 2.2。
3. 高性能并行 prefill：进一步要求 $\mathcal{C}_L$ 可通过并行、融合、重排或 packed layout 高效实现，同时仍满足定义 2.2。

层次 1 不推出层次 2；层次 2 不推出层次 3。

### 3. B0：标准 Factorized Graph Runtime

这一节定义简化分支 B 的基线版本。这个基线应从一开始就能自然表达 Transformer、Mamba / SSM、Linear Attention 等主流自回归模型。

B0 已经吸收了旧版本中“factorized node state”的 B1：空间节点状态从一开始就拆成可通信隐藏激活值与私有 memory/cache/state。这里的“激活值”是数值表示，不是动态节点事件的实例化。这样做的目的，是让起点本身就是高性能自回归模型熟悉的形式，而不是先定义一个过弱的 activation-only graph，再额外补 memory/cache。

B0 不包含 LH-style input/output cortex、bridge phase、selector、readout cache 或 pronounce memory。但它包含标准自回归模型需要的两个基本状态因子：

- 当前输入步在该空间节点上的可通信隐藏激活值。
- 空间节点私有的跨输入步 memory/cache/state。

#### 定义 3.1：B0 静态结构

令 $V$ 是有限非空空间节点集合，$E\subseteq V\times V$ 是空间有向边集合。

定义有向图：

$$
G=(V,E)
$$

指定输入节点与输出节点：

$$
i\in V,\quad o\in V
$$

令 $R\in\mathbb{N}_{>0}$ 为每个 external input step 内的 internal round 数。

> [!note] 固定步长 B0 与一般重叠注入模型
> 本节把一次输入的 $R$ 个内部轮次封装进单步 transition $\mathcal T^{B0}$，再按输入位置顺序做 fold；它是便于承载 Transformer/Mamba chain 的 fixed-step baseline。第二部分研究另一种窗口语义：输入位置按固定外部周期注入，长路径消息可以跨边界延续。除非 B0 state 显式保存 in-flight messages 与状态提交轨迹，否则不能把本节的 step-complete fold 与该重叠模型直接视为同一个 transition。

#### 定义 3.2：B0 空间

给定集合：

$$
X=\text{input value space}
$$

$$
A=\text{visible activation space}
$$

$$
U=\text{private node memory/cache/state space}
$$

$$
M=\text{message space}
$$

$$
Y=\text{output/readout space}
$$

定义带空消息值的消息空间：

$$
\overline{M}=M\cup\{\bot\}
$$

其中 $\bot\notin M$，表示当前内部轮次没有有效消息。这里的 $\bot$ 是一个计算核返回值，不表示发生了一个载荷为空的消息实例；B0 尚未显式展开一般 DAG 文档中的消息实例与消息标识符。

B0 的单步 transition-state 空间为：

$$
\mathcal{S}_{B0}=A^V\times U^V
$$

若 $(a,\mu)\in A^V\times U^V$，则：

- $a_v\in A$ 是空间节点 $v$ 当前可通信的隐藏激活值或 residual stream slot。
- $\mu_v\in U$ 是节点 $v$ 的私有 memory/cache/state。

对 Transformer，$\mu_v$ 可包含该层 KV cache；对 Mamba / SSM，$\mu_v$ 可包含 SSM recurrent state；对 Linear Attention，$\mu_v$ 可包含 prefix accumulator。$a_v$ 通常是当前输入步的 residual / activation slot，它虽然形式上属于单步 transition 的状态空间，但可以由每次 $\operatorname{Init}$ 清空或覆盖；它与真正跨输入步累积的 $\mu_v$ 具有不同生命周期。

因此，$(a,\mu)$ 整体是 transition 的状态参数，但只有 $\mu$ 默认属于持久上下文。若某个具体模型允许旧的 $a$ 在下一次 $\operatorname{Init}$ 前被读取，则该模型必须把这种读取写进 transition，此时相应 $a$ 分量也成为持久上下文，不能再把它当作纯当前步槽位。

#### 定义 3.3：B0 kernels

给定 step 初始化函数：

$$
\operatorname{Init}:X\times A^V\times U^V\to A^V\times U^V
$$

`Init` 负责把当前输入值写入输入锚点，并按模型语义初始化当前输入步的隐藏激活槽。典型行为是：

- 在输入空间节点写入输入 embedding。
- 清空或覆盖非输入空间节点的当前输入步隐藏激活槽。
- 保留各节点的 private memory/cache/state。

对每个 round $r\in\{1,\ldots,R\}$ 与每条边 $e\in E$，给定 edge kernel：

$$
\phi_e^r:A\times U\to \overline{M}
$$

对每个节点 $v\in V$ 与 round $r\in\{1,\ldots,R\}$，先定义该节点 mailbox 空间：

$$
\mathcal{B}_v=\overline{M}^{E^{-}(v)}
$$

给定聚合函数：

$$
\operatorname{Agg}_v^r:\overline{M}^{E^{-}(v)}\to \mathcal{B}_v
$$

以及空间节点更新计算核：

$$
\psi_v^r:A\times U\times\mathcal{B}_v\to A\times U
$$

给定 readout 函数：

$$
\rho:A\times U\to Y
$$

#### B0 与已知架构的直观对应

B0 的作用不是发明一种新 kernel，而是把“一个输入步内，状态如何沿 graph 被局部 kernel 更新”写成统一形式。许多熟知架构可以被看成 B0 的特例或近似特例。

标准表达方式一是 block-as-node chain。对一个有 $N$ 个 block 的 Transformer / Mamba，可写为：

$$
V=\{0,\ldots,N\}
$$

$$
E=\{(j,j+1)\mid j=0,\ldots,N-1\}
$$

其中 node $0$ 是 input / embedding anchor，node $1,\ldots,N$ 分别代表 $N$ 个 layer / block，输出节点为 $o=N$。若不单独计算 input anchor，读者也可以把“$N$ 个 block node”理解为主模型部分；本文公式显式保留 input anchor，因此 $|V|=N+1$。

一个输入步内运行 $R=N$ 个 round 时，信息可以沿 chain 从输入端逐步传播到输出端。标准 chain 的 round gating 可写成：对任意 $j=1,\ldots,N$、$a\in A$ 与 $\mu\in U$，

$$
\phi_{(j-1,j)}^r(a,\mu)=\bot\quad \text{when } r\neq j
$$

也就是说，第 $j$ 个 block 只在第 $j$ 个 round 接收来自上一个 block 的当前输入步隐藏激活值。尚未收到有效输入的节点，其 $\psi_v^r$ 可以是 identity / no-op。

若把一个 Transformer block 拆成 attention、FFN、norm/residual 等更细单元，也可以使用更长的 chain：

$$
|V|\approx 2N \text{ or } 3N
$$

相应地使用 $R\approx 2N$ 或 $R\approx 3N$ 个 round。此时每个非 anchor node 的 $\psi_v^r$ 对应 attention、FFN、residual/norm 或 Mamba/SSM 子模块之一，round gating 同样规定哪个子模块在当前 round 接收有效输入。

残差连接也可以在 B0 中表达，常见有两种方式：

- 把 residual stream 放入 $a_v$ 或 $\mu_v$，由 node update kernel $\psi_v^r$ 在节点内部完成 add / norm / gating。
- 把 residual / skip connection 显式写成 graph edge，例如从上游 residual source 连到下游 add node。

标准表达方式二是 block-as-node with internal substeps。此时 graph 仍是长度 $N$ 的 chain，每个 node 是一个完整 block；attention / SSM、FFN、residual、norm、cache append 等子步骤被封装在同一个 $\psi_v^r$ 内部。若后续需要把这些子步骤的 read/write/commit 顺序作为证明对象，标准做法仍是把 block 展开成更长的 B0 chain，或在实现文档中描述 node-local kernel contract。

因此，B2 不是替代 B0 chain 的主表达，也不是把 Transformer / Mamba 的 block 或子模块编号改写成 phase。B0 chain 是表达标准 Transformer / Mamba layer stack 的自然起点；B2 只用于 runtime 明确存在大范围 role / direction / visibility barrier 的情形，例如 LH / Tide 的 input、output、iobridge、oibridge、readout 等阶段。

| 架构组件 | B0 中的自然对应方式 | `prefill == decode fold` 的来源 |
| --- | --- | --- |
| Transformer attention block | $a_v$ 是当前输入步 residual activation value，$\mu_v$ 是该层 KV cache；$\psi_v^r$ 做 Q/K/V projection、KV append、causal attention、output projection；$\phi_e^r$ 抽取要传给下一层的 residual stream。 | 标准 causal attention 的 prefill 与逐 token decode 等价，前提是 causal mask 与 KV append order 一致；position information 暂不作为 attention 证明核心，若引入则必须由 decode/chunk 一致的确定性 position 函数给出。 |
| Transformer FFN / MLP block | $a_v$ 是当前输入步 residual activation value，$\mu_v$ 可为空或平凡；$\psi_v^r$ 是 FFN/MLP；$\phi_e^r$ 抽取 FFN 后 activation value。 | FFN 对 token 位置逐点作用，没有跨 token recurrence；只要输入 activation value 一致，prefill 与 decode 逐点一致。 |
| Mamba / SSM block | $a_v$ 是当前输入步 activation value，$\mu_v$ 是 SSM recurrent state；$\psi_v^r$ 做 selective state update 与输出；$\phi_e^r$ 抽取传给下一层的 activation value。 | decode 是 recurrent update；prefill 等价依赖 scan / chunk scan 实现与逐步 recurrence 等价。 |
| Linear attention block | $a_v$ 是当前输入步 activation value，$\mu_v$ 是 linear-attention accumulator；$\psi_v^r$ 更新 accumulator 并产生当前输出。 | prefill 等价依赖 accumulator 的 causal prefix 更新与逐 token update 等价。 |

这张表的用意是帮助理解符号。B0 已经把 Transformer/Mamba/Linear Attention 这类已有高性能 `prefill == decode` 实现路径的主流自回归模型纳入数学对象中；后续 B-family 层级不应再把 Transformer/Mamba 的基本 cache/state 表达能力当作新增能力，而应研究 typed edge、workspace、phase、selector、readout 等额外机制。B0 本身只定义 reference transition；具体 chunk prefill 是否高性能且正确，仍必须按定义 2.2 另行证明。

#### 定义 3.4：B0 单步 transition

定义：

$$
\mathcal{T}^{B0}:X\times (A^V\times U^V)\to Y\times (A^V\times U^V)
$$

对任意 $x\in X$ 与 $(a,\mu)\in A^V\times U^V$，$\mathcal{T}^{B0}(x,(a,\mu))$ 按以下方式计算。

先初始化当前 token 的 step-local state：

$$
(a^0,\mu^0)=\operatorname{Init}(x,a,\mu)
$$

对每个 round $r=1,\ldots,R$，对每条边 $e\in E$ 定义消息：

$$
m_e^r=\phi_e^r(a_{\operatorname{src}(e)}^{r-1},\mu_{\operatorname{src}(e)}^{r-1})
$$

对每个节点 $v\in V$ 定义 mailbox：

$$
b_v^r=
\operatorname{Agg}_v^r
\left(
(m_e^r)_{e\in E^{-}(v)}
\right)
$$

对每个节点 $v\in V$ 更新：

$$
(a_v^r,\mu_v^r)=\psi_v^r(a_v^{r-1},\mu_v^{r-1},b_v^r)
$$

执行完 $R$ 个 round 后，定义输出：

$$
y=\rho(a_o^R,\mu_o^R)
$$

定义下一持久状态：

$$
S'=(a^R,\mu^R)
$$

于是：

$$
\mathcal{T}^{B0}(x,(a,\mu))=(y,S')
$$

#### 定理 3.5：B0 的顺序 prefill / decode 等价

对任意 $L\in\mathbb{N}$、任意 $x_{0:L}\in X^L$ 与任意 $S_0\in A^V\times U^V$：

$$
\operatorname{Prefill}^{seq,L}_{\mathcal{T}^{B0}}(x_{0:L},S_0)
=
\operatorname{Decode}_{\mathcal{T}^{B0}}^L(x_{0:L},S_0)
$$

**证明。**

由定理 1.5，取 $\mathcal{T}=\mathcal{T}^{B0}$ 即得。

<div class="qed" aria-label="证毕">∎</div>

#### B0 proof gate：主流 kernel family 的 chunk prefill 正确性

B0 的理论入口不应停在“能表达 Transformer / Mamba”。真正的 B0 proof gate 是：在 B0 内给出具体 kernel family 的 reference transition $\mathcal{T}$、chunk implementation $\mathcal{C}_L$，并证明 $\mathcal{C}_L$ 满足定义 2.2。

也就是说，B0 先要证明若干重要特例满足：

$$
\mathcal{C}_L(x_{0:L},S_0)=\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

这些特例不是任意 B0 graph / 任意 B0 kernel，而是 Transformer / Mamba / Linear Attention / FFN 这类后续会反复使用的主力 kernel family。后续 B1-B6 的问题，是在这些已证明正确的 B0 kernel 之上继续加入 mailbox、phase、selector、readout、pronounce 等机制，并检查它们是否保持或破坏 chunk prefill 正确性。

##### 定义 3.6：B0 kernel family 通过 proof gate

给定一个 B0 kernel family $\mathfrak{K}$，并给定它的参数集合：

$$
\Theta_{\mathfrak{K}}
$$

称 $\mathfrak{K}$ 通过 B0 proof gate，当且仅当对每个具体参数实例 $\theta\in\Theta_{\mathfrak{K}}$：

1. 给出一个 B0 transition：

$$
\mathcal{T}_{\theta}:X_{\theta}\times\mathcal{S}_{\theta}\to Y_{\theta}\times\mathcal{S}_{\theta}
$$

2. 对每个 $L\in\mathbb{N}$，给出一个 chunk implementation：

$$
\mathcal{C}_{\theta,L}:X_{\theta}^{L}\times\mathcal{S}_{\theta}\to Y_{\theta}^{L}\times\mathcal{S}_{\theta}
$$

3. 证明对所有 $x_{0:L}\in X_{\theta}^{L}$ 与 $S_0\in\mathcal{S}_{\theta}$：

$$
\mathcal{C}_{\theta,L}(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}_{\theta}}^L(x_{0:L},S_0)
$$

4. 给出高性能实现见证：说明 $\mathcal{C}_{\theta,L}$ 可由 matmul、causal mask、parallel prefix / scan、kernel fusion、packed layout 或 backend lowering 等方式实现。高性能实现见证不替代第 3 条的正确性证明。

##### 定义 3.6a：logical event DAG program

本节使用 $e,n,m$ 表示 logical event DAG 的事件顶点标识符，不表示 B0 空间图中的空间节点。事件顶点的局部值由后文的 $F_n$ 计算；实现若另外保存事件头，则完整事件记录是“事件标识符、依赖元数据与该局部值”组成的有限元组，而不是一个新的空间节点。

给定长度 $L\in\mathbb{N}$，定义 frontier index space：

$$
\mathbb F_L
=
\{-1\}\cup[L].
$$

给定有限 totally ordered logical timestamp set：

$$
(\Theta_L,<_{\Theta}).
$$

令 $\mathcal{EID}_L$ 是有限 logical event id 集合。每个 event id $e\in\mathcal{EID}_L$ 都带有：

$$
\operatorname{time}(e)\in\Theta_L,
$$

$$
\operatorname{support}(e)\subseteq[L],
$$

$$
\operatorname{frontier}(e)\in\mathbb F_L.
$$

$\operatorname{support}(e)$ 表示该事件顶点直接联合处理或在外部接口上标识的 `owner` 索引；$\operatorname{frontier}(e)$ 表示事件值对输入前缀的保守依赖上界。支持集不是实际依赖集合，也不能用整个前缀集合代替因果前沿；语义融合还可能产生不属于输入支持集的提升后输出 `owner`。

给定 logical event order：

$$
\prec_L
$$

要求 $\prec_L$ 是 strict total order。这里 strict total order 指满足以下三条的二元关系：

1. irreflexive：不存在 $e\prec_L e$。
2. transitive：若 $e_1\prec_L e_2$ 且 $e_2\prec_L e_3$，则 $e_1\prec_L e_3$。
3. total：对任意 $e\neq e'$，恰有一个关系成立：$e\prec_L e'$ 或 $e'\prec_L e$。

还要求若：

$$
\operatorname{time}(e)<_{\Theta}\operatorname{time}(e'),
$$

则：

$$
e\prec_L e'.
$$

同一 timestamp 内的 tie 必须由 owner order、phase-local microstep、canonical event id 或显式 joint-event semantics 唯一确定，不能依赖物理线程竞争顺序。

$\prec_L$ 是为了给参考求值与产物序列化提供确定顺序的规范总序；它可以把两个互不依赖的事件排出先后。只有 $(e,e')\in\mathcal E_L$ 才表示事件依赖，单独的 $e\prec_L e'$ 不产生数据、状态或控制依赖。因而 canonical event id 可以用于稳定并列消解，但不能凭标识符大小创造依赖边。

例如，普通 Transformer 可取：

$$
e=(t,o)
$$

其中 $o$ 是 token-local operation slot，$\operatorname{support}(e)=\{t\}$，$\operatorname{frontier}(e)=t$。固定周期 Tide event 可取：

$$
e=(\text{kind},\text{spatial node},\text{absolute round},\text{phase},\text{owner support})
$$

其中第二个坐标是空间节点位置；并把 absolute round 与 phase 放入 $\operatorname{time}(e)$。这样输入位置索引、逻辑时间与因果前沿不再复用同一个符号。

这里定义的是某次有限执行已经实例化后的逻辑事件，不要求 Tide 静态空间图本身无环，也不要求运行时在执行前预先枚举完整路径。未来若允许选择器在线生成事件，需要额外证明：该次执行终止、事件集合有限，并且每条依赖严格推进某个良基逻辑秩。普通 CFG / recurrent graph 的回边可以通过输入位置、内部轮次或迭代索引展开；同一逻辑秩内的零时延环不在当前定义覆盖范围内。

一个长度为 $L$ 的逻辑事件图的事件顶点集合为：

$$
\mathcal{N}_L\subseteq \mathcal{EID}_L
$$

给定有向边集合：

$$
\mathcal{E}_L\subseteq \mathcal{N}_L\times\mathcal{N}_L
$$

称 $D_L=(\mathcal{N}_L,\mathcal{E}_L)$ 是 causal logical event DAG，当且仅当：

1. $D_L$ 是有向无环图。
2. 若 $(e',e)\in\mathcal{E}_L$，则 $e'\prec_L e$。

DAG 条件 2 表示依赖只来自 reference logical order 中更早的 event。物理执行可以乱序，但逻辑依赖必须映射回这个 DAG。一般 kernel 可以通过 overwrite、mask 或已证明的 projection 得到更小 frontier；只有特定 monotone-frontier profile 才额外要求 dependency edge 上 frontier 单调。

对任意事件顶点 $n\in\mathcal{N}_L$，定义直接前驱集合：

$$
\operatorname{Pred}(n)=\{m\in\mathcal{N}_L\mid (m,n)\in\mathcal{E}_L\}
$$

定义直接后继集合：

$$
\operatorname{Succ}(n)=\{m\in\mathcal{N}_L\mid (n,m)\in\mathcal{E}_L\}
$$

一个 topological order 是 $\mathcal{N}_L$ 的一个 tuple：

$$
\pi=(n_1,\ldots,n_K)
$$

其中 $K=|\mathcal{N}_L|$，每个事件顶点在 $\pi$ 中恰好出现一次，并且若 $(n_i,n_j)\in\mathcal{E}_L$，则 $i<j$。

对每个事件顶点 $n\in\mathcal{N}_L$，给定事件值空间 $\mathcal{V}_n$ 和局部计算核：

$$
F_n:
\left(\prod_{m\in\operatorname{Pred}(n)}\mathcal{V}_m\right)
\times X^L
\times\mathcal{S}
\to
\mathcal{V}_n
$$

这里把输入序列 $x_{0:L}$ 与初始 state $S_0$ 作为 boundary data 传入，是为了统一表达 input injection、position / clock、old KV cache、old SSM state 等边界信息。

还要求每个 $F_n$ 满足 prefix-causal boundary condition。令：

$$
c=\operatorname{frontier}(n).
$$

则 $F_n$ 对 $x_{0:L}$ 的依赖只能通过前缀 $x_{0:c+1}$；当 $c=-1$ 时，它不能读取任何 input token。若 $c\geq 0$，形式化地说，若两个输入序列 $x_{0:L}$ 与 $\bar{x}_{0:L}$ 满足：

$$
x_j=\bar{x}_j,\quad j=0,\ldots,c
$$

则在相同前驱值与相同初始 state 下，$F_n$ 的输出相同。若某个 $F_n$ 使用 $x_{t'}$ 且 $t'>c$，则该 program 不满足 causal chunk 前提。

给定 output / final-state extraction 函数：

$$
G_L:
\left(\prod_{n\in\mathcal{N}_L}\mathcal{V}_n\right)
\times X^L
\times\mathcal{S}
\to
Y^L\times\mathcal{S}
$$

一个 logical event graph program 是：

$$
\mathcal{P}_L=(D_L,(F_n)_{n\in\mathcal{N}_L},G_L)
$$

##### 定义 3.6b：logical event DAG 的 evaluation

给定 transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

以及 logical event graph program $\mathcal{P}_L$。

定义 decode order 为 $\prec_L$ 限制在 $\mathcal{N}_L$ 上得到的事件顶点顺序。因为 $D_L$ 是因果逻辑事件 DAG，decode order 是 $D_L$ 的一个拓扑序。

令：

$$
\pi=(n_1,\ldots,n_K)
$$

是 $D_L$ 的任意 topological order，其中：

$$
K=|\mathcal{N}_L|
$$

对任意输入序列 $x_{0:L}\in X^L$ 与初始状态 $S_0\in\mathcal{S}$，定义沿 $\pi$ 的事件值族：

$$
v^{\pi}_{n}\in\mathcal{V}_{n},\quad n\in\mathcal{N}_L
$$

其递归定义如下。对 $j=1,\ldots,K$，令 $n=n_j$。因为 $\pi$ 是 topological order，若 $m\in\operatorname{Pred}(n)$，则 $m$ 已经出现在 $n$ 之前，因此 $v_m^\pi$ 已定义。令：

$$
v_n^\pi
=
F_n((v_m^\pi)_{m\in\operatorname{Pred}(n)},x_{0:L},S_0)
$$

定义沿 $\pi$ 的 graph evaluation：

$$
\operatorname{Eval}_{\pi}(\mathcal{P}_L,x_{0:L},S_0)
=
G_L((v_n^\pi)_{n\in\mathcal{N}_L},x_{0:L},S_0)
$$

令 $\pi_{dec}$ 表示 decode order。称 $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}}^L$ 的 decode unfolding，当且仅当对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$：

$$
\operatorname{Eval}_{\pi_{dec}}(\mathcal{P}_L,x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

称 chunk implementation $\mathcal{C}_L$ 是 $\mathcal{P}_L$ 的 graph evaluation，当且仅当存在 $D_L$ 的某个 topological order $\pi$，使得对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$：

$$
\mathcal{C}_L(x_{0:L},S_0)
=
\operatorname{Eval}_{\pi}(\mathcal{P}_L,x_{0:L},S_0)
$$

实现上，$\mathcal{C}_L$ 可以使用 batched evaluation、masked matmul、parallel scan、fusion 或 packed layout；数学上，它必须等价于某个 topological evaluation。

##### 定理 3.6c：B0 Logical Event DAG Theorem

给定 transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

若对某个 $L\in\mathbb{N}$，存在 causal logical event graph program $\mathcal{P}_L$，满足：

1. $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}}^L$ 的 decode unfolding。
2. $\mathcal{C}_L$ 是 $\mathcal{P}_L$ 的 graph evaluation。

则：

$$
\mathcal{C}_L(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$ 成立。因此 $\mathcal{C}_L$ 对 $\mathcal{T}$ 正确。

**证明。**

因为 $D_L$ 是有限 DAG，所以存在 topological order。decode order $\pi_{dec}$ 是 $D_L$ 的一个 topological order，因为每条边都指向 $\prec_L$ 中更晚的 event。

先证明任意两个 topological order 的 evaluation 相同。

对任意事件顶点 $n\in\mathcal{N}_L$，定义其 DAG 深度：

$$
d(n)=
\begin{cases}
0,& \operatorname{Pred}(n)=\varnothing,\\
1+\max_{m\in\operatorname{Pred}(n)}d(m),& \operatorname{Pred}(n)\neq\varnothing.
\end{cases}
$$

由于 $D_L$ 是有限 DAG，$d(n)$ 对所有事件顶点都良定义。

对 $d(n)$ 归纳。若 $d(n)=0$，则 $n$ 没有前驱，所以任何 topological order 中：

$$
v_n=
F_n((),x_{0:L},S_0)
$$

因此 $v_n$ 唯一。

假设所有深度小于 $q$ 的事件顶点值唯一。若 $d(n)=q$，则所有 $m\in\operatorname{Pred}(n)$ 都满足 $d(m)<q$。由归纳假设，所有前驱事件值唯一。因为 $F_n$ 是函数，$v_n$ 也唯一。

因此所有事件值与拓扑序无关。应用同一个提取函数 $G_L$ 后，$\operatorname{Eval}_{\pi}$ 也与拓扑序无关。

现在由定理前提 2，存在某个 topological order $\pi$，使得：

$$
\mathcal{C}_L(x_{0:L},S_0)=\operatorname{Eval}_{\pi}(\mathcal{P}_L,x_{0:L},S_0)
$$

由刚证明的 topological-order independence：

$$
\operatorname{Eval}_{\pi}(\mathcal{P}_L,x_{0:L},S_0)
=
\operatorname{Eval}_{\pi_{dec}}(\mathcal{P}_L,x_{0:L},S_0)
$$

再由定理前提 1：

$$
\operatorname{Eval}_{\pi_{dec}}(\mathcal{P}_L,x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

合并三式得到结论。

<div class="qed" aria-label="证毕">∎</div>

这个定理只证明 correctness。它不声称 $\mathcal{C}_L$ 自动高性能。高性能来自具体 kernel family 的额外结构，例如 token-wise map 的批量化、attention 的 masked matmul / fused attention、affine recurrence 的 parallel scan、有限 layer chain 的逐层批量执行。

##### 备注 3.6d：逻辑次序与墙钟完成顺序

定理 3.6c 约束的是逻辑依赖次序，不是设备上的执行、完成或缓冲区写入先后。对一般图运行时，特别是 LH-like runtime，可以允许 `owner` 较大的消息在墙钟时间上先完成，只要每个消息实例保留足够的逻辑元数据，例如：

$$
(\text{message id},\text{owner index},\text{absolute round},\text{phase},\text{source spatial node})
$$

并且空间节点计算核按这些元数据分桶、排序、掩码或缓冲，最终读取的仍是参考语义规定的逻辑可见集合。墙钟先完成不会改写消息的逻辑到达时间戳。

可以保持 correctness 的情况包括：

- 消息保留独立标识符、`owner`、逻辑轮次与阶段等字段；其中 `owner` 是归属字段，轮次与阶段才构成逻辑时间戳。
- mailbox 或 workspace 中的聚合是带标签集合，后续计算核仍可区分不同消息实例或逻辑事件的贡献。
- 对同一个状态槽的提交次序由 $\prec_L$ 或明确的冲突消解规则决定，而不是由物理写入先后决定。
- chunk implementation 虽然乱序执行，但最终每个逻辑事件的值与参考 DAG 方程相同。

会破坏 chunk prefill correctness 的情况包括：

- 不同 `owner` 或逻辑轮次的消息在空间节点内被不可逆聚合，且聚合结果丢失消息标识符、归属和时间标签。
- 计算核的行为依赖墙钟首达或线程竞争次序，而参考转移依赖逻辑次序。
- 尚未在某事件逻辑时间戳可见的较晚输入，通过无标记聚合影响了该事件、局部输出或状态提交。

因此，完整涵盖既有 LH 实现不一定可能。若 LH 某处把同一 tick 收到的多源消息做不可逆、无时间戳的聚合，则输入影响关系可能被折叠，无法构造与 decode fold 等价的事件 DAG。若决定把该机制纳入严格 chunk-prefill family，就需要把聚合改成可追踪的带标签聚合，或证明该聚合对所有相关计算核是可交换、可结合、且不影响参考逻辑可见性；若做不到，也可以在保持“局部通信 + 超稀疏”总体目标的前提下简化或替换该机制，而不是把完整 LH compatibility 设为定理前提。

##### 定义 3.6e：semantics-preserving aggregation quotient

定义 2.3-2.5 说明了 transition-level 的语义强弱：如果 reference semantic contract 本身已经是 coarse semantics，则实现只需复现该 coarse contract。本节进一步处理 event-level 的聚合：在一个给定 logical event DAG program 内，哪些 event value 可以被压缩为 quotient value 而不改变该 program 对 reference contract 的输出与最终状态。

给定 logical event DAG program：

$$
\mathcal{P}_L=(D_L,(F_n)_{n\in\mathcal{N}_L},G_L)
$$

对每个事件顶点 $n\in\mathcal{N}_L$，给定商值空间 $\widehat{\mathcal{V}}_n$ 与抽象映射：

$$
\alpha_n:\mathcal{V}_n\to\widehat{\mathcal{V}}_n
$$

这些 $\alpha_n$ 可以表示：

- identity / tagged collection：不丢失事件值的实例标签；完整来源信息还要求保留事件依赖关系。
- sum / max / mean / histogram 等聚合：丢失部分 provenance。
- packed layout / sparse row layout：改变表示但保留语义。

称一组 quotient kernels：

$$
\widehat{F}_n:
\left(\prod_{m\in\operatorname{Pred}(n)}\widehat{\mathcal{V}}_m\right)
\times X^L
\times\mathcal{S}
\to
\widehat{\mathcal{V}}_n
$$

以及 quotient extraction：

$$
\widehat{G}_L:
\left(\prod_{n\in\mathcal{N}_L}\widehat{\mathcal{V}}_n\right)
\times X^L
\times\mathcal{S}
\to
Y^L\times\mathcal{S}
$$

定义 quotient program：

$$
\widehat{\mathcal{P}}_L
=
(D_L,(\widehat{F}_n)_{n\in\mathcal{N}_L},\widehat{G}_L)
$$

注意：$\widehat{\mathcal{P}}_L$ 使用同一个逻辑事件 DAG $D_L$，但每个事件顶点的值空间从 $\mathcal{V}_n$ 改为 $\widehat{\mathcal{V}}_n$。

称 $\widehat{\mathcal{P}}_L$ 构成 $\mathcal{P}_L$ 的 semantics-preserving aggregation quotient，当且仅当：

1. 对每个事件顶点 $n$、任意前驱值族 $(v_m)_{m\in\operatorname{Pred}(n)}$、任意输入 $x_{0:L}$ 与任意初始状态 $S_0$，局部计算核与抽象映射交换：

$$
\alpha_n
\left(
F_n((v_m)_{m\in\operatorname{Pred}(n)},x_{0:L},S_0)
\right)
=
\widehat{F}_n
\left(
(\alpha_m(v_m))_{m\in\operatorname{Pred}(n)},x_{0:L},S_0
\right)
$$

2. 对任意事件值族 $(v_n)_{n\in\mathcal{N}_L}$、任意输入 $x_{0:L}$ 与任意初始状态 $S_0$，输出与最终状态提取可通过商值因子化：

$$
G_L((v_n)_{n\in\mathcal{N}_L},x_{0:L},S_0)
=
\widehat{G}_L((\alpha_n(v_n))_{n\in\mathcal{N}_L},x_{0:L},S_0)
$$

直观地说，$\alpha$ 丢掉的信息必须对所有后续 kernel 与最终输出无关。此时 quotient value 是后续语义的充分统计量。

##### 定理 3.6f：Aggregation Quotient Theorem

给定 transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

若对某个 $L\in\mathbb{N}$：

1. $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}}^L$ 的 decode unfolding。
2. $\widehat{\mathcal{P}}_L$ 是 $\mathcal{P}_L$ 的 semantics-preserving aggregation quotient。
3. chunk implementation $\mathcal{C}_L$ 是 $\widehat{\mathcal{P}}_L$ 的 graph evaluation，意义同定义 3.6b，只是把 value space、kernel 与 extraction 换成 quotient 版本。定义 3.6b 对 quotient value spaces 可逐字应用。

则：

$$
\mathcal{C}_L(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$ 成立。

**证明。**

令 $\pi$ 是定理前提 3 中使 $\mathcal{C}_L$ 等于 $\widehat{\mathcal{P}}_L$ graph evaluation 的 topological order。由于定理 3.6c 中已经证明 topological evaluation 与所选 order 无关，并且该证明只依赖 DAG、局部函数和 extraction，不依赖具体 value space，所以同样适用于 quotient program $\widehat{\mathcal{P}}_L$。下面沿 decode order 证明 quotient event value 与 reference event value 的关系。

按 decode order 对 event 做归纳。设 reference program $\mathcal{P}_L$ 中 event $n$ 的值为 $v_n$，quotient program $\widehat{\mathcal{P}}_L$ 中 event $n$ 的值为 $\widehat{v}_n$。归纳假设为：所有前驱 $m$ 都满足：

$$
\widehat{v}_m=\alpha_m(v_m)
$$

由 quotient 条件 1，对当前 event $n$，reference kernel 后再抽象，等于先抽象前驱再运行 quotient kernel。结合归纳假设：

$$
\begin{aligned}
\widehat{v}_n
&=
\widehat{F}_n((\widehat{v}_m)_{m\in\operatorname{Pred}(n)},x_{0:L},S_0)\\
&=
\widehat{F}_n((\alpha_m(v_m))_{m\in\operatorname{Pred}(n)},x_{0:L},S_0)\\
&=
\alpha_n\left(F_n((v_m)_{m\in\operatorname{Pred}(n)},x_{0:L},S_0)\right)\\
&=
\alpha_n(v_n).
\end{aligned}
$$

当 $\operatorname{Pred}(n)=\varnothing$ 时，上式中的前驱族是定义 0.5 中的唯一空 tuple，因此同样成立。

归纳到所有 event 后，quotient evaluation 得到的 quotient values 等于 reference values 经 $\alpha$ 映射后的结果。

由 quotient 条件 2，最终 output / state extraction 只依赖这些 quotient values，因此 quotient execution 的输出与 reference event DAG 的输出相同。

又因为定理前提 1 说明 $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}}^L$ 的 decode unfolding，reference event DAG 的输出等于 $\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)$。

定理前提 3 给出 $\mathcal{C}_L$ 等于 quotient graph evaluation。因此 $\mathcal{C}_L(x_{0:L},S_0)$ 也等于 $\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)$。

<div class="qed" aria-label="证毕">∎</div>

##### 推论 3.6g：三类聚合的判定

1. 同一 logical event 内的多源聚合是安全的，只要 reference decode 本来也在该 event 上执行同一个确定性聚合。此时聚合就是 $F_n$ 的一部分，不需要跨 event quotient。
2. 带标签的跨输入位置/跨逻辑轮次聚合是安全的，只要标签与显式关系保留了后续计算核需要区分的实例、时间、归属和来源信息。标签本身不自动等于完整 provenance；满足要求时，$\alpha$ 可以近似看作 identity 或 layout change。
3. untagged irreversible aggregation 只有在它满足定义 3.6e 的 quotient 条件时才安全。若存在两组 reference event values 在聚合后相同，但某个后续 kernel 或最终输出不同，则不存在 semantics-preserving quotient，不能一般性证明 chunk prefill correctness。

因此，跨输入位置或逻辑轮次的无标签聚合不是绝对禁止；它必须是下游语义的充分统计量。sum / max / histogram 等聚合在某些计算核中可能安全，但在需要区分输入位置影响、逻辑轮次标签或逐位置状态提交的计算核中通常不安全。时间/归属标签与完整来源关系仍是不同对象。

##### 定义 3.6h：Contract-DAG-Quotient correctness certificate

给定 fine reference transition：

$$
\mathcal{T}^{fine}:X\times\mathcal{S}^{fine}
\to
Y^{fine}\times\mathcal{S}^{fine}
$$

以及 coarse reference transition：

$$
\mathcal{T}^{coarse}:X\times\mathcal{S}^{coarse}
\to
Y^{coarse}\times\mathcal{S}^{coarse}
$$

对某个长度 $L\in\mathbb{N}$，一个 Contract-DAG-Quotient correctness certificate，简称 CDQ correctness certificate，由以下对象组成：

$$
\mathcal{C}_L:
X^L\times\mathcal{S}^{coarse}
\to
(Y^{coarse})^L\times\mathcal{S}^{coarse}
$$

$$
\mathfrak{C}_L
=
(\alpha,\beta,\mathcal{P}_L,\widehat{\mathcal{P}}_L,\mathcal{C}_L)
$$

并满足：

1. $\mathcal{T}^{coarse}$ 是 $\mathcal{T}^{fine}$ 关于状态抽象 $\alpha$ 与输出抽象 $\beta$ 的 semantic quotient，意义同定义 2.4。
2. $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}^{coarse}}^L$ 的 decode unfolding，意义同定义 3.6b。
3. $\widehat{\mathcal{P}}_L$ 是 $\mathcal{P}_L$ 的 semantics-preserving aggregation quotient，意义同定义 3.6e。
4. $\mathcal{C}_L$ 是 $\widehat{\mathcal{P}}_L$ 的 graph evaluation。

这四层分别回答：

```text
reference contract 要求保留什么？
decode computation 如何展开为 logical events？
哪些 event values 可以安全压缩？
chunk implementation 实际计算哪个 quotient DAG？
```

##### 定理 3.6i：Unified Contract-DAG-Quotient Theorem

若 $\mathfrak{C}_L$ 是定义 3.6h 中的 CDQ correctness certificate，并且：

$$
\operatorname{Fold}_{\mathcal{T}^{fine}}^L
(x_{0:L},S_0^{fine})
=
(y_{0:L}^{fine},S_L^{fine})
$$

则：

$$
\mathcal{C}_L(x_{0:L},\alpha(S_0^{fine}))
=
(\beta^L(y_{0:L}^{fine}),\alpha(S_L^{fine}))
$$

对所有 $x_{0:L}\in X^L$ 与 $S_0^{fine}\in\mathcal{S}^{fine}$ 成立。

**证明。**

由 CDQ 条件 1 与引理 2.5：

$$
\operatorname{Fold}_{\mathcal{T}^{coarse}}^L
(x_{0:L},\alpha(S_0^{fine}))
=
(\beta^L(y_{0:L}^{fine}),\alpha(S_L^{fine}))
$$

由 CDQ 条件 2-4 与定理 3.6f：

$$
\mathcal{C}_L(x_{0:L},\alpha(S_0^{fine}))
=
\operatorname{Fold}_{\mathcal{T}^{coarse}}^L
(x_{0:L},\alpha(S_0^{fine}))
$$

合并两式即得：

$$
\mathcal{C}_L(x_{0:L},\alpha(S_0^{fine}))
=
(\beta^L(y_{0:L}^{fine}),\alpha(S_L^{fine}))
$$

<div class="qed" aria-label="证毕">∎</div>

##### 推论 3.6j：三个退化情形

1. 若 transition-level 的 $\alpha,\beta$ 都是 identity，则定理 3.6i 退化为 Aggregation Quotient Theorem。
2. 若 event-level 的 $\alpha_n$ 都是 identity，且 $\widehat{\mathcal{P}}_L=\mathcal{P}_L$，则定理 3.6i 退化为 coarse contract 上的 Logical Event DAG Theorem。
3. 若 transition-level 与 event-level abstraction 都是 identity，则定理 3.6i 退化为原 reference transition 上的直接 logical event DAG correctness。

因此，定理 3.6i 统一了三种原本容易混在一起的情况：改变 reference semantic resolution、压缩 event representation、改变物理执行顺序。

##### 定义 3.6k：non-degenerate chunk certificate

CDQ correctness certificate 只证明语义正确。若允许任意 logical event granularity，给定任意 transition：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

可以构造单事件顶点 oracle 计算核：

$$
F_{oracle}:X^L\times\mathcal{S}\to Y^L\times\mathcal{S}
$$

$$
F_{oracle}(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

然后宣称该单事件顶点程序是 chunk implementation。这个构造在形式上正确，但没有揭示任何可复用计算核、并行结构或性能来源。

为排除这种退化，一个 non-degenerate chunk certificate 由以下内容组成。

1. **Correctness witness**：给出定义 3.6h 的 CDQ correctness certificate。
2. **Uniform primitive family**：给定与长度 $L$ 无关的有限 primitive kind 集合 $\mathfrak{K}_{prim}$。每个 logical event 与 physical operation 都必须由 $\mathfrak{K}_{prim}$ 中的 primitive kind 加已声明类型的 event-local metadata 实例化；metadata 不能充当任意 program 的不透明编码，也不能为每个 $L$ 临时引入一个任意的新函数。
3. **Explicit logical granularity**：每个输出位置 $t\in[L]$ 有显式 designated output event；persistent state 的每个声明组件也有显式 commit event。logical extractions $G_L$ 与 $\widehat{G}_L$ 只能投影、拼接或执行已登记 primitive，不能隐藏完整 fold。
4. **Explicit lowering**：给出有限 physical execution DAG：

$$
H_L=(\mathcal{R}_L,\mathcal{A}_L)
$$

对每个 physical operation $r\in\mathcal{R}_L$，定义其直接前驱：

$$
\operatorname{Pred}_{H}(r)
=
\{q\in\mathcal{R}_L\mid(q,r)\in\mathcal{A}_L\}
$$

给定 physical value space $\mathcal{U}_r$ 与 deterministic primitive kernel：

$$
\Phi_r:
\left(\prod_{q\in\operatorname{Pred}_{H}(r)}\mathcal{U}_q\right)
\times X^L
\times\mathcal{S}^{coarse}
\to
\mathcal{U}_r
$$

并给定 physical extraction：

$$
J_L:
\left(\prod_{r\in\mathcal{R}_L}\mathcal{U}_r\right)
\times X^L
\times\mathcal{S}^{coarse}
\to
(Y^{coarse})^L\times\mathcal{S}^{coarse}
$$

$J_L$ 同样只能投影、拼接或执行 $\mathfrak{K}_{prim}$ 中已登记的 extraction primitive，不能隐藏完整 fold。

$H_L$ 的 topological evaluation 按定义 3.6b 的递归方式计算，只是把 logical kernels $F_n$ 与 extraction $G_L$ 换成 physical primitive kernels $\Phi_r$ 与 extraction $J_L$。

以及 lowering map：

$$
\lambda_L:\mathcal{N}_L\to\mathcal{R}_L
$$

其中 $\lambda_L(n)$ 表示哪个 physical operation 实现 logical event $n$。还要求对每条 logical edge $(m,n)\in\mathcal{E}_L$：

- 若 $\lambda_L(m)\neq\lambda_L(n)$，则 $H_L$ 中存在从 $\lambda_L(m)$ 到 $\lambda_L(n)$ 的有向路径。
- 若 $\lambda_L(m)=\lambda_L(n)$，则该 physical operation 必须在其内部语义中保持 $m$ 先于 $n$ 的 logical dependency。

按照 $\mathfrak{K}_{prim}$ 的 primitive semantics 对 $H_L$ 做任意 topological evaluation，必须得到函数 $\mathcal{C}_L$。多个 logical events 可以映射到同一个 physical operation，以表达 batching 或 fusion；但该 fused primitive 必须有独立的语义保持证明。

这里采用一个规范化约定：$\lambda_L$ 只直接表达“一个 logical event 由一个 physical operation 承载”以及“多个 logical events 被同一个 physical operation 融合承载”。若某个实现要把一个较粗的 logical event lower 为多个 physical operations，则必须先把该 event 语义保持地细化为一个 logical sub-DAG，再对细化后的 events 定义 $\lambda_L$。这个约定不是说 runtime 不能使用多步 kernel，而是要求证明对象先显式暴露这些中间依赖，避免把任意复杂计算藏在一个未展开的 logical event 中。

5. **No-oracle condition**：$\mathfrak{K}_{prim}$ 中不能包含语义为“对任意输入直接运行 $\operatorname{Fold}_{\mathcal{T}}^L$”或“对任意 program 直接运行 $\operatorname{Eval}_{\pi}(\mathcal{P}_L,\cdot,\cdot)$”的 primitive。primitive 只能实现预先声明的 kernel family，例如 token-wise map、masked matmul、associative combine、scan step、pack、copy 或固定 extraction。
6. **Complete cost ledger**：给定 machine-cost model $\mathfrak{M}$。对每个 physical operation $r\in\mathcal{R}_L$，$\mathfrak{M}$ 给出 work cost $w(r)\ge 0$ 与 span cost $d(r)\ge 0$。定义总 work：

$$
\operatorname{Work}_L
=
\sum_{r\in\mathcal{R}_L}w(r)
$$

令 $\operatorname{Path}(H_L)$ 是 $H_L$ 的所有有向路径组成的集合，定义 span：

$$
\operatorname{Span}_L
=
\max_{\gamma\in\operatorname{Path}(H_L)}
\sum_{r\in\gamma}d(r)
$$

当 $\mathcal{R}_L=\varnothing$ 时，约定 $\operatorname{Work}_L=\operatorname{Span}_L=0$。certificate 还必须给出 peak live memory 上界 $\operatorname{Mem}_L$ 与 communication volume 上界 $\operatorname{Comm}_L$。mask/index 构造、packing、layout conversion、copy、runtime bookkeeping/metadata 与 quotient maintenance 都必须计入相应成本，不能被视为免费 runtime；离线数学证明或编译期验证本身不计入每次 runtime execution cost。

这里 $H_L$ 是 physical execution DAG，定义 3.6a 中的 $D_L$ 是 logical event DAG。二者不能混淆：$D_L$ 定义 reference dependencies，$H_L$ 描述某个具体 batching、fusion、scan 或 backend lowering 如何执行这些 dependencies。

##### 定义 3.6l：parallel-prefill witness

给定同一个 primitive family 与 machine-cost model。令：

$$
H_L^{dec}=(\mathcal{R}_L^{dec},\mathcal{A}_L^{dec})
$$

是按顺序 decode fold 执行相同 reference contract 的有限 physical execution DAG。按照定义 3.6k 的同一 cost ledger 公式，定义：

$$
\operatorname{Work}_L^{dec}
=
\sum_{r\in\mathcal{R}_L^{dec}}w(r)
$$

$$
\operatorname{Span}_L^{dec}
=
\max_{\gamma\in\operatorname{Path}(H_L^{dec})}
\sum_{r\in\gamma}d(r)
$$

当 $\mathcal{R}_L^{dec}=\varnothing$ 时，同样约定 $\operatorname{Work}_L^{dec}=\operatorname{Span}_L^{dec}=0$。

一个 non-degenerate chunk certificate 称为 asymptotic parallel-prefill witness，当且仅当存在常数 $c>0$ 与 $L_0\in\mathbb{N}$，使得对所有 $L\ge L_0$：

$$
\operatorname{Span}_L^{dec}>0
$$

$$
\operatorname{Work}_L
\le
c\operatorname{Work}_L^{dec}
$$

并且：

$$
\lim_{L\to\infty}
\frac{\operatorname{Span}_L}{\operatorname{Span}_L^{dec}}
=0
$$

第一式要求 chunk implementation 不通过无界增加总工作量换取并行；第二式要求其 critical-path span 相对于逐 token decode 渐近下降。

若只能在有限硬件和有限长度上观察收益，则应称为 practical performance witness，并报告实际的 $\operatorname{Work}_L$、$\operatorname{Span}_L$、$\operatorname{Mem}_L$、$\operatorname{Comm}_L$ 或对应测量值，而不声称得到 asymptotic parallel-prefill witness。

##### 例 3.6m：证书的正例与反例

1. 单个 `RunFold` primitive 直接返回整个 $\operatorname{Fold}_{\mathcal{T}}^L$，违反 uniform primitive family 与 no-oracle condition，因此不是 non-degenerate certificate。
2. token-wise map 可把每个位置建成独立 logical event，再用一个 batched-map physical primitive 实现这些 events。理想并行模型下，它可具有线性 work 与常数级或硬件相关的低 span。
3. affine recurrence 可用固定 combine primitive 与 parallel scan lowering。其 correctness 将由后文定理 3.11 证明；其非退化性来自固定 affine-combine primitive、显式 scan DAG 与完整 cost ledger。
4. causal attention 的 correctness 将由后文定理 3.9 证明；是否构成高性能 witness，还需要对 batched QKV、causal mask、attention kernel、KV write 与 memory traffic 给出 machine-specific cost ledger。

从本节开始，定义 3.6 中的“高性能实现见证”应优先解释为：先给出 non-degenerate chunk certificate，再判断它是否进一步构成 asymptotic 或 practical parallel-prefill witness。

non-degenerate chunk certificate 是本研究选择的可审计充分标准，不声称是所有正确实现的数学必要条件。某个实现可能正确但尚未找到这种证书；此时结论应是“尚未被本 proof system 认证”，而不是直接判定实现错误。若允许任意 primitive 与任意事件粒度，则所谓全局充要条件会退化为单事件顶点 oracle 构造，因此不具有研究价值。

定理 3.6i 与定义 3.6k-3.6l 的分工是：

```text
Unified CDQ Theorem: 证明结果正确。
Non-degenerate certificate: 证明没有通过巨型 oracle kernel 作弊。
Parallel-prefill witness: 说明性能收益来自明确的 work/span 结构。
```

##### 定理 3.7：token-wise kernel 的 chunk prefill 正确性

给定集合 $X,Y$ 与函数：

$$
f:X\to Y
$$

定义无持久更新的 transition：

$$
\mathcal{T}^{tok}:X\times\{*\}\to Y\times\{*\}
$$

其中 $\{*\}$ 是 singleton state space，且：

$$
\mathcal{T}^{tok}(x,*)=(f(x),*)
$$

对每个 $L\in\mathbb{N}$，定义 chunk implementation：

$$
\mathcal{C}^{tok}_{L}:X^L\times\{*\}\to Y^L\times\{*\}
$$

其中：

$$
\mathcal{C}^{tok}_{L}(x_{0:L},*)=
((f(x_0),\ldots,f(x_{L-1})),*)
$$

则 $\mathcal{C}^{tok}_{L}$ 对 $\mathcal{T}^{tok}$ 正确。

**证明。**

由顺序 fold 定义，对所有 $t\in[L]$：

$$
(y_t,*)=\mathcal{T}^{tok}(x_t,*)=(f(x_t),*)
$$

因此：

$$
\operatorname{Fold}_{\mathcal{T}^{tok}}^L(x_{0:L},*)=
((f(x_0),\ldots,f(x_{L-1})),*)
$$

这与 $\mathcal{C}^{tok}_{L}$ 的定义相同。

<div class="qed" aria-label="证毕">∎</div>

FFN / MLP、逐 token norm、逐 token residual add、逐 token gating 都属于这个证明模式，或属于这个模式与有限维状态无关函数的直接乘积。

##### 定义 3.8：causal attention decode reference

这一节定义单层、单头 causal attention；多头 attention 是有限个单头的乘积加线性投影，不改变证明结构。

给定维度 $d,d_k,d_v\in\mathbb{N}_{>0}$。令：

$$
X=\mathbb{R}^{d}
$$

令 KV cache state space 为：

$$
\mathcal{S}_{attn}=\bigcup_{P\in\mathbb{N}}\left((\mathbb{R}^{d_k})^P\times(\mathbb{R}^{d_v})^P\right)
$$

若 $S=(K_{0:P},V_{0:P})\in\mathcal{S}_{attn}$，则 $P$ 是已有 prefix cache 长度。

给定 projection 函数：

$$
\operatorname{Proj}_Q:X\to\mathbb{R}^{d_k}
$$

$$
\operatorname{Proj}_K:X\to\mathbb{R}^{d_k}
$$

$$
\operatorname{Proj}_V:X\to\mathbb{R}^{d_v}
$$

给定按 prefix 长度索引的 attention readout 函数族。对每个 $P'\in\mathbb{N}_{>0}$，给定：

$$
\operatorname{Attn}_{P'}:\mathbb{R}^{d_k}\times(\mathbb{R}^{d_k})^{P'}\times(\mathbb{R}^{d_v})^{P'}\to\mathbb{R}^{d_v}
$$

例如 $\operatorname{Attn}_{P'}$ 可以是长度为 $P'$ 的 softmax dot-product attention；证明只要求 decode 与 chunk 在同一 prefix 长度上使用同一个 $\operatorname{Attn}_{P'}$。

定义 causal attention decode transition：

$$
\mathcal{T}^{attn}:X\times\mathcal{S}_{attn}\to\mathbb{R}^{d_v}\times\mathcal{S}_{attn}
$$

对 $x\in X$ 与 $S=(K_{0:P},V_{0:P})$，令：

$$
q=\operatorname{Proj}_Q(x),\quad k=\operatorname{Proj}_K(x),\quad v=\operatorname{Proj}_V(x)
$$

定义 appended cache：

$$
K'_{0:P+1}=(K_0,\ldots,K_{P-1},k)
$$

$$
V'_{0:P+1}=(V_0,\ldots,V_{P-1},v)
$$

输出：

$$
y=\operatorname{Attn}_{P+1}(q,K'_{0:P+1},V'_{0:P+1})
$$

于是：

$$
\mathcal{T}^{attn}(x,(K_{0:P},V_{0:P}))=(y,(K'_{0:P+1},V'_{0:P+1}))
$$

##### 定理 3.9：causal attention 的 chunk prefill 正确性

给定 $L\in\mathbb{N}$、输入 $x_{0:L}\in X^L$ 与初始 cache：

$$
S_0=(K^{old}_{0:P},V^{old}_{0:P})\in\mathcal{S}_{attn}
$$

定义 chunk projection：

$$
q_t=\operatorname{Proj}_Q(x_t),\quad k_t=\operatorname{Proj}_K(x_t),\quad v_t=\operatorname{Proj}_V(x_t),\quad t\in[L]
$$

定义最终 concatenated cache：

$$
\widetilde{K}_{0:P+L}=(K^{old}_0,\ldots,K^{old}_{P-1},k_0,\ldots,k_{L-1})
$$

$$
\widetilde{V}_{0:P+L}=(V^{old}_0,\ldots,V^{old}_{P-1},v_0,\ldots,v_{L-1})
$$

当 $L=0$ 时，上式没有新增 $k_t,v_t$，因此 $\widetilde{K}_{0:P}=K^{old}_{0:P}$ 且 $\widetilde{V}_{0:P}=V^{old}_{0:P}$。

对每个 $t\in[L]$，定义 causal prefix：

$$
\widetilde{K}^{\le t}_{0:P+t+1}=(K^{old}_0,\ldots,K^{old}_{P-1},k_0,\ldots,k_t)
$$

$$
\widetilde{V}^{\le t}_{0:P+t+1}=(V^{old}_0,\ldots,V^{old}_{P-1},v_0,\ldots,v_t)
$$

定义 chunk implementation：

$$
\mathcal{C}^{attn}_{L}(x_{0:L},S_0)=(y_{0:L},(\widetilde{K}_{0:P+L},\widetilde{V}_{0:P+L}))
$$

其中：

$$
y_t=
\operatorname{Attn}_{P+t+1}(q_t,\widetilde{K}^{\le t}_{0:P+t+1},\widetilde{V}^{\le t}_{0:P+t+1})
$$

则 $\mathcal{C}^{attn}_{L}$ 对 $\mathcal{T}^{attn}$ 正确。

**证明。**

若 $L=0$，chunk implementation 与顺序 fold 都返回空输出和初始 cache，结论成立。

对 $t$ 归纳。$t=0$ 时，decode transition 先把 $k_0,v_0$ append 到 old cache，再用 prefix $(K^{old}_{0:P},k_0)$ 与 $(V^{old}_{0:P},v_0)$ 计算输出，等于 chunk 定义中的 $y_0$。

假设对所有 $j<t$，decode 后的 cache 为：

$$
(K^{old}_0,\ldots,K^{old}_{P-1},k_0,\ldots,k_{t-1})
$$

与：

$$
(V^{old}_0,\ldots,V^{old}_{P-1},v_0,\ldots,v_{t-1})
$$

则第 $t$ 步 decode append $k_t,v_t$ 后，输出正是：

$$
\operatorname{Attn}_{P+t+1}(q_t,\widetilde{K}^{\le t}_{0:P+t+1},\widetilde{V}^{\le t}_{0:P+t+1})
$$

即 chunk 定义中的 $y_t$。最终 cache 也等于 concatenated cache。

<div class="qed" aria-label="证毕">∎</div>

高性能实现见证：$q_{0:L},k_{0:L},v_{0:L}$ 可由 batched projection / matmul 得到；每个位置只读 $\le t$ 的 prefix 可由 causal mask 或 FlashAttention-style fused attention 实现。这里的高性能主要来自矩阵化与融合，不等于 attention work 本身从二次复杂度变成线性复杂度。

##### 定义 3.10：affine scan recurrence

给定 state vector space $\mathcal{H}$、input space $X$ 与 output space $Y$。对每个输入 $x\in X$，给定 affine state update：

$$
g_x:\mathcal{H}\to\mathcal{H}
$$

并写成：

$$
g_x(h)=A_x h+b_x
$$

其中 $A_x$ 是作用在 $\mathcal{H}$ 上的线性算子，$b_x\in\mathcal{H}$。

给定 output 函数：

$$
o:X\times\mathcal{H}\to Y
$$

定义 recurrence transition：

$$
\mathcal{T}^{scan}:X\times\mathcal{H}\to Y\times\mathcal{H}
$$

其中：

$$
h'=g_x(h)
$$

$$
y=o(x,h')
$$

$$
\mathcal{T}^{scan}(x,h)=(y,h')
$$

##### 定理 3.11：affine scan recurrence 的 chunk prefill 正确性

给定 $x_{0:L}\in X^L$ 与初始状态 $h_0\in\mathcal{H}$。对每个 $t\in[L]$，令：

$$
g_t=g_{x_t}
$$

定义前缀复合：

$$
G_t=g_t\circ g_{t-1}\circ\cdots\circ g_0
$$

并定义：

$$
h_{t+1}=G_t(h_0)
$$

$$
y_t=o(x_t,h_{t+1})
$$

当 $L=0$ 时，没有 $G_t$ 或 $y_t$，并约定最终状态为 $h_L=h_0$。

定义 chunk implementation：

$$
\mathcal{C}^{scan}_{L}(x_{0:L},h_0)=((y_0,\ldots,y_{L-1}),h_L)
$$

则 $\mathcal{C}^{scan}_{L}$ 对 $\mathcal{T}^{scan}$ 正确。

**证明。**

函数复合满足结合律。顺序 decode 的状态满足：

$$
h_{t+1}=g_t(h_t)
$$

对 $t$ 归纳可得：

$$
h_{t+1}=g_t\circ g_{t-1}\circ\cdots\circ g_0(h_0)=G_t(h_0)
$$

输出也同为：

$$
y_t=o(x_t,h_{t+1})
$$

因此 chunk implementation 与顺序 fold 相同。

<div class="qed" aria-label="证毕">∎</div>

高性能实现见证：affine map 可用 pair 表示为 $(A,b)$，其复合为：

$$
(A_2,b_2)\circ(A_1,b_1)=(A_2A_1,A_2b_1+b_2)
$$

该复合由函数复合继承结合律，因此可用 parallel prefix / scan / chunk scan 实现所有前缀 $G_t$。Mamba / selective SSM 的许多高性能 prefill 路线正落在这个证明模板内；具体实现还要检查 discretization、gating、normalization、layout 与浮点重排。

##### 推论 3.12：linear attention accumulator 的 chunk prefill 正确性

给定函数：

$$
u:X\to\mathcal{H}
$$

若 linear attention 的持久状态是 prefix accumulator $h\in\mathcal{H}$，并且每个 token 的更新可写为：

$$
h'=h+u(x)
$$

输出为：

$$
y=o(x,h')
$$

则它是定理 3.11 的特例，其中：

$$
A_x=I,\quad b_x=u(x)
$$

因此 linear attention accumulator 的 chunk prefill 正确性由 associative prefix sum / scan 得到。

##### 定理 3.13：有限 B0 chain 的 layer-wise chunk 正确性

给定 $N\in\mathbb{N}_{>0}$。给定 layer input/output spaces：

$$
X_1,\ldots,X_{N+1}
$$

以及 layer state spaces：

$$
\mathcal{S}_1,\ldots,\mathcal{S}_N
$$

对每个 $j=1,\ldots,N$，给定 layer transition：

$$
\mathcal{T}_j:X_j\times\mathcal{S}_j\to X_{j+1}\times\mathcal{S}_j
$$

每个 $\mathcal{T}_j$ 都属于已经通过 B0 proof gate 的 kernel family，并有正确 chunk implementation：

$$
\mathcal{C}_{j,L}:X_j^L\times\mathcal{S}_j\to X_{j+1}^L\times\mathcal{S}_j
$$

定义 stack state space：

$$
\mathcal{S}^{stack}=\mathcal{S}_1\times\cdots\times\mathcal{S}_N
$$

定义一个 token 的 layer stack reference transition：

$$
\mathcal{T}^{stack}:X_1\times\mathcal{S}^{stack}\to X_{N+1}\times\mathcal{S}^{stack}
$$

对 $x\in X_1$ 与 $S=(S_1,\ldots,S_N)\in\mathcal{S}^{stack}$，令：

$$
z_0=x
$$

并对 $j=1,\ldots,N$ 递归定义：

$$
(z_j,S_j')=\mathcal{T}_j(z_{j-1},S_j)
$$

于是：

$$
\mathcal{T}^{stack}(x,(S_1,\ldots,S_N))=(z_N,(S_1',\ldots,S_N'))
$$

定义 layer-wise chunk implementation $\mathcal{C}^{stack}_L$。给定 $x_{0:L}\in X_1^L$ 与 $S=(S_1,\ldots,S_N)$，令：

$$
z^0_{0:L}=x_{0:L}
$$

并对 $j=1,\ldots,N$ 递归定义：

$$
(z^j_{0:L},S_j')=\mathcal{C}_{j,L}(z^{j-1}_{0:L},S_j)
$$

最后定义：

$$
\mathcal{C}^{stack}_L(x_{0:L},S)=(z^N_{0:L},(S_1',\ldots,S_N'))
$$

若每层 chunk implementation 都满足定义 2.2，则 $\mathcal{C}^{stack}_L$ 对 $\mathcal{T}^{stack}$ 正确。

**证明。**

对 layer index $j$ 归纳。$j=1$ 时由 $\mathcal{C}_{1,L}$ 的正确性得到第 1 层所有位置输出 $z^1_{0:L}$ 与最终 state $S_1'$ 等于对 $\mathcal{T}_1$ 做顺序 fold 的结果。

假设前 $j$ 层的 chunk 输出序列与这些层的最终 state 等于 reference stack 在前 $j$ 层逐 token 执行的结果。则第 $j+1$ 层收到的输入序列 $z^j_{0:L}$ 与初始 state $S_{j+1}$ 与 reference 相同。由 $\mathcal{C}_{j+1,L}$ 的正确性，第 $j+1$ 层输出与 state 也相同。

归纳到 $N$，得到 $\mathcal{C}^{stack}_L$ 与 $\operatorname{Fold}_{\mathcal{T}^{stack}}^L$ 相同。

<div class="qed" aria-label="证毕">∎</div>

##### 定理 3.14：B0-Transformer chunk prefill 正确性

考虑一个不含 stochastic dropout、且不含非因果 sequence-level 操作的标准自回归 Transformer。每一层由有限个以下 B0 kernel 组合而成：

- token-wise deterministic kernels，例如 embedding、linear projection、output projection、FFN / MLP、norm、residual add、gating。
- causal attention kernels，如定义 3.8。
- 有限个 attention head 的 product / concat，以及后续 token-wise output projection。

position encoding 暂不作为本定理的核心对象。若需要加入 position encoding，则要求它是由 absolute position $P+t$ 或等价 position state 决定的确定性 token-wise augmentation，并且 decode 与 chunk prefill 使用同一个 position 函数。在此前提下，它可并入 token-wise deterministic kernel。

令 $\mathcal{T}^{tr}$ 是该 Transformer 在 B0 中的逐 token decode reference transition，令 $\mathcal{C}^{tr}_L$ 是按层执行的 chunk prefill implementation：每层对长度 $L$ 的序列批量执行 token-wise kernels，并对 attention 使用定理 3.9 的 causal chunk attention。

则对所有 $L\in\mathbb{N}$、输入序列 $x_{0:L}$ 与初始 state $S_0$：

$$
\mathcal{C}^{tr}_L(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}^{tr}}^L(x_{0:L},S_0)
$$

**证明。**

token-wise deterministic kernels 由定理 3.7 满足 chunk prefill 正确性。causal attention kernel 由定理 3.9 满足 chunk prefill 正确性。有限个 attention head 的 product / concat 是有限个相同输入上的 component-wise transition；每个 component 的 chunk 输出与顺序 fold 相同，则它们的 product / concat 也相同。attention 后的 output projection、FFN、norm、residual 等仍是 token-wise kernels。

从一般图角度看，Transformer 的 logical event graph 只包含同一输入位置内部的 layer order、旧 KV cache、当前 chunk 内 causal prefix attention edge，不包含 future-token dependency；position information 若存在，也由 prefix-causal position / clock 函数给出。因此它满足定理 3.6c 的 causal graph correctness 前提。

因此，每个 Transformer layer 都通过 B0 proof gate。由定理 3.13 的有限 B0 chain layer-wise chunk 正确性，整个 Transformer stack 的 chunk prefill implementation 与逐 token decode fold 相同。

<div class="qed" aria-label="证毕">∎</div>

高性能实现见证：token-wise kernels 可批量矩阵化或融合；causal attention 可用 batched QKV、causal mask、FlashAttention-style fused attention 等实现。因此，B0-Transformer 不只是可表达，而且在实数语义下满足 chunk prefill 正确性；具体浮点 backend 的误差属于实现层的数值模拟问题。

##### 定理 3.15：B0-Mamba / SSM chunk prefill 正确性

考虑一个自回归 Mamba / selective SSM stack。每一层由有限个以下 B0 kernel 组合而成：

- token-wise deterministic kernels，例如 input projection、gate projection、output projection、norm、residual add。
- 有限宽 causal convolution。它可表示为有限维 shift-register state 的 affine recurrence，因此属于定理 3.11 的特例。
- selective SSM recurrence。对每个 token $x$，其状态更新可写为：

$$
h'=A_xh+b_x
$$

输出可写为：

$$
y=o(x,h')
$$

其中 $A_x,b_x,o$ 可由当前 token 的 token-wise kernels 决定。

令 $\mathcal{T}^{ssm}$ 是该 Mamba / SSM stack 在 B0 中的逐 token decode reference transition，令 $\mathcal{C}^{ssm}_L$ 是按层执行的 chunk prefill implementation：token-wise kernels 批量执行，causal convolution 与 selective SSM recurrence 使用 parallel prefix / chunk scan 实现。

则对所有 $L\in\mathbb{N}$、输入序列 $x_{0:L}$ 与初始 state $S_0$：

$$
\mathcal{C}^{ssm}_L(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}^{ssm}}^L(x_{0:L},S_0)
$$

**证明。**

token-wise deterministic kernels 由定理 3.7 满足 chunk prefill 正确性。有限宽 causal convolution 是有限维 shift-register 的 affine recurrence，因此由定理 3.11 满足 chunk prefill 正确性。selective SSM recurrence 的状态更新已经写成 $h'=A_xh+b_x$，输出写成 $y=o(x,h')$，因此也由定理 3.11 满足 chunk prefill 正确性。

从一般图角度看，Mamba / SSM 的 logical event graph 只包含同一输入位置内部的 layer order、有限 causal convolution state、SSM prefix recurrence state，不包含 future-token dependency。因此它满足定理 3.6c 的 causal graph correctness 前提。

因此，每个 Mamba / SSM layer 都通过 B0 proof gate。由定理 3.13 的有限 B0 chain layer-wise chunk 正确性，整个 Mamba / SSM stack 的 chunk prefill implementation 与逐 token decode fold 相同。

<div class="qed" aria-label="证毕">∎</div>

高性能实现见证：token-wise kernels 可批量矩阵化或融合；causal convolution 与 selective SSM recurrence 的 affine map 复合满足结合律，可用 parallel prefix / scan / chunk scan 实现。因此，B0-Mamba / SSM 在实数语义下满足 chunk prefill 正确性；具体浮点 backend 的误差属于实现层的数值模拟问题。

### 4. B-family：逐层增加机制

这一节把 B0 扩展为 B1-B6。B0 已经是能表达 Transformer/Mamba 的标准 factorized graph runtime；后续层级不再引入“基本 memory/cache”，而是列出更强的 graph/runtime 机制候选。

B1-B6 不是必须依次完整实现的唯一架构路线，也不是为了最终逐项复刻 LH。它们更准确地说是 extension schema / mechanism catalog：每一层声明一种新增 state、workspace、kernel 或 schedule 约束。研究时可以保留、简化、替换或拒绝某一机制；裁决标准是它是否服务于“局部通信 + 超稀疏”总体目标，并能否在可接受 contract 下获得 chunk prefill correctness 与有意义的 parallel-prefill witness。

只有当某个 schema 与具体 kernel 组合成明确的单步 transition 后，才可应用后面的 B-family 引理。

#### B1：typed edge 与 step-local mailbox

B1 是在 B0 上增加 edge role 与显式 mailbox lifetime 的 schema。它本身不改变 transition 的顺序 fold 语义；真正的 transition 还需要指定 typed edge kernel、aggregation 与 node update。

##### 定义 4.1：edge role

给定有限 edge role 集合 $R_E$ 与 edge role 函数：

$$
\tau_E:E\to R_E
$$

typed edge kernel 可写为：

$$
\phi_{\tau_E(e)}^r:A\times U\to \overline{M}
$$

##### 定义 4.2：mailbox workspace

对每个输入步与内部轮次，引入临时 mailbox：

$$
W_{box}^r=(b_v^r)_{v\in V}
$$

其中 $b_v^r\in\mathcal{B}_v$。

mailbox 不是持久状态。若没有显式 commit，$W_{box}^r$ 不属于下一输入步的 $S'$。

#### B2：phase schedule

B2 不是用来把 Transformer / Mamba 的 $N$ 个 block 拆成 $N$ 个 phase。标准 block 顺序应优先由 B0 chain + rounds 表达。

B2 的用途是表达 LH / Tide 这类 runtime 中的大范围执行阶段划分，例如 input-side update、output-side update、input-to-output bridge、output-to-input bridge、readout cache、pronounce 等。也就是说，phase 更像 role / direction / visibility 的全局 barrier，而不是普通 layer index。

##### 定义 4.3：phase

给定持久状态空间 $\mathcal{S}$ 与 workspace 空间 $\mathcal{W}$。

一个 phase 是三元组：

$$
p=(\operatorname{read}_p,\operatorname{kernel}_p,\operatorname{commit}_p)
$$

其中存在 view 空间 $\mathcal{V}_p$ 与 delta 空间 $\Delta_p$，满足：

$$
\operatorname{read}_p:\mathcal{S}\times\mathcal{W}\to\mathcal{V}_p
$$

$$
\operatorname{kernel}_p:\mathcal{V}_p\to\Delta_p
$$

$$
\operatorname{commit}_p:\mathcal{S}\times\mathcal{W}\times\Delta_p\to\mathcal{S}\times\mathcal{W}
$$

##### 定义 4.4：schedule

一个 flat schedule 是有限 phase 序列：

$$
\Pi=(p_1,\ldots,p_K)
$$

其中 $K\in\mathbb{N}_{>0}$。

此时定义：

$$
\operatorname{flat}(\Pi)=\Pi
$$

若存在 internal round，则先给定 round 数：

$$
R_{\Pi}\in\mathbb{N}_{>0}
$$

并可把 nested schedule 写成 phase 序列的序列：

$$
\Pi=(\Pi^1,\ldots,\Pi^{R_{\Pi}})
$$

其中：

$$
\Pi^r=(p_1^r,\ldots,p_{K_r}^r)
$$

且：

$$
K_r\in\mathbb{N}_{>0},\quad r=1,\ldots,R_{\Pi}
$$

对 nested schedule，定义其展平结果：

$$
\operatorname{flat}(\Pi)=(p_1,\ldots,p_K)
$$

其中：

$$
K=\sum_{r=1}^{R_{\Pi}}K_r
$$

后续 transition 只读取 $\operatorname{flat}(\Pi)$。因此，无论实现上是否保留 internal round 结构，数学上的单步 transition 都是一个有限 phase 序列。

##### 定义 4.5：phase transition

给定 schedule $\Pi$、初始化函数：

$$
\operatorname{Init}:X\times\mathcal{S}\to\mathcal{W}
$$

以及 finalize 函数：

$$
F:\mathcal{S}\times\mathcal{W}\to Y\times\mathcal{S}
$$

定义 phase-based transition：

$$
\mathcal{T}^{phase}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

令：

$$
\operatorname{flat}(\Pi)=(p_1,\ldots,p_K)
$$

对输入 $x$ 与状态 $S$，先令：

$$
(S^0,W^0)=(S,\operatorname{Init}(x,S))
$$

对 $k=1,\ldots,K$：

$$
v_k=\operatorname{read}_{p_k}(S^{k-1},W^{k-1})
$$

$$
\delta_k=\operatorname{kernel}_{p_k}(v_k)
$$

$$
(S^k,W^k)=\operatorname{commit}_{p_k}(S^{k-1},W^{k-1},\delta_k)
$$

最后：

$$
\mathcal{T}^{phase}(x,S)=F(S^K,W^K)
$$

phase schedule 的数学作用是显式规定 barrier、visibility 与 commit order。

##### 约束 4.5a：高性能并行 prefill 的基本语义约束

给定定义 2.1 的 chunk prefill implementation $\mathcal{C}_L$，并令定义 2.2 中的 reference transition 为：

$$
\mathcal{T}=\mathcal{T}^{phase}
$$

若 $\mathcal{C}_L$ 通过并行、融合、重排或 packed layout 实现 $\mathcal{T}^{phase}$，则至少必须保持：

- token causality：位置 $t$ 的输出与状态不得依赖任意 $x_{t'}$，其中 $t'>t$。
- phase barrier：不同 phase 的可见性边界不得被无证明地重排。
- read visibility：每个 $\operatorname{read}_p$ 看到的 state/workspace 与 $\operatorname{Fold}_{\mathcal{T}}^L$ 一致。
- write / commit order：每个 $\operatorname{commit}_p$ 的效果与 $\operatorname{Fold}_{\mathcal{T}}^L$ 一致，除非证明可交换或可结合。
- workspace lifetime：step-local workspace 不得跨输入步泄漏；若固定周期 profile 需要跨边界在途消息，必须把它们显式纳入延续状态。

这些是证明 $\mathcal{C}_L$ 满足定义 2.2 的必要审查项，不是充分条件。

#### B3：selector / controller state

##### 定义 4.6：controller state

给定 controller scope 集合 $C$ 与 controller state space $Q$。

controller state 空间为：

$$
Q^C
$$

若 $q\in Q^C$，则 $q_c$ 是 scope $c\in C$ 的 controller state。

##### 定义 4.7：selector kernel

给定候选记录空间 $\mathcal{C}_{cand}$ 与已选动作/路由记录空间 $\mathcal{R}$。候选记录可以包含空间位置与数值隐藏激活；$\mathcal R$ 表示被选择的记录或动作，不是隐藏 activation value 本身。

selector kernel 是函数：

$$
\sigma:\mathcal{C}_{cand}\times Q^C\to \mathcal{R}\times Q^C
$$

其输出既包含被选择的动作/路由记录，也包含更新后的 controller state。

若 chunk prefill 把多个输入位置的候选集合联合输入 selector，必须证明该联合 selector 与按输入位置顺序应用 $\sigma$ 的 fold 等价。

#### B4：step-local readout cache

##### 定义 4.8：readout cache

给定 cache element space $Z$。若每个输入步内有 $R$ 个 internal round，则 step-local readout cache 空间可写为：

$$
Z^R
$$

对输入位置 $t$ 的 readout cache 记为：

$$
c_t=(z_t^1,\ldots,z_t^R)\in Z^R
$$

约束是：

$$
c_t\text{ 不属于持久状态，且不得被输入位置 }t+1\text{ 读取}
$$

除非它被 finalize 显式写入持久状态。

#### B5：pronounce memory

##### 定义 4.9：pronounce memory

给定 pronounce memory space $P$。

令不含 pronounce memory 的基础持久状态空间为：

$$
\mathcal{S}_{base}
$$

加入 pronounce memory 后，完整持久状态空间为：

$$
\mathcal{S}_{B5}=\mathcal{S}_{base}\times P
$$

完整状态写为：

$$
(S,\pi)\in\mathcal{S}_{base}\times P
$$

其中 $\pi$ 是 pronounce memory。

finalize kernel 可写为：

$$
F:\mathcal{S}_{base}\times Z^R\times P\to Y\times\mathcal{S}_{base}\times P
$$

如果 $P$ 的更新不是可结合 scan，则高性能 chunk prefill 必须按 token 顺序更新 pronounce memory，或提供额外等价性证明。

#### B6：input/output roles 与 bridge

##### 定义 4.10：role-aware graph

给定 node role 集合 $R_V$ 与 edge role 集合 $R_E$。

role-aware graph 为：

$$
G=(V,E,\tau_V,\tau_E,\mathsf{Anc})
$$

其中：

$$
\tau_V:V\to R_V
$$

$$
\tau_E:E\to R_E
$$

$\mathsf{Anc}$ 是 anchor 集合，例如 input anchor、readout anchor、bridge anchor。

对 LH-like runtime，通常至少区分：

$$
V=V_{in}\cup V_{out}
$$

以及：

$$
E=E_{in}\cup E_{out}\cup E_{io}\cup E_{oi}
$$

其中 $E_{io}$ 与 $E_{oi}$ 是有方向的 bridge edge。

##### 定义 4.11：LH-like schedule 约束

LH-like schedule 至少需要定义以下 phase 的 read / commit 语义：

$$
\Pi_{LH}=
(
p_{oi},
p_{input},
p_{io},
p_{in\_update},
p_{out\_update},
p_{cache}
)
$$

其中：

- 每个 $p_*$ 都是定义 4.3 中的 phase。
- $p_{oi}$ 读 output-side 旧状态，写 input-side mailbox。
- $p_{input}$ 在指定 internal round 写 input anchor。
- $p_{io}$ 读 input-side 旧状态，写 output-side mailbox。
- $p_{in\_update}$ 只更新 input-side state namespace。
- $p_{out\_update}$ 只更新 output-side state namespace。
- $p_{cache}$ 只读 output readout anchor，写 step-local readout cache。

B6 已经接近 LH，但它是否等价于 LH C++，还取决于 selector、hidden、KV cache、pronounce 与 tie-breaking 等 kernel 细节是否逐 phase 对齐。

#### 引理 4.12：B-family 的顺序 fold 等价

对任意 $k\in\{0,\ldots,6\}$，若 Bk 定义出一个 transition system：

$$
\mathcal{T}^{Bk}:X\times\mathcal{S}_{Bk}\to Y\times\mathcal{S}_{Bk}
$$

则对任意 $L\in\mathbb{N}$、$x_{0:L}\in X^L$、$S_0\in\mathcal{S}_{Bk}$：

$$
\operatorname{Prefill}^{seq,L}_{\mathcal{T}^{Bk}}(x_{0:L},S_0)
=
\operatorname{Decode}_{\mathcal{T}^{Bk}}^L(x_{0:L},S_0)
$$

**证明。**

由定理 1.5 直接得到。

<div class="qed" aria-label="证毕">∎</div>

### 5. Optimized Kernel 的模拟关系

性能实现通常会改变内部表示，例如 reference layout 与 packed / crossbatch layout 不同。因此需要定义状态等价关系。

#### 定义 5.1：两个 transition systems

给定 reference transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

以及 optimized transition system：

$$
\widehat{\mathcal{T}}:X\times\widehat{\mathcal{S}}\to Y\times\widehat{\mathcal{S}}
$$

其中 $\mathcal{S}$ 与 $\widehat{\mathcal{S}}$ 可以是不同的状态表示空间。

#### 定义 5.2：状态等价关系

定义二元关系：

$$
\sim\ \subseteq \mathcal{S}\times\widehat{\mathcal{S}}
$$

若：

$$
S\sim\widehat{S}
$$

则表示 $S$ 与 $\widehat{S}$ 语义上代表同一个运行时状态。

例子：

- per-sample KV list 与 batch KV cache 表示同一组 KV。
- sparse activation vector 与 packed active rows 表示同一组数值隐藏激活。
- vector selector count 与 tensor selector count 表示同一组 controller state。

#### 定义 5.3：step simulation

称 $\widehat{\mathcal{T}}$ step-simulates $\mathcal{T}$，当且仅当对任意 $x\in X$、$S\in\mathcal{S}$、$\widehat{S}\in\widehat{\mathcal{S}}$，若：

$$
S\sim\widehat{S}
$$

且：

$$
\mathcal{T}(x,S)=(y,S')
$$

$$
\widehat{\mathcal{T}}(x,\widehat{S})=(\widehat{y},\widehat{S}')
$$

则：

$$
y=\widehat{y}
$$

且：

$$
S'\sim\widehat{S}'
$$

在工程实现中，若存在浮点重排，可把 $y=\widehat{y}$ 替换为预先声明的数值容差关系，例如 `allclose`。但 $S'\sim\widehat{S}'$ 仍必须明确说明。

#### 定理 5.4：step simulation 推出序列级等价

若：

$$
S_0\sim\widehat{S}_0
$$

且 $\widehat{\mathcal{T}}$ step-simulates $\mathcal{T}$，则对任意 $L\in\mathbb{N}$ 与 $x_{0:L}\in X^L$：

$$
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)=(y_{0:L},S_L)
$$

$$
\operatorname{Fold}_{\widehat{\mathcal{T}}}^L(x_{0:L},\widehat{S}_0)=(\widehat{y}_{0:L},\widehat{S}_L)
$$

蕴含：

$$
y_{0:L}=\widehat{y}_{0:L}
$$

且：

$$
S_L\sim\widehat{S}_L
$$

**证明。**

对 $L$ 归纳。

当 $L=0$ 时，由 $S_0\sim\widehat{S}_0$ 与空输出序列得到结论。

假设长度 $L$ 成立。考虑长度 $L+1$。前 $L$ 个 token 后，由归纳假设得到：

$$
y_{0:L}=\widehat{y}_{0:L}
$$

且：

$$
S_L\sim\widehat{S}_L
$$

由 step simulation，对 token $x_L$ 可得：

$$
y_L=\widehat{y}_L
$$

且：

$$
S_{L+1}\sim\widehat{S}_{L+1}
$$

因此长度 $L+1$ 成立。

<div class="qed" aria-label="证毕">∎</div>

#### 推论 5.5：kernel 等价证明路线

若 optimized implementation 能逐 phase 保持：

- read scope。
- write target。
- commit timing。
- workspace lifetime。
- persistent state equivalence。

并且每个 optimized phase 在状态等价关系下模拟 reference phase，则 optimized StepTransition step-simulates reference StepTransition。

由定理 5.4，optimized sequence 与 reference sequence 等价。

### 6. 当前数学结论

- `prefill = decode fold` 只有在顺序 fold 语义下由定义成立。
- chunk prefill correctness 永远相对于一个 reference semantic contract；对 coarse quotient 正确，不推出对 fine contract 正确。
- 真正需要证明的是 chunk implementation 是否满足 [[#^eq-chunk-prefill-correctness|式 (2.1)]]。
- 定理 3.6c 给出一般 B0 Logical Event DAG Theorem：若 chunk implementation 计算的是同一个 logical event DAG、同一组 kernel equation、同一个 output/final-state extraction，则 correctness 成立。它允许物理执行乱序，但不允许 logical dependency / visibility / commit order 被打乱。
- 定理 3.6f 给出 Aggregation Quotient Theorem：不可逆聚合只有在构成 semantics-preserving quotient 时才安全；tagged aggregation 与同一 logical event 内确定性聚合是安全特例。
- 定理 3.6i 把 transition semantic quotient、logical event DAG 与 event-level aggregation quotient 合并为 Unified Contract-DAG-Quotient Theorem。
- 定义 3.6k-3.6l 用 uniform primitives、explicit lowering、no-oracle condition 与完整 work/span ledger 排除无意义的单事件顶点 fold，并区分 correctness certificate 与 parallel-prefill witness。
- B0 proof gate 先证明 token-wise / FFN、causal attention、affine scan recurrence、linear attention accumulator 以及有限 layer stack 这些主流 kernel family 的 chunk prefill 正确性；在这些结果上，定理 3.14 给出 B0-Transformer chunk prefill 正确性，定理 3.15 给出 B0-Mamba / SSM chunk prefill 正确性。
- 上述命名定理不推出任意 B0 graph / 任意 B0 kernel 都有高性能 chunk prefill；它们证明的是 Transformer / Mamba 这类主力结构在 B0 中满足 $\mathcal{C}_L=\operatorname{Fold}_{\mathcal{T}}^L$。
- B1-B6 是 mechanism catalog，不是必须完整复刻 LH 的唯一升级路径；每个机制都可保留、修改、替换或拒绝。
- selector、pronounce memory、KV append、phase barrier、workspace lifetime 是最容易破坏 chunk/prefill 等价的机制。
- packed / crossbatch / backend lowering 的正确证明入口是 step simulation，而不是只比较最终 logits。

### 7. 第一部分之后的完成项与未决项

整合后的第四部分已经给出有限事件秩引理、zero-delay 环没有普通拓扑求值顺序的命题，以及禁止隐藏恢复成本的 strict-core 约束。第二部分已经给出显式 allocator 空间 DAG 的拓扑序构造。它们不应继续列为“尚未开始”的候选。

当前仍需证明或实现的目标是：

1. **Dependency-Complete Local Refinement Theorem**：把第一部分已有的 event-DAG、quotient 与 simulation 结果整理为一个显式覆盖数据、状态、控制、可见性和提交依赖的局部 refinement 定理。
2. **Allocator 时间分块组合律**：定义逐绝对轮次节点参考转移，并证明第二部分式 A-6.3，而不是把节点分块等价直接作为前提。
3. **Dynamic/Cyclic Tide Instantiation**：对带正时延反馈的静态环给出有限窗口展开与 boundary-state contract；零延迟 SCC 只允许进入独立 implicit-kernel family。
4. **Capability Witness**：为 mailbox、phase、selector、readout、pronounce 及主力 node kernel 分别给出低-span lowering 或显式 sequential fallback 成本。
5. **Backward 与数值语义**：在 exact reference contract 稳定后，再声明浮点容差、梯度边界、重计算和跨 chunk BPTT 规则。

---

## 第二部分：显式 allocator 的一般空间 DAG



> [!summary] 本页定位
> 本部分是 Tide `prefill / decode` 正向设计的当前主线候选。它先把最低层模型收缩为：有限空间 DAG、单位边时延、节点持有状态、带到达轮次的消息、边界延续状态、显式 allocator 节点和节点级 artifact equality。`owner / frontier` 不作为本部分核心前提；它们是第三部分用于证明 token 因果性、读出归因和细粒度调试的增强字段。

> [!important] 核心结论
> 显式 allocator 方案可以处理不等长路径。只要空间图是 DAG，allocator 也是 DAG 中的普通节点，并且每个窗口级节点转导器只读取自己的左边界状态与拓扑上游消息，那么窗口执行方程可以按节点拓扑序唯一构造。一次 chunk 调度只需调用每个节点一次；每个节点内部可以批量处理当前 chunk 中到达本节点的所有消息。

> [!warning] 本页不自动证明的内容
> 本部分首先证明空间方向的拓扑序 chunk 构造与 artifact equality，不把同一组窗口方程循环命名为“流式执行”。要进一步证明真正的 `prefill = decode`，还必须定义逐绝对轮次的节点参考转移，并证明窗口级节点转导器等于这些逐轮转移的折叠。节点内部若使用 attention、SSM、scan、分段打包、稀疏选择或 learned routing，也需要分别证明相应实现满足这个时间组合律与同一个节点参考语义。

### 0. 写作规则与基础记号

#### 定义 0.1：正式对象规则

本文中进入定义、引理、定理或证明的对象，必须在使用前被声明为下列对象之一：

1. 集合。
2. 集合元素。
3. 函数或部分函数。
4. 关系。
5. 有限序列。
6. 有限元组。
7. 由上述对象定义出的性质。

直观说明可以保留，但不承担证明前提。若一个词在证明中起作用，它必须能回溯到某个集合、函数、关系、有限序列或有限元组。

#### 定义 0.2：自然数、有限区间与序列

定义自然数集合：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $n\in\mathbb N$，定义：

$$
[n]=\{0,1,\ldots,n-1\}.
$$

若 $A$ 是集合，定义 $A^\star$ 为 $A$ 上所有有限序列构成的集合：

$$
A^\star=\bigcup_{n\in\mathbb N}A^n.
$$

若 $\mathbf a=(a_0,\ldots,a_{n-1})\in A^n$，定义：

$$
\operatorname{len}(\mathbf a)=n.
$$

定义 $A$ 的有限子集集合：

$$
\mathcal P_{\mathrm{fin}}(A)=\{S\subseteq A\mid S\text{ 是有限集}\}.
$$

定义有限序列的元素集合函数：

$$
\operatorname{elem}_A:A^\star\to\mathcal P_{\mathrm{fin}}(A)
$$

如下：

$$
\operatorname{elem}_A(\mathbf a)
=
\{a_i\mid i\in[\operatorname{len}(\mathbf a)]\}.
\tag{D-0.2a}
$$

若 $I$ 是有限集，且对每个 $i\in I$ 给定集合 $A_i$，定义有限笛卡尔积：

$$
\prod_{i\in I}A_i
=
\{f\mid f:I\to\bigcup_{i\in I}A_i
\text{ 且 } f(i)\in A_i\text{ 对每个 }i\in I\}.
\tag{D-0.2b}
$$

#### 定义 0.3：窗口位置集合

给定 $B,L\in\mathbb N$，定义长度为 $L$、从全局位置 $B$ 开始的窗口位置集合：

$$
\mathbb I_{B,L}=\{B,B+1,\ldots,B+L-1\}.
\tag{D-0.3}
$$

若 $L=0$，则 $\mathbb I_{B,0}=\varnothing$。

### 1. 输入流、绝对轮次与边界切面

#### 定义 1.1：输入输出集合与全局输入流

给定非空集合 $X$ 与 $Y$，分别称为输入值集合与输出值集合。

给定函数：

$$
x:\mathbb N\to X,
$$

称为全局输入流。对 $t\in\mathbb N$，元素 $x_t=x(t)$ 是第 $t$ 个输入值。

对窗口 $(B,L)$，定义当前 chunk：

$$
x_{B:B+L}\in X^{\mathbb I_{B,L}},
\qquad
x_{B:B+L}(t)=x_t.
\tag{D-1.1}
$$

#### 定义 1.2：外部周期与边界切面

给定常数：

$$
R\in\mathbb N_{>0},
$$

称为外部输入周期。定义边界切面函数：

$$
\beta:\mathbb N\to\mathbb N,
\qquad
\beta(b)=Rb.
\tag{D-1.2}
$$

第 $t$ 个输入值注入的绝对轮次定义为：

$$
\tau_{\mathrm{in}}(t)=\beta(t)=Rt.
\tag{D-1.3}
$$

定义第 $t$ 个输出位置的名义读出切面：

$$
\tau_{\mathrm{read}}(t)=\beta(t+1)=R(t+1).
\tag{D-1.4}
$$

窗口 $(B,L)$ 的内部可消费轮次集合定义为：

$$
\mathbb T_{B,L}
=
\{\tau\in\mathbb N\mid \beta(B)\leq\tau<\beta(B+L)\}.
\tag{D-1.5}
$$

直观地说，$B$ 和 $B+L$ 是输入位置边界，$\beta(B)$ 和 $\beta(B+L)$ 是执行切面。当前窗口从左切面继续执行，到右切面停止；没有在右切面前消费完的消息进入右边界延续状态。

### 2. 一般空间 DAG 与单位边时延

#### 定义 2.1：有限空间 DAG

给定有限非空集合 $V$ 和关系：

$$
E\subseteq V\times V.
$$

定义空间图：

$$
G=(V,E).
$$

固定两个不同元素：

$$
v_{\mathrm{in}},v_{\mathrm{out}}\in V,
\qquad
v_{\mathrm{in}}\neq v_{\mathrm{out}},
$$

分别称为输入节点与输出节点。

称 $G$ 是 DAG，当且仅当不存在 $k\in\mathbb N_{>0}$ 和序列 $(v_0,\ldots,v_k)\in V^{k+1}$ 满足：

$$
v_0=v_k,
\qquad
(v_i,v_{i+1})\in E\quad(i\in[k]).
$$

对 $a,b\in V$，从 $a$ 到 $b$ 的有向路径是一个有限序列 $(u_0,\ldots,u_k)\in V^{k+1}$，其中 $k\in\mathbb N$，并且：

$$
u_0=a,\qquad u_k=b,
$$

且对每个 $i\in[k]$：

$$
(u_i,u_{i+1})\in E.
$$

本文要求：

1. 不存在 $u\in V$ 使 $(u,v_{\mathrm{in}})\in E$。
2. 对每个 $v\in V$，存在从 $v_{\mathrm{in}}$ 到 $v$ 的有向路径。
3. 对每个 $v\in V$，存在从 $v$ 到 $v_{\mathrm{out}}$ 的有向路径。

这些条件不要求所有从 $v_{\mathrm{in}}$ 到 $v_{\mathrm{out}}$ 的路径等长。

#### 定义 2.2：前驱、后继与拓扑序

对 $v\in V$，定义前驱集合与后继集合：

$$
\operatorname{Pred}_G(v)=\{u\in V\mid(u,v)\in E\},
\qquad
\operatorname{Succ}_G(v)=\{u\in V\mid(v,u)\in E\}.
\tag{D-2.2}
$$

空间拓扑序是有限序列：

$$
\pi=(v_0,\ldots,v_{|V|-1})\in V^{|V|}
$$

满足：

$$
\{v_i\mid i\in[|V|]\}=V,
$$

且若 $(v_i,v_j)\in E$，则 $i<j$。

#### 引理 2.3：有限 DAG 存在拓扑序

若 $G=(V,E)$ 满足定义 2.1，则至少存在一个定义 2.2 意义下的拓扑序。

**证明。**

先证明任意有限非空 DAG 的任意非空诱导子图至少有一个入度为零的节点。若某个非空诱导子图中的每个节点都有来自该子图的入边，则从其中任意节点开始不断沿入边向前选择节点。由于该诱导子图的节点集合有限，所得序列中必有重复节点，从而得到有向环，与原图为 DAG 矛盾。

从 $V$ 开始，反复在当前非空诱导子图中选择一个入度为零的节点，把它追加到序列末尾，再从当前节点集合中删除它。每一步都能由上一段的结论完成；经过 $|V|$ 步后得到包含 $V$ 中每个节点恰好一次的序列。若 $(u,v)\in E$，则删除 $v$ 时 $u$ 不可能仍在当前节点集合中，否则 $v$ 的当前入度不为零。因此 $u$ 必在 $v$ 之前被追加，所得序列是拓扑序。

<div class="qed" aria-label="证毕">∎</div>

#### 定义 2.4：空间深度与拓扑层

对 $v\in V$，定义：

$$
\mathsf{Path}_{G}(v)
=
\bigcup_{k\in\mathbb N}
\left\{
(u_0,\ldots,u_k)\in V^{k+1}
\ \middle|\
u_0=v_{\mathrm{in}},\ u_k=v,
(u_i,u_{i+1})\in E\text{ 对每个 }i\in[k]
\right\}.
$$

$\mathsf{Path}_{G}(v)$ 的元素称为从 $v_{\mathrm{in}}$ 到 $v$ 的有向路径。若路径属于 $V^{k+1}$，定义其长度为 $k$。因为 $G$ 是有限 DAG，一条有向路径不可能重复经过同一节点，所以 $\mathsf{Path}_{G}(v)$ 是有限非空集合。

定义空间深度函数：

$$
d_G:V\to\mathbb N,
\qquad
d_G(v)=\max\{k\in\mathbb N\mid
\mathsf{Path}_{G}(v)\text{ 中存在长度为 }k\text{ 的路径}\}.
\tag{D-2.4a}
$$

定义：

$$
D_G=1+\max\{d_G(v)\mid v\in V\},
\qquad
V_j=\{v\in V\mid d_G(v)=j\}
\quad(j\in[D_G]).
\tag{D-2.4b}
$$

有限性与定义 2.1 的可达性保证上述最大值存在。若 $(u,v)\in E$，则任意一条到达 $u$ 的最长路径后接边 $(u,v)$ 得到一条到达 $v$ 的路径，所以：

$$
d_G(u)<d_G(v).
\tag{A-2.4}
$$

因此 $(V_0,\ldots,V_{D_G-1})$ 是 $V$ 的一个分割，同一 $V_j$ 内不存在空间边。取一个深度为 $D_G-1$ 的节点及到达它的一条最长路径；式 A-2.4 保证该路径依次经过深度 $0,1,\ldots,D_G-1$ 的节点，所以每个 $V_j$ 都非空。这里的空间深度只是由一般 DAG 导出的并行调度分层；它不要求所有到达同一节点的路径等长，也不把一般 DAG 改成 leveled DAG。

#### 定义 2.5：单位边时延

给定非空集合 $\mathsf{Payload}$，称为消息载荷集合。定义消息标识符集合：

$$
\mathsf{MID}=V\times\mathbb N\times\mathbb N.
$$

标识符 $(u,\tau,j)\in\mathsf{MID}$ 的三个坐标分别表示源节点、发送绝对轮次和该源节点在该轮次使用的局部序号。定义三个投影函数：

$$
\operatorname{idnode}:\mathsf{MID}\to V,
\qquad
\operatorname{idtime}:\mathsf{MID}\to\mathbb N,
\qquad
\operatorname{idserial}:\mathsf{MID}\to\mathbb N
$$

为：

$$
\operatorname{idnode}(u,\tau,j)=u,
\quad
\operatorname{idtime}(u,\tau,j)=\tau,
\quad
\operatorname{idserial}(u,\tau,j)=j.
$$

定义候选消息记录集合：

$$
\mathfrak M
=
\mathsf{MID}\times\mathbb N\times\mathbb N\times V\times V\times\mathsf{Payload}.
$$

定义投影函数：

$$
\operatorname{id}:\mathfrak M\to\mathsf{MID},
\qquad
\operatorname{send}:\mathfrak M\to\mathbb N,
\qquad
\operatorname{arrival}:\mathfrak M\to\mathbb N,
$$

$$
\operatorname{src}:\mathfrak M\to V,
\qquad
\operatorname{dst}:\mathfrak M\to V,
\qquad
\operatorname{payload}:\mathfrak M\to\mathsf{Payload}.
$$

若 $m=(\iota,\tau_s,\tau_a,u,v,p)$，规定：

$$
\operatorname{id}(m)=\iota,
\quad
\operatorname{send}(m)=\tau_s,
\quad
\operatorname{arrival}(m)=\tau_a,
$$

$$
\operatorname{src}(m)=u,
\quad
\operatorname{dst}(m)=v,
\quad
\operatorname{payload}(m)=p.
$$

定义有效消息集合：

$$
\mathsf{Msg}_G
=
\{m\in\mathfrak M
\mid
(\operatorname{src}(m),\operatorname{dst}(m))\in E
\text{ 且 }
\operatorname{arrival}(m)=\operatorname{send}(m)+1,
\operatorname{idnode}(\operatorname{id}(m))=\operatorname{src}(m),
\operatorname{idtime}(\operatorname{id}(m))=\operatorname{send}(m)
\}.
\tag{D-2.5}
$$

这就是单位边时延：沿一条空间边发送的消息在下一个绝对轮次到达。

### 3. 节点状态与边界延续状态

#### 定义 3.1：节点状态

对每个 $v\in V$，给定非空集合 $\mathcal S_v$，称为节点 $v$ 的状态集合。

定义全图状态集合：

$$
\mathcal S_G=\prod_{v\in V}\mathcal S_v.
\tag{D-3.1}
$$

若 $\mathbf S\in\mathcal S_G$，则 $\mathbf S(v)\in\mathcal S_v$ 表示节点 $v$ 的状态。

状态只由所属节点持有。若一个 allocator 需要历史负载估计、quota 计数或 learned routing 参数，它们必须是该 allocator 节点状态集合 $\mathcal S_v$ 的坐标，或经由上游消息输入，而不是隐藏全局变量。

#### 定义 3.2：消息标识符唯一性

若 $M\in\mathcal P_{\mathrm{fin}}(\mathsf{Msg}_G)$，定义性质 $\operatorname{UniqueMID}(M)$ 为：

$$
\operatorname{UniqueMID}(M)
\Longleftrightarrow
\bigl(
\forall m,m'\in M,
\operatorname{id}(m)=\operatorname{id}(m')
\Longrightarrow m=m'
\bigr).
\tag{D-3.2}
$$

该性质表示 $M$ 中一个消息标识符至多对应一条消息记录。

#### 定义 3.3：边界延续状态

对 $b\in\mathbb N$，定义边界 $b$ 的延续状态集合：

$$
\mathsf{Cont}_b
=
\left\{
(\mathbf S,M)\in
\mathcal S_G\times\mathcal P_{\mathrm{fin}}(\mathsf{Msg}_G)
\ \middle|\
\operatorname{UniqueMID}(M)
\text{ 且 }
\forall m\in M,
\operatorname{arrival}(m)=\beta(b)
\right\}.
\tag{D-3.3}
$$

若 $C_b=(\mathbf S^b,\mathcal M_b^\partial)\in\mathsf{Cont}_b$，则 $\mathbf S^b$ 是切面 $\beta(b)$ 左侧已经提交的节点状态，$\mathcal M_b^\partial$ 是恰好在该切面到达、尚未被消费的消息集合。因为每条边的时延为 $1$，已经发送但尚未消费的消息不可能跨越多个未来轮次；若以后允许大于 $1$ 的边时延，式 D-3.3 才需要改回到达轮次不小于 $\beta(b)$ 的形式。

本文采用约定：所有到达轮次小于 $\beta(b)$ 的历史消息已经被消费，其影响已经包含在 $\mathbf S^b$ 中。由单位边时延可知，$b=0$ 时 $\mathcal M_0^\partial=\varnothing$。

### 4. 显式 allocator 节点与节点转导器

#### 定义 4.1：节点角色

定义角色集合：

$$
\mathsf{Role}
=
\{\mathtt{input},\mathtt{output},\mathtt{compute},\mathtt{allocator}\}.
$$

给定函数：

$$
\operatorname{role}:V\to\mathsf{Role}.
\tag{D-4.1}
$$

要求：

$$
\operatorname{role}^{-1}(\{\mathtt{input}\})=\{v_{\mathrm{in}}\},
\qquad
\operatorname{role}^{-1}(\{\mathtt{output}\})=\{v_{\mathrm{out}}\}.
$$

若 $\operatorname{role}(v)=\mathtt{allocator}$，称 $v$ 为显式 allocator 节点。allocator 不是隐藏调度器；它只是空间 DAG 中的一个节点。

#### 定义 4.2：输入原子、时间桶与节点输入序列

定义输入原子标签集合：

$$
\mathsf{AtomTag}=\{\mathtt{inj},\mathtt{msg}\},
\qquad
\mathtt{inj}\neq\mathtt{msg}.
$$

对节点 $v\in V$，定义输入原子集合：

$$
\mathsf{Atom}_{v,B,L}
=
\left(
\{\mathtt{msg}\}\times\{m\in\mathsf{Msg}_G\mid\operatorname{dst}(m)=v\}
\right)
\cup
\mathsf{InjAtom}_{v,B,L},
$$

其中：

$$
\mathsf{InjAtom}_{v,B,L}
=
\begin{cases}
\{\mathtt{inj}\}\times\mathbb I_{B,L}\times X,&v=v_{\mathrm{in}},\\
\varnothing,&v\neq v_{\mathrm{in}}.
\end{cases}
$$

定义输入原子的时间函数：

$$
\operatorname{atime}_{v,B,L}:\mathsf{Atom}_{v,B,L}\to\mathbb N
$$

如下。若 $a=(\mathtt{msg},m)$，则：

$$
\operatorname{atime}_{v,B,L}(a)=\operatorname{arrival}(m).
$$

若 $v=v_{\mathrm{in}}$ 且 $a=(\mathtt{inj},t,x)$，其中 $t\in\mathbb I_{B,L}$ 且 $x\in X$，则：

$$
\operatorname{atime}_{v,B,L}(a)=\tau_{\mathrm{in}}(t).
$$

定义时间桶集合：

$$
\mathsf{Bucket}_{v,B,L}
=
\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_{v,B,L}).
$$

元素 $(\tau,A)\in\mathsf{Bucket}_{v,B,L}$ 合法，当且仅当对每个 $a\in A$：

$$
\operatorname{atime}_{v,B,L}(a)=\tau.
\tag{A-4.2a}
$$

定义节点输入序列集合：

$$
\mathfrak U_{v,B,L}
=
\bigcup_{n\in\mathbb N}
\left\{
((\tau_0,A_0),\ldots,(\tau_{n-1},A_{n-1}))
\in\mathsf{Bucket}_{v,B,L}^{n}
\ \middle|\
\begin{array}{l}
\forall i\in[n],\ \forall a\in A_i,
\operatorname{atime}_{v,B,L}(a)=\tau_i,\\
\forall i\in[n],\ \tau_i\in\mathbb T_{B,L}
\text{ 且 }A_i\neq\varnothing,\\
\forall i\in\{j\in\mathbb N\mid j+1<n\},\
\tau_i<\tau_{i+1}
\end{array}
\right\}.
\tag{D-4.2b}
$$

时间桶允许一个节点在同一绝对轮次联合处理多个消息或注入原子。是否在桶内进一步排序、联合计算或按子 kernel 打包，是节点转导器的内部语义。

#### 定义 4.3：路由记录、局部输出与提交记录

给定非空集合 $\mathsf{RID}$、$\mathsf{OID}$ 与 $\mathsf{Meta}$，分别称为路由记录标识符集合、局部输出标识符集合与元数据集合。

对节点 $v\in V$，定义路由记录集合：

$$
\mathsf{Route}_v
=
\{(\rho,\tau,w,U,\mu)
\in
\mathsf{RID}\times\mathbb N\times V\times\mathcal P_{\mathrm{fin}}(\operatorname{Succ}_G(v))\times\mathsf{Meta}
\mid
w=v\}.
\tag{D-4.3a}
$$

定义投影函数：

$$
\operatorname{rid}:\mathsf{Route}_v\to\mathsf{RID},
\qquad
\operatorname{rtime}:\mathsf{Route}_v\to\mathbb N,
\qquad
\operatorname{rnode}:\mathsf{Route}_v\to V,
$$

$$
\operatorname{rdst}:\mathsf{Route}_v\to\mathcal P_{\mathrm{fin}}(\operatorname{Succ}_G(v)),
\qquad
\operatorname{rmeta}:\mathsf{Route}_v\to\mathsf{Meta}.
$$

若 $r=(\rho,\tau,v,U,\mu)\in\mathsf{Route}_v$，规定：

$$
\operatorname{rid}(r)=\rho,
\quad
\operatorname{rtime}(r)=\tau,
\quad
\operatorname{rnode}(r)=v,
\quad
\operatorname{rdst}(r)=U,
\quad
\operatorname{rmeta}(r)=\mu.
$$

定义节点 $v$ 的提交记录集合：

$$
\mathsf{Commit}_v=\mathbb N\times\mathcal S_v.
\tag{D-4.3b}
$$

定义输出节点的局部输出记录集合：

$$
\mathsf{Out}_{v_{\mathrm{out}},B,L}
=
\mathsf{OID}\times\mathbb I_{B,L}\times Y.
\tag{D-4.3c}
$$

对 $v\neq v_{\mathrm{out}}$，定义：

$$
\mathsf{Out}_{v,B,L}
=
\mathsf{OID}\times\mathsf{Meta}.
\tag{D-4.3d}
$$

对每个 $v\in V$，定义局部输出标识符投影：

$$
\operatorname{oid}_{v,B,L}:
\mathsf{Out}_{v,B,L}\to\mathsf{OID}
$$

为元组第一坐标，即：

$$
\operatorname{oid}_{v_{\mathrm{out}},B,L}(\omega,t,y)=\omega,
\qquad
\operatorname{oid}_{v,B,L}(\omega,\mu)=\omega
\quad(v\neq v_{\mathrm{out}}).
\tag{D-4.3e}
$$

#### 定义 4.4：节点 artifact、投影函数与合法性

对节点 $v\in V$，先定义节点原始产物集合：

$$
\mathfrak A_{v,B,L}
=
\mathsf{Out}_{v,B,L}^\star
\times
\mathsf{Commit}_v^\star
\times
\mathsf{Route}_v^\star
\times
\mathsf{Msg}_G^\star
\times
\mathcal S_v.
\tag{D-4.4}
$$

五个坐标依次是：

1. 局部输出记录序列。
2. 状态提交记录序列。
3. 路由记录序列。
4. 出站消息序列。
5. 右侧节点状态。

定义投影函数：

$$
\operatorname{localOut}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Out}_{v,B,L}^\star,
$$

$$
\operatorname{commits}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Commit}_v^\star,
$$

$$
\operatorname{routes}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Route}_v^\star,
$$

$$
\operatorname{outbox}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Msg}_G^\star,
$$

$$
\operatorname{state}^+_{v,B,L}:\mathfrak A_{v,B,L}\to\mathcal S_v.
$$

若：

$$
A=(O,Q,R_s,M_s,S^+)\in\mathfrak A_{v,B,L},
$$

规定：

$$
\operatorname{localOut}_{v,B,L}(A)=O,
\quad
\operatorname{commits}_{v,B,L}(A)=Q,
\quad
\operatorname{routes}_{v,B,L}(A)=R_s,
$$

$$
\operatorname{outbox}_{v,B,L}(A)=M_s,
\quad
\operatorname{state}^+_{v,B,L}(A)=S^+.
$$

称 $A\in\mathfrak A_{v,B,L}$ 是合法节点产物，当且仅当满足以下条件。

第一，提交记录只提交当前窗口内部轮次。对每个 $(\tau,S)\in\operatorname{elem}_{\mathsf{Commit}_v}(\operatorname{commits}_{v,B,L}(A))$：

$$
\tau\in\mathbb T_{B,L}.
\tag{A-4.4a}
$$

第二，路由记录只属于当前节点与当前窗口内部轮次。对每个 $r\in\operatorname{elem}_{\mathsf{Route}_v}(\operatorname{routes}_{v,B,L}(A))$：

$$
\operatorname{rnode}(r)=v,
\qquad
\operatorname{rtime}(r)\in\mathbb T_{B,L}.
\tag{A-4.4b}
$$

第三，出站消息必须由当前节点在当前窗口内部轮次发送。对每个 $m\in\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{v,B,L}(A))$：

$$
\operatorname{src}(m)=v,
\qquad
\operatorname{send}(m)\in\mathbb T_{B,L}.
\tag{A-4.4c}
$$

第四，每条出站消息必须被某条路由记录覆盖。对每个 $m\in\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{v,B,L}(A))$，存在 $r\in\operatorname{elem}_{\mathsf{Route}_v}(\operatorname{routes}_{v,B,L}(A))$ 使：

$$
\operatorname{send}(m)=\operatorname{rtime}(r),
\qquad
\operatorname{dst}(m)\in\operatorname{rdst}(r).
\tag{A-4.4d}
$$

第五，出站消息序列中的标识符两两不同。若：

$$
\operatorname{outbox}_{v,B,L}(A)=(m_0,\ldots,m_{n-1}),
$$

则对任意 $i,j\in[n]$：

$$
\operatorname{id}(m_i)=\operatorname{id}(m_j)
\Longrightarrow
i=j.
\tag{A-4.4e}
$$

第六，路由记录序列中的标识符两两不同。若：

$$
\operatorname{routes}_{v,B,L}(A)=(r_0,\ldots,r_{q-1}),
$$

则对任意 $i,j\in[q]$：

$$
\operatorname{rid}(r_i)=\operatorname{rid}(r_j)
\Longrightarrow i=j.
\tag{A-4.4f}
$$

第七，局部输出记录序列中的标识符两两不同。若：

$$
\operatorname{localOut}_{v,B,L}(A)=(o_0,\ldots,o_{p-1}),
$$

则对任意 $i,j\in[p]$：

$$
\operatorname{oid}_{v,B,L}(o_i)
=
\operatorname{oid}_{v,B,L}(o_j)
\Longrightarrow i=j.
\tag{A-4.4g}
$$

定义节点完整产物集合：

$$
\mathsf{Artifact}_{v,B,L}
=
\{A\in\mathfrak A_{v,B,L}\mid A\text{ 是合法节点产物}\}.
\tag{D-4.4h}
$$

#### 定义 4.5：节点参考转导器

节点参考转导器是确定函数：

$$
\operatorname{Ref}_{v,B,L}:
\mathfrak U_{v,B,L}\times\mathcal S_v
\to
\mathsf{Artifact}_{v,B,L}.
\tag{D-4.5}
$$

allocator 节点没有特殊的隐藏输入。若 $v$ 是 allocator，则 $\operatorname{Ref}_{v,B,L}$ 仍只能读取 $\mathbf U_v\in\mathfrak U_{v,B,L}$ 与左边界状态 $S_v^B\in\mathcal S_v$，并通过路由记录和出站消息影响拓扑下游节点。

#### 定义 4.6：实现节点算子与精确节点契约

节点实现算子是函数：

$$
\mathcal C_{v,B,L}:
\mathfrak U_{v,B,L}\times\mathcal S_v
\to
\mathsf{Artifact}_{v,B,L}.
\tag{D-4.6}
$$

称 $\mathcal C_{v,B,L}$ 满足精确节点契约，当且仅当对所有 $\mathbf U\in\mathfrak U_{v,B,L}$ 与 $S\in\mathcal S_v$：

$$
\mathcal C_{v,B,L}(\mathbf U,S)
=
\operatorname{Ref}_{v,B,L}(\mathbf U,S).
\tag{A-4.6}
$$

该等式比较定义 4.4 中五个坐标的完整相等，而不仅是最终输出或最终状态。由于值域是 $\mathsf{Artifact}_{v,B,L}$，参考转导器和实现节点算子都只能返回合法节点产物。

#### 定义 4.7：发送激活与实际发送目标

给定 $A\in\mathsf{Artifact}_{v,B,L}$，定义节点 $v$ 的发送激活轮次集合：

$$
\operatorname{Active}_{v,B,L}(A)
=
\{\tau\in\mathbb T_{B,L}\mid
\exists m\in
\operatorname{elem}_{\mathsf{Msg}_G}
(\operatorname{outbox}_{v,B,L}(A)),
\operatorname{send}(m)=\tau\}.
\tag{D-4.7a}
$$

若 $\tau\in\operatorname{Active}_{v,B,L}(A)$，称节点 $v$ 在绝对轮次 $\tau$ 发生一次发送激活。定义该轮次的实际发送目标集合：

$$
\operatorname{SentDst}_{v,B,L}(A,\tau)
=
\{\operatorname{dst}(m)\mid
m\in\operatorname{elem}_{\mathsf{Msg}_G}
(\operatorname{outbox}_{v,B,L}(A)),
\operatorname{send}(m)=\tau\}.
\tag{D-4.7b}
$$

发送激活只表示“至少产生一条发往空间后继的消息”。条件 $\tau\notin\operatorname{Active}_{v,B,L}(A)$ 不禁止节点状态变化；是否变化由节点参考转导器决定，并通过提交记录与右侧节点状态进入 artifact。路由记录中的 $\operatorname{rdst}(r)$ 是参考语义声明的允许或选择目标，而 $\operatorname{SentDst}_{v,B,L}(A,\tau)$ 是出站消息实际到达的目标。式 A-4.4d 只要求实际发送目标被某条同轮次路由记录覆盖，不要求每个被声明的目标都产生消息。

### 5. 窗口执行与拓扑序 chunk 调度

#### 定义 5.1：节点入站原子构造

固定窗口 $(B,L)$、左边界延续状态：

$$
C_B=(\mathbf S^B,\mathcal M_B^\partial)\in\mathsf{Cont}_B,
$$

对每个节点 $v\in V$，定义其前驱 artifact 赋值集合：

$$
\mathsf{PredArtifact}_{v,B,L}
=
\prod_{u\in\operatorname{Pred}_G(v)}
\mathsf{Artifact}_{u,B,L}.
\tag{D-5.1a}
$$

取 $\mathbf P_v\in\mathsf{PredArtifact}_{v,B,L}$。对节点 $v\in V$，定义候选入站消息集合：

$$
\mathcal M_v(\mathbf P_v)
=
\{m\in\mathcal M_B^\partial\mid\operatorname{dst}(m)=v\}
\cup
\bigcup_{u\in\operatorname{Pred}_G(v)}
\{m\in\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{u,B,L}(\mathbf P_v(u)))\mid\operatorname{dst}(m)=v\}.
\tag{D-5.1b}
$$

定义窗口内可消费入站消息集合：

$$
\mathcal M_v^{\mathrm{in}}(\mathbf P_v)
=
\{m\in\mathcal M_v(\mathbf P_v)\mid\operatorname{arrival}(m)\in\mathbb T_{B,L}\}.
\tag{D-5.2}
$$

定义节点 $v$ 的输入原子集合：

$$
\mathcal A_v(\mathbf P_v)
=
\{(\mathtt{msg},m)\mid m\in\mathcal M_v^{\mathrm{in}}(\mathbf P_v)\}
\cup
\mathcal J_v,
\tag{D-5.3}
$$

其中：

$$
\mathcal J_v
=
\begin{cases}
\{(\mathtt{inj},t,x_t)\mid t\in\mathbb I_{B,L}\},&v=v_{\mathrm{in}},\\
\varnothing,&v\neq v_{\mathrm{in}}.
\end{cases}
$$

#### 定义 5.2：由入站原子得到节点输入序列

对节点 $v$ 与前驱 artifact 赋值 $\mathbf P_v\in\mathsf{PredArtifact}_{v,B,L}$，定义轮次集合：

$$
\mathcal T_v(\mathbf P_v)
=
\{\operatorname{atime}_{v,B,L}(a)\mid a\in\mathcal A_v(\mathbf P_v)\}.
\tag{D-5.4}
$$

若：

$$
\mathcal T_v(\mathbf P_v)=\{\tau_0,\ldots,\tau_{n-1}\}
$$

且 $\tau_0<\cdots<\tau_{n-1}$，定义：

$$
\mathbf U_v(\mathbf P_v)
=
((\tau_0,A_0),\ldots,(\tau_{n-1},A_{n-1})),
\tag{D-5.5}
$$

其中：

$$
A_i=\{a\in\mathcal A_v(\mathbf P_v)\mid
\operatorname{atime}_{v,B,L}(a)=\tau_i\}.
$$

若 $\mathcal T_v(\mathbf P_v)=\varnothing$，定义 $\mathbf U_v(\mathbf P_v)$ 为空序列。

#### 定义 5.3：窗口执行记录集合

定义窗口执行记录集合：

$$
\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})
=
\left\{
\mathbf A=(A_v)_{v\in V}
\in\prod_{v\in V}\mathsf{Artifact}_{v,B,L}
\ \middle|\
\forall v\in V,
A_v=
\operatorname{Ref}_{v,B,L}
(\mathbf U_v(\mathbf A|_{\operatorname{Pred}_G(v)}),\mathbf S^B(v))
\right\}.
\tag{D-5.6}
$$

其中 $\mathbf A|_{\operatorname{Pred}_G(v)}$ 是函数 $\mathbf A$ 在集合 $\operatorname{Pred}_G(v)$ 上的限制，因而属于 $\mathsf{PredArtifact}_{v,B,L}$。元素 $\mathbf A\in\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$ 称为窗口执行记录。式 D-5.6 是固定点式写法，但在空间 DAG 上它可以按拓扑序构造，不需要求解一般循环固定点。

#### 定义 5.4：右边界延续状态与窗口读出

对窗口执行记录 $\mathbf A$，定义全消息集合：

$$
\mathcal M_{\mathrm{all}}(\mathbf A)
=
\mathcal M_B^\partial
\cup
\bigcup_{v\in V}
\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{v,B,L}(A_v)).
\tag{D-5.7}
$$

定义右边界在途消息集合：

$$
\mathcal M_{B+L}^\partial(\mathbf A)
=
\{m\in\mathcal M_{\mathrm{all}}(\mathbf A)
\mid
\operatorname{arrival}(m)=\beta(B+L)\}.
\tag{D-5.8}
$$

定义：

$$
\mathbf S^{B+L}_{\mathbf A}(v)=\operatorname{state}^+_{v,B,L}(A_v).
\tag{D-5.9}
$$

定义右边界候选延续状态：

$$
C_{B+L}(\mathbf A)
=
(\mathbf S^{B+L}_{\mathbf A},\mathcal M_{B+L}^\partial(\mathbf A)).
\tag{D-5.10}
$$

若对每个 $t\in\mathbb I_{B,L}$，$\operatorname{elem}_{\mathsf{Out}_{v_{\mathrm{out}},B,L}}(\operatorname{localOut}_{v_{\mathrm{out}},B,L}(A_{v_{\mathrm{out}}}))$ 中存在唯一记录 $(\omega,t,y_t)\in\mathsf{OID}\times\mathbb I_{B,L}\times Y$，则定义窗口读出函数：

$$
y_{\mathbf A}\in Y^{\mathbb I_{B,L}},
\qquad
y_{\mathbf A}(t)=y_t.
\tag{D-5.11}
$$

若唯一性条件不满足，则该窗口执行没有定义良好的窗口读出。

#### 引理 5.5：右边界候选延续状态类型正确

对每个窗口执行记录 $\mathbf A\in\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$：

$$
C_{B+L}(\mathbf A)\in\mathsf{Cont}_{B+L}.
\tag{L-5.5}
$$

**证明。**

由式 D-5.9，$\mathbf S^{B+L}_{\mathbf A}\in\mathcal S_G$。由式 D-5.8，$\mathcal M_{B+L}^\partial(\mathbf A)$ 中每条消息的到达轮次都等于 $\beta(B+L)$。

还需证明 $\operatorname{UniqueMID}(\mathcal M_{B+L}^\partial(\mathbf A))$。左边界消息集合已经由 $C_B\in\mathsf{Cont}_B$ 满足 $\operatorname{UniqueMID}$。当 $L>0$ 时，左边界消息的到达轮次为 $\beta(B)$，不会进入式 D-5.8；当 $L=0$ 时，没有当前窗口出站消息，式 D-5.8 只保留原左边界消息。

对 $L>0$，式 D-5.8 中的消息都来自节点出站序列。若两条这类消息具有同一标识符，则其标识符的源节点坐标与发送轮次坐标相同。若源节点不同，标识符不可能相同；若源节点相同，则两条消息属于同一节点出站序列，式 A-4.4e 保证它们是同一序列位置上的同一消息。因此 $\mathcal M_{B+L}^\partial(\mathbf A)$ 满足 $\operatorname{UniqueMID}$。代入定义 3.3 即得式 L-5.5。

<div class="qed" aria-label="证毕">∎</div>

#### 定义 5.6：节点拓扑序 chunk 调度

给定拓扑序：

$$
\pi=(v_0,\ldots,v_{|V|-1}).
$$

节点拓扑序 chunk 调度按 $i=0,\ldots,|V|-1$ 依次构造 $A_{v_i}$。

构造 $A_{v_i}$ 时，所有空间前驱 $u\in\operatorname{Pred}_G(v_i)$ 已经被处理。令 $\mathbf P_{v_i}$ 为已经构造出的 artifact 族在 $\operatorname{Pred}_G(v_i)$ 上的赋值，则 $\mathbf P_{v_i}\in\mathsf{PredArtifact}_{v_i,B,L}$，且 $\mathbf U_{v_i}(\mathbf P_{v_i})$ 可由定义 5.1 和定义 5.2 得到。然后令：

$$
A_{v_i}
=
\mathcal C_{v_i,B,L}
(\mathbf U_{v_i}(\mathbf P_{v_i}),\mathbf S^B(v_i)).
\tag{D-5.12}
$$

定义 2.4 的每个拓扑层 $V_j$ 内部不存在空间边，因此同一 $V_j$ 中的节点可以并行执行。每个节点被调用一次，但单次调用可以处理当前 chunk 中所有到达该节点的时间桶。

### 6. 主定理：显式 allocator DAG 的拓扑序 chunk 构造

#### 定理 6.1：窗口执行记录唯一性与拓扑序 chunk 构造

固定 $B,L,R,G,C_B,x_{B:B+L}$。假设：

1. $G=(V,E)$ 满足定义 2.1 的有限空间 DAG 条件。
2. 每个节点实现算子 $\mathcal C_{v,B,L}$ 满足式 A-4.6 的精确节点契约。
3. allocator 节点只是满足定义 4.4、定义 4.5 和定义 4.6 的普通节点，不具有额外隐藏输入、隐藏状态读写或反向控制通道。

则：

1. 集合 $\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$ 至多包含一个元素。
2. 任意拓扑序 chunk 调度都构造出这个唯一窗口执行记录 $\mathbf A$。
3. 不同拓扑序 chunk 调度构造出的窗口执行记录相同。
4. 该执行记录给出的右边界延续状态 $C_{B+L}(\mathbf A)$ 由全部节点 artifact 唯一确定；若式 D-5.11 前的读出唯一性条件成立，则窗口读出 $y_{\mathbf A}$ 也唯一确定。

**证明。**

取拓扑序：

$$
\pi=(v_0,\ldots,v_{|V|-1}).
$$

先证明拓扑序 chunk 调度构造出的 $\mathbf A$ 满足式 D-5.6。对拓扑序下标 $i$ 作归纳。

当 $i=0$ 时，$v_0=v_{\mathrm{in}}$。因为定义 2.1 要求每个节点从 $v_{\mathrm{in}}$ 可达，任意非输入节点都必须在拓扑序中排在 $v_{\mathrm{in}}$ 之后。节点 $v_{\mathrm{in}}$ 没有空间前驱，所以 $\mathsf{PredArtifact}_{v_{\mathrm{in}},B,L}$ 只含空函数。记该函数为 $\mathbf P_{v_{\mathrm{in}}}$。定义 5.6 用当前窗口注入记录构造 $\mathbf U_{v_{\mathrm{in}}}(\mathbf P_{v_{\mathrm{in}}})$，再由式 A-4.6 得到：

$$
A_{v_{\mathrm{in}}}
=
\operatorname{Ref}_{v_{\mathrm{in}},B,L}
(\mathbf U_{v_{\mathrm{in}}}(\mathbf P_{v_{\mathrm{in}}}),\mathbf S^B(v_{\mathrm{in}})).
$$

假设结论已经对 $v_0,\ldots,v_{i-1}$ 成立。考虑 $v_i$。若 $u\in\operatorname{Pred}_G(v_i)$，则由拓扑序定义，$u$ 必在 $v_i$ 之前。因此所有前驱 artifact 已经构造完毕，前驱赋值 $\mathbf P_{v_i}$ 被唯一确定。左边界在途消息也是给定输入，所以 $\mathbf U_{v_i}(\mathbf P_{v_i})$ 被唯一确定。

定义 5.6 调用：

$$
\mathcal C_{v_i,B,L}
(\mathbf U_{v_i}(\mathbf P_{v_i}),\mathbf S^B(v_i)).
$$

由式 A-4.6，该值等于：

$$
\operatorname{Ref}_{v_i,B,L}
(\mathbf U_{v_i}(\mathbf P_{v_i}),\mathbf S^B(v_i)).
$$

所以式 D-5.6 中的节点方程对 $v_i$ 成立。归纳完成，式 D-5.6 中的节点方程对所有 $v\in V$ 成立。

接着证明唯一性。设 $\mathbf A,\mathbf A'\in\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$。仍按同一拓扑序做归纳。

当 $i=0$ 时，两个执行记录在 $v_{\mathrm{in}}$ 的前驱限制都是同一个空函数 $\mathbf P_{v_{\mathrm{in}}}$，所以：

$$
\mathbf U_{v_{\mathrm{in}}}(\mathbf A|_{\operatorname{Pred}_G(v_{\mathrm{in}})})
=
\mathbf U_{v_{\mathrm{in}}}(\mathbf A'|_{\operatorname{Pred}_G(v_{\mathrm{in}})}).
$$

由式 D-5.6 和 $\operatorname{Ref}_{v_{\mathrm{in}},B,L}$ 的确定性：

$$
A_{v_{\mathrm{in}}}=A'_{v_{\mathrm{in}}}.
$$

假设 $A_{v_j}=A'_{v_j}$ 对所有 $j<i$ 成立。对 $v_i$，所有空间前驱都在 $v_i$ 之前，所以：

$$
\mathbf A|_{\operatorname{Pred}_G(v_i)}
=
\mathbf A'|_{\operatorname{Pred}_G(v_i)}.
$$

因此：

$$
\mathbf U_{v_i}(\mathbf A|_{\operatorname{Pred}_G(v_i)})
=
\mathbf U_{v_i}(\mathbf A'|_{\operatorname{Pred}_G(v_i)}).
$$

再由式 D-5.6 和 $\operatorname{Ref}_{v_i,B,L}$ 的确定性：

$$
A_{v_i}=A'_{v_i}.
$$

归纳完成，$\mathbf A=\mathbf A'$。因此窗口执行记录至多存在一个；拓扑序 chunk 调度已经构造出一个，所以它就是唯一窗口执行记录。因为唯一性证明不依赖所选拓扑序，不同拓扑序调度构造出的记录也相同。

右边界延续状态由定义 5.4 的式 D-5.7--D-5.10 从 $\mathbf A$ 确定。若读出唯一性条件成立，则窗口读出由式 D-5.11 从 $A_{v_{\mathrm{out}}}$ 确定。因此两者都由全部节点 artifact 唯一确定。

<div class="qed" aria-label="证毕">∎</div>

#### 推论 6.2：空间遍历次数不随 chunk 长度增长

在定理 6.1 的前提下，节点拓扑序 chunk 调度调用节点算子的次数等于 $|V|$，与 $L$ 无关。

若把定义 2.4 的同一拓扑层中的节点并行执行，则图级同步阶段数等于 $D_G$，且 $D_G\leq|V|$，也与 $L$ 无关。节点内部处理多少时间桶、多少消息和多少输入位置，属于节点算子的内部 work/span 问题。

**证明。**

定义 5.6 明确按拓扑序中每个节点构造一次 artifact。拓扑序长度为 $|V|$，所以节点算子调用次数为 $|V|$。由定义 2.4，拓扑层共有 $D_G$ 个；每层非空且各层两两不交，所以 $D_G\leq|V|$。

<div class="qed" aria-label="证毕">∎</div>

#### 定义 6.3：窗口转导与时间分块组合律

对固定的全局输入流 $x$，定义窗口转导的定义域：

$$
\mathsf{Dom}_{B,L}
=
\left\{
C\in\mathsf{Cont}_B
\ \middle|\
\begin{array}{l}
\mathsf{Exec}_{B,L}(C,x_{B:B+L})=\{\mathbf A\}
\text{ 对某个 }\mathbf A,\\
y_{\mathbf A}\text{ 由式 D-5.11 定义}
\end{array}
\right\}.
\tag{D-6.3a}
$$

由定理 6.1，集合中的 $\mathbf A$ 若存在则唯一。定义部分函数：

$$
\Phi_{B,L}:\mathsf{Dom}_{B,L}
\to
\mathsf{Cont}_{B+L}\times Y^{\mathbb I_{B,L}}
$$

为：

$$
\Phi_{B,L}(C)
=
(C_{B+L}(\mathbf A),y_{\mathbf A}),
\tag{D-6.3b}
$$

其中 $\mathsf{Exec}_{B,L}(C,x_{B:B+L})=\{\mathbf A\}$。

给定 $L_1,L_2\in\mathbb N$、$y^{(1)}\in Y^{\mathbb I_{B,L_1}}$ 与 $y^{(2)}\in Y^{\mathbb I_{B+L_1,L_2}}$，定义拼接函数：

$$
y^{(1)}\mathbin{\|}y^{(2)}
\in Y^{\mathbb I_{B,L_1+L_2}}
$$

为：

$$
(y^{(1)}\mathbin{\|}y^{(2)})(t)
=
\begin{cases}
y^{(1)}(t),&t\in\mathbb I_{B,L_1},\\
y^{(2)}(t),&t\in\mathbb I_{B+L_1,L_2}.
\end{cases}
\tag{D-6.3c}
$$

称窗口转导族 $(\Phi_{B,L})_{B,L\in\mathbb N}$ 满足时间分块组合律，当且仅当对所有 $B,L_1,L_2\in\mathbb N$ 和 $C\in\mathsf{Dom}_{B,L_1}$，若：

$$
\Phi_{B,L_1}(C)=(C',y^{(1)}),
\qquad
C'\in\mathsf{Dom}_{B+L_1,L_2},
$$

且：

$$
\Phi_{B+L_1,L_2}(C')=(C'',y^{(2)}),
$$

则 $C\in\mathsf{Dom}_{B,L_1+L_2}$，并且：

$$
\Phi_{B,L_1+L_2}(C)
=
(C'',y^{(1)}\mathbin{\|}y^{(2)}).
\tag{A-6.3}
$$

式 A-6.3 才是把一个长 chunk 与两个相邻短 chunk 联系起来的正式条件。反复取 $L_1=1$ 后，它给出长 chunk 与逐 token 窗口执行之间的数学等价。

#### 命题 6.4：空间拓扑序构造不自动推出时间分块组合律

定义 0--5 与定理 6.1 的前提不蕴含式 A-6.3。

**证明。**

取 $X=\{x_*\}$、$Y=\{0,1\}$、$R=1$，空间图只有节点 $v_{\mathrm{in}},v_{\mathrm{out}}$ 和边 $(v_{\mathrm{in}},v_{\mathrm{out}})$。令所有节点状态集合与消息载荷集合都是单元素集合；令所有节点转导器都不产生路由记录和出站消息，并保持节点状态不变。取 $\mathsf{OID}=\mathbb N\times\mathbb N$。

输出节点参考转导器对每个 $t\in\mathbb I_{B,L}$ 产生唯一局部输出记录，并规定：当 $L=1$ 时输出值为 $0$，当 $L>1$ 时输出值为 $1$；记录标识符取 $(L,t)$。实现节点算子取为对应参考转导器本身。由定理 6.1，每个窗口都有唯一拓扑序执行记录。

但是，长度为 $2$ 的单个窗口输出为 $(1,1)$，两个连续的长度为 $1$ 的窗口输出拼接为 $(0,0)$。因此式 A-6.3 不成立。

<div class="qed" aria-label="证毕">∎</div>

命题 6.4 表明，当前主定理严格证明的是空间调度性质。下一步若要证明 `prefill = decode`，必须再给出逐绝对轮次的节点参考转移，并证明 $\operatorname{Ref}_{v,B,L}$ 是这些逐轮转移在 $\mathbb T_{B,L}$ 上的折叠；或者直接证明整个窗口转导族满足式 A-6.3。只有在加入这一层之后，才可以把节点拓扑序 chunk 执行称为逐轮 decode 执行的等价重排。

### 7. 不等长路径如何进入模型

#### 7.1 不等长路径不是 allocator 的障碍

不等长路径只会导致同一节点在不同绝对轮次收到不同路径上的消息。定义 4.2 已把节点输入写成按绝对轮次排序的时间桶序列：

$$
\mathbf U_v=((\tau_0,A_0),\ldots,(\tau_{n-1},A_{n-1})).
$$

因此，节点不需要知道“所有路径是否等长”。它只需要处理已经到达本节点、且到达轮次落在当前窗口可消费轮次集合 $\mathbb T_{B,L}$ 内的输入桶。

#### 7.2 长路径跨 chunk 的处理

在单位边时延模型中，若某条消息 $m$ 满足：

$$
\operatorname{arrival}(m)=\beta(B+L),
$$

则它不会在当前窗口被消费，而是由式 D-5.8 放入右边界在途消息集合 $\mathcal M_{B+L}^\partial$。下一个窗口从 $C_{B+L}$ 开始时再继续消费它。

一条较长空间路径不是由同一消息跨越多条边完成，而是由相邻节点依次产生的新消息完成。因而在任意窗口切面上，单条在途消息只位于一条边上；较长路径的整体影响可以经过多个窗口继续传播。

所以 general DAG 从中间开始执行时，不需要重新注入历史输入。历史影响只通过两类对象进入当前窗口：

1. 左边界节点状态 $\mathbf S^B$。
2. 左边界在途消息 $\mathcal M_B^\partial$。

#### 7.3 输出时延是语义选择

按式 D-1.4，第 $t$ 个输出位置的名义读出切面是 $\tau_{\mathrm{read}}(t)=\beta(t+1)$。若希望某条从 $v_{\mathrm{in}}$ 到 $v_{\mathrm{out}}$ 的路径影响同一输入位置的输出，则外部周期 $R$ 和输出节点参考转导器必须让该路径的消息在该切面前到达并被消费。

若 $R$ 较小，较长路径的消息可以合法地跨过当前读出切面，成为影响未来窗口的上下文消息。这不是调度错误，而是不同参考语义。设计时必须明确：

1. 哪些路径被允许影响同一位置输出。
2. 哪些路径只允许作为未来上下文。
3. 哪些消息到右边界时必须被保留为在途消息。

当前窗口级参考转导器尚未被约束为只能使用名义读出切面之前的输入来产生 $y_t$。因此本节给出的是待满足的读出语义要求，不是定理 6.1 已经证明的 token-prefix causality；该缺口已列入第 11 节。

### 8. allocator 抽象与负载均衡自由度

#### 定义 8.1：通信局部性与发送激活稀疏性

给定关系：

$$
\mathsf{Near}\subseteq V\times V.
$$

称 $G=(V,E)$ 对 $\mathsf{Near}$ 是通信局部的，当且仅当：

$$
E\subseteq\mathsf{Near}.
\tag{D-8.1a}
$$

$\mathsf{Near}$ 可以由几何邻接、Delaunay 邻接、固定半径邻接或其他设计规则给出；本页定理只使用 $E$ 是 DAG，不预设 $\mathsf{Near}$ 的具体构造。

给定非空有限集合：

$$
\mathscr R
\subseteq
\mathcal P_{\mathrm{fin}}(V)\setminus\{\varnothing\},
$$

其元素称为观测区域。给定函数：

$$
\kappa:\mathscr R\times\mathbb N\to\mathbb N,
$$

称为区域发送预算。对窗口执行记录 $\mathbf A=(A_v)_{v\in V}$，称 $\mathbf A$ 满足 $(\mathscr R,\kappa)$-发送稀疏性，当且仅当对每个 $Q\in\mathscr R$ 与 $\tau\in\mathbb T_{B,L}$：

$$
\left|
\{v\in Q\mid
\tau\in\operatorname{Active}_{v,B,L}(A_v)\}
\right|
\leq
\kappa(Q,\tau).
\tag{D-8.1b}
$$

式 D-8.1a 与式 D-8.1b 是两个不同性质。局部空间连接只限制一条消息可以发往哪些节点；若每个节点都向许多后继发送，分岔仍可能使发送激活迅速覆盖大部分空间图。发送稀疏性另外限制每个绝对轮次、每个观测区域中实际发送消息的节点数。

未发生发送激活的节点仍可更新本地状态。因而本页使用“发送激活”指式 D-4.7a 定义的消息发射性质，不把它等同于“节点 kernel 完全未执行”，也不把它等同于神经网络张量中的 activation value。

#### 8.2 allocator 的安全约束

在本页模型中，allocator 安全性的关键不是“它是否复杂”，而是“它是否显式位于空间 DAG 中”。显式 allocator 必须满足：

1. 它读取的当前窗口动态信息只能来自拓扑上游消息。
2. 它读取的历史负载、quota、统计量或 learned 参数必须属于自己的左边界状态 $\mathbf S^B(v)$，或由上游消息携带。
3. 它输出的路由决定只能通过路由记录与出站消息影响拓扑下游节点；发送激活由式 D-4.7a 从出站消息导出。
4. 它不能读取拓扑下游节点在当前窗口中尚未提交的状态。
5. 它不能反向改变拓扑上游节点在当前窗口中的计算结果。

这些约束已经由定义 4.4、定义 4.5、定义 4.6 和定理 6.1 的前提表达：节点转导器的输入只有 $\mathbf U_v$ 与 $S_v^B$，出站影响只能沿 $E$ 前向传播。

上述约束足以保持定理 6.1 的空间拓扑序构造，但不自动保证式 A-6.3。若 allocator 的窗口级决定依赖 chunk 长度，或其状态更新不能分解为逐轮转移的折叠，命题 6.4 的同类反例仍然成立。因此每一种 stateful、quota-based 或 learned allocator 还必须单独证明时间分块组合律。

#### 8.3 allocator 的放置范围与实现方式

allocator 的放置范围可以分为：

1. **Level 0：无 allocator**。普通节点按固定规则向所有后继或固定后继子集发送消息。
2. **Level 1：节点局部选择**。普通节点的参考转导器根据自己的状态和入站消息决定实际出站消息；这里没有独立的 allocator 节点。
3. **Level 2：显式局部 allocator 节点**。若干上游节点向一个 allocator 节点发送摘要，allocator 再向拓扑下游发送决定或数据消息。
4. **Level 3：显式区域 allocator 子图**。一个由多个显式节点构成的 allocator 子图汇总若干上游分支并分配下游容量；该子图的全部边仍属于空间 DAG。

固定规则、带历史状态的规则与 learned 规则是另一条独立维度，而不是上述放置范围之后的新 Level。任一 Level 都可以采用确定的固定函数、读取本节点左边界状态的有状态函数，或由训练得到的函数；数学上它们都属于相应节点参考转导器。

Level 3 可以表达比节点局部选择更强的区域负载均衡，但不能退化为隐藏全局 selector。只要 allocator 子图读取和影响的方向仍遵守空间 DAG，定理 6.1 仍适用。

#### 8.4 当前模型是否要求全部路由进入 allocator

当前定义不要求全部路由决定只能由角色为 $\mathtt{allocator}$ 的节点产生。定义 4.5 允许每个普通计算节点的参考转导器根据本节点状态和入站消息产生路由记录与出站消息；因此 Level 1、Level 2 和 Level 3 都可表达。

“所有稀疏激活与路由都由显式 allocator 产生，其他节点只做计算、状态更新并按命令发送”是一个更强的 allocator normal form。若采用该形式，还必须新增至少三个正式对象：

1. allocator 命令集合。
2. 命令消息与被控制计算节点之间的对应关系。
3. 普通节点只在收到何种命令时允许产生哪些出站消息的合法性条件。

这些对象尚未进入当前最低层定义。因而本页已经证明显式 allocator 可以安全嵌入一般空间 DAG，但尚未证明任意节点局部选择都能无代价地改写成“全部决定集中到 allocator 节点”的 normal form。

#### 8.5 与 LH selector 的区别

LH 的空间图局部连接首先保证通信局部性，但不自动保证发送稀疏性。LH 风格 selector 可以被理解为一个隐式 allocator：它读取一个范围内多个节点的当前信息，再联合决定其中哪些节点继续产生消息。它同时承担稀疏化与负载均衡，但若其读取集合和影响集合跨越空间拓扑的前后方向，就会在显式 DAG 之外创建隐藏依赖边，破坏一次拓扑序 chunk 调度。

本页方案不是取消 selector 的功能，而是把 selector 显式化为 allocator 节点或 allocator 子图。显式化之后：

1. selector 的输入成为 allocator 的入站消息。
2. selector 的内部负载状态成为 allocator 的节点状态。
3. selector 的路由结果成为路由记录与出站消息 artifact，发送激活集合由出站消息导出。
4. selector 的依赖边必须进入空间 DAG。

### 9. artifact equality

#### 定义 9.1：节点 artifact equality

给定节点 $v$、输入序列 $\mathbf U\in\mathfrak U_{v,B,L}$ 和左状态 $S\in\mathcal S_v$。设参考产物：

$$
A^{\mathrm{ref}}
=
\operatorname{Ref}_{v,B,L}(\mathbf U,S),
$$

实现产物：

$$
A^{\mathrm{impl}}
=
\mathcal C_{v,B,L}(\mathbf U,S).
$$

称节点 $v$ 在 $(\mathbf U,S)$ 上满足 artifact equality，当且仅当：

$$
A^{\mathrm{impl}}=A^{\mathrm{ref}}.
\tag{D-9.1}
$$

根据定义 4.4，这要求同时比较：

1. 局部输出记录序列。
2. 状态提交记录序列。
3. 路由记录序列。
4. 出站消息序列。
5. 右侧节点状态。

allocator 的路由记录由 $\operatorname{routes}_{v,B,L}$ 给出；实际发送目标和发送激活集合由 $\operatorname{outbox}_{v,B,L}$ 按定义 4.7 导出。因此 allocator 方案可以对路由决定、实际消息与发送稀疏性做 artifact equality 检查。

#### 推论 9.2：节点 artifact equality 推出窗口产物相等

在定理 6.1 的前提下，若每个节点实现都满足定义 9.1，则拓扑序 chunk 调度得到的全部节点 artifact 与右边界延续状态等于参考转导器定义出的对应对象；若读出唯一性条件成立，则窗口读出也相等。

**证明。**

定义 9.1 等价于式 A-4.6。将其代入定理 6.1 即得。

<div class="qed" aria-label="证毕">∎</div>

### 10. `owner / frontier` 在本页之外的位置

本页最低层模型没有使用 `owner / frontier`。这不是说它们无用，而是把职责分开：

1. 一般空间 DAG、不等长路径、显式 allocator 和跨 chunk 在途消息，只需要消息标识符、到达轮次、源节点、目标节点和载荷。
2. 若要证明自回归 token-prefix causality，需要额外说明每个输出 $y_t$ 不能依赖 $x_{t+1},x_{t+2},\ldots$。这可以通过 `owner / frontier` 字段证明，也可以通过其他因果证书证明。
3. 若要调试同一轮次多 token 消息的归属、融合输出、读出归因或 prefix leakage，`owner / frontier / support` 是有用的增强字段。
4. 若加入这些字段，它们应作为消息记录和局部输出记录的额外坐标，而不改变本页的空间 DAG、节点状态、边界延续状态和 artifact equality 主结构。

因此，第三部分作为本模型的增强语义层：它处理 token 归属、因果前沿、同刻融合与更细读出约束；第二部分则保留当前主线所需的最低空间 DAG 与显式 allocator 框架。

### 11. 当前设计边界

本页可以支持：

1. 一般有限空间 DAG。
2. 不等长路径。
3. 从任意全局位置 $B$ 开始的 chunk 执行。
4. 跨 chunk 在途消息。
5. 显式 allocator 节点或 allocator 子图。
6. 节点级与 allocator 级 artifact equality。
7. 常数次空间拓扑遍历的 chunk 调度。
8. 对通信局部性与区域发送稀疏性分别建模。

本页尚未支持或尚未证明：

1. 空间图中有环。
2. 隐式全局 selector。
3. 当前窗口内读取下游动态状态后再反向影响上游。
4. 任意节点 kernel 的低 span 实现。
5. 式 A-6.3 的时间分块组合律；因此当前空间拓扑序定理尚不等同于完整的 `prefill = decode` 定理。
6. 自回归 token-prefix causality 的完整证明。
7. “全部路由只能由 allocator 产生”的 normal form 及其表达力、性能保持证明。
8. 反向传播、浮点误差、设备后端或 Ascend NPU lowering。

下一步应在本页框架内分别研究三类节点 kernel：

1. 已知可 chunk 化的 dense / attention / SSM / FFN kernel。
2. 可由 scan、reduce、segmented pack 支持的局部状态 kernel。
3. 显式 allocator kernel，包括负载历史、quota、容量分配和 learned scoring。
4. 逐绝对轮次节点参考转移及其窗口折叠，用于证明式 A-6.3。

---

## 第三部分：可选的归属与因果证书

本部分不改变第二部分的一般空间 DAG 执行语义。它只为消息和读出增加可检查字段，用于回答“这条消息标记给哪个输入位置”“它实际上依赖哪些输入位置”以及“它由哪个事件产生”。这些问题在最低 allocator 模型中不是必需的，但在检查自回归前缀因果性、同刻多输入融合和 artifact equality 时有用。

### 定义 C.1：增强消息记录

给定第二部分定义的基础消息集合 $\mathsf{Msg}_G$。给定非空事件标识符集合 $\mathsf{EID}$，并定义自然数有限子集集合：

$$
\mathcal P_{\mathrm{fin}}(\mathbb N)
=
\{A\subseteq\mathbb N\mid A\text{ 是有限集合}\}.
$$

定义增强消息集合：

$$
\mathsf{Msg}_G^+
=
\mathsf{Msg}_G
\times\mathbb N
\times\mathcal P_{\mathrm{fin}}(\mathbb N)
\times\mathbb N
\times\mathsf{EID}.
\tag{C.1}
$$

一个增强消息是五元组：

$$
m^+=(m,o,P,c,e),
$$

其中：

- $m\in\mathsf{Msg}_G$ 是第二部分已经定义的基础消息；
- $o\in\mathbb N$ 称为 `owner`，是该消息对外声明的输入位置标签；
- $P\in\mathcal P_{\mathrm{fin}}(\mathbb N)$ 称为声明输入支撑集；
- $c\in\mathbb N$ 称为因果前沿上界；
- $e\in\mathsf{EID}$ 是生产该消息的事件标识符。

定义投影函数：

$$
\operatorname{base}(m^+)=m,
\quad
\operatorname{owner}(m^+)=o,
\quad
\operatorname{support}(m^+)=P,
$$

$$
\operatorname{frontier}(m^+)=c,
\quad
\operatorname{producer}(m^+)=e.
$$

称 $m^+$ 合法，当且仅当：

$$
o\le c
\quad\text{且}\quad
\forall p\in P, p\le c.
\tag{C.2}
$$

`owner`、输入支撑集和生产事件是三个不同对象。相同 `owner` 可以沿不同路径产生多条消息；一个融合消息可以有单一 `owner`，同时让输入支撑集包含多个位置；生产事件标识符也不能由 `owner` 或因果前沿唯一恢复。

### 定义 C.2：精确支撑与保守支撑

给定非空有限位置集合 $J\subseteq\mathbb N$。对每个 $j\in J$，给定非空输入值集合 $X_j$。定义有限乘积集合：

$$
X_J=\prod_{j\in J}X_j.
$$

对 $x\in X_J$，将其写成有限索引族 $x=(x_j)_{j\in J}$，其中 $x_j\in X_j$。定义本节的 $f$ 时，模型参数、左边界状态和非输入变量均视为已经固定；本节只度量 $f$ 对当前列出的输入坐标是否实质依赖。

给定非空值集合 $Y$ 和函数：

$$
f:X_J\to Y.
$$

对 $j\in J$，称 $f$ 实质依赖坐标 $j$，当且仅当存在 $x,x'\in X_J$ 满足：

$$
\forall k\in J\setminus\{j\},\ x_k=x'_k,
\qquad
f(x)\ne f(x').
\tag{C.3}
$$

定义 $f$ 的精确输入支撑集：

$$
\operatorname{Ess}(f)
=
\{j\in J\mid f\text{ 实质依赖坐标 }j\}.
\tag{C.4}
$$

若增强消息 $m^+$ 的基础载荷由函数 $f$ 产生，则称声明集合 $P=\operatorname{support}(m^+)$ 是精确支撑，当且仅当：

$$
P=\operatorname{Ess}(f).
$$

称 $P$ 是保守支撑，当且仅当：

$$
\operatorname{Ess}(f)\subseteq P.
$$

若 $P$ 是保守支撑且 $m^+$ 满足式 C.2，则 $\operatorname{frontier}(m^+)$ 是保守因果前沿。工程实现可以只维护保守前沿；形式化调试、归因或 prefix-leakage 定位可以维护完整支撑集。两者都不是物理完成时间，也不是消息到达轮次。

### 定义 C.3：同一逻辑时刻的多归属输入

给定空间节点 $v\in V$ 和逻辑到达轮次 $\tau\in\mathbb N$。设该节点在该轮次收到的合法增强消息有限集合为：

$$
I_{v,\tau}^+\subseteq\mathsf{Msg}_G^+.
$$

定义该收件集合中的归属位置集合：

$$
O_{v,\tau}
=
\{\operatorname{owner}(m^+)\mid m^+\in I_{v,\tau}^+\}.
$$

给定非空局部输出载荷集合 $Z_v$。定义增强局部输出记录集合：

$$
\mathsf{LocalOut}_v^+
=
\left\{
(\omega,o,P,c,z)
\in
\mathsf{OID}
\times\mathbb N
\times\mathcal P_{\mathrm{fin}}(\mathbb N)
\times\mathbb N
\times Z_v
\ \middle|\
o\le c,
\ \forall p\in P,\ p\le c
\right\}.
\tag{C.5}
$$

节点在 $(v,\tau)$ 的局部输出是有限序列：

$$
\mathbf z_{v,\tau}\in(\mathsf{LocalOut}_v^+)^\star.
$$

对每个 $o\in O_{v,\tau}$，定义归属桶：

$$
I_{v,\tau,o}^+
=
\{m^+\in I_{v,\tau}^+\mid\operatorname{owner}(m^+)=o\}.
$$

记录的第一坐标 $\omega\in\mathsf{OID}$ 是局部输出标识符，第二坐标 $o\in\mathbb N$ 才是 `owner`；两者不能互相替代。

若 $P$ 要作为因果证书，则对产生载荷 $z$ 的输出函数，$P$ 必须满足定义 C.2 的保守支撑条件。节点参考转导器还必须声明下列三类中的一类；这三类是对其函数类型和依赖范围的约束：

1. **分别输出**：$\mathbf z_{v,\tau}$ 可写成按 $o\in O_{v,\tau}$ 的自然数升序连接得到的子序列；归属 $o$ 的子序列只读取 $I_{v,\tau,o}^+$ 和节点左状态。
2. **联合计算但保留归属**：转导器可以读取整个 $I_{v,\tau}^+$；每条输出记录的 `owner` 必须属于 $O_{v,\tau}$，并且 reference contract 明确每个被保留归属对应哪些输出记录。
3. **融合输出**：转导器可以读取整个 $I_{v,\tau}^+$，并产生任意有限序列 $\mathbf z_{v,\tau}$；每条输出记录仍必须显式给出 `(owner, support, frontier)` 三个坐标。

这三种选择定义不同的 reference semantics。融合输出若丢失分别输出所需的信息，不能在没有额外证明时声称与分别输出等价。

### 定义 C.4：自回归前缀因果证书

给定位置 $t\in\mathbb N$、非空读出值集合 $Y_t$、非空有限位置集合 $J_t\subseteq\mathbb N$，以及非空输入值集合族 $(X_j)_{j\in J_t}$。给定读出函数：

$$
g_t:\prod_{j\in J_t}X_j\to Y_t.
$$

给定 $g_t$ 的保守支撑 $P_t\in\mathcal P_{\mathrm{fin}}(\mathbb N)$，即：

$$
\operatorname{Ess}(g_t)\subseteq P_t.
$$

称二元组 $(g_t,P_t)$ 满足位置 $t$ 的前缀因果证书，当且仅当：

$$
P_t\subseteq[t+1].
\tag{C.6}
$$

式 C.6 只证明“读出没有依赖未来输入”。它不证明节点 kernel 具有低 span，也不证明 selector 可并行，更不证明物理执行已经高效实现。

### 命题 C.5：消息增强字段对基础 allocator 语义是保守的

定义消息投影函数：

$$
\pi_{\mathrm{msg}}:\mathsf{Msg}_G^+\to\mathsf{Msg}_G,
\qquad
\pi_{\mathrm{msg}}(m^+)=\operatorname{base}(m^+).
$$

对节点 $v\in V$，定义增强输入原子集合：

$$
\mathsf{Atom}_{v,B,L}^+
=
\left(
\{\mathtt{msg}\}
\times
\{m^+\in\mathsf{Msg}_G^+\mid
\operatorname{dst}(\pi_{\mathrm{msg}}(m^+))=v\}
\right)
\cup
\mathsf{InjAtom}_{v,B,L}.
$$

定义原子投影 $\pi_v^{\mathrm{atom}}:\mathsf{Atom}_{v,B,L}^+\to\mathsf{Atom}_{v,B,L}$：

$$
\pi_v^{\mathrm{atom}}(\mathtt{msg},m^+)
=(\mathtt{msg},\pi_{\mathrm{msg}}(m^+)),
$$

并令 $\pi_v^{\mathrm{atom}}$ 在 $\mathsf{InjAtom}_{v,B,L}$ 上为恒等函数。用 $\mathsf{Atom}_{v,B,L}^+$ 替换定义 4.2 中的 $\mathsf{Atom}_{v,B,L}$，并用基础消息的到达轮次定义增强消息原子的时间，得到合法增强节点输入序列集合 $\mathfrak U_{v,B,L}^+$。把 $\pi_v^{\mathrm{atom}}$ 逐元素作用于每个有限时间桶和时间桶序列，定义函数：

$$
\pi_v^{\mathrm{in}}:
\mathfrak U_{v,B,L}^+
\to
\mathfrak U_{v,B,L}.
$$

定义增强节点原始产物集合：

$$
\mathfrak A_{v,B,L}^+
=
\mathsf{Out}_{v,B,L}^\star
\times\mathsf{Commit}_v^\star
\times\mathsf{Route}_v^\star
\times(\mathsf{Msg}_G^+)^\star
\times\mathcal S_v.
$$

称 $A^+\in\mathfrak A_{v,B,L}^+$ 是合法增强节点产物，当且仅当：其每条增强出站消息满足式 C.2，并且把所有增强出站消息应用 $\pi_{\mathrm{msg}}$ 后，所得五元组满足定义 4.4 的全部合法节点产物条件。定义：

$$
\mathsf{Artifact}_{v,B,L}^+
=
\{A^+\in\mathfrak A_{v,B,L}^+\mid A^+\text{ 是合法增强节点产物}\}.
$$

定义产物投影：

$$
\Pi_v:\mathsf{Artifact}_{v,B,L}^+
\to\mathsf{Artifact}_{v,B,L}
$$

为：对出站消息序列逐元素应用 $\pi_{\mathrm{msg}}$，对局部输出、提交、路由和右状态坐标使用恒等函数。

给定确定的增强节点参考转导器：

$$
\operatorname{Ref}_{v,B,L}^+:
\mathfrak U_{v,B,L}^+
\times\mathcal S_v
\to\mathsf{Artifact}_{v,B,L}^+.
$$

假设对每个 $\mathbf U_v^+\in\mathfrak U_{v,B,L}^+$ 和每个左边界状态 $S_v\in\mathcal S_v$，局部交换关系成立：

$$
\Pi_v\left(
\operatorname{Ref}_{v,B,L}^+(\mathbf U_v^+,S_v)
\right)
=
\operatorname{Ref}_{v,B,L}\left(
\pi_v^{\mathrm{in}}(\mathbf U_v^+),S_v
\right).
\tag{C.7}
$$

则将一次增强执行中的所有消息和节点产物分别应用 $\pi_{\mathrm{msg}}$ 与 $\Pi_v$ 后，所得节点输入、状态提交、基础输出和窗口读出与第二部分的基础执行相同。

**证明。**

按第二部分给定的空间拓扑序归纳。输入节点处，$\pi_v^{\mathrm{in}}$ 不改变注入原子。假设节点 $v$ 的所有前驱消息投影后与基础执行相同，则 $\pi_v^{\mathrm{in}}(\mathbf U_v^+)$ 等于基础执行给 $v$ 构造的输入序列。由式 C.7，$v$ 的投影产物等于基础节点产物，因而状态提交、局部输出、路由和发往后继的基础消息均相同。有限拓扑序归纳完成后，所有节点状态和窗口读出相同。

<div class="qed" aria-label="证毕">∎</div>

命题 C.5 只处理基础消息到增强消息的保守扩展。若节点采用定义 C.3 的增强局部输出记录，还必须另外定义从 $\mathsf{LocalOut}_v^+$ 到 $\mathsf{Out}_{v,B,L}$ 的输出投影，并为该投影证明与式 C.7 同型的局部交换关系；本命题不自动给出该结论。

### 已归档结果 C.6：固定周期 token-owned profile

整合前的 `token-owned-general-dag-routing.md` 还定义过一个更强、也更复杂的固定周期 profile：有限单位时延空间 DAG、按输入位置标记的 `owner/frontier`、显式消息生产者与消费者、边界在途消息、逐节点规范输入序列，以及绝对时间流式调度和节点拓扑序分块调度。该 profile 在以下额外前提下证明两种调度产生相同的事件值、节点提交、读出和右边界延续状态：

1. 当前窗口产生的事件和消息集合有限。
2. 所有空间边只指向拓扑序更大的节点。
3. 每个节点的分块算子精确实现其逐事件参考转导器的完整产物。
4. 消息生命周期、状态依赖和读出依赖全部显式记录。
5. 同一逻辑时刻的输入顺序、融合语义与 source order 已成为 reference contract。

该结果不直接等于第二部分尚缺的式 A-6.3：旧 profile 把更强的事件生命周期和节点分块等价直接作为前提，而当前 allocator 主线要从更小的逐绝对轮次节点转移推出时间分块组合律。为避免同时维护两套大幅重叠的基础定义，旧 profile 的逐定义证明不再复制到当前正文；其完整历史版本保存在 Git 提交 `d27819f`。本页保留其可复用结论、增强字段和适用边界，但不把“已归档结果”编号当作当前形式化推导中的可引用定理。

> [!note] 何时启用本部分
> 默认 runtime 只需要第二部分的消息标识符、源、目标、到达轮次和载荷。只有当模型 contract 需要按输入位置归因、检查自回归前缀、表达同刻多位置融合，或要求这些字段参与 artifact equality 时，才启用增强记录。增强字段不能代替真实的事件依赖边。

---

## 第四部分：有限事件展开与 zero-delay 边界

### 定义 D.1：有限执行事件图

给定有限事件集合 $\mathcal E$ 和依赖关系：

$$
\prec\ \subseteq\mathcal E\times\mathcal E.
$$

若 $(e,e')\in\prec$，则事件 $e'$ 的合法求值需要事件 $e$ 已经产生的值、状态版本、控制决定或提交事实。称有向图 $(\mathcal E,\prec)$ 为该次执行的事件图。

### 定义 D.2：事件秩函数

设 $N=|\mathcal E|$。一个事件秩函数是函数：

$$
\rho:\mathcal E\to[N],
$$

满足：

$$
(e,e')\in\prec
\Longrightarrow
\rho(e)<\rho(e').
\tag{D.1}
$$

这里 $\rho(e)$ 只是证明依赖严格向前推进的自然数，不是事件标识符、输入位置或物理时间。

### 引理 D.3：事件秩函数推出有限 DAG

若有限事件图 $(\mathcal E,\prec)$ 存在满足式 D.1 的事件秩函数，则该图不存在有向环。

**证明。**

反设存在有向环：

$$
e_0\prec e_1\prec\cdots\prec e_k=e_0.
$$

由式 D.1 反复得到：

$$
\rho(e_0)<\rho(e_1)<\cdots<\rho(e_k)=\rho(e_0),
$$

这与自然数严格小于关系的反自反性矛盾。

<div class="qed" aria-label="证毕">∎</div>

### 推论 D.3a：有限事件 DAG 与事件秩函数等价

有限事件图 $(\mathcal E,\prec)$ 不含有向环，当且仅当存在满足式 D.1 的事件秩函数。

**证明。**

“存在事件秩函数推出不含有向环”就是引理 D.3。反之，若 $(\mathcal E,\prec)$ 不含有向环，则它是有限 DAG。把第二部分引理 2.3 应用于顶点集合 $\mathcal E$ 和边集合 $\prec$，得到一个拓扑序；令 $\rho(e)$ 等于事件 $e$ 在该拓扑序中的下标，即得到满足式 D.1 的函数。

<div class="qed" aria-label="证毕">∎</div>

### 定义 D.4：带延迟的环与零延迟强连通分量

给定有限静态空间图 $G=(V,E)$。对每条边 $a\in E$，给定非负整数时延：

$$
d:E\to\mathbb N.
$$

一条有向环称为带延迟环，当环上至少存在一条边 $a$ 满足 $d(a)>0$。一条有向环称为零延迟环，当环上所有边的时延均为零。

定义零延迟边集合和零延迟子图：

$$
E_0=\{a\in E\mid d(a)=0\},
\qquad
G_0=(V,E_0).
$$

给定非空集合 $W\subseteq V$。称 $W$ 在 $G_0$ 中强连通，当且仅当对任意 $u,v\in W$，$G_0$ 中存在从 $u$ 到 $v$ 的有向路径。称 $W$ 是 $G_0$ 的强连通分量，当且仅当 $W$ 强连通，并且不存在严格包含 $W$ 的强连通集合 $W'\subseteq V$。

称强连通分量 $W$ 是零延迟循环分量，当且仅当：

$$
|W|>1
\quad\text{或}\quad
\bigl(W=\{v\}\text{ 且 }(v,v)\in E_0\bigr).
$$

因此，零延迟循环分量恰好是零延迟子图中包含有向环的强连通分量。

带延迟环在有限 token、round 或状态版本下展开时，可以让依赖从较小版本指向较大版本。零延迟环则要求同一逻辑时刻内的值相互定义，例如：

$$
x=F(y,u),
\qquad
y=G(x,u).
$$

### 命题 D.5：零延迟环没有普通拓扑求值顺序

若一次执行的依赖关系包含零延迟有向环，则不存在满足式 D.1 的事件秩函数，也不存在把环内每个节点各求值一次的普通拓扑顺序。

**证明。**

零延迟环本身就是事件依赖有向环。由引理 D.3 的逆否命题，不存在满足式 D.1 的事件秩函数。拓扑顺序的序号函数本应满足式 D.1，因此普通拓扑顺序也不存在。

<div class="qed" aria-label="证毕">∎</div>

### 约束 D.6：Tide strict core 的环处理规则

Tide strict core 对静态图中的每个环必须采用下列两种处理之一：

1. 环跨越显式 token、round、phase、状态提交或正时延边，使任意有限执行能够按版本展开为有限事件 DAG。
2. 将整个零延迟强连通分量封装为具有独立 reference contract 的 `FixedPointKernel`、`RootSolveKernel` 或有限 $K$ 步迭代 kernel。

否则该图在 strict core 中非法。若 kernel 的实际定义是固定 $K$ 步迭代：

$$
z^{(j+1)}=F(z^{(j)},u),
\qquad j\in[K],
$$

则 reference semantics 是这 $K$ 步有限迭代，而不是未经声明的理想不动点。

### 约束 D.7：局部 lowering 与禁止语义复活

设 reference 节点值空间为 $A$，实现值空间为 $\widehat A$，并给定函数：

$$
\alpha:A\to\widehat A.
$$

若实现用 $\alpha(a)$ 代替 $a$，则所有后继 kernel 必须直接在 $\widehat A$ 上实现 reference contract 所需的商语义，或者证明局部交换关系成立。实现不得把昂贵逆问题或信息恢复过程隐藏在后继 kernel 中，再据此宣称上游聚合具有工程价值。即使存在某个逆映射，其 work、span、memory 与 communication 成本也必须进入实现成本账本。

> [!important] 当前边界
> 第四部分给出有限事件 DAG 与 zero-delay 的 strict-core 规则，不把任意动态 runtime 自动提升为高性能 prefill。高性能还需要各节点声明并证明 token-local、scan、causal bulk 或其他低-span 实现见证；无法收缩的自适应控制链受 [[adaptive-routing-prefill-lower-bound]] 约束。
