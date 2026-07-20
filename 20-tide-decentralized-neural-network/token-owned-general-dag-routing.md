---
type: note
status: draft
cssclasses:
  - textbook-math
tags:
  - tide
  - prefill-decode
  - sparse-routing
  - load-balancing
  - math
---

# 一般 DAG 中携带 `token` 归属信息的消息路由

> [!summary] 本页定位
> 本页给出一个从全局流中间开始执行的 general DAG 参考模型。给定全局起点 $B$、长度 $L$ 和左边界延续状态 $C_B$，当前输入变量只有 $x_{B:B+L}$；历史 $x_0,\ldots,x_{B-1}$ 的影响只能通过 $C_B$ 中的节点状态与边界在途消息出现。本文把一个有限窗口执行定义为从左切面 $\beta_B$ 到右切面 $\beta_{B+L}$ 的事件系统，并证明：在空间图为有限单位时延 DAG、消息带 `owner/frontier/arrival`、状态由唯一节点持有、节点分块算子精确实现节点参考转导器时，绝对时间流式调度可以等价重排为节点拓扑序分块调度，且得到同一读出 $y_{B:B+L}$ 与同一右边界延续状态 $C_{B+L}$。

> [!important] 核心结论
> 对 general DAG，不要求所有路径等长，也不要求从 $0$ 开始执行。真正需要显式定义的是：当前窗口位置集合、左/右边界切面、边界延续状态、在途消息、消息产生/消费函数、节点状态提交轨迹、事件依赖关系和节点分块契约。只要这些对象都被定义为集合、元素、函数或关系，prefill 从中间开始执行就不是“重新注入历史 token”，而是从 $C_B$ 继续计算有限窗口。

> [!warning] 正确性不自动推出高性能
> 主定理只证明两种调度计算同一个参考语义。它允许一个节点一次处理多个 `token` 位置、多个内部轮次和多个入站消息，但节点内部是否能用注意力、SSM/scan、分段批量或紧凑打包获得低并行跨度，需要为具体节点计算核另行证明。顺序回退也能满足正确性，但不能据此声称 Transformer/Mamba 意义上的高性能 chunk prefill。

## 0. 文档规范与基础记号

### 定义 0.1：形式化对象类型

从本节开始，凡进入定义、命题、定理或证明的对象，必须在使用前声明为以下类型之一：

1. 集合。
2. 集合元素。
3. 函数或部分函数。
4. 关系。
5. 有限序列。
6. 有限多重集。
7. 有限元组。
8. 由上述对象定义出的性质。

直观说明可以保留，但不能作为证明前提。若一个词在证明中起作用，就必须能回溯到本页中的某个集合、函数、关系或元组坐标。

### 0.1a：数学写作守则

本小节不是新的数学定义，而是本文后续编辑和审稿的检查规则。它把定义 0.1 的对象类型要求落实到写作过程。

1. 概念首次进入正式定义、命题、定理或证明前，必须说明它所属的集合，或把它声明为集合、集合元素、函数、部分函数、关系、有限序列、有限多重集、有限元组，或由这些对象定义出的性质。
2. 上一条也约束定义正文中的概念，而不只约束证明中的符号。不能用未声明的“键”“凭证”“谱系”“阶段内位置”等词代替数学对象；若这些词有必要，就先把它们定义成集合、坐标、函数或关系。
3. 一个函数必须给出定义域和值域；一个关系必须说明它是哪两个集合笛卡尔积的子集；一个有限元组必须给出每个坐标所属的集合。
4. 同一个符号不应同时承担事件身份、逻辑时间、消息归属和来源关系等不同职责。若同名投影在多个类型上重载，每个分支仍须单独给出定义域和值域，并且实参类型必须唯一确定所用分支。
5. 全文复用的正式对象必须由编号定义赋予数学类型；只在一个命题或证明内使用的局部对象，也必须在当地明确写出其类型。两者都没有做到的词只能是普通语言说明，不能作为后续推理前提。
6. 若一个概念只在单个证明中使用，就在该证明内直接定义相应集合、关系或函数，不额外提升为全文术语。
7. 直观说明可以不形式化，但必须同时满足两点：其含义无需一串新术语即可直接理解；正文明确它不承担定义或证明前提。若一段文字为了显得准确而引入多个未定义抽象词，就必须改写成数学定义。
8. 本页不从其他文档导入正式定义或定理。外部文档只能提供研究关系、历史或参考；本页使用的数学对象、前提与结论必须在本页重新声明。

### 0.1b：排版与编号约定

定义只引入对象、函数、关系、集合、记录类型或约束；证明只跟在引理、定理或推论之后。若某个等式从定义推出，应单独写成引理或推论，而不放在定义内部证明。

本文公式标签按用途加前缀。只有需要被引用或强调的展示公式才必须编号；普通中间推导可以不编号。

1. `D-*` 表示定义式，例如某个函数或构造的规定。
2. `A-*` 表示假设、约束或契约条件。
3. `L-*` 表示引理中的结论。
4. `T-*` 表示定理中的核心结论。
5. `C-*` 表示推论中的结论。

前缀后的数字尽量跟随所在小节编号。例如 `A-5.8d` 表示定义 5.8 中的第四类约束。若一个公式只是中间推导，通常不编号。

### 定义 0.2：自然数、有限区间与函数族

定义：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $n\in\mathbb N$，定义有限区间：

$$
[n]=\{0,1,\ldots,n-1\}.
$$

若 $n=0$，则 $[0]=\varnothing$。

若 $S$ 是有限集，$|S|\in\mathbb N$ 表示 $S$ 的元素个数。

对集合 $A$ 与 $n\in\mathbb N$，$A^n$ 表示从 $[n]$ 到 $A$ 的函数集合，也可等价看作长度为 $n$ 的有限序列集合。定义：

$$
A^\star=\bigcup_{n\in\mathbb N}A^n.
$$

对集合 $I$ 与 $A$，定义：

$$
A^I=\{f\mid f:I\to A\}.
$$

当 $x\in A^I$ 且 $i\in I$ 时，写 $x_i$ 表示 $x(i)$。

对集合 $A$，定义幂集：

$$
2^A=\{S\mid S\subseteq A\}.
$$

定义有限序列中的出现次数函数：

$$
\operatorname{occ}_A:A^\star\times A\to\mathbb N.
$$

若 $\mathbf a=(a_0,\ldots,a_{n-1})\in A^n$ 且 $a\in A$，规定：

$$
\operatorname{occ}_A(\mathbf a,a)
=
|\{i\in[n]\mid a_i=a\}|.
$$

若集合 $A$ 可由实参类型唯一确定，下标 $A$ 省略。

定义有限子集集合：

$$
\mathcal P_{\mathrm{fin}}(A)
=
\{S\subseteq A\mid S\text{ 是有限集}\}.
$$

定义有限序列的值集合函数：

$$
\operatorname{elem}_A:A^\star\to\mathcal P_{\mathrm{fin}}(A),
\qquad
\operatorname{elem}_A(\mathbf a)=\{a\in A\mid\operatorname{occ}_A(\mathbf a,a)>0\}.
$$

若类型可唯一确定，下标 $A$ 省略。后文说 $a$ 是序列 $\mathbf a$ 中的一个值，严格含义都是 $a\in\operatorname{elem}(\mathbf a)$。

定义 $A$ 上的有限多重集集合：

$$
\mathcal M_{\mathrm{fin}}(A)
=
\left\{
\mu:A\to\mathbb N
\ \middle|\
\{a\in A\mid \mu(a)\neq0\}\text{ 是有限集}
\right\}.
$$

若 $\mu\in\mathcal M_{\mathrm{fin}}(A)$，则 $\mu$ 是一个函数；对 $a\in A$，数 $\mu(a)$ 是 $a$ 在该多重集中的重数。定义支撑集函数：

$$
\operatorname{supp}_A:\mathcal M_{\mathrm{fin}}(A)\to 2^A,
\qquad
\operatorname{supp}_A(\mu)=\{a\in A\mid \mu(a)>0\}.
$$

若类型可唯一确定，下标 $A$ 省略。

定义空多重集：

$$
0_A\in\mathcal M_{\mathrm{fin}}(A),
\qquad
0_A(a)=0\quad(a\in A).
$$

若类型可唯一确定，下标 $A$ 省略。

若 $I$ 是有限集且 $\mu_i\in\mathcal M_{\mathrm{fin}}(A)$，定义多重集和：

$$
\left(\biguplus_{i\in I}\mu_i\right)(a)
=
\sum_{i\in I}\mu_i(a),
\qquad a\in A.
$$

对集合族 $(A_i)_{i\in I}$，定义带标签不交并：

$$
\bigsqcup_{i\in I}A_i
=
\{(i,a)\mid i\in I,\ a\in A_i\}.
$$

固定一个符号 $\bot$。除非某个定义显式把 $\bot$ 放入集合，否则约定 $\bot$ 不属于该集合。

若 $f:A\rightharpoonup B$，表示存在 $D\subseteq A$ 使 $f:D\to B$ 是函数；定义 $\operatorname{dom}(f)=D$。

### 定义 0.3：全局因果前沿序

定义全局因果前沿集合：

$$
\mathbb F=\{-1\}\cup\mathbb N.
$$

定义 $\mathbb F$ 上的严格全序 $<_\mathbb F$：对 $a,b\in\mathbb F$，

$$
a<_\mathbb F b
$$

当且仅当以下两个条件之一成立：

$$
a=-1,\ b\in\mathbb N,
$$

或：

$$
a,b\in\mathbb N,\ a<b
$$

其中第二个 $<$ 是自然数通常次序。相应非严格次序记为 $\leq_\mathbb F$。后文在不引起歧义时把 $\leq_\mathbb F$ 简写为 $\leq$。

对 $b\in\mathbb N$，定义边界前历史前沿集合：

$$
\mathbb F_{<b}
=
\{-1\}\cup[b].
$$

若 $b=0$，则 $\mathbb F_{<0}=\{-1\}$。

定义前一位置函数：

$$
\operatorname{prev}:\mathbb N\to\mathbb F,
\qquad
\operatorname{prev}(b)
=
\begin{cases}
-1,&b=0,\\
b-1,&b>0.
\end{cases}
$$

边界位置 $b$ 之前的最大历史位置是 $\operatorname{prev}(b)$。

## 1. 全局输入窗口与固定周期时间

### 定义 1.1：当前窗口、历史前缀与输入变量

给定非空集合 $X$ 与 $Y$，分别称为输入值集合与读出值集合。固定：

$$
B\in\mathbb N,\qquad
L\in\mathbb N,\qquad
R\in\mathbb N_{>0}.
$$

定义全局输入流集合：

$$
\mathsf{Stream}_X=X^{\mathbb N}.
$$

若 $\mathbf x\in\mathsf{Stream}_X$，则 $\mathbf x$ 是函数 $\mathbf x:\mathbb N\to X$。对 $t\in\mathbb N$，写 $x_t=\mathbf x(t)$。

定义当前 `chunk` 的全局位置集合：

$$
\mathbb I_{B,L}
=
\{B+i\mid i\in[L]\}.
$$

定义当前窗口结束前的全局位置集合：

$$
\mathbb P_{B,L}
=
[B+L].
$$

定义当前窗口可用的因果前沿集合：

$$
\mathbb F_{B,L}
=
\{-1\}\cup\mathbb P_{B,L}.
$$

当前输入变量是函数：

$$
x_{B:B+L}\in X^{\mathbb I_{B,L}}.
$$

若 $x_{B:B+L}$ 来自某个全局输入流 $\mathbf x\in\mathsf{Stream}_X$，则它是限制函数：

$$
x_{B:B+L}(t)=\mathbf x(t)
\qquad(t\in\mathbb I_{B,L}).
$$

对 $t\in\mathbb I_{B,L}$，值 $x_t\in X$ 是全局位置 $t$ 的输入值。本文写“`token` $t$”时，指位置索引 $t$ 和它的出现 $(t,x_t)$；它不是消息、事件或计算轨迹。

历史位置 $0,\ldots,B-1$ 不属于当前输入变量的定义域。它们对当前窗口的影响只能通过定义 3.4 的左边界延续状态 $C_B$ 出现。

### 定义 1.2：当前窗口上的前缀因果函数

给定集合 $\mathcal Q$、函数：

$$
f:X^{\mathbb I_{B,L}}\to\mathcal Q,
$$

以及 $c\in\mathbb F_{B,L}$。称 $f$ 是 $c$-前缀因果的，当且仅当对任意 $x,\bar x\in X^{\mathbb I_{B,L}}$，若：

$$
x_j=\bar x_j
\qquad
\text{对所有 }j\in\mathbb I_{B,L}\text{ 且 }j\leq c,
$$

则：

$$
f(x)=f(\bar x).
$$

若 $c<B$，上面的比较条件不涉及当前窗口内任何坐标，因此该条件表示 $f$ 对当前窗口输入变量是常函数。它仍可以依赖已经固定的边界延续状态 $C_B$，因为 $C_B$ 不是当前函数的变量。

若记录可能不存在，给定集合 $\mathcal Q$，定义：

$$
\mathcal Q_\bot=\mathcal Q\cup\{\bot\},
\qquad
\bot\notin\mathcal Q.
$$

