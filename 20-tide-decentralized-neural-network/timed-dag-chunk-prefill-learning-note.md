---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-10
tags:
  - tide
  - timed-dag
  - prefill
  - chunk
  - logical-time
  - region
  - selector
  - selector-history
  - mathematics
  - learning-note
---

# TimedDAG 的分块预填充：支持集、时间切面与分层区域

> [!summary] 本文的阅读前提
> 本文只以 [[timed-dag-region-selector-learning-note|《带区域选择的 TimedDAG：从零开始的数学定义》]] 为前置。前置文档定义的节点、边、正时延、输入记录、时间纤维、节点状态、区域、selector-history、selector、完整计算、阶段化轨迹、seal、事件图与切面状态，在本文中直接使用。
>
> 本文研究一个比“能否正确执行”更窄的问题：哪些 TimedDAG 结构允许一个统一外层执行器把连续输入按大时间块交给节点或区域，而不被空间依赖强迫退化为逐 token、逐事件调用。

> [!warning] “高性能”的本文含义
> 本文只把**外层没有拆碎昂贵节点事件**形式化。第 6.4 节将它定义为“节点级时间批暴露”：固定空间图以后，每个节点的昂贵时间事件只被分成数量不随 chunk 长度增长的批次，昂贵计算与控制之间也只有数量不随 chunk 长度增长的外层阶段。本文不从这个性质推出硬件耗时、算术工作量、显存访问效率或 selector 的并行深度。
>
> 若允许把任意有限计算封装成一个 `RunWholeGraph` 调用，那么每个有限 TimedDAG 都可以被表面上写成“一次调用”。为避免这个说法失去内容，本文始终区分：
>
> 1. seal 是否已经固定 tile 的全部输入；
> 2. 拓扑是否允许把整个 tile 一次交给某个区域；
> 3. backend 是否另行给出了保持语义的联合求值实现。

> [!tip] 分三次阅读
> 第一次读第 1--4 节，理解“不交错不是大块 prefill 的必要条件”。第二次读第 5--8 节，理解 selector 为什么会改变合法 tile，以及严格分层 region 如何恢复区域拓扑扫描。第三次读第 9--11 节，研究 Transformer、MoE、混合 token 纤维与结论边界。

本文的主要结论是：

1. 任意正时延 TimedDAG 都有按完整逻辑时间切面继续的正确算法；这不自动给出大块执行。
2. 路径时延不交错且 selector closure 相容时，可以使用按 token 对齐的节点 tile。
3. 路径时延交错时，仍可使用按逻辑时间对齐的 tile；必须保存跨切面的在途消息。
4. 若 region 内没有空间边，且所有跨 region 边服从一个严格区域次序，则每个封闭时间块可以按区域次序扫描，每个 region 只访问一次。
5. 在严格分层类中，selector-history 可以在一次 region tile 内顺序扫描；若节点另有精确 batch witness，随后仍可按节点一次批量应用主时间块中的全部昂贵完整输出函数。这满足第 6.4 节的节点级时间批暴露，但不自动给出低 span。
6. 任一大 tile 的精确联合求值，仍是独立于 seal 与拓扑的 backend 义务。

## 1. 从前置文档导入的对象

### 1.1 固定 TimedDAG 规格

本文固定前置文档所定义的带区域选择的 TimedDAG 规格。其空间图为：

$$
G=(V,A,\operatorname{src},\operatorname{dst},\delta),
$$

其中 $G$ 是有限 DAG，且：

$$
\delta:A\to\mathbb N_{>0}.
$$

区域集合为有限集合 $J$，区域映射为满射：

$$
\rho:V\to J.
$$

对 $j\in J$，仍记：

$$
\mathcal R_j=\rho^{-1}(\{j\}).
$$

完整计算中的节点时间纤维、候选集合和 active set 分别记为：

$$
B_{v,\theta},
\qquad
\mathcal C_{j,\theta},
\qquad
\mathcal A_{j,\theta}.
$$

区域 $j$ 在时间 $\theta$ 以前的 selector-history 记为 $y_j^\theta$。前置文档的 selector step 同时确定：

$$
(\mathcal A_{j,\theta},y_j^{\theta+1}).
$$

节点在时间 $\theta$ 的准备、状态采用与完整输出作用仍记为：

$$
P_{v,\theta},
\qquad
U_{v,\theta},
\qquad
F_{v,\theta},
$$

区域选择作用记为 $S_{j,\theta}$；它就是上述 selector step 的函数作用。

本文不会改变这些对象的定义。一个实现只要声称“等于 TimedDAG 语义”，比较对象仍然是前置文档第 6 节定义的完整计算记录 $\mathcal T_x$，其中包括完整 selector-history 序列。

### 1.2 正则单输入流

为了把路径时延与 token 位置分开，本文先研究单输入情形：

$$
\mathsf I=\{i_\star\}.
$$

令唯一输入端口的目标节点为：

$$
s=\gamma(i_\star)\in V.
$$

固定输入长度 $L\in\mathbb N_{>0}$、token 值序列：

$$
x:[L]\to P,
$$

以及注入间距 $D\in\mathbb N_{>0}$。规定 token $t\in[L]$ 的逻辑输入时间为：

$$
\iota(t)=Dt.
\tag{1}
$$

多输入端口的对应版本可以给每个端口增加固定相位，再把相位加入后文的路径时延集合。正文先保留式 (1) 的单流形式，以免 token 对齐关系被端口记号遮蔽。

只研究从 $s$ 可达的节点。不可达节点不会因这条输入流产生非空时间纤维，可以从本篇性能问题中删去。

### 1.3 三种不同的存在性问题

本文将以下命题严格分开。

1. **语义存在性**：前置文档的逐逻辑时间递归是否唯一确定结果。
2. **外层保块存在性**：是否能把节点的昂贵时间事件分成数量不随 chunk 长度增长的批次，并只经历有界个 heavy/control 阶段。
3. **低成本 backend 存在性**：是否存在一个具体联合函数，以可接受的工作量和并行深度实现该 tile。

前置文档已经证明第一项。本文主要研究第二项，并把第三项写成显式契约，而不把它隐藏进图论结论。

## 2. 路径时延与结构支持集

### 2.1 到达一个节点的路径时延集合

若 $\zeta$ 是从 $s$ 到 $v$ 的有向路径，沿用前置文档的定义：

$$
\Delta(\zeta)
=
\sum_{a\in\zeta}\delta(a).
$$

长度为零的路径只允许在 $v=s$ 时使用，并具有时延 $0$。定义：

$$
\mathcal D(v)
=
\{\Delta(\zeta)\mid
\zeta:s\leadsto v\}.
\tag{2}
$$

因为 $G$ 是有限 DAG，$\mathcal D(v)$ 是有限非空自然数集合。定义：

$$
d_{\min}(v)=\min\mathcal D(v),
\qquad
d_{\max}(v)=\max\mathcal D(v),
\tag{3}
$$

以及节点 $v$ 的路径时延跨度：

$$
w(v)=d_{\max}(v)-d_{\min}(v).
\tag{4}
$$

$d_{\max}(v)$ 是一个绝对到达时延；$w(v)$ 比较到达同一节点的不同路径。二者不是同一个量。

### 2.2 单个 token 的结构支持集

定义 token $t$ 在节点 $v$ 的结构支持集：

$$
\mathsf{Supp}_t(v)
=
Dt+\mathcal D(v)
=
\{Dt+d\mid d\in\mathcal D(v)\}.
\tag{5}
$$

它是一个自然数集合，而不是消息集合。$\theta\in\mathsf{Supp}_t(v)$ 只表示：存在一条空间路径，使 token $t$ 沿这条路径传播时可以在坐标 $(v,\theta)$ 到达。

一个具体输入上的 selector 可能使某条路径不实际产生消息。因此，结构支持集给出可能坐标，不保证每个坐标都发生节点事件。

