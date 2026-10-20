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

图、区域和逻辑时间沿用 [SettleGraph](../../settlegraph-learning-note.md)、[TimedDAG](../../timed-dag-region-selector-learning-note.md) 与 [PositiveDelayGraph](../../positive-delay-graph-finite-cut-learning-note.md)。这里选择它们允许的局部函数。读者只需有限集合、向量、函数与归纳法。

[区域分配](region-allocation-learning-note.md)定义评分与发送函数；[带权 KV](kv-memory-learning-note.md)、[基础循环记忆](recurrent-memory/affine-delta-learning-note.md)、[Gated DeltaNet](recurrent-memory/gated-delta-learning-note.md)和 [Mamba-2／SSD](recurrent-memory/ssd-learning-note.md)分别给出完整的状态、更新与读取。后两者共用[固定逻辑时间短卷积](recurrent-memory/causal-convolution-learning-note.md)。选定这些函数，再绑定图和时间，就得到一个确定的模型。设计取舍集中在[设计总览](../../memos/design/weighted-message-design.md)。

本支线采用接收驱动的状态更新：全部候选保留更新，区域选择历史为单点，发送控制为 $[0,1]$ 中的标量，正控制触发沿全部出边的广播。第 3—4 节给出这些选择的完整公式。它们在正典允许的函数中确定本支线的范围；稠密与稀疏发送均可在此范围内组成模型。

## 1. 消息、输入与候选

固定有限节点集 $V$、区域划分 $V=\bigsqcup_j\mathcal R_j$、有限输入端口集 $\mathsf I$ 与输出端口集 $\mathsf O$，以及具有独立身份和正整数时延的有向边。记 $\rho(v)$ 为节点所属区域，$\operatorname{In}(v),\operatorname{Out}(v)$ 为入边与出边集合，$\mathsf I_v,\operatorname{OutPort}(v)$ 为归属该节点的输入与输出端口集合。逻辑时间为 $\theta\in\mathbb N$。边 $a$ 在时间 $\eta$ 发出的消息于 $\eta+\delta(a)$ 到达。

每个输入原子保留来源身份和载荷。外部原子写作 $(\mathrm{ext},i,k,p)$，其中 $i$ 是输入端口、$k$ 是该端口的输入序号、$p$ 是载荷；内部原子写作 $(\mathrm{msg},\eta,a,p)$，其中 $\eta$ 是发送时间、$a$ 是边。节点 $v$ 在 $\theta$ 的完整原子集合记为 $B_{v,\theta}$，称为输入纤维。只有 $B_{v,\theta}\ne\varnothing$ 时产生节点作用；区域的候选集合为

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

为节点 $v$ 固定有限类别集 $\mathsf L_v$ 和来源分类函数

$$
\operatorname{SrcClass}_v:
 (\{\mathrm{ext}\}\times\mathsf I_v)
 \sqcup(\{\mathrm{msg}\}\times\operatorname{In}(v))\longrightarrow\mathsf L_v.
$$

将完整输入集合 $B$ 中的原子逐个编号。第 $i$ 个原子的载荷记为 $(m_i,z_i)$，来源 $s_i$ 取其 $(\mathrm{ext},\text{输入端口})$ 或 $(\mathrm{msg},\text{入边})$，类别为 $a_i=\operatorname{SrcClass}_v(s_i)$。分类不使用输入序号或发送时间；原子仍保留完整身份，相同类别的不同原子各参与一次聚合。

取 $\alpha_{\mathrm{agg}}\ge0$，对每个类别 $a\in\mathsf L_v$ 固定在有界集上有界的连续函数 $F_{v,a}:\mathbb R^d\to\mathbb R^d$。聚合空间取 $X_v=\mathbb R^{1+d}$，定义

$$
\begin{aligned}
r^{\mathrm{in}}&=\sum_i(m_i)_+,\\
u&=\begin{cases}
\displaystyle\frac{\sum_i(m_i)_+z_i+
 \alpha_{\mathrm{agg}}\sum_i(m_i)_+F_{v,a_i}(z_i)}{r^{\mathrm{in}}},&r^{\mathrm{in}}>0,\\
0,&r^{\mathrm{in}}=0,
\end{cases}\\
\operatorname{Agg}_v(\theta,B)&=(r^{\mathrm{in}},u).
\end{aligned}
\tag{3}
$$

