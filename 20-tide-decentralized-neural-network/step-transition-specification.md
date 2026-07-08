---
type: note
status: active
tags:
  - tide
  - prefill-decode
  - step-transition
---

# StepTransition 规范模型

> [!summary] 本页定位
> 本页尝试把 `prefill / decode` 等价性讨论从 LH 的实现细节中抽出来，先定义一个人类可理解的规范模型。它既可作为承载 LH 的上层语义，也可作为后续更简单、更通用大 graph 执行模型的起点。

## 为什么需要这个抽象

当前讨论中，LH 带来了许多实现概念：

- `iacts / oacts`
- `ichs / ochs`
- `iselector / oselector`
- `internal tick`
- bridge phase
- readout cache
- pronounce memory
- selector count
- hidden / KV cache

这些概念对复刻 LH 很重要，但如果直接以它们作为 `prefill / decode` 等价性的证明对象，人类理解成本会很高，也容易被具体实现细节绑住。

因此，需要先定义一个更高层的规范模型：

```text
StepTransition(Graph, Schedule, State, input_token)
  -> output_logits, State'
```

证明与设计应优先落在这个规范模型上，再把 LH 映射进来。

## 人类可理解的五个概念

### 1. Graph

`Graph` 描述系统中有哪些节点、边、角色和 anchor。

它不只是普通无类型图，而是 typed graph：

- node 有 role。
- edge 有 role。
- 有 input anchor。
- 有 readout anchor。
- 可以有 input-side / output-side / bridge 等结构性标签。

### 2. State

`State` 是跨 external token 持久存在的运行时状态。

它至少可包含：

- node activation。
- node memory。
- selector / controller state。
- pronounce / readout memory。

关键点是：`State` 是持久的。token `t+1` 只能读取 token `t` 完整 commit 后的 `State`。

### 3. Workspace

`Workspace` 是当前 token 内的临时状态。

它可包含：

- 当前 internal tick 的 staged messages / extra inputs。
- 当前 token 的 readout cache。

关键点是：`Workspace` 不等于持久 `State`。它的生命周期由 step 和 phase 规则决定。

### 4. Schedule

`Schedule` 是一个 token 内按顺序执行的 phase 列表。

每个 phase 必须声明：

- 读什么。
- 写什么。
- 是否修改持久 state。
- 什么时候 commit。
- 哪些结果只在 workspace 中可见。

### 5. Kernel

`Kernel` 是局部计算函数。

它只负责当前 phase 的局部 transition，例如：

- edge emit。
- message gather。
- node update。
- selector。
- readout。
- pronounce。

kernel 不应偷偷改变 phase 顺序、可见性或 commit timing。

## StepTransition

一个 external token step 可写成：

```text
Step(input_token, State):
  Workspace = empty

  for internal_round in rounds:
    for phase in Schedule:
      view = read(State, Workspace, phase.read_scope)
      delta = Kernel_phase(view, phase.params)
      commit(State, Workspace, delta, phase.write_scope)

  logits, State = ReadoutOrPronounce(State, Workspace)
  return logits, State
```

这就是后续 `prefill / decode` 等价性的核心对象。

人类只需理解：

- 持久 `State`。
- 当前 token 临时 `Workspace`。
- 有序 phase 读写规则。
- 局部 `Kernel`。

## LH 如何纳入

LH 的实现概念可以映射到这个规范模型，而不需要直接成为证明语言。

| LH 内容 | 规范模型中的位置 |
| --- | --- |
| `iacts / oacts` | `State.activation[node_id]`，node 带 input/output role。 |
| `ichs / ochs` | `State.memory[node_id]`。 |
| `iselector / oselector` | `State.controller[selector_scope]`。 |
| `input_extra / output_extra` | `Workspace.mailbox[node_id]`。 |
| `internal tick` | `internal_round`。 |
| `OiBridge / IoBridge` | edge-message phase，读一组 role nodes，写另一组 mailbox。 |
| `ExternalInput` | input injection phase，只在 round 0 写 input anchor mailbox。 |
| `InputUpdate / OutputUpdate` | node-update phase，读 activation + mailbox，写 activation / memory / selector。 |
| `ReadoutCache` | 当前 token 的 workspace accumulator。 |
| `Pronounce` | final readout kernel，读 workspace output cache，改 pronounce memory，输出 logits。 |

因此，LH 可被理解为一个较复杂的 `StepTransition` 实例，而不是 `StepTransition` 本身。

## Prefill / Decode 等价性

在规范模型中，decode 是一步 transition：

```text
Decode(x_t, S_t) = StepTransition(x_t, S_t)
```

prefill 的最基本定义是 decode fold：

```text
Prefill(x_0:T, S_0):
  S = S_0
  for t in 0..T-1:
    y_t, S = Decode(x_t, S)
  return y_0:T, S
```

如果 `prefill` 第一版就是这个 fold，那么模型级等价性由定义成立。

后续优化的证明目标是：

```text
OptimizedKernel(view, state_slice)
==
ReferenceKernel(view, state_slice)
```

同时保持：

- phase 顺序不变。
- read scope 不变。
- write scope 不变。
- commit timing 不变。
- workspace 生命周期不变。
- external token 顺序不变。