函数 $f:X^{\mathbb I_{B,L}}\to\mathcal Q_\bot$ 的 $c$-前缀因果性按同一规则定义。若 $f(x)=\bot$，表示记录不存在；它不是一个值为空的实际事件。

### 定义 1.3：阶段、完整逻辑时间戳与窗口切面

取：

$$
N_{\mathrm{phase}}\in\mathbb N_{>0},
\qquad
N_{\mathrm{phase}}\geq 6,
$$

并定义阶段集合：

$$
\Phi=\{0,\ldots,N_{\mathrm{phase}}-1\}.
$$

定义完整逻辑时间戳集合：

$$
\Theta=\mathbb N\times\Phi.
$$

对 $\theta=(\tau,i)\in\Theta$，定义投影：

$$
\operatorname{round}(\theta)=\tau,
\qquad
\operatorname{phase}(\theta)=i.
$$

定义 $\Theta$ 上的字典序 $<_\Theta$：对 $(\tau,i),(\tau',i')\in\Theta$，

$$
(\tau,i)<_\Theta(\tau',i')
$$

当且仅当：

$$
\tau<\tau'
$$

或：

$$
\tau=\tau'\quad\text{且}\quad i<i'.
$$

非严格次序记为 $\leq_\Theta$。

取六个两两不同的阶段：

$$
i_{\mathrm{arrive}},
i_{\mathrm{step}},
i_{\mathrm{commit}},
i_{\mathrm{read}},
i_{\mathrm{sample}},
i_{\mathrm{inject}}
\in\Phi,
$$

并要求：

$$
i_{\mathrm{arrive}}
<
i_{\mathrm{step}}
<
i_{\mathrm{commit}}
<
i_{\mathrm{read}}
<
i_{\mathrm{sample}}
<
i_{\mathrm{inject}}.
\tag{A-1.3}
$$

对 $t\in\mathbb I_{B,L}$，定义：

$$
\theta_t^{\mathrm{in}}=(Rt,i_{\mathrm{inject}}),
$$

$$
\theta_t^{\mathrm{out}}=(R(t+1),i_{\mathrm{read}}),
$$

$$
\theta_t^{\mathrm{sample}}=(R(t+1),i_{\mathrm{sample}}).
$$

定义边界切面函数：

$$
\beta:\mathbb N\to\Theta,
\qquad
\beta(b)=(Rb,i_{\mathrm{inject}}).
$$

当前窗口的左边界切面与右边界切面分别是：

$$
\beta_B=\beta(B),
\qquad
\beta_{B+L}=\beta(B+L).
$$

定义当前窗口执行时间戳集合：

$$
\Theta_{B,L}^{\mathrm{run}}
=
\{\theta\in\Theta\mid
\beta_B\leq_\Theta\theta<_\Theta\beta_{B+L}\}.
$$

因此当前窗口包含 $x_B,\ldots,x_{B+L-1}$ 的注入，以及 $y_B,\ldots,y_{B+L-1}$ 的读出；它不包含 $x_{B+L}$ 的注入。

### 定义 1.4：时间戳处可见的当前窗口前缀

定义函数：

$$
a_{R,B,L}:\Theta\to\mathbb F_{B,L}
$$

如下。对任意 $\theta\in\Theta$，

$$
a_{R,B,L}(\theta)
=
\max
\left(
\{\operatorname{prev}(B)\}
\cup
\{t\in\mathbb I_{B,L}\mid \theta_t^{\mathrm{in}}\leq_\Theta\theta\}
\right).
\tag{D-1.4a}
$$

最大值存在，因为集合非空且有限。

称四元组 $(\mathcal Q,f,\theta,c)$ 是有效带时间戳前缀因果量，当且仅当：

$$
f:X^{\mathbb I_{B,L}}\to\mathcal Q
$$

是 $c$-前缀因果的，且：

$$
c\leq a_{R,B,L}(\theta).
\tag{D-1.4b}
$$

### 引理 1.5：读出时刻的可见前缀

若 $t\in\mathbb I_{B,L}$，则：

$$
a_{R,B,L}(\theta_t^{\mathrm{out}})=t.
\tag{L-1.5}
$$

**证明。**

对任意 $j\in\mathbb I_{B,L}$，若 $j\leq t$，则 $Rj\leq Rt<R(t+1)$，所以 $\theta_j^{\mathrm{in}}\leq_\Theta\theta_t^{\mathrm{out}}$。若 $j>t$，则 $j\geq t+1$；当 $j=t+1$ 时，二者轮次同为 $R(t+1)$，但 $i_{\mathrm{read}}<i_{\mathrm{inject}}$，所以 $\theta_t^{\mathrm{out}}<_\Theta\theta_j^{\mathrm{in}}$；当 $j>t+1$ 时，$R(t+1)<Rj$，所以同样有 $\theta_t^{\mathrm{out}}<_\Theta\theta_j^{\mathrm{in}}$。故 $\theta_j^{\mathrm{in}}\leq_\Theta\theta_t^{\mathrm{out}}$ 当且仅当 $j\leq t$。代入式 D-1.4a 即得结论。

<div class="qed" aria-label="证毕">∎</div>

### 定义 1.6：给定序列与自回归接口

给定序列 `prefill` 参考把 $x_{B:B+L}$ 作为外部给定函数，但逻辑可见性仍由定义 1.4 约束。

自回归 `decode` 参考还给定确定函数：

$$
\operatorname{SelectToken}:Y\to X.
$$

若 $t,t+1\in\mathbb I_{B,L}$，则要求：

$$
x_{t+1}=\operatorname{SelectToken}(y_t).
\tag{A-1.6}
$$

窗口左端 $x_B$ 是否可由 $y_{B-1}$ 接续，不由 $x_{B:B+L}$ 本身表达，而由左边界延续状态 $C_B$ 是否来自前一窗口决定。

## 2. 空间 DAG 与单位时延

### 定义 2.1：带输入输出节点的有限空间 DAG

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
\qquad v_{\mathrm{in}}\neq v_{\mathrm{out}},
$$

分别称为输入节点与输出节点。

称 $G$ 是有限 DAG，当且仅当不存在 $k\in\mathbb N_{>0}$ 和序列 $(v_0,\ldots,v_k)\in V^{k+1}$ 满足：

$$
v_0=v_k,
\qquad
(v_i,v_{i+1})\in E\quad(i\in[k]).
$$

本文进一步要求：

1. 没有边指向 $v_{\mathrm{in}}$，即不存在 $u\in V$ 使 $(u,v_{\mathrm{in}})\in E$。
2. 对每个 $v\in V$，存在从 $v_{\mathrm{in}}$ 到 $v$ 的有向路径。
3. 对每个 $v\in V$，存在从 $v$ 到 $v_{\mathrm{out}}$ 的有向路径。

这些条件只排除与输入输出无关的孤立节点，不要求路径等长。

### 定义 2.2：路径集合

对 $u,v\in V$ 与 $k\in\mathbb N$，从 $u$ 到 $v$ 的长度为 $k$ 的路径是序列：

$$
p=(v_0,\ldots,v_k)\in V^{k+1}
$$

满足：

$$
v_0=u,\qquad v_k=v,
$$

且：

$$
(v_i,v_{i+1})\in E\quad(i\in[k]).
$$

定义 $|p|=k$。定义路径集合：

$$
\mathsf{Path}_G(u,v)
=
\{p\mid p\text{ 是从 }u\text{ 到 }v\text{ 的有限有向路径}\}.
$$

### 引理 2.3：有限 DAG 的路径集合有限

对任意 $u,v\in V$，路径集合 $\mathsf{Path}_G(u,v)$ 是有限集。

**证明。**

若 $p=(v_0,\ldots,v_k)\in\mathsf{Path}_G(u,v)$ 且存在 $0\leq i<j\leq k$ 使 $v_i=v_j$，则 $(v_i,\ldots,v_j)$ 给出有向环，违反定义 2.1 的 DAG 条件。因此 $p$ 中没有重复节点，所以 $k\leq |V|-1$。集合 $V$ 有限，长度不超过 $|V|-1$ 的 $V$ 中元素序列只有有限多个，故 $\mathsf{Path}_G(u,v)$ 有限。

<div class="qed" aria-label="证毕">∎</div>

### 定义 2.4：空间深度与固定周期

定义 2.1 保证 $\mathsf{Path}_G(v_{\mathrm{in}},v_{\mathrm{out}})$ 非空；引理 2.3 保证相关路径集合有限，所以本定义中的 $d_{\min}$ 与 $D$ 都存在。

定义最短输入输出距离：

$$
d_{\min}
=
\min\{|p|\mid p\in\mathsf{Path}_G(v_{\mathrm{in}},v_{\mathrm{out}})\}.
$$

定义全图最大路径长度：

$$
D
=
\max\{|p|\mid u,v\in V,\ p\in\mathsf{Path}_G(u,v)\}.
$$

本文的固定周期读出默认取：

$$
R=d_{\min}.
\tag{A-2.4}
$$

### 定义 2.5：单位时延空间边

若一个事件在空间节点 $u$、绝对轮次 $\tau$ 产生沿空间边 $(u,v)\in E$ 的消息，则该消息的到达时间戳必须为：

$$
(\tau+1,i_{\mathrm{arrive}}).
\tag{A-2.5}
$$

因此同一绝对轮次内没有跨空间边的零时延传播。

## 3. 状态、消息与边界延续状态

### 定义 3.1：节点持有状态

对每个 $v\in V$，给定非空集合 $\mathcal S_v$，称为节点 $v$ 的数值状态集合。定义增广状态集合：

$$
\widetilde{\mathcal S}_v
=
\mathcal S_v\times\mathbb F.
$$

若 $\widetilde S=(S,c)\in\widetilde{\mathcal S}_v$，定义：

$$
\operatorname{num}(\widetilde S)=S,
\qquad
\operatorname{frontier}(\widetilde S)=c.
$$

状态属于空间节点，不属于某个 `token`。每个可变状态位置只能由一个节点持有。KV cache、SSM 状态、线性注意力累加器和显式节点记忆都应作为某个 $\mathcal S_v$ 的坐标，而不是作为隐藏全局变量。

给定原点状态：

$$
S_v^0\in\mathcal S_v.
$$

定义：

$$
\widetilde S_v^0=(S_v^0,-1).
$$

### 定义 3.2：消息记录

给定非空集合 $\mathsf{EID}$、$\mathsf{MID}$、$\mathcal U$ 与 $\mathsf{Payload}$，分别称为事件标识符集合、消息标识符集合、元数据集合与载荷集合。给定 $\mathsf{MID}$ 上的严格全序 $<_{\mathsf{MID}}$。

定义当前窗口可讨论的候选消息记录集合：

$$
\mathfrak R_{B,L}
=
\mathsf{MID}
\times\mathbb P_{B,L}
\times\mathbb F_{B,L}
\times\Theta
\times V\times V
\times\mathcal U
\times\mathsf{Payload}.
$$

一个候选消息记录是八元组：

$$
m=(\iota,o,c,\theta,u,v,\mu,p)\in\mathfrak R_{B,L}.
$$

八个坐标依次称为消息标识符、`owner`、`frontier`、到达时间戳、源节点、目标节点、元数据和载荷。定义投影：

$$
\operatorname{id}(m)=\iota,
\quad
\operatorname{owner}(m)=o,
\quad
\operatorname{frontier}(m)=c,
\quad
\operatorname{arrival}(m)=\theta,
$$

$$
\operatorname{src}(m)=u,
\quad
\operatorname{dst}(m)=v,
\quad
\operatorname{meta}(m)=\mu,
\quad
\operatorname{payload}(m)=p.
$$

定义有效消息集合：

$$
\mathcal R_{B,L}
=
\left\{
m\in\mathfrak R_{B,L}
\ \middle|\
\begin{array}{l}
\operatorname{owner}(m)\leq\operatorname{frontier}(m),\\
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})
\text{ 对某个 }\tau\in\mathbb N,\\
(\operatorname{src}(m),\operatorname{dst}(m))\in E
\end{array}
\right\}.
$$

对任意边界位置 $b\in\mathbb N$，定义边界前候选消息记录集合：

$$
\mathfrak R_{<b}
=
\mathsf{MID}
\times[b]
\times\mathbb F_{<b}
\times\Theta
\times V\times V
\times\mathcal U
\times\mathsf{Payload}.
$$

在 $\mathfrak R_{<b}$ 上使用与 $\mathfrak R_{B,L}$ 相同的八个坐标投影函数：$\operatorname{id}$、$\operatorname{owner}$、$\operatorname{frontier}$、$\operatorname{arrival}$、$\operatorname{src}$、$\operatorname{dst}$、$\operatorname{meta}$ 与 $\operatorname{payload}$。

定义边界前有效消息集合：

$$
\mathcal R_{<b}
=
\left\{
m\in\mathfrak R_{<b}
\ \middle|\
\begin{array}{l}
\operatorname{owner}(m)\leq\operatorname{frontier}(m),\\
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})
\text{ 对某个 }\tau\in\mathbb N,\\
(\operatorname{src}(m),\operatorname{dst}(m))\in E
\end{array}
\right\}.
$$

这里 $\mathcal R_{<b}$ 用于定义边界位置 $b$ 的在途历史消息。若 $b\leq B+L$，则 $\mathcal R_{<b}\subseteq\mathcal R_{B,L}$。

