---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-11
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
> 本文只以 [[timed-dag-region-selector-learning-note|《带区域选择的 TimedDAG：从零开始的数学定义》]] 为前置。前置文档定义的节点、边、正时延、输入记录、时间纤维、节点状态、区域、selector-history、selector、完整计算、阶段化暴露轨迹、seal、事件图与切面状态，在本文中直接使用。
>
> 本文研究一个比“能否正确执行”更窄的问题：哪些 TimedDAG 结构允许一个统一外层执行器把连续输入按大时间块交给节点或区域，而不被空间依赖强迫退化为逐 token、逐事件调用。

> [!warning] “高性能”的本文含义
> 本文只把**外层没有拆碎昂贵节点事件**形式化。第 6.4 节将它定义为“节点级时间批暴露”：固定架构模板以后，每个节点的昂贵时间事件只被分成数量不随 chunk 长度增长的批次，昂贵计算与控制之间也只有数量不随 chunk 长度增长的外层阶段。本文不从这个性质推出硬件耗时、算术工作量、显存访问效率或 selector 的并行深度。
>
> 若允许把任意有限计算封装成一个 `RunWholeGraph` 调用，那么每个有限 TimedDAG 都可以被表面上写成“一次调用”。为避免这个说法失去内容，本文始终区分：
>
> 1. seal 是否已经固定 tile 的全部输入；
> 2. 拓扑是否允许把整个 tile 一次交给某个区域；
> 3. backend 是否另行给出了保持语义的联合求值实现。
>
> 此处的 `chunk`、`tile`、`backend` 与 heavy/control 只是导读用语；第 6.1--6.4 节再给出相应的数学对象。

> [!tip] 分三次阅读
> 第一次读第 1--4 节，理解“不交错不是大块 prefill 的必要条件”。第二次读第 5--8 节，理解 selector 为什么会改变合法 tile，以及严格分层 region 如何恢复区域拓扑扫描。第三次读第 9--12 节，研究 Transformer、MoE、混合 token 纤维与结论边界。

本文的主要结论是：

1. 任意正时延 TimedDAG 都有按完整逻辑时间切面继续的正确算法；这不自动给出大块执行。
2. 路径时延不交错只给出按 token 对齐的节点坐标；合法 tile 还必须收齐同刻 selector 的全部输入，并保持跨时间 history 依赖。
3. 路径时延交错时，仍可使用按逻辑时间对齐的 tile；必须保存跨切面的在途消息。
4. 若 region 内没有空间边，且所有跨 region 边服从一个严格区域次序，则每个封闭时间块可以按区域次序扫描，每个 region 只访问一次。
5. 在严格分层类中，selector-history 可以在一次 region tile 内顺序扫描；若节点另有对明示 Full 解释类一致的精确 batch witness，随后仍可按节点一次批量应用主时间块中的全部昂贵完整输出函数。这满足第 6.4 节的节点级时间批暴露，但不自动给出低 span。
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

结合式 (10) 与正边时延，可以得到：

$$
D\ge\Delta_{\max}
\Longrightarrow
D>w(v)
\qquad(\forall v\in V).
\tag{13}
$$

事实上，$w(s)=0$。若存在 $v\ne s$，则正边时延给出 $d_{\min}(v)\ge1$，同时 $\Delta_{\max}\ge1$，所以对每个这样的 $v$：

$$
w(v)\le \Delta_{\max}-1.
$$

再用 $D>0$ 即得式 (13)。它是强充分条件，不是必要条件；即使 $D<\Delta_{\max}$，仍可能对每个节点都有 $D>w(v)$。

命题 2 只固定节点输入坐标的几何次序。若同一 selector 在一个时间还联合其他节点，则执行仍需收齐这些节点的同刻输入，并延续此前的 selector-history；第 7 节再把这两项写成 tile 条件。不交错本身不消除这种跨节点依赖。

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

式 (16) 要成为整个函数作用事件的执行切面，还需 selector 与这些节点边界相容：同一个 $S_{j,\theta}$ 所需的全部准备作用必须一起就绪，跨 tile 的 selector-history 也必须从左边界开始按时间次序延续。graded 性质只对齐消息支持坐标，不自动给出这两项相容性；第 7.1 节再给出正式条件。

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
>
> 此外，二者在右边界具有相同的：
> $$
> (q_v^{Dq})_{v\in V},
> \qquad
> (y_j^{Dq})_{j\in J},
> \qquad
> W_{Dq}.
> $$

**证明。** 对 $\theta=0,1,\ldots,Dq-1$ 作归纳。

两次计算来自同一个固定规格，所以初始节点状态 $(q_v^0)_{v\in V}$ 与初始 selector-history $(y_j^0)_{j\in J}$ 相同。

在时间 $\theta$，两个输入包含相同的外部记录，因为所有新增 token 的输入时间都不小于 $Dq$。到达时间 $\theta$ 的任意内部消息都由更小逻辑时间的完整输出作用产生，这是 $\delta(a)>0$ 的结果。归纳假设保证这些作用及其消息相同，所以全部 $B_{v,\theta}$ 相同。

随后，前置文档式 (22)--(28) 中的聚合、候选状态、描述量、选择、状态采用和完整输出都是固定函数。相同的旧节点状态、旧 selector-history 与时间纤维产生相同的 active set、新历史及其余结果。归纳完成。时间 $Dq$ 的状态与历史由所有更小时间的作用确定；$W_{Dq}$ 也只收集发送时间小于 $Dq$ 的消息，所以三项边界数据同样相同。$\square$

定理 4 不要求路径不交错，也不要求区域商图无环。它只使用规则输入时间与正边时延。

当 $q=0$ 时，相应结论退化为初始的时间切面 $0$，不需要另作归纳。

### 4.2 通用标量切面

当 token $0,\ldots,q-1$ 已经公开时，定义：

$$
c_q=Dq.
\tag{18}
$$

