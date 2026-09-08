---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-07
tags:
  - tide
  - timed-dag
  - region
  - selector
  - logical-time
  - mathematics
  - learning-note
---

# 带区域选择的 TimedDAG：从零开始的数学定义

> [!summary] 本文的阅读前提
> 本文只假设读者熟悉集合、函数、自然数、有限求和、最小值和数学归纳法。有向图、逻辑时间、输入端口、消息、时间纤维、区域、候选集合、选择函数、封闭下界以及事件图都会在本文中重新定义。
>
> 本文的每一项定义都写在文内，其他文档与讨论均不是阅读前提。标题中的 `region`、`selector` 和完整 `TimedDAG` 规格只是待定义对象的名称；它们分别在第 2.4、5.3、6.5 节获得精确定义。
>
> 正文先给数学对象，再给例子和定理。计算机系统中的常用说法统一放在附录 S；删除附录 S 后，正文仍然构成完整的数学规格。

> [!tip] 分四次阅读
> 第一次只读第 1--3 节，目标是能从式 (8) 独立算出一个时间纤维；读到这里就停止。第二次读第 4--7 节，完整手算两个例子。第三次只研究第 8--9 节的封闭下界与次序无关。第 10 节以后讨论事件图、切面与性能分层，不是理解主定义的前置。

本文要定义的是一个有限确定性模型。它具有以下能力：

1. 有有限多个外部输入端口，也有有限多个外部输出端口；
2. 每个外部输入位置带有一个自然数时间；
3. 节点沿固定有向边发送值，每条边增加一个正整数时间；
4. 到达同一节点、同一时间的全部外部输入和内部消息被共同处理；
5. 节点集合被划分为若干区域；同一区域中，在同一时间收到至少一个输入的全部节点共同参加一次选择；
6. 只有在能够证明这组节点不会再增加时，在线求值过程才可以作出选择；
7. 区域不是节点，不接收消息，也不发送消息；
8. 区域之间不要求构成 DAG。

正文分成两个层次。

- 第 1--7 节先假定一次输入全部给定，定义唯一的完整结果。这是模型本身的含义。
- 第 8--9 节再定义一个求值者只逐步看见输入和消息时，怎样证明当前知道的集合已经完整。这只改变求值次序，不改变模型结果。

这个顺序很重要：必须先知道“正确的完整结果是什么”，才能定义“一个尚未看全的求值过程何时已经知道得足够多”。

## 1. 基础记号

### 1.1 自然数、有限集合与半开区间

定义：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

若 $L\in\mathbb N_{>0}$，定义：

$$
[L]=\{0,1,\ldots,L-1\}.
$$

若 $r,s\in\mathbb N$ 且 $r\le s$，定义：

$$
[r,s)=\{\theta\in\mathbb N\mid r\le\theta<s\}.
$$

对任意集合 $X$，用：

$$
\mathcal P_{\mathrm{fin}}(X)
$$

表示 $X$ 的所有有限子集所成的集合，用 $|X|$ 表示有限集合 $X$ 的元素个数。

对任意集合 $E,Y$，定义：

$$
Y^E=\{f\mid f:E\to Y\}.
$$

也就是说，$Y^E$ 是所有从 $E$ 到 $Y$ 的函数所成的集合。

本文说一个映射是**全函数**，只表示定义域中的每个元素都恰有一个函数值；它不表示这个函数一定容易计算。

### 1.2 带名字的函数坐标

设 $C$ 是有限集合，并且每个 $v\in C$ 都有一个集合 $D_v$。定义：

$$
\prod_{v\in C}D_v
=
\{d\mid d\text{ 是定义在 }C\text{ 上的函数，且 }d(v)\in D_v\}.
$$

因此，$(d_v)_{v\in C}$ 表示“由 $v$ 标记的函数坐标族”，不是一个依赖排列顺序的列表。若 $C=\{a,b\}$，那么 $(d_v)_{v\in C}$ 就是同时规定 $d(a)$ 与 $d(b)$；交换纸面上书写 $a,b$ 的顺序不会改变这个函数。

### 1.3 一个表示“不产生值”的符号

固定一个非空集合 $P$，其元素称为**承载值**。本文不限制 $P$ 是实数、向量还是别的集合。

另取一个不属于 $P$ 的符号 $\bot$，定义：

$$
P_\bot=P\cup\{\bot\}.
$$

以后，一个以 $P_\bot$ 为值域的函数在某个坐标上取 $\bot$，只表示“这次在该坐标上不产生承载值”。

## 2. 固定结构：时间、节点图、端口与区域划分

本节定义一次具体输入到来以前就已经固定的数据。

### 2.1 逻辑时间

定义逻辑时间集合：

$$
\mathbb T=\mathbb N.
$$

本文中的 $\theta\in\mathbb T$ 只是一项数学坐标。它可以相加、比较大小，并作为函数的自变量。定义本身没有说 $\theta=5$ 等于五秒，也没有说它是某个程序执行的第五步。

两个对象具有相同逻辑时间，严格地说只表示它们的时间坐标是同一个自然数。

### 2.2 有限有向图与 DAG

给定五元组：

$$
G=(V,A,\operatorname{src},\operatorname{dst},\delta).
\tag{1}
$$

其中：

- $V$ 是有限非空集合，其元素称为节点；
- $A$ 是有限集合，其元素称为有向边；
- $\operatorname{src}:A\to V$ 给出边的起点；
- $\operatorname{dst}:A\to V$ 给出边的终点；
- $\delta:A\to\mathbb N_{>0}$ 给出边的正整数时延。

若起点节点在逻辑时间 $\eta$ 产生一个准备沿边 $a$ 传递的值，则规定该值在逻辑时间 $\eta+\delta(a)$ 到达终点节点。因此，$\delta(a)$ 是这两个逻辑时间坐标之差。若希望把源节点的逻辑计算耗时和边上传递耗时分开，可以另外给定：

$$
c:V\to\mathbb N,
\qquad
d:A\to\mathbb N,
$$

并令：

$$
\delta(a)=c(\operatorname{src}(a))+d(a)>0.
$$

后文只使用总和 $\delta(a)$，所以这种分解不改变任何递归或封闭下界定义。这里的 $c,d$ 只是 $\delta$ 的一种分解，不会额外定义“节点完成时间”坐标；消息的第一个时间坐标仍取源节点处理输入时的逻辑时间。若要让节点完成时间本身成为可观察坐标，或者记录外部值的逻辑可用时间，就需要另外定义相应坐标或输出端口时延函数，不能暗中改变 $\theta$ 的含义。

两条边即使具有相同起点和终点，只要它们是 $A$ 中不同的元素，仍然是两条不同的边。

对 $v\in V$ 定义：

$$
\operatorname{In}(v)
=\{a\in A\mid\operatorname{dst}(a)=v\},
$$

$$
\operatorname{Out}(v)
=\{a\in A\mid\operatorname{src}(a)=v\}.
$$

若 $(a_1,\ldots,a_k)$ 是非空有限边序列，并且：

$$
\operatorname{dst}(a_\ell)
=
\operatorname{src}(a_{\ell+1})
\qquad(1\le\ell<k),
$$

则称它为一条有向路径。若还满足：

$$
\operatorname{dst}(a_k)=\operatorname{src}(a_1),
$$

则称它为有向环。

本文规定式 (1) 中不存在有向环。满足这个条件的有限有向图称为有向无环图，英文缩写为 **DAG**。

因此，本文标题中的 `DAG` 首先指式 (1) 的固定节点图是 DAG。第 10 节还会从一次具体计算构造另一张事件 DAG；两张图不是同一个数学对象。

### 2.3 多个输入端口与多个输出端口

给定两个有限非空集合：

$$
\mathsf I=\text{输入端口集合},
\qquad
\mathsf O=\text{输出端口集合},
$$

以及两个函数：

$$
\gamma:\mathsf I\to V,
\qquad
\varepsilon:\mathsf O\to V.
\tag{2}
$$

$\gamma(i)$ 是端口 $i$ 的值进入的节点；$\varepsilon(o)$ 是唯一可以向端口 $o$ 产生值的节点。端口不是 $V$ 中的节点。

对节点 $v$ 定义：

$$
\operatorname{InPort}(v)
=\{i\in\mathsf I\mid\gamma(i)=v\},
$$

$$
\operatorname{OutPort}(v)
=\{o\in\mathsf O\mid\varepsilon(o)=v\}.
$$

允许多个输入端口进入同一节点，也允许同一节点连接多个输出端口。

对每个 $i\in\mathsf I$，固定一个正整数 $L_i$。端口 $i$ 的输入位置集合是 $[L_i]$。一次完整外部输入是函数族：

$$
x=(x_i)_{i\in\mathsf I},
\qquad
x_i:[L_i]\to P.
\tag{3}
$$

再为每个端口固定严格递增函数：

$$
\iota_i:[L_i]\to\mathbb N,
\qquad
k<k'\Longrightarrow\iota_i(k)<\iota_i(k').
\tag{4}
$$

输入位置 $(i,k)$ 带有值 $x_i(k)$，并具有逻辑时间 $\iota_i(k)$。严格递增只发生在同一个端口内部；不同端口的位置可以具有相同逻辑时间。

### 2.4 区域是节点集合的划分

给定有限非空集合 $J$ 和满射：

$$
\rho:V\to J.
\tag{5}
$$

这里“满射”明确表示：

$$
\forall j\in J,\quad
\exists v\in V:\rho(v)=j.
$$

对每个 $j\in J$ 定义：

$$
\mathcal R_j=\rho^{-1}(\{j\})
=\{v\in V\mid\rho(v)=j\}.
\tag{6}
$$

由于 $\rho$ 是满射，每个 $\mathcal R_j$ 都非空；并且：

