---
type: note
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - prefill-decode
  - step-transition
  - math
---

# StepTransition Mathematical Specification

> [!summary] 本页定位
> 本页只处理 `StepTransition`、`prefill`、`decode`、chunk prefill 与 kernel 优化的数学定义。实现对象、LH 映射、phase 工程约束放在 [[step-transition-implementation-specification]]。

> [!note] 写作与证明约定
> 本页按“定义先于使用、简单例子先于复杂架构、引理先于定理、证明不跳步”的顺序推进。CPU ISA、编译器、SSA、内存模型等外部概念只作为参考谱系，见 [[logical-event-dag-related-theories]]；它们不替代本页的数学证明。

> [!note] 中英文术语
> Tide 数学文档共用 [[token-owned-general-dag-routing#术语约定与中英文对照|术语约定与中英文对照]]。`token`、`prefill`、`decode`、`logits` 以及数学符号、公式字段、代码接口、固定缩写和模型专名保留英文，其余解释性正文优先使用中文。

> [!important] 对象层级约定
> 本页沿用 [[token-owned-general-dag-routing#六种容易混淆的身份、归属与来源信息|身份、归属与来源信息]] 以及 [[token-owned-general-dag-routing#定义 4.2b：消息来源图、消息分支、分叉与汇聚|消息来源图]] 的区分。$t$ 是输入位置，$x_t$ 是输入值，二者都不是计算轨迹；空间图的节点是可复用计算位置，逻辑事件 DAG 的顶点是一次有限执行中的事件。数学符号 $\mathcal S$ 表示在相邻 transition 调用之间传递的 **transition-state 容器**；其中只有旧值能够影响下一步语义的分量才称为**持久上下文**。B0 为统一表达而把会被 `Init` 无条件覆盖的当前步 activation slot 也放进 $\mathcal S$，但它不承载跨步历史。临时工作区、局部输出记录、消息和事件值若不属于返回的 $\mathcal S$，则不自动成为 transition state 或持久上下文。

> [!roadmap] 当前形式化边界
> 第 1-5 节已经定义顺序折叠、分块正确性、语义商、有限逻辑事件 DAG、主力计算核族与步骤模拟。[[token-owned-general-dag-routing]] 已对“固定周期 + 有限单位时延空间 DAG + 仅向前路由”这一受限语义配置给出类型化事件 DAG 与封闭有限调度等价定理；可接续 `decode` 的边界状态嵌入、任意有环拓扑、一般动态事件生成、零时延强连通分量与定点计算核仍未形成统一定理，其候选推进顺序见 [[finite-event-dag-and-zero-delay-loops-memo]]。

> [!important] 证否边界
> 本页以构造性 correctness 为主。任意黑盒自适应 routing 在 exact、work-efficient 前提下为何不能获得次线性 adaptive-depth prefill，见独立数学文档 [[adaptive-routing-prefill-impossibility]]。该下界不自动等价于具体 LH selector 的不可能性结论。

阅读本页时，所有结论按以下强度区分：

- `定义`：约定数学对象的含义。
- `例`：帮助理解定义，不承担一般性证明。
- `引理 / 定理`：在明确前提下给出可证明结论。
- `高性能实现见证`：说明已有实现结构可承载该数学对象，不等于 complexity theorem。
- `工程验证`：检查具体实现，不自动提升为一般数学定理。
- 定义、引理、定理、推论与例使用标题编号；引用时优先链接到对应标题。
- 只有会被正文交叉引用的公式才编号；显示编号使用 `\tag{...}`，稳定锚点使用语义化 block ID `^eq-...`。
- 证明统一以“**证明。**”开始，并以右对齐的 `∎` 结束；不同时重复使用“证毕”。

## 0. 记号约定

### 定义 0.1：自然数与区间

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

### 定义 0.2：有限序列

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

### 定义 0.3：有限索引族

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

### 定义 0.4：有向边的 source / destination

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

### 定义 0.5：有限依赖族的乘积空间

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

## 1. Transition 与顺序 Fold

这一节先定义最基础的 transition 与 fold。后文所有 `prefill = decode fold` 都引用这里的定义。

### 定义 1.1：单步 transition system

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

### 定义 1.2：顺序 fold

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

### 定义 1.3：Decode 语义

给定 transition system $\mathcal{T}$。对每个 $L\in\mathbb{N}$，定义长度为 $L$ 的 decode 语义为：

$$
\operatorname{Decode}_{\mathcal{T}}^L(x_{0:L},S_0)
:=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

也就是说，decode 是逐 token 应用同一个单步 transition。

### 定义 1.4：顺序 prefill 语义

给定 transition system $\mathcal{T}$。对每个 $L\in\mathbb{N}$，定义长度为 $L$ 的最保守顺序 prefill 语义为：

$$
\operatorname{Prefill}^{seq,L}_{\mathcal{T}}(x_{0:L},S_0)
:=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

这里的 `seq` 明确表示它只是顺序 fold，不代表高性能并行 prefill。

### 定理 1.5：顺序 prefill 与 decode 等价

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

## 2. Correctness、Semantic Contract 与等价层次

### 定义 2.1：chunk prefill implementation

给定 transition system $\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}$。

对任意长度 $L\in\mathbb{N}$，一个 chunk prefill implementation 是函数：

$$
\mathcal{C}_L:X^L\times\mathcal{S}\to Y^L\times\mathcal{S}
$$

### 定义 2.2：chunk prefill 正确性

称 $\mathcal{C}_L$ 对 $\mathcal{T}$ 正确，当且仅当对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$：

$$
\mathcal{C}_L(x_{0:L},S_0)
=
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
\tag{2.1}
$$

^eq-chunk-prefill-correctness

### 定义 2.3：reference semantic contract

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

### 定义 2.4：transition semantic quotient

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

#### 例 2.4a：完整历史 contract 与求和 contract

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

### 引理 2.5：semantic quotient 保持顺序 fold

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

### 定义 2.6：三个层次

本页区分三个层次：

1. 顺序 fold 等价：对每个 $L$，$\operatorname{Prefill}^{seq,L}_{\mathcal{T}}=\operatorname{Decode}_{\mathcal{T}}^L$。这是定义性等价。
2. chunk forward 等价：证明某个 $\mathcal{C}_L$ 满足定义 2.2。
3. 高性能并行 prefill：进一步要求 $\mathcal{C}_L$ 可通过并行、融合、重排或 packed layout 高效实现，同时仍满足定义 2.2。

层次 1 不推出层次 2；层次 2 不推出层次 3。

## 3. B0：标准 Factorized Graph Runtime

这一节定义简化分支 B 的基线版本。这个基线应从一开始就能自然表达 Transformer、Mamba / SSM、Linear Attention 等主流自回归模型。

B0 已经吸收了旧版本中“factorized node state”的 B1：空间节点状态从一开始就拆成可通信隐藏激活值与私有 memory/cache/state。这里的“激活值”是数值表示，不是动态节点事件的实例化。这样做的目的，是让起点本身就是高性能自回归模型熟悉的形式，而不是先定义一个过弱的 activation-only graph，再额外补 memory/cache。

B0 不包含 LH-style input/output cortex、bridge phase、selector、readout cache 或 pronounce memory。但它包含标准自回归模型需要的两个基本状态因子：

- 当前输入步在该空间节点上的可通信隐藏激活值。
- 空间节点私有的跨输入步 memory/cache/state。

### 定义 3.1：B0 静态结构

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
> 本节把一次输入的 $R$ 个内部轮次封装进单步 transition $\mathcal T^{B0}$，再按输入位置顺序做 fold；它是便于承载 Transformer/Mamba chain 的 fixed-step baseline。[[token-owned-general-dag-routing]] 研究另一种固定周期 streaming semantics：输入位置 $t$ 在 $Rt$ 注入，第 $t$ 个读出在 $R(t+1)$ 发生，长路径消息可以跨边界延续。除非 B0 state 显式保存 in-flight messages 与状态提交轨迹，否则不能把本节的 step-complete fold 与该重叠模型直接视为同一个 transition。

### 定义 3.2：B0 空间

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

### 定义 3.3：B0 kernels

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

### B0 与已知架构的直观对应

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

### 定义 3.4：B0 单步 transition

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

### 定理 3.5：B0 的顺序 prefill / decode 等价

对任意 $L\in\mathbb{N}$、任意 $x_{0:L}\in X^L$ 与任意 $S_0\in A^V\times U^V$：

$$
\operatorname{Prefill}^{seq,L}_{\mathcal{T}^{B0}}(x_{0:L},S_0)
=
\operatorname{Decode}_{\mathcal{T}^{B0}}^L(x_{0:L},S_0)
$$

**证明。**

由定理 1.5，取 $\mathcal{T}=\mathcal{T}^{B0}$ 即得。

<div class="qed" aria-label="证毕">∎</div>

### B0 proof gate：主流 kernel family 的 chunk prefill 正确性

B0 的理论入口不应停在“能表达 Transformer / Mamba”。真正的 B0 proof gate 是：在 B0 内给出具体 kernel family 的 reference transition $\mathcal{T}$、chunk implementation $\mathcal{C}_L$，并证明 $\mathcal{C}_L$ 满足定义 2.2。

也就是说，B0 先要证明若干重要特例满足：

$$
\mathcal{C}_L(x_{0:L},S_0)=\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

这些特例不是任意 B0 graph / 任意 B0 kernel，而是 Transformer / Mamba / Linear Attention / FFN 这类后续会反复使用的主力 kernel family。后续 B1-B6 的问题，是在这些已证明正确的 B0 kernel 之上继续加入 mailbox、phase、selector、readout、pronounce 等机制，并检查它们是否保持或破坏 chunk prefill 正确性。

#### 定义 3.6：B0 kernel family 通过 proof gate

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

#### 定义 3.6a：logical event DAG program

本节使用 $e,n,m$ 表示逻辑事件 DAG 的事件顶点标识符，不表示 B0 空间图中的空间节点。事件顶点的局部值由后文的 $F_n$ 计算；把事件头与该值配对后，才对应 [[token-owned-general-dag-routing#定义 2.1a：抽象逻辑事件头与事件值|完整逻辑事件实例]]。

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

#### 定义 3.6b：logical event DAG 的 evaluation

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

#### 定理 3.6c：B0 Logical Event DAG Theorem

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

#### 备注 3.6d：逻辑次序与墙钟完成顺序

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

#### 定义 3.6e：semantics-preserving aggregation quotient

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

#### 定理 3.6f：Aggregation Quotient Theorem

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

#### 推论 3.6g：三类聚合的判定

1. 同一 logical event 内的多源聚合是安全的，只要 reference decode 本来也在该 event 上执行同一个确定性聚合。此时聚合就是 $F_n$ 的一部分，不需要跨 event quotient。
2. 带标签的跨输入位置/跨逻辑轮次聚合是安全的，只要标签与显式关系保留了后续计算核需要区分的实例、时间、归属和来源信息。标签本身不自动等于完整 provenance；满足要求时，$\alpha$ 可以近似看作 identity 或 layout change。
3. untagged irreversible aggregation 只有在它满足定义 3.6e 的 quotient 条件时才安全。若存在两组 reference event values 在聚合后相同，但某个后续 kernel 或最终输出不同，则不存在 semantics-preserving quotient，不能一般性证明 chunk prefill correctness。

因此，跨输入位置或逻辑轮次的无标签聚合不是绝对禁止；它必须是下游语义的充分统计量。sum / max / histogram 等聚合在某些计算核中可能安全，但在需要区分输入位置影响、逻辑轮次标签或逐位置状态提交的计算核中通常不安全。时间/归属标签与完整来源关系仍是不同对象。

#### 定义 3.6h：Contract-DAG-Quotient correctness certificate

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

#### 定理 3.6i：Unified Contract-DAG-Quotient Theorem

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

#### 推论 3.6j：三个退化情形

1. 若 transition-level 的 $\alpha,\beta$ 都是 identity，则定理 3.6i 退化为 Aggregation Quotient Theorem。
2. 若 event-level 的 $\alpha_n$ 都是 identity，且 $\widehat{\mathcal{P}}_L=\mathcal{P}_L$，则定理 3.6i 退化为 coarse contract 上的 Logical Event DAG Theorem。
3. 若 transition-level 与 event-level abstraction 都是 identity，则定理 3.6i 退化为原 reference transition 上的直接 logical event DAG correctness。

因此，定理 3.6i 统一了三种原本容易混在一起的情况：改变 reference semantic resolution、压缩 event representation、改变物理执行顺序。

#### 定义 3.6k：non-degenerate chunk certificate

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

#### 定义 3.6l：parallel-prefill witness

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

#### 例 3.6m：证书的正例与反例

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

#### 定理 3.7：token-wise kernel 的 chunk prefill 正确性

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

#### 定义 3.8：causal attention decode reference

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

#### 定理 3.9：causal attention 的 chunk prefill 正确性

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

#### 定义 3.10：affine scan recurrence

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

#### 定理 3.11：affine scan recurrence 的 chunk prefill 正确性

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

#### 推论 3.12：linear attention accumulator 的 chunk prefill 正确性

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

#### 定理 3.13：有限 B0 chain 的 layer-wise chunk 正确性

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

#### 定理 3.14：B0-Transformer chunk prefill 正确性

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

#### 定理 3.15：B0-Mamba / SSM chunk prefill 正确性

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

## 4. B-family：逐层增加机制

这一节把 B0 扩展为 B1-B6。B0 已经是能表达 Transformer/Mamba 的标准 factorized graph runtime；后续层级不再引入“基本 memory/cache”，而是列出更强的 graph/runtime 机制候选。

B1-B6 不是必须依次完整实现的唯一架构路线，也不是为了最终逐项复刻 LH。它们更准确地说是 extension schema / mechanism catalog：每一层声明一种新增 state、workspace、kernel 或 schedule 约束。研究时可以保留、简化、替换或拒绝某一机制；裁决标准是它是否服务于“局部通信 + 超稀疏”总体目标，并能否在可接受 contract 下获得 chunk prefill correctness 与有意义的 parallel-prefill witness。

只有当某个 schema 与具体 kernel 组合成明确的单步 transition 后，才可应用后面的 B-family 引理。

### B1：typed edge 与 step-local mailbox

B1 是在 B0 上增加 edge role 与显式 mailbox lifetime 的 schema。它本身不改变 transition 的顺序 fold 语义；真正的 transition 还需要指定 typed edge kernel、aggregation 与 node update。

#### 定义 4.1：edge role

给定有限 edge role 集合 $R_E$ 与 edge role 函数：

$$
\tau_E:E\to R_E
$$

typed edge kernel 可写为：

$$
\phi_{\tau_E(e)}^r:A\times U\to \overline{M}
$$

#### 定义 4.2：mailbox workspace

对每个输入步与内部轮次，引入临时 mailbox：

$$
W_{box}^r=(b_v^r)_{v\in V}
$$

其中 $b_v^r\in\mathcal{B}_v$。

mailbox 不是持久状态。若没有显式 commit，$W_{box}^r$ 不属于下一输入步的 $S'$。

### B2：phase schedule

B2 不是用来把 Transformer / Mamba 的 $N$ 个 block 拆成 $N$ 个 phase。标准 block 顺序应优先由 B0 chain + rounds 表达。

B2 的用途是表达 LH / Tide 这类 runtime 中的大范围执行阶段划分，例如 input-side update、output-side update、input-to-output bridge、output-to-input bridge、readout cache、pronounce 等。也就是说，phase 更像 role / direction / visibility 的全局 barrier，而不是普通 layer index。

#### 定义 4.3：phase

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

#### 定义 4.4：schedule

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

#### 定义 4.5：phase transition

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

#### 约束 4.5a：高性能并行 prefill 的基本语义约束

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

### B3：selector / controller state

#### 定义 4.6：controller state

给定 controller scope 集合 $C$ 与 controller state space $Q$。

controller state 空间为：

$$
Q^C
$$

若 $q\in Q^C$，则 $q_c$ 是 scope $c\in C$ 的 controller state。

#### 定义 4.7：selector kernel

给定候选记录空间 $\mathcal{C}_{cand}$ 与已选动作/路由记录空间 $\mathcal{R}$。候选记录可以包含空间位置与数值隐藏激活；$\mathcal R$ 表示被选择的记录或动作，不是隐藏 activation value 本身。

selector kernel 是函数：

$$
\sigma:\mathcal{C}_{cand}\times Q^C\to \mathcal{R}\times Q^C
$$

其输出既包含被选择的动作/路由记录，也包含更新后的 controller state。

若 chunk prefill 把多个输入位置的候选集合联合输入 selector，必须证明该联合 selector 与按输入位置顺序应用 $\sigma$ 的 fold 等价。

### B4：step-local readout cache

#### 定义 4.8：readout cache

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

### B5：pronounce memory

#### 定义 4.9：pronounce memory

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

### B6：input/output roles 与 bridge

#### 定义 4.10：role-aware graph

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

#### 定义 4.11：LH-like schedule 约束

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

### 引理 4.12：B-family 的顺序 fold 等价

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

## 5. Optimized Kernel 的模拟关系

性能实现通常会改变内部表示，例如 reference layout 与 packed / crossbatch layout 不同。因此需要定义状态等价关系。

### 定义 5.1：两个 transition systems

给定 reference transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

以及 optimized transition system：

$$
\widehat{\mathcal{T}}:X\times\widehat{\mathcal{S}}\to Y\times\widehat{\mathcal{S}}
$$

其中 $\mathcal{S}$ 与 $\widehat{\mathcal{S}}$ 可以是不同的状态表示空间。

### 定义 5.2：状态等价关系

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

### 定义 5.3：step simulation

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

### 定理 5.4：step simulation 推出序列级等价

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

### 推论 5.5：kernel 等价证明路线

若 optimized implementation 能逐 phase 保持：

- read scope。
- write target。
- commit timing。
- workspace lifetime。
- persistent state equivalence。

并且每个 optimized phase 在状态等价关系下模拟 reference phase，则 optimized StepTransition step-simulates reference StepTransition。

由定理 5.4，optimized sequence 与 reference sequence 等价。

## 6. 当前数学结论

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

## 7. 下一数学阶段

本节只列出尚未证明的目标，不把它们记作当前定理。

1. **Finite Logical Event DAG Representation Lemma**：若一次 execution 产生有限 event，且所有 dependencies 严格增加良基 logical rank，则 dynamic event graph 是有限 DAG。
2. **Dependency-Complete Local Refinement Theorem**：若参考事件 DAG 依赖完备，实现对每个事件或子 DAG 给出局部 simulation 或 semantics-preserving quotient，参考依赖被保留为路径、融合算子内部顺序或经证明安全消除，且提取映射交换，则 chunk implementation 正确。
3. **Zero-Delay Cycle Dichotomy**：同一 logical rank 内的 dependency cycle 没有普通 topological evaluation；必须增加 delay/state boundary、把 SCC 声明为具有独立语义的 simultaneous/fixed-point kernel，或判定 program 非法。
4. **No Semantic Resurrection Audit**：quotient kernel 应直接消费 quotient representation；若通过 reconstruction 恢复 fine representation，必须证明 reference contract 允许该代表元，并把 inverse/re-encoding 的 work、span、memory 与 communication 全部计入成本。
5. **Dynamic Tide Instantiation**：在上述结果稳定后，再把 mailbox、phase、selector、readout、pronounce 等机制逐个实例化，而不是一次性证明完整 LH。