定理 4 首先是一个关于完整计算的数学不变性：未来输入不能改变 $\theta<c_q$ 的计算或切面数据。若前 $q$ 个输入已经给定，而且输入 seal 证明时间 $c_q$ 以前不会再出现遗漏输入，那么 $c_q$ 才是执行器可以采用的安全**目标切面**。这仍不表示执行已经到达该切面；还必须实际完成其左侧的函数作用，并公开切面定义所需的结果。

完成这些条件以后，前置文档的切面状态：

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

才是一个对所有未来扩展都安全的 continuation 状态。

若下一次又公开 token $q,\ldots,q+T-1$，其中 $T\in\mathbb N_{>0}$ 且 $q+T\le L$，并给出相应输入 seal，则新的安全目标切面是：

$$
c_{q+T}=D(q+T).
$$

本轮目标逻辑时间块为：

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

定义可能到达坐标 $(v,\theta)$ 的 token 位置集合：

$$
\mathsf{Tok}(v,\theta)
=
\{t\in[L]\mid
\theta\in\mathsf{Supp}_t(v)\}.
\tag{28}
$$

若 $|\mathsf{Tok}(v,\theta)|>1$，则不同 token 的空间传播波可以在同一个节点时间坐标汇合。实际是否同时产生消息仍由完整计算决定。

若存在两条到达 $v$ 的路径，时延分别为 $d_{\mathrm{long}}>d_{\mathrm{short}}$，并且：

$$
d_{\mathrm{long}}-d_{\mathrm{short}}=kD,
\tag{29}
$$

其中 $k\in\mathbb N_{>0}$，且所讨论的位置满足 $t+k<L$，则 token $t$ 的长路径坐标与 token $t+k$ 的短路径坐标相同：

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

$\mathsf{Tok}(v,\theta)$ 描述空间路径可以把哪些 token 带到一个坐标；$\operatorname{Anc}(\xi)$ 描述一个具体函数作用实际可能依赖哪些输入。selector-history 边和节点状态边会使后者比前者更大：较早输入可以经 $y_j^\theta$ 改变较晚时间的选择。

若外部输出记录 $z$ 由事件 $F_{v,\theta}$ 产生，定义：

$$
\operatorname{Anc}(z)
=
\operatorname{Anc}(F_{v,\theta}).
$$

若外部输出记录 $z_r$ 用于在自回归语义中预测位置 $r+1$，一个自然的 token 因果条件是：

$$
\operatorname{Anc}(z_r)
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
\mathsf{Done}_K
\subseteq
\mathscr V_x^{\mathrm{ev}}\setminus K
$$

并且：

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

一个 backend tile witness 由两个集合 $W_{\mathrm{in}},W_{\mathrm{out}}$ 与三个函数：

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

若只固定一个具体的 $\operatorname{Full}$，再口头禁止控制逻辑重算它，这个禁止不可检验。下面把 $\operatorname{Full}$ 留成解释槽，并要求同一策略对一整个解释类成立；同时先统一不同输入长度的记录定义域。

为了同时讨论不同输入长度，先定义一个不含完整输出函数的公共骨架 $\mathfrak G^\circ$。它固定空间图、端口、region、状态与描述量集合、初值、$\operatorname{Upd}$、三类 $\operatorname{Read}$、$\operatorname{SelStep}$ 和注入间距 $D$。外部记录使用共同的环境集合：

$$
\mathsf{Ext}_\infty
=
\{(\mathrm{ext},i_\star,t,p)\mid
t\in\mathbb N,\ p\in P\},
$$

并规定这类记录的输入端口、位置、目标、时间和值分别为 $i_\star$、$t$、$s$、$Dt$ 和 $p$。令：

$$
\mathsf{Atom}_{\infty,v}
=
\{z\in\mathsf{Ext}_\infty\cup\mathsf{Msg}
\mid\operatorname{target}(z)=v\}.
$$

骨架为每个节点固定一个共同的全函数：

$$
\operatorname{Agg}_v^\infty:
\mathbb N\times
\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_{\infty,v})
\longrightarrow X_v.
$$

长度 $L$ 的实例取：

$$
\mathsf{Ext}^{(L)}
=
\{(\mathrm{ext},i_\star,t,p)\in\mathsf{Ext}_\infty
\mid t<L\},
$$

$$
\mathsf{Atom}_v^{(L)}
=
\mathsf{Atom}_{\infty,v}
\cap
(\mathsf{Ext}^{(L)}\cup\mathsf{Msg}),
$$

并取自然限制：

$$
\operatorname{Agg}_v^{(L)}
=
\left.
\operatorname{Agg}_v^\infty
\right|_{\mathbb N\times
\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v^{(L)})}.
$$

其余控制函数的定义域不依赖 $L$，直接由骨架固定。于是不同 $L$ 的输入记录都属于同一个 $\mathsf{Ext}_\infty$，切面状态都属于共同的环境集合：

$$
\mathsf Q_b
=
\{b\}\times
\prod_{v\in V}S_v\times
\prod_{j\in J}Y_j\times
\mathcal P_{\mathrm{fin}}(\mathsf{Msg}).
$$

记前置文档式 (12) 的共同值域为 $\mathcal O_v$。骨架留下的完整输出函数槽由一个非空解释类填入：

$$
\varnothing\ne\mathfrak F
\subseteq
\prod_{v\in V}
\{f\mid f:S_v\times\mathbb N\times X_v\to\mathcal O_v\}.
$$

对 $\Phi=(\Phi_v)_{v\in V}\in\mathfrak F$，写 $\operatorname{Full}_v^\Phi=\Phi_v$。$\mathfrak F$ 可以是全部类型正确的函数，也可以由事先写明的函数类约束限制，例如要求某些节点共享参数；它不能随当前输入或尚未公开的函数值改变。

若 $\mathfrak F$ 只有一个元素，“同一策略对所有解释成立”本身不能排除把这个解释硬编码进策略。下面的动作语法仍要求每个 Full 作用显式进入 batch；但凡依赖 black-box 不可区分性的反例或下界，还必须另外选取足够丰富且明确量化的 $\mathfrak F$。第 10.6 节将取全部类型正确的解释。