对节点 $v$，定义入站消息类型：

$$
\mathcal R_{v,B,L}
=
\{m\in\mathcal R_{B,L}\mid \operatorname{dst}(m)=v\}.
$$

`owner` 是消息字段。它不是消息身份、不是路径身份，也不是状态归属。当前窗口中允许 $\operatorname{owner}(m)<B$，但这只可能来自左边界延续状态中的历史在途消息或其后继。

### 定义 3.3：边界注入记录

定义当前窗口的边界注入记录集合：

$$
\mathcal B_{\mathrm{in}}^{B,L}
=
\{(t,\theta_t^{\mathrm{in}},v_{\mathrm{in}},x)\mid t\in\mathbb I_{B,L},\ x\in X\}.
$$

对输入 $x_{B:B+L}$ 与 $t\in\mathbb I_{B,L}$，定义实际注入记录：

$$
b_t^{\mathrm{in}}
=
(t,\theta_t^{\mathrm{in}},v_{\mathrm{in}},x_t)
\in\mathcal B_{\mathrm{in}}^{B,L}.
$$

注入记录不是空间边消息。它在第 5 节被实例化为输入事件。

### 定义 3.4：边界延续状态

对任意边界位置 $b\in\mathbb N$，定义延续状态集合 $\mathsf{Cont}_b$。其元素是二元组：

$$
C_b=(\mathbf S^b,\mathcal M_b^\partial),
$$

满足下列条件。

第一，$\mathbf S^b$ 是函数：

$$
\mathbf S^b:V\to\bigsqcup_{v\in V}\widetilde{\mathcal S}_v,
$$

并且对每个 $v\in V$，存在唯一 $\widetilde S_v^b\in\widetilde{\mathcal S}_v$ 使：

$$
\mathbf S^b(v)=(v,\widetilde S_v^b).
$$

第二，$\mathcal M_b^\partial$ 是有限集合：

$$
\mathcal M_b^\partial\in\mathcal P_{\mathrm{fin}}(\mathcal R_{<b}).
$$

第三，状态和消息不依赖边界之后的输入。形式上，对每个 $v\in V$：

$$
\operatorname{frontier}(\widetilde S_v^b)\leq\operatorname{prev}(b).
\tag{A-3.4a}
$$

对每个 $m\in\mathcal M_b^\partial$：

$$
\operatorname{frontier}(m)\leq\operatorname{prev}(b),
\tag{A-3.4b}
$$

并且：

$$
\beta(b)<_\Theta\operatorname{arrival}(m).
\tag{A-3.4c}
$$

式 A-3.4c 表示这些消息在切面 $\beta(b)$ 之后才到达；若某条历史消息在同一轮次 $Rb$ 的到达阶段已经到达，它应已经被边界状态 $\mathbf S^b$ 吸收，而不应仍放在 $\mathcal M_b^\partial$ 中。

第四，消息标识符在 $\mathcal M_b^\partial$ 上单射。即对 $m,m'\in\mathcal M_b^\partial$：

$$
\operatorname{id}(m)=\operatorname{id}(m')
\Longrightarrow
m=m'.
$$

第五，若 $b=0$，则要求：

$$
\mathcal M_b^\partial=\varnothing,
\qquad
\widetilde S_v^0=\widetilde S_v^b\quad(v\in V).
$$

当前窗口的左边界延续状态是某个 $C_B\in\mathsf{Cont}_B$。此时由 $\mathcal R_{<B}\subseteq\mathcal R_{B,L}$，左边界在途消息也可作为当前窗口消息集合的元素。

### 定义 3.5：右边界延续状态

给定一次窗口执行后得到的节点提交轨迹与消息生命周期，右边界延续状态 $C_{B+L}$ 也是二元组：

$$
C_{B+L}=(\mathbf S^{B+L},\mathcal M_{B+L}^\partial).
$$

它由定义 5.9 的右边界构造给出。直观上，$\mathbf S^{B+L}$ 是每个节点在右切面 $\beta_{B+L}$ 前最后可见的状态，$\mathcal M_{B+L}^\partial$ 是到达时间戳严格晚于 $\beta_{B+L}$ 的未消费消息。这里先只说明它的类型；构造公式在定义 5.9 中给出。

## 4. 节点局部对象与路由对象

### 定义 4.1：收件箱分桶

固定有限消息集合：

$$
\mathcal M\in\mathcal P_{\mathrm{fin}}(\mathcal R_{B,L}).
$$

对 $v\in V$、$\tau\in\mathbb N$ 与 $t\in\mathbb P_{B,L}$，定义多重集：

$$
I_{v,\tau,t}^{\mathcal M}:\mathcal R_{v,B,L}\to\mathbb N
$$

为：

$$
I_{v,\tau,t}^{\mathcal M}(m)
=
\begin{cases}
1,
&m\in\mathcal M,
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}}),\
\operatorname{owner}(m)=t,\\
0,&\text{其他情形}.
\end{cases}
\tag{D-4.1}
$$

定义同一节点同一轮次出现的 `owner` 集合：

$$
\mathcal O_{v,\tau}^{\mathcal M}
=
\{t\in\mathbb P_{B,L}\mid I_{v,\tau,t}^{\mathcal M}\neq0_{\mathcal R_{v,B,L}}\}.
$$

定义完整收件箱：

$$
I_{v,\tau}^{\mathcal M}
=
\biguplus_{t\in\mathcal O_{v,\tau}^{\mathcal M}}
I_{v,\tau,t}^{\mathcal M}.
$$

若 $\mathcal M$ 已由上下文固定，省略上标 $\mathcal M$。

### 定义 4.2：同一 `owner` 桶的数值聚合

对每个 $v\in V$，给定非空集合 $X_v^{\mathrm{num}}$ 与确定函数：

$$
\operatorname{Aggregate}_v:
\mathcal M_{\mathrm{fin}}(\mathcal R_{v,B,L})
\to X_v^{\mathrm{num}}.
$$

定义节点输入值集合：

$$
X_v^{\mathrm{node}}
=
X_v^{\mathrm{num}}\times\mathbb F_{B,L}.
$$

若 $t\in\mathcal O_{v,\tau}$，定义：

$$
\bar x_{v,\tau,t}
=
\operatorname{Aggregate}_v(I_{v,\tau,t}),
$$

$$
c_{v,\tau,t}^{X}
=
\max\{\operatorname{frontier}(m)\mid m\in\operatorname{supp}(I_{v,\tau,t})\},
$$

以及：

$$
x_{v,\tau,t}^{\mathrm{node}}
=
(\bar x_{v,\tau,t},c_{v,\tau,t}^{X})
\in X_v^{\mathrm{node}}.
$$

这里的聚合只在同一 $(v,\tau,t)$ 桶内发生，不混合同一轮次的不同 `owner`。

### 定义 4.3：局部输出记录

对每个 $v\in V$，给定非空集合 $H_v$。定义：

$$
\mathcal Z_v
=
\{\bot\}\cup(H_v\times\mathbb F_{B,L}).
$$

定义局部输出记录集合：

$$
\mathcal L_{v,B,L}
=
\mathbb P_{B,L}\times\mathcal Z_v.
$$

本小节中的 $z$ 只是 $\mathcal Z_v$ 的元素变量，不表示空间输出节点；空间输出节点始终记为 $v_{\mathrm{out}}$。

若 $\ell=(t,z)\in\mathcal L_{v,B,L}$，定义：

$$
\operatorname{owner}(\ell)=t.
$$

定义两个部分函数：

$$
\operatorname{payload}_v^{\mathcal Z}:\mathcal Z_v\rightharpoonup H_v,
\qquad
\operatorname{frontier}_v^{\mathcal Z}:\mathcal Z_v\rightharpoonup\mathbb F_{B,L}.
$$

二者的定义域都是 $H_v\times\mathbb F_{B,L}\subseteq\mathcal Z_v$。若 $z=(h,c)\in H_v\times\mathbb F_{B,L}$，规定：

$$
\operatorname{payload}_v^{\mathcal Z}(z)=h,
\qquad
\operatorname{frontier}_v^{\mathcal Z}(z)=c.
$$

若 $\ell=(t,z)$ 且 $z\neq\bot$，要求：

$$
\operatorname{owner}(\ell)\leq\operatorname{frontier}_v^{\mathcal Z}(z).
$$

因此一次节点事件消费多个 `owner` 后，是否分别输出、联合输出或融合输出，必须体现为 $\mathcal L_{v,B,L}^\star$ 中的明确记录序列。不存在“无归属的激活信号”。

### 定义 4.4：状态提交记录

给定非空集合 $\mathsf{CID}$。定义提交次序键集合：

$$
\mathsf{CKey}=\Theta\times\mathbb N.
$$

在 $\mathsf{CKey}$ 上使用字典序：$(\theta,j)<_{\mathsf{CKey}}(\theta',j')$ 当且仅当 $\theta<_\Theta\theta'$，或 $\theta=\theta'$ 且 $j<j'$。

对节点 $v$，定义提交记录集合：

$$
\mathcal Q_{v,B,L}
=
\mathsf{CID}\times\mathsf{CKey}\times\widetilde{\mathcal S}_v.
$$

若 $q=(\gamma,\chi,\widetilde S)\in\mathcal Q_{v,B,L}$，定义：

$$
\operatorname{cid}(q)=\gamma,
\qquad
\operatorname{ckey}(q)=\chi,
\qquad
\operatorname{version}(q)=\widetilde S.
$$

若 $\operatorname{ckey}(q)=(\theta,j)$，定义：

$$
\operatorname{ctime}(q)=\theta.
$$

### 定义 4.5：状态输入记录

固定左边界延续状态 $C_B=(\mathbf S^B,\mathcal M_B^\partial)$。对每个 $v\in V$，定义：

$$
\mathcal{SI}_{v}^{C_B}
=
\bigl(\{\mathtt{boundaryState}\}\times\{\widetilde S_v^B\}\bigr)
\cup
\bigl(\{\mathtt{commitState}\}\times\mathcal Q_{v,B,L}\bigr).
$$

定义状态值投影：

$$
\operatorname{stateVersion}:\mathcal{SI}_{v}^{C_B}\to\widetilde{\mathcal S}_v
$$

为：

$$
\operatorname{stateVersion}((\mathtt{boundaryState},\widetilde S_v^B))
=
\widetilde S_v^B,
$$

$$
\operatorname{stateVersion}((\mathtt{commitState},q))
=
\operatorname{version}(q).
$$

定义部分函数：

$$
\operatorname{stateCommit}:\mathcal{SI}_{v}^{C_B}\rightharpoonup\mathcal Q_{v,B,L}
$$

其定义域为 $\{\mathtt{commitState}\}\times\mathcal Q_{v,B,L}$，且：

$$
\operatorname{stateCommit}((\mathtt{commitState},q))=q.
$$

### 定义 4.6：出边、路由记录与派发

定义出边集合函数：

$$
\operatorname{Out}:V\to 2^E,
\qquad
\operatorname{Out}(v)=\{(v,u)\in E\}.
$$

对节点 $v$，定义路由记录集合：

$$
\mathcal{RR}_{v,B,L}
=
\mathsf{EID}
\times\Theta
\times\mathbb N
\times\mathbb P_{B,L}
\times\mathcal Z_v
\times2^{\operatorname{Out}(v)}.
$$

若 $r=(\eta,\theta,j,t,z,A)\in\mathcal{RR}_{v,B,L}$，定义：

$$
\operatorname{sourceEvent}(r)=\eta,
\quad
\operatorname{sourceTime}(r)=\theta,
\quad
\operatorname{slot}(r)=j,
$$

$$
\operatorname{owner}(r)=t,
\quad
\operatorname{output}(r)=z,
\quad
\operatorname{edges}(r)=A.
$$

若 $\operatorname{output}(r)=\bot$，要求 $\operatorname{edges}(r)=\varnothing$。若 $\operatorname{output}(r)=(h,c)$，要求：

$$
\operatorname{owner}(r)\leq c.
$$

对每条空间边 $(v,u)\in E$，给定非空集合：

$$
\mathsf{Payload}_{v\to u}\subseteq\mathsf{Payload}
$$

和确定函数：

$$
P_{v\to u}:H_v\to\mathsf{Payload}_{v\to u}.
$$

定义派发请求集合：

$$
\mathcal D_{v,B,L}
=
\{(r,(v,u))\mid
r\in\mathcal{RR}_{v,B,L},\
\operatorname{output}(r)=(h,c)\in H_v\times\mathbb F_{B,L},\
(v,u)\in\operatorname{edges}(r)
\}.
$$

定义：

$$
\mathcal D_{B,L}
=
\bigsqcup_{v\in V}\mathcal D_{v,B,L}.
$$

派发函数是确定函数：

$$
\operatorname{Dispatch}:\mathcal D_{B,L}\to\mathcal R_{B,L}.
$$

若 $\delta=(v,(r,(v,u)))\in\mathcal D_{B,L}$、$\operatorname{sourceTime}(r)=\theta$ 且 $\operatorname{output}(r)=(h,c)$，令 $m'=\operatorname{Dispatch}(\delta)$，要求：

