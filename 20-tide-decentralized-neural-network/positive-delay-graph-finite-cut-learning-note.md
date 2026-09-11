---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-11
tags:
  - tide
  - positive-delay-graph
  - directed-cycle
  - finite-cut
  - continuation
  - selector-history
  - scc
  - mathematics
  - learning-note
---

# 正时延有向图的有限切面语义：从 TimedDAG 到有环 Graph

> [!summary] 本文的阅读前提
> 本文只以 [[timed-dag-region-selector-learning-note|《带区域选择的 TimedDAG：从零开始的数学定义》]] 为前置，不以前置 chunk-prefill 教材、旧的 TIDE 长文或任何 runtime 实现。读者应当已经知道时间纤维、节点状态、region selector、selector-history 和正整数边时延的定义；本文会把发生变化的对象与全部主递归重新写出。
>
> 第 10 节会在本文内重新定义所需的外层性能概念；[[timed-dag-chunk-prefill-learning-note|TimedDAG chunk-prefill 教材]] 只提供更完整的 DAG 正例，不是本文的阅读前提。
>
> 本文允许固定节点图含有向环，但仍要求每条边具有严格正时延。核心对象不再是“一次最终结束的完整计算”，而是每个有限逻辑时间切面以下的唯一记录。

> [!tip] 建议分三次阅读
> 第一次读第 1--4 节，目标是理解为什么一个全局永不结束的自环仍在每个有限切面上存在唯一有限结果。第二次读第 5--8 节，手算 seal、在途消息和两段继续。第三次才读第 9--10 节的 SCC 与外层 lowering；SCC 不是理解 finite-cut 语义的前置。

本文只做一项结构推广：固定消息图不再要求无环。这里的 **Tide** 是研究线名称，不是另一个尚未定义的数学对象。本文保留以下约束：

1. 节点、边、端口和 region 的集合有限；
2. 每条消息边的时延属于 $\mathbb N_{>0}$；
3. 每个节点在同一逻辑时间至多处理一个完整时间纤维；
4. 一次完整输出作用在每条出边、每个输出端口上至多产生一个值；
5. 节点状态由节点唯一持有，selector-history 由 region 唯一持有；
6. 所有局部函数和 selector 都是确定的全函数。

这组约束足以证明：即使一条消息可以沿环永久传播，每个有限切面以前仍只有有限多个函数作用，并且它们的值唯一。

## 1. 从 TimedDAG 保留什么，改变什么

### 1.1 基础记号

沿用：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
\mathbb N_{>0}=\{1,2,3,\ldots\},
\qquad
[r,s)=\{\theta\in\mathbb N\mid r\le\theta<s\},
$$

以及有限子集集合 $\mathcal P_{\mathrm{fin}}(X)$。固定非空承载值集合 $P$，另取 $\bot\notin P$，并令 $P_\bot=P\cup\{\bot\}$。

对 $L\in\mathbb N$，本文写：

$$
[L]=\{0,1,\ldots,L-1\};
$$

特别地，$[0]=\varnothing$。

本文把 cut 译为**逻辑时间切面**。切面 $b\in\mathbb N$ 把逻辑时间分成 $[0,b)$ 与 $[b,\infty)$。它不是图论中把顶点分成两组的 edge cut，也不是墙钟截止时刻。

### 1.2 允许有环的正时延消息图

给定：

$$
G=(V,A,\operatorname{src},\operatorname{dst},\delta),
\qquad
\delta:A\to\mathbb N_{>0}.
\tag{1}
$$

其中 $V$ 是有限非空节点集合，$A$ 是有限边标识符集合，$\operatorname{src},\operatorname{dst}:A\to V$ 分别给出边的起点与终点。不同边可以有相同起点和终点；边标识符仍然不同。

式 (1) 单独称为**正时延消息图**。本文所说的一个完整 **PositiveDelayGraph 规格**，则由式 (1) 连同第 1.3--1.5 节的端口、输入时间、region、状态空间和全部函数共同组成。因而“消息图有环”只陈述 $G$ 的性质，不会抹去 selector 或状态带来的依赖。

与 TimedDAG 唯一的图结构差别是：本文不要求 $G$ 无环。例如，允许：

```text
v ──a──> v
```

也允许：

```text
u ──a──> v ──c──> u
```

但若一条消息在逻辑时间 $\eta$ 沿边 $a$ 产生，它只能在：

$$
\eta+\delta(a)>\eta
$$

到达。因此，空间上返回旧节点不表示逻辑时间返回过去。

若消息图 $G$ 无环、第 1.3 节的输出端口集合 $\mathsf O\ne\varnothing$，并且每个输入位置集合都是非空有限初始区间，则恰好得到前置教材中的 TimedDAG 特例；允许空输入端口或 $\mathsf O=\varnothing$ 只是无关紧要的边界扩展。本文主要放宽的是消息图无环与输入总长度有限这两项限制。

对 $v\in V$ 定义 $\operatorname{In}(v)$ 与 $\operatorname{Out}(v)$，含义仍分别是以 $v$ 为终点和起点的边集合。

### 1.3 端口、region 与局部有限输入历史

给定有限非空输入端口集合 $\mathsf I$、有限输出端口集合 $\mathsf O$，以及：

$$
\gamma:\mathsf I\to V,
\qquad
\varepsilon:\mathsf O\to V.
$$

再给定有限非空 region 标识符集合 $J$ 和满射 $\rho:V\to J$。令：

$$
\mathcal R_j=\{v\in V\mid\rho(v)=j\}.
$$

每个节点恰属一个 $\mathcal R_j$。region 不是普通消息节点；它不增加一条未声明来源的输入边。

为了同时覆盖有限输入与可以继续增长的输入流，对每个 $i\in\mathsf I$ 选择一个位置集合 $K_i$：它或者等于某个有限初始区间 $[L_i]$（其中 $L_i\in\mathbb N$），或者等于 $\mathbb N$。再给定：

$$
x_i:K_i\to P,
\qquad
\iota_i:K_i\to\mathbb N,
\qquad
k<k'\Longrightarrow\iota_i(k)<\iota_i(k').
\tag{2}
$$

定义可能的外部输入记录集合与本次实际输入历史：

$$
\begin{aligned}
\mathsf{Ext}
&=\{(\mathrm{ext},i,k,y)\mid
i\in\mathsf I,\ k\in K_i,\ y\in P\},\\
E_x
&=\{(\mathrm{ext},i,k,x_i(k))\mid
i\in\mathsf I,\ k\in K_i\}.
\end{aligned}
\tag{3}
$$

若 $e=(\mathrm{ext},i,k,y)$，定义：

$$
\operatorname{target}(e)=\gamma(i),
\quad
\operatorname{time}(e)=\iota_i(k),
\quad
\operatorname{value}(e)=y.
$$

式 (2) 保证每个端口在任意有界时间区间内只有有限条输入记录。它不要求整个 $E_x$ 有限。

### 1.4 内部消息、输出和局部函数

定义内部消息：

$$
\begin{aligned}
\mathsf{Msg}
&=\{(\mathrm{msg},\eta,a,y)\mid
\eta\in\mathbb N,\ a\in A,\ y\in P\},\\
\operatorname{send}(\mathrm{msg},\eta,a,y)&=\eta,\\
\operatorname{edge}(\mathrm{msg},\eta,a,y)&=a,\\
\operatorname{target}(\mathrm{msg},\eta,a,y)&=\operatorname{dst}(a),\\
\operatorname{time}(\mathrm{msg},\eta,a,y)&=\eta+\delta(a).
\end{aligned}
\tag{4}
$$

外部输出记录仍写成 $(\mathrm{out},\theta,o,y)$；它的输出时间、端口和值分别是 $\theta,o,y$。

令 $\mathsf{Atom}=\mathsf{Ext}\cup\mathsf{Msg}$，并令 $\mathsf{Atom}_v$ 是目标为 $v$ 的原子集合。对每个 $v\in V$，定义：

$$
\operatorname{OutPort}(v)
=\{o\in\mathsf O\mid\varepsilon(o)=v\}.
$$

再给定非空集合 $S_v,X_v,D_v$、初态 $q_v^{\mathrm{init}}\in S_v$，以及全函数：

$$
\begin{aligned}
\operatorname{Agg}_v&:
\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)
\to X_v,\\
\operatorname{Upd}_v&:
S_v\times\mathbb N\times X_v\to S_v,\\
\operatorname{Read}_v^0&:
\mathbb N\times X_v\to D_v,\\
\operatorname{Read}_v^-&:
S_v\times\mathbb N\times X_v\to D_v,\\
\operatorname{Read}_v^+&:
S_v\times\mathbb N\times X_v\to D_v,\\
\operatorname{Full}_v&:
S_v\times\mathbb N\times X_v
\to(P_\bot)^{\operatorname{Out}(v)}
\times(P_\bot)^{\operatorname{OutPort}(v)}.
\end{aligned}
\tag{5}
$$

$\operatorname{Agg}_v$ 虽然在所有有限子集上有定义，正文只在非空、同一时间的纤维上调用它。

### 1.5 selector-history 与状态采用

对每个 $j\in J$，给定：

- 非空历史状态集合 $Y_j$ 与初态 $y_j^{\mathrm{init}}$；
- 容量 $1\le K_j\le|\mathcal R_j|$；
- 描述量模式 $\tau_j\in\{0,-,+\}$；
- 状态采用模式 $\kappa_j\in\{0,1\}$。

对每个 $C\subseteq\mathcal R_j$，给定确定的全函数：

$$
\operatorname{SelStep}_{j,C}:
Y_j\times\mathbb N\times\prod_{v\in C}D_v
\to
\{A'\subseteq C\mid|A'|\le K_j\}
\times Y_j,
\tag{6}
$$

并规定 $\operatorname{SelStep}_{j,\varnothing}(y,\theta,())=(\varnothing,y)$。

若 $C$ 是候选集合、$A\subseteq C$ 是 active set，定义状态采用集合：

$$
O_j(C,A)
=
\begin{cases}
A,&\kappa_j=0,\\
C,&\kappa_j=1.
\end{cases}
\tag{7}
$$

同一时间的依赖次序仍是：

