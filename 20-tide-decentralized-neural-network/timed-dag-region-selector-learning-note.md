---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-04
tags:
  - tide
  - timed-dag
  - region
  - selector
  - logical-time
  - mathematics
  - learning-note
---

# TimedDAG：从多输入、多输出到 region 与 selector 的完整数学学习笔记

> [!summary] 阅读约定
> 本文从有限集合、函数、自然数和数学归纳法开始，独立定义一套包含多个输入端口、多个输出端口、逻辑时间、消息、完整输入桶、seal、region 与 selector 的 TimedDAG 候选语义。阅读本文不要求先读另一份 TimedDAG 笔记。
>
> 正文只让已经定义的数学对象承担推理。`region`、`selector`、`SD`、`BO`、`prefill` 等计算机系统词汇的解释统一放在文末附录 S；删除整个附录以后，正文的定义、引理和证明目标仍然完整。
>
> 第一次只读第 0 节并完成四道题，然后停止。第二次只读第 1 节，确认每个符号的定义域；第三次只读第 2 节，手算一次选择；第四次才读第 3--4.5 节并独立证明候选集合关闭引理。后面的内容只在准备相应证明时阅读。

本文研究一个有限模型：

> 不同输入位置产生的量可以在同一节点、同一逻辑时间汇合；同一组中的多个节点可以在这个逻辑时间共同接受一次选择；只有在所有同刻消息都已经确定以后，选择与节点状态变化才能发生。

模型从一开始就允许有限多个外部输入端口和有限多个外部输出端口。第 0 节为了只展示一个困难，暂时只画出两个输入位置；第 1 节的主定义不作单输入或单输出限制。

本文同时区分三种对象：

1. **固定空间图**：哪些节点之间允许发送值；
2. **区域划分**：哪些节点在同一逻辑时间共同接受选择；
3. **事件图**：给定一次具体输入后，一组函数作用及足以保证正确求值的先后关系。

区域不是固定空间图中的新节点。本文也不要求把区域收缩后所得的图无环。固定空间图暂时仍然是有限 DAG，每条边暂时仍然具有正整数逻辑时延。

本文首先定义一般情形下唯一正确的计算。区域结构何时允许一次向前计算很大的逻辑时间区间，是以后附加条件下的定理，不是当前合法性的前提。

## 0. 第一次只看一个最小例子

记：

$$
\mathbb N=\{0,1,2,\ldots\}.
$$

先只看某一个外部输入端口上的两个位置 $0,1$，并暂时把这个端口的逻辑时间函数简写为 $\iota$。两个位置的逻辑注入时间分别为：

$$
\iota(0)=0,
\qquad
\iota(1)=1.
$$

位置 $0$ 产生的一个量经过总时延 $5$ 到达节点 $a$；位置 $1$ 产生的一个量经过总时延 $4$ 到达节点 $b$。于是两个量的逻辑到达时间都是：

$$
0+5=1+4=5.
$$

把到达 $a,b$ 的两个量分别记为 $z_a,z_b$，则完整输入桶为：

$$
B_{a,5}=\{z_a\},
\qquad
B_{b,5}=\{z_b\}.
$$

现在把两个节点放进同一个固定集合：

$$
\mathcal R=\{a,b\}.
$$

因为两个桶都非空，逻辑时间 $5$ 的候选节点集合是：

$$
\mathcal C_{\mathcal R,5}=\{a,b\}.
$$

假设两个节点分别由自己的完整桶算出一个数：

$$
d_{a,5}=2,
\qquad
d_{b,5}=7.
$$

再定义一个函数：它从候选节点中选择 $d$ 最大的一个。于是：

$$
\operatorname{Select}_{\mathcal R}
\left(
5,\{(a,2),(b,7)\}
\right)
=\{b\}.
$$

这里的 $\{(a,2),(b,7)\}$ 是函数 $a\mapsto2,\ b\mapsto7$ 的图；它的两个坐标由节点标记，不表示先把 $a$ 再把 $b$ 交给函数。

把被选节点集合记为：

$$
\mathcal A_{\mathcal R,5}=\{b\}.
$$

这次选择以后，仍然是节点 $b$ 读取自己的状态、执行自己的函数、沿自己的固定出边发送消息，并且可以向与 $b$ 相连的一个或多个外部输出端口给值。集合 $\mathcal R$ 本身不接收或发送边消息，也不产生外部输出。

### 0.1 为什么不能看见一个消息就立刻选择

假设机器先看见 $z_a$，过了一段现实时间才看见 $z_b$。在只看见 $z_a$ 时，机器暂时看到的候选集合是 $\{a\}$，但完整候选集合仍然是 $\{a,b\}$。

因此不能立即选择 $a$。必须先得到一个可以证明的条件：

$$
\text{通向 }a,b\text{ 的全部入边都不会再出现逻辑到达时间为 }5\text{ 的消息。}
$$

后文用严格大于 $5$ 的 seal 表达这个条件。等待的不是固定秒数，而是等待这个全称命题成立。

如果再有节点 $c\in\mathcal R$，并且它最终满足：

$$
B_{c,5}=\varnothing,
$$

仍然需要证明通向 $c$ 的消息不会再到来，才能确定 $c$ 不属于候选集合。证明“没有消息”与收集已经出现的消息同样重要。

### 0.2 同一节点还可以接收多个同刻消息

若另一个例子中有两条消息 $m_0,m_1$ 都在逻辑时间 $5$ 到达同一节点 $v$，则：

$$
B_{v,5}=\{m_0,m_1\}.
$$

节点 $v$ 只作为一个候选出现，并从整个集合 $\{m_0,m_1\}$ 算出一个描述量。不能先用 $\{m_0\}$ 选择或更新一次，再用 $\{m_1\}$ 选择或更新一次。

所以本文同时允许：

- 不同输入位置的消息在同一节点、同一逻辑时间汇合；
- 不同节点在同一 region、同一逻辑时间共同选择。

### 0.3 第一次阅读的四道题

1. 位置 $0$ 与位置 $1$ 的量由机器以相反次序看见，会不会改变它们两个等式 $0+5=1+4=5$？
2. 只看见 $z_a$、但关于 $b$ 的 seal 尚未越过 $5$ 时，能否确定候选集合是 $\{a\}$？
3. 节点 $c$ 的桶最终为空时，为什么仍然需要等待关于 $c$ 的 seal？
4. selector 选出 $b$ 后，是 region 发送消息和产生外部输出，还是 $b$ 沿自己的出边发送并向自己的输出端口给值？

答案是：不会；不能；因为暂时没看见消息不能证明以后不会出现同刻消息；由节点 $b$ 发送和给出外部输出。

第一次阅读到这里即可停止。

## 1. 固定数据：节点、边、输入输出端口与逻辑时间

### 1.1 数、有限集合与函数族

定义：

$$
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $L\in\mathbb N_{>0}$，定义：

$$
[L]=\{0,1,\ldots,L-1\}.
$$

对 $c,b\in\mathbb N$ 且 $c\le b$，定义：

$$
[c,b)
=
\{\theta\in\mathbb N\mid c\le\theta<b\}.
$$

对任意集合 $X$，用：

$$
\mathcal P_{\mathrm{fin}}(X)
$$

表示 $X$ 的全部有限子集所成的集合。对集合 $E,Y$，用 $Y^E$ 表示全部函数 $E\to Y$ 所成的集合。

### 1.2 固定空间图以及输入、输出端口

定义五元组：

$$
G=(V,A,\alpha,\beta,\delta).
\tag{1}
$$

各分量如下：

- $V$ 是有限非空节点集合；
- $A$ 是有限边集合；
- $\alpha:A\to V$ 给出边的起点；
- $\beta:A\to V$ 给出边的终点；
- $\delta:A\to\mathbb N_{>0}$ 给出边的逻辑时延。

一条边 $a$ 的方向是：

$$
\alpha(a)\longrightarrow\beta(a).
$$

即使两条边起点和终点相同，只要它们是 $A$ 中两个不同元素，它们仍是两条不同的边。

对节点 $v$，定义：

$$
\operatorname{In}(v)
=
\{a\in A\mid\beta(a)=v\},
$$

$$
\operatorname{Out}(v)
=
\{a\in A\mid\alpha(a)=v\}.
$$

对 $k\in\mathbb N_{>0}$，称边序列 $(a_1,\ldots,a_k)$ 是一条有向路径，当且仅当：

$$
\beta(a_\ell)=\alpha(a_{\ell+1})
\qquad
(1\le \ell<k).
$$

这条路径的起点是 $\alpha(a_1)$，终点是 $\beta(a_k)$；若二者分别为 $u,v$，就称它是从 $u$ 到 $v$ 的有向路径。

若还有：

$$
\beta(a_k)=\alpha(a_1),
$$

则称这条非空路径是有向环。本文称 $G$ 是 DAG，当且仅当 $G$ 有限且不存在有向环。

再给定两个有限非空集合：

$$
\mathsf I=\text{外部输入端口集合},
\qquad
\mathsf O=\text{外部输出端口集合},
$$

以及两个函数：

$$
\gamma:\mathsf I\to V,
\qquad
\varepsilon:\mathsf O\to V.
$$

$\gamma(i)$ 是输入端口 $i$ 注入值的节点；$\varepsilon(o)$ 是可以向输出端口 $o$ 给值的节点。对每个节点定义：

$$
\operatorname{InPort}(v)
=
\{i\in\mathsf I\mid\gamma(i)=v\},
$$

$$
\operatorname{OutPort}(v)
=
\{o\in\mathsf O\mid\varepsilon(o)=v\}.
$$

端口不是 $V$ 中的额外节点。输入端口只提供外部输入原子；输出端口只记录节点给出的值，不再向图内发送消息。

本文暂时要求：

1. $G$ 没有有向环；
2. 对每个 $v\in V$，至少存在一个 $i\in\mathsf I$，使得 $v=\gamma(i)$，或者存在一条从 $\gamma(i)$ 到 $v$ 的有向路径。

第二条只排除永远不可能收到任何外部因果来源的多余节点。它允许多个输入端口进入同一节点，也允许一个输入节点同时具有图内入边；输入节点不再是唯一的。

这里的 DAG 只描述节点和边。区域划分尚未出现。

### 1.3 region 是节点集合的划分

取一个有限非空集合 $J$，并给定满射：

$$
\rho:V\to J.
\tag{2}
$$

对每个 $j\in J$，定义：

$$
\mathcal R_j
=
\{v\in V\mid\rho(v)=j\}.
\tag{3}
$$

于是：

$$
V=\bigcup_{j\in J}\mathcal R_j,
$$

并且：

