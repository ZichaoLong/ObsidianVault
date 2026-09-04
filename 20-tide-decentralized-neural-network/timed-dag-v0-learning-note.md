---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-04
tags:
  - tide
  - timed-dag
  - logical-time
  - mathematics
  - learning-note
---

# TimedDAG-v0：从有限集合与函数开始的定义

> [!summary] 阅读约定
> 本文只预设有限集合、函数、有限序列和数学归纳法。一个名称必须在定义之后才能承担推理；若正文使用了没有定义的专门词，那是本文需要修正的问题，不是读者应当自行补齐的背景知识。
>
> 第一次只读第 0 节并完成末尾四题，然后停止。第 1--2 节把这个例子一般化；第 3 节讨论消息尚未全部出现时怎样安全计算。后面的内容在准备相应证明时再读。

本文不是一般 Graph 的最终理论。它只研究一个最小问题：

> 两个不同输入位置产生的量，能否在同一节点、同一逻辑时刻组成一个集合，并由一次函数作用共同处理？

当前路线入口见 [[current-mainline]]。

## 0. 先说明究竟有哪两张图

本文会定义两张不同的图。

1. **固定空间图**：计算开始前给定的有限图。它说明哪些节点之间允许传值。
2. **事件图**：给定具体输入后，由实际发生的函数作用构成的图。它说明这一次计算中，哪个函数作用影响了哪个函数作用。

“DAG”表示有限且没有有向环的有向图；有向环的精确定义在第 1.2 节。TimedDAG-v0 当前要求固定空间图是 DAG；由一次输入产生的事件图也将是 DAG。前者是预先给定的数学数据，后者是计算结果的一部分。第 4 节会分别定义它们。

相对于 SettleGraph，本文只增加一件事：SettleGraph 把不同输入位置分开结算；TimedDAG-v0 允许它们在到达时间相等时进入同一个集合。

### 0.1 第一次只看这个例子

记：

$$
\mathbb N=\{0,1,2,\ldots\}.
$$

对任意集合 $X$，用 $\mathcal P_{\mathrm{fin}}(X)$ 表示 $X$ 的全部有限子集所成的集合。

设输入只有位置 $0$ 和位置 $1$。给每个位置规定一个自然数，称为逻辑注入时间：

$$
\iota(0)=0,
\qquad
\iota(1)=1.
$$

假设位置 $0$ 产生的量经过总延迟 $5$ 后到达节点 $v$，位置 $1$ 产生的量经过总延迟 $4$ 后也到达 $v$。把逻辑到达时间定义为“逻辑注入时间加总延迟”，则：

$$
0+5=1+4=5.
$$

把这两个到达的量分别记为 $m_0,m_1$，并定义：

$$
B_{v,5}=\{m_0,m_1\}.
$$

$B_{v,5}$ 只是“到达节点 $v$、逻辑到达时间等于 $5$ 的全部量”所成的集合。

给定两个集合 $S,Y$，并给定函数：

$$
f_v:S\times\mathbb N\times
\mathcal P_{\mathrm{fin}}(\{m_0,m_1\})
\to S\times Y.
$$

$S$ 的元素表示节点从过去保留的量，$Y$ 的元素表示本次产生的结果。取 $q\in S$，在 $(v,5)$ 只计算一次：

$$
f_v(q,5,\{m_0,m_1\}).
$$

这就是本文唯一要新增的现象。它不同于先计算：

$$
f_v(q,5,\{m_0\})=(q',y'),
$$

再计算：

$$
f_v(q',5,\{m_1\}).
$$

这种做法调用了两次函数，而且第二次使用第一次产生的新状态 $q'$；一般而言，它不会等于联合计算。

### 0.2 第一次阅读的四道题

1. 等式 $\iota(1)=1$ 是模型必须满足的公理，还是本例对函数 $\iota$ 的一个选择？若改成 $\iota(t)=2t$，输入位置是否改变？
2. 若一台机器先看见 $m_1$、后看见 $m_0$，集合 $\{m_0,m_1\}$ 是否改变？
3. 把两个量放在同一个矩阵中，却调用两次 $f_v$，是否等于上面的一次联合计算？
4. 真正的新困难是否是“如何算 $f_v$”，还是“如何证明不会再有第三个时间为 $5$ 的量到来”？

答案是：它只是本例的选择，位置不变而逻辑注入时间改变；集合不改变；不等于；后一项。第 1--2 节只把这个例子写成一般有限图，第 3 节才定义“不会再来”的条件。

第一次阅读到这里即可停止。

## 1. 完整输入已经给定时，怎样定义一次计算

本节暂时假设全部输入都已知。这样可以先定义“正确答案是什么”，再在第 3 节研究消息以任意先后次序出现时怎样得到同一个答案。

### 1.1 数、区间与有限子集

定义：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $b\in\mathbb N$，定义：

$$
[b]=\{n\in\mathbb N\mid n<b\}.
$$

对 $0\le c\le b$，定义：

$$
[c,b)=\{n\in\mathbb N\mid c\le n<b\}.
$$

对集合 $X$，用 $\mathcal P_{\mathrm{fin}}(X)$ 表示 $X$ 的全部有限子集所成的集合。对集合 $I,Z$，用 $Z^I$ 表示全部函数 $I\to Z$ 所成的集合。

### 1.2 固定空间图

定义一个六元组：

$$
G=(V,A,\alpha,\beta,\delta,v_{\mathrm{in}}).
\tag{1}
$$

它的各项含义如下。

- $V$ 是有限非空集合；其元素称为**节点**。
- $A$ 是有限集合；其元素称为**边**。
- $\alpha:A\to V$ 给出边的起点。
- $\beta:A\to V$ 给出边的终点。
- $\delta:A\to\mathbb N_{>0}$ 给出边的延迟。
- $v_{\mathrm{in}}\in V$ 是输入节点。

这里一条边 $a$ 的方向是：

$$
\alpha(a)\longrightarrow\beta(a).
$$

边是集合 $A$ 的元素，所以即使两条边具有相同起点和终点，它们仍可以是 $A$ 中两个不同的元素。

对 $k\ge1$，一条长度为 $k$ 的有向路径是边的有限序列 $(a_1,\ldots,a_k)$，满足：

$$
\beta(a_i)=\alpha(a_{i+1})
\qquad (1\le i<k).
$$

若 $\alpha(a_1)=u$ 且 $\beta(a_k)=v$，就称它是从 $u$ 到 $v$ 的路径。

若还满足 $\beta(a_k)=\alpha(a_1)$，则称这条非空路径为有向环。

TimedDAG-v0 要求：

1. $G$ 没有有向环；
2. 没有边以 $v_{\mathrm{in}}$ 为终点；
3. 每个 $v\ne v_{\mathrm{in}}$ 都存在一条从 $v_{\mathrm{in}}$ 到 $v$ 的有向路径。

“DAG”在本文中正是“有限且没有有向环的有向图”的缩写，不附带其他含义。

对 $v\in V$，定义其入边集和出边集：

$$
\operatorname{In}(v)=\{a\in A\mid\beta(a)=v\},
$$

$$
\operatorname{Out}(v)=\{a\in A\mid\alpha(a)=v\}.
$$

因为 $G$ 有限且无环，存在一个节点排列：

$$
(v_0,v_1,\ldots,v_{|V|-1}),
$$

使每条边的起点都排在终点之前。本文把满足这个条件的排列称为**拓扑序**。

### 1.3 输入位置、输入值与逻辑时间

固定一个非空集合 $P$，称为值集合。神经网络中可以取 $P=\mathbb R^d$；第一次手算时可以取 $P=\mathbb Z$。

固定输入长度 $L\in\mathbb N$。一次输入是函数：

$$
x:[L]\to P.
$$

本文把二元组 $(t,x(t))$ 称为第 $t$ 个 **Token**。因此 Token 在本文中没有未定义的内部结构：它只是输入位置及该位置的值。

再给定严格递增函数：

$$
\iota:[L]\to\mathbb N,
\qquad
t<t'\Longrightarrow\iota(t)<\iota(t').
\tag{2}
$$

$\iota(t)$ 称为第 $t$ 个输入的**逻辑注入时间**。

逻辑时间只是自然数标签。式 (2) 没有声称计算一共经过了多少秒，也没有声称某台机器何时完成工作。节点函数只能看到这个自然数，不能看到现实中的完成时刻。

### 1.4 消息

一条候选消息定义为三元组：

$$
m=(\theta,a,y)
\in
\mathbb N\times A\times P.
\tag{3}
$$

其数学含义由下列函数完全给出：

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
\operatorname{arrival}(m)=\theta+\delta(a).
\tag{4}
$$

式 (4) 中的 arrival 仍然是逻辑时间，不是现实中的送达时刻。

TimedDAG-v0 暂时规定：节点 $\alpha(a)$ 在一个逻辑时刻 $\theta$ 至多沿 $a$ 产生一条消息。因此二元组 $(\theta,a)$ 已经足以区分本模型中的消息。两条消息的值即使相等，只要它们的 $(\theta,a)$ 不同，就仍是两条不同消息。