如果每个 kernel 替换都满足上述条件，则整个 `StepTransition` 不变；如果每个 step 的 `StepTransition` 不变，则 `prefill` 与 decode fold 等价。

## 三个等价性层次

后续讨论中需要区分三个层次，否则容易把“定义性正确”误认为“高性能 prefill 已经解决”。

### 层次 1：顺序 fold 等价

这是最弱、最干净的语义定义：

$$
\operatorname{Prefill}(x_{0:T},S_0)
:=
\operatorname{fold}_{t=0}^{T-1} T_{x_t}(S_t)
$$

它只说明 prefill 和 decode 使用同一个 step transition。

### 层次 2：chunk forward 等价

工程上更有用的 prefill 通常不是逐 token 调 `Step`，而是一个 chunk kernel：

$$
C(x_{0:T},S_0)\to (y_{0:T},S_T)
$$

此时必须额外证明：

$$
C(x_{0:T},S_0)
=
\operatorname{fold}_{t=0}^{T-1} T_{x_t}(S_t)
$$

这个证明不由 StepTransition 定义自动给出。

### 层次 3：高性能并行 prefill

如果 `C` 还要并行化 token、batch、node、edge 或 internal round，则还需要证明并行执行不会改变：

- token causality。
- phase barrier。
- read visibility。
- write / commit order。
- workspace lifetime。
- persistent state update order。

因此，本页后续所有“prefill = decode”默认指层次 1。只要讨论 `forward_chunk == Step fold` 或 sequence-parallel prefill，就进入层次 2 或层次 3。

## 符号约定：完整 StepTransition 模型

这一节给出承载 LH 或其他复杂 graph runtime 时使用的完整符号集合。它比后面的简化分支 B 更一般。

### 静态结构

设 typed graph 为：

$$
G=(V,E,\tau_V,\tau_E,A)
$$

其中：

- $V$ 是 node 集合。
- $E\subseteq V\times V$ 是 edge 集合。
- $\tau_V:V\to R_V$ 是 node role。
- $\tau_E:E\to R_E$ 是 edge role。
- $A$ 是 anchor 集合，例如 input anchor、readout anchor、bridge anchor。

对 LH-like runtime，$R_V$ 可包含：

$$
\text{input-cortex},\quad
\text{output-cortex},\quad
\text{hub},\quad
\text{lead-point},\quad
\text{local-point}
$$

$R_E$ 可包含：

$$
\text{input-intra},\quad
\text{output-intra},\quad
\text{io-bridge},\quad
\text{oi-bridge}
$$

### 持久状态

设持久状态空间为：

$$
\mathcal{S}
$$

一个状态可写成带命名空间的 state store：

$$
S=
(
S^{act},
S^{mem},
S^{ctrl},
S^{readout},
\ldots
)
$$

例如：

$$
S^{act}:V\times N_{act}\to H
$$

$$
S^{mem}:V\times N_{mem}\to U
$$

$$
S^{ctrl}:C\to Q
$$

这里 $N_{act}$、$N_{mem}$ 是状态命名空间，$C$ 是 controller / selector scope 集合。对 LH，input activation 与 output activation 可以理解为不同 namespace，而不是同一个普通 activation tensor。

### 临时 Workspace

设 step-local workspace 空间为：

$$
\mathcal{W}
$$

workspace 可写成：

$$
W=
(
W^{mailbox},
W^{message},
W^{cache},
W^{artifact},
\ldots
)
$$

其中：

$$
W^{mailbox}:V\times N_{box}\to B
$$

$$
W^{cache}:N_{cache}\to Z
$$

workspace 的关键约束是生命周期：

$$
W_t \text{ 只属于 token } t
$$

除非某个 phase 显式 commit，否则 workspace 内容不能成为 $S_{t+1}$ 的一部分。

### Phase 与 Schedule

一个 phase 定义为：

$$
p=(R_p,K_p,C_p)
$$

其中：

$$
R_p:\mathcal{S}\times\mathcal{W}\to \mathcal{V}_p
$$

是 read function，决定当前 phase 可见的 view。

$$
K_p:\mathcal{V}_p\to \Delta_p
$$

是 kernel function。

$$
C_p:\mathcal{S}\times\mathcal{W}\times\Delta_p
\to
\mathcal{S}\times\mathcal{W}
$$

是 commit function，决定 delta 写入 state 还是 workspace，以及何时对后续 phase 可见。

一个 token 内的 schedule 是有序列表：

$$
\Pi=(p_1,\ldots,p_K)
$$

如果有 internal round：

$$
\Pi=(\Pi^1,\ldots,\Pi^R),
\quad
\Pi^r=(p_1^r,\ldots,p_{K_r}^r)
$$

### StepTransition

给定输入：

$$
x_t\in X
$$

以及 token 开始时的持久状态：

$$
S_t\in\mathcal{S}
$$

初始化：

$$
W_t^{init}=I(x_t,S_t)
$$

并令：

$$
(S_t^0,W_t^0)=(S_t,W_t^{init})
$$

按 schedule 执行：

$$
v_k=R_{p_k}(S_t^{k-1},W_t^{k-1})
$$

$$
\delta_k=K_{p_k}(v_k)
$$

$$
(S_t^k,W_t^k)=
C_{p_k}(S_t^{k-1},W_t^{k-1},\delta_k)
$$