$$
j\ne j'
\Longrightarrow
\mathcal R_j\cap\mathcal R_{j'}=\varnothing.
$$

所以每个节点恰好属于一个 $\mathcal R_j$。正文把 $\mathcal R_j$ 称为一个 **region**，把 $\rho$ 称为区域归属函数。

式 (2)--(3) 没有在 $J$ 上定义边。本文允许一条节点路径离开一个 region 后，在更大的逻辑时间重新进入同一个 region；也允许同一 region 包含一条路径上前后位置不同的节点。

### 1.4 多个输入端口、输入位置与逻辑注入时间

固定一个非空值集合 $P$。对每个输入端口 $i\in\mathsf I$，给定正整数 $L_i$，并定义这个端口的位置集合：

$$
[L_i]=\{0,1,\ldots,L_i-1\}.
$$

一次多端口输入是函数族：

$$
x=(x_i)_{i\in\mathsf I},
\qquad
x_i:[L_i]\to P.
$$

再对每个 $i\in\mathsf I$ 给定严格递增函数：

$$
\iota_i:[L_i]\to\mathbb N,
\qquad
t<t'
\Longrightarrow
\iota_i(t)<\iota_i(t').
\tag{4}
$$

输入位置由二元组 $(i,t)$ 唯一确定；它携带值 $x_i(t)$，并在逻辑时间 $\iota_i(t)$ 注入节点 $\gamma(i)$。这个时间是自然数标签，不表示现实中经过了多少秒。

不同端口之间不要求 $\iota_i(t)$ 彼此不同。因此，多个端口完全可以在同一个逻辑时间向同一节点或不同节点注入值。

### 1.5 消息与逻辑到达时间

一条候选消息是三元组：

$$
m=(\theta,a,y)
\in
\mathbb N\times A\times P.
\tag{5}
$$

定义：

$$
\operatorname{send}(m)=\theta,
\qquad
\operatorname{edge}(m)=a,
\qquad
\operatorname{value}(m)=y,
$$

$$
\operatorname{sender}(m)=\alpha(a),
\qquad
\operatorname{receiver}(m)=\beta(a),
$$

$$
\operatorname{arrival}(m)
=
\theta+\delta(a).
\tag{6}
$$

式 (6) 中的 arrival 仍然是逻辑时间。它不是消息在某台机器中变为可见的现实时间。

若还想为每个节点指定一个非负整数逻辑计算耗时 $c(v)$，并为每条边指定一个非负整数逻辑传递耗时 $d(a)$，只需在固定数据中取：

$$
\delta(a)=c(\alpha(a))+d(a),
\qquad
\delta(a)>0.
$$

后文只使用总时延 $\delta(a)$，所以无需改变桶、selector 或解释器定义。这里仍然只是在定义逻辑时间差，不是在测量现实计算耗时。

本文暂时规定：同一节点在同一逻辑时间沿同一出边至多产生一条消息。因此消息集合 $M$ 必须满足：

$$
(\theta,a,y)\in M,
\quad
(\theta,a,y')\in M
\Longrightarrow
y=y'.
\tag{7}
$$

### 1.6 输入原子与完整桶

对每个节点 $v$，定义外部输入原子集合：

$$
\mathsf{InAtom}_v
=
\{(0,i,t,y)\mid
i\in\operatorname{InPort}(v),\ t\in[L_i],\ y\in P\}.
$$

对每个节点 $v$，定义边消息原子集合：

$$
\mathsf{MsgAtom}_v
=
\{(1,m)\mid\operatorname{receiver}(m)=v\}.
$$

开头的 $0,1$ 只用于区分两种原子。定义：

$$
\mathsf{Atom}_v
=
\mathsf{InAtom}_v\cup\mathsf{MsgAtom}_v.
$$

定义原子的逻辑到达时间：

$$
\operatorname{atime}(0,i,t,y)=\iota_i(t),
$$

$$
\operatorname{atime}(1,m)=\operatorname{arrival}(m).
$$

节点 $v$ 在时间 $\theta$ 的输入桶是满足下式的有限集合 $B\subseteq\mathsf{Atom}_v$：

$$
z\in B
\Longrightarrow
\operatorname{atime}(z)=\theta.
$$

一次具体输入的**完整输入桶**记为 $B_{v,\theta}$：它包含这次完整计算中到达 $(v,\theta)$ 的全部外部输入原子和边消息原子。

同一桶是集合，没有先后次序。完整桶可以为空；只有非空桶才产生候选节点事件。

例如，取两个输入端口 $i_0,i_1$，令：

$$
\gamma(i_0)=\gamma(i_1)=v,
\qquad
L_{i_0}=L_{i_1}=1,
\qquad
\iota_{i_0}(0)=\iota_{i_1}(0)=5.
$$

若时间 $5$ 没有图内消息到达 $v$，则：

$$
B_{v,5}
=
\{
(0,i_0,0,x_{i_0}(0)),
(0,i_1,0,x_{i_1}(0))
\}.
$$

即使两个值相等，端口坐标不同也使它们是两个不同的输入原子。

第二次阅读到这里即可停止。此时只需能指出：一个输入原子由哪个端口、哪个位置、哪个值和哪个逻辑时间确定。

## 2. 节点函数、候选集合与 selector

### 2.1 节点状态与本地内容

对每个节点 $v\in V$，给定：

- 非空状态集合 $S_v$；
- 初始状态 $q_v^0\in S_v$；
- 非空本地内容集合 $X_v$；
- 非空选择描述量集合 $D_v$；
- 非空观察值集合 $R_v$，以及一个指定元素 $r_v^\circ\in R_v$。

给定全函数：

$$
\operatorname{Aggregate}_v:
\mathbb N
\times
\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)
\to X_v.
\tag{8}
$$

对非空完整桶定义：

$$
h_{v,\theta}
=
\operatorname{Aggregate}_v(\theta,B_{v,\theta}).
\tag{9}
$$

如果节点需要区分不同入边，式 (8) 可以读取消息原子中的边 $a$；若要区分外部来源，也可以读取输入原子中的端口 $i$。它不能读取这些原子被机器看见的先后次序。

### 2.2 候选新状态

给定全函数：

$$
\operatorname{Update}_v:
S_v\times\mathbb N\times X_v
\to S_v.
\tag{10}
$$

设 $q^-_{v,\theta}$ 是节点处理逻辑时间 $\theta$ 以前全部更小时间事件后保留的状态。定义候选新状态：

$$
\widetilde q_{v,\theta}
=
\operatorname{Update}_v
\left(q^-_{v,\theta},\theta,h_{v,\theta}\right).
\tag{11}
$$

式 (11) 只定义了一个 $S_v$ 中的值。它不表示后续事件已经可以读取这个值。第 2.7 节才决定它是否成为当前事件后的状态。

### 2.3 content、pre 与 post 描述量

给定三个全函数：

$$
\operatorname{Read}^{\mathrm{content}}_v:
\mathbb N\times X_v\to D_v,
$$

$$
\operatorname{Read}^{\mathrm{pre}}_v:
S_v\times\mathbb N\times X_v\to D_v,
$$

$$
\operatorname{Read}^{\mathrm{post}}_v:
S_v\times\mathbb N\times X_v\to D_v.
$$

分别定义：

$$
d^{\mathrm{content}}_{v,\theta}
=
\operatorname{Read}^{\mathrm{content}}_v
(\theta,h_{v,\theta}),
\tag{12}
$$

$$
d^{\mathrm{pre}}_{v,\theta}
=
\operatorname{Read}^{\mathrm{pre}}_v
(q^-_{v,\theta},\theta,h_{v,\theta}),
\tag{13}
$$

$$
d^{\mathrm{post}}_{v,\theta}
=
\operatorname{Read}^{\mathrm{post}}_v
(\widetilde q_{v,\theta},\theta,h_{v,\theta}).
\tag{14}
$$

pre 与 post 一般不是同一个函数输入。如果 $\operatorname{Update}_v$ 会压缩或遗忘旧状态，$\widetilde q$ 甚至未必能够恢复 $q^-$。

### 2.4 同一 region、同一时间的候选集合

固定 $j\in J$ 和 $\theta\in\mathbb N$。定义：

$$
\mathcal C_{j,\theta}
=
\{v\in\mathcal R_j\mid B_{v,\theta}\ne\varnothing\}.
\tag{15}
$$

这是 region $\mathcal R_j$ 在逻辑时间 $\theta$ 的完整候选集合。

若一个节点的桶含有多条消息，它仍然只在式 (15) 中出现一次。若一个节点的桶为空，它不属于候选集合。

### 2.5 selector 的固定输入类型

对每个 $j\in J$，固定：

$$
\tau_j
\in
\{\mathrm{content},\mathrm{pre},\mathrm{post}\}.
$$

对 $v\in\mathcal R_j$，简写：

$$
d_{v,\theta}=d^{\tau_j}_{v,\theta}.
\tag{16}
$$

再固定整数：

$$
1\le K_j\le|\mathcal R_j|.
$$

对每个 $C\subseteq\mathcal R_j$，定义合法激活集合所成的集合：

$$
\mathsf{Act}_{j,C}
=
\{A'\subseteq C\mid |A'|\le K_j\}.
\tag{17}
$$

### 2.6 selector 是完整候选族上的函数

对每个 $j\in J$ 和每个子集 $C\subseteq\mathcal R_j$，给定全函数：

$$
\operatorname{Select}_{j,C}:
\mathbb N
\times
\prod_{v\in C}D_v
\to
\mathsf{Act}_{j,C}.
\tag{18}
$$

$\prod_{v\in C}D_v$ 的元素写成 $(d_v)_{v\in C}$。每个坐标由节点 $v$ 标记，所以这个输入没有机器到达顺序。

令 $C=\mathcal C_{j,\theta}$。当 $C\ne\varnothing$ 时，定义 active set：

$$
\mathcal A_{j,\theta}
=
\operatorname{Select}_{j,C}
\left(
\theta,
(d_{v,\theta})_{v\in C}
\right).
\tag{19}
$$

由值域可知：

$$
\mathcal A_{j,\theta}
\subseteq
\mathcal C_{j,\theta},
$$

$$
|\mathcal A_{j,\theta}|\le K_j.
$$

若 $C=\varnothing$，规定：

$$
\mathcal A_{j,\theta}=\varnothing,
$$

并且该 $(j,\theta)$ 不产生选择事件。

式 (18) 没有规定 selector 必须怎样选择。Top-$K$ 打分只是它的一个可能实例。若使用分数并可能出现相等值，必须事先在 $V$ 上给定一个固定全序来打破平局，不能让机器中先完成的节点获胜。

### 2.7 SD 与 BO 决定哪些候选状态被采用

对每个 region 固定：

$$
\pi_j\in\{\mathrm{SD},\mathrm{BO}\}.
$$

定义状态采用集合：

$$
\mathcal O_{j,\theta}
=
\begin{cases}
\mathcal A_{j,\theta},&\pi_j=\mathrm{SD},\\
\mathcal C_{j,\theta},&\pi_j=\mathrm{BO}.
\end{cases}
\tag{20}
$$

对 $v\in\mathcal C_{j,\theta}$，定义两个指示量：

$$
\chi_{v,\theta}
=
\begin{cases}
1,&v\in\mathcal A_{j,\theta},\\
0,&v\notin\mathcal A_{j,\theta},
\end{cases}
$$

$$
\omega_{v,\theta}
=
\begin{cases}
1,&v\in\mathcal O_{j,\theta},\\
0,&v\notin\mathcal O_{j,\theta}.
\end{cases}
\tag{21}
$$

$\chi$ 决定是否执行完整节点计算；$\omega$ 决定是否采用候选新状态。

定义当前事件后的状态：

$$
q^+_{v,\theta}
=
\begin{cases}
\widetilde q_{v,\theta},&\omega_{v,\theta}=1,\\
q^-_{v,\theta},&\omega_{v,\theta}=0.
\end{cases}
\tag{22}
$$

因此：

- SD 中只有 active candidates 采用候选新状态；
- BO 中全部 candidates 采用候选新状态；
- 两者都只有 active candidates 执行完整计算。

### 2.8 完整节点计算、图内消息与外部输出

取新符号 $\bot\notin P$，并定义：

$$
P_\bot=P\cup\{\bot\}.
$$

一条候选外部输出记录是三元组：

$$
z=(\theta,o,y)
\in
\mathbb N\times\mathsf O\times P.
$$

定义：

$$
\operatorname{otime}(z)=\theta,
\qquad
\operatorname{oport}(z)=o,
\qquad
\operatorname{ovalue}(z)=y.
$$

对每个节点给定全函数：

$$
\operatorname{Full}_v:
S_v\times\mathbb N\times X_v
\to
(P_\bot)^{\operatorname{Out}(v)}
\times
(P_\bot)^{\operatorname{OutPort}(v)}
\times R_v.
\tag{23}
$$

定义两个全空函数：

$$
\bot_v^A(a)=\bot
\qquad
(a\in\operatorname{Out}(v)),
$$

$$
\bot_v^O(o)=\bot
\qquad
(o\in\operatorname{OutPort}(v)).
$$

对候选节点定义：

$$
(o^A_{v,\theta},o^O_{v,\theta},r_{v,\theta})
=
\begin{cases}
\operatorname{Full}_v
(q^+_{v,\theta},\theta,h_{v,\theta}),
&\chi_{v,\theta}=1,\\
(\bot_v^A,\bot_v^O,r_v^\circ),
&\chi_{v,\theta}=0.
\end{cases}
\tag{24}
$$

若 $o^A_{v,\theta}(a)=y\in P$，则产生图内消息；若 $o^O_{v,\theta}(o)=y'\in P$，则产生外部输出记录：

$$
\begin{aligned}
m&=(\theta,a,y),
\\
z&=(\theta,o,y').
\end{aligned}
\tag{25}
$$

外部输出记录的三个坐标分别是逻辑产生时间、输出端口和值。若相应函数值为 $\bot$，本次事件就在该边或该输出端口上不产生记录。因为每个 $o\in\mathsf O$ 具有唯一来源节点 $\varepsilon(o)$，任意实际输出集合 $Z$ 都满足：

$$
(\theta,o,y)\in Z,
\quad
(\theta,o,y')\in Z
\Longrightarrow
y=y'.
$$

region 和 selector 都不产生式 (25) 的图内消息或外部输出。selector 只产生 $\mathcal A_{j,\theta}$；节点根据它得到的 $\chi,\omega$ 更新自己的状态，沿自己的边发送，并向自己的输出端口给值。

所以“区分输入来源”与“区分输出去向”是两个独立能力：前者来自桶中保留的 $i$ 或 $a$，后者来自两个输出函数分别以内部边 $a$ 和外部端口 $o$ 为坐标；不需要二选一。

例如，若 $\operatorname{OutPort}(v)=\{o_0,o_1\}$，并且某次 active 计算给出：

$$
o^O_{v,\theta}(o_0)=y_0,
\qquad
o^O_{v,\theta}(o_1)=y_1,
$$

则 $Z$ 同时加入 $(\theta,o_0,y_0)$ 与 $(\theta,o_1,y_1)$。它们是两个命名输出，不是图内的两条新消息。

### 2.9 两条互相独立的配置轴

$\tau_j$ 决定 selector 读取哪个值，$\pi_j$ 决定哪些 candidates 采用新状态。它们不是同一件事。

| 条件 | selector 读取 | 状态采用集合 | 完整计算集合 |
| --- | --- | --- | --- |
| SD + content | 当前本地内容 | active | active |
| SD + pre | 旧状态与当前内容 | active | active |
| BO + content | 当前本地内容 | candidates | active |
| BO + pre | 旧状态与当前内容 | candidates | active |
| BO + post | 候选新状态与当前内容 | candidates | active |

数学上还可以定义 SD + post：先为全部 candidates 定义候选新状态并读取它们，选择后只让 active candidates 采用。若使用这种组合，应把它作为独立条件明确记录，而不能用 SD 或 post 中任何一个词代替完整定义。

### 2.10 为什么不能只给每个节点旧式的局部函数

在 selector 已经给出 $\chi,\omega$ 后，式 (8)--(24) 可以合成为节点局部函数：

$$
\Gamma_v
\left(
q^-_{v,\theta},
\theta,
B_{v,\theta},
\chi_{v,\theta},
\omega_{v,\theta}
\right)
=
\left(
q^+_{v,\theta},
o^A_{v,\theta},
o^O_{v,\theta},
r_{v,\theta}
\right).
\tag{26}
$$

但 $\chi_{v,\theta}$ 一般依赖同一 region 中全部 candidates 的描述量，所以不能由节点 $v$ 独自从 $(q,\theta,B)$ 算出。

因此，包含 region selector 的一般模型需要：

$$
\text{节点本地准备}
\longrightarrow
\text{region 选择}
\longrightarrow
\text{节点本地完成}.
$$

把整个 region 收缩成一个节点虽然可以得到某种编码，却不是本文的定义，因为那会隐藏节点各自的状态、出边和完整计算。

从此以后，本文把第 1--2 节全部有限集合、函数、初值和约束固定下来所得的数据族，称为一个 **TimedDAG-region-selector 规格**。这个名称没有再加入任何未写出的对象；第 3 节只是在一次输入上求这些已给函数的值。

第三次阅读到这里即可停止。此时只需能从一组非空完整桶依次算出 $\mathcal C_{j,\theta}$、$\mathcal A_{j,\theta}$、$q^+_{v,\theta}$、图内消息和外部输出。

## 3. 完整输入已知时怎样定义唯一计算

### 3.1 为什么按逻辑时间递归

区域划分可能把拓扑深度不同的节点放在一起。例如：

$$
u\longrightarrow v\longrightarrow w,
$$

而：

$$
u,w\in\mathcal R_0,
\qquad
v\in\mathcal R_1.
$$

因此一般不能先把 $u$ 的全部逻辑时间处理完，再处理 $v,w$。时间为 $\theta$ 的 $u,w$ 可能需要参加同一次式 (18)。

本文改用逻辑时间递增的递归。正时延保证时间 $\theta$ 新产生的消息只能影响更大的逻辑时间。

### 3.2 一个有限的时间上界

因为节点图有限且无环，从任一输入端口所指节点出发的有向路径只有有限多条。允许只停留在 $\gamma(i)$ 的长度 $0$ 路径，并把它的总时延定义为 $0$。对路径 $\zeta$ 定义：

$$
\Delta(\zeta)=\sum_{a\in\zeta}\delta(a).
$$

再定义：

$$
\Delta_{\max}
=
\max_{\zeta}\Delta(\zeta),
$$

其中 $\zeta$ 遍历从某个 $\gamma(i)$ 出发的全部上述路径。最后定义：

$$
\Theta_{\max}
=
\max_{\substack{i\in\mathsf I\\t\in[L_i]}}\iota_i(t)
+
\Delta_{\max}.
\tag{27}
$$

任何实际消息都可以沿其因果来源向前追溯到一个外部输入；每经过一条边只增加该边时延。因此任何非空节点事件的逻辑时间都不大于 $\Theta_{\max}$。

### 3.3 直接递归

令图内消息集合 $M$ 与外部输出记录集合 $Z$ 初始为空，令每个节点状态为 $q_v^0$。

依次取：

$$
\theta=0,1,\ldots,\Theta_{\max}.
$$

在每个 $\theta$，执行以下四步。

**第一步：构造全部完整桶与 candidates。**

定义：

$$
\begin{aligned}
B_{v,\theta}
={}&
\{(0,i,t,x_i(t))
\mid i\in\operatorname{InPort}(v),
\ t\in[L_i],
\iota_i(t)=\theta\}
\\
&\cup
\{(1,m)
\mid m\in M,
\operatorname{receiver}(m)=v,
\operatorname{arrival}(m)=\theta\}.
\end{aligned}
\tag{28}
$$

再用式 (15) 得到每个 $\mathcal C_{j,\theta}$。

**第二步：计算 candidates 的本地量。**

对每个 $v\in\mathcal C_{j,\theta}$，用当前节点状态作为 $q^-_{v,\theta}$，计算式 (9)、(11) 和式 (16) 所需的描述量。

式 (11) 在这里定义候选新状态；尚未用它替换节点保存的状态。

**第三步：每个非空 region-time 选择一次。**

对每个满足 $\mathcal C_{j,\theta}\ne\varnothing$ 的 $j$，应用一次式 (18)--(19)，得到 $\mathcal A_{j,\theta}$。

不同 regions 在同一 $\theta$ 不读取彼此的选择结果，所以这些函数作用可以采用任意顺序。

**第四步：状态采用、完整计算、发送与外部输出。**

对每个 candidate 应用式 (20)--(24)，并把节点保存状态改成 $q^+_{v,\theta}$。每当式 (24) 给出 $o^A_{v,\theta}(a)=y\in P$，把消息 $(\theta,a,y)$ 加入 $M$；每当它给出 $o^O_{v,\theta}(o)=y'\in P$，把外部输出记录 $(\theta,o,y')$ 加入 $Z$。

不属于任何 $\mathcal C_{j,\theta}$ 的节点在当前 $\theta$ 不改变状态，也不产生图内消息或外部输出。

### 3.4 当前时间的图内输出不能改变当前候选集合

式 (25) 中产生的图内消息满足：

$$
\operatorname{arrival}(\theta,a,y)
=
\theta+\delta(a)
>
\theta.
\tag{29}
$$

所以第四步新产生的消息不会重新进入第一步的时间 $\theta$ 桶。当前 candidate set 在 selector 作用前已经完整，不会由这次 selector 的结果反过来改变。

### 3.5 有限性与唯一性

递归只遍历有限个逻辑时间、有限个节点、有限个 regions 和有限个输出端口。每个 candidate 在每条出边和每个相连输出端口至多产生一个值，所以全部函数作用、消息和外部输出记录都有限。

唯一性可以按 $\theta$ 归纳。

- 时间 $0$ 的桶只由逻辑注入时间为 $0$ 的外部输入决定；全部固定函数因而给出唯一结果。
- 假设所有小于 $\theta$ 的结果唯一。由式 (29)，到达时间 $\theta$ 的边消息全部来自更小时间事件，所以式 (28) 唯一。式 (8)--(24) 都是函数，故时间 $\theta$ 的结果唯一。

自然数归纳法因而给出唯一的最终消息集合：

$$
M^*,
$$

唯一的外部输出记录集合：

$$
Z^*,
$$

唯一的最终状态族：

$$
(q_v^{\mathrm{final}})_{v\in V},
$$

以及唯一的 candidate、active 和观察记录。

把完整结果记录定义为：

$$
\mathcal T_x
=
\left(
M^*,
Z^*,
(q_v^{\mathrm{final}})_{v\in V},
(\mathcal C_{j,\theta},\mathcal A_{j,\theta})_{j,\theta},
((q^-_{v,\theta},q^+_{v,\theta},r_{v,\theta}))_{v,\theta}
\right),
$$

其中后两个族只在相应 candidate set 或节点桶非空的位置记录。这里 $x=(x_i)_{i\in\mathsf I}$ 是整个输入函数族。固定本文全部结构数据后，用 $\mathbf T$ 表示所有可能的 $\mathcal T_x$ 所成的集合。

这就是本文的直接数学解释器。它相对于已经给定且可求值的式 (8)、(10)、三个 Read、式 (18) 和式 (23)，只做有限次集合构造和函数作用。

## 4. 消息尚未全部可见时怎样证明候选集合完整

### 4.1 看见的输入与消息

第 3 节从完整输入直接定义了 $M^*$。现在用 $n\in\mathbb N$ 表示机器外部操作的先后编号；$n$ 不会传入任何节点函数或 selector。

在阶段 $n$，对每个 $i\in\mathsf I$ 设：

$$
U_{i,n}\subseteq[L_i]
$$

是端口 $i$ 上已经看见的位置集合，并设：

$$
H_n\subseteq M^*
$$

是已经看见的消息集合。消息不必按照逻辑到达时间递增进入 $H_n$。

定义阶段 $n$ 看见的桶：

$$
\begin{aligned}
B^{(n)}_{v,\theta}
={}&
\{(0,i,t,x_i(t))
\mid i\in\operatorname{InPort}(v),
\ t\in U_{i,n},
\iota_i(t)=\theta\}
\\
&\cup
\{(1,m)
\mid m\in H_n,
\operatorname{receiver}(m)=v,
\operatorname{arrival}(m)=\theta\}.
\end{aligned}
\tag{30}
$$

显然：

$$
B^{(n)}_{v,\theta}
\subseteq
B_{v,\theta}.
$$

### 4.2 边与输入的有效封闭下界

给定函数：

$$
\sigma_n:A\to\mathbb N,
\qquad
\sigma_n^{\mathrm{in}}:\mathsf I\to\mathbb N.
$$

定义：$\sigma_n(a)=b$ 是阶段 $n$ 关于边 $a$ 的有效封闭下界，当且仅当：

$$
\forall m\in M^*\setminus H_n,
\quad
\operatorname{edge}(m)=a
\Longrightarrow
\operatorname{arrival}(m)\ge b.
\tag{31}
$$

定义：$\sigma_n^{\mathrm{in}}(i)=b$ 是阶段 $n$ 关于输入端口 $i$ 的有效封闭下界，当且仅当：

$$
\forall t\in[L_i]\setminus U_{i,n},
\quad
\iota_i(t)\ge b.
\tag{32}
$$

正文以后把满足式 (31)--(32) 的数简称为 **seal**。

seal 是关于全部尚未看见消息或输入的全称命题。队列暂时为空、等待很久或某个函数已经返回，都不能单独证明式 (31)--(32)。

seal $=b$ 仍允许以后出现逻辑时间恰好为 $b$ 的输入，所以关闭时间 $\theta$ 需要严格不等式：

$$
b>\theta.
$$

### 4.3 节点封闭前沿

对每个节点 $v$，定义非空有限数集：

$$
L_n(v)
=
\{\sigma_n(a)\mid a\in\operatorname{In}(v)\}
\cup
\{\sigma_n^{\mathrm{in}}(i)
\mid i\in\operatorname{InPort}(v)\}.
$$

这个集合非空：若 $v$ 本身是某个输入端口的目标，第二个集合非空；否则第 1.2 节的可达条件保证 $v$ 至少有一条入边。

定义节点封闭前沿：

$$
\lambda_n(v)=\min L_n(v).
\tag{33}
$$

若：

$$
\lambda_n(v)>\theta,
$$

则节点的每条入边和可能的外部输入都排除了尚未可见的时间 $\theta$ 原子。因此：

$$
B^{(n)}_{v,\theta}
=
B_{v,\theta}.
\tag{34}
$$

**证明。** 左边显然包含于右边。若右边存在一个左边没有、来自端口 $i$ 的外部输入原子，式 (32) 与 $\sigma_n^{\mathrm{in}}(i)>\theta$ 排除它；若存在一个左边没有的边消息原子，式 (31) 与相应 $\sigma_n(a)>\theta$ 排除它。因此右边也包含于左边。$\square$

### 4.4 region 封闭前沿

定义：

$$
\lambda_n(\mathcal R_j)
=
\min_{v\in\mathcal R_j}\lambda_n(v).
\tag{35}
$$

这个最小值存在，因为 $\mathcal R_j$ 非空且有限。

定义阶段 $n$ 暂时看见的候选集合：

$$
\mathcal C^{(n)}_{j,\theta}
=
\{v\in\mathcal R_j
\mid B^{(n)}_{v,\theta}\ne\varnothing\}.
\tag{36}
$$

### 4.5 候选集合关闭引理

若：

$$
\lambda_n(\mathcal R_j)>\theta,
$$

则：

$$
\mathcal C^{(n)}_{j,\theta}
=
\mathcal C_{j,\theta}.
\tag{37}
$$

**证明。** 由式 (35)，对每个 $v\in\mathcal R_j$ 都有：

$$
\lambda_n(v)>\theta.
$$

式 (34) 因而给出：

$$
B^{(n)}_{v,\theta}=B_{v,\theta}.
$$

所以：

$$
B^{(n)}_{v,\theta}\ne\varnothing
\Longleftrightarrow
B_{v,\theta}\ne\varnothing.
$$

把满足等价条件的全部 $v\in\mathcal R_j$ 收集起来，就得到式 (37)。$\square$

这个引理是 selector 可以忽略机器消息到达次序的核心理由。它同时说明：必须获得 region 中每个节点的封闭证明，包括最终没有消息的节点。

第四次阅读可以先停在这里，并在不看上面证明的情况下重新证明式 (37)。第 4.6 节以后才讨论状态就绪与实际求值次序。

### 4.6 输入已经完整不等于节点状态已经就绪

式 (37) 只证明时间 $\theta$ 的输入桶和 candidate set 已经完整。若描述量读取 $q^-_{v,\theta}$，还必须保证节点 $v$ 的全部更小逻辑时间非空事件已经完成状态采用。

定义：节点 $v$ 的时间 $\theta$ 状态已经就绪，当且仅当，对每个满足：

$$
\theta'<\theta,
\qquad
B_{v,\theta'}\ne\varnothing
$$

的 $\theta'$，式 (22) 已经完成，并且这些状态采用按 $\theta'$ 递增连接起来。

本文先采用下面这个统一而简单的充分条件：region $\mathcal R_j$ 在阶段 $n$ 可以对时间 $\theta$ 应用 selector，当：

1. $\lambda_n(\mathcal R_j)>\theta$；
2. 每个 $v\in\mathcal C_{j,\theta}$ 的时间 $\theta$ 状态已经就绪；
3. $(j,\theta)$ 尚未应用过式 (18)。

第一条证明所有 selector 输入桶完整；第二条证明 pre/post 所需状态唯一；第三条防止同一次选择重复发生。

当 $\tau_j=\mathrm{content}$ 时，selector 本身并不读取旧状态，所以第二条不是作出选择的逻辑必要条件。本文的基准解释器仍等待它，是为了让选择后的每个 candidate 都能立即进入状态采用阶段。以后可以把 content 选择提前、再等待状态采用；那只放宽合法求值次序，不改变式 (8)--(25) 定义的结果。

### 4.7 可以提前求值，但不能提前改变语义状态

某个节点自己的桶已经关闭以后，可以先求：

$$
h_{v,\theta},
\qquad
d^{\mathrm{content}}_{v,\theta}.
$$

它的旧状态也已经确定以后，还可以求：

$$
d^{\mathrm{pre}}_{v,\theta},
\qquad
\widetilde q_{v,\theta},
\qquad
d^{\mathrm{post}}_{v,\theta}.
$$

这些只是已经定义的函数值。在其他 region 成员尚未就绪时，可以把它们保存在不属于节点持久状态的临时数学变量中。

但在式 (19) 得到 $\mathcal A_{j,\theta}$ 以前，不得：

- 用式 (22) 让未来事件读取 $q^+_{v,\theta}$；
- 应用只允许 active 节点执行的式 (23)；
- 产生式 (25) 的图内消息或外部输出记录。

提前求一个纯函数的值不会改变语义；提前发布尚未获准的状态、消息或外部输出会改变语义。

### 4.8 seal 的单调性与不得倒填

随着阶段 $n$ 增加，每个 $U_{i,n}$ 和 $H_n$ 只能增大，每个 $\sigma_n^{\mathrm{in}}(i)$ 与 $\sigma_n(a)$ 只能不减小。

如果已经公布：

$$
\sigma_n(a)=b,
$$

以后又让一条满足：

$$
\operatorname{edge}(m)=a,
\qquad
\operatorname{arrival}(m)<b
$$

的此前未见消息进入 $H_{n'}$，就直接否定式 (31)。这样的过程不是本文的合法异步计算。

同样，若已经公布 $\sigma_n^{\mathrm{in}}(i)=b$，以后才让某个满足 $\iota_i(t)<b$ 的未见输入位置进入 $U_{i,n'}$，就否定式 (32)，也不合法。

## 5. 一般异步解释器需要遵守什么

### 5.1 四类数学作用

对一个非空候选事件，可以把第 3.3 节进一步拆成四类作用：

1. 节点本地准备：由完整桶和旧状态求 $h$、所需描述量及可能的候选新状态；
2. region 选择：由完整 candidate set 的描述量族求 active set；
3. 节点状态采用：由 $\pi_j$ 和 active set 求 $q^+$；
4. active 节点完整计算：求逐出边输出与逐输出端口的值，并产生图内消息和外部输出记录。

这些作用可以在机器中由不同计算步骤完成，但其数学依赖不能颠倒。

### 5.2 一次合法 region 选择

在阶段 $n$，任取满足第 4.6 节三条条件的 $(j,\theta)$。一次合法选择必须：

1. 使用式 (37) 已经固定的完整 $\mathcal C_{j,\theta}$；
2. 对每个 candidate 使用式 (16) 指定的 $d_{v,\theta}$：content 只由完整桶得到，pre/post 还使用唯一旧状态；
3. 恰好应用一次式 (18)；
4. 得到与直接解释器式 (19) 相同的 $\mathcal A_{j,\theta}$。

不能只对机器当前已经完成本地准备的部分 candidates 应用 selector；第 4.5 节的集合相等才允许选择。

### 5.3 一次合法节点完成

region 选择以后，每个 candidate 节点可以分别完成。节点 $v$ 的一次合法完成必须：

1. 使用该 $(j,\theta)$ 已经确定的 $\chi_{v,\theta}$ 与 $\omega_{v,\theta}$；
2. 按式 (22) 得到唯一的新状态；
3. 仅在 $\chi_{v,\theta}=1$ 时应用式 (23)；
4. 仅把式 (24) 中非 $\bot$ 的结果变成相应的图内消息或外部输出记录；
5. 在同一节点任何更大逻辑时间事件读取状态以前完成式 (22)。

同一 region 中不同 candidate 节点完成的机器先后次序可以不同，因为它们只修改各自的节点状态。由一个 active 节点产生的消息也可以晚于另一个 active 节点的消息才被机器看见。

### 5.4 消息可见与出边 seal 的先后

定义：节点 $v$ 已完成到 $b$，当且仅当：

1. $\lambda_n(v)\ge b$，所以以后不会再发现新的逻辑时间小于 $b$ 的非空桶；
2. 它的所有逻辑时间小于 $b$ 的非空完整桶都已经完成第 5.3 节。

inactive candidate 也必须完成一次最终判定：

- SD 下，它确定状态保持不变，且没有图内消息或外部输出；
- BO 下，它确定采用候选新状态，但没有图内消息或外部输出。

节点完成到 $b$ 时，它在所有小于 $b$ 的逻辑时间产生的外部输出记录也已经确定。外部输出不再进入任何节点桶，所以它不参与下面的边 seal 递推。

若 $v$ 已完成到 $b$，它以后尚未发生的事件发送时间都不小于 $b$。所以沿任意 $a\in\operatorname{Out}(v)$，以后尚未产生的消息逻辑到达时间都不小于：

$$
b+\delta(a).
$$

还要等待已经产生且到达时间小于 $b+\delta(a)$ 的消息全部进入可见集合 $H_n$。只有这两件事都成立，才能把 $b+\delta(a)$ 作为边 $a$ 的新有效 seal。

因此必须遵守：

$$
\text{先让实际消息可见}
\quad\Longrightarrow\quad
\text{再让越过它的 seal 可见}.
$$

### 5.5 合法次序可以怎样不同

一个异步解释器可以：

- 先看见逻辑时间较大的消息，后看见逻辑时间较小的消息；
- 先准备一个尚不能选择的 candidate；
- 先选择一个逻辑时间较大的独立 region-time；
- 把同一选择以后彼此独立的节点交给不同求值过程；
- 在保证状态依赖的前提下改变不同节点完成的先后。

它不可以：

- 在 region 前沿尚未越过 $\theta$ 时固定 candidate set；
- 用部分桶计算最终描述量；
- 让机器先完成者改变式 (18) 的输出；
- 在选择以前提交 SD 的候选状态；
- 先发布 seal，再补入被该 seal 排除的消息；
- 对同一 $(j,\theta)$ 选择两次，或对同一 $(v,\theta)$完成两次。

### 5.6 合法次序无关的证明路线

比较任意两个都完成同一个有限逻辑时间边界的合法次序。证明可以按：

$$
(\theta,p)
$$

作字典序归纳，其中 $p$ 是第 5.1 节的作用种类编号。

- 式 (34) 保证关闭后的节点桶与直接解释器相同；
- 式 (37) 保证完整 candidate set 相同；
- 更小逻辑时间状态已经相同，所以描述量相同；
- 式 (18) 是函数，所以 active set 相同；
- 式 (20)--(24) 给出相同的新状态、观察值和输出函数值，式 (25) 因而给出相同的图内消息和外部输出记录。

这给出了证明的骨架。正式定理还需要把已准备位置、已选择位置、已完成位置、可见消息集合和 seal 逐项写成随 $n$ 单调变化的有限集合。

## 6. SD、BO、pre 与 post 的完整手算例子

取一个只有两个 candidates 的 region：

$$
\mathcal R=\{a,b\},
\qquad
K=1.
$$

假设时间 $5$ 的两个完整桶都非空，并且式 (9) 给出：

$$
h_{a,5}=10,
\qquad
h_{b,5}=1.
$$

两个节点的旧状态为：

$$
q^-_{a,5}=0,
\qquad
q^-_{b,5}=6.
$$

对两个节点都定义：

$$
\operatorname{Update}(q,\theta,h)=q+h,
$$

$$
\operatorname{Read}^{\mathrm{pre}}(q,\theta,h)=q,
$$

$$
\operatorname{Read}^{\mathrm{post}}(\widetilde q,\theta,h)=\widetilde q.
$$

selector 选择描述量更大的一个节点。相等时按一个事先给定的固定节点全序选择。

候选新状态为：

$$
\widetilde q_{a,5}=10,
\qquad
\widetilde q_{b,5}=7.
$$

### 6.1 SD + pre

pre 描述量为：

$$
d_{a,5}=0,
\qquad
d_{b,5}=6.
$$

因此：

$$
\mathcal A_{\mathcal R,5}=\{b\}.
$$

SD 只让 active node 采用候选状态，所以：

$$
q^+_{a,5}=0,
\qquad
q^+_{b,5}=7.
$$

只有 $b$ 应用式 (23)。

### 6.2 BO + pre

selector 仍然读取 $(0,6)$，所以 active set 仍是：

$$
\mathcal A_{\mathcal R,5}=\{b\}.
$$

BO 让全部 candidates 采用候选状态，所以：

$$
q^+_{a,5}=10,
\qquad
q^+_{b,5}=7.
$$

仍然只有 $b$ 应用式 (23)。这已经说明 BO 不等于“selector 必须读取更新后状态”。

### 6.3 BO + post

post 描述量为：

$$
d_{a,5}=10,
\qquad
d_{b,5}=7.
$$

所以 active set 改成：

$$
\mathcal A_{\mathcal R,5}=\{a\}.
$$

BO 仍让两个节点采用候选状态：

$$
q^+_{a,5}=10,
\qquad
q^+_{b,5}=7,
$$

但这次只有 $a$ 应用式 (23)。

三种条件可合写为：

| 条件 | active set | 最终状态 $(q_a^+,q_b^+)$ |
| --- | --- | --- |
| SD + pre | $\{b\}$ | $(0,7)$ |
| BO + pre | $\{b\}$ | $(10,7)$ |
| BO + post | $\{a\}$ | $(10,7)$ |

所以 SD/BO 和 pre/post 通常改变状态或输出。它们属于节点与 selector 的数学定义，不是仅仅改变机器求值顺序的选择。

## 7. 由一次计算产生的一张规范细分事件 DAG

### 7.1 固定空间图与细分事件图不是同一张图

式 (1) 的 $G$ 在输入以前固定。给定具体 $x$ 并执行第 3 节后，可以从实际发生的函数作用构造另一张图。

本文构造的是一张便于证明的规范依赖图，不声称它是唯一或边数最少的依赖图。例如第 4.6 节已经说明，content selector 可以在旧状态就绪前提前求值；规范图仍采用较强的统一次序。删去这种保守先后关系属于调度优化，不改变正文函数值。

对每个 candidate 位置 $(v,\theta)$，按需要引入：

$$
P_{v,\theta}=\text{节点本地准备作用},
$$

$$
U_{v,\theta}=\text{状态采用作用}.
$$

对每个非空 candidate set，引入：

$$
S_{j,\theta}=\text{region 选择作用}.
$$

对每个 active node，引入：

$$
E_{v,\theta}=\text{完整计算、图内发送与外部输出作用}.
$$

这些是一次具体输入产生的函数作用位置。$S_{j,\theta}$ 的存在不表示 $j$ 是固定空间图的消息节点。

### 7.2 同一逻辑时间的因果关系

当 $v\in\mathcal C_{j,\theta}$ 时，加入：

$$
P_{v,\theta}
\longrightarrow
S_{j,\theta}
\longrightarrow
U_{v,\theta}.
\tag{38}
$$

当 $v\in\mathcal A_{j,\theta}$ 时，再加入：

$$
U_{v,\theta}
\longrightarrow
E_{v,\theta}.
\tag{39}
$$

在 post 条件中，候选新状态的求值属于 $P_{v,\theta}$；$U_{v,\theta}$ 仍表示式 (22) 决定它是否成为未来状态。在 SD + pre 中，程序可以等选择以后才实际求式 (11)，但所得数学值仍由相同输入唯一确定。

### 7.3 同一节点的状态先后

若节点 $v$ 的两个非空事件时间满足 $\theta<\theta'$，并且两者之间没有另一个 $v$ 的非空事件，则加入：

$$
U_{v,\theta}
\longrightarrow
P_{v,\theta'}.
\tag{40}
$$

这表示时间 $\theta'$ 的旧状态来自更早事件完成后的状态。

### 7.4 消息影响

若 $E_{v,\theta}$ 产生消息：

$$
m=(\theta,a,y),
$$

则加入：

$$
E_{v,\theta}
\longrightarrow
P_{\beta(a),\theta+\delta(a)}.
\tag{41}
$$

若目标桶还包含其他消息，目标准备作用同时依赖那些消息的产生者。

$E_{v,\theta}$ 产生的外部输出记录没有指向后续节点作用的因果边，因为输出端口不返回图内；它们仍然是这个作用的结果，并被记录在 $Z^*$ 中。

式 (41) 只画出了实际消息带来的数值影响。在线判断完整桶时，还需要知道某些边在对应时间没有消息。若把这种证明过程也画成作用位置，可以加入“桶已确定”的证明位置 $\Xi_{v,\theta}$：active 节点的逐边输出判定、inactive 节点的全空输出判定以及上游完成 seal 都指向相应的 $\Xi$。

因为 $\delta(a)>0$，决定目标时间 $\theta$ 是否有边 $a$ 消息，只涉及发送时间：

$$
\theta-\delta(a)<\theta.
$$

所以把这些 seal 与无消息证明也加入以后，它们仍然只从更小逻辑时间指向当前桶确定位置，不会破坏下面的递增量证明。

### 7.5 为什么细分事件图没有环

给四类作用分配阶段编号：

$$
p(P)=0,
\qquad
p(S)=1,
\qquad
p(U)=2,
\qquad
p(E)=3.
$$

把一个作用的秩定义为：

$$
(\theta,p).
$$

按字典序比较这些二元组。同一逻辑时间的式 (38)--(39) 严格增加 $p$；式 (40) 严格增加 $\theta$；由 $\delta(a)>0$，式 (41) 也严格增加 $\theta$。

因此每条因果边都严格增加 $(\theta,p)$。沿有向边前进不可能回到原来的二元组，所以细分事件图没有有向环。

### 7.6 为什么不需要 region 收缩图无环

只为比较另定义一个关系：

$$
Q_\rho
=
\{(j,j')\in J\times J
\mid j\ne j',
\ \exists a\in A,
\ \rho(\alpha(a))=j,
\rho(\beta(a))=j'\}.
$$

把 $(J,Q_\rho)$ 称为 region 收缩图。它不是正文消息图的一部分；它只记录是否至少有一条节点边从一个 region 指向另一个 region。

考虑：

$$
u\xrightarrow{a}v\xrightarrow{b}w,
$$

并令：

$$
u,w\in\mathcal R_0,
\qquad
v\in\mathcal R_1.
$$

若把 regions 收缩成点，会画出：

$$
\mathcal R_0
\longrightarrow
\mathcal R_1
\longrightarrow
\mathcal R_0.
$$

但实际消息影响是：

$$
(u,\theta)
\longrightarrow
(v,\theta+\delta(a))
\longrightarrow
(w,\theta+\delta(a)+\delta(b)).
$$

最后一个事件虽然再次属于 $\mathcal R_0$，其逻辑时间已经严格增大。region 名称重复不等于事件位置重复。

因此，region 收缩后的环不妨碍第 7.5 节的证明。区域划分只在同一时间建立式 (38) 的共同选择关系，不是第二张消息图。

### 7.7 正时延是当前证明的必要前提

若允许某条边满足 $\delta(a)=0$，式 (41) 可能从时间 $\theta$ 的阶段 $3$ 指向同一时间的阶段 $0$。这不再严格增加 $(\theta,p)$，并可能让当前选择的输出反过来决定当前候选集合。

因此本文结论依赖：

$$
\forall a\in A,
\quad
\delta(a)>0.
$$

零时延边必须另行规定同刻依赖怎样求值，不能在本文中悄悄加入。

## 8. 在逻辑时间边界停止与继续

### 8.1 逻辑时间切面

给定 $b\in\mathbb N$，把节点事件位置分成：

$$
\mathcal E^{<b}
=
\{(v,\theta)\mid
B_{v,\theta}\ne\varnothing,
\ \theta<b\},
$$

$$
\mathcal E^{\ge b}
=
\{(v,\theta)\mid
B_{v,\theta}\ne\varnothing,
\ \theta\ge b\}.
$$

对 region 选择位置也定义：

$$
\mathcal S^{<b}
=
\{(j,\theta)\mid
\mathcal C_{j,\theta}\ne\varnothing,
\ \theta<b\},
$$

$$
\mathcal S^{\ge b}
=
\{(j,\theta)\mid
\mathcal C_{j,\theta}\ne\varnothing,
\ \theta\ge b\}.
$$

一个完整的逻辑时间切面要求 $\mathcal E^{<b}$ 中每个 candidate 都已经完成状态采用与必要的完整计算，$\mathcal S^{<b}$ 中每个位置都已经完成选择，并且它们产生的图内消息与外部输出记录都已经确定。

这个定义不允许把同一个 $\theta<b$ 的 region 选择停在一半。机器在任意中间步骤暂停是另一个更丰富的问题。

### 8.2 跨过切面的消息

定义：

$$
W_b
=
\{m\in M^*\mid
\operatorname{send}(m)<b
\le
\operatorname{arrival}(m)\}.
\tag{42}
$$

$W_b$ 中的消息已经由左侧事件产生，但其逻辑到达时间属于右侧。若停止后丢掉它们，右侧某些完整桶会缺少元素。

再定义已经产生的外部输出前缀：

$$
Z^{<b}
=
\{z\in Z^*\mid\operatorname{otime}(z)<b\}.
$$

它不影响右侧节点计算，但若恢复后还要重建完整的多端口输出记录，就必须保留它，或者保证它已经由外部接收者可靠保存。

### 8.3 切面处的节点状态

对每个节点 $v$，令 $q_v^b$ 是按逻辑时间递增完成所有满足：

$$
\theta<b,
\qquad
B_{v,\theta}\ne\varnothing
$$

的状态采用以后得到的状态。若不存在这样的 $\theta$，令：

$$
q_v^b=q_v^0.
$$

在本文的无状态 selector 定义下，一个候选 continuation 是：

$$
Q_b
=
\left(
b,
(q_v^b)_{v\in V},
W_b,
Z^{<b}
\right).
\tag{43}
$$

固定图、端口关联、各 $L_i$ 与 $\iota_i$、区域划分和所有函数属于已经给定的数据，不需要重复放进 $Q_b$。

### 8.4 右侧外部输入

定义从时间 $b$ 开始尚未消费的外部输入集合：

$$
X_{\ge b}
=
\{(i,t,x_i(t))
\mid i\in\mathsf I,\ t\in[L_i],
\iota_i(t)\ge b\}.
\tag{44}
$$

从 $Q_b$ 与式 (44) 继续计算时：

1. 节点初态取 $q_v^b$；
2. $W_b$ 中到达时间不小于 $b$ 的消息参加对应完整桶；
3. 只再处理逻辑时间不小于 $b$ 的外部输入、region 选择和节点事件。

### 8.5 分段计算需要证明什么

记一次直接完整计算的结果为：

$$
\operatorname{Direct}(x).
$$

记从式 (43)--(44) 继续所得结果为：

$$
\operatorname{Continue}(Q_b,X_{\ge b}).
$$

需要证明：继续计算产生的所有时间不小于 $b$ 的图内消息、外部输出记录、状态变化、candidate sets、active sets 和观察值，与 $\operatorname{Direct}(x)$ 的相应后缀完全相同；再与 $Z^{<b}$ 合并后，完整外部输出集合仍是 $Z^*$。

证明路线仍是对 $\theta\ge b$ 作归纳。式 (43) 给出相同旧状态，式 (42) 与 (44) 给出相同输入桶来源，此后式 (8)--(25) 产生相同结果。

若以后加入式 (49) 那样的 selector-history，continuation 还必须保存每个 selector 在切面 $b$ 的状态。若允许停在同一逻辑时间的准备、选择或状态采用之间，还必须保存相应未完成阶段；式 (43) 不声称覆盖那种暂停位置。

## 9. 与较简单 TimedDAG 以及单端口特例的关系

### 9.1 单节点 region 退化为局部节点函数

假设每个 region 都是单节点集合，并规定每个非空候选始终 active、始终采用候选状态。那么：

$$
\chi_{v,\theta}=1,
\qquad
\omega_{v,\theta}=1.
$$

式 (26) 退化为：

$$
F_v(q,\theta,B)
=
\Gamma_v(q,\theta,B,1,1).
\tag{45}
$$

这正是每个节点只依赖自己的旧状态和完整桶的 TimedDAG。因而本文不是删除局部节点模型，而是在它前面加入一次有严格输入边界的区域选择。

### 9.2 单输入是主定义的特例

第 1.2、1.4 节已经直接使用有限输入端口集 $\mathsf I$。每个端口都有自己的位置集合、值函数、严格递增逻辑注入时间和式 (32) 的 seal；式 (28)、(30) 与 (33) 同时对所有端口生效。

若只要一个输入端口，取：

$$
\mathsf I=\{i_0\}.
$$

旧式“唯一输入节点”就是 $\gamma(i_0)$；旧式长度 $L$、输入 $x$ 和时间函数 $\iota$ 分别是 $L_{i_0}$、$x_{i_0}$ 和 $\iota_{i_0}$。所以单输入是删去端口下标所得的特例，而多输入不是正文外的后续扩展。

### 9.3 单输出也是主定义的特例

第 1.2、2.8 节已经直接使用有限输出端口集 $\mathsf O$。对每个 $o\in\mathsf O$，从 $Z^*$ 中取出该端口的带时间输出集合：

$$
Z_o^*
=
\{(\theta,y)\mid(\theta,o,y)\in Z^*\}.
\tag{46}
$$

全部图外输出是函数族：

$$
(Z_o^*)_{o\in\mathsf O}.
$$

不同输出端口可以属于同一节点，也可以属于不同节点；一个端口还可以在多个逻辑时间产生值。若只要一个输出，取 $\mathsf O=\{o_0\}$。因此单输出同样只是主定义的特例。

由第 2.8 节的唯一性条件，每个 $Z_o^*$ 是一个从某个有限逻辑时间子集到 $P$ 的函数图。若需要序列表示，只需按 $\theta$ 递增排列；这个排列没有增加新的语义数据。

## 10. 一般正确性与大块推进性质分开研究

### 10.1 region 前沿由最慢成员决定

由式 (35)：

$$
\lambda_n(\mathcal R_j)
\le
\lambda_n(v)
\qquad
(v\in\mathcal R_j).
$$

例如：

$$
\lambda_n(v_1)=100,
\quad
\lambda_n(v_2)=96,
\quad
\lambda_n(v_3)=17
$$

时：

$$
\lambda_n(\mathcal R_j)=17.
$$

前两个节点虽然已经能证明更远时间的桶完整，整个 region 仍然只能安全确定小于 $17$ 的 candidate sets。

### 10.2 已关闭的 region-time 窗口

若 $c_j$ 是 region 尚未处理的最小逻辑时间，则当前已经具有固定 candidate set 的区间是：

$$
[c_j,\lambda_n(\mathcal R_j)).
$$

其中实际非空 candidate set 的时间数为：

$$
K^{\mathrm{ready}}_{j,n}
=
\left|
\left\{
\theta\in[c_j,\lambda_n(\mathcal R_j))
\mid
\mathcal C_{j,\theta}\ne\varnothing
\right\}
\right|.
\tag{47}
$$

式 (47) 是由当前 seal 状态导出的数学量。它没有声称这些事件一定存在高效的联合求值方法。

还可以定义成员前沿偏斜：

$$
\operatorname{Skew}_n(\mathcal R_j)
=
\max_{v\in\mathcal R_j}\lambda_n(v)
-
\min_{v\in\mathcal R_j}\lambda_n(v).
\tag{48}
$$

式 (48) 较大时，一些成员已经知道得很远，但整个 region 仍受最慢成员限制。本文不把偏斜小规定为合法性条件。

### 10.3 三层理论

本文建议以后依次研究：

1. **一般层**：允许任意区域划分，只证明完整候选集合、唯一计算、合法次序无关和分段继续；
2. **附加结构层**：研究 region 收缩关系无环、区域局部性或前沿偏斜上界等条件，是否推出更简单的推进顺序和更大的式 (47)；
3. **联合求值层**：再证明某些 selector、状态更新与完整节点函数，对多个逻辑时间存在与逐时间递归相等的联合求值函数。

region-DAG 可以成为第二层的一种充分条件，但不是第一层的合法性公理。即使 region-DAG 成立，也不能自动推出第三层；一般状态递归仍可能必须逐时间求值。

### 10.4 图与划分只给出可用并行性的上界

固定图、逻辑时延、区域划分和 selector/state 依赖决定哪些数学输入能够同时完整。解释器可以发现并利用这些位置，但不能在式 (37) 不成立时制造一个更大的完整 candidate set。

另一方面，即使式 (47) 很大，也还要证明相应函数确实存在联合求值公式。某些递归可以用结合运算或矩阵公式重写，另一些一般递归可能没有这种性质。

所以高性能结果由两类事实共同决定：

$$
\left(
\text{图与 region 给出的就绪窗口},
\text{节点函数的可联合求值性质}
\right).
$$

通用解释器负责保持正确性并利用已经证明的机会；它不负责保证任意合法图都同样快。

### 10.5 可选的 selector-history

本文核心 selector 没有跨逻辑时间可变状态。若以后确实需要，对每个 $j$ 给定非空集合 $H_j$、初值 $s_j^0\in H_j$，并把式 (18) 改成：

$$
\operatorname{Select}_{j,C}:
H_j
\times\mathbb N
\times\prod_{v\in C}D_v
\to
H_j\times\mathsf{Act}_{j,C}.
\tag{49}
$$

这时同一 region 的选择还必须按逻辑时间递增更新 $H_j$；式 (43) 也要加入切面处的 selector 状态。

式 (49) 仍然不把 region 变成消息节点，但它会增加跨时间状态依赖，并可能缩小能够联合求值的时间窗口。第一次证明本文模型时不需要加入它。

## 11. 当前证明目标

### 11.1 已经给出证明的两个引理

正文已经证明：

$$
\lambda_n(v)>\theta
\Longrightarrow
B^{(n)}_{v,\theta}=B_{v,\theta},
$$

以及：

$$
\lambda_n(\mathcal R_j)>\theta
\Longrightarrow
\mathcal C^{(n)}_{j,\theta}
=
\mathcal C_{j,\theta}.
$$

第二个结论正是“selector 的 candidate set 不会再增加”的数学形式。

### 11.2 完整输入下有限且唯一

需要检查第 3 节递归的每一步定义域，并完整证明：

- 每个 $(j,\theta)$ 至多选择一次；
- 每个 $(v,\theta)$ 至多采用一次状态；
- 每个 active $(v,\theta)$ 至多沿每条出边产生一条消息；
- 每个 active $(v,\theta)$ 至多向每个相连输出端口产生一个值；
- 全部事件、选择、消息和外部输出记录有限；
- 最终结果唯一。

### 11.3 合法异步次序与直接解释器相同

需要把第 5 节扩写成严格的合法次序定义，再证明任何完成同一有限逻辑时间边界的合法次序都得到相同的：

$$
(q_v)_{v\in V},
\qquad
M,
\qquad
Z,
\qquad
(\mathcal C_{j,\theta},\mathcal A_{j,\theta})_{j,\theta},
$$

以及相同的观察记录。证明建议使用第 5.6 节的 $(\theta,p)$ 归纳。

### 11.4 分段继续

需要证明式 (43) 确实保留未来计算所需的全部信息，并证明第 8.5 节要求的前缀加后缀等于一次直接计算。

### 11.5 受限模型的嵌入

需要证明：

1. 式 (45) 的单节点 always-active 条件精确还原局部 TimedDAG；
2. 给 SettleGraph 选择不发生跨 Token 同刻汇合的时间编码后，附录 S.9 的全坐标翻译成立。

这些目标完成以前，本文仍是学习中的候选定义，不是已经证明完备的通用 Graph 理论。

## 12. 建议的学习顺序

1. 用整数重新手算第 0 节，并分别改变消息的机器可见次序和逻辑时延，确认只有后者可能改变 candidate set。
2. 取两个输入端口和两个输出端口，按式 (28) 写出一个同时含两个外部输入原子的桶，再按式 (25) 写出两个不同端口的输出记录。
3. 从式 (31)--(35) 独立证明式 (37)，不看正文证明。
4. 手算第 6 节，并另造一组让 SD + pre 与 BO + post 的 active set 相同、最终状态不同的数。
5. 对第 7.6 节的三个节点，列出三个连续逻辑时间的 $P,S,U,E$ 位置，验证每条关系严格增加 $(\theta,p)$。
6. 选择一个 $b$，手算式 (42)--(44)，检查丢掉 $W_b$ 会使哪个未来桶错误。
7. 尝试补全第 11.2--11.4 节；遇到缺定义时先修改数学对象，不用程序行为填补定义。
8. 最后才把这些有限集合和函数逐项翻译成整数参考程序。

完成前七步以前，不需要证明 region-DAG、大块联合求值或硬件性能性质。

## 13. 明确延期的内容

本文暂时不加入：

- 固定节点图中的有向环；
- 零时延边；
- 一个节点在同一出边、同一发送时间产生多条消息；
- selector 读取未声明的跨 region 信息；
- 随墙钟时间、线程竞争或现实设备负载改变的 selector；
- 同一节点在同一逻辑时间参加多个 region；
- 未关闭完整桶就产生不可撤销状态或消息；
- 迟到消息修改已经发布的 active set；
- 随机 selector 所需的随机性状态；
- selector 概率、训练梯度和辅助损失；
- 任意机器中间步骤上的暂停恢复；
- region-DAG 推出大块推进的定理；
- packed attention 或其他联合求值的正确性与复杂度；
- 无限节点、无限输入或无限时间运行。

这些内容不是被否定，而是不能暗中成为本文定义或证明的前提。下一次扩展每次只应加入其中一项，并重新检查式 (37)、第 7.5 节的递增量和式 (43) 是否仍然充分。

## 14. 相关文档

本文是可独立阅读的完整版本。另一个更小、没有显式 region selector 的学习模型见：

- [[timed-dag-v0-learning-note|TimedDAG-v0：从有限集合与函数开始的定义]]

SettleGraph 当前权威语义见：

- [experiment-semantics-and-naming.md](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/experiment-semantics-and-naming.md)

旧 TIDE 长文只在本文已经提出具体问题时按需查阅，不能用其中未重新定义的术语反过来改变本文对象。

## 附录 S：计算机系统词汇与数学对象的对应（可选）

本附录不是正文数学定义的一部分。下面各块默认折叠；遇到相应词汇时再展开。每个词都说明它是数学对象的简称、导出量、计算机表示，还是尚待证明的性质。

> [!info]- S.0　identifier、schema、semantic coordinate、wall clock 与 chunk
> **1. identifier、ID（标识符）**
>
> - 正文直接用集合元素 $v\in V$、$a\in A$、$i\in\mathsf I$、$o\in\mathsf O$ 和 $j\in J$ 区分对象，不需要先把它们编码成字符串。
> - 若程序必须使用整数，可以给某个有限集合 $X$ 选择一个单射 $\operatorname{id}_X:X\to\mathbb N$。单射表示：
>   $$
>   x\ne x'
>   \Longrightarrow
>   \operatorname{id}_X(x)\ne\operatorname{id}_X(x').
>   $$
> - “ID 稳定”的最小数学含义是：$\operatorname{id}_X$ 在固定结构数据以后就是同一个函数；它不随第 4 节的阶段 $n$、消息可见次序或本次分块方式改变。
> - 例如可以固定一个单射 $\operatorname{id}_{\mathrm{event}}:V\times\mathbb N\to\mathbb N$。系统语言“由 schema 和语义坐标决定”在这里恰好表示：编码函数的定义域是规定好的积集合 $V\times\mathbb N$，输入只有 $(v,\theta)$，没有墙钟 $w$、阶段 $n$、线程号或块编号。
>
> **2. schema（数据形状约定）**
>
> - 它通常对应一个已经写出的集合或积集合。例如式 (5) 规定消息属于 $\mathbb N\times A\times P$，也就规定了三个坐标各自来自哪个集合。
> - schema 是计算机保存这些坐标时的类型与字段约定；正文真正使用的是积集合及其投影函数。
> - 改变字段名但保持这些集合与函数不变，只改变表示；删掉边坐标 $a$ 则可能改变数学对象，因为式 (8) 将不能再区分入边。
>
> **3. semantic coordinate（语义坐标）**
>
> - 这不是正文额外假设的一种时间。它只是“用哪个有序组唯一指出一个数学位置”的系统说法。
> - 本文的例子包括输入位置 $(i,t)$、节点事件位置 $(v,\theta)$、region 选择位置 $(j,\theta)$、图内发送位置 $(\theta,a)$ 和外部输出位置 $(\theta,o)$。
> - 有序组的坐标来自已经定义的集合；把机器线程号加入日志，不会使线程号自动成为上述有序组的一部分。
>
> **4. wall clock、machine time（墙钟、机器时间）**
>
> - 若记录现实完成时刻，可以另取 $w\in\mathbb R_{\ge0}$。正文的 Aggregate、Update、Select 和 Full 都没有 $w$ 这个自变量，所以改变 $w$ 不能改变它们的数学值。
> - 第 4 节的 $n\in\mathbb N$ 只排列机器操作先后，也不传入这些函数。逻辑时间 $\theta$ 则是消息、桶和状态事件定义中的坐标；三者不能互换。
>
> **5. chunk、chunk partition（块、分块）**
>
> - 若待计算的有限位置集合为 $E$，一次分块可数学化为非空子集族 $(E_1,\ldots,E_k)$，满足：
>   $$
>   E=\bigcup_{\ell=1}^k E_\ell,
>   \qquad
>   \ell\ne\ell'
>   \Longrightarrow
>   E_\ell\cap E_{\ell'}=\varnothing.
>   $$
> - 块只是在一次联合求值中把哪些位置放在一起。正文的语义位置仍是 $(v,\theta)$ 或 $(j,\theta)$，不会因分块边界改变。
> - 若两种分块得到不同的 $M^*$、$Z^*$、状态或 active sets，至少一种联合程序没有实现正文定义；“本次怎样分块”不是 selector 可以读取的新输入。

> [!info]- S.1　graph、port、node、edge、logical time、message、output 与 bucket
> **1. graph、spatial graph（图、固定空间图）**
>
> - 数学对应：式 (1) 的五元组 $G$。
> - 它在一次输入以前给定，只说明哪些节点之间允许沿边传值及每条边增加多少逻辑时间。
> - 它不是第 7 节由具体输入产生的细分事件图。
>
> **2. input/output port、ingress/egress（输入、输出端口）**
>
> - 数学对应：$\mathsf I,\mathsf O$ 及函数 $\gamma,\varepsilon$。
> - 输入端口 $i$ 向 $\gamma(i)$ 注入带位置和逻辑时间的外部值；输出端口 $o$ 只接收 $\varepsilon(o)$ 产生的外部输出记录。
> - 端口不是节点，也不因多个端口连接同一节点而把这些输入合成一个没有身份的值。
>
> **3. node、receiver（节点、接收节点）**
>
> - 数学对应：$v\in V$。
> - 节点持有 $S_v$ 中的私有状态，读取自己的完整桶，沿 $\operatorname{Out}(v)$ 中的边发送，并向 $\operatorname{OutPort}(v)$ 中的外部端口给值。
> - SettleGraph 的 receiver 翻译到本文时应对应节点，而不是 region。
>
> **4. edge、channel（边、通道）**
>
> - 数学对应：$a\in A$；起点、终点和时延分别为 $\alpha(a),\beta(a),\delta(a)$。
> - 若系统另说“节点计算逻辑耗时”和“传递逻辑耗时”，正文第 1.5 节把二者之和写入 $\delta(a)$；解释器只需读取这个总数。
> - 实现可以用队列、数组或网络连接表示一条边；这些表示不是数学定义本身。
>
> **5. logical time（逻辑时间）**
>
> - 数学对应：$\theta\in\mathbb N$。
> - 它参与式 (4)、(5)--(6)、完整桶和事件状态先后。
> - $\theta=5$ 不表示现实经过五秒，也不表示机器执行第五步。
>
> **6. message、payload（消息、承载值）**
>
> - 整条消息对应式 (5) 的 $(\theta,a,y)$。
> - payload 只对应 $y\in P$；发送时间与边身份不是 payload。
> - logical arrival 对应式 (6)，机器 visibility 对应消息何时进入第 4.1 节的 $H_n$。两者不能混同。
>
> **7. external output record（外部输出记录）**
>
> - 数学对应：式 (25) 的 $(\theta,o,y)$ 以及最终集合 $Z^*$。
> - 输出端口身份 $o$ 与逻辑时间 $\theta$ 都是记录的一部分；多个输出不是把若干值无标记地放进同一个列表。
> - 外部输出不返回图内，因此不参加节点桶或边 seal。
>
> **8. bucket、time bucket（桶、同刻输入桶）**
>
> - 数学对应：第 1.6 节的有限集合 $B_{v,\theta}$。
> - 同一节点、同一逻辑时间的全部原子只形成一个桶。集合没有消息到达顺序。
> - 外部输入原子保留端口 $i$，图内消息原子保留边 $a$；式 (8) 因而可以区分输入来源。
> - 把桶放在一个数组中是表示；是否完整由 seal 证明，不由数组当前是否为空证明。
>
> **9. DAG**
>
> - 固定 DAG 表示式 (1) 的节点边图没有有向环。
> - event DAG 表示第 7 节实际函数作用之间的因果关系没有有向环。
> - region partition 不是有向图，所以本文不要求它满足 DAG 条件。

> [!info]- S.2　region、selector、candidate、active、Top-K 与 routing
> **1. region（区域、选择域）**
>
> - 数学对应：式 (3) 的集合 $\mathcal R_j=\rho^{-1}(j)$。
> - 它只规定哪些节点在同一逻辑时间共同接受式 (18)。它不持有节点消息，不是固定空间图的新节点。
>
> **2. region partition（区域划分）**
>
> - 数学对应：满射 $\rho:V\to J$ 及其互不相交的原像族。
> - 每个节点恰好属于一个 region 是式 (2)--(3) 的结果，不是程序通过查表偶然做到的性质。
>
> **3. candidate、reached（候选、已到达）**
>
> - 数学对应：式 (15) 中满足 $B_{v,\theta}\ne\varnothing$ 的节点。
> - 某节点已经有一条可见消息只能说明它最终是 candidate；不能说明全部 candidates 已经出现。
> - candidate set 完整的证明是式 (37)。
>
> **4. selector（选择器、门控器）**
>
> - 数学对应：式 (18) 的函数族。
> - 程序中可以用神经网络、线性函数、固定规则或查表求它；这些只是同一数学函数的可能实现。
> - selector 的输出是 active set，不是边消息。
>
> **5. active、selected（激活、被选中）**
>
> - 数学对应：$v\in\mathcal A_{j,\theta}$，等价于 $\chi_{v,\theta}=1$。
> - active 决定是否执行式 (23)；是否采用状态还要看 $\omega$。
>
> **6. Top-K**
>
> - 它是式 (18) 的一种具体选择函数，且 active set 大小由式 (17) 限制。
> - 分数相等时必须由固定数学规则给出唯一结果，不能依赖线程完成次序。
>
> **7. routing、route（路由、实际路径）**
>
> - 在本文中，它可以由全部 active sets 和实际产生消息的边导出。
> - selector 不改变固定边集合；它通过决定哪些节点执行式 (23)，改变本次输入实际产生哪些消息。
> - route 不是输入以前另给的一张动态图。

> [!info]- S.3　proposal、pre/post、observe、commit、SD/BO 与 NodeCompute
> **1. proposal（候选更新、候选新状态）**
>
> - 数学对应：式 (11) 的 $\widetilde q_{v,\theta}$。
> - proposal 是一个纯函数值，不表示式 (22) 已经采用它。
> - 程序中的临时数组可以表示 proposal，但数组写入时间不进入本文语义。
>
> **2. content-only、pre-update、post-update**
>
> - content 对应式 (12)，只读取当前本地内容。
> - pre 对应式 (13)，读取旧状态 $q^-$ 与当前内容。
> - post 对应式 (14)，读取候选新状态 $\widetilde q$ 与当前内容。
> - post 不表示其他事件已经可以读取新状态；未来状态仍由式 (22) 决定。
>
> **3. Observe set、state update、commit（观察集合、状态更新、提交）**
>
> - Observe set 对应式 (20) 的 $\mathcal O_{j,\theta}$。
> - $\omega=1$ 表示采用候选新状态。
> - commit 的最小数学含义是式 (22)：以后更大逻辑时间事件读取 $q^+$ 而不是 $q^-$。
> - 这不自动提供数据库事务、断电恢复或某种 CPU 原子指令。
>
> **4. SD（selected-dispatch）**
>
> - 数学对应：$\mathcal O_{j,\theta}=\mathcal A_{j,\theta}$。
> - 只有 active candidates 采用当前内容形成的新状态。
> - SD 与 pre 是不同坐标；标准 SD 可以使用 content 或 pre。
>
> **5. BO（broadcast-observe）**
>
> - 数学对应：$\mathcal O_{j,\theta}=\mathcal C_{j,\theta}$。
> - 全部 candidates 采用新状态，仍只有 active candidates 完整计算和发送。
> - BO 与 post 是不同坐标；BO 也可以使用 content 或 pre。
>
> **6. expensive compute、NodeCompute、full compute（昂贵计算、节点完整计算）**
>
> - 数学对应：式 (23) 的 $\operatorname{Full}_v$。
> - 只有 $\chi=1$ 时求值；它读取式 (22) 已经决定的当前计算状态。
> - “昂贵”不是集合论性质，只说明实现希望避免为 inactive 节点求这个函数。
>
> **7. Emit、dispatch、send（发射、派发、发送）**
>
> - 数学对应：从式 (24) 的两个输出函数中取非 $\bot$ 值，并形成式 (25) 的图内消息或外部输出记录。
> - region 不发送消息或输出；active node 沿自己的固定出边发送，并向自己的命名输出端口给值。

> [!info]- S.4　seal、ready、barrier、frontier、watermark 与异步执行
> **1. seal（封闭下界）**
>
> - 精确定义只有式 (31)--(32)。例如 $\sigma_n(a)=b$ 表示边 $a$ 上所有尚未可见消息的逻辑到达时间都不小于 $b$。
> - 每个输入端口也有自己的 $\sigma_n^{\mathrm{in}}(i)$；一个节点的前沿同时取其所有图内入边与输入端口 seal 的最小值。
> - seal 是一个带全称量词的数学命题，不是队列中的特殊消息，也不是“已经等了足够久”。
> - seal $=5$ 仍允许逻辑时间恰好为 $5$ 的消息；关闭桶 $5$ 需要 seal $>5$。
>
> **2. node frontier（节点输入前沿）**
>
> - 数学对应：式 (33) 的 $\lambda_n(v)$。
> - 它是节点全部输入 seal 的最小值。$\lambda_n(v)>\theta$ 推出式 (34)，但不自动表示节点已经计算完这些桶。
>
> **3. region frontier、region seal（区域前沿、区域 seal）**
>
> - 数学对应：式 (35) 的 $\lambda_n(\mathcal R_j)$。
> - 严格说它是各节点前沿的导出最小值。若系统文档简称 region seal，仍必须保留式 (35) 的含义。
> - 它由最慢成员决定，不替代各条边 seal 的真实性证明。
>
> **4. ready（就绪）**
>
> - 它是一个谓词，不是新对象。
> - “region $(j,\theta)$ ready”至少展开成第 4.6 节三条：候选集合关闭、candidate 旧状态就绪、尚未选择。
> - 某个数组已经有数据、某个线程空闲或某些 candidates 已完成准备，都不能单独推出 ready。
>
> **5. barrier（屏障、等待点）**
>
> - 数学对应：式 (18) 必须等待第 4.6 节条件成立。
> - 它不表示所有机器线程同时停止；第 4.7 节允许独立准备不对外可见的值。
>
> **6. asynchronous、out-of-order visibility（异步、乱序可见）**
>
> - 数学对应：消息进入 $H_n$ 的次序不必服从式 (6) 的逻辑到达时间次序。
> - 异步不允许越过 seal，也不允许使用部分 candidate set 选择。
>
> **7. watermark（水位）**
>
> - 这个系统词用法不统一。若它表示输入已经确定到哪里，可对应式 (33) 或 (35)；若它表示节点已经完成到哪里，应对应第 5.4 节的另一种完成前沿。
> - 输入前沿与完成前沿是两个数学谓词，不能只因都叫 watermark 就混成一个数。
>
> **8. late message、no-backdating（迟到消息、不得倒填）**
>
> - 逻辑时间较小但机器较晚看见的消息不必非法。
> - 真正非法的是新可见消息满足 $\operatorname{arrival}(m)<\sigma_n(a)$，从而否定已经公布的式 (31)。

> [!info]- S.5　schedule、phase、event、runtime、workspace 与并发
> **1. schedule（计算次序、调度）**
>
> - 数学对应：第 5 节所描述的可见集合、seal、已准备位置、已选择位置和已完成位置随 $n$ 增长的序列。
> - 改变 schedule 可以改变独立作用的机器先后，不能改变式 (18) 或式 (22)--(24) 的输入。
>
> **2. phase、stage（阶段）**
>
> - 数学对应：第 7.5 节的 $p\in\{0,1,2,3\}$。
> - 多个阶段可以具有同一个逻辑时间 $\theta$；阶段编号只表达该事件内部与 selector 之间的因果顺序。
> - 阶段不是新的模型时间单位，也不表示固定现实耗时。
>
> **3. event（事件）**
>
> - 粗粒度节点事件位置是 $(v,\theta)$；第 7 节为了研究依赖，把它细分为 $P,U,E$，并另加入选择作用 $S$。
> - 消息不是事件；一个节点事件可以消费多条消息，也可以不产生消息。
>
> **4. runtime、executor（运行时、执行器）**
>
> - 指真正维护消息表示、节点状态、seal 和完成记录，并选择合法作用求值的程序。
> - runtime 是试图实现第 3--5 节的外部对象，不是数学图、selector 或节点函数本身。
>
> **5. scheduler（调度器）**
>
> - 数学投影是从当前满足就绪条件的位置中选择下一项或下一组求值。
> - scheduler 可以影响现实性能，却不能把 $\lambda_n(\mathcal R_j)\le\theta$ 的位置宣布为候选集合完整。
>
> **6. workspace、temporary buffer（临时工作区、临时缓冲）**
>
> - 数学对应：第 4.7 节中已经求出、但尚未成为节点持久状态或边消息的纯函数值。
> - 它可以保存 $h,d,\widetilde q$ 的编码；其他语义事件不得把它误当成式 (22) 已提交的状态。
>
> **7. concurrency、parallelism（并发、并行）**
>
> - 若两个作用之间在第 7 节的因果关系中不存在先后路径，数学语义不强迫它们使用某个机器顺序。
> - 是否真的同时执行还取决于有限资源和具体程序；无因果先后只提供许可，不提供性能保证。
>
> **8. atomic commit（原子提交）**
>
> - 当前最小数学含义是：其他语义事件只能读取式 (22) 以前的 $q^-$ 或式 (22) 以后确定的 $q^+$，不能读取未定义的部分状态。
> - 它不声称整个节点事件是一条处理器原子指令。实现可以分步写内存，但必须证明投影结果符合这个边界。

> [!info]- S.6　chunk、prefill、decode、packing、fast path 与 region-DAG
> **1. chunk（分块）**
>
> - 数学上应先说明它对应哪些输入位置或逻辑时间位置。例如式 (47) 计数的是当前已经关闭的非空 region-time 集合。
> - 一次接口调用或一段连续张量不是天然的语义 chunk；它只是某组数学输入的一种编码。
>
> **2. prefill**
>
> - 系统语境通常指一次给出一个已知输入前缀，并联合计算其中许多位置。
> - 对本文至少需要三项独立证明：相关桶已经关闭；相关 region selections 可以确定；联合节点程序等于逐时间应用式 (8)--(25)。
> - 较大的式 (47) 只帮助第一、二项，不自动证明第三项。
>
> **3. decode**
>
> - 系统语境通常指输入位置逐步增加，每次处理一个或少量新位置。
> - 若某个 prefill 程序声称与 decode 等价，必须比较图内消息、各端口外部输出、全部状态、candidate sets、active sets 和观察值，而不能只比较最终一个输出张量。
>
> **4. batching、packing（批处理、紧凑打包）**
>
> - 假设参考语义已经给出 $k$ 个作用的输入 $z_1,\ldots,z_k$。一个联合程序 $K$ 的正确性至少要求：
>   $$
>   \operatorname{Unpack}
>   \left(
>   K(\operatorname{Pack}(z_1,\ldots,z_k))
>   \right)
>   =
>   \left(
>   f_1(z_1),\ldots,f_k(z_k)
>   \right),
>   \tag{S1}
>   $$
>   其中右边是正文逐项函数的结果。
> - 一次联合程序调用不会把 $k$ 个不同的 $(v,\theta)$ 变成一个语义事件。
>
> **5. packed attention**
>
> - 它是某些具体状态、Read 和 Full 函数的联合求值程序。
> - seal 证明输入不再改变；packed-attention 等价证明说明对这些固定输入采用联合程序没有改变逐时间结果。两种证明不能互相替代。
>
> **6. region-DAG、region quotient DAG（区域收缩 DAG）**
>
> - 数学对应：第 7.6 节定义的关系 $Q_\rho$ 与图 $(J,Q_\rho)$。
> - 本文核心语义不使用这张图，也不要求它无环。
> - 它以后可以作为第 10.3 节第二层的附加结构条件，帮助证明 region 拓扑推进；不能作为式 (37) 的隐藏前提。
>
> **7. head-of-line blocking（最慢成员阻塞）**
>
> - 一个最小数学表现是某个成员 $v_0$ 使 $\lambda_n(\mathcal R_j)=\lambda_n(v_0)$，而其他成员前沿远大于它。
> - 式 (48) 可以记录成员差异，但它不是现实耗时，也不单独证明某个硬件程序很慢。
>
> **8. wavefront（波前推进）**
>
> - 可指一组已经满足就绪条件、彼此没有因果先后的 $(j,\theta)$ 或细分作用位置。
> - region 收缩图有环时，可能需要随逻辑时间在多个 regions 之间反复推进；这不等于第 7 节事件图有环。
>
> **9. fast path、fallback（快速路径、一般后备路径）**
>
> - 可以先对任意合法划分实现第 5 节的一般解释器，再对满足额外结构和代数条件的对象采用联合程序。
> - fast path 必须证明投影回正文结果；一般解释器正确不表示所有合法对象都具有相同性能。

> [!info]- S.7　continuation、checkpoint、replay、projection 与 refinement
> **1. continuation（续算所需数学状态）**
>
> - 当前逻辑切面上的候选 continuation 是式 (43) 的 $Q_b$。
> - 它保存节点状态、跨界消息和已产生的多端口输出前缀；无状态 selector 不需要额外保存 selector 状态。
> - $Z^{<b}$ 不影响未来计算；保留它只是为了恢复后仍能重建完整输出记录。若外部接收者已经可靠保存此前输出，计算端可以只保存这一事实而不重复保存值。
>
> **2. checkpoint（检查点、保存点）**
>
> - checkpoint 是 $Q_b$ 的某种计算机编码。若保存和读取函数为 $\operatorname{save}$ 与 $\operatorname{load}$，基本无损条件是：
>   $$
>   \operatorname{load}(\operatorname{save}(Q_b))=Q_b.
>   \tag{S2}
>   $$
> - 式 (S2) 不自动证明任意机器中间阶段都能保存；正文只定义完整逻辑时间切面。
>
> **3. replay、resume（重放、恢复）**
>
> - 数学对应：从相同 $Q_b$ 和相同式 (44) 再执行未来递归。
> - 与一次算完相同是第 8.5 节的证明目标，不是 replay 这个词自动保证的性质。
>
> **4. trace（轨迹、记录）**
>
> - 可由图内消息、带输出端口的外部输出，以及所有带 $(v,\theta)$ 或 $(j,\theta)$ 标签的 candidate、active、状态和观察值组成。
> - 墙钟耗时、线程号和日志打印顺序不自动属于语义 trace。
>
> **5. projection（投影）**
>
> - 数学上只是函数 $\Pi:X\to Y$，用于从更丰富的实现记录中删除临时数组、线程号等坐标，只保留正文结果。
> - 删除哪些坐标必须写明；不能只说“忽略实现细节”。
>
> **6. refinement（精化、实现正确关系）**
>
> - 若实现运行结果为 $\operatorname{Run}(x,s)$，其中 $s$ 是合法机器调度，参考结果为 $\operatorname{Direct}(x)$，典型证明目标是：
>   $$
>   \forall x,\ \forall s\in\operatorname{Legal}(x),
>   \qquad
>   \Pi(\operatorname{Run}(x,s))
>   =
>   \operatorname{Direct}(x).
>   \tag{S3}
>   $$
> - 式 (S3) 允许机器步骤不同，但不允许投影后的图内消息、外部输出、状态和选择结果不同。

> [!info]- S.8　四句系统语言的逐句数学翻译
> **句子一：“selector 所需的输入已经 ready。”**
>
> 本文基准解释器采用的充分条件是：
>
> 1. $\lambda_n(\mathcal R_j)>\theta$，所以式 (37) 成立；
> 2. 每个 candidate 的更小逻辑时间状态事件已经完成；
> 3. $(j,\theta)$ 尚未选择过。
>
> 对 pre/post，第二条是 selector 输入定义所需；对 content，它是第 4.6 节为了统一基准次序而采用的保守条件，可以在不改变数学结果时放宽。只说“已经收到一些消息”不能推出第一条。
>
> **句子二：“BO 读取更新后状态，SD 读取更新前状态。”**
>
> 这句话把两个坐标混在了一起。应拆成：
>
> - pre/post 由式 (13)--(14) 决定 selector 读取 $q^-$ 还是 $\widetilde q$；
> - SD/BO 由式 (20) 决定采用候选状态的是 active set 还是整个 candidate set。
>
> 因而 BO + pre 是合法条件，SD + post 也可以被单独定义。
>
> **句子三：“region-DAG 会给出更好的 seal。”**
>
> 在固定的 $(U_{i,n})_{i\in\mathsf I},H_n$ 与所有输入、边 seal 下，region-DAG 不改变式 (31)--(35) 的数值。更准确的候选命题是：某些区域结构允许一种计算次序，使各成员前沿更同步、更快地产生较大的式 (47)。这需要另行证明，不能作为 seal 定义的一部分。
>
> **句子四：“奇怪的 region 使高性能 prefill 不可行。”**
>
> 当前可以严格说的是：奇怪的划分可能使式 (35) 长期受某个成员限制，并使式 (47) 很小；通用解释器不能违反这个完整性上界。
>
> 但要证明任何高性能联合程序都不可能存在，还必须指定计算模型并排除特殊代数重写。本文没有提出这样的下界定理。

> [!info]- S.9　SettleGraph 与本文数学对象的对应
> 把 SettleGraph 放入本文模型时，需要给出一个明确翻译，使：
>
> - receiver 对应 $v\in V$；
> - graph ingress 与 graph egress 分别对应 $\mathsf I$ 和 $\mathsf O$ 中的端口；
> - receiver state 对应 $S_v$ 中的状态；
> - 每 Token 的聚合输入对应某个完整桶；
> - content/pre/post 对应式 (12)--(14)；
> - selection region 对应式 (3)；
> - active set 对应式 (19)；
> - SD/BO 对应式 (20)；
> - NodeCompute 与 Emit 对应式 (23)--(25)；
> - `DATA` 对应实际图内消息，`CLOSED` 对应没有图内消息且相应 seal 已经越过该逻辑时间；
> - 模型最终给外部的命名结果对应 $Z^*$ 中按输出端口标记的记录。
>
> 翻译正确性的目标不是只比较最终一个数，而是比较：
>
> $$
> \text{外部输出、全部状态、active sets、观察记录和逐边结算结果}.
> $$
>
> SettleGraph 按单个 Token 对固定 region 依赖图进行结算；要求 region 收缩图无环，就可以直接给出一个 region 拓扑序。本文则在每个逻辑时间形成 $\mathcal C_{j,\theta}$，并由正时延保证当前图内输出只影响更大时间。第 7.5 节已经用 $(\theta,p)$ 证明细分事件图无环，所以不把 region 收缩图无环作为一般合法性条件。
>
> 这不表示 SettleGraph 的条件错误。它定义的是一个更受限、可能更容易得到规则计算次序的子类。`fractal-latcarf` 的语义文档仍决定 SettleGraph 一侧的精确定义；本文只提供目标模型中的数学位置，尚未声称已经完成整个翻译证明。
