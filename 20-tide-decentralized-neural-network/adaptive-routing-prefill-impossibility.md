---
type: note
status: draft
cssclasses:
  - textbook-math
tags:
  - tide
  - prefill-decode
  - lower-bound
  - adaptive-routing
  - math
---

# Adaptive Routing Prefill Impossibility

> [!summary] 本页定位
> 本页研究一个证否问题：当早期 token 的晚期 Graph 信号以不可预知的方式决定后续 token 的 routing 时，是否存在对整个模型类别都有效的、精确且 work-efficient 的高性能 chunk prefill。正文先给出自足的黑盒查询模型，再证明自适应路由链的并行轮数下界，最后说明该结论如何嵌入局部通信、超稀疏的 Tide Graph。

> [!note] 与构造性主线的关系
> [[step-transition-mathematical-specification]] 主要给出 chunk correctness 的构造性充分条件；本页给出一般动态 routing 的反向边界。它不证明每一个跨 token routing 模型都无法并行，而是证明：只要模型类别允许任意、不可组合的 pointer-chasing 式 routing，就不存在对该类别所有实例都有效的通用高性能 exact prefill。

> [!warning] 结论强度
> “早期 token 可以影响后续 routing”本身不足以推出不可能性。若影响可表示为 prefix sum、affine scan、有限且紧凑的函数复合，仍可能并行。本页下界依赖四个明确条件：exactness、自适应地址依赖、黑盒 transition、以及不枚举整个 routing state space 的 work budget。

## 0. 结论概览

本页证明的核心结论是：

> 对长度为 $L$ 的任意自适应路由链，若 routing state space 足够大，算法必须精确处理所有 transition，又只允许接近 reference route chain 的工作量，那么每一轮并行查询至多可靠推进一个 routing step。因此 adaptive depth 至少为 $L$，不能得到 $o(L)$ 的 token-axis chunk prefill。

这个结论直接对应以下 Tide-like 情形：

```text
早期 token 的晚期信号
-> 决定后续 token 应访问哪个 node
-> 该 node 的输出再决定更后续 token 的 node
-> 路由地址只能随执行逐步揭示
```

证明路线为：

```text
反例：跨 token 影响不必然串行
-> 定义任意 routing transition
-> 定义 parallel query round
-> 定义 exactness、work 与 adaptive depth
-> 证明 fresh-address lemma
-> 证明一轮至多推进一个未知路由
-> 得到 Omega(L) adaptive-depth 下界
-> 嵌入局部通信、超稀疏 Graph
```

## 1. 为什么“跨 Token 影响”还不足以证否

这一节先给出两个正例，说明必须把待证明命题收紧到“自适应地址依赖”，而不能只写“前序 token 影响后序 token”。

本页所说的 `parallel prefix scan` 指：给定满足结合律的二元运算 $\otimes$ 和序列 $(a_0,\ldots,a_{L-1})$，用平衡树式组合同时计算所有前缀：

$$
a_0,
\quad
a_0\otimes a_1,
\quad\ldots,\quad
a_0\otimes\cdots\otimes a_{L-1}.
$$

结合律保证不同括号顺序得到相同结果，因此不必严格按从左到右的顺序逐项计算。

### 例 1.1：前缀异或

令：

$$
q_0=0
$$

并对 $t=0,1,\ldots,L-1$ 定义：

$$
q_{t+1}=q_t\mathbin{\mathrm{xor}}b_t,
$$

其中 $b_t\in\{0,1\}$。这里 $\mathrm{xor}$ 表示二进制异或：两个输入不同时结果为 $1$，相同时结果为 $0$。

每个 $q_{t+1}$ 都依赖 $q_t$，但 `xor` 满足结合律：

$$
(a\mathbin{\mathrm{xor}}b)\mathbin{\mathrm{xor}}c
=
a\mathbin{\mathrm{xor}}(b\mathbin{\mathrm{xor}}c).
$$

因此全部 prefix values 可以通过 parallel prefix scan 计算。这里存在跨 token 依赖，却不存在本页要证明的不可并行性。

### 例 1.2：仿射 recurrence

令 routing state 属于实数向量空间，并定义：

$$
q_{t+1}=A_tq_t+b_t.
$$

把单步 transition 表示成 pair $(A_t,b_t)$，定义组合：

$$
(A_2,b_2)\otimes(A_1,b_1)
=
(A_2A_1,A_2b_1+b_2).
$$

这个组合满足结合律，所以同样可以 scan。Mamba/SSM 的部分高性能 prefill 路线属于这一类结构化 recurrence。

### 本页真正研究的问题

本页研究的不是一般 recurrence，而是：

> 下一次 transition 应该在哪个 routing address 上执行，只有前一次 transition 返回后才能知道；transition family 又不承诺任何可供 scan 或 bulk composition 使用的代数结构。

这种计算通常称为 `pointer chasing`。本页不预设读者了解该术语，后续将从集合、函数和查询开始完整定义。

## 2. 基础记号

### 定义 2.1：自然数与有限下标集

定义：

$$
\mathbb N=\{0,1,2,\ldots\}.
$$

定义正整数集合：

$$
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

记非负实数集合为：

$$
\mathbb R_{\geq0}=\{x\in\mathbb R\mid x\geq0\}.
$$

对任意 $L\in\mathbb N$，定义：

$$
[L]=\{0,1,\ldots,L-1\}.
$$

若 $L=0$，则 $[L]=\varnothing$。

