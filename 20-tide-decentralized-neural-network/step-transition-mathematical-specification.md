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
| Transformer attention block | $a_v$ 是当前 token residual activation，$\mu_v$ 是该层 KV cache；$\psi_v^r$ 做 Q/K/V projection、KV append、causal attention、output projection；$\phi_e^r$ 抽取要传给下一层的 residual stream。 | 标准 causal attention 的 prefill 与逐 token decode 等价，前提是 causal mask 与 KV append order 一致；position signal 暂不作为 attention 证明核心，若引入则必须由 decode/chunk 一致的确定性 position 函数给出。 |
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

### B0 proof gate：主流 kernel family 的 chunk prefill 正确性

B0 的理论入口不应停在“能表达 Transformer / Mamba”。真正的 B0 proof gate 是：在 B0 内给出具体 kernel family 的 reference transition $\mathcal{T}$、chunk implementation $\mathcal{C}_L$，并证明 $\mathcal{C}_L$ 满足定义 2.2。

也就是说，B0 先要证明若干重要特例满足：

$$
\mathcal{C}_L(x_{0:L},S_0)=\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

这些特例不是任意 B0 graph / 任意 B0 kernel，而是 Transformer / Mamba / Linear Attention / FFN 这类后续会反复使用的主力 kernel family。后续 B1-B6 的问题，是在这些已证明正确的 B0 kernel 之上继续加入 mailbox、phase、selector、readout、pronounce 等机制，并检查它们是否保持或破坏 chunk prefill 正确性。

#### 定义 3.6：B0 kernel family 通过 proof gate

给定一个 B0 kernel family $\mathfrak{K}$。称 $\mathfrak{K}$ 通过 B0 proof gate，当且仅当对每个具体参数实例 $\theta\in\Theta_{\mathfrak{K}}$：

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

给定长度 $L\in\mathbb{N}$。令 $\mathcal{EID}_L$ 是有限 logical event id 集合。每个 event id $e\in\mathcal{EID}_L$ 都带有 external token index：

$$
\tau(e)\in[L]
$$

并给定 logical event order：

$$
\prec_L
$$

要求 $\prec_L$ 是 strict total order，并且若 $\tau(e)<\tau(e')$，则 $e\prec_L e'$。也就是说，decode reference 的 logical order 至少按 external token tick 单调；同一 token 内可继续包含 internal round、phase、node、edge、mailbox 等字段。

例如，普通 Transformer 可取：

$$
e=(t,o)
$$

其中 $o$ 是 token-local operation slot。LH-like runtime 可取：

$$
e=(t,r,p,v)
$$

其中 $t$ 是 external token tick，$r$ 是 internal round tick，$p$ 是 phase，$v$ 是 node 或 edge endpoint。

一个长度为 $L$ 的 logical event graph 的节点集合为：

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

条件 2 表示依赖只来自 reference logical order 中更早的 event；由于 $\prec_L$ 至少按 external token tick 单调，它排除 future-token dependency。物理执行可以乱序，但逻辑依赖必须能映射回这个 DAG。

对每个节点 $n\in\mathcal{N}_L$，给定 value space $\mathcal{V}_n$。若 $\operatorname{Pred}(n)$ 是 $n$ 的直接前驱集合，则给定局部 kernel：

$$
F_n:
\left(\prod_{m\in\operatorname{Pred}(n)}\mathcal{V}_m\right)
\times X^L
\times\mathcal{S}
\to
\mathcal{V}_n
$$

这里把输入序列 $x_{0:L}$ 与初始 state $S_0$ 作为 boundary data 传入，是为了统一表达 input injection、position / clock、old KV cache、old SSM state 等边界信息。

还要求每个 $F_n$ 满足 prefix-causal boundary condition。若 $\tau(n)=t$，则 $F_n$ 对 $x_{0:L}$ 的依赖只能通过前缀 $x_{0:t+1}$。形式化地说，若两个输入序列 $x_{0:L}$ 与 $\bar{x}_{0:L}$ 满足：

$$
x_j=\bar{x}_j,\quad j=0,\ldots,t
$$

则在相同前驱值与相同初始 state 下，$F_n$ 的输出相同。若某个 $F_n$ 使用 $x_{t'}$ 且 $t'>t$，则该 program 不满足 causal chunk 前提。

给定 output / final-state extraction 函数：

$$
G_L:
\left(\prod_{n\in\mathcal{N}_L}\mathcal{V}_n\right)
\times X^L
\times\mathcal{S}
\to
Y^L\times\mathcal{S}
$$

一个 time-expanded graph program 是：

$$
\mathcal{P}_L=(D_L,(F_n)_{n\in\mathcal{N}_L},G_L)
$$

#### 定义 3.6b：decode unfolding 与 chunk evaluation 一致

给定 transition system：

$$
\mathcal{T}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

以及 time-expanded graph program $\mathcal{P}_L$。

定义 decode order 为 $\prec_L$ 限制在 $\mathcal{N}_L$ 上得到的节点顺序。

称 $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}}^L$ 的 decode unfolding，当且仅当对所有 $x_{0:L}\in X^L$ 与 $S_0\in\mathcal{S}$，若按 decode order 计算 $\mathcal{P}_L$ 中所有节点值，并再应用 $G_L$，得到的结果等于：

