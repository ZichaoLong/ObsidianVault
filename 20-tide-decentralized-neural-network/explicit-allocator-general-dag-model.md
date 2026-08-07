---
type: note
status: draft
cssclasses:
  - textbook-math
tags:
  - tide
  - prefill-decode
  - sparse-routing
  - allocator
  - math
---

# 显式 allocator 的一般空间 DAG 模型

> [!summary] 本页定位
> 本页是 Tide `prefill / decode` 正向设计的当前主线候选。它先把最低层模型收缩为：有限空间 DAG、单位边时延、节点持有状态、带到达轮次的消息、边界延续状态、显式 allocator 节点和节点级 artifact equality。`owner / frontier` 不作为本页核心前提；它们是后续证明 token 因果性、读出归因和细粒度调试时可加入的增强字段。

> [!important] 核心结论
> 显式 allocator 方案可以处理不等长路径。只要空间图是 DAG，allocator 也是 DAG 中的普通节点，并且每个窗口级节点转导器只读取自己的左边界状态与拓扑上游消息，那么窗口执行方程可以按节点拓扑序唯一构造。一次 chunk 调度只需调用每个节点一次；每个节点内部可以批量处理当前 chunk 中到达本节点的所有消息。

> [!warning] 本页不自动证明的内容
> 本页首先证明空间方向的拓扑序 chunk 构造与 artifact equality，不把同一组窗口方程循环命名为“流式执行”。要进一步证明真正的 `prefill = decode`，还必须定义逐绝对轮次的节点参考转移，并证明窗口级节点转导器等于这些逐轮转移的折叠。节点内部若使用 attention、SSM、scan、分段打包、稀疏选择或 learned routing，也需要分别证明相应实现满足这个时间组合律与同一个节点参考语义。

## 0. 写作规则与基础记号

### 定义 0.1：正式对象规则

本文中进入定义、引理、定理或证明的对象，必须在使用前被声明为下列对象之一：

1. 集合。
2. 集合元素。
3. 函数或部分函数。
4. 关系。
5. 有限序列。
6. 有限元组。
7. 由上述对象定义出的性质。

直观说明可以保留，但不承担证明前提。若一个词在证明中起作用，它必须能回溯到某个集合、函数、关系、有限序列或有限元组。

### 定义 0.2：自然数、有限区间与序列

定义自然数集合：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $n\in\mathbb N$，定义：

$$
[n]=\{0,1,\ldots,n-1\}.
$$

若 $A$ 是集合，定义 $A^\star$ 为 $A$ 上所有有限序列构成的集合：

$$
A^\star=\bigcup_{n\in\mathbb N}A^n.
$$

若 $\mathbf a=(a_0,\ldots,a_{n-1})\in A^n$，定义：

$$
\operatorname{len}(\mathbf a)=n.
$$

定义 $A$ 的有限子集集合：

$$
\mathcal P_{\mathrm{fin}}(A)=\{S\subseteq A\mid S\text{ 是有限集}\}.
$$

定义有限序列的元素集合函数：

$$
\operatorname{elem}_A:A^\star\to\mathcal P_{\mathrm{fin}}(A)
$$

如下：

$$
\operatorname{elem}_A(\mathbf a)
=
\{a_i\mid i\in[\operatorname{len}(\mathbf a)]\}.
\tag{D-0.2a}
$$

若 $I$ 是有限集，且对每个 $i\in I$ 给定集合 $A_i$，定义有限笛卡尔积：

$$
\prod_{i\in I}A_i
=
\{f\mid f:I\to\bigcup_{i\in I}A_i
\text{ 且 } f(i)\in A_i\text{ 对每个 }i\in I\}.
\tag{D-0.2b}
$$

### 定义 0.3：窗口位置集合

给定 $B,L\in\mathbb N$，定义长度为 $L$、从全局位置 $B$ 开始的窗口位置集合：

$$
\mathbb I_{B,L}=\{B,B+1,\ldots,B+L-1\}.
\tag{D-0.3}
$$

若 $L=0$，则 $\mathbb I_{B,0}=\varnothing$。

## 1. 输入流、绝对轮次与边界切面

### 定义 1.1：输入输出集合与全局输入流

给定非空集合 $X$ 与 $Y$，分别称为输入值集合与输出值集合。

给定函数：

$$
x:\mathbb N\to X,
$$

称为全局输入流。对 $t\in\mathbb N$，元素 $x_t=x(t)$ 是第 $t$ 个输入值。

对窗口 $(B,L)$，定义当前 chunk：

$$
x_{B:B+L}\in X^{\mathbb I_{B,L}},
\qquad
x_{B:B+L}(t)=x_t.
\tag{D-1.1}
$$

### 定义 1.2：外部周期与边界切面

给定常数：

$$
R\in\mathbb N_{>0},
$$

称为外部输入周期。定义边界切面函数：

$$
\beta:\mathbb N\to\mathbb N,
\qquad
\beta(b)=Rb.
\tag{D-1.2}
$$

第 $t$ 个输入值注入的绝对轮次定义为：

$$
\tau_{\mathrm{in}}(t)=\beta(t)=Rt.
\tag{D-1.3}
$$

定义第 $t$ 个输出位置的名义读出切面：

$$
\tau_{\mathrm{read}}(t)=\beta(t+1)=R(t+1).
\tag{D-1.4}
$$

窗口 $(B,L)$ 的内部可消费轮次集合定义为：

$$
\mathbb T_{B,L}
=
\{\tau\in\mathbb N\mid \beta(B)\leq\tau<\beta(B+L)\}.
\tag{D-1.5}
$$

直观地说，$B$ 和 $B+L$ 是输入位置边界，$\beta(B)$ 和 $\beta(B+L)$ 是执行切面。当前窗口从左切面继续执行，到右切面停止；没有在右切面前消费完的消息进入右边界延续状态。

## 2. 一般空间 DAG 与单位边时延

### 定义 2.1：有限空间 DAG

给定有限非空集合 $V$ 和关系：

$$
E\subseteq V\times V.
$$

定义空间图：

$$
G=(V,E).
$$

固定两个不同元素：

$$
v_{\mathrm{in}},v_{\mathrm{out}}\in V,
\qquad
v_{\mathrm{in}}\neq v_{\mathrm{out}},
$$

分别称为输入节点与输出节点。

称 $G$ 是 DAG，当且仅当不存在 $k\in\mathbb N_{>0}$ 和序列 $(v_0,\ldots,v_k)\in V^{k+1}$ 满足：

$$
v_0=v_k,
\qquad
(v_i,v_{i+1})\in E\quad(i\in[k]).
$$

对 $a,b\in V$，从 $a$ 到 $b$ 的有向路径是一个有限序列 $(u_0,\ldots,u_k)\in V^{k+1}$，其中 $k\in\mathbb N$，并且：

$$
u_0=a,\qquad u_k=b,
$$

且对每个 $i\in[k]$：

$$
(u_i,u_{i+1})\in E.
$$

本文要求：

1. 不存在 $u\in V$ 使 $(u,v_{\mathrm{in}})\in E$。
2. 对每个 $v\in V$，存在从 $v_{\mathrm{in}}$ 到 $v$ 的有向路径。
3. 对每个 $v\in V$，存在从 $v$ 到 $v_{\mathrm{out}}$ 的有向路径。

这些条件不要求所有从 $v_{\mathrm{in}}$ 到 $v_{\mathrm{out}}$ 的路径等长。

### 定义 2.2：前驱、后继与拓扑序

对 $v\in V$，定义前驱集合与后继集合：

$$
\operatorname{Pred}_G(v)=\{u\in V\mid(u,v)\in E\},
\qquad
\operatorname{Succ}_G(v)=\{u\in V\mid(v,u)\in E\}.
\tag{D-2.2}
$$

空间拓扑序是有限序列：

$$
\pi=(v_0,\ldots,v_{|V|-1})\in V^{|V|}
$$

满足：

$$
\{v_i\mid i\in[|V|]\}=V,
$$