最后：

$$
(y_t,S_{t+1})=F(S_t^K,W_t^K)
$$

其中 $F$ 是 finalize / readout / pronounce。

于是：

$$
T_x:\mathcal{S}\to Y\times\mathcal{S}
$$

$$
T_x(S_t)=(y_t,S_{t+1})
$$

### 语义不变量

任何优化、融合或 backend lowering 都必须保持这些不变量：

- 同一 token 内 phase 顺序不变，除非能证明重排等价。
- 每个 phase 的 read view 不变。
- 每个 phase 的 write target 不变。
- 每个 delta 的 commit timing 不变。
- workspace 不跨 token 泄漏。
- persistent state 只通过声明的 commit function 更新。
- token `t` 不能读 token `t+1` 的 state、workspace 或 selector decision。

## 数学化定义一：简化分支 B 的最小 Graph Runtime

这一节只定义分支 B 的最小版本，不引入 LH 的 phase、selector、readout cache、pronounce memory。

### 定义 1：图与空间

设有向图：

$$
G=(V,E)
$$

其中：

$$
E \subseteq V \times V
$$

指定输入节点与输出节点：

$$
i \in V,\quad o \in V
$$

设：

$$
X=\text{token/input space}
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

### 定义 2：B0 持久状态

B0 只有节点 activation：

$$
S = h \in H^V
$$

即每个节点有：

$$
h_v \in H,\quad v\in V
$$

没有 node memory、selector、phase state、pronounce memory。

### 定义 3：输入注入

给定 token：

$$
x_t \in X
$$

定义输入注入函数：

$$
\iota: X \to H
$$

token `t` 开始时：

$$
h_i^{t,0} = \iota(x_t)
$$

$$
h_v^{t,0} = h_v^t,\quad v\neq i
$$

其中 $h^t$ 是 token `t` 开始前的持久图状态。

### 定义 4：round 内消息传递

对 internal round：

$$
r=1,\ldots,R
$$

每条边产生消息：

$$
m_{u\to v}^{t,r} = \phi_{u\to v}^{r}(h_u^{t,r-1})
$$

其中：

$$
\phi_{u\to v}^{r}: H \to M
$$

节点聚合 incoming messages：

$$
b_v^{t,r} =
\operatorname{Agg}_{v}^{r}
\left(
  \{m_{u\to v}^{t,r} \mid (u,v)\in E\}
\right)
$$

节点更新：

$$
h_v^{t,r}
=
\psi_v^r(h_v^{t,r-1}, b_v^{t,r})
$$

其中：

$$
\psi_v^r: H \times \operatorname{Mailbox}(M) \to H
$$

### 定义 5：输出与状态提交

执行 $R$ 个 round 后：

$$
y_t = \rho(h_o^{t,R})
$$

其中：

$$
\rho: H \to Y
$$

提交下一 token 的持久状态：

$$
h^{t+1} = h^{t,R}
$$

于是 B0 的单步转移定义为：

$$
T_x: H^V \to Y \times H^V
$$

$$
T_x(h^t) = (y_t, h^{t+1})
$$

### 定义 6：Decode

给定序列：

$$
x_{0:T} = (x_0,\ldots,x_{T-1})
$$

decode fold 定义为：

$$
(y_t, h^{t+1}) = T_{x_t}(h^t),\quad t=0,\ldots,T-1
$$

记作：

$$
\operatorname{Decode}_G(x_{0:T}, h^0)
=
(y_{0:T}, h^T)
$$

### 定义 7：Prefill

B0 中最保守的 prefill 定义为同一个单步转移的 fold：

$$
\operatorname{Prefill}_G(x_{0:T}, h^0)
:=
\operatorname{fold}_{t=0}^{T-1}
T_{x_t}(h^t)
$$

因此：

$$
\operatorname{Prefill}_G(x_{0:T}, h^0)
=
\operatorname{Decode}_G(x_{0:T}, h^0)
$$

这是定义性等价。

### 定理 1：B0 的 prefill / decode fold 等价

若 $\operatorname{Prefill}_G$ 被定义为按 token 顺序应用同一个 $T_x$，则对任意 $x_{0:T}$ 与 $h^0$：

$$
\operatorname{Prefill}_G(x_{0:T}, h^0)
=
\operatorname{Decode}_G(x_{0:T}, h^0)
$$

证明：

对序列长度 $T$ 归纳。

当 $T=0$ 时，二者都返回空输出与初始状态 $h^0$。

假设长度 $T$ 成立。长度 $T+1$ 时，前 $T$ 个 token 由归纳假设得到相同的 $y_{0:T}$ 与 $h^T$。第 $T$ 个 token 二者都计算：

$$
(y_T,h^{T+1}) = T_{x_T}(h^T)
$$

因此长度 $T+1$ 也成立。

证毕。

### B0 的边界

定理 1 只说明：

$$
\text{prefill} = \text{sequential decode fold}
$$

它不说明存在高性能并行 prefill。

若要定义一个 chunk prefill：

$$
C_G(x_{0:T}, h^0) \to (y_{0:T}, h^T)
$$

必须额外证明：

$$
C_G(x_{0:T}, h^0)
=
\operatorname{fold}_{t=0}^{T-1} T_{x_t}(h^t)
$$

