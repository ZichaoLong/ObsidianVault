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

# Token-Owned General DAG Routing

> [!summary] 本页定位
> 本页研究一个固定周期 Tide reference model。Token $t$ 在 absolute internal round $Rt$ 注入；模型在 $R(t+1)$ 的固定 boundary 产生第 $t$ 个 readout；空间结构是任意有限 unit-delay DAG，长路径消息可以跨 boundary 继续传播。本文定义消息、状态、typed logical event、event dependency DAG、三种同刻 transition profile，以及 absolute-time streaming 与 node-topological chunk 两种 schedules。

> [!important] 核心结论
> Leveled DAG 不是 closed finite exact chunk execution 的必要条件。对本文固定周期、空间无环的 strict profile，只要消息保留 owner/frontier/timestamp，每个 mutable state 有唯一 node owner，routing 只沿空间 DAG 前进，并且每个 node 对完整 timestamped event stream 提供 exact chunk transducer，absolute-time streaming schedule 就可以等价重排为 node-topological chunk schedule。该结论包含固定周期 readout artifacts，但不自动给出低 span，也尚未构造可直接接续 decode 的 boundary state。

> [!warning] Correctness 不自动推出高性能
> 本页主定理只证明 streaming 与 chunk 两种 schedules 计算同一 reference semantics。它允许一个 node 在一次调用中处理完整 chunk，并消除逐 token 的全局 host orchestration；但若 node-local transition 本身有顺序 state/control chain，其内部 span 仍可随事件数线性增长。Transformer/Mamba 意义上的低 token-axis span 还要求 causal attention、scan、segmented bulk、packed sparse kernel 等额外结构，并要求总 event 数受控。

## 0. 记号与固定周期外部接口

### 定义 0.1：基础集合记号

定义自然数与正整数：

$$
\mathbb N=\{0,1,2,\ldots\},
$$

$$
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $L\in\mathbb N$，定义：

$$
[L]=\{0,1,\ldots,L-1\}.
$$

若 $L=0$，则 $[L]=\varnothing$。

有限序列使用圆括号表示。有限 multiset 保留重复元素，不因 payload 相等而去重。