$$
V=\bigcup_{j\in J}\mathcal R_j,
\qquad
j\ne j'\Longrightarrow
\mathcal R_j\cap\mathcal R_{j'}=\varnothing.
$$

从现在起，集合 $\mathcal R_j$ 的系统别名是 **region**，中文称为区域。式 (5)--(6) 是这个词在正文中的全部基础含义：每个节点恰好属于一个区域。

区域没有自己的入边、出边或状态。$J$ 上目前也没有定义任何边。第 10.6 节会为了比较额外构造一张区域商图，但那张商图不参与本模型的消息传递。

## 3. 外部输入记录、内部消息与时间纤维

本节先定义哪些记录可以到达一个节点，再用目标节点与逻辑时间从这些记录中取出一个有限子集。

### 3.1 外部输入记录

定义所有可能的外部输入记录所成的集合：

$$
\mathsf{Ext}
=
\{(\mathrm{ext},i,k,y)\mid
i\in\mathsf I,\ k\in[L_i],\ y\in P\}.
$$

对 $e=(\mathrm{ext},i,k,y)\in\mathsf{Ext}$ 定义：

$$
\operatorname{inport}(e)=i,
\qquad
\operatorname{position}(e)=k,
$$

$$
\operatorname{target}(e)=\gamma(i),
\qquad
\operatorname{time}(e)=\iota_i(k),
\qquad
\operatorname{value}(e)=y.
$$

坐标 $i$ 与 $k$ 被保留。因此，即使两个端口给出相等的值，它们仍然是两个不同的记录。

### 3.2 内部消息与外部输出记录

定义所有可能的内部消息所成的集合：

$$
\mathsf{Msg}
=
\{(\mathrm{msg},\eta,a,y)\mid
\eta\in\mathbb N,\ a\in A,\ y\in P\}.
$$

对 $m=(\mathrm{msg},\eta,a,y)\in\mathsf{Msg}$ 定义：

$$
\operatorname{send}(m)=\eta,
\qquad
\operatorname{edge}(m)=a,
$$

$$
\operatorname{target}(m)=\operatorname{dst}(a),
\qquad
\operatorname{time}(m)=\eta+\delta(a),
\qquad
\operatorname{value}(m)=y.
\tag{7}
$$

$\eta$ 是源节点处理相应输入并产生该消息时所用的逻辑时间坐标；函数名 $\operatorname{send}$ 是它的简写。$\eta+\delta(a)$ 是逻辑到达时间。两者都是自然数坐标。若按第 2.2 节把 $\delta$ 分成节点耗时与传递耗时，$\eta$ 仍是源节点的输入处理时间坐标，而不是新引入的节点完成坐标。

定义所有可能的外部输出记录：

$$
\mathsf{OutRec}
=
\{(\mathrm{out},\theta,o,y)\mid
\theta\in\mathbb N,\ o\in\mathsf O,\ y\in P\}.
$$

对 $z=(\mathrm{out},\theta,o,y)\in\mathsf{OutRec}$ 定义：

$$
\operatorname{outtime}(z)=\theta,
\qquad
\operatorname{outport}(z)=o,
\qquad
\operatorname{outvalue}(z)=y.
$$

外部输出记录不会再次进入节点图，所以不为它定义 $\operatorname{target}$。

### 3.3 到达原子的集合

由于外部输入记录以 $\mathrm{ext}$ 开头，内部消息以 $\mathrm{msg}$ 开头，两个集合不相交。定义：

$$
\mathsf{Atom}=\mathsf{Ext}\cup\mathsf{Msg},
$$

以及节点 $v$ 所能接收的原子集合：

$$
\mathsf{Atom}_v
=
\{z\in\mathsf{Atom}\mid\operatorname{target}(z)=v\}.
$$

函数 $\operatorname{target}$、$\operatorname{time}$ 和 $\operatorname{value}$ 在 $\mathsf{Ext}$ 与 $\mathsf{Msg}$ 上已经分别定义，因此也在它们的不交并 $\mathsf{Atom}$ 上定义。

### 3.4 由节点与时间取出的纤维

任取有限集合 $E\subseteq\mathsf{Ext}$ 和 $M\subseteq\mathsf{Msg}$。对 $v\in V$ 与 $\theta\in\mathbb N$，定义：

$$
B_{v,\theta}(E,M)
=
\{z\in E\cup M
\mid
\operatorname{target}(z)=v,
\ \operatorname{time}(z)=\theta\}.
\tag{8}
$$

式 (8) 是映射：

$$
z\longmapsto
(\operatorname{target}(z),\operatorname{time}(z))
$$

在点 $(v,\theta)$ 上的逆像，所以定义它为节点 $v$ 在时间 $\theta$ 的**时间纤维**。附录 S 才把系统词 bucket / 输入桶对应到这个集合；正文推理统一使用“时间纤维”。

时间纤维不是一个额外容器公理；它就是式 (8) 所定义的有限集合。由集合的定义可立即得到：

- 同一时间纤维中的元素没有先后次序；
- 一条边的身份 $a$ 和一个输入端口的身份 $i$ 没有被删除；
- 一个时间纤维可以包含零个、一个或多个原子；
- 两个原子数值相等，并不推出它们是同一个原子。

例如，若：

$$
e_0=(\mathrm{ext},i_0,0,y),
\qquad
e_1=(\mathrm{ext},i_1,0,y),
$$

且 $\gamma(i_0)=\gamma(i_1)=v$、$\iota_{i_0}(0)=\iota_{i_1}(0)=5$，那么：

$$
B_{v,5}(\{e_0,e_1\},\varnothing)=\{e_0,e_1\}.
$$

这个集合有两个元素，即使两者承载的值都是 $y$。

本节尚未定义一次计算实际会产生哪些内部消息。因此，式 (8) 目前是任意 $E,M$ 上的集合构造。第 6 节通过递归定义实际消息集合；到那以后，才会定义一次输入对应的**完整时间纤维**。

## 4. 节点的局部函数

本节定义：在一个节点的旧状态与一个非空时间纤维已经给定时，该节点能算出哪些数学量。它尚不决定哪些节点被选择。

### 4.1 状态、本地内容与描述量

对每个 $v\in V$，给定：

- 非空状态集合 $S_v$；
- 初始状态 $q_v^{\mathrm{init}}\in S_v$；
- 非空本地内容集合 $X_v$；
- 非空选择描述量集合 $D_v$。

给定两个全函数：

$$
\operatorname{Agg}_v:
\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)
\to X_v,
$$

$$
\operatorname{Upd}_v:
S_v\times\mathbb N\times X_v
\to S_v.
\tag{9}
$$

任取旧状态 $q\in S_v$、时间 $\theta\in\mathbb N$ 和非空集合 $B\subseteq\mathsf{Atom}_v$，并假定 $B$ 中每个原子的时间都是 $\theta$。定义：

$$
h=\operatorname{Agg}_v(\theta,B),
\qquad
\widetilde q=\operatorname{Upd}_v(q,\theta,h).
\tag{10}
$$

$h$ 称为本地内容，$\widetilde q$ 称为候选新状态。这里“候选”表示 $\widetilde q$ 只是一个已经定义的函数值；它是否成为节点下一时刻可读的状态，要到第 5 节由区域选择结果共同决定。

$\operatorname{Agg}_v$ 的输入是原子集合本身。因此它可以读取外部记录中的端口 $i$，也可以读取内部消息中的边 $a$。若一个具体 $\operatorname{Agg}_v$ 只对所有 $\operatorname{value}(z)$ 求和，那是这个函数的特殊选择，不是式 (9) 强迫它忘记来源。

### 4.2 三种选择描述量

对每个节点给定三个全函数：

$$
\operatorname{Read}^{0}_v:
\mathbb N\times X_v\to D_v,
$$

$$
\operatorname{Read}^{-}_v:
S_v\times\mathbb N\times X_v\to D_v,
$$

$$
\operatorname{Read}^{+}_v:
S_v\times\mathbb N\times X_v\to D_v.
$$

对式 (10) 中的 $q,h,\widetilde q$，定义：

$$
d^0=\operatorname{Read}^{0}_v(\theta,h),
$$

$$
d^-=\operatorname{Read}^{-}_v(q,\theta,h),
$$

$$
d^+=\operatorname{Read}^{+}_v(\widetilde q,\theta,h).
\tag{11}
$$

三个上标的数学含义如下：

- $0$：不读取状态；
- $-$：读取处理当前非空时间纤维以前的状态 $q$；
- $+$：读取由本次输入算出的候选新状态 $\widetilde q$。

上标 $+$ 不表示 $\widetilde q$ 已经被采用。它只说明描述量函数以 $\widetilde q$ 为自变量。

### 4.3 节点的完整输出函数

对每个节点给定全函数：

$$
\operatorname{Full}_v:
S_v\times\mathbb N\times X_v
\to
(P_\bot)^{\operatorname{Out}(v)}
\times
(P_\bot)^{\operatorname{OutPort}(v)}.
\tag{12}
$$

若：

$$
(f^A,f^O)=\operatorname{Full}_v(q',\theta,h),
$$

则：

- 对每条 $a\in\operatorname{Out}(v)$，$f^A(a)\in P_\bot$ 决定是否沿边 $a$ 产生一个值；
- 对每个 $o\in\operatorname{OutPort}(v)$，$f^O(o)\in P_\bot$ 决定是否向外部输出端口 $o$ 产生一个值。

不同出边和不同输出端口是函数的不同坐标。因此模型直接支持一个节点向多个内部去向和多个外部去向给出不同的值。

## 5. 区域候选集合、选择函数与状态采用

本节在第 2.4 节的节点划分上定义共同选择。所有对象都只涉及同一个逻辑时间。

### 5.1 候选节点集合

先固定 $\theta\in\mathbb N$，并任取：

$$
B=(B_v)_{v\in V}
\in
\prod_{v\in V}\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v),
$$

其中每个 $B_v$ 的全部元素都具有时间 $\theta$。对区域 $j\in J$ 定义：

$$
C_j(B)
=
\{v\in\mathcal R_j\mid B_v\ne\varnothing\}.
\tag{13}
$$

这个集合的元素是节点，而不是原子。即使 $B_v$ 含有十个原子，节点 $v$ 也只在 $C_j(B)$ 中出现一次。

第 6 节把 $B_v$ 取为一次完整计算在 $(v,\theta)$ 的纤维，并把所得集合记为 $\mathcal C_{j,\theta}$。从现在起，$C_j(B)$ 的系统别名是候选集合，其中的节点称为候选节点。

### 5.2 选择描述量模式

对每个 $j\in J$ 固定：

$$
\tau_j\in\{0,-,+\}.
$$

若 $v\in\mathcal R_j$，则该区域为节点 $v$ 使用式 (11) 中的 $d^{\tau_j}$。区域中的所有候选节点使用同一种模式，但各节点的读取函数可以不同。

### 5.3 选择函数

对每个 $j\in J$ 固定整数：

$$
1\le K_j\le|\mathcal R_j|.
$$

对每个子集 $C\subseteq\mathcal R_j$，定义允许的选择结果集合：

$$
\mathsf{Allowed}_{j,C}
=
\{A'\subseteq C\mid |A'|\le K_j\}.
$$

再给定全函数族：

$$
\operatorname{Sel}_{j,C}:
\mathbb N\times\prod_{v\in C}D_v
\to\mathsf{Allowed}_{j,C}.
\tag{14}
$$

并规定 $\operatorname{Sel}_{j,\varnothing}$ 的值是 $\varnothing$。

若某个时间的完整候选集合是 $C$，候选描述量族是 $(d_v)_{v\in C}$，定义：

$$
A
=
\operatorname{Sel}_{j,C}
(\theta,(d_v)_{v\in C}).
\tag{15}
$$

从现在起，式 (14) 的系统别名是 **selector**，式 (15) 的集合 $A$ 称为 active set，其中的元素称为 active nodes。由值域定义自动得到：

$$
A\subseteq C,
\qquad
|A|\le K_j.
$$

式 (14) 没有规定必须按最大分数选择。最大值、Top-$K$、固定查表或任何别的确定性规则都可以成为一个具体的 $\operatorname{Sel}_{j,C}$。若规则可能遇到相等描述量，必须把确定的平局规则写进函数；不得让观察顺序代替函数定义。

### 5.4 哪些候选节点采用候选新状态

对每个区域固定一个二值参数：

$$
\kappa_j\in\{0,1\}.
$$

给定候选集合 $C$ 与 active set $A\subseteq C$，定义状态采用集合：

$$
O_j(C,A)
=
\begin{cases}
A,&\kappa_j=0,\\
C,&\kappa_j=1.
\end{cases}
\tag{16}
$$

对候选节点 $v\in C$，旧状态为 $q_v$，候选新状态为 $\widetilde q_v$，定义本次状态采用后的状态：

$$
q_v'
=
\begin{cases}
\widetilde q_v,&v\in O_j(C,A),\\
q_v,&v\notin O_j(C,A).
\end{cases}
\tag{17}
$$

只有 $v\in A$ 时才应用式 (12) 的 $\operatorname{Full}_v$。因此，以下两个问题被严格分开：

1. 节点是否采用候选新状态，由 $v\in O_j(C,A)$ 决定；
2. 节点是否执行完整输出函数，由 $v\in A$ 决定。

附录 S 把 $\kappa_j=0$ 与 $\kappa_j=1$ 分别对应到 `SD` 与 `BO`。正文只依赖式 (16)，不依赖这两个缩写。

### 5.5 同一时间内的数学依赖顺序

对一个非空候选集合，本模型的定义顺序是：

$$
\text{完整纤维}
\longrightarrow
(h,\widetilde q,d)
\longrightarrow
A
\longrightarrow
q'
\longrightarrow
\operatorname{Full}.
\tag{18}
$$

式 (18) 是函数自变量之间的依赖，不是对处理器指令或现实耗时的描述。一个实现可以提前求出某个纯函数值，但不能让后续函数作用读取尚未由式 (17) 确定的状态，也不能在式 (15) 以前发布只允许 active 节点产生的消息。

区域只计算集合 $A$。消息和外部输出始终由 $v\in A$ 的节点按照自己的式 (12) 产生。

## 6. 完整输入下的直接语义

前五节只给出了固定数据与局部函数。本节把它们组合成一次输入 $x$ 上的唯一完整计算。

### 6.1 一个有限逻辑时间上界

允许长度为零的路径停留在某个 $\gamma(i)$，并规定它的总时延为 $0$。对非空路径 $\zeta=(a_1,\ldots,a_k)$ 定义：

$$
\Delta(\zeta)=\sum_{\ell=1}^{k}\delta(a_\ell).
$$

因为 $G$ 是有限 DAG，从输入目标节点 $\gamma(i)$ 出发的路径总数有限。定义：