### 定义 2.2：有限序列

给定集合 $A$ 与长度 $L\in\mathbb N$，一个长度为 $L$ 的 $A$-值序列是函数：

$$
a:[L]\to A.
$$

记：

$$
a_t=a(t),
$$

并写成：

$$
a_{0:L}=(a_0,a_1,\ldots,a_{L-1}).
$$

### 定义 2.3：二进制对数

对任意实数 $x>0$，$\log_2x$ 表示以 $2$ 为底的对数。本页写 $\log x$ 时均指 $\log_2x$。

### 定义 2.4：渐近上界 $O$

设 $f,g:\mathbb N\to\mathbb R_{\geq 0}$。若存在常数 $c>0$ 和 $L_0\in\mathbb N$，使对所有 $L\geq L_0$：

$$
f(L)\leq c g(L),
$$

则记：

$$
f(L)=O(g(L)).
$$

### 定义 2.5：渐近下界 $\Omega$

设 $f,g:\mathbb N\to\mathbb R_{\geq 0}$。若存在常数 $c>0$ 和 $L_0\in\mathbb N$，使对所有 $L\geq L_0$：

$$
f(L)\geq c g(L),
$$

则记：

$$
f(L)=\Omega(g(L)).
$$

### 定义 2.6：严格次线性 $o(L)$

设 $f:\mathbb N\to\mathbb R_{\geq 0}$。若：

$$
\lim_{L\to\infty}\frac{f(L)}{L}=0,
$$

则记：

$$
f(L)=o(L).
$$

直观上，$f(L)=o(L)$ 表示 $f$ 的增长速度严格慢于线性增长。

### 定义 2.7：Polylog 因子

若存在常数 $c>0$ 与整数 $k\in\mathbb N$，使：

$$
f(L)\leq c\bigl(\log(L+2)\bigr)^k,
$$

则称 $f(L)$ 至多是一个 polylogarithmic factor，简称 `polylog factor`。

式中使用 $L+2$，只是为了让 $L=0$ 或 $L=1$ 时对数仍有定义且为正数。

### 定义 2.8：有向图、路径与 DAG

一个有限有向图是 pair：

$$
G=(V,E),
$$

其中 $V$ 是有限节点集合，$E\subseteq V\times V$ 是有向边集合。

若：

$$
(v_i,v_{i+1})\in E,
\qquad 0\leq i<m,
$$

则节点序列：

$$
(v_0,v_1,\ldots,v_m)
$$

称为一条有向路径。

若一条非空路径从某节点出发并回到同一节点，则称它包含一个有向环。没有任何有向环的有限有向图称为有向无环图，英文为 `directed acyclic graph`，简称 `DAG`。

节点 $v$ 的出度是从 $v$ 出发的有向边数量：

$$
\operatorname{outdeg}(v)
=
|\{u\in V\mid(v,u)\in E\}|.
$$

## 3. 自适应路由链

### 定义 3.1：Routing state space

给定整数 $N\in\mathbb N_{>0}$，定义 routing state space：

$$
\Omega_N=\{0,1,\ldots,N-1\}.
$$

一个元素 $q\in\Omega_N$ 可以表示：

- 下一个应激活的 node address。
- 下一个应读取的 memory address。
- selector 选择的 branch id。
- 下一次 local kernel 应处理的 routing state。

### 定义 3.2：Routing oracle

一个 routing oracle 是函数：

$$
F:\Omega_N\to\Omega_N.
$$

称它为 `oracle`，表示算法不能直接读取整个函数表或假定它具有线性、仿射、结合律等内部结构。算法只能选择一个输入 $q\in\Omega_N$，获得对应的函数值 $F(q)$。

这只是一个明确的黑盒计算模型，不表示实际 Tide kernel 必须由外部服务实现。实际 node/kernel 只要在所研究的抽象层上被视为“必须执行后才知道输出”，就可以用 oracle query 表示。

### 定义 3.3：长度为 $L$ 的 routing oracle family

给定 $L\in\mathbb N_{>0}$，一个长度为 $L$ 的 routing oracle family 是函数序列：

$$
F_{0:L}=(F_0,F_1,\ldots,F_{L-1}),
$$

其中每个：

$$
F_t:\Omega_N\to\Omega_N.
$$

Token value、internal round state、node hidden 或其他确定信息，都可以吸收到相应 $F_t$ 的定义中。因此本页不再为 token value 单独增加一个参数。

### 定义 3.4：Reference route chain

给定初始 routing state：

$$
q_0\in\Omega_N,
$$

递归定义：

$$
q_{t+1}=F_t(q_t),
\qquad t\in[L].
\tag{AR-1}
$$
^eq-adaptive-routing-chain

称：

$$
q_{0:L+1}=(q_0,q_1,\ldots,q_L)
$$

为由 $(F_{0:L},q_0)$ 生成的 reference route chain。

### 定义 3.5：可观察结果

本页把最终 routing state $q_L$ 作为计算的可观察结果。也就是说，算法必须输出 $q_L$ 本身，而不是只输出某个无法区分不同 routing states 的常量。

在 Tide 中，这一条件可以通过以下任一方式满足：

- $q_L$ 决定最终 output node。
- $q_L$ 决定输出 logits。
- $q_L$ 属于 semantic contract 要求保持的最终 persistent state。
- 两个不同的 $q_L$ 会导致后续合法输入上的可观察行为不同。