且若 $(v_i,v_j)\in E$，则 $i<j$。

### 引理 2.3：有限 DAG 存在拓扑序

若 $G=(V,E)$ 满足定义 2.1，则至少存在一个定义 2.2 意义下的拓扑序。

**证明。**

先证明任意有限非空 DAG 的任意非空诱导子图至少有一个入度为零的节点。若某个非空诱导子图中的每个节点都有来自该子图的入边，则从其中任意节点开始不断沿入边向前选择节点。由于该诱导子图的节点集合有限，所得序列中必有重复节点，从而得到有向环，与原图为 DAG 矛盾。

从 $V$ 开始，反复在当前非空诱导子图中选择一个入度为零的节点，把它追加到序列末尾，再从当前节点集合中删除它。每一步都能由上一段的结论完成；经过 $|V|$ 步后得到包含 $V$ 中每个节点恰好一次的序列。若 $(u,v)\in E$，则删除 $v$ 时 $u$ 不可能仍在当前节点集合中，否则 $v$ 的当前入度不为零。因此 $u$ 必在 $v$ 之前被追加，所得序列是拓扑序。

<div class="qed" aria-label="证毕">∎</div>

### 定义 2.4：空间深度与拓扑层

对 $v\in V$，定义：

$$
\mathsf{Path}_{G}(v)
=
\bigcup_{k\in\mathbb N}
\left\{
(u_0,\ldots,u_k)\in V^{k+1}
\ \middle|\
u_0=v_{\mathrm{in}},\ u_k=v,
(u_i,u_{i+1})\in E\text{ 对每个 }i\in[k]
\right\}.
$$

$\mathsf{Path}_{G}(v)$ 的元素称为从 $v_{\mathrm{in}}$ 到 $v$ 的有向路径。若路径属于 $V^{k+1}$，定义其长度为 $k$。因为 $G$ 是有限 DAG，一条有向路径不可能重复经过同一节点，所以 $\mathsf{Path}_{G}(v)$ 是有限非空集合。

定义空间深度函数：

$$
d_G:V\to\mathbb N,
\qquad
d_G(v)=\max\{k\in\mathbb N\mid
\mathsf{Path}_{G}(v)\text{ 中存在长度为 }k\text{ 的路径}\}.
\tag{D-2.4a}
$$

定义：

$$
D_G=1+\max\{d_G(v)\mid v\in V\},
\qquad
V_j=\{v\in V\mid d_G(v)=j\}
\quad(j\in[D_G]).
\tag{D-2.4b}
$$

有限性与定义 2.1 的可达性保证上述最大值存在。若 $(u,v)\in E$，则任意一条到达 $u$ 的最长路径后接边 $(u,v)$ 得到一条到达 $v$ 的路径，所以：

$$
d_G(u)<d_G(v).
\tag{A-2.4}
$$

因此 $(V_0,\ldots,V_{D_G-1})$ 是 $V$ 的一个分割，同一 $V_j$ 内不存在空间边。取一个深度为 $D_G-1$ 的节点及到达它的一条最长路径；式 A-2.4 保证该路径依次经过深度 $0,1,\ldots,D_G-1$ 的节点，所以每个 $V_j$ 都非空。这里的空间深度只是由一般 DAG 导出的并行调度分层；它不要求所有到达同一节点的路径等长，也不把一般 DAG 改成 leveled DAG。

### 定义 2.5：单位边时延

给定非空集合 $\mathsf{Payload}$，称为消息载荷集合。定义消息标识符集合：

$$
\mathsf{MID}=V\times\mathbb N\times\mathbb N.
$$

标识符 $(u,\tau,j)\in\mathsf{MID}$ 的三个坐标分别表示源节点、发送绝对轮次和该源节点在该轮次使用的局部序号。定义三个投影函数：

$$
\operatorname{idnode}:\mathsf{MID}\to V,
\qquad
\operatorname{idtime}:\mathsf{MID}\to\mathbb N,
\qquad
\operatorname{idserial}:\mathsf{MID}\to\mathbb N
$$

为：

$$
\operatorname{idnode}(u,\tau,j)=u,
\quad
\operatorname{idtime}(u,\tau,j)=\tau,
\quad
\operatorname{idserial}(u,\tau,j)=j.
$$

定义候选消息记录集合：

$$
\mathfrak M
=
\mathsf{MID}\times\mathbb N\times\mathbb N\times V\times V\times\mathsf{Payload}.
$$

定义投影函数：

$$
\operatorname{id}:\mathfrak M\to\mathsf{MID},
\qquad
\operatorname{send}:\mathfrak M\to\mathbb N,
\qquad
\operatorname{arrival}:\mathfrak M\to\mathbb N,
$$

$$
\operatorname{src}:\mathfrak M\to V,
\qquad
\operatorname{dst}:\mathfrak M\to V,
\qquad
\operatorname{payload}:\mathfrak M\to\mathsf{Payload}.
$$

若 $m=(\iota,\tau_s,\tau_a,u,v,p)$，规定：

$$
\operatorname{id}(m)=\iota,
\quad
\operatorname{send}(m)=\tau_s,
\quad
\operatorname{arrival}(m)=\tau_a,
$$

$$
\operatorname{src}(m)=u,
\quad
\operatorname{dst}(m)=v,
\quad
\operatorname{payload}(m)=p.
$$

定义有效消息集合：

$$
\mathsf{Msg}_G
=
\{m\in\mathfrak M
\mid
(\operatorname{src}(m),\operatorname{dst}(m))\in E
\text{ 且 }
\operatorname{arrival}(m)=\operatorname{send}(m)+1,
\operatorname{idnode}(\operatorname{id}(m))=\operatorname{src}(m),
\operatorname{idtime}(\operatorname{id}(m))=\operatorname{send}(m)
\}.
\tag{D-2.5}
$$

这就是单位边时延：沿一条空间边发送的消息在下一个绝对轮次到达。

## 3. 节点状态与边界延续状态

### 定义 3.1：节点状态

对每个 $v\in V$，给定非空集合 $\mathcal S_v$，称为节点 $v$ 的状态集合。

定义全图状态集合：

$$
\mathcal S_G=\prod_{v\in V}\mathcal S_v.
\tag{D-3.1}
$$

若 $\mathbf S\in\mathcal S_G$，则 $\mathbf S(v)\in\mathcal S_v$ 表示节点 $v$ 的状态。

状态只由所属节点持有。若一个 allocator 需要历史负载估计、quota 计数或 learned routing 参数，它们必须是该 allocator 节点状态集合 $\mathcal S_v$ 的坐标，或经由上游消息输入，而不是隐藏全局变量。

### 定义 3.2：消息标识符唯一性

若 $M\in\mathcal P_{\mathrm{fin}}(\mathsf{Msg}_G)$，定义性质 $\operatorname{UniqueMID}(M)$ 为：

