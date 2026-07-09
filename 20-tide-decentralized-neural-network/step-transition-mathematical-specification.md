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

若 $a\in A^L$，则写作：

$$
a_{0:L}=(a_0,\ldots,a_{L-1})
$$

空序列记作：

$$
a_{0:0}=()
$$

### 定义 0.3：有限索引族

若 $I$ 是有限集合，记：

$$
A^I=\{f:I\to A\}
$$

也就是说，$A^I$ 是以 $I$ 为索引的一组 $A$ 中元素。

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

定义顺序 fold 函数：

$$
\operatorname{Fold}_{\mathcal{T}}:X^L\times\mathcal{S}\to Y^L\times\mathcal{S}
$$

其中：

$$
\operatorname{Fold}_{\mathcal{T}}(x_{0:L},S_0)=(y_{0:L},S_L)
$$

当 $L=0$ 时：

$$
\operatorname{Fold}_{\mathcal{T}}(x_{0:0},S_0)=((),S_0)
$$

这就是后文所谓 `fold` 的严格含义。

### 定义 1.3：Decode 语义

给定 transition system $\mathcal{T}$，定义 decode 语义为：

$$
\operatorname{Decode}_{\mathcal{T}}(x_{0:L},S_0)
:=
\operatorname{Fold}_{\mathcal{T}}(x_{0:L},S_0)
$$

也就是说，decode 是逐 token 应用同一个单步 transition。

### 定义 1.4：顺序 prefill 语义

给定 transition system $\mathcal{T}$，定义最保守的顺序 prefill 语义为：

$$
\operatorname{Prefill}^{seq}_{\mathcal{T}}(x_{0:L},S_0)
:=
\operatorname{Fold}_{\mathcal{T}}(x_{0:L},S_0)
$$

这里的 `seq` 明确表示它只是顺序 fold，不代表高性能并行 prefill。

### 定理 1.5：顺序 prefill 与 decode 等价

对任意 transition system $\mathcal{T}$、任意 $L\in\mathbb{N}$、任意 $x_{0:L}\in X^L$、任意 $S_0\in\mathcal{S}$：

$$
\operatorname{Prefill}^{seq}_{\mathcal{T}}(x_{0:L},S_0)
=
\operatorname{Decode}_{\mathcal{T}}(x_{0:L},S_0)
$$

证明：

二者都被定义为：

$$
\operatorname{Fold}_{\mathcal{T}}(x_{0:L},S_0)
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
\operatorname{Fold}_{\mathcal{T}}(x_{0:L},S_0)
$$

### 定义 2.3：三个层次

本页区分三个层次：

1. 顺序 fold 等价：$\operatorname{Prefill}^{seq}_{\mathcal{T}}=\operatorname{Decode}_{\mathcal{T}}$。这是定义性等价。
2. chunk forward 等价：证明某个 $\mathcal{C}_L$ 满足定义 2.2。
3. 高性能并行 prefill：进一步要求 $\mathcal{C}_L$ 可通过并行、融合、重排或 packed layout 高效实现，同时仍满足定义 2.2。

层次 1 不推出层次 2；层次 2 不推出层次 3。

## 3. B0：最小 Graph Runtime

这一节定义简化分支 B 的最小版本。它不包含 LH 的 phase、selector、readout cache 或 pronounce memory。

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
H=\text{node activation space}
$$

$$
M=\text{message space}
$$

$$
Y=\text{output/logit space}
$$

B0 的持久状态空间为：

$$
\mathcal{S}_{B0}=H^V
$$

若 $h\in H^V$，则 $h_v$ 表示节点 $v$ 的 activation。

### 定义 3.3：B0 kernels

给定输入注入函数：

$$
\iota:X\to H
$$

对每个 round $r\in\{1,\ldots,R\}$ 与每条边 $e\in E$，给定 edge kernel：

$$
\phi_e^r:H\to M
$$

对每个节点 $v\in V$ 与 round $r\in\{1,\ldots,R\}$，先定义该节点 mailbox 空间：

$$
\mathcal{B}_v=M^{E^{-}(v)}
$$

给定聚合函数：

$$
\operatorname{Agg}_v^r:M^{E^{-}(v)}\to \mathcal{B}_v
$$

以及 node update kernel：

$$
\psi_v^r:H\times\mathcal{B}_v\to H
$$

给定 readout 函数：

$$
\rho:H\to Y
$$

### 定义 3.4：B0 单步 transition

定义：

$$
\mathcal{T}^{B0}:X\times H^V\to Y\times H^V
$$

对任意 $x\in X$ 与 $h\in H^V$，$\mathcal{T}^{B0}(x,h)$ 按以下方式计算。

先定义 step-local activation：

$$
a^0\in H^V
$$

其中：

$$
a_i^0=\iota(x)
$$

$$
a_v^0=h_v,\quad v\neq i
$$

对每个 round $r=1,\ldots,R$，对每条边 $e\in E$ 定义消息：

$$
m_e^r=\phi_e^r(a_{\operatorname{src}(e)}^{r-1})
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
a_v^r=\psi_v^r(a_v^{r-1},b_v^r)
$$

