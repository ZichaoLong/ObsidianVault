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

## 9. 本文怎样处理容易造成误解的词

本文不需要把以下词当成预备知识。

- **schema**：在本模型中可以把它精确定义为输入值 $x$ 以外、预先固定的有序元组
  $$
  \Sigma=
  \left(
  G,P,L,\iota,
  (S_v,q_v^0,R_v,F_v)_{v\in V}
  \right).
  $$
  本文直接使用元组中的各项，不再让 schema 这个名称承担额外含义。
- **identifier**：对集合 $X$，数学上的标识函数可以定义为某个单射 $h:X\to K$；单射性保证不同元素不会得到同一个标签。本文不需要另给事件构造这种函数：事件本身就是 $(v,\theta)$。在任意满足第 1.4 节唯一性条件的消息集合上，$(\theta,a,y)\mapsto(\theta,a)$ 已经是单射。
- **stable**：若对每一种合法计算次序 $\rho$ 都构造标识函数 $h_\rho$，那么“稳定”可以定义为
  $$
  \forall\rho,\rho',\ \forall z\in X,
  \qquad
  h_\rho(z)=h_{\rho'}(z).
  $$
  本文直接用事件 $(v,\theta)$ 和消息 $(\theta,a)$ 自身，不再额外构造依赖计算次序的 $h_\rho$。
- **semantic coordinates**：这个名称不是新的数学对象，只是指积集合中用于确定元素的分量。例如事件属于 $V\times\mathbb N$，其两个分量就是 $(v,\theta)$；消息在本文中的区分分量是 $(\theta,a)\in\mathbb N\times A$。
- **wall-clock time**：令 $\mathbb R_{\ge0}=\{r\in\mathbb R\mid r\ge0\}$。若确实测量现实耗时，可以另给一个单调函数
  $$
  w:[N+1]\to\mathbb R_{\ge0},
  \qquad
  n<n'\Longrightarrow w(n)\le w(n'),
  $$
  其中 $w(n)$ 是第 $n$ 个外部操作发生时测得的秒数。TimedDAG-v0 不把 $w$ 放入式 (5)；式 (15) 只使用操作序号 $n$。
- **chunk**：在本文中若它表示一段输入，就精确定义为式 (22) 的集合。对 $0\le c\le b$，有不交分解
  $$
  I_{[0,b)}=I_{[0,c)}\mathbin{\dot\cup}I_{[c,b)}.
  $$
- **interpreter**：只指第 1.6 节列出的有限递归；第 8 节明确说明了它没有自动包含哪一种程序存在性结论。
- **continuation**：只指边界后继续计算所需保存的对象；本模型中的候选对象已在式 (20) 给出。
- **异步**：只指第 3.1 节定义的“被看见的先后次序不必按逻辑到达时间排列”。它不允许一个未关闭的桶提前改变状态。

如果以后需要新词，应先增加相应的集合、函数或关系，再给它命名。

## 10. 自回归因果性是另一个数学条件

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

## 11. 明确延期的内容

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

## 12. 建议的数学学习顺序

1. 用整数值重做第 2 节，亲自写出两个路径、全部消息和 $B_{v,5}$。
2. 不看正文，独立证明式 (14)。
3. 对一个三节点小图写出 $M^*$、$\mathcal E^*$ 和事件图 (16)。
4. 选择 $c<b$，手算式 (19)--(25)。
5. 尝试证明第 6.2 节；遇到缺定义时先修定义，不写程序补洞。
6. 最后才把这些有限集合和函数逐项翻译成整数程序。

完成前五步以前，不需要阅读 TIDE 旧长文中比本文更一般的图与时间模型。

## 13. 按需查阅

只有遇到本文已经提出的具体证明问题时，才查旧材料：

- [[tide-mathematical-foundations#1. 输入流、绝对轮次与边界切面|输入流与绝对轮次]]
- [[tide-mathematical-foundations#定义 4.2：输入原子、时间桶与节点输入序列|时间桶]]
- [[tide-mathematical-foundations#命题 6.4：空间拓扑序构造不自动推出时间分块组合律|时间分段反例]]
- [[tide-mathematical-foundations#定义 D.9：source seal、progress frontier 与 hard output watermark|更一般的封闭下界]]

旧材料中的定义比 TimedDAG-v0 更一般；它们不能反过来改变本文的最小模型。