$$
\Delta_{\max}
=
\max\{\Delta(\zeta)\mid
\zeta\text{ 从某个 }\gamma(i)\text{ 出发，包括长度零路径}\}.
$$

再定义：

$$
\Theta_{\max}
=
\max_{i\in\mathsf I,\ k\in[L_i]}\iota_i(k)
+\Delta_{\max}.
\tag{19}
$$

第 6.5 节将证明，任何满足 $B_{v,\theta}\ne\varnothing$ 的坐标都满足 $\theta\le\Theta_{\max}$。

### 6.2 实际外部输入集合

由式 (3) 的具体输入 $x$ 定义：

$$
E_x
=
\{(\mathrm{ext},i,k,x_i(k))\mid
i\in\mathsf I,\ k\in[L_i]\}
\subseteq\mathsf{Ext}.
\tag{20}
$$

$E_x$ 包含每个输入位置恰好一条记录。

### 6.3 按逻辑时间递归

对每个节点，定义递归开始时的状态：

$$
q_v^{0}=q_v^{\mathrm{init}}.
$$

令 $M_{<0}=\varnothing$。依次对：

$$
\theta=0,1,\ldots,\Theta_{\max}
$$

执行下列纯数学递归。

#### 第一步：定义完整时间纤维与候选集合

假设更小逻辑时间产生的消息集合 $M_{<\theta}$ 已经定义。令：

$$
B_{v,\theta}
=
B_{v,\theta}(E_x,M_{<\theta}).
\tag{21}
$$

这里左边的 $B_{v,\theta}$ 是本次输入的一个确定集合；右边是式 (8) 的集合构造。从现在起，左边称为本次计算在 $(v,\theta)$ 的**完整时间纤维**。

对每个 $j\in J$ 定义：

$$
\mathcal C_{j,\theta}
=
\{v\in\mathcal R_j\mid B_{v,\theta}\ne\varnothing\}.
\tag{22}
$$

#### 第二步：为每个候选节点定义本地量

若 $v\in\mathcal C_{j,\theta}$，令它的旧状态为 $q_v^{\theta}$，并定义：

$$
h_{v,\theta}
=\operatorname{Agg}_v(\theta,B_{v,\theta}),
$$

$$
\widetilde q_{v,\theta}
=\operatorname{Upd}_v(q_v^{\theta},\theta,h_{v,\theta}).
$$

再按 $\tau_j$ 取式 (11) 中相应的描述量：

$$
d_{v,\theta}
=
\begin{cases}
\operatorname{Read}^{0}_v(\theta,h_{v,\theta}),&\tau_j=0,\\
\operatorname{Read}^{-}_v(q_v^{\theta},\theta,h_{v,\theta}),&\tau_j=-,\\
\operatorname{Read}^{+}_v(\widetilde q_{v,\theta},\theta,h_{v,\theta}),&\tau_j=+.
\end{cases}
\tag{23}
$$

#### 第三步：每个区域选择一次

定义：

$$
\mathcal A_{j,\theta}
=
\operatorname{Sel}_{j,\mathcal C_{j,\theta}}
\left(
\theta,
(d_{v,\theta})_{v\in\mathcal C_{j,\theta}}
\right).
\tag{24}
$$

当 $\mathcal C_{j,\theta}=\varnothing$ 时，式 (24) 的值按第 5.3 节规定为 $\varnothing$。

#### 第四步：定义时间 $\theta$ 以后的节点状态

对 $v\in\mathcal R_j$ 定义：

$$
q_v^{\theta+1}
=
\begin{cases}
\widetilde q_{v,\theta},
&v\in O_j(\mathcal C_{j,\theta},\mathcal A_{j,\theta}),\\
q_v^{\theta},&\text{其余情形}.
\end{cases}
\tag{25}
$$

不属于候选集合的节点自动落在第二种情形，所以状态不变。

#### 第五步：active 节点产生内部消息与外部输出

对每个 $v\in\mathcal A_{j,\theta}$ 定义：

$$
(f^A_{v,\theta},f^O_{v,\theta})
=
\operatorname{Full}_v
(q_v^{\theta+1},\theta,h_{v,\theta}).
\tag{26}
$$

定义时间 $\theta$ 产生的消息集合：

$$
\begin{aligned}
M_\theta
=\{&(\mathrm{msg},\theta,a,y)
\mid
j\in J,\ v\in\mathcal A_{j,\theta},\\
&a\in\operatorname{Out}(v),\\
&f^A_{v,\theta}(a)=y\in P\}.
\end{aligned}
\tag{27}
$$

定义时间 $\theta$ 产生的外部输出记录集合：

$$
\begin{aligned}
Z_\theta
=\{&(\mathrm{out},\theta,o,y)
\mid
j\in J,\ v\in\mathcal A_{j,\theta},\\
&o\in\operatorname{OutPort}(v),\\
&f^O_{v,\theta}(o)=y\in P\}.
\end{aligned}
\tag{28}
$$

最后令：

$$
M_{<\theta+1}=M_{<\theta}\cup M_\theta.
$$

这就完成从时间 $\theta$ 到 $\theta+1$ 的递归。

注意，由式 (7) 和 $\delta(a)>0$，任意 $m\in M_\theta$ 都满足：

$$
\operatorname{time}(m)=\theta+\delta(\operatorname{edge}(m))>\theta.
\tag{29}
$$

所以时间 $\theta$ 才产生的消息不会反过来改变式 (21) 已经定义的当前时间纤维。

### 6.4 节点事件与区域选择事件

本节中的“事件”不是概率论中作为样本空间子集的事件。这里先定义相应集合，再把属于这些集合的元素称为相应事件；“发生一次”只是对这种元素的文字称呼，不是额外的数学关系。

固定输入 $x$ 以及式 (21)--(29) 的递归结果，定义**节点事件集合**：

$$
\mathcal E_x^{\mathrm{node}}
=
\{(v,\theta)\in V\times[0,\Theta_{\max}+1)
\mid B_{v,\theta}\ne\varnothing\}.
$$

一个元素：

$$
e=(v,\theta)\in\mathcal E_x^{\mathrm{node}}
$$

称为输入 $x$ 的一个**节点事件**。它的节点坐标是 $v$，逻辑时间坐标是 $\theta$。本文直接用二元组 $(v,\theta)$ 表示这个事件，不再另外创造一个具有相同坐标的对象。

节点事件 $(v,\theta)$ 所处理的输入是完整时间纤维 $B_{v,\theta}$。二者不是同一个对象：前者是 $V\times\mathbb N$ 中的一个二元组，后者是 $\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)$ 中的一个有限集合。因此：