形式上，消息集合 $M$ 必须满足：

$$
(\theta,a,y)\in M,
\quad
(\theta,a,y')\in M
\Longrightarrow
y=y'.
$$

下文出现的消息集合都默认满足这个条件。

### 1.5 节点的状态与函数

对每个节点 $v\in V$，给定：

- 非空状态集合 $S_v$；
- 初始状态 $q_v^0\in S_v$；
- 非空观察值集合 $R_v$。

状态一词在本文中只表示 $S_v$ 的一个元素。它概括节点已经处理的过去输入中、未来计算仍然需要的全部信息。

若不需要额外记录节点事件，可以取 $R_v=\{*\}$；这里 $*$ 只是唯一的占位元素。

定义输入原子集合。对输入节点：

$$
\mathsf{InAtom}
=
\{(0,t,y)\mid t\in[L],\ y\in P\}.
$$

对节点 $v$ 的消息原子：

$$
\mathsf{MsgAtom}_v
=
\{(1,m)\mid m\text{ 满足式 (3)，且 }
\operatorname{receiver}(m)=v\}.
$$

开头的 $0$ 和 $1$ 只用于区分“外部输入”和“边上传来的消息”。定义：

$$
\mathsf{Atom}_v
=
\begin{cases}
\mathsf{InAtom}\cup\mathsf{MsgAtom}_v,
&v=v_{\mathrm{in}},\\
\mathsf{MsgAtom}_v,
&v\ne v_{\mathrm{in}}.
\end{cases}
$$

定义原子的时间：

$$
\operatorname{atime}(0,t,y)=\iota(t),
\qquad
\operatorname{atime}(1,m)=\operatorname{arrival}(m).
$$

节点 $v$ 在时间 $\theta$ 的一个**输入桶**是有限集 $B\subseteq\mathsf{Atom}_v$，并满足：

$$
z\in B\Longrightarrow\operatorname{atime}(z)=\theta.
$$

“桶”只是“具有相同节点和相同逻辑时间的输入所成的集合”的简称；集合没有先后次序。式 (5) 为书写简洁仍在全部有限子集上定义，但实际计算只把满足上述时间条件的桶传给它。

取一个不属于 $P$ 的新符号 $\bot$，并定义：

$$
P_\bot=P\cup\{\bot\}.
$$

对每个节点 $v$，给定函数：

$$
F_v:
S_v
\times\mathbb N
\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)
\longrightarrow
S_v
\times(P_\bot)^{\operatorname{Out}(v)}
\times R_v.
\tag{5}
$$

若：