$$
\operatorname{UniqueMID}(M)
\Longleftrightarrow
\bigl(
\forall m,m'\in M,
\operatorname{id}(m)=\operatorname{id}(m')
\Longrightarrow m=m'
\bigr).
\tag{D-3.2}
$$

该性质表示 $M$ 中一个消息标识符至多对应一条消息记录。

### 定义 3.3：边界延续状态

对 $b\in\mathbb N$，定义边界 $b$ 的延续状态集合：

$$
\mathsf{Cont}_b
=
\left\{
(\mathbf S,M)\in
\mathcal S_G\times\mathcal P_{\mathrm{fin}}(\mathsf{Msg}_G)
\ \middle|\
\operatorname{UniqueMID}(M)
\text{ 且 }
\forall m\in M,
\operatorname{arrival}(m)=\beta(b)
\right\}.
\tag{D-3.3}
$$

若 $C_b=(\mathbf S^b,\mathcal M_b^\partial)\in\mathsf{Cont}_b$，则 $\mathbf S^b$ 是切面 $\beta(b)$ 左侧已经提交的节点状态，$\mathcal M_b^\partial$ 是恰好在该切面到达、尚未被消费的消息集合。因为每条边的时延为 $1$，已经发送但尚未消费的消息不可能跨越多个未来轮次；若以后允许大于 $1$ 的边时延，式 D-3.3 才需要改回到达轮次不小于 $\beta(b)$ 的形式。

本文采用约定：所有到达轮次小于 $\beta(b)$ 的历史消息已经被消费，其影响已经包含在 $\mathbf S^b$ 中。由单位边时延可知，$b=0$ 时 $\mathcal M_0^\partial=\varnothing$。

## 4. 显式 allocator 节点与节点转导器

### 定义 4.1：节点角色

定义角色集合：

$$
\mathsf{Role}
=
\{\mathtt{input},\mathtt{output},\mathtt{compute},\mathtt{allocator}\}.
$$

给定函数：

$$
\operatorname{role}:V\to\mathsf{Role}.
\tag{D-4.1}
$$

要求：

$$
\operatorname{role}^{-1}(\{\mathtt{input}\})=\{v_{\mathrm{in}}\},
\qquad
\operatorname{role}^{-1}(\{\mathtt{output}\})=\{v_{\mathrm{out}}\}.
$$

若 $\operatorname{role}(v)=\mathtt{allocator}$，称 $v$ 为显式 allocator 节点。allocator 不是隐藏调度器；它只是空间 DAG 中的一个节点。

### 定义 4.2：输入原子、时间桶与节点输入序列

定义输入原子标签集合：

$$
\mathsf{AtomTag}=\{\mathtt{inj},\mathtt{msg}\},
\qquad
\mathtt{inj}\neq\mathtt{msg}.
$$

对节点 $v\in V$，定义输入原子集合：

$$
\mathsf{Atom}_{v,B,L}
=
\left(
\{\mathtt{msg}\}\times\{m\in\mathsf{Msg}_G\mid\operatorname{dst}(m)=v\}
\right)
\cup
\mathsf{InjAtom}_{v,B,L},
$$

其中：

$$
\mathsf{InjAtom}_{v,B,L}
=
\begin{cases}
\{\mathtt{inj}\}\times\mathbb I_{B,L}\times X,&v=v_{\mathrm{in}},\\
\varnothing,&v\neq v_{\mathrm{in}}.
\end{cases}
$$

定义输入原子的时间函数：

$$
\operatorname{atime}_{v,B,L}:\mathsf{Atom}_{v,B,L}\to\mathbb N
$$

如下。若 $a=(\mathtt{msg},m)$，则：

$$
\operatorname{atime}_{v,B,L}(a)=\operatorname{arrival}(m).
$$

若 $v=v_{\mathrm{in}}$ 且 $a=(\mathtt{inj},t,x)$，其中 $t\in\mathbb I_{B,L}$ 且 $x\in X$，则：

$$
\operatorname{atime}_{v,B,L}(a)=\tau_{\mathrm{in}}(t).
$$

定义时间桶集合：

$$
\mathsf{Bucket}_{v,B,L}
=
\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_{v,B,L}).
$$

元素 $(\tau,A)\in\mathsf{Bucket}_{v,B,L}$ 合法，当且仅当对每个 $a\in A$：

$$
\operatorname{atime}_{v,B,L}(a)=\tau.
\tag{A-4.2a}
$$

定义节点输入序列集合：

$$
\mathfrak U_{v,B,L}
=
\bigcup_{n\in\mathbb N}
\left\{
((\tau_0,A_0),\ldots,(\tau_{n-1},A_{n-1}))
\in\mathsf{Bucket}_{v,B,L}^{n}
\ \middle|\
\begin{array}{l}
\forall i\in[n],\ \forall a\in A_i,
\operatorname{atime}_{v,B,L}(a)=\tau_i,\\
\forall i\in[n],\ \tau_i\in\mathbb T_{B,L}
\text{ 且 }A_i\neq\varnothing,\\
\forall i\in\{j\in\mathbb N\mid j+1<n\},\
\tau_i<\tau_{i+1}
\end{array}
\right\}.
\tag{D-4.2b}
$$

时间桶允许一个节点在同一绝对轮次联合处理多个消息或注入原子。是否在桶内进一步排序、联合计算或按子 kernel 打包，是节点转导器的内部语义。

### 定义 4.3：路由记录、局部输出与提交记录

给定非空集合 $\mathsf{RID}$、$\mathsf{OID}$ 与 $\mathsf{Meta}$，分别称为路由记录标识符集合、局部输出标识符集合与元数据集合。

对节点 $v\in V$，定义路由记录集合：

$$
\mathsf{Route}_v
=
\{(\rho,\tau,w,U,\mu)
\in
\mathsf{RID}\times\mathbb N\times V\times\mathcal P_{\mathrm{fin}}(\operatorname{Succ}_G(v))\times\mathsf{Meta}
\mid
w=v\}.
\tag{D-4.3a}
$$

定义投影函数：

$$
\operatorname{rid}:\mathsf{Route}_v\to\mathsf{RID},
\qquad
\operatorname{rtime}:\mathsf{Route}_v\to\mathbb N,
\qquad
\operatorname{rnode}:\mathsf{Route}_v\to V,
$$

$$
\operatorname{rdst}:\mathsf{Route}_v\to\mathcal P_{\mathrm{fin}}(\operatorname{Succ}_G(v)),
\qquad
\operatorname{rmeta}:\mathsf{Route}_v\to\mathsf{Meta}.
$$

若 $r=(\rho,\tau,v,U,\mu)\in\mathsf{Route}_v$，规定：

$$
\operatorname{rid}(r)=\rho,
\quad
\operatorname{rtime}(r)=\tau,
\quad
\operatorname{rnode}(r)=v,
\quad
\operatorname{rdst}(r)=U,
\quad
\operatorname{rmeta}(r)=\mu.
$$

定义节点 $v$ 的提交记录集合：

$$
\mathsf{Commit}_v=\mathbb N\times\mathcal S_v.
\tag{D-4.3b}
$$

定义输出节点的局部输出记录集合：

$$
\mathsf{Out}_{v_{\mathrm{out}},B,L}
=
\mathsf{OID}\times\mathbb I_{B,L}\times Y.
\tag{D-4.3c}
$$

对 $v\neq v_{\mathrm{out}}$，定义：

$$
\mathsf{Out}_{v,B,L}
=
\mathsf{OID}\times\mathsf{Meta}.
\tag{D-4.3d}
$$

对每个 $v\in V$，定义局部输出标识符投影：

$$
\operatorname{oid}_{v,B,L}:
\mathsf{Out}_{v,B,L}\to\mathsf{OID}
$$

为元组第一坐标，即：

$$
\operatorname{oid}_{v_{\mathrm{out}},B,L}(\omega,t,y)=\omega,
\qquad
\operatorname{oid}_{v,B,L}(\omega,\mu)=\omega
\quad(v\neq v_{\mathrm{out}}).
\tag{D-4.3e}
$$

### 定义 4.4：节点 artifact、投影函数与合法性

对节点 $v\in V$，先定义节点原始产物集合：

$$
\mathfrak A_{v,B,L}
=
\mathsf{Out}_{v,B,L}^\star
\times
\mathsf{Commit}_v^\star
\times
\mathsf{Route}_v^\star
\times
\mathsf{Msg}_G^\star
\times
\mathcal S_v.
\tag{D-4.4}
$$

五个坐标依次是：

1. 局部输出记录序列。
2. 状态提交记录序列。
3. 路由记录序列。
4. 出站消息序列。
5. 右侧节点状态。

定义投影函数：

$$
\operatorname{localOut}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Out}_{v,B,L}^\star,
$$

$$
\operatorname{commits}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Commit}_v^\star,
$$

$$
\operatorname{routes}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Route}_v^\star,
$$

$$
\operatorname{outbox}_{v,B,L}:\mathfrak A_{v,B,L}\to\mathsf{Msg}_G^\star,
$$

