---
type: mathematical-learning-note
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - local-semantics
  - semantic-anchor
  - learning-note
---

# 带权消息的有状态局部架构

节点收到消息后，先保存本次信息，再描述当前内容与已有记忆。区域依据这些描述分配发送强度；获得正发送强度的节点计算完整内容，并向下游发送。本文给出这一类局部架构的共同定义。

图、区域和逻辑时间沿用 [SettleGraph](settlegraph-learning-note.md)、[TimedDAG](timed-dag-region-selector-learning-note.md) 与 [PositiveDelayGraph](positive-delay-graph-finite-cut-learning-note.md)。这里选择它们允许的局部函数。读者只需有限集合、向量、函数与归纳法。

[区域分配](region-allocation-learning-note.md)定义评分与发送函数；[带权 KV](weighted-kv-sparse-activation-example.md)和[循环记忆](recurrent-memory-learning-note.md)分别给出完整的状态、更新与读取。选定这些函数，再绑定图和时间，就得到一个确定的模型。设计取舍集中在[设计总览](memos/architecture/selector-and-memory.md)。

## 1. 消息、输入与候选

固定有限节点集 $V$、区域划分 $V=\bigsqcup_j\mathcal R_j$、有限输入与输出端口，以及具有独立身份和正整数时延的有向边。逻辑时间为 $\theta\in\mathbb N$。边 $a$ 在时间 $\eta$ 发出的消息于 $\eta+\delta(a)$ 到达。

每个输入原子保留来源身份和载荷。外部原子写作 $(\mathrm{ext},i,k,p)$，内部原子写作 $(\mathrm{msg},\eta,a,p)$。节点 $v$ 在 $\theta$ 的完整原子集合记为 $B_{v,\theta}$，称为输入纤维。只有 $B_{v,\theta}\ne\varnothing$ 时产生节点作用；区域的候选集合为

$$
C=\{v\in\mathcal R_j:B_{v,\theta}\ne\varnothing\}.
$$

固定内容宽度 $d\ge1$，载荷空间取 $P=\mathbb R^{1+d}$，载荷 $(m,z)$ 含强度 $m$ 与内容 $z\in\mathbb R^d$。记 $x_+=\max(x,0)$。接收使用 $m_+$，实际发送的强度非负。缺席记为 $\bot$。数值比较使用

$$
\pi_P(m,z)=(m_+,m_+z),\qquad \pi_P(\bot)=0.
\tag{1}
$$

存在的零强度消息仍产生输入原子；缺席不产生原子。两者的数值投影相同，原始事件记录可以不同。

## 2. 接收聚合

固定 $\epsilon>0$，对 $p$ 维向量定义

$$
\mathcal N_p(x)=\frac{x}{\sqrt{\epsilon+\|x\|_2^2/p}},\qquad
\sigma(x)=\frac1{1+e^{-x}},\qquad \operatorname{SiLU}(x)=x\sigma(x).
\tag{2}
$$

向量上的标量函数逐分量作用，$\odot$ 表示逐分量乘法，方括号表示拼接。

组合为每个节点的输入端口与入边指定有限来源类别 $\operatorname{SrcClass}_v$。将有限输入集合枚举为来源与载荷 $(a_i,(m_i,z_i))$；身份不同的原子各参与一次。固定连续函数 $F_{v,a}:\mathbb R^d\to\mathbb R^d$，要求它在有界内容上有界。定义

$$
\begin{aligned}
r&=\sum_i(m_i)_+,\\
u&=\begin{cases}
\displaystyle\frac{\sum_i(m_i)_+z_i+
 \alpha_{\mathrm{agg}}\sum_i(m_i)_+F_{v,\operatorname{SrcClass}_v(a_i)}(z_i)}r,&r>0,\\
0,&r=0,
\end{cases}\\
\operatorname{Agg}_v(\theta,B)&=(r,u),\qquad X_v=\mathbb R^{1+d},\quad \alpha_{\mathrm{agg}}\ge0.
\end{aligned}
\tag{3}
$$

这里 $r$ 是接收强度之和，$u$ 是聚合内容。全部输入强度同比例缩放时，$u$ 保持，$r$ 按比例变化。空集同样得到 $(0,0)$；无输入节点由正典规则保持状态。