本文的成本 profile 是固定的二元组 $(\mathfrak G^\circ,\mathfrak F)$：$\operatorname{Full}^\Phi$ 属于昂贵作用，其余上述函数以及 seal、提交和公开 bookkeeping 属于控制作用。若主要计算位于 $\operatorname{Upd}_v$，就必须改换 profile。每个 $\Phi$ 都给出一份普通 TimedDAG 规格，但后文的调度策略与批次数上界必须对整个 $\mathfrak F$ 一致。

每个有限实例选择 $L\in\mathbb N_{>0}$ 与 $x:[L]\to P$，并由式 (1) 取 $\iota_L(t)=Dt$。对从位置 $q$ 开始的 chunk，记主时间块为：

$$
I_{q,T}
:=
[Dq,D(q+T)),
\qquad
I_T:=I_{q,T}\quad(q\text{ 固定}).
\tag{36}
$$

以下固定 $b=Dq$ 与 $c=D(q+T)$。对完整输入 $x$，令：

$$
E_x
=
\{(\mathrm{ext},i_\star,t,x(t))\mid t\in[L]\},
$$

$$
E_{x,<b}
=
\{e\in E_x\mid\operatorname{time}(e)<b\},
\qquad
E_{x,[b,c)}
=
\{e\in E_x\mid b\le\operatorname{time}(e)<c\}.
$$

对 $a\in\overline{\mathbb N}$，还记 $E_x(<a)=\{e\in E_x\mid\operatorname{time}(e)<a\}$。固定 $\Phi\in\mathfrak F$，用 $Q_b^\Phi(x)$ 表示输入 $x$ 在该解释下的切面状态，并把长度 $L$ 的合法可见实例正式定义为：

$$
\begin{aligned}
\Omega_{q,T}^{(L)}(\Phi)
=\{(Q,E,\sigma)\in{}&
\mathsf Q_b\times
\mathcal P_{\mathrm{fin}}(\mathsf{Ext}_\infty)
\times\overline{\mathbb N}
\mid{}\\
&\exists x:[L]\to P:\quad
Q=Q_b^\Phi(x),\quad
E=E_{x,[b,c)},\\
&\sigma\ge c,\quad
E_x(<\sigma)\subseteq E_{x,<b}\cup E
\}.
\end{aligned}
$$

这里 $\sigma$ 是单输入端口 seal；最后一个包含关系正是前置文档式 (33) 的单端口形式。定义普通并集：

$$
\Omega_{q,T}(\Phi)
=
\bigcup_{L\ge q+T}\Omega_{q,T}^{(L)}(\Phi).
$$

普通并集会把不同 $L$ 中相同的三元组 $(Q,E,\sigma)$ 识别为同一个元素。因此，$L$、见证输入 $x$ 和位置 $t\ge q+T$ 的未来记录都不是计划可以读取的自变量。

每个 $\omega=(Q,E,\sigma)\in\Omega_{q,T}(\Phi)$ 唯一确定 $[b,c)$ 内的参考记录和右切面。确实，按前置文档的切面继续规则从同一个 $Q$ 开始时，左侧跨界消息相同；由 $\sigma\ge c$ 与包含关系，区间内没有遗漏的外部记录。对 $\theta=b,\ldots,c-1$ 逐时归纳，正边时延保证当前消息只来自更小时间，而两个有限实例上的聚合函数都是同一个 $\operatorname{Agg}_v^\infty$ 的限制；其余函数和 $\Phi$ 也相同。因此两个见证 $L,x$ 给出相同的区间记录与右切面。这里不需要把定理 4 越过不同 $L$ 使用。

把这段唯一记录记为 $\operatorname{Ref}_{q,T}^\Phi(\omega)$。对节点 $v$，定义其 active 时间坐标集合：

$$
\Lambda_v(I_{q,T};\Phi,\omega)
=
\{\theta\in I_{q,T}\mid
v\in\mathcal A_{\rho(v),\theta}\}.
\tag{37}
$$

先定义阶段可以调用的节点接口。对 $\Phi\in\mathfrak F$ 与任意有限非空 $\Theta\subseteq\mathbb N$，令 $\mathsf{Adm}_{v,\Theta}^\Phi$ 为所有在 $\Phi$ 的某条合法完整轨迹中同时作为这些 active 坐标的 $\operatorname{Full}_v^\Phi$ 输入而出现的递增序列，其中 $\bar q_\theta\in S_v$、$h_\theta\in X_v$：

$$
\left((\bar q_\theta,\theta,h_\theta)\right)_{\theta\in\Theta}^{\uparrow}.
$$

一个**类级节点 batch 接口**是一族全函数：

$$
\operatorname{BatchFull}_{v,\Theta}^\Phi:
\mathsf{Adm}_{v,\Theta}^\Phi
\longrightarrow
\mathcal O_v^{\Theta}
\qquad(\Phi\in\mathfrak F).
$$

上标 $\Phi$ 只索引语义解释；策略调用的共同接口名不携带这个上标，也不会获知 $\Phi$。这类接口需要满足的逐坐标精确性条件在下文式 (39) 给出。

一个**外层阶段**先执行有限条因果合法的骨架控制作用 $\mathsf{Ctrl}_r$，再一次确定有限组节点调用 $\mathsf{Batch}_r$。每个调用坐标都必须已经被控制记录确定为 active，调用自变量必须是该作用已经确定的自变量，而且全部事件前驱必须已经由 $\omega$、较早阶段或 $\mathsf{Ctrl}_r$ 完成；不能用反事实输入探测 $\Phi$。调用开始后，本阶段不再求新的控制值；返回值连同调用标签记入 $\mathsf{Ans}_r$，只在阶段末一起公开。把完整阶段记录记为 $\pi_r=(\mathsf{Ctrl}_r,\mathsf{Batch}_r,\mathsf{Ans}_r)$。