> [!lemma] 引理 1：实际节点事件落在结构支持集中
> 对任意完整计算中的节点事件 $(v,\theta)$，存在 $t\in[L]$，使：
> $$
> \theta\in\mathsf{Supp}_t(v).
> \tag{6}
> $$

**证明。** 前置文档定理 1 的有限性证明从任意非空时间纤维反向追踪实际消息。由于空间图无环，追踪最终到达某条外部输入记录，并把节点事件时间写成该输入时间加一条空间路径的总时延。再用式 (1) 与式 (5) 即得结论。$\square$

定义节点在整个长度 $L$ 输入上的结构支持集：

$$
\mathsf{Supp}(v)
=
\bigcup_{t\in[L]}\mathsf{Supp}_t(v).
\tag{7}
$$

式 (6) 立即给出：

$$
(v,\theta)\in\mathcal E_x^{\mathrm{node}}
\Longrightarrow
\theta\in\mathsf{Supp}(v).
\tag{8}
$$

### 2.3 全局最大路径时延

沿用前置文档的 $\Delta_{\max}$。在当前单输入限制下：

$$
\Delta_{\max}
=
\max_{v\in V}d_{\max}(v).
\tag{9}
$$

于是：

$$
0\le w(v)\le d_{\max}(v)\le\Delta_{\max}.
\tag{10}
$$

因此，使用 $\Delta_{\max}$ 可以得到统一但可能很保守的界；研究单个节点是否交错时，应优先使用 $w(v)$。

## 3. 不交错与 token 对齐 tile

### 3.1 不交错的定义

称相邻 token 在节点 $v$ **严格不交错**，当且仅当对每个 $t\in[L-1]$：

$$
\max\mathsf{Supp}_t(v)
<
\min\mathsf{Supp}_{t+1}(v).
\tag{11}
$$

这里要求的是前一个集合的所有时间都严格早于后一个集合的所有时间。“两个集合没有共同元素”比式 (11) 弱，不能排除：

$$
\{0,10\}
\quad\text{与}\quad
\{5,15\}
$$

这样的交错。

> [!proposition] 命题 2：不交错判据
> 相邻 token 在节点 $v$ 严格不交错，当且仅当：
> $$
> D>w(v).
> \tag{12}
> $$

**证明。** 由式 (3) 与式 (5)：

$$
\max\mathsf{Supp}_t(v)=Dt+d_{\max}(v),
$$

$$
\min\mathsf{Supp}_{t+1}(v)=D(t+1)+d_{\min}(v).
$$

把二式代入式 (11)，消去 $Dt$，所得不等式正是：

$$
d_{\max}(v)-d_{\min}(v)<D.
$$

再用式 (4) 即得。$\square$

由式 (10) 可知：

$$
D>\Delta_{\max}
\Longrightarrow
D>w(v)
\qquad(\forall v\in V).
\tag{13}
$$

式 (13) 是强充分条件，不是必要条件。

命题 2 只固定节点输入坐标的几何次序。若同一 selector 在一个时间还联合其他节点，则节点 tile 仍需满足第 7 节的 selector closure；不交错本身不消除这种跨节点依赖。

若 $D=\Delta_{\max}$，式 (13) 的严格不等式并未成立，某条最长路径仍可能与下一 token 的最短路径在边界时间相遇；是否实际交错仍应回到式 (12) 检查。

### 3.2 为什么最短输入输出路径也不够

把 $D$ 取成某个输出节点的最短路径时延，只规定了 token 注入的流水间距，不控制同一节点的路径时延跨度。

例如某节点有两条输入路径，其时延集合为：

$$
\mathcal D(v)=\{5,20\}.
$$

若取 $D=5$，token $0$ 的长路径在时间 $20$ 到达，而 token $3$ 的短路径也在时间 $20$ 到达。这里 $D$ 等于最短路径时延，却有：

$$
w(v)=20-5=15>D.
$$

所以，以最短路径作为 token 间距可以形成高重叠流水，但不能推出 token 对齐的节点 tile。第 4 节将说明这种重叠仍可使用逻辑时间 tile。

### 3.3 graded DAG

称当前带时延空间 DAG 相对于输入节点 $s$ 是 **graded** 的，当且仅当存在函数：

$$
r:V\to\mathbb N
$$

满足：

$$
r(s)=0,
\qquad
r(\operatorname{dst}(a))
=
r(\operatorname{src}(a))+\delta(a)
\quad(\forall a\in A).
\tag{14}
$$

> [!lemma] 引理 3：graded DAG 的路径时延唯一
> 若式 (14) 成立，则对每个节点 $v$：
> $$
> \mathcal D(v)=\{r(v)\},
> \qquad
> w(v)=0.
> \tag{15}
> $$

**证明。** 任取从 $s$ 到 $v$ 的路径 $\zeta=(a_1,\ldots,a_m)$。沿路径反复使用式 (14)，中间节点的秩相消，得到：

$$
\Delta(\zeta)=r(v)-r(s)=r(v).
$$

每条路径都有同一时延，所以式 (15) 成立。$\square$

因此，graded DAG 对任意 $D>0$ 都满足逐节点不交错。对节点输入支持而言，自然的 token 边界不是一个统一标量，而是倾斜的节点边界：

$$
b_q(v)=Dq+r(v).
\tag{16}
$$

对于边 $a:u\to v$，式 (14) 给出：

$$
b_q(v)=b_q(u)+\delta(a).
\tag{17}
$$

这正是一个随拓扑层级倾斜的切面。

式 (16) 要成为整个函数作用事件的执行切面，还需 selector 与这些节点边界相容；第 7 节将给出这一限制。

### 3.4 Transformer 链

考虑链：

$$
v_0\to v_1\to\cdots\to v_{15},
\qquad
\delta(v_r,v_{r+1})=1.
$$

令 $r(v_r)=r$。它满足式 (14)。若取 $D=16$，则：

$$
\theta_{r,t}=16t+r.
$$

不同 token 的整个全图时间带互不重合。若取 $D=1$，则：

$$
\theta_{r,t}=t+r.
$$

不同 token 在全图中形成重叠流水，但同一节点仍有：

$$
\mathsf{Supp}_t(v_r)=\{t+r\},
$$

所以节点内 token 次序没有交错。由此可见，$\Delta_{\max}=15$ 并不迫使 $D>15$；决定节点级 chunk 能否对齐的是式 (12)，不是 $D$ 与绝对深度的比较。

## 4. 允许交错时的逻辑时间块

### 4.1 输入前缀与扩展

固定 $q\in\{0,\ldots,L\}$。记：

$$
x_{<q}=(x(0),\ldots,x(q-1)).
$$

其中规定 $x_{<0}$ 是空序列。称同一定长规格中的另一个输入序列：

$$
x':[L]\to P
$$

是 $x_{<q}$ 的扩展，当且仅当：

$$
x'(t)=x(t)
\qquad(0\le t<q).
$$

任何未由该前缀固定的 token 都有位置 $t\ge q$，因而输入时间不小于 $Dq$。

某次完整计算中的全部事件可能在 $Dq$ 以前已经结束。若其有限时间上界小于 $Dq$，本文把前置文档的状态作规范的空闲延拓：在原有限上界以后令所有时间纤维为空、节点状态与 selector-history 保持不变，并且不增加事件或消息，直到时间 $Dq$。这个延拓只为定义下一输入切面处的状态，不改变原完整计算记录中的任何对象。

> [!theorem] 定理 4：标量输入切面以下的前缀不变性
> 对任意两个具有相同前 $q$ 个 token 的输入，二者完整计算在所有 $\theta<Dq$ 的下列对象相同：
>
> - 每个节点时间纤维；
> - 每个候选集合与 active set；
> - 每个节点状态、selector-history、状态采用与完整输出作用；
> - 这些作用产生的内部消息与外部输出记录。

**证明。** 对 $\theta=0,1,\ldots,Dq-1$ 作归纳。

两次计算来自同一个固定规格，所以初始节点状态 $(q_v^0)_{v\in V}$ 与初始 selector-history $(y_j^0)_{j\in J}$ 相同。