一种完整的来源函数是

$$
F_{v,a}(z)=B_{v,a}\operatorname{SiLU}(A_{v,a}\mathcal N_d(z)+e_{v,a}),
\tag{4}
$$

其中 $A_{v,a}\in\mathbb R^{p_a\times d}$、$B_{v,a}\in\mathbb R^{d\times p_a}$、$e_{v,a}\in\mathbb R^{p_a}$，参数有限。以下绑定给出四种聚合：

| 绑定 | 参数 |
|---|---|
| 区域共享 | $A_{v,a}=A_j,B_{v,a}=B_j,e_{v,a}=e_{j,a}$ |
| 节点独立 | $A_{v,a}=A_v,B_{v,a}=B_v$，嵌入按节点和类别指定 |
| 来源独立 | $A_{v,a}=A_{j,a},B_{v,a}=B_{j,a},e_{v,a}=e_{j,a}$ |
| 节点与来源适配 | $A_{v,a}=A_j+L^A_{v,a}R^A_{v,a}$，$B_{v,a}=B_j+L^B_{v,a}R^B_{v,a}$ |

最后一行的因子取相容形状与指定秩。聚合在压缩前引入来源差异；聚合后的函数只能使用已保留的 $u$。相同来源类别、载荷多重集和参数才保证聚合值相同。$\alpha_{\mathrm{agg}}=0$ 给出加权均值。

## 3. 状态与记忆描述

每个节点选择状态空间 $S_v$、初态 $q_v^{\mathrm{init}}$ 与接收更新

$$
\widetilde q=\operatorname{Upd}_v(q,\theta,h),\qquad h=(r,u).
\tag{5}
$$

本支线的共同采用规则是 $\kappa_j=1$：全部候选都以 $q^{\mathrm{cmp}}=\widetilde q$ 作为本次计算状态，并保留更新：

$$
\operatorname{Next}_v(q,q^{\mathrm{cmp}},\theta,h,a,c)=q^{\mathrm{cmp}}.
\tag{6}
$$

因此记忆写入不等待区域选择，未激活候选也保留自己的更新。Full 的返回值经消息影响以后的作用。Next 与区域历史不读取或重算本次 Full。

为接入下面的评分族，记忆模块提供一个描述函数

$$
\operatorname{Mem}_v(q,\theta,u)
 =(M_{v,\mathrm{short}},M_{v,\mathrm{long}},W_{v,\mathrm{short}},W_{v,\mathrm{long}}),
\tag{7}
$$

其中两个 $M$ 属于 $\mathbb R^{d_s}$，两个 $W$ 非负；另提供当前内容特征 $p_v(u)\in\mathbb R^{d_s}$。KV 中 $M$ 是时间摘要或内容检索结果，$W$ 是相应有效写入权重之和。循环模块给出自己的衰减摘要与累积权重。这些统计量的含义由各模块定义。

$\operatorname{Describe}_v(q,\theta,h)$ 把上述记忆描述与当前内容交给[区域分配教材](region-allocation-learning-note.md#1-节点向区域提供什么)，得到 $D_v$ 中的描述量。三种正典读取为

$$
\begin{aligned}
\operatorname{Read}_v^+(\widetilde q,\theta,h)&=\operatorname{Describe}_v(\widetilde q,\theta,h),\\
\operatorname{Read}_v^-(q,\theta,h)&=\operatorname{Describe}_v(q,\theta,h),\\
\operatorname{Read}_v^0(\theta,h)&=\operatorname{Describe}_v(q_v^{\mathrm{init}},\theta,h).
\end{aligned}
\tag{8}
$$

选择描述模式 $\tau_j=+$ 时，评分可看见本次写入；选 $-$ 时，评分使用旧记忆并显式接收当前 $u$；选 $0$ 时只使用当前内容与固定初态。三者的 Full 均读取 $\widetilde q$。状态模块必须定义在查询时刻如何读取旧状态，特别是逻辑时间空档内的衰减与过期。

式 (7) 为本教材评分族提供共同输入。采用其他描述空间时，需同时给出对应 Describe 与 SelStep；正典本身允许更一般的空间。

## 4. 分配、完整计算与发送

区域根据全部候选的描述量返回

$$
\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_{v\in C})
 =(A,(c_v)_{v\in C},*),\qquad
 A=\{v\in C:c_v>0\},\quad \mathsf C_v=[0,1].