这里的 $r$ 是 control-then-batch 屏障的编号，不是前置文档阶段化暴露模型的阶段秩 $n$。二者没有预设的一一对应关系；特别地，不能默认某个 $H_n$ 恰好等于第 $r$ 个外层阶段已经公开的消息。若要把计划精化成前置文档的阶段化暴露轨迹，必须另行给出满足单调性与 seal 条件的暴露阶段。

任一决策点的**可见 transcript**是元组：

$$
\mathsf{Tr}_{r,k}
=
\left(
q,T,
\omega,
(\mathsf{Ctrl}_s,\mathsf{Batch}_s,\mathsf{Ans}_s)_{s<r},
\mathsf{Ctrl}_{r,\le k}
\right).
$$

其中 $q,T$ 是本轮公开的 chunk 坐标，$\mathsf{Ctrl}_{r,\le k}$ 是本阶段迄今已经求出的控制作用及其值。除初始给定的 $\omega$ 外，运行中新出现的 $\Phi$ 相关原始信息只能作为某个 $\mathsf{Ans}_s$ 中已经记录的 $\operatorname{BatchFull}^\Phi$ 返回值进入 transcript；消息、状态等派生值只能由骨架函数从这些已记录值算出。transcript 不含 $L$、见证输入、未来输入、$\Phi$ 本身或尚未调用的 $\operatorname{Full}^\Phi$ 值。

一个**动作级因果策略** $\mathcal S$ 是从可见 transcript 到下一动作的确定函数；动作只能是应用一个输入已知的骨架控制函数、一次确定 $\mathsf{Batch}_r$ 并结束当前阶段，或在目标切面完成后停止。$\mathcal S$ 不以 $\Phi$ 为自变量。因此，即使两个 transcript 来自不同解释，只要它们相同，下一动作也必须相同。每个参考 $\operatorname{Full}^\Phi$ 作用必须恰好属于一次显式 batch 调用。

固定一组类级 batch 接口后，用 $\operatorname{Run}_{\mathcal S}^{\Phi}(q,T,\omega)$ 表示 $\mathcal S$ 在解释 $\Phi$ 下的运行；若它有限停止，用 $\operatorname{Rec}_{\mathcal S}^{\Phi}(q,T,\omega)$ 表示所得记录。称该 profile 具有 **exact 外层计划族**，当且仅当存在同一个 $\mathcal S$，满足以下量词顺序：

$$
\begin{aligned}
&\exists\mathcal S\quad
\forall\Phi\in\mathfrak F\quad
\forall q\in\mathbb N\quad
\forall T\in\mathbb N_{>0}\quad
\forall L\ge q+T\quad
\forall\omega\in\Omega_{q,T}^{(L)}(\Phi):\\
&\operatorname{Run}_{\mathcal S}^{\Phi}(q,T,\omega)
\text{ 有限停止，且 }
\operatorname{Rec}_{\mathcal S}^{\Phi}(q,T,\omega)
=
\operatorname{Ref}_{q,T}^{\Phi}(\omega).
\end{aligned}
$$

这里的 $\operatorname{Rec}$ 包括 $I_{q,T}$ 内记录、右切面 $Q_{D(q+T)}$，以及区间内发送但越过右切面的在途消息。不能为每个 $\Phi$ 或输入事后另选一条已经知道参考答案的阶段序列。固定 $\mathcal S$ 后，把一次运行的阶段序列记为：

$$
\Pi_{q,T}^{\Phi}(\omega)
=
(\pi_1,\ldots,
\pi_{N_{\mathrm{stage}}(q,T,\Phi,\omega)}).
$$

对每个节点，这些显式调用把式 (37) 分成不交的非空逻辑时间批次 $\Theta_{v,1},\ldots,\Theta_{v,m_v(q,T,\Phi,\omega)}$。若存在常数 $C_G^{\mathrm{stage}}\in\mathbb N$ 与 $C_{G,v}\in\mathbb N$，使每个 $\Phi\in\mathfrak F$、$q\in\mathbb N$、$T\in\mathbb N_{>0}$、$L\ge q+T$ 和 $\omega\in\Omega_{q,T}^{(L)}(\Phi)$ 都满足：

$$
\Lambda_v(I_{q,T};\Phi,\omega)
=
\bigsqcup_{r=1}^{m_v(q,T,\Phi,\omega)}\Theta_{v,r},
\qquad
N_{\mathrm{stage}}(q,T,\Phi,\omega)\le C_G^{\mathrm{stage}},
\qquad
m_v(q,T,\Phi,\omega)\le C_{G,v},
\tag{38}
$$

当 $\Lambda_v(I_{q,T};\Phi,\omega)=\varnothing$ 时取 $m_v(q,T,\Phi,\omega)=0$，并把式 (38) 右侧理解为空并。上述常数可以依赖固定的 $(\mathfrak G^\circ,\mathfrak F)$ 与 batch 契约，但不依赖 $\Phi,L,q,T$ 或 $\omega$。

称类级 batch 接口为**逐坐标精确 witness**，当且仅当它满足全称恒等式：

$$
\begin{aligned}
&\forall\Phi\in\mathfrak F,\quad
\forall\mathbf u
=
\left((\bar q_\theta,\theta,h_\theta)\right)_{\theta\in\Theta}^{\uparrow}
\in\mathsf{Adm}_{v,\Theta}^{\Phi},\\
&\qquad
\operatorname{BatchFull}_{v,\Theta}^{\Phi}(\mathbf u)
=
\left(
\Phi_v
\left(\bar q_\theta,\theta,h_\theta\right)
\right)_{\theta\in\Theta}^{\uparrow}.
\end{aligned}
\tag{39}
$$

若 exact 外层计划族使用满足式 (39) 的 witness，并存在满足式 (38) 的一致常数，就称这个 profile 具有**节点级时间批暴露**。本文也把这样的计划称为**控制顺序、计算整块的 exact prefill**。

这里“显式”是数学要求，不是物理 launch 要求。同一阶段的多个节点批次仍可融合进一次 packed API 或编译循环；witness 只需保留式 (38) 的批次分解，并在解包后满足式 (39)。$\Theta_{v,r}$ 按逻辑时间坐标组成，不要求这些坐标属于唯一 token；因此该定义直接容纳第 5 节的信号交错。