这里 $r^{\mathrm{in}}$ 是接收强度之和，$u$ 是聚合内容；写出节点下标时记为 $r_v^{\mathrm{in}},u_v$。全部输入强度同乘正数时，$u$ 保持，$r^{\mathrm{in}}$ 按比例变化。空集同样得到 $(0,0)$；无输入节点由正典规则保持状态。

取正整数宽度 $p_a$ 以及矩阵 $A_{v,a}\in\mathbb R^{p_a\times d}$、$B_{v,a}\in\mathbb R^{d\times p_a}$ 和向量 $e_{v,a}\in\mathbb R^{p_a}$。一种完整的来源函数是

$$
F_{v,a}(z)=B_{v,a}\operatorname{SiLU}(A_{v,a}\mathcal N_d(z)+e_{v,a}),
\tag{4}
$$

参数均有限。令 $j=\rho(v)$，以下绑定给出四种聚合；共享矩阵的宽度须相同：

| 绑定 | 参数 |
|---|---|
| 区域共享 | $A_{v,a}=A_j,B_{v,a}=B_j,e_{v,a}=e_{j,a}$ |
| 节点独立 | $A_{v,a}=A_v,B_{v,a}=B_v$，嵌入按节点和类别指定 |
| 来源独立 | $A_{v,a}=A_{j,a},B_{v,a}=B_{j,a},e_{v,a}=e_{j,a}$ |
| 节点与来源适配 | $A_{v,a}=A_j+L^A_{v,a}R^A_{v,a}$，$B_{v,a}=B_j+L^B_{v,a}R^B_{v,a}$ |

最后一行的因子取相容形状与指定秩。聚合在压缩前引入来源差异；聚合后的函数只能使用已保留的 $u$。相同来源类别、载荷多重集和参数才保证聚合值相同。$\alpha_{\mathrm{agg}}=0$ 给出加权均值。

## 3. 状态与记忆描述

每个节点选择非空状态空间 $S_v$、初态 $q_v^{\mathrm{init}}\in S_v$ 和函数 $\operatorname{Upd}_v:S_v\times\mathbb N\times X_v\to S_v$。给定旧状态 $q$ 和聚合 $h=(r^{\mathrm{in}},u)$，候选状态为

$$
\widetilde q=\operatorname{Upd}_v(q,\theta,h).
\tag{5}
$$

本次选择的激活指示记为 $a\in\{0,1\}$，发送控制记为 $c\in[0,1]$。本支线的共同采用规则是 $\kappa_j=1$：全部候选都以 $q^{\mathrm{cmp}}=\widetilde q$ 作为本次计算状态，并保留更新：

$$
\operatorname{Next}_v(q,q^{\mathrm{cmp}},\theta,h,a,c)=q^{\mathrm{cmp}}.
\tag{6}
$$

因此记忆写入不等待区域选择，未激活候选也保留自己的更新。Full 的返回值经消息影响以后的作用。Next 与区域历史不读取或重算本次 Full。

固定正整数描述宽度 $d_s$。记忆模块提供两个向量 $M_{v,\mathrm{short}},M_{v,\mathrm{long}}\in\mathbb R^{d_s}$ 和两个非负统计量 $W_{v,\mathrm{short}},W_{v,\mathrm{long}}$，组成函数

$$
\operatorname{Mem}_v(q,\theta,u)
 =(M_{v,\mathrm{short}},M_{v,\mathrm{long}},W_{v,\mathrm{short}},W_{v,\mathrm{long}}),
\tag{7}
$$

模块另提供当前内容特征 $p_v(u)\in\mathbb R^{d_s}$。KV 中 $M$ 是时间摘要或内容检索结果，$W$ 是相应有效写入权重之和。循环模块可提供衰减摘要或矩阵查询；Gated DeltaNet 与 SSD 的 state 描述用短期摘要和矩阵读出分别占据两个通道。$W$ 的含义由各模块定义，循环的接收写入量不表示矩阵中的可恢复信息量。

