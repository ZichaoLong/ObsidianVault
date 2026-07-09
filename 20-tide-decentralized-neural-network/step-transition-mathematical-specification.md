---
type: note
status: active
tags:
  - tide
  - prefill-decode
  - step-transition
  - math
---

# StepTransition Mathematical Specification

> [!summary] 本页定位
> 本页只处理 `StepTransition`、`prefill`、`decode`、chunk prefill 与 kernel 优化的数学定义。实现对象、LH 映射、phase 工程约束放在 [[step-transition-implementation-specification]]。

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

## 1. Transition 与顺序 Fold

这一节先定义最基础的 transition 与 fold。后文所有 `prefill = decode fold` 都引用这里的定义。

### 定义 1.1：单步 transition system

给定三个集合：

$$
X=\text{input/token space}
$$

$$
Y=\text{output/logit space}
$$

$$
\mathcal{S}=\text{persistent state space}
$$

一个单步 transition system 是函数：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

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

证明：

二者都被定义为：

$$
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

因此等价。

证毕。

## 2. 三个等价性层次

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
$$

### 定义 2.3：三个层次

本页区分三个层次：

1. 顺序 fold 等价：对每个 $L$，$\operatorname{Prefill}^{seq,L}_{\mathcal{T}}=\operatorname{Decode}_{\mathcal{T}}^L$。这是定义性等价。
2. chunk forward 等价：证明某个 $\mathcal{C}_L$ 满足定义 2.2。
3. 高性能并行 prefill：进一步要求 $\mathcal{C}_L$ 可通过并行、融合、重排或 packed layout 高效实现，同时仍满足定义 2.2。

层次 1 不推出层次 2；层次 2 不推出层次 3。

## 3. B0：标准 Factorized Graph Runtime

这一节定义简化分支 B 的基线版本。这个基线应从一开始就能自然表达 Transformer、Mamba / SSM、Linear Attention 等主流自回归模型。

B0 已经吸收了旧版本中“factorized node state”的 B1：节点状态从一开始就拆成 visible activation 与 private memory/cache/state。这样做的目的，是让起点本身就是高性能自回归模型熟悉的形式，而不是先定义一个过弱的 activation-only graph，再额外补 memory/cache。

B0 不包含 LH-style input/output cortex、bridge phase、selector、readout cache 或 pronounce memory。但它包含标准自回归模型需要的两个基本状态因子：

- 当前 token 在该 node 上的可通信 activation。
- node 私有的跨 token memory/cache/state。

### 定义 3.1：B0 静态结构

令 $V$ 是有限非空节点集合，$E\subseteq V\times V$ 是有向边集合。

定义有向图：

$$
G=(V,E)
$$

指定输入节点与输出节点：

$$
i\in V,\quad o\in V
$$

令 $R\in\mathbb{N}_{>0}$ 为每个 external token step 内的 internal round 数。

### 定义 3.2：B0 空间

给定集合：

$$
X=\text{input/token space}
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
Y=\text{output/logit space}
$$

定义带 empty signal 的 message space：

$$
\overline{M}=M\cup\{\bot\}
$$

其中 $\bot\notin M$，表示当前 round 没有有效消息。

B0 的持久状态空间为：

$$
\mathcal{S}_{B0}=A^V\times U^V
$$

若 $(a,\mu)\in A^V\times U^V$，则：

- $a_v\in A$ 是节点 $v$ 当前可通信 activation / residual stream slot。
- $\mu_v\in U$ 是节点 $v$ 的私有 memory/cache/state。

对 Transformer，$\mu_v$ 可包含该层 KV cache；对 Mamba / SSM，$\mu_v$ 可包含 SSM recurrent state；对 Linear Attention，$\mu_v$ 可包含 prefix accumulator。$a_v$ 通常是当前 token 的 residual / activation slot，它可以在每个 token step 初始化时被清空或覆盖。

### 定义 3.3：B0 kernels

给定 step 初始化函数：

$$
\operatorname{Init}:X\times A^V\times U^V\to A^V\times U^V
$$

`Init` 负责把当前 token 写入 input anchor，并按模型语义初始化当前 token 的 activation slots。典型行为是：

- 在 input node 写入 token embedding。
- 清空或覆盖非 input node 的当前-token activation slot。
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

以及 node update kernel：

$$
\psi_v^r:A\times U\times\mathcal{B}_v\to A\times U
$$

给定 readout 函数：

$$
\rho:A\times U\to Y
$$

### B0 与已知架构的直观对应

B0 的作用不是发明一种新 kernel，而是把“一个 token step 内，状态如何沿 graph 被局部 kernel 更新”写成统一形式。许多熟知架构可以被看成 B0 的特例或近似特例。

标准表达方式一是 block-as-node chain。对一个有 $N$ 个 block 的 Transformer / Mamba，可写为：

$$
V=\{0,\ldots,N\}
$$

$$
E=\{(j,j+1)\mid j=0,\ldots,N-1\}
$$