式 (38) 允许 selector、selector-history 与节点状态在每个大块内作 $\Theta(T)$ 长度的顺序控制扫描；它约束的是昂贵作用被外层拆成多少批，而不是控制 span。式 (39) 也只规定 backend 的函数值，不规定 batch kernel 内部算法。因而这个定义不声称 low span、work efficiency、设备利用率或实测加速。

这个定义也容纳“主体一批、薄边界若干批”的计划。固定成本 profile 后，若边界只需 $r_G$ 个 heavy/control 阶段，其中 $r_G$ 可以依赖 $h_\Delta$ 但不依赖 $T$ 或 $\Phi$，就在式 (38) 中把相应常数增大即可。真正不满足定义的是批次数或 heavy/control 阶段数随 $T$ 增长。

这个定义不能由一次不透明的 `RunWholeGraph` 见证：每个 $\operatorname{Full}$ 事件必须显式属于式 (38) 的某个节点批次；若存在反复的 $\operatorname{Full}\to\text{control}\to\operatorname{Full}$ 依赖，它必须表现为不同外层阶段，并计入 $N_{\mathrm{stage}}(q,T,\Phi,\omega)$。

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

设本轮需要从已经完成的切面 $b$ 推进到目标切面 $c>b$。选择 region 顺序：

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

由定理 4，未来输入不会改变 $b$ 左侧的已完成结果；新的输入 seal 又使 $c$ 成为安全目标。定理 7 的算法完成以后才实际得到 $Q_c$。固定空间图后，本轮外层 region tile 调用数量恰为 $|J|$，不随 $T$ 增长；每个非平凡 region tile 的时间宽度为 $DT$。

若这是有限输入的最后一个 chunk，则式 (22) 给出有限尾部。可以再按同一 region 顺序执行一次 drain。若 $\Delta_{\max}=kD$，尾部的逻辑时间尺度至多为 $k$ 个 token 间距。于是，大 chunk 的保守边界比例具有尺度：

$$
\frac{k}{T}.
\tag{48}
$$

式 (48) 是 tile 边界的比例，不是总算术工作量的加速比。

### 9.4 严格分层类的节点级时间批暴露

严格分层消除了 region 内消息反馈，但节点状态与 selector-history 仍可能跨时间递归。特别是，时间 $\theta+1$ 的 selector 输入可以经 $q_v^{\theta+1}$ 或 $y_j^{\theta+1}$ 依赖时间 $\theta$ 的选择结果。因此，定理 7 保证一次区域扫描，却不保证区域内部具有与 $T$ 无关的并行深度。

这个区别可以直接从事件图中看出。固定前置文档的一次完整输入 $x$ 及由它决定的事件图，再固定 $I=[b,c)$。对每个 region $j$ 和节点 $v$，把区间内实际存在的事件分成控制块与完整输出块；这个分块不增加或删除事件：

$$
\begin{aligned}
\mathsf C_j(I)
:={}&
\{P_{w,\theta}\in\mathscr V_x^{\mathrm{ev}}\mid
w\in\mathcal R_j,\ \theta\in I\}
\cup
\{U_{w,\theta}\in\mathscr V_x^{\mathrm{ev}}\mid
w\in\mathcal R_j,\ \theta\in I\}
\\
&\cup
\{S_{j,\theta}\in\mathscr V_x^{\mathrm{ev}}\mid
\theta\in I\},
\\
\mathsf F_v(I)
:={}&
\{F_{v,\theta}\in\mathscr V_x^{\mathrm{ev}}\mid
\theta\in I\}.
\end{aligned}
$$

时间 $b$ 的节点状态、selector-history 与从左侧跨入区间的在途消息由边界 $Q_b$ 提供。时间 $c$ 的节点状态与 selector-history，以及所有发送时间小于 $c$、到达时间不小于 $c$ 的在途消息，则属于右边界 $Q_c$。两个边界都不算作区间内部的事件块。给非空事件块赋字典序块秩：

$$
R_{\mathrm{blk}}(\mathsf C_j(I))=(\ell(j),0),
\qquad
R_{\mathrm{blk}}(\mathsf F_v(I))=(\ell(\rho(v)),1).
$$

$P\to S\to U$、$P\to U$、节点状态边与 selector-history 边都留在同一个 $\mathsf C_j(I)$；$U_{v,\theta}\to F_{v,\theta}$ 与 $P_{v,\theta}\to F_{v,\theta}$ 从 $\mathsf C_j(I)$ 指向 $\mathsf F_v(I)$，严格增加秩的第二坐标；消息边 $F_{v,\theta}\to P_{w,\theta+\delta(a)}$ 由式 (46) 满足 $\ell(\rho(v))<\ell(\rho(w))$，严格增加第一坐标。因此，每条跨块依赖都严格增加块秩。把每个非空块收缩为一个顶点，所得块图至多有 $|J|+|V|$ 个顶点，不随 $|I|$（因而也不随主时间块的 $T$）增长。按这个秩排列以后，它呈现为块上三角形：

```text
Q_b 中到达时间落在 I 内的消息、外部输入、较低层 Full
              │
              ▼
┌────────────────────────────────┐
│ C_j(I)：区间内全部 P / S / U    │
│ state 与 history 可有 Θ(|I|) 顺序扫描 │
└───────────────┬────────────────┘
                │ Full 的全部自变量已经确定
       ┌────────┼────────┐
       ▼        ▼        ▼
    F_v1(I)  F_v2(I)  …  F_vk(I)
      一批      一批        一批
       └────────┬────────┘
                ├── 跨界在途消息 ──→ Q_c
                │ 区间内只流向 ℓ 更高的控制块
                ▼
          C_k(I),  ℓ(k) > ℓ(j)

Q_b 中越过 c 的旧在途消息 ────────────→ Q_c
```