更一般地，若实际模型只观察函数：

$$
\alpha:\Omega_N\to Z,
$$

并且只要求算法输出 $\alpha(q_L)$，那么本页证明需要保证最终构造的 $a,b$ 满足：

$$
\alpha(a)\neq\alpha(b).
$$

若 $\alpha$ 把所有 routing states 都映射到同一个结果，本页下界不适用于这个被弱化后的观察问题。

### 例 3.6：地址追逐

若 $q_t$ 表示当前 node address，而 node $q_t$ 的 local selector 返回下一个 node address：

$$
q_{t+1}=F_t(q_t),
$$

那么计算 $q_L$ 就必须沿着实际选中的 addresses 逐步前进。这就是后文所谓 pointer chasing。

## 4. Parallel Query Algorithm

这一节定义“算法可以并行做什么”。

### 定义 4.1：Oracle query

一个 oracle query 是 pair：

$$
(t,q)\in[L]\times\Omega_N.
$$

它的返回值定义为：

$$
\operatorname{Ans}(t,q)=F_t(q).
$$

一次 query 对应一次实际 local transition evaluation、一次 node routing evaluation，或者对 routing table 中一个地址的读取。

### 定义 4.2：Parallel query round

第 $r$ 个 parallel query round 由一个有限 query set：

$$
B_r\subseteq[L]\times\Omega_N
$$

组成。

该轮中所有 queries 同时提交；算法只有在整个 $B_r$ 的答案返回后，才能根据这些答案构造下一轮 $B_{r+1}$。

因此，同一轮中的 query 不能依赖该轮中另一个 query 的返回值。

### 定义 4.3：Deterministic parallel query algorithm

一个 deterministic parallel query algorithm $\mathcal A$ 按以下规则工作：

1. 在第 $0$ 轮开始前，只知道 $L,N,q_0$ 与算法自身代码。
2. $B_0$ 只能由 $L,N,q_0$ 决定。
3. 对 $r\geq1$，$B_r$ 可以由 $L,N,q_0$ 和前 $r$ 轮的全部 queries 与 answers 决定。
4. 执行有限轮后，算法输出某个 $\widehat q_L\in\Omega_N$。

算法是 deterministic，表示相同的已知信息总会产生相同的下一轮 queries 和相同输出。

### 定义 4.4：Query transcript

算法执行到某一轮后，所有已经提交的 queries 及其 answers 的有序记录称为 query transcript。

两个 oracle families 若对 transcript 中出现的所有 queries 都给出相同答案，则算法到当前时刻无法区分这两个 oracle families。

### 定义 4.5：Exactness

若对任意 oracle family $F_{0:L}$ 与任意初始状态 $q_0\in\Omega_N$，算法输出均满足：

$$
\widehat q_L=q_L,
$$