\tag{9}
$$

历史空间为 $Y_j=\{*\}$。空候选返回 $(\varnothing,(),*)$。$c_v$ 是本次发送强度，各种分配的具体定义见区域分配教材。

记忆模块另提供内容函数 $G_v:S_v\times\mathbb N\times\mathbb R^d\to\mathbb R^d$。定义

$$
\begin{aligned}
\operatorname{EmitValue}_v(q^{\mathrm{cmp}},\theta,(r,u),c)
 &=\begin{cases}(c,G_v(q^{\mathrm{cmp}},\theta,u)),&c>0,\\(0,0),&c=0,\end{cases}\\
\Delta_v(p)&=\big((p)_{a\in\operatorname{Out}(v)},(p)_{o\in\operatorname{OutPort}(v)}\big),\\
\operatorname{Full}_v&=\Delta_v\circ\operatorname{EmitValue}_v.
\end{aligned}
\tag{10}
$$

只有激活节点调用 Full。它返回逐出边与逐输出端口两个值族，每个坐标均为同一载荷。数值贡献为 $(c,cG_v)$，完整内容及其残差都受同一个发送强度控制。广播在每条边复制载荷。

若节点 $v$ 的出度为 $d_v^+$，区域本次发送强度之和为 $S=\sum_vc_v$，内部边上的总强度为 $\sum_vd_v^+c_v$。节点激活数、区域强度和广播工作是三个量。

固定有限输出坐标集合 $\Lambda\subseteq\mathbb N\times\mathsf O$，从完整记录 $Z$ 取这些坐标的载荷 $(m_i,z_i)$，定义

$$
\operatorname{ReadOut}_\Lambda(Z)=
 \frac{\sum_i(m_i)_+z_i}{\max(1,\sum_i(m_i)_+)}.
\tag{11}
$$

空集读出零，单个单位载荷原样读出。读出在图外汇集，不增加图内作用。正强度输出的存在与读出向量非零分别判断，内容可以相消。

## 5. 如何组成一个模型

一份组合依次指定下列对象：

| 对象 | 必须给定的内容 |
|---|---|
| 图与时间 | 节点、区域、边身份及时延、端口、输入日程、输出坐标 |
| 接收 | 内容宽度、来源分类与 Agg 参数 |
| 记忆 | 状态、初态、Upd、Mem、当前特征 $p_v$、内容函数 $G_v$ |
| 描述与评分 | 读取模式、Describe 与 SelStep 使用的共同 $D_v$，局部和区域评分 |
| 发送 | 所选分配函数及其参数、正典容量 $K_j$ |
| 延续 | 本文 Next 与广播 Full，状态的时钟、窗口及边界恢复 |

相连节点共用载荷宽度；同一区域的描述须能进入同一个区域评分函数。不同状态宽度可先映到共同描述宽度 $d_s$。本文已定义的 KV 与循环模块可在不同区域组合；同一区域异构时还须统一描述和匹配宽度。所有函数对其声明空间都是确定的全函数。

三个图层级使用同一组 Agg、Upd、Read、SelStep、Next、Full。正时延图允许反馈；图无环时得到 TimedDAG；进一步满足区域严格分层和到达对齐时得到 SettleGraph。各图的条件由对应正典和[全连接](weighted-kv-layered-example.md)、[HB](weighted-kv-hb-lattice-example.md)实例给出。

## 6. 数值性质的条件

选择函数签名相同，仍可能具有不同的正分量、零边界和温度极限。组合须按所选函数声明需要的性质：

| 性质 | 所需的局部条件 |
|---|---|
| 精确分段继续 | 完整状态、区域历史、在途消息与原始时间可恢复，前后使用同一函数及参数 |
| 零消息删除后数值相同 | 零接收保持有效状态，零候选不影响其余评分和控制，且其发送为零 |
| 固定正温度的输入连续性 | 弱写入对有效状态影响趋零；弱候选发送和对区域的影响趋零；正接收处读取连续，有限时间内内容有界 |
| 约束分配趋向硬选择 | 上述状态与读取条件，单位外部强度、对应硬运行的严格评分条件，以及区域分配教材规定的成对选择函数 |
| 精确联合求值 | 给出完整驱动输入下返回全部规范记录的联合函数，并证明它等于逐次求值 |