$$
\operatorname{state}^+_{v,B,L}:\mathfrak A_{v,B,L}\to\mathcal S_v.
$$

若：

$$
A=(O,Q,R_s,M_s,S^+)\in\mathfrak A_{v,B,L},
$$

规定：

$$
\operatorname{localOut}_{v,B,L}(A)=O,
\quad
\operatorname{commits}_{v,B,L}(A)=Q,
\quad
\operatorname{routes}_{v,B,L}(A)=R_s,
$$

$$
\operatorname{outbox}_{v,B,L}(A)=M_s,
\quad
\operatorname{state}^+_{v,B,L}(A)=S^+.
$$

称 $A\in\mathfrak A_{v,B,L}$ 是合法节点产物，当且仅当满足以下条件。

第一，提交记录只提交当前窗口内部轮次。对每个 $(\tau,S)\in\operatorname{elem}_{\mathsf{Commit}_v}(\operatorname{commits}_{v,B,L}(A))$：

$$
\tau\in\mathbb T_{B,L}.
\tag{A-4.4a}
$$

第二，路由记录只属于当前节点与当前窗口内部轮次。对每个 $r\in\operatorname{elem}_{\mathsf{Route}_v}(\operatorname{routes}_{v,B,L}(A))$：

$$
\operatorname{rnode}(r)=v,
\qquad
\operatorname{rtime}(r)\in\mathbb T_{B,L}.
\tag{A-4.4b}
$$

第三，出站消息必须由当前节点在当前窗口内部轮次发送。对每个 $m\in\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{v,B,L}(A))$：

$$
\operatorname{src}(m)=v,
\qquad
\operatorname{send}(m)\in\mathbb T_{B,L}.
\tag{A-4.4c}
$$

第四，每条出站消息必须被某条路由记录覆盖。对每个 $m\in\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{v,B,L}(A))$，存在 $r\in\operatorname{elem}_{\mathsf{Route}_v}(\operatorname{routes}_{v,B,L}(A))$ 使：

$$
\operatorname{send}(m)=\operatorname{rtime}(r),
\qquad
\operatorname{dst}(m)\in\operatorname{rdst}(r).
\tag{A-4.4d}
$$

第五，出站消息序列中的标识符两两不同。若：

$$
\operatorname{outbox}_{v,B,L}(A)=(m_0,\ldots,m_{n-1}),
$$

则对任意 $i,j\in[n]$：

$$
\operatorname{id}(m_i)=\operatorname{id}(m_j)
\Longrightarrow
i=j.
\tag{A-4.4e}
$$

第六，路由记录序列中的标识符两两不同。若：

$$
\operatorname{routes}_{v,B,L}(A)=(r_0,\ldots,r_{q-1}),
$$

则对任意 $i,j\in[q]$：

$$
\operatorname{rid}(r_i)=\operatorname{rid}(r_j)
\Longrightarrow i=j.
\tag{A-4.4f}
$$

第七，局部输出记录序列中的标识符两两不同。若：

$$
\operatorname{localOut}_{v,B,L}(A)=(o_0,\ldots,o_{p-1}),
$$

则对任意 $i,j\in[p]$：

$$
\operatorname{oid}_{v,B,L}(o_i)
=
\operatorname{oid}_{v,B,L}(o_j)
\Longrightarrow i=j.
\tag{A-4.4g}
$$

定义节点完整产物集合：

$$
\mathsf{Artifact}_{v,B,L}
=
\{A\in\mathfrak A_{v,B,L}\mid A\text{ 是合法节点产物}\}.
\tag{D-4.4h}
$$

### 定义 4.5：节点参考转导器

节点参考转导器是确定函数：

$$
\operatorname{Ref}_{v,B,L}:
\mathfrak U_{v,B,L}\times\mathcal S_v
\to
\mathsf{Artifact}_{v,B,L}.
\tag{D-4.5}
$$

allocator 节点没有特殊的隐藏输入。若 $v$ 是 allocator，则 $\operatorname{Ref}_{v,B,L}$ 仍只能读取 $\mathbf U_v\in\mathfrak U_{v,B,L}$ 与左边界状态 $S_v^B\in\mathcal S_v$，并通过路由记录和出站消息影响拓扑下游节点。

### 定义 4.6：实现节点算子与精确节点契约

节点实现算子是函数：

$$
\mathcal C_{v,B,L}:
\mathfrak U_{v,B,L}\times\mathcal S_v
\to
\mathsf{Artifact}_{v,B,L}.
\tag{D-4.6}
$$

称 $\mathcal C_{v,B,L}$ 满足精确节点契约，当且仅当对所有 $\mathbf U\in\mathfrak U_{v,B,L}$ 与 $S\in\mathcal S_v$：

$$
\mathcal C_{v,B,L}(\mathbf U,S)
=
\operatorname{Ref}_{v,B,L}(\mathbf U,S).
\tag{A-4.6}
$$

该等式比较定义 4.4 中五个坐标的完整相等，而不仅是最终输出或最终状态。由于值域是 $\mathsf{Artifact}_{v,B,L}$，参考转导器和实现节点算子都只能返回合法节点产物。

### 定义 4.7：发送激活与实际发送目标

给定 $A\in\mathsf{Artifact}_{v,B,L}$，定义节点 $v$ 的发送激活轮次集合：

$$
\operatorname{Active}_{v,B,L}(A)
=
\{\tau\in\mathbb T_{B,L}\mid
\exists m\in
\operatorname{elem}_{\mathsf{Msg}_G}
(\operatorname{outbox}_{v,B,L}(A)),
\operatorname{send}(m)=\tau\}.
\tag{D-4.7a}
$$

若 $\tau\in\operatorname{Active}_{v,B,L}(A)$，称节点 $v$ 在绝对轮次 $\tau$ 发生一次发送激活。定义该轮次的实际发送目标集合：

$$
\operatorname{SentDst}_{v,B,L}(A,\tau)
=
\{\operatorname{dst}(m)\mid
m\in\operatorname{elem}_{\mathsf{Msg}_G}
(\operatorname{outbox}_{v,B,L}(A)),
\operatorname{send}(m)=\tau\}.
\tag{D-4.7b}
$$

发送激活只表示“至少产生一条发往空间后继的消息”。条件 $\tau\notin\operatorname{Active}_{v,B,L}(A)$ 不禁止节点状态变化；是否变化由节点参考转导器决定，并通过提交记录与右侧节点状态进入 artifact。路由记录中的 $\operatorname{rdst}(r)$ 是参考语义声明的允许或选择目标，而 $\operatorname{SentDst}_{v,B,L}(A,\tau)$ 是出站消息实际到达的目标。式 A-4.4d 只要求实际发送目标被某条同轮次路由记录覆盖，不要求每个被声明的目标都产生消息。

## 5. 窗口执行与拓扑序 chunk 调度

### 定义 5.1：节点入站原子构造

固定窗口 $(B,L)$、左边界延续状态：

$$
C_B=(\mathbf S^B,\mathcal M_B^\partial)\in\mathsf{Cont}_B,
$$

对每个节点 $v\in V$，定义其前驱 artifact 赋值集合：

$$
\mathsf{PredArtifact}_{v,B,L}
=
\prod_{u\in\operatorname{Pred}_G(v)}
\mathsf{Artifact}_{u,B,L}.
\tag{D-5.1a}
$$

取 $\mathbf P_v\in\mathsf{PredArtifact}_{v,B,L}$。对节点 $v\in V$，定义候选入站消息集合：

$$
\mathcal M_v(\mathbf P_v)
=
\{m\in\mathcal M_B^\partial\mid\operatorname{dst}(m)=v\}
\cup
\bigcup_{u\in\operatorname{Pred}_G(v)}
\{m\in\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{u,B,L}(\mathbf P_v(u)))\mid\operatorname{dst}(m)=v\}.
\tag{D-5.1b}
$$

定义窗口内可消费入站消息集合：