$$
F_v(q,\theta,B)=(q',o,r),
$$

则：

- $q'$ 是新状态；
- $o:\operatorname{Out}(v)\to P_\bot$ 是每条出边的输出选择；
- $r\in R_v$ 是这次函数作用留下的观察值；
- $o(a)=\bot$ 表示这次不在边 $a$ 上产生消息；
- $o(a)=y\in P$ 表示产生消息 $(\theta,a,y)$。

式 (5) 的输入是集合 $B$，所以交换 $B$ 中元素的书写顺序不会改变函数输入。若某个节点需要区分两条入边，它可以读取消息中的边 $a$；它不需要依靠消息先被写在集合的哪一行。

本文要求 $F_v$ 是全函数。“全函数”在这里表示：对定义域中的每个 $(q,\theta,B)$，式 (5) 都有且只有一个值。

一次**节点事件**定义为：在某个 $(v,\theta)\in V\times\mathbb N$ 上，对非空输入桶应用一次 $F_v$。节点与逻辑时间的二元组 $(v,\theta)$ 就是该事件在数学中的位置。

### 1.6 按拓扑序定义完整计算

现在给出一个有限递归，它定义完整输入 $(x,\iota)$ 的计算结果。

先取第 1.2 节的一组拓扑序。令消息集合 $M$ 初始为空，并令每个节点的状态为 $q_v^0$。

依次处理拓扑序中的节点 $v$。在处理 $v$ 时，所有可能向 $v$ 发送消息的节点已经处理完毕。定义 $v$ 的非空时间集合：

$$
T_v
=
\{\iota(t)\mid v=v_{\mathrm{in}},\ t\in[L]\}
\cup
\{\operatorname{arrival}(m)
\mid m\in M,\ \operatorname{receiver}(m)=v\}.
\tag{6}
$$

对每个 $\theta\in\mathbb N$，定义完整输入桶：

$$
\begin{aligned}
B_{v,\theta}
= {} &
\{(0,t,x(t))
\mid v=v_{\mathrm{in}},\ \iota(t)=\theta\}
\\
&\cup
\{(1,m)
\mid m\in M,
\operatorname{receiver}(m)=v,
\operatorname{arrival}(m)=\theta\}.
\end{aligned}
\tag{7}
$$

由式 (6)--(7)，$B_{v,\theta}$ 非空当且仅当 $\theta\in T_v$。把有限集合 $T_v$ 按自然数从小到大写成：

$$
\theta_1<\theta_2<\cdots<\theta_k.
$$

从 $q_v^0$ 开始，按 $\theta_1,\ldots,\theta_k$ 的顺序应用式 (5)。每次得到 $o(a)=y\in P$ 时，把消息 $(\theta_j,a,y)$ 加入 $M$；同时记录观察值：

$$
((v,\theta_j),r_{v,\theta_j}).
$$

处理完全部节点后，记最终消息集合为 $M^*$，全部事件位置的集合为：

$$
\mathcal E^*
=
\{(v,\theta)\mid v\in V,\ \theta\in T_v\}.
\tag{8}
$$

这段有限递归就是本文所说的**直接解释器**：解释器不是另一个神秘对象，而是第 1.6 节列出的计算顺序。

### 1.7 为什么上述递归一定是有限的

输入节点至多有 $L$ 个非空时间桶，所以它至多发生 $L$ 个事件；每个事件在每条出边上至多产生一条消息，因此输入节点产生的消息有限。

沿拓扑序归纳。假设所有具有某条边 $a$ 满足 $\beta(a)=v$ 的节点 $\alpha(a)$ 都只产生有限条消息，则 $v$ 只收到有限条消息，因而式 (6) 中的 $T_v$ 有限；所以 $v$ 只发生有限个事件并产生有限条消息。

节点集合 $V$ 有限，因此 $M^*$、$\mathcal E^*$ 和全部观察值都有限。这是集合有限性结论；实际程序是否能算出每个 $F_v$，是第 8 节单独说明的另一个问题。

## 2. 用一般定义重写第 0 节的例子

对路径 $\pi=(a_1,\ldots,a_k)$，定义总延迟：

$$
\Delta(\pi)=\sum_{i=1}^{k}\delta(a_i).
$$

取 $L=2$、$\iota(0)=0$、$\iota(1)=1$。若两个输入产生的量分别沿 $\pi_0,\pi_1$ 到达 $v$，且：

$$
\Delta(\pi_0)=5,
\qquad
\Delta(\pi_1)=4,
$$

那么式 (4) 给出两个最终消息 $m_0,m_1$ 的到达时间都是 $5$。式 (7) 因而给出：

$$
B_{v,5}=\{(1,m_0),(1,m_1)\}.
\tag{9}
$$

第 0 节的 $f_v$ 正是这里只保留新状态和最终结果时的 $F_v$。一般定义仍然只在 $(v,5)$ 对整个集合 (9) 应用一次函数。

## 3. 消息没有同时出现时，何时可以安全计算

第 1 节从完整消息集合 $M^*$ 定义了答案。本节研究某一阶段只看见其中一部分消息时，怎样证明一个桶已经完整。

### 3.1 看见的子集

用 $n\in\mathbb N$ 表示“现在已经进行了第几个外部操作”。这个 $n$ 只给操作的先后次序编号，不会传入任何 $F_v$。

在第 $n$ 阶段，设：

$$
U_n\subseteq[L]
$$

是已经看见的输入位置集合，并设：

$$
H_n\subseteq M^*
$$

是已经看见的消息集合。

这里没有要求消息按照 $\operatorname{arrival}$ 从小到大被看见。若到达标签为 $8$ 的消息先进入 $H_n$，到达标签为 $5$ 的消息以后才进入，这仍是允许的。本文把这种“看见的先后次序不必服从逻辑到达时间”的情形称为**异步出现**。

节点在第 $n$ 阶段实际看见的桶定义为：

$$
\begin{aligned}
B^{(n)}_{v,\theta}
= {} &
\{(0,t,x(t))
\mid v=v_{\mathrm{in}},\ t\in U_n,\ \iota(t)=\theta\}
\\
&\cup
\{(1,m)
\mid m\in H_n,
\operatorname{receiver}(m)=v,
\operatorname{arrival}(m)=\theta\}.
\end{aligned}
\tag{10}
$$

### 3.2 封闭下界

给定函数 $\sigma_n:A\to\mathbb N$，并给输入流一个自然数 $\sigma_n^{\mathrm{in}}$。

定义：$\sigma_n(a)=b$ 是第 $n$ 阶段关于边 $a$ 的**有效封闭下界**，当且仅当：

$$
\forall m\in M^*\setminus H_n,
\quad
\operatorname{edge}(m)=a
\Longrightarrow
\operatorname{arrival}(m)\ge b.
\tag{11}
$$

定义：$\sigma_n^{\mathrm{in}}=b$ 是输入流的有效封闭下界，当且仅当：

$$
\forall t\in[L]\setminus U_n,
\quad
\iota(t)\ge b.
\tag{12}
$$

式 (11) 的意思是：尚未看见的边 $a$ 消息中，不再有到达时间小于 $b$ 的消息。式 (12) 对输入位置表达同一件事。

等价地，它们分别写成：

$$
\{m\in M^*
\mid \operatorname{edge}(m)=a,
\operatorname{arrival}(m)<b\}
\subseteq H_n,
$$

$$
\{t\in[L]\mid\iota(t)<b\}
\subseteq U_n.
$$

本文以后把这样的数简称为 **seal**。所以 seal 没有定义之外的含义；它就是满足式 (11) 或式 (12) 的下界。声明这个数的一方还需要说明相应的全称命题为什么成立；这个说明才是证明。

随着 $n$ 增加，$U_n,H_n$ 只能增大，$\sigma_n(a)$ 与 $\sigma_n^{\mathrm{in}}$ 只能不减小。若已经宣布 $\sigma_n(a)=b$，以后再加入一条到达时间小于 $b$ 的边 $a$ 消息，就违反式 (11)。

定义桶 $(v,\theta)$ 在第 $n$ 阶段已经关闭，当且仅当：

$$
\left(
v=v_{\mathrm{in}}
\Longrightarrow
\sigma_n^{\mathrm{in}}>\theta
\right)
\land
\left(
\forall a\in\operatorname{In}(v),
\ \sigma_n(a)>\theta
\right).
\tag{13}
$$

严格不等号不能改成大于等于。例如 $\sigma_n(a)=5$ 只排除了到达时间小于 $5$ 的新消息，并没有排除以后出现一条到达时间恰好为 $5$ 的消息。

### 3.3 关闭桶不再改变

**引理。** 若式 (13) 对 $(v,\theta)$ 成立，则：

$$
B^{(n)}_{v,\theta}=B_{v,\theta}.
\tag{14}
$$

这里右边是式 (7) 的完整桶。

**证明。** 已看见的输入和消息都属于完整输入与 $M^*$，所以左边包含于右边。反过来，假设右边有一个尚未出现在左边的元素。

- 若它是输入原子，则 $v=v_{\mathrm{in}}$，其时间为 $\theta$。式 (12) 和 $\sigma_n^{\mathrm{in}}>\theta$ 排除了它尚未被看见的可能。
- 若它是边 $a$ 上的消息，则式 (11) 和 $\sigma_n(a)>\theta$ 排除了它尚未被看见的可能。

所以右边也包含于左边，式 (14) 成立。∎

因此，等待的对象不是“再等若干秒”，而是式 (13) 这个可以进入证明的条件。

### 3.4 允许哪些计算先后次序

设 $D_n\subseteq\mathcal E^*$ 是第 $n$ 阶段已经计算的事件位置集合。一串集合：

$$
(U_n,H_n,D_n,\sigma_n^{\mathrm{in}},\sigma_n)_{n=0}^{N}
\tag{15}
$$

称为一个合法计算次序，当且仅当：

1. 对每个 $n$，$\sigma_n^{\mathrm{in}}$ 和 $\sigma_n$ 都满足式 (11)--(12)；
2. $U_n,H_n,D_n$ 随 $n$ 单调增大，两个 seal 随 $n$ 单调不减；
3. 消息 $(\theta,a,y)$ 进入 $H_n$ 以前，事件 $(\alpha(a),\theta)$ 已经进入 $D_n$；
4. 事件 $(v,\theta)$ 进入 $D_n$ 时，式 (13) 成立且可见桶非空；
5. 若同一节点还有更小逻辑时间的非空桶，则对应事件已经进入 $D_n$；
6. 每次事件都对式 (10) 的整个集合应用一次式 (5)。

下标 $n$ 只描述式 (15) 的排列次序。改变这个排列而保持六条条件，就是改变实际计算的先后次序而不改变数学模型。式 (15) 是相对于第 1.6 节完整结果的正确性条件，不是用来循环定义第二套答案。

### 3.5 seal 怎样沿边推出

定义：若节点 $v$ 的所有逻辑时间小于 $b$ 的完整非空桶都已经计算，并且式 (13) 已保证这些桶不会再增加元素，就称 $v$ 已完成到 $b$。

若 $v$ 已完成到 $b$，则它以后尚未发生的事件时间都不小于 $b$。因此对任意 $a\in\operatorname{Out}(v)$，以后尚未产生的消息满足：

$$
\operatorname{arrival}(m)
=
\operatorname{send}(m)+\delta(a)
\ge
b+\delta(a).
$$

还必须等待已经产生、且到达时间小于 $b+\delta(a)$ 的边 $a$ 消息全部进入 $H_n$。在这个条件也成立后，$M^*\setminus H_n$ 中剩余的边 $a$ 消息只能来自发送时间不小于 $b$ 的事件，因而 $b+\delta(a)$ 满足式 (11)，可以作为边 $a$ 的新 seal。

这就是“先让消息可见，再让越过它的 seal 可见”的数学原因。由于空间图是 DAG，可以沿拓扑序从输入节点向后反复使用这个推理。

## 4. 由一次计算产生的事件 DAG

固定空间图就是式 (1) 的 $G$。它在输入 $x$ 之前已经给定。

现在由第 1.6 节的完整计算定义另一张图：

$$
\mathcal D_x=(\mathcal E^*,\leadsto).
\tag{16}
$$

顶点集 $\mathcal E^*$ 已由式 (8) 定义。关系 $\leadsto$ 由两类边组成。

第一类是消息影响。若消息 $m=(\theta,a,y)\in M^*$，则加入：

$$
(\alpha(a),\theta)
\leadsto
(\beta(a),\theta+\delta(a)).
\tag{17}
$$

第二类是同一节点的状态先后。若 $v$ 的事件时间依次为：

$$
\theta_1<\theta_2<\cdots<\theta_k,
$$

则对 $1\le i<k$ 加入：

$$
(v,\theta_i)\leadsto(v,\theta_{i+1}).
\tag{18}
$$

式 (17) 中 $\delta(a)>0$，式 (18) 中 $\theta_i<\theta_{i+1}$，所以每一条 $\leadsto$ 边都严格增大逻辑时间。沿有向边走一圈不可能回到原来的自然数，因此 $\mathcal D_x$ 没有有向环。

结论是：

> TimedDAG-v0 是固定空间 DAG $G$ 上的一套计算定义；每个具体输入 $x$ 又产生一张动态事件 DAG $\mathcal D_x$。事件图不是预先交给解释器的另一张固定图。

保留空间图无环，是为了让第 1.6 节的拓扑序构造保持简单。下一阶段才考虑空间图有环、但式 (17) 仍严格增加时间的情形。

## 5. 在逻辑时间边界停止和继续

### 5.1 边界

给定 $b\in\mathbb N$，把事件分为：

$$
\mathcal E^{<b}
=
\{(v,\theta)\in\mathcal E^*\mid\theta<b\},
$$

$$
\mathcal E^{\ge b}
=
\{(v,\theta)\in\mathcal E^*\mid\theta\ge b\}.
$$

整数 $b$ 连同这个分割称为一个**逻辑时间边界**，也简称 cut。它不是把某个数组机械地切成两块，而是按事件的逻辑时间定义的集合分割。

### 5.2 边界状态

令 $q_v^b$ 表示节点 $v$ 处理完全部时间小于 $b$ 的事件后的状态。定义穿过边界、尚待右侧使用的消息集合：

$$
W_b
=
\{m\in M^*
\mid
\operatorname{send}(m)<b
\le
\operatorname{arrival}(m)\}.
\tag{19}
$$

定义边界状态：

$$
Q_b
=
\left(
b,
(q_v^b)_{v\in V},
W_b
\right).
\tag{20}
$$

本文把能够从边界继续计算所保留的数学对象称为 **continuation**；在 TimedDAG-v0 的这个最小模型中，候选 continuation 就是式 (20)。以后若加入计时器、一次事件内部的未完成工作或环，式 (20) 很可能不再充分。

观察值按事件位置记录。定义：

$$
\mathcal R_{[c,b)}
=
\left\{
((v,\theta),r_{v,\theta})
\middle|
(v,\theta)\in\mathcal E^*,
c\le\theta<b
\right\}.
\tag{21}
$$

### 5.3 分段计算等式

定义这一段进入系统的输入：

$$
I_{[c,b)}
=
\{(t,x(t))\mid c\le\iota(t)<b\}.
\tag{22}
$$

用：

$$
\Phi_{c,b}(Q_c,I_{[c,b)})
=
(Q_b,\mathcal R_{[c,b)})
\tag{23}
$$

表示：从式 (20) 的边界状态出发，只计算逻辑时间位于 $[c,b)$ 的事件，保存所有跨过 $b$ 的消息，并返回这一段的观察值。

初始边界状态是：

$$
Q_0
=
\left(
0,
(q_v^0)_{v\in V},
\varnothing
\right).
$$

设：

$$
(Q_c,\mathcal R_{[0,c)})
=
\Phi_{0,c}(Q_0,I_{[0,c)}),
$$

再设：

$$
(Q_b,\mathcal R_{[c,b)})
=
\Phi_{c,b}(Q_c,I_{[c,b)}).
$$

分段计算需要证明的等式是：若

$$
(\widetilde Q_b,\widetilde{\mathcal R}_{[0,b)})
=
\Phi_{0,b}(Q_0,I_{[0,b)}),
$$

则：

$$
Q_b=\widetilde Q_b,
\tag{24}
$$

$$
\mathcal R_{[0,c)}
\cup
\mathcal R_{[c,b)}
=
\widetilde{\mathcal R}_{[0,b)}.
\tag{25}
$$

式 (24)--(25) 就是本文所说的“停止后继续，与一次算完相同”。它不依赖 chunk 这个词；若其他文档说 chunk，在本文中只能指式 (22) 这样的输入区间。

## 6. TimedDAG-v0 当前需要证明的四个结果

前面的式子定义了对象，但尚未自动证明所有想要的性质。当前只保留以下四个证明目标。

### 6.1 有限边界完成

对每个 $b\in\mathbb N$：

$$
|\mathcal E^{<b}|
\le
|V|b.
\tag{26}
$$

因为 $\mathcal E^{<b}\subseteq V\times[b]$，式 (26) 立即成立。还需结合第 3.5 节证明：只要输入的 seal 已越过 $b$，第 1.6 节的构造能在有限次函数作用后证明所有节点完成到 $b$，而不会把“暂时没看见消息”误当成“以后没有消息”。

### 6.2 合法计算次序无关

对任意两串满足式 (15) 后六条条件、并且最终都恰好满足

$$
D_N=\mathcal E^{<b}
$$

的合法计算次序，需要证明它们得到相同的：

$$
(q_v^b)_{v\in V},
\qquad
M^*\text{ 在时间 }b\text{ 以前确定的部分},
\qquad
\mathcal R_{[0,b)}.
$$

建议按逻辑时间 $\theta$ 归纳。第 3.3 节保证关闭桶相同；式 (5) 是函数；式 (17)--(18) 保证一个事件只依赖更早的事件。

### 6.3 分段计算

证明式 (20) 确实保留了未来所需的全部信息，再证明式 (24)--(25)。不能仅通过若干整齐例子就假定该等式成立。

### 6.4 SettleGraph 是受限情形

需要给出第 7 节的两个函数 $\mathcal T$ 和 $\Pi$，并证明式 (28)。这保证 TimedDAG-v0 没有在旧对象上悄悄改变已经定义的输出、状态或边结算。

四项全部完成之前，TimedDAG-v0 仍是学习中的候选定义，不是已经完成的通用 Graph 理论。

## 7. 怎样把 SettleGraph 放进这个模型

本节只给证明的形状，不把它冒充成已经完成的定理。

为了写出这个证明的形状，只使用 SettleGraph Plan 的下列数学数据：

- 单个 Token 的有限操作集合 $O$；
- $O$ 上没有有向环的依赖关系 $\prec$；
- 每个操作的确定函数；
- 最终输出、节点状态和逐边结算记录。

逐边结算记录只有两种形式：$\operatorname{DATA}(y)$ 表示边上有值 $y$，$\operatorname{CLOSED}$ 表示已经确定该边没有值。`fractal-latcarf` 的正式 SettleGraph 定义负责给出上述集合、关系和函数的具体内容。

因为 $(O,\prec)$ 有限且无环，可以选择单射：

$$
r:O\to\{0,1,\ldots,R\},
$$

满足：

$$
o\prec o'
\Longrightarrow
r(o)<r(o').
$$

取整数 $K>R$，把第 $t$ 个 Token 的操作 $o$ 放在逻辑时间：

$$
\theta(t,o)=Kt+r(o).
\tag{27}
$$

同时取 $\iota(t)=Kt$。不同 $t$ 的时间区间互不相交，所以这个构造不会发生跨 Token 汇合。若 $o\prec o'$ 对应一条直接依赖边，就令该边的延迟为 $r(o')-r(o)>0$。

定义函数 $\mathcal T$：它把 SettleGraph Plan 转换成上述 $G$ 与节点函数族 $(F_v)_{v\in V}$。转换时：

- `DATA(y)` 变成值为 $y$ 的消息；
- `CLOSED` 变成“没有该消息，并且相应 seal 已越过该时间”；
- 每个操作 $o$ 变成逻辑时间为 $\theta(t,o)$ 的一个确定节点事件。

再定义函数 $\Pi$：它删除式 (27) 引入的整数时间，并把消息、状态和观察值还原成 SettleGraph 的逐 Token 记录。

记 $\operatorname{TimedDAG}(\mathcal T(\mathrm{Plan}),x)$ 为第 1.6 节返回的三元组：最终消息集合、全部节点最终状态、全部观察值。记 $\operatorname{SettleGraph}(\mathrm{Plan},x)$ 为 SettleGraph 定义返回的完整结果元组。

本文把下面的等式称为 **SettleGraph 嵌入定理**：

$$
\Pi
\left(
\operatorname{TimedDAG}(\mathcal T(\mathrm{Plan}),x)
\right)
=
\operatorname{SettleGraph}(\mathrm{Plan},x).
\tag{28}
$$

等号必须比较 SettleGraph 定义返回的全部坐标，包括输出、全部状态、选择与路径记录以及每条边的 `DATA/CLOSED`，不能只比较最终值。

建议先证明三种有限依赖关系：$|O|=1$；$O$ 被 $\prec$ 排成一条链；四个操作满足 $o_0\prec o_1,o_2$ 且 $o_1,o_2\prec o_3$。最后才证明一般有限无环关系。

## 8. 本文究竟证明哪一种“解释器存在”

式 (5) 把每个 $F_v$ 作为已经给定、可以求值的数学函数。第 1.6 节的结论是：

> 相对于这些函数求值，完整计算只需要有限次集合构造、自然数排序和函数作用。

这就是本文当前所称的“解释器存在”。它没有声称任意集合论函数都能被现实中的计算机求值。

若以后要证明“存在一段保证停止的程序”，必须先另选一种严格的程序数学模型，再定义 $P,S_v,R_v$ 中元素怎样由有限数据表示，并证明每个 $F_v$ 在该模型中可以求值且总会停止。本文暂不引入这套新理论，也不使用尚未定义的“程序存在”替代第 1.7 节的有限性证明。

## 9. 自回归因果性是另一个数学条件

跨 Token 汇合本身不保证自回归计算合法。

固定一个输出集合 $Y$ 和位置 $t\in[L]$。假设模型对输入 $x\in P^{[L]}$ 产生第 $t$ 个读出：

$$
y_t:P^{[L]}\to Y.
$$

定义 $y_t$ 满足前缀因果性，当且仅当对任意 $x,x'\in P^{[L]}$：

$$
\left(
\forall j\in[t+1],\ x(j)=x'(j)
\right)
\Longrightarrow
y_t(x)=y_t(x').
\tag{29}
$$

式 (29) 表示第 $t$ 个输出不能依赖位置大于 $t$ 的输入。如果 Token 0 与 Token 1 在同一个事件中汇合，而某个第 0 个读出实质使用了 Token 1，那么它违反式 (29)。仅仅给结果写上“属于 Token 0”的名称不能改变函数依赖关系。

因此 TimedDAG 的时间正确性与自回归前缀因果性需要分别证明。

## 10. 明确延期的内容

TimedDAG-v0 暂时不加入：

- 固定空间图中的环；
- 延迟为 $0$ 的边；
- 一个事件在同一出边产生多条消息；
- 多个外部输入节点；
- 在式 (13) 成立以前应用 $F_v$；
- 把一次 $F_v$ 的状态变化拆成多个可见步骤；
- 删除或修改已经进入 $M^*$ 的消息；
- 在输入桶为空时产生事件；
- 用偏序集或实数代替 $\mathbb N$ 作为逻辑时间；
- 无限节点集、无限边集或无限输入长度。

这些内容不是被否定，而是不能与当前唯一的新能力同时加入。下一阶段 `DelayedGraph-v0` 只删除“固定空间图无环”这一项，仍保留每条边 $\delta(a)>0$。

本文也没有定义怎样把这些集合表示成大规模数值数组，或怎样更快地计算它们；这些问题必须在数学等式固定以后另写。

## 11. 建议的数学学习顺序

1. 用整数值重做第 2 节，亲自写出两个路径、全部消息和 $B_{v,5}$。
2. 不看正文，独立证明式 (14)。
3. 对一个三节点小图写出 $M^*$、$\mathcal E^*$ 和事件图 (16)。
4. 选择 $c<b$，手算式 (19)--(25)。
5. 尝试证明第 6.2 节；遇到缺定义时先修定义，不写程序补洞。
6. 最后才把这些有限集合和函数逐项翻译成整数程序。

完成前五步以前，不需要阅读 TIDE 旧长文中比本文更一般的图与时间模型。

## 12. 按需查阅

只有遇到本文已经提出的具体证明问题时，才查旧材料：

- [[tide-mathematical-foundations#1. 输入流、绝对轮次与边界切面|输入流与绝对轮次]]
- [[tide-mathematical-foundations#定义 4.2：输入原子、时间桶与节点输入序列|时间桶]]
- [[tide-mathematical-foundations#命题 6.4：空间拓扑序构造不自动推出时间分块组合律|时间分段反例]]
- [[tide-mathematical-foundations#定义 D.9：source seal、progress frontier 与 hard output watermark|更一般的封闭下界]]

旧材料中的定义比 TimedDAG-v0 更一般；它们不能反过来改变本文的最小模型。

## 附录 S：计算机系统词汇与数学对象的对应（可选）

本附录不属于 TimedDAG-v0 的数学定义。把本附录整体删除以后，第 0--12 节的定义、引理与证明目标仍然完整。下面每个蓝色说明块默认折叠，可以在遇到相应词时才展开；第一次只建议展开 S.1、读完其中第 1--4 项，然后停止。

这里的“对应”分为四种，不能混为一谈：

1. **简称**：系统词只是已定义数学对象的短名字；
2. **导出量**：它可以由已定义对象通过函数算出；
3. **表示**：它是同一数学对象在计算机中的一种编码；
4. **证明义务**：它不是一个新对象，而是两个数学结果必须满足的等式。

若一个词不属于这四种，本附录会明确写“TimedDAG-v0 尚未定义”，而不让它暗中成为前提。以后讨论本路线时，系统词第一次出现应尽量同时写出它对应的数学对象或式号。

> [!info]- S.1　对象、名称与数据：schema、ID、payload、channel
> 本块回答“计算机文档在给什么东西起名字”。其中只有数学对象和函数有推理效力，英文词本身没有。
>
> **1. schema（模式、结构说明）**
>
> - 数学对应：把一次计算以前固定的全部数据合写成有序元组
>   $$
>   \Sigma=
>   \left(
>   G,P,L,\iota,
>   (S_v,q_v^0,R_v,F_v)_{v\in V}
>   \right).
>   \tag{S1}
>   $$
>   这些分量分别在式 (1)、(2) 和第 1.5 节定义。
> - 系统语境：当许多次输入共用同一张空间图、状态类型和节点函数时，用 schema 指“这些运行共同遵守的结构说明”。
> - 不额外表示：式 (S1) 不包含某一次的输入值函数 $x$，也不包含该次计算才产生的 $M^*$ 和 $\mathcal E^*$。它更不自动表示某种 JSON 文件、数据库表、版本号或程序类。
>
> **2. identifier、identity、ID（标识符、身份）**
>
> - 一般数学定义：若要给集合 $X$ 的元素另贴标签，可选一个单射
>   $$
>   h:X\to K.
>   \tag{S2}
>   $$
>   单射性
>   $$
>   h(z)=h(z')\Longrightarrow z=z'
>   $$
>   保证不同对象不会共用同一个标签。
> - 本文的简化：事件不需要另贴标签，它本身就是 $(v,\theta)\in\mathcal E^*$；在满足第 1.4 节唯一性条件的消息集合上，消息可由 $(\theta,a)$ 区分。也就是说，本文直接把数学坐标当作 identity。
> - 不额外表示：ID 不一定是字符串、整数、内存地址或密码学散列；这些都只是 $K$ 的可能选择。消息值 $y$ 相同也不表示消息身份相同。
>
> **3. stable ID（稳定标识符）**
>
> - 设 $X_\Sigma$ 是要标识的语义对象集合，$\mathfrak R$ 是同一 $\Sigma$ 和 $x$ 下全部合法计算次序的集合，并设每个次序 $\rho\in\mathfrak R$ 都给出单射 $h_\rho:X_\Sigma\to K$。那么“对计算次序稳定”精确定义为
>   $$
>   \forall \rho,\rho'\in\mathfrak R,\ \forall z\in X_\Sigma,
>   \qquad
>   h_\rho(z)=h_{\rho'}(z).
>   \tag{S3}
>   $$
> - 本文的事件键 $(v,\theta)$ 和消息键 $(\theta,a)$ 根本不以 $\rho$ 为自变量，所以天然满足这种不变性。
> - 原句“标识符由 schema 和语义坐标决定”可以严格改写为：存在一个函数
>   $$
>   h_\Sigma:V\times\mathbb N\to K,
>   $$
>   其中 $h_\Sigma$ 是单射，并且事件标签只取值 $h_\Sigma(v,\theta)$；实际操作编号 $n$、测得的秒数和输入分段边界都不是这个函数的自变量。
> - 不额外表示：stable 不表示标签在所有未来版本、所有 schema 或所有机构之间永久相同，也不表示标签不可伪造。若 $\Sigma$ 改变，式 (S3) 没有要求标签保持不变。
> - 作用域：上式把一次计算看成一个单独命名空间。若多次不同输入的事件必须同时存进同一集合，就还需定义运行集合 $\mathsf{Run}$，并把事件键扩成 $(r,v,\theta)\in\mathsf{Run}\times V\times\mathbb N$；TimedDAG-v0 当前没有这项全局命名要求。
>
> **4. semantic coordinates、semantic key（语义坐标、语义键）**
>
> - 数学对应：它们只是积集合中已经定义的坐标。例如事件是 $V\times\mathbb N$ 的元素，其坐标为 $(v,\theta)$；消息是 $\mathbb N\times A\times P$ 的元素，而在当前唯一性条件下用来区分消息的坐标为 $(\theta,a)$。
> - “semantic”只是在提醒：这些坐标来自数学模型，而不是来自某次运行偶然使用的线程号、内存地址或消息被看见的名次。
> - 不额外表示：这里没有引入一种名为“语义空间”的新集合，也没有声称自然语言意义可以被坐标完全刻画。
>
> **5. payload（承载值、消息内容）**
>
> - 数学对应：输入的 payload 是 $x(t)\in P$；消息 $m=(\theta,a,y)$ 的 payload 是
>   $$
>   \operatorname{value}(m)=y\in P.
>   $$
> - 系统语境：一条实际传输记录常把“要计算的值”和“说明它从哪里来、何时生效的字段”分开放置，前者通常叫 payload。
> - 不额外表示：payload 不是整条消息。$a$、$\theta$ 和由式 (4) 算出的到达时间都不是 $y$ 的一部分。神经网络中 payload 可以是 Tensor，但本文只要求它属于集合 $P$。
>
> **6. channel（通道）与 edge（边）**
>
> - 当前最小对应：每条边 $a\in A$ 可以被实现看作一个单向 channel；其发送端、接收端和逻辑延迟分别是
>   $$
>   \alpha(a),\qquad\beta(a),\qquad\delta(a).
>   $$
> - 两条边即使具有相同的 $\alpha(a)$ 和 $\beta(a)$，只要它们是 $A$ 的不同元素，就仍是两个 channel。这是第 1.2 节保留边身份的原因。
> - 不额外表示：这里的 channel 不是操作系统队列、网络连接或共享内存。它只规定哪些消息在数学上可以从哪个节点影响哪个节点。
>
> **7. port（端口）**
>
> - TimedDAG-v0 尚未定义独立的 port 集合。当前节点若要区分来源，直接读取消息中的 $a\in\operatorname{In}(v)$。
> - 若以后确实需要“一条边连接某个节点的第几个入口”，必须另给端口集合及边到端口的函数；在这些数据写出以前，port 不能参与证明。
> - 因此当前交流中说“input port $a$”，只能作为“入边 $a$”的非正式简称。
>
> **8. canonical order、canonical serialization（规范顺序、规范序列化）**
>
> - 本文的桶 $B_{v,\theta}$ 是集合，没有内部顺序。直接解释器只选择一组空间拓扑序，并在同一节点内按 $\theta$ 递增计算；它没有定义字节格式。
> - 记 $\{0,1\}^*$ 为所有有限 0--1 串所成的集合。若实现需要把某类数学对象 $X$ 保存成有限字符串，可以另给编码函数
>   $$
>   \operatorname{enc}:X\to\{0,1\}^*.
>   \tag{S4}
>   $$
>   “无损”至少要求 $\operatorname{enc}$ 为单射；“canonical”还要求同一个 $z\in X$ 无论从哪一种合法次序得到，都使用同一个 $\operatorname{enc}(z)$。
> - 不额外表示：为了打印而排序，不会给桶增加数学顺序，也不会把式 (5) 的集合输入改成序列输入。序列化格式的相等比数学对象的相等更强，正文的正确性不依赖这种更强要求。

> [!info]- S.2　时间与执行：logical time、schedule、async、seal、ready
> 本块最重要的区分是：逻辑到达时间是消息的一个自然数函数值；机器何时真的看见该消息，是另一件事。
>
> **1. logical time（逻辑时间）**
>
> - 数学对应：$\theta\in\mathbb N$。输入的逻辑注入时间是 $\iota(t)$，消息的逻辑发送时间与到达时间由式 (3)--(4) 给出：
>   $$
>   \operatorname{send}(m)=\theta,
>   \qquad
>   \operatorname{arrival}(m)=\theta+\delta(a).
>   $$
> - 用途：它规定哪些输入属于同一个桶、同一节点的状态先后，以及 cut 怎样分割事件。
> - 不额外表示：$\theta=5$ 不表示计算进行了五秒，也不表示这是机器执行的第五步。
>
> **2. wall-clock time（墙钟时间、现实测得的时间）**
>
> - 记 $\mathbb R_{\ge0}=\{r\in\mathbb R\mid r\ge0\}$。若确实要记录现实耗时，可以另给单调函数
>   $$
>   w:[N+1]\to\mathbb R_{\ge0},
>   \qquad
>   n<n'\Longrightarrow w(n)\le w(n'),
>   \tag{S5}
>   $$
>   其中 $w(n)$ 是第 $n$ 个外部操作发生时钟表测得的秒数。
> - TimedDAG-v0 的 $F_v$ 没有 $w(n)$ 这个自变量。因此两台机器用时不同，不会因此改变式 (5) 的数学结果。
> - wall-clock 的 wall 只是强调“现实世界共同经过的钟表时间”，并不引入一种特殊的数学时间。
>
> **3. stage、step、schedule（阶段、步骤、调度次序）**
>
> - 第 3.1 节的 $n\in\mathbb N$ 是外部操作的顺序编号。式 (15) 的整串
>   $$
>   (U_n,H_n,D_n,\sigma_n^{\mathrm{in}},\sigma_n)_{n=0}^{N}
>   $$
>   连同第 3.4 节的六条限制，就是本文可接受的 schedule 的数学内容。
> - 把这串对象投影到事件加入 $D_n$ 的先后次序，便得到“事件调度次序”。不同 schedule 可以先算不同的彼此独立节点。
> - 不额外表示：schedule 不是逻辑时间函数，也不是空间图的拓扑序。拓扑序是节点的一个固定排列；schedule 是一次具体计算中可见信息和已计算事件怎样逐步增长。
>
> **4. delivery、visibility（机器送达、变为可见）**
>
> - 对最终会被看见的消息 $m$，可以从 $H_n$ 导出它第一次可见的阶段
>   $$
>   \eta(m)=\min\{n\in[N+1]\mid m\in H_n\}.
>   \tag{S6}
>   $$
> - $\operatorname{arrival}(m)$ 是自然数逻辑标签；$\eta(m)$ 是式 (15) 中的操作编号；若再记录 $w$，现实送达时刻是 $w(\eta(m))$。三者的定义域和值域都不同。
> - 为避免英语 arrival 的歧义，后续最好说 logical arrival 表示式 (4)，说 delivery 或 visibility 表示进入 $H_n$。
>
> **5. asynchronous arrival（异步到达）**
>
> - 本文的精确定义见第 3.1 节。用式 (S6) 可等价地说：不要求
>   $$
>   \operatorname{arrival}(m)<\operatorname{arrival}(m')
>   \Longrightarrow
>   \eta(m)\le\eta(m').
>   \tag{S7}
>   $$
> - 所以逻辑时间为 $8$ 的消息可以先被机器看见，逻辑时间为 $5$ 的消息可以后被看见。
> - 不额外表示：异步不允许忽略式 (13) 而提前计算，也不表示 $F_v$ 在一次事件内部被拆成任意交错的小步骤。
>
> **6. event（事件）**
>
> - 数学对应：第 1.5 节定义的非空桶上的一次函数作用，其位置为 $(v,\theta)\in\mathcal E^*$。
> - “事件发生”表示对整个 $B_{v,\theta}$ 恰好应用一次 $F_v$。事件图的顶点正是这些位置，依赖边由式 (17)--(18) 给出。
> - 不额外表示：这里的事件不是操作系统中断、日志行或单条消息。一条事件可以同时消费多条消息，也可以产生零条或多条出边消息。
>
> **7. ready（就绪）**
>
> - 它是一个谓词，不是一个新对象。在阶段 $n$，可以把“$(v,\theta)$ ready”展开为：
>   1. $B^{(n)}_{v,\theta}\ne\varnothing$；
>   2. 式 (13) 成立；
>   3. $(v,\theta)\notin D_n$；
>   4. 同一节点所有更小逻辑时间的非空桶都已经计算。
> - 第 3.3 节保证第 2 条成立时 $B^{(n)}_{v,\theta}=B_{v,\theta}$，因此 ready 事件看见的是完整桶。
> - 不额外表示：队列非空只给出第 1 条，不能推出 ready；机器有空闲线程也不能推出 ready。
>
> **8. fire、execute（触发、执行）**
>
> - 数学对应：选择一个 ready 的 $(v,\theta)$，对 $B^{(n)}_{v,\theta}$ 应用一次式 (5)，把事件加入 $D_n$，更新节点状态并产生相应消息。
> - ready 是“允许做”的真假条件；execute 是“做一次状态转移”。这两个词不能互换。
> - 本文要求同一事件至多 execute 一次。这个限制来自 $D_n$，不是来自 $F_v$ 自己具有某种特殊代数性质。
>
> **9. seal（封闭下界）**
>
> - 精确定义只有式 (11)--(12)。例如 $\sigma_n(a)=b$ 表示：
>   $$
>   \forall m\in M^*\setminus H_n,\quad
>   \operatorname{edge}(m)=a
>   \Longrightarrow
>   \operatorname{arrival}(m)\ge b.
>   $$
> - 它是关于“所有尚未看见的消息”的全称命题。队列暂时为空、等待了很久或某个线程已经结束，都不能单独证明这个命题。
> - seal $=b$ 允许以后出现逻辑时间恰好为 $b$ 的消息，所以关闭时间 $\theta$ 的桶需要 seal $>\theta$。
>
> **10. frontier（前沿）与 watermark（水位）**
>
> - 这两个系统词在不同系统中用法不统一，必须先说明是哪一个数学量。对当前模型，可以从 seal 导出节点输入前沿
>   $$
>   f_n(v)=
>   \begin{cases}
>   \sigma_n^{\mathrm{in}},&v=v_{\mathrm{in}},\\
>   \min\{\sigma_n(a)\mid a\in\operatorname{In}(v)\},&v\ne v_{\mathrm{in}}.
>   \end{cases}
>   \tag{S8}
>   $$
>   由空间图的条件，第二行所取的集合非空。式 (13) 等价于 $f_n(v)>\theta$。
> - 第 3.5 节的“节点已完成到 $b$”是另一种 completed frontier：它还要求所有小于 $b$ 的非空桶已经执行。输入已经封闭到 $b$ 与节点已经完成到 $b$ 不是同一句话。
> - 本文没有单独定义 output watermark。若以后用 watermark 指式 (11) 的硬承诺，它只是 seal 的别名；若指“输出已经产生到哪里”，就必须新增定义，不能沿用式 (S8)。
>
> **11. late message、no-backdating（迟到消息、不得倒填）**
>
> - 一条逻辑时间较小、但物理上较晚进入 $H_n$ 的消息只是乱序可见，并不必然非法。
> - 真正非法的是：已经有有效 seal $\sigma_n(a)=b$ 后，又加入边 $a$ 上满足
>   $$
>   \operatorname{arrival}(m)<b
>   $$
>   的新消息。这直接否定式 (11)。系统文档常把这条限制叫 no-backdating。
> - 因而“迟到”必须说明相对于逻辑时间的观察顺序，还是相对于已经公布的 seal；只有后一种越界才违反模型。
>
> **12. atomic commit（原子提交）**
>
> - 抽象数学含义：一次式 (5) 从
>   $$
>   (q_v,\theta,B_{v,\theta})
>   $$
>   得到新状态、输出选择和观察值；模型不允许其他事件看见这次函数作用的某个“中间状态”。第 10 节也明确延期了把一次状态变化拆成多个可见步骤。
> - 系统语境：实现需要安排写状态、记录事件和发布消息，使外部可观察结果能投影成上述一次转移。
> - 不额外表示：它不声称整个事件是一条 CPU 原子指令，也不自动提供数据库事务、断电恢复或多机共识。

> [!info]- S.3　停止、恢复与记录：cut、chunk、continuation、checkpoint
> 本块区分数学上“继续计算所需的信息”与计算机中“怎样把这些信息存下来”。
>
> **1. state（状态）**
>
> - 数学对应：节点 $v$ 的状态是 $q_v\in S_v$；初值为 $q_v^0$。它概括已经处理的过去中，未来计算仍会读取的全部信息。
> - 系统表示可以是 Tensor、整数、结构体或文件内容；这些只是 $S_v$ 元素的编码。
> - 不额外表示：状态不是全部历史。若两个不同历史导向同一个 $q_v$，模型允许未来无法再区分它们。
>
> **2. state version（状态版本）**
>
> - TimedDAG-v0 没有把 version 作为独立输入。若节点 $v$ 的事件时间为
>   $$
>   \theta_1<\cdots<\theta_k,
>   $$
>   可以把处理完 $\theta_i$ 后的导出编号定义为 $i$，或把事件键 $(v,\theta_i)$ 直接当作该次更新的版本标签。
> - 这个编号只帮助实现检测旧写入；真正决定数学状态先后的仍是第 1.6 节的时间递增和事件图边 (18)。
> - 不额外表示：version 增大不表示逻辑时间必须连续，也不表示两个节点的相同 version 可以互相比较。
>
> **3. cut（切面、逻辑时间边界）**
>
> - 精确定义见第 5.1 节。一个 $b\in\mathbb N$ 把事件集合分成
>   $$
>   \mathcal E^{<b}\mathbin{\dot\cup}\mathcal E^{\ge b}.
>   $$
>   符号 $\dot\cup$ 表示两部分的交集为空。
> - cut 是按事件逻辑时间定义的集合分割。它适合提出“左侧全部完成后，右侧如何继续”的问题。
> - 不额外表示：cut 不是把内存数组从第 $k$ 个字节切开，也不是按机器运行了多少秒暂停。
>
> **4. chunk（分块、输入块）**
>
> - 在本文中，chunk 只应指式 (22) 的逻辑时间输入区间
>   $$
>   I_{[c,b)}
>   =
>   \{(t,x(t))\mid c\le\iota(t)<b\}.
>   $$
> - 对 $0\le c\le b$，有不交分解
>   $$
>   I_{[0,b)}
>   =
>   I_{[0,c)}\mathbin{\dot\cup}I_{[c,b)}.
>   \tag{S9}
>   $$
> - 不额外表示：一次 API 调用、一段连续 Tensor 或固定数量的 Token 只有在被明确证明对应式 (S9) 时，才是本文意义的 chunk。改变 chunk 边界不应改变事件身份。
>
> **5. continuation（续算状态）**
>
> - 数学对应：第 5.2 节的候选 continuation 是
>   $$
>   Q_b=
>   \left(
>   b,(q_v^b)_{v\in V},W_b
>   \right).
>   $$
> - 它是“从 cut $b$ 继续时未来仍需要的数学信息”。式 (24)--(25) 是它是否充分的证明义务。
> - 不额外表示：continuation 不是文件，也不必已经序列化。本文还明确保留了一个风险：加入计时器、事件内部未完成工作或环以后，$Q_b$ 可能不再充分。
>
> **6. checkpoint（检查点、保存点）**
>
> - checkpoint 是 continuation 的一种计算机表示。若
>   $$
>   \operatorname{save}:\mathcal Q\to\{0,1\}^*,
>   \qquad
>   \operatorname{load}:\{0,1\}^*\rightharpoonup\mathcal Q,
>   $$
>   其中 $\mathcal Q$ 是合法 $Q_b$ 的集合，那么最基本的无损条件是
>   $$
>   \operatorname{load}(\operatorname{save}(Q_b))=Q_b.
>   \tag{S10}
>   $$
>   这里 $\rightharpoonup$ 表示部分函数：任意 0--1 串未必都是合法 checkpoint，所以 $\operatorname{load}$ 可以在某些串上没有定义。
> - restart 或 resume 表示先 load，再从所得 $Q_b$ 计算 $\Phi_{b,d}$。
> - 不额外表示：数学 continuation 充分，不自动证明某种文件格式无损、写盘不会中断或跨软件版本兼容。真实异步 executor 若还有尚未投影到 $Q_b$ 的传输状态，还必须额外保存它并证明投影正确。
>
> **7. pending、in-flight message（待处理、传输中的消息）**
>
> - cut 处明确需要保留的逻辑跨界消息是式 (19)
>   $$
>   W_b
>   =
>   \{m\in M^*\mid
>   \operatorname{send}(m)<b\le\operatorname{arrival}(m)\}.
>   $$
>   它们已经由左侧事件产生，但逻辑到达时间属于右侧。
> - 阶段 $n$ 的 $M^*\setminus H_n$ 只表示“尚未可见的最终消息”。当前抽象模型没有再区分其中哪些尚未产生、哪些已经产生但仍在网络中，因此不能把整个 $M^*\setminus H_n$ 都叫物理 in-flight。
> - 若实现需要这种区分，必须增加“已产生集合”和“已送达集合”，物理 in-flight 才能定义为二者之差。
>
> **8. artifact、observation、semantic trace（产物、观察值、语义轨迹）**
>
> - 当前数学对应：一次事件的 observation 是式 (5) 的 $r_{v,\theta}\in R_v$；区间上的全部记录是式 (21) 的集合
>   $$
>   \mathcal R_{[c,b)}
>   =
>   \{((v,\theta),r_{v,\theta})\mid c\le\theta<b\}.
>   $$
> - 旧文档中的 semantic artifact 在当前最小模型里应投影到这样的事件键—观察值对。若按事件键规范排列这些对，可得到一种 semantic trace 的序列表示。
> - 不额外表示：调试日志、打印文本、耗时和线程号不自动属于 $\mathcal R$。若把实际先后记录成序列 $(n,(v,\theta))$，那是 schedule log；不同合法执行的 schedule log 可以不同。
>
> **9. replay（重放）**
>
> - 从同一个 $Q_c$ 和同一个 $I_{[c,b)}$ 再计算一次 $\Phi_{c,b}$，称为 replay。对第 1.6 节固定的直接解释器，函数性要求相同输入得到相同输出。
> - 若 replay 采用另一种合法 schedule，结果仍相同则是第 6.2 节“合法计算次序无关”的证明目标，而不是 replay 这个词自动保证的事实。
> - checkpoint/replay 正确通常需要同时证明式 (S10) 与式 (24)--(25)。
>
> **10. deduplication、exactly once（去重、恰好一次）**
>
> - 逻辑消息集合满足第 1.4 节的唯一性条件，同一键 $(\theta,a)$ 不能对应两个不同值。若物理网络重复交付同一逻辑消息，实现可按这个键把多个传输副本投影为一个集合元素；这一步叫 deduplication。
> - 对事件，$(v,\theta)\notin D_n$ 是尚未执行的条件；执行后把它加入 $D_n$，从而表达逻辑上的 at most once。与“所有非空完整桶最终都会执行”的进展条件合在一起，才得到 exactly once。
> - 不额外表示：当前数学模型直接从集合开始，并没有描述产生重复网络副本的过程。
>
> **11. idempotence（幂等性）**
>
> - 一个函数 $T:X\to X$ 幂等，按定义是
>   $$
>   T(T(z))=T(z)
>   \qquad(\forall z\in X).
>   \tag{S11}
>   $$
> - TimedDAG-v0 不要求节点事件转移幂等。对同一状态重复调用 $F_v$ 可能再次改变状态或重复产生输出；模型靠 $D_n$ 防止同一事件重复执行。
> - 因此“从相同 checkpoint 重放得到相同结果”是确定性；“对已经更新的状态再做一次仍不变”才是幂等性。二者不能互换。

> [!info]- S.4　解释器、实现与等价：runtime、projection、refinement、packed
> 本块回答“数学定义与真正程序之间还差什么”。第 8 节是正文中的权威边界。
>
> **1. semantics、model（语义、模型）**
>
> - 在本文中，它们指第 1--5 节给出的集合、函数、递归和等式。固定 $\Sigma$ 与输入 $x$ 后，它们规定正确结果是什么。
> - 它们不规定对象在内存中怎样编码、由几个线程计算、采用哪种硬件或耗时多少。
>
> **2. interpreter（解释器）**
>
> - 数学对应：第 1.6 节按空间拓扑序、再按节点内逻辑时间递增进行的有限递归。
> - 它的“输入”是已定义的集合、函数与输入值；它的“基本动作”包括有限集合构造、自然数排序和调用 $F_v$。
> - 第 8 节只证明相对于 $F_v$ 求值，它需要有限次动作；并未由此得到一段可在任意机器上运行的程序。
>
> **3. evaluator（节点函数求值器）**
>
> - 若要把抽象函数 $F_v$ 变成程序，需要为 $S_v$、$P$、$R_v$ 和有限桶选择编码，并给出一个总会停止且满足
>   $$
>   \operatorname{decode}
>   \bigl(
>   \operatorname{Eval}_v(\operatorname{encode}(q,\theta,B))
>   \bigr)
>   =
>   F_v(q,\theta,B)
>   \tag{S12}
>   $$
>   的程序 $\operatorname{Eval}_v$。
> - 这正是第 8 节所说、从集合论函数到可运行解释器仍需补充的前提。
>
> **4. executor、runtime（执行器、运行时系统）**
>
> - 它们指真正维护队列、状态和 seal，并选择 ready 事件执行的程序。它可以使用不同线程、设备和消息搬运次序。
> - TimedDAG-v0 尚未给出某个 executor 的程序数学模型。要声称它正确，必须先定义从它的机器状态到本文对象的投影，再证明每次运行的投影满足第 3.4 节和目标等式。
> - runtime 因而不是 $F_v$，也不是事件图；它是试图实现整套解释过程的外部对象。
>
> **5. reference semantics 与 reference implementation（参考语义与参考实现）**
>
> - 第 1.6 节首先是 reference semantics：它用数学递归指定答案。
> - 只有把全部集合元素有限编码，并实现满足式 (S12) 的程序后，那段刻意保持简单、用来比较其他实现的程序才叫 reference implementation。
> - 两者不能因都含 reference 一词而混同。数学递归可以已经定义良好，而程序尚未写出。
>
> **6. oracle（判定基准）**
>
> - 测试语境中的 oracle 是一个给定输入返回期望观察结果的函数。例如可把直接解释器产生的
>   $$
>   (M^*,(q_v^{\mathrm{final}})_{v\in V},
>   \mathcal R)
>   $$
>   作为小规模测试的 oracle 输出。
> - oracle 不是额外的神秘计算能力；在这里它通常只是“我们暂时信任的简单定义或实现”。若 reference 自身未证明或有错误，oracle 也可能错。
>
> **7. projection（投影）**
>
> - 数学上它只是一个函数
>   $$
>   \Pi:X_{\mathrm{rich}}\to X_{\mathrm{observed}},
>   \tag{S13}
>   $$
>   用来忘掉实现细节或翻译表示。例如删除线程号和物理送达次序，只留下事件键、消息、状态与观察值。
> - 第 7 节的 $\Pi$ 是具体实例：它删除式 (27) 引入的时间编码，并还原 SettleGraph 结果。
> - 投影会忘掉什么必须逐项写明；不能只说“忽略无关细节”，因为哪些细节无关正是需要证明的内容。
>
> **8. refinement（精化、实现关系）**
>
> - 若丰富系统 $I$ 的一次运行结果为 $\operatorname{Run}_I(\xi,\rho)$，参考模型结果为 $\operatorname{Ref}(\xi)$，并用 $\operatorname{Legal}_I(\xi)$ 表示输入 $\xi$ 下允许的实现调度集合，那么一个典型的 refinement 证明义务是
>   $$
>   \forall\xi,\ \forall\rho\in\operatorname{Legal}_I(\xi),
>   \qquad
>   \Pi(\operatorname{Run}_I(\xi,\rho))
>   =
>   \operatorname{Ref}(\xi).
>   \tag{S14}
>   $$
> - 它表示实现可以含有更多状态和更多步骤，但投影后的可观察数学结果与参考定义相同。
> - 式 (28) 是相反方向上的一个具体翻译/精化目标：把 SettleGraph 放入 TimedDAG，再投影回去，必须得到原完整结果。
>
> **9. equivalence（等价）**
>
> - equivalence 不是一个没有宾语的词，必须声明比较哪些坐标。本文至少有三种不同等价：
>   1. 不同合法 schedule 的 cut 结果相同：第 6.2 节；
>   2. 分段与一次算完相同：式 (24)--(25)；
>   3. TimedDAG 翻译与 SettleGraph 结果相同：式 (28)。
> - 两次运行的墙钟耗时、线程次序或调试日志不同，不妨碍它们在指定投影下等价。反过来，只比较最终一个 Tensor 相等，也不足以推出状态、消息和观察记录都等价。
>
> **10. batching、packed execution（批处理、紧凑打包执行）**
>
> - 假设参考语义允许独立计算 $k$ 个事件输入
>   $$
>   z_i=(q_i,\theta_i,B_i)
>   \qquad(1\le i\le k).
>   $$
>   实现可先用 $\operatorname{Pack}$ 把它们放入一个大数组，由一次 kernel $K$ 计算，再用 $\operatorname{Unpack}$ 分开。正确性要求
>   $$
>   \operatorname{Unpack}
>   \left(
>   K(\operatorname{Pack}(z_1,\ldots,z_k))
>   \right)
>   =
>   \left(
>   F_{v_1}(q_1,\theta_1,B_1),\ldots,
>   F_{v_k}(q_k,\theta_k,B_k)
>   \right).
>   \tag{S15}
>   $$
> - 式 (S15) 中仍有 $k$ 个语义事件；一次 kernel 调用不等于一个语义事件。
> - 与此相反，若来自多个 Token 的消息本来就属于同一个 $B_{v,\theta}$，正文要求对这个并集调用一次 $F_v$。把它拆成两个 $F_v$ 调用再声称只是 packed，通常会改变状态语义。
>
> **11. packed attention 的位置**
>
> - packed attention 是式 (S15) 中 $K$ 的一种高性能候选实现。它需要证明 unpack 后的数值结果等于逐事件参考函数，并说明浮点误差采用哪一种相等关系。
> - 它解决“怎样更快求值”，不负责证明桶已经由 seal 关闭，也不负责决定两个 Token 是否属于同一事件。前者属于第 3 节，后者由相同的 $(v,\theta)$ 和式 (7) 决定。
>
> **12. monolithic、online、streaming（一次算完、在线、流式）**
>
> - monolithic 可对应从 $Q_0$ 一次计算 $\Phi_{0,b}$；chunked/streaming 可对应依次计算 $\Phi_{0,c}$ 与 $\Phi_{c,b}$。
> - 两者语义一致的内容正是式 (24)--(25)，不是因为程序按顺序调用两次就自动成立。
> - online 通常还表示输入和消息逐步进入 $U_n,H_n$；其合法性需要式 (11)--(15)，而不仅是分块等式。

> [!info]- S.5　三句旧系统语言的逐句数学翻译
> 这一块不是增加定义，而是示范今后怎样把系统说法还原成可以证明的句子。
>
> **句子一**
>
> “稳定标识符由 schema 和语义坐标决定，不由墙钟顺序、线程编号或本次 chunk 划分决定。”
>
> 数学翻译：
>
> 1. schema 是式 (S1) 的 $\Sigma$；
> 2. 事件的语义坐标是 $(v,\theta)$；
> 3. 标识函数取形如 $h_\Sigma(v,\theta)$；
> 4. 对同一 $\Sigma,v,\theta$，改变合法计算次序 $\rho$、墙钟记录 $w$、实现线程分配或式 (S9) 的分割点，都不改变 $h_\Sigma(v,\theta)$。
>
> 在当前最小模型中甚至不必构造 $h_\Sigma$：直接用 $(v,\theta)$ 即可。于是这整句真正排除的是“用第几个完成、在哪个线程完成、在哪次 API 调用中完成来命名事件”。
>
> **句子二**
>
> “channel 的 seal 越过时间 5 后，时间桶 5 才能 ready；runtime 可以乱序收消息，但不能在 seal 后接收倒填消息。”
>
> 数学翻译：
>
> 1. channel 是入边 $a$；
> 2. “越过 5”要求每条入边 $a\in\operatorname{In}(v)$ 都有 $\sigma_n(a)>5$；若 $v=v_{\mathrm{in}}$，还要求 $\sigma_n^{\mathrm{in}}>5$，也就是完整满足式 (13)；
> 3. ready 还需要桶非空、事件不在 $D_n$ 中、同节点更早事件已经计算；
> 4. 乱序是式 (S7) 不必成立；
> 5. 倒填非法是新消息满足 $\operatorname{arrival}(m)<\sigma_n(a)$，从而违反式 (11)。
>
> 所以 seal $=5$ 仍不够关闭桶 5，seal $=6$ 才越过它。
>
> **句子三**
>
> “保存 checkpoint 后用任意 chunk 恢复，结果应与 monolithic reference 等价。”
>
> 数学翻译：
>
> 1. continuation 候选是 $Q_c$；
> 2. checkpoint 编解码满足式 (S10)；
> 3. chunk 是 $I_{[c,b)}$；
> 4. 恢复计算是 $\Phi_{c,b}(Q_c,I_{[c,b)})$；
> 5. monolithic reference 是 $\Phi_{0,b}(Q_0,I_{[0,b)})$；
> 6. “等价”必须具体展开为式 (24) 的边界状态相等和式 (25) 的观察值集合相等。
>
> 若还要求换一种异步 schedule，必须再使用第 6.2 节的次序无关结论；它不是 chunk composition 自带的结论。

本附录采用一个持续约定：以后若系统词已经能还原为本文对象，就写成“系统词（数学对象）”；若还不能，就明确标成“尚未定义的实现概念”或“下一版待增加的数据”，不让读者凭领域背景猜测。