执行完 $R$ 个 round 后，定义输出：

$$
y=\rho(a_o^R)
$$

定义下一持久状态：

$$
h'=a^R
$$

于是：

$$
\mathcal{T}^{B0}(x,h)=(y,h')
$$

### 定理 3.5：B0 的顺序 prefill / decode 等价

对任意 $L\in\mathbb{N}$、任意 $x_{0:L}\in X^L$ 与任意 $h_0\in H^V$：

$$
\operatorname{Prefill}^{seq}_{\mathcal{T}^{B0}}(x_{0:L},h_0)
=
\operatorname{Decode}_{\mathcal{T}^{B0}}(x_{0:L},h_0)
$$

证明：

由定理 1.5，取 $\mathcal{T}=\mathcal{T}^{B0}$ 即得。

证毕。

## 4. B-family：逐层增加机制

这一节把 B0 扩展为 B1-B7。每一层都先声明新增 state / workspace / kernel，再讨论等价性。

### B1：node memory

#### 定义 4.1：B1 状态空间

给定 node memory space：

$$
U=\text{node memory space}
$$

B1 的持久状态空间为：

$$
\mathcal{S}_{B1}=H^V\times U^V
$$

记状态为：

$$
S=(h,\mu)
$$

其中 $h\in H^V$，$\mu\in U^V$。

#### 定义 4.2：B1 kernels

B1 edge kernel 类型变为：

$$
\phi_e^r:H\times U\to M
$$

B1 node update 类型变为：

$$
\psi_v^r:H\times U\times \mathcal{B}_v\to H\times U
$$

#### 定义 4.3：B1 transition

B1 transition：

$$
\mathcal{T}^{B1}:X\times\mathcal{S}_{B1}\to Y\times\mathcal{S}_{B1}
$$

对任意 $x\in X$ 与 $(h,\mu)\in\mathcal{S}_{B1}$，先定义：

$$
a_i^0=\iota(x)
$$

$$
a_v^0=h_v,\quad v\neq i
$$

并令：

$$
\mu^0=\mu
$$

对每个 round $r=1,\ldots,R$ 与每条边 $e\in E$，定义：

$$
m_e^r=
\phi_e^r(a_{\operatorname{src}(e)}^{r-1},\mu_{\operatorname{src}(e)}^{r-1})
$$

对每个节点 $v\in V$，定义：

$$
b_v^r=
\operatorname{Agg}_v^r
\left(
(m_e^r)_{e\in E^{-}(v)}
\right)
$$

每个节点更新产生：

$$
(a_v^r,\mu_v^r)=\psi_v^r(a_v^{r-1},\mu_v^{r-1},b_v^r)
$$

下一持久状态为：

$$
S'=(a^R,\mu^R)
$$

只要 decode 与 prefill 使用同一个 $\mathcal{T}^{B1}$，顺序 fold 等价由定理 1.5 成立。

高性能 chunk prefill 还必须证明任意 token $t$ 的 $\mu$ 更新不依赖未来 token。

### B2：typed edge 与 token-local mailbox

#### 定义 4.4：edge role

给定有限 edge role 集合 $R_E$ 与 edge role 函数：

$$
\tau_E:E\to R_E
$$

typed edge kernel 可写为：

$$
\phi_{\tau_E(e)}^r:H\times U\to M
$$

#### 定义 4.5：mailbox workspace

对每个 token step 与 round，引入临时 mailbox：

$$
W_{box}^r=(b_v^r)_{v\in V}
$$

其中 $b_v^r\in\mathcal{B}_v$。

mailbox 不是持久状态。若没有显式 commit，$W_{box}^r$ 不属于下一 token 的 $S'$。

### B3：phase schedule

#### 定义 4.6：phase

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

#### 定义 4.7：schedule

一个 token step 内的 schedule 是有限 phase 序列：

$$
\Pi=(p_1,\ldots,p_K)
$$

其中 $K\in\mathbb{N}_{>0}$。

若存在 internal round，可写成 phase 序列的序列：

$$
\Pi=(\Pi^1,\ldots,\Pi^R)
$$

其中：

$$
\Pi^r=(p_1^r,\ldots,p_{K_r}^r)
$$

#### 定义 4.8：phase transition

给定初始化函数：

$$
I:X\times\mathcal{S}\to\mathcal{W}
$$

以及 finalize 函数：

$$
F:\mathcal{S}\times\mathcal{W}\to Y\times\mathcal{S}
$$

定义 phase-based transition：

$$
\mathcal{T}^{phase}:X\times\mathcal{S}\to Y\times\mathcal{S}
$$

对输入 $x$ 与状态 $S$，先令：

$$
(S^0,W^0)=(S,I(x,S))
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

#### 约束 4.8a：高性能并行 prefill 的基本语义约束

给定定义 2.1 的 chunk prefill implementation $\mathcal{C}_L$，并令定义 2.2 中的 reference transition 为：

$$
\mathcal{T}=\mathcal{T}^{phase}
$$

若 $\mathcal{C}_L$ 通过并行、融合、重排或 packed layout 实现 $\mathcal{T}^{phase}$，则至少必须保持：

- token causality：位置 $t$ 的输出与状态不得依赖任意 $x_{t'}$，其中 $t'>t$。
- phase barrier：不同 phase 的可见性边界不得被无证明地重排。
- read visibility：每个 $\operatorname{read}_p$ 看到的 state/workspace 与 $\operatorname{Fold}_{\mathcal{T}}$ 一致。
- write / commit order：每个 $\operatorname{commit}_p$ 的效果与 $\operatorname{Fold}_{\mathcal{T}}$ 一致，除非证明可交换或可结合。
- workspace lifetime：token-local workspace 不得跨 token 泄漏。

这些是证明 $\mathcal{C}_L$ 满足定义 2.2 的必要审查项，不是充分条件。

### B4：selector / controller state

#### 定义 4.9：controller state

给定 controller scope 集合 $C$ 与 controller state space $Q$。

controller state 空间为：

$$
Q^C
$$

若 $q\in Q^C$，则 $q_c$ 是 scope $c\in C$ 的 controller state。

#### 定义 4.10：selector kernel

给定候选空间 $\mathcal{A}$ 与 active-set 空间 $\mathcal{R}$。

selector kernel 是函数：

$$
\sigma:\mathcal{A}\times Q^C\to \mathcal{R}\times Q^C
$$

其输出既包含被选择的 active set，也包含更新后的 controller state。

若 chunk prefill 把多个 token 的候选集合联合输入 selector，必须证明该联合 selector 与逐 token 应用 $\sigma$ 的 fold 等价。

### B5：token-local readout cache

#### 定义 4.11：readout cache

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

### B6：pronounce memory

#### 定义 4.12：pronounce memory

给定 pronounce memory space $P$。

令不含 pronounce memory 的基础持久状态空间为：

$$
\mathcal{S}_{base}
$$

加入 pronounce memory 后，完整持久状态空间为：

$$
\mathcal{S}_{B6}=\mathcal{S}_{base}\times P
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

### B7：input/output roles 与 bridge

#### 定义 4.13：role-aware graph

给定 node role 集合 $R_V$ 与 edge role 集合 $R_E$。

role-aware graph 为：

$$
G=(V,E,\tau_V,\tau_E,A)
$$

其中：

$$
\tau_V:V\to R_V
$$

$$
\tau_E:E\to R_E
$$

$A$ 是 anchor 集合，例如 input anchor、readout anchor、bridge anchor。

对 LH-like runtime，通常至少区分：

$$
V=V_{in}\cup V_{out}
$$

以及：

$$
E=E_{in}\cup E_{out}\cup E_{io}\cup E_{oi}
$$

其中 $E_{io}$ 与 $E_{oi}$ 是有方向的 bridge edge。

#### 定义 4.14：LH-like schedule 约束

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

- 每个 $p_*$ 都是定义 4.6 中的 phase。
- $p_{oi}$ 读 output-side 旧状态，写 input-side mailbox。
- $p_{input}$ 在指定 internal round 写 input anchor。
- $p_{io}$ 读 input-side 旧状态，写 output-side mailbox。
- $p_{in\_update}$ 只更新 input-side state namespace。
- $p_{out\_update}$ 只更新 output-side state namespace。
- $p_{cache}$ 只读 output readout anchor，写 token-local readout cache。

B7 已经接近 LH，但它是否等价于 LH C++，还取决于 selector、hidden、KV cache、pronounce 与 tie-breaking 等 kernel 细节是否逐 phase 对齐。

### 引理 4.15：B-family 的顺序 fold 等价

对任意 $k\in\{0,\ldots,7\}$，若 Bk 定义出一个 transition system：

$$
\mathcal{T}^{Bk}:X\times\mathcal{S}_{Bk}\to Y\times\mathcal{S}_{Bk}
$$

则对任意 $L\in\mathbb{N}$、$x_{0:L}\in X^L$、$S_0\in\mathcal{S}_{Bk}$：

$$
\operatorname{Prefill}^{seq}_{\mathcal{T}^{Bk}}(x_{0:L},S_0)
=
\operatorname{Decode}_{\mathcal{T}^{Bk}}(x_{0:L},S_0)
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
\operatorname{Fold}_{\mathcal{T}}(x_{0:L},S_0)=(y_{0:L},S_L)
$$

$$
\operatorname{Fold}_{\widehat{\mathcal{T}}}(x_{0:L},\widehat{S}_0)=(\widehat{y}_{0:L},\widehat{S}_L)
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
- 真正需要证明的是 chunk implementation $\mathcal{C}_L$ 是否等价于 $\operatorname{Fold}_{\mathcal{T}}$。
- B0-B7 的每一层只要定义出清楚的单步 transition，就保持顺序 fold 等价。
- selector、pronounce memory、KV append、phase barrier、workspace lifetime 是最容易破坏 chunk/prefill 等价的机制。
- packed / crossbatch / backend lowering 的正确证明入口是 step simulation，而不是只比较最终 logits。