- 一个时间纤维含有多个原子时，仍然只对应一个节点事件；
- $B_{v,\theta}=\varnothing$ 时，$(v,\theta)$ 不是节点事件；
- $(v,\theta)$ 与 $(v',\theta)$ 在 $v\ne v'$ 时是两个不同的节点事件；
- 即使 $v\notin\mathcal A_{\rho(v),\theta}$，只要 $B_{v,\theta}\ne\varnothing$，$(v,\theta)$ 仍然是节点事件。

节点事件的逻辑时间坐标没有定义机器执行时刻或持续长度。$q_v^\theta$ 是处理这个节点事件以前的状态，$q_v^{\theta+1}$ 是按式 (25) 完成状态采用以后的状态。

再定义**区域选择事件集合**：

$$
\mathcal E_x^{\mathrm{sel}}
=
\{(j,\theta)\in J\times[0,\Theta_{\max}+1)
\mid\mathcal C_{j,\theta}\ne\varnothing\}.
$$

其中的元素 $(j,\theta)$ 称为输入 $x$ 的一个**区域选择事件**。它表示把区域 $j$ 在时间 $\theta$ 的整个候选描述量族一次交给式 (24)。当候选集合为空时，式 (24) 仍有规定值 $\varnothing$，但本文不把这个没有候选节点的平凡位置收入 $\mathcal E_x^{\mathrm{sel}}$。

由式 (22) 立即得到：

$$
\mathcal C_{j,\theta}
=
\{v\in\mathcal R_j\mid
(v,\theta)\in\mathcal E_x^{\mathrm{node}}\}.
$$

所以同一区域、同一逻辑时间的一个或多个节点事件共同对应一个区域选择事件。区域选择事件是否存在由 $\mathcal C_{j,\theta}$ 是否非空决定，不由 $\mathcal A_{j,\theta}$ 是否非空决定。

从本节以后，不加限定的“节点事件”总是指 $\mathcal E_x^{\mathrm{node}}$ 的元素，“区域选择事件”总是指 $\mathcal E_x^{\mathrm{sel}}$ 的元素。第 10 节还会把它们分解成更细的函数作用事件，并单独定义这些细分事件的集合。

### 6.5 有限性与唯一性定理

> [!theorem] 定理 1：完整计算存在、有限且唯一
> 固定第 1--5 节的全部集合、函数与参数，并给定式 (3) 的输入 $x$。则第 6.3 节唯一确定：
>
> - 每个完整时间纤维 $B_{v,\theta}$；
> - 每个候选集合 $\mathcal C_{j,\theta}$；
> - 每个 active set $\mathcal A_{j,\theta}$；
> - 节点事件集合 $\mathcal E_x^{\mathrm{node}}$ 与区域选择事件集合 $\mathcal E_x^{\mathrm{sel}}$；
> - 每个节点的状态序列；
> - 有限内部消息集合 $M^*$；
> - 有限多端口外部输出集合 $Z^*$。

**证明。** 对 $\theta$ 作归纳。

在 $\theta=0$ 时，$M_{<0}=\varnothing$，所以式 (21) 只由已给的 $E_x$ 唯一确定。第 4--5 节给定的 $\operatorname{Agg}$、$\operatorname{Upd}$、三个 $\operatorname{Read}$、$\operatorname{Sel}$ 与 $\operatorname{Full}$ 都是全函数，因而按式 (22)--(28) 依次求值会给出唯一结果。

假设所有小于 $\theta$ 的结果已经唯一确定，则 $M_{<\theta}$ 唯一。式 (21) 因而唯一；随后所有步骤仍是已给函数的求值，所以时间 $\theta$ 的结果唯一。自然数归纳法给出整个递归的唯一性。

还需证明递归不会产生到达时间超出式 (19) 的消息。任取节点事件 $(v,\theta)$，它所对应的 $B_{v,\theta}$ 至少含有一个到达原子 $z$。若 $z$ 是来自输入位置 $(i,k)$ 的外部输入记录，则 $v=\gamma(i)$ 且 $\theta=\iota_i(k)$。若 $z$ 是内部消息，则它来自某条终点为 $v$ 的边；沿这条消息回到产生它的节点事件，并继续向前追溯。每追溯一条边，节点在固定图中向上游移动一次。由于固定节点图无环，经过有限条边后必定到达某个外部输入记录。因此，每个节点事件的逻辑时间都可以写成：

$$
\iota_i(k)+\Delta(\zeta),
$$

其中 $\zeta$ 是从 $\gamma(i)$ 出发的一条有向路径。它不大于 $\Theta_{\max}$。若这个节点事件沿出边 $a$ 产生消息，就把 $a$ 接到 $\zeta$ 后面；所得仍是从 $\gamma(i)$ 出发的路径，所以这条新消息的到达时间也不大于 $\Theta_{\max}$。固定时间上界、有限节点、有限边和有限端口共同推出两个事件集合、消息集合和输出记录集合均有限。$\square$

定义：

$$
M^*=\bigcup_{\theta=0}^{\Theta_{\max}}M_\theta,
\qquad
Z^*=\bigcup_{\theta=0}^{\Theta_{\max}}Z_\theta.
\tag{30}
$$

最终状态是 $(q_v^{\Theta_{\max}+1})_{v\in V}$。把完整计算记录明确定义为：

$$
\mathcal T_x
=
\left(
(B_{v,\theta})_{\substack{v\in V\\\theta\in[0,\Theta_{\max}+1)}},
(\mathcal C_{j,\theta},\mathcal A_{j,\theta})_
{\substack{j\in J\\\theta\in[0,\Theta_{\max}+1)}},
(q_v^\theta)_
{\substack{v\in V\\\theta\in[0,\Theta_{\max}+2)}},
M^*,Z^*,
(f^A_{v,\theta},f^O_{v,\theta})_
{\substack{j\in J,\ \theta\in[0,\Theta_{\max}+1)\\
v\in\mathcal A_{j,\theta}}}
\right),
$$

其中时间纤维、选择和逐坐标输出函数值的时间坐标满足 $0\le\theta\le\Theta_{\max}$，状态还包含递归结束后的 $\theta=\Theta_{\max}+1$。称 $\mathcal T_x$ 为输入 $x$ 的完整计算记录。

本文把第 1--5 节的数据以及第 6 节所定义的直接语义合称为一个**带区域选择的 TimedDAG 规格**。

### 6.6 多输入、多输出不是后续扩展

多输入直接出现在式 (2)--(4) 与式 (20)--(21) 中。一个完整时间纤维可以同时包含：

- 不同端口产生的记录；
- 不同入边产生的消息；
- 外部输入记录与内部消息。

只要这些原子的 $\operatorname{target}$ 与 $\operatorname{time}$ 相同，它们就在式 (21) 的同一个集合中。由式 (4) 的严格递增性，同一输入端口在同一个逻辑时间至多贡献一个位置；不同端口不受这个限制。

多输出直接出现在式 (12) 与式 (28) 中。对每个 $o\in\mathsf O$，可以从 $Z^*$ 取出：

$$
Z_o^*
=
\{(\operatorname{outtime}(z),\operatorname{outvalue}(z))
\mid z\in Z^*,\ \operatorname{outport}(z)=o\}.
$$

整个外部结果是由端口标记的函数族 $(Z_o^*)_{o\in\mathsf O}$。单输入或单输出只是在 $\mathsf I$ 或 $\mathsf O$ 恰有一个元素时得到的特例。

对固定的 $(\theta,o)$，$Z^*$ 中至多有一个值 $y$：端口 $o$ 由式 (2) 指向唯一节点，而该节点的式 (12) 在坐标 $o$ 上只有一个函数值。因此每个 $Z_o^*$ 都是某个有限自然数子集到 $P$ 的函数图。

## 7. 一个从固定数据开始的完整手算例子

本节第一次使用前面全部定义。例子不要求任何外部文档。

### 7.1 固定集合与图

取：

$$
P=\mathbb N,
\qquad
V=\{s_0,s_1,a,b\},
\qquad
A=\{e_0,e_1\}.
$$

两条边定义为：

$$
\operatorname{src}(e_0)=s_0,
\quad
\operatorname{dst}(e_0)=a,
\quad
\delta(e_0)=5,
$$

$$
\operatorname{src}(e_1)=s_1,
\quad
\operatorname{dst}(e_1)=b,
\quad
\delta(e_1)=4.
$$

这张图只有 $s_0\to a$ 与 $s_1\to b$，所以没有有向环。

取两个输入端口和两个输出端口：

$$
\mathsf I=\{i_0,i_1\},
\qquad
\mathsf O=\{o_a,o_b\},
$$

$$
\gamma(i_0)=s_0,
\quad
\gamma(i_1)=s_1,
\quad
\varepsilon(o_a)=a,
\quad
\varepsilon(o_b)=b.
$$

两个输入端口都只有一个位置：

$$
L_{i_0}=L_{i_1}=1.
$$

具体输入与时间为：

$$
x_{i_0}(0)=2,
\quad
\iota_{i_0}(0)=0,
$$

$$
x_{i_1}(0)=7,
\quad
\iota_{i_1}(0)=1.
$$

区域划分为：

$$
\mathcal R_0=\{s_0\},
\qquad
\mathcal R_1=\{s_1\},
\qquad
\mathcal R_2=\{a,b\}.
$$

### 7.2 局部函数与选择函数

为简化状态，令每个节点的状态集合都是单点集 $\{*\}$，初态为 $*$，更新函数总返回 $*$。

令每个 $X_v=D_v=\mathbb N$，并定义：

$$
\operatorname{Agg}_v(\theta,B)
=
\sum_{z\in B}\operatorname{value}(z),
$$

$$
\operatorname{Read}^{0}_v(\theta,h)
=
\operatorname{Read}^{-}_v(*,\theta,h)
=
\operatorname{Read}^{+}_v(*,\theta,h)
=h.
$$

各区域都取 $\tau_j=0$ 和 $\kappa_j=0$，并取 $K_0=K_1=K_2=1$。单节点区域 $\mathcal R_0,\mathcal R_1$ 的 selector 在候选非空时选择唯一节点。

区域 $\mathcal R_2$ 取 $K_2=1$，其 selector 选择描述量较大的节点；若相等，固定选择 $a$。这条平局规则使它成为一个确定函数。

$s_0$ 的完整输出函数把 $h$ 沿 $e_0$ 发送；$s_1$ 把 $h$ 沿 $e_1$ 发送。节点 $a,b$ 没有图内出边；若它们 active，则分别把 $h$ 送到 $o_a,o_b$。其他值坐标均取 $\bot$。这样，式 (12) 要求的函数在其整个定义域上都已给定。

### 7.3 时间 0 与时间 1

实际外部输入集合为：

$$
E_x=
\{(\mathrm{ext},i_0,0,2),
(\mathrm{ext},i_1,0,7)\}.
$$

时间 $0$：

$$
B_{s_0,0}=\{(\mathrm{ext},i_0,0,2)\}.
$$

所以 $s_0$ 是区域 $0$ 的唯一候选并被选择，产生：

$$
m_0=(\mathrm{msg},0,e_0,2),
\qquad
\operatorname{time}(m_0)=0+5=5.
$$

时间 $1$：

$$
B_{s_1,1}=\{(\mathrm{ext},i_1,0,7)\}.
$$

所以 $s_1$ 被选择，产生：

$$
m_1=(\mathrm{msg},1,e_1,7),
\qquad
\operatorname{time}(m_1)=1+4=5.
$$

这里 $m_0,m_1$ 的发送时间不同，但逻辑到达时间相同。

### 7.4 时间 5 的共同选择

由式 (21)：

$$
B_{a,5}=\{m_0\},
\qquad
B_{b,5}=\{m_1\}.
$$

所以区域 $2$ 的完整候选集合是：

$$
\mathcal C_{2,5}=\{a,b\}.
$$

本地内容和描述量为：

$$
h_{a,5}=d_{a,5}=2,
\qquad
h_{b,5}=d_{b,5}=7.
$$

因此：

$$
\mathcal A_{2,5}=\{b\}.
$$

只有 $b$ 应用完整输出函数，于是：

$$
Z_5=\{(\mathrm{out},5,o_b,7)\}.
$$

$o_a$ 仍然是模型定义中的合法输出端口；本次输入只是在该端口没有产生记录。区域 $\mathcal R_2$ 没有发送任何东西，是节点 $b$ 向自己的输出端口产生了值。

### 7.5 这个例子已经说明什么

这个例子只使用式 (1)--(30)，并说明：

1. 两个外部输入端口可以有不同输入位置和不同注入时间；
2. 两条路径的总时延可以使它们在同一逻辑时间到达不同节点；
3. 同一区域的这些节点共同形成一个完整候选集合；
4. selector 的输入由节点名字标记，不带消息观察次序；
5. 模型有多个输出端口，即使一次具体计算只在其中一部分端口产生记录。

若再增加两个都指向节点 $a$ 的输入端口，并让它们在时间 $5$ 注入，那么两个外部记录会与 $m_0$ 一同出现在 $B_{a,5}$ 中。节点 $a$ 仍只作为一个候选出现，但 $\operatorname{Agg}_a$ 会接收整个三元素集合。

### 7.6 描述量模式与状态采用模式的四种组合

下面是另一个局部例子，不沿用第 7.1--7.5 节的单点状态集合。单独考察一个已经具有完整候选集合的区域时间位置，设：

$$
\mathcal C_{j,5}=\{a,b\},
\qquad
K_j=1,
$$

旧状态与本地内容分别为：

$$
q_a^5=0,
\quad
q_b^5=6,
\qquad
h_{a,5}=10,
\quad
h_{b,5}=1.
$$

取 $S_a=S_b=X_a=X_b=D_a=D_b=\mathbb N$，并定义：

$$
\operatorname{Upd}_v(q,\theta,h)=q+h,
$$

$$
\operatorname{Read}^{-}_v(q,\theta,h)=q,
\qquad
\operatorname{Read}^{+}_v(\widetilde q,\theta,h)=\widetilde q.
$$

于是候选新状态是：

$$
\widetilde q_{a,5}=10,
\qquad
\widetilde q_{b,5}=7.
$$

令 selector 选择描述量较大的一个节点。若 $\tau_j=-$，它读取旧状态 $(0,6)$，所以：

$$
\mathcal A_{j,5}=\{b\}.
$$

若 $\tau_j=+$，它读取候选新状态 $(10,7)$，所以：

$$
\mathcal A_{j,5}=\{a\}.
$$

再分别代入式 (16)--(17)，得到四种完整结果：

| $(\tau_j,\kappa_j)$ | selector 读取 | $\mathcal A_{j,5}$ | 状态采用集合 | $(q_a^6,q_b^6)$ | 应用 $\operatorname{Full}$ 的节点 |
| --- | --- | --- | --- | --- | --- |
| $(-,0)$ | $(0,6)$ | $\{b\}$ | $\{b\}$ | $(0,7)$ | $b$ |
| $(-,1)$ | $(0,6)$ | $\{b\}$ | $\{a,b\}$ | $(10,7)$ | $b$ |
| $(+,0)$ | $(10,7)$ | $\{a\}$ | $\{a\}$ | $(10,6)$ | $a$ |
| $(+,1)$ | $(10,7)$ | $\{a\}$ | $\{a,b\}$ | $(10,7)$ | $a$ |

所以 $\tau_j$ 与 $\kappa_j$ 是两项独立数学参数：前者可能改变 active set，后者可能改变未被选节点的未来状态。附录 S 中的 `pre/post` 与 `SD/BO` 只是这四种数学组合的系统名称。

## 8. 部分可见输入、封闭下界与候选集合关闭

第 6 节直接使用完整的 $E_x$ 与递归产生的 $M^*$。现实求值过程通常不会同时看见这些记录。本节不用现实时间描述这种差异，而是定义一列逐渐增大的有限集合。

### 8.1 观察阶段

取阶段编号 $n\in\mathbb N$。在阶段 $n$，令：

$$
E_n\subseteq E_x,
\qquad
H_n\subseteq M^*,
$$

分别表示已经可见的外部输入记录和内部消息。要求：

$$
E_n\subseteq E_{n+1},
\qquad
H_n\subseteq H_{n+1}.
\tag{31}
$$

$n$ 只给观察阶段排序，不传入 $\operatorname{Agg}$、$\operatorname{Upd}$、$\operatorname{Sel}$ 或 $\operatorname{Full}$。特别地，$n$ 与逻辑时间 $\theta$ 是两个不同的自然数变量。

定义阶段 $n$ 已看见的时间纤维：

$$
B^{(n)}_{v,\theta}
=
B_{v,\theta}(E_n,H_n).
\tag{32}
$$

由集合包含关系立即得到：

$$
B^{(n)}_{v,\theta}\subseteq B_{v,\theta}.
$$

这里右边是第 6 节定义的完整纤维。事实上，正时延还给出：

$$
B_{v,\theta}
=
B_{v,\theta}(E_x,M^*),
$$

因为任何到达时间为 $\theta$ 的实际消息都在小于 $\theta$ 的时间发送，因而已经属于式 (21) 使用的 $M_{<\theta}$。这个等式说明本节确实是在完整记录 $E_x\cup M^*$ 中逐步看见更多元素。

### 8.2 扩充自然数与最小值约定

定义：

$$
\overline{\mathbb N}=\mathbb N\cup\{\infty\},
$$

并规定每个 $b\in\mathbb N$ 都满足 $b<\infty$。再规定：

$$
\min\varnothing=\infty.
$$

引入 $\infty$ 只为了统一表示“以后没有尚未可见的记录”。它不属于节点函数使用的逻辑时间集合 $\mathbb T$。

### 8.3 输入端口和边的有效下界

在阶段 $n$，给定两个函数：

$$
\sigma_n^{\mathrm{in}}:\mathsf I\to\overline{\mathbb N},
\qquad
\sigma_n^{A}:A\to\overline{\mathbb N}.
$$

称它们**有效**，当且仅当同时满足：

$$
\begin{aligned}
\forall e\in E_x\setminus E_n,\qquad
&\operatorname{time}(e)
\ge
\sigma_n^{\mathrm{in}}(\operatorname{inport}(e)),
\\
\forall m\in M^*\setminus H_n,\qquad
&\operatorname{time}(m)
\ge
\sigma_n^{A}(\operatorname{edge}(m)).
\end{aligned}
\tag{33}
$$

附录 S 把 $\sigma$ 称为 seal。式 (33) 才是这个词的数学含义。

例如，$\sigma_n^A(a)=6$ 表示：边 $a$ 上任何尚未可见的实际消息，其逻辑到达时间都不小于 $6$。它仍允许以后看见时间 $6$ 的消息；它排除的是时间小于 $6$ 的尚未可见消息。

若 $\sigma_n^A(a)=\infty$，那么式 (33) 迫使边 $a$ 上没有任何尚未可见的实际消息。

相对于已经定义的完整记录，可以写出每个通道的最大有效下界：

$$
\widehat\sigma_n^{\mathrm{in}}(i)
=
\min\left(
\{\operatorname{time}(e)\mid
e\in E_x\setminus E_n,\ \operatorname{inport}(e)=i\}
\right),
$$

$$
\widehat\sigma_n^A(a)
=
\min\left(
\{\operatorname{time}(m)\mid
m\in M^*\setminus H_n,\ \operatorname{edge}(m)=a\}
\right).
$$

空集的最小值按第 8.2 节取 $\infty$。任意不大于相应 $\widehat\sigma$ 的数都是有效下界；大于它的数无效。这个公式只刻画“有效”一词，不是在线算法。

式 (33) 用完整结果 $M^*$ 判断一个下界是否为真，并不允许在线求值者预先读取 $M^*$。在线求值者必须从外部输入源的承诺或第 9.6 节的上游完成条件推出这个全称命题；不能任意填写一个较大的数。

合法的观察过程还要求这些下界不减小：

$$
\sigma_n^{\mathrm{in}}(i)
\le\sigma_{n+1}^{\mathrm{in}}(i),
\qquad
\sigma_n^A(a)\le\sigma_{n+1}^A(a).
\tag{34}
$$

### 8.4 节点与区域的封闭前沿

定义节点 $v$ 的封闭前沿：

$$
\lambda_n(v)
=
\min
\left(
\{\sigma_n^A(a)\mid a\in\operatorname{In}(v)\}
\cup
\{\sigma_n^{\mathrm{in}}(i)\mid i\in\operatorname{InPort}(v)\}
\right).
\tag{35}
$$

若节点没有入边也没有输入端口，括号内是空集，按第 8.2 节规定有 $\lambda_n(v)=\infty$。这种节点的所有完整时间纤维本来就为空。

定义区域的封闭前沿：

$$
\lambda_n(\mathcal R_j)
=
\min_{v\in\mathcal R_j}\lambda_n(v).
\tag{36}
$$

### 8.5 节点纤维关闭引理

> [!lemma] 引理 2：节点纤维关闭
> 若 $\lambda_n(v)>\theta$，则：
> $$
> B^{(n)}_{v,\theta}=B_{v,\theta}.
> \tag{37}
> $$

**证明。** 已知左边包含于右边。若右边还有一个左边没有的元素 $z$，则分两种情况。

若 $z$ 是来自端口 $i$ 的外部输入记录，则 $z\in E_x\setminus E_n$，且 $\operatorname{time}(z)=\theta$。由式 (35) 与 $\lambda_n(v)>\theta$ 可得 $\sigma_n^{\mathrm{in}}(i)>\theta$；这与式 (33) 要求 $\theta\ge\sigma_n^{\mathrm{in}}(i)$ 矛盾。

若 $z$ 是沿边 $a$ 到达的内部消息，同理得到 $\sigma_n^A(a)>\theta$，又与式 (33) 矛盾。因此不存在这样的 $z$，两集合相等。$\square$

严格不等式不能换成 $\lambda_n(v)\ge\theta$。下界等于 $\theta$ 时，式 (33) 仍允许一个尚未可见记录恰好具有时间 $\theta$。

### 8.6 区域候选集合关闭定理

定义阶段 $n$ 看见的候选集合：

$$
\mathcal C^{(n)}_{j,\theta}
=
\{v\in\mathcal R_j
\mid B^{(n)}_{v,\theta}\ne\varnothing\}.
$$

> [!theorem] 定理 3：完整候选集合不会再增加
> 若：
> $$
> \lambda_n(\mathcal R_j)>\theta,
> $$
> 则：
> $$
> \mathcal C^{(n)}_{j,\theta}
> =
> \mathcal C_{j,\theta}.
> \tag{38}
> $$

**证明。** 由式 (36)，区域中的每个 $v$ 都满足 $\lambda_n(v)>\theta$。引理 2 对每个成员给出：

$$
B^{(n)}_{v,\theta}=B_{v,\theta}.
$$

因此对每个 $v\in\mathcal R_j$：

$$
B^{(n)}_{v,\theta}\ne\varnothing
\Longleftrightarrow
B_{v,\theta}\ne\varnothing.
$$

取所有满足条件的节点，便得到式 (38)。$\square$

定理同时处理“有一个消息的节点”和“完整时间纤维为空的节点”。暂时没有看见到达节点 $c$ 的消息，并不能证明 $c$ 不在候选集合；只有 $\lambda_n(c)>\theta$ 才排除了以后补入时间 $\theta$ 的原子。

### 8.7 用第 7 节例子检查严格不等式

设某个阶段已经看见 $m_0$，但尚未看见 $m_1$。若关于边 $e_1$ 的有效下界是：

$$
\sigma_n^A(e_1)=5,
$$

这是可能的，因为尚未可见的 $m_1$ 恰好在时间 $5$ 到达。此时：

$$
\lambda_n(\mathcal R_2)\le5,
$$

所以不能对时间 $5$ 使用定理 3。当前看见的集合 $\{a\}$ 不是完整候选集合。

看见 $m_1$ 后，若两条边都再无不可见消息，可以有效地令：

$$
\sigma_{n'}^A(e_0)=\sigma_{n'}^A(e_1)=\infty.
$$

于是 $\lambda_{n'}(\mathcal R_2)=\infty>5$，定理 3 才证明候选集合等于 $\{a,b\}$。

### 8.8 输入完整与状态就绪是两个命题

定理 3 只证明时间 $\theta$ 的候选节点和每个候选节点的完整纤维已经确定。若式 (23) 使用 $q_v^\theta$ 或 $\widetilde q_{v,\theta}$，还必须先知道 $q_v^\theta$。

任取一个已经完成的节点事件集合：

$$
\mathsf{Done}\subseteq\mathcal E_x^{\mathrm{node}},
$$

并假定 $\mathsf{Done}$ 中的每个节点事件都已经按式 (25) 完成，而且同一节点在 $\mathsf{Done}$ 中的事件按逻辑时间递增完成。定义：节点 $v$ 在时间 $\theta$ 的旧状态关于 $\mathsf{Done}$ **就绪**，当且仅当所有满足：

$$
0\le r<\theta,
\qquad
(v,r)\in\mathcal E_x^{\mathrm{node}}
$$

的节点事件 $(v,r)$ 都属于 $\mathsf{Done}$。这时这些式 (25) 按 $r$ 递增连接成与第 6 节相同的唯一状态 $q_v^\theta$。

所以，对区域选择事件 $(j,\theta)\in\mathcal E_x^{\mathrm{sel}}$，一个统一而保守的求值条件是：

1. $\lambda_n(\mathcal R_j)>\theta$；
2. 每个 $v\in\mathcal C_{j,\theta}$ 的旧状态关于当前已完成节点事件集合 $\mathsf{Done}$ 就绪；
3. 每个候选描述量已经按式 (23) 求出；
4. $(j,\theta)$ 尚未应用过式 (24)。

当 $\tau_j=0$ 时，描述量本身不读取状态，可以先求描述量，再等待状态就绪后采用状态和执行完整函数。这种提前求值不会改变式 (21)--(30) 定义的结果。

## 9. 合法的乱序求值

第 6 节按逻辑时间递增定义结果，但这不要求实际求值者以完全相同的顺序工作。本节定义哪些次序变化不改变结果。

### 9.1 三类完成记录

在观察阶段 $n$，可以另外维护三个有限集合：

$$
\mathsf{Prepared}_n\subseteq\mathcal E_x^{\mathrm{node}},
$$

$$
\mathsf{Selected}_n\subseteq\mathcal E_x^{\mathrm{sel}},
$$

$$
\mathsf{Completed}_n\subseteq\mathcal E_x^{\mathrm{node}}.
$$

它们分别记录：

- $(v,\theta)$ 的完整纤维和所需本地量已经确定；
- $(j,\theta)$ 已经应用一次式 (24)；
- $(v,\theta)$ 已经完成式 (25)--(28) 中属于它的状态与输出判定。

三个集合都只能随 $n$ 增大。记录一个事件的前提是该事件使用的每个函数自变量都已经由第 6 节的相同数学对象确定。此外，内部消息只有在产生它的式 (26)--(27) 已经完成后才可以进入 $H_n$；这保证“看见消息”不先于“定义消息”。

在第 8.8 节的状态就绪定义中，现在取 $\mathsf{Done}=\mathsf{Completed}_n$。

### 9.2 合法选择

在阶段 $n$，对区域选择事件 $(j,\theta)\in\mathcal E_x^{\mathrm{sel}}$ 应用式 (24) 是合法的，当且仅当：

1. 定理 3 的前提成立；
2. 每个 $v\in\mathcal C_{j,\theta}$ 都满足 $(v,\theta)\in\mathsf{Prepared}_n$；
3. 每个 $v\in\mathcal C_{j,\theta}$ 的旧状态关于 $\mathsf{Completed}_n$ 就绪；
4. $(j,\theta)\notin\mathsf{Selected}_n$。

合法选择必须把完整函数族：

$$
(d_{v,\theta})_{v\in\mathcal C_{j,\theta}}
$$

一次交给式 (24)。不能只对已经较早准备好的真子集作出不可撤销选择。

若 $\mathcal C_{j,\theta}=\varnothing$，则 $(j,\theta)\notin\mathcal E_x^{\mathrm{sel}}$。此时式 (24) 的值已经按定义等于 $\varnothing$，不需要执行选择作用，也不在 $\mathsf{Selected}_n$ 中留下记录。

### 9.3 合法节点完成

若 $v\in\mathcal C_{j,\theta}$，则完成 $(v,\theta)$ 是合法的，当且仅当：

1. $(j,\theta)\in\mathsf{Selected}_n$；
2. 采用该次选择确定的 $\mathcal A_{j,\theta}$；
3. 这个节点的所有更小逻辑时间节点事件已经完成；
4. $(v,\theta)\notin\mathsf{Completed}_n$。

合法完成按式 (25) 唯一确定状态。只有 active 节点应用式 (26)，并且只把式 (27)--(28) 中非 $\bot$ 的坐标加入实际消息或输出集合。

同一区域中的不同节点事件在选择以后可以按不同观察阶段完成，因为它们修改的是不同状态坐标 $S_v$。但同一节点的节点事件必须按逻辑时间递增完成。

### 9.4 纯函数可以提前求值，语义结果不能提前发布

若 $B_{v,\theta}$ 已经由引理 2 确定，可以先求 $h_{v,\theta}$。若旧状态也已经确定，还可以先求 $\widetilde q_{v,\theta}$ 和三个描述量。

这些值可以保存在临时变量中，但在区域选择以前不得：

- 让更大逻辑时间的节点事件读取 $\widetilde q_{v,\theta}$；
- 应用只允许 active 节点执行的 $\operatorname{Full}_v$；
- 把候选消息加入可见消息集合；
- 把候选外部输出加入 $Z$。

原因不是“程序步骤必须长得一样”，而是这些动作会改变后续函数的数学自变量。

### 9.5 不得在下界之后倒填

若阶段 $n$ 已经公布有效值 $\sigma_n^A(a)=b$，后续阶段就不能首次加入满足：

$$
\operatorname{edge}(m)=a,
\qquad
\operatorname{time}(m)<b
$$

的消息。否则式 (33) 在阶段 $n$ 就是假的。

逻辑时间较小的消息可以比逻辑时间较大的消息更晚变得可见，只要此前的有效下界尚未越过它。非法的不是“观察得晚”，而是推翻一个已经用来作出不可撤销选择的全称命题。

### 9.6 边下界怎样由上游完成推出

定义：节点 $v$ 已经**完成到 $b\in\mathbb N$**，当且仅当：

1. $\lambda_n(v)\ge b$，所以它不再有尚未可见的时间小于 $b$ 的输入原子；
2. 对每个 $\theta<b$，若 $B_{v,\theta}\ne\varnothing$，则 $(v,\theta)\in\mathsf{Completed}_n$。

若 $v$ 已完成到 $b$，则以后尚未完成的任何节点事件 $(v,\theta)$ 都满足 $\theta\ge b$。对任意 $a\in\operatorname{Out}(v)$，这些节点事件以后可能产生的消息，其到达时间不小于：

$$
b+\delta(a).
$$

如果此前已经产生、且到达时间小于 $b+\delta(a)$ 的边 $a$ 消息也全部进入 $H_n$，那么：

$$
\sigma_n^A(a)=b+\delta(a)
\tag{39}
$$

是一个有效下界。

式 (39) 解释了为什么必须先使实际消息可见，再发布越过这些消息的边下界。空队列本身没有出现在证明中；证明使用的是上游完成命题和所有较早已产生消息均已可见这两个条件。

### 9.7 次序无关定理

> [!theorem] 定理 4：合法求值次序不改变完整结果
> 任取两个过程。假设它们从相同固定规格与输入 $x$ 开始，所有 $\sigma$ 都满足式 (33)--(34)，每一步都满足第 9.2--9.6 节，并且最终完成 $\mathcal E_x^{\mathrm{node}}$ 中的全部节点事件。则两个过程得到相同的 $\mathcal T_x$。

**证明。** 对二元组 $(\theta,p)$ 作字典序归纳，其中 $p=0,1,2,3$ 依次表示本地准备、区域选择、状态采用、完整输出。

在准备阶段，引理 2 保证所用纤维等于式 (21)，更小逻辑时间的归纳假设保证旧状态等于 $q_v^\theta$，所以式 (23) 的全部量相同。

在选择阶段，定理 3 保证候选集合相同；式 (14) 是函数，因此 active set 相同。

在状态采用与完整输出阶段，式 (16)、(25)--(28) 的每一步都由已经固定的输入和全函数唯一确定，因而新状态、消息和外部输出相同。对有限集合 $\mathcal E_x^{\mathrm{node}}$ 与 $\mathcal E_x^{\mathrm{sel}}$ 中的全部事件完成归纳，便得到整个记录相同。$\square$

这个定理允许改变独立函数作用的求值先后，但不允许改变函数的输入集合。

## 10. 一次计算产生的事件 DAG

第 6.4 节把 $(v,\theta)$ 作为一个完整的节点事件。但一个节点事件内部既有本地准备和状态采用，同一区域的多个节点事件又共同依赖一次区域选择。为了表示这些依赖，本节把节点事件与区域选择事件进一步拆成较细的**函数作用事件**，再构造它们之间的值与状态依赖图。

第 8--9 节在线证明“以后不会再有另一个原子”的封闭证书没有作为函数作用事件加入本图。若研究在线求值者自身的完整操作图，还需另外加入这些证书及其推导关系；本文不会把未画出的封闭证明冒充为值依赖边。

### 10.1 函数作用事件的集合

固定一次输入 $x$ 及其完整记录 $\mathcal T_x$。先取一个恰有四个元素的集合：

$$
\mathsf{ActKind}
=
\{\mathrm{prep},\mathrm{select},\mathrm{adopt},\mathrm{full}\},
$$

并明确规定其中四个标签两两不同。对节点事件 $(v,\theta)\in\mathcal E_x^{\mathrm{node}}$ 定义：

$$
P_{v,\theta}=(\mathrm{prep},v,\theta),
\qquad
U_{v,\theta}=(\mathrm{adopt},v,\theta).
$$

它们分别称为该节点事件的**本地准备作用事件**与**状态采用作用事件**。对区域选择事件 $(j,\theta)\in\mathcal E_x^{\mathrm{sel}}$ 定义：

$$
S_{j,\theta}=(\mathrm{select},j,\theta),
$$

称为该区域选择事件的**选择作用事件**。若 $v\in\mathcal A_{j,\theta}$，再定义：

$$
F_{v,\theta}=(\mathrm{full},v,\theta),
$$

称为 active 节点的**完整输出作用事件**。四个两两不同的标签保证四类函数作用事件彼此不同，即使它们其余坐标在集合论上碰巧相同。

定义全部函数作用事件所成的有限集合：

$$
\begin{aligned}
\mathscr V_x^{\mathrm{ev}}
={}&
\{P_{v,\theta},U_{v,\theta}\mid
v\in V,\ \theta\in[0,\Theta_{\max}+1),
B_{v,\theta}\ne\varnothing\}
\\
&\cup
\{S_{j,\theta}\mid
j\in J,\ \theta\in[0,\Theta_{\max}+1),
\mathcal C_{j,\theta}\ne\varnothing\}
\\
&\cup
\{F_{v,\theta}\mid
j\in J,\ \theta\in[0,\Theta_{\max}+1),
v\in\mathcal A_{j,\theta}\}.
\end{aligned}
$$

这里的 $P,S,U,F$ 只是上述带标签有序组的简称。$\mathscr V_x^{\mathrm{ev}}$ 的元素将成为另一张有向图的顶点；这个定义不向固定节点集合 $V$、区域集合 $J$、节点事件集合 $\mathcal E_x^{\mathrm{node}}$ 或区域选择事件集合 $\mathcal E_x^{\mathrm{sel}}$ 添加元素。

令：

$$
\mathscr A_x^{\mathrm{ev}}
\subseteq
\mathscr V_x^{\mathrm{ev}}
\times
\mathscr V_x^{\mathrm{ev}}
$$

是恰好由第 10.2--10.4 节所列有序对组成的关系；除这些小节列出的有序对以外，不加入其他边。定义事件图：

$$
\mathscr G_x^{\mathrm{ev}}
=
(\mathscr V_x^{\mathrm{ev}},\mathscr A_x^{\mathrm{ev}}).
$$

### 10.2 同一时间内的依赖边

若 $v\in\mathcal C_{j,\theta}$，令下列两个有序对属于 $\mathscr A_x^{\mathrm{ev}}$：

$$
P_{v,\theta}
\longrightarrow
S_{j,\theta}
\longrightarrow
U_{v,\theta}.
$$

若 $v\in\mathcal A_{j,\theta}$，再令下列有序对属于 $\mathscr A_x^{\mathrm{ev}}$：

$$
U_{v,\theta}\longrightarrow F_{v,\theta}.
$$

这些边正是式 (18) 中的依赖。

### 10.3 同一节点的状态依赖

若：

$$
(v,\theta),(v,\theta')\in\mathcal E_x^{\mathrm{node}},
\qquad
\theta<\theta',
$$

并且不存在满足：

$$
\theta<r<\theta',
\qquad
(v,r)\in\mathcal E_x^{\mathrm{node}}
$$

的 $r\in\mathbb N$，则令下列有序对属于 $\mathscr A_x^{\mathrm{ev}}$：

$$
U_{v,\theta}\longrightarrow P_{v,\theta'}.
$$

它表示 $P_{v,\theta'}$ 使用的旧状态由前一个节点事件的状态采用作用 $U_{v,\theta}$ 决定。

### 10.4 消息依赖

若 $F_{v,\theta}$ 产生消息：

$$
m=(\mathrm{msg},\theta,a,y),
$$

则令下列有序对属于 $\mathscr A_x^{\mathrm{ev}}$：

$$
F_{v,\theta}
\longrightarrow
P_{\operatorname{dst}(a),\theta+\delta(a)}.
$$

一个目标纤维若含多个消息，其准备顶点就可以有多个消息依赖前驱。

### 10.5 事件图无环

先在 $\mathscr V_x^{\mathrm{ev}}$ 上定义时间函数，使每个形式符号的时间都是其第二个下标：

$$
\operatorname{etime}(P_{v,\theta})
=\operatorname{etime}(U_{v,\theta})
=\operatorname{etime}(S_{j,\theta})
=\operatorname{etime}(F_{v,\theta})
=\theta.
$$

再定义阶段函数：

$$
p(P_{v,\theta})=0,
\qquad
p(S_{j,\theta})=1,
\qquad
p(U_{v,\theta})=2,
\qquad
p(F_{v,\theta})=3.
$$

对每个事件顶点 $\xi\in\mathscr V_x^{\mathrm{ev}}$ 定义秩：

$$
\operatorname{rank}(\xi)
=
(\operatorname{etime}(\xi),p(\xi))
\in\mathbb N\times\{0,1,2,3\}.
\tag{40}
$$

这里的字典序定义为：

$$
(\theta,p)<_{\mathrm{lex}}(\theta',p')
\Longleftrightarrow
\bigl(\theta<\theta'\bigr)
\qquad\text{或}\qquad
\bigl(\theta=\theta'\ \text{且}\ p<p'\bigr).
$$

按这个次序比较秩。同一时间内的依赖严格增加 $p$；状态依赖严格增加 $\theta$；消息依赖由 $\delta(a)>0$ 也严格增加 $\theta$。所以每条事件边都严格增加式 (40)。沿有向边不可能回到原秩，因此事件图没有有向环。

由此得到两项不同事实：

1. 固定空间图 $G$ 按第 2.2 节的假设是 DAG；
2. 每次具体输入产生的上述细分事件图也由式 (40) 证明为 DAG。

`TimedDAG` 不是在这两者中二选一。本文的规格以固定空间 DAG 为结构，并且它的每次运行还导出一张依赖于输入的事件 DAG。前者说明允许在哪里传值，后者说明这一次实际发生的函数作用怎样依赖。

### 10.6 区域商图可以有环

只为研究区域布局，定义关系：

$$
Q_\rho
=
\{(j,j')\in J\times J
\mid j\ne j',
\ \exists a\in A:
\rho(\operatorname{src}(a))=j,
\rho(\operatorname{dst}(a))=j'\}.
\tag{41}
$$

称 $(J,Q_\rho)$ 为区域商图。它不是消息图。

$\mathcal R_j$ 本身只是一个节点子集。如果把 $G$ 中起点和终点都位于 $\mathcal R_j$ 的边取出来，就得到 $G$ 在该子集上的诱导子图；由于 $G$ 已经是 DAG，这个诱导子图自动无环，不需要再加一条“region 无环”公理。与此不同，式 (41) 把每个节点子集收缩成一个点，所得区域商图可以有环。

即使固定节点图是路径：

$$
u\longrightarrow v\longrightarrow w,
$$

只要 $u,w\in\mathcal R_0$ 且 $v\in\mathcal R_1$，区域商图就含有：

$$
0\longrightarrow1\longrightarrow0.
$$

这不构成函数作用事件图中的有向环。即使某次计算确实沿这两条空间边依次产生消息，每条消息依赖边也会因 $\delta(a)>0$ 而严格增加逻辑时间。若第一条消息由逻辑时间 $\theta$ 的节点事件产生，那么返回区域 $0$ 时，对应的节点事件与区域选择事件具有某个逻辑时间 $\theta'>\theta$。本文因此不要求区域商图无环。

## 11. 在逻辑时间切面停止与继续

### 11.1 完整切面

固定 $b\in\mathbb N$，并要求 $0\le b\le\Theta_{\max}+1$。称计算已经完成时间切面 $b$，当且仅当同时满足：

1. 每个满足 $(v,\theta)\in\mathcal E_x^{\mathrm{node}}$ 且 $\theta<b$ 的节点事件都已经完成 $P_{v,\theta}$ 与 $U_{v,\theta}$；若 $v\in\mathcal A_{\rho(v),\theta}$，还已经完成 $F_{v,\theta}$；
2. 每个满足 $(j,\theta)\in\mathcal E_x^{\mathrm{sel}}$ 且 $\theta<b$ 的区域选择事件都已经完成 $S_{j,\theta}$；
3. 上述完整输出作用事件产生的内部消息和外部输出都已经确定。

这是一个逻辑时间边界。它不包含“在同一次区域选择进行到一半时暂停”的情况。

### 11.2 跨越切面的内部消息

定义：

$$
W_b
=
\{m\in M^*\mid
\operatorname{send}(m)<b
\le\operatorname{time}(m)\}.
\tag{42}
$$

$W_b$ 中的每条消息都已经由某个满足 $\theta<b$ 的完整输出作用事件 $F_{v,\theta}$ 产生，但它到达的完整时间纤维位于切面右侧。丢掉 $W_b$ 会改变未来某些式 (21)。

### 11.3 切面状态、未来输入和输出前缀

第 6 节的 $q_v^b$ 正好是节点 $v$ 完成所有满足 $\theta<b$ 的状态采用作用事件 $U_{v,\theta}$ 以后、处理逻辑时间 $b$ 的任何节点事件以前的状态。

定义未来外部输入记录：

$$
E_{\ge b}
=
\{e\in E_x\mid\operatorname{time}(e)\ge b\},
$$

以及已经产生的外部输出前缀：

$$
Z_{<b}
=
\{z\in Z^*\mid\operatorname{outtime}(z)<b\}.
$$

定义切面上的未来计算状态：

$$
Q_b
=
\left(
b,
(q_v^b)_{v\in V},
W_b
\right).
\tag{43}
$$

$Z_{<b}$ 不影响未来节点计算；若要在恢复后重建完整多端口输出记录，则还要保存 $Z_{<b}$ 或保存“这些输出已被外部可靠接收”的等价证据。

### 11.4 分段继续定理

> [!theorem] 定理 5：完整切面上的继续等于一次算完
> 从 $Q_b$ 开始，以 $(q_v^b)$ 为初始节点状态，令恢复递归开始时已有消息集合 $M^{\mathrm{res}}_{<b}=W_b$，并只使用 $E_{\ge b}$。随后把式 (21) 改写为：
> $$
> B^{\mathrm{res}}_{v,\theta}
> =
> B_{v,\theta}(E_{\ge b},M^{\mathrm{res}}_{<\theta})
> \qquad(\theta\ge b),
> $$
> 其余步骤仍按第 6.3 节递归。所得时间不小于 $b$ 的状态、候选集合、active sets、内部消息和外部输出，与完整计算 $\mathcal T_x$ 的相应后缀相同。

**证明。** 对 $\theta\ge b$ 归纳。时间 $b$ 的旧状态由式 (43) 与完整计算相同。其外部输入由 $E_{\ge b}$ 相同；所有从左侧跨入的消息恰好是式 (42)，所以时间 $b$ 的完整纤维相同。按式 (22)--(28) 依次求值时，每一步都由已给函数和集合构造唯一确定，因此时间 $b$ 的结果相同。

假设直到 $\theta-1$ 都相同，则右侧已经新产生的消息相同，加上相同的 $W_b$ 与未来外部输入，时间 $\theta$ 的完整纤维相同；再次应用相同函数得到相同结果。归纳完成。$\square$

这个定理说明式 (43) 足以在完整逻辑切面恢复当前的无状态 selector 模型。若以后让 selector 自身跨时间保存状态，该状态也必须加入 $Q_b$。

## 12. 正确性、区域结构与联合求值必须分层

### 12.1 区域前沿由最慢成员决定

由式 (36)，对每个 $v\in\mathcal R_j$：

$$
\lambda_n(\mathcal R_j)\le\lambda_n(v).
$$

例如成员前沿分别为 $100,96,17$ 时，区域前沿是 $17$。前两个节点已经能够证明更远时间的纤维完整，但整个区域在时间不小于 $17$ 处仍可能新增候选成员。

这不是实现策略，而是最小值定义的直接结果。

### 12.2 当前已经关闭的区域时间集合

任取 $c_j\in\mathbb N$，并要求 $0\le c_j\le\Theta_{\max}+1$；把它作为本次要研究的时间区间左端点。定义：

$$
\mathcal W_{j,n}
=
\{\theta\in[c_j,\Theta_{\max}+1)
\mid
\theta<\lambda_n(\mathcal R_j),
\ \mathcal C_{j,\theta}\ne\varnothing\}.
\tag{44}
$$

对每个 $\theta\in\mathcal W_{j,n}$，定理 3 已经固定候选集合。集合很大只表示有很多区域时间位置的输入完整；它不自动给出一个能同时求值所有递归状态的快速公式。

### 12.3 区域商图无环只是一项可选附加条件

若式 (41) 的 $(J,Q_\rho)$ 恰好无环，可以选择一个区域全序，使每条商图边的起点都排在终点以前；这样的全序称为区域拓扑序。随后可以沿这个次序研究一种更规则的前沿传播方法。这可能帮助构造较大的式 (44)，但它不改变式 (33)--(36) 中任何一个已给下界的数值。

反之，区域商图有环也不破坏第 6 节的语义、定理 3 或第 10.5 节的事件 DAG 证明。

因此：

$$
\text{区域商图无环}
$$

可以是以后性能定理的前提，但不是当前合法性的前提。

### 12.4 联合求值还需要函数的代数性质

固定 $k\in\mathbb N_{>0}$。对每个 $\ell\in\{1,\ldots,k\}$，给定集合 $X_\ell,Y_\ell$ 和函数：

$$
f_\ell:X_\ell\to Y_\ell.
$$

再给定两个集合 $W_{\mathrm{in}},W_{\mathrm{out}}$。若要用一个联合函数代替逐项求值，至少要构造三个有明确类型的函数：

$$
\operatorname{Pack}:
\prod_{\ell=1}^{k}X_\ell
\to W_{\mathrm{in}},
$$

$$
\mathcal K:W_{\mathrm{in}}\to W_{\mathrm{out}},
$$

$$
\operatorname{Unpack}:
W_{\mathrm{out}}
\to\prod_{\ell=1}^{k}Y_\ell,
$$

并证明对所有 $(z_\ell)_{\ell=1}^{k}\in\prod_{\ell=1}^{k}X_\ell$：

$$
\operatorname{Unpack}
\left(
\mathcal K(\operatorname{Pack}((z_\ell)_{\ell=1}^{k}))
\right)
=
\left(f_\ell(z_\ell)\right)_{\ell=1}^{k}.
\tag{45}
$$

并且右边若含状态递归，必须按第 6 节的状态依赖解释。

定理 3 证明输入不再增加；式 (45) 证明一次联合计算没有改变结果。这是两个不同命题。

### 12.5 四层研究顺序

可以把后续工作分成四层：

1. **语义层**：第 1--6 节定义什么结果是正确的；
2. **知识层**：第 8--9 节证明何时已经知道足够多，可以不可撤销地求值；
3. **代数层**：证明哪些逐时间函数满足式 (45) 一类联合求值等式；
4. **实现层**：为已经证明的联合函数寻找具体硬件上的高效程序。

任一层都不能由后一层的术语替代。区域划分给出共同选择的边界，但不会替任意节点函数制造可联合求值性质。

## 13. 从当前 TimedDAG 继续扩展时会改变什么

本节不是当前定义的一部分，只说明每种扩展会触及哪一条证明。

### 13.1 允许固定节点图有环，但仍保持正时延

若删除第 2.2 节“固定图无环”的条件，而仍保持每条边 $\delta(a)>0$，则对任意固定有限时间上界 $B$，按 $\theta=0,\ldots,B$ 的递归仍然唯一，因为当前消息只能影响更大时间。

但一次完整运行可能沿有向环不断产生更大时间的消息，不再具有式 (19) 的全局有限上界。因此要改为研究：给定有限逻辑时间切面，是否能在有限工作后完成该切面。定理 1 的“整个运行有限”部分不能原样保留。

### 13.2 允许零时延边

若某条边满足 $\delta(a)=0$，时间 $\theta$ 的完整输出可能立即改变同一时间的输入纤维。式 (29) 失效，事件秩可能从阶段 $3$ 指回同一时间的阶段 $0$。

这时必须另外定义同刻求值序、固定点、方程求解器或拒绝某些环。不能只把 $0$ 填入现有 $\delta$ 而继续使用当前证明。

### 13.3 节点内部异步计算

在完整纤维已经确定后，一个节点可以把 $\operatorname{Agg}$、$\operatorname{Upd}$、读取函数和 $\operatorname{Full}$ 分成许多内部步骤。只要存在一个删除这些内部中间量的函数，并且删除后得到的状态、消息和输出仍等于式 (9)--(12)，这种分解就没有改变正文语义。

若希望在同一逻辑时间的完整纤维尚未确定前，就根据部分原子发布不可撤销状态或图内消息，则已不再实现本文函数。它需要新的节点语义，并必须重新证明候选集合、消息发射和封闭下界之间的关系。

### 13.4 为 selector 增加跨时间状态

当前 $\operatorname{Sel}_{j,C}$ 只读取 $\theta$ 与当前描述量族。若为区域 $j$ 增加非空状态集合 $Y_j$，需要把式 (14) 改为：

$$
\operatorname{Sel}_{j,C}:
Y_j\times\mathbb N\times\prod_{v\in C}D_v
\to Y_j\times\mathsf{Allowed}_{j,C}.
$$

随后，同一区域的选择必须按时间连接 selector 状态，第 10 节事件图要增加状态边，第 11 节的 $Q_b$ 也要保存切面处的 $Y_j$ 元素。

### 13.5 允许一个节点属于多个选择域

当前满射 $\rho:V\to J$ 保证每个节点恰属一个区域。若一个节点同时参加多个选择，必须定义多个选择结果发生冲突时怎样决定状态采用与完整输出。把 $\rho$ 换成一般关系而不增加冲突规则，不会得到一个完整函数。

## 14. 本文已经证明的结果与尚未证明的结果

本文正文已经给出：

1. 完整输入下有限且唯一的直接语义（定理 1）；
2. 节点时间纤维的关闭条件（引理 2）；
3. 区域候选集合不会再增加的条件（定理 3）；
4. 在所列合法条件下的求值次序无关（定理 4）；
5. 完整逻辑时间切面上的继续等于一次算完（定理 5）；
6. 每次有限运行的规范值与状态依赖事件图无环；
7. 区域商图不必无环。

仍需单独完成的工作包括：

- 把第 9 节的阶段过程实现成最小整数参考解释器，并以随机可见次序检验定理 4；
- 给出从更受限模型到本文坐标的完整嵌入证明，而不只比较最终输出；
- 找到能推出较大关闭窗口的区域结构定理；
- 对具体神经节点证明式 (45) 的联合求值等式与复杂度；
- 扩展到带正时延环的有限切面语义；
- 最后才研究零时延环或更一般的 Graph。

## 15. 建议的学习顺序

第一次阅读只完成以下步骤：

1. 读第 1--3 节，独立写出一个 $B_{v,\theta}(E,M)$；确认它只是由目标与时间取出的集合。
2. 读第 4--5 节，给定一个旧状态和非空纤维，依次写出 $h,\widetilde q,d,C,A,O,q'$。
3. 手算第 7 节，直到能够解释为什么 $m_0,m_1$ 的发送时间不同而到达时间相同。

第二次阅读再做：

4. 从式 (33)--(36) 不看证明地重证引理 2 与定理 3。
5. 构造一个节点最终完整时间纤维为空的例子，说明为什么仍需该节点的前沿越过 $\theta$。
6. 分别取 $\tau_j=-,+$ 与 $\kappa_j=0,1$，手算四种组合，确认“读取哪个状态”和“采用哪个状态”是不同坐标。

第三次阅读才做：

7. 为第 7 节列出 $P,S,U,F$ 事件顶点，并检查每条边都增加式 (40)。
8. 选择一个切面 $b$，写出 $W_b$，然后检查丢掉它会使哪个未来完整时间纤维缺元素。
9. 最后研究式 (44)--(45)，不要把较大的关闭窗口误当成已经存在高效联合算法。

## 16. 可选的相关材料

本文的数学定义不依赖下列材料。只有在已经能够独立手算第 7 节后，才建议按目的查阅：

- [[timed-dag-v0-learning-note|较小的无显式区域选择学习模型]]；
- [SettleGraph 的独立语义文档](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/experiment-semantics-and-naming.md)；
- [[current-mainline|TIDE 当前研究台阶]]。

这些材料中的同名词不能反过来改写本文公式；若两份文档要建立关系，必须给出从一边全部数学坐标到另一边全部数学坐标的函数或关系。

## 附录 S：计算机系统词汇与正文数学对象的对应（可选）

本附录只做翻译，不增加正文定理的前提。每个块默认折叠，可以在遇到相应系统词时再展开。

> [!info]- S.1　logical time、machine time、arrival 与 visibility
> **logical time（逻辑时间）**对应第 2.1 节的 $\theta\in\mathbb N$。内部消息的逻辑到达时间由式 (7) 定义。
>
> **machine time / wall clock（机器时间、墙钟时间）**若需要记录，可以另取 $w\in\mathbb R_{\ge0}$。正文所有节点函数和 selector 都没有 $w$ 这个自变量，所以墙钟先后不能改变函数值。
>
> **visibility（可见）**对应某条记录何时进入第 8.1 节的 $E_n$ 或 $H_n$。观察阶段 $n$ 也不是逻辑时间；它只排列“已经知道哪些记录”。
>
> 一条逻辑到达时间为 $5$ 的消息可以在很晚的观察阶段才进入 $H_n$。只要此前没有发布排除它的有效下界，这仍是合法过程。

> [!info]- S.2　message、port、bucket 与 channel identity
> **message（消息）**对应 $m=(\mathrm{msg},\eta,a,y)\in\mathsf{Msg}$。payload 只对应 $y$；发送时间 $\eta$ 和边 $a$ 也是完整消息的坐标。
>
> **input/output port（输入、输出端口）**对应 $\mathsf I,\mathsf O$ 与式 (2)。端口不是节点。多个端口可以属于同一节点。
>
> **bucket / input bucket / time bucket（输入桶、时间桶）**严格对应式 (8) 的纤维 $B_{v,\theta}(E,M)$。在完整语义里，式 (21) 把它实例化为 $B_{v,\theta}$。
>
> **channel identity（通道身份）**对应内部消息保留的边坐标 $a$；外部输入来源对应端口坐标 $i$。$\operatorname{Agg}_v$ 可以区分它们。数组或队列只是这些有限集合的一种编码。

> [!info]- S.3　region、candidate、selector、active 与 Top-K
> **region（区域）**只对应式 (6) 的节点子集 $\mathcal R_j$。它不持有消息和节点状态。
>
> **candidate（候选）**对应式 (22) 中满足 $B_{v,\theta}\ne\varnothing$ 的节点。
>
> **selector（选择器）**对应式 (14) 的函数族。它的完整输入包括整个候选集合的带节点坐标描述量族。
>
> **active / selected（激活、选中）**对应 $v\in\mathcal A_{j,\theta}$。只有 active 节点应用式 (26)。
>
> **Top-K**只是式 (14) 的一种实例。若分数相等，固定平局规则属于函数定义的一部分。
>
> **routing（路由）**可以从实际 active sets 与式 (27) 真正产生的边消息导出。selector 不修改固定边集合 $A$。

> [!info]- S.4　content、pre、post、SD、BO 与 expensive compute
> `content` 对应 $\tau_j=0$ 与式 (11) 的 $d^0$；`pre` 对应 $\tau_j=-$ 与 $d^-$；`post` 对应 $\tau_j=+$ 与 $d^+$。
>
> `SD`（selected-dispatch）对应 $\kappa_j=0$，即式 (16) 中只有 active nodes 采用候选新状态。
>
> `BO`（broadcast-observe）对应 $\kappa_j=1$，即全部 candidates 采用候选新状态，但仍只有 active nodes 执行完整输出函数。
>
> 因此 `content/pre/post` 决定 selector 读取什么；`SD/BO` 决定哪些候选状态被采用。它们是两条独立的配置轴。
>
> **proposal** 对应候选新状态 $\widetilde q$。**commit** 的最小语义对应式 (25) 使同一节点在更大逻辑时间的本地准备作用事件读取新状态。**expensive compute / NodeCompute** 对应式 (12) 与 (26) 的 $\operatorname{Full}_v$；“昂贵”不是数学性质，只是实现动机。

> [!info]- S.5　seal、frontier、watermark、ready 与 barrier
> **seal（封闭下界）**对应式 (33) 中的 $\sigma_n^{\mathrm{in}}(i)$ 或 $\sigma_n^A(a)$。它是关于所有尚未可见记录的全称命题，不是“当前队列为空”。
>
> **node frontier** 对应式 (35)；**region frontier** 对应式 (36)。区域前沿是成员前沿的最小值。
>
> **watermark** 在不同系统中含义不统一。若它表示“输入已经确定到哪里”，必须明确对应哪一个 $\sigma$ 或 $\lambda$；若它表示“计算已经完成到哪里”，则对应第 9.6 节的另一项完成谓词。两者不能因为同名而合并。
>
> **ready（就绪）**是一个复合谓词。本文的保守区域就绪条件列在第 8.8 节，既包括候选集合关闭，也包括所需旧状态已经确定。
>
> **barrier（屏障）**是实现等待这些数学条件成立的位置，并不要求所有处理器同时停止。

> [!info]- S.6　identifier、schema 与 semantic coordinate
> **identifier / ID（标识符）**在正文中首先就是集合元素本身，例如 $v\in V$、$a\in A$。若程序需要整数，可为本文任一有限对象集合 $X$ 固定单射 $\operatorname{id}_X:X\to\mathbb N$。单射保证不同对象有不同整数。
>
> **schema（数据形状约定）**对应一个积集合以及各坐标的所属集合。例如 $\mathsf{Msg}$ 规定消息具有标签、发送时间、边和值四个坐标。字段名可以改变；删除边坐标则会改变正文对象。
>
> **semantic coordinate（语义坐标）**是在已经说明对象类型后，用于唯一指出该类型中数学对象的有序组。节点事件的语义坐标是 $(v,\theta)$，区域选择事件的语义坐标是 $(j,\theta)$，函数作用事件还包含 $\mathrm{prep}$、$\mathrm{select}$、$\mathrm{adopt}$ 或 $\mathrm{full}$ 标签；输出位置的坐标是 $(\theta,o)$。
>
> 若三类事件需要共享一个整数 ID 空间，先取三个两两不同的标签 $\mathrm{node},\mathrm{sel},\mathrm{act}$，并定义有限编码域：
> $$
> \mathsf{EventRef}_x
> =
> (\{\mathrm{node}\}\times\mathcal E_x^{\mathrm{node}})
> \cup
> (\{\mathrm{sel}\}\times\mathcal E_x^{\mathrm{sel}})
> \cup
> (\{\mathrm{act}\}\times\mathscr V_x^{\mathrm{ev}}).
> $$
> 再固定单射：
> $$
> \operatorname{id}_{\mathrm{event},x}:
> \mathsf{EventRef}_x\to\mathbb N.
> $$
> 外层标签先把不同层次的事件变成不同编码对象，随后单射保证不同编码对象不会共用一个整数。这里 $\mathsf{EventRef}_x$ 只是一项编码域，不把三种事件合并成同一种语义作用。这项编码固定在输入 $x$ 的完整事件集合上；在同一次计算中，观察阶段 $n$、线程编号、墙钟时刻和本次分块编号都不在编码函数的输入中，所以改变它们不会改变 ID。若还要求不同输入之间共享稳定整数 ID，就需要另外在一个与输入无关的全局坐标域上固定编码；这不是本文语义的前提。

> [!info]- S.7　chunk、prefill、decode、packing 与 fast path
> **chunk（分块）**可以数学化为一个选定有限事件集合的划分，并且必须先说明采用节点事件、区域选择事件还是函数作用事件这一粒度。若 $\mathscr E=\mathscr E_1\cup\cdots\cup\mathscr E_k$ 且各 $\mathscr E_i$ 两两不交，那么 $(\mathscr E_i)$ 是 $\mathscr E$ 的一种分块。它不改变任何事件原有的标签或语义坐标。
>
> **prefill** 通常表示一次联合处理许多已知输入位置；**decode** 通常表示逐个或小批增加输入位置。要声称二者等价，必须比较第 6 节的状态、内部消息、所有输出端口、候选集合和 active sets，而不只是最后一个张量。
>
> **packing / packed attention** 是式 (45) 中 $\operatorname{Pack},\mathcal K,\operatorname{Unpack}$ 的具体实现候选。seal 证明输入不会再增加；式 (45) 证明联合求值等于参考递归。两项证明不能互相替代。
>
> **fast path** 可以在额外图结构和代数条件成立时使用联合函数；一般路径仍须实现第 6 与第 9 节的语义。

> [!info]- S.8　runtime、scheduler、workspace、commit 与 trace
> **runtime / executor（运行时、解释器）**是维护可见集合、状态、下界和完成记录，并求正文函数值的程序。它不是固定图本身。
>
> **scheduler（调度器）**从当前满足第 9.2--9.3 节条件的区域选择事件或节点事件中选下一项。它可以影响现实性能，不能改变 selector 的数学输入。
>
> **workspace（临时工作区）**可以保存第 9.4 节提前求出的 $h,\widetilde q,d$。临时变量不等于式 (25) 已经采用的状态。
>
> **atomic commit（原子提交）**在本文中的最小要求是：依赖该状态的后继函数作用事件只能读取式 (25) 确定以前的 $q_v^\theta$ 或确定以后的 $q_v^{\theta+1}$，不能读取一个未由规格定义的中间状态。它不声称使用某条特定处理器原子指令。
>
> **trace（轨迹）**可以取为 $\mathcal T_x$ 的某个投影。墙钟耗时、线程号和日志打印顺序只有显式加入结果集合后才属于另一个更丰富的 trace。

> [!info]- S.9　continuation、checkpoint、resume 与 refinement
> **continuation** 对应式 (43) 的 $Q_b$。**checkpoint** 是 $Q_b$ 的某种可保存编码。
>
> 若保存与读取函数分别为 $\operatorname{save}$ 和 $\operatorname{load}$，无损编码至少要求：
> $$
> \operatorname{load}(\operatorname{save}(Q_b))=Q_b.
> $$
>
> **resume / replay** 对应从相同 $Q_b$ 与 $E_{\ge b}$ 再执行未来递归。定理 5 给出它与一次算完相同的数学目标。
>
> **refinement（实现精化）**可以写成：若 $\operatorname{Run}(x,s)$ 是调度 $s$ 下的程序结果，$\Pi$ 删除临时数组、线程号等实现坐标，那么应证明：
> 令 $\operatorname{Legal}(x)$ 表示所有满足第 9 节条件的阶段序列所成的集合，并令：
> $$
> \Pi:\mathsf{ImplTrace}\to\mathsf{SemanticTrace}
> $$
> 是从较丰富程序记录中只取正文语义坐标的函数。这时应证明：
> $$
> \forall s\in\operatorname{Legal}(x),
> \qquad
> \Pi(\operatorname{Run}(x,s))=\mathcal T_x.
> $$

> [!info]- S.10　SettleGraph 的可选对应
> 本块只帮助比较两个独立规格，不是阅读正文的前置知识。SettleGraph 一侧的精确定义仍由其自己的语义文档决定。
>
> 本块中的 Token 是 SettleGraph 给一个外部输入位置使用的标签，不是本文的内部消息或节点事件。
>
> 一个待证明的翻译至少需要逐项给出：
>
> - receiver 到 $v\in V$ 的映射；
> - graph ingress/egress 到 $\mathsf I,\mathsf O$ 的映射；
> - receiver state 到 $S_v$ 的映射；
> - 每 Token 聚合输入到某个 $B_{v,\theta}$ 的映射；
> - AGG-CUSTOM 到保留端口或入边坐标的 $\operatorname{Agg}_v$ 的映射；
> - selection region 到 $\mathcal R_j$ 的映射；
> - active set、SD/BO、NodeCompute 与 Emit 到式 (24)--(28) 的映射；
> - `DATA` 与 `CLOSED` 到实际消息和有效封闭命题的映射。
>
> SettleGraph 对每个 Token、每个 region 等待该 Token 的所有相关边结算；本文允许不同输入位置通过逻辑时间映射落入同一个 $(v,\theta)$ 或 $(j,\theta)$。要证明前者是后者的受限情形，必须给出一种时间编码，使不同 Token 不会发生被禁止的同刻汇合，并比较完整状态、消息、输出端口、候选集合和 active sets。