$$
\mathcal M_v^{\mathrm{in}}(\mathbf P_v)
=
\{m\in\mathcal M_v(\mathbf P_v)\mid\operatorname{arrival}(m)\in\mathbb T_{B,L}\}.
\tag{D-5.2}
$$

定义节点 $v$ 的输入原子集合：

$$
\mathcal A_v(\mathbf P_v)
=
\{(\mathtt{msg},m)\mid m\in\mathcal M_v^{\mathrm{in}}(\mathbf P_v)\}
\cup
\mathcal J_v,
\tag{D-5.3}
$$

其中：

$$
\mathcal J_v
=
\begin{cases}
\{(\mathtt{inj},t,x_t)\mid t\in\mathbb I_{B,L}\},&v=v_{\mathrm{in}},\\
\varnothing,&v\neq v_{\mathrm{in}}.
\end{cases}
$$

### 定义 5.2：由入站原子得到节点输入序列

对节点 $v$ 与前驱 artifact 赋值 $\mathbf P_v\in\mathsf{PredArtifact}_{v,B,L}$，定义轮次集合：

$$
\mathcal T_v(\mathbf P_v)
=
\{\operatorname{atime}_{v,B,L}(a)\mid a\in\mathcal A_v(\mathbf P_v)\}.
\tag{D-5.4}
$$

若：

$$
\mathcal T_v(\mathbf P_v)=\{\tau_0,\ldots,\tau_{n-1}\}
$$

且 $\tau_0<\cdots<\tau_{n-1}$，定义：

$$
\mathbf U_v(\mathbf P_v)
=
((\tau_0,A_0),\ldots,(\tau_{n-1},A_{n-1})),
\tag{D-5.5}
$$

其中：

$$
A_i=\{a\in\mathcal A_v(\mathbf P_v)\mid
\operatorname{atime}_{v,B,L}(a)=\tau_i\}.
$$

若 $\mathcal T_v(\mathbf P_v)=\varnothing$，定义 $\mathbf U_v(\mathbf P_v)$ 为空序列。

### 定义 5.3：窗口执行记录集合

定义窗口执行记录集合：

$$
\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})
=
\left\{
\mathbf A=(A_v)_{v\in V}
\in\prod_{v\in V}\mathsf{Artifact}_{v,B,L}
\ \middle|\
\forall v\in V,
A_v=
\operatorname{Ref}_{v,B,L}
(\mathbf U_v(\mathbf A|_{\operatorname{Pred}_G(v)}),\mathbf S^B(v))
\right\}.
\tag{D-5.6}
$$

其中 $\mathbf A|_{\operatorname{Pred}_G(v)}$ 是函数 $\mathbf A$ 在集合 $\operatorname{Pred}_G(v)$ 上的限制，因而属于 $\mathsf{PredArtifact}_{v,B,L}$。元素 $\mathbf A\in\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$ 称为窗口执行记录。式 D-5.6 是固定点式写法，但在空间 DAG 上它可以按拓扑序构造，不需要求解一般循环固定点。

### 定义 5.4：右边界延续状态与窗口读出

对窗口执行记录 $\mathbf A$，定义全消息集合：

$$
\mathcal M_{\mathrm{all}}(\mathbf A)
=
\mathcal M_B^\partial
\cup
\bigcup_{v\in V}
\operatorname{elem}_{\mathsf{Msg}_G}(\operatorname{outbox}_{v,B,L}(A_v)).
\tag{D-5.7}
$$

定义右边界在途消息集合：

$$
\mathcal M_{B+L}^\partial(\mathbf A)
=
\{m\in\mathcal M_{\mathrm{all}}(\mathbf A)
\mid
\operatorname{arrival}(m)=\beta(B+L)\}.
\tag{D-5.8}
$$

定义：

$$
\mathbf S^{B+L}_{\mathbf A}(v)=\operatorname{state}^+_{v,B,L}(A_v).
\tag{D-5.9}
$$

定义右边界候选延续状态：

$$
C_{B+L}(\mathbf A)
=
(\mathbf S^{B+L}_{\mathbf A},\mathcal M_{B+L}^\partial(\mathbf A)).
\tag{D-5.10}
$$

若对每个 $t\in\mathbb I_{B,L}$，$\operatorname{elem}_{\mathsf{Out}_{v_{\mathrm{out}},B,L}}(\operatorname{localOut}_{v_{\mathrm{out}},B,L}(A_{v_{\mathrm{out}}}))$ 中存在唯一记录 $(\omega,t,y_t)\in\mathsf{OID}\times\mathbb I_{B,L}\times Y$，则定义窗口读出函数：

$$
y_{\mathbf A}\in Y^{\mathbb I_{B,L}},
\qquad
y_{\mathbf A}(t)=y_t.
\tag{D-5.11}
$$

若唯一性条件不满足，则该窗口执行没有定义良好的窗口读出。

### 引理 5.5：右边界候选延续状态类型正确

对每个窗口执行记录 $\mathbf A\in\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$：

$$
C_{B+L}(\mathbf A)\in\mathsf{Cont}_{B+L}.
\tag{L-5.5}
$$

**证明。**

由式 D-5.9，$\mathbf S^{B+L}_{\mathbf A}\in\mathcal S_G$。由式 D-5.8，$\mathcal M_{B+L}^\partial(\mathbf A)$ 中每条消息的到达轮次都等于 $\beta(B+L)$。

还需证明 $\operatorname{UniqueMID}(\mathcal M_{B+L}^\partial(\mathbf A))$。左边界消息集合已经由 $C_B\in\mathsf{Cont}_B$ 满足 $\operatorname{UniqueMID}$。当 $L>0$ 时，左边界消息的到达轮次为 $\beta(B)$，不会进入式 D-5.8；当 $L=0$ 时，没有当前窗口出站消息，式 D-5.8 只保留原左边界消息。

对 $L>0$，式 D-5.8 中的消息都来自节点出站序列。若两条这类消息具有同一标识符，则其标识符的源节点坐标与发送轮次坐标相同。若源节点不同，标识符不可能相同；若源节点相同，则两条消息属于同一节点出站序列，式 A-4.4e 保证它们是同一序列位置上的同一消息。因此 $\mathcal M_{B+L}^\partial(\mathbf A)$ 满足 $\operatorname{UniqueMID}$。代入定义 3.3 即得式 L-5.5。

<div class="qed" aria-label="证毕">∎</div>

### 定义 5.6：节点拓扑序 chunk 调度

给定拓扑序：

$$
\pi=(v_0,\ldots,v_{|V|-1}).
$$

节点拓扑序 chunk 调度按 $i=0,\ldots,|V|-1$ 依次构造 $A_{v_i}$。

构造 $A_{v_i}$ 时，所有空间前驱 $u\in\operatorname{Pred}_G(v_i)$ 已经被处理。令 $\mathbf P_{v_i}$ 为已经构造出的 artifact 族在 $\operatorname{Pred}_G(v_i)$ 上的赋值，则 $\mathbf P_{v_i}\in\mathsf{PredArtifact}_{v_i,B,L}$，且 $\mathbf U_{v_i}(\mathbf P_{v_i})$ 可由定义 5.1 和定义 5.2 得到。然后令：

$$
A_{v_i}
=
\mathcal C_{v_i,B,L}
(\mathbf U_{v_i}(\mathbf P_{v_i}),\mathbf S^B(v_i)).
\tag{D-5.12}
$$

定义 2.4 的每个拓扑层 $V_j$ 内部不存在空间边，因此同一 $V_j$ 中的节点可以并行执行。每个节点被调用一次，但单次调用可以处理当前 chunk 中所有到达该节点的时间桶。

## 6. 主定理：显式 allocator DAG 的拓扑序 chunk 构造

### 定理 6.1：窗口执行记录唯一性与拓扑序 chunk 构造

固定 $B,L,R,G,C_B,x_{B:B+L}$。假设：