控制块内部可以很长，但一个 Full 结果不能返回本控制块。若允许这种返回，展开以后就可能出现随时间反复延伸的 $\operatorname{Full}\to\mathrm{control}\to\operatorname{Full}$ 拉链，并迫使时间块继续拆批。

这个块分解给出下列两阶段求值次序。对固定 region，先按 $\theta$ 扫描控制作用：

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
> 固定第 6.4 节的骨架与非空解释类。在定理 7 的结构条件下，再假设每个节点对任意合法有限坐标集都有满足式 (39) 的类级 batch witness。则同一个区域顺序策略对所有 $\Phi\in\mathfrak F$ 都是 exact 的，并在主时间块 $I_T$ 上具有节点级时间批暴露；对所有 $q,T,L$ 满足 $q\in\mathbb N$、$T\in\mathbb N_{>0}$、$L\ge q+T$，以及所有 $\Phi\in\mathfrak F$、$\omega\in\Omega_{q,T}^{(L)}(\Phi)$，均可取：
>
> $$
> N_{\mathrm{stage}}(q,T,\Phi,\omega)
> =C_G^{\mathrm{stage}}=|J|,
> \qquad
> m_v(q,T,\Phi,\omega)\le C_{G,v}=1
> \quad(v\in V).
> \tag{49}
> $$

**证明。** 按严格层次依次处理 region，并把每个 region 作为一个外层阶段。进入当前 region 的时间纤维已经由切面或较早 region 固定；上面的顺序控制扫描不调用 $\operatorname{Full}^\Phi$，所以它先确定该 region 中所有节点的全部 batch 输入。对每个节点 $v$，若 $\Lambda_v(I_{q,T};\Phi,\omega)$ 非空，就令唯一批次 $\Theta_{v,1}=\Lambda_v(I_{q,T};\Phi,\omega)$；若为空，则不调用。策略只读取骨架控制值和已经记录的 batch 返回，因而同一个动作函数适用于全部 $\Phi$。控制记录与参考递归相同，式 (39) 又给出逐坐标相同的完整输出，故该构造本身满足精确 region-tile 契约；再应用定理 7，所有阶段合成后也精确。因此式 (49) 成立。$\square$

这里的批次按**逻辑时间坐标**组成，而不按 token 身份组成。即使多个 token 的信号在某个 $h_{v,\theta}$ 中汇合，$\theta$ 仍只是 $\Lambda_v(I_{q,T};\Phi,\omega)$ 的一个元素，不会单独迫使批次拆分。第 4.4 节的“主体约为 $T-h_\Delta$、边界约为 $h_\Delta$”描述的是时间切面附近的几何厚度，不是两个互相独立的 token 子问题。

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
\Lambda_e^{\mathrm{MoE}}
=
\{\theta\in[b,c)
\mid
e\in\mathcal A_{\rho(e),\theta}\}.
\tag{50}
$$

随后把 $\Lambda_e^{\mathrm{MoE}}$ 对应的输入打包交给 expert tile。式 (50) 允许不同专家获得不同大小的批次；算法存在性不保证每个 $\Lambda_e^{\mathrm{MoE}}$ 都足够大，也不保证负载均衡。history 扫描顺序执行并不要求把昂贵 expert 计算也拆成逐时间调用。

### 10.3 真正的 graded DAG

空间图可以有分支、跳边和重新汇合，而不必是一条链。只要式 (14) 成立，到达同一节点的所有路径总时延仍相同。此时节点边界式 (16) 为整个 token chunk 给出坐标对齐；要把它变成合法执行 tile，仍须满足式 (41) 的 selector closure，并从每个倾斜 tile 的左边界按时间延续 selector-history。

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

下面给出一个完整反例。固定 $N\ge2$，取 $N$ 节点单位时延链：

$$
v_0\longrightarrow v_1\longrightarrow\cdots
\longrightarrow v_{N-1},
\qquad D=N,
$$

令唯一输入端口指向 $v_0$，取 $P=X_{v_r}=D_{v_r}=\{0,1\}$、$S_{v_r}=\{*\}$，并把全部节点放入同一个 region $j$。取 $K_j=1$、$Y_j=\{0,1\}$、$y_j^{\mathrm{init}}=0$、$\tau_j=0$ 与 $\kappa_j=0$。聚合函数返回唯一到达比特，$\operatorname{Read}_{v_r}^0$ 返回这个比特；对单点候选集合规定：

$$
\operatorname{SelStep}_{j,\{v\}}(y,\theta,(d))
=
\begin{cases}
(\{v\},d),&d=y,\\
(\varnothing,d),&d\ne y.
\end{cases}
$$

其余尚未指定的骨架函数与初值任意作固定的合法补全，并取 $\mathfrak F=\mathfrak F_{\mathrm{all}}$，即全部类型正确的完整输出解释所成的类；batch 接口任取满足式 (39) 者。考虑其中一个解释 $\Phi^{\mathrm{pass}}$：对 $r<N-1$，$\Phi^{\mathrm{pass}}_{v_r}$ 在通向 $v_{r+1}$ 的边坐标上输出其输入比特；其余输出坐标任意固定。取长度 $T$ 的全零输入 $x_T$，并令：

$$
\omega_T
=
\left(Q_0^{\Phi^{\mathrm{pass}}}(x_T),
E_{x_T,[0,NT)},NT\right)
\in
\Omega_{0,T}^{(T)}(\Phi^{\mathrm{pass}}).
$$

于是每个候选都 active，候选坐标恰为 $Nt+r$，其中 $0\le t<T$、$0\le r<N$；每个时间至多有一个候选，所以式 (42) 成立。第 6.4 节的动作级策略不能用控制作用代替尚未调用的 $\Phi^{\mathrm{pass}}$ 值：在每个尚未返回的 $F_{v_0,Nt}$ 调用点，$\mathfrak F_{\mathrm{all}}$ 还含有一个与全部已记录答案相同、但在该边坐标输出比特 $1$ 的解释；该值会使下一候选把 history 改成 $1$，所以同一个 transcript 不能预先断定下一个 token 的 $v_0$ active。