这通常需要额外结构，例如 causal dependency、可结合 scan、可物化中间 state、checkpoint / recompute，或严格的无未来 token 泄漏约束。

## 数学化定义一-B：简化分支 B 的逐层扩展

这一节把前面的 B0 扩展成一组可逐层增加复杂度的数学对象。它不是 LH 的完整形式化，而是后续研究 `prefill / decode` 等价性时更容易理解的起点。

### B-family 的共同外形

对任意简化 B 模型，都要求存在一个单步转移：

$$
T_x:S\to Y\times S
$$

以及一个按 token 顺序运行的序列语义：

$$
(y_t,S_{t+1})=T_{x_t}(S_t)
$$

这意味着模型首先是一个 causal recurrent graph runtime。所有新增机制都必须说明自己新增了什么 $S$、什么临时 workspace $W$，以及是否改变 $T_x$。

### B1：加入 node memory

B1 的持久状态为：

$$
S=(h,\mu)
$$

其中：

$$
h\in H^V
$$

$$
\mu\in U^V
$$

$h_v$ 是节点 activation，$\mu_v$ 是节点本地 memory。

边消息可以读取 source node 的 activation 与 memory：

$$
m_{u\to v}^{t,r}
=
\phi_{u\to v}^{r}(h_u^{t,r-1},\mu_u^{t,r-1})
$$

聚合仍为：

$$
b_v^{t,r}
=
\operatorname{Agg}_v^r
\left(
\{m_{u\to v}^{t,r}\mid (u,v)\in E\}
\right)
$$

节点更新变成：

$$
(h_v^{t,r},\mu_v^{t,r})
=
\psi_v^r(h_v^{t,r-1},\mu_v^{t,r-1},b_v^{t,r})
$$

提交：

$$
S_{t+1}=(h^{t,R},\mu^{t,R})
$$

若 prefill 仍定义为同一个 $T_x$ 的顺序 fold，则等价性仍由定义成立。

高性能 chunk prefill 的关键约束是：