$$
\operatorname{owner}(m')=\operatorname{owner}(r),
\qquad
\operatorname{frontier}(m')=c,
$$

$$
\operatorname{arrival}(m')
=
(\operatorname{round}(\theta)+1,i_{\mathrm{arrive}}),
$$

$$
\operatorname{src}(m')=v,
\qquad
\operatorname{dst}(m')=u,
\qquad
\operatorname{payload}(m')=P_{v\to u}(h).
$$

还要求 $\operatorname{id}\circ\operatorname{Dispatch}$ 在 $\mathcal D_{B,L}$ 上单射。

## 5. 事件系统与窗口执行记录

### 定义 5.1：语义配置与事件头

定义语义配置集合：

$$
\mathsf{Mode}=\{\mathrm{ord},\mathrm{joint},\mathrm{front}\}.
$$

固定：

$$
P\in\mathsf{Mode}.
$$

定义事件位置集合：

$$
\mathsf{Loc}=V\cup\{\mathtt{external}\}.
$$

定义边界事件种类集合：

$$
\mathcal K_{\mathrm{bdry}}
=
\{\mathtt{carry},\mathtt{inject},\mathtt{readout},\mathtt{sample}\}.
$$

对每个 $P\in\mathsf{Mode}$，取一个符号 $\mathtt{node}_P$，并要求三个 $\mathtt{node}_P$ 两两不同且都不属于 $\mathcal K_{\mathrm{bdry}}$。定义：

$$
\mathcal K^P
=
\mathcal K_{\mathrm{bdry}}\cup\{\mathtt{node}_P\}.
$$

定义事件头集合：

$$
\mathfrak H_{B,L}^P
=
\mathsf{EID}
\times\mathcal K^P
\times\mathsf{Loc}
\times\Theta
\times2^{\mathbb P_{B,L}}
\times\mathbb F_{B,L}.
$$

若：

$$
h=(\eta,\kappa,\ell,\theta,\Omega,c)\in\mathfrak H_{B,L}^P,
$$

六个坐标分别称为事件标识符、事件种类、事件位置、事件时间戳、归属支持集和事件因果前沿。定义事件头投影函数：

$$
\operatorname{id}:\mathfrak H_{B,L}^P\to\mathsf{EID},
\qquad
\operatorname{kind}:\mathfrak H_{B,L}^P\to\mathcal K^P,
$$

$$
\operatorname{loc}:\mathfrak H_{B,L}^P\to\mathsf{Loc},
\qquad
\operatorname{time}:\mathfrak H_{B,L}^P\to\Theta,
$$

$$
\operatorname{support}:\mathfrak H_{B,L}^P\to2^{\mathbb P_{B,L}},
\qquad
\operatorname{frontier}:\mathfrak H_{B,L}^P\to\mathbb F_{B,L}.
$$

若 $h=(\eta,\kappa,\ell,\theta,\Omega,c)$，规定：

$$
\operatorname{id}(h)=\eta,\quad
\operatorname{kind}(h)=\kappa,\quad
\operatorname{loc}(h)=\ell,
$$

$$
\operatorname{time}(h)=\theta,\quad
\operatorname{support}(h)=\Omega,\quad
\operatorname{frontier}(h)=c.
$$

### 定义 5.2：事件值集合

固定 $C_B$。对节点 $v$，定义常规节点事件值集合：

$$
\mathcal W_{v,B,L}^{\mathrm{node}}
=
\mathcal{SI}_{v}^{C_B}
\times
\mathcal M_{\mathrm{fin}}(\mathcal R_{v,B,L})
\times
\mathcal L_{v,B,L}^{\star}
\times
\mathcal Q_{v,B,L}^{\star}
\times
\mathcal{RR}_{v,B,L}^{\star}
\times
\mathcal R_{B,L}^{\star}.
$$

六个坐标依次是：状态输入记录、消费的入站消息多重集、局部输出记录序列、提交记录序列、路由记录序列、出站消息序列。定义投影：

$$
\operatorname{stateInput},\operatorname{inbox},\operatorname{local},
\operatorname{commits},\operatorname{routes},\operatorname{outbox}
$$

为相应坐标投影。

定义输入事件值集合：

$$
\mathcal W_{v_{\mathrm{in}},B,L}^{\mathrm{in}}
=
\mathcal B_{\mathrm{in}}^{B,L}
\times
\mathcal{SI}_{v_{\mathrm{in}}}^{C_B}
\times
\mathcal L_{v_{\mathrm{in}},B,L}^{\star}
\times
\mathcal Q_{v_{\mathrm{in}},B,L}^{\star}
\times
\mathcal{RR}_{v_{\mathrm{in}},B,L}^{\star}
\times
\mathcal R_{B,L}^{\star}.
$$

其第一个坐标称为边界注入记录，投影记为 $\operatorname{boundary}$；其余坐标与常规节点事件值同名。

定义 carry 事件值集合：

$$
\mathcal W_{B,L}^{\mathrm{carry}}
=
\mathcal R_{B,L}.
$$

定义事件值全集：

$$
\mathsf{EVal}_{B,L}^P
=
\mathcal W_{B,L}^{\mathrm{carry}}
\cup
\mathcal W_{v_{\mathrm{in}},B,L}^{\mathrm{in}}
\cup
\bigcup_{v\in V}\mathcal W_{v,B,L}^{\mathrm{node}}
\cup X\cup Y.
$$

这里使用普通并集。若同一个底层数学对象同时属于两个值集合，则事件头 $h$ 通过 $\mathcal V_{B,L}^P(h)$ 唯一指定该事件值在当前事件中的类型分支；后文只在事件种类已经确定时使用相应坐标投影。

定义事件值空间函数：

$$
\mathcal V_{B,L}^P:\mathfrak H_{B,L}^P\to2^{\mathsf{EVal}_{B,L}^P}
$$

如下。若 $h=(\eta,\kappa,\ell,\theta,\Omega,c)$，则：

$$
\mathcal V_{B,L}^P(h)
=
\begin{cases}
\mathcal W_{B,L}^{\mathrm{carry}},
&\kappa=\mathtt{carry},\ \ell\in V,\\
\mathcal W_{v_{\mathrm{in}},B,L}^{\mathrm{in}},
&\kappa=\mathtt{inject},\ \ell=v_{\mathrm{in}},\\
\mathcal W_{v,B,L}^{\mathrm{node}},
&\kappa=\mathtt{node}_P,\ \ell=v\in V,\\
Y,
&\kappa=\mathtt{readout},\ \ell=v_{\mathrm{out}},\\
X,
&\kappa=\mathtt{sample},\ \ell=\mathtt{external},\\
\varnothing,
&\text{其他情形}.
\end{cases}
$$

定义事件实例集合：

$$
\mathfrak E_{B,L}^P
=
\{(h,\nu)\mid h\in\mathfrak H_{B,L}^P,\ \nu\in\mathcal V_{B,L}^P(h)\}.
$$

若 $e=(h,\nu)\in\mathfrak E_{B,L}^P$，定义：

$$
\operatorname{head}(e)=h,
\qquad
\operatorname{value}(e)=\nu.
$$

定义事件实例上的同名投影函数，其定义域都是 $\mathfrak E_{B,L}^P$，其值等于先取 $\operatorname{head}(e)$ 再取对应事件头投影。例如：

$$
\operatorname{time}(e)
=
\operatorname{time}(\operatorname{head}(e)).
$$

其他五个投影 $\operatorname{id}$、$\operatorname{kind}$、$\operatorname{loc}$、$\operatorname{support}$ 与 $\operatorname{frontier}$ 同理定义。

### 定义 5.3：固定事件标识符函数

固定下列函数，并要求它们的像集两两不交。

边界输入、读出、采样标识符：

$$
\eta^{\mathrm{in}},
\eta^{\mathrm{out}},
\eta^{\mathrm{sample}}:
\mathbb I_{B,L}\to\mathsf{EID}.
$$

节点事件标识符：

$$
\eta^{\mathrm{node,ord}}:
V\times\mathbb N\times\mathbb P_{B,L}\to\mathsf{EID},
$$

$$
\eta^{\mathrm{node,joint}},
\eta^{\mathrm{node,front}}:
V\times\mathbb N\to\mathsf{EID}.
$$

给定左边界在途消息集合 $\mathcal M_B^\partial$，还固定单射：

$$
\eta^{\mathrm{carry}}:\mathcal M_B^\partial\to\mathsf{EID},
$$

且其像集与上述所有像集不交。

同样固定提交标识符函数：

$$
\gamma^{\mathrm{in}}:\mathbb I_{B,L}\to\mathsf{CID},
$$

$$
\gamma^{\mathrm{node,ord}}:
V\times\mathbb N\times\mathbb P_{B,L}\to\mathsf{CID},
$$

$$
\gamma^{\mathrm{node,joint}},
\gamma^{\mathrm{node,front}}:
V\times\mathbb N\to\mathsf{CID},
$$

并要求它们单射且像集两两不交。

### 定义 5.4：边界事件头

对 $t\in\mathbb I_{B,L}$，定义：

$$
h_t^{\mathrm{in}}
=
(\eta^{\mathrm{in}}(t),\mathtt{inject},v_{\mathrm{in}},\theta_t^{\mathrm{in}},\{t\},t),
$$

$$
h_t^{\mathrm{out}}
=
(\eta^{\mathrm{out}}(t),\mathtt{readout},v_{\mathrm{out}},\theta_t^{\mathrm{out}},\{t\},t),
$$

$$
h_t^{\mathrm{sample}}
=
(\eta^{\mathrm{sample}}(t),\mathtt{sample},\mathtt{external},\theta_t^{\mathrm{sample}},\{t\},t).
$$

若 $B>0$，定义：

$$
\theta_B^{\mathrm{carry}}=(RB-1,N_{\mathrm{phase}}-1).
$$

若 $m\in\mathcal M_B^\partial$，定义 carry 事件头：

$$
h_m^{\mathrm{carry}}
=
(\eta^{\mathrm{carry}}(m),\mathtt{carry},
\operatorname{src}(m),
\theta_B^{\mathrm{carry}},
\{\operatorname{owner}(m)\},
\operatorname{frontier}(m)).
$$

当 $B=0$ 时，由定义 3.4 有 $\mathcal M_0^\partial=\varnothing$，所以不需要定义 $\theta_B^{\mathrm{carry}}$ 或实际 carry 事件。

carry 事件是边界参数的事件化表示。它不表示当前窗口重新计算历史消息，只用于让当前窗口内被消费的历史在途消息有一个事件图内的生产者。

### 定义 5.5：节点事件头

给定有限消息集合 $\mathcal M$，用定义 4.1 构造 $\mathcal O_{v,\tau}$ 与 $I_{v,\tau}$。

配置 $\mathrm{ord}$ 中，若 $t\in\mathcal O_{v,\tau}$ 且 $(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}$，节点事件头为：

$$
h_{v,\tau,t}^{\mathrm{ord}}
=
(\eta^{\mathrm{node,ord}}(v,\tau,t),
\mathtt{node}_{\mathrm{ord}},
v,
(\tau,i_{\mathrm{commit}}),
\{t\},
c_{v,\tau,t}^{\mathrm{ord}}),
$$

其中 $c_{v,\tau,t}^{\mathrm{ord}}\in\mathbb F_{B,L}$ 是该事件值的有效因果前沿；执行记录中所有事件前沿还必须满足定义 5.8 的统一可见性条件。

配置 $\mathrm{joint}$ 中，若 $I_{v,\tau}\neq0_{\mathcal R_{v,B,L}}$ 且 $(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}$，节点事件头为：

$$
h_{v,\tau}^{\mathrm{joint}}
=
(\eta^{\mathrm{node,joint}}(v,\tau),
\mathtt{node}_{\mathrm{joint}},
v,
(\tau,i_{\mathrm{commit}}),
\mathcal O_{v,\tau},
c_{v,\tau}^{\mathrm{joint}}),
$$

其中 $c_{v,\tau}^{\mathrm{joint}}\in\mathbb F_{B,L}$ 是有效因果前沿；执行记录中所有事件前沿还必须满足定义 5.8 的统一可见性条件。

配置 $\mathrm{front}$ 中，若 $I_{v,\tau}\neq0_{\mathcal R_{v,B,L}}$ 且 $(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}$，节点事件头为：

$$
h_{v,\tau}^{\mathrm{front}}
=
(\eta^{\mathrm{node,front}}(v,\tau),
\mathtt{node}_{\mathrm{front}},
v,
(\tau,i_{\mathrm{commit}}),
\mathcal O_{v,\tau},
c_{v,\tau}^{\mathrm{front}}),
$$

其中 $c_{v,\tau}^{\mathrm{front}}\in\mathbb F_{B,L}$ 是有效因果前沿；执行记录中所有事件前沿还必须满足定义 5.8 的统一可见性条件。

本定义只规定事件头的集合类型和时间位置；具体局部输出、状态更新与出站消息由事件值和节点转导器决定。

### 定义 5.6：消息生命周期

给定有限事件集合：

$$
\mathcal E\in\mathcal P_{\mathrm{fin}}(\mathfrak E_{B,L}^P)
$$

和有限消息集合：

$$
\mathcal M\in\mathcal P_{\mathrm{fin}}(\mathcal R_{B,L}).
$$

要求事件标识符在 $\mathcal E$ 上单射，消息标识符在 $\mathcal M$ 上单射。

消息生产函数是函数：

$$
\operatorname{producer}:\mathcal M\to\mathcal E.
$$

消息消费函数是部分函数：

$$
\operatorname{consumer}:\mathcal M\rightharpoonup\mathcal E.
$$

要求对每个 $m\in\mathcal M$：

$$
\operatorname{loc}(\operatorname{producer}(m))=\operatorname{src}(m),
$$

且：

$$
\operatorname{time}(\operatorname{producer}(m))<_\Theta\operatorname{arrival}(m).
$$

若 $m\in\operatorname{dom}(\operatorname{consumer})$，则：

$$
\operatorname{kind}(\operatorname{consumer}(m))=\mathtt{node}_P,
$$

$$
\operatorname{loc}(\operatorname{consumer}(m))=\operatorname{dst}(m),
$$

且：

$$
\operatorname{arrival}(m)<_\Theta\operatorname{time}(\operatorname{consumer}(m)).
$$

当前窗口要求：

$$
\mathcal M_B^\partial\subseteq\mathcal M.
\tag{A-5.6a}
$$

若 $m\in\mathcal M_B^\partial$，则 $\operatorname{producer}(m)$ 是唯一头为 $h_m^{\mathrm{carry}}$ 的 carry 事件，并且：

$$
\operatorname{value}(\operatorname{producer}(m))=m.
\tag{A-5.6b}
$$

若 $m\notin\mathcal M_B^\partial$，则要求：

$$
\operatorname{kind}(\operatorname{producer}(m))
\in
\{\mathtt{inject},\mathtt{node}_P\},
$$

并且：

$$
\operatorname{occ}(
\operatorname{outbox}(\operatorname{value}(\operatorname{producer}(m))),
m)
=1.
$$

若：

$$
\operatorname{arrival}(m)<_\Theta\beta_{B+L},
\tag{A-5.6c}
$$

则 $m\in\operatorname{dom}(\operatorname{consumer})$。若：

$$
\beta_{B+L}<_\Theta\operatorname{arrival}(m),
$$

则 $m\notin\operatorname{dom}(\operatorname{consumer})$，并进入右边界在途消息集合。

式 A-5.6c 使用右切面 $\beta_{B+L}$，所以在轮次 $R(B+L)$ 的到达、计算、提交、读出与采样阶段发生的事件仍属于当前窗口；只有下一次注入 $x_{B+L}$ 及其以后不属于当前窗口。

### 定义 5.7：状态依赖、读出依赖与事件 DAG

本定义假设：对每个 $t\in\mathbb I_{B,L}$，$\mathcal E$ 中存在唯一头为 $h_t^{\mathrm{in}}$ 的事件和唯一头为 $h_t^{\mathrm{out}}$ 的事件。分别把它们记为 $e_t^{\mathrm{in}}$ 与 $e_t^{\mathrm{out}}$。若该唯一性条件不成立，则本定义的状态键函数、读出依赖关系和事件图均不定义。

定义具有状态输入的事件集合：

$$
\mathcal E_{\mathrm{state}}
=
\{e\in\mathcal E\mid
\operatorname{kind}(e)\in\{\mathtt{inject},\mathtt{node}_P\}\}.
$$

定义状态键函数：

$$
\operatorname{stateKey}:\mathcal E_{\mathrm{state}}\to\mathsf{CKey}.
$$

若 $e$ 是输入事件 $e_t^{\mathrm{in}}$，定义：

$$
\operatorname{stateKey}(e)=(\theta_t^{\mathrm{in}},t).
$$

若 $P=\mathrm{ord}$ 且 $e$ 是头为 $h_{v,\tau,t}^{\mathrm{ord}}$ 的节点事件，定义：

$$
\operatorname{stateKey}(e)=((\tau,i_{\mathrm{commit}}),t).
$$

若 $P=\mathrm{joint}$ 且 $e$ 是头为 $h_{v,\tau}^{\mathrm{joint}}$ 的节点事件，或 $P=\mathrm{front}$ 且 $e$ 是头为 $h_{v,\tau}^{\mathrm{front}}$ 的节点事件，定义：

$$
\operatorname{stateKey}(e)=((\tau,i_{\mathrm{commit}}),0).
$$

对 $e'\in\mathcal E_{\mathrm{state}}$，定义同节点先前提交集合：

$$
\mathcal C_{e'}^{\mathrm{state}}
=
\left\{
(e,q)
\ \middle|\
\begin{array}{l}
e\in\mathcal E_{\mathrm{state}},\
\operatorname{loc}(e)=\operatorname{loc}(e'),\\
q\in\operatorname{elem}(\operatorname{commits}(\operatorname{value}(e))),\\
\operatorname{ckey}(q)<_{\mathsf{CKey}}\operatorname{stateKey}(e')
\end{array}
\right\}.
$$

若 $\mathcal C_{e'}^{\mathrm{state}}=\varnothing$，要求：

$$
\operatorname{stateInput}(\operatorname{value}(e'))
=
(\mathtt{boundaryState},\widetilde S_{\operatorname{loc}(e')}^B).
\tag{A-5.7a}
$$

若 $\mathcal C_{e'}^{\mathrm{state}}\neq\varnothing$，要求存在唯一 $(e,q)\in\mathcal C_{e'}^{\mathrm{state}}$ 使 $q$ 的提交键最大，并要求：

$$
\operatorname{stateInput}(\operatorname{value}(e'))
=
(\mathtt{commitState},q).
\tag{A-5.7b}
$$

定义部分函数 $\operatorname{stateProducer}:\mathcal E_{\mathrm{state}}\rightharpoonup\mathcal E_{\mathrm{state}}$：当式 A-5.7b 适用时，$\operatorname{stateProducer}(e')=e$。

定义消息依赖关系：

$$
\mathcal A_{\mathrm{msg}}
=
\{(\operatorname{producer}(m),\operatorname{consumer}(m))
\mid m\in\operatorname{dom}(\operatorname{consumer})\}.
$$

定义状态依赖关系：

$$
\mathcal A_{\mathrm{state}}
=
\{(\operatorname{stateProducer}(e),e)
\mid e\in\operatorname{dom}(\operatorname{stateProducer})\}.
$$

对 $t\in\mathbb I_{B,L}$，定义输出节点在读出前的提交集合：

$$
\mathcal C_t^{\mathrm{read}}
=
\left\{
(e,q)
\ \middle|\
\begin{array}{l}
e\in\mathcal E_{\mathrm{state}},\
\operatorname{loc}(e)=v_{\mathrm{out}},\\
q\in\operatorname{elem}(\operatorname{commits}(\operatorname{value}(e))),\\
\operatorname{ctime}(q)<_\Theta\theta_t^{\mathrm{out}}
\end{array}
\right\}.
$$

若 $\mathcal C_t^{\mathrm{read}}\neq\varnothing$，要求存在唯一 $(e_t^{\mathrm{read}},q_t^{\mathrm{read}})\in\mathcal C_t^{\mathrm{read}}$ 使 $q_t^{\mathrm{read}}$ 的提交键最大。定义读出依赖关系：

$$
\mathcal A_{\mathrm{read}}
=
\{(e_t^{\mathrm{read}},e_t^{\mathrm{out}})
\mid t\in\mathbb I_{B,L},\
\mathcal C_t^{\mathrm{read}}\neq\varnothing\}.
$$

给定序列执行的直接依赖关系定义为：

$$
\mathcal A
=
\mathcal A_{\mathrm{msg}}
\cup
\mathcal A_{\mathrm{state}}
\cup
\mathcal A_{\mathrm{read}}
\subseteq\mathcal E\times\mathcal E.
$$

定义事件图：

$$
D_{\mathscr X}=(\mathcal E,\mathcal A).
$$

### 定义 5.8：窗口执行记录

一次给定序列窗口执行记录是七元组：

$$
\mathscr X_{B,L}^P
=
(x_{B:B+L},C_B,\mathcal E,\mathcal M,
\operatorname{producer},\operatorname{consumer},\mathcal A),
$$

先定义边界允许事件头集合：

$$
\mathcal H_{\mathrm{bdry}}^{B,L}
=
\{h_t^{\mathrm{in}}\mid t\in\mathbb I_{B,L}\}
\cup
\{h_t^{\mathrm{out}}\mid t\in\mathbb I_{B,L}\}
\cup
\{h_m^{\mathrm{carry}}\mid m\in\mathcal M_B^\partial\}.
$$

再定义节点允许事件头集合。若 $P=\mathrm{ord}$，令：

$$
\mathcal H_{\mathrm{node}}^{P,\mathcal M}
=
\{h_{v,\tau,t}^{\mathrm{ord}}
\mid
v\in V,\
\tau\in\mathbb N,\
t\in\mathcal O_{v,\tau}^{\mathcal M},\
(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}
\}.
$$

若 $P=\mathrm{joint}$，令：

$$
\mathcal H_{\mathrm{node}}^{P,\mathcal M}
=
\{h_{v,\tau}^{\mathrm{joint}}
\mid
v\in V,\
\tau\in\mathbb N,\
I_{v,\tau}^{\mathcal M}\neq0_{\mathcal R_{v,B,L}},\
(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}
\}.
$$

若 $P=\mathrm{front}$，令：

$$
\mathcal H_{\mathrm{node}}^{P,\mathcal M}
=
\{h_{v,\tau}^{\mathrm{front}}
\mid
v\in V,\
\tau\in\mathbb N,\
I_{v,\tau}^{\mathcal M}\neq0_{\mathcal R_{v,B,L}},\
(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}
\}.
$$

执行记录满足定义 5.1--5.7 的全部条件，并且：

1. 对每个 $e\in\mathcal E$：

$$
\operatorname{head}(e)
\in
\mathcal H_{\mathrm{bdry}}^{B,L}
\cup
\mathcal H_{\mathrm{node}}^{P,\mathcal M}.
$$

2. 对每个 $m\in\mathcal M_B^\partial$，$\mathcal E$ 中存在唯一头为 $h_m^{\mathrm{carry}}$ 的事件。
3. 对每个 $t\in\mathbb I_{B,L}$，$\mathcal E$ 中存在唯一头为 $h_t^{\mathrm{in}}$ 的输入事件和唯一头为 $h_t^{\mathrm{out}}$ 的读出事件。
4. 给定序列执行不包含 $\mathtt{sample}$ 事件；自回归扩展可在定义 1.6 的基础上加入采样事件。
5. 若 $e\in\mathcal E_{\mathrm{state}}$ 且 $v=\operatorname{loc}(e)$，则其路由记录与出站消息满足以下四个条件。第一，对每个 $r\in\operatorname{elem}(\operatorname{routes}(\operatorname{value}(e)))$：

$$
\operatorname{sourceEvent}(r)=\operatorname{id}(e),
\qquad
\operatorname{sourceTime}(r)=\operatorname{time}(e).
$$

第二，定义有限集合：

$$
\Delta_e
=
\{(v,(r,(v,u)))
\mid
r\in\operatorname{elem}(\operatorname{routes}(\operatorname{value}(e))),
(v,u)\in\operatorname{edges}(r)
\}
\subseteq\mathcal D_{B,L}.
$$

则：

$$
\operatorname{elem}(\operatorname{outbox}(\operatorname{value}(e)))
=
\{\operatorname{Dispatch}(\delta)\mid\delta\in\Delta_e\}.
$$

第三，对每个 $m\in\operatorname{elem}(\operatorname{outbox}(\operatorname{value}(e)))$：

$$
\operatorname{producer}(m)=e.
$$

第四，对每个 $m\in\mathcal R_{B,L}$：

$$
\operatorname{occ}(\operatorname{outbox}(\operatorname{value}(e)),m)\leq1.
$$

6. 消息消费函数与节点事件 inbox 满足双向一致性。对每个 $e\in\mathcal E$，若 $\operatorname{kind}(e)=\mathtt{node}_P$，则对每个 $m\in\mathcal R_{\operatorname{loc}(e),B,L}$：

$$
\operatorname{inbox}(\operatorname{value}(e))(m)\in\{0,1\},
$$

且：

$$
\operatorname{inbox}(\operatorname{value}(e))(m)=1
\Longleftrightarrow
\left(
m\in\operatorname{dom}(\operatorname{consumer})
\text{ 且 }
\operatorname{consumer}(m)=e
\right).
$$

7. 对每个 $e\in\mathcal E$，都有：

$$
\operatorname{frontier}(e)\leq
a_{R,B,L}(\operatorname{time}(e)).
\tag{A-5.8a}
$$

并且对每个 $t\in\operatorname{support}(e)$，都有：

$$
t\leq\operatorname{frontier}(e).
\tag{A-5.8b}
$$

8. 若 $e\in\mathcal E_{\mathrm{state}}$ 且 $q\in\operatorname{elem}(\operatorname{commits}(\operatorname{value}(e)))$，则 $q\in\mathcal Q_{\operatorname{loc}(e),B,L}$，并且：

$$
\operatorname{ckey}(q)=\operatorname{stateKey}(e).
\tag{A-5.8c}
$$

并且：

$$
\operatorname{frontier}(\operatorname{version}(q))
\leq
\operatorname{frontier}(e).
\tag{A-5.8d}
$$

9. 对每个 $e\in\mathcal E_{\mathrm{state}}$，若 $q,q'\in\operatorname{elem}(\operatorname{commits}(\operatorname{value}(e)))$，则：

$$
q=q'.
\tag{A-5.8e}
$$

因此每个输入事件或节点事件在当前模型中至多产生一个状态提交记录。若未来需要一个事件提交多个互不相同的状态位置，应把 $\mathcal S_v$ 拆成多个由不同节点持有的状态集合，或把提交键扩展为包含状态子坐标。

10. 对每个 $t\in\mathbb I_{B,L}$，读出值为 $y_t=\operatorname{value}(e_t^{\mathrm{out}})\in Y$。

定义执行记录集合 $\mathfrak X_{B,L}^P$ 为所有满足上述条件的七元组集合。

### 定义 5.9：右边界构造

给定 $\mathscr X_{B,L}^P\in\mathfrak X_{B,L}^P$，定义右边界在途消息集合：

$$
\mathcal M_{B+L}^\partial
=
\{m\in\mathcal M\mid
m\notin\operatorname{dom}(\operatorname{consumer})
\text{ 且 }
\beta_{B+L}<_\Theta\operatorname{arrival}(m)\}.
\tag{D-5.9a}
$$

对每个节点 $v$，令：

$$
\mathcal C_v^{<\beta_{B+L}}
=
\left\{
q
\ \middle|\
\begin{array}{l}
e\in\mathcal E_{\mathrm{state}},\
\operatorname{loc}(e)=v,\\
q\in\operatorname{elem}(\operatorname{commits}(\operatorname{value}(e))),\\
\operatorname{ctime}(q)<_\Theta\beta_{B+L}
\end{array}
\right\}.
$$

若 $\mathcal C_v^{<\beta_{B+L}}=\varnothing$，定义：

$$
\widetilde S_v^{B+L}=\widetilde S_v^B.
$$

若 $\mathcal C_v^{<\beta_{B+L}}\neq\varnothing$，要求存在唯一 $q_v^\star\in\mathcal C_v^{<\beta_{B+L}}$ 使 $q_v^\star$ 的提交键最大，并定义：

$$
\widetilde S_v^{B+L}=\operatorname{version}(q_v^\star).
$$

定义 $\mathbf S^{B+L}$ 为函数 $v\mapsto(v,\widetilde S_v^{B+L})$，并定义：

$$
C_{B+L}(\mathscr X_{B,L}^P)
=
(\mathbf S^{B+L},\mathcal M_{B+L}^\partial).
\tag{D-5.9b}
$$

这是当前窗口交给下一个窗口的延续状态；它不是冲刷后最终状态。

### 引理 5.10：右边界构造给出合法延续状态

若 $\mathscr X_{B,L}^P\in\mathfrak X_{B,L}^P$，则式 D-5.9b 定义的 $C_{B+L}(\mathscr X_{B,L}^P)$ 属于 $\mathsf{Cont}_{B+L}$。

**证明。**

先看状态部分。对每个 $v\in V$，式 D-5.9b 定义了唯一 $\widetilde S_v^{B+L}\in\widetilde{\mathcal S}_v$，所以 $\mathbf S^{B+L}$ 是从 $V$ 到 $\bigsqcup_{v\in V}\widetilde{\mathcal S}_v$ 的函数，且第 $v$ 个值属于第 $v$ 个带标签分支。

若 $\widetilde S_v^{B+L}=\widetilde S_v^B$，则由 $C_B\in\mathsf{Cont}_B$：

$$
\operatorname{frontier}(\widetilde S_v^{B+L})
\leq
\operatorname{prev}(B)
\leq
\operatorname{prev}(B+L).
$$

若 $\widetilde S_v^{B+L}=\operatorname{version}(q_v^\star)$，则 $q_v^\star$ 由某个状态事件 $e$ 产生，且 $\operatorname{ctime}(q_v^\star)<_\Theta\beta_{B+L}$。由式 A-5.8d：

$$
\operatorname{frontier}(\widetilde S_v^{B+L})
\leq
\operatorname{frontier}(e).
$$

事件前沿满足式 A-5.8a，所以：

$$
\operatorname{frontier}(e)
\leq
a_{R,B,L}(\operatorname{time}(e)).
$$

由 $a_{R,B,L}$ 的定义以及 $\operatorname{time}(e)<_\Theta\beta_{B+L}$，可知：

$$
a_{R,B,L}(\operatorname{time}(e))
\leq
\operatorname{prev}(B+L).
$$

因此状态部分满足 $\mathsf{Cont}_{B+L}$ 的前沿条件。

再看消息部分。$\mathcal M_{B+L}^\partial$ 是有限集合 $\mathcal M$ 的子集，所以有限。若 $m\in\mathcal M_{B+L}^\partial$，由式 D-5.9a：

$$
\beta_{B+L}<_\Theta\operatorname{arrival}(m).
$$

又因为 $m\in\mathcal R_{B,L}$，有：

$$
\operatorname{owner}(m)\in[B+L],
\qquad
\operatorname{frontier}(m)\in\{-1\}\cup[B+L],
$$

所以 $m\in\mathcal R_{<B+L}$，并且：

$$
\operatorname{frontier}(m)\leq\operatorname{prev}(B+L).
$$

消息标识符单射性由 $\mathcal M_{B+L}^\partial\subseteq\mathcal M$ 和定义 5.6 中 $\mathcal M$ 上的单射性继承。若 $B+L=0$，则 $B=0$ 且 $L=0$，由定义 3.4 左边界无在途消息，当前窗口也无注入事件，因此右边界在途消息为空，原点状态条件也成立。

综上，$C_{B+L}(\mathscr X_{B,L}^P)$ 满足定义 3.4 中边界位置 $b=B+L$ 的全部条件。

<div class="qed" aria-label="证毕">∎</div>

### 定义 5.11：事件值依赖完备性

对 $e\in\mathcal E$，定义直接前驱集合：

$$
\operatorname{Pred}(e)
=
\{e'\in\mathcal E\mid(e',e)\in\mathcal A\}.
$$

定义前驱值赋值集合：

$$
\mathcal P_e
=
\left\{
g:\operatorname{Pred}(e)\to\mathsf{EVal}_{B,L}^P
\ \middle|\
g(e')\in\mathcal V_{B,L}^P(\operatorname{head}(e'))
\text{ 对每个 }e'\in\operatorname{Pred}(e)
\right\}.
$$

定义边界参数集合：

$$
\mathcal B_e
=
\begin{cases}
X,&\operatorname{kind}(e)=\mathtt{inject},\\
\mathcal R_{B,L},&\operatorname{kind}(e)=\mathtt{carry},\\
\widetilde{\mathcal S}_{v_{\mathrm{out}}},&\operatorname{kind}(e)=\mathtt{readout},\\
\{\mathtt{unit}\},&\text{其他情形},
\end{cases}
$$

其中 $\mathtt{unit}$ 是一个固定符号。实际边界参数 $b_e\in\mathcal B_e$ 定义为：

1. 若 $e=e_t^{\mathrm{in}}$，则 $b_e=x_t$。
2. 若 $e$ 是 carry 事件且 $\operatorname{value}(e)=m$，则 $b_e=m$。
3. 若 $e=e_t^{\mathrm{out}}$，则 $b_e=\widetilde S_{v_{\mathrm{out}}}^B$。
4. 其他情形下，$b_e=\mathtt{unit}$。

因此，当 $\mathcal C_t^{\mathrm{read}}=\varnothing$ 时，读出事件仍可通过参数 $b_{e_t^{\mathrm{out}}}$ 读取左边界输出节点状态；当 $\mathcal C_t^{\mathrm{read}}\neq\varnothing$ 时，读出事件还可通过 $\mathcal A_{\mathrm{read}}$ 读取窗口内最新提交事件的值。

称事件图 $D_{\mathscr X}$ 对执行记录是事件值依赖完备的，当且仅当对每个 $e\in\mathcal E$，存在确定函数：

$$
F_e:
\{\operatorname{head}(e)\}
\times\mathcal P_e
\times\mathcal B_e
\to
\mathcal V_{B,L}^P(\operatorname{head}(e)),
$$

使得实际前驱赋值：

$$
g_e(e')=\operatorname{value}(e')
\qquad(e'\in\operatorname{Pred}(e))
$$

满足：

$$
\operatorname{value}(e)=F_e(\operatorname{head}(e),g_e,b_e).
\tag{D-5.11}
$$

该定义只允许事件值读取事件头、直接前驱值和已类型化边界参数。模型权重、拓扑和固定超参数被视为函数 $F_e$ 本身的一部分，不作为隐藏输入通道。

## 6. 节点规范输入序列与分块契约

### 定义 6.1：节点规范输入记录

固定 $\mathscr X_{B,L}^P\in\mathfrak X_{B,L}^P$。对节点 $v$，定义常规分组记录集合：

$$
\mathcal G_{v,B,L}
=
\mathbb N
\times
\mathcal M_{\mathrm{fin}}(\mathcal R_{v,B,L})
\times
\left(\mathbb P_{B,L}\times X_v^{\mathrm{node}}\right)^\star.
$$

若 $I_{v,\tau}\neq0_{\mathcal R_{v,B,L}}$，令：

$$
m_{v,\tau}=|\mathcal O_{v,\tau}|.
$$

令 $(t_0,\ldots,t_{m_{v,\tau}-1})\in(\mathbb P_{B,L})^{m_{v,\tau}}$ 是 $\mathcal O_{v,\tau}$ 在通常自然数次序下的严格递增枚举，定义有限序列：

$$
B_{v,\tau}
=
\bigl(
(t_0,x_{v,\tau,t_0}^{\mathrm{node}}),
\ldots,
(t_{m_{v,\tau}-1},x_{v,\tau,t_{m_{v,\tau}-1}}^{\mathrm{node}})
\bigr),
$$

并定义：

$$
g_{v,\tau}=(\tau,I_{v,\tau},B_{v,\tau})
\in\mathcal G_{v,B,L}.
$$

取两个不同标签 $\mathtt{group}$ 与 $\mathtt{injectRecord}$。定义节点 $v$ 的输入记录集合：

$$
\mathcal U_{v,B,L}^{\mathrm{rec}}
=
\begin{cases}
\{\mathtt{group}\}\times\Theta\times\mathcal G_{v,B,L},
&v\neq v_{\mathrm{in}},\\
\bigl(\{\mathtt{group}\}\times\Theta\times\mathcal G_{v_{\mathrm{in}},B,L}\bigr)
\cup
\bigl(\{\mathtt{injectRecord}\}\times\Theta\times\mathcal B_{\mathrm{in}}^{B,L}\bigr),
&v=v_{\mathrm{in}}.
\end{cases}
$$

定义时间投影：

$$
\operatorname{utime}((\mathtt{group},\theta,g))=\theta,
$$

若 $v=v_{\mathrm{in}}$，还定义：

$$
\operatorname{utime}((\mathtt{injectRecord},\theta,b))=\theta.
$$

定义合法规范输入序列集合 $\mathfrak U_{v,B,L}\subseteq(\mathcal U_{v,B,L}^{\mathrm{rec}})^\star$。序列 $\mathbf U=(u_0,\ldots,u_{n-1})\in(\mathcal U_{v,B,L}^{\mathrm{rec}})^n$ 属于 $\mathfrak U_{v,B,L}$，当且仅当对每个 $i,j\in[n]$：

$$
\operatorname{utime}(u_i)=\operatorname{utime}(u_j)
\Longrightarrow
i=j,
$$

且对每个 $i\in[n]$ 满足 $i+1<n$：

$$
\operatorname{utime}(u_i)<_\Theta\operatorname{utime}(u_{i+1}).
$$

现在定义由执行记录 $\mathscr X_{B,L}^P$ 产生的节点输入记录集合。先定义分组轮次集合：

$$
\mathcal T_v^{\mathrm{grp}}(\mathscr X_{B,L}^P)
=
\{\tau\in\mathbb N
\mid
I_{v,\tau}^{\mathcal M}\neq0_{\mathcal R_{v,B,L}}
\text{ 且 }
(\tau,i_{\mathrm{commit}})\in\Theta_{B,L}^{\mathrm{run}}
\}.
$$

对 $\tau\in\mathcal T_v^{\mathrm{grp}}(\mathscr X_{B,L}^P)$，定义分组输入记录：

$$
u_{v,\tau}^{\mathrm{grp}}
=
(\mathtt{group},(\tau,i_{\mathrm{commit}}),g_{v,\tau})
\in\mathcal U_{v,B,L}^{\mathrm{rec}}.
$$

若 $v=v_{\mathrm{in}}$ 且 $t\in\mathbb I_{B,L}$，定义注入输入记录：

$$
u_t^{\mathrm{inj}}
=
(\mathtt{injectRecord},\theta_t^{\mathrm{in}},b_t^{\mathrm{in}})
\in\mathcal U_{v_{\mathrm{in}},B,L}^{\mathrm{rec}}.
$$

定义有限集合：

$$
\mathsf{USet}_v(\mathscr X_{B,L}^P)
=
\{u_{v,\tau}^{\mathrm{grp}}
\mid
\tau\in\mathcal T_v^{\mathrm{grp}}(\mathscr X_{B,L}^P)\}
$$

若 $v\neq v_{\mathrm{in}}$；若 $v=v_{\mathrm{in}}$，定义：

$$
\mathsf{USet}_{v_{\mathrm{in}}}(\mathscr X_{B,L}^P)
=
\{u_{v_{\mathrm{in}},\tau}^{\mathrm{grp}}
\mid
\tau\in\mathcal T_{v_{\mathrm{in}}}^{\mathrm{grp}}(\mathscr X_{B,L}^P)\}
\cup
\{u_t^{\mathrm{inj}}\mid t\in\mathbb I_{B,L}\}.
$$

集合 $\mathsf{USet}_v(\mathscr X_{B,L}^P)$ 有限，因为 $\mathcal M$ 和 $\mathbb I_{B,L}$ 都有限。函数 $\operatorname{utime}$ 在该集合上单射：两个分组记录若时间相同则轮次相同，因而是同一记录；两个注入记录若时间相同则全局位置相同；分组记录使用阶段 $i_{\mathrm{commit}}$，注入记录使用阶段 $i_{\mathrm{inject}}$，二者阶段不同。

令 $n_v=|\mathsf{USet}_v(\mathscr X_{B,L}^P)|$。定义节点 $v$ 的规范输入序列：

$$
\mathbf U_v(\mathscr X_{B,L}^P)
=
(u_0,\ldots,u_{n_v-1})
\in
(\mathcal U_{v,B,L}^{\mathrm{rec}})^{n_v}
$$

为唯一满足下列两个条件的序列：

$$
\operatorname{elem}(\mathbf U_v(\mathscr X_{B,L}^P))
=
\mathsf{USet}_v(\mathscr X_{B,L}^P),
$$

且对每个 $i\in[n_v]$ 满足 $i+1<n_v$：

$$
\operatorname{utime}(u_i)<_\Theta\operatorname{utime}(u_{i+1}).
$$

由有限集合上的严格全序枚举，$\mathbf U_v(\mathscr X_{B,L}^P)$ 存在且唯一，并且 $\mathbf U_v(\mathscr X_{B,L}^P)\in\mathfrak U_{v,B,L}$。

### 定义 6.2：节点参考转导器

对节点 $v$，定义完整产物集合：

$$
\mathsf{Artifact}_{v,B,L}^P
=
(\mathcal{SI}_{v}^{C_B})^\star
\times
\mathcal L_{v,B,L}^\star
\times
\mathcal Q_{v,B,L}^\star
\times
\mathcal{RR}_{v,B,L}^\star
\times
\mathcal R_{B,L}^\star
\times
\widetilde{\mathcal S}_v.
$$

节点参考转导器是确定函数：

$$
\operatorname{Ref}_{v,B,L}^P:
\mathfrak U_{v,B,L}
\times
\widetilde{\mathcal S}_v
\to
\mathsf{Artifact}_{v,B,L}^P.
$$

输入 $(\mathbf U_v,\widetilde S_v^B)$ 的函数值写为：

$$
\operatorname{Ref}_{v,B,L}^P(\mathbf U_v,\widetilde S_v^B)
=
(\mathbf\Sigma_v^P,\mathbf H_v^P,\mathbf Q_v^P,
\mathbf R_v^P,\mathbf M_{v,\mathrm{out}}^P,
\widetilde S_v^{P,+}).
\tag{D-6.2}
$$

六个坐标分别是状态输入记录序列、局部输出记录序列、状态提交记录序列、路由记录序列、出站消息序列和右侧局部状态。

本页不强制规定 $\operatorname{Ref}_{v,B,L}^P$ 内部必须是 O、J 或 F 的哪种具体计算。配置 $P$ 的含义由事件头形状、事件值、路由记录和实现给出的相等性测试共同确定。若实现声称某个联合或融合 kernel 等价于逐 `owner` 折叠，必须另外证明它在式 D-6.2 的六个坐标上完全相等。

### 定义 6.3：节点分块算子契约

节点 $v$ 的分块算子是函数：

$$
\mathcal C_{v,B,L}^P:
\mathfrak U_{v,B,L}
\times
\widetilde{\mathcal S}_v
\to
\mathsf{Artifact}_{v,B,L}^P.
$$

称它满足精确节点分块契约，当且仅当对所有 $\mathbf U_v\in\mathfrak U_{v,B,L}$：

$$
\mathcal C_{v,B,L}^P(\mathbf U_v,\widetilde S_v^B)
=
\operatorname{Ref}_{v,B,L}^P(\mathbf U_v,\widetilde S_v^B).
\tag{A-6.3}
$$

该等式比较式 D-6.2 的全部六个坐标。只比较最终状态、最终读出或总消息数不构成精确节点分块契约。

## 7. 有限性与事件 DAG

### 引理 7.1：当前窗口事件与消息有限

若 $\mathscr X_{B,L}^P\in\mathfrak X_{B,L}^P$，则其中的消息集合 $\mathcal M$ 和事件集合 $\mathcal E$ 都是有限集。

**证明。**

由定义 5.6，执行记录中的 $\mathcal E$ 满足：

$$
\mathcal E\in\mathcal P_{\mathrm{fin}}(\mathfrak E_{B,L}^P),
$$

并且 $\mathcal M$ 满足：

$$
\mathcal M\in\mathcal P_{\mathrm{fin}}(\mathcal R_{B,L}).
$$

按定义 0.2，$\mathcal P_{\mathrm{fin}}$ 的元素都是有限集。

<div class="qed" aria-label="证毕">∎</div>

### 引理 7.2：窗口事件图是有限 DAG

若执行记录满足定义 5.6、定义 5.7 与定义 5.8，则事件图 $D_{\mathscr X}=(\mathcal E,\mathcal A)$ 是有限 DAG。

**证明。**

有限性由引理 7.1 给出。

定义集合：

$$
\mathcal K_{\lambda}
=
\Theta\times\mathbb N.
$$

在 $\mathcal K_{\lambda}$ 上使用字典序。定义函数：

$$
\lambda:\mathcal E\to\mathcal K_{\lambda}.
$$

若 $e$ 是 carry 事件，定义：

$$
\lambda(e)=(\operatorname{time}(e),0).
$$

若 $e\in\mathcal E_{\mathrm{state}}$，定义：

$$
\lambda(e)=\operatorname{stateKey}(e).
$$

若 $e=e_t^{\mathrm{out}}$，定义：

$$
\lambda(e)=(\theta_t^{\mathrm{out}},0).
$$

对任意消息边 $(e,e')\in\mathcal A_{\mathrm{msg}}$，存在消息 $m$ 使 $e=\operatorname{producer}(m)$ 且 $e'=\operatorname{consumer}(m)$。由定义 5.6：

$$
\operatorname{time}(e)<_\Theta\operatorname{arrival}(m)<_\Theta\operatorname{time}(e'),
$$

所以 $\lambda(e)<\lambda(e')$。

对任意状态边 $(e,e')\in\mathcal A_{\mathrm{state}}$，定义 5.7 选择的提交记录 $q$ 满足：

$$
\operatorname{ckey}(q)<_{\mathsf{CKey}}\operatorname{stateKey}(e').
$$

而 $q$ 由事件 $e$ 产生，由式 A-5.8c 可得 $\operatorname{stateKey}(e)=\operatorname{ckey}(q)$，所以 $\lambda(e)<\lambda(e')$。

对任意读出边 $(e,e_t^{\mathrm{out}})\in\mathcal A_{\mathrm{read}}$，由定义 5.7，存在提交记录 $q_t^{\mathrm{read}}$ 使 $(e,q_t^{\mathrm{read}})\in\mathcal C_t^{\mathrm{read}}$，且：

$$
\operatorname{ctime}(q_t^{\mathrm{read}})<_\Theta\theta_t^{\mathrm{out}}.
$$

由式 A-5.8c，$\lambda(e)=\operatorname{ckey}(q_t^{\mathrm{read}})$。因此：

$$
\lambda(e)<\lambda(e_t^{\mathrm{out}}).
$$

因此每条依赖边都使 $\lambda$ 严格增加。若存在有向环 $e_0\to e_1\to\cdots\to e_k=e_0$，沿环传递得到 $\lambda(e_0)<\lambda(e_0)$，与字典序的反自反性矛盾。因此无环。

<div class="qed" aria-label="证毕">∎</div>

## 8. 流式调度、分块调度与主定理

### 定义 8.1：绝对时间流式调度

绝对时间流式调度是按 $<_\Theta$ 递增处理 $\Theta_{B,L}^{\mathrm{run}}$ 中的事件，并把 carry 事件值作为左边界已给定根事件的调度。它满足：

1. 左边界状态为 $\widetilde S_v^B$。
2. 左边界在途消息为 $\mathcal M_B^\partial$。
3. 在 $\theta_t^{\mathrm{in}}$ 执行输入事件 $e_t^{\mathrm{in}}$。
4. 在消息到达轮次的节点提交阶段执行相应节点事件。
5. 在 $\theta_t^{\mathrm{out}}$ 执行读出事件 $e_t^{\mathrm{out}}$。
6. 产生的消息按单位时延进入未来轮次。
7. 到达时间晚于 $\beta_{B+L}$ 的未消费消息进入右边界延续状态。

该定义是参考语义，不规定物理线程或设备执行顺序。

### 定义 8.2：空间拓扑序

空间 DAG 的拓扑序是有限序列：

$$
\pi=(v_0,\ldots,v_{|V|-1})\in V^{|V|}
$$

满足：

$$
\operatorname{occ}(\pi,v)=1
\qquad(v\in V),
$$

并且若 $(v_i,v_j)\in E$，则 $i<j$。

### 引理 8.3：有限 DAG 存在拓扑序

定义 2.1 的每个有限空间 DAG 都至少存在一个定义 8.2 意义下的拓扑序。

**证明。**

先证明任意有限非空 DAG 至少有一个入度为零的节点。反设每个节点都有入边。从任意节点 $v_0$ 开始，递归选择 $v_{j+1}$ 使 $(v_{j+1},v_j)\in E$。由于 $V$ 有限，序列 $v_0,v_1,\ldots$ 中存在 $a<b$ 使 $v_a=v_b$，从而得到有向环，矛盾。

对 $|V|$ 作归纳。若 $|V|=1$，唯一节点序列就是拓扑序。若 $|V|>1$，取入度为零的节点 $u$，删除 $u$ 及其出边得到较小 DAG。由归纳假设，剩余节点存在拓扑序。把 $u$ 放在该序列最前面，得到原图的拓扑序。

<div class="qed" aria-label="证毕">∎</div>

### 定义 8.4：节点拓扑序分块调度

给定拓扑序 $\pi=(v_0,\ldots,v_{|V|-1})$ 和执行记录 $\mathscr X_{B,L}^P$。节点拓扑序分块调度按 $\pi$ 处理空间节点。

处理节点 $v$ 时，使用定义 6.1 给出的规范输入序列：

$$
\mathbf U_v(\mathscr X_{B,L}^P).
$$

该序列由三类记录构成：

1. 左边界在途消息中目标为 $v$ 且到达当前窗口内的消息分组。
2. 已经处理完的空间前驱节点派发到 $v$ 且到达当前窗口内的消息分组。
3. 当 $v=v_{\mathrm{in}}$ 时的当前窗口注入记录 $b_t^{\mathrm{in}}$。

然后调用：

$$
\mathcal C_{v,B,L}^P(\mathbf U_v(\mathscr X_{B,L}^P),\widetilde S_v^B).
$$

该调用产物中的出站消息被放入后继节点的待处理输入。若消息到达时间晚于 $\beta_{B+L}$，则它不在当前窗口内被消费，而进入右边界在途消息集合。

### 定理 8.5：全局窗口 general DAG 调度等价定理

固定 $B,L,R,G,C_B,x_{B:B+L}$ 与语义配置 $P$。假设：

1. $G=(V,E)$ 满足定义 2.1 的有限空间 DAG 条件。
2. $R=d_{\min}$ 满足式 A-2.4，且时间阶段满足式 A-1.3。
3. $C_B\in\mathsf{Cont}_B$。
4. 执行记录 $\mathscr X_{B,L}^P\in\mathfrak X_{B,L}^P$ 满足定义 5.1--5.8，右边界延续状态按定义 5.9 构造，且事件值满足定义 5.11 的依赖完备性。
5. 对每个 $v\in V$，分块算子 $\mathcal C_{v,B,L}^P$ 满足式 A-6.3。

则绝对时间流式调度与节点拓扑序分块调度产生相同的以下对象：

1. 每个节点的规范输入序列 $\mathbf U_v$。
2. 每个节点的状态输入记录序列、局部输出记录序列、提交记录序列、路由记录序列、出站消息序列和右侧局部状态。
3. 每条消息的完整八元组、生产者和消费者。
4. 当前窗口读出族 $(y_t)_{t\in\mathbb I_{B,L}}$。
5. 右边界延续状态 $C_{B+L}$。

**证明。**

取空间拓扑序：

$$
\pi=(v_0,\ldots,v_{|V|-1}).
$$

对拓扑序下标做归纳。对每个节点 $v_i$，记流式调度构造的规范输入序列为 $\mathbf U_{v_i}^{\mathrm{stream}}$，分块调度构造的规范输入序列为 $\mathbf U_{v_i}^{\mathrm{block}}$。两者都必须满足定义 6.1 的构造规则。

边界在途消息集合 $\mathcal M_B^\partial$ 和边界状态 $\widetilde S_v^B$ 是两种调度的共同输入。因此，对任何节点 $v$，来自左边界且目标为 $v$ 的消息在两种调度中相同。

若 $i=0$，则 $v_0=v_{\mathrm{in}}$。理由如下：定义 2.1 要求每个节点都从 $v_{\mathrm{in}}$ 可达；若 $u\neq v_{\mathrm{in}}$，则存在从 $v_{\mathrm{in}}$ 到 $u$ 的长度大于 $0$ 的有向路径，所以任意拓扑序都把 $v_{\mathrm{in}}$ 放在 $u$ 之前。因此拓扑序第一项只能是 $v_{\mathrm{in}}$。

节点 $v_{\mathrm{in}}$ 没有空间前驱，故其规范输入只由左边界目标为 $v_{\mathrm{in}}$ 的在途消息和当前注入记录 $b_t^{\mathrm{in}}$ 构成。这些对象在两种调度中相同，所以：

$$
\mathbf U_{v_{\mathrm{in}}}^{\mathrm{stream}}
=
\mathbf U_{v_{\mathrm{in}}}^{\mathrm{block}}.
$$

由式 A-6.3，两种调度对 $v_{\mathrm{in}}$ 得到相同的式 D-6.2 六类产物，特别是相同的出站消息序列。

假设结论对 $v_0,\ldots,v_{i-1}$ 成立。考虑 $v_i$。由拓扑序定义，所有指向 $v_i$ 的空间前驱都属于 $\{v_0,\ldots,v_{i-1}\}$。根据归纳假设，这些前驱在两种调度中产生相同的出站消息序列。再加上两种调度共同拥有的左边界在途消息，可知 $v_i$ 的全部入站消息相同。若 $v_i=v_{\mathrm{in}}$，当前注入记录也相同。因此：

$$
\mathbf U_{v_i}^{\mathrm{stream}}
=
\mathbf U_{v_i}^{\mathrm{block}}.
$$

再由式 A-6.3，两种调度在 $v_i$ 上产生相同的六类产物。归纳完成，故所有节点产物相同。

对每个 $t\in\mathbb I_{B,L}$，读出事件 $e_t^{\mathrm{out}}$ 的事件头相同。若 $\mathcal C_t^{\mathrm{read}}\neq\varnothing$，则两种调度具有相同的最大提交记录 $q_t^{\mathrm{read}}$ 和相同的读出直接前驱事件值；若 $\mathcal C_t^{\mathrm{read}}=\varnothing$，则两种调度具有相同的读出边界参数 $\widetilde S_{v_{\mathrm{out}}}^B$。由定义 5.11 的事件值依赖完备性，每个 $y_t$ 相同。

右边界状态由式 D-5.9b 定义，只读取各节点在 $\beta_{B+L}$ 前的最大提交记录和未消费且到达晚于 $\beta_{B+L}$ 的消息。两种调度的提交轨迹、消息集合和消费函数相同，所以 $C_{B+L}$ 相同。

<div class="qed" aria-label="证毕">∎</div>

### 定义 8.6：单窗口转移关系

定义单窗口转移关系：

$$
\mathcal T_{B,L}^P
\subseteq
\left(X^{\mathbb I_{B,L}}\times\mathsf{Cont}_B\right)
\times
\left(Y^{\mathbb I_{B,L}}\times\mathsf{Cont}_{B+L}\right)
$$

如下。对：

$$
x\in X^{\mathbb I_{B,L}},
\quad
C\in\mathsf{Cont}_B,
\quad
y\in Y^{\mathbb I_{B,L}},
\quad
C'\in\mathsf{Cont}_{B+L},
$$

规定：

$$
((x,C),(y,C'))\in\mathcal T_{B,L}^P
$$

当且仅当存在满足定理 8.5 前提的执行记录：

$$
\mathscr X_{B,L}^P
=
(x,C,\mathcal E,\mathcal M,\operatorname{producer},\operatorname{consumer},\mathcal A)
$$

使得对每个 $t\in\mathbb I_{B,L}$：

$$
y(t)=\operatorname{value}(e_t^{\mathrm{out}}),
$$

且：

$$
C'=C_{B+L}(\mathscr X_{B,L}^P).
$$

若关系 $\mathcal T_{B,L}^P$ 对第一坐标单值，即对任意 $(x,C)$ 至多存在一个 $(y,C')$ 使 $((x,C),(y,C'))\in\mathcal T_{B,L}^P$，则可把 $\mathcal T_{B,L}^P$ 视为部分函数：

$$
\mathcal T_{B,L}^P:
X^{\mathbb I_{B,L}}\times\mathsf{Cont}_B
\rightharpoonup
Y^{\mathbb I_{B,L}}\times\mathsf{Cont}_{B+L}.
$$

### 推论 8.7：从中间开始的 `prefill == decode` 形式

若关系 $\mathcal T_{B,L}^P$ 对第一坐标单值，并且定理 8.5 的节点分块契约成立，则节点拓扑序分块执行与定义 8.1 的同一窗口绝对时间流式执行得到同一 $(y,C_{B+L})$。

若还要把该窗口执行拆成 $L$ 个长度为 $1$ 的相邻窗口转移：

$$
\mathcal T_{B,1}^P,\mathcal T_{B+1,1}^P,\ldots,\mathcal T_{B+L-1,1}^P,
$$

则需要另行证明这些相邻窗口的右边界状态与下一窗口左边界状态逐一相等；该切分兼容性不由单个窗口定理自动给出。

**证明。**

定理 8.5 已证明定义 8.1 的窗口流式调度与节点拓扑序分块调度在当前窗口上产生相同读出函数 $y\in Y^{\mathbb I_{B,L}}$ 与右边界延续状态 $C_{B+L}$。若 $\mathcal T_{B,L}^P$ 单值，则这个关系值可无歧义地写成部分函数值。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.8：窗口局部性

给定两个全局输入流：

$$
\mathbf x,\mathbf x'\in\mathsf{Stream}_X.
$$

令 $x,x'\in X^{\mathbb I_{B,L}}$ 分别为它们在 $\mathbb I_{B,L}$ 上的限制。若：

$$
x=x',
$$

则对任意 $C_B\in\mathsf{Cont}_B$，集合：

$$
\{(y,C')\mid ((x,C_B),(y,C'))\in\mathcal T_{B,L}^P\}
$$

等于集合：

$$
\{(y,C')\mid ((x',C_B),(y,C'))\in\mathcal T_{B,L}^P\}.
$$

**证明。**

关系 $\mathcal T_{B,L}^P$ 的定义只使用当前窗口输入函数 $x\in X^{\mathbb I_{B,L}}$ 与左边界延续状态 $C_B$。它不把 $\mathbf x$ 或 $\mathbf x'$ 在 $\mathbb N\setminus\mathbb I_{B,L}$ 上的值作为变量。由 $x=x'$，两个集合按外延相等。

<div class="qed" aria-label="证毕">∎</div>

该推论说明“从中间开始”不是把 $x_0,\ldots,x_{B-1}$ 重新放入当前 `chunk`，而是把它们已经造成的影响压入给定的 $C_B$。如果 $C_B$ 不同，即使当前限制函数 $x_{B:B+L}$ 相同，窗口输出也可以不同。

## 9. 归属语义、性能边界与设计含义

### 9.1 `owner`、`frontier` 与事件来源不是同一对象

对消息 $m$：

$$
\operatorname{owner}(m)\in\mathbb P_{B,L}
$$

是归属索引；

$$
\operatorname{frontier}(m)\in\mathbb F_{B,L}
$$

是当前窗口变量上的因果前沿上界；

$$
\operatorname{producer}(m),\operatorname{consumer}(m)
$$

是消息生命周期函数给出的事件来源关系。相同的 `owner/frontier` 可以对应不同消息标识符、不同路径和不同事件来源，所以不能用 `owner/frontier` 代替事件 DAG。

### 9.2 同刻多 `owner` 到达时信号属于谁

若同一节点 $v$、同一轮次 $\tau$ 有多个非空桶 $I_{v,\tau,t}$，则这些桶先形成集合 $\mathcal O_{v,\tau}$ 与序列 $B_{v,\tau}$。真正发往下游的归属由节点事件值中的局部输出记录决定：

$$
\operatorname{local}(\operatorname{value}(e))
\in
\mathcal L_{v,B,L}^{\star}.
$$

因此有三种可定义语义：

1. 分别输出：产生多个 $(t,z_t)$。
2. 联合但保留归属：联合计算后仍产生多个 $(t,z_t)$。
3. 融合输出：产生一个或少数记录 $(t^\star,z^\star)$，其中 $z^\star\neq\bot$，且 $t^\star$ 是节点转导器明确写出的 `owner`；常见选择是 $t^\star=\operatorname{frontier}_v^{\mathcal Z}(z^\star)$。

三者都可以进入定理 8.5，但它们是不同参考语义。若一个节点把多个输入压成不可逆充分统计量，那么后续执行只需保持这个参考语义；若它声称等价于分别输出的参考语义，就必须证明式 A-6.3 的完整产物相等。

### 9.3 general DAG 能从中间开始，但不自动低 span

定理 8.5 只依赖空间拓扑序，不依赖所有路径等长。历史长路径消息通过 $\mathcal M_B^\partial$ 进入当前窗口；当前长路径消息通过 $\mathcal M_{B+L}^\partial$ 离开当前窗口。这样，有限窗口执行可以从任意 $B$ 开始。

但高性能还需要额外性质。对每个节点 $v$，可以给出一个实现操作 DAG：

$$
(\mathcal O_v^{\mathrm{op}},\mathcal A_v^{\mathrm{op}}),
$$

其中 $\mathcal O_v^{\mathrm{op}}$ 是有限操作集合，$\mathcal A_v^{\mathrm{op}}\subseteq\mathcal O_v^{\mathrm{op}}\times\mathcal O_v^{\mathrm{op}}$ 是操作依赖关系。若最长操作依赖路径随节点输入记录数线性增长，则该节点只是把顺序链藏进本地 kernel；正确性成立，但没有 Transformer/Mamba 意义上的高性能 chunk prefill。

适合优先研究的节点实现族包括：

1. `token` 局部映射，例如 FFN。
2. 因果批量计算，例如 decode-only Transformer attention。
3. 可扫描转移，例如 SSM、Mamba 或线性注意力累加器。
4. 分段集合计算，例如同一 $(v,\tau)$ 的有限集合交互。
5. 顺序回退，用作正确性基线而非性能主张。

### 9.4 固定来源槽位作为稀疏上界示例

给定 $K\in\mathbb N_{>0}$，定义来源槽位集合：

$$
\mathsf{Slot}_{B,L,K}
=
\mathbb P_{B,L}\times[K].
$$

一个槽位赋值是函数：

$$
\sigma:\mathcal M\to\mathsf{Slot}_{B,L,K}.
$$

若要求同一槽位上的消息沿空间 DAG 形成单链，且每个来源位置最多使用 $K$ 个槽位，则每个来源位置的空间节点访问次数不超过 $K|V|$。因此当前窗口中新注入位置贡献的节点访问数有上界：

$$
LK|V|.
$$

边界历史消息的槽位访问数应单独计入 $\mathcal M_B^\partial$ 的剩余路径预算，不能免费并入当前 $L$ 个输入位置。

## 10. 当前可主张与不可主张

当前可以主张：

1. general DAG 不需要等层化即可定义从中间开始的有限窗口执行。
2. 当前输入变量可以是 $x_{B:B+L}$，历史影响通过 $C_B$ 提供。
3. 带 `owner/frontier/arrival` 的消息和显式生命周期函数足以区分归属、因果前沿和来源关系。
4. 在节点分块契约成立时，绝对时间流式调度可重排为节点拓扑序分块调度。
5. 分块调度可产生同一当前读出和同一右边界延续状态。

当前不能主张：

1. 任意节点转导器都有低并行跨度。
2. 任意选择器都兼容 Transformer/Mamba 意义上的高性能 prefill。
3. 不可逆聚合之后仍能恢复被聚合前的分别归属语义，除非另证该聚合是相应参考语义的充分统计量。
4. 带环空间图或零时延代数环已被覆盖。
5. 浮点重排误差、反向传播、设备后端和 Ascend NPU 实现已由本页定理解决。

## 11. 实现检查清单

实现 Tide general DAG 窗口执行时，至少需要记录并对齐：

1. 左边界状态 $\widetilde S_v^B$。
2. 左边界在途消息集合 $\mathcal M_B^\partial$。
3. 当前注入记录 $b_t^{\mathrm{in}}$。
4. 每条消息的八元组。
5. 每条消息的生产者与消费者。
6. 每个节点的规范输入序列 $\mathbf U_v$。
7. 每个节点的式 D-6.2 六类产物。
8. 每个读出 $y_t$。
9. 右边界状态 $\widetilde S_v^{B+L}$。
10. 右边界在途消息集合 $\mathcal M_{B+L}^\partial$。

若只对齐最终 logits，而不对齐上述对象，就不能判断差异来自节点 kernel、路由、状态边界、消息生命周期还是读出切面。