$$
\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)
$$

称 chunk implementation $\mathcal{C}_L$ 是 $\mathcal{P}_L$ 的 graph evaluation，当且仅当对所有 $x_{0:L}$ 与 $S_0$，$\mathcal{C}_L$ 计算同一个 $D_L$、同一组 kernel $(F_n)$ 与同一个 extraction $G_L$，但允许使用任意 topological order、batched evaluation、masked matmul、parallel scan、fusion 或 packed layout，只要每个节点的数学值与 $\mathcal{P}_L$ 中的方程相同。

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

证明：

因为 $D_L$ 是 DAG，所以存在 topological order。decode order 是 $D_L$ 的一个 topological order，因为每条边都指向 $\prec_L$ 中更晚的 event。

任取另一个 topological order。对该 order 做归纳。设当前节点为 $n$。它的所有前驱都已在两个 evaluation 中被计算。归纳假设给出所有前驱值相同。由于两个 evaluation 使用同一个 kernel $F_n$、同一个输入 $x_{0:L}$ 与同一个初始状态 $S_0$，当前节点值也相同。

归纳到所有节点后，两个 evaluation 中所有节点值完全相同。再由于二者使用同一个 extraction $G_L$，输出序列与最终 state 相同。

又因为 $\mathcal{P}_L$ 是 $\operatorname{Fold}_{\mathcal{T}}^L$ 的 decode unfolding，decode order evaluation 后应用 $G_L$ 等于 $\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)$。因此任意 graph evaluation，即 $\mathcal{C}_L$，也等于 $\operatorname{Fold}_{\mathcal{T}}^L(x_{0:L},S_0)$。

证毕。

这个定理只证明 correctness。它不声称 $\mathcal{C}_L$ 自动高性能。高性能来自具体 kernel family 的额外结构，例如 token-wise map 的批量化、attention 的 masked matmul / fused attention、affine recurrence 的 parallel scan、有限 layer chain 的逐层批量执行。

#### 备注 3.6d：logical order 与物理到达顺序

定理 3.6c 约束的是 logical dependency order，不是物理执行或消息到达顺序。对一般 graph runtime，特别是 LH-like runtime，可以允许 late-token 的消息在物理上先于 early-token 的消息到达某个 node，只要这些消息带有足够的 logical metadata，例如：

$$
(\text{token id},\text{internal round id},\text{phase id},\text{source node id})
$$

并且 node kernel 按 metadata 分桶、排序、mask 或 buffer，最终读取的仍是 reference logical visibility set。

可以保持 correctness 的情况包括：

- message 保留 token / round / phase 等 logical timestamp。
- mailbox 或 workspace 中的聚合是 tagged collection，后续 kernel 仍可区分不同 logical event 的贡献。
- 对同一个 state slot 的 commit order 由 $\prec_L$ 或明确的 conflict resolution 规则决定，而不是由物理 arrival order 决定。
- chunk implementation 虽然乱序执行，但最终每个 logical event 的值与 reference DAG 方程相同。

会破坏 chunk prefill correctness 的情况包括：

- 多个不同 token 或 round 的消息在 node 内被不可逆聚合，且聚合结果丢失 token / round / phase provenance。
- kernel 的行为依赖 physical first-arrival / race order，而 reference transition 依赖 logical order。
- late-token 的信息通过无标记聚合影响 early-token 的 event、output 或 state commit。

因此，完整涵盖既有 LH 实现不一定可能。若 LH 某处把同一 tick 收到的多源信号做不可逆、无时间戳的聚合，则 token influence relation 可能被折叠，无法构造与 decode fold 等价的 event DAG。要让 LH-like graph 支持 chunk prefill correctness，需要把聚合改成可追踪的 tagged aggregation，或证明该聚合对所有相关 kernel 是可交换、可结合、且不影响 reference logical visibility。

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

证明：

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

证毕。

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

证明：

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

证毕。

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

定义 chunk implementation：

$$
\mathcal{C}^{scan}_{L}(x_{0:L},h_0)=((y_0,\ldots,y_{L-1}),h_L)
$$

则 $\mathcal{C}^{scan}_{L}$ 对 $\mathcal{T}^{scan}$ 正确。

证明：

函数复合满足结合律。顺序 decode 的状态满足：

$$
h_{t+1}=g_t(h_t)
$$