KV 教材附录证明其数值命题，循环教材证明对应的状态条件。固定总强度 Attention 是完整的稠密架构；它采用自己的零输入规则。固定正温度输入连续性与趋零温度下整网比较分别陈述。

对满足 $c_v\le\mu_v=\min(1,\gamma_v r_v)$、$\gamma_v\le\Gamma_v<\infty$ 的发送，在无其他输入的长度 $L$ 单路径上，末端强度不超过 $r_0\prod_{\ell=1}^L\Gamma_\ell$。因此有限路径允许弱信号放大，也保持 $r_0\to0$ 时末端趋零。例如单候选、各步取增益 $4$ 且发送达到上限时，$0.01$ 可依次变为 $0.04,0.16,0.64,1$。区域竞争可以使实际发送低于这个上限。

## 7. 切面与联合求值

切面 $b$ 的继续状态沿用正典：

$$
Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b),
\tag{12}
$$

其中 $W_b$ 保存此前发出、在 $b$ 或以后到达的消息。下一段沿用全局时间与同一位置函数。精确继续保存原始状态；用于连续性比较的有效状态投影可能遗忘过期条目或等价表示，两种比较关系各有用途。

给定窗口内区域全部节点、全部时刻的完整输入纤维，包括确定为空的纤维，各模块可构造 BatchRegionState 与逐节点 BatchFull。前者返回实际 P/S/U 作用、全部值与右边界状态，后者返回全部正式 Full 值及展开的边消息和端口记录。KV 前缀与循环仿射复合分别给出这种契约的见证。输入完整性何时成立，由图和[分块预填充教材](timed-dag-chunk-prefill-learning-note.md)确定。

## 附录 S：名称、配置与计算工作

### S.1 配置对应

| 配置名 | 数学选择 |
|---|---|
| memory_family | kv、affine、delta：选择状态、Upd、Mem 与 $G_v$ 的完整绑定 |
| memory_read | KV 的 sum、qry；循环模块的 sum、state，见各模块教材 |
| read_mode | 正典 $\tau_j\in\{0,-,+\}$；本文完整例子默认 $+$ |
| local_score、region_score | 区域分配教材的 cat／match、ind／att |
| send_gain、query_weight | 发送增益与区域 query 的汇集权重，分别指定 |
| selection_mode | 区域分配教材附录 S.1 所列发送函数 |

其余参数包括宽度、矩阵、偏置、共享关系、窗口、时钟与位置。参数空间和状态空间随这些绑定确定。默认 KV 例子保留 sum、cat、ind、fixed、quad 及 Read$^+$ 的完整组合。函数名称对应数学定义；下游可按配置构造模型，其已支持形状和求值内核由实现声明。

配置改变可以改变参数形状、前向函数和历史状态。形状相同也不自动使旧状态等于新模型从头计算的状态；继续、重算或显式转换各自给出比较关系。

### S.2 工作量

设 $\mathcal E_C,\mathcal E_A,\mathcal E_S$ 分别为候选、激活和区域选择的时间坐标，$\mathcal M$ 为内部消息。按不重复归属的工作代价，有

$$
\mathcal W=\sum_{(v,\theta)\in\mathcal E_C}
 (C^{\mathrm{Agg}}+C^{\mathrm{Upd}}+C^{\mathrm{Read}})_{v,\theta}
 +\sum_{(j,\theta)\in\mathcal E_S}C^{\mathrm{Sel}}_{j,\theta}
 +\sum_{(v,\theta)\in\mathcal E_A}C^{\mathrm{Full}}_{v,\theta}
 +\sum_{m\in\mathcal M}C_m^{\mathrm{msg}}.
$$

共享计算计一次，缓存与读出工作计入对应项。零发送先省去本次 Full 和广播；下游若没有其他输入，还会省去整次准备。局部支持数与端到端工作之间还隔着拓扑、邻域重叠和状态成本。并行跨度另由依赖偏序决定。