$$
(q,B)\longrightarrow(h,\widetilde q,d)
\longrightarrow(A,y')
\longrightarrow q'
\longrightarrow\operatorname{Full}.
\tag{8}
$$

节点状态 $q_v$ 只属于节点 $v$，历史 $y_j$ 只属于 selector $j$。多个局部函数可以使用同一个固定参数对象；固定参数不是一次前向运行中被前序事件改写的状态，所以这种共享不会给式 (8) 增加运行时依赖边。若允许两个节点共同读写可变状态，则必须另外定义它的唯一 owner 与读写次序；本文没有暗中允许这种情形。

## 2. 有限切面以前的直接递归

### 2.1 输入前缀是有限的

对 $b\in\mathbb N$ 定义：

$$
E_{x,<b}=\{e\in E_x\mid\operatorname{time}(e)<b\}.
$$

由于同一端口的输入时间严格递增：

$$
|E_{x,<b}|\le b|\mathsf I|<\infty.
\tag{9}
$$

不同端口可以在同一时间各提供一条记录，所以式 (9) 中保留 $|\mathsf I|$。

### 2.2 逐逻辑时间递归

固定 cut $b\in\mathbb N$。令：

$$
q_v^0=q_v^{\mathrm{init}},
\qquad
y_j^0=y_j^{\mathrm{init}},
\qquad
M_{<0}^{\mathrm{send}}=\varnothing.
$$

依次对 $\theta\in[0,b)$ 定义以下对象。假定所有发送时间小于 $\theta$ 的消息已经定义，令：

$$
B_{v,\theta}
=
\{z\in E_x\cup M_{<\theta}^{\mathrm{send}}
\mid
\operatorname{target}(z)=v,
\ \operatorname{time}(z)=\theta\}.
\tag{10}
$$

对每个 $j\in J$，定义候选集合；并对其中每个节点定义本地内容与候选新状态：

$$
\begin{aligned}
\mathcal C_{j,\theta}
&=\{v\in\mathcal R_j\mid B_{v,\theta}\ne\varnothing\},\\
h_{v,\theta}
&=\operatorname{Agg}_v(\theta,B_{v,\theta}),\\
\widetilde q_{v,\theta}
&=\operatorname{Upd}_v(q_v^\theta,\theta,h_{v,\theta})
\qquad(v\in\mathcal C_{j,\theta}).
\end{aligned}
\tag{11}
$$

按 region 的模式定义描述量：

$$
d_{v,\theta}
=
\begin{cases}
\operatorname{Read}_v^0(\theta,h_{v,\theta}),&\tau_j=0,\\
\operatorname{Read}_v^-(q_v^\theta,\theta,h_{v,\theta}),&\tau_j=-,\\
\operatorname{Read}_v^+(\widetilde q_{v,\theta},\theta,h_{v,\theta}),&\tau_j=+.
\end{cases}
\tag{12}
$$

每个 region 在时间 $\theta$ 应用一次式 (6)：

$$
(\mathcal A_{j,\theta},y_j^{\theta+1})
=
\operatorname{SelStep}_{j,\mathcal C_{j,\theta}}
\left(
y_j^\theta,
\theta,
(d_{v,\theta})_{v\in\mathcal C_{j,\theta}}
\right).
\tag{13}
$$

然后对 $v\in\mathcal R_j$ 定义：

$$
q_v^{\theta+1}
=
\begin{cases}
\widetilde q_{v,\theta},
&v\in O_j(\mathcal C_{j,\theta},\mathcal A_{j,\theta}),\\
q_v^\theta,&\text{其余情形}.
\end{cases}
\tag{14}
$$

只有 $v\in\mathcal A_{j,\theta}$ 时，才定义：

$$
(f^A_{v,\theta},f^O_{v,\theta})
=
\operatorname{Full}_v(q_v^{\theta+1},\theta,h_{v,\theta}).
\tag{15}
$$

令该时间新产生的消息与外部输出为：

$$
\begin{aligned}
M_\theta
=\{&(\mathrm{msg},\theta,a,z)\mid
v\in\mathcal A_{\rho(v),\theta},\
a\in\operatorname{Out}(v),\
f^A_{v,\theta}(a)=z\in P\},\\
Z_\theta
=\{&(\mathrm{out},\theta,o,z)\mid
v\in\mathcal A_{\rho(v),\theta},\
o\in\operatorname{OutPort}(v),\
f^O_{v,\theta}(o)=z\in P\},\\
M_{<\theta+1}^{\mathrm{send}}
&=M_{<\theta}^{\mathrm{send}}\cup M_\theta.
\end{aligned}
\tag{16}
$$

由严格正时延立即得到：

$$
m\in M_\theta
\Longrightarrow
\operatorname{time}(m)
=\theta+\delta(\operatorname{edge}(m))>\theta.
\tag{17}
$$

所以 $M_\theta$ 不会反过来改变式 (10) 中已经取出的时间 $\theta$ 纤维。这个事实不使用空间图无环。

### 2.3 cut trace 包含什么

定义：

$$
M_{<b}^{\mathrm{send}}=\bigcup_{\theta<b}M_\theta,
\qquad
Z_{<b}=\bigcup_{\theta<b}Z_\theta.
\tag{18}
$$

注意 $M_{<b}^{\mathrm{send}}$ 按**发送时间**截断。某条消息即使到达时间不小于 $b$，只要由 $\theta<b$ 的事件产生，也已经属于这个集合。

定义 cut $b$ 以下的完整记录：

$$
\begin{aligned}
\mathcal T_{x,<b}
=\bigl(&
(B_{v,\theta})_{v\in V,\,\theta<b},
(\mathcal C_{j,\theta},\mathcal A_{j,\theta})_{j\in J,\,\theta<b},\\
&(h_{v,\theta},\widetilde q_{v,\theta},d_{v,\theta})_
{\theta<b,\,v\in\mathcal C_{\rho(v),\theta}},\\
&(q_v^\theta)_{v\in V,\,0\le\theta\le b},
(y_j^\theta)_{j\in J,\,0\le\theta\le b},\\
&(f^A_{v,\theta},f^O_{v,\theta})_
{\theta<b,\,v\in\mathcal A_{\rho(v),\theta}},
M_{<b}^{\mathrm{send}},Z_{<b}
\bigr).
\end{aligned}
\tag{19}
$$

这一定义没有要求 $\mathcal T_{x,<b}$ 以后最终出现一个“最后事件”。

定义 cut 内的节点事件集合与选择事件集合：

$$
\mathcal E^{\mathrm{node}}_{x,<b}
=\{(v,\theta)\in V\times[0,b)\mid B_{v,\theta}\ne\varnothing\},
$$

$$
\mathcal E^{\mathrm{sel}}_{x,<b}
=\{(j,\theta)\in J\times[0,b)\mid
\mathcal C_{j,\theta}\ne\varnothing\}.
$$

### 2.4 有限 cut 的主定理

> [!theorem] 定理 1：每个有限 cut 的记录存在、有限且唯一
> 固定第 1 节的全部集合、函数、参数和式 (2) 的输入历史。对每个 $b\in\mathbb N$，式 (10)--(19) 唯一确定一个有限记录 $\mathcal T_{x,<b}$。此外：
>
> $$
> \begin{aligned}
> |E_{x,<b}|&\le b|\mathsf I|,\\
> |\mathcal E^{\mathrm{node}}_{x,<b}|&\le b|V|,\\
> |\mathcal E^{\mathrm{sel}}_{x,<b}|&\le b|J|,\\
> |M_{<b}^{\mathrm{send}}|&\le b|A|,\\
> |Z_{<b}|&\le b|\mathsf O|.
> \end{aligned}
> \tag{20}
> $$

**证明。** 对 $\theta\in[0,b)$ 归纳。

在 $\theta=0$，没有发送时间更小的内部消息。式 (10) 的每个纤维由时间为 $0$ 的外部输入唯一确定，而且由式 (9) 为有限集合。式 (5)--(7) 中全函数按式 (11)--(16) 的顺序给出唯一结果。

假设所有发送时间小于 $\theta$ 的消息、状态与历史都已唯一确定。式 (17) 表明时间 $\theta$ 的纤维只可能包含外部输入和更早时间产生的消息；这些对象已经确定。随后每一步仍是有限集合上的全函数求值，所以时间 $\theta$ 的全部坐标唯一。

固定 $v,\theta$ 至多有一个节点事件，固定 $j,\theta$ 至多有一个选择事件。固定 $\theta$ 的 active 节点在每条出边上至多产生一条消息；因为每条边只有一个源节点，所以固定 $(a,\theta)$ 至多对应一条消息。输出端口同理。结合式 (9)，便得到式 (20)，从而整个记录有限。$\square$

定理 1 中的“有限”首先表示有限集合与有限次抽象函数作用。若要进一步断言某台机器能在有限墙钟时间内算完，还必须假设式 (5)--(6) 的每个全函数都有一个会终止的实现。集合论中的全函数不会自动附送算法与复杂度界。

### 2.5 不同 cut 彼此相容

若 $0\le c<b$，令 $\operatorname{Res}_c(\mathcal T_{x,<b})$ 表示：保留所有逻辑时间小于 $c$ 的函数作用坐标、发送时间小于 $c$ 的消息、输出时间小于 $c$ 的输出，以及状态和历史的 $0,\ldots,c$ 坐标。

> [!corollary] 推论 2：cut 限制相容
> 对任意 $0\le c<b$：
> $$
> \operatorname{Res}_c(\mathcal T_{x,<b})
> =\mathcal T_{x,<c}.
> \tag{21}
> $$

**证明。** 两边在时间 $0$ 使用相同输入与初态；若在所有更小时间相同，则式 (10)--(16) 的自变量逐项相同。因此对 $\theta<c$ 归纳即可。$\square$

所以一次可能无限延续的计算可以严格定义为相容族：

$$
(\mathcal T_{x,<b})_{b\in\mathbb N}.
$$

这里每个成员都有限；整个族不必在某个有限 $b$ 后保持不变。

> [!theorem] 定理 3：输入前缀不变性（input-prefix invariance）
> 若两份输入历史 $x,x'$ 满足 $E_{x,<b}=E_{x',<b}$，而固定图、局部函数、初始节点状态与初始 selector-history 相同，则：
> $$
> \mathcal T_{x,<b}=\mathcal T_{x',<b}.
> $$

**证明。** 再次对 $\theta<b$ 归纳。未来时间不小于 $b$ 的外部记录从未进入式 (10) 的当前纤维；由更早时间产生的内部消息又由归纳假设相同。$\square$

这个定理只比较两个完整数学输入历史：若它们在切面左侧相同，未来输入就不能改变左侧记录。在线求值者怎样知道自己已经取得完整前缀，要到第 5 节用 source seal 回答；该知识不是定理 3 的前提中暗含的能力。

## 3. 三个最小例子

### 3.1 延迟为 1 的单节点自环

取 $V=\{v\}$、$A=\{a\}$，并令：

$$
\operatorname{src}(a)=\operatorname{dst}(a)=v,
\qquad
\delta(a)=1.
$$

令 $v$ 在时间 $0$ 收到唯一外部值 $p$。取单点节点状态、单点 selector-history、总是选择唯一候选的 selector，并令 $\operatorname{Full}_v$ 把收到的值原样沿 $a$ 发回。于是对每个 $\theta\in\mathbb N$ 都产生：

$$
m_\theta=(\mathrm{msg},\theta,a,p),
\qquad
\operatorname{time}(m_\theta)=\theta+1.
\tag{22}
$$

这次计算永不全局静止。但对 cut $b$，只有 $\theta\in[0,b)$ 的 $b$ 个节点事件和 $b$ 条已发送消息属于 $\mathcal T_{x,<b}$。因此：

$$
\text{全局不终止}
\not\Rightarrow
\text{某个有限 cut 不存在或无限}.
$$

这里的关键不是环“足够简单”，而是每绕一圈逻辑时间至少增加 $1$。

### 3.2 两节点正时延环

取两条边：

$$
u\xrightarrow[\delta=1]{a}v,
\qquad
v\xrightarrow[\delta=2]{c}u.
$$

若 $u$ 在时间 $0$ 收到一个值，两个节点都在收到值时原样转发，那么节点事件的时间依次是：

$$
(u,0),(v,1),(u,3),(v,4),(u,6),\ldots
$$

空间路径返回 $u$，逻辑时间却从 $0$ 增加到 $3$。没有任何事件依赖回到旧的 $(u,0)$。

### 3.3 为什么跨 cut 消息不能丢

把第 3.1 节改成 $\delta(a)=2$。在 cut $b=1$ 时，时间 $0$ 的节点事件已经产生消息 $m_0$，但：

$$
\operatorname{send}(m_0)=0<1<2=\operatorname{time}(m_0).
$$

若在 cut $1$ 停止时只保存节点状态，而丢掉 $m_0$，恢复后的时间 $2$ 纤维为空；一次算完时该纤维非空。第 6.2 节会把这类消息定义为 $W_b$。

## 4. finite-cut 函数作用事件图

### 4.1 四类事件

固定 $b$ 与 $\mathcal T_{x,<b}$，并取四个两两不同的标签
$\mathrm{prep},\mathrm{select},\mathrm{adopt},\mathrm{full}$。若
$B_{v,\theta}\ne\varnothing$，定义本地准备与状态采用事件：

$$
P_{v,\theta}=(\mathrm{prep},v,\theta),
\qquad
U_{v,\theta}=(\mathrm{adopt},v,\theta).
$$

若 $\mathcal C_{j,\theta}\ne\varnothing$，定义选择事件：

$$
S_{j,\theta}=(\mathrm{select},j,\theta).
$$

若 $v\in\mathcal A_{j,\theta}$，定义完整输出事件：

$$
F_{v,\theta}=(\mathrm{full},v,\theta).
$$

其中都要求 $\theta<b$。相应的四个事件集合是：

$$
\begin{aligned}
\mathscr V^P_{x,<b}
&=\{P_{v,\theta}\mid(v,\theta)\in\mathcal E^{\mathrm{node}}_{x,<b}\},\\
\mathscr V^U_{x,<b}
&=\{U_{v,\theta}\mid(v,\theta)\in\mathcal E^{\mathrm{node}}_{x,<b}\},\\
\mathscr V^S_{x,<b}
&=\{S_{j,\theta}\mid(j,\theta)\in\mathcal E^{\mathrm{sel}}_{x,<b}\},\\
\mathscr V^F_{x,<b}
&=\{F_{v,\theta}\mid
\theta<b, v\in\mathcal A_{\rho(v),\theta}\}.
\end{aligned}
$$

四类有序组的首坐标不同，因而这些集合两两不交。写 $\sqcup$ 表示不交并，并定义：

$$
\mathscr V^{\mathrm{ev}}_{x,<b}
=\mathscr V^P_{x,<b}\sqcup\mathscr V^S_{x,<b}
\sqcup\mathscr V^U_{x,<b}\sqcup\mathscr V^F_{x,<b}.
$$

### 4.2 直接依赖边

本节的事件图采用**边关系**表示：边集是下列笛卡尔积的一个子集：

$$
\mathscr V^{\mathrm{ev}}_{x,<b}
\times\mathscr V^{\mathrm{ev}}_{x,<b}.
$$

与式 (1) 的消息图不同，每条事件边
没有另设边标识符。

函数作用事件之间只加入以下直接依赖：

1. 同一时间的函数依赖：
   $$
   P_{v,\theta}\longrightarrow S_{j,\theta}
   \longrightarrow U_{v,\theta},
   \qquad
   P_{v,\theta}\longrightarrow U_{v,\theta},
   $$
   其中 $j=\rho(v)$、$v\in\mathcal C_{j,\theta}$；若 $v$ active，再加入：
   $$
   U_{v,\theta}\longrightarrow F_{v,\theta},
   \qquad
   P_{v,\theta}\longrightarrow F_{v,\theta}.
   $$
   其中 $P_{v,\theta}\to U_{v,\theta}$ 记录状态采用直接读取准备所得的候选新状态，
   $P_{v,\theta}\to F_{v,\theta}$ 记录完整输出直接读取准备所得的本地内容；
2. 同一节点相邻两个实际节点事件之间的状态边：
   $$
   U_{v,\theta}\longrightarrow P_{v,\theta'}
   \qquad(\theta<\theta');
   $$
3. 同一 region 相邻两个实际选择事件之间的历史边：
   $$
   S_{j,\theta}\longrightarrow S_{j,\theta'}
   \qquad(\theta<\theta');
   $$
4. 若 $F_{u,\eta}$ 沿 $a$ 产生一条在 cut 内到达 $v$ 的消息，则加入：
   $$
   F_{u,\eta}\longrightarrow
   P_{v,\eta+\delta(a)}.
   $$

第 2、3 项中的“相邻”表示两者之间没有同一节点或同一 region 的另一个实际事件。
即使 $P\to U$ 与 $P\to F$ 已分别被同刻路径蕴含，仍因它们表示直接函数自变量而保留；
其余间接依赖只由有向路径表示，不重复加入全部远距离边。

令：

$$
\mathscr E^{\mathrm{ev}}_{x,<b}
\subseteq
\mathscr V^{\mathrm{ev}}_{x,<b}
\times\mathscr V^{\mathrm{ev}}_{x,<b}
$$

**恰好**由上述四类有序事件对组成，并正式定义 finite-cut 函数作用事件图：

$$
\mathscr G^{\mathrm{ev}}_{x,<b}
=\bigl(\mathscr V^{\mathrm{ev}}_{x,<b},
\mathscr E^{\mathrm{ev}}_{x,<b}\bigr).
$$

“恰好”排除了任何未声明的依赖边；间接依赖只由这张图中的有向路径表示。

### 4.3 事件秩

定义：

$$
\begin{aligned}
\operatorname{rank}(P_{v,\theta})&=(\theta,0),\\
\operatorname{rank}(S_{j,\theta})&=(\theta,1),\\
\operatorname{rank}(U_{v,\theta})&=(\theta,2),\\
\operatorname{rank}(F_{v,\theta})&=(\theta,3),
\end{aligned}
\tag{23}
$$

并在 $\mathbb N\times\{0,1,2,3\}$ 上使用字典序：$(\theta,r)<_{\mathrm{lex}}(\theta',r')$ 当且仅当 $\theta<\theta'$，或 $\theta=\theta'$ 且 $r<r'$。

> [!theorem] 定理 4：finite-cut 事件图是有限 DAG
> 第 4.1--4.2 节定义的事件图有限，并且每条依赖边都严格增加式 (23) 的秩。因此它不含有向环。

**证明。** 有限性由定理 1 得到。同刻依赖严格增加第二坐标；节点状态边和 selector-history 边严格增加第一坐标；消息边由 $\delta(a)>0$ 严格增加第一坐标。因此每条边都严格增加字典序。若存在有向环，沿环严格增加秩以后又回到原秩，矛盾。$\square$

所以必须区分：

- **structural cycle**：固定消息图 $G$ 中的有向环；
- **finite-cut event DAG**：一次输入、一个 cut 所实例化的有限函数依赖图。

前者可以存在，后者仍然无环。

### 4.4 零时延为什么不在本文内

若把第 3.1 节的自环改成 $\delta(a)=0$，则时间 $\theta$ 的 $F_{v,\theta}$ 会试图产生同一时间纤维所需的消息，形成：

$$
P_{v,\theta}\longrightarrow S_{j,\theta}
\longrightarrow U_{v,\theta}
\longrightarrow F_{v,\theta}
\longrightarrow P_{v,\theta}.
$$

式 (23) 的最后一条边会从 $(\theta,3)$ 返回 $(\theta,0)$。这时必须另给固定点、方程求解或有限轮迭代语义；把 $0$ 代入式 (1) 并不能继续使用定理 1 与定理 4。

## 5. seal、关闭与有限切面进展

直接递归假定完整输入历史已经作为数学对象给定。在线求值时，求值者通常只持有其中一部分记录。本节定义：一份部分记录在什么条件下足以证明某个时间纤维不会再增加。

### 5.1 部分记录与有效 seal

由推论 2 定义可能无限的实际消息集合：

$$
M^\infty=\bigcup_{b\in\mathbb N}M_{<b}^{\mathrm{send}}.
$$

取当前已纳入求值记录的集合：

$$
E^\circ\subseteq E_x,
\qquad
H\subseteq M^\infty.
$$

$H$ 是已经纳入当前阶段的实际内部消息集合，不是由 $E^\circ$ 自动决定的代数闭包。合法阶段还要求一条消息只有在其源完整输出事件已经完成以后才能进入 $H$。

令 $\overline{\mathbb N}=\mathbb N\cup\{\infty\}$，其中每个自然数都小于 $\infty$。若 $e=(\mathrm{ext},i,k,y)$，定义 $\operatorname{inport}(e)=i$。对 $s\in\overline{\mathbb N}$ 定义：

$$
\begin{aligned}
E_x(i,<s)
&=\{e\in E_x\mid
\operatorname{inport}(e)=i,\ \operatorname{time}(e)<s\},\\
M^\infty(a,<s)
&=\{m\in M^\infty\mid
\operatorname{edge}(m)=a,\ \operatorname{time}(m)<s\}.
\end{aligned}
\tag{24}
$$

给定函数：

$$
\sigma^{\mathrm{in}}:\mathsf I\to\overline{\mathbb N},
\qquad
\sigma^A:A\to\overline{\mathbb N}.
$$

称它们相对于 $(E^\circ,H)$ **有效**，当且仅当：

$$
\begin{aligned}
E_x(i,<\sigma^{\mathrm{in}}(i))&\subseteq E^\circ
&& (i\in\mathsf I),\\
M^\infty(a,<\sigma^A(a))&\subseteq H
&& (a\in A).
\end{aligned}
\tag{25}
$$

式 (25) 是本文中 seal 的全部数学含义。它是关于“所有较早记录”的全称命题；$E^\circ$ 或 $H$ 当前没有新增元素并不能推出这个命题。

这里定义的只是相对于完整实际消息集 $M^\infty$ 的**外延有效性**，不是让在线求值者预知未来消息的办法。定理 8 会给出一条不读取未来消息的构造轨迹；研究任意在线暴露顺序时，还必须沿用前置教材的源事件约束，也就是上面的合法阶段条件：只有相应 $F_{v,\theta}$ 完成以后，其消息才可进入 $H$。

定理 3 从外部比较两个完整输入历史，并不告诉在线求值者何时已经看全前缀。若 $\sigma^{\mathrm{in}}(i)\ge b$ 对每个输入端口成立，则式 (25) 的第一行正是这种知识：$E^\circ$ 已包含所有时间小于 $b$ 的源记录。source seal 因而是识别定理 3 所讨论输入前缀的一份证明，而不是另一种输入值。

### 5.2 节点前沿与纤维关闭

定义：

$$
\begin{aligned}
\lambda(v)
&=\min\left(
\{\sigma^A(a)\mid a\in\operatorname{In}(v)\}
\cup
\{\sigma^{\mathrm{in}}(i)\mid\gamma(i)=v\}
\right),\\
\lambda(\mathcal R_j)
&=\min_{v\in\mathcal R_j}\lambda(v),
\end{aligned}
\tag{26}
$$

并规定空集的最小值为 $\infty$。定义当前部分纤维：

$$
B^\circ_{v,\theta}
=\{z\in E^\circ\cup H\mid
\operatorname{target}(z)=v,\ \operatorname{time}(z)=\theta\}.
$$

> [!lemma] 引理 5：节点纤维关闭
> 若 $\lambda(v)>\theta$，则：
> $$
> B^\circ_{v,\theta}=B_{v,\theta}.
> \tag{27}
> $$

**证明。** 左边显然包含于完整纤维。若完整纤维还有一个未出现的外部记录，它会违反式 (25) 的第一项；若还有一个未出现的内部消息，它会违反第二项。两种矛盾都使用 $\operatorname{time}(z)=\theta<\lambda(v)$。$\square$

严格不等式不能改成 $\lambda(v)\ge\theta$：seal 等于 $\theta$ 仍允许一条到达时间恰为 $\theta$ 的记录尚未进入当前集合。

> [!theorem] 定理 6：region 候选集合关闭
> 若 $\lambda(\mathcal R_j)>\theta$，则：
> $$
> \{v\in\mathcal R_j\mid B^\circ_{v,\theta}\ne\varnothing\}
> =\mathcal C_{j,\theta}.
> $$

**证明。** 式 (26) 给出每个 $v\in\mathcal R_j$ 都满足 $\lambda(v)>\theta$；逐节点应用引理 5，再比较纤维是否为空。$\square$

定理 6 只关闭候选集合。应用式 (13) 以前，还必须知道每个候选节点的旧状态 $q_v^\theta$，并完成同一 region 在所有更小逻辑时间的实际 selector step，从而得到唯一的 $y_j^\theta$。输入关闭、节点状态就绪和 selector-history 就绪是三个不同命题。

### 5.3 节点完成怎样推出出边 seal

取当前阶段已经完成的复合节点事件集合：

$$
\mathsf{Done}
\subseteq
\bigcup_{b\in\mathbb N}\mathcal E^{\mathrm{node}}_{x,<b}.
$$

这里 $(v,\theta)\in\mathsf{Done}$ 表示：$P_{v,\theta}$、相应的
$S_{\rho(v),\theta}$ 与 $U_{v,\theta}$ 已经完成；若 $v$ active，则
$F_{v,\theta}$ 也已经完成，它产生的输出已经确定，并且它产生的每条内部消息都已经纳入当前 $H$。这一定义把“函数已经返回”与“结果已经进入当前数学记录”一并包括在 $\mathsf{Done}$ 的成员关系中。对 $r\in\mathbb N$，定义：

$$
\operatorname{DoneTo}(v,r)
\Longleftrightarrow
\left(
\lambda(v)\ge r
\ \land\
\{(v,\theta)\mid\theta<r,\ B_{v,\theta}\ne\varnothing\}
\subseteq\mathsf{Done}
\right).
\tag{28}
$$

第一项证明时间小于 $r$ 的输入纤维已经关闭；第二项证明其中实际存在的节点事件已经完成。两项不能互相替代。

这里的 $\mathsf{Done}$ 特意比前置 TimedDAG 教材中的 $\operatorname{Completed}_n$ 更强：后者允许完整输出先完成、消息随后才进入公开集合；本文的成员关系已经要求相应内部消息属于 $H$。这个加强正是下一个引理可以直接使用 $m\in H$ 的原因。

> [!lemma] 引理 7：正时延出边的 seal 推进
> 设 $a\in\operatorname{Out}(v)$。若 $\operatorname{DoneTo}(v,r)$ 成立，则以下取值有效：
> $$
> \sigma^A(a)=r+\delta(a).
> \tag{29}
> $$

**证明。** 任取沿 $a$ 到达时间小于 $r+\delta(a)$ 的实际消息 $m$。由式 (4)：

$$
\operatorname{send}(m)+\delta(a)<r+\delta(a),
$$

所以 $\operatorname{send}(m)<r$。令 $\theta=\operatorname{send}(m)$；消息的存在蕴含源节点 $v$ 在时间 $\theta$ active，因而 $B_{v,\theta}\ne\varnothing$。式 (28) 给出 $(v,\theta)\in\mathsf{Done}$，而 $\mathsf{Done}$ 的成员定义又给出 $m\in H$。故式 (25) 的第二项成立。$\square$

正时延还提供一个不需要任何消息已经产生的初始事实：

$$
M^\infty(a,<\delta(a))=\varnothing
\qquad(a\in A).
\tag{30}
$$

因此即使 $a$ 是自环，$\sigma^A(a)=\delta(a)>0$ 也是初始有效 seal。它关闭时间 $0$，完成时间 $0$ 后，引理 7 又把 seal 推到更远时间。正是这个严格增量使环上的有限进展归纳能够启动。

### 5.4 source-sealed cut 一定可以有限推进

> [!theorem] 定理 8：严格正时延规格的 finite-cut productivity
> 固定 $b\in\mathbb N$ 与 $E^\circ\subseteq E_x$。若对每个输入端口 $i$ 都有 $\sigma^{\mathrm{in}}(i)\ge b$ 且
> $E_x(i,<\sigma^{\mathrm{in}}(i))\subseteq E^\circ$，则存在一条按逻辑时间递增的求值轨迹，完成所有 $\theta<b$ 的节点事件与选择事件，产生恰好 $\mathcal T_{x,<b}$，并证明此后不会新增时间小于 $b$ 的外部输出。该轨迹只含有限多个抽象函数作用。

**证明。** 当 $b=0$ 时结论为空。以下轨迹只从 $E^\circ$ 读取外部记录；对任意 $\theta<b$，输入 seal 假设与 $E^\circ\subseteq E_x$ 保证其中时间为 $\theta$ 的记录恰好等于 $E_x$ 的相应记录。

设 $b>0$。在开始处理时间 $\theta$ 时，记当前消息集合与边 seal 为 $H_\theta,\sigma^A_\theta$。初始取：

$$
H_0=\varnothing,
\qquad
\sigma^A_0(a)=\delta(a).
$$

式 (30) 证明这些初始 seal 有效；输入端口 seal 也严格大于时间 $0$。所以所有时间 $0$ 的节点纤维和 region 候选集合都由引理 5、定理 6 关闭。先准备全部候选，再为每个 region 应用式 (13)，最后应用式 (14)--(16) 并立即把实际消息纳入 $H_1$。

更一般地，在开始处理时间 $\theta<b$ 时使用以下归纳不变量：$H_\theta=\bigcup_{\eta<\theta}M_\eta$，所有时间小于 $\theta$ 的事件都已完成，而且每条边 $a$ 已有有效 seal：

$$
\sigma^A_\theta(a)=\theta+\delta(a).
$$

记 $\lambda_\theta$ 为式 (26) 对 $(\sigma^{\mathrm{in}},\sigma^A_\theta)$ 的实例。上述不变量在 $\theta=0$ 时由式 (30) 成立。由于 $\delta(a)>0$ 且外部输入 seal 至少为 $b$，每个节点都满足 $\lambda_\theta(v)>\theta$；较早状态采用和 selector-history 更新也已经完成。因此可以唯一完成时间 $\theta$ 的全部作用，并令 $H_{\theta+1}=H_\theta\cup M_\theta$。

完成以后，对每条 $c\in\operatorname{In}(v)$ 都有
$\sigma^A_\theta(c)=\theta+\delta(c)\ge\theta+1$；输入端口 seal 也至少为 $b\ge\theta+1$。所以 $\lambda_\theta(v)\ge\theta+1$。把刚完成的复合节点事件纳入 $\mathsf{Done}$、把它们产生的消息纳入 $H_{\theta+1}$ 后，以当前这些对象解释式 (28)，$\operatorname{DoneTo}(v,\theta+1)$ 对每个 $v$ 成立。引理 7 把每条出边 $a$ 的 seal 推进为 $\sigma^A_{\theta+1}(a)=\theta+1+\delta(a)$，正好建立下一时间的不变量。

直到 $b-1$ 的归纳产生定理 1 的唯一记录。以后任何节点事件的输出时间都不小于 $b$，所以不能新增输出时间小于 $b$ 的记录。有限函数作用数由式 (20) 得到。$\square$

若式 (5)--(6) 的局部函数各有终止的参考程序，定理 8 立即给出一个会终止的 reference interpreter。若它们只是抽象全函数，定理只给出有限的函数作用结构，不声称机器已经知道怎样计算每个函数值。

### 5.5 两个不能混淆的反例

1. **队列暂时为空不等于 seal。** 一个输入源当前没有交付记录，但以后仍可能交付逻辑时间为 $3$ 的合法记录；此时不能声称它 seal 到 $4$。
2. **已收到很多晚消息不能补偿一条早消息。** 式 (25) 是集合覆盖条件。即使 $H$ 含一百万条到达时间大于 $10$ 的消息，只要漏掉一条到达时间为 $2$ 的实际消息，就不能把相应边 seal 到 $3$。

## 6. 在完整逻辑时间切面停止

### 6.1 完整切面

对一份满足第 5.3 节成员含义的合法部分记录，定义：

$$
\operatorname{CutDone}(b)
\Longleftrightarrow
\mathcal E^{\mathrm{node}}_{x,<b}\subseteq\mathsf{Done}.
$$

称求值**完成 cut $b$**，当且仅当 $\operatorname{CutDone}(b)$ 成立。每个实际选择事件至少有一个候选节点，所以这个集合包含关系同时蕴含：全部 $\theta<b$ 的准备、选择与状态采用已经完成；全部 active 节点的 $\operatorname{Full}$ 已经完成；并且：

$$
M_{<b}^{\mathrm{send}}\subseteq H.
$$

外部输出则是这些已完成 $\operatorname{Full}$ 值中的 $Z_{<b}$ 坐标；若另设当前已交付输出集合 $Z^\circ$，外部交付完成还要单独要求 $Z_{<b}\subseteq Z^\circ$。它不参与本文的未来递归。因此，$\operatorname{CutDone}(b)$ 不允许停在一次式 (13) 的中间，也不允许把已经求出但尚未纳入 $H$ 的内部消息留在隐藏临时变量中。

### 6.2 跨越切面的在途消息

定义：

$$
W_b
=\{m\in M_{<b}^{\mathrm{send}}
\mid
\operatorname{time}(m)\ge b\}.
\tag{31}
$$

由于 $m\in M_{<b}^{\mathrm{send}}$ 已经蕴含 $\operatorname{send}(m)<b$，式 (31) 等价于：

$$
W_b
=\{m\in M^\infty\mid
\operatorname{send}(m)<b\le\operatorname{time}(m)\}.
$$

边界必须包含等号：恰在时间 $b$ 到达的消息还没有被时间小于 $b$ 的节点事件消费。

当前微节点规格还能给出一个与 $b$ 无关的界：

$$
|W_b|\le\sum_{a\in A}\delta(a).
\tag{32}
$$

**证明。** 固定边 $a$。跨越 cut 的消息发送时间 $\eta$ 必须满足：

$$
\max(0,b-\delta(a))\le\eta<b.
$$

其中至多有 $\delta(a)$ 个自然数。每个 $(a,\eta)$ 至多产生一条消息；再对全部边求和。$\square$

式 (32) 依赖“每个节点事件在每条出边上至多产生一条消息”。若以后允许一次产生任意大小 batch，这个界必须重证，不能只保留同一个 $W_b$ 名字。

### 6.3 continuation

定义 cut $b$ 的未来计算状态：

$$
Q_b
=
\left(
b,
(q_v^b)_{v\in V},
(y_j^b)_{j\in J},
W_b
\right).
\tag{33}
$$

四个坐标分别保存：

1. 绝对逻辑时间；
2. 每个节点完成所有逻辑时间 $\theta<b$ 的作用后所得状态；
3. 每个 region 完成所有逻辑时间 $\theta<b$ 的 selector step 后所得历史；
4. 已由左侧产生、但将在右侧到达的消息。

把第 3.3 节的单节点自环继续手算三步，可以同时看见这些对象。设唯一外部输入在时间 $0$ 到达，输入端口 seal 为 $\infty$，$\delta(a)=2$，并记时间 $0,2$ 发出的消息为 $m_0,m_2$。完成 $[0,b)$ 后可取 $H_b=\bigcup_{\eta<b}M_\eta$、$\sigma_b^A(a)=b+2$；于是 $\lambda_b(v)=b+2$。因为只有一个节点和一个 region，表中省略状态族的下标。前四个切面为：

| $b$ | $H_b$ | $\sigma_b^A(a)=\lambda_b(v)$ | 已成立的完成谓词 | $W_b$ | $Q_b$ |
| ---: | --- | ---: | --- | --- | --- |
| $0$ | $\varnothing$ | $2$ | $\operatorname{DoneTo}(v,0)$ | $\varnothing$ | $(0,q^0,y^0,\varnothing)$ |
| $1$ | $\{m_0\}$ | $3$ | $\operatorname{DoneTo}(v,1)$ | $\{m_0\}$ | $(1,q^1,y^1,\{m_0\})$ |
| $2$ | $\{m_0\}$ | $4$ | $\operatorname{DoneTo}(v,2)$ | $\{m_0\}$ | $(2,q^2,y^2,\{m_0\})$ |
| $3$ | $\{m_0,m_2\}$ | $5$ | $\operatorname{DoneTo}(v,3)$ | $\{m_2\}$ | $(3,q^3,y^3,\{m_2\})$ |

$H_b$ 是累计记录，所以 $m_0$ 在时间 $2$ 被消费后仍留在其中；$W_b$ 只保留跨越当前切面的消息。$\sigma_b^A,\lambda_b$ 是从完成事实推出的进展证书，不是 $Q_b$ 的坐标。

$b$ 不能一般地从其余坐标恢复，因为式 (5)--(6) 的函数允许显式读取逻辑时间。$Q_b$ 也没有保存过去输出 $Z_{<b}$：这些输出不参与未来节点递归。若目标还包括恢复完整输出日志或保证外部 exactly-once 交付，则必须另存 $Z_{<b}$ 或一份交付账本。

$Q_b$ 是**语义 continuation**，不是式 (25) 的在线进展证书：它不保存已经消费的全部历史消息，也不保存 source seal。第 6.4 节的 continuation sufficiency 定理假定 $Q_b$ 确实来自一个已完成的合法 cut。在线恢复还要可信地知道这一来源，并取得覆盖目标区间的输入端口 seal。

更明确地说，令 $E^{\ge b}\subseteq E_x$ 是恢复后已经取得、时间不小于 $b$ 的外部记录，$H^{\ge b}$ 是恢复后新发送且已经纳入记录的消息。输入端口的相对覆盖条件是：

$$
\{e\in E_x\mid
\operatorname{inport}(e)=i,
b\le\operatorname{time}(e)<s\}
\subseteq E^{\ge b}.
$$

对内部消息定义：

$$
M^\infty_{\ge b}(a,<s)
=\{m\in M^\infty\mid
\operatorname{edge}(m)=a,
\operatorname{send}(m)\ge b,
\operatorname{time}(m)<s\}.
$$

suffix-relative edge seal 的覆盖条件是
$M^\infty_{\ge b}(a,<s)\subseteq H^{\ge b}$。在线恢复的当前纤维从
$E^{\ge b}\cup W_b\cup H^{\ge b}$ 取得：$W_b$ 覆盖全部较早发送而尚未到达的消息，相对 seal 只量化恢复后发送的消息。后者沿边 $a$ 最早在 $b+\delta(a)$ 到达，所以初始相对 edge seal 可取 $s=b+\delta(a)$；随后可用与定理 8 相同的逐时间归纳推进。这个额外证书属于在线 progress 层，不改变 $Q_b$ 的未来函数值。

### 6.4 从 continuation 恢复

固定 $c\ge b$。给定 $Q_b$ 与未来外部记录：

$$
E_{x,[b,c)}
=\{e\in E_x\mid b\le\operatorname{time}(e)<c\}.
$$

从 $q_v^b,y_j^b$ 开始，对 $\theta\in[b,c)$ 把式 (10) 改成：

$$
\begin{aligned}
B^{b\to c}_{v,\theta}
=\{z\in
E_{x,[b,c)}\cup W_b
\cup\bigcup_{\eta\in[b,\theta)}M^{b\to c}_\eta
\mid{}&
\operatorname{target}(z)=v,\\
&\operatorname{time}(z)=\theta\}.
\end{aligned}
\tag{34}
$$

其余步骤按式 (11)--(16) 原样执行。在终点 $c$，对旧在途消息与本段新消息的整个并集按到达时间过滤，定义：

$$
W_c
=
\left\{m\in
W_b\cup\bigcup_{\eta\in[b,c)}M^{b\to c}_\eta
\ \middle|\
\operatorname{time}(m)\ge c
\right\}.
$$

因此，已经在 $[b,c)$ 到达并被消费的旧 $W_b$ 消息不会继续留在 $W_c$。

当 $c=b$ 时，区间为空；约定不调用任何局部函数，并原样返回 $Q_b$。

> [!theorem] 定理 9：continuation sufficiency
> 若两段合法过去在同一个 cut $b$ 上得到相同 $Q_b$，并且随后得到相同的外部输入记录，则式 (34) 在任意未来有限区间中产生相同的时间纤维、候选集合、active sets、节点状态、selector-history、消息、输出和下一 continuation。

**证明。** 在时间 $b$，两次恢复具有相同绝对时间、节点状态、selector-history、跨界消息与当前外部输入，所以式 (34) 相同。式 (11)--(16) 都是确定函数，因而本时刻结果相同。对后续时间作归纳即可。$\square$

所以 $Q_b$ 是本文未来语义的一个充分统计量；本文没有声称它是所有等价编码中最小的。若实现中的函数还能读取隐藏日志、墙钟、未登记随机数发生器或共享可变状态，则式 (33) 将不再充分，那些对象必须显式进入状态或 continuation。

## 7. cut transition 与 composition

### 7.1 区间转导

称某个 $Q_a$ **可达**，若它由式 (33) 从一段合法 cut trace 得到。对 $a\le b$，定义区间转导：

$$
\Phi_{a,b}:
(Q_a,E_{x,[a,b)})
\longmapsto
(\mathcal U_{x,[a,b)},Q_b),
\tag{35}
$$

其中 $\mathcal U_{x,[a,b)}$ 保存本区间的全部式 (10)--(16) 坐标、发送时间位于 $[a,b)$ 的新消息和输出时间位于 $[a,b)$ 的新输出。它不把 $W_a$ 重复登记成“本段新产生的消息”。定义域只取如下配对：$Q_a$ 来自某段合法过去，而 $E_{x,[a,b)}$ 是与这段过去相容的合法、完整输入片段。“完整”表示它不是当前已公开输入的任意子集，而是所选输入历史在该区间的全部记录。source seal 是在线执行者证明这份完整性的方式之一，不是 $\Phi_{a,b}$ 的自变量。

对空区间定义：

$$
\Phi_{a,a}(Q_a,\varnothing)=(\varnothing,Q_a),
$$

其中第一项是空区间记录。

若第一段转导的输出 continuation 与第二段转导的输入 continuation 是同一个完整 $Q_b$，定义 $\mathcal U_{x,[a,b)}\odot_b\mathcal U_{x,[b,c)}$ 为两段区间记录的规范粘合：

- 事件坐标按逻辑时间不交地并合；
- 新消息按发送时间不交地并合；
- 两份边界状态与 selector-history 在时间 $b$ 的共同坐标上识别一次；
- $W_b$ 只作为第二段的输入边界，不作为本段新生成的记录重复出现。

空区间记录是这个粘合的单位元。

### 7.2 composition 定理

> [!theorem] 定理 10：cut composition
> 任取 $a\le b\le c$。若：
> $$
> \begin{aligned}
> \Phi_{a,b}(Q_a,E_{x,[a,b)})
> &=(\mathcal U_{x,[a,b)},Q_b),\\
> \Phi_{b,c}(Q_b,E_{x,[b,c)})
> &=(\mathcal U_{x,[b,c)},Q_c),
> \end{aligned}
> $$
> 则：
> $$
> \Phi_{a,c}(Q_a,E_{x,[a,c)})
> =
> \left(
> \mathcal U_{x,[a,b)}\odot_b\mathcal U_{x,[b,c)},
> Q_c
> \right).
> \tag{36}
> $$

**证明。** 第一段在时间 $b$ 给出的节点状态与 selector-history，按定义就是一次执行到达同一切面时的相应坐标。第一段给出的 $W_b$ 恰好包含所有更早产生而将在时间不小于 $b$ 到达的消息。

因此，一次执行的式 (10) 与分段执行的式 (34) 虽取自不同的原始并集，但在时间 $b$ 按目标节点与到达时间过滤后产生相同纤维：第一段的 $W_b$ 恰好保留更早产生且到达时间不小于 $b$ 的消息，到达时间小于 $b$ 的记录则都被过滤掉。假设两者直到 $\theta-1$ 相同，则它们已经新产生的消息相同，时间 $\theta$ 的纤维以及式 (11)--(16) 的全部函数值也相同。对 $\theta\in[b,c)$ 归纳，得到两段未来记录相同。

在切面 $c$，两种执行都对“先前 $W_a$ 与区间 $[a,c)$ 新消息”的整个并集应用 $\operatorname{time}(m)\ge c$ 这一过滤条件，所以最终 $W_c$、节点状态和 selector-history 也相同。规范粘合的定义随后给出式 (36)。$\square$

令：

$$
Q_0=\left(0,(q_v^{\mathrm{init}})_{v\in V},
(y_j^{\mathrm{init}})_{j\in J},\varnothing\right).
$$

反复应用定理 10，便得到“一次推进到 $c$”与“沿任意完整逻辑时间切面分块推进到 $c$”的精确等价。这个结论是 chunk correctness，不是低 span 或硬件高性能结论。

### 7.3 为什么 continuation 的每个坐标都必要

- 丢掉 $W_b$：第 3.3 节的延迟自环在恢复后漏掉未来事件。
- 丢掉某个 $q_v^b$：节点未来的 $\operatorname{Upd}_v$ 或 $\operatorname{Read}^{-}_v$ 可以改变。
- 丢掉某个 $y_j^b$：后续式 (13) 的 active set 可以改变。
- 丢掉 $b$：若 selector 按时间奇偶选择，两个数值状态相同的切面仍可能有不同未来。

若允许在非完整切面暂停，还必须保存未提交候选状态、部分 selector 输入或已求出但未纳入 $W_b$ 的消息。式 (33) 只为第 6.1 节定义的完整切面充分。

## 8. 合法调度与 reference interpreter

### 8.1 直接递归是定义，不是唯一实现顺序

式 (10)--(16) 按时间写出，是为了给每个数学坐标一个无歧义值。任何实现都可以改变彼此独立的函数作用次序，只要它尊重第 4.2 节的依赖，并且只在式 (25) 已证明相应纤维关闭后作出不可撤销选择。

特别地，一个合法调度不得：

1. 在候选集合尚可能增加时只对当前真子集应用 selector；
2. 让同一节点的晚状态更新先于早状态更新；
3. 跳过同一 region 的较早 selector-history 更新；
4. 在源完整输出事件以前公开相应消息；
5. 用线程完成顺序替代 selector 的确定平局规则。

由定理 4，略去式 (13) 中空候选集合的恒等位置后，第 4.1 节定义的全部实际函数作用事件形成有限 DAG。这里的拓扑序是事件顶点的一个
全序，并要求每条边的起点都排在终点以前。任意拓扑序都给出相同函数值；seal
另行证明这个有限事件集合已经完整，而不是只看见了其中一个真子集。

### 8.2 最小 reference interpreter 契约

一个最小解释器接受：

$$
(\text{固定规格},Q_a,E_{x,[a,b)},b),
$$

然后：

1. 对 $\theta=a,a+1,\ldots,b-1$ 构造式 (34) 的全部纤维；
2. 按式 (11)--(16) 完成该时间的准备、选择、状态采用与完整输出；
3. 以 $(\operatorname{send}(m),\operatorname{edge}(m))$ 为稳定消息来源坐标；
4. 返回完整区间记录与式 (33) 的 $Q_b$。

正确性测试至少比较：

$$
B,\mathcal C,h,\widetilde q,d,\mathcal A,q,y,
f^A,f^O,M,Z,W
$$

以及逐边消息身份。这里 $h,\widetilde q,d,f^A,f^O$ 也可以由已比较的自变量和固定函数逐项重建，但测试若直接保存它们，更容易定位首个分歧；只比较最终输出 payload 不足以检验定理 10。

本文附带的最小可执行见证是 [positive_delay_graph_reference.py](examples/positive_delay_graph_reference.py)。它用延迟自环和两节点环检查一次执行与多种 cut 切分，并故意展示丢失 $W_b$ 会怎样破坏恢复。它还从 reference trace 构造一张与第 4 节事件图具有相同传递闭包的稀疏调度图：只省略已经分别由 $P\to S\to U$ 与 $P\to S\to U\to F$ 蕴含的 $P\to U$、$P\to F$，再以随机 ready-event 拓扑序重新求值完整 cut。该程序是定理的可执行样例，不代替上述证明。

### 8.3 随机调度对拍的边界

附带解释器已经随机选择当前无未完成前驱的事件，并把所得完整记录与 continuation
同直接递归逐项比较。这个测试使用已经由 reference recursion 确定的有限事件集合，
检验的是这张稀疏调度图的前驱关系足以支持与直接递归相同、且不依赖所选拓扑序的重求值。

若进一步模拟在线 closure，还应随机延迟消息进入 $H$，但只有在相应源事件完成以后才允许进入，并用式 (25) 检查每次 seal 推进。那会检验进展证书的实现，而不是为定理 4 增加另一种事件语义。

随机测试可以发现解释器遗漏依赖；它不能证明所有输入上的定理。

## 9. structural SCC 与 selector 边界

finite-cut 语义已经在任意正时延消息图上成立，不需要先求 SCC。本节才研究能否把若干节点作为语义封闭的宏节点。

### 9.1 message SCC 与 condensation DAG

本节约定“可达”允许长度为 $0$ 的路径；因此每个节点都可达自身。

对 $u,v\in V$，定义：

$$
u\sim_G v
\Longleftrightarrow
u\text{ 在 }G\text{ 中可达 }v
\text{ 且 }v\text{ 在 }G\text{ 中可达 }u.
\tag{37}
$$

$\sim_G$ 是等价关系：长度为 $0$ 的可达给出自反性，定义本身给出对称性，
有向路径的拼接给出传递性。因此可以定义它的等价类集合及分量间边关系：

$$
\begin{aligned}
\mathcal S_G&=V/{\sim_G},\\
E_{\mathrm{cond}}
&=\{(C,D)\in\mathcal S_G^2\mid
C\ne D,\ \exists a\in A:\
\operatorname{src}(a)\in C,\
\operatorname{dst}(a)\in D\}.
\end{aligned}
$$

$\mathcal S_G$ 的元素称为 **message structural SCC**，$(\mathcal S_G,E_{\mathrm{cond}})$ 称为 message condensation graph。宏边界仍必须保留每个原边 $a$ 的身份、端点和时延；$E_{\mathrm{cond}}$ 中的有序对不能代替实际消息端口。

> [!theorem] 定理 11：message condensation graph 是 DAG
> $(\mathcal S_G,E_{\mathrm{cond}})$ 不含有向环。

**证明。** 若不同 SCC 在 condensation graph 中形成环，把各分量内部的互达路径与分量之间的边依次拼接，就得到环上所有节点两两互达。它们应属于同一个 $\sim_G$ 等价类，与分量不同矛盾。$\square$

定理 11 是图论结论。它没有说明一个 SCC 内怎样求值，也没有说明 region selector 的依赖是否被 message SCC 边界包含。

### 9.2 为什么跨 SCC region 会破坏宏边界

考虑：

$$
V=\{u,v\},
\qquad
A=\varnothing,
\qquad
\mathcal R_j=\{u,v\},
\qquad
K_j=1.
$$

时间 $0$ 两个节点都从各自输入端口成为候选。即使 $Y_j$ 是单点集，selector 仍可比较 $d_{u,0},d_{v,0}$，再决定是否让 $v$ active。函数作用依赖包含：

$$
P_{u,0}\longrightarrow S_{j,0}
\longrightarrow U_{v,0}\longrightarrow F_{v,0}.
$$

但 message graph 中没有从 $u$ 到 $v$ 的边；式 (37) 会把它们分成两个 SCC。若先把 $\{v\}$ 当成独立宏节点求值，它还不知道 $u$ 的描述量，因而边界不完整。

候选永不共现也不充分。若时间 $0$ 只有 $u$ 是候选，时间 $1$ 只有 $v$ 是候选，而 $S_{j,0}$ 更新的 $y_j^1$ 改变 $S_{j,1}$，则仍有：

$$
P_{u,0}\longrightarrow S_{j,0}
\longrightarrow S_{j,1}\longrightarrow U_{v,1}.
$$

这个依赖同样没有出现在 message condensation graph 中。

### 9.3 SCC-local region profile

令 $\pi:V\to\mathcal S_G$ 把节点映到其 message SCC。定义附加条件：

$$
\forall j\in J,\ \forall u,v\in\mathcal R_j,
\qquad
\pi(u)=\pi(v).
\tag{38}
$$

称式 (38) 为 **SCC-local region 条件**。它只用于本节的 message-SCC 宏定理，不是第 1--8 节 finite-cut 语义的前提。

在式 (38) 下，把 $P_{v,\theta},U_{v,\theta},F_{v,\theta}$ 归于 $\pi(v)$，并把 $S_{j,\theta}$ 与 $y_j$ 归于包含 $\mathcal R_j$ 的唯一 SCC。于是：

- 节点状态依赖留在一个 SCC 内；
- selector-history 依赖留在一个 SCC 内；
- 同刻准备、选择、采用与完整输出依赖留在一个 SCC 内；
- 唯一可能跨 SCC 的函数作用边是原消息边。

固定共享参数不会在一次前向运行中被这些事件改写，所以不要求使用同一参数的节点进入同一 SCC。共享可变状态则不同：若以后允许它，必须把相应读写依赖加入宏边界，不能继续直接使用上述结论。

为避免“属于一个 SCC”停留在口头层面，对 $C\in\mathcal S_G$ 定义：

$$
\begin{aligned}
J_C&=\{j\in J\mid\mathcal R_j\subseteq C\},\\
q^a\!\downarrow_C&=(q_v^a)_{v\in C},
&y^a\!\downarrow_C&=(y_j^a)_{j\in J_C},\\
W_a\!\downarrow_C&=\{m\in W_a\mid\operatorname{target}(m)\in C\},
&E_{x,[a,b)}\!\downarrow_C
&=\{e\in E_{x,[a,b)}\mid\operatorname{target}(e)\in C\}.
\end{aligned}
$$

对 condensation edge $D\to C$，相应的直接跨入消息是发送节点属于 $D$、目标节点属于 $C$ 的逐边消息。式 (38) 保证 $(J_C)_{C\in\mathcal S_G}$ 是 $J$ 的划分；上面的 $W_a$ 与外部输入投影也按目标 SCC 两两不交。区间记录中的节点、selector 和输出按 owner SCC 归属，新消息按源 SCC 归属，因此所有局部结果都有无歧义的不交并合。

若前驱 $D$ 已经完成区间 $[a,b)$，它交给 $C$ 的直接跨入消息精确为：

$$
M^{D\to C}_{[a,b)}
=\left\{m\in\bigcup_{\theta\in[a,b)}M_\theta
\ \middle|\
\operatorname{src}(\operatorname{edge}(m))\in D,
\operatorname{target}(m)\in C
\right\}.
$$

> [!theorem] 定理 12：SCC-local profile 的精确外层 cut 调度
> 假设式 (38) 成立。固定可达 continuation $Q_a$ 和 $a\le b$。按定理 11 选择 message SCC 的任一拓扑序；对每个 $C$，把 $q^a\!\downarrow_C$、$y^a\!\downarrow_C$、$W_a\!\downarrow_C$ 作为左边界，把 $E_{x,[a,b)}\!\downarrow_C$ 与所有前驱 $D$ 已产生的 $M^{D\to C}_{[a,b)}$ 作为输入，在 $C$ 内按式 (34) 的逻辑时间顺序推进到 $b$。按上述 owner 规则并合所得全图区间记录与 $Q_b$，恰等于式 (35) 的 $\Phi_{a,b}$。

**证明。** 对 SCC 的拓扑序归纳。一个 SCC 的所有跨边界输入消息只可能来自 condensation graph 中的前驱；否则存在一条来自尚未处理后继的反向边，与拓扑序矛盾。归纳假设因此已经给出该 SCC 在区间内的全部跨边界消息，$W_a$ 又给出过去产生但尚未到达的消息。

式 (38) 保证任何 selector 及其全部候选节点、历史状态和状态采用事件都在同一 SCC 内。固定一个 SCC 后，再对逻辑时间作归纳，式 (17) 保证内部反馈只从更小时间到更大时间。因此该 SCC 的受限记录逐项等于全图直接递归的相应投影。完成全部 SCC 后，按 owner SCC 不交并合便得到相同的节点、selector、消息与输出记录；节点状态与 selector-history 也按 owner SCC 并合，而式 (31) 给出的各 $W_b$ 投影按目标 SCC 并合，于是得到同一个 $Q_b$。$\square$

定理 12 给出 exact 外层框架，但没有证明 SCC 内的昂贵节点作用可以按时间整批暴露。把整个 SCC 放进一次 API 调用，也可能只是在调用内部让控制作用与昂贵作用交替执行 $b-a$ 次。即使以后证明了这种整批暴露，也仍不自动得到低 span：selector-history 的控制扫描可以保持线性。

还有一个容易忽略的边界：若 message graph 本身是 DAG，则它的 SCC 都是单点，式 (38) 会迫使每个 region 也是单点。因此，式 (38) 绝不能倒过来成为整篇教材的基础假设；一般多节点 region 已由第 1--8 节覆盖，只是不能直接按 message SCC 独立求值。

### 9.4 dependency-complete 静态图

沿用第 4.2 节已经正式定义的事件图
$\mathscr G^{\mathrm{ev}}_{x,<b}$。它随输入历史与 cut 改变。

为了寻找不随一次运行改变的宏边界，先把每个事件投影到持有相应节点状态或
selector-history 的对象。取与 $V$ 不交的带标签集合
$\{s_j\mid j\in J\}$，定义：

$$
\begin{aligned}
\operatorname{own}(P_{v,\theta})
&=\operatorname{own}(U_{v,\theta})
=\operatorname{own}(F_{v,\theta})=v,\\
\operatorname{own}(S_{j,\theta})&=s_j.
\end{aligned}
$$

这里的 $s_j$ 只是 selector $j$ 及其历史 $y_j$ 的 owner 标识，不是消息节点。

> [!definition] dependency-complete 静态图
> 顶点集为 $V^\dagger=V\sqcup\{s_j\mid j\in J\}$ 的有向图
> $\Gamma=(V^\dagger,E_\Gamma)$，其中
> $E_\Gamma\subseteq V^\dagger\times V^\dagger$，称为对本文事件语义
> **dependency-complete**，若对
> 任意合法输入历史 $x$、任意 cut $b$，以及
> 任意 $(e,e')\in\mathscr E^{\mathrm{ev}}_{x,<b}$，都有
> $$
> \operatorname{own}(e)=\operatorname{own}(e')
> \quad\text{或}\quad
> \bigl(\operatorname{own}(e),\operatorname{own}(e')\bigr)\in E_\Gamma.
> $$

换言之，把一条实际事件路径投影到 owner 并删去连续重复项以后，所得有限顶点
序列的每对相邻项都是 $\Gamma$ 的一条边。这个定义只要求静态图不漏掉第 4.2
节的直接依赖，不要求每条静态边都在每次运行中出现。

对任一固定的 dependency-complete 图 $\Gamma$，定义 $z\sim_\Gamma z'$ 当且仅当
$z,z'$ 在 $\Gamma$ 中互相可达。与 $\sim_G$ 相同，它也是等价关系。令：

$$
\mathcal S_\Gamma=V^\dagger/{\sim_\Gamma}.
$$

$\mathcal S_\Gamma$ 才是相对于这张固定静态图的 SCC 集合。换用一张经过证明的更小静态图，可能改变这些等价类，因此后文所有这类 SCC 都明确带上 $\Gamma$。

现在定义一个无需分析具体函数即可构造的静态图：

$$
\begin{aligned}
V^\dagger
&=V\sqcup\{s_j\mid j\in J\},\\
E^\dagger
&=\{(\operatorname{src}(a),\operatorname{dst}(a))\mid a\in A\}\\
&\quad\cup
\{(v,s_j),(s_j,v)\mid j\in J,\ v\in\mathcal R_j\}.
\end{aligned}
\tag{39}
$$

记 $G^\dagger=(V^\dagger,E^\dagger)$。
$v\to s_j$ 表示 selector 可能读取节点描述量，$s_j\to v$ 表示选择结果可能改变节点的状态采用或完整输出。$\mathcal S_{G^\dagger}$ 会自动把跨 message-SCC 的 region 依赖合入同一个宏边界。

> [!proposition] 命题 13：$G^\dagger$ 是 dependency-complete 静态图
> 式 (39) 的 $G^\dagger$ 满足上述定义。

**证明。** 逐类检查第 4.2 节的直接事件边。同刻边
$P_{v,\theta}\to S_{j,\theta}$ 投影成 $v\to s_j$，而
$S_{j,\theta}\to U_{v,\theta}$ 投影成 $s_j\to v$；两者都在式 (39)
中。$P_{v,\theta}\to U_{v,\theta}$、$U_{v,\theta}\to F_{v,\theta}$ 与
$P_{v,\theta}\to F_{v,\theta}$ 的 owner 都相同。节点状态边两端都由 $v$
持有，selector-history 边两端都由 $s_j$ 持有。最后，消息边
$F_{u,\eta}\to P_{v,\eta+\delta(a)}$ 投影成原消息边 $u\to v$，也在
式 (39) 中。直接依赖已经穷尽，结论成立。$\square$

除非明确换用另一张已证明 dependency-complete 的静态图，第 10--12 节固定取 $\Gamma=G^\dagger$，因而 $\mathcal S_\Gamma=\mathcal S_{G^\dagger}$。下文所谓宏分量均指某个明确的 $C\in\mathcal S_\Gamma$。

下面用同一个例子区分四张容易混淆的图。取正时延消息图 $G$ 恰为

```text
u → v → w
```

并令 $\mathcal R_A=\{u,w\}$、$\mathcal R_B=\{v\}$。记两条边的时延为
$d_1,d_2>0$。本节只为比较而定义区域商图边集：

$$
Q_\rho
=\left\{
\bigl(\rho(\operatorname{src}(a)),\rho(\operatorname{dst}(a))\bigr)
\ \middle|\
a\in A,\ \rho(\operatorname{src}(a))\ne\rho(\operatorname{dst}(a))
\right\}.
$$

四张图分别为：

| 图 | 在这个例子中的形状 | 它说明什么 |
| --- | --- | --- |
| 消息图 $G$ | $u\to v\to w$ | 是 DAG；三个 message SCC 都是单点。 |
| 区域商图 $(J,Q_\rho)$ | $A\to B\to A$ | 收缩 region 会产生环，但它不是事件环。 |
| 静态图 $G^\dagger$ | 增加 $u,w\leftrightarrow s_A$ 与 $v\leftrightarrow s_B$ | 含有 $u\to v\to w\to s_A\to u$，且五个顶点都在同一 SCC。 |
| 一次运行的 $\mathscr G^{\mathrm{ev}}_{x,<b}$ | 只含本次实际存在的带时间事件 | 仍由定理 4 保证是有限 DAG。 |

例如，若 $F_{u,\theta}$ 产生第一条消息，$v$ 随后 active 并产生第二条消息，
且 $b>\theta+d_1+d_2$，事件图便含有路径

$$
\begin{aligned}
F_{u,\theta}
&\longrightarrow P_{v,\theta+d_1}
\longrightarrow S_{B,\theta+d_1}
\longrightarrow U_{v,\theta+d_1}
\longrightarrow F_{v,\theta+d_1}\\
&\longrightarrow P_{w,\theta+d_1+d_2}
\longrightarrow S_{A,\theta+d_1+d_2}.
\end{aligned}
$$

若 $u$ 在最后一个时间也成为候选并被选中，这条路径还可继续到
$U_{u,\theta+d_1+d_2}\to F_{u,\theta+d_1+d_2}$。其 owner 已经沿
$G^\dagger$ 返回 $u$，事件却到达了更晚时间的另一个 $F_u$，并未返回
$F_{u,\theta}$。所以 $G^\dagger$ 的静态环不是 finite-cut 事件环。

式 (39) 是安全但不必最小的静态包络：它不检查某类事件是否对所有合法输入都
不可能出现。若另行证明某对 owner 之间的全部直接依赖在每个合法运行中都不会
实例化，可以删去这对 owner 之间的静态边。只看到某次输入没有激活它，不足以
这样做。若还要利用“selector 在整个定义域上与某个输入坐标无关”来删边，则须
先相应细化第 4.2 节的保守事件依赖关系，再对
细化后的关系证明 dependency-complete。

$G^\dagger$ 是“可能影响与所有权”的静态图，不是正时延消息图。不能把
$v\leftrightarrow s_j$ 草率解释为两条零时延消息，再宣称出现代数环；实际同刻
依赖仍按式 (23) 的 $P<S<U<F$ 阶段前进。命题 13 只证明它是安全的静态边界；
它还丢弃了平行消息边的身份。后续宏 runtime 仍须保留每个 $a\in A$，并另外
证明完整多端口契约与外层保块。

## 10. correctness、外层保块与低 span 是不同层级

本节说的 **work** 是所选计算模型中的总 primitive 成本，**span** 是同一模型下依赖图中最长路径的成本；二者都必须先指定各类函数作用的成本，不能从逻辑时间本身读出。

### 10.1 本文已经得到哪一级算法

定理 8、10、12 分别给出 finite-cut 顺序求值、切面组合与式 (38) 的
SCC-local 条件下的 message-SCC 调度；命题 13 只给出静态依赖包络。它们属于
exact correctness 或 finite progress，尚不推出性能。

后文依次区分三个更强层级：外层是否保留节点时间批，给定成本模型后的 work/span，以及具体 backend 的硬件表现。前一层成立不自动推出后一层；第 10.2 节只定义第一层。

### 10.2 第一性能台阶：节点级时间批暴露

先固定一份不含 $\operatorname{Full}$ 的**无限日程骨架**
$\mathfrak B_\infty$。对每个 $i\in\mathsf I$，先固定严格递增的共同注入日程
$\bar\iota_i:\mathbb N\to\mathbb N$。为使不同输入长度具有共同的函数类型，定义：

$$
\mathsf{Ext}_\infty
=\{(\mathrm{ext},i,k,y)\mid
i\in\mathsf I,\ k\in\mathbb N,\ y\in P\}.
$$

对 $e=(\mathrm{ext},i,k,y)\in\mathsf{Ext}_\infty$，令
$\operatorname{target}(e)=\gamma(i)$、
$\operatorname{time}(e)=\bar\iota_i(k)$、$\operatorname{value}(e)=y$。
再令：

$$
\mathsf{Atom}_\infty
=\mathsf{Ext}_\infty\cup\mathsf{Msg},
\qquad
\mathsf{Atom}_{\infty,v}
=\{z\in\mathsf{Atom}_\infty\mid\operatorname{target}(z)=v\}.
$$

骨架还包含第 1 节的图、端口、region、容量与模式、状态空间、初态，全部
$\operatorname{Upd},\operatorname{Read},\operatorname{SelStep}$，以及共同全函数：

$$
\operatorname{Agg}_v^\infty:
\mathbb N\times
\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_{\infty,v})
\longrightarrow X_v.
$$

对长度向量
$\mathbf L=(L_i)_{i\in\mathsf I}\in\mathbb N^{\mathsf I}$，令：

$$
\begin{aligned}
K_i^{\mathbf L}&=[L_i],
&
\iota_i^{\mathbf L}
&=\bar\iota_i\!\upharpoonright_{[L_i]},\\
\mathsf{Ext}_{\mathbf L}
&=\{(\mathrm{ext},i,k,y)\in\mathsf{Ext}_\infty\mid k<L_i\},
&
\mathsf{Atom}_{\mathbf L,v}
&=\mathsf{Atom}_{\infty,v}
\cap(\mathsf{Ext}_{\mathbf L}\cup\mathsf{Msg}),\\
\operatorname{Agg}_v^{\mathbf L}
&=\operatorname{Agg}_v^\infty\!
\upharpoonright_{
\mathbb N\times
\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_{\mathbf L,v})}.
\end{aligned}
$$

因此改变 $\mathbf L$ 只取共同对象的限制，不会暗中更换 aggregation 规则。
令：

$$
\mathcal O_v
=(P_\bot)^{\operatorname{Out}(v)}
\times(P_\bot)^{\operatorname{OutPort}(v)}.
$$

再固定一个非空的 admissible $\operatorname{Full}$ **解释类**
$\mathfrak F$。它的元素是函数族
$\mathbf F=(F_v)_{v\in V}$，其中：

$$
F_v:S_v\times\mathbb N\times X_v\longrightarrow\mathcal O_v.
$$

若不利用 $\operatorname{Full}$ 的额外结构，$\mathfrak F$ 可取全部这种全函数族；
也可用明确写出的统一结构契约限制它。后文计划只能使用这份共同契约，不能读取
当前 $\mathbf F$ 的身份。对每个 $\mathbf F\in\mathfrak F$ 与 $\mathbf L$，
记 $\mathfrak G_{\mathbf L}^{\mathbf F}$ 为令
$K_i=K_i^{\mathbf L}$、$\iota_i=\iota_i^{\mathbf L}$，把第 1 节的
$\mathsf{Ext},\mathsf{Atom}_v,\operatorname{Agg}_v$ 分别取成
$\mathsf{Ext}_{\mathbf L},\mathsf{Atom}_{\mathbf L,v},\operatorname{Agg}_v^{\mathbf L}$，
并令 $\operatorname{Full}_v=F_v$ 得到的规格。
成本 profile 把 $F_v$ 查询视为昂贵作用，把骨架函数与 seal bookkeeping
视为控制作用。

固定 $\mathbf F,\mathbf L$ 与 $a<b$，并写 $T=b-a$。令
$Q_a^{\mathbf F}(x)$ 表示输入
$x=(x_i:[L_i]\to P)_{i\in\mathsf I}$ 的规范递归在完整 cut $a$ 上产生的
式 (33) continuation。定义
$\omega=(Q_a,E,\sigma^{\mathrm{in}})\in\Omega_{\mathbf L,a,b}^{\mathbf F}$，
当且仅当存在上述输入 $x$，使：

$$
\begin{aligned}
Q_a&=Q_a^{\mathbf F}(x),\\
E&=E_{x,[a,b)},\\
\sigma^{\mathrm{in}}&\in\overline{\mathbb N}^{\mathsf I},\\
\sigma^{\mathrm{in}}(i)&\ge b
\quad\text{且}\quad
E_x(i,<\sigma^{\mathrm{in}}(i))
\subseteq E_{x,<a}\cup E
\qquad(i\in\mathsf I).
\end{aligned}
$$

最后一行正是式 (25) 相对于 $E_{x,<a}\cup E$ 有效。对固定
$\mathbf F$，所有这些三元组都属于共同集合：

$$
\left(
\{a\}\times\prod_{v\in V}S_v
\times\prod_{j\in J}Y_j
\times\mathcal P_{\mathrm{fin}}(\mathsf{Msg})
\right)
\times\mathcal P_{\mathrm{fin}}(\mathsf{Ext}_\infty)
\times\overline{\mathbb N}^{\mathsf I}.
$$

因此可以取普通并集：

$$
\Omega_{a,b}^{\mathbf F}
=\bigcup_{\mathbf L\in\mathbb N^{\mathsf I}}
\Omega_{\mathbf L,a,b}^{\mathbf F}.
$$

相同可见元组在这个并集中只算同一个元素；$\mathbf L$ 与见证 $x$ 不是计划可读
坐标。即使同一 $\omega$ 有两个不同的 $\mathbf L,x$ 见证，它们也从相同
$Q_a$ 和区间输入 $E$ 开始；source seal 排除区间内遗漏输入，而两边的
aggregation 都是同一个 $\operatorname{Agg}_v^\infty$ 在当前纤维上的值。
按 $\theta=a,\ldots,b-1$ 归纳，式 (34) 与式 (11)--(16) 的全部坐标因此相同。
所以对固定 $\mathbf F$，$\omega$ 唯一确定参考区间记录
$\mathcal U_{x,[a,b)}^{\mathbf F}$ 与 $Q_b^{\mathbf F}$。
下文用 $q_v^\theta(\mathbf F,\omega)$、
$h_{v,\theta}(\mathbf F,\omega)$ 和
$\mathcal A_{j,\theta}^{\mathbf F}(\omega)$ 表示这份唯一参考记录中的相应坐标。

定义 active 时间集合：

$$
\Lambda_v^{\mathbf F}([a,b);\omega)
=\{\theta\in[a,b)\mid
v\in\mathcal A_{\rho(v),\theta}^{\mathbf F}(\omega)\}.
$$

对 $\mathbf F\in\mathfrak F$ 与非空有限
$\Theta\subseteq\mathbb N$，定义该解释下的合法 batch 输入域：

$$
\mathsf{Adm}_{v,\Theta}^{\mathbf F}
=\left\{
\left(
q_v^{\theta+1}(\mathbf F,\omega),
\theta,
h_{v,\theta}(\mathbf F,\omega)
\right)_{\theta\in\Theta}
\ \middle|\
\begin{array}{l}
\mathbf L\in\mathbb N^{\mathsf I},\
a,b\in\mathbb N,\ a<b,\\
\omega\in\Omega_{\mathbf L,a,b}^{\mathbf F},\
\Theta\subseteq
\Lambda_v^{\mathbf F}([a,b);\omega)
\end{array}
\right\}.
$$

元组一律按 $\theta$ 递增排列。再令：

$$
\mathsf{BOut}_{v,\Theta}
=\prod_{\theta\in\Theta}\mathcal O_v.
$$

一次显式 batch query 写成
$\mathsf{Query}(v,\Theta,\xi)$，其中
$\xi=((s_\theta,\theta,h_\theta))_{\theta\in\Theta}$ 且
$\xi\in\mathsf{Adm}_{v,\Theta}^{\mathbf F}$。query 的语法不携带
$\mathbf F$；在解释
$\mathbf F$ 下，它的唯一精确回答由下列全函数给出：

$$
\begin{aligned}
\operatorname{BatchFull}_{v,\Theta}^{\mathbf F}
&:\mathsf{Adm}_{v,\Theta}^{\mathbf F}
\longrightarrow\mathsf{BOut}_{v,\Theta},\\
\operatorname{BatchFull}_{v,\Theta}^{\mathbf F}(\xi)
&=\left(F_v(s_\theta,\theta,h_\theta)\right)_{\theta\in\Theta}.
\end{aligned}
$$

这族等式是解释类上的逐坐标精确 batch 契约；具体 backend witness 还须实现
相应函数，本文不由此声称 batch 内部高效。

一个**外层阶段**
$\pi_r=(\mathsf{Ctrl}_r,\mathsf{Batch}_r)$ 有两个依次发生的部分。
$\mathsf{Ctrl}_r$ 是有限条因果合法的骨架作用及其值；
$\mathsf{Batch}_r$ 是随后一次确定的有限组 $\mathsf{Query}$。确定它时，每个
query 的输入及第 4.2 节中的全部事件前驱都必须已经由
$\omega$、较早阶段或 $\mathsf{Ctrl}_r$ 确定。batch 开始以后，本阶段不再求
新的控制值；回答及由它们产生的消息、输出只在阶段末一起进入
$\mathsf{Pub}_r$。

在第 $r$ 个阶段已经完成 $k$ 条控制作用的决策点，定义**可见 transcript**：

$$
\mathfrak t_{r,k}
=\left(
\omega,
(\pi_s,\mathsf{Pub}_s)_{s<r},
\mathsf{Ctrl}_{r,\le k}
\right),
$$

其中 $\mathsf{Ctrl}_{r,\le k}$ 同时记录已经发生的骨架作用及其值。一个
**因果外层策略** $\mathscr S$ 是从 $(a,b,\mathfrak t_{r,k})$ 到下一动作的
同一个确定函数；下一动作可以是求一个当前合法的骨架作用，或确定
$\mathsf{Batch}_r$ 并结束本阶段，或在阶段边界且目标 cut 已完成时停止。
$\mathbf F$ 不是它的自变量。因此两个解释若给出相同的
$(a,b,\mathfrak t_{r,k})$，$\mathscr S$ 必须给出相同动作；只有显式 query
返回不同回答以后，后续动作才可分岔。

query 以外的求值器只含 $\mathfrak B_\infty$ 的函数与确定的集合
bookkeeping。所以新的 $F_v$ 值，以及由它产生的消息或输出记录，只能经显式
query 回答进入 $\mathsf{Pub}_r$；不得由控制作用复现、内联或免费产生。
transcript 也不含 $\mathbf L$、见证 $x$、区间外输入或尚未回答的参考
$F_v$ 值。这些条件合起来就是本文的**因果且无 oracle**要求。

这里的 $r$ 是 heavy/control barrier 的外层阶段号，不是前置教材阶段化暴露
$E_n,H_n$ 的索引 $n$，也不是逻辑时间 $\theta$；三者之间没有预设相等关系。

固定 $\mathscr S$ 和回答解释 $\mathbf F$。若一次运行有限停止，记其阶段序列为：

$$
\Pi_{a,b}^{\mathbf F}(\omega)
=(\pi_1,\ldots,\pi_{N_{\mathbf F}(a,b,\omega)}).
$$

称这次运行 **exact**，若最终记录与 continuation 恰等于
$(\mathcal U_{x,[a,b)}^{\mathbf F},Q_b^{\mathbf F})$，包括越过右切面的新消息；
并且对每个 $v$，令 $m=m_{v,\mathbf F}(a,b,\omega)$ 后，全部 query 恰为：

$$
\mathsf{Query}(v,\Theta_{v,1},\xi_{v,1}),\ldots,
\mathsf{Query}(v,\Theta_{v,m},\xi_{v,m}).
$$

这里 $\xi_{v,k}$ 是相应参考坐标组成的元组，并且：

$$
\Lambda_v^{\mathbf F}([a,b);\omega)
=\bigsqcup_{k=1}^{m_{v,\mathbf F}(a,b,\omega)}
\Theta_{v,k}.
$$

因此 exact 运行既不能遗漏或重复 active 坐标，也不能额外探测
$F_v$。active 集为空时约定 $m_{v,\mathbf F}(a,b,\omega)=0$。

称解释类 $(\mathfrak B_\infty,\mathfrak F)$ 具有
**节点级时间批暴露**或**外层保块**，若量词顺序为：

$$
\begin{aligned}
\exists\mathscr S,\ B_{\mathrm{stage}}\in\mathbb N,\
(B_v)_{v\in V}\in\mathbb N^V,\quad
\forall\mathbf F\in\mathfrak F,
\forall\mathbf L\in\mathbb N^{\mathsf I},\\
\forall a,b\in\mathbb N\ (a<b),\
\forall\omega\in\Omega_{\mathbf L,a,b}^{\mathbf F}:
\quad
\begin{cases}
\text{上述运行 exact},\\
N_{\mathbf F}(a,b,\omega)\le B_{\mathrm{stage}},\\
m_{v,\mathbf F}(a,b,\omega)\le B_v
\quad(v\in V).
\end{cases}
\end{aligned}
$$

策略和界必须先于 $\mathbf F$ 选择；这些界也不能依赖 $\mathbf L$、区间宽度
$T$ 或实例 $\omega$。解释类可以携带明确的共同结构契约，但若
$\mathfrak F$ 只是单点集，这个全称量词本身不足以见证 black-box 隔离：
策略可能把唯一函数硬编码进去。此时还须另证策略只使用上述骨架与 query
指令集，或改用足以区分相关回答的非平凡解释类。

这个定义允许 $\Theta(T)$ 的顺序控制扫描，也允许同阶段 query 进入一个
packed API；它只保护昂贵作用的外层分块，不给出 work、span 或硬件性能结论。
相较于 TimedDAG chunk-prefill 教材对单输入流、对齐 cuts 的同类规则，这里对
所有 $a<b$ 和多端口长度向量同时量化，是一个 interval-uniform 强化。

### 10.3 真正的外层保块障碍

考虑延迟为 $1$ 的自环，其中状态满足：

$$
q^{\theta+1}=f_\theta(q^\theta),
$$

并且每个 $f_\theta$ 只能作为黑盒查询。若 $f_{\theta+1}$ 的有效输入必须等待 $q^{\theta+1}$，那么宽度为 $T$ 的逻辑时间区间含有长度为 $T$ 的状态依赖链。固定 $\Gamma=G^\dagger$ 时，$\mathcal S_\Gamma$ 只有一个分量；把它命名为宏节点不会缩短这条链。

这条线性链本身还不必破坏第 10.2 节的第一性能台阶：若 $f_\theta$ 只是廉价控制，扫描结束后才调用不再反馈到本块控制的昂贵作用，后者仍可按 node 打包。真正的障碍是随 $T$ 增长的 heavy/control 交替，例如：

$$
\text{heavy}_{\theta}
\longrightarrow \text{control}_{\theta+1}
\longrightarrow \text{heavy}_{\theta+1}
\longrightarrow \cdots .
$$

若较早昂贵输出经反馈消息以及由此引起的节点状态变化，改变较晚候选描述量和 route，外层就必须反复等待昂贵作用以后才能确定下一批参数，所需 batch 数可能增长为 $\Theta(T)$。任意 selector-history 递归只有在造成这种反馈时才成为外层保块的反例；顺序 history 扫描本身不是反例。

可以把严格分层类与一般反馈类的差别看成事件块之间的差别。这里“严格分层”指存在 $\ell:J\to\mathbb N$，使每条消息边 $a$ 都满足
$\ell(\rho(\operatorname{src}(a)))<\ell(\rho(\operatorname{dst}(a)))$；它是消息图无环的一个特例。记一个 control-only 事件块为 $\mathsf C$，同一节点的一批昂贵作用为 $\mathsf F$。其精确分块证明见 [[timed-dag-chunk-prefill-learning-note#9.4 严格分层类的节点级时间批暴露|TimedDAG chunk-prefill 教材第 9.4 节]]；这里只使用它允许的形状：

$$
\mathsf C_j\longrightarrow\mathsf F_v
\longrightarrow\mathsf C_k,
\qquad j,k\in J,\quad v\in\mathcal R_j,
\quad \ell(k)>\ell(j),
$$

所以每次经过昂贵作用，region 层次都严格上升。一般正时延反馈则可能沿逻辑时间展开为

$$
\mathsf C^{(1)}\longrightarrow\mathsf F^{(1)}
\longrightarrow\mathsf C^{(2)}\longrightarrow\mathsf F^{(2)}
\longrightarrow\cdots .
$$

后一条阶梯并不与定理 4 冲突：静态图可以有环，而任一 finite cut 中展开后的事件图仍是有限 DAG；返回边只是从较早时间指向较晚时间。要量化静态环可能多快返回，必须先给静态边补上来源与权重。

为了使“反馈时延”无歧义，给默认静态图 $G^\dagger$ 定义保留平行消息边的带标签多重图。令：

$$
\begin{aligned}
\widehat A^\dagger
={}&\{m_a=(\mathrm{message},a)\mid a\in A\}\\
&\sqcup\{r_{v,j}=(\mathrm{read},v,j)
\mid j\in J, v\in\mathcal R_j\}\\
&\sqcup\{c_{j,v}=(\mathrm{control},j,v)
\mid j\in J, v\in\mathcal R_j\}.
\end{aligned}
$$

三个标签使边标识符集合两两不交。定义其起点、终点与权重：

$$
\begin{array}{c|ccc}
e&\widehat{\operatorname{src}}(e)
&\widehat{\operatorname{dst}}(e)&w(e)\\ \hline
m_a&\operatorname{src}(a)&\operatorname{dst}(a)&\delta(a)\\
r_{v,j}&v&s_j&0\\
c_{j,v}&s_j&v&0
\end{array}
$$

于是：

$$
\widehat G^\dagger
=\left(
V^\dagger,\widehat A^\dagger,
\widehat{\operatorname{src}},
\widehat{\operatorname{dst}},w
\right)
$$

是一张有向带权多重图；忘掉边标识符与权重并合并平行边，恰得到式 (39) 的 $G^\dagger$。

对 $n\in\mathbb N_{>0}$，称
$\zeta=(e_1,\ldots,e_n)\in(\widehat A^\dagger)^n$ 为闭游走，若：

$$
\widehat{\operatorname{dst}}(e_r)
=\widehat{\operatorname{src}}(e_{r+1})
\quad(1\le r<n),
\qquad
\widehat{\operatorname{dst}}(e_n)
=\widehat{\operatorname{src}}(e_1).
$$

定义它的**消息时延**：

$$
d_{\mathrm{fb}}(\zeta)
=\sum_{r=1}^{n}w(e_r).
$$

它只累计原消息边的逻辑时延；read/control 边不是零时延消息。第 4.2 节中同 owner 的节点状态等待与 selector-history 等待在 dependency-complete 投影中由 owner 相等吸收，没有成为 $\widehat G^\dagger$ 的边，因此也不计入 $d_{\mathrm{fb}}$；这不是断言它们不耗逻辑时间。若换用另一张 $\Gamma$，必须另给保留来源标签的多重图，才能定义同类时延。

$d_{\mathrm{fb}}$ 不是完整事件路径的总时长；一条实际实现该闭游走的事件路径还可能含有上述同 owner 等待。当 $d_{\mathrm{fb}}(\zeta)>0$ 时，$T/d_{\mathrm{fb}}(\zeta)$ 因而只是潜在返回轮数的量级启发，不是拓扑定理。要接近这个轮数，闭游走必须在所考察输入上持续实例化，较早数值必须在函数意义上改变后续控制，而且这项依赖必须真正阻塞下一次昂贵 batch。具体运行的动态事件图 $\mathscr G^{\mathrm{ev}}_{x,<b}$ 的 owner 投影也可能只实现静态包络边的一部分；这张图按第 4.2 节保守记录函数作用依赖，本身也未必是最小的数值敏感图。零消息时延的 control 闭游走则不能用这个商估计逻辑时间返回周期。

因此，若某个与 $T$ 无关的常数 $R$ 保证至多发生 $R$ 轮有效返回，并且其余依赖可按第 10.2 节成批安排，就仍可能保持 $O(1)$ 的节点级时间批暴露；$O(\log T)$、$o(T)$ 等增长率也可作为以后研究的弱化 profile。这里的交替轮数只是寻找正类与反例的候选指标，不是本文已经证明的结构定理。要得到外层保块上界，还必须给出一个因果、满足 no-oracle 要求的统一调度 witness，不能只在完整运行结束后观察事件图。

### 10.4 在外层保块之上，何时还能得到 scan

递归并不必然只能顺序求值。取域 $\mathbb F$ 上的向量空间 $\mathcal Q$，记 $\operatorname{End}_{\mathbb F}(\mathcal Q)$ 为 $\mathcal Q$ 上线性算子的集合，并设 $q^\theta,c_\theta\in\mathcal Q$、$A_\theta\in\operatorname{End}_{\mathbb F}(\mathcal Q)$。若：

$$
q^{\theta+1}=A_\theta q^\theta+c_\theta,
$$

则一步可以表示为二元组 $(A_\theta,c_\theta)$，而相邻两步的复合是：

$$
(A_2,c_2)\circ(A_1,c_1)
=
(A_2A_1,A_2c_1+c_2).
\tag{40}
$$

式 (40) 对复合封闭且满足结合律，所以在具体线性代数计算模型下可以研究 parallel prefix scan。这里还必须在 scan 开始以前取得全部系数 $(A_\theta,c_\theta)$；若后一个系数要等待前缀状态或尚未查询的 $\operatorname{Full}$ 值，结合律本身并没有暴露可并行的输入序列。可能缩短控制 span 的正面 profile 还包括：

- 固定轮数展开；
- 具有紧凑结合摘要的递归；
- 已证明等价的 causal-bulk kernel；

与这些 low-span witness 不同，“顺序控制扫描后，把不再影响后续控制的昂贵节点作用按 node packed”只证明第 10.2 节的外层保块。它的额外前提正是：被推迟的节点作用不能经反馈消息及其随后引起的状态变化改变本块后续 selector。只知道“它们都在同一个 $C\in\mathcal S_\Gamma$”远远不够。

### 10.5 固定 $\Gamma$ 的 SCC profile 应分别登记什么

对固定 dependency-complete 图 $\Gamma$ 的每个候选分量 $C\in\mathcal S_\Gamma$，应分别登记：

| 项目 | 要回答的问题 |
| --- | --- |
| reference semantics | 是否等于第 2 节的微观递归？ |
| finite-cut progress | 对哪些 sealed cuts 必然返回？ |
| cost profile | 哪些作用是控制，哪些节点作用是昂贵计算？ |
| temporal batch exposure | 外层 heavy/control 阶段需要多少轮；每个节点的昂贵时间事件需要多少批；二者是否与 $T$ 无关？ |
| work | 总 primitive 数怎样随有限时间区间的宽度增长？ |
| control span | 控制扫描的最长依赖链怎样增长？是否有代数 scan witness？ |
| memory | continuation、临时量和批量张量多大？ |
| communication | 跨 $\mathcal S_\Gamma$ 分量的逐边消息与 seal 有多少？ |
| lowering witness | sequential loop、packed loop、scan、fixed unfold 还是专用 kernel？ |

`sequential fallback` 只见证 correctness；`packed API` 只有显式满足第 10.2 节的分解与一致界时才见证外层保块，仍不见证其内部 span 或硬件表现。

## 11. 已证明结果、开放问题与练习

### 11.1 本文已经证明

1. 任意有限 cut 的直接记录存在、唯一且结构有限（定理 1）；
2. 不同 cuts 构成相容族，相同输入前缀给出相同 cut trace（推论 2、定理 3）；
3. 每个 finite cut 的函数作用事件图是有限 DAG（定理 4）；
4. seal 推出纤维与候选集合关闭，节点完成沿正时延边推进 seal（引理 5、定理 6、引理 7）；
5. 获得 source seal 的任意有限 cut 都有有限的顺序推进结构（定理 8）；
6. 节点状态、selector-history、绝对时间与跨界消息构成充分 continuation（定理 9）；
7. 任意完整时间切分满足 cut composition（定理 10）；
8. message condensation graph 是 DAG；在 SCC-local region profile 下，可以按其拓扑序精确构造一个 cut（定理 11--12）；
9. owner 投影把每次运行的直接事件依赖健全地抽象到式 (39) 的 dependency-complete 静态图（命题 13）。

### 11.2 本文没有证明

- 零时延边、同刻代数环或 fixed-point solver 的语义；
- 允许无限节点、无限同刻 firing、无限 batch 或隐藏 microstep 后的局部有限性；
- 任意共享可变状态或来源未声明的公共 context；
- 任意 region 下按 message SCC 独立求值；
- $\mathcal S_\Gamma$ 中任意分量的通用多端口 runtime；
- $\mathcal S_\Gamma$ 中任意分量都具有节点级时间批暴露；
- 任意具有这种批量暴露的 $\mathcal S_\Gamma$ 分量还具有低 span；
- 图结构本身推出某种硬件利用率。

### 11.3 建议练习

1. 对第 3.1 节的自环手算 $\mathcal T_{x,<3}$、$W_1,W_2,W_3$，检查式 (32)。
2. 对第 3.2 节的两节点环分别在 cut $2$ 与 cut $5$ 停止，写出全部跨界消息。
3. 不看证明，重新用 $\delta(a)>0$ 证明定理 4；指出证明的哪一步在 $\delta(a)=0$ 时失效。
4. 构造一个 $q_v^b$ 全部相同但 $y_j^b$ 不同的例子，说明只保存节点状态为何不充分。
5. 构造两个输入历史，它们在 $[0,b)$ 相同、在 $[b,\infty)$ 不同，并直接验证定理 3。
6. 对第 9.4 节的三节点例子，分别画出消息图 $G$、区域商图 $(J,Q_\rho)$、静态图 $G^\dagger$ 和一次 finite-cut 事件图；计算前三张图的 SCC，验证 dependency-complete 条件，并求闭游走 $u\to v\to w\to s_A\to u$ 的消息时延。
7. 给出一种递归摘要及其结合复合律；再给出一种没有紧凑闭合摘要的黑盒递归。

## 12. 下一研究台阶

本文已经把“正时延有环 Graph 是否具有无歧义 finite-cut 语义”闭合为肯定答案。下一步不是立即加入零时延，也不是直接要求低 span，而是从固定 $\Gamma$ 的 $\mathcal S_\Gamma$ 中选择具体子类，寻找 exact 且具有节点级时间批暴露的外层 lowering。这里允许控制、selector 与 selector-history 顺序扫描；第一目标只是证明外层没有把昂贵节点作用拆成随推进区间宽度增长的许多批。

优先顺序应当是：

1. 为 $C\in\mathcal S_\Gamma$ 定义保留 edge identity 的输入、输出与 continuation 投影，并先实现、对拍 exact sequential fallback；
2. 固定 control/heavy 成本 profile，寻找阶段数与每节点 batch 数一致有界的子类；对每个子类同时给出正面 witness 和造成 $\Theta(T)$ 次交替的最小反例；
3. 再为具有 affine/associative、固定轮展开或 causal-bulk 结构的子类研究低-span lowering；
4. 最后讨论 kernel 内部实现与硬件映射。

零时延 SCC、一般 solver、偏序时间、backpressure 和任意 partial/divergent local function 继续延期。

## 附录 S：系统语言与本文数学对象的对应

本附录只翻译词汇，不增加正文定理前提。

> [!info]- S.1　finite cut、open execution 与 termination
> **finite cut** 对应 $[0,b)$ 及其记录 $\mathcal T_{x,<b}$。**open execution** 对应相容族 $(\mathcal T_{x,<b})_{b\in\mathbb N}$。
>
> **global termination / quiescence** 表示存在某个 $b_0$，以后不再产生新事件或消息。第 3.1 节没有这个性质，但每个 finite cut 仍由定理 1 有限且唯一。
>
> **finite-cut productivity** 对应定理 8：获得足够 source seal 后，所要求的有限切面能由有限个抽象函数作用完成。它不等于全局 termination。

> [!info]- S.2　visibility、publication、seal 与 closure
> 当前已“可见或公开”的外部输入记录和内部消息分别对应 $E^\circ$ 与 $H$ 的成员关系；若另行跟踪已交付外部输出，则对应第 6.1 节可选集合 $Z^\circ$ 的成员关系。一条消息可以已经由源事件产生但尚未进入 $H$；正文要求它不能反过来先于源事件公开。
>
> 本文有意用“是否属于相应当前集合”这一个成员谓词抽象 visibility 与 publication。若某个实现还要区分 produced、committed、published、consumer-visible 或 acknowledged，就必须为这些阶段分别增加集合及其单调包含关系；不能把这种更细状态偷偷塞回同一个 $H$。
>
> **seal** 对应式 (25) 的集合覆盖命题。**closure** 对应式 (27) 的纤维等式或定理 6 的候选集合等式。seal 是推出 closure 的充分信息，不是同一个对象。
>
> **queue empty** 只描述某个当前编码中没有元素，不能证明式 (25) 中关于全部未来的全称命题。

> [!info]- S.3　state adoption、completed、hard watermark 与 no-backdating
> **state adoption / state commit** 对应事件 $U_{v,\theta}$ 以及式 (14)：在 selector 已经给出 active set 以后，节点状态坐标由 $q_v^\theta$ 变成唯一的 $q_v^{\theta+1}$。它不是把任意临时张量写入共享存储。
>
> 节点 **completed to $r$** 对应式 (28) 的复合谓词：输入纤维已经关闭，并且所有实际较早节点事件已经完成。本文的 $(v,\theta)\in\mathsf{Done}$ 还要求 active $\operatorname{Full}$ 所产生的每条内部消息已经属于 $H$；这比前置 TimedDAG 教材中允许消息稍后公开的 $\operatorname{Completed}_n$ 更强。
>
> 输出端口在 cut $b$ 的 **hard output watermark** 表示：以后不可能再产生输出时间小于 $b$ 的新记录。定理 8 的按时间递增完成给出这一事实。
>
> **no-backdating** 对应推论 2 与定理 3：合法未来扩展和继续不能改变 $\mathcal T_{x,<b}$。它不是“实现通常不会这样做”的经验约定。

> [!info]- S.4　in-flight、continuation、checkpoint 与 resume
> **in-flight message** 在 cut $b$ 对应式 (31) 的 $W_b$；它已经产生，但逻辑到达时间位于切面右侧。
>
> **continuation** 对应式 (33) 的 $Q_b$。**checkpoint** 是 $Q_b$ 的无损编码；若保存函数和读取函数分别是 $\operatorname{save},\operatorname{load}$，最低要求是：
> $$
> \operatorname{load}(\operatorname{save}(Q_b))=Q_b.
> $$
>
> **resume** 对应式 (34)；**chunk composition** 对应式 (36)。外部交付的 exactly-once 语义还需要输出记录或交付账本，不由 $Q_b$ 自动提供。

> [!info]- S.5　structural SCC、macro 与 dependency-complete
> **message structural SCC** 对应式 (37) 的 $\sim_G$ 等价类。**condensation DAG** 只给出这些等价类之间的消息方向。
>
> **macro node** 若采用 message SCC，必须满足式 (38) 或另证 selector/control/state 依赖没有跨边界。否则 message SCC 只是图论集合，不是语义封闭模块。
>
> **dependency-complete static graph** 的正式定义见第 9.4 节：每次运行的直接事件边经 owner 投影后，都必须留在同一 owner 或落到一条静态边上。固定这样的 $\Gamma$ 后，其宏候选是明确的 $\mathcal S_\Gamma$；本文默认 $\Gamma=G^\dagger$。式 (39) 给出这个安全但不必最小的构造，命题 13 证明其 dependency-complete。它把 selector 的可能读取、控制和 history owner 纳入静态边界，但这些附加边不是普通正时延消息；它也不是 seal 或 closure 的在线证书，$\mathcal S_\Gamma$ 中的分量不自动获得宏 runtime 或性能保证。

> [!info]- S.6　correctness、外层保块、work 与 span
> **exact / correctness** 表示所得记录等于本文指定的完整记录或明确投影。**cost profile** 是对控制与昂贵作用的附加分类。**节点级时间批暴露 / 外层保块**对应第 10.2 节同一个 action-level transcript 策略：它只经显式 query 取得 $\operatorname{Full}$ 值，并对解释类 $\mathfrak F$、输入长度、任意区间及合法实例统一 exact；$B_{\mathrm{stage}},B_v$ 也按相同量词一致有界。外层阶段号 $r$ 不等于阶段化暴露索引 $n$ 或逻辑时间 $\theta$。
>
> 控制可以顺序扫描，交错信号也可在同一时间纤维汇合；只有必须反复等待“昂贵作用—后续控制—昂贵作用”时，batch 数才可能随 $T$ 增长。`packed API` 只是若干已定义 batch 的共同调用边界。**work/span** 对应第 10 节开头的成本量，式 (40) 是一种 scan witness；硬件性能还需另外的设备成本模型与测量。

> [!info]- S.7　参数共享与状态共享
> 多个节点函数使用同一个固定参数，对应这些函数具有同一个参数坐标。在一次前向语义中该坐标不被事件改写，所以不会增加 finite-cut 事件依赖边。在损失是可微标量、并采用通常的反向模式微分时，共享参数的总梯度是各使用点对该参数贡献的和；不满足这些微分前提时，本文不使用这句话定义“梯度”。
>
> 多个节点读写同一可变状态则会产生额外的版本与次序依赖。本文只允许每个 $q_v$ 由节点 $v$ 持有、每个 $y_j$ 由 region selector $j$ 持有；若放宽，必须重定义 continuation 和固定 $\Gamma$ 及其 $\mathcal S_\Gamma$。

## 可选相关材料

- [[timed-dag-region-selector-learning-note|前置：TimedDAG 的完整数学语义]]；
- [[timed-dag-chunk-prefill-learning-note|节点级时间批暴露在空间 DAG 上的正例]]；
- [[adaptive-routing-prefill-lower-bound|黑盒自适应路由为什么一般不能自动低 span]]；
- [[current-mainline|TIDE 当前 Graph 线入口]]。

这些文档中的系统接口或更一般宏契约不会反向改写本文定义。若以后推广本文，必须明确指出改变了哪个函数类型、状态 owner、时延条件或 cut 坐标。