本文沿用 [[step-transition-mathematical-specification#定义 1.2：顺序 fold|顺序 fold]]、[[step-transition-mathematical-specification#定义 3.6a：logical event DAG program|logical event DAG]] 与 [[adaptive-routing-prefill-impossibility]] 的结论，但本页所需对象均在首次使用前重新定义。

### 定义 0.2：输入序列与固定周期

给定 token space $X$、readout space $Y$、chunk length $L\in\mathbb N$、固定周期：

$$
R\in\mathbb N_{>0},
$$

以及输入序列：

$$
x_{0:L}=(x_0,\ldots,x_{L-1})\in X^L.
$$

对每个 $t\in[L]$，定义 token $x_t$ 的 absolute injection round：

$$
\operatorname{InTime}(t)=Rt.
\tag{GD-0.1}
$$
^eq-fixed-injection-time

定义第 $t$ 个 readout 的 absolute round：

$$
\operatorname{OutTime}(t)=R(t+1).
\tag{GD-0.2}
$$
^eq-fixed-readout-time

$R$ 是 reference semantics 的常数，不依赖 input value、node state、任何模型内部决策或当前 runtime activity。内部计算不能推迟或提前式 GD-0.1 与 GD-0.2 规定的 boundary。

这里 $R$ 首先是逻辑周期。若还要求真实设备每隔固定 wall-clock period $T_{\mathrm{ext}}>0$ 输出一个 token，则 implementation 必须证明第 $t$ 个 readout 在 wall-clock deadline $(t+1)T_{\mathrm{ext}}$ 前完成。该 real-time throughput 条件属于 performance witness，不由后文的 schedule-equivalence theorem 自动推出。

### 定义 0.3：Phase 与完整逻辑时间戳

取 phase 数：

$$
N_{\mathrm{phase}}\in\mathbb N_{>0},
\qquad
N_{\mathrm{phase}}\geq 6,
$$

以及按执行先后排列的 phase tuple：

$$
\mathcal P
=
(\varphi_0,\ldots,\varphi_{N_{\mathrm{phase}}-1}).
$$

定义完整逻辑时间戳集合：

$$
\Theta
=
\mathbb N\times\{0,\ldots,N_{\mathrm{phase}}-1\}.
$$

对 $(\tau,i),(\tau',j)\in\Theta$，定义 lexicographic strict order $<_{\Theta}$：

$$
(\tau,i)<_{\Theta}(\tau',j)
$$

当且仅当：

$$
\tau<\tau',
$$

或：

$$
\tau=\tau'
\quad\text{且}\quad
i<j.
$$

指定六个不同 phase indices：

$$
i_{\mathrm{arrive}},
i_{\mathrm{step}},
i_{\mathrm{commit}},
i_{\mathrm{read}},
i_{\mathrm{sample}},
i_{\mathrm{inject}}
\in
\{0,\ldots,N_{\mathrm{phase}}-1\},
$$

满足：

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
\tag{GD-0.3}
$$
^eq-boundary-phase-order

定义第 $t$ 个 token 的 injection timestamp：

$$
\theta_t^{\mathrm{in}}
=
(Rt,i_{\mathrm{inject}}),
$$

以及第 $t$ 个 readout 与 sampling timestamps：

$$
\theta_t^{\mathrm{out}}
=
(R(t+1),i_{\mathrm{read}}),
$$

$$
\theta_t^{\mathrm{sample}}
=
(R(t+1),i_{\mathrm{sample}}).
$$

因此当 $t+1\in[L]$ 时：

$$
\theta_t^{\mathrm{out}}
<_{\Theta}
\theta_t^{\mathrm{sample}}
<_{\Theta}
\theta_{t+1}^{\mathrm{in}}.
\tag{GD-0.4}
$$
^eq-read-sample-inject-order

### 定义 0.4：Teacher-Forced 与 Autoregressive 外部接口

在 teacher-forced/prefill reference 中，$x_{0:L}$ 是给定 boundary data；虽然物理实现可以一次持有整个 tensor，token $x_t$ 在逻辑上只能从 $\theta_t^{\mathrm{in}}$ 开始可见。

在 autoregressive reference 中，给定确定性 token selection function：

$$
\operatorname{SelectToken}:Y\to X,
$$

并要求第 $t$ 个固定周期 readout $y_t\in Y$ 产生后：

$$
x_{t+1}
=
\operatorname{SelectToken}(y_t),
\qquad t+1\in[L].
\tag{GD-0.5}
$$
^eq-autoregressive-token-selection

Arrival、node transition 与 state commit 均在 readout 之前完成，因此 absolute round $R(t+1)$ 到达 output node 的最短路径 message 可以影响 $y_t$。式 GD-0.4 保证随后先选择 token，最后注入下一 token。后文的 chunk correctness theorem 以给定输入序列的 teacher-forced reference 为比较对象；式 GD-0.5 额外定义 pure inference 如何把连续两个固定周期连接起来。

## 1. 一般 Unit-Delay 空间 DAG

### 定义 1.1：带输入输出的空间 DAG

一个带输入输出的空间 DAG 是三元组：

$$
(G,s,z),
$$

其中：

- $G=(V,E)$ 是有限有向无环图。
- $s\in V$ 是唯一 input node。
- $z\in V$ 是唯一 output node。
- $s\neq z$。
- 每个 $v\in V$ 都位于至少一条从 $s$ 到 $z$ 的有向路径上。

另外固定 node set $V$ 与 edge set $E$ 的 static total orders $<_{V}$、$<_{E}$，只用于 canonical serialization 与 deterministic tie-breaking；它们不表示额外计算依赖。

对 edge $(u,v)\in E$，$u$ 称为 $v$ 的直接空间前驱，$v$ 称为 $u$ 的直接空间后继。

### 定义 1.2：有向路径与路径长度

从 node $u$ 到 node $v$ 的一条有向路径是 node tuple：

$$
p=(v_0,v_1,\ldots,v_k),
$$

满足：

$$
v_0=u,\qquad v_k=v,
$$

并且对每个 $i\in\{0,\ldots,k-1\}$：

$$
(v_i,v_{i+1})\in E.
$$

路径 $p$ 的 edge 数称为路径长度，记为：

$$
|p|=k.
$$

定义从 input node 到 $v$ 的可达路径长度集合：

$$
\Lambda(v)
=
\{|p|\mid p\text{ 是从 }s\text{ 到 }v\text{ 的有向路径}\}.
$$

因为 $G$ 有限且无环，$\Lambda(v)$ 是有限非空集合。

定义空间 DAG 的最大路径长度：

$$
D
=
\max_{v\in V}\max\Lambda(v).
$$

由于有向路径不能重复经过同一个 node：

$$
D\leq |V|-1.
$$

定义 input 到 output 的最短路径长度：

$$
d_{\min}
=
\min\Lambda(z).
$$

本文固定周期 strict profile 取：

$$
R=d_{\min}.
\tag{GD-1.1}
$$
^eq-period-shortest-path

由 $s\neq z$，有 $d_{\min}\geq 1$，所以式 GD-1.1 与定义 0.2 的 $R\in\mathbb N_{>0}$ 一致。因此 token $t$ 沿最短 input-output path 产生的 signal 恰好在 absolute round $R(t+1)$ 到达 output boundary。式 [[#^eq-read-sample-inject-order|GD-0.4]] 进一步规定同一 boundary 上先 readout，再 sample，最后 injection。当 $D>R$ 时，更长路径仍会跨越该 boundary，并只能影响逻辑时间更晚的 state/readouts。

### 定义 1.3：Unit-delay edge

本文假设每条 edge 的 reference propagation delay 恰好为一个 global internal round：

$$
\operatorname{delay}(u,v)=1,
\qquad (u,v)\in E.
$$

这是一条语义约束，不是硬件传输延迟。物理 runtime 可以 fusion、buffer 或异步执行，但必须保持 logical arrival time。

> [!note] 一般 DAG 与 Leveled DAG
> 若对任意 node $v$，集合 $\Lambda(v)$ 只有一个元素，则所有从 $s$ 到 $v$ 的路径等长，旧文档中的 leveled DAG 是本页模型的特殊情形。本文不再把这一性质作为前提，也不通过 relay nodes 改变原 edge 的单位时延。

## 2. Prefix Causality 与固定周期路径时间

### 定义 2.1：Prefix-Causal Object 与 Causal Frontier

定义 frontier index space：

$$
\mathbb F_L
=
\{-1\}\cup[L].
$$

给定由输入序列 $x_{0:L}$ 决定的任意 semantic object $q$，以及 $c\in\mathbb F_L$。称 $q$ 是 $c$-prefix-causal 的，当且仅当对任意两个输入序列 $x_{0:L}$ 与 $\bar x_{0:L}$：

$$
x_j=\bar x_j,
\qquad
0\leq j\leq c,
$$

都蕴含两次 execution 中的 $q$ 相同。若 $c=-1$，该条件表示 $q$ 与全部 input tokens 无关。

若 $q$ 是一个动态产生的可选 record，则把它的值域扩展为：

$$
\mathcal Q_\bot
=
\mathcal Q\cup\{\bot\},
$$

其中 $\bot$ 表示该 record 不存在。因此“$q$ 相同”同时要求两次 execution 中 presence 与存在时的数值都相同。这里的 $q$ 仍只是 optional semantic object；$q=\bot$ 不表示发生了一次带空值的计算记录。

若 runtime 为 $q$ 声明：

$$
\operatorname{frontier}(q)=c,
$$

则要求 $q$ 至少是 $c$-prefix-causal 的。Frontier 可以是保守上界，不要求一定是最小依赖 token index。Input token 满足：

$$
\operatorname{frontier}(x_t)=t.
$$

### 定义 2.1a：抽象 Logical Event Header 与 Event Value

给定有限 event-kind set $\mathcal K$。一次已经实例化的 execution 中，一个 actual logical event header 是六元组：

$$
h_e
=
(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e),
\tag{GD-2.0}
$$
^eq-logical-event-header

其中：

- $\eta_e$ 是来自 static totally ordered id space 的、全局唯一且确定生成的 logical event id。
- $\kappa_e\in\mathcal K$ 是 event kind。
- $\ell_e\in V\cup\{\mathtt{external}\}$ 是 event location。
- $\theta_e\in\Theta$ 是 event value 对后继可见的 logical commit timestamp。
- $\Omega_e\subseteq[L]$ 是该 event 直接联合处理或标识的 owner support。
- $c_e\in\mathbb F_L$ 是 event value 的有效 causal frontier。

对每个 actual event header $h_e$，声明 value space $\mathcal V_e$，并赋予唯一 event value：

$$
\nu(e)\in\mathcal V_e.
$$

定义 actual event 的字段投影：

$$
\operatorname{id}(e)=\eta_e,
\quad
\operatorname{kind}(e)=\kappa_e,
\quad
\operatorname{loc}(e)=\ell_e,
$$

$$
\operatorname{time}(e)=\theta_e,
\quad
\operatorname{support}(e)=\Omega_e,
\quad
\operatorname{frontier}(e)=c_e.
$$

本文把二元组 $(h_e,\nu(e))$ 称为 logical event instance，并在 value 已明确时简写为 $e$。Actual event set 只包含真正发生的 events。动态 presence 不通过“value 为 $\bot$ 的假 event”表达，而通过 source event value 中的 optional route/message records 表达。一个已经发生的 node event 仍可以把“无 route-visible hidden”作为其结构化 value 的某个 $\bot$ 分量；这不表示该 event 未发生。

### 定义 2.1b：抽象 Event Graph 与 Dependency Edge

给定一次有限 execution 的 actual event set $\mathcal E$，以及二元关系：

$$
\mathcal A\subseteq\mathcal E\times\mathcal E.
$$

定义 event graph：

$$
D=(\mathcal E,\mathcal A).
$$

要求 $\mathcal A$ 中每个 pair 都表示 reference semantics 中的直接 data、state 或 control dependency：$e'$ 的 header、presence 或 value 读取了 $e$ 产生的某个 artifact。该关系此处可以不完备，但不能加入没有 semantic dependency 的任意 ordering edge。

若 $(e,e')\in\mathcal A$，称 $e$ 是 $e'$ 的 direct dependency，并记为：

$$
e\longrightarrow e'.
$$

若 $D$ 无有向环，则称其为 logical event DAG。这里尚未规定哪些 reference dependencies 必须进入 $\mathcal A$；第 7 节将为固定周期 Tide execution 实例化 relation $\mathcal A_L^P$，并定义 dependency completeness。

### 定义 2.1c：固定 Boundary Event Headers

定义 boundary event-kind set：

$$
\mathcal K_{\mathrm{bdry}}
=
\{\mathtt{inject},\mathtt{readout},\mathtt{sample}\}.
$$

对每个 $t\in[L]$，定义必定发生的 input event header：

$$
h_{e_t^{\mathrm{in}}}
=
(\eta_t^{\mathrm{in}},\mathtt{inject},s,
\theta_t^{\mathrm{in}},\{t\},t),
$$

以及必定发生的 fixed readout event header：

$$
h_{e_t^{\mathrm{out}}}
=
(\eta_t^{\mathrm{out}},\mathtt{readout},z,
\theta_t^{\mathrm{out}},[t+1],t).
$$

Autoregressive execution 还定义 sample event header：

$$
h_{e_t^{\mathrm{sample}}}
=
(\eta_t^{\mathrm{sample}},\mathtt{sample},\mathtt{external},
\theta_t^{\mathrm{sample}},[t+1],t).
$$

Teacher-forced execution 不实例化 sample event。Boundary event 的 value spaces 与 values 在定义 7.1 中登记；本定义只固定 event identity、kind、location、timestamp、support 与 frontier。

### 定义 2.2：Ambient Period 与 Round Offset

对 absolute round $\tau\in\mathbb N$，定义 ambient period index：

$$
q_R(\tau)
=
\left\lfloor\frac{\tau}{R}\right\rfloor,
$$

以及 period-local round offset：

$$
r_R(\tau)
=
\tau-Rq_R(\tau).
$$

由 Euclidean division：

$$
0\leq r_R(\tau)<R.
$$

$q_R(\tau)$ 是全局时钟已经进入的周期编号，不是任意 message 的 owner token。

### 定义 2.3：Path Age 与固定周期到达时间

给定 token index $t\in[L]$、node $v\in V$ 与一条从 $s$ 到 $v$ 的路径 $p$。定义该 path instance 的 path age：

$$
k(p)=|p|,
$$

absolute arrival round：

$$
A_R(t,p)
=
Rt+|p|,
\tag{GD-2.1}
$$
^eq-fixed-arrival-round

以及 arrival timestamp：

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(A_R(t,p),i_{\mathrm{arrive}}).
\tag{GD-2.2}
$$
^eq-fixed-arrival-timestamp

Path age 可以大于 $R$。此时该 path instance 在 token $t+1$ 的 injection boundary 之后才到达，固定周期本身不截断它。

### 推论 2.3a：最短路径在固定 Readout 前 Commit

若 $p$ 是从 $s$ 到 $z$ 的最短路径，则 $|p|=R$，并且：

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(R(t+1),i_{\mathrm{arrive}}).
$$

由式 GD-0.3：

$$
(R(t+1),i_{\mathrm{arrive}})
<_{\Theta}
(R(t+1),i_{\mathrm{commit}})
<_{\Theta}
\theta_t^{\mathrm{out}}.
$$

因此，只要最短路径到达所触发的 output-node transition 在本 round 正常执行，其 committed state 可以被第 $t$ 个固定 readout 读取。

**证明。**

由 $|p|=R$ 与式 GD-2.1，arrival round 为 $Rt+R=R(t+1)$；phase inequality 直接来自式 GD-0.3。

<div class="qed" aria-label="证毕">∎</div>

### 定义 2.4：Timestamp-Available Input Prefix

若 $L>0$，对任意 $\theta\in\Theta$，定义在 $\theta$ 之前已经完成 injection 的最大 token index：

$$
a_{R,L}(\theta)
=
\max
\left(
\{-1\}
\cup
\{t\in[L]\mid \theta_t^{\mathrm{in}}\leq_{\Theta}\theta\}
\right),
\tag{GD-2.3}
$$
^eq-available-prefix

其中 $\leq_{\Theta}$ 是由 $<_{\Theta}$ 诱导的非严格次序。

本文要求每个 kernel 只读取在其 timestamp 已经可见的 input tokens。任意在 timestamp $\theta$ 产生并声明 frontier 的 well-formed semantic object $q$ 必须具有有效 causal frontier，并满足：

$$
\operatorname{frontier}(q)
\leq
a_{R,L}(\theta)
\tag{GD-2.4}
$$
^eq-timestamp-frontier-bound

特别地，每个 logical event instance $e$ 必须满足：

$$
\operatorname{frontier}(e)
\leq
a_{R,L}(\operatorname{time}(e)),
$$

并且 $\nu(e)$ 是定义 2.1 意义下的 $\operatorname{frontier}(e)$-prefix-causal object。动态 event presence 的 prefix causality 必须在产生该 event 的 optional route/message record 上单独登记，不能由 actual event header 自行推出。

特别地，在 boundary round $R(t+1)$ 的 readout phase，下一次 injection 尚未发生，因此对每个 $t\in[L]$：

$$
a_{R,L}(\theta_t^{\mathrm{out}})=t.
\tag{GD-2.5}
$$
^eq-readout-prefix

**证明。**

Tokens $x_0,\ldots,x_t$ 的 injection timestamps 都不晚于 $\theta_t^{\mathrm{out}}$。若 $j>t$ 且 $j\in[L]$，则 $\theta_j^{\mathrm{in}}\geq_{\Theta}\theta_{t+1}^{\mathrm{in}}>_{\Theta}\theta_t^{\mathrm{out}}$；当 $t=L-1$ 时不存在这样的 $j$。代入式 [[#^eq-available-prefix|GD-2.3]] 即得式 GD-2.5。

<div class="qed" aria-label="证毕">∎</div>

### 例 2.5：不同 Token Path Instances 的同刻碰撞

考虑：

```text
s -----------------> v
s -> a -> b --------> v
```

记长路径为 $p_A=(s,a,b,v)$，短路径为 $p_B=(s,v)$。它们的长度分别为 $3$ 与 $1$。取固定周期：

$$
R=2.
$$

- Token A 的 index 为 $0$，沿长路径到达 $v$ 的 round 为 $A_R(0,p_A)=0+3=3$。
- Token B 的 index 为 $1$，沿短路径到达 $v$ 的 round 为 $A_R(1,p_B)=2+1=3$。

因此两个 path instances 在同一 node $v$、同一 arrival timestamp $(3,i_{\mathrm{arrive}})$ 到达。

### 命题 2.6：一般 DAG 中 Owner 不能由 Node 与时间恢复

若存在 node $v$、两个不同 token indices $t_A,t_B\in[L]$ 与两条从 $s$ 到 $v$ 的路径 $p_A,p_B$，满足：

$$
Rt_A+|p_A|
=
Rt_B+|p_B|,
$$

则 $(v,A_R(t_A,p_A))$ 不能唯一确定 path instance 的 token index。因此后文定义 message 时必须显式保留 owner 字段。

**证明。**

两个 path instances 的 arrival rounds 分别为：

$$
\tau_A=Rt_A+|p_A|,
$$

$$
\tau_B=Rt_B+|p_B|.
$$

由题设：

$$
\tau_B
=
Rt_B+|p_B|
=
Rt_A+|p_A|
=
\tau_A.
$$

但 $t_A\neq t_B$，所以 $(v,\tau)$ 不能唯一确定 owner。

<div class="qed" aria-label="证毕">∎</div>

这个命题说明 owner label 不是冗余字段。若把同刻不同 token paths 的 records 无标签合并，后续 output alignment、routing、loss、replay 与归因都会失去明确语义。

### 命题 2.7：前序 Token 晚到与 Owner Inversion 条件

取 $t_A<t_B$，并令两条 paths $p_A,p_B$ 都从 $s$ 到达同一 node $v$。则后序 token B 的 path instance 先于前序 token A 的 path instance 到达，当且仅当：

$$
|p_A|-|p_B|
>
R(t_B-t_A).
$$

二者同刻到达，当且仅当上式中的 $>$ 改为 $=$。

**证明。**

由式 [[#^eq-fixed-arrival-round|GD-2.1]]：

$$
\tau_A=Rt_A+|p_A|,
\qquad
\tau_B=Rt_B+|p_B|.
$$

因此：

$$
\tau_B<\tau_A
$$

当且仅当：

$$
Rt_B+|p_B|
<
Rt_A+|p_A|,
$$

移项即得结论。同刻条件同理。

<div class="qed" aria-label="证毕">∎</div>

这个命题表明：即使 input/output clock 固定，只要路径长度差超过 token injection round 差，一般 DAG 仍会出现后序 token path 先到。该事实由 topology 与固定 $R$ 共同决定，不由 selector 改写 timestamp。

## 3. 可选的双 Cortex 空间结构

### 定义 3.1：Input/Output 双 Cortex DAG

设 input cortex 为：

$$
G_I=(V_I,E_I),
$$

其执行方向从 input node $s$ 指向 input bridge node $b_I$。

设 output cortex 为：

$$
G_O=(V_O,E_O),
$$

其执行方向从 output bridge node $b_O$ 指向 output node $z$。

假设：

$$
V_I\cap V_O=\varnothing.
$$

增加唯一单向 bridge：

$$
(b_I,b_O).
$$

组合图定义为：

$$
G
=
\left(
V_I\cup V_O,\,
E_I\cup E_O\cup\{(b_I,b_O)\}
\right).
$$

$G_O$ 可以与 $G_I$ 反向同构，但反向同构只描述结构对应关系，不增加从 output cortex 返回 input cortex 的执行 edge。

### 引理 3.2：单向 Bridge 保持 DAG

若 $G_I$ 与 $G_O$ 都是 DAG，且不存在从 $V_O$ 指向 $V_I$ 的 edge，则定义 3.1 的组合图 $G$ 是 DAG。

**证明。**

假设 $G$ 中存在有向环。若该环完全位于 $V_I$ 或 $V_O$，分别与 $G_I$ 或 $G_O$ 是 DAG 矛盾。

若该环同时经过两侧，则它必须通过 bridge $(b_I,b_O)$ 从 $V_I$ 进入 $V_O$。要回到 $V_I$，环中必须存在一条从 $V_O$ 指向 $V_I$ 的 edge，但前提排除了这种 edge，矛盾。

所以 $G$ 无有向环。

<div class="qed" aria-label="证毕">∎</div>

## 4. Message、Inbox 与有限事件性

### 定义 4.1：Causally Labelled Timestamped Message

给定带 static total order 的 logical message-id space $\mathsf{MID}$、metadata space $\mathcal U$ 与 payload space $\mathcal P$。若不同 edges 使用不同 payload types，可把 $\mathcal P$ 取为带 edge/type tag 的 disjoint union。

一条 message 是 tuple：

$$
m=(\iota,t,c,\theta,u,v,\mu,p),
$$

属于：

$$
\mathsf{MID}
\times[L]
\times\mathbb F_L
\times\Theta
\times V\times V
\times\mathcal U
\times\mathcal P,
$$

其中：

- $\iota$ 是全局唯一 logical message id。
- $t\in[L]$ 是 owner token。
- $c\in\mathbb F_L$ 是满足定义 2.1 的 causal frontier。
- $t\leq c$，即 message frontier 同时覆盖 trajectory owner provenance。
- $\theta=(\tau,i_{\mathrm{arrive}})\in\Theta$ 是 arrival timestamp。
- $u\in V$ 是 source node。
- $v\in V$ 是 destination node。
- $(u,v)\in E$。
- $\mu\in\mathcal U$ 是 metadata，例如 birth slot、source port、route id 或 lineage id；不需要 metadata 时可令 $\mathcal U$ 为 singleton set。
- $p\in\mathcal P$ 是 payload。

定义字段读取函数：

$$
\operatorname{id}(m)=\iota,
\qquad
\operatorname{owner}(m)=t,
$$

$$
\operatorname{frontier}(m)=c,
\qquad
\operatorname{arrival}(m)=\theta,
\qquad
\operatorname{src}(m)=u,
\qquad
\operatorname{dst}(m)=v.
$$

若 $\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})$，定义：

$$
\operatorname{arrivalRound}(m)=\tau.
$$

记所有满足上述约束的 valid messages 的集合为 $\mathcal R$。对 node $v$，定义其 incoming message-record space：

$$
\mathcal R_v
=
\{m\in\mathcal R\mid\operatorname{dst}(m)=v\}.
$$

Message id 使重复 payload 仍保持为不同 messages。Logical message id 必须由 input id、route lineage、source/destination、owner/frontier、timestamp 或 birth slot 等语义字段确定性生成，不能来自依赖线程竞争顺序的全局自增计数。Reference semantics 不依赖物理线程首先写入 inbox 的顺序。

对每个 input token $t\in[L]$，定义不属于 edge message 集合的 boundary injection record：

$$
b_t^{\mathrm{in}}
=
(t,\theta_t^{\mathrm{in}},s,x_t).
$$

该 record 在第 7 节实例化为 input logical event。它的 owner/frontier 都是 $t$，但它不是从某条 spatial edge 到达的 message。

### 定义 4.2：Unit-delay dispatch

若 regular node event 在 absolute round $\tau$ 的 commit phase，或 input event 在 $(\tau,i_{\mathrm{inject}})$，产生带 owner $t'\in[L]$ 与 frontier $c'\in\mathbb F_L$ 的 output record，其中 $t'\leq c'$，并沿 selected edge $(v,w)\in E$ dispatch，则新 message 必须满足：

$$
\operatorname{owner}(m')=t',
\qquad
\operatorname{frontier}(m')=c',
$$

$$
\operatorname{arrival}(m')
=
(\tau+1,i_{\mathrm{arrive}}),
\tag{GD-3}
$$
^eq-unit-delay-dispatch

$$
\operatorname{src}(m')=v,
\qquad
\operatorname{dst}(m')=w.
$$

Routing 可以更新 payload、message id 与其他 metadata，但不能独立改写 node output 已声明的 owner/frontier，也不能改写 logical arrival timestamp。

### 定义 4.2a：Carry-Over Boundary Semantics

一条 message trajectory 是有限 message sequence：

$$
\gamma=(m_1,\ldots,m_q),
$$

满足 $m_1$ 是某个 boundary injection record $b_t^{\mathrm{in}}$ 产生的第一跳 edge message，并且对每个 $j<q$，消费 $m_j$ 的 node transition 产生了 $m_{j+1}$。Trajectory 可以在 selector 终止 dispatch 时结束，也可以在不同 trajectories 被 joint/fusion transition 消费时合并。

固定周期 boundary 本身不删除、吸收或重写任何已经存在的 edge message。一个 message 只会因为以下两种原因结束生命周期：

1. 它到达 destination 并被相应 node event 消费。
2. 产生它的 selector 明确选择不再 dispatch 后继 message。

特别地，若某条 trajectory 的下一条 message 的 arrival round 大于 $R(t+1)$，该 message 仍保留其式 GD-3 决定的 timestamp，并在后续 period 到达。Readout、sampling 与下一 token injection 不执行隐式 clear。

### 定义 4.3：按 Node、时间和 Owner 分桶的 Inbox

对 node $v$、absolute time $\tau$ 与 owner $t$，定义 finite message multiset：

$$
I_{v,\tau,t}
=
\left\{
m\ \middle|\
\operatorname{dst}(m)=v,\,
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}}),\,
\operatorname{owner}(m)=t
\right\}_{\mathrm{multi}}.
\tag{GD-4}
$$
^eq-general-owner-inbox

定义同刻到达 $v$ 的 owner 集合：

$$
\mathcal O_{v,\tau}
=
\{t\in[L]\mid I_{v,\tau,t}\neq\varnothing\}.
$$

把它按 token index 递增排列：

$$
O_{v,\tau}^{\uparrow}=(t_1,t_2,\ldots,t_m),
\qquad t_1<t_2<\cdots<t_m.
$$

### 定义 4.4：同 Owner、同刻聚合

对每个 node $v$，给定 input space $X_v$ 和确定性聚合器：

$$
\operatorname{Aggregate}_v:
\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\to X_v,
$$

其中 $\mathcal R_v$ 是到达 $v$ 的 message record 空间，$\mathcal M_{\mathrm{fin}}(\mathcal R_v)$ 表示其有限 multisets。

定义：

$$
x_{v,\tau,t}
=
\operatorname{Aggregate}_v(I_{v,\tau,t}).
\tag{GD-5}
$$
^eq-general-owner-aggregate

聚合值默认声明保守 frontier：

$$
\operatorname{frontier}(x_{v,\tau,t})
=
\max_{m\in I_{v,\tau,t}}
\operatorname{frontier}(m).
$$

若聚合器能够证明忽略了某些高-frontier messages，可以声明更小但仍有效的 frontier；不能在没有证明时降低 label。

如果聚合器与顺序无关，它直接作用于 multiset。若业务语义要求顺序，必须先按固定字段，例如 `(source node id, message id)`，做 canonical sort；不能使用物理 arrival race 作为隐式顺序。

不同 absolute times 的 messages 不在本步骤聚合。同一个 owner 可以因不同路径长度在同一 node 多次激活：

$$
x_{v,\tau_1,t},
\qquad
x_{v,\tau_2,t},
\qquad
\tau_1\neq\tau_2.
$$

### 引理 4.5：有限 Horizon

若 token 数为 $L>0$，则所有由这些 tokens 产生并沿 $G$ 传播的 messages 都满足：

$$
0\leq\tau\leq R(L-1)+D.
\tag{GD-6}
$$
^eq-finite-horizon

**证明。**

对每条 message 保留一个只用于 timing proof 的 witness $(t,p)$：$t\in[L]$ 是某个触发该 event chain 的 input injection，$p$ 是从 $s$ 到当前 destination 的有向路径，并满足：

$$
\tau=Rt+|p|.
$$

从 boundary injection record 产生的第一条 message 使用从 $s$ 开始的相应一-edge path。若 node invocation 由一条带 witness $(t,p)$ 的 incoming message 触发，则沿 edge $(v,w)$ 发出的任意 message 可以取延长路径 $p\mathbin{\|}(v,w)$ 作为 witness。Owner/frontier promotion 不改变 absolute time，也不影响这个 timing witness。

因为默认 profile 不在 empty timestamp 自主发射 message，所有 dispatched messages 都可由上述归纳得到 witness。又因为 $t\leq L-1$ 且 $|p|\leq D$：

$$
\tau=Rt+|p|
\leq
R(L-1)+D.
$$

<div class="qed" aria-label="证毕">∎</div>

### 引理 4.6：有限事件性

假设每次 node invocation 只沿有限 outgoing edge 集合发出有限条 messages。对任意有限输入 chunk，一次 execution 产生的 message 集合有限。

**证明。**

有限 DAG 中有向路径数量有限。每条 message 只能沿 edge 方向前进，不能返回已经经过的 node。初始 injection 数有限，每次 invocation 的 fan-out 有限，所以对有限路径树做有限次展开后，总 message 数有限。

<div class="qed" aria-label="证毕">∎</div>

有限不等于高效。一般 DAG 的路径数量可以随 $|V|$ 指数增长，因此后文仍需单独加入 sparse event budget。

## 5. Node-Owned State 与三种同刻/融合语义

### 定义 5.1：Node-owned persistent context

每个 node $v$ 有 state space：

$$
\mathcal S_v,
$$

以及初始 state：

$$
S_v^0\in\mathcal S_v.
$$

其具体实现可以是：

- KV cache。
- Mamba/SSM recurrent state。
- Linear-attention accumulator。
- 显式 node memory。
- 其他具有 chunk correctness contract 的 state。

Strict profile 要求每个 mutable state location 有唯一 owner node。若多个 nodes 必须联合修改同一 state，应把它们封装为一个具有独立 event-stream contract 的 supernode/subgraph operator。

Persistent state 属于 node，不属于某个 token。为进行 causal audit，把实际数值 state 与其 frontier 写成 augmented state：

$$
\widetilde S_v=(S_v,c_v^S),
\qquad
c_v^S\in\mathbb F_L.
$$

定义 augmented state space：

$$
\widetilde{\mathcal S}_v
=
\mathcal S_v\times\mathbb F_L.
$$

初始 state 不依赖输入，声明：

$$
c_v^{S,0}=-1.
$$

因此 augmented initial state 为：

$$
\widetilde S_v^0=(S_v^0,-1).
$$

对任意 $\widetilde S=(S,c^S)\in\widetilde{\mathcal S}_v$，定义投影：

$$
\operatorname{num}(\widetilde S)=S,
\qquad
\operatorname{frontier}(\widetilde S)=c^S.
$$

从本定义之后，所有 reference transition 的 state 参数和值域都使用 augmented state space $\widetilde{\mathcal S}_v$；数值 kernel 只需读取 $\operatorname{num}(\widetilde S)$，但 runtime 必须同时传播并 commit frontier 投影。前两种 profile 可以只把该 label 用于审计，frontier-fusion profile 则会用它决定新的 outgoing owner。

对任意 node transition，若它读取 $n\in\mathbb N_{>0}$ 个 semantic objects，其 frontiers 为：

$$
c_1,\ldots,c_n,
$$

则 output hidden 与 post-state 默认声明：

$$
c_{\mathrm{out}}
=
\max_{1\leq i\leq n}c_i.
$$

Kernel 若通过 causal mask、versioned state 或独立证明得到更紧的 dependency bound，可以声明更小的有效 frontier；但 owner-labelled route/message record 还必须把该 trajectory owner 计入保守 provenance bound，因此不得把 frontier 降到 owner 以下。Owner-ordered/atomic-joint profile 保留 trajectory owner，即使 $c_{\mathrm{out}}>\operatorname{owner}$；这个不等式正是 owner-prefix contamination 的显式检测信号。

因此：

```text
message / hidden / route record -> owner-labelled + frontier-labelled
persistent context             -> node-owned + frontier-labelled
```

### 定义 5.2：同刻 Owner tuple

对非空 owner 集合：

$$
O_{v,\tau}^{\uparrow}=(t_1,\ldots,t_m),
$$

定义 node $v$ 在 time $\tau$ 的 owner-indexed input tuple：

$$
B_{v,\tau}
=
\bigl(
(t_1,x_{v,\tau,t_1}),
\ldots,
(t_m,x_{v,\tau,t_m})
\bigr).
$$

该 tuple 的顺序由 token index 唯一决定，不依赖 runtime scheduling。

同时定义不按 owner 分开的完整同刻 inbox：

$$
I_{v,\tau}
=
\biguplus_{t\in\mathcal O_{v,\tau}}
I_{v,\tau,t},
$$

其中 $\biguplus$ 表示保留重复 messages 的 multiset union。Frontier-fusion profile 直接对 $I_{v,\tau}$ 做一次联合计算。

默认 strict profile 中，没有 inbox event 的 node state 保持不变。若模型需要在空 timestamp 执行 decay，应另行定义：

$$
\operatorname{Idle}_v:
\mathbb N\times\widetilde{\mathcal S}_v
\to
\widetilde{\mathcal S}_v,
$$

并把所有 empty-time updates 纳入第 7 节定义的 node reference 与 chunk artifacts。本文后续公式取 $\operatorname{Idle}_v(\tau,S)=S$；非平凡 idle/decay 是相同证明框架下的扩展，不是免费省略项。

#### 定义 5.2a：Node 的 Absolute-Time Event Order

对同一 node 的两个 owner-event order keys：

$$
k=(\tau,t),
\qquad
k'=(\tau',t'),
$$

定义：

$$
k\prec_v k'
$$

当且仅当：

$$
\tau<\tau',
$$

或：

$$
\tau=\tau'
\quad\text{且}\quad
t<t'.
$$

因此 node state 首先按 absolute time 演进；只有 absolute time 相同，才使用 owner token 打破并列。

#### 例 5.2b：跨时间的 Owner Inversion

取固定周期 $R=2$。考虑 owner A 的 token index 为 $0$，沿长度 $4$ 的路径到达 $v$；owner B 的 token index 为 $1$，沿长度 $1$ 的路径到达 $v$。二者 arrival rounds 为：

$$
\tau_A=R\cdot 0+4=4,
\qquad
\tau_B=R\cdot 1+1=3.
$$

虽然 $t_A<t_B$，但在 absolute-time event order 中：

$$
(\tau_B,t_B)\prec_v(\tau_A,t_A).
$$

所以 B 的短路径 event 会先更新 node state，A 的晚到 event 可能读取 B 的影响。后文的 owner-ordered profile 只规定同一 $\tau$ 内的顺序，不消除这种跨时间 owner inversion。

### 5.3 Profile O：Owner-Ordered Within-Timestamp Fold

#### 定义 5.3：单 Owner event transition

给定 numerical hidden space $H_v$。定义 route-visible labelled hidden space：

$$
\mathcal Z_v
=
\{\bot\}
\uplus
(H_v\times\mathbb F_L),
$$

其中 $\uplus$ 表示 disjoint union。若 $z=(h,c)\in H_v\times\mathbb F_L$，定义：

$$
\operatorname{payload}(z)=h,
\qquad
\operatorname{frontier}(z)=c.
$$

一个 owner-labelled output record 是 pair $r=(t,z)\in[L]\times\mathcal Z_v$。定义 $\operatorname{owner}(r)=t$；当 $z\neq\bot$ 时，定义 $\operatorname{frontier}(r)=\operatorname{frontier}(z)$，并要求：

$$
\operatorname{owner}(r)
\leq
\operatorname{frontier}(r).
$$

$\bot$ 表示该 event 已执行，但不产生 route-visible hidden。Node $v$ 的单 event transition 是确定函数：

$$
\mathcal T_v:
\mathbb N\times\mathbb N\times X_v\times\widetilde{\mathcal S}_v
\to
\mathcal Z_v\times\widetilde{\mathcal S}_v.
$$

输入的两个自然数依次是 owner token $t$ 与 absolute time $\tau$。返回的 labelled hidden 与 post-state 必须满足定义 5.1 的 frontier 传播规则。

#### 定义 5.4：Owner-ordered 同刻 transition

给定：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad t_1<\cdots<t_m,
$$

以及进入该 timestamp 前的 augmented state $\widetilde S^{(0)}\in\widetilde{\mathcal S}_v$。递归定义：

$$
(z_i,\widetilde S^{(i)})
=
\mathcal T_v(t_i,\tau,x_i,\widetilde S^{(i-1)}),
\qquad i=1,\ldots,m.
\tag{GD-7}
$$
^eq-owner-ordered-group

该 timestamp 的 owner outputs 与提交后 state 分别为：

$$
Z_{v,\tau}^{\mathrm{ord}}
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr),
$$

其中每个非 $\bot$ 的 $z_i$ 都显式包含 causal frontier，不再省略该字段。

$$
\widetilde S^+
=
\widetilde S^{(m)}.
$$

若 A、B 同刻到达且 $t_A<t_B$，则 B 的 transition 读取 A 已经更新后的 state。因果方向是：

$$
A\longrightarrow B.
$$

Owner-ordered 是同一 timestamp 内的 reference semantics；完整 node event stream 仍按定义 5.2a 的 $(\tau,t)$ lexicographic order 演进。它不要求物理实现真的逐 owner 循环。若能证明一个 causal mask、scan 或其他 bulk kernel 等于式 [[#^eq-owner-ordered-group|GD-7]]，则可以联合执行。

### 5.4 Profile J：Atomic Joint Timestamp Transition

#### 定义 5.5：Joint transition 与 collective delta

定义 $\mathcal B_v$ 为所有有限 owner-indexed input tuples 的集合。其任意元素具有形式：

$$
B
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad
t_1<\cdots<t_m.
$$

其中 $m\in\mathbb N_{>0}$、$t_i\in[L]$ 且 $x_i\in X_v$。

定义 $\mathcal Z_v^\star$ 为所有具有相同 owner-key 形式的有限 labelled-hidden tuples 的集合：

$$
Z
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr).
$$

其中 $z_i\in\mathcal Z_v$。

调用 $\mathcal J_v$ 时，output tuple 必须与 input tuple 使用完全相同的 owner-key sequence；若某个 owner 不产生 hidden，则相应位置写为 $\bot$。

对 node $v$，给定 delta space $\Delta_v$、commit function：

$$
\operatorname{Commit}_v:
\widetilde{\mathcal S}_v\times\Delta_v
\to\widetilde{\mathcal S}_v,
$$

并要求 $\operatorname{Commit}_v$ 是确定函数，且其返回 state 的 frontier 投影满足定义 5.1 的有效 causal-frontier 规则；$\Delta_v$ 可以携带 numerical delta 与计算该 label 所需的审计信息。

以及 atomic joint transition：

$$
\mathcal J_v:
\mathbb N\times\mathcal B_v\times\widetilde{\mathcal S}_v
\to
\mathcal Z_v^\star\times\Delta_v.
$$

对任意 timestamp $\tau$、owner tuple $B_{v,\tau}$ 与进入该 timestamp 前的 augmented state $\widetilde S$，定义：

$$
\mathcal J_v(\tau,B_{v,\tau},\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{joint}},
\Delta_{v,\tau}
\right),
\tag{GD-8}
$$
^eq-atomic-joint-transition

其中：

$$
Z_{v,\tau}^{\mathrm{joint}}
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr)
$$

仍为 owner-indexed outputs；每个非 $\bot$ 的 $z_i$ 显式包含经过证明或按默认 max 规则得到的 causal frontier。State 只在 joint computation 结束后提交一次：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau}).
\tag{GD-9}
$$
^eq-atomic-joint-commit

定义 joint transition 与 commit 的组合：

$$
\operatorname{Atomic}_v(\tau,B_{v,\tau},\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{joint}},
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau})
\right).
\tag{GD-9a}
$$
^eq-atomic-joint-composed

$\Delta_{v,\tau}$ 属于 node 的 collective state update，不要求归属于某个单独 token。为了 replay 与 attribution，可以额外保留 per-owner delta decomposition，但它不是数学正确性的必要字段。

Atomic-joint 允许：

- 所有 owners 读取同一个 pre-state。
- Joint kernel 比较多个 owners 的 inputs。
- 每个 owner 的 output 依赖同刻其他 owners。
- Joint kernel 使用 owner index 构造 triangular mask。

它不允许把多个 owners 变成一个永久无 owner 的 travelling signal。Outgoing records 仍必须按 owner 分开。

#### 定义 5.6：同刻 Owner-causal Joint Operator

对 $t\in\mathcal O_{v,\tau}$，定义 owner prefix：

若：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
$$

并且 $t=t_j$，则：

$$
B_{v,\tau}^{\leq t}
=
\bigl((t_1,x_1),\ldots,(t_j,x_j)\bigr).
$$

若 owner $t$ 的 hidden 与 route decision 只依赖：

$$
(\widetilde S,\tau,B_{v,\tau}^{\leq t}),
$$

而不依赖 owner 大于 $t$ 的 inputs，则称 joint operator 在该 timestamp 内是 owner-causal 的。

这是比 arbitrary joint 更强的约束。Arbitrary joint 只保证 absolute-time semantics；它不自动保证 token-owner 意义下的 prefix causality。

### 定义 5.7：Joint Operator 与 Ordered Fold 等价

把定义 5.4 的递归结果记为：

$$
\operatorname{GroupFold}_{\mathcal T_v}(\tau,B,\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{ord}},
\widetilde S^{(m)}
\right).
\tag{GD-9b}
$$
^eq-owner-group-fold

若对任意 $\tau$、任意 owner tuple $B\in\mathcal B_v$ 和任意 augmented state $\widetilde S\in\widetilde{\mathcal S}_v$：

$$
\operatorname{Atomic}_v(\tau,B,\widetilde S)
=
\operatorname{GroupFold}_{\mathcal T_v}(\tau,B,\widetilde S),
\tag{GD-10}
$$
^eq-joint-ordered-equivalence

则称 atomic-joint operator 与 owner-ordered group fold 等价。这里要求相等的是：

- 每个 owner 的 hidden。
- 每个 owner 的 route-visible record。
- Timestamp 结束后的 state。

只比较 collective delta 或 final state 不足以建立等价。

### 命题 5.8：Fold-Equivalent Joint Execution 不改变语义

若式 [[#^eq-joint-ordered-equivalence|GD-10]] 对 node $v$ 成立，则在该 node 上用 $\mathcal J_v$ 一次执行整个 timestamp group，与按 owner token 顺序执行 $\mathcal T_v$ 得到相同 observable artifacts。

**证明。**

这是式 [[#^eq-joint-ordered-equivalence|GD-10]] 的直接展开：定义已经要求 owner outputs、route-visible records 与 final state 全部相等。

<div class="qed" aria-label="证毕">∎</div>

### 例 5.9：Final State 相同但语义不同

本例只写 numerical payload，并假设两种实现使用相同的合法 frontier labels；因此省略式中的 augmented-state 与 labelled-hidden 外壳。

令：

$$
S\in\mathbb R,
$$

单 event transition 为：

$$
\mathcal T(x,S)=(S+x,S+x).
$$

取：

$$
S=0,\qquad x_A=1,\qquad x_B=2.
$$

Owner-ordered fold 得到：

$$
h_A=1,\qquad h_B=3,\qquad S^+=3.
$$

若 snapshot-joint 分别从旧 state 计算，再把 delta 相加，则可能得到：

$$
h_A=1,\qquad h_B=2,\qquad S^+=3.
$$

两者 final state 都是 $3$，但 B 的 hidden 不同，所以后续 routing 与 output 也可能不同。

### 5.10 Profile F：Frontier-Owned Atomic Fusion

#### 定义 5.10：Fusion Frontier

给定 node $v$ 在 time $\tau$ 的非空完整 inbox $I_{v,\tau}$ 与 augmented pre-state $\widetilde S$，记：

$$
c_v^{S,-}
=
\operatorname{frontier}(\widetilde S).
$$

定义本次 fusion 的 causal frontier：

$$
c_{v,\tau}^{\star}
=
\max
\left(
\{c_v^{S,-}\}
\cup
\{\operatorname{frontier}(m)\mid m\in I_{v,\tau}\}
\right).
\tag{GD-F1}
$$
^eq-frontier-fusion-max

这个定义必须读取 pre-state frontier。若当前 inputs 只有 A、B，但 pre-state 已经受 C 影响且 $C>B$，则：

$$
c_{v,\tau}^{\star}=C,
$$

不能把新 output 错误标记为 B。

#### 定义 5.11：Atomic Fusion Transition

Frontier-fusion kernel 是确定函数：

$$
\mathcal F_v:
\mathbb N
\times
\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\times
\widetilde{\mathcal S}_v
\to
(H_v\cup\{\bot\})
\times
\Delta_v.
$$

它对完整同刻 inbox 与 augmented pre-state 做一次联合计算：

$$
\mathcal F_v(\tau,I_{v,\tau},\widetilde S)
=
(h^\star,\Delta^\star).
\tag{GD-F2}
$$
^eq-frontier-fusion-transition

Augmented state 仍通过 $\operatorname{Commit}_v$ 一次提交：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta^\star),
$$

并要求其 frontier 投影满足：

$$
\operatorname{frontier}(\widetilde S^+)
=
c_{v,\tau}^{\star}.
$$

若 $h^\star\neq\bot$，该 timestamp 只产生一个 unified owner record：

$$
Z_{v,\tau}^{\mathrm{front}}
=
\bigl((c_{v,\tau}^{\star},z^\star)\bigr),
\tag{GD-F3}
$$
^eq-frontier-owned-output

其中：

$$
z^\star
=
(h^\star,c_{v,\tau}^{\star})
\in
\mathcal Z_v,
$$

且该 owner-labelled record 满足：

$$
\operatorname{owner}(c_{v,\tau}^{\star},z^\star)
=
\operatorname{frontier}(z^\star)
=
c_{v,\tau}^{\star}.
$$

所有 outgoing messages 都继承这个 owner/frontier。原始 A/B trajectory lineage 可以保存在 metadata 中，但不再各自产生 travelling output。该操作因此是一个明确的 semantic quotient，而不是对 owner-ordered 或 atomic-joint profile 的免费重排。

#### 例 5.11a：A/B Unified Emission 与 Pre-State Contamination

令 A、B 的 token indices 分别为：

$$
A=0,
\qquad
B=1.
$$

若同刻 inbox 只含 A/B，且 pre-state frontier 不超过 B，则：

$$
c^\star
=
\max(c_v^{S,-},0,1)
=
1,
$$

所以联合计算可以只发射一个 owner/frontier 都为 B 的 output。

若 pre-state 已经受 token C 影响，且：

$$
C=2>B,
\qquad
c_v^{S,-}=2,
$$

则：

$$
c^\star
=
\max(2,0,1)
=
2.
$$

此时数值计算即使当前只混合 A/B，也不能把 output 标记为 B；必须标记为 C，或改用不含 C 的 versioned/masked state。

#### 定义 5.11b：Frontier-Fusion Routing Primitive

定义 node $v$ 的 outgoing edge set：

$$
\operatorname{Out}(v)
=
\{(v,u)\in E\}.
$$

Frontier-fusion routing primitive 是确定函数：

$$
\operatorname{Route}_v^{\mathrm{front}}:
\mathbb N\times([L]\times\mathcal Z_v)
\to
2^{\operatorname{Out}(v)}.
$$

它只能读取 absolute time、unified owner-labelled output 与 static parameters；对 $z=\bot$ 返回空集。沿任一 selected edge 生成的 message 必须保留该 output 的 owner/frontier，且 message id、metadata 与 payload construction 都必须是确定函数。第 6 节将在此 primitive 上增加 candidate score，并定义另外两种 profile 的 selector。

#### 引理 5.12：Prefix-Causal Composition

给定 $n\in\mathbb N_{>0}$。设 semantic objects：

$$
q_1,\ldots,q_n
$$

分别具有有效 frontiers：

$$
c_1,\ldots,c_n.
$$

若 $f$ 是不读取其他 input-token 数据的确定函数，令：

$$
q=f(q_1,\ldots,q_n)
$$

并定义：

$$
c^\star
=
\max_{1\leq i\leq n}c_i,
$$

则 $q$ 是 $c^\star$-prefix-causal 的。

**证明。**

取任意两个在 prefix $0{:}c^\star$ 上相同的输入序列。因为每个 $c_i\leq c^\star$，两次 execution 中所有 $q_i$ 都相同。$f$ 是确定函数且不读取其他 token 数据，所以两次得到的 $q$ 相同。

<div class="qed" aria-label="证毕">∎</div>

#### 定理 5.13：Frontier-Fusion Token-Prefix Invariant

假设：

1. Initial state frontier 为 $-1$。
2. 定义 2.1c 的 input event $e_t^{\mathrm{in}}$ 的 owner support 为 $\{t\}$，frontier 为 $t$。
3. 每个 numerical kernel 只读取其显式 inbox、pre-state、static parameters 与 logical metadata；routing 使用定义 5.11b 的纯函数。
4. 每次 fusion 按式 [[#^eq-frontier-fusion-max|GD-F1]] 更新 state frontier，并按式 [[#^eq-frontier-owned-output|GD-F3]] 标记 unified output。

则任意 frontier-fusion state 或 message 若声明 frontier/owner 为 $c$，其数值内容只依赖：

$$
x_0,\ldots,x_c.
$$

特别地，不会出现一个 owner 为 A 的 late signal 读取 B 后仍继续标记为 A；它至少被提升到当前 causal frontier。

**证明。**

沿 absolute-time streaming execution 归纳。Initial states 与 tokens 无关，所以 frontier $-1$ 有效；input $x_t$ 的 frontier $t$ 有效。

假设某次 fusion 的 pre-state 与全部 inbox messages 都具有有效 frontiers。式 [[#^eq-frontier-fusion-max|GD-F1]] 取这些 frontiers 的最大值 $c^\star$。由引理 5.12，$\mathcal F_v$ 产生的 $h^\star$、$\Delta^\star$ 与 commit 后的 numerical state 都是 $c^\star$-prefix-causal 的。式 [[#^eq-frontier-owned-output|GD-F3]] 又把 output owner/frontier 与 $c^\star$ 对齐，所以 invariant 被保持。

定义 5.11b 的 routing primitive 是这些 prefix-causal outputs、absolute time 与 static parameters 的确定函数，所以 selected-route existence 也保持同一个 frontier bound。Unit-delay spatial dispatch 只复制已经有效的 owner/frontier label，不读取新的 token 数据。对所有 absolute times 与其中的 node events 重复上述论证，结论成立。

<div class="qed" aria-label="证毕">∎</div>

#### 推论 5.13a：Dependency-Frontier Monotonicity

对 frontier-fusion logical event $e$，使用定义 2.1a 的 event-level frontier。Input event 取 token index；node fusion event 取式 GD-F1 的 $c_{v,\tau}^{\star}$；readout/sample event 取对应 fixed-period prefix index。

在定理 5.13 的前提下，对 frontier-fusion execution 的任意 logical dependency edge：

$$
e\longrightarrow e',
$$

都有：

$$
\operatorname{frontier}(e)
\leq
\operatorname{frontier}(e').
$$

因此有限 logical event DAG 可以先按 frontier 递增分组，再在同一 frontier 内取 topological order；不存在从较大 frontier 指向较小 frontier 的 dependency edge。

**证明。**

Spatial dispatch 保持 owner/frontier 不变，所以 spatial dependency edge 上 frontier 相等。Local state/fusion dependency 的 output frontier 由式 [[#^eq-frontier-fusion-max|GD-F1]] 取所有 inputs 与 pre-state frontiers 的最大值，所以不小于任一 predecessor frontier。

对 boundary dependencies，第 $t$ 个 readout/sample event 的 frontier 都是 $t$；由式 GD-2.4，任何在 $\theta_t^{\mathrm{out}}$ 前可见的 state predecessor frontier 都不超过 $t$。Autoregressive sample 到下一 input 的 edge 从 frontier $t$ 指向 $t+1$。Input event 没有更早 token-data predecessor。

因此每条 dependency edge 上 frontier 单调不减。把有限 event nodes 按 frontier 分组后，跨组 edges 只会从较小组指向较大组；每个同-frontier induced subgraph 仍是 DAG，所以可在组内取 topological order。

<div class="qed" aria-label="证毕">∎</div>

这个推论使 frontier-fusion 更容易嵌入 [[step-transition-mathematical-specification#定义 3.6a：logical event DAG program|token-prefix logical event DAG]]：frontier 是 causal dependency 的 token upper bound。但它仍不推出每个 frontier/token 恰好产生一个 output readout。

#### 命题 5.14：Frontier Promotion 不自动带来高性能 Prefill

式 [[#^eq-frontier-fusion-max|GD-F1]] 中的 $\max$ 是 associative reduction，可以低成本批量计算。但 numerical state 若按 timestamp groups $G_0,\ldots,G_{q-1}$ 满足：

$$
S_{j+1}=\Phi_{G_j}(S_j),
$$

则 arbitrary $\Phi_{G_j}$ 仍形成：

$$
S_0\to S_1\to\cdots\to S_q
$$

的顺序依赖链。要获得 Transformer/Mamba 意义上的高性能 chunk prefill，还需要至少一种额外结构：

- $\Phi_{G_j}$ 有 compact representation，并在函数 composition 下闭合，可用 parallel/blocked scan。
- 全部 outputs 可由 causal mask、segmented attention 或其他 causal-bulk kernel 联合计算。
- Node transition 是 token-local/group-local，不读取前序 mutable state。

例如 affine recurrence：

$$
S_{j+1}=A_jS_j+b_j
$$

可以通过 associative pair composition 做 scan；Mamba/SSM 属于这一方向。Causal attention 则通过 masked bulk kernel 获得 prefill。Frontier ownership 解决的是 causal labelling，不替代这些 numerical contraction。

### 5.15 三种 Profile 的边界

| Profile | 同刻计算 | Outgoing owner | Owner/frontier 关系 | 高性能前提 |
| --- | --- | --- | --- | --- |
| Owner-ordered | A commit 后 B 读取 | 保留 trajectory owner | 跨时间 inversion 可使 frontier 大于 owner；label 必须显式记录 | Causal-bulk/scan |
| Atomic-joint | A/B 与 pre-state 一次联合计算，保留 per-owner outputs | 保留各 trajectory owners | Arbitrary joint 连同刻 owner-prefix 也不保证；需分别登记 frontier | Joint chunk contract |
| Frontier-fusion | A/B 与 pre-state 一次联合计算，只发射 unified output | 提升为全部依赖的最大 frontier | Owner 与 frontier 对齐，并由定理 5.13 给出 prefix 上界 | 仍需 scan、causal-bulk 或 state-free group kernel |

## 6. 一般 DAG 上的 Routing

### 定义 6.1：Local candidate score

对 node $v$ 在 time $\tau$ 产生的非空 labelled output：

$$
(t,z),
\qquad
z=(h,c)\in H_v\times\mathbb F_L,
$$

以及每条 outgoing edge $(v,u)\in E$，定义：

$$
s_{v,\tau,t\to u}
=
g_{v\to u}(h)
+b_{v\to u}
+d_{v\to u}(t,\tau).
\tag{GD-11}
$$
^eq-general-routing-score

其中：

- $g_{v\to u}:H_v\to\mathbb R$ 是 learned content score。
- $b_{v\to u}\in\mathbb R$ 是静态 learned/configured bias。
- $d_{v\to u}:[L]\times\mathbb N\to\mathbb R$ 是只读取 owner、absolute time 与 edge/node 静态配置的 deterministic prior。

三项都不读取此前 tokens 的实际 hard-route counts。

### 定义 6.2：Pure Label-Preserving Selector

Owner-ordered profile 给定确定函数：

$$
\rho_v^{\mathrm{ord}}:
\mathbb N\times[L]\times\mathcal Z_v
\to
2^{\operatorname{Out}(v)},
$$

其中 $2^{\operatorname{Out}(v)}$ 表示 $\operatorname{Out}(v)$ 的 power set。

并定义：

$$
A_{v,\tau,t}
=
\rho_v^{\mathrm{ord}}(\tau,t,z)
\subseteq
\operatorname{Out}(v).
$$

要求 $\rho_v^{\mathrm{ord}}(\tau,t,\bot)=\varnothing$。

Owner-ordered profile 中，$A_{v,\tau,t}$ 只能读取该 owner 的 $z$ 与静态配置。需要由 node state 影响 routing 的信息，必须先由 $\mathcal T_v$ 显式写入 $z$ 的 payload；selector 不再隐式选择读取 commit 前还是 commit 后的 state view。

令 $\mathcal A_v^\star$ 为所有有限 owner-indexed selected-edge-set tuples：

$$
\bigl((t_1,A_1),\ldots,(t_m,A_m)\bigr),
\qquad
m\in\mathbb N_{>0},
\qquad
t_i\in[L],
\qquad
t_1<\cdots<t_m,
\qquad
A_i\subseteq\operatorname{Out}(v).
$$

Atomic-joint profile 给定确定函数：

$$
\rho_v^{\mathrm{joint}}:
\mathbb N\times\mathcal Z_v^\star
\to
\mathcal A_v^\star.
$$

它读取 $\tau$ 与整个 $Z_{v,\tau}^{\mathrm{joint}}$，并返回具有完全相同 owner-key sequence 的 selected-edge-set tuple：

$$
\bigl((t,A_{v,\tau,t})\bigr)_{t\in O_{v,\tau}^{\uparrow}}
=
\rho_v^{\mathrm{joint}}
\left(
\tau,Z_{v,\tau}^{\mathrm{joint}}
\right).
$$

因此 joint selector 可以比较同刻多个 owner-labelled hiddens，但 joint transition 的 pre-state/post-state visibility 已经在 $Z_{v,\tau}^{\mathrm{joint}}$ 的定义中固定，不由 selector 临时决定。

Frontier-fusion profile 只有一个 unified record：

$$
(t,z)
=
\left(
c_{v,\tau}^{\star},
z^\star
\right),
$$

Frontier-fusion profile 使用定义 5.11b 的 routing primitive，并只对该 unified record 选择：

$$
A_{v,\tau,t}
=
\operatorname{Route}_v^{\mathrm{front}}(\tau,(t,z)).
$$

无论使用哪种 profile，selector 都必须：

- 确定性处理 tie-breaking。
- 只选择 $v$ 的 outgoing edges。
- 对每个 outgoing message 保留 node output 已声明的 owner/frontier labels；owner promotion 只能发生在定义 5.11 的 fusion transition 内。
- 不根据 route result 追溯修改已经提交的同刻 node state，除非这种修改已写入 node transition contract。

若 selector 具有 mutable state，该 state 必须有唯一 owner node，并纳入 $\widetilde{\mathcal S}_v$ 以及第 7 节定义的 node reference/chunk contract。这足以定义 correctness，但不自动提供高性能。Strict high-performance profile 进一步要求：`affectcount/selectcount` 一类跨 event feedback 要么删除，要么给出独立的 scan/bulk contraction 证明。

### 定义 6.3：Selected payload dispatch

若 labelled output 为 $(t,z)$、$z=(h,c)$，且 $(v,u)\in A_{v,\tau,t}$，给定 payload subtype $\mathcal P_{v\to u}\subseteq\mathcal P$ 与 projection $P_{v\to u}:H_v\to\mathcal P_{v\to u}$，定义：

$$
p'
=
P_{v\to u}(h),
$$

并发出满足式 [[#^eq-unit-delay-dispatch|GD-3]] 的 message：

$$
m'
=
(\iota',t,c,(\tau+1,i_{\mathrm{arrive}}),v,u,\mu',p').
$$

其中 $\iota'\in\mathsf{MID}$ 与 $\mu'\in\mathcal U$ 必须由 source event id、selected edge、owner/frontier、birth slot 与 lineage 等已声明字段确定性生成，不能依赖物理线程竞争顺序。

不同 owners 可以选择同一 edge。它们仍是两条 owner-distinct messages。

### 备注 6.4：A 影响后续 Routing 的三条语义路径

Owner-ordered profile 中，A 可以先更新 node-owned state，B 再读取该 state：

$$
x_A
\to
S_A
\to
h_B
\to
A_{v,\tau,B}.
$$

Atomic-joint profile 中，A 的当前 input 可以通过 joint operator 直接影响 B 的 hidden 或 route：

$$
(x_A,x_B,S)
\to
\mathcal J_v
\to
h_B
\to
A_{v,\tau,B}.
$$

前两条路径语义不同，实验时不能只看 final state 后把它们视为同一个模型。

Frontier-fusion profile 不再保留 A/B 两条 outgoing trajectories，而是：

$$
(I_A,I_B,S)
\to
\mathcal F_v
\to
(h^\star,c^\star)
\to
A_{v,\tau,c^\star}.
$$

若 $c^\star=B$，则 unified emission 归属 B；若 pre-state 已受 C 影响且 $C>B$，则 emission 必须归属 C。

## 7. Typed Logical Events、Node Stream 与 Chunk Contract

### 定义 7.1：Profile-Specific Logical Events

取 profile：

$$
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\}.
$$

定义 event kind 集合：

$$
\mathcal K^P
=
\mathcal K_{\mathrm{bdry}}
\cup
\{\mathtt{node}_P\}.
$$

Profile-$P$ event 是定义 2.1a 的 logical event instance，并取 $\mathcal K=\mathcal K^P$。为便于阅读，后文把它的 header 继续写成：

$$
h_e
=
(\eta,\kappa,\ell,\theta,\Omega,c),
\tag{GD-E1}
$$
^eq-logical-event-instance

该 header 是 [[step-transition-mathematical-specification#定义 3.6a：logical event DAG program|定义 3.6a]] 的固定周期 Tide 实例化：$\theta$ 对应 abstract logical timestamp，$\Omega$ 对应 support，$c$ 对应 frontier。每个 event 的 value $\nu(e)$ 与 header 一起满足定义 2.1a 和式 GD-2.4。Event-level frontier $c$ 是整个 event value 的有效保守上界；value 内的单个 hidden、state 或 message artifact 可以登记不大于 $c$ 的更紧 frontier。

Actual event set 只登记真正发生的 events。Selector 不选择某条 edge 时，相应 node event 的 route set 中没有该 edge，也不会产生该 outgoing message；不会为“未发生的下游 event”伪造一个 value 为 $\bot$ 的 event。另一方面，已经发生的 node event 可以包含 $\bot$ hidden 分量，表示该 transition 已执行但没有产生 route-visible hidden。

本文使用以下 event instances：

1. 对每个 $t\in[L]$，使用定义 2.1c 的 input event header $h_{e_t^{\mathrm{in}}}$。

2. 对非空 regular inbox group：owner-ordered profile 为每个 $(v,\tau,t)$ 建立一个 event，其 commit timestamp 为 $(\tau,i_{\mathrm{commit}})$、owner support 为 $\{t\}$；joint/frontier profile 为每个 $(v,\tau)$ 建立一个 event，owner support 为 $\mathcal O_{v,\tau}$。其 event-level frontier 必须是该 event value 的有效上界；frontier-fusion profile 取式 GD-F1 的 $c_{v,\tau}^{\star}$。

3. 对每个 $t\in[L]$，使用定义 2.1c 的 fixed readout event header $h_{e_t^{\mathrm{out}}}$。

Readout event 对每个 $t$ 必定存在，不能被 selector 取消、推迟或改写 timestamp。

4. Autoregressive execution 额外包含定义 2.1c 的 sample event header $h_{e_t^{\mathrm{sample}}}$。

Teacher-forced chunk theorem 不需要 sample event；它把 $x_{0:L}$ 作为 boundary data。

Event value spaces 必须按 kind 显式登记：input event value 包含 boundary injection record $b_t^{\mathrm{in}}$；input/node event value 还至少包含 labelled hidden、committed state version、route records 与 dispatched messages；$\nu(e_t^{\mathrm{out}})=y_t\in Y$；$\nu(e_t^{\mathrm{sample}})=\operatorname{SelectToken}(y_t)\in X$。实现不能把这些 reference-visible artifacts 隐藏为未比较的副作用。

### 定义 7.2：Direct Dependency 与 Dependency Completeness

给定一次已经实例化的有限 reference execution，其 event set 记为：

$$
\mathcal E_L^P.
$$

定义 direct dependency relation：

$$
\mathcal A_L^P
\subseteq
\mathcal E_L^P\times\mathcal E_L^P,
$$

为包含下列 edges 的最小关系：

1. **Message edge**：若 event $e$ dispatch 的 message 被 event $e'$ 的 inbox 消费，则 $(e,e')\in\mathcal A_L^P$。Input event 产生的第一跳 message 也使用该规则。
2. **State edge**：若同一 node 的 event $e'$ 读取 event $e$ commit 后的 state version，且中间没有其他覆盖该 version 的 commit，则 $(e,e')\in\mathcal A_L^P$。
3. **Readout edge**：若 $e$ 是 output node $z$ 在 $\theta_t^{\mathrm{out}}$ 之前的最后一个 state-commit event，则 $(e,e_t^{\mathrm{out}})\in\mathcal A_L^P$；若不存在这样的 event，readout 使用 boundary initial state。
4. **Autoregressive boundary edge**：在 pure inference 中，$(e_t^{\mathrm{out}},e_t^{\mathrm{sample}})\in\mathcal A_L^P$，并且当 $t+1\in[L]$ 时，$(e_t^{\mathrm{sample}},e_{t+1}^{\mathrm{in}})\in\mathcal A_L^P$。

若 selector 被细化为独立 event，则 selector value 到 route/message-producing event 的 control edge 也必须加入 $\mathcal A_L^P$。本文默认 selector 是相应 node event 的内部 primitive；selected-route set 与每条 optional outgoing message 都属于该 node event value，不能依赖未声明的全局状态。某个下游 regular event 是否实例化，由其 inbox 是否非空决定；该 inbox 中每条 message 都必须通过 message edge 追溯到 source event。

定义 event graph：

$$
D_L^P
=
(\mathcal E_L^P,\mathcal A_L^P).
$$

称 $D_L^P$ dependency-complete，当且仅当任何被 actual execution 读取、且可能改变 event header、event value、state version、route、message 或 readout 的 reference dependency，都由 $\mathcal A_L^P$ 中的一条 edge、显式 boundary-data argument，或 event-local primitive 内部已声明的顺序表示。未选择的 route/message 以 source event value 中的空集合或缺失 optional record 表示，不额外建立 value 为 $\bot$ 的 event node。

对 $e\in\mathcal E_L^P$，定义：

$$
\operatorname{Pred}(e)
=
\{e'\in\mathcal E_L^P\mid(e',e)\in\mathcal A_L^P\}.
$$

对每个 event $e$，给定显式声明的 boundary-data space $\mathcal B_e$。它只能包含该 event 允许读取的 input-token prefix、其 location 的初始 state 投影、static parameters 与 logical metadata。给定确定性 event function：

$$
F_e:
\{h_e\}
\times
\left(
\prod_{e'\in\operatorname{Pred}(e)}\mathcal V_{e'}
\right)
\times\mathcal B_e
\to
\mathcal V_e,
$$

并要求 $F_e$ 只读取式 GD-E1 的 header $h_e$、direct predecessors 与已声明 boundary data。Header 不是额外的 token-data channel：其中任何会随 execution 改变的 support/frontier/id 字段，都必须由 direct predecessor records 与 static canonicalization rule 唯一导出；不能把未声明的 numerical information 编码进 event id 或 metadata。较粗 event 若 lower 为多个 physical operations，必须先细化为 dependency-complete logical sub-DAG，或给出 fused primitive 的语义保持证明。

对本文 strict Tide profile，只有 $e_t^{\mathrm{in}}$ 可以从 $X^L$ 直接读取 $x_t$。Regular node events 只能通过 incoming messages、local state predecessor、static parameters 与 logical metadata 获得 token-dependent information；readout event 只能读取式 GD-E3 指定的 output-node state snapshot；sample event 只能读取对应 readout value 与静态 selection parameters。

### 定义 7.3：完整 Node Input Stream

对每个非空 regular timestamp group，定义：

$$
E_{v,\tau}
=
\left(
q_R(\tau),
r_R(\tau),
I_{v,\tau},
B_{v,\tau}
\right).
$$

定义 regular group record 的 execution timestamp：

$$
\theta_{v,\tau}^{\mathrm{step}}
=
(\tau,i_{\mathrm{step}}).
$$

对 node $v$，把全部 regular group records 与仅在 $v=s$ 时存在的 injection records 合并，并按 $<_{\Theta}$ 排列，得到完整 node input stream：

$$
\mathbf U_v.
$$

更明确地，$\mathbf U_v$ 的 record set 为：

$$
\left\{
(\theta_{v,\tau}^{\mathrm{step}},E_{v,\tau})
\mid I_{v,\tau}\neq\varnothing
\right\}
$$

与：

$$
\left\{
(\theta_t^{\mathrm{in}},b_t^{\mathrm{in}})
\mid t\in[L],\ v=s
\right\}
$$

的 disjoint union。由引理 4.5 与引理 4.6，$\mathbf U_v$ 是有限序列。

### 定义 7.4：Node Reference Transducer 与 Commit Trace

给定 input-node injection transition：

$$
\mathcal I_s:
[L]\times X\times\widetilde{\mathcal S}_s
\to
\mathcal Z_s\times\widetilde{\mathcal S}_s.
$$

若 $\mathcal I_s$ 对 token $t$ 返回非空 labelled hidden $z$，则 input event 的 owner-labelled output 为 $(t,z)$，并必须满足 $t\leq\operatorname{frontier}(z)$。

Node reference transducer $\operatorname{Ref}_v^P$ 按 $\mathbf U_v$ 的 timestamp 顺序处理 records：

- Injection record 使用 $\mathcal I_s$。
- 若 $P=\mathrm{ord}$，regular group 使用式 [[#^eq-owner-ordered-group|GD-7]]。
- 若 $P=\mathrm{joint}$，regular group 使用式 [[#^eq-atomic-joint-transition|GD-8]] 与式 [[#^eq-atomic-joint-commit|GD-9]]。
- 若 $P=\mathrm{front}$，regular group 使用式 [[#^eq-frontier-fusion-transition|GD-F2]] 与式 [[#^eq-frontier-owned-output|GD-F3]]。
- 每个 labelled output 经过第 6 节 selector 与 unit-delay dispatch。

每次 state update 都产生一个 commit record：

$$
q=(\eta_q,\chi_q,\widetilde S_v^q),
$$

其中 $\chi_q\in\mathbb N\times\{0,\ldots,N_{\mathrm{phase}}-1\}\times\mathbb N$ 是完整 commit-order key。Regular owner event 使用 $\chi_q=(\tau,i_{\mathrm{commit}},t)$；joint/frontier event 使用 $\chi_q=(\tau,i_{\mathrm{commit}},0)$；injection transition 使用 $\chi_q=(Rt,i_{\mathrm{inject}},t)$。若 $\chi_q=(\tau_q,i_q,j_q)$，定义 commit timestamp projection：

$$
\operatorname{ctime}(q)=(\tau_q,i_q)\in\Theta.
$$

按 $\chi_q$ 的 lexicographic order 排列全部 commit records，得到 state commit trace $\mathbf Q_v^P$。

定义：

$$
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0)
=
\left(
\mathbf H_v^P,
\mathbf Q_v^P,
\mathbf R_v^P,
\mathbf M_{v,\mathrm{out}}^P,
\widetilde S_v^{P,\mathrm{final}}
\right).
\tag{GD-E2}
$$
^eq-node-reference-artifacts

五项依次是 labelled hidden records、完整 state commit trace、route records、outgoing message stream 与 final augmented state。

上述四类 record streams 都必须使用 canonical logical order：先按 source event 的 commit key，再按 owner、edge id 与 deterministic record/message id 排序。它们不能按物理线程完成或 buffer append 的先后顺序排列；否则式 GD-E2 与 GD-12 中的序列相等没有确定含义。

### 定义 7.5：固定周期 Readout

给定 readout function：

$$
\rho_z:
[L]\times\widetilde{\mathcal S}_z
\to Y.
$$

任何 readout 所需的 hidden/output register 都必须是 $\mathcal S_z$ 的显式组件，不能作为 $\rho_z$ 的隐藏全局输入。

对任意 timestamp $\theta$，定义：

$$
\mathbf Q_z^{P,<\theta}
=
\{q\in\mathbf Q_z^P\mid\operatorname{ctime}(q)<_{\Theta}\theta\}.
$$

若该集合非空，在其中按完整 $\chi_q$ 次序取最后一个 commit record，并把其 augmented state 定义为 $\widetilde S_z^{<\theta}$；若集合为空，则定义 $\widetilde S_z^{<\theta}=\widetilde S_z^0$。

第 $t$ 个固定周期 readout 定义为：

$$
y_t
=
\rho_z
\left(
t,
\widetilde S_z^{<\theta_t^{\mathrm{out}}}
\right).
\tag{GD-E3}
$$
^eq-fixed-period-readout

定义 readout sequence：

$$
y_{0:L}=(y_0,\ldots,y_{L-1})\in Y^L.
$$

式 GD-E3 对每个 $t\in[L]$ 必须执行一次。长路径 message 若在 $\theta_t^{\mathrm{out}}$ 之后才 commit，只能影响后续 readouts，不能追溯修改 $y_t$。

### 定义 7.6：Node Event-Stream Chunk Operator

Node $v$ 的 profile-$P$ chunk operator 是函数：

$$
\mathcal C_v^P:
(\mathbf U_v,\widetilde S_v^0)
\mapsto
\left(
\widehat{\mathbf H}_v^P,
\widehat{\mathbf Q}_v^P,
\widehat{\mathbf R}_v^P,
\widehat{\mathbf M}_{v,\mathrm{out}}^P,
\widehat{\widetilde S}_v^{P,\mathrm{final}}
\right).
$$

称它满足 exact node chunk contract，当且仅当对任意有限合法 node input stream：

$$
\mathcal C_v^P(\mathbf U_v,\widetilde S_v^0)
=
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0).
\tag{GD-12}
$$
^eq-node-event-stream-contract

等式比较式 GD-E2 的全部五类 artifacts。特别地，只比较 final state 或最终 logits 不足以证明该 contract。

### 引理 7.7：有限 Reference Execution 的 Event DAG

在引理 4.6 的条件下，给定任意 profile $P$，teacher-forced event graph $D_L^P$ 是有限 DAG。若再加入定义 7.1 的 sample events 与 autoregressive boundary edges，有限 prefix 的 autoregressive event graph 仍是 DAG。

**证明。**

由引理 4.6，message 与 regular node event 数有限；input、readout 与 sample events 各至多 $L$ 个，所以 event set 有限。

给每个 event 定义 lexicographic rank。Injection、readout 与 sample event 使用其 $\Theta$ timestamp，并追加 tie-break coordinate $0$。Owner-ordered node event 使用：

$$
\operatorname{rank}(e_{v,\tau,t})
=
(\tau,i_{\mathrm{commit}},t).
$$

Joint/frontier node event 使用：

$$
\operatorname{rank}(e_{v,\tau})
=
(\tau,i_{\mathrm{commit}},0).
$$

Message edge 把 round 从 $\tau$ 推进到 $\tau+1$。Local state edge 按 node reference order 指向更大的 timestamp，或在 owner-ordered 同刻 group 内指向更大的 owner index。Readout edge 由式 GD-0.3 从 commit phase 指向 readout phase。Autoregressive boundary edge 由式 GD-0.4 从 readout 指向 sample，再指向下一 injection。每类 edge 都严格增加 rank，所以不存在有向环。

<div class="qed" aria-label="证毕">∎</div>

### 例 7.8：Kernel Family 与 Chunk Lowering

| Node kernel | Logical event semantics | 可能的 chunk implementation |
| --- | --- | --- |
| Token-wise map / FFN | Events 独立读取各自 input | Batched matmul / fused pointwise |
| Causal attention | Event value 只读取允许的 causal prefix | Packed QKV + causal mask / fused attention |
| Mamba/SSM | State edges 形成 affine/selective recurrence | Parallel/blocked scan 或 selective-scan kernel |
| Linear attention | Prefix accumulator state edges | Associative scan / chunked accumulator |
| Same-round set interaction | Atomic-joint node event | Segmented set kernel / grouped attention |
| Frontier-owned state fusion | 同刻 multiset 与 pre-state 产生一个 event value | Segmented reduction + scan/causal-bulk kernel |
| 任意黑盒 transition | 按 dependency-complete event order | Sequential fallback；只证明 correctness |

Chunk lowering 可以按 $(\tau,q_R(\tau),r_R(\tau),t,c,\mu)$ 排序与 pack，但必须保持式 GD-12 和全部 direct dependencies。

### 7.9 Inbox Completeness 与 Node 内等待

在同步 absolute-time reference 中，每个 internal round 的 phase barrier 直接保证 inbox group 完整，不需要 watermark 作为模型语义。

异步 physical runtime 若要在没有全局 barrier 的情况下执行同一 reference，可以使用 watermark、predecessor completion 或 end-of-chunk marker，证明不会再补来 timestamp 不超过某界的 message。Watermark 是 physical progress certificate，不是 logical event；只有当模型行为显式读取 watermark 时，它才必须提升为 control event。

即使完整 $\mathbf U_v$ 已一次性交给 node，state edges 仍可能形成顺序依赖。Chunk operator 可以使用 batched map、scan、masked bulk kernel，或在没有 contraction 时使用 node-local sequential loop。后者仍可满足 GD-12，但 node-local span 可以是 $\Theta(M_v)$。

如果生成 $\mathbf U_v$ 必须先读取 $v$ 自己尚未产生的 output、沿空间 cycle 返回的 message，或未纳入 event graph 的共享 mutable selector state，则 node-topological factorization 失败。本页的空间 DAG、唯一 state owner 与 forward-only routing 正是用于排除这类 circular readiness dependency。

## 8. Streaming 与 Node-Topological Chunk Schedules

### 定义 8.1：Absolute-Time Streaming Schedule

若 $L=0$，execution 没有 input injection，所有 node 保持初始 state。若 $L>0$，streaming reference 按：

$$
\tau=0,1,\ldots,H_L,
$$

推进，其中：

$$
H_L
=
R(L-1)+D.
\tag{GD-8.1}
$$
^eq-streaming-horizon

由 $R=d_{\min}\leq D$，有 $RL\leq H_L$，所以最后一个固定 readout round $RL$ 已包含在该 horizon 内。

本定义采用 **closed finite execution**：在第 $L-1$ 个 readout 后不再注入新 token，但继续执行到 $H_L$，使这 $L$ 个 injections 已经产生的所有空间 messages 都被消费或显式终止。因此本节得到的 final node states 是 post-flush states，不是 hypothetical next-injection boundary $RL$ 上、仍保留 in-flight messages 的 continuation state。后者必须把 boundary state snapshots 与 in-flight message multiset 一起定义，属于风险九所述的下一步 embedding theorem。

在每个 absolute round $\tau$，严格按定义 0.3 的 phase order 执行：

1. 在 $i_{\mathrm{arrive}}$ 收集 arrival timestamp 为 $(\tau,i_{\mathrm{arrive}})$ 的 messages，构造 $I_{v,\tau,t}$、$I_{v,\tau}$ 与 $B_{v,\tau}$。
2. 在 $i_{\mathrm{step}}$ 执行全部非空 regular node groups，并在 $i_{\mathrm{commit}}$ 提交 state、route 与 outgoing message records。
3. 若存在 $t\in[L]$ 满足 $\tau=R(t+1)$，在 $i_{\mathrm{read}}$ 执行固定 readout event $e_t^{\mathrm{out}}$；autoregressive execution 随后在 $i_{\mathrm{sample}}$ 执行 $e_t^{\mathrm{sample}}$。
4. 若存在 $t\in[L]$ 满足 $\tau=Rt$，在 $i_{\mathrm{inject}}$ 执行 input event $e_t^{\mathrm{in}}$。Teacher-forced reference 读取给定 $x_t$；autoregressive reference 对 $t>0$ 读取前一 sample event 的 value。
5. 本 round dispatch 的 spatial messages 按式 GD-3 在 $(\tau+1,i_{\mathrm{arrive}})$ 到达。

每个固定 readout 都按式 GD-E3 读取 commit trace snapshot。因为每条 edge delay 为 $1$，同一个 round 内不存在从一个 spatial node 到另一个 spatial node 的 zero-delay message dependency。

### 定义 8.2：Spatial Topological Order

空间 DAG 的 topological order 是 tuple：

$$
\pi=(v_1,v_2,\ldots,v_N),
\qquad N=|V|,
$$

满足每个 node 恰好出现一次，并且：

$$
(v_i,v_j)\in E
\quad\Longrightarrow\quad
i<j.
$$

有限 DAG 至少存在一个 topological order。

### 定义 8.3：Node-Topological Chunk Schedule

给定 teacher-forced boundary sequence $x_{0:L}$ 与 topological order $\pi$。Chunk schedule 依次处理：

$$
v_1,v_2,\ldots,v_N.
$$

处理 node $v_i$ 时：

1. 它的所有空间前驱已经完成。
2. 从所有前驱 outgoing streams 合并 regular inbox groups；若 $v_i=s$，再加入固定 injection records，得到完整 $\mathbf U_{v_i}$。
3. 调用 $\mathcal C_{v_i}^P$ 一次处理整条 node input stream。
4. 把得到的 outgoing messages 追加到空间后继的待处理 inbox。

全部 nodes 完成后，使用 $\widehat{\mathbf Q}_z^P$ 按式 GD-E3 计算固定 readout sequence。互不依赖的 nodes 可以并行执行；tuple $\pi$ 只用于定义一种合法顺序。

### 定理 8.4：Fixed-Period General DAG Schedule Equivalence

给定任意有限输入 chunk、任意 profile：

$$
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\},
$$

并假设：

1. 空间图 $G$ 满足定义 1.1，不要求 $\Lambda(v)$ 为 singleton。
2. 固定周期满足 $R=d_{\min}$，injection/readout/sample phases 满足式 GD-0.3 与 GD-0.4。
3. 每条 edge 满足 unit-delay dispatch，boundary 满足定义 4.2a 的 carry-over semantics。
4. 每条 message 保留 owner、causal frontier、arrival timestamp 与 message id。
5. Inbox aggregation 满足定义 4.4。
6. 每个 mutable state location 有唯一 owner node。
7. Routing 只沿 $E$ 前进且是确定函数；任何 mutable routing state 都由唯一 node 持有，并包含在该 node event/value 与 chunk contract 中。
8. Event graph 满足定义 7.2 的 dependency completeness。
9. 每个 node 的 chunk operator 满足式 GD-12，并比较完整 commit trace。
10. Execution 满足引理 4.6 的有限事件条件。

则 node-topological chunk schedule 与 absolute-time streaming schedule 产生完全相同的：

- 每个 node 的 timestamped inbox。
- 每条 owner/frontier-labelled hidden record。
- 每个 node 的完整 state commit trace。
- Selected routes。
- 全部 dispatched messages。
- 每个 node 在 closed horizon $H_L$ 后的 post-flush final context state 与 state frontier。
- 固定 timestamps $\theta_t^{\mathrm{out}}$ 上的 readout sequence $y_{0:L}$。

因此 teacher-forced streaming 与 chunk execution 计算同一个 closed finite fixed-period reference semantics。

**证明。**

取空间 DAG 的任意 topological order：

$$
\pi=(v_1,\ldots,v_N).
$$

由前提 6-8，每个 node 的 mutable dependencies 都由该 node 的 augmented state、incoming messages、static parameters 与已声明 boundary data 给出；不存在跨 node 的隐藏 shared-state dependency。因此，一旦 $\mathbf U_v$ 与 $\widetilde S_v^0$ 相同，$\operatorname{Ref}_v^P$ 的全部 artifacts 就唯一确定。

对 $i=1,\ldots,N$ 做数学归纳，证明 node $v_i$ 在两种 schedules 中得到相同完整 $\mathbf U_{v_i}$，并产生式 GD-E2 的相同 artifacts。

当 $i=1$ 时，$v_1=s$。定义 1.1 要求每个 $v\neq s$ 都位于一条从 $s$ 出发的非零长度路径上，所以它至少有一个空间前驱。另一方面，$s$ 不可能有 incoming edge：若 $(u,s)\in E$，则 $u$ 可从 $s$ 到达，进而形成从 $s$ 到 $u$ 再回到 $s$ 的有向环。因此 $s$ 是唯一 indegree-zero node，任意 topological order 都以 $s$ 开始。Input node 的 $\mathbf U_s$ 在两种 schedules 中都由同一组固定 records $b_t^{\mathrm{in}}$ 构成。由式 GD-12，chunk operator 与 streaming reference transducer 产生相同 hidden records、commit trace、routes、outgoing messages 与 final augmented state。

假设结论对 $v_1,\ldots,v_{i-1}$ 成立。考虑 $v_i$。由 topological order 的定义，$v_i$ 的每个直接前驱都位于：

$$
\{v_1,\ldots,v_{i-1}\}.
$$

由归纳假设，每个前驱在两种 schedules 中产生完全相同的 outgoing message stream。因此，把所有 destination 为 $v_i$ 的 messages 按 $(\tau,t)$ 分桶后，得到相同的：

$$
I_{v_i,\tau,t},
$$

相同的 raw multiset $I_{v_i,\tau}$、owner tuple $B_{v_i,\tau}$，以及相同的完整 node input stream $\mathbf U_{v_i}$。

在 streaming schedule 中，node $v_i$ 按 reference event order 对 $\mathbf U_{v_i}$ 执行 $\operatorname{Ref}_{v_i}^P$。在 chunk schedule 中，它执行 $\mathcal C_{v_i}^P$。由式 GD-12，两者产生式 GD-E2 的全部相同 artifacts。

所以结论对 $v_i$ 成立。由数学归纳法，结论对所有 nodes 成立，特别地 $\mathbf Q_z^P=\widehat{\mathbf Q}_z^P$。对每个 $t\in[L]$ 应用同一个式 GD-E3，得到相同 $y_t$。

证明中没有使用“所有到达同一 node 的路径等长”，所以一般 DAG 中的 path-length collision 被完整保留，而不是通过 relay node 消除。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.4a：固定周期 Readout 不被长路径追溯修改

在定理 8.4 的条件下，任意 arrival/commit timestamp 晚于 $\theta_t^{\mathrm{out}}$ 的 event 都不会改变 $y_t$，但可以通过后续 state edges 影响 $y_{t+1},y_{t+2},\ldots$。

**证明。**

由式 GD-E3，$y_t$ 只读取 $\theta_t^{\mathrm{out}}$ 之前的最后 committed state。更晚 event 不属于该 snapshot；后续 readout 使用更晚 snapshot，因而仍可读取其影响。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.5：Owner-Ordered Profile 正确性

若每个 node 的 chunk operator 精确实现 owner-ordered event-stream fold，则 node-topological chunk execution 与 owner-ordered absolute-time streaming reference 等价。

**证明。**

在定理 8.4 中取 $P=\mathrm{ord}$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.6：Atomic-Joint Profile 正确性

若每个 node 的 chunk operator 精确实现 atomic-joint timestamp transitions，则 node-topological chunk execution 与 atomic-joint absolute-time streaming reference 等价。

**证明。**

在定理 8.4 中取 $P=\mathrm{joint}$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.6a：Frontier-Fusion Profile 正确性

若每个 node 的 chunk operator 精确实现 frontier-owned atomic fusion event-stream transition，则 node-topological chunk execution 与 frontier-fusion absolute-time streaming reference 等价，并在定理 5.13 的前提下保持 token-prefix frontier invariant。

**证明。**

在定理 8.4 中取 $P=\mathrm{front}$，得到 schedule equivalence；再应用定理 5.13，得到 causal-frontier invariant。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.7：Fold-Equivalent Joint Lowering

若每个 node 的 joint operator 还满足式 [[#^eq-joint-ordered-equivalence|GD-10]]，则 joint chunk execution、owner-ordered chunk execution 与 owner-ordered streaming reference 三者等价。

**证明。**

由命题 5.8，每个 timestamp group 上 joint 与 ordered artifacts 相同。对每个 node 的 timestamp stream 归纳，可得两种 node reference transducers 相同。再分别应用推论 8.5 与推论 8.6。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.8：等长路径模型是本定理的特殊情形

若对每个 node $v$，存在唯一 $d(v)$ 使：

$$
\Lambda(v)=\{d(v)\},
$$

则 token $t$ 的任意 trajectory message 到达 $v$ 的 round 唯一为 $Rt+d(v)$；不同 trajectory owners 不会在同一 $v$、同一 arrival round 到达。定理 8.4 仍然成立，并在 owner-ordered/atomic-joint profile 中退化为 leveled-DAG schedule-equivalence 结论；frontier-fusion profile 仍可因 persistent state dependency 发生 owner promotion。

**证明。**

由式 GD-2.1，任意从 token $t$ 注入并到达 $v$ 的 trajectory path 都有 $\tau=Rt+d(v)$。若 $t\neq t'$：

$$
Rt+d(v)
\neq
Rt'+d(v),
$$

所以不存在同刻 trajectory-owner collision。其余结论直接由定理 8.4 得到。

<div class="qed" aria-label="证毕">∎</div>

## 9. 正确性之外：Work、Span 与超稀疏约束

### 9.0 三层性能目标

本文把“支持 chunk prefill”拆成三个不能混用的层级：

| 层级 | 要求 | 允许的 node 内实现 | 本页状态 |
| --- | --- | --- | --- |
| Closed-finite exact chunk correctness | 一次 chunk 调用与 closed finite 逐 timestamp reference artifacts 完全相同 | 包括 sequential fallback | 由定理 8.4 归约到 node contract |
| Node-local chunk throughput | 一个 node 一次或少量调用处理完整多 token / 多 round stream；本地 pack，批量收发 edge messages，无逐 token 全局 orchestration | 普通 C++/device loop、branch、top-k、gather/scatter、局部矩阵 kernel 均可 | Tide 当前首要性能目标 |
| Sequence-axis low span | 跨 token/event 依赖可被 contraction，不保留长度随 chunk 线性增长的 critical path | Token-local map、causal attention、scan、segmented bulk 等 | 更强的可选目标，需逐 kernel 证明 |

在默认 identity idle semantics 下，固定周期 $R$ 不会自动破坏前两层；它只决定 injection/readout deadlines 与每个 node 的 timestamped event stream。若 empty timestamp 也执行非平凡 decay/update，其 work/span 必须另行计入。真正阻止第三层的是 node-local state/control transition 缺少可组合结构，而不是“一个 external period 含 $R$ 个 internal rounds”这一事实本身。

因此，若每个 node 映射到独立设备，合理的第一阶段实现是：空间前驱批量生成完整或分块 event streams，node 在本设备内对这些 records 做 sort/segment/pack 后一次处理，再批量 dispatch。Node 内某些 selector/routing 代码即使只能顺序执行，也不要求 runtime 回到逐 token 的跨设备控制循环；但它的实际 span 与吞吐必须诚实计入性能报告。

### 定义 9.1：Node Event Count

定义 closed execution 的 round-index set：

$$
\mathbb T_L
=
\begin{cases}
\varnothing,&L=0,\\
\{0,\ldots,H_L\},&L>0.
\end{cases}
$$

定义 node $v$ 的 owner-event count：

$$
M_v
=
\sum_{\tau\in\mathbb T_L}|\mathcal O_{v,\tau}|.
$$

定义全图 owner-event count：

$$
M
=
\sum_{v\in V}M_v.
$$

令 $\mathcal M_{\mathrm{dispatch}}$ 为 execution 中全部 dispatched messages 的集合，定义其 message 总数：

$$
N_{\mathrm{msg}}
=
\left|\mathcal M_{\mathrm{dispatch}}\right|.
$$

Atomic-joint 与 frontier-fusion profile 的 timestamp group 数可能小于 $M_v$，但 joint/fusion kernel 的 work 必须计入它读取的全部 raw messages 与 owner records。

定义实际 regular node event 数：

$$
M_{\mathrm{node}}^P
=
\begin{cases}
M,&P=\mathrm{ord},\\
\displaystyle\sum_{v\in V}
\left|\{\tau\in\mathbb T_L\mid I_{v,\tau}\neq\varnothing\}\right|,
&P\in\{\mathrm{joint},\mathrm{front}\}.
\end{cases}
$$

Teacher-forced execution 还固定包含 $L$ 个 injection events 与 $L$ 个 readout events。因此若把全部 logical events 计入，定义：

$$
M_{\mathrm{all}}^{\mathrm{TF}}
=
M_{\mathrm{node}}^P+2L,
$$

其中 $M_{\mathrm{node}}^P$ 是按所选 profile 实际建立的 regular node event 数。Autoregressive finite prefix 另增加 $L$ 个 sample events。性能报告不能把这些 boundary events、commit trace 或 readout cost 视为免费。

### 定义 9.2：Node Chunk Work 与 Span

记 node $v$ 的 chunk operator work upper bound 与 parallel span upper bound 分别为：

$$
W_v,
\qquad
P_v.
$$

Work 是总 primitive operation 数的抽象；span 是在依赖与无限处理器理想化下的 critical-path length。二者都是性能见证，不属于定理 8.4 的 correctness 结论。

### 命题 9.3：Coarse Node-Topological Work/Span 上界

令 $W_{\mathrm{transport}}$ 表示全部 dispatched messages 的 serialization、transport、merge 与 materialization work。Node-topological schedule 的总 work 满足：

$$
W_{\mathrm{graph}}
\leq
\sum_{v\in V}W_v
+W_{\mathrm{transport}}
+W_{\mathrm{out}}.
\tag{GD-13}
$$
^eq-general-dag-work

其中 $W_{\mathrm{out}}$ 是从 output-node commit trace 计算并记录全部 $L$ 个固定 readouts 的 work。对每个 node $v$，令 $C_v^{\mathrm{sched}}\geq 0$ 表示未包含在 $P_v$ 中的 inter-node stream merge、transport 与 scheduler span；令 $P_{\mathrm{out}}$ 表示同一 readout 阶段的 span。若无依赖 nodes 可并行，coarse span 满足：

$$
P_{\mathrm{graph}}
\leq
\max_{p}
\sum_{v\in p}
\bigl(P_v+C_v^{\mathrm{sched}}\bigr)
+P_{\mathrm{out}},
\tag{GD-14}
$$
^eq-general-dag-span

其中最大值遍历空间 DAG 的所有有向路径。

**证明。**

这里 $W_v$ 已包含 node-local inbox aggregation、transition、routing，以及 input node 对 injection records 的处理。Message payload size、跨设备通信、全局 sort 或非线性索引构建的成本全部计入 $W_{\mathrm{transport}}$；固定 readout function $\rho_z$ 与 output materialization 的全部成本计入 $W_{\mathrm{out}}$。把三类互不重叠的 work 相加即得式 GD-13。

Chunk schedule 的 node-level dependency graph 就是空间 DAG。任意 node-computation critical path 对应其中一条有向路径；沿该路径累加每个 node 的 chunk span 与调度开销，再加入 output readout extraction 的 span，得到式 GD-14。

<div class="qed" aria-label="证毕">∎</div>

这个命题解释了“一般 DAG 仍可能支持高性能 chunk prefill”的准确含义：

- Graph-level 顺序深度由空间 critical path 决定，而不是由 token 数直接决定。
- 但若某个 $P_v=\Theta(M_v)$ 且没有 scan/bulk contraction，token-axis 顺序链只是被封装进 node kernel，并没有消失。
- 若 $M$ 本身因 fan-out 指数增长，即使 span 较小，总 work 与 memory 仍不可接受。

### 定义 9.4：固定 Birth Signal Slots

给定常数：

$$
K\in\mathbb N_{>0}.
$$

每个 input token $b\in[L]$ 在注入时最多创建 $K$ 个 immutable birth slots：

$$
(b,q),
\qquad
q\in[K].
$$

这里 $b$ 是 birth token，不随后续 owner/frontier promotion 改变。Slot id $(b,q)$ 写入 message metadata。Strict slot profile 要求：

- 每个 slot 在任一时刻最多对应一条 active travelling message。
- 一个 slot 到达 node 后，最多选择一条 outgoing edge。
- Slot 可以终止或与其他 slots 在 node 内联合计算，但不能复制为两个同时活跃的同 id slots。
- 每个 birth slot 在 injection/split 时至多初始化一次；终止后不能重新初始化或复用。已初始化 slot 可以沿一条空间路径依次访问多个 nodes。
- 若需要 split，只能从同一 birth token 从未激活过的固定 slot pool 中分配；新 slot 从 split node 开始一条新的单路径 trajectory。
- Frontier fusion 可以消费多个 incoming birth slots，并保留其中一个或若干已有 slots继续传播；不能因为 owner 提升到更大的 frontier 而获得新的 slot pool。

在该 profile 中，routing record 不再只是 edge set，而是 slot-edge assignment：

$$
A_{v,\tau}^{\mathrm{slot}}
\subseteq
([L]\times[K])
\times
\{(v,u)\in E\}.
$$

同一个 birth slot id 在 $A_{v,\tau}^{\mathrm{slot}}$ 中至多出现一次。若多个 slots 在同一 event group 中聚合，node kernel 必须显式给出哪些 slots merge、terminate 与继续传播；不能在丢失 slot identity 后仍声称满足 slot conservation。

### 命题 9.5：固定 Slot 的 Event 上界

在 strict slot profile 中，每个 birth token 的全部 slot node visits 不超过：

$$
K|V|.
$$

长度为 $L$ 的 chunk 的 owner-event 总数满足：

$$
M\leq LK|V|.
\tag{GD-15}
$$
^eq-owner-slot-event-bound

**证明。**

每个 birth slot 至多初始化一次，并且初始化后不复制，只沿一条 routing path 前进。空间图无环，所以该路径最多访问每个 node 一次，node visits 不超过 $|V|$。每个 birth token 最多有 $K$ 个 slots，因此其全部 slot visits 不超过 $K|V|$。Frontier promotion 只改变 causal owner label，不创建 birth slots。每个 owner-event 至少消费一个 slot visit，所以 owner-event count 不超过 slot visit count；对 $L$ 个 birth tokens 求和得到式 GD-15。

<div class="qed" aria-label="证毕">∎</div>

固定 birth slot 不是唯一 sparse design，但它给出一个不依赖 spatial level、owner promotion，也不需要跨 token online counter 的明确上界。若改为“每个 event 独立 top-$K$ fan-out”，最坏 event 数可能随 DAG depth 指数增长，不能称为超稀疏保证。

## 10. 空间/时间均衡与 Selector Profile

### 定义 10.1：Node Activation Load

在 fixed-slot profile 中，定义：

$$
a_{b,q,v}
=
\begin{cases}
1,&\text{birth token }b\text{ 的 slot }q\text{ 访问 node }v,\\
0,&\text{否则}.
\end{cases}
$$

定义长度为 $L$ 的 node load：

$$
n_v^{(L)}
=
\sum_{b\in[L]}\sum_{q\in[K]}a_{b,q,v}.
\tag{GD-16}
$$
^eq-general-node-load

若不采用 slot profile，可以把 $n_v^{(L)}$ 改为到达 $v$ 的 owner-event 数，但必须同时报告 event duplication。

### 10.2 当前 LH Online Counter Selector

给定 hidden-summary space $\mathcal H$、control-state space $\mathcal Q$ 与 hard-route space $\mathcal R_{\mathrm{route}}$，以及确定函数：

$$
\rho:
\mathcal H\times\mathcal Q
\to
\mathcal R_{\mathrm{route}},
$$

$$
U:
\mathcal Q\times\mathcal R_{\mathrm{route}}
\to
\mathcal Q.
$$

给定有限 event count $J\in\mathbb N_{>0}$。对按 reference order 排列的 $j\in[J]$，当前 LH-like selector 可以抽象为：

$$
R_j=\rho(H_j,Q_j),
$$

$$
Q_{j+1}=U(Q_j,R_j),
$$

其中第二式只对 $j+1\in[J]$ 使用；$H_j\in\mathcal H$、$Q_j\in\mathcal Q$、$R_j\in\mathcal R_{\mathrm{route}}$，且 $Q_j$ 包含 `affectcount/selectcount`。这可以直接惩罚近期热点，但形成：

$$
Q_0\to R_0\to Q_1\to R_1\to\cdots.
$$

若 $j$ 沿 token/event axis 增长且 combined transition 不具有已证明的 scan/bulk structure，就进入 [[adaptive-routing-prefill-impossibility]] 的自适应控制链。

### 命题 10.3：强 Online Feedback 的依赖代价

如果后一个 route 必须读取由前一个实际 hard route 更新的 control state，且该 update/route composition 没有额外已证明的 contraction，则 exact execution 存在相应长度的顺序 control chain。

**证明。**

后一个 route 需要更新后的 $Q_{j+1}$；$Q_{j+1}$ 需要前一个 hard route $R_j$；$R_j$ 又读取 $Q_j$。因此每一步都依赖前一步，得到上述 chain。

<div class="qed" aria-label="证毕">∎</div>

### 10.4 Prefill-Compatible 均衡层

在 strict profile 中，均衡拆成以下互不替代的层：

| 层 | 方法 | 是否进入逐 event forward state |
| --- | --- | --- |
| 结构上界 | 固定 birth slots、有限出度、静态 availability | 否 |
| 静态容量 | Edge/node bias、设备容量权重、拓扑分区 | 否 |
| 确定性时间分散 | $d_{v\to u}(t,\tau)$ | 否 |
| 训练期均衡 | Node load / time-window loss | 只影响梯度 |
| 在线硬均衡 | Persistent route counters | 是；通常形成 control chain |

给定目标 node capacity weights：

$$
\pi_v>0,
\qquad
\sum_{v\in V}\pi_v=1,
$$

定义归一化实际 load：

$$
\widehat p_v
=
\frac{n_v^{(L)}}{\sum_{u\in V}n_u^{(L)}}.
$$

分母为 $0$ 时把 loss 定义为 $0$。空间均衡目标可以写为：

$$
\mathcal L_{\mathrm{space}}
=
\sum_{v\in V}
(\widehat p_v-\pi_v)^2.
\tag{GD-17}
$$
^eq-general-space-balance-loss

给定 window width $B\in\mathbb N_{>0}$。对每个 $j\in\mathbb N$，定义 absolute-time window：

$$
W_j
=
\{jB,\ldots,(j+1)B-1\},
$$

可以统计到达时间落入 $W_j$ 的 node events，构造 $\mathcal L_{\mathrm{time}}$。它约束真实 pipeline 时间上的热点，而不是把 external token index 误当作唯一 arrival time。

### 命题 10.5：Hard Cross-Token Capacity 的三种基本选择

给定 hard capacity $C\in\mathbb N$。若要求任意输入上、任意时间窗口内 node $v$ 的 hard admission 不超过 $C$，而多个 owners 都可能选择 $v$，则 exact selector 至少采用以下一种机制：

1. 用静态 eligibility/quota 预先限制可选 owners/slots。
2. 联合观察一个已知 owner/event 集合后做 assignment。
3. 在线维护已使用 capacity，让后续 decision 读取此前 admissions。

第二种机制是否允许取决于 reference semantics：atomic-joint 与 frontier-fusion 可以在同一 timestamp group 内使用它，但不能免费跨越尚未形成的未来 groups。第三种机制形成 online control chain。第一种最容易保持 strict prefill-native，但限制内容 routing 自由度。

**证明。**

若资格未预先限制，当超过 $C$ 个 candidates 同时或先后希望进入 $v$ 时，selector 必须依据其他 candidates 拒绝一部分。若同时观察一个已知集合后联合决定，属于第二类；若按到达顺序读取已用 capacity，属于第三类；剩余情形只能提前限制资格，属于第一类。

<div class="qed" aria-label="证毕">∎</div>

### 10.6 三种 Selector Profile

| Profile | State 与均衡 | Chunk-prefill 位置 |
| --- | --- | --- |
| `LH-exact streaming` | 每次 hard route 后更新 persistent counts | 保留原行为，但通常含长 adaptive chain |
| `General-DAG strict` | Fixed birth slots、static bias/prior、training loss | 满足定理 8.4 closed-finite correctness 的候选 |
| `Block-lagged` | Block 内冻结 counters，block 后更新 | Block 内可批量，block 间仍顺序 |

## 11. 三种同刻/融合语义的实验设计

Owner-ordered、atomic-joint 与 frontier-fusion 不应混成一个实验条件。前两种保留 per-owner trajectories；第三种主动做 semantic quotient，并改变 outgoing owner。

### 11.1 必做 Correctness Gates

| Gate | Reference | Chunk candidate | 判定 |
| --- | --- | --- | --- |
| Ordered scalar | 按 $(\tau,t)$ 顺序执行 | Packed/scan/causal-bulk | 全 artifact equality |
| Joint scalar | 按 $\tau$ 调用 $\mathcal J_v$ | Grouped/segmented bulk | 全 artifact equality |
| Frontier-fusion scalar | 按 $\tau$ 调用 $\mathcal F_v$，统一发射 | Segmented fusion + scan/causal-bulk | 全 artifact equality |
| Frontier invariant | 式 GD-F1 的 scalar propagation | Batched max/frontier propagation | 所有 output/state 满足定理 5.13 |
| Joint vs ordered | 两套 reference | 直接比较 | 只在式 GD-10 成立时期待相等 |
| Fusion vs per-owner | 三套 reference | 直接比较 | 默认不期待相等；评估 quotient 的质量/效率 |
| Streaming vs topological | Closed finite absolute-time schedule | Node-topological schedule | 定理 8.4 artifacts |

Artifact equality 至少包括：

- Per-owner/frontier hidden。
- 完整 state commit trace 与每次 commit 的 order key。
- State causal frontier。
- Selected edges。
- Message id、owner、frontier、birth slot、arrival timestamp、destination 与 payload。
- Final node states。
- 每个固定 $\theta_t^{\mathrm{out}}$ 的 readout $y_t$。

### 11.2 最小诊断任务

1. **Unequal-path collision**：直接边与两跳/三跳路径使多个 owners 在同一 node、同一 $\tau$ 相遇。
2. **Cross-time owner inversion**：让 B 的短路径 event 先于 A 的长路径 event 到达，检查 absolute-time state visibility。
3. **State-frontier contamination**：当前 inputs 只有 A/B，但 pre-state frontier 为 C>B；验证 emission 必须归属 C 而不是 B。
4. **Frontier fusion**：A/B 同刻联合计算，只发射一个 owner B 的 message，并与 per-owner joint 输出比较。
5. **Accumulator counterexample**：复现实例 5.9，确保测试能发现“final state 相同但 per-owner output 不同”。
6. **Causal attention node**：分别验证 event-order mask 与 owner-order mask 的 scalar/bulk equivalence。
7. **SSM/linear-attention node**：验证 irregular event stream 的 packed scan。
8. **Joint interaction node**：让 route B 显式依赖同刻 A 的 feature，检查 joint semantics。
9. **Sparse birth-slot routing**：检查 event bound、slot conservation、fusion slot consumption 与 output reachability。
10. **Dual cortex DAG**：验证多路径 input cortex、单向 bridge 与 output cortex 的完整 topological execution。

### 11.3 性能与质量指标

- Correct output / artifact equality。
- Total owner-event count $M$。
- Node chunk work 与 measured latency。
- Graph critical-path span。
- Packing utilization 与 padding waste。
- Node/edge load distribution。
- Collision density：同一 $(v,\tau)$ 中 owner 数分布。
- Frontier promotion distance 与 promotion frequency。
- Fusion compression ratio：raw owner records / unified outputs。
- Routing stability 与训练质量。
- Ordered、joint 与 frontier-fusion profile 的任务质量差异。

## 12. 对当前 LH/Tide 机制的迁移

| 当前机制 | 一般 DAG strict profile 的处理 |
| --- | --- |
| Input/output cortex + bridge | 保留为定义 3.1 的可选空间结构 |
| 每条 edge unit delay | 直接保留 |
| Signal payload | 增加 message id、owner、causal frontier、arrival timestamp、birth slot |
| External token clock | 固定为 $Rt$ injection 与 $R(t+1)$ readout，不由 selector/routing 改写 |
| 同 absolute internal round 多源聚合 | 同时保留 raw inbox 与 owner view；选择 ordered、joint 或 frontier-fusion contract |
| Local hidden/KV | 归入 node-owned state 与 node transducer |
| `signal norm` | 作为式 GD-11 的 local content feature |
| `affectcount/selectcount` | Streaming profile 保留；strict profile 改为日志、训练统计或 static bias 来源 |
| Persistent fairness ordering | 不进入 strict exact forward routing |
| `clear_after_activation` | 必须成为 node transition 的显式 state update，并证明 chunk contract；不能作为 selector side effect |
| PACKED/CROSSBATCH | 作为 $\mathcal C_v^P$ 的 physical lowering，不改变 reference semantics |
| Phase barriers | 可封装在 node/subgraph transducer；不得产生未声明 zero-delay shared-state cycle |

当前 native LH 可以继续作为 golden oracle，但本页不主张它自动满足任一 strict profile。特别需要逐项检查：

- 现有 aggregate 是否保留 owner/time provenance。
- 现有 state/message 是否能增加 causal-frontier audit label。
- Selector counters 是否跨 owners/events 形成 adaptive chain。
- 同一 absolute internal round 的 node update 是 ordered、joint、frontier-fusion，还是依赖线程顺序。
- Memory clear/decay 的 visibility 与 commit timing。
- Output state 是否显式包含式 GD-E3 所需的 readout register。

## 13. 全面设计审视

### 13.1 已经解决的结构问题

1. **不再修改路径时延**：skip edge 保持 unit delay，不通过 relay leveling 改写 reference semantics。
2. **外部时钟固定**：token $t$ 在 $Rt$ injection，第 $t$ 个 readout 在 $R(t+1)$ 发生；selector/routing 不能修改 clock。
3. **完整逻辑时间明确**：absolute round、phase、path age、owner 与 frontier 是不同字段；同一 boundary 的 commit/readout/sample/injection 顺序由式 GD-0.3 固定。
4. **Logical event 已类型化**：input、node、readout 与 sample events 都有 event id、kind、location、timestamp、owner support 与 frontier。
5. **Dependency completeness 已成为前提**：message、state、readout 与 autoregressive boundary dependencies 均显式进入 event DAG。
6. **固定 readout 已进入 correctness contract**：node chunk 必须对齐完整 commit trace，定理 8.4 直接推出每个 $y_t$ 相同。
7. **一般 DAG 有直接证明**：证明按空间 topological order 归纳，不要求等长路径。
8. **长期上下文位置明确**：长期历史进入 node-owned KV/SSM/accumulator，不藏在无 owner 的游走 signal 中。
9. **Correctness 与 performance 分层**：定理 8.4 证明 schedule equivalence；第 9 节再区分 node-local chunk throughput、token-axis low span、work 与 event bound。
10. **稀疏性不再依赖 spatial level**：fixed birth slots 给出适用于一般 DAG 与 owner promotion 的 $LK|V|$ 上界。

这里“已经解决”只指 streaming 与 chunk schedules 相对同一个 absolute-time reference 的等价性，不表示已经解决该 reference 与标准 token-prefix autoregressive semantics 的关系。

### 13.2 仍然存在的主要风险

#### 风险一：Node Chunk Contract 可能只是把顺序链藏进 Kernel

式 GD-12 是 correctness contract，不是性能结论。若 selector/state transition 是 arbitrary black box，$\mathcal C_v^P$ 可能只能顺序执行整条 event stream。

研究上必须为每类 node 声明：

- Token-local。
- Causal attention/bulk。
- Scan-composable。
- Same-time joint。
- Sequential fallback。

并分别给出 work/span witness。

#### 风险二：一般 DAG 的 Absolute-Time Order 不自动等于 Token Order

即使选择 owner-ordered profile，一般 DAG 仍允许例 5.2b 的 owner inversion：由命题 2.7，当路径长度差超过固定值 $R(t_B-t_A)$ 时，较晚 token 的短路径 event 会先于较早 token 的长路径 event 修改同一 node state。该行为由固定 $R$ 与 topology 决定，runtime selector 不能改写其 timestamp。Atomic-joint 还进一步允许较早 owner 的同刻 output 读取较晚 owner 的 input。

这些行为属于本文 absolute-time reference；它们不要求 owner 小的 event 永远先于 owner 大的 event。Token-prefix correctness 改由完整 timestamp visibility 与 frontier bound 保证：式 GD-2.5 要求第 $t$ 个 readout 发生时尚不可见 $x_{t+1}$，式 GD-2.4 要求 event value 的 frontier 不超过其 timestamp 可见 prefix。

因此仍需要分别验证：

- Streaming absolute-time causality。
- 每个 event function 是否满足式 GD-2.4。
- Output readout 是否满足 frontier $\leq t$。
- 是否允许跨时间 owner inversion。
- 是否要求定义 5.6 的 owner-causal joint 条件。
- 是否实际满足式 GD-10。
- 是否采用定理 5.13 的 frontier promotion invariant。

#### 风险三：Owner/Frontier 不能代替完整 Provenance

同一 owner/frontier 可以经不同 path、不同 birth slot、不同 absolute time 多次到达同一 node。Frontier 只给出 dependency upper bound，不说明具体依赖了哪些 tokens；仅保留 owner/frontier 仍不足以 replay。Logical event id、message id、arrival timestamp、source、birth slot 与 route lineage 都应进入 trace。

#### 风险四：Fixed Slots 可能限制表达力

$K$ 条 birth-slot trajectories 给出干净上界，但禁止无界 split。需要实验判断：

- 小 $K$ 是否足以覆盖有用的局部通信。
- Merge/fusion 后如何保留、消费或释放 birth slots。
- Training 是否出现 slot collapse。
- 是否需要静态分层 slot pool，而不是自由 cloning。

如果放松 slot conservation，必须提供新的 event-count bound。

#### 风险五：Global Load Balance 仍未被免费解决

Static bias、prior 和 training loss 只保证分布意义上的均衡，不保证任意输入的即时 hard balance。Atomic-joint/frontier-fusion 只能联合处理已知 timestamp group，不能自动解决跨全部未来 events 的容量分配。

#### 风险六：固定 Readout 已定义，但其表示能力尚未验证

式 GD-E3 已固定“一周期一 readout”，并要求 readout register 是 $\mathcal S_z$ 的显式组件。剩余风险不再是 readout 是否存在，而是：

- 固定 deadline 前的 event ancestors 是否足以产生有训练价值的 $y_t$。
- 长路径只影响未来 readouts 的归纳偏置是否合理。
- Frontier-fusion 是否过早丢失 per-owner trajectory information。
- Readout state 的训练目标、loss alignment 与 gradient path 是否明确。

#### 风险七：本页不覆盖 Graph Cycle

空间 DAG 无环是主定理前提。特殊 recurrent subgraph 可以：

- 按有限 round 展开为 event DAG。
- 增加 delay/state boundary。
- 封装为有独立 chunk contract 的 supernode。

同一 logical time 的 zero-delay algebraic loop 不在本页范围内，见 [[finite-event-dag-and-zero-delay-loops-memo]]。

#### 风险八：训练与 Backend Lowering 仍需独立验证

Schedule correctness 不自动证明：

- Backward graph 与 gradient accumulation 等价。
- Sparse packed kernel 在 Ascend 上高效。
- Dynamic shape、segment sorting 与 communication cost 可接受。
- 数值重排只产生声明范围内的浮点误差。

#### 风险九：Fixed-Period Event Reference 尚未嵌入统一 StepTransition

本页把 fixed-period event semantics 作为 primary reference，并证明其两种 closed finite schedules 等价。定义 8.1 在最后一个 readout 后继续 flush 到 $H_L$，所以式 GD-E2 的 final states 是 post-flush states；它们不等于下一 injection boundary 上“node states + 尚未到达 messages”组成的 continuation state。

要得到可接续 decode 的 prefill handoff，尚需构造单周期 transition：

$$
\mathcal T_R:
X\times\mathcal S_R
\to
Y\times\mathcal S_R
$$

使 $\mathcal S_R$ 显式包含全部 node states 与跨 boundary in-flight messages；定义每个 boundary cut 的 state snapshot；再证明连续 $L$ 个周期的 event execution 正好是 $\operatorname{Fold}_{\mathcal T_R}^L$ 的 unfolding。该 embedding theorem 是把本页结果提升为统一 model-level `prefill == decode` theorem 的下一步。

### 13.3 当前推荐的最小实现顺序

1. 实现固定 $R$、六 phase boundary order 与每周期强制 readout。
2. 实现 typed event key：`(event_id, kind, location, timestamp, owner_support, frontier)`。
3. 实现 message key：`(message_id, owner, frontier, arrival_timestamp, src, dst, birth_slot, lineage)`。
4. 实现一般 DAG absolute-time scalar oracle，并输出完整 event/message/commit ledger。
5. 实现 owner-ordered node-topological chunk executor，并对齐式 GD-E2 的五类 artifacts 与全部 $y_t$。
6. 定义 boundary cut、in-flight message multiset 与统一 $\mathcal T_R$，证明 continuation state 的 fold embedding。
7. 为 token-wise、attention、SSM/linear attention 增加 packed node kernels；其他局部逻辑先允许 sequential fallback。
8. 实现 atomic-joint 与 frontier-fusion scalar/chunk profiles。
9. 用 unequal-path collision、owner inversion、跨 boundary carry-over、fixed readout 与 state-frontier contamination 比较三种 profile。
10. 加入 fixed birth slots、work/span 与 load metrics。
11. 最后再引入训练期均衡和更复杂 selector。

### 13.4 当前可主张与不可主张

当前可以主张：

- 一般 finite unit-delay DAG 在本文条件下具有 closed-finite exact node-topological chunk schedule。
- 固定周期 injection/readout 与 carry-over messages 可以同时纳入该 schedule equivalence。
- 每个有限 teacher-forced execution 在本文条件下具有 typed dependency-complete event DAG。
- Token owner 在非等长路径中是必要 provenance 字段。
- Owner-ordered、atomic-joint 与 frontier-fusion 都可以分别建立 schedule-equivalence theorem。
- Fold-equivalent joint kernel 可以批量实现 owner-ordered semantics。
- Frontier-fusion 在定理 5.13 的条件下保持显式 token-prefix dependency upper bound。
- Fixed birth slots 给出一个兼容 owner promotion 的超稀疏事件上界。

当前不能主张：

- 任意一般 DAG、任意 node kernel 都有高性能 prefill。
- Atomic-joint 与 owner-ordered 在未证明式 GD-10 时语义相同。
- Frontier-fusion 的 numerical state transition 自动具有 scan/bulk 高性能实现。
- 当前 kernel/selector family 已经给出 low-span parallel-prefill witness。
- 当前 LH selector 已满足 strict profile。
- Static/training balance 能提供任意输入上的 hard capacity。
- Closed execution 的 post-flush final state 可以直接作为下一 token boundary 的 decode continuation state。
- 本页 schedule theorem 已经等同于统一 $\mathcal T_R$ 上的完整 model-level `prefill == decode` theorem。
- 本页已经解决 graph cycle、backward 或 Ascend lowering。

## 14. 研究结论

一般 DAG 下，owner 与 causal frontier 都不应被删除，但二者职责不同。Absolute time 决定何时发生；trajectory owner 表示哪条 token path 正被推进；causal frontier 给出数值内容依赖到哪个 token prefix；node-owned state 决定历史如何影响当前计算。Frontier-fusion 会主动终止多个旧 trajectories，并把 unified output owner 提升为 causal frontier。

最小正向命题是：

> 对任意满足 $R=d_{\min}$ 的有限 unit-delay 空间 DAG，只要固定 injection/readout phase order、carry-over semantics、typed event dependencies、唯一 state ownership 与 exact node chunk contract 均成立，就可以把 closed finite teacher-forced absolute-time streaming execution 重排为 node-topological chunk execution，并保持全部 hidden、commit、route、message、post-flush final-state 与固定周期 readout artifacts。

这个命题保留了 Tide 所需的一般空间 DAG，也把真正的性能问题准确地下推到：

- Node event-stream kernel 是否至少具有可接受的 local chunk throughput，以及是否进一步具有 causal-bulk/scan/joint low-span structure。
- Event 数是否有超稀疏上界。
- Selector 是否避免不可收缩的跨 token control chain。
- Ordered、joint 与 frontier-fusion semantics 中哪一种更有训练价值、任务价值与可实现的 numerical contraction。