其中 node $0$ 是 input / embedding anchor，node $1,\ldots,N$ 分别代表 $N$ 个 layer / block，输出节点为 $o=N$。若不单独计算 input anchor，读者也可以把“$N$ 个 block node”理解为主模型部分；本文公式显式保留 input anchor，因此 $|V|=N+1$。

一个 token step 内运行 $R=N$ 个 round 时，信息可以沿 chain 从输入端逐步传播到输出端。标准 chain 的 round gating 可写成：对任意 $j=1,\ldots,N$、$a\in A$ 与 $\mu\in U$，

$$
\phi_{(j-1,j)}^r(a,\mu)=\bot\quad \text{when } r\neq j
$$

也就是说，第 $j$ 个 block 只在第 $j$ 个 round 接收来自上一个 block 的当前 token activation。尚未收到有效输入的节点，其 $\psi_v^r$ 可以是 identity / no-op。

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
| Transformer attention block | $a_v$ 是当前 token residual activation，$\mu_v$ 是该层 KV cache；$\psi_v^r$ 做 Q/K/V projection、KV append、causal attention、output projection；$\phi_e^r$ 抽取要传给下一层的 residual stream。 | 标准 causal attention 的 prefill 与逐 token decode 等价，前提是 causal mask、position encoding、KV append order 与数值实现一致。 |
| Transformer FFN / MLP block | $a_v$ 是当前 token residual activation，$\mu_v$ 可为空或平凡；$\psi_v^r$ 是 FFN/MLP；$\phi_e^r$ 抽取 FFN 后 activation。 | FFN 对 token 位置逐点作用，没有跨 token recurrence；只要输入 activation 一致，prefill 与 decode 逐点一致。 |
| Mamba / SSM block | $a_v$ 是当前 token activation，$\mu_v$ 是 SSM recurrent state；$\psi_v^r$ 做 selective state update 与输出；$\phi_e^r$ 抽取传给下一层的 activation。 | decode 是 recurrent update；prefill 等价依赖 scan / chunk scan 实现与逐步 recurrence 等价。 |
| Linear attention block | $a_v$ 是 current activation，$\mu_v$ 是 linear-attention accumulator；$\psi_v^r$ 更新 accumulator 并产生当前输出。 | prefill 等价依赖 accumulator 的 causal prefix 更新与逐 token update 等价。 |

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

证明：

由定理 1.5，取 $\mathcal{T}=\mathcal{T}^{B0}$ 即得。

证毕。

## 4. B-family：逐层增加机制

这一节把 B0 扩展为 B1-B6。B0 已经是能表达 Transformer/Mamba 的标准 factorized graph runtime；后续层级不再引入“基本 memory/cache”，而是增加更强的 graph/runtime 结构。B1-B6 更准确地说是 extension schema：它们声明新增 state / workspace / kernel / schedule 约束。只有当这些 schema 与具体 kernel 组合成单步 transition 后，才可应用后面的 B-family 引理。

### B1：typed edge 与 token-local mailbox

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

对每个 token step 与 round，引入临时 mailbox：

$$
W_{box}^r=(b_v^r)_{v\in V}
$$

其中 $b_v^r\in\mathcal{B}_v$。

mailbox 不是持久状态。若没有显式 commit，$W_{box}^r$ 不属于下一 token 的 $S'$。

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
- workspace lifetime：token-local workspace 不得跨 token 泄漏。

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

给定候选空间 $\mathcal{C}_{cand}$ 与 active-set 空间 $\mathcal{R}$。

selector kernel 是函数：

$$
\sigma:\mathcal{C}_{cand}\times Q^C\to \mathcal{R}\times Q^C
$$

其输出既包含被选择的 active set，也包含更新后的 controller state。

若 chunk prefill 把多个 token 的候选集合联合输入 selector，必须证明该联合 selector 与逐 token 应用 $\sigma$ 的 fold 等价。

### B4：token-local readout cache

#### 定义 4.8：readout cache

给定 cache element space $Z$。若每个 token 内有 $R$ 个 internal round，则 token-local readout cache 空间可写为：

$$
Z^R
$$

对 token $t$ 的 readout cache 记为：

$$
c_t=(z_t^1,\ldots,z_t^R)\in Z^R
$$

约束是：

$$
c_t\text{ 不属于持久状态，且不得被 token }t+1\text{ 读取}
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
- $p_{cache}$ 只读 output readout anchor，写 token-local readout cache。

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

证明：

由定理 1.5 直接得到。

证毕。

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
- sparse signal vector 与 packed active rows 表示同一组 activation。
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

证明：

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

证毕。

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
- 真正需要证明的是 chunk implementation $\mathcal{C}_L$ 是否等价于 $\operatorname{Fold}_{\mathcal{T}}^L$。
- B0-B6 的每一层只要定义出清楚的单步 transition，就保持顺序 fold 等价。
- selector、pronounce memory、KV append、phase barrier、workspace lifetime 是最容易破坏 chunk/prefill 等价的机制。
- packed / crossbatch / backend lowering 的正确证明入口是 step simulation，而不是只比较最终 logits。