现在看函数作用事件图。对 $0\le t<T$ 与 $0\le r<N-1$，消息与作用前驱给出：

$$
F_{v_r,Nt+r}
\to P_{v_{r+1},Nt+r+1}
\to S_{j,Nt+r+1}
\to U_{v_{r+1},Nt+r+1}
\to F_{v_{r+1},Nt+r+1}.
$$

同一 region 的 history 边又连接最后一次选择与下一 token 的第一次选择。因此，对每个 $0\le t<T-1$：

$$
F_{v_0,Nt}
\leadsto
S_{j,Nt+N-1}
\to
S_{j,N(t+1)}
\to
U_{v_0,N(t+1)}
\to
F_{v_0,N(t+1)}.
$$

这条路径使前一 $F_{v_0,Nt}$ 成为后一 $F_{v_0,N(t+1)}$ 的因果祖先。第 6.4 节要求一个阶段的全部控制前驱先完成，随后才一次确定 $\mathsf{Batch}_r$，而该批次的返回值直到阶段末才公开。因此，这两个事件不能属于同一个 $\Theta_{v_0,r}$，也不能位于同一外层阶段。对相应实例 $\omega_T$：

$$
m_{v_0}(0,T,\Phi^{\mathrm{pass}},\omega_T)\ge T,
\qquad
N_{\mathrm{stage}}(0,T,\Phi^{\mathrm{pass}},\omega_T)\ge T.
$$

由于 $T$ 任意，这排除了该 profile 上与 $T$ 无关的 $C_{G,v_0}$ 和 $C_G^{\mathrm{stage}}$。逐函数作用调用单点 batch 的同一策略仍对整个 $\mathfrak F_{\mathrm{all}}$ exact；反例否定的只是有界批次，而不是可执行性。障碍不是候选同时出现，而是 region 内消息与共享 history 共同形成了时间拉链。

### 10.7 商图强连通分量

在有限有向图中，若从顶点 $j$ 有路径到 $j'$，并且从 $j'$ 也有路径回到 $j$，则称二者互相可达。一个**强连通分量**是一个按包含关系极大的非空顶点集合，其中任意两个顶点都互相可达。

若区域商图有环，可以把每个强连通分量收缩成一个执行 supertile。以这些分量为顶点、保留分量间有向边所得的图称为**凝聚图**。凝聚图总是 DAG：否则，凝聚图中的一个有向环会证明环上多个分量彼此可达，与每个分量已经极大矛盾。

这种收缩只给出空间上的 DAG。要由此证明节点级时间批暴露，还必须分别证明：每个 supertile 内的 heavy/control 阶段数有界，并且每个节点的昂贵时间事件只需有界批次。分量规模小可能帮助构造这种 witness，但不能单独推出它；分量内部仍可能随 $T$ 反复出现 heavy--control 反馈。

若一个强连通分量覆盖大部分 region，融合依然在数学上合法；但“调用一个 supertile”已经接近调用全图，更不能单靠一次外层调用声称保块或高性能。

### 10.8 工具返回形成的大输入块

设模型在一次工具调用后同时得到 $T$ 个新的已知 token。公开这些记录并给出相应输入 seal，会把安全目标切面一次前移 $DT$。在严格分层类中，定理 7 因而允许每个 region 处理一个宽度为 $DT$ 的时间 tile，而不是进行 $T$ 轮全图调用；全部 region 完成后，执行才实际到达该切面。

若随后立即进入自回归 decode，还需先完成生成下一 token 所必需的尾部事件，或者在模型定义中给出明确的 prefill--decode 边界状态。这个 drain 的空间传播尺度由式 (23) 保守控制。若 $h_\Delta\ll T$，只能推出边界的 token 尺度宽度比例较小；它的实际成本仍取决于事件密度与 backend。任何用于生成下一 token 的输出还必须满足式 (32)。

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

1. **任意正时延 TimedDAG**：定理 4 给出对未来扩展不变的标量边界；输入 seal 使它成为安全目标，前置文档再给出包含节点状态、selector-history 与在途消息的精确 continuation。
2. **路径时延跨度有界**：式 (23)--(27) 给出 chunk 边界厚度的结构尺度。
3. **graded DAG**：引理 3 给出节点支持的 token 对齐边界；合法执行仍需 selector/history 相容性。
4. **严格分层 region**：定理 7 给出每个时间块只扫描一次所有 region 的算法。
5. **带类级节点 batch witness 的严格分层 region**：推论 8 给出 $C_G^{\mathrm{stage}}=|J|$、$C_{G,v}=1$ 的节点级时间批暴露；命题 5 保证精确 tile 替换不改变完整语义。

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
\text{精确类级节点 BatchFull witness}
\\[1mm]
\Longrightarrow
\text{节点级时间批暴露：}
C_G^{\mathrm{stage}}=|J|,\ C_{G,v}=1.
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
> `input chunk` 是一批新公开的外部输入记录。对式 (1) 的 token $q,\ldots,q+T-1$，相应输入 seal 使 $D(q+T)$ 成为安全目标切面；执行实际完成其左前缀以后，切面状态才从 $Q_{Dq}$ 推进到 $Q_{D(q+T)}$。
>
> `logical-time tile` 是式 (20) 的逻辑时间区间及其包含的函数作用事件。它可能含有多个 token 的混合消息，不等于输入 token 集合。

> [!info]- S.2　prefill 与 streaming
> 本文中的 `prefill` 表示外层策略从一批已经给定的输入位置出发，精确推进相应逻辑时间块；节点的昂贵作用可以按式 (38) 组成时间批次。
>
> `streaming` 表示随着输入 seal 前进，反复完成新的逻辑时间前缀。允许 streaming 不表示必须逐 token 调用节点；每次 seal 可以推进一个大时间块。