在时间 $\theta$，两个输入包含相同的外部记录，因为所有新增 token 的输入时间都不小于 $Dq$。到达时间 $\theta$ 的任意内部消息都由更小逻辑时间的完整输出作用产生，这是 $\delta(a)>0$ 的结果。归纳假设保证这些作用及其消息相同，所以全部 $B_{v,\theta}$ 相同。

随后，前置文档式 (22)--(28) 中的聚合、候选状态、描述量、选择、状态采用和完整输出都是固定函数。相同的旧节点状态、旧 selector-history 与时间纤维产生相同的 active set、新历史及其余结果。归纳完成。$\square$

定理 4 不要求路径不交错，也不要求区域商图无环。它只使用规则输入时间与正边时延。

当 $q=0$ 时，相应结论退化为初始切面 $c_0=0$，不需要另作归纳。

### 4.2 通用标量切面

当 token $0,\ldots,q-1$ 已经公开时，定义：

$$
c_q=Dq.
\tag{18}
$$

定理 4 表示：未来输入不能改变 $\theta<c_q$ 的计算。因此，前置文档的切面状态：

$$
Q_{c_q}
=
\left(
c_q,
(q_v^{c_q})_{v\in V},
(y_j^{c_q})_{j\in J},
W_{c_q}
\right)
\tag{19}
$$

是一个对所有未来扩展都安全的 continuation 状态。

若下一次又公开 token $q,\ldots,q+T-1$，其中 $T\in\mathbb N_{>0}$ 且 $q+T\le L$，新的安全切面是：

$$
c_{q+T}=D(q+T).
$$

本轮新关闭的逻辑时间块为：

$$
I_{q,T}
=
[c_q,c_{q+T}).
\tag{20}
$$

其逻辑时间宽度恰好为 $DT$。这个结论与路径交错程度无关。

### 4.3 跨切面消息不是错误

一个较早 token 的慢路径消息可以在 $c_{q+T}$ 以后才到达。只要它已经在切面左侧产生，就属于前置文档定义的 $W_{c_{q+T}}$。若它还要经过后续节点才能继续产生消息，则相应节点状态、selector-history 与已有在途消息共同保存于式 (19)。

因此：

$$
\text{完成切面 }c_{q+T}
\ne
\text{完成这 }T\text{ 个 token 的全部未来影响}.
\tag{21}
$$

前者是严格定义的逻辑时间前缀；后者在带持久状态的模型中甚至可能没有有限终点。

### 4.4 一个保守的边界厚度

对一个从 token $0$ 开始、长度为 $T$ 的有限输入，最后一个输入时间为 $D(T-1)$。前置文档的有限性证明给出：任何非空节点事件时间都不大于：

$$
D(T-1)+\Delta_{\max}.
\tag{22}
$$

对任意非负实数 $z$，用 $\lfloor z\rfloor$ 表示不大于 $z$ 的最大自然数。

定义全局空间传播厚度：

$$
h_\Delta
=
\left\lfloor
\frac{\Delta_{\max}}{D}
\right\rfloor.
\tag{23}
$$

若 $t\le T-h_\Delta-1$，则：

$$
Dt+\Delta_{\max}<DT.
\tag{24}
$$

这是因为 $T-t\ge h_\Delta+1>\Delta_{\max}/D$。

所以这些输入位置沿任意纯空间路径产生的结构支持坐标都位于切面 $DT$ 左侧。最后至多 $h_\Delta$ 个 token 的部分路径坐标可能越过该切面。

若 $\Delta_{\max}=kD$ 且 $k\in\mathbb N$，则 $h_\Delta=k$。这就是“主体尺度约为 $T-k$，边界尺度约为 $k$”的保守来源。

式 (24) 不能被解释成先删除最后 $h_\Delta$ 个 token，再独立计算前面的 token。交错时，最后几个 token 的快路径消息可能已经进入 $DT$ 左侧，并与更早 token 的慢路径消息位于同一时间纤维。合法切分对象是式 (20) 的时间块，而不是一个按 token 身份过滤的消息子集。

### 4.5 节点交错深度

若只研究节点 $v$ 的两相邻 token 支持，可以定义：

$$
h(v)
=
\left\lfloor
\frac{w(v)}D
\right\rfloor.
\tag{25}
$$

$h(v)=0$ 等价于式 (12) 的严格不交错。一般地，$h(v)$ 给出可以在节点 $v$ 的时间带中越过一个 token 的后续位置数量上界。

当 selector 联合多个节点时，不能只看每个节点自己的 $h(v)$。定义：

$$
\mathcal D(j)
=
\bigcup_{v\in\mathcal R_j}\mathcal D(v),
\tag{26}
$$

并令：

$$
h(j)
=
\left\lfloor
\frac{\max\mathcal D(j)-\min\mathcal D(j)}D
\right\rfloor.
\tag{27}
$$

未来 token 在 region 中较早节点上的候选，可能改变同一时间对另一个节点的联合选择。因此，式 (27) 是 arbitrary selector 下比 $\max_{v\in\mathcal R_j}h(v)$ 更保守、也更安全的几何指标。

$h(j)>0$ 只表示 region 支持区间允许交错，不证明具体离散支持集合一定相交，更不证明一次具体输入必然产生汇合。

## 5. 消息不必属于唯一 token

### 5.1 同一时间纤维的可能 token 标签

定义：

$$
T(v,\theta)
=
\{t\in[L]\mid
\theta\in\mathsf{Supp}_t(v)\}.
\tag{28}
$$

若 $|T(v,\theta)|>1$，则不同 token 的空间传播波可以在同一个节点时间坐标汇合。实际是否同时产生消息仍由完整计算决定。

若存在两条到达 $v$ 的路径，时延分别为 $d_{\mathrm{long}}>d_{\mathrm{short}}$，并且：

$$
d_{\mathrm{long}}-d_{\mathrm{short}}=kD,
\tag{29}
$$

则 token $t$ 的长路径坐标与 token $t+k$ 的短路径坐标相同：

$$
Dt+d_{\mathrm{long}}
=
D(t+k)+d_{\mathrm{short}}.
\tag{30}
$$

这给出了跨度为 $k$ 的直接时间尺度汇合。

### 5.2 因果祖先集合

当一个非线性节点共同处理多个 token 的消息后，它的输出通常不能唯一拆成“属于各 token 的部分”。此时应记录依赖关系，而不是所有权。

把前置文档的函数作用事件图增加输入顶点 $e_t$，并在输入记录属于 $B_{s,Dt}$ 时加入：

$$
e_t\longrightarrow P_{s,Dt}.
$$

所得有向图仍称为增广事件图。对任意事件顶点 $\xi$，定义：

$$
\operatorname{Anc}(\xi)
=
\{t\in[L]\mid
e_t\leadsto\xi
\text{ 在增广事件图中成立}\}.
\tag{31}
$$

$T(v,\theta)$ 描述空间路径可以把哪些 token 带到一个坐标；$\operatorname{Anc}(\xi)$ 描述一个具体函数作用实际可能依赖哪些输入。selector-history 边和节点状态边会使后者比前者更大：较早输入可以经 $y_j^\theta$ 改变较晚时间的选择。

若外部输出记录 $z$ 由事件 $F_{v,\theta}$ 产生，定义：

$$
\operatorname{Anc}(z)
=
\operatorname{Anc}(F_{v,\theta}).
$$

若外部输出记录 $y_r$ 用于在自回归语义中预测位置 $r+1$，一个自然的 token 因果条件是：

$$
\operatorname{Anc}(y_r)
\subseteq
\{0,1,\ldots,r\}.
\tag{32}
$$

正边时延只保证逻辑时间沿消息边增加，并不自动推出式 (32)。

## 6. 执行 tile 与 backend 契约

### 6.1 tile 是函数作用事件的有限集合

固定一次完整计算的函数作用事件图 $\mathscr G_x^{\mathrm{ev}}$。一个**执行 tile**是有限集合：