展开得到：

$$
h_{t+1}=g_t\circ g_{t-1}\circ\cdots\circ g_0(h_0)=G_t(h_0)
$$

输出也同为：

$$
y_t=o(x_t,h_{t+1})
$$

因此 chunk implementation 与顺序 fold 相同。

证毕。

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

证明：

对 layer index $j$ 归纳。$j=1$ 时由 $\mathcal{C}_{1,L}$ 的正确性得到第 1 层所有位置输出 $z^1_{0:L}$ 与最终 state $S_1'$ 等于对 $\mathcal{T}_1$ 做顺序 fold 的结果。

假设前 $j$ 层的 chunk 输出序列与这些层的最终 state 等于 reference stack 在前 $j$ 层逐 token 执行的结果。则第 $j+1$ 层收到的输入序列 $z^j_{0:L}$ 与初始 state $S_{j+1}$ 与 reference 相同。由 $\mathcal{C}_{j+1,L}$ 的正确性，第 $j+1$ 层输出与 state 也相同。

归纳到 $N$，得到 $\mathcal{C}^{stack}_L$ 与 $\operatorname{Fold}_{\mathcal{T}^{stack}}^L$ 相同。

证毕。

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

证明：

token-wise deterministic kernels 由定理 3.7 满足 chunk prefill 正确性。causal attention kernel 由定理 3.9 满足 chunk prefill 正确性。有限个 attention head 的 product / concat 是有限个相同输入上的 component-wise transition；每个 component 的 chunk 输出与顺序 fold 相同，则它们的 product / concat 也相同。attention 后的 output projection、FFN、norm、residual 等仍是 token-wise kernels。

从一般图角度看，Transformer 的 time-expanded graph 只包含同 token layer order、旧 KV cache、当前 chunk 内 causal prefix attention edge，不包含 future-token dependency；position signal 若存在，也由 prefix-causal position / clock 函数给出。因此它满足定理 3.6c 的 causal graph correctness 前提。

因此，每个 Transformer layer 都通过 B0 proof gate。由定理 3.13 的有限 B0 chain layer-wise chunk 正确性，整个 Transformer stack 的 chunk prefill implementation 与逐 token decode fold 相同。

证毕。

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

证明：

token-wise deterministic kernels 由定理 3.7 满足 chunk prefill 正确性。有限宽 causal convolution 是有限维 shift-register 的 affine recurrence，因此由定理 3.11 满足 chunk prefill 正确性。selective SSM recurrence 的状态更新已经写成 $h'=A_xh+b_x$，输出写成 $y=o(x,h')$，因此也由定理 3.11 满足 chunk prefill 正确性。

从一般图角度看，Mamba / SSM 的 time-expanded graph 只包含同 token layer order、有限 causal convolution state、SSM prefix recurrence state，不包含 future-token dependency。因此它满足定理 3.6c 的 causal graph correctness 前提。

因此，每个 Mamba / SSM layer 都通过 B0 proof gate。由定理 3.13 的有限 B0 chain layer-wise chunk 正确性，整个 Mamba / SSM stack 的 chunk prefill implementation 与逐 token decode fold 相同。

证毕。

高性能实现见证：token-wise kernels 可批量矩阵化或融合；causal convolution 与 selective SSM recurrence 的 affine map 复合满足结合律，可用 parallel prefix / scan / chunk scan 实现。因此，B0-Mamba / SSM 在实数语义下满足 chunk prefill 正确性；具体浮点 backend 的误差属于实现层的数值模拟问题。

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
- 定理 3.6c 给出一般 B0 Logical Event DAG Theorem：若 chunk implementation 计算的是同一个 logical event DAG、同一组 kernel equation、同一个 output/final-state extraction，则 correctness 成立。它允许物理执行乱序，但不允许 logical dependency / visibility / commit order 被打乱。
- B0 proof gate 先证明 token-wise / FFN、causal attention、affine scan recurrence、linear attention accumulator 以及有限 layer stack 这些主流 kernel family 的 chunk prefill 正确性；在这些结果上，定理 3.14 给出 B0-Transformer chunk prefill 正确性，定理 3.15 给出 B0-Mamba / SSM chunk prefill 正确性。
- 上述命名定理不推出任意 B0 graph / 任意 B0 kernel 都有高性能 chunk prefill；它们证明的是 Transformer / Mamba 这类主力结构在 B0 中满足 $\mathcal{C}_L=\operatorname{Fold}_{\mathcal{T}}^L$。
- B0-B6 的每一层只要定义出清楚的单步 transition，就保持顺序 fold 等价。
- selector、pronounce memory、KV append、phase barrier、workspace lifetime 是最容易破坏 chunk/prefill 等价的机制。
- packed / crossbatch / backend lowering 的正确证明入口是 step simulation，而不是只比较最终 logits。