为每个节点指定描述空间 $D_v$ 和函数 $\operatorname{Describe}_v:S_v\times\mathbb N\times X_v\to D_v$。[区域分配教材](region-allocation-learning-note.md#1-节点向区域提供什么)用上述记忆描述与当前内容定义两组具体的 $D_v$ 和 Describe。给定其中一组，三种正典读取为

$$
\begin{aligned}
\operatorname{Read}_v^+(\widetilde q,\theta,h)&=\operatorname{Describe}_v(\widetilde q,\theta,h),\\
\operatorname{Read}_v^-(q,\theta,h)&=\operatorname{Describe}_v(q,\theta,h),\\
\operatorname{Read}_v^0(\theta,h)&=\operatorname{Describe}_v(q_v^{\mathrm{init}},\theta,h).
\end{aligned}
\tag{8}
$$

选择描述模式 $\tau_j=+$ 时，评分可看见本次写入；选 $-$ 时，评分使用旧记忆并显式接收当前 $u$；选 $0$ 时只使用当前内容与固定初态。三者的 Full 均读取 $\widetilde q$。状态模块必须定义在查询时刻如何读取旧状态，特别是逻辑时间空档内的衰减与过期。

式 (7) 是当前评分族所用的描述接口。状态模块分别解释 short、long 两个通道及其统计量；通道名称不要求状态内部保存两个副本。其他记忆可给出同型描述以复用该评分族，或同时定义新的 Describe 与 SelStep。

## 4. 分配、完整计算与发送

区域历史空间取 $Y_j=\{*\}$，控制空间取 $\mathsf C_v=[0,1]$。给定候选描述 $d_v\in D_v$，所选分配函数确定每个候选的发送强度 $c_v$；激活集合为 $\mathcal A=\{v\in C:c_v>0\}$。区域返回

$$
\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_{v\in C})
 =(\mathcal A,(c_v)_{v\in C},*).
\tag{9}
$$

空候选返回 $(\varnothing,(),*)$。各种分配及其激活数量容量见区域分配教材 §2。

完整内容由函数 $G_v:S_v\times\mathbb N\times\mathbb R^d\to\mathbb R^d$ 给出。历史读取与读出后的内容变换分别组成这个函数；KV 与循环教材各自给出一套读取加前馈残差的完整绑定。记忆状态、描述读取和内容函数分别声明，允许共享参数。定义

$$
\begin{aligned}
\operatorname{EmitValue}_v(q^{\mathrm{cmp}},\theta,(r^{\mathrm{in}},u),c)
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
| 记忆 | 状态、初态、Upd、Mem、当前特征 $p_v$ |
| 完整内容 | 历史读取及随后变换组成的 $G_v$，与记忆模块的参数共享关系 |
| 描述与评分 | 读取模式、Describe 与 SelStep 使用的共同 $D_v$，局部和区域评分 |
| 发送 | 所选分配函数及其参数、正典容量 $K_j$ |
| 延续 | 本文 Next 与广播 Full，状态的时钟、窗口及边界恢复 |

相连节点共用载荷宽度；同一区域的描述须能进入同一个区域评分函数。不同状态宽度可先映到共同描述宽度 $d_s$。本文已定义的 KV 与循环模块可在不同区域组合；同一区域异构时还须统一描述和匹配宽度。所有函数对其声明空间都是确定的全函数。