$$
K\subseteq\mathscr V_x^{\mathrm{ev}}.
$$

在准备运行 $K$ 时，设已经完成的事件集合为 $\mathsf{Done}_K$。称 $K$ 的外部依赖已经满足，当且仅当：

$$
\{\xi\mid
\exists\zeta\in K:
(\xi,\zeta)\in\mathscr A_x^{\mathrm{ev}}
\}
\subseteq
\mathsf{Done}_K\cup K.
\tag{33}
$$

式 (33) 允许 tile 内部保留依赖；它只禁止 tile 读取一个既不在 tile 中、也尚未完成的事件。

seal 的作用是证明相关时间纤维已经固定。式 (33) 的作用是证明函数依赖已经就绪。这是两个不同条件。

### 6.2 精确联合求值

固定一个满足式 (33) 的 tile $K$。把它从边界状态与边界记录到全部应提交结果的参考递归记为全函数：

$$
\operatorname{Ref}_K:X_K\to Y_K.
$$

定义 $X_K$ 为 tile $K$ 的全部合法边界节点状态、边界 selector-history 与边界记录所成的集合，定义 $Y_K$ 为相应的应提交节点状态、selector-history、选择、逐坐标完整输出函数值、内部消息和外部输出所成的集合。$\operatorname{Ref}_K$ 内部仍严格遵守函数作用事件图的依赖顺序。

一个 backend tile witness 由函数：

$$
\operatorname{Pack}_K:
X_K\to W_{\mathrm{in}},
$$

$$
\mathcal K:W_{\mathrm{in}}\to W_{\mathrm{out}},
$$

$$
\operatorname{Unpack}_K:
W_{\mathrm{out}}\to Y_K
$$

组成，并要求：

$$
\operatorname{Unpack}_K
\left(
\mathcal K
\left(
\operatorname{Pack}_K(z)
\right)
\right)
=
\operatorname{Ref}_K(z)
\qquad(\forall z\in X_K).
\tag{34}
$$

式 (34) 不要求 tile 内部的事件数学上相互独立；它要求联合 backend 与完整参考递归给出同一结果。

### 6.3 外层执行循环

一个 seal 驱动的外层循环可以写成：

$$
\text{找到满足 seal 与式 (33) 的 }K
\longrightarrow
\operatorname{RunTile}(K)
\longrightarrow
\text{commit}
\longrightarrow
\text{publish}
\longrightarrow
\text{推进 seal}.
\tag{35}
$$

其中：

1. `RunTile` 使用式 (34) 的 witness；
2. `commit` 采用相应节点状态与 selector-history；
3. `publish` 把实际输出消息加入阶段集合 $H_n$；
4. 新 seal 只在前置文档式 (33) 的集合包含成立时推进。

> [!proposition] 命题 5：精确 tile 替换不改变完整结果
> 若一列两两不交的 tile 恰好覆盖全部函数作用事件，每个 tile 运行前满足式 (33)，每个 backend 满足式 (34)，并且所有节点状态与 selector-history 提交、消息公开都遵守前置文档的事件依赖，则用这些 tile 替换逐事件求值不会改变 $\mathcal T_x$。

**证明。** 函数作用事件图是有限 DAG。按其任一拓扑序归纳。一个 tile 的外部前驱已经与参考计算相同；式 (34) 因而使 tile 的全部输出与参考计算相同。提交和公开又只把这些相同结果交给后继。覆盖全部事件后，完整计算记录相同。$\square$

### 6.4 外层保块与节点级时间批暴露

只数 `RunTile` 调用没有意义：一次不透明的 `RunWholeGraph` 也可以包住全部逐事件递归。要表达“外层调度没有拆碎昂贵节点计算”，必须先固定一个**成本 profile**，即声明哪些函数作用属于本节要保护的昂贵作用。

本文采用的 profile 是：每个 $\operatorname{Full}_v$ 是昂贵作用；$\operatorname{Agg}_v$、$\operatorname{Upd}_v$、三类 $\operatorname{Read}_v$、$\operatorname{SelStep}_{j,C}$ 以及 seal、提交和公开 bookkeeping 归入控制作用。在这个计数中，控制作用不能免费复现或内联 $\operatorname{Full}_v$ 的求值。这是附加的成本约定，不是 TimedDAG 语义的结论。若某个模型把主要计算放在 $\operatorname{Upd}_v$ 中，就必须修改 profile，并重新证明相应的保块性质。

第 1.2 节为一次参考计算固定了输入长度 $L$；本节定义的是跨输入长度的计划族，因而不再固定某一个 $L$。固定完整 TimedDAG 规格、注入间距 $D$、region 划分和成本 profile，只让有限输入前缀、chunk 的起点 $q$ 与长度 $T$ 变化。对从位置 $q$ 开始的 chunk，记主时间块为：

$$
I_{q,T}
:=
[Dq,D(q+T)),
\qquad
I_T:=I_{q,T}\quad(q\text{ 固定}).
\tag{36}
$$

令 $\Omega_{q,T}$ 是全部可达合法实例的集合；一个 $\omega\in\Omega_{q,T}$ 由切面状态 $Q_{Dq}$、新公开的 $T$ 条输入记录以及推进到 $D(q+T)$ 的输入 seal 组成。它唯一确定参考计算在 $I_{q,T}$ 内的轨迹。对节点 $v$，定义其 active 时间坐标集合：

$$
\Lambda_v(I_{q,T};\omega)
=
\{\theta\in I_{q,T}\mid
v\in\mathcal A_{\rho(v),\theta}\}.
\tag{37}
$$

一个 **exact 外层计划**由 $L(q,T,\omega)$ 个依次执行的阶段组成。每个阶段先进行不含 $\operatorname{Full}$ 的合法控制求值，再对已经确定全部输入的坐标显式调用节点级 `BatchFull`；每个批次归属于一个阶段，调用时其中全部事件前驱都必须已经完成。本阶段的完整输出只在阶段结束时公开给后续阶段。

计划族必须由同一组调度规则给出。第 $r$ 阶段只能读取 $\omega$、先前阶段已经公开的结果，以及本阶段按事件依赖合法求出的控制值；不得查询尚未求出的参考 $\operatorname{Full}$ 值来选择批次。全部阶段合成后必须产生与参考语义相同的 $I_{q,T}$ 内记录和右切面 $Q_{D(q+T)}$；这包括在 $I_{q,T}$ 内发送、但到达时间越过右切面的在途消息。

对每个节点，这些显式调用把式 (37) 分成不交的非空批次 $K_{v,1},\ldots,K_{v,m_v(q,T,\omega)}$。若存在常数 $L_G$ 与 $C_{G,v}$，使每个 $q\in\mathbb N$、$T\in\mathbb N_{>0}$ 和 $\omega\in\Omega_{q,T}$ 都满足：

$$
\Lambda_v(I_{q,T};\omega)
=
\bigsqcup_{r=1}^{m_v(q,T,\omega)}K_{v,r},
\qquad
L(q,T,\omega)\le L_G,
\qquad
m_v(q,T,\omega)\le C_{G,v},
\tag{38}
$$

当 $\Lambda_v(I_{q,T};\omega)=\varnothing$ 时取 $m_v(q,T,\omega)=0$，并把式 (38) 右侧理解为空并。上述常数可以依赖固定 TimedDAG 规格、$D$、region 划分和成本 profile，但不依赖 $q,T$ 或 $\omega$。此外，要求每个批次都具有逐坐标精确的 witness：

$$
\operatorname{BatchFull}_{v,K}
\left(
\left(q_v^{\theta+1},\theta,h_{v,\theta}\right)_{\theta\in K}
\right)
=
\left(
\operatorname{Full}_v
\left(q_v^{\theta+1},\theta,h_{v,\theta}\right)
\right)_{\theta\in K},
\tag{39}
$$

其中元组按 $\theta$ 递增排列，则称这一计划族具有**节点级时间批暴露**。本文也把满足它的精确计划称为**控制顺序、计算整块的 exact prefill**。