其中 $q_L$ 由式 [[#^eq-adaptive-routing-chain|AR-1]] 定义，则称算法对长度 $L$ 的自适应路由链是 exact 的。

### 定义 4.6：Query work

若算法执行 $R$ 个 parallel query rounds，定义总 query work：

$$
Q_{\mathcal A}
=
\sum_{r=0}^{R-1}|B_r|.
\tag{AR-2}
$$
^eq-query-work

重复提交同一个 query 仍计入 work。一个最保守的算法只沿实际 route chain 查询：

$$
(0,q_0),(1,q_1),\ldots,(L-1,q_{L-1}),
$$

其 query work 为 $L$。

本页只用 query work 建立下界，没有把普通算术、memory movement 或调度开销计入 $Q_{\mathcal A}$。把这些额外成本加入总 work 只会使算法更昂贵，不会削弱后面的 query lower bound。

### 定义 4.7：Adaptive depth

算法从开始到输出经历的 parallel query round 数量称为 adaptive depth，记为：

$$
R_{\mathcal A}.
$$

这个量只计算“必须等待上一批答案后才能决定下一批 queries”的轮数，不计算同一轮内部有多少 queries。

### 定义 4.8：Parallel query algorithm scheme

一个 parallel query algorithm scheme 是一族算法：

$$
\mathfrak A
=
(\mathcal A_{L,N})_{L\geq1,N\geq1},
$$

其中 $\mathcal A_{L,N}$ 处理长度为 $L$、routing state space size 为 $N$ 的实例。

若每个 $\mathcal A_{L,N}$ 都满足定义 4.5 的 exactness，则称 algorithm scheme $\mathfrak A$ 是 exact 的。

### 定义 4.9：Work-efficient algorithm scheme

若存在常数 $c>0$、$k\in\mathbb N$ 与 $L_0\in\mathbb N$，使对所有 $L\geq L_0$ 和所有 $N\geq1$：

$$
Q_{\mathcal A_{L,N}}
\leq
cL\bigl(\log(L+2)\bigr)^k,
\tag{AR-3}
$$
^eq-work-efficient

则称 $\mathfrak A$ 相对于长度为 $L$ 的 reference route chain 是 work-efficient 的。

这里的上界对 $N$ 一致成立。这个定义允许相对于 reference route chain 的 polylog overhead，但不允许为了避免自适应等待而枚举一个远大于实际 route chain 的 routing state space。

### 定义 4.10：Token-axis high-performance prefill

若 algorithm scheme $\mathfrak A$ exact、work-efficient，并且存在函数 $r:\mathbb N\to\mathbb R_{\geq0}$ 满足：

$$
r(L)=o(L),
\tag{AR-4}
$$
^eq-high-performance-prefill

且对所有 $L,N\geq1$：

$$
R_{\mathcal A_{L,N}}\leq r(L),
$$

则称 $\mathfrak A$ 在本页模型中具有 token-axis high-performance prefill。

这是一个数学上的必要性能区分，不是完整的硬件性能模型。实际时间还受 kernel work、memory bandwidth、communication 与设备利用率影响。

## 5. 两个初等引理

### 引理 5.1：Fresh address lemma

设 $U\subseteq\Omega_N$，且：

$$
|U|\leq N-1.
$$

则存在 $q\in\Omega_N$，使：

$$
q\notin U.
$$

**证明。**

集合 $\Omega_N$ 有 $N$ 个元素，而 $U$ 至多有 $N-1$ 个元素。因此 $U$ 不可能包含 $\Omega_N$ 的全部元素，至少有一个 $q\in\Omega_N$ 不属于 $U$。

<div class="qed" aria-label="证毕">∎</div>

### 引理 5.2：两个 fresh addresses

设 $U\subseteq\Omega_N$，且：

$$
|U|\leq N-2.
$$

则存在两个不同的 $a,b\in\Omega_N$，使：

$$
a\notin U,
\qquad
b\notin U,
\qquad
a\neq b.
$$

**证明。**

补集 $\Omega_N\setminus U$ 至少包含：

$$
N-(N-2)=2
$$

个元素。从中选取两个不同元素，分别记为 $a,b$，结论成立。

<div class="qed" aria-label="证毕">∎</div>

## 6. 自适应路由链下界

### 定理 6.1：Exact adaptive routing lower bound

给定：

- 长度 $L\in\mathbb N_{>0}$。
- Query budget $Q\in\mathbb N$。
- Routing state space size $N\in\mathbb N_{>0}$。
- 一个 deterministic parallel query algorithm $\mathcal A$。

假设：

1. $\mathcal A$ 对所有 routing oracle families $F_{0:L}$ 都是 exact 的。
2. $\mathcal A$ 在任意 oracle family 上的总 query work 都不超过 $Q$。
3. Routing state space 满足：

$$
N\geq Q+L+2.
\tag{AR-5}
$$
^eq-domain-size-condition

那么：

$$
R_{\mathcal A}\geq L.
\tag{AR-6}
$$
^eq-adaptive-depth-lower-bound

即任意 exact 且不枚举 routing state space 的算法，至少需要 $L$ 个 adaptive query rounds。

**证明。**

证明使用一种逐轮构造 oracle answers 的方法。这里的“构造者”只是数学证明中的选择规则，不是实际系统中的攻击者。若同一个 query 被重复提交，构造始终返回第一次已经选定的相同 answer，从而保证全部 answers 最终可以补全为真正的函数。

开始时，$q_0$ 已知。称 chain prefix：

$$
q_0,q_1,\ldots,q_k
$$

已经揭示，表示对所有 $0\leq t<k$，query：

$$
(t,q_t)
$$

已经返回，并且其答案满足：

$$
F_t(q_t)=q_{t+1}.
$$

初始时只有 $q_0$ 已知，所以已揭示 prefix 的长度参数为 $k=0$。

现在考虑任意一个 parallel query round。算法在看到本轮 answers 之前，必须先一次性提交本轮 query set。

若本轮没有提交下一项必要 query：

$$
(k,q_k),
$$

则本轮不能确定 $q_{k+1}$，已揭示 chain prefix 不增长。

若本轮提交了 $(k,q_k)$，先考虑 $k<L-1$ 的情形。把算法在当前轮及以前对下一个 oracle $F_{k+1}$ 已经查询过的全部输入地址组成集合 $U$。

由于算法全部执行期间的总 query work 不超过 $Q$，所以：

$$
|U|\leq Q.
$$

已经选定的 chain values 最多为：

$$
q_0,q_1,\ldots,q_k,
$$

共 $k+1\leq L+1$ 个。把 $U$ 与这些 chain values 的集合并起来，所得集合大小至多：

$$
Q+L+1.
$$

由条件 [[#^eq-domain-size-condition|AR-5]] 和引理 5.1，至少存在一个 routing state $q_{k+1}\in\Omega_N$，它既没有作为 $F_{k+1}$ 的已查询输入出现，也不同于此前已选定的 chain values。

令当前必要 query 的 answer 为：

$$
F_k(q_k)=q_{k+1}.
$$

本轮其余首次出现的 queries 可以任意选择 answers；重复 queries 继续使用先前已经固定的 answers。

因为算法在提交本轮 queries 时还不知道这个 $q_{k+1}$，而我们又选择它避开了本轮对 $F_{k+1}$ 的所有查询输入，所以 query：

$$
(k+1,q_{k+1})
$$

不可能已经在本轮或更早轮次得到答案。

因此，即使本轮成功揭示了 $q_{k+1}$，也不能在同一轮继续可靠揭示 $q_{k+2}$。一个 parallel query round 至多把已知 chain prefix 推进一步。

若 $k=L-1$，为 query $(L-1,q_{L-1})$ 选择任意与既有 answers 一致的返回值 $q_L$，其余 queries 仍按前述一致性规则回答。本轮最多揭示这个最终结果，同样只把 chain prefix 推进一步；此时不需要定义不存在的 $F_L$。

由数学归纳法，经过 $r$ 个 parallel query rounds 后，最多能够可靠揭示到 $q_r$。

现在反设：

$$
R_{\mathcal A}<L.
$$

算法停止时最多揭示到某个 $q_k$，其中 $k<L$。取 $k$ 为已经揭示的最大下标。Query $(k,q_k)$ 不可能已经出现在 transcript 中；否则它的 answer 会确定 $q_{k+1}$，与 $k$ 的最大性矛盾。

设全部 transcript 中作为 query 输入出现过的 routing addresses，以及已经选定的 chain values，共同组成集合 $V$。由 query budget 与 chain 长度：

$$
|V|\leq Q+L.
$$

结合条件 $N\geq Q+L+2$ 与引理 5.2，可以选择两个不同的 fresh addresses：

$$
a,b\in\Omega_N\setminus V.
$$

构造两个完整 oracle families $\mathcal F^{(a)}$ 和 $\mathcal F^{(b)}$：

- 它们对 transcript 中所有已经出现的 queries 给出完全相同的 answers。
- 在 family $\mathcal F^{(a)}$ 中，定义 $F_k(q_k)=a$，并对所有 $j>k$ 定义 $F_j(a)=a$。
- 在 family $\mathcal F^{(b)}$ 中，定义 $F_k(q_k)=b$，并对所有 $j>k$ 定义 $F_j(b)=b$。
- 所有尚未定义的其他函数值任意补全，使每个 $F_j$ 成为从 $\Omega_N$ 到 $\Omega_N$ 的完整函数。

因为 $a,b$ 从未作为 query 输入出现，上述补全不与 transcript 中的任何 answer 冲突。

算法在两个 oracle families 上看到完全相同的 transcript，所以 deterministic algorithm 必须输出相同的 $\widehat q_L$。

但根据 reference route chain：

$$
q_L^{(a)}=a,
$$

$$
q_L^{(b)}=b,
$$

而 $a\neq b$。因此同一个输出不可能同时对两个 oracle families 正确，与 exactness 假设矛盾。

所以反设不成立，必有：

$$
R_{\mathcal A}\geq L.
$$

<div class="qed" aria-label="证毕">∎</div>

## 7. Work-Efficient Prefill 不可能性

### 推论 7.1：不存在通用 work-efficient sublinear-depth prefill

设 $\mathfrak A=(\mathcal A_{L,N})_{L,N\geq1}$ 是一个 deterministic、exact、work-efficient 的 parallel query algorithm scheme。由定义 4.9，存在常数 $c>0$、$k\in\mathbb N$ 与 $L_0\in\mathbb N$，使对所有 $L\geq L_0$ 和所有 $N\geq1$：

$$
Q_{\mathcal A_{L,N}}
\leq
cL\bigl(\log(L+2)\bigr)^k.
$$

定义整数 query bound：

$$
Q(L)
=
\left\lceil
cL\bigl(\log(L+2)\bigr)^k
\right\rceil.
$$

这里 $\lceil x\rceil$ 表示不小于实数 $x$ 的最小整数。

对每个 $L\geq L_0$，选择 routing state space size：

$$
N(L)
=Q(L)+L+2.
$$

则：

$$
R_{\mathcal A_{L,N(L)}}\geq L.
$$

因此，$\mathfrak A$ 不满足定义 4.10 的一致 $o(L)$ adaptive-depth 要求。所以，不存在对所有 routing state sizes 和任意 routing oracle families 都有效的 token-axis high-performance prefill algorithm scheme。

**证明。**

对每个固定 $L\geq L_0$，算法 $\mathcal A_{L,N(L)}$ 的 query work 不超过 $Q(L)$。把：

$$
Q=Q(L)
$$

代入定理 6.1，即得：

$$
R_{\mathcal A_{L,N(L)}}\geq L.
$$

若 $\mathfrak A$ 满足定义 4.10，则应存在 $r(L)=o(L)$，对所有 $N$ 都有 $R_{\mathcal A_{L,N}}\leq r(L)$。特别地，应有 $R_{\mathcal A_{L,N(L)}}\leq r(L)$。但上式给出 $R_{\mathcal A_{L,N(L)}}\geq L$，所以 $r(L)\geq L$，与 $r(L)=o(L)$ 矛盾。

<div class="qed" aria-label="证毕">∎</div>

### 解释 7.2：为什么并行猜测没有推翻定理

算法可以在一轮中猜测很多可能的 $q_{t+1}$，并查询：

$$
F_{t+1}(0),F_{t+1}(1),\ldots.
$$

若它查询 $F_{t+1}$ 的全部 $N$ 个输入，就一定覆盖真实的 $q_{t+1}$。随后可以继续枚举更深层候选。

但这需要至少 $N$ 个 queries，违反定理中的 $N>Q+L$ 条件。在 Tide 语境中，这对应：

- 执行所有候选 nodes。
- 展开所有可能路径。
- 把超稀疏 route chain 退化为 dense candidate evaluation。

本页不是说枚举在逻辑上不可能，而是说它不属于相对于实际 route chain 的 work-efficient prefill。

## 8. 嵌入局部通信、超稀疏 Graph

本节构造的是有限长度执行的 time-unrolled graph，而不是要求物理模型为每个 token 复制一套永久 nodes。坐标 $t$ 表示 logical token/time layer；routing address $q$ 才对应可复用的物理或逻辑 node state。

在下面的嵌入中，读取节点 $(t,q)$ 的唯一出边终点，计为一次 query $(t,q)$。一次性读取所有 nodes 的出边，等价于枚举 routing table，并计入相应 query work。

### 定义 8.1：Layered routing graph

给定 $L,N$ 与 oracle family $F_{0:L}$，定义有向图：

$$
G_{L,N,F}=(V,E).
$$

节点集合为：

$$
V=\{(t,q)\mid 0\leq t\leq L,\ q\in\Omega_N\}.
$$

对每个 $t\in[L]$ 和 $q\in\Omega_N$，加入一条有向边：

$$
((t,q),(t+1,F_t(q)))\in E.
$$

因此每个非终止节点的出度恰好为 $1$。

### 定义 8.2：Active path

从初始节点 $(0,q_0)$ 开始，只激活当前节点的唯一出边。由式 [[#^eq-adaptive-routing-chain|AR-1]]，实际 active path 为：

$$
(0,q_0)
\to
(1,q_1)
\to
\cdots
\to
(L,q_L).
$$

该 path 一共只访问 $L+1$ 个 nodes，尽管完整 Graph 有：

$$
(L+1)N
$$

个 nodes。

### 命题 8.3：Routing chain 与 layered graph 等价

计算 reference route chain 的最终状态 $q_L$，等价于确定 layered routing graph 中从 $(0,q_0)$ 出发的唯一 active path 的终点。

**证明。**

由定义 8.1，节点 $(t,q_t)$ 的唯一出边终点为：

$$
(t+1,F_t(q_t)).
$$

由式 [[#^eq-adaptive-routing-chain|AR-1]]：

$$
F_t(q_t)=q_{t+1}.
$$

所以唯一下一节点为 $(t+1,q_{t+1})$。从 $t=0$ 开始反复应用该结论，得到唯一 active path 的终点为 $(L,q_L)$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.4：局部通信与超稀疏不自动带来 chunk prefill

Layered routing graph 同时满足：

- 每个 active node 只沿一条边局部发送信号。
- 每层只有一个 node 位于实际 active path。
- Reference active path 恰好执行 $L$ 次 routing transitions。
- 下一个 active address 由当前 node 的 local transition 决定。

但由定理 6.1，任意 exact、work-efficient 的通用算法仍需至少 $L$ 个 adaptive rounds。

因此，“局部通信 + 超稀疏”本身不能推出高性能 chunk prefill。

**证明。**

由命题 8.3，确定 Graph 终点等价于计算 $q_L$。对该计算应用定理 6.1，即得 adaptive-depth 下界。

<div class="qed" aria-label="证毕">∎</div>

## 9. 早期 Token 晚期信号与交错控制路径

### 定义 9.1：Control event 与跨 token 自适应依赖

若一次 node/selector/kernel evaluation 的输出决定未来 evaluation 是否存在、激活哪个 node、选择哪条 edge，或者调用哪个 branch/kernel，则称这次 evaluation 为 control event。

对每个 token $t$，设 $c_t$ 是一个 routing control event。若 $c_t$ 的输出决定 token $t+1$ 的某个 routing address，并且该 address 在 $c_t$ 完成前未知，则记：

$$
c_t\rightsquigarrow c_{t+1}.
$$

符号 $\rightsquigarrow$ 在本页专门表示这种“下一 control query address 由前一 control result 决定”的自适应依赖，而不只是普通数值依赖。

### 定义 9.2：绝对逻辑时间中的交错

对一组 control events，绝对逻辑时间是函数：

$$
\tau:\{c_0,c_1,\ldots,c_{L-1}\}\to\mathbb N.
$$

若：

$$
c_t\rightsquigarrow c_{t+1},
$$

则要求：

$$
\tau(c_t)<\tau(c_{t+1}).
$$

其他 token、node 和 edge events 可以具有介于 $\tau(c_t)$ 与 $\tau(c_{t+1})$ 之间的时间，也可以与某个 $c_t$ 处于同一绝对时间的联合 inbox evaluation 中。这里的“交错”表示不同 token 的其他事件可以穿插出现，但必要的 control results 仍按上述严格时间顺序逐步揭示。

### 定义 9.3：Oracle-complete 交错控制链

若存在 control events：

$$
c_0,c_1,\ldots,c_{L-1},
$$

满足：

$$
c_0\rightsquigarrow c_1
\rightsquigarrow\cdots
\rightsquigarrow c_{L-1},
$$

并且对任意 $N$ 与任意 routing oracle family $F_{0:L}$，都可以选择该模型的合法参数和初始状态，使：

$$
q_{t+1}=F_t(q_t),
$$

且 runtime 获得任意函数值 $F_t(q)$ 的唯一允许方式，是实际执行并计数一次对应 control evaluation，则称该模型类别允许长度为 $L$ 的 oracle-complete 交错控制链。

最后一个条件排除了 runtime 免费读取 transition 的完整符号表达或完整函数表；它把可用信息严格限制为第 4 节定义的 oracle queries。在该查询模型下，这条链没有额外暴露可供 scan 或 bulk composition 使用的 summary。

此外，要求这些 control events 具有定义 9.2 的严格递增绝对逻辑时间。定义只要求这条必要 control path 始终存在，不限制其间还执行多少其他并行事件。

### 推论 9.4：交错控制传播下界

若一个 Tide-like 模型类别对任意 $L$ 都允许定义 9.3 的 oracle-complete 交错控制链，且最终 route state 满足定义 3.5 的可观察条件，那么该模型类别不存在对所有实例均有效的 exact、work-efficient、$o(L)$ adaptive-depth chunk prefill algorithm。

**证明。**

根据定义 9.3，该模型类别可以实现定理 6.1 中任意 routing oracle family，并且每次获得 $F_t(q)$ 都计为一次 query。若存在题设中的 chunk prefill algorithm，把它应用于这些实例，就得到一个违反推论 7.1 的 adaptive routing algorithm scheme，矛盾。

<div class="qed" aria-label="证毕">∎</div>

### 定义 9.5：Weighted execution DAG 与 critical-path span

设：

$$
\mathcal D=(\mathcal E,\mathcal A)
$$

是一个有限 DAG，其中 $\mathcal E$ 是 event 集合，$\mathcal A\subseteq\mathcal E\times\mathcal E$ 是 dependency edge 集合。

给每个 event $e\in\mathcal E$ 指定正执行成本：

$$
w(e)>0.
$$

对任意有向路径：

$$
\pi=(e_0,e_1,\ldots,e_m),
$$

定义路径总成本：

$$
w(\pi)=\sum_{i=0}^{m}w(e_i).
$$

定义 critical-path span：

$$
\operatorname{Span}(\mathcal D)
=
\max_{\pi}w(\pi),
$$

其中最大值取遍 $\mathcal D$ 中全部有向路径。即使有无限多处理器，任何保持这些 dependencies 的执行时间也不能小于 $\operatorname{Span}(\mathcal D)$。

### 推论 9.6：内部传播路径的额外 span

设 $L\geq2$。假设 execution DAG 中存在一条依次经过：

$$
c_0,c_1,\ldots,c_{L-1}
$$

的有向路径。再假设对每个 $0\leq t<L-1$，从紧接 $c_t$ 之后到包含 $c_{t+1}$ 为止的 path segment 总执行成本至少为 $\lambda>0$。

则整个 execution 的 critical-path span 至少为：

$$
\lambda(L-1).
$$

**证明。**

题设中的整条有向路径包含 $L-1$ 个互不重叠的连续 segments，每个 segment 的总执行成本至少为 $\lambda$。因此整条路径的总成本至少为 $\lambda(L-1)$。根据定义 9.5，DAG critical-path span 不小于任意一条有向路径的总成本，因此结论成立。

<div class="qed" aria-label="证毕">∎</div>

### 解释 9.7：其他并行事件为什么不能消除下界

同一绝对逻辑时间内，可以存在大量彼此没有依赖、因而能够并行执行的其他 events：

```text
A token 的其他支路
B token 的局部计算
数千个互不冲突的 node/edge events
其他 batch samples
```

这些 events 可以提高硬件利用率和 streaming throughput。但只要从输入到 required output 仍存在推论 9.4 的必要 control chain，所有其他并行工作都不能缩短这条 critical path。

## 10. 本定理没有证明什么

### 10.1 不是所有跨 token 依赖都不可并行

例 1.1 的 xor recurrence 和例 1.2 的 affine recurrence 都有跨 token 依赖，却可以 scan。下界针对的是任意、黑盒、自适应地址依赖。

### 10.2 不是每个动态 Graph 都不可并行

MoE 的 active expert graph 在执行 router 前同样未知，但一层中所有 token 的 route 可以由一个 bulk router 产生。它没有形成长度随 token 数增长的 pointer-chasing chain。

### 10.3 不是说完整 active DAG 必须预先生成

高性能 prefill 可以逐 layer 或逐 round 生成 active DAG。关键不是“是否一次性知道完整 DAG”，而是动态 control stages 的数量是否随 $L$ 线性增长。

### 10.4 不是无条件排除枚举全部候选

如果允许查询全部 $N$ 个 routing addresses，定理 6.1 的 domain-size 条件不再成立。此时可以用 dense candidate evaluation 换取较少 adaptive rounds，但这通常违背超稀疏 work 目标。

### 10.5 不是具体 LH selector 的既成下界

要把推论 9.4 应用于具体 LH/Tide selector，还需要额外证明至少一项：

- Selector 与 node state 可以嵌入足够大的任意 routing map。
- Selector 的 transition family 不存在所需的 compact associative summary。
- 某个受关注参数区域已经包含 pointer-chasing hard instances。

在完成这种 embedding 或结构分析前，本页只给出模型类别级别的通用下界，不能直接宣称每个 LH 配置都必然达到最坏情况。

### 10.6 当前定理只处理 deterministic exact algorithm

本页没有分析允许错误概率的 randomized algorithm，也没有分析近似 routing、近似最终状态或容忍输出误差的算法。若后续允许 approximation，需要重新定义 correctness，并单独证明相应下界。

### 10.7 不把免费离线预处理藏在模型之外

本页把读取或求值 $F_t(q)$ 计为 query work。若所有 routing maps 在部署前已经固定，允许 runtime 免费获得完整函数表并做无限离线预处理，那么 oracle model 不再适用。

对 Tide 使用本页结论时，需要满足至少一个条件：routing transition 依赖当前 token、hidden、node memory 或 selector state，因而只能在运行时确定；或者读取与预处理完整 routing maps 的成本必须计入 work。

## 11. 逃离下界的结构化特例

### 11.1 Token-local routing

若：

$$
q_t=\rho(h_t),
$$

并且同层所有 $h_t$ 已经可用，各 token 的 routing 不更新彼此可见的 mutable selector state，则所有 routes 可以批量计算。标准 MoE router 接近这一情形。

### 11.2 Scan-composable transition

若每个 transition 有固定大小 summary $m_t$，并存在 associative operator $\otimes$，使区间 transition 可以组合，则前缀 state 可以通过 scan 得到。Mamba/SSM 的仿射状态更新是主要例子。

### 11.3 Causal-bulk operator

若跨 token 依赖由一个已证明等价的 causal chunk kernel 承载，则无需逐 token 暴露 routing query。GPT-style causal attention 属于这一类。

### 11.4 有限个 Chunk-Wide Routing Frontiers

本节把 `chunk-wide routing frontier` 定义为：对固定 Graph round $r$，同时处理 chunk 中全部 token positions 的一组 routing computations。它们可以有不同 active nodes，但不能通过同一 round 内逐 token 更新的 mutable selector state 形成新的自适应链。

若对固定 $R$：

$$
A_{0:L}^{(r+1)}
=
\mathcal R_L^{(r)}(H_{0:L}^{(r)}),
\qquad 0\leq r<R,
$$

且每个 $\mathcal R_L^{(r)}$ 都是 token-local、scan-composable 或 causal-bulk，那么 active Graph 可以经过 $R$ 个 chunk-wide stages 逐步生成，而不是经过 $L$ 个自适应 token stages。

### 11.5 小状态空间的全枚举

若 $N$ 足够小，可以先查询整个 transition table，再对函数表做 composition。它从数学上有效，但 work 与 memory 至少依赖 $N$，不能作为巨大超稀疏 Graph 的默认解法。

## 12. 与显式程序复杂度下界的关系

定理 6.1 是黑盒查询模型中的无条件结论。它不需要假设任何尚未解决的复杂度理论命题。

编译器、数据流与并行执行的相关背景见 [[logical-event-dag-related-theories]]；本节只说明本页定理的边界，不把外部理论当作证明步骤。

如果不把 node/kernel transition 看作 oracle，而要求对任意显式给出的程序证明“绝不存在 polynomial-work、polylog-depth 的等价实现”，问题会更困难。

复杂度理论中：

- `P` 粗略表示可由顺序计算机在输入长度 $n$ 的 $c n^k$ 时间内求解的问题，其中 $c,k$ 是与输入无关的常数。
- `NC` 粗略表示可用多项式总工作量和 polylogarithmic parallel depth 求解的问题。

许多一般顺序状态机和程序执行问题可以表达 `P` 中最难并行化的一类问题。若能无条件证明所有这类显式 transition 都没有高效并行算法，可能需要解决或绕开 `P` 与 `NC` 关系中的长期未决问题。

因此，Tide 当前更稳的证否路径是：

1. 先用本页 oracle theorem 证明一般 adaptive routing runtime 不存在通用 work-efficient prefill。
2. 再分析具体 Tide/LH selector 是否能够嵌入该 oracle hard family。
3. 对无法嵌入的受限子类，寻找 token-local、scan、causal-bulk 或有限 chunk-wide routing stages。

## 13. 对 Tide 数学与架构主线的约束

### 13.1 Correctness 与高性能必须分开

绝对 logical time、phase、state version 与 event DAG 可以给任意有限执行定义清楚的 correctness，但不会自动降低 adaptive depth。

### 13.2 局部通信与超稀疏只控制 work

Layered routing graph 已经同时具有有界出度和单 active path，却仍有 $\Omega(L)$ adaptive depth。因此局部通信、超稀疏与低 span 是三个不同性质。

### 13.3 原始交错传播更自然地属于 Streaming/Decode

若早期 token 的晚期 Graph 信号持续决定后续 token 的 routing，并且这种机制不可删除，那么它可以继续利用：

- Graph node/edge parallelism。
- 多 batch parallelism。
- 同一绝对时间的 ready-event packing。
- Pipeline streaming throughput。

但在本页前提下，不应再把 Transformer/Mamba 式 chunk prefill 作为该完整语义的通用能力承诺。

### 13.4 Prefill 研究应转向结构化逃离条件

证明一般下界后，后续正向问题应改为：

> 在保持“局部通信 + 超稀疏”的前提下，哪些受限 routing/state families 能逃离 adaptive routing lower bound？

优先研究对象包括：

1. Token-local sparse routing。
2. Node-local affine/SSM state。
3. Causal-bulk message kernels。
4. 有限个 chunk-wide routing frontiers。
5. 可证明 compact composition 的小型 controller state。

## 14. 后续待证明问题

1. **LH selector embedding**：当前 `affectcount / selectcount / signal norm` selector 是否能编码足够一般的 pointer-chasing family？
2. **Restricted selector algebra**：去掉 conditional clear 或 persistent fairness 后，是否出现 compact transition composition？
3. **Adaptive-depth upper bound theorem**：对固定 $R$ 的 chunk-wide sparse Graph，如何从 local capability contracts 推出必须顺序等待的 routing stages 数量与 $L$ 无关？
4. **Work-span witness**：如何同时报告 active work、adaptive depth、kernel span、communication 与 memory，而不把 fused sequential loop 误报成 prefill parallelism？
5. **Model split**：是否应把完整交错传播定义为 Tide Streaming profile，把满足结构化限制的模型定义为 Tide Prefill profile？

这些问题中，第 1 项决定本页下界能否直接作用于当前 LH-like mechanism；第 2-3 项决定是否存在保留主要研究动机、同时逃离下界的结构化 Tide 子类。