1. $G=(V,E)$ 满足定义 2.1 的有限空间 DAG 条件。
2. 每个节点实现算子 $\mathcal C_{v,B,L}$ 满足式 A-4.6 的精确节点契约。
3. allocator 节点只是满足定义 4.4、定义 4.5 和定义 4.6 的普通节点，不具有额外隐藏输入、隐藏状态读写或反向控制通道。

则：

1. 集合 $\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$ 至多包含一个元素。
2. 任意拓扑序 chunk 调度都构造出这个唯一窗口执行记录 $\mathbf A$。
3. 不同拓扑序 chunk 调度构造出的窗口执行记录相同。
4. 该执行记录给出的右边界延续状态 $C_{B+L}(\mathbf A)$ 由全部节点 artifact 唯一确定；若式 D-5.11 前的读出唯一性条件成立，则窗口读出 $y_{\mathbf A}$ 也唯一确定。

**证明。**

取拓扑序：

$$
\pi=(v_0,\ldots,v_{|V|-1}).
$$

先证明拓扑序 chunk 调度构造出的 $\mathbf A$ 满足式 D-5.6。对拓扑序下标 $i$ 作归纳。

当 $i=0$ 时，$v_0=v_{\mathrm{in}}$。因为定义 2.1 要求每个节点从 $v_{\mathrm{in}}$ 可达，任意非输入节点都必须在拓扑序中排在 $v_{\mathrm{in}}$ 之后。节点 $v_{\mathrm{in}}$ 没有空间前驱，所以 $\mathsf{PredArtifact}_{v_{\mathrm{in}},B,L}$ 只含空函数。记该函数为 $\mathbf P_{v_{\mathrm{in}}}$。定义 5.6 用当前窗口注入记录构造 $\mathbf U_{v_{\mathrm{in}}}(\mathbf P_{v_{\mathrm{in}}})$，再由式 A-4.6 得到：

$$
A_{v_{\mathrm{in}}}
=
\operatorname{Ref}_{v_{\mathrm{in}},B,L}
(\mathbf U_{v_{\mathrm{in}}}(\mathbf P_{v_{\mathrm{in}}}),\mathbf S^B(v_{\mathrm{in}})).
$$

假设结论已经对 $v_0,\ldots,v_{i-1}$ 成立。考虑 $v_i$。若 $u\in\operatorname{Pred}_G(v_i)$，则由拓扑序定义，$u$ 必在 $v_i$ 之前。因此所有前驱 artifact 已经构造完毕，前驱赋值 $\mathbf P_{v_i}$ 被唯一确定。左边界在途消息也是给定输入，所以 $\mathbf U_{v_i}(\mathbf P_{v_i})$ 被唯一确定。

定义 5.6 调用：

$$
\mathcal C_{v_i,B,L}
(\mathbf U_{v_i}(\mathbf P_{v_i}),\mathbf S^B(v_i)).
$$

由式 A-4.6，该值等于：

$$
\operatorname{Ref}_{v_i,B,L}
(\mathbf U_{v_i}(\mathbf P_{v_i}),\mathbf S^B(v_i)).
$$

所以式 D-5.6 中的节点方程对 $v_i$ 成立。归纳完成，式 D-5.6 中的节点方程对所有 $v\in V$ 成立。

接着证明唯一性。设 $\mathbf A,\mathbf A'\in\mathsf{Exec}_{B,L}(C_B,x_{B:B+L})$。仍按同一拓扑序做归纳。

当 $i=0$ 时，两个执行记录在 $v_{\mathrm{in}}$ 的前驱限制都是同一个空函数 $\mathbf P_{v_{\mathrm{in}}}$，所以：