> [!info]- S.3　halo、tail 与 drain
> `halo` 或 `boundary band` 在本文对应主切面附近的纯空间传播坐标和在途消息；式 (23) 的 $h_\Delta$ 是其保守 token 尺度宽度，$W_b$ 保存实际跨界消息，节点状态与 selector-history 则另存于 $Q_b$。halo 不是一组可以从计算中删除的 token。
>
> `tail` 是有限输入最后一个主切面以后的剩余事件。`drain` 表示输入已经声明结束后，把这些剩余事件推进到完整终点。

> [!info]- S.4　tile、kernel 与 launch
> `tile` 对应第 6.1 节的有限事件集合 $K$；式 (33) 是它的外部依赖就绪条件，不是 tile 的定义。边界状态同时包括节点状态与 selector-history。`kernel` 对应式 (34) 中的联合函数 $\mathcal K$。`launch count` 是实现实际发起多少次这样的函数调用。
>
> 第 6.4 节的 $N_{\mathrm{stage}}(q,T,\Phi,\omega)$ 数 heavy/control 阶段，$m_v(q,T,\Phi,\omega)$ 数显式节点批次；二者都不必等于物理 launch 数。$\Phi$ 表示当前的完整输出函数解释。`packed API` 表示一次实现调用承载多个已经显式列出的节点批次；它不把这些批次在式 (38) 中合并。少量 launch 不等于少量算术工作；整个参考递归若被隐藏进一次全图调用，launch count 就不再是有意义的性能指标。

> [!info]- S.5　region、selector 与 placement
> `region` 对应 $\rho$ 的一个纤维 $\mathcal R_j$。`selector` 对应前置文档的函数 $\operatorname{SelStep}_{j,C}$，在事件图中对应作用 $S_{j,\theta}$；式 (40) 只定义它在该次作用读取的候选集合。`selector-history` 对应 $y_j^\theta$，不是任一节点的 $q_v^\theta$。
>
> region 不是设备、线程组、并行域或内存位置。实现可以让一个 region 跨设备，也可以把多个 region 放在同一设备；若要讨论局部性，必须另给 placement 与成本模型。

> [!info]- S.6　ready 与 selector closure
> 一个 tile 的输入纤维已被 seal，并且满足式 (33) 的外部依赖条件时，可以称它为 `ready`。若 tile 含区域选择作用，还必须满足式 (41) 的 selector closure。
>
> “某节点当前有输入”不足以证明 selector ready，因为同一区域、同一时间仍可能出现尚未公开的其他候选节点；当前 selector-history 也必须由左边界或前一选择作用确定。
>
> 前置文档中的 $(v,\theta)\in\mathsf{Completed}_n$ 只表示相应函数作用已经进入完成集合；其消息仍可能稍后才进入 $H_n$。因此本文的阶段计划另行要求在阶段末公开输出，后续 tile 的 `ready` 不能只由 $\mathsf{Completed}_n$ 推出。

> [!info]- S.7　state 与 selector-history scan
> `state scan` 表示按时间组合节点状态或 selector-history 转移。若转移具有结合的函数复合表示，可以采用 parallel scan；若没有这种结构，`RunRegionTile` 内部可能仍需顺序处理状态。
>
> 本文的大块调度定理不把任意状态递归自动视为可并行 scan。

> [!info]- S.8　pipeline latency 与 throughput
> 若输出作用发生在逻辑时间 $\theta_{\mathrm{out}}$，并依赖 token $t$，则 $\theta_{\mathrm{out}}-\iota(t)$ 是模型内的**逻辑延迟**。路径时延与 halo 都是分析这个量的模型内结构量；节点状态与 selector-history 还可能把依赖延续到更晚时间。它们都不是设备上的 pipeline latency。
>
> 物理 latency、steady-state throughput 以及二者的关系都需要另给计算设备、并行算法和成本模型。本文不能仅由大时间 tile 推出其中任何一个指标。

> [!info]- S.9　causal leakage
> `causal leakage` 在本文中表示某个用于预测位置 $r+1$ 的输出违反式 (32)，即它在增广事件图中依赖了位置大于 $r$ 的输入。逻辑时间递增本身不能排除这种 token 次序泄漏。

> [!info]- S.10　高性能通用 prefill
> 本文的 `高性能通用 prefill` 正式对应第 6.4 节相对于已声明成本 profile 的**节点级时间批暴露**；`通用` 表示同一个动作级策略对明示解释类 $\mathfrak F$ 中的全部 $\Phi$ 和全部合法 chunk 都成立。“控制顺序、计算整块”是同一性质的直白说法。
>
> 严格分层类由推论 8 给出 $C_G^{\mathrm{stage}}=|J|$ 与 $C_{G,v}=1$。该术语允许 selector-history 顺序扫描，也不等于 low-span、work-efficient、设备高利用率或端到端加速。

> [!info]- S.11　cost profile、heavy/control、work 与 span
> `cost profile` 对应非 Full 骨架 $\mathfrak G^\circ$ 与允许的 Full 解释类 $\mathfrak F$；节点级时间批暴露还另需式 (39) 的 batch 契约。它是对语义规格增加的成本分类，不是空间图自身的性质。`heavy/control stage` 对应 $\Pi_{q,T}^{\Phi}(\omega)$ 的一个阶段：先作控制求值，再提交该阶段显式列出的昂贵节点批次；它不是逻辑时间单位，也不是前置文档的暴露阶段 $n$。若未另给精化映射，不能把 $H_n$ 与某个外层阶段末直接对齐。
>
> `visible transcript` 对应第 6.4 节的元组 $\mathsf{Tr}_{r,k}$；`causal` 与 `no-oracle` 表示同一个动作函数只读取这个元组。除初始切面状态外，新出现的 Full 信息只能来自其中已经记录的 $\mathsf{Ans}_s$，所以两个相同 transcript 不能因解释 $\Phi$ 或未调用的 Full 值而分岔；batch 也只能查询已经确定为 active 的实际作用，不能用反事实输入探测 $\Phi$。
>
> `work` 需要先选定计算模型，再数算法执行的总基本操作；`span` 是同一算法依赖 DAG 上的最长基本操作链。本文只界定外层阶段数和节点批次数，未给出计算模型，所以没有把二者作为式 (38) 的结论。