三个图层级使用同一组 Agg、Upd、Read、SelStep、Next、Full。正时延图允许反馈；图无环时得到 TimedDAG；进一步满足区域严格分层和到达对齐时得到 SettleGraph。[全连接分层](../../topologies/fully-connected-layered.md)与 [HB-Lattice](../../topologies/hb-lattice.md)分别给出独立的图与时间定义；[完整实例](../../README.md#具体拓扑与完整实例)将它们与本支线的局部函数绑定。

## 6. 数值性质的组合

### 6.1 比较对象与局部条件

固定有限正时延图、有限切面 $B$、外部输入槽及其原始时间、全部参数和初态。外部槽按端口与输入序号对齐，内部消息按边与发送时间对齐，缺席槽的 $\pi_P$ 取零。为每个状态模块指定在时刻 $\theta$ 的有效状态投影

$$
e_{v,\theta}=\pi_{v,\theta}(q_v).
$$

它取值于固定的有限维向量空间，可随节点和比较时刻变化。KV 用窗口内的加权条目，循环模块用同一时刻的有效矩阵和摘要；带短卷积的模块还包括按原始时间对齐并补零的有效缓存。该投影只用于数值比较；精确记录与分段继续仍使用完整状态。

下面三个命题要求每个状态与内容模块满足以下条件，均在固定有限时间范围内讨论：

1. **有界性。** 有界接收内容和强度产生有界的有效状态、记忆描述、当前特征和完整内容 $G_v$。界可依赖参数和时间范围，在所比较的温度族上统一。
2. **零接收中性。** 在固定时间槽插入一次零接收，保持当前及以后时刻的有效状态和读取结果；空槽也按保持保存状态处理。
3. **更新连续性。** 旧有效状态收敛、$r^{\mathrm{in},(n)}\to r^{\mathrm{in}}$、$u^{(n)}$ 有界，且在 $r^{\mathrm{in}}>0$ 时 $u^{(n)}\to u$，则更新后的有效状态及其随后按固定时间推进的投影收敛。$r^{\mathrm{in}}=0$ 时极限为该槽不发生接收的状态。
4. **读取连续性。** 有效状态与当前内容收敛时，Mem、当前特征和 $G_v$ 收敛；Read 的旧状态、新状态和初态分别按第 3 节使用。正极限接收处因而具有连续的描述与增益。

[KV 附录 A](kv-memory-learning-note.md#附录-a局部性质的证明)、[基础循环附录 A](recurrent-memory/affine-delta-learning-note.md#附录-a状态性质的证明)、[Gated DeltaNet 附录 A](recurrent-memory/gated-delta-learning-note.md#附录-a局部性质的证明)与 [SSD 附录 A](recurrent-memory/ssd-learning-note.md#附录-a局部性质的证明)分别验证这些条件；短卷积的固定时间引理由对应部件教材证明。各节点可使用不同模块，只需第 5 节的类型相容。

### 6.2 零消息与正温度输入

以下沿用[区域分配 §1](region-allocation-learning-note.md#1-节点向区域提供什么)的接收量 $w_v$、有界增益 $\gamma_v$、接收相关发送量 $\mu_v$ 和评分函数，以及该文 §2 定义的发送函数。区域 query 按 $\mu_v$ 或 $w_v$ 汇集。零接收候选对共同 query 无贡献，正接收处评分连续；有界描述给出有界评分。

**命题 1：零消息删除。** 各区域采用约束分配、直接 Attention、基权重为 $\mu$ 的固定总强度 Attention、区域总量分配、按比例分配或硬选择时，增加或删除零强度消息保持消息数值投影、有效状态和 ReadOut。把零控制的 Full 及其零广播显式计算，也保持这些数值。

**命题 2：正温度输入连续性。** 各区域采用约束分配、直接 Attention、区域总量分配或按比例分配。若外部输入的 $\pi_P$ 收敛、内容一致有界，所使用的温度各自趋向正值，则切面以前的消息投影、有效状态及 ReadOut 收敛到极限输入的运行。

各命题允许区域之间采用该命题所列的不同发送函数。零消息删除比较精确为零的消息；输入连续性还比较正接收趋零的极限。固定总强度 $a=\mu$ 在单候选、$\mu=\varepsilon>0$ 时始终发送 $1$，到 $\mu=0$ 时发送 $0$，因此满足命题 1 而一般不满足命题 2。

取相同评分，向一个正接收候选所在区域加入一个零接收候选。固定总强度 $a=\mu$ 的分配由 $(1)$ 变为 $(1,0)$；$a=1$ 则变为 $(1/2,1/2)$，消息数值因而改变。两种固定总强度函数均可按第 5、7 节组成模型并精确继续。

对满足 $c_v\le\mu_v=\min(1,\gamma_v r_v^{\mathrm{in}})$、$\gamma_v\le\Gamma_v<\infty$ 的发送，在无其他输入的长度 $L$ 单路径上，末端强度不超过 $r_0^{\mathrm{in}}\prod_{\ell=1}^L\Gamma_\ell$。有限路径允许弱信号放大，同时保持 $r_0^{\mathrm{in}}\to0$ 时末端趋零。例如单候选、各步取增益 $4$ 且发送达到上限时，$0.01$ 可依次变为 $0.04,0.16,0.64,1$。区域竞争可以使实际发送低于这个上限。

### 6.3 单位输入的软硬极限

固定同一外部输入，全部外部强度为 $1$。一份运行在每个区域使用[约束分配](region-allocation-learning-note.md#21-约束分配)，正则形状固定；另一份使用[硬选择](region-allocation-learning-note.md#27-硬选择)。两份运行使用相同的评分、增益、$k_j,\eta_j$、记忆和内容函数，分别从相同初态开始。正典容量在前者取 $K_j=|\mathcal R_j|$，后者取 $K_j=k_j$。

**命题 3：整网软硬收敛。** 假设硬运行在切面以前的每次区域选择满足[区域分配 §5.1](region-allocation-learning-note.md#51-一次约束分配)的评分条件。约束运行的各区域温度共同趋零时，其消息投影、有效状态和 ReadOut 收敛到硬运行。不同区域可以使用不同的趋零温度序列及不同的固定正则形状。

硬运行的每条实际消息强度为 $1$，故接收强度是非负整数；$\gamma_v\ge1$ 使其 $w_v,\mu_v$ 取 $0$ 或 $1$。软运行中的上限可以介于零和一之间，并随整网消息一起趋向上述端点。固定某些 $0<\mu_v<1$ 的上限只降低温度时，应使用区域分配教材的局部极限及反例。

**推论：充分小正温度的精确运行。** 在命题 3 的条件下，若每个区域的正则为 quad 或固定 $\alpha>1$ 的 ent，则存在 $\tau_*>0$，使所有区域温度均满足 $0<\tau_{\mathrm{sel},j}\le\tau_*$ 时，两份运行在切面以前的实际作用支持、全部作用结果、原始状态、消息与端口记录完全相同，切面继续状态也相同。

阈值 $\tau_*$ 依赖所固定的参数、输入和有限时间范围。不同输入可有不同阈值，训练改变参数后也需重新判断。Shannon 与 bern 的正温度解一般只有数值收敛；本推论使用 quad 与 ent 的有限响应阈值。

这些结论适用于固定稀疏或稠密图、多区域以及有限时间内的正时延反馈。梯度、训练收敛和无限时域稳定性各需自己的分析。证明见附录 A。

### 6.4 发送规则的性质对照

下表沿用 §6.1 的局部条件与各命题的比较对象；“适用”包含相应的温度、输入与评分条件。

| 发送规则 | 零消息删除（命题 1） | 正温度输入连续性（命题 2） | 软硬比较中的角色（命题 3） |
|---|---|---|---|
| 约束分配 | 适用 | 适用 | 软端 |
| 直接 Attention，两种基权重 | 适用 | 适用 | 未纳入 |
| 固定总强度 Attention，$a=\mu$ | 适用 | 一般不成立 | 未纳入 |
| 固定总强度 Attention，$a=1$ | 一般不成立 | 一般不成立 | 未纳入 |
| 区域总量分配 | 适用 | 适用 | 未纳入 |
| 按比例分配 | 适用 | 适用 | 未纳入 |
| 硬选择 | 适用 | 未纳入 | 硬端 |

硬选择可在评分边界不连续。命题 3 只比较约束分配与配对硬选择；quad 和固定 $\alpha>1$ 的 ent 还满足其正温度精确性推论。其他发送函数的温度极限需按自身定义分析。

## 7. 切面与联合求值

切面 $b$ 的继续状态沿用正典：

$$
Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b),
\tag{12}
$$

其中 $W_b$ 保存此前发出、在 $b$ 或以后到达的消息。下一段沿用全局时间与同一位置函数。精确继续保存原始状态；用于连续性比较的有效状态投影可能遗忘过期条目或等价表示，两种比较关系各有用途。

给定窗口内区域全部节点、全部时刻的完整输入纤维，包括确定为空的纤维，各模块可构造 BatchRegionState 与逐节点 BatchFull。前者返回实际 P/S/U 作用、全部值与右边界状态，后者返回全部正式 Full 值及展开的边消息和端口记录。KV 前缀与循环仿射复合分别给出这种契约的见证；Gated DeltaNet 与 SSD 先由完整驱动计算短卷积，再求矩阵递归。输入完整性何时成立，由图和[分块预填充教材](../../timed-dag-chunk-prefill-learning-note.md)确定。

## 附录 A：组合定理的证明

### A.1 有限槽与聚合

固定切面以前，每条边的每个发送时间至多有一个槽，输入槽也有限。把缺席按零投影补齐，得到共同的有限比较空间。正时延使时间 $\theta$ 的内部输入只来自更早发送。

若输入投影收敛，则接收强度 $r^{\mathrm{in}}$ 收敛。正极限强度的单条内容可由 $(m,mz)$ 相除恢复；零极限强度的有界内容和来源项对加权和的贡献趋零。故 $r^{\mathrm{in},*}>0$ 时聚合内容 $u\to u^*$；$r^{\mathrm{in}}\to0$ 时只需 $u$ 有界。有限槽、发送强度不超过 $1$ 及 §6.1 的局部有界性，沿时间给出与所比较温度无关的有限时间界。

### A.2 零消息与正温度

**命题 1。** 零消息不改变 Agg 的加权和。只含零输入的候选保持有效状态，$w=\mu=0$，对共同 query 无贡献。固定总强度 $a=\mu$ 中，这些坐标对归一化分母无贡献，其他份额保持；其余所列分配也忽略这些零接收坐标，硬排序只使用有效候选。零控制的载荷投影为零。按时间归纳，增加或删除这些原子及其后继零广播保持全部所述数值。原始事件支持可以不同。$\square$

**命题 2。** 假设此前消息投影和有效状态已收敛。A.1 与 §6.1 的更新条件给出当前有效状态收敛；正极限接收处的描述、增益与评分收敛。两种 query 权重均随接收趋零，消失候选对共同 query 的影响趋零。

约束分配使用[区域分配附录 A.1](region-allocation-learning-note.md#a1-约束解的连续性)，其余函数使用该文附录 A.3，得到 $c_v\to c_v^*$，并在接收趋零处得到 $c_v\to0$。若 $c_v^*>0$，接收极限为正，读取条件给出 $G_v\to G_v^*$。若 $c_v^*=0$，有界性给出 $(c_v,c_vG_v)\to0$。所以本步消息投影收敛；Next 保留相应更新，推进到下一时间。初态相同启动归纳，有限读出和式及正分母保持收敛。$\square$

### A.3 单位输入与温度极限

**命题 3。** 从单位外部输入开始归纳：若更早硬发送强度为 $1$，当前接收是非负整数，故 $\mu\in\{0,1\}$；硬选择的每个正控制又为 $1$。这给出整个硬运行的二元上限。

比较约束运行与该硬运行。此前消息和有效状态收敛时，A.1 与局部更新、读取条件使当前上限和正极限接收处评分收敛。区域分配 §5.1 的评分条件保证极限线性问题有唯一解，且为对应硬向量；该文附录 A.1 的零温结论遂给出控制收敛。再使用 A.2 对发送和状态的归纳即可。每步仅用更早逻辑时间，故有限时间的反馈和异构记忆均被包含。$\square$

### A.4 充分小正温度的精确性

**证明推论。** 记硬运行在切面以前的区域选择事件集合为 $E$。它是有限集；每个事件的有效上限均为 $1$。由[区域分配 §5.3](region-allocation-learning-note.md#53-正温度的精确性)，每个事件 $e\in E$ 有一个 $\delta_e>0$，使固定该次硬输入的约束分配在 $0<\tau\le\delta_e$ 时精确等于硬向量。有效候选至多一个时可任取正界。$E$ 非空时取 $\tau_*=\min_{e\in E}\delta_e$，否则取 $\tau_*=1$。

沿逻辑时间归纳。初态和外部输入相同。若此前原始状态与实际消息相同，则当前完整纤维、候选、Upd、Read、增益和评分相同；当前上限也与硬运行相同。温度界使控制与激活集合精确相同，Next 和 Full 因而给出相同原始状态、消息及端口记录。没有新增候选，因为当前消息的存在性已经相同。归纳得到全部所述记录相同；切面状态与在途消息从这些记录取得，因而也相同。$\square$

## 附录 S：名称、配置与计算工作

### S.1 配置对应

| 配置名 | 数学选择 |
|---|---|
| memory_family | kv、affine、delta、gated_delta、ssd：选择各模块已给出的状态、读取与默认内容函数绑定；各职责见 §3—5 |
| memory_read | KV 的 sum、qry；各循环模块的 sum、state。state 的具体查询与通道含义由所选模块定义 |
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