$$
\mathbf U_{v_{\mathrm{in}}}(\mathbf A|_{\operatorname{Pred}_G(v_{\mathrm{in}})})
=
\mathbf U_{v_{\mathrm{in}}}(\mathbf A'|_{\operatorname{Pred}_G(v_{\mathrm{in}})}).
$$

由式 D-5.6 和 $\operatorname{Ref}_{v_{\mathrm{in}},B,L}$ 的确定性：

$$
A_{v_{\mathrm{in}}}=A'_{v_{\mathrm{in}}}.
$$

假设 $A_{v_j}=A'_{v_j}$ 对所有 $j<i$ 成立。对 $v_i$，所有空间前驱都在 $v_i$ 之前，所以：

$$
\mathbf A|_{\operatorname{Pred}_G(v_i)}
=
\mathbf A'|_{\operatorname{Pred}_G(v_i)}.
$$

因此：

$$
\mathbf U_{v_i}(\mathbf A|_{\operatorname{Pred}_G(v_i)})
=
\mathbf U_{v_i}(\mathbf A'|_{\operatorname{Pred}_G(v_i)}).
$$

再由式 D-5.6 和 $\operatorname{Ref}_{v_i,B,L}$ 的确定性：

$$
A_{v_i}=A'_{v_i}.
$$

归纳完成，$\mathbf A=\mathbf A'$。因此窗口执行记录至多存在一个；拓扑序 chunk 调度已经构造出一个，所以它就是唯一窗口执行记录。因为唯一性证明不依赖所选拓扑序，不同拓扑序调度构造出的记录也相同。

右边界延续状态由定义 5.4 的式 D-5.7--D-5.10 从 $\mathbf A$ 确定。若读出唯一性条件成立，则窗口读出由式 D-5.11 从 $A_{v_{\mathrm{out}}}$ 确定。因此两者都由全部节点 artifact 唯一确定。

<div class="qed" aria-label="证毕">∎</div>

### 推论 6.2：空间遍历次数不随 chunk 长度增长

在定理 6.1 的前提下，节点拓扑序 chunk 调度调用节点算子的次数等于 $|V|$，与 $L$ 无关。

若把定义 2.4 的同一拓扑层中的节点并行执行，则图级同步阶段数等于 $D_G$，且 $D_G\leq|V|$，也与 $L$ 无关。节点内部处理多少时间桶、多少消息和多少输入位置，属于节点算子的内部 work/span 问题。

**证明。**

定义 5.6 明确按拓扑序中每个节点构造一次 artifact。拓扑序长度为 $|V|$，所以节点算子调用次数为 $|V|$。由定义 2.4，拓扑层共有 $D_G$ 个；每层非空且各层两两不交，所以 $D_G\leq|V|$。

<div class="qed" aria-label="证毕">∎</div>

### 定义 6.3：窗口转导与时间分块组合律

对固定的全局输入流 $x$，定义窗口转导的定义域：

$$
\mathsf{Dom}_{B,L}
=
\left\{
C\in\mathsf{Cont}_B
\ \middle|\
\begin{array}{l}
\mathsf{Exec}_{B,L}(C,x_{B:B+L})=\{\mathbf A\}
\text{ 对某个 }\mathbf A,\\
y_{\mathbf A}\text{ 由式 D-5.11 定义}
\end{array}
\right\}.
\tag{D-6.3a}
$$

由定理 6.1，集合中的 $\mathbf A$ 若存在则唯一。定义部分函数：

$$
\Phi_{B,L}:\mathsf{Dom}_{B,L}
\to
\mathsf{Cont}_{B+L}\times Y^{\mathbb I_{B,L}}
$$

为：

$$
\Phi_{B,L}(C)
=
(C_{B+L}(\mathbf A),y_{\mathbf A}),
\tag{D-6.3b}
$$

其中 $\mathsf{Exec}_{B,L}(C,x_{B:B+L})=\{\mathbf A\}$。

给定 $L_1,L_2\in\mathbb N$、$y^{(1)}\in Y^{\mathbb I_{B,L_1}}$ 与 $y^{(2)}\in Y^{\mathbb I_{B+L_1,L_2}}$，定义拼接函数：

$$
y^{(1)}\mathbin{\|}y^{(2)}
\in Y^{\mathbb I_{B,L_1+L_2}}
$$

为：

$$
(y^{(1)}\mathbin{\|}y^{(2)})(t)
=
\begin{cases}
y^{(1)}(t),&t\in\mathbb I_{B,L_1},\\
y^{(2)}(t),&t\in\mathbb I_{B+L_1,L_2}.
\end{cases}
\tag{D-6.3c}
$$

称窗口转导族 $(\Phi_{B,L})_{B,L\in\mathbb N}$ 满足时间分块组合律，当且仅当对所有 $B,L_1,L_2\in\mathbb N$ 和 $C\in\mathsf{Dom}_{B,L_1}$，若：

$$
\Phi_{B,L_1}(C)=(C',y^{(1)}),
\qquad
C'\in\mathsf{Dom}_{B+L_1,L_2},
$$

且：

$$
\Phi_{B+L_1,L_2}(C')=(C'',y^{(2)}),
$$

则 $C\in\mathsf{Dom}_{B,L_1+L_2}$，并且：

$$
\Phi_{B,L_1+L_2}(C)
=
(C'',y^{(1)}\mathbin{\|}y^{(2)}).
\tag{A-6.3}
$$

式 A-6.3 才是把一个长 chunk 与两个相邻短 chunk 联系起来的正式条件。反复取 $L_1=1$ 后，它给出长 chunk 与逐 token 窗口执行之间的数学等价。

### 命题 6.4：空间拓扑序构造不自动推出时间分块组合律

定义 0--5 与定理 6.1 的前提不蕴含式 A-6.3。

**证明。**

取 $X=\{x_*\}$、$Y=\{0,1\}$、$R=1$，空间图只有节点 $v_{\mathrm{in}},v_{\mathrm{out}}$ 和边 $(v_{\mathrm{in}},v_{\mathrm{out}})$。令所有节点状态集合与消息载荷集合都是单元素集合；令所有节点转导器都不产生路由记录和出站消息，并保持节点状态不变。取 $\mathsf{OID}=\mathbb N\times\mathbb N$。

输出节点参考转导器对每个 $t\in\mathbb I_{B,L}$ 产生唯一局部输出记录，并规定：当 $L=1$ 时输出值为 $0$，当 $L>1$ 时输出值为 $1$；记录标识符取 $(L,t)$。实现节点算子取为对应参考转导器本身。由定理 6.1，每个窗口都有唯一拓扑序执行记录。

但是，长度为 $2$ 的单个窗口输出为 $(1,1)$，两个连续的长度为 $1$ 的窗口输出拼接为 $(0,0)$。因此式 A-6.3 不成立。

<div class="qed" aria-label="证毕">∎</div>

命题 6.4 表明，当前主定理严格证明的是空间调度性质。下一步若要证明 `prefill = decode`，必须再给出逐绝对轮次的节点参考转移，并证明 $\operatorname{Ref}_{v,B,L}$ 是这些逐轮转移在 $\mathbb T_{B,L}$ 上的折叠；或者直接证明整个窗口转导族满足式 A-6.3。只有在加入这一层之后，才可以把节点拓扑序 chunk 执行称为逐轮 decode 执行的等价重排。

## 7. 不等长路径如何进入模型

### 7.1 不等长路径不是 allocator 的障碍

不等长路径只会导致同一节点在不同绝对轮次收到不同路径上的消息。定义 4.2 已把节点输入写成按绝对轮次排序的时间桶序列：

$$
\mathbf U_v=((\tau_0,A_0),\ldots,(\tau_{n-1},A_{n-1})).
$$

因此，节点不需要知道“所有路径是否等长”。它只需要处理已经到达本节点、且到达轮次落在当前窗口可消费轮次集合 $\mathbb T_{B,L}$ 内的输入桶。

### 7.2 长路径跨 chunk 的处理

在单位边时延模型中，若某条消息 $m$ 满足：

$$
\operatorname{arrival}(m)=\beta(B+L),
$$

则它不会在当前窗口被消费，而是由式 D-5.8 放入右边界在途消息集合 $\mathcal M_{B+L}^\partial$。下一个窗口从 $C_{B+L}$ 开始时再继续消费它。

一条较长空间路径不是由同一消息跨越多条边完成，而是由相邻节点依次产生的新消息完成。因而在任意窗口切面上，单条在途消息只位于一条边上；较长路径的整体影响可以经过多个窗口继续传播。

所以 general DAG 从中间开始执行时，不需要重新注入历史输入。历史影响只通过两类对象进入当前窗口：

1. 左边界节点状态 $\mathbf S^B$。
2. 左边界在途消息 $\mathcal M_B^\partial$。

### 7.3 输出时延是语义选择

按式 D-1.4，第 $t$ 个输出位置的名义读出切面是 $\tau_{\mathrm{read}}(t)=\beta(t+1)$。若希望某条从 $v_{\mathrm{in}}$ 到 $v_{\mathrm{out}}$ 的路径影响同一输入位置的输出，则外部周期 $R$ 和输出节点参考转导器必须让该路径的消息在该切面前到达并被消费。

若 $R$ 较小，较长路径的消息可以合法地跨过当前读出切面，成为影响未来窗口的上下文消息。这不是调度错误，而是不同参考语义。设计时必须明确：

1. 哪些路径被允许影响同一位置输出。
2. 哪些路径只允许作为未来上下文。
3. 哪些消息到右边界时必须被保留为在途消息。

当前窗口级参考转导器尚未被约束为只能使用名义读出切面之前的输入来产生 $y_t$。因此本节给出的是待满足的读出语义要求，不是定理 6.1 已经证明的 token-prefix causality；该缺口已列入第 11 节。

## 8. allocator 抽象与负载均衡自由度

### 定义 8.1：通信局部性与发送激活稀疏性

给定关系：

$$
\mathsf{Near}\subseteq V\times V.
$$

称 $G=(V,E)$ 对 $\mathsf{Near}$ 是通信局部的，当且仅当：

$$
E\subseteq\mathsf{Near}.
\tag{D-8.1a}
$$

$\mathsf{Near}$ 可以由几何邻接、Delaunay 邻接、固定半径邻接或其他设计规则给出；本页定理只使用 $E$ 是 DAG，不预设 $\mathsf{Near}$ 的具体构造。

给定非空有限集合：

$$
\mathscr R
\subseteq
\mathcal P_{\mathrm{fin}}(V)\setminus\{\varnothing\},
$$

其元素称为观测区域。给定函数：

$$
\kappa:\mathscr R\times\mathbb N\to\mathbb N,
$$

称为区域发送预算。对窗口执行记录 $\mathbf A=(A_v)_{v\in V}$，称 $\mathbf A$ 满足 $(\mathscr R,\kappa)$-发送稀疏性，当且仅当对每个 $Q\in\mathscr R$ 与 $\tau\in\mathbb T_{B,L}$：

$$
\left|
\{v\in Q\mid
\tau\in\operatorname{Active}_{v,B,L}(A_v)\}
\right|
\leq
\kappa(Q,\tau).
\tag{D-8.1b}
$$

式 D-8.1a 与式 D-8.1b 是两个不同性质。局部空间连接只限制一条消息可以发往哪些节点；若每个节点都向许多后继发送，分岔仍可能使发送激活迅速覆盖大部分空间图。发送稀疏性另外限制每个绝对轮次、每个观测区域中实际发送消息的节点数。

未发生发送激活的节点仍可更新本地状态。因而本页使用“发送激活”指式 D-4.7a 定义的消息发射性质，不把它等同于“节点 kernel 完全未执行”，也不把它等同于神经网络张量中的 activation value。

### 8.2 allocator 的安全约束

在本页模型中，allocator 安全性的关键不是“它是否复杂”，而是“它是否显式位于空间 DAG 中”。显式 allocator 必须满足：

1. 它读取的当前窗口动态信息只能来自拓扑上游消息。
2. 它读取的历史负载、quota、统计量或 learned 参数必须属于自己的左边界状态 $\mathbf S^B(v)$，或由上游消息携带。
3. 它输出的路由决定只能通过路由记录与出站消息影响拓扑下游节点；发送激活由式 D-4.7a 从出站消息导出。
4. 它不能读取拓扑下游节点在当前窗口中尚未提交的状态。
5. 它不能反向改变拓扑上游节点在当前窗口中的计算结果。

这些约束已经由定义 4.4、定义 4.5、定义 4.6 和定理 6.1 的前提表达：节点转导器的输入只有 $\mathbf U_v$ 与 $S_v^B$，出站影响只能沿 $E$ 前向传播。

上述约束足以保持定理 6.1 的空间拓扑序构造，但不自动保证式 A-6.3。若 allocator 的窗口级决定依赖 chunk 长度，或其状态更新不能分解为逐轮转移的折叠，命题 6.4 的同类反例仍然成立。因此每一种 stateful、quota-based 或 learned allocator 还必须单独证明时间分块组合律。

### 8.3 allocator 的放置范围与实现方式

allocator 的放置范围可以分为：

1. **Level 0：无 allocator**。普通节点按固定规则向所有后继或固定后继子集发送消息。
2. **Level 1：节点局部选择**。普通节点的参考转导器根据自己的状态和入站消息决定实际出站消息；这里没有独立的 allocator 节点。
3. **Level 2：显式局部 allocator 节点**。若干上游节点向一个 allocator 节点发送摘要，allocator 再向拓扑下游发送决定或数据消息。
4. **Level 3：显式区域 allocator 子图**。一个由多个显式节点构成的 allocator 子图汇总若干上游分支并分配下游容量；该子图的全部边仍属于空间 DAG。

固定规则、带历史状态的规则与 learned 规则是另一条独立维度，而不是上述放置范围之后的新 Level。任一 Level 都可以采用确定的固定函数、读取本节点左边界状态的有状态函数，或由训练得到的函数；数学上它们都属于相应节点参考转导器。

Level 3 可以表达比节点局部选择更强的区域负载均衡，但不能退化为隐藏全局 selector。只要 allocator 子图读取和影响的方向仍遵守空间 DAG，定理 6.1 仍适用。

### 8.4 当前模型是否要求全部路由进入 allocator

当前定义不要求全部路由决定只能由角色为 $\mathtt{allocator}$ 的节点产生。定义 4.5 允许每个普通计算节点的参考转导器根据本节点状态和入站消息产生路由记录与出站消息；因此 Level 1、Level 2 和 Level 3 都可表达。

“所有稀疏激活与路由都由显式 allocator 产生，其他节点只做计算、状态更新并按命令发送”是一个更强的 allocator normal form。若采用该形式，还必须新增至少三个正式对象：

1. allocator 命令集合。
2. 命令消息与被控制计算节点之间的对应关系。
3. 普通节点只在收到何种命令时允许产生哪些出站消息的合法性条件。

这些对象尚未进入当前最低层定义。因而本页已经证明显式 allocator 可以安全嵌入一般空间 DAG，但尚未证明任意节点局部选择都能无代价地改写成“全部决定集中到 allocator 节点”的 normal form。

### 8.5 与 LH selector 的区别

LH 的空间图局部连接首先保证通信局部性，但不自动保证发送稀疏性。LH 风格 selector 可以被理解为一个隐式 allocator：它读取一个范围内多个节点的当前信息，再联合决定其中哪些节点继续产生消息。它同时承担稀疏化与负载均衡，但若其读取集合和影响集合跨越空间拓扑的前后方向，就会在显式 DAG 之外创建隐藏依赖边，破坏一次拓扑序 chunk 调度。

本页方案不是取消 selector 的功能，而是把 selector 显式化为 allocator 节点或 allocator 子图。显式化之后：

1. selector 的输入成为 allocator 的入站消息。
2. selector 的内部负载状态成为 allocator 的节点状态。
3. selector 的路由结果成为路由记录与出站消息 artifact，发送激活集合由出站消息导出。
4. selector 的依赖边必须进入空间 DAG。

## 9. artifact equality

### 定义 9.1：节点 artifact equality

给定节点 $v$、输入序列 $\mathbf U\in\mathfrak U_{v,B,L}$ 和左状态 $S\in\mathcal S_v$。设参考产物：

$$
A^{\mathrm{ref}}
=
\operatorname{Ref}_{v,B,L}(\mathbf U,S),
$$

实现产物：

$$
A^{\mathrm{impl}}
=
\mathcal C_{v,B,L}(\mathbf U,S).
$$

称节点 $v$ 在 $(\mathbf U,S)$ 上满足 artifact equality，当且仅当：

$$
A^{\mathrm{impl}}=A^{\mathrm{ref}}.
\tag{D-9.1}
$$

根据定义 4.4，这要求同时比较：

1. 局部输出记录序列。
2. 状态提交记录序列。
3. 路由记录序列。
4. 出站消息序列。
5. 右侧节点状态。

allocator 的路由记录由 $\operatorname{routes}_{v,B,L}$ 给出；实际发送目标和发送激活集合由 $\operatorname{outbox}_{v,B,L}$ 按定义 4.7 导出。因此 allocator 方案可以对路由决定、实际消息与发送稀疏性做 artifact equality 检查。

### 推论 9.2：节点 artifact equality 推出窗口产物相等

在定理 6.1 的前提下，若每个节点实现都满足定义 9.1，则拓扑序 chunk 调度得到的全部节点 artifact 与右边界延续状态等于参考转导器定义出的对应对象；若读出唯一性条件成立，则窗口读出也相等。

**证明。**

定义 9.1 等价于式 A-4.6。将其代入定理 6.1 即得。

<div class="qed" aria-label="证毕">∎</div>

## 10. `owner / frontier` 在本页之外的位置

本页最低层模型没有使用 `owner / frontier`。这不是说它们无用，而是把职责分开：

1. 一般空间 DAG、不等长路径、显式 allocator 和跨 chunk 在途消息，只需要消息标识符、到达轮次、源节点、目标节点和载荷。
2. 若要证明自回归 token-prefix causality，需要额外说明每个输出 $y_t$ 不能依赖 $x_{t+1},x_{t+2},\ldots$。这可以通过 `owner / frontier` 字段证明，也可以通过其他因果证书证明。
3. 若要调试同一轮次多 token 消息的归属、融合输出、读出归因或 prefix leakage，`owner / frontier / support` 是有用的增强字段。
4. 若加入这些字段，它们应作为消息记录和局部输出记录的额外坐标，而不改变本页的空间 DAG、节点状态、边界延续状态和 artifact equality 主结构。

因此，[[token-owned-general-dag-routing]] 更适合作为本页的增强语义版本：它处理 token 归属、因果前沿、同刻融合与更细读出约束；本页则保留当前主线所需的最低空间 DAG 与显式 allocator 框架。

## 11. 当前设计边界

本页可以支持：

1. 一般有限空间 DAG。
2. 不等长路径。
3. 从任意全局位置 $B$ 开始的 chunk 执行。
4. 跨 chunk 在途消息。
5. 显式 allocator 节点或 allocator 子图。
6. 节点级与 allocator 级 artifact equality。
7. 常数次空间拓扑遍历的 chunk 调度。
8. 对通信局部性与区域发送稀疏性分别建模。

本页尚未支持或尚未证明：

1. 空间图中有环。
2. 隐式全局 selector。
3. 当前窗口内读取下游动态状态后再反向影响上游。
4. 任意节点 kernel 的低 span 实现。
5. 式 A-6.3 的时间分块组合律；因此当前空间拓扑序定理尚不等同于完整的 `prefill = decode` 定理。
6. 自回归 token-prefix causality 的完整证明。
7. “全部路由只能由 allocator 产生”的 normal form 及其表达力、性能保持证明。
8. 反向传播、浮点误差、设备后端或 Ascend NPU lowering。

下一步应在本页框架内分别研究三类节点 kernel：

1. 已知可 chunk 化的 dense / attention / SSM / FFN kernel。
2. 可由 scan、reduce、segmented pack 支持的局部状态 kernel。
3. 显式 allocator kernel，包括负载历史、quota、容量分配和 learned scoring。
4. 逐绝对轮次节点参考转移及其窗口折叠，用于证明式 A-6.3。