这里“显式”是数学要求，不是物理 launch 要求。同一阶段的多个节点批次仍可融合进一次 packed API 或编译循环；witness 只需保留式 (38) 的批次分解，并在解包后满足式 (39)。

式 (38) 允许 selector、selector-history 与节点状态在每个大块内作 $\Theta(T)$ 长度的顺序控制扫描；它约束的是昂贵作用被外层拆成多少批，而不是控制 span。式 (39) 也只规定 backend 的函数值，不规定 batch kernel 内部算法。因而这个定义不声称 low span、work efficiency、设备利用率或实测加速。

这个定义也容纳“主体一批、薄边界若干批”的计划。固定图以后，若边界只需 $r_G$ 个 heavy/control 阶段，其中 $r_G$ 可以依赖 $h_\Delta$ 但不依赖 $T$，就在式 (38) 中把相应常数增大即可。真正不满足定义的是批次数或 heavy/control 阶段数随 $T$ 增长。

这个定义不能由一次不透明的 `RunWholeGraph` 见证：每个 $\operatorname{Full}$ 事件必须显式属于式 (38) 的某个节点批次；若存在反复的 $\operatorname{Full}\to\text{control}\to\operatorname{Full}$ 依赖，它必须表现为不同外层阶段，并计入 $L(q,T,\omega)$。

## 7. selector 为什么会改变合法 tile

### 7.1 selector 是同刻联合决策

在 region $j$ 与时间 $\theta$，前置文档定义：

$$
\mathcal C_{j,\theta}
=
\{v\in\mathcal R_j\mid
B_{v,\theta}\ne\varnothing\}.
\tag{40}
$$

同一选择作用还读取 $y_j^\theta$，并通过前置文档的 selector step 同时产生 $\mathcal A_{j,\theta}$ 与 $y_j^{\theta+1}$。

所有 $v\in\mathcal C_{j,\theta}$ 的准备作用都是 $S_{j,\theta}$ 的前驱。因而，一个包含 $S_{j,\theta}$ 的 tile 必须同时满足：

$$
\{P_{v,\theta}\mid
v\in\mathcal C_{j,\theta}
\}
\subseteq
\mathsf{Done}_K\cup K.
\tag{41}
$$

式 (41) 称为该 tile 在 $(j,\theta)$ 的 **selector closure**。region 首先是这种语义同步域，不是处理器并行分组或内存放置声明。

此外，$S_{j,\theta}$ 的前一个同区域选择作用必须已经完成或与它一同位于保持该依赖的 tile 内；tile 从中间时间开始时，则必须把左边界 history 作为 $X_K$ 的一部分。式 (41) 只写同刻候选 closure，不替代这条跨时间依赖。

### 7.2 一个不会产生真实联合候选的充分条件

如果：

$$
|\mathcal C_{j,\theta}|\le1
\qquad
(\forall j,\theta),
\tag{42}
$$

那么 selector 在每个时间至多读取一个候选节点。此时，即使一个 region 含有许多节点，也不会在同一时间产生跨节点竞争；同一个 region 的 selector-history 仍可把不同时刻的选择串联起来。

式 (42) 可以由互不相交的结构支持集保证。例如 16 节点链取 $\theta_{r,t}=16t+r$ 时，不同节点时间坐标具有不同的模 $16$ 余数，所以全局单 region 仍满足式 (42)。

相反，若取 $\theta_{r,t}=t+r$ 并把全部 block 放入一个 region，则稳定阶段同一 $\theta$ 可以同时包含：

$$
v_0\text{ 的 token }\theta,
\quad
v_1\text{ 的 token }\theta-1,
\quad\ldots
$$

全局 selector 会把多个拓扑层和多个 token 位置联合起来。一般不能先让 $v_0$ 完成整个 chunk，再让 $v_1$ 完成整个 chunk；合法顺序可能成为对角时间波前。

### 7.3 支持集感知的关闭条件

前置文档使用区域最小前沿：

$$
\lambda_n(\mathcal R_j)
=
\min_{v\in\mathcal R_j}\lambda_n(v).
$$

它是正确但可能保守的统一下界。如果完整有限输入的结构支持集已经由式 (7) 给定，则固定 $(j,\theta)$ 的候选集合还可以使用以下逐坐标充分条件：

$$
\forall v\in\mathcal R_j,
\qquad
\theta\notin\mathsf{Supp}(v)
\quad\text{或}\quad
\lambda_n(v)>\theta.
\tag{43}
$$

若第一种情形成立，引理 1 排除该节点在 $\theta$ 成为候选；若第二种情形成立，前置文档的纤维关闭引理固定其完整时间纤维。因此式 (43) 足以固定 $\mathcal C_{j,\theta}$。

式 (43) 只改进关闭证明，不自动证明跨多个 $\theta$ 的 selector 可以联合求值，也不证明当前 $y_j^\theta$ 已经就绪。

## 8. 区域商图与严格分层 region

### 8.1 区域商图

重新写出前置文档的区域商图边集：

