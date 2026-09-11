---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-11
tags:
  - tide
  - timed-dag
  - region
  - selector
  - selector-history
  - logical-time
  - mathematics
  - learning-note
---

# 带区域选择的 TimedDAG：从零开始的数学定义

> [!summary] 本文的阅读前提
> 本文只假设读者熟悉集合、函数、自然数、有限求和、最小值和数学归纳法。有向图、逻辑时间、输入端口、消息、时间纤维、区域、候选集合、选择函数、选择历史、封闭下界以及事件图都会在本文中重新定义。
>
> 本文的每一项定义都写在文内，其他文档与讨论均不是阅读前提。标题中的 `region`、`selector` 和完整 `TimedDAG` 规格只是待定义对象的名称；它们分别在第 2.4、5.3、6.5 节获得精确定义。
>
> 正文先给数学对象，再给例子和定理；计算机系统中常用说法的集中解释放在附录 S。删除附录 S 后，正文仍然构成完整的数学规格。

> [!tip] 分四次阅读
> 第一次只读第 1--3 节，目标是能从式 (8) 独立算出一个时间纤维；读到这里就停止。第二次读第 4--7 节，完整手算两个例子。第三次只研究第 8--9 节的封闭下界与阶段化暴露。第四次再读第 10 节以后的事件图、切面与性能分层；它们不是理解主定义的前置。

本文要定义的是一个有限确定性模型。它具有以下能力：

1. 有有限多个外部输入端口，也有有限多个外部输出端口；
2. 每个外部输入位置带有一个自然数时间；
3. 节点沿固定有向边发送值，每条边增加一个正整数时间；
4. 到达同一节点、同一时间的全部外部输入和内部消息被共同处理；
5. 节点集合被划分为若干区域；同一区域中，在同一时间收到至少一个输入的全部节点共同参加一次选择；
6. 在阶段化暴露模型中，只有能够证明这组节点不会再增加时，才可以暴露相应的选择；
7. 每个区域的 selector 可以保存一个显式的跨时间历史状态；
8. 区域不是节点，不接收普通消息，也不发送普通消息；
9. 区域之间不要求构成 DAG。

`Tide` 在本文中只是这条研究线的名称，不是额外的数学对象；本文实际定义的对象是第 1--6 节给出的带区域选择的 TimedDAG 规格。

正文分成两个层次。

- 第 1--7 节先假定一次输入全部给定，定义唯一的完整结果。这是模型本身的含义。
- 第 8--9 节再在固定的 $\mathcal T_x$ 上定义阶段化暴露轨迹，并把“可见、完成、关闭”对应到其中的函数与集合关系。它排列规范记录的坐标，不另行定义计算结果。

这个顺序很重要：必须先知道“正确的完整结果是什么”，才能定义“一个部分暴露何时已经包含足够的规范坐标”。

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

本文还使用以下逻辑记号：

$$
\forall x\in X,\ P(x)
$$

表示集合 $X$ 的每个元素都满足命题 $P$；记号 $\exists x\in X:P(x)$ 表示至少有一个元素满足它。若 $f:X\to Y$ 且 $D\subseteq Y$，定义 $D$ 在 $f$ 下的**逆像**：

$$
f^{-1}(D)=\{x\in X\mid f(x)\in D\}.
$$

逆像是一种集合构造，不要求 $f$ 可逆。例如，后文的 $\rho^{-1}(\{j\})$ 就是所有被 $\rho$ 映到 $j$ 的节点。

### 1.2 带名字的函数坐标

设 $C$ 是有限集合，并且每个 $v\in C$ 都有一个集合 $D_v$。定义：

$$
\prod_{v\in C}D_v
=
\{d\mid d\text{ 是定义在 }C\text{ 上的函数，且 }d(v)\in D_v\}.
$$

因此，$(d_v)_{v\in C}$ 表示“由 $v$ 标记的函数坐标族”，不是一个依赖排列顺序的列表。若 $C=\{a,b\}$，那么 $(d_v)_{v\in C}$ 就是同时规定 $d(a)$ 与 $d(b)$；交换纸面上书写 $a,b$ 的顺序不会改变这个函数。

当 $C=\varnothing$ 时，上式的积集合只含唯一的空函数；本文把这个空函数记为 $()$。

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

有限 DAG 的任一有向路径都不会重复经过节点，否则两次经过之间便给出有向环；所以路径长度至多为 $|V|-1$。

本文还会用二元关系表示不需要独立边身份与边时延的辅助有向图。若 $W$ 是有限集合、$R\subseteq W\times W$，则 $(w_0,\ldots,w_k)$ 称为关系图 $(W,R)$ 的有向路径，当且仅当 $k\ge 1$ 且 $(w_{r-1},w_r)\in R$ 对每个 $1\le r\le k$ 成立；若再有 $w_0=w_k$，它就是一条非空有向闭路。不含这种闭路的关系图也称为 DAG。第 10 节的事件图与区域商图采用这个定义。

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

区域作为节点子集没有自己的入边、出边或节点状态。第 5.3 节会另外为每个 $j\in J$ 定义 selector-history；它不属于任何 $S_v$，也不直接接收或发送原子。$J$ 上目前没有定义任何边。第 10.6 节会为了比较额外构造一张区域商图，但那张商图不参与本模型的消息传递。

## 3. 外部输入记录、内部消息与时间纤维

本节先定义哪些记录可以到达一个节点，再用目标节点与逻辑时间从这些记录中取出一个有限子集。

### 3.1 外部输入记录

先取三个两两不同的形式标签 $\mathrm{ext},\mathrm{msg},\mathrm{out}$。它们只用于区分下述三类有序组。

定义所有可能的外部输入记录所成的集合：

$$
\mathsf{Ext}
=
\{(\mathrm{ext},i,k,y)\mid
i\in\mathsf I,\ k\in[L_i],\ y\in P\}.
$$

这里 $\mathrm{ext}$ 表示外部输入记录；下面的 $\mathrm{msg}$ 与 $\mathrm{out}$ 分别表示内部消息与输出记录。
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

## 5. 区域候选集合、选择函数、选择历史与状态采用

本节在第 2.4 节的节点划分上定义共同选择。本次选择只读取同一逻辑时间的候选描述量，但 selector-history 会连接同一区域在不同时间的选择。

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

### 5.3 带历史的选择函数

对每个 $j\in J$，给定非空集合 $Y_j$ 和元素：

$$
y_j^{\mathrm{init}}\in Y_j.
$$

$Y_j$ 称为区域 $j$ 的**选择历史状态集合**，$y_j^{\mathrm{init}}$ 是初始选择历史。

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
\operatorname{SelStep}_{j,C}:
Y_j\times\mathbb N\times\prod_{v\in C}D_v
\to\mathsf{Allowed}_{j,C}\times Y_j.
\tag{14}
$$

对空候选集合，规定：

$$
\operatorname{SelStep}_{j,\varnothing}(y,\theta,())
=(\varnothing,y).
$$

若某个时间的完整候选集合是 $C$，选择以前的历史是 $y\in Y_j$，候选描述量族是 $(d_v)_{v\in C}$，定义：