$$
\mu^{t,r}\text{ 不可依赖任意 }x_{t'>t}
$$

也就是 node memory 的写入顺序不能被未来 token 污染。

### B2：加入 typed edges 与 mailbox

B2 增加 edge role：

$$
\tau_E:E\to R_E
$$

并把当前 round 的消息放入临时 mailbox：

$$
W^{t,r}=b^{t,r}\in B^V
$$

edge kernel 为：

$$
m_{e}^{t,r}
=
\phi_{\tau_E(e)}^r(h_{\operatorname{src}(e)}^{t,r-1},\mu_{\operatorname{src}(e)}^{t,r-1})
$$

mailbox 聚合为：

$$
b_v^{t,r}
=
\operatorname{Agg}_{v,\tau_E}^r
\left(
\{m_e^{t,r}\mid \operatorname{dst}(e)=v\}
\right)
$$

节点更新仍为：

$$
(h_v^{t,r},\mu_v^{t,r})
=
\psi_v^r(h_v^{t,r-1},\mu_v^{t,r-1},b_v^{t,r})
$$

B2 的新增语义不在于改变 recurrence，而在于把 edge role 和 mailbox lifetime 显式化。

关键约束是：

$$
W^{t,r}\text{ 只能在 token }t\text{ 的 round }r\text{ 或声明的后续 phase 中可见}
$$

如果 mailbox 被跨 token 复用，或在未声明的 phase 中可见，B2 就不再是原来的 $T_x$。

### B3：加入 phase schedule

B3 不再把一个 round 写成固定的：

```text
edge kernel -> aggregate -> node update
```

而是写成 phase 列表：

$$
\Pi=(p_1,\ldots,p_K)
$$

持久状态与 workspace 分别为：

$$
S=(h,\mu,\ldots)
$$

$$
W=(mailbox,artifact,\ldots)
$$

每个 phase：

$$
p_k=(R_k,K_k,C_k)
$$

执行：

$$
v_k=R_k(S^{k-1},W^{k-1})
$$

$$
\delta_k=K_k(v_k)
$$

$$
(S^k,W^k)=C_k(S^{k-1},W^{k-1},\delta_k)
$$

B3 的本质是把 barrier、visibility、commit order 从实现细节提升为模型语义。

只要 decode 和 prefill 使用同一个 $\Pi$，顺序 fold 等价仍成立。高性能 prefill 的风险则来自跨 phase 重排：

$$
K_a;K_b \not\equiv K_b;K_a
$$

除非能证明二者 read/write scope 不冲突，或者存在显式交换律。

### B4：加入 selector / controller state

B4 增加 controller state：

$$
q\in Q^C
$$

完整状态为：

$$
S=(h,\mu,q)
$$

selector phase 可写成：

$$
(a^{t,r},q^{t,r})
=
\sigma(c^{t,r},q^{t,r-1})
$$

其中：

- $c^{t,r}$ 是候选 activation 或候选 node 集合。
- $a^{t,r}$ 是被选择的 active set。
- $q$ 是 selector 历史状态，例如 select count、affect count、quota state。

B4 的关键点是：selector 不是纯粹的无状态过滤器，而是会改变未来 active path 的 controller。

因此 chunk prefill 不能把多个 token 的候选集合合并后一次性选择：

$$
\sigma(c^t,c^{t+1},q^{t-1})
$$

除非能证明它与顺序执行：

$$
(a^t,q^t)=\sigma(c^t,q^{t-1})
$$

$$
(a^{t+1},q^{t+1})=\sigma(c^{t+1},q^t)
$$

等价。

### B5：加入 token-local readout cache

B5 增加 token-local cache：

$$
W^{cache}_t=(z_t^1,\ldots,z_t^R)
$$

每个 internal round 可追加：

$$
z_t^r=\chi(S_t^r,W_t^r)
$$

finalize 读取：

$$
y_t=\rho(W^{cache}_t,S_t^R)
$$

关键约束是：

$$
W^{cache}_t \cap W^{cache}_{t+1}=\varnothing
$$

readout cache 不是持久状态，不能跨 token 泄漏。若需要跨 token 的读出记忆，应进入 B6。

### B6：加入 pronounce memory

B6 增加跨 token pronounce memory：

$$
\pi_t\in P
$$

状态为：

$$
S_t=(h_t,\mu_t,q_t,\pi_t)
$$

finalize 变成：

$$
(y_t,\pi_{t+1})
=
\rho(W^{cache}_t,S_t^R,\pi_t)
$$

这仍满足顺序 fold 等价，但会增加高性能 prefill 的难度。若 $\rho$ 对 $\pi$ 的更新不是可结合 scan，就必须按 token 顺序更新 pronounce memory。

### B7：加入 input/output roles 与 bridge

B7 增加 node role：

$$
\tau_V:V\to R_V
$$

并至少区分：

$$
V=V_{in}\cup V_{out}
$$

edge role 至少区分：

$$
E_{in},E_{out},E_{io},E_{oi}
$$

schedule 变成 LH-like：

$$
\Pi =
(
p_{oi},
p_{input},
p_{io},
p_{in\_update},
p_{out\_update},
p_{cache}
)
$$

其中必须显式规定：

- $p_{oi}$ 读 output-side 旧状态，写 input-side mailbox。
- $p_{input}$ 只在 token 的指定时刻写 input anchor。
- $p_{io}$ 读 input-side 旧状态，写 output-side mailbox。
- $p_{in\_update}$ 只更新 input-side state namespace。
- $p_{out\_update}$ 只更新 output-side state namespace。
- $p_{cache}$ 只读 output readout anchor，写 token-local readout cache。

这一步已经接近 LH，但它仍然是规范模型中的一个实例。它是否等价于 LH C++，还取决于 selector、hidden、KV cache、pronounce 与 tie-breaking 等 kernel 细节是否逐相位对齐。

### 引理：B-family 顺序 fold 等价

对任意 B0-B7 层，只要存在确定的单步转移：

$$
T_x:S\to Y\times S
$$

且 prefill 被定义为：

$$
\operatorname{Prefill}(x_{0:T},S_0)
=
\operatorname{fold}_{t=0}^{T-1}T_{x_t}(S_t)
$$

则：

$$
\operatorname{Prefill}(x_{0:T},S_0)
=
\operatorname{Decode}(x_{0:T},S_0)
$$

证明仍是对 token 长度归纳。

这个引理的价值是把问题从“所有机制是否天然支持 prefill”转化为：

- 新机制是否仍能定义清楚的 $T_x$？
- chunk kernel 是否模拟这个 $T_x$ 的 fold？
- 并行实现是否只改变表示与执行效率，而不改变 $T_x$？

## 数学化定义二：带 State / Workspace 的一般 StepTransition

这一节是前面“完整 StepTransition 模型”的压缩定理版本，用于后续证明。它不是另起一套模型；B0 是它的特例，B1-B7 则是在其中逐步增加 state、workspace 与 phase 约束。

### 定义 8：一般持久状态

设一般持久状态空间为：

$$
\mathcal{S}
$$

其中一个状态：

$$
S_t \in \mathcal{S}
$$

可包含：

$$
S_t =
(\text{activation},\text{memory},\text{controller},\text{pronounce memory},\ldots)
$$

B0 中：

$$
\mathcal{S}=H^V
$$

### 定义 9：Workspace

设 step-local workspace 空间为：

$$
\mathcal{W}
$$

一个 token step 内的 workspace：

$$
W_t \in \mathcal{W}
$$

可包含：

$$
W_t =
(\text{mailbox},\text{round messages},\text{readout cache},\ldots)
$$

workspace 不属于持久状态，除非某个 phase 显式 commit 到 $S$。

### 定义 10：Phase

设一个 phase 为：

$$
p = (\operatorname{read}_p,\operatorname{kernel}_p,\operatorname{commit}_p)
$$

其中：

$$
\operatorname{read}_p: \mathcal{S}\times\mathcal{W} \to \mathcal{V}_p
$$

读取当前 phase 可见的 view。

$$
\operatorname{kernel}_p: \mathcal{V}_p \to \Delta_p
$$

计算 phase delta。

$$
\operatorname{commit}_p: \mathcal{S}\times\mathcal{W}\times\Delta_p
\to
\mathcal{S}\times\mathcal{W}
$$

将 delta 写入持久 state 或 step-local workspace。

### 定义 11：Schedule

设一个 token step 内的 schedule 为有序 phase 列表：

$$
\Pi = (p_1,\ldots,p_K)
$$

如果存在 internal round，可写成：

$$
\Pi =
\left(
  \Pi^1,\ldots,\Pi^R
\right)
$$

其中每个：

$$
\Pi^r = (p_1^r,\ldots,p_{K_r}^r)
$$

### 定义 12：一般 StepTransition

给定输入 token：

$$
x_t \in X
$$

先初始化当前 token workspace：

$$
W_t^{init} = \operatorname{initWorkspace}(x_t,S_t)
$$

然后按 schedule 依次执行 phase。

令：

$$
(S_t^{0},W_t^{0})=(S_t,W_t^{init})
$$

对 $k=1,\ldots,K$：

$$
v_k = \operatorname{read}_{p_k}(S_t^{k-1},W_t^{k-1})
$$

$$
\delta_k = \operatorname{kernel}_{p_k}(v_k)
$$

$$
(S_t^{k},W_t^{k})
=
\operatorname{commit}_{p_k}(S_t^{k-1},W_t^{k-1},\delta_k)
$$

最后：

$$
(y_t,S_{t+1})
=
\operatorname{finalize}(S_t^{K},W_t^{K})
$$

定义：

$$
T_x(S_t) = (y_t,S_{t+1})
$$

### 定理 2：一般 StepTransition 的 prefill / decode fold 等价

若：

$$
\operatorname{Prefill}(x_{0:T},S_0)
$$

被定义为按 token 顺序应用同一个一般 StepTransition：

$$
(y_t,S_{t+1})=T_{x_t}(S_t)
$$

则：

$$
\operatorname{Prefill}(x_{0:T},S_0)
=
\operatorname{Decode}(x_{0:T},S_0)
$$

证明同定理 1，对 token 长度归纳。

## 数学化定义三：优化 kernel 的模拟关系

性能优化通常会改变内部表示，例如 reference layout 与 packed / crossbatch layout 不同。因此需要定义状态等价关系。

### 定义 13：状态等价

设 reference state 空间为 $\mathcal{S}$，optimized state 空间为 $\widehat{\mathcal{S}}$。

定义状态等价关系：

$$
S \sim \widehat{S}
$$

表示二者在语义上代表同一个运行时状态。

例如：

- per-sample KV list 与 batch KV cache 表示同一组 KV。
- `SignalVec` 与 packed active rows 表示同一组 activation。
- vector selector count 与 tensor selector count 表示同一组 controller state。

### 定义 14：step 模拟

设 reference step 为：

$$
T_x:\mathcal{S}\to Y\times\mathcal{S}
$$

optimized step 为：

$$
\widehat{T}_x:\widehat{\mathcal{S}}\to Y\times\widehat{\mathcal{S}}
$$

如果对任意 $x$、$S$、$\widehat{S}$，都有：

$$
S\sim\widehat{S}
\Rightarrow
\begin{cases}
T_x(S)=(y,S') \\
\widehat{T}_x(\widehat{S})=(\widehat{y},\widehat{S}') \\
y=\widehat{y} \\
S'\sim\widehat{S}'
\end{cases}
$$

则称 $\widehat{T}_x$ 模拟 $T_x$。

在纯数学定义中使用精确等号。工程实现中，如果涉及浮点重排、packed / crossbatch fusion 或 backend lowering，可将 $y=\widehat{y}$ 替换为预先声明的数值容差关系，例如 `allclose`，但状态语义仍应通过明确的 $S'\sim\widehat{S}'$ 给出。

### 定理 3：step 模拟推出序列级等价

若初始状态：

$$
S_0 \sim \widehat{S}_0
$$

且对所有 token $x_t$，$\widehat{T}_{x_t}$ 模拟 $T_{x_t}$，则对任意序列 $x_{0:T}$：

$$
y_{0:T}=\widehat{y}_{0:T}
$$

且：

$$
S_T \sim \widehat{S}_T
$$

证明：

对 token 位置 $t$ 归纳。

当 $t=0$ 时，由前提 $S_0\sim\widehat{S}_0$。第一个 step 由模拟定义得到 $y_0=\widehat{y}_0$ 且 $S_1\sim\widehat{S}_1$。

假设 $t$ 前状态等价，即 $S_t\sim\widehat{S}_t$。由 step 模拟定义可得：

$$
y_t=\widehat{y}_t,\quad S_{t+1}\sim\widehat{S}_{t+1}
$$

因此对所有 token 成立。

证毕。

### 推论：kernel 等价的证明路线

若每个 phase 的 optimized kernel 都保持：

$$
\operatorname{read\ scope}
$$

$$
\operatorname{write\ scope}
$$

$$
\operatorname{commit\ timing}
$$

且每个 optimized phase 在状态等价关系下模拟 reference phase，则 optimized StepTransition 模拟 reference StepTransition。由定理 3，optimized sequence 与 reference sequence 等价。

这就是后续 packed / crossbatch / 并行实现的证明入口。

## 为什么完整涵盖 LH 可能很难

完整涵盖 LH 并自动得到严格 `prefill / decode` 等价性，大概率需要对 `Graph` 与 `Schedule` 施加强约束。

原因是 LH 具有许多会影响等价性的状态机制：

- selector 的历史依赖。
- hidden / KV cache 的 append 顺序。
- internal tick 内的 read / write 可见性。
- readout cache 只在当前 token 内跨 internal tick 累积。
- pronounce memory 跨 token 持久存在。
- external input 只在 tick 0 可见。

如果这些机制没有被显式约束，`prefill` 很容易在实现中无意改变语义，例如：

- token `t` 读到 token `t+1` 的 state。
- chunk 内 selector 基于未来 token 做联合决策。
- KV cache 一次性 append 整段 chunk，导致早期 token 看到未来 token。
- readout cache 或 workspace 生命周期被拉长到跨 token。

因此，`StepTransition` 抽象不是为了证明任意 graph 都天然等价，而是为了找出哪些约束会保持或破坏等价性。

## 两条研究分支

### 分支 A：涵盖 LH

目标：

```text
Typed Graph + StateStore + Workspace + PhaseSchedule + KernelRegistry
```

这条路线保留 LH 的 phase、selector、readout、pronounce 和 memory 语义。

优势：

- 可复刻 LH。
- 可对齐 native LH。
- 可用现有工程作为 golden reference。

代价：

- 抽象较复杂。
- 需要显式 state scope、selector scope、workspace lifetime。
- 证明不可能只靠普通 graph，需要依赖 phase schedule 与 state contract。

### 分支 B：不强行涵盖 LH

目标：

```text
for round:
  messages = EdgeKernel(Graph, State)
  State.nodes = NodeUpdate(messages, State.nodes)
logits = Readout(State)
```

这条路线选择更简单的通用 graph recurrent runtime。

优势：

- 更容易解释。
- 更容易定义严格 `prefill = decode fold`。
- 更可能成为后续可训练性实验的最小核心。

代价：

- 不一定能完整复刻 LH。
- 可能丢掉 LH 中某些为局部通信、超稀疏、selector 历史设计的机制。
- 需要重新验证其表达力、训练稳定性与性能价值。

## 从分支 B 逐层逼近 LH

后续推进可以从分支 B 出发，逐步引入 LH 中的要素。这样做的目的不是预设 LH 一定正确，而是让每个新增机制都被单独审视：它到底新增了什么状态、什么临时工作区、什么调度约束，以及它对 `prefill = decode fold` 和高性能并行 prefill 有何影响。

### B0：activation-only graph recurrent step

最小模型：

```text
State:
  activation[node]

Workspace:
  messages

Step(input_token, State):
  State.activation[input_node] = Embed(input_token)

  for round in 0..R-1:
    Workspace.messages = EdgeKernel(Graph, State.activation)
    next_activation = NodeKernel(Graph, State.activation, Workspace.messages)
    State.activation = next_activation

  logits = Readout(State.activation[output_node])
  return logits, State
```

如果 `Prefill` 定义为逐 token 调用 `Step`，则 `prefill = decode fold` 由定义成立。

这一层的价值是给出最干净的正确性基准，但它尚未提供真正 sequence-parallel prefill；高性能 prefill 仍需证明 `forward_chunk == Step fold`。

### B1：加入 node memory

新增：

```text
State:
  activation[node]
  memory[node]
```

`NodeKernel` 变成：

```text
NodeKernel(messages, activation, memory_before)
  -> activation_delta, memory_after
```

只要 memory 按 token 顺序更新，`prefill = decode fold` 仍然直接成立。

风险是高性能 chunk prefill：如果一次性处理多个 token，必须保证 token `t` 的 node update 不能读到 token `t+1` 写入的 memory。

### B2：加入 typed edge 与 mailbox

新增：

```text
Graph:
  typed edge roles

Workspace:
  mailbox[node]
```

edge kernel 从“直接生成 messages”变成：

```text
EdgeKernel(source_activation, edge_role)
  -> mailbox[target_node]
```

这一层仍然容易保持 `prefill = decode fold`，前提是 mailbox 是当前 step / 当前 round 的临时对象，不能跨 token 持久存在。

### B3：加入 internal rounds 和 phase schedule

新增：

```text
Schedule:
  ordered phases
  read_scope
  write_scope
  commit timing
```

这是从普通 graph recurrent step 走向 LH-like runtime 的关键一步。

`Step` 不再只是：

```text
messages -> node_update
```

而是：

```text
for internal_round:
  for phase in Schedule:
    view = read(State, Workspace, phase.read_scope)
    delta = Kernel(view)
    commit(delta, phase.write_scope)
```

只要 phase schedule 在 prefill 和 decode 中完全一致，`prefill = decode fold` 仍可由 step 等价推出。

高性能并行 prefill 的风险在于跨 phase 或跨 token 重排。允许的优化应主要发生在同一 phase 内，而不是改变 phase barrier。

### B4：加入 selector / controller state

新增：

```text
State:
  controller[scope]
```

selector 不应被藏进普通 node kernel 的内部细节，因为它有历史依赖，并会影响后续 active path。

等价性要求：

```text
SelectorKernel(candidates, controller_before)
  -> selected, controller_after
```

prefill 与 decode 的 selector 更新顺序必须一致。chunk prefill 如果想并行处理多个 token，不能让早期 token 的 selector 决策依赖未来 token 的 candidates 或 controller state。

### B5：加入 readout cache

新增：

```text
Workspace:
  readout_cache
```

readout cache 是当前 token 内跨 internal rounds 累积的临时对象。

这一点非常关键：

- 它不是跨 token 的持久 `State`。
- 它也不是每个 phase 都可见的普通 message。
- 它在 token step 结束后被 pronounce 使用，然后应结束生命周期。

如果 readout cache 被错误地跨 token 保留，`prefill = decode fold` 会被破坏。

### B6：加入 pronounce memory

新增：

```text
State:
  pronounce_memory
```

pronounce kernel 变成：

```text
Pronounce(readout_cache, pronounce_memory_before)
  -> logits, pronounce_memory_after
```

它是跨 token 持久状态，因此必须按 token 顺序更新。

这会让高性能 prefill 更难，因为即使 node graph 的一部分可并行，最终 pronounce memory 仍然是 step recurrence 的一部分，除非额外证明它可以 associative scan 或其他等价并行化。

### B7：加入 LH-like input/output roles and bridges

新增：

```text
Graph:
  input-role nodes
  output-role nodes
  io bridge edges
  oi bridge edges

State:
  activation[node_id]
  memory[node_id]
  controller[selector_scope]
```

这一步可以用统一大 graph 表达 input/output 两套 cortex，但仍需要 role、scope 和 phase schedule。

它不能把 LH 简化成普通无类型 graph traversal，因为：

- `ExternalInput` 只写 input anchor。
- `OiBridge` 与 `IoBridge` 有方向和可见性规则。
- `InputUpdate` 与 `OutputUpdate` 写不同 role 的 node state。
- `Readout` 只读 output readout anchor。
- selector scope 仍然需要区分。

到这一层，已经接近 LH 的 StepTransition 形态。

## 每一层必须回答的问题

逐层推进时，每一层都应回答同一组问题：

1. `State` 新增了什么？
2. `Workspace` 新增了什么？
3. `Schedule` 新增了什么？
4. `Kernel` 的输入输出变成什么？
5. `prefill = decode fold` 是否仍然由 step 定义成立？
6. 如果做高性能并行 prefill，能否实现 `forward_chunk == Step fold`？
7. 为了实现高性能并行 prefill，需要什么 mask、ordering、state materialization、checkpoint 或 scan 结构？
8. 哪些优化只能在同一 phase 内做，哪些优化会跨 phase 或跨 token 改变语义？
9. 新增机制是否是局部通信目标下的必要机制，还是 LH 的实现选择？

这组问题本身就是后续文档推进模板。

## 逐层判断

| 层级 | 新增机制 | `prefill = decode fold` | 高性能并行 prefill 风险 |
| --- | --- | --- | --- |
| B0 | activation-only graph step | 由定义成立 | 需要证明 chunk 等价于逐 step。 |
| B1 | node memory | 仍成立 | 不能让 token `t` 读未来 memory。 |
| B2 | typed edge / mailbox | 仍成立 | mailbox 必须 step-local / round-local。 |
| B3 | internal rounds / phase schedule | 仍成立 | 不可跨 phase 改 barrier / visibility。 |
| B4 | selector / controller state | 仍成立但更脆弱 | selector 不能基于未来 token 联合决策。 |
| B5 | readout cache | 仍成立 | readout cache 必须 token-local。 |
| B6 | pronounce memory | 仍成立但有 recurrence | 可能需要 scan / checkpoint / sequential update。 |
| B7 | LH-like input/output roles and bridges | 可成立 | 必须保留 role、scope、phase read-write contract。 |

当前判断：最小分支 B 满足 `prefill = decode fold`，但不自动支持高性能并行 prefill。它的价值是提供一个干净、可理解的正确性基准。真正的研究价值在于逐层引入 LH 机制时，找出哪些机制仍容易保持等价，哪些机制让高性能 prefill 变难。

## 当前建议

建议先走中间路线：

1. 用 `StepTransition` 作为规范层。
2. 让规范层先能解释 LH，但不把 LH 细节变成唯一正确答案。
3. 在工程上继续保留 LH 对齐路径，作为复杂 reference family。
4. 在理论和实验上另行探索更简单的 strict family。
5. 以 `prefill / decode` 等价性为裁决标准，反过来约束 graph、state、schedule、kernel 的设计。

第一步可以不是完整证明，而是建立最小可检查对象：

```text
StepTransition Spec
StateStore Spec
Workspace Lifetime Spec
Phase Read/Write Scope Spec
Kernel Equivalence Spec
Prefill = Decode Fold Test
```

只有这些对象被明确下来，后续讨论“是否支持 prefill”、“是否可 sequence-parallel”、“是否可 packed / crossbatch fusion”才不会被 LH 的具体实现细节淹没。

## 开放问题

- 哪些 graph 约束足以保证 `prefill = decode fold`？
- selector 是否必须被视为 controller state，而不是 node kernel 内部细节？
- workspace 是否必须严格 token-local？
- internal tick 是否是必要概念，还是 LH-specific 复杂度？
- readout cache 与 pronounce memory 是否应进入通用模型？
- `forward_chunk` 能否在不破坏 step semantics 的情况下提供真正 sequence-parallel prefill？
- 哪些 LH 机制是局部通信目标下必要的，哪些只是当前实现选择？