$$
Q_\rho
=
\{(j,j')\in J\times J
\mid
j\ne j',
\ \exists a\in A:
\rho(\operatorname{src}(a))=j,
\rho(\operatorname{dst}(a))=j'
\}.
\tag{44}
$$

它把每个 region 收缩成一个点，只保留跨 region 边。

原图是 DAG，并不保证 $(J,Q_\rho)$ 是 DAG。例如：

$$
v_0\to v_1\to v_2,
$$

若 $v_0,v_2\in\mathcal R_A$ 而 $v_1\in\mathcal R_B$，则商图同时含有：

$$
A\to B,
\qquad
B\to A.
$$

原图没有返回 $v_0$；收缩只是把后面的 $v_2$ 与前面的 $v_0$ 识别成同一个区域点。

### 8.2 为什么式 (44) 不含自环

式 (44) 明确要求 $j\ne j'$。因此，一条 region 内部边：

$$
u\to v,
\qquad
\rho(u)=\rho(v)=j
$$

不会在 $Q_\rho$ 中产生 $(j,j)$。

若另定义保留对角边的关系：

$$
\widehat Q_\rho
=
\{(
\rho(\operatorname{src}(a)),
\rho(\operatorname{dst}(a))
)
\mid a\in A\},
\tag{45}
$$

那么 region 内部边确实会变成长度为 $1$ 的自环。但原图中的 $u\to v$ 并不是计算循环；它只是被收缩隐藏的内部依赖。因此，正文继续把“region 内无边”和“跨 region 商图无环”作为两个不同性质。

### 8.3 严格分层条件

称 region 划分是**严格分层的**，当且仅当存在函数：

$$
\ell:J\to\mathbb N
$$

使每条空间边 $a\in A$ 都满足：

$$
\ell(\rho(\operatorname{src}(a)))
<
\ell(\rho(\operatorname{dst}(a))).
\tag{46}
$$

> [!proposition] 命题 6：严格分层的等价刻画
> 式 (46) 成立，当且仅当同时满足：
>
> 1. region 内没有空间边；
> 2. 区域商图 $(J,Q_\rho)$ 是 DAG。

**证明。** 若式 (46) 成立，一条 region 内部边会要求 $\ell(j)<\ell(j)$，不可能存在。任意商图边都严格增加 $\ell$，所以商图不能含有有向环。

反之，若 region 内无边且 $(J,Q_\rho)$ 是有限 DAG，取商图的任一拓扑序，并令 $\ell(j)$ 为 $j$ 在该顺序中的位置。每条原图边都是跨 region 边，因而严格增加 $\ell$。$\square$

严格分层时，同一 region 中的两个节点之间不存在有向路径：路径上的每条边都严格增加 $\ell$，不可能从 $j$ 出发又回到 $j$。所以每个 region 是空间可达偏序中的一个反链。

region 私有的 selector-history 只连接同一 $j$ 的不同逻辑时间，不向 $Q_\rho$ 增加空间边，所以式 (46) 不需因它而加强。若以后允许多个 region 共享可变 history，就必须另行定义控制依赖图，并重新检查它与 $Q_\rho$ 的并图；当前模型不含这种共享。

若所有节点都属于同一个 region，式 (46) 只有在 $A=\varnothing$ 时才能成立。因此，全局单 selector 的非平凡链不属于这个充分条件所定义的类；它仍可能因式 (42) 等其他结构而可批量化。

## 9. 严格分层类的通用分块算法

### 9.1 region 时间块的参考求值器

固定严格分层函数 $\ell$，以及一个逻辑时间半开区间：

$$
I=[b,c).
$$

对 region $j$，假设已经给定：

1. 每个 $v\in\mathcal R_j$ 在时间 $b$ 的状态 $q_v^b$；
2. region 在时间 $b$ 的 selector-history $y_j^b$；
3. 全部 $B_{v,\theta}$，其中 $v\in\mathcal R_j$ 且 $\theta\in I$；
4. 所有从切面左侧跨入 $I$ 的内部消息。

定义 $\mathsf{TileIn}_{j,I}$ 为所有满足上述四项条件的合法边界数据所成的集合。定义 $\mathsf{TileOut}_{j,I}$ 为相应 active sets、区间内的完整节点状态与 selector-history 序列、逐坐标完整输出函数值、内部消息和外部输出所成的集合；其中状态序列包括左边界以后直至时间 $c$ 的全部坐标。定义全函数：

$$
\operatorname{RefRegionTile}_{j,I}:
\mathsf{TileIn}_{j,I}\to\mathsf{TileOut}_{j,I},
$$

其函数值由下列递归给出：按 $\theta=b,b+1,\ldots,c-1$，对该 region 应用前置文档的聚合、候选状态、描述量、selector step、状态采用和完整输出规则。空纤维保持节点状态与 selector-history 不变。

一个实现函数：

$$
\operatorname{RunRegionTile}_{j,I}:
\mathsf{TileIn}_{j,I}\to\mathsf{TileOut}_{j,I}
$$

是精确的，当且仅当它与 $\operatorname{RefRegionTile}_{j,I}$ 是同一个函数。换言之，它对所有合法输入都产生相同的：

- active sets；
- $(q_v^\theta)_{v\in\mathcal R_j,\ \theta\in[b,c+1)}$；
- $(y_j^\theta)_{\theta\in[b,c+1)}$；
- 每个 active 坐标的完整输出函数值；
- 内部消息；
- 外部输出。

这就是式 (34) 在一个 region 时间块上的具体化。

### 9.2 算法

设本轮需要从完整切面 $b$ 推进到完整切面 $c>b$。选择 region 顺序：

$$
j_1,\ldots,j_m
$$

使：

$$
\ell(j_1)\le\cdots\le\ell(j_m).
$$

若两个 region 具有相同 $\ell$，式 (46) 保证二者之间没有空间边，可以任意排列。

依次对 $r=1,\ldots,m$ 执行：

1. 收集 $\mathcal R_{j_r}$ 在 $[b,c)$ 的外部输入、跨切面消息和来自已完成 region 的消息；
2. 用 seal 证明这些时间纤维完整；
3. 调用一次 $\operatorname{RunRegionTile}_{j_r,[b,c)}$；
4. 提交 region 中所有节点的新状态与 region 的新 selector-history；
5. 公开发往后续 region 的消息，并推进相应边 seal。

全部 region 完成后，保存 $Q_c$。

> [!theorem] 定理 7：严格分层 region 的一次扫描定理
> 假设：
>
> 1. region 划分满足式 (46)；
> 2. 含 $(q_v^b)_{v\in V}$ 与 $(y_j^b)_{j\in J}$ 的切面 $b$ 已经完成，$c>b$ 是本轮目标切面，并且所有时间小于 $c$ 的外部输入都已经被 seal；
> 3. 每个 $\operatorname{RunRegionTile}_{j,[b,c)}$ 都满足精确性契约，并公开它产生的全部实际消息。
>
> 则第 9.2 节的算法与前置文档在 $[b,c)$ 上的直接语义相同，而且每个 region 在本轮恰好调用一次。

**证明。** 对 region 顺序归纳。

考虑当前 region $j_r$。由式 (46)，进入 $j_r$ 的任意空间边只能来自 $\ell$ 更小的 region。因此，到达 $[b,c)$ 的消息要么已经属于切面 $b$ 保存的跨界消息，要么由此前已经运行的 region tile 产生。region 内没有空间边，所以当前 region 的完整输出不会反过来增加本 region 的任何时间纤维。来自 $\ell$ 更大 region 的边也不存在。

此前 region 已经完成所有发送时间小于 $c$ 的作用，并公开相应实际消息，所以其出边 seal 可以推进到至少 $c$。结合已经给定的外部输入 seal，当前 region 在整个 $[b,c)$ 上的全部时间纤维可以在一次调用前固定。当前 region 的 selector-history 只按逻辑时间在本 region 内递推；它不增加任何输入纤维。精确性契约保证该调用产生与参考规则相同的选择、节点状态、selector-history 和输出。它的所有跨 region 输出只流向后续 region，不要求重新访问已经完成的 region。

归纳到 $j_m$ 后，区间中的节点状态、selector-history 和输出都与直接语义相同。前置文档的切面继续定理再给出相同的 $Q_c$。$\square$

### 9.3 chunk prefill 推论

对输入 chunk $q,\ldots,q+T-1$，在定理 7 中取：

$$
b=Dq,
\qquad
c=D(q+T).
\tag{47}
$$

由定理 4，这两个标量切面对未来输入扩展安全。固定空间图后，本轮外层 region tile 调用数量恰为 $|J|$，不随 $T$ 增长；每个非平凡 region tile 的时间宽度为 $DT$。

若这是有限输入的最后一个 chunk，则式 (22) 给出有限尾部。可以再按同一 region 顺序执行一次 drain。若 $\Delta_{\max}=kD$，尾部的逻辑时间尺度至多为 $k$ 个 token 间距。于是，大 chunk 的保守边界比例具有尺度：

$$
\frac{k}{T}.
\tag{48}
$$

式 (48) 是 tile 边界的比例，不是总算术工作量的加速比。

### 9.4 严格分层类的节点级时间批暴露

严格分层消除了 region 内消息反馈，但节点状态与 selector-history 仍可能跨时间递归。特别是，时间 $\theta+1$ 的 selector 输入可以经 $q_v^{\theta+1}$ 或 $y_j^{\theta+1}$ 依赖时间 $\theta$ 的选择结果。因此，定理 7 保证一次区域扫描，却不保证区域内部具有与 $T$ 无关的并行深度。

不过，当前语义给出下列两阶段求值次序。对固定 region，先按 $\theta$ 扫描控制作用：

$$
\left(
(B_{v,\theta})_{v\in\mathcal R_j},
(q_v^\theta)_{v\in\mathcal R_j},
y_j^\theta
\right)
\longmapsto
\left(
(h_{v,\theta},\widetilde q_{v,\theta},d_{v,\theta})_
{v\in\mathcal C_{j,\theta}},
\mathcal A_{j,\theta},
(q_v^{\theta+1})_{v\in\mathcal R_j},
y_j^{\theta+1}
\right).
$$

这一步不必先应用任何 $\operatorname{Full}_v$：前置文档式 (14) 的 selector step 不读取完整输出，而式 (46) 既排除了 region 内消息边，也使当前 region 的输出只流向严格更后层。扫描结束后，每个 active 完整输出作用的 $(q_v^{\theta+1},\theta,h_{v,\theta})$ 都已经确定，可以按节点收集后交给式 (39) 的 batch backend。

> [!corollary] 推论 8：严格分层类的节点级时间批暴露
> 在定理 7 的条件下，再假设每个节点对任意合法有限坐标集都有满足式 (39) 的精确 batch witness。则第 9.2 节的算法在主时间块 $I_T$ 上具有节点级时间批暴露，并可取：
>
> $$
> L(q,T,\omega)=L_G=|J|,
> \qquad
> m_v(q,T,\omega)\le C_{G,v}=1
> \quad(v\in V).
> \tag{49}
> $$

**证明。** 按严格层次依次处理 region，并把每个 region 作为一个外层阶段。进入当前 region 的时间纤维已经由切面或较早 region 固定；上面的顺序控制扫描不调用 $\operatorname{Full}$，所以它先确定该 region 中所有节点的全部 batch 输入。对每个节点 $v$，若 $\Lambda_v(I_{q,T};\omega)$ 非空，就令唯一批次 $K_{v,1}=\Lambda_v(I_{q,T};\omega)$；若为空，则不调用。控制记录与参考递归相同，式 (39) 又给出逐坐标相同的完整输出，故该构造本身满足精确 region-tile 契约；再应用定理 7，所有阶段合成后也精确。因此式 (49) 成立。$\square$

这里的批次按**逻辑时间坐标**组成，而不按 token 身份组成。即使多个 token 的信号在某个 $h_{v,\theta}$ 中汇合，$\theta$ 仍只是 $\Lambda_v(I_{q,T};\omega)$ 的一个元素，不会单独迫使批次拆分。第 4.4 节的“主体约为 $T-h_\Delta$、边界约为 $h_\Delta$”描述的是时间切面附近的几何厚度，不是两个互相独立的 token 子问题。

若有限输入的 drain 被单列为第二个时间块，同一论证允许每个节点再增加至多一个批次；对主时间块与 drain 的联合计划重新计数时，每个节点至多两批。selector-history 的控制扫描仍可具有 $\Theta(T)$ span，而不违反推论 8；低 span 与 batch kernel 的实际性能仍需另证。

## 10. 典型拓扑

### 10.1 串行 Transformer block

把每个 block 作为一个节点，并让每个节点单独构成一个 region。region 内自然无边，区域商图就是原链，所以式 (46) 成立。

普通 Transformer 可以把每个 $Y_j$ 取为单点集，或让 selector-history 不改变 always-active 选择；这样新增坐标不会改变通常的 chunk prefill。

若节点 backend 已经证明 causal attention、SSM 或 FFN 的 chunk 求值与逐 token 语义相同，则定理 7 的 region 顺序就是普通 block 顺序：

$$
\text{block }0\text{ 的整个 chunk}
\to
\text{block }1\text{ 的整个 chunk}
\to\cdots.
$$

链的空间深度决定顺序 region 数量；它不迫使每个 block 把 token 维拆成单元素调用。

### 10.2 MoE 层

可以把同一 MoE 层的全部专家放入一个 region，并要求专家之间没有空间边。前一 region 的 router 或输入节点产生候选描述，当前 selector 在每个时间选择 active experts。

selector-history 可以保存各专家的饱和计数或固定精度移动平均负载，并让后续选择读取这些数值。对一个完整时间块，先沿时间扫描 history 并求出 active sets。对专家 $e$ 定义其 active 坐标集合：

$$
T_e
=
\{\theta\in[b,c)
\mid
e\in\mathcal A_{\rho(e),\theta}\}.
\tag{50}
$$

随后把 $T_e$ 对应的输入打包交给 expert tile。式 (50) 允许不同专家获得不同大小的批次；算法存在性不保证每个 $T_e$ 都足够大，也不保证负载均衡。history 扫描顺序执行并不要求把昂贵 expert 计算也拆成逐时间调用。

### 10.3 真正的 graded DAG

空间图可以有分支、跳边和重新汇合，而不必是一条链。只要式 (14) 成立，到达同一节点的所有路径总时延仍相同。此时节点边界式 (16) 允许整个 token chunk 沿拓扑序推进。

若一条跳边跨过多个层级，它的 $\delta$ 必须等于所跨秩差。把所有边机械地设成 $1$，一般会破坏 graded 性质。

### 10.4 非 graded 的重新汇合 DAG

若同一节点存在不同总时延路径，式 (29) 可能成立。此时不能坚持每个节点事件具有唯一 token 标签，但定理 4 仍给出标量时间块，定理 7 仍可用于严格分层 region。

这种执行更接近一个有固定边界状态的时间流水：每个新 chunk 推进一个宽度为 $DT$ 的时间 slab，较早 token 的慢路径尾部在后续 slab 中继续。

### 10.5 奇偶 region

对链：

$$
v_0\to v_1\to v_2\to v_3,
$$

若：

$$
\mathcal R_A=\{v_0,v_2\},
\qquad
\mathcal R_B=\{v_1,v_3\},
$$

则区域商图含 $A\to B\to A$。它不满足式 (46)。若坚持以完整 region 为执行 tile，就必须在 $A,B$ 间交替，或者把二者融合成一个执行 supertile。

这不表示该 TimedDAG 必然没有任何保块实现。若实际支持时间互不重合，式 (43) 可能恢复更细的节点 tile。严格分层只是一个容易验证的充分条件。

### 10.6 所有节点共用一个 selector

此时 $J$ 只有一个元素，区域商图没有跨区域边，因而平凡无环。但这没有说明 region 内部能否批量化。

若式 (42) 成立，全局 selector 每次至多处理一个候选，但共享的 selector-history 仍会把不同时刻串联起来；只有这种依赖可由一次 tile 内扫描承接时，它才可能不妨碍节点 chunk。若许多拓扑层在同一时间成为候选，全局 selector 还会形成跨节点屏障，节点级整块顺序一般不再成立。

这说明：

$$
\text{区域商图无环}
\nRightarrow
\text{节点级时间批暴露}.
\tag{51}
$$

### 10.7 商图强连通分量

在有限有向图中，若从顶点 $j$ 有路径到 $j'$，并且从 $j'$ 也有路径回到 $j$，则称二者互相可达。一个**强连通分量**是一个按包含关系极大的非空顶点集合，其中任意两个顶点都互相可达。

若区域商图有环，可以把每个强连通分量收缩成一个执行 supertile。以这些分量为顶点、保留分量间有向边所得的图称为**凝聚图**。凝聚图总是 DAG：否则，凝聚图中的一个有向环会证明环上多个分量彼此可达，与每个分量已经极大矛盾。

这种收缩只给出空间上的 DAG。要由此证明节点级时间批暴露，还必须分别证明：每个 supertile 内的 heavy/control 阶段数有界，并且每个节点的昂贵时间事件只需有界批次。分量规模小可能帮助构造这种 witness，但不能单独推出它；分量内部仍可能随 $T$ 反复出现 heavy--control 反馈。

若一个强连通分量覆盖大部分 region，融合依然在数学上合法；但“调用一个 supertile”已经接近调用全图，更不能单靠一次外层调用声称保块或高性能。

### 10.8 工具返回形成的大输入块

设模型在一次工具调用后同时得到 $T$ 个新的已知 token。公开这些记录并给出相应输入 seal，会把安全标量切面一次推进 $DT$。在严格分层类中，定理 7 因而允许每个 region 处理一个宽度为 $DT$ 的时间 tile，而不是进行 $T$ 轮全图调用。

若随后立即进入自回归 decode，还需先完成生成下一 token 所必需的尾部事件，或者在模型定义中给出明确的 prefill--decode 边界状态。这个 drain 的空间传播尺度由式 (23) 保守控制。若 $h_\Delta\ll T$，边界成本相对于工具返回主体较小；但任何用于生成下一 token 的输出仍必须满足式 (32)。

## 11. 多时间尺度交互及其边界

### 11.1 可能的结构优势

式 (29) 表示路径时延差可以直接编码 token lag。若一个节点同时具有短、中、长多组路径，它可以在同一时间纤维或连续状态更新中接触多个时间尺度。

这可能形成：

1. 对近期输入的短路径响应；
2. 对较早输入的长路径记忆；
3. 稀疏而固定的长程 token 交互；
4. 对具有不同输入速率的多个流进行汇合。

这些只是由结构支持的建模可能性，不是精度、可训练性或 scaling 优势定理。

### 11.2 需要单独检查的风险

允许交错以后，至少要检查：

1. **token 因果性**：式 (32) 是否对所有自回归输出成立；
2. **训练与 decode 一致性**：训练时是否使用了在线生成时尚不存在的输入；
3. **来源可辨识性**：$\operatorname{Agg}_v$ 是否保留了需要的边、端口或时间信息；
4. **状态稳定性**：不同时间尺度是否造成不可控制的状态增长或梯度路径；
5. **边界成本**：$W_b$ 的大小、drain 延迟和 halo 是否可接受；
6. **selector 负载**：active 坐标是否足以形成有用批次；
7. **history 闭环**：负载反馈是否稳定，history 的表示与更新时间是否保持有界。

TimedDAG 语义允许这些结构，但不替模型设计或训练实验回答上述问题。

## 12. 结论边界

本文已经得到的正向结论可以按强度排列为：

1. **任意正时延 TimedDAG**：定理 4 给出安全标量输入切面，前置文档给出包含节点状态、selector-history 与在途消息的精确 continuation。
2. **路径时延跨度有界**：式 (23)--(27) 给出 chunk 边界厚度的结构尺度。
3. **graded DAG**：引理 3 给出节点级 token 对齐切面。
4. **严格分层 region**：定理 7 给出每个时间块只扫描一次所有 region 的算法。
5. **带节点 batch witness 的严格分层 region**：推论 8 给出 $L_G=|J|$、$C_{G,v}=1$ 的节点级时间批暴露；命题 5 保证精确 tile 替换不改变完整语义。

本文没有证明：

1. 所有 TimedDAG 都具有节点级时间批暴露；
2. 区域商图无环单独足以推出节点级时间批暴露；
3. 任意 selector、selector-history 或节点状态递归都可以低深度并行；
4. $T-h$ 可以被解释成一个与后 $h$ 个 token 完全分离的 token 子问题；
5. tile 数量少自动表示实际运行时间短；
6. 多时间尺度汇合一定有利于训练或模型效果。

把本文核心结论压缩成一个式子，是：

$$
\boxed{
\begin{array}{c}
\text{seal 固定输入}
+
\text{严格分层 region}
\\[1mm]
+
\text{精确节点 BatchFull witness}
\\[1mm]
\Longrightarrow
\text{节点级时间批暴露：}L_G=|J|,\ C_{G,v}=1.
\end{array}
}
\tag{52}
$$

路径交错不改变式 (52)；式 (23) 的边界厚度只控制主时间块以外还要 drain 多宽。

## 13. 建议练习

1. 对两路径时延集合 $\mathcal D(v)=\{5,20\}$ 和 $D=5$，写出 token $0,1,2,3$ 的四个 $\mathsf{Supp}_t(v)$，找出全部同刻汇合。
2. 对 16 节点单位时延链，分别取 $D=1$ 与 $D=16$，计算 $w(v_r)$、$h(v_r)$ 和 $\Delta_{\max}$。
3. 把链 $v_0\to\cdots\to v_5$ 分成连续 region 与奇偶 region，分别写出 $Q_\rho$。
4. 给定一个严格分层函数 $\ell$，证明同一 region 中不存在两个互相可达的不同节点。
5. 对一个长度 $T$ 的输入，在纸上写出 $Q_{DT}$ 中必须保留的节点状态、selector-history 与跨界消息；解释为什么不能只保存最后一个节点的状态。
6. 构造一个所有节点共用 selector、但满足式 (42) 的例子；再构造一个不满足式 (42) 并迫使对角时间波前的例子。
7. 为一个两专家 MoE region 写出累计激活次数 history，手算式 (50) 的两个 active 坐标集合；说明为何可以先完成 history 扫描，再按专家批量应用 $\operatorname{Full}$。
8. 给出一个满足式 (29) 的两路径 DAG，并检查某个自回归输出是否满足式 (32)。

---

## 附录 S：系统语言与本文数学对象的对应

> [!info]- S.1　input chunk 与逻辑时间块
> `input chunk` 是一批新公开的外部输入记录。对式 (1) 的 token $q,\ldots,q+T-1$，它把安全输入切面从 $Dq$ 推进到 $D(q+T)$。
>
> `logical-time tile` 是式 (20) 的逻辑时间区间及其包含的函数作用事件。它可能含有多个 token 的混合消息，不等于输入 token 集合。

> [!info]- S.2　prefill 与 streaming
> 本文中的 `prefill` 表示把许多已经给定的输入位置联合交给一个精确 tile backend。
>
> `streaming` 表示随着输入 seal 前进，反复完成新的逻辑时间前缀。允许 streaming 不表示必须逐 token 调用节点；每次 seal 可以推进一个大时间块。

> [!info]- S.3　halo、tail 与 drain
> `halo` 或 `boundary band` 对应主切面附近尚未与未来输入完全分离的时间坐标和在途消息。它不是一组可以从计算中删除的 token。
>
> `tail` 是有限输入最后一个主切面以后的剩余事件。`drain` 表示输入已经声明结束后，把这些剩余事件推进到完整终点。

> [!info]- S.4　tile、kernel 与 launch
> `tile` 对应式 (33) 的有限事件集合及其边界输入；边界状态同时包括节点状态与 selector-history。`kernel` 对应式 (34) 中的联合函数 $\mathcal K$。`launch count` 是实现实际发起多少次这样的函数调用。
>
> 第 6.4 节的 $L(q,T,\omega)$ 数 heavy/control 阶段，$m_v(q,T,\omega)$ 数显式节点批次；二者都不必等于物理 launch 数，因为多个批次可以融合。少量 launch 不等于少量算术工作；整个参考递归若被隐藏进一次全图调用，launch count 就不再是有意义的性能指标。

> [!info]- S.5　region、selector 与 placement
> `region` 对应 $\rho$ 的一个纤维 $\mathcal R_j$。`selector` 对应固定时间上式 (40) 的完整候选集合及旧 history 上的函数；`selector-history` 对应 $y_j^\theta$，不是任一节点的 $q_v^\theta$。
>
> region 不是设备、线程组、并行域或内存位置。实现可以让一个 region 跨设备，也可以把多个 region 放在同一设备；若要讨论局部性，必须另给 placement 与成本模型。

> [!info]- S.6　ready 与 selector closure
> 一个 tile 的输入纤维已被 seal，并且满足式 (33) 的外部依赖条件时，可以称它为 `ready`。若 tile 含区域选择作用，还必须满足式 (41) 的 selector closure。
>
> “某节点当前有输入”不足以证明 selector ready，因为同一区域、同一时间仍可能出现尚未公开的其他候选节点；当前 selector-history 也必须由左边界或前一选择作用确定。

> [!info]- S.7　state 与 selector-history scan
> `state scan` 表示按时间组合节点状态或 selector-history 转移。若转移具有结合的函数复合表示，可以采用 parallel scan；若没有这种结构，`RunRegionTile` 内部可能仍需顺序处理状态。
>
> 本文的大块调度定理不把任意状态递归自动视为可并行 scan。

> [!info]- S.8　pipeline latency 与 throughput
> 路径时延和 halo 会增加一个输入位置到完整输出之间的 pipeline latency。大时间 tile 可以同时保持较高 steady-state throughput。这两个量不能互相替代。

> [!info]- S.9　causal leakage
> `causal leakage` 在本文中表示某个用于预测位置 $r+1$ 的输出违反式 (32)，即它在增广事件图中依赖了位置大于 $r$ 的输入。逻辑时间递增本身不能排除这种 token 次序泄漏。

> [!info]- S.10　高性能通用 prefill
> 本文的 `高性能通用 prefill` 正式对应第 6.4 节相对于已声明成本 profile 的**节点级时间批暴露**；`通用` 只针对明示的结构类和 backend 契约。“控制顺序、计算整块”是同一性质的直白说法。
>
> 严格分层类由推论 8 给出 $L_G=|J|$ 与 $C_{G,v}=1$。该术语允许 selector-history 顺序扫描，也不等于 low-span、work-efficient、设备高利用率或端到端加速。