$$
(A,y')
=
\operatorname{SelStep}_{j,C}
\left(y,\theta,(d_v)_{v\in C}\right).
\tag{15}
$$

这里 $y'$ 是本次选择以后的历史。式 (15) 的两个输出属于同一个确定函数值，因此 $y'$ 可以记录 $A$、候选集合、描述量或由它们算出的数值摘要。它不能读取尚未应用的 $\operatorname{Full}_v$ 输出，因为这些输出不在式 (14) 的定义域中。

从现在起，式 (14) 的系统别名是 **selector step**，简称 selector；$y$ 的系统别名是 **selector-history**。式 (15) 的集合 $A$ 称为 active set，其中的元素称为 active nodes。由值域定义自动得到：

$$
A\subseteq C,
\qquad
|A|\le K_j.
$$

式 (14) 没有规定必须按最大分数选择。最大值、Top-$K$、固定查表或任何别的确定性规则都可以成为一个具体的 $\operatorname{SelStep}_{j,C}$。若规则可能遇到相等描述量，必须把确定的平局规则写进函数；不得让观察顺序代替函数定义。

若 $Y_j$ 是单点集，就精确退化为不保存历史的 selector。若取 $Y_j=\mathbb N^{\mathcal R_j}$，其元素可以记录区域内各节点过去被选择的次数；取实数坐标族还可以记录确定性移动平均。这里的“概率”只能是状态中保存的数值；若要让选择本身随机，还必须另给概率空间和随机变量，当前确定性规格没有暗中加入它们。

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
\begin{aligned}
(q,B)&\longrightarrow(h,\widetilde q,d),\\
(y,d)&\longrightarrow(A,y'),\\
(A,q,\widetilde q)&\longrightarrow q',\\
(q',\theta,h)&\longrightarrow\operatorname{Full}.
\end{aligned}
\tag{18}
$$

式 (18) 是函数自变量之间的依赖，不是对处理器指令或现实耗时的描述。一个实现可以提前求出某个纯函数值，但不能让后续函数作用读取尚未由式 (15) 或 (17) 确定的状态，也不能在式 (15) 以前发布只允许 active 节点产生的消息。特别地，本次 $\operatorname{Full}$ 不参与本次 selector-history 更新。

区域选择作用只确定 $(A,y')$。普通消息和外部输出仍始终由 $v\in A$ 的节点按照式 (12) 产生。

## 6. 完整输入下的直接语义

前五节只给出了固定数据与局部函数。本节把它们组合成一次输入 $x$ 上的唯一完整计算。

### 6.1 一个有限逻辑时间上界

允许长度为零的路径停留在某个 $\gamma(i)$，并规定它的总时延为 $0$。对非空路径 $\zeta=(a_1,\ldots,a_k)$ 定义：

$$
\Delta(\zeta)=\sum_{\ell=1}^{k}\delta(a_\ell).
$$

因为有向路径长度至多为 $|V|-1$，而边集有限，所以从输入目标节点 $\gamma(i)$ 出发的路径总数有限。定义：

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

对每个区域，同时定义递归开始时的选择历史：

$$
y_j^0=y_j^{\mathrm{init}}.
$$

以后，$y_j^\theta$ 表示处理时间 $\theta$ 的区域选择以前的历史；上标是逻辑时间切面，不是已经发生的选择次数。

令 $M_{<0}=\varnothing$。依次对：

$$
\theta=0,1,\ldots,\Theta_{\max}
$$

执行下列纯数学递归。这里的“递归”是自然数上的递归定义：先给出时间 $0$ 所需的初值，再假定所有更小时间的量已经定义，由已给函数唯一写出当前时间的量。它不是程序中的递归调用，也不依赖调用栈或 $\lambda$ 演算。式 (29) 将保证右边只读取更小逻辑时间产生的消息，因此这个定义不会循环地要求一个尚未定义的当前值。

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
(\mathcal A_{j,\theta},y_j^{\theta+1})
=
\operatorname{SelStep}_{j,\mathcal C_{j,\theta}}
\left(
y_j^\theta,
\theta,
(d_{v,\theta})_{v\in\mathcal C_{j,\theta}}
\right).
\tag{24}
$$

当 $\mathcal C_{j,\theta}=\varnothing$ 时，第 5.3 节的规定给出：

$$
\mathcal A_{j,\theta}=\varnothing,
\qquad
y_j^{\theta+1}=y_j^\theta.
$$

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

这就同时完成节点状态与选择历史从时间 $\theta$ 到 $\theta+1$ 的递归。

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

其中的元素 $(j,\theta)$ 称为输入 $x$ 的一个**区域选择事件**。它表示把区域 $j$ 在时间 $\theta$ 的旧选择历史与整个候选描述量族一次交给式 (24)，并共同确定 active set 与下一选择历史。当候选集合为空时，式 (24) 仍规定 active set 为空、选择历史不变，但本文不把这个恒等位置收入 $\mathcal E_x^{\mathrm{sel}}$。

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

定义本次计算产生的全部内部消息与外部输出记录：

$$
M^*=\bigcup_{\theta=0}^{\Theta_{\max}}M_\theta,
\qquad
Z^*=\bigcup_{\theta=0}^{\Theta_{\max}}Z_\theta.
\tag{30}
$$

> [!theorem] 定理 1：完整计算存在、有限且唯一
> 固定第 1--5 节的全部集合、函数与参数，并给定式 (3) 的输入 $x$。则第 6.3 节唯一确定：
>
> - 每个完整时间纤维 $B_{v,\theta}$；
> - 每个候选集合 $\mathcal C_{j,\theta}$；
> - 每个 active set $\mathcal A_{j,\theta}$；
> - 每个候选节点的 $h_{v,\theta},\widetilde q_{v,\theta},d_{v,\theta}$；
> - 每个区域的 selector-history 序列；
> - 节点事件集合 $\mathcal E_x^{\mathrm{node}}$ 与区域选择事件集合 $\mathcal E_x^{\mathrm{sel}}$；
> - 每个节点的状态序列；
> - 有限内部消息集合 $M^*$；
> - 有限多端口外部输出集合 $Z^*$。

**证明。** 对 $\theta$ 作归纳。

在 $\theta=0$ 时，$M_{<0}=\varnothing$，所以式 (21) 只由已给的 $E_x$ 唯一确定。第 4--5 节给定的 $\operatorname{Agg}$、$\operatorname{Upd}$、三个 $\operatorname{Read}$、$\operatorname{SelStep}$ 与 $\operatorname{Full}$ 都是全函数；已知 $y_j^0$ 后，式 (24) 还同时唯一确定 $\mathcal A_{j,0}$ 与 $y_j^1$。因而按式 (22)--(28) 依次求值会给出唯一结果。

假设所有小于 $\theta$ 的结果已经唯一确定，则 $M_{<\theta}$ 唯一。式 (21) 因而唯一；随后所有步骤仍是已给函数的求值，所以时间 $\theta$ 的结果唯一。自然数归纳法给出整个递归的唯一性。

还需证明递归不会产生到达时间超出式 (19) 的消息。任取节点事件 $(v,\theta)$，它所对应的 $B_{v,\theta}$ 至少含有一个到达原子 $z$。若 $z$ 是来自输入位置 $(i,k)$ 的外部输入记录，则 $v=\gamma(i)$ 且 $\theta=\iota_i(k)$。若 $z$ 是内部消息，则它来自某条终点为 $v$ 的边；沿这条消息回到产生它的节点事件，并继续向前追溯。每追溯一条边，节点在固定图中向上游移动一次。由于固定节点图无环，经过有限条边后必定到达某个外部输入记录。因此，每个节点事件的逻辑时间都可以写成：

$$
\iota_i(k)+\Delta(\zeta),
$$

其中 $\zeta$ 是从 $\gamma(i)$ 出发的一条有向路径。它不大于 $\Theta_{\max}$。若这个节点事件沿出边 $a$ 产生消息，就把 $a$ 接到 $\zeta$ 后面；所得仍是从 $\gamma(i)$ 出发的路径，所以这条新消息的到达时间也不大于 $\Theta_{\max}$。固定时间上界、有限节点、有限区域、有限边和有限端口共同推出两类事件集合、两类状态坐标族、消息集合和输出记录集合均有限。$\square$

最终节点状态和最终选择历史分别是：

$$
(q_v^{\Theta_{\max}+1})_{v\in V},
\qquad
(y_j^{\Theta_{\max}+1})_{j\in J}.
$$

把完整计算记录明确定义为：

$$
\mathcal T_x
=
\left(
(B_{v,\theta})_{\substack{v\in V\\\theta\in[0,\Theta_{\max}+1)}},
(h_{v,\theta},\widetilde q_{v,\theta},d_{v,\theta})_
{\substack{j\in J,\ \theta\in[0,\Theta_{\max}+1)\\
v\in\mathcal C_{j,\theta}}},
(\mathcal C_{j,\theta},\mathcal A_{j,\theta})_
{\substack{j\in J\\\theta\in[0,\Theta_{\max}+1)}},
(q_v^\theta)_
{\substack{v\in V\\\theta\in[0,\Theta_{\max}+2)}},
(y_j^\theta)_
{\substack{j\in J\\\theta\in[0,\Theta_{\max}+2)}},
M^*,Z^*,
(f^A_{v,\theta},f^O_{v,\theta})_
{\substack{j\in J,\ \theta\in[0,\Theta_{\max}+1)\\
v\in\mathcal A_{j,\theta}}}
\right),
$$

其中时间纤维、本地量、选择和逐坐标输出函数值的时间坐标满足 $0\le\theta\le\Theta_{\max}$，两类状态还包含递归结束后的 $\theta=\Theta_{\max}+1$。称 $\mathcal T_x$ 为输入 $x$ 的完整计算记录。

本文把第 1--5 节的数据以及第 6 节所定义的直接语义合称为一个**带区域选择的 TimedDAG 规格**。

### 6.6 多输入、多输出

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

取 $J=\{0,1,2\}$，并定义：

$$
\rho(s_0)=0,
\qquad
\rho(s_1)=1,
\qquad
\rho(a)=\rho(b)=2.
$$

于是 $\rho$ 是满射，区域划分为：

$$
\rho^{-1}(\{0\})=\mathcal R_0=\{s_0\},
\qquad
\rho^{-1}(\{1\})=\mathcal R_1=\{s_1\},
\qquad
\rho^{-1}(\{2\})=\mathcal R_2=\{a,b\}.
$$

从输入目标节点出发的最长路径是 $s_0\to a$，总时延为 $5$。因此：

$$
\Delta_{\max}=5,
\qquad
\Theta_{\max}=\max\{0,1\}+5=6.
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

本例先令每个 $Y_j=\{*\}$、$y_j^{\mathrm{init}}=*$；每个 selector step 的第二个输出仍为 $*$。因此，本例的选择历史不携带额外信息。

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

至此，式 (30) 与最终状态分别给出：

$$
M^*=\{m_0,m_1\},
\qquad
Z^*=\{(\mathrm{out},5,o_b,7)\},
$$

$$
q_v^7=*\quad(v\in V),
\qquad
y_j^7=*\quad(j\in J).
$$

在 $v\in V$、$\theta\in[0,7)$ 的范围内，非空完整时间纤维恰好是本节已经列出的 $B_{s_0,0},B_{s_1,1},B_{a,5},B_{b,5}$；其余 $B_{v,\theta}$ 全为空。相应地，除 $M_0=\{m_0\},M_1=\{m_1\}$ 与上述 $Z_5$ 外，其余 $M_\theta,Z_\theta$ 都为空。

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

本例取 $Y_j=\{*\}$，使 selector-history 不影响下面的比较。

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

### 7.7 一个会影响未来选择的历史

只考察区域 $\mathcal R_j=\{a,b\}$，取：

$$
Y_j=\mathbb N^{\{a,b\}},
\qquad
y_j^0(a)=y_j^0(b)=0,
\qquad K_j=1.
$$

定义 selector step 在候选非空时选择历史计数最小的候选，计数相等时固定令 $a$ 排在 $b$ 前；随后只把被选节点的计数加一。假设时间 $0$ 与 $2$ 的候选集合都是 $\{a,b\}$，时间 $1$ 的候选集合为空。于是：

$$
\mathcal A_{j,0}=\{a\},
\qquad
(y_j^1(a),y_j^1(b))=(1,0),
$$

$$
y_j^2=y_j^1,
$$

$$
\mathcal A_{j,2}=\{b\},
\qquad
(y_j^3(a),y_j^3(b))=(1,1).
$$

时间 $2$ 的描述量即使与时间 $0$ 相同，旧历史不同也会改变 active set。这里的 $y_j^\theta$ 是递归状态，不是把全部过去事件原样保存的一份日志。

## 8. 规范记录的阶段化暴露、封闭下界与候选集合关闭

第 6 节直接使用完整的 $E_x$ 与递归产生的 $M^*$。本节不再定义另一份计算结果，而是在已经固定的完整记录 $\mathcal T_x$ 上增加一项数学数据：各记录进入一条递增子集链的阶段。数学中常把这种递增子集族称为过滤（filtration）；本文称它为 $\mathcal T_x$ 的**阶段化暴露模型**。它只记录规范坐标何时进入子集，不从部分输入重新定义另一份语义。附录 S 才把“进入当前子集”翻译成系统语言中的可见或公开。

本节的 $H_n$ 是已经进入阶段 $n$ 的**内部消息集合**；它与式 (14) 的 selector-history 状态 $y_j^\theta$ 是两种不同对象。

### 8.1 阶段编号与阶段秩

定义：

$$
\overline{\mathbb N}=\mathbb N\cup\{\infty\},
$$

保留 $\mathbb N$ 上原有的次序，规定每个 $b\in\mathbb N$ 都满足 $b<\infty$，并规定 $\infty\le\infty$。因而每个 $c\in\overline{\mathbb N}$ 都满足 $c\le\infty$。同时规定 $\min\varnothing=\infty$。这里的 $\infty$ 不是逻辑时间，只表示一个元素没有进入所研究的阶段序列。

取两个函数，称为外部记录与内部消息的**阶段秩**：

$$
\alpha_E:E_x\to\overline{\mathbb N},
\qquad
\alpha_M:M^*\to\overline{\mathbb N}.
$$

对每个阶段编号 $n\in\mathbb N$，定义：

$$
E_n
=\{e\in E_x\mid\alpha_E(e)\le n\},
\qquad
H_n
=\{m\in M^*\mid\alpha_M(m)\le n\}.
\tag{31}
$$

由式 (31) 立即得到：

$$
E_n\subseteq E_{n+1},
\qquad
H_n\subseteq H_{n+1}.
$$

反之，任意这样的递增消息链都由 $\alpha_M(m)=\min\{n\mid m\in H_n\}$ 唯一表示。

$\alpha_E$ 与 $\alpha_M$ 是在 $x$ 和 $\mathcal T_x$ 之外另行选择的数据。因此 $H_n$ 不是由 $E_n$ 决定的“可计算消息闭包”；它只是式 (31) 给出的 $M^*$ 子集。

若 $\alpha_E(e)=\infty$ 或 $\alpha_M(m)=\infty$，相应元素不会进入任何有限阶段。称这条记录链**穷尽**完整记录，当且仅当：

$$
\bigcup_{n\in\mathbb N}E_n=E_x,
\qquad
\bigcup_{n\in\mathbb N}H_n=M^*.
$$

这等价于所有阶段秩都有限；由于两个集合有限，也等价于某个 $N$ 满足 $E_N=E_x$ 且 $H_N=M^*$。第 8 节的关闭结论不要求整条链穷尽。

$n$ 只给阶段排序，不传入任何节点函数；它与逻辑时间 $\theta$ 无关。多个元素可以具有相同阶段秩，$\alpha_M$ 也不必随消息的逻辑到达时间递增。

### 8.2 阶段时间纤维

定义阶段 $n$ 的时间纤维：

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

因为到达时间为 $\theta$ 的消息都在小于 $\theta$ 的时间发送，已经属于式 (21) 使用的 $M_{<\theta}$。因此，$B^{(n)}_{v,\theta}$ 就是完整记录中阶段秩不大于 $n$ 的 $(v,\theta)$ 纤维。

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

为了把这个全称命题改写成集合覆盖关系，对 $i\in\mathsf I$、$a\in A$ 与 $b\in\overline{\mathbb N}$ 定义：

$$
E_x(i,<b)
=\{e\in E_x\mid
\operatorname{inport}(e)=i,
\ \operatorname{time}(e)<b\},
$$

$$
M^*(a,<b)
=\{m\in M^*\mid
\operatorname{edge}(m)=a,
\ \operatorname{time}(m)<b\}.
$$

于是式 (33) 等价于：

$$
E_x\bigl(i,<\sigma_n^{\mathrm{in}}(i)\bigr)
\subseteq E_n
\quad(i\in\mathsf I),
$$

$$
M^*\bigl(a,<\sigma_n^A(a)\bigr)
\subseteq H_n
\quad(a\in A).
$$

所以 $\sigma_n^A(a)=b$ 只断言：边 $a$ 上到达时间严格小于 $b$ 的全部实际消息都属于 $H_n$。$|H_n|$ 不出现在条件中；一个较早消息不属于 $H_n$，不能由许多个较晚消息属于 $H_n$ 来补偿。

若 $\sigma_n^A(a)=\infty$，上述包含关系要求边 $a$ 上的全部实际消息都属于 $H_n$。

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

空集的最小值按第 8.1 节取 $\infty$。任意不大于相应 $\widehat\sigma$ 的数都是有效下界；大于它的数无效。这个公式只刻画“有效”一词，不给出仅由当前阶段数据构造下界的方法。

式 (33) 借助完整结果 $M^*$ 判断一个下界是否为真；它是判定有效性的条件，不是一条只由当前阶段数据构造下界的规则。可用证据例如外部输入源给出的完整性条件，或第 9.6 节由上游完成推出的条件；无论采用什么证据，它都必须推出式 (33) 的全称命题，不能只凭当前集合看起来没有新元素便任意填写一个较大的数。

合法的阶段化暴露链还要求这些下界不减小：

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

若节点没有入边也没有输入端口，括号内是空集，按第 8.1 节规定有 $\lambda_n(v)=\infty$。这种节点的所有完整时间纤维本来就为空。

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

严格不等式不能换成 $\lambda_n(v)\ge\theta$。下界等于 $\theta$ 时，式 (33) 仍允许某个不属于 $E_n\cup H_n$ 的记录恰好具有时间 $\theta$。

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

定理同时处理“有一个消息的节点”和“完整时间纤维为空的节点”。$B^{(n)}_{c,\theta}=\varnothing$ 并不能证明 $c$ 不在完整候选集合；还需要 $\lambda_n(c)>\theta$。

### 8.7 用第 7 节例子检查严格不等式

设某个阶段满足 $m_0\in H_n$ 且 $m_1\notin H_n$。若边 $e_1$ 的有效下界是：

$$
\sigma_n^A(e_1)=5,
$$

这是可能的，因为 $\operatorname{time}(m_1)=5$。此时：

$$
\lambda_n(\mathcal R_2)\le5,
$$

所以不能对时间 $5$ 使用定理 3；当前候选集合 $\{a\}$ 不是完整候选集合。

若在阶段 $n'$，两条边上的全部实际消息都已属于 $H_{n'}$，则可以有效地令：

$$
\sigma_{n'}^A(e_0)=\sigma_{n'}^A(e_1)=\infty.
$$

于是 $\lambda_{n'}(\mathcal R_2)=\infty>5$，定理 3 才证明候选集合等于 $\{a,b\}$。

### 8.8 输入完整、节点状态与选择历史就绪是三个命题

定理 3 只证明时间 $\theta$ 的候选节点和每个候选节点的完整纤维已经确定。若式 (23) 使用 $q_v^\theta$ 或 $\widetilde q_{v,\theta}$，还必须先知道 $q_v^\theta$。

任取一个节点事件子集：

$$
\mathsf{Done}\subseteq\mathcal E_x^{\mathrm{node}},
$$

对 $v\in V$ 与 $\theta\in\mathbb N$ 定义状态前驱集合：

$$
\operatorname{StatePred}(v,\theta)
=
\{(v,r)\in\mathcal E_x^{\mathrm{node}}\mid r<\theta\}.
$$

定义：节点 $v$ 在时间 $\theta$ 的旧状态关于 $\mathsf{Done}$ **就绪**，当且仅当：

$$
\operatorname{StatePred}(v,\theta)
\subseteq\mathsf{Done}.
$$

$\operatorname{StatePred}(v,\theta)$ 索引的式 (25) 按 $r$ 递增组成第 6 节状态序列的完整前缀；上述包含关系成立时，该前缀已经到达唯一的 $q_v^\theta$。

再任取一个区域选择事件子集：

$$
\mathsf{Selected}\subseteq\mathcal E_x^{\mathrm{sel}}.
$$

对区域 $j$ 定义选择历史前驱集合：

$$
\operatorname{HistPred}(j,\theta)
=
\{(j,r)\in\mathcal E_x^{\mathrm{sel}}\mid r<\theta\}.
$$

定义区域 $j$ 在时间 $\theta$ 的旧选择历史关于 $\mathsf{Selected}$ **就绪**，当且仅当：

$$
\operatorname{HistPred}(j,\theta)
\subseteq\mathsf{Selected}.
$$

候选集合为空的时间只应用恒等规则，不产生区域选择事件；因此，上述集合恰好索引所有真正改变或读取历史的较早 selector step。包含关系成立时，这些步骤按时间组成唯一的 $y_j^\theta$。

所以，对区域选择事件 $(j,\theta)\in\mathcal E_x^{\mathrm{sel}}$，一个统一而保守的求值条件是：

1. $\lambda_n(\mathcal R_j)>\theta$；
2. 每个 $v\in\mathcal C_{j,\theta}$ 的旧状态关于当前已完成节点事件集合 $\mathsf{Done}$ 就绪；
3. $\operatorname{HistPred}(j,\theta)\subseteq\mathsf{Selected}$；
4. 每个候选描述量已经按式 (23) 求出；
5. $(j,\theta)$ 尚未应用过式 (24)。

当 $\tau_j=0$ 时，描述量本身不读取节点状态，可以先求描述量，再等待节点状态与 selector-history 就绪后选择、采用状态和执行完整函数。这种提前求值不会改变式 (21)--(30) 定义的结果。

## 9. 规范记录的合法阶段化暴露

第 6 节按逻辑时间递增定义唯一结果。本节只研究这份规范记录的坐标可以按哪些阶段次序暴露；它不是一套从未知结果独立生成 $\mathcal T_x$ 的解释器语义。程序是否正确地算出这些坐标，还须另外给出附录 S.9 所述的精化投影。

### 9.1 阶段化暴露轨迹

再取三个阶段秩函数，并对 $n\in\mathbb N$ 定义相应子集：

$$
\begin{aligned}
\alpha_P&:\mathcal E_x^{\mathrm{node}}\to\overline{\mathbb N},
&\mathsf{Prepared}_n
&=\{e\in\mathcal E_x^{\mathrm{node}}\mid\alpha_P(e)\le n\},\\
\alpha_S&:\mathcal E_x^{\mathrm{sel}}\to\overline{\mathbb N},
&\mathsf{Selected}_n
&=\{s\in\mathcal E_x^{\mathrm{sel}}\mid\alpha_S(s)\le n\},\\
\alpha_C&:\mathcal E_x^{\mathrm{node}}\to\overline{\mathbb N},
&\mathsf{Completed}_n
&=\{e\in\mathcal E_x^{\mathrm{node}}\mid\alpha_C(e)\le n\}.
\end{aligned}
\tag{39}
$$

三个集合分别索引已经确定节点本地量、已经应用式 (24) 并同时确定 active set 与下一选择历史，以及已经应用式 (25)--(28) 中相应坐标的事件。“prepared”“selected”“completed”在数学上分别就是式 (39) 的成员关系；阶段秩不是事件固有的逻辑时间。

为了使轨迹中的函数值也形式确定，对每个节点事件定义规范准备标签：

$$
\operatorname{Lab}_P(v,\theta)
=
(B_{v,\theta},q_v^\theta,h_{v,\theta},
\widetilde q_{v,\theta},d_{v,\theta}),
$$

对每个区域选择事件定义规范选择标签：

$$
\operatorname{Lab}_S(j,\theta)
=
(\mathcal C_{j,\theta},y_j^\theta,
(d_{v,\theta})_{v\in\mathcal C_{j,\theta}},
\mathcal A_{j,\theta},y_j^{\theta+1}),
$$

并对每个节点事件定义规范完成标签：

$$
\operatorname{Lab}_C(v,\theta)
=
\begin{cases}
(q_v^{\theta+1},(f^A_{v,\theta},f^O_{v,\theta})),
&v\in\mathcal A_{\rho(v),\theta},\\
(q_v^{\theta+1},()),
&v\notin\mathcal A_{\rho(v),\theta}.
\end{cases}
$$

阶段 $n$ 的三类函数值分别是这些标签函数在 $\mathsf{Prepared}_n,\mathsf{Selected}_n,\mathsf{Completed}_n$ 上的限制。它们不是另行任取的坐标：第 9.2--9.3 节只约束何时可以扩大限制；事件首次进入时，新增值就是相应的规范标签，而关闭与前驱条件保证其全部自变量已经确定。完成标签中的 $f^A,f^O$ 再按式 (27)--(28) 唯一派生消息与输出记录。

第 8 节的记录链、下界函数、式 (39) 的三条事件链及上述标签限制合在一起，称为一条**阶段化暴露轨迹**。下面先补上内部消息与其源事件之间的约束，再给出“合法”的完整条件。

每条实际消息都有唯一的源节点事件。定义：

$$
g:M^*\to\mathcal E_x^{\mathrm{node}},
\qquad
g(m)=
\bigl(\operatorname{src}(\operatorname{edge}(m)),
\operatorname{send}(m)\bigr).
$$

由式 (27)，$g(m)$ 确实属于节点事件集合。定义源事件已完成的消息集合，并要求：

$$
M_n^{\mathrm{src}}
=g^{-1}(\mathsf{Completed}_n),
\qquad
H_n\subseteq M_n^{\mathrm{src}}
\qquad(n\in\mathbb N).
\tag{40}
$$

每条实际输出记录也有唯一的源节点事件。定义：

$$
g_Z:Z^*\to\mathcal E_x^{\mathrm{node}},
\qquad
g_Z(z)=
(\varepsilon(\operatorname{outport}(z)),\operatorname{outtime}(z)),
$$

以及完成标签已经确定的输出集合：

$$
Z_n^{\mathrm{comp}}
=g_Z^{-1}(\mathsf{Completed}_n).
$$

因此 $H_n\subseteq M_n^{\mathrm{src}}\subseteq M^*\subseteq\mathsf{Msg}$。等价地，对每个 $m\in M^*$ 都有 $\alpha_C(g(m))\le\alpha_M(m)$。这里的 $\mathsf{Completed}_n$ 只表示源事件的完成标签已经确定；一般模型允许该事件产生的消息稍后才进入 $H_n$。若研究“完成即进入”的特例，才另外增加 $H_n=M_n^{\mathrm{src}}$。输出没有另设延迟进入链，故由 $Z_n^{\mathrm{comp}}$ 直接记录。

一条阶段化暴露轨迹**合法**，当且仅当对每个阶段满足：式 (33) 的有效性、式 (34) 的单调性、式 (40) 的源事件约束、第 9.2 节的准备与选择首次进入条件，以及第 9.3 节的完成首次进入条件。第 9.5 节是这些条件的推论；第 9.6 节只给出构造某些有效边下界的一种充分方法，不是额外的合法性公理。本文取 $\mathsf{Prepared}_0=\mathsf{Selected}_0=\mathsf{Completed}_0=\varnothing$。

称合法暴露轨迹**完整**，当且仅当存在 $N\in\mathbb N$ 使：

$$
E_N=E_x,
\quad H_N=M^*,
\quad
\mathsf{Prepared}_N=\mathsf{Completed}_N
=\mathcal E_x^{\mathrm{node}},
\quad
\mathsf{Selected}_N=\mathcal E_x^{\mathrm{sel}}.
$$

所以 $H_n=\varnothing$ 可以是合法暴露轨迹的中间截面，却不能在 $M^*\ne\varnothing$ 时成为完整轨迹的最终截面。

在第 8.8 节的状态就绪定义中，以下取 $\mathsf{Done}=\mathsf{Completed}_n$。

### 9.2 合法准备与合法选择

为避免“已经”一词隐藏先后关系，定义阶段 $n$ 到 $n+1$ 的首次进入集合：

$$
\Delta\mathsf{Prepared}_n
=\mathsf{Prepared}_{n+1}\setminus\mathsf{Prepared}_n,
$$

并类似定义 $\Delta\mathsf{Selected}_n$ 与 $\Delta\mathsf{Completed}_n$。以下前提都在阶段 $n$ 的集合上检查，因此同一步新增事件不能互为这些前提。

节点事件 $(v,\theta)$ 只有满足下列条件才可属于 $\Delta\mathsf{Prepared}_n$：

1. $\lambda_n(v)>\theta$；
2. $\operatorname{StatePred}(v,\theta)\subseteq\mathsf{Completed}_n$。

进入时，以 $B^{(n)}_{v,\theta}$ 和 $q_v^\theta$ 求出 $h_{v,\theta},\widetilde q_{v,\theta},d_{v,\theta}$。引理 2 保证这些值等于第 6 节的相应坐标。

区域选择事件 $(j,\theta)$ 只有满足下列条件才可属于 $\Delta\mathsf{Selected}_n$：

1. $\lambda_n(\mathcal R_j)>\theta$；
2. 每个 $v\in\mathcal C_{j,\theta}$ 都满足 $(v,\theta)\in\mathsf{Prepared}_n$；
3. $\operatorname{HistPred}(j,\theta)\subseteq\mathsf{Selected}_n$。

合法选择必须把完整函数族：

$$
(d_{v,\theta})_{v\in\mathcal C_{j,\theta}}
$$

与旧选择历史 $y_j^\theta$ 一次交给式 (24)。不能只对已经较早准备好的真子集作出不可撤销选择，也不能跳过一个尚未应用的较早 selector step。

若 $\mathcal C_{j,\theta}=\varnothing$，则 $(j,\theta)\notin\mathcal E_x^{\mathrm{sel}}$。此时式 (24) 已按定义令 active set 为空并保持历史，不需要执行选择作用，也不在 $\mathsf{Selected}_n$ 中留下记录。

### 9.3 合法节点完成

若 $v\in\mathcal C_{j,\theta}$，则 $(v,\theta)$ 只有满足下列条件才可属于 $\Delta\mathsf{Completed}_n$：

1. $(j,\theta)\in\mathsf{Selected}_n$；
2. $\operatorname{StatePred}(v,\theta)\subseteq\mathsf{Completed}_n$。

合法完成使用该次选择确定的 $\mathcal A_{j,\theta}$，并按式 (25) 唯一确定状态。只有 active 节点应用式 (26)，并且只把式 (27)--(28) 中非 $\bot$ 的坐标加入实际消息或输出集合。事件进入 $\mathsf{Completed}_{n+1}$ 时，其消息与输出分别属于 $M_{n+1}^{\mathrm{src}}$ 与 $Z_{n+1}^{\mathrm{comp}}$；这些消息可以同时进入 $H_{n+1}$，也可以稍后进入，但式 (40) 禁止它们更早进入。

同一区域中的不同节点事件在选择以后可以具有不同完成阶段，因为它们修改的是不同状态坐标 $S_v$。但同一节点的节点事件必须按逻辑时间递增完成。

### 9.4 纯函数可以提前求值，规范坐标不能提前暴露

固定 $v\in\mathcal C_{j,\theta}$。若 $B_{v,\theta}$ 已经由引理 2 确定，可以先求 $h_{v,\theta}$。若旧状态也已经确定，还可以先求 $\widetilde q_{v,\theta}$ 和三个描述量。若旧选择历史尚未就绪，则仍不能提前确定式 (24) 的任一输出。

这些值可以保存在临时变量中，但在区域选择以前不得：

- 让更大逻辑时间的节点事件读取 $\widetilde q_{v,\theta}$；
- 令 $(v,\theta)$ 属于 $\mathsf{Completed}_n$；
- 令任何满足 $g(m)=(v,\theta)$ 的 $m\in M^*$ 属于 $H_n$；
- 令任何满足 $g_Z(z)=(v,\theta)$ 的 $z\in Z^*$ 属于 $Z_n^{\mathrm{comp}}$。

后三项分别违反第 9.3 节、式 (40) 或 $Z_n^{\mathrm{comp}}$ 的逆像定义。提前算出的临时值不是阶段化暴露轨迹中的规范完成标签。

### 9.5 有效下界约束消息阶段秩

若有效值 $\sigma_n^A(a)=b$，则式 (33) 要求每个满足：

$$
\operatorname{edge}(m)=a,
\qquad
\operatorname{time}(m)<b
$$

的消息都属于 $H_n$，即 $\alpha_M(m)\le n$。所以这样的消息不可能在更晚阶段首次进入 $H$。

阶段秩不必随逻辑到达时间递增；它只受已经给出的有效下界约束。

### 9.6 边下界怎样由上游完成推出

对 $v\in V$ 与 $b\in\mathbb N$ 定义谓词：

$$
\operatorname{DoneTo}_n(v,b)
\Longleftrightarrow
\left(
\lambda_n(v)\ge b
\land
\operatorname{StatePred}(v,b)
\subseteq\mathsf{Completed}_n
\right).
\tag{41}
$$

系统语言称 $\operatorname{DoneTo}_n(v,b)$ 为“阶段 $n$ 节点 $v$ 已完成到 $b$”。第一项覆盖时间小于 $b$ 的输入，第二项覆盖相应的全部节点事件；这两个条件不能互相替代。

若 $\operatorname{DoneTo}_n(v,b)$ 成立，则尚未属于 $\mathsf{Completed}_n$ 的任何节点事件 $(v,\theta)$ 都满足 $\theta\ge b$。对任意 $a\in\operatorname{Out}(v)$，这些事件对应消息的到达时间不小于：

$$
b+\delta(a).
$$

如果还满足：

$$
M_n^{\mathrm{src}}
\cap M^*\bigl(a,<b+\delta(a)\bigr)
\subseteq H_n,
$$

那么：

$$
\sigma_n^A(a)=b+\delta(a)
\tag{42}
$$

是一个有效下界。

事实上，任取 $m\in M^*(a,<b+\delta(a))$，都有 $\operatorname{send}(m)<b$，故 $g(m)\in\operatorname{StatePred}(v,b)\subseteq\mathsf{Completed}_n$。于是 $m$ 属于上述交集，并由附加条件属于 $H_n$；再用式 (33) 即得结论。

式 (42) 使用的是谓词 (41) 和两个有限集合的包含关系，而不是“当前队列为空”。附录 S 把前者翻译为上游完成，把后者翻译为较早消息均已可见。

### 9.7 一条顺序参考轨迹

> [!proposition] 命题 4：完整合法顺序参考轨迹存在
> 对任意固定规格与输入 $x$，至少存在一条完整合法阶段化暴露轨迹。

**证明。** 令全部外部记录从阶段 $0$ 起属于 $E_n$。从空的三类事件集合与 $H_0=\varnothing$ 开始，依次处理 $\theta=0,1,\ldots,\Theta_{\max}$：先在一次阶段转移中准备时间 $\theta$ 的全部节点事件，再在下一次转移中选择时间 $\theta$ 的全部区域选择事件，最后完成时间 $\theta$ 的全部节点事件。每次完成转移后，令 $H_{n+1}=M_{n+1}^{\mathrm{src}}$；在其余转移中也保持 $H_n=M_n^{\mathrm{src}}$。每个阶段都取第 8.3 节由当前 $E_n,H_n$ 定义的最大有效下界 $\widehat\sigma_n^{\mathrm{in}},\widehat\sigma_n^A$。

在准备时间 $\theta$ 以前，所有更小逻辑时间的节点事件都已完成。若一条尚未属于 $H_n$ 的消息满足 $\operatorname{time}(m)\le\theta$，则由正时延有 $\operatorname{send}(m)<\theta$；其源事件已经完成，又因 $H_n=M_n^{\mathrm{src}}$，得到 $m\in H_n$，矛盾。因此每条入边的最大有效下界都严格大于 $\theta$；外部记录已经全部属于 $E_n$，所以输入端口下界为 $\infty$。于是每个节点 $v$ 都满足 $\lambda_n(v)>\theta$，待准备事件的状态前驱也均已完成。

下一次转移时，本时间的准备事件都已进入，所有更早选择事件也已进入；再下一次转移时，本时间的选择事件均已进入。因此第 9.2--9.3 节的条件逐项成立。$E_n,H_n$ 只增不减，故最大有效下界满足式 (34)，而 $H_n=M_n^{\mathrm{src}}$ 满足式 (40)。各次首次进入暴露第 6.3 节的规范标签。最后在某个阶段 $N$，全部事件均进入且 $H_N=M^*$。对所有 $n\ge N$，令全部集合、标签限制与下界保持阶段 $N$ 的值，便得到定义在整个 $\mathbb N$ 上的完整轨迹。$\square$

命题 4 只证明合法性条件并非空设；它没有声称这种逐逻辑时间轨迹是唯一或高效的暴露次序。

### 9.8 完整暴露的终值

> [!theorem] 定理 5：规范记录的完整暴露与次序无关
> 任取两条从相同固定规格与输入 $x$ 开始的完整合法阶段化暴露轨迹。它们可以具有不同阶段秩和中间子集，但在各自完整阶段暴露相同的 $E_x,M^*,Z^*$ 以及全部规范准备、选择与完成标签；忽略阶段秩以后，终端所暴露的规范记录都是同一个 $\mathcal T_x$。

**证明。** 完整性给出 $E_N=E_x$、$H_N=M^*$ 以及三类事件集合的完整定义域。第 9.1 节又把每个阶段的函数值定义为固定规范标签函数在相应子集上的限制，所以完整定义域上的限制就是标签函数本身；并且 $Z_N^{\mathrm{comp}}=Z^*$。对空纤维 $B_{v,\theta}=\varnothing$ 与空候选集合 $\mathcal C_{j,\theta}=\varnothing$，式 (25) 与式 (24) 的恒等情形分别唯一补出 $q_v^{\theta+1}=q_v^\theta$ 与 $y_j^{\theta+1}=y_j^\theta$。阶段秩只改变这些限制扩大的先后，不改变其终值。$\square$

定理 5 是固定 $\mathcal T_x$ 上的过滤结论，不是独立的解释器正确性定理。程序正确性需要另行给出实现记录到规范记录的精化证明；见附录 S.9。

## 10. 一次计算产生的事件 DAG

第 6.4 节把 $(v,\theta)$ 作为一个完整的节点事件。但一个节点事件内部既有本地准备和状态采用，同一区域的多个节点事件又共同依赖一次区域选择。为了表示这些依赖，本节把节点事件与区域选择事件进一步拆成较细的**函数作用事件**，再构造它们之间的值、节点状态与 selector-history 依赖图。

第 8--9 节用来判定“以后不会再有另一个原子”的封闭证书没有作为函数作用事件加入本图。若要研究这些证书本身的推导过程，还需另外加入相应顶点与依赖关系；本文不会把未画出的封闭证明冒充为值依赖边。

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

称为该区域选择事件的**选择作用事件**。它是式 (24) 的一次函数作用，同时产生 $\mathcal A_{j,\theta}$ 与 $y_j^{\theta+1}$。若 $v\in\mathcal A_{j,\theta}$，再定义：

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

若 $v\in\mathcal C_{j,\theta}$，令下列三个有序对属于 $\mathscr A_x^{\mathrm{ev}}$：

$$
P_{v,\theta}
\longrightarrow
S_{j,\theta}
\longrightarrow
U_{v,\theta},
\qquad
P_{v,\theta}\longrightarrow U_{v,\theta}.
$$

若 $v\in\mathcal A_{j,\theta}$，再令下列两个有序对属于 $\mathscr A_x^{\mathrm{ev}}$：

$$
U_{v,\theta}\longrightarrow F_{v,\theta},
\qquad
P_{v,\theta}\longrightarrow F_{v,\theta}.
$$

这些边分别记录式 (18) 在同一逻辑时间内的直接函数自变量依赖：选择读取准备所得的描述量，状态采用读取选择结果与候选新状态，完整输出读取采用后的状态与准备所得的本地内容。

### 10.3 节点状态与 selector-history 的跨时间依赖

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

类似地，若：

$$
(j,\theta),(j,\theta')\in\mathcal E_x^{\mathrm{sel}},
\qquad
\theta<\theta',
$$

并且不存在满足：

$$
\theta<r<\theta',
\qquad
(j,r)\in\mathcal E_x^{\mathrm{sel}}
$$

的 $r\in\mathbb N$，则令：

$$
S_{j,\theta}\longrightarrow S_{j,\theta'}
$$

属于 $\mathscr A_x^{\mathrm{ev}}$。候选集合为空的中间时间只保持历史，所以 $S_{j,\theta'}$ 读取的 $y_j^{\theta'}$ 由前一个实际选择作用确定。这里没有从 $F_{v,\theta}$ 指向后续 $S_{j,\theta'}$ 的 history 边；式 (14) 已经排除了这种直接依赖。不过，过去的完整输出仍可经普通消息影响未来的描述量和选择，例如形成 $F_{v,\theta}\to P_{w,\theta'}\to S_{j,\theta'}$ 的消息依赖路径。

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
\tag{43}
$$

这个秩由事件坐标固定，只用于证明无环；它不是第 8--9 节可随轨迹改变的阶段秩 $\alpha_E,\alpha_M,\alpha_P,\alpha_S,\alpha_C$。

这里的字典序定义为：

$$
(\theta,p)<_{\mathrm{lex}}(\theta',p')
\Longleftrightarrow
\bigl(\theta<\theta'\bigr)
\qquad\text{或}\qquad
\bigl(\theta=\theta'\ \text{且}\ p<p'\bigr).
$$

按这个次序比较秩。同一时间内的依赖严格增加 $p$；节点状态与 selector-history 依赖严格增加 $\theta$；消息依赖由 $\delta(a)>0$ 也严格增加 $\theta$。所以每条事件边都严格增加式 (43)。沿有向边不可能回到原秩，因此事件图没有有向环。

由此得到两项不同事实：

1. 固定空间图 $G$ 按第 2.2 节的假设是 DAG；
2. 每次具体输入产生的上述细分事件图也由式 (43) 证明为 DAG。

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
\tag{44}
$$

称 $(J,Q_\rho)$ 为区域商图。它不是消息图。

$\mathcal R_j$ 本身只是一个节点子集。如果把 $G$ 中起点和终点都位于 $\mathcal R_j$ 的边取出来，就得到 $G$ 在该子集上的诱导子图；由于 $G$ 已经是 DAG，这个诱导子图自动无环，不需要再加一条“region 无环”公理。与此不同，式 (44) 把每个节点子集收缩成一个点，所得区域商图可以有环。

即使固定节点图是路径：

$$
u\longrightarrow v\longrightarrow w,
$$

只要 $u,w\in\mathcal R_0$ 且 $v\in\mathcal R_1$，区域商图就含有：

$$
0\longrightarrow1\longrightarrow0.
$$

这不构成函数作用事件图中的有向环。即使某次计算确实沿这两条空间边依次产生消息，每条消息依赖边也会因 $\delta(a)>0$ 而严格增加逻辑时间。若第一条消息由逻辑时间 $\theta$ 的节点事件产生，那么返回区域 $0$ 时，对应的节点事件与区域选择事件具有某个逻辑时间 $\theta'>\theta$。selector-history 只给同一个 $j$ 的选择事件增加跨时间边，不增加式 (44) 的跨区域边。本文因此不要求区域商图无环。

## 11. 在逻辑时间切面停止与继续

### 11.1 完整记录的左前缀

固定 $b\in\mathbb N$，并要求 $0\le b\le\Theta_{\max}+1$。定义 $\mathcal T_x$ 在切面 $b$ 左侧的**规范前缀** $\mathcal T_{x,<b}$，它由以下坐标组成：

1. $q_v^0,\ldots,q_v^b$ 与 $y_j^0,\ldots,y_j^b$；
2. 所有逻辑时间小于 $b$ 的规范准备、选择与完成标签；
3. 由这些完成标签按式 (27)--(28) 派生的全部内部消息与外部输出记录。

等价地，第二项取第 10 节中满足 $\operatorname{etime}(\xi)<b$ 的全部函数作用事件及其函数值。由于一个 $S_{j,\theta}$ 同时确定 active set 与 $y_j^{\theta+1}$，这个前缀不会停在一次区域选择的两个输出之间。$\mathcal T_{x,<b}$ 是唯一完整记录 $\mathcal T_x$ 的限制，不依赖某条阶段轨迹是否已经求得它。

### 11.2 跨越切面的内部消息

定义：

$$
W_b
=
\{m\in M^*\mid
\operatorname{send}(m)<b
\le\operatorname{time}(m)\}.
\tag{45}
$$

$W_b$ 中的每条消息都已经由某个满足 $\theta<b$ 的完整输出作用事件 $F_{v,\theta}$ 产生，但它到达的完整时间纤维位于切面右侧。丢掉 $W_b$ 会改变未来某些式 (21)。

### 11.3 切面状态、未来输入和输出前缀

第 6 节的 $q_v^b$ 正好是节点 $v$ 完成所有满足 $\theta<b$ 的状态采用作用事件 $U_{v,\theta}$ 以后、处理逻辑时间 $b$ 的任何节点事件以前的状态。

同样，$y_j^b$ 是区域 $j$ 完成所有满足 $\theta<b$ 的选择作用事件以后、处理时间 $b$ 的任何区域选择事件以前的历史；候选为空的时间只作恒等传递。

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
(y_j^b)_{j\in J},
W_b
\right).
\tag{46}
$$

$Z_{<b}$ 不影响未来节点计算；若要在恢复后重建完整多端口输出记录，则还要保存 $Z_{<b}$ 或保存“这些输出已被外部可靠接收”的等价证据。

### 11.4 分段继续定理

> [!theorem] 定理 6：规范左前缀上的继续等于一次算完
> 从 $Q_b$ 开始，以 $(q_v^b)$ 为初始节点状态、以 $(y_j^b)$ 为初始选择历史，令恢复递归开始时已有消息集合 $M^{\mathrm{res}}_{<b}=W_b$，并只使用 $E_{\ge b}$。对
> $$
> \theta=b,b+1,\ldots,\Theta_{\max}
> $$
> 依次递归，把式 (21) 改写为：
> $$
> B^{\mathrm{res}}_{v,\theta}
> =
> B_{v,\theta}(E_{\ge b},M^{\mathrm{res}}_{<\theta})
> \qquad(b\le\theta\le\Theta_{\max}),
> $$
> 其余步骤仍按第 6.3 节递归；把本次按式 (27) 产生的消息记为 $M_\theta^{\mathrm{res}}$，并在每一步令：
> $$
> M^{\mathrm{res}}_{<\theta+1}
> =M^{\mathrm{res}}_{<\theta}\cup M_\theta^{\mathrm{res}}.
> $$
> 所得第 6.3 节全部时间不小于 $b$ 的后缀坐标——完整时间纤维 $B$，候选节点的 $h,\widetilde q,d$，候选集合 $\mathcal C$，active sets $\mathcal A$，节点状态 $q$，选择历史 $y$，以及 active 节点的 $f^A,f^O$——逐坐标等于 $\mathcal T_x$ 的相应值。重新产生的内部消息恰为
> $$
> \{m\in M^*\mid\operatorname{send}(m)\ge b\},
> $$
> 重新产生的外部输出恰为
> $$
> \{z\in Z^*\mid\operatorname{outtime}(z)\ge b\}.
> $$
> $W_b$ 则恰好提供满足 $\operatorname{send}(m)<b\le\operatorname{time}(m)$ 的边界消息；它们是右侧时间纤维的已有输入，不会被重新产生。

若 $b=\Theta_{\max}+1$，上述递归区间为空；由定理 1 还有 $W_b=\varnothing$，且不存在发送时间或输出时间不小于 $b$ 的记录，定理结论直接成立。

**证明。** 以下设 $b\le\Theta_{\max}$，并对 $\theta=b,\ldots,\Theta_{\max}$ 归纳。归纳中保持消息不变量：

$$
M^{\mathrm{res}}_{<\theta}
=
W_b\cup\bigcup_{r=b}^{\theta-1}M_r.
$$

它在 $\theta=b$ 时由恢复递归的初值成立。时间 $b$ 的旧节点状态与旧选择历史都由式 (46) 给出，并与完整计算相同。

一般地，任取 $\theta\ge b$。完整计算中能进入时间 $\theta$ 纤维的外部记录必属于 $E_{\ge b}$。能进入该纤维的内部消息由式 (29) 满足 $\operatorname{send}(m)<\theta$：其中发送时间小于 $b$ 的消息恰由 $W_b$ 提供，发送时间 $r\in[b,\theta)$ 的消息则由归纳式右边的 $M_r$ 提供。恢复集合刻意不保存发送时间与到达时间都小于 $b$ 的已消费消息，但这些消息不可能成为时间 $\theta$ 的原子。因此，恢复集合与原累积消息集合虽然未必相等，却在构造 $B_{v,\theta}$ 时给出完全相同的原子。

于是式 (21)--(28) 的全部自变量相同，所得 $B,h,\widetilde q,d,\mathcal C,\mathcal A,q,y,f^A,f^O$ 以及本时间的消息与输出均逐坐标相同。特别地 $M_\theta^{\mathrm{res}}=M_\theta$；代入恢复消息更新式便得到时间 $\theta+1$ 的同一不变量。归纳完成。$\square$

这个定理说明式 (46) 中的节点状态、selector-history 与跨界消息共同足以从规范前缀 $\mathcal T_{x,<b}$ 的右边继续当前模型。

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
\tag{47}
$$

对每个 $\theta\in\mathcal W_{j,n}$，定理 3 已经固定候选集合。集合很大只表示有很多区域时间位置的输入完整；它不自动给出一个能同时求值所有节点状态与 selector-history 递归的快速公式。

### 12.3 区域商图无环只是一项可选附加条件

若式 (44) 的 $(J,Q_\rho)$ 恰好无环，可以选择一个区域全序，使每条商图边的起点都排在终点以前；这样的全序称为区域拓扑序。其存在性可对 $|J|$ 归纳证明：有限 DAG 至少有一个无入边顶点，否则不断逆着入边行走会重复顶点并形成环；先把该顶点排在最前，删除后对剩余有限 DAG 重复。随后可以沿这个次序研究一种更规则的前沿传播方法。这可能帮助构造较大的式 (47)，但它不改变式 (33)--(36) 中任何一个已给下界的数值。

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
\tag{48}
$$

并且右边若含状态递归，必须按第 6 节的节点状态与 selector-history 依赖解释。

定理 3 证明输入不再增加；式 (48) 证明一次联合计算没有改变结果。这是两个不同命题。

### 12.5 四层研究顺序

可以把后续工作分成四层：

1. **语义层**：第 1--6 节定义映射 $x\mapsto\mathcal T_x$；
2. **阶段层**：第 8--9 节定义阶段秩、合法暴露轨迹与关闭条件；
3. **代数层**：证明哪些逐时间函数满足式 (48) 一类联合求值等式；
4. **实现层**：选定计算模型、算法与成本函数以后研究效率。

任一层都不能由后一层的术语替代。区域划分给出共同选择的边界，但不会替任意节点函数制造可联合求值性质。

## 13. 从当前 TimedDAG 继续扩展时会改变什么

本节不是当前定义的一部分，只说明每种扩展会触及哪一条证明。

### 13.1 允许固定节点图有环，但仍保持正时延

若删除第 2.2 节“固定图无环”的条件，而仍保持每条边 $\delta(a)>0$，则对任意固定有限时间上界 $B$，按 $\theta=0,\ldots,B$ 的递归仍然唯一，因为当前消息只能影响更大时间。

但一次完整运行可能沿有向环不断产生更大时间的消息，不再具有式 (19) 的全局有限上界。因此要改为研究：给定有限逻辑时间切面，是否能在有限工作后完成该切面。定理 1 的“整个运行有限”部分不能原样保留。

这一推广现已在续篇 [[positive-delay-graph-finite-cut-learning-note|《正时延有向图的有限切面语义》]] 中完成。续篇不改写本文的 TimedDAG 定义，而是以相容的有限 cut 记录代替全局有限完整记录，并证明 seal、continuation 与 cut composition。

### 13.2 允许零时延边

若某条边满足 $\delta(a)=0$，时间 $\theta$ 的完整输出可能立即改变同一时间的输入纤维。式 (29) 失效，事件秩可能从阶段 $3$ 指回同一时间的阶段 $0$。

这时必须另外定义同刻求值序、固定点、方程求解器或拒绝某些环。不能只把 $0$ 填入现有 $\delta$ 而继续使用当前证明。

### 13.3 节点内部异步计算

在完整纤维已经确定后，一个节点可以把 $\operatorname{Agg}$、$\operatorname{Upd}$、读取函数和 $\operatorname{Full}$ 分成许多内部步骤。只要存在一个删除这些内部中间量的函数，并且删除后得到的状态、消息和输出仍等于式 (9)--(12)，这种分解就没有改变正文语义。

若希望在同一逻辑时间的完整纤维尚未确定前，就根据部分原子发布不可撤销状态或图内消息，则已不再实现本文函数。它需要新的节点语义，并必须重新证明候选集合、消息发射和封闭下界之间的关系。

### 13.4 让 selector-history 读取完整输出

当前式 (14) 只允许 selector step 读取旧历史、逻辑时间和当前描述量，并在 $\operatorname{Full}$ 以前确定新历史。若要让 $y_j^{\theta+1}$ 读取某个 $f^A_{v,\theta}$ 或 $f^O_{v,\theta}$，就必须改变式 (14)，并把历史更新从当前选择作用中拆出。

事件图随后会出现从 $F_{v,\theta}$ 到后续历史更新或选择作用的边。直接语义仍需重新规定更新发生在哪个逻辑时间；第 10 节的依赖图、第 11 节的 continuation，以及“先确定整个时间块的 route、再批量应用 $\operatorname{Full}$”的求值次序都要重新证明。

### 13.5 允许一个节点属于多个选择域

当前满射 $\rho:V\to J$ 保证每个节点恰属一个区域。若一个节点同时参加多个选择，必须定义多个选择结果发生冲突时怎样决定状态采用与完整输出。把 $\rho$ 换成一般关系而不增加冲突规则，不会得到一个完整函数。

## 14. 本文已经证明的结果与尚未证明的结果

本文正文已经给出：

1. 完整输入下有限且唯一的直接语义（定理 1）；
2. 节点时间纤维的关闭条件（引理 2）；
3. 区域候选集合不会再增加的条件（定理 3）；
4. 至少一条完整合法顺序暴露轨迹存在（命题 4）；
5. 规范记录的完整暴露与阶段次序无关（定理 5）；
6. 规范逻辑时间左前缀上的继续等于一次算完（定理 6）；
7. selector-history 的唯一递归、跨时间依赖与切面保存；
8. 每次有限运行的规范值与状态依赖事件图无环；
9. 区域商图不必无环。

仍需单独完成的工作包括：

- 把第 9 节实现成规范记录上的阶段暴露检查器，并以随机合法阶段秩检验式 (33)--(40)；程序求值的正确性则按附录 S.9 另作精化检验；
- 给出从更受限模型到本文坐标的完整嵌入证明，而不只比较最终输出；
- 找到能推出较大关闭窗口的区域结构定理；
- 对具体神经节点证明式 (48) 的联合求值等式与复杂度；
- 对本文以外更一般的动态 firing、无限 batch 或隐藏 microstep 重新证明有限切面局部有限性；正时延微节点 Graph 的有限切面语义已由续篇完成；
- 最后才研究零时延环或更一般的 Graph。

## 15. 建议的学习顺序

第一次阅读只完成以下步骤：

1. 读第 1--3 节，独立写出一个 $B_{v,\theta}(E,M)$；确认它只是由目标与时间取出的集合。
2. 读第 4--5 节，给定一个旧节点状态、旧选择历史和非空纤维，依次写出 $h,\widetilde q,d,C,(A,y'),O,q'$。
3. 手算第 7 节，直到能够解释为什么 $m_0,m_1$ 的发送时间不同而到达时间相同。

第二次阅读再做：

4. 从式 (33)--(36) 不看证明地重证引理 2 与定理 3。
5. 构造一个节点最终完整时间纤维为空的例子，说明为什么仍需该节点的前沿越过 $\theta$。
6. 分别取 $\tau_j=-,+$ 与 $\kappa_j=0,1$，手算四种组合，确认“读取哪个状态”和“采用哪个状态”是不同坐标；再手算第 7.7 节的两次历史更新。

第三次阅读才做：

7. 为第 7 节列出 $P,S,U,F$ 事件顶点，并检查节点状态边、selector-history 边和消息边都增加式 (43)。
8. 选择一个切面 $b$，写出 $W_b$，然后检查丢掉它会使哪个未来完整时间纤维缺元素。
9. 最后研究式 (47)--(48)，不要把较大的关闭窗口误当成已经存在高效联合算法。

## 16. 可选的相关材料

本文的数学定义不依赖下列材料。只有在已经能够独立手算第 7 节后，才建议按目的查阅：

- [[timed-dag-chunk-prefill-learning-note|以本文为唯一前置的 chunk prefill、时间 tile 与严格分层 region 续篇]]；
- [[positive-delay-graph-finite-cut-learning-note|以本文为唯一前置的正时延有环 Graph、finite-cut 与 SCC 边界续篇]]；
- [SettleGraph 的独立语义文档](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/experiment-semantics-and-naming.md)；
- [[current-mainline|TIDE 当前研究台阶]]。

这些材料中的同名词不能反过来改写本文公式；若两份文档要建立关系，必须给出从一边全部数学坐标到另一边全部数学坐标的函数或关系。

## 附录 S：计算机系统词汇与正文数学对象的对应（可选）

本附录只做翻译，不增加正文定理的前提。系统词的含义依赖所选模型；以下对应只适用于本文已经定义的数学对象。

> [!info]- S.1　semantics、logical time、stage 与 visibility
> **semantics（语义）**对应固定规格下由定理 1 唯一确定的映射 $x\mapsto\mathcal T_x$。两个过程“语义相同”表示它们得到相同的 $\mathcal T_x$，或得到事先明确指定的同一投影。
>
> **logical time（逻辑时间）**对应第 2.1 节的 $\theta\in\mathbb N$；内部消息的逻辑到达时间由式 (7) 定义。**machine time / wall clock（机器时间、墙钟时间）**若需记录，要另加坐标 $w\in\mathbb R_{\ge0}$。
>
> **stage（阶段）**对应第 8.1 节的索引 $n$。它排列阶段化暴露轨迹，不是逻辑时间或墙钟时间。
>
> 外部输入记录的 **visibility（可见）**对应 $\alpha_E(e)\le n$，内部消息的 **visibility / publication（可见、公开）**对应 $\alpha_M(m)\le n$。它们不等于“可以由现有数据推导”；消息还须满足式 (40) 的源事件约束。外部输出记录在阶段 $n$ 已经确定对应 $z\in Z_n^{\mathrm{comp}}$；本文没有再为输出定义一个独立的 publication 阶段秩。
>
> 本文只有一个全局 $H_n$。若不同消费者可以在不同阶段得到同一消息，必须另加消费者坐标并定义 $H_{c,n}$；这不是当前模型的一部分。

> [!info]- S.2　message、port、bucket 与 channel identity
> **message（消息）**的类型是 $m=(\mathrm{msg},\eta,a,y)\in\mathsf{Msg}$；一次输入实际产生的消息构成 $M^*\subseteq\mathsf{Msg}$。payload 只对应 $y$，发送时间 $\eta$ 和边 $a$ 也是消息坐标。
>
> 在完整语义中，**produced / generated（产生）**对应 $m\in M^*$；在阶段 $n$，源事件已经完成对应 $m\in M_n^{\mathrm{src}}$。它仍不推出 $m\in H_n$。
>
> **input/output port（输入、输出端口）**对应 $\mathsf I,\mathsf O$ 与式 (2)。端口不是节点。多个端口可以属于同一节点。
>
> **bucket / input bucket / time bucket（输入桶、时间桶）**严格对应式 (8) 的纤维 $B_{v,\theta}(E,M)$。在完整语义里，式 (21) 把它实例化为 $B_{v,\theta}$。
>
> **channel identity（通道身份）**对应内部消息保留的边坐标 $a$；外部输入来源对应端口坐标 $i$。$\operatorname{Agg}_v$ 可以区分它们。数组或队列只是这些有限集合的一种编码。

> [!info]- S.3　region、candidate、selector、active 与 Top-K
> **region（区域）**只对应式 (6) 的节点子集 $\mathcal R_j$。它不持有普通消息和节点状态；由 $j$ 索引的 selector 另有选择历史 $y_j^\theta$。
>
> **candidate（候选）**在完整记录中对应式 (22) 的 $\mathcal C_{j,\theta}$；阶段 $n$ 暂得的候选是第 8.6 节的 $\mathcal C^{(n)}_{j,\theta}$。式 (38) 成立时二者才相等。
>
> **selector（选择器）**对应式 (14) 的一步全函数族。一次调用由区域索引 $j$、完整候选集合 $C$、旧选择历史 $y$、逻辑时间 $\theta$ 与带节点坐标的描述量族 $(d_v)_{v\in C}$ 共同确定；其中 $j,C$ 索引所调用的函数族成员，后三项是该成员的普通自变量。
>
> **selector-history（选择历史）**对应 $y_j^\theta\in Y_j$。它可以编码累计激活次数、移动平均、最近激活位置或预算，但不是程序日志，也不必逐项保留过去。若 $Y_j$ 为单点集，就没有有效历史信息。
>
> **active node / selected node（激活、选中节点）**对应 $v\in\mathcal A_{j,\theta}$。只有这类节点应用式 (26)；$\mathsf{Selected}_n$ 则是已应用区域选择事件的集合，不是 active nodes 的集合。
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
> **proposal** 对应候选新状态 $\widetilde q$。**state commit（状态提交）**对应式 (25) 的节点状态采用作用 $U_{v,\theta}$；选择作用 $S_{j,\theta}$ 则同时确定下一 selector-history。二者都不同于节点事件进入 $\mathsf{Completed}_n$，也不同于消息进入 $H_n$；单独使用 `commit` 时必须说明提交哪一种对象。**expensive compute / NodeCompute** 对应式 (12) 与 (26) 的 $\operatorname{Full}_v$；“昂贵”不是数学性质。

> [!info]- S.5　seal、frontier、watermark、closure 与 ready
> **seal（封闭下界）**对应式 (33) 的 $\sigma$。例如边 seal 为 $b$ 精确表示 $M^*(a,<b)\subseteq H_n$，不是“当前队列为空”。
>
> 系统中的 seal 控制记录对应 $\sigma_n$ 到 $\sigma_{n+1}$ 的变化；正文只规定该值何时有效，不规定控制记录的编码或证明算法。
>
> **node frontier** 对应式 (35)；**region frontier** 对应式 (36)。区域前沿是成员前沿的最小值。
>
> **closed / closure（关闭）**对应式 (37) 的纤维相等或式 (38) 的候选集合相等。seal 是推出关闭的前提，二者不是同一个对象。
>
> **watermark** 若表示“输入确定到哪里”，对应某个 $\sigma$ 或 $\lambda$；若表示“节点完成到哪里”，对应式 (41) 的 $\operatorname{DoneTo}_n(v,b)$。必须注明采用哪一种。
>
> **ready（就绪）**对节点状态对应第 8.8 节的 $\operatorname{StatePred}(v,\theta)\subseteq\mathsf{Done}$，对选择历史对应 $\operatorname{HistPred}(j,\theta)\subseteq\mathsf{Selected}$；区域选择还要满足第 9.2 节的纤维关闭与准备条件。
>
> **barrier（屏障）**是实现等待这些数学条件成立的位置，并不要求所有处理器同时停止。

> [!info]- S.6　identifier、schema 与 semantic coordinate
> **identifier / ID（标识符）**在正文中首先就是集合元素本身，例如 $v\in V$、$a\in A$。若程序需要整数，可为本文任一有限对象集合 $X$ 固定单射 $\operatorname{id}_X:X\to\mathbb N$。单射保证不同对象有不同整数。
>
> **schema（数据形状约定）**对应一个积集合以及各坐标的所属集合。例如 $\mathsf{Msg}$ 规定消息具有标签、发送时间、边和值四个坐标。字段名可以改变；删除边坐标则会改变正文对象。
>
> **semantic coordinate（语义坐标）**是在已经说明对象类型后，用于唯一指出该类型中数学对象的有序组。节点事件的语义坐标是 $(v,\theta)$，区域选择事件的语义坐标是 $(j,\theta)$，函数作用事件还包含 $\mathrm{prep}$、$\mathrm{select}$、$\mathrm{adopt}$ 或 $\mathrm{full}$ 标签；其中 $\mathrm{select}$ 同时产生 active set 与下一选择历史。输出位置的坐标是 $(\theta,o)$。
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
> 外层标签先把不同层次的事件变成不同编码对象，随后单射保证不同编码对象不会共用一个整数。这里 $\mathsf{EventRef}_x$ 只是一项编码域，不把三种事件合并成同一种语义作用。这项编码固定在输入 $x$ 的完整事件集合上；阶段 $n$、线程编号、墙钟时刻和本次分块编号都不在编码函数的输入中，所以改变它们不会改变 ID。若还要求不同输入之间共享稳定整数 ID，就需要另外在一个与输入无关的全局坐标域上固定编码；这不是本文语义的前提。

> [!info]- S.7　chunk、prefill、decode、packing 与 fast path
> **input chunk（输入分块）**可以对应 $E_{n+1}\setminus E_n$；同一批进入 $H$ 的消息对应 $H_{n+1}\setminus H_n$。**compute chunk（计算分块）**则是某类事件集合的划分。两者必须区分。
>
> 若 $\mathscr E=\mathscr E_1\cup\cdots\cup\mathscr E_k$ 且各 $\mathscr E_i$ 两两不交，那么 $(\mathscr E_i)$ 是事件集合 $\mathscr E$ 的一种分块；还须说明 $\mathscr E$ 采用节点事件、区域选择事件还是函数作用事件。
>
> **prefill** 通常表示一次联合处理许多已知输入位置；**decode** 通常表示逐个或小批增加输入位置。要声称二者等价，必须比较第 6 节的节点状态、selector-history、内部消息、所有输出端口、候选集合和 active sets，而不只是最后一个张量。
>
> **packing / packed attention** 是式 (48) 中 $\operatorname{Pack},\mathcal K,\operatorname{Unpack}$ 的具体实现候选。seal 证明输入不会再增加；式 (48) 证明联合求值等于参考递归。两项证明不能互相替代。
>
> **fast path** 可以在额外图结构和代数条件成立时使用联合函数；一般路径仍须得到第 6 节的规范记录。若还要比较分阶段进展，则另须投影到第 9 节的合法阶段化暴露轨迹。

> [!info]- S.8　runtime、scheduler、workspace、commit 与 trace
> **compute / evaluate（计算、求值）**在正文中只指取已给全函数的函数值；本文没有定义指令集或成本函数。因此“可求值”不包含时间复杂度结论。
>
> **runtime / executor（运行时、解释器）**不是正文定义的数学对象。第 9.1 节的轨迹已经是固定 $\mathcal T_x$ 上的阶段化暴露，不能单凭“程序产生了这样一条轨迹”证明程序算对；实现与规范记录之间还必须另行给出附录 S.9 定义的精化关系。
>
> **scheduler（调度器）**在通过精化投影以后，对应选择哪些合格事件进入第 9.2--9.3 节的 $\Delta\mathsf{Prepared}_n,\Delta\mathsf{Selected}_n,\Delta\mathsf{Completed}_n$。选择事件还必须满足 selector-history 就绪条件；投影后的调度只改变阶段秩，不能改变 $\mathcal T_x$。
>
> **workspace（临时工作区）**可以保存第 9.4 节提前求出的 $h,\widetilde q,d$。临时变量不等于式 (25) 已经采用的状态。
>
> **event completion（事件完成）**对应 $(v,\theta)\in\mathsf{Completed}_n$，即 $\alpha_C((v,\theta))\le n$。**completed to $b$（完成到 $b$）**对应式 (41) 的复合谓词。二者都不等于消息可见：本文允许源事件完成以后，其消息再在更晚阶段进入 $H_n$。若另一份规格把“消息已经进入 $H$”也纳入 completed 的定义，那是更强的另一种约定，不能与本文的 $\mathsf{Completed}_n$ 混用。
>
> **atomic commit（原子提交）**在本文中的最小要求是：节点状态后继只能读取式 (25) 确定以前的 $q_v^\theta$ 或确定以后的 $q_v^{\theta+1}$；选择历史后继只能读取式 (24) 确定以前的 $y_j^\theta$ 或确定以后的 $y_j^{\theta+1}$。二者都不能读取规格未定义的中间状态。这不声称使用某条特定处理器原子指令。
>
> **semantic trace（语义记录）**对应唯一的 $\mathcal T_x$；**staged exposure trace（阶段化暴露轨迹）**对应第 9.1 节的递增子集与标签限制，同一 $x$ 可以有多条。**execution trace（执行记录）**属于实现另行定义的记录集合。普通语义精化只保留规范坐标；若要比较阶段化暴露，还须另给保留阶段秩与递增子集的精化投影。两种投影都在附录 S.9 定义。

> [!info]- S.9　continuation、checkpoint、resume 与 refinement
> **continuation** 对应式 (46) 的 $Q_b$，其中同时含节点状态、selector-history 与跨界消息。只为继续未来计算而保存的 **checkpoint** 可以是 $Q_b$ 的某种可保存编码。
>
> 若保存与读取函数分别为 $\operatorname{save}$ 和 $\operatorname{load}$，无损编码至少要求：
> $$
> \operatorname{load}(\operatorname{save}(Q_b))=Q_b.
> $$
>
> **resume** 对应从相同 $Q_b$ 与 $E_{\ge b}$ 再执行未来递归。定理 6 给出它与一次算完相同的数学目标。$Q_b$ 并不是规范左前缀 $\mathcal T_{x,<b}$ 的完整编码；若要重建整个语义记录，还须保存该前缀或保存足以重算它的数据。若只要求拼回完整外部输出记录，则至少还须保存 $Z_{<b}$，或保存这些输出已被可靠接收的等价证据。
>
> **refinement（实现精化）**需要先给出调度集合 $\mathsf{Sched}$、程序记录集合 $\mathsf{ImplTrace}$，以及一个包含全部规范记录和可能错误的同形记录的集合 $\mathsf{SemTrace}$。再给出函数：
> $$
> \operatorname{Run}:
> \left(\prod_{i\in\mathsf I}P^{[L_i]}\right)
> \times\mathsf{Sched}
> \to\mathsf{ImplTrace}.
> $$
> 令 $\operatorname{Legal}_{\mathrm{impl}}(x)\subseteq\mathsf{Sched}$ 是实现一侧的容许调度谓词，例如检查类型、因果等待与 seal 证据；它的定义不能预先把“程序记录投影后已经等于规范记录”当作条件。定义相应的程序记录子集：
> $$
> \mathsf{ImplTrace}_{\mathrm{legal}}
> =\{\operatorname{Run}(x,s)\mid
> x\in\prod_{i\in\mathsf I}P^{[L_i]},\
> s\in\operatorname{Legal}_{\mathrm{impl}}(x)\}.
> $$
> 只需在这个子集上给出删除线程、墙钟和阶段等实现坐标的普通语义投影：
> $$
> \Pi:\mathsf{ImplTrace}_{\mathrm{legal}}\to
> \mathsf{SemTrace}.
> $$
> 其中每个 $\mathcal T_x$ 都属于 $\mathsf{SemTrace}$。这里的 $\Pi$ 必须是预先固定的遗忘投影：它保留全部规范坐标及其原值，只删除线程、墙钟、缓存、阶段等额外实现坐标。它不得调用参考语义、重新执行递归，或按照输入修补程序记录中的错误值。下式是实现的**安全性**目标：
> $$
> \forall x\in\prod_{i\in\mathsf I}P^{[L_i]},\quad
> \forall s\in\operatorname{Legal}_{\mathrm{impl}}(x),
> \qquad
> \Pi(\operatorname{Run}(x,s))=\mathcal T_x.
> $$
> 它单独成立时可能只是因为没有容许调度。还须另列**可执行性**条件：
> $$
> \forall x\in\prod_{i\in\mathsf I}P^{[L_i]},
> \qquad
> \operatorname{Legal}_{\mathrm{impl}}(x)\ne\varnothing.
> $$
> $\Pi$ 的值不含第 8--9 节的阶段秩。若还要验证执行记录的分阶段进展，另给一个包含阶段信息的记录集合 $\mathsf{StageTrace}$、投影
> $$
> \Pi_{\mathrm{stage}}:
> \mathsf{ImplTrace}_{\mathrm{legal}}
> \to\mathsf{StageTrace},
> $$
> $\Pi_{\mathrm{stage}}$ 同样必须预先固定；它只比 $\Pi$ 保留更多已有的阶段坐标，不得补写、重算或修正程序记录以制造一条合法轨迹。
>
> 令 $\mathsf{LegalExposure}(x)\subseteq\mathsf{StageTrace}$ 表示第 9 节中输入 $x$ 的全部完整合法阶段化暴露轨迹，并要求：
> $$
> \forall x\in\prod_{i\in\mathsf I}P^{[L_i]},\quad
> \forall s\in\operatorname{Legal}_{\mathrm{impl}}(x),
> \qquad
> \Pi_{\mathrm{stage}}(\operatorname{Run}(x,s))
> \in\mathsf{LegalExposure}(x).
> $$
> 这个条件保留阶段信息，不能用普通语义投影 $\Pi$ 代替。

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
> - selector-history 的 owner、初态、更新与切面状态到 $Y_j,y_j^{\mathrm{init}},\operatorname{SelStep}_{j,C},y_j^b$ 的映射；
> - 已生成 `DATA` 到 $m\in M_n^{\mathrm{src}}$、已进入接收侧输入的 `DATA` 到 $m\in H_n$ 的映射；
> - 边 $a$ 在 $b$ 前 `CLOSED` 到 $M^*(a,<b)\subseteq H_n$ 的映射。
>
> SettleGraph 对每个 Token、每个 region 等待该 Token 的所有相关边结算；本文允许不同输入位置通过逻辑时间映射落入同一个 $(v,\theta)$ 或 $(j,\theta)$。若一个 SettleGraph profile 没有有效 selector-history，可把它映为单点集合 $Y_j$。要证明前者是后者的受限情形，必须给出一种时间编码，使不同 Token 不会发生被禁止的同刻汇合，并比较完整节点状态、selector-history、消息、输出端口、候选集合和 active sets。
