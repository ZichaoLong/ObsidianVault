---
type: mathematical-learning-note
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - semantic-anchor
  - local-semantics
  - learning-note
  - memory
  - sparse-activation
---

# 带权 KV：局部计算与区域选择

本文从节点收到的一组消息出发，依次定义聚合、记忆写入、评分、共同选择和发送。节点保存自己的记忆；同一区域共同决定各候选的发送强度。选择函数可以让全部有效候选参与，也可以令部分候选的发送强度精确为零，从而跳过其完整计算。以下只需向量、函数、有限求和与凸优化的基本知识。

第 1—6 节建立一个完整模型并手算其结果；第 7 节给出可替换的局部函数；第 8—9 节讨论导数、连续性和软硬选择的极限关系。第 10 节将这些函数纳入正典接口，说明拓扑组合、联合求值与分段继续。长证明和计算表示分别放在附录 A、S。

[全连接分层实例](weighted-kv-layered-example.md)与 [HB-Lattice 实例](weighted-kv-hb-lattice-example.md)给出具体的图与时间安排。[机制备忘](memos/architecture/selector-and-memory.md)讨论设计取舍，[训练实验](memos/learning-systems/weighted-kv-experiment-plan.md)给出比较方案，[实现核对](weighted-kv-implementation-checks.md)列出程序应验证的性质。

## 1. 节点、消息与候选

### 1.1 图、区域与时间

固定有限非空节点集 $V$，并将它划分为非空区域 $\mathcal R_j$，$j\in J$。记 $\rho(v)$ 为节点 $v$ 所在区域的编号。图有有限条有向边，每条边有自己的名字、源节点、目标节点及正整数时延。源节点在逻辑时间 $\eta$ 发出的消息，经过时延 $\delta$ 后在 $\eta+\delta$ 到达。逻辑时间取自 $\mathbb N=\{0,1,2,\ldots\}$。

有限输入端口集记为 $\mathsf I$，有限输出端口集记为 $\mathsf O$。输入端口向指定节点提供外部输入，输出端口接收指定节点的结果。$\operatorname{Out}(v)$ 和 $\operatorname{OutPort}(v)$ 分别表示节点 $v$ 的出边集合和输出端口集合。一次运行固定图、区域、各端口的输入时刻及全部函数参数。每个节点的记忆初始为空。

在时间 $\theta$，节点 $v$ 收集本时刻到达的全部输入。每项输入保留来源和值：外部输入记为 $(\mathrm{ext},i,k,p)$，其中 $i$ 是端口、$k$ 是该端口的输入序号、$p$ 是值；内部消息记为 $(\mathrm{msg},\eta,a,p)$，其中 $a$ 是入边、$\eta$ 是发送时间。这些带身份的输入称为原子，全部可能原子的集合记为 $\mathsf{Atom}_v$。

记 $B_{v,\theta}\subseteq\mathsf{Atom}_v$ 为本次完整输入集合，在正典中称为输入纤维。身份不同的原子即使值相同，也分别保留。$B_{v,\theta}\ne\varnothing$ 时，节点称为本时刻的候选；区域 $j$ 的候选集合为

$$
C=\{v\in\mathcal R_j:B_{v,\theta}\ne\varnothing\}.
$$

区域在本时刻的输入全部确定后，对这些候选作一次共同选择。没有输入的节点保持原状态。正时延保证当前输入只依赖更早的内部发送。

### 1.2 消息强度与内容

固定正整数内容宽度 $d$。消息值空间为 $P=\mathbb R^{1+d}$，一个值写作 $(m,z)$，其中 $m$ 是强度，$z\in\mathbb R^d$ 是内容。对实数 $x$ 记 $x_+=\max(x,0)$。接收函数使用 $m_+$，从而在整个 $P$ 上有定义；本模型实际发出的强度非负。

用 $\bot$ 表示确定没有值。数值比较使用

$$
\pi_P(m,z)=(m_+,m_+z),
\qquad \pi_P(\bot)=0\in\mathbb R^{1+d}.
\tag{1}
$$

因此消息的内容贡献是 $m_+z$。存在的零强度消息 $(0,z)$ 仍使接收者成为候选；缺席 $\bot$ 不提供输入原子。两者在上述数值投影中均为零。第 9 节用这个投影讨论弱消息消失时的连续性。

### 1.3 归一化与参数

固定 $\epsilon>0$。对宽度为 $p$ 的实向量定义 RMS 归一化，并定义两个标量函数：

$$
\mathcal N_p(x)=\frac{x}{\sqrt{\epsilon+\|x\|_2^2/p}},
\qquad
\sigma(x)=\frac1{1+e^{-x}},
\qquad
\operatorname{SiLU}(x)=x\,\sigma(x).
\tag{2}
$$

对向量使用 $\sigma$ 或 SiLU 时，分别作用于它的每个分量。$\odot$ 表示对应分量相乘，方括号表示向量拼接。下文矩阵、偏置和尺度均为有限实参数；各宽度在使用时取正整数。相连节点使用相同的内容宽度 $d$，其余宽度可按区域声明。

## 2. 聚合消息与写入记忆

### 2.1 聚合函数 Agg

对区域 $j$，固定有限来源类别集，以及从每个节点输入端口或入边标签到来源类别的映射 $\operatorname{SrcClass}_v$。具体类别由组合配置给出，不依赖当前候选数或消息到达次序。不同来源可以使用同一类别，所有输入原子仍分别参与聚合。

固定聚合中间宽度 $p_a$。区域共享 $A_j\in\mathbb R^{p_a\times d}$、$B_j\in\mathbb R^{d\times p_a}$ 和来源嵌入 $e_{j,a}\in\mathbb R^{p_a}$，固定尺度 $\alpha_{\mathrm{agg}}\ge0$。对 $z=(\mathrm{ext},i,k,p)$ 取来源标签 $(\mathrm{ext},i)$，对 $z=(\mathrm{msg},\eta,a,p)$ 取 $(\mathrm{msg},a)$，记为 $\operatorname{source}(z)$。对任意有限 $B\subseteq\mathsf{Atom}_v$，将各原子的来源和值记为 $(a_i,(m_i,z_i))$；这个枚举只用于求和，仍保留所有原子。定义

$$
\begin{aligned}
r&=\sum_i(m_i)_+,\\
\bar z&=\frac{\sum_i(m_i)_+z_i}{r}
&& (r>0),\\
\bar f&=\frac{\sum_i(m_i)_+
  \operatorname{SiLU}(A_j\mathcal N_d(z_i)+e_{j,\operatorname{SrcClass}_v(a_i)})}{r}
&& (r>0),\\
u&=\begin{cases}
\bar z+\alpha_{\mathrm{agg}}B_j\bar f,&r>0,\\
0,&r=0,
\end{cases}
\qquad h=(r,u).
\end{aligned}
\tag{3}
$$

当 $r=0$ 时直接取 $u=0$。把聚合结果空间记为 $X_v=P=\mathbb R^{1+d}$，以 $\mathcal P_{\mathrm{fin}}$ 表示有限子集的集合，并令

$$
\operatorname{Agg}_v:\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)\to X_v,
\qquad \operatorname{Agg}_v(\theta,B)=(r,u).
$$

空集同样由式 (3) 得到 $(0,0)$；没有输入的节点保持原状态。来源分类可忽略不需要的时间坐标，原子和完整记录仍保留这些坐标。

均值残差保留内容尺度；非线性来源项使相反内容、不同来源的组合不必因均值相同而不可区分。它将输入内容压缩为 $d$ 维摘要，部分消息信息会丢失。$\alpha_{\mathrm{agg}}=0$ 恢复普通加权均值。

这里 $r$ 是接收强度之和，$u$ 是聚合内容；同时讨论多个节点时写为 $r_v,u_v$。全体输入强度同时乘一个正数时，$u$ 保持，$r$ 按该比例变化。零强度项对两个加权和的贡献为零。

共享的 $A_j,B_j$ 让节点在共同特征空间解释来源，减少参数，并在输入相同时允许复用聚合。来源嵌入进入非线性之前，能改变不同来源的响应，但仍共享投影方向。稀疏图中不同节点收到不同邻域的消息，即使参数共享，内容和历史也会分化。

### 2.2 写入函数 Upd

固定记忆描述宽度 $d_s$、KV 适配秩 $r_a$、Attention 头数 $H_{\mathrm{att}}$ 和每头宽度 $d_h$，满足 $H_{\mathrm{att}}d_h=d$。

节点状态空间 $S_v$ 是全部有限序列

$$
q=((\xi_i,k_i,\nu_i,p_i,w_i))_{i=1}^N,
\quad \xi_i\in\mathbb N,\quad
k_i,\nu_i\in\mathbb R^d,\quad
p_i\in\mathbb R^{d_s},\quad w_i\ge0.
\tag{4}
$$

$k_i$ 是匹配记忆所用的 key，$\nu_i$ 是读取时被加权的 value。它们分别分成 $H_{\mathrm{att}}$ 个 $d_h$ 维子向量，记为 $k_{i,h},\nu_{i,h}$；$p_i$ 是供后续评分使用的摘要特征，$w_i$ 是独立的写入权重，$\xi_i$ 是原始逻辑时间。初态为空；实际运行中每节点每逻辑时间至多写一项。

区域共享基座 $W_j^{\mathrm{KV}}\in\mathbb R^{2d\times d}$，节点各有 $U_v\in\mathbb R^{2d\times r_a}$、$V_v^{\mathrm{ad}}\in\mathbb R^{r_a\times d}$ 与 $W_v^S\in\mathbb R^{d_s\times d}$。定义

$$
\begin{aligned}
[k_v(u);\nu_v(u)]
  &=(W_j^{\mathrm{KV}}+U_vV_v^{\mathrm{ad}})\mathcal N_d(u),\\
p_v(u)&=W_v^S\mathcal N_d(u),
\qquad w(r)=\min(1,r_+).
\end{aligned}
\tag{5}
$$

共享基座给出区域共同的 KV 投影，节点差异由秩至多为 $r_a$ 的乘积提供。相同输入的基座投影可共同求值，各节点仍保存私有条目。取 $r_a=d$、$W_j^{\mathrm{KV}}=0$、$V_v^{\mathrm{ad}}=I_d$ 与 $U_v=[W_v^K;W_v^V]$，即可表示任意独立的 K、V 投影。式 (5) 定义写入；Attention 读取由第 5.2 节给出。

为每节点固定窗口 $T_v\in\mathbb N_{\ge1}\cup\{\infty\}$，以原始逻辑时间计量。定义遮罩

$$
\chi_{v,\theta}(\xi)=\mathbf1[0\le\theta-\xi<T_v].
$$

$q|_{v,\theta}$ 表示按原序保留 $\chi_{v,\theta}(\xi_i)=1$ 的条目。接收更新是

$$
\widetilde q=\operatorname{Upd}_v(q,\theta,(r,u))
=\begin{cases}
q|_{v,\theta}\mathbin{\oplus}
  (\theta,k_v(u),\nu_v(u),p_v(u),w(r)),&r>0,\\
q,&r\le0.
\end{cases}
\tag{6}
$$

$\oplus$ 表示追加。每次正接收只写一条，KV 内容不预乘 $w$；接收强度为零时保留原序列。是否执行本节点 Full 不参与写入决定。

所有读取同样使用 $\chi_{v,\theta}$。没有候选或只有零强度输入时，保存序列可以含已过期条目，但它们不会再被读出；下一次正接收再清理。有限 $T_v$ 下，由每逻辑时间至多写一项，实际保存序列始终至多含 $T_v$ 项。$T_v=\infty$ 保留全部接收历史，在任意有限时间范围内仍只有有限项。历史覆盖范围取决于该节点实际收到的内容。

窗口按原始写入时间定义。一条强度趋零的输入会产生权重趋零的新条目；窗口内已有条目的保留仍由各自的写入时间决定。

## 3. 从记忆得到评分与发送上限

### 3.1 短期与长期摘要

对每节点取 $\beta_{v,\mathrm{long}}=0$、$\beta_{v,\mathrm{short}}>0$，均按逻辑时间计量。固定节点后省略部分下标，对 $a\in\{\mathrm{short},\mathrm{long}\}$ 定义

$$
\begin{aligned}
\omega_i^a(\theta)&=\chi_{v,\theta}(\xi_i)w_i
 e^{-\beta_{v,a}(\theta-\xi_i)_+},\\
W_a(q,\theta)&=\sum_i\omega_i^a(\theta),\\
M_a^{\mathrm{sum}}(q,\theta)&=
 \frac{\sum_i\omega_i^a(\theta)p_i}{\max(1,W_a(q,\theta))}.
\end{aligned}
\tag{7}
$$

短期摘要突出近期接收，长期摘要覆盖整个窗口；分母使最后一条弱记忆消失时摘要也趋零。摘要本身只按时间和写入权重汇集，当前内容在后续评分中与它交互。

### 3.2 局部评分

本节取 $M_a=M_a^{\mathrm{sum}}$，$a\in\{\mathrm{short},\mathrm{long}\}$。当前内容、接收强度、记忆摘要及记忆权重之和共同参与评分。

固定评分隐藏宽度 $d_r$，取 $W_v^r\in\mathbb R^{d_r\times(d+4d_s+3)}$、$a_v,b_v^r\in\mathbb R^{d_r}$、$b_v\in\mathbb R$，均按节点独立。定义

$$
\begin{aligned}
f_v(q,\theta,r,u)=
\big[&\mathcal N_d(u);\ \log(1+r_+);\
 M_{\mathrm{short}};\ M_{\mathrm{long}};\\
 &\log(1+W_{\mathrm{short}});\
 \log(1+W_{\mathrm{long}});\\
 &p_v(u)\odot M_{\mathrm{short}};\
 p_v(u)\odot M_{\mathrm{long}}\big],\\
s_v^{\mathrm{cat}}(q,\theta,r,u)
 &=b_v+a_v^\top
   \operatorname{SiLU}(W_v^r f_v(q,\theta,r,u)+b_v^r).
\end{aligned}
\tag{8}
$$

$f_v$ 的宽度为 $d+4d_s+3$。这是拼接特征上的单隐藏层网络；不同列的权重分别解释内容、强度、记忆权重之和与交互项。

记本节的局部评分为 $s_v^{\mathrm{loc}}=s_v^{\mathrm{cat}}$。它是一个实数，用于比较候选；完整发送内容将在选择之后计算。

### 3.3 每个节点的发送上限

固定有限常数 $\gamma_{\max}\ge1$，为每个节点选择增益 $1\le\gamma_v\le\gamma_{\max}$。定义

$$
\mu_v(q,\theta,r,u)=\min(1,\gamma_v r_+).
\tag{9}
$$

$\mu_v$ 是节点 $v$ 本次允许发送的最大强度，范围为 $[0,1]$。例如接收强度为 $0.2$、增益为 $2$ 时，发送上限为 $0.4$。它与写入权重 $w(r)$ 各有用途：写入按接收强度计量，发送允许使用有界增益。

这一函数保留 $q,\theta,u$ 自变量，便于第 7.5 节代入依赖内容的增益。固定增益可以直接给定，也可以用 $\gamma_v=1+(\gamma_{\max}-1)\sigma(\zeta_v)$ 参数化。两种情况下都有 $\mu_v\le\gamma_{\max}r_+$；接收强度趋零时发送上限趋零，接收强度至少为 $1$ 时发送上限等于 $1$。

### 3.4 描述函数 Read

每个候选把发送上限和局部评分交给区域，组成描述量：

$$
D_v^{\mathrm{ind}}=[0,1]\times\mathbb R,\qquad
\operatorname{Describe}_v^{\mathrm{ind}}(q,\theta,(r,u))
=(\mu_v(q,\theta,r,u),s_v^{\mathrm{loc}}(q,\theta,r,u)).
$$

这里 ind 表示各节点独立产生评分。本节令 $D_v=D_v^{\mathrm{ind}}$、$\operatorname{Describe}_v=\operatorname{Describe}_v^{\mathrm{ind}}$。记 $h=(r,u)$，读取更新后的记忆：

$$
\operatorname{Read}_v^+(\widetilde q,\theta,h)
=\operatorname{Describe}_v(\widetilde q,\theta,h).
\tag{10}
$$

上标 $+$ 表示读取本次写入后的状态。区域收到每个候选的 $(\mu_v,s_v)$，其中 $s_v=s_v^{\mathrm{loc}}$。第 7.6 节会给出传递更多描述信息的区域 Attention 评分；它沿用同一个 Read 函数形式。

## 4. 区域如何选择节点

### 4.1 软选择函数

固定区域 $j$ 的一次选择，输入为候选集合 $C\subseteq\mathcal R_j$ 及其描述量。以下 $c_v$ 表示候选 $v$ 本次发送的强度，它对应正典接口中的控制量。每个候选分别满足

$$
0\le c_v\le\mu_v.
$$

向量 $c=(c_v)_{v\in C}$ 按节点编号，每个分量对应一个候选。定义

$$
C_{\mathrm{eff}}=\{v\in C:\mu_v>0\},\qquad
M_j=\sum_{v\in C}\mu_v,\qquad
b_j=\min(1,M_j),\qquad S=\sum_{v\in C}c_v.
$$

$C_{\mathrm{eff}}$ 中的节点称为有效候选，即有正发送上限的候选；$M_j$ 是所有候选的发送上限之和；$S$ 是本次发送强度之和。每个候选在这个和中计一次，广播到多条出边的副本另按图计数。模型要求 $S\ge b_j$，从而在 $C_{\mathrm{eff}}$ 非空时保证至少一个候选发送。

固定整数 $1\le k_j\le|\mathcal R_j|$，用它限制 $S$ 的上限。另固定评分阈值 $\eta_j\in\mathbb R$ 和温度 $\tau_{\mathrm{soft}}>0$，记 $t_v=s_v-\eta_j$。本节使用二次正则

$$
R(c;\mu)=R^{\mathrm{quad}}(c;\mu)=-\frac12\sum_{v\in C}c_v^2.
\tag{11}
$$

软选择是下面优化问题的解：

$$
\begin{aligned}
F(\mu)&=\left\{c:0\le c_v\le\mu_v,\quad b_j\le\sum_{v\in C}c_v\le k_j\right\},\\
c^{\tau_{\mathrm{soft}}}
  &=\mathop{\arg\max}_{c\in F(\mu)}
  \left\{\sum_{v\in C}t_vc_v+
    \tau_{\mathrm{soft}}R(c;\mu)\right\}.
\end{aligned}
\tag{12}
$$

由 $b_j\le M_j$ 与 $b_j\le1\le k_j$，可行集非空；它还紧且凸。目标严格凹，故解存在且唯一。温度控制正则项相对于评分项的强度；第 7.7 节给出另外两种正则。

以下写 $c=c^{\tau_{\mathrm{soft}}}$。本模型激活发送强度为正的候选。区域不保存额外选择历史，以单点 $*$ 表示历史值，选择函数 SelStep 返回

$$
A=\{v\in C:c_v>0\},\qquad (c_v)_{v\in C},\qquad *.
\tag{13}
$$

所有候选都有 $c_v$，激活者构成集合 $A$。空候选返回 $(\varnothing,(),*)$；候选的发送上限全为零时，所有 $c_v$ 为零。正温度的解可以含有精确的零，因此软选择也可以产生实际稀疏。

### 4.2 总和约束的两个推论

固定一次选择，省略区域下标，写 $M=\sum_v\mu_v$、$b=\min(1,M)$、$k=k_j$。

**性质（分配被约束固定的情形）。** 若 $M\le1$，则唯一可行分配为 $c=\mu$。因为 $b=M$，约束给出 $M\le\sum_vc_v\le\sum_v\mu_v=M$；每个 $\mu_v-c_v$ 都非负且总和为零，故分别为零。在这一情形，评分和正则均无法改变分配。

**性质（共同阈值的作用）。** 若 $k=1$ 且 $M\ge1$，则 $S=1$。目标中的共同阈值项为常数 $-\eta_jS=-\eta_j$，所以阈值不影响软选择。结合上一性质，$k=1$ 时该结论覆盖所有 $M$。当 $k>1$ 且可行分配允许不同的 $S$ 时，阈值可以影响发送强度之和；一旦最优解的总和达到下限，保持其他输入不变而继续增大阈值，分配保持不变。

一般约束给出 $b\le S\le\min(k,M)$。相对全部使用各节点上限，最多可减少的发送强度之和为 $M-b$。例如 $\mu=(1,1)$、$k=2$ 时，$(1,0)$ 和 $(1,0.5)$ 都是可行分配，总和分别为 $1$、$1.5$。这描述同一次优化的可行范围；给定全部输入和温度后，最优分配仍唯一。将 $S$ 直接固定为 $\min(k,M)$ 会定义另一种选择函数。

### 4.3 发送强度与激活数量

每个 $c_v\le1$，故 $S\le|A|$。例如 $k=2$ 时，分配 $(0.8,0.6,0.4,0.2)$ 满足 $S=2$，同时激活四个节点。软选择中的 $k$ 约束强度之和；实际激活数量由解中正分量的个数决定。

取两个候选，$\mu=(1,1)$、$k=1$，记评分差 $\Delta=s_1-s_2$、温度 $\tau=\tau_{\mathrm{soft}}$。由 $c_2=1-c_1$，对二次目标求导并限制在 $[0,1]$，得到

$$
c_1=\operatorname{clip}\left(\frac12+\frac{\Delta}{2\tau},0,1\right),
\qquad c_2=1-c_1,
$$

其中 $\operatorname{clip}(x,l,h)=\min(h,\max(l,x))$。$|\Delta|<\tau$ 时两个节点均激活；$\Delta\ge\tau$ 时分配为 $(1,0)$。在 $\Delta>\tau$ 的范围内，小幅改变评分仍得到同一分配。称这种分量固定在零或发送上限的情形为饱和。

再取 $t=(4,3,2,1)$、发送上限全为 $1$、$k=2$：

| 温度 $\tau$ | 发送强度 $c$ | 激活数量 $\lvert A\rvert$ |
|---|---|---|
| $5$ | $(0.8,0.6,0.4,0.2)$ | $4$ |
| $2$ | $(1,0.75,0.25,0)$ | $3$ |
| $0.4$ | $(1,1,0,0)$ | $2$ |

激活者才计算 Full 并发送，所有候选已经完成本次接收与记忆写入。上游不发送还可能使下游节点没有任何输入，从而省去下游的整次计算。

### 4.4 硬选择函数

硬选择直接限制激活数量，沿用同一个整数 $k_j$。固定节点全序用于同分时排序，令

$$
C_+=\{v\in C_{\mathrm{eff}}:t_v>0\}.
$$

若 $C_+\ne\varnothing$，按 $t_v$ 降序取前 $\min(k_j,|C_+|)$ 个。若 $C_+=\varnothing$ 且 $C_{\mathrm{eff}}\ne\varnothing$，取有效候选中评分最高的一个。有效候选为空时取 $A=\varnothing$。同分按固定节点序决定。发送强度为

$$
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in A]\quad(v\in C),
\qquad \text{下一历史为 }*.
\tag{14}
$$

SelStep 返回 $(A,(c_v^{\mathrm{hard}})_{v\in C},*)$。有效候选非空时，激活数量介于 $1$ 与 $\min(k_j,|C_{\mathrm{eff}}|)$ 之间；阈值影响是否在最高分候选以外继续选取。

硬选择的发送强度为 $0$ 或该节点的 $\mu_v$。例如 $\mu_v=0.8$ 的节点被选中时发送强度为 $0.8$。所有上限均属于 $\{0,1\}$ 时，激活者各发送单位强度，此时 $S=|A|$。

软选择与硬选择分别由式 (12) 和式 (14) 定义。前者约束 $S\le k_j$，后者约束 $|A|\le k_j$。第 9 节说明软选择在何种条件下随温度趋零而收敛到这个硬选择。训练或推理采用哪个函数，由具体配置给出。

## 5. 保留状态、计算内容与发送

### 5.1 下一状态与计算所用状态

全部候选保留本次写入后的记忆。用 $q^{\mathrm{cmp}}$ 表示本次内容计算读取的状态，下一状态函数为

$$
q^{\mathrm{cmp}}=\widetilde q,\qquad
\operatorname{Next}_v(q,q^{\mathrm{cmp}},\theta,h,
             \mathbf1[v\in A],c_v)=q^{\mathrm{cmp}}.
\tag{15}
$$

因此未激活候选也保留 $\widetilde q$。Full 的结果经消息影响下游；本节点已经确定的下一状态仍为 $\widetilde q$。没有输入的节点保持原状态。

### 5.2 带权 Attention

对每个头 $1\le h\le H_{\mathrm{att}}$，取查询矩阵 $W^Q_{v,h}\in\mathbb R^{d_h\times d}$。从本次计算状态 $q$ 中读取窗口内的记忆，定义

$$
\begin{aligned}
Q_{v,h}(u)&=W^Q_{v,h}\mathcal N_d(u),\\
\widehat w_i&=\chi_{v,\theta}(\xi_i)w_i,\qquad
W=\sum_i\widehat w_i,\qquad a(W)=\min(1,W),\\
\ell_{i,h}&=Q_{v,h}(u)^\top k_{i,h}/\sqrt{d_h},\\
R_{v,h}(q,\theta,u)
&=\begin{cases}
\displaystyle a(W)
 \frac{\sum_i\widehat w_i e^{\ell_{i,h}}\nu_{i,h}}
      {\sum_i\widehat w_i e^{\ell_{i,h}}},&W>0,\\
0,&W=0.
\end{cases}
\end{aligned}
\tag{16}
$$

$\ell_{i,h}$ 是当前内容与第 $i$ 条记忆的匹配分数。$\widehat w_i$ 是本次读取中该条目的有效权重，$W$ 是这些权重之和。$R_{v,h}$ 先对记忆的 value 作归一化加权平均，再乘 $a(W)$。

窗口内有效权重全为 $1$ 时，得到通常的多头 Attention 读取。最后一条弱记忆消失时，$a(W)$ 使读取趋零；单位记忆有 $a(1)=1$。本节的匹配只使用内容，第 7.2 节加入位置坐标与旋转。

### 5.3 内容函数与广播 Full

固定前馈宽度 $d_f$，取 $W_v^O\in\mathbb R^{d\times d}$、$W_v^{\mathrm{gate}},W_v^{\mathrm{up}}\in\mathbb R^{d_f\times d}$、$W_v^{\mathrm{down}}\in\mathbb R^{d\times d_f}$ 以及非负残差尺度 $\alpha_{\mathrm{att}},\alpha_{\mathrm{ff}}$，定义

$$
\begin{aligned}
x_v&=u+\alpha_{\mathrm{att}}W_v^O
       [R_{v,1};\ldots;R_{v,H_{\mathrm{att}}}],\\
G_v(q,\theta,u)
 &=x_v+\alpha_{\mathrm{ff}}W_v^{\mathrm{down}}
 \left[
 \operatorname{SiLU}(W_v^{\mathrm{gate}}\mathcal N_d(x_v))
 \odot W_v^{\mathrm{up}}\mathcal N_d(x_v)
 \right].
\end{aligned}
\tag{17}
$$

第二行为预归一化的 SwiGLU 前馈残差。控制空间为 $\mathsf C_v=[0,1]$，载荷函数 $\operatorname{EmitValue}_v:S_v\times\mathbb N\times X_v\times\mathsf C_v\to P$ 定义为

$$
\operatorname{EmitValue}_v(q^{\mathrm{cmp}},\theta,(r,u),c)
=\begin{cases}
(0,0),&c=0,\\
(c,G_v(q^{\mathrm{cmp}},\theta,u)),&c>0.
\end{cases}
\tag{18}
$$

发送值为 $(c,G_v)$，按式 (1) 比较时内容贡献为 $cG_v$。发送强度乘在整个内容上，包括输入残差；它只在数值投影中乘一次。

定义广播函数

$$
\Delta_v(p)=
\bigl((p)_{a\in\operatorname{Out}(v)},
      (p)_{o\in\operatorname{OutPort}(v)}\bigr),
\qquad \operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v.
$$

模型只对 $v\in A$ 调用 Full。一次激活向所有出边和输出端口发送同一个载荷；来源信息在接收时由固定边标签提供。每条出边使用同一个发送强度。

式 (18) 同时定义了 $c=0$ 时直接返回 $(0,0)$ 的分支，使 Full 在整个控制空间上有定义。

### 5.4 输出读出

一个输出坐标由输出时刻与端口 $(\theta,o)$ 确定。记全部输出记录为 $Z$，$\operatorname{outtime}$ 和 $\operatorname{outport}$ 分别取记录的时刻与端口。先固定有限输出坐标集合 $\Lambda\subseteq\mathbb N\times\mathsf O$。从完整输出记录 $Z$ 取

$$
Z_\Lambda=\{z\in Z:(\operatorname{outtime}(z),\operatorname{outport}(z))\in\Lambda\}.
$$

对任意有限输出记录集合 $\mathcal M$，将其载荷记为 $(m_i,z_i)$，定义

$$
O(\mathcal M)=\frac{\sum_i(m_i)_+z_i}{\max(1,\sum_i(m_i)_+)},\qquad
\operatorname{ReadOut}_\Lambda(Z)=O(Z_\Lambda).
\tag{19}
$$

空集合给零向量。所选输出坐标全部确定后求值。一个单位载荷原样读出，多个相同单位载荷的读出保持原尺度，总强度趋零时读出趋零。原始输出的端口和时间身份仍保留在 $Z$ 中；全零输出与缺席输出均读出零。

组合配置选择有限集合 $\Lambda$，并声明其任务含义。例如序列模型可为每个输入位置指定一组 $\Lambda_t$，令 $O_t=\operatorname{ReadOut}_{\Lambda_t}(Z)$。这种数值汇集发生在图外，不增加图内作用或输出记录。

## 6. 两个完整例子

### 6.1 从接收到输出

沿用第 1—5 节的二次正则、拼接评分与固定增益。取无内部边的区域 $\{a,b,c\}$，初始缓存为空，$d=d_s=H_{\mathrm{att}}=1$、$\epsilon=1$、$\alpha_{\mathrm{agg}}=0$、$\gamma_v=1$，Attention 只按内容匹配。本次 $a$ 收到 $(0.5,1),(0.5,1)$，$b$ 收到 $(1,-1)$，$c$ 收到 $(0,9)$。三个节点都是候选。令 key、query 为零，value 与摘要投影均为 $\sqrt2$，故单位内容的归一化投影仍是 $\pm1$。

评分网络输出常数 $s=(2,1,100)$，可由零输出权重与相应偏置实现。取 $\eta_j=0,k_j=1,\tau_{\mathrm{soft}}=2$。

| 节点 | 聚合 $(r,u)$ | 新写入 $(k,\nu,p,w)$ | 上界 $\mu$ | 评分 $s$ | 发送强度 $c$ |
|---|---|---|---|---|---|
| $a$ | $(1,1)$ | $(0,1,1,1)$ | $1$ | $2$ | $0.75$ |
| $b$ | $(1,-1)$ | $(0,-1,-1,1)$ | $1$ | $1$ | $0.25$ |
| $c$ | $(0,0)$ | 不追加 | $0$ | $100$ | $0$ |

节点 $c$ 的发送上限为零，其高分不影响选择。$a,b$ 的分配由第 4.3 节的两节点公式得到。三者均保留接收后的状态，随后计算激活者的 Full。

令 $W_v^O=1,\alpha_{\mathrm{att}}=1,\alpha_{\mathrm{ff}}=0$。$a,b$ 的 Attention 分别读出 $1,-1$，Full 内容为 $2,-2$，发送 $(0.75,2),(0.25,-2)$。若直接作为终端，$O=1$；若共同到达采用式 (3) 且 $\alpha_{\mathrm{agg}}=0$ 的下游，则下游得到 $(r,u)=(1,1)$，再开始自己的接收流程。

保持评分不变，将温度降到 $0.5$，发送强度已经是 $(1,0,0)$，只执行 $a$ 的 Full，终端 $O=2$。共同阈值的作用已由第 4.2 节确定。采用硬选择时，有效候选中最高分的 $a$ 激活，节点 $c$ 始终因发送上限为零而排除。

### 6.2 未激活时保留的记忆

再取同一区域的两个节点 $a,b$，各有输入与输出端口，没有内部边。各输入端口在时间 $1,4$ 分别收到 $(1,1),(1,-1)$，取 $T_a=T_b\ge4$。沿用上一例的投影与 Full，每次读出同刻两个端口的输出；采用硬选择，取 $k_j=1,\eta_j=0$，评分改为

$$
s_a=0.5,\qquad
s_b=0.75-M_{\mathrm{long}}^{\mathrm{sum}}(\widetilde q_b,\theta).
$$

这属于式 (8) 的网络：$\operatorname{SiLU}(x)-\operatorname{SiLU}(-x)=x$，两个隐藏单元即可表达该线性项。

| 位置 | 两节点新写入的 $(\xi,\nu,p,w)$ | $M_{\mathrm{long}}$ | $(s_a,s_b)$ | 激活者 | 终端 $O$ |
|---|---|---|---|---|---|
| $0$ | $(1,1,1,1)$ | $1$ | $(0.5,-0.25)$ | $a$ | $2$ |
| $1$ | $(4,-1,-1,1)$ | $0$ | $(0.5,0.75)$ | $b$ | $-1$ |

第一次 $b$ 未激活，但保留 $+1$ 的记忆。第二次它的 Attention 读出 $(1-1)/2=0$，残差内容为 $-1$；若误删第一次未激活时的写入，Attention 会返回 $-1$，Full 内容变成 $-2$。本次选择与内容计算因此使用了前次未激活时保留的记忆。

## 7. 可替换的局部函数

以下替换各自保留前述函数的输入与输出含义。不同区域可以选用不同组合；一次运行固定所选函数及参数。各函数的配置名称集中列于第 10 节和附录 S.2。

### 7.1 节点与来源的聚合投影

为各节点或来源分别选择投影时，将式 (3) 的非线性残差写为

$$
\begin{aligned}
F_{v,a}(z)&=B_{v,a}\operatorname{SiLU}
 (A_{v,a}\mathcal N_d(z)+e_{v,a}),\\
u&=\bar z+\frac{\alpha_{\mathrm{agg}}}{r}
 \sum_i(m_i)_+F_{v,\operatorname{SrcClass}_v(a_i)}(z_i)
 \quad(r>0),
\qquad u=0\quad(r=0).
\end{aligned}
\tag{20}
$$

其中 $A_{v,a}\in\mathbb R^{p_a\times d}$、$B_{v,a}\in\mathbb R^{d\times p_a}$、$e_{v,a}\in\mathbb R^{p_a}$。下列绑定均给出完整的 Agg：

| 聚合配置 | 参数绑定 | 主要取舍 |
|---|---|---|
| 区域共享 | $A_{v,a}=A_j,B_{v,a}=B_j,e_{v,a}=e_{j,a}$ | 恢复式 (3)，共享特征空间与参数 |
| 节点独立 | $A_{v,a}=A_v,B_{v,a}=B_v$，嵌入按节点和类别声明 | 节点可在压缩前提取不同信息，增加准备成本 |
| 来源独立 | $A_{v,a}=A_{j,a},B_{v,a}=B_{j,a},e_{v,a}=e_{j,a}$ | 不同来源采用不同投影，参数随类别数增长 |
| 节点与来源适配 | $A_{v,a}=A_j+L^A_{v,a}R^A_{v,a}$，$B_{v,a}=B_j+L^B_{v,a}R^B_{v,a}$ | 以指定秩控制分化与成本 |

最后一行取正整数秩 $r_{\mathrm{agg}}$；$L^A,R^A,L^B,R^B$ 的形状依次为 $p_a\times r_{\mathrm{agg}}$、$r_{\mathrm{agg}}\times d$、$d\times r_{\mathrm{agg}}$、$r_{\mathrm{agg}}\times p_a$，嵌入另行声明。按需共享其中因子也属于这个绑定。

这些差异发生在消息被压缩之前；聚合后的节点适配一般无法恢复已经丢失的信息。附录 A 的证明适用于上述全部绑定：所需条件是固定、连续且在有界内容上有界的 $F_{v,a}$，以及强度加权。

### 7.2 位置坐标与旋转

为每个节点固定位置函数

$$
\operatorname{Pos}_v:\mathbb N\to\mathbb R.
$$

逻辑时间 $\theta$ 决定消息到达、状态顺序和窗口成员；$\operatorname{Pos}_v(\theta)$ 为 Attention 提供位置坐标。本文使用的仿射族为

$$
\operatorname{Pos}_v(\theta)
=\frac{\theta-o_v^{\mathrm{pos}}}{s_v^{\mathrm{pos}}},
\qquad o_v^{\mathrm{pos}}\in\mathbb R,\quad s_v^{\mathrm{pos}}>0.
$$

$o_v^{\mathrm{pos}}=0,s_v^{\mathrm{pos}}=1$ 直接编码逻辑时间。在 SettleGraph 中，令 $\ell(j)$ 为区域的秩、$t$ 为输入位置，取位置间隔 $D>\max_j\ell(j)$。时间安排为 $\theta_{v,t}=Dt+\ell(\rho(v))$ 时，可取 $o_v^{\mathrm{pos}}=\ell(\rho(v)),s_v^{\mathrm{pos}}=D$，于是 $\operatorname{Pos}_v(\theta_{v,t})=t$，恢复通常的输入位置。一般图中，同一次接收可以汇合不同输入位置的消息；这里编码当前聚合的处理时间和历史条目的写入时间，无需给混合内容指定唯一来源位置。

位置函数在整条继续运行中固定，不随接收次数、激活次数或分段边界改变。更一般的固定实值位置函数也可用于下文定义与有限切面证明；具体组合须给出其完整定义。

固定偶数 $0\le d^{\mathrm{rot}}_{v,h}\le d_h$、坐标配对与有限频率 $\omega^{\mathrm{rot}}_{v,h,a}$，定义

$$
\begin{aligned}
\operatorname{Rot}_{v,h}(p)
 &=I_{d_h-d^{\mathrm{rot}}_{v,h}}
   \oplus\bigoplus_{a=1}^{d^{\mathrm{rot}}_{v,h}/2}
   \begin{pmatrix}
   \cos(\omega^{\mathrm{rot}}_{v,h,a}p)&-\sin(\omega^{\mathrm{rot}}_{v,h,a}p)\\
   \sin(\omega^{\mathrm{rot}}_{v,h,a}p)&\cos(\omega^{\mathrm{rot}}_{v,h,a}p)
   \end{pmatrix}.
\end{aligned}
$$

这里的 $\oplus$ 为矩阵直和。旋转维数为零时 $\operatorname{Rot}=I_{d_h}$；旋转全部或部分坐标分别得到完整或部分 RoPE。旋转维数与评分隐藏宽度 $d_r$ 各自独立。

另取非负距离偏置斜率 $b^{\mathrm{pos}}_{v,h}$，将式 (16) 中的匹配分数替换为

$$
\ell_{i,h}=\frac{
 [\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\theta))Q_{v,h}(u)]^\top
 [\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\xi_i))k_{i,h}]}{\sqrt{d_h}}
 -b^{\mathrm{pos}}_{v,h}
   (\operatorname{Pos}_v(\theta)-\operatorname{Pos}_v(\xi_i))_+.
\tag{21}
$$

数学状态中的 $k_i$ 保持未旋转形式，$\nu_i,p_i$ 也不施加旋转。上述旋转满足

$$
\operatorname{Rot}_{v,h}(p)^\top\operatorname{Rot}_{v,h}(q)
=\operatorname{Rot}_{v,h}(q-p),
$$

故旋转后的匹配依赖相对坐标，并包含各频率对应的相位信息。下面三种配置共用这一匹配公式：

| 配置 | 旋转维数 | 距离偏置 |
|---|---|---|
| NoPE | $d^{\mathrm{rot}}_{v,h}=0$ | $b^{\mathrm{pos}}_{v,h}=0$ |
| 完整 RoPE | $d^{\mathrm{rot}}_{v,h}=d_h$，要求 $d_h$ 为偶数 | 通常为零 |
| 部分 RoPE | $0<d^{\mathrm{rot}}_{v,h}<d_h$，旋转维数为偶数 | 通常为零 |

NoPE 的 Full 匹配使用内容，时间窗口、摘要和状态顺序仍保留时间信息。令 $\Delta p=\operatorname{Pos}_v(\theta)-\operatorname{Pos}_v(\xi_i)$，可选的线性距离偏置在 softmax 中乘入 $e^{-b^{\mathrm{pos}}_{v,h}\Delta p_+}$，是一种距离衰减；它与 RoPE 的旋转可以分别配置。

### 7.3 用当前内容检索记忆

取偶数 $0\le d_v^{\mathrm{rot,read}}\le d_s$、坐标配对及有限频率 $\omega_{v,a}^{\mathrm{rot,read}}$。$\operatorname{Rot}_v^{\mathrm{read}}$ 使用第 7.2 节的旋转矩阵族，宽度换为 $d_s$，采用这些独立参数；零旋转维数给出内容匹配。它沿用同一 $\operatorname{Pos}_v$，与 Full 的位置配置分别选择。

取节点矩阵 $W_v^{\mathrm{RQ}},W_v^{\mathrm{RK}},W_v^{\mathrm{RV}}\in\mathbb R^{d_s\times d}$，定义

$$
\begin{aligned}
Q_v^{\mathrm{read}}(u)&=W_v^{\mathrm{RQ}}\mathcal N_d(u),\qquad
K_{v,i}^{\mathrm{read}}=W_v^{\mathrm{RK}}k_i,\qquad
V_{v,i}^{\mathrm{read}}=W_v^{\mathrm{RV}}\nu_i,\\
\ell_{v,i}^{\mathrm{read}}&=
\frac{
 [\operatorname{Rot}_v^{\mathrm{read}}(\operatorname{Pos}_v(\theta))Q_v^{\mathrm{read}}(u)]^\top
 [\operatorname{Rot}_v^{\mathrm{read}}(\operatorname{Pos}_v(\xi_i))K_{v,i}^{\mathrm{read}}]
}{\sqrt{d_s}},\\
M_a^{\mathrm{qry}}(q,\theta,u)&=
\begin{cases}
\displaystyle \min(1,W_a)
 \frac{\sum_i\omega_i^a e^{\ell_{v,i}^{\mathrm{read}}}V_{v,i}^{\mathrm{read}}}
      {\sum_i\omega_i^a e^{\ell_{v,i}^{\mathrm{read}}}},&W_a>0,\\
0,&W_a=0.
\end{cases}
\end{aligned}
\tag{22}
$$

两个时间尺度共用本次匹配分数。检索结果替换第 3.1 节的摘要。宽度与检索量允许接近 Full，成本按实际配置计量。

固定 $\mathfrak m_j\in\{\mathrm{sum},\mathrm{qry}\}$ 后，评分特征中的 $M_a$ 均使用相应记忆描述，均在 $(q,\theta,u)$ 的适用自变量上求值。

### 7.4 分组编码与记忆匹配评分

固定匹配宽度 $d_{\mathrm{sel}}$，将评分输入分为三组

$$
z_v^{\mathrm{cur}}=\mathcal N_d(u),\qquad
z_v^{\mathrm{mem}}=[M_{\mathrm{short}};M_{\mathrm{long}}],\qquad
z_v^{\mathrm{stat}}=[\log(1+r_+);\log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})].
$$

对 $g\in\{\mathrm{cur},\mathrm{mem},\mathrm{stat}\}$，输入宽度依次为 $n_g=d,2d_s,3$。取 $B_v^{\mathrm{enc},g}\in\mathbb R^{d_r\times n_g}$、$C_v^{\mathrm{enc},g}\in\mathbb R^{d_{\mathrm{sel}}\times d_r}$，两个偏置分别为 $d_r,d_{\mathrm{sel}}$ 维；$W_v^{\mathrm{match,gate}},W_v^{\mathrm{match,up}}\in\mathbb R^{d_r\times3d_{\mathrm{sel}}}$，$b_v^{\mathrm{match,gate}},b_v^{\mathrm{match,up}},w_v^{\mathrm{match}}\in\mathbb R^{d_r}$，$b_v^{\mathrm{match}}$ 为标量。两个非负尺度及全部参数有限。

定义

$$
\begin{aligned}
E_v^g(z)&=\mathcal N_{d_{\mathrm{sel}}}
 \bigl(C_v^{\mathrm{enc},g}\operatorname{SiLU}(B_v^{\mathrm{enc},g} z+b_v^{\mathrm{enc},g})+d_v^{\mathrm{enc},g}\bigr),\\
x_v^{\mathrm{match}}&=E_v^{\mathrm{cur}}(z_v^{\mathrm{cur}}),\qquad
e_v^{\mathrm{match}}=E_v^{\mathrm{mem}}(z_v^{\mathrm{mem}}),\qquad
z_v^{\mathrm{match}}=E_v^{\mathrm{stat}}(z_v^{\mathrm{stat}}),\\
h_v^{\mathrm{match}}&=[x_v^{\mathrm{match}};e_v^{\mathrm{match}};z_v^{\mathrm{match}}],\\
F_v^{\mathrm{match}}(h)&=(w_v^{\mathrm{match}})^\top
 \left[\operatorname{SiLU}(W_v^{\mathrm{match,gate}}h+b_v^{\mathrm{match,gate}})
       \odot(W_v^{\mathrm{match,up}}h+b_v^{\mathrm{match,up}})\right],\\
s_v^{\mathrm{match}}&=b_v^{\mathrm{match}}
 +\alpha_v^{\mathrm{match}}\frac{(x_v^{\mathrm{match}})^\top e_v^{\mathrm{match}}}{\sqrt{d_{\mathrm{sel}}}}
 +\alpha_v^{\mathrm{res}}F_v^{\mathrm{match}}(h_v^{\mathrm{match}}),\\
s_v^{\mathrm{loc}}&=s_v^{\mathfrak f_j},\qquad
\mathfrak f_j\in\{\mathrm{cat},\mathrm{match}\}.
\end{aligned}
\tag{23}
$$

各组先独立编码并归一化，匹配项表达当前内容与记忆的关系，残差项补充统计量及非线性交互。参数默认按节点独立，也可在配置中声明同形评分头的参数相等。

$\mathrm{cat}$ 提供较小的基线；$\mathrm{match}$ 加入结构性偏好和准备成本。分组后的非线性、归一化与显式匹配构成函数差异；仅将一个线性矩阵拆成三块再相加，会得到原来的线性运算。两种局部评分均可搭配任一种记忆描述与下述区域评分。

### 7.5 根据内容调整发送增益

记第 3.3 节的固定增益为 $\gamma_v^{\mathrm{fixed}}=\gamma_v$。另一种选择读取式 (8) 的同一特征。取 $W_v^\gamma\in\mathbb R^{d_r\times(d+4d_s+3)}$，$a_v^\gamma,b_v^{\gamma,h}\in\mathbb R^{d_r}$，$b_v^\gamma\in\mathbb R$。定义

$$
\gamma_v^{\mathrm{context}}(q,\theta,r,u)
 =1+(\gamma_{\max}-1)\sigma\!\left(
 b_v^\gamma+(a_v^\gamma)^\top
 \operatorname{SiLU}(W_v^\gamma f_v(q,\theta,r,u)+b_v^{\gamma,h})\right).
\tag{24}
$$

取 $\mathfrak g_j\in\{\mathrm{fixed},\mathrm{context}\}$，在式 (9) 中使用所选的 $\gamma_v^{\mathfrak g_j}$。

这个增益可根据当前内容及已有记忆调整唤醒程度。$\gamma_{\max}=1$ 给出不放大的对照。两种增益都在 $[1,\gamma_{\max}]$ 内，因此第 3.3 节的发送上限界继续成立。

### 7.6 区域 Attention 评分

为该区域固定匹配宽度 $d_{\mathrm{sel}}$。$W_v^{\mathrm{loc}}$、$W_v^{\mathrm{mem}}$ 的形状为 $d_{\mathrm{sel}}\times d$、$d_{\mathrm{sel}}\times(2d_s+2)$，两个偏置属于 $\mathbb R^{d_{\mathrm{sel}}}$。同一区域共享匹配宽度和坐标含义，投影参数按节点声明。

描述量同时传递当前内容的特征、记忆特征及局部评分：

$$
\begin{aligned}
x_v^{\mathrm{sel}}(u)&=W_v^{\mathrm{loc}}\mathcal N_d(u)+b_v^{\mathrm{loc}},\\
K_v^{\mathrm{sel}}(q,\theta,u)&=W_v^{\mathrm{mem}}
 [M_{\mathrm{short}};M_{\mathrm{long}};
 \log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})]
 +b_v^{\mathrm{mem}},\\
D_v^{\mathrm{att}}&=[0,1]\times\mathbb R^{d_{\mathrm{sel}}}
 \times\mathbb R^{d_{\mathrm{sel}}}\times\mathbb R,\\
\operatorname{Describe}_v^{\mathrm{att}}(q,\theta,(r,u))
 &=(\mu_v(q,\theta,r,u),x_v^{\mathrm{sel}}(u),K_v^{\mathrm{sel}}(q,\theta,u),s_v^{\mathrm{loc}}(q,\theta,r,u)).
\end{aligned}
\tag{25}
$$

取区域共享矩阵 $W_j^{\mathrm{in,sel}},W_j^{\mathrm{out,sel}}\in\mathbb R^{d_{\mathrm{sel}}\times d_{\mathrm{sel}}}$、同宽度偏置和非负尺度 $\alpha_j^{\mathrm{loc}},\alpha_j^{\mathrm{sel}}$。对完整候选集 $C$，SelStep 内部先形成共享 query，再产生各候选评分：

$$
\begin{aligned}
\bar x_j&=\frac{\sum_{v\in C}\mu_v x_v^{\mathrm{sel}}}
                    {\max(1,\sum_{v\in C}\mu_v)},\\
Q_j^{\mathrm{sel}}&=\psi_j(\bar x_j),\qquad
\psi_j(x)=W_j^{\mathrm{out,sel}}
 \operatorname{SiLU}(W_j^{\mathrm{in,sel}}x+b_j^{\mathrm{in,sel}})
 +b_j^{\mathrm{out,sel}},\\
s_v&=\alpha_j^{\mathrm{loc}}s_v^{\mathrm{loc}}
  +\alpha_j^{\mathrm{sel}}
   \frac{(Q_j^{\mathrm{sel}})^\top K_v^{\mathrm{sel}}}{\sqrt{d_{\mathrm{sel}}}}.
\end{aligned}
\tag{26}
$$

取 $\alpha_j^{\mathrm{loc}}=1,\alpha_j^{\mathrm{sel}}=0$ 恢复独立评分的数值；取 $\alpha_j^{\mathrm{loc}}=0$ 隔离区域匹配的作用。空候选仍直接返回空选择。

共享 query 表达该区域当前收到的信息，keys 表达各节点的私有记忆；$\mathrm{qry}$ 配置还让 keys 随本次内容检索而改变。Attention 匹配产生评分，第 4 节的选择函数再决定发送强度和激活集合。这里的单 query 匹配对候选数是线性工作量，无须构造候选两两匹配矩阵。

$\mu_v$ 加权使发送上限为零的候选不影响其他节点的 query，趋零候选的影响也趋零；按候选数直接取均值一般不具备这个性质。区域划分同时规定选择可共享的信息范围。多个局部区域分别形成 query，无须在整个层上集中选择。

记这两种描述方式为 $\mathfrak s_j\in\{\mathrm{ind},\mathrm{att}\}$，取 $D_v=D_v^{\mathfrak s_j}$、$\operatorname{Describe}_v=\operatorname{Describe}_v^{\mathfrak s_j}$。Read 继续按式 (10) 读取更新后的状态；SelStep 按同一种描述方式取得 $(\mu_v,s_v)$ 后，应用同一个软选择或硬选择函数。

独立评分中，发送上限进入选择约束及适用的正则。区域 Attention 还用它汇集 query。两种评分都允许与时间摘要、内容检索、两种局部评分及两种增益组合。

**例：弱候选如何影响共同 query。**

取 $d_{\mathrm{sel}}=2$，两个候选的描述量满足

$$
\begin{aligned}
\mu_a=1,\quad &x_a^{\mathrm{sel}}=(1,0),\quad K_a^{\mathrm{sel}}=(\sqrt2,0),\\
\mu_b=\varepsilon,\quad &x_b^{\mathrm{sel}}=(-1,0),\quad K_b^{\mathrm{sel}}=(-\sqrt2,0),
\qquad 0\le\varepsilon\le\tfrac12.
\end{aligned}
$$

取 $\alpha_j^{\mathrm{loc}}=0,\alpha_j^{\mathrm{sel}}=1$，$\psi_j(x_1,x_2)=(x_1,0)$。这个函数属于式 (26)：取零偏置、$W_j^{\mathrm{in,sel}}=\left(\begin{smallmatrix}1&0\\-1&0\end{smallmatrix}\right)$、$W_j^{\mathrm{out,sel}}=\left(\begin{smallmatrix}1&-1\\0&0\end{smallmatrix}\right)$，利用 SiLU 的差恒等式即可。

于是

$$
Q_j^{\mathrm{sel}}=\left(\frac{1-\varepsilon}{1+\varepsilon},0\right),\qquad
s_a=\frac{1-\varepsilon}{1+\varepsilon},\quad s_b=-s_a.
$$

采用二次正则，取 $k_j=1,\eta_j=0,\tau_{\mathrm{soft}}=1$。发送强度之和为 $1$，投影给出

$$
c_b=\max\left(0,\frac{3\varepsilon-1}{2(1+\varepsilon)}\right),
\qquad c_a=1-c_b.
$$

在给定范围内 $c_b\le\varepsilon$。当 $\varepsilon=1/2$ 时，发送强度为 $(5/6,1/6)$；当 $\varepsilon\le1/3$ 时为 $(1,0)$。$b$ 在未激活但有正上界时仍参与 query，其上界趋零后影响连续消失，得到只保留 $a$ 的结果。加入任意发送上限为零的候选也不会改变 query 或这些控制量。

### 7.7 熵正则

软选择保留第 4.1 节的全部约束。固定形状参数 $\alpha=\alpha_j^{\mathrm{ent}}\in[1,2]$，定义两个可替换二次正则的函数：

$$
\begin{aligned}
R^{\mathrm{bern}}(c;\mu)&=\sum_{v:\mu_v>0}\mu_v h_B(c_v/\mu_v),
& h_B(p)&=-p\log p-(1-p)\log(1-p),\\
R^{\mathrm{ent}}(c;\mu)&=\sum_v h_\alpha(c_v),
& h_\alpha(c)&=
\begin{cases}
-c\log c,&\alpha=1,\\
\dfrac{c-c^\alpha}{\alpha(\alpha-1)},&1<\alpha\le2.
\end{cases}
\end{aligned}
\tag{27}
$$

端点按 $0\log0=0$ 延拓；bern 的零上限项取零。bern 将二元熵作用于每个节点使用发送上限的比例 $c_v/\mu_v$；ent 将 Shannon 或 Tsallis 熵作用于发送强度 $c_v$。

用 $\mathfrak b_j\in\{\mathrm{quad},\mathrm{bern},\mathrm{ent}\}$ 指定正则，在式 (12) 中取 $R=R^{\mathfrak b_j}$。三种目标在可改变的分量上严格凹，均有唯一解。约束本身的性质直接沿用第 4.2 节；第 8 节比较正则带来的差异。

### 7.8 固定尺度的稠密 Attention

固定 $\tau_{\mathrm{soft}}>0$，在式 (12) 中取 $\mathfrak b_j=\mathrm{ent}$、$\alpha_j^{\mathrm{ent}}=1$，即 Shannon 熵。训练与推理均可持续使用这一函数和同一个正温度。这里稠密表示每个有效候选均发送，即 $A=C_{\mathrm{eff}}$；图上的边仍由拓扑单独给定。

这一正性可由熵在零处的导数得到。第 4.2 节的强制分配情形已经满足正性。在其余情形，若最优解某个有效分量为零，可从一个正分量移入足够小的 $\varepsilon>0$，保持总和及各节点上限。新分量的熵增量为 $-\varepsilon\log\varepsilon$，评分项及原正分量的变化为 $O(\varepsilon)$，故目标增大，矛盾。没有有效候选时，仍按式 (13) 返回全零控制和空激活集合。

进一步设 $C_{\mathrm{eff}}$ 非空，取 $k_j=1$，且每个有效候选的 $\mu_v=1$。可行分配在 $C_{\mathrm{eff}}$ 上满足 $c_v\ge0,\sum_vc_v=1$，即概率单纯形。解为

$$
c_v=
\begin{cases}
\displaystyle
\frac{\exp(s_v/\tau_{\mathrm{soft}})}
     {\sum_{u\in C_{\mathrm{eff}}}\exp(s_u/\tau_{\mathrm{soft}})},
&v\in C_{\mathrm{eff}},\\
0,&v\notin C_{\mathrm{eff}}.
\end{cases}
$$

这就是 softmax。对正分量写最优性条件，得到 $s_v-\tau_{\mathrm{soft}}(1+\log c_v)$ 为共同常数，再由总和为 $1$ 确定分母；共同阈值的消去已由第 4.2 节说明。发送强度之和为 $1$，激活数量为 $|C_{\mathrm{eff}}|$。

若评分采用式 (26)，取 $\alpha_j^{\mathrm{loc}}=0,\alpha_j^{\mathrm{sel}}=1$，上述控制量恰为区域 query 对节点 keys 的 Attention 权重。SelStep 按式 (13) 返回，Agg、Upd、Read、Next 和广播 Full 均沿用此前定义。固定正温度给出一个完整的计算函数；第 9 节另行讨论改变温度时的极限。

一般图允许 $0<\mu_v<1$。此时 Shannon 选择继续使用式 (12) 的全部约束，其求解见第 8.1 节。例如取 $\mu=(0.2,1)$、$s=(0,0)$、$k=1$，任意正温度下有：

| 分配方法 | 发送强度 | 与当前约束的关系 |
|---|---|---|
| 式 (12) 的 Shannon 选择 | $(0.2,0.8)$ | 满足各节点上限与总和下限 |
| 直接对评分取 softmax | $(0.5,0.5)$ | 第一节点超过发送上限 |
| 将上述 softmax 分量各乘对应 $\mu_v$ | $(0.1,0.5)$ | 总和 $0.6$ 小于所需下限 $1$ |

因此，普通 softmax 公式适用于上述单纯形条件；固定正温度的 Shannon 选择适用于本文的一般发送约束。后者仍可能达到节点的发送上限，其梯度按第 8 节的约束分支计算。Shannon 熵在此给出正分配；直接删去式 (12) 的正则项则得到线性优化，最优解可位于边界，也可能不唯一。

## 8. 选择函数的响应与导数

本节固定一次区域选择，省略区域下标，写 $\tau=\tau_{\mathrm{soft}}$、$\mathfrak b=\mathfrak b_j$。先取 $M>1$；$M\le1$ 的解已由第 4.2 节确定。

### 8.1 用一个乘子协调总和

对每个候选，定义标量响应函数 $g_{\mathfrak b}(x,\mu;\tau)$：

| 正则 | $g_{\mathfrak b}(x,\mu;\tau)$ |
|---|---|
| $\mathrm{quad}$ | $\operatorname{clip}(x/\tau,0,\mu)$ |
| $\mathrm{bern}$ | $\mu\,\sigma(x/\tau)$ |
| $\mathrm{ent},\alpha=1$ | $\min(\mu,\exp(x/\tau-1))$ |
| $\mathrm{ent},1<\alpha\le2$ | $\min\!\left(\mu,\left[(\alpha-1)x/\tau+1/\alpha\right]_+^{1/(\alpha-1)}\right)$ |

其中 clip 已在第 4.3 节定义，$\sigma$ 已在第 1.3 节定义。令 $\lambda_U,\lambda_L$ 分别为总和上限、下限的乘子，解满足

$$
\begin{aligned}
c_v&=g_{\mathfrak b}(t_v-\lambda,\mu_v;\tau),\\
\lambda&=\lambda_U-\lambda_L,\qquad \lambda_U,\lambda_L\ge0,\\
b&\le S\le k,\qquad
\lambda_U(S-k)=0,\qquad \lambda_L(b-S)=0.
\end{aligned}
\tag{28}
$$

先尝试 $\lambda=0$；若 $S>k$，求 $S=k$ 的非负乘子；若 $S<b$，求 $S=b$ 的非正乘子。各响应单调，故只需求一个标量根。二次族可按断点排序，全部族均可用二分或带区间保护的 Newton 法；反向由最优性条件直接求导。求解映射与分段导数见附录 S.3。

### 8.2 正则如何影响激活与饱和

式 (28) 将各坐标写为 $c_v=g(t_v-\lambda,\mu_v;\tau)$。把满足 $0<c_v<\mu_v$ 的候选集合记为 $\mathcal F$，称其发送强度未触及上下限。固定乘子和发送上限，记响应斜率为 $a_v=\partial g/\partial(t_v-\lambda)$。下表在 $M>1$ 的光滑分支上成立。

| 正则 | 正温度的激活与边界 | 未触及上下限时的斜率 $a_v$ |
|---|---|---|
| quad | 可精确为零或达到上界 | $1/\tau$ |
| bern | 每个有效候选严格处于上下界之间 | $\mu_v p_v^{\mathrm{occ}}(1-p_v^{\mathrm{occ}})/\tau$，$p_v^{\mathrm{occ}}=c_v/\mu_v$ |
| ent，$\alpha=1$ | 每个有效候选为正，可达到上界 | $c_v/\tau$ |
| ent，$1<\alpha\le2$ | 可精确为零或达到上界 | $c_v^{2-\alpha}/\tau$ |

quad 与 ent 的严格零或达到发送上限的分支对评分的直接斜率为零。$1<\alpha<2$ 时，未触及上限的正发送强度趋零也使斜率趋零；quad 在区间内的斜率保持 $1/\tau$，到边界再切换分支。bern 的斜率随比例 $c_v/\mu_v$ 接近两端而趋小。完整导数还需计入共同乘子，见 §8.3。

### 8.3 评分与发送上限如何影响梯度

固定发送上限、温度和评分阈值。以下扰动保持各候选的零值、内部值或上限状态，以及总和约束取等号的情形，称为在同一光滑分支内求导。若发送强度之和固定为 $B=1$ 或 $B=k$，微分 $\sum_vc_v=B$ 得

$$
d\lambda=\frac{\sum_v a_v\,ds_v}{\sum_v a_v},\qquad
dc_v=a_v(ds_v-d\lambda),\qquad \sum_v a_v>0.
$$

对任意可微标量目标 $\mathcal L$，令 $g_v=\partial\mathcal L/\partial c_v$、$\bar g=\sum_v a_vg_v/\sum_v a_v$，于是

$$
\frac{\partial\mathcal L}{\partial s_v}=a_v(g_v-\bar g).
$$

分配比较未触及上下限的各候选对目标的边际影响。$a_v>0$ 且 $g_v<\bar g$ 时，该评分的负梯度方向为增大；固定其余评分且至少有两个未触及上下限的候选时，提高该评分会把发送强度分向该候选。共同乘子协调各未触及上下限的候选，ind 的独立评分也具有这个分配耦合。总和上下限均松弛时，乘子为零，各坐标直接按自身响应变化。

quad 对集合 $\mathcal F$ 内评分的 Jacobian 子块为 $\tau^{-1}(I-\mathbf1\mathbf1^\top/|\mathcal F|)$，其中 $\mathcal F$ 已在第 8.2 节定义。发送强度之和固定且只有一个未触及上下限的候选时，该评分导数为零；所有未触及上下限的候选的 $g_v$ 相同时，中心化同样给出零梯度。在 $M<1$ 的开区域，第 4.2 节给出评分 Jacobian 为零、对发送上限的 Jacobian 为单位矩阵。上界变化及各分支边界的完整导数见附录 S.3。

发送投影 $(c_v,c_vG_v)$ 同时依赖控制和 Full 内容。描述量经评分参与分配，区域 Attention 的共享 query 又让各候选内容影响其他评分；因此零发送强度但正上界的候选可经 query 保留其他候选的反馈。未激活者保存的写入还可进入未来 Read 或 Full，沿保留的依赖链传回导数。未求值的 Full 内容不提供该步替代分支的数值依据。

强度与内容在这些依赖中相互作用：强度决定加权聚合、写入和上界，内容与记忆决定评分及上下文增益。全部输入强度同比例缩放时聚合均值保持；若后续写入、上界和读出尺度也处于饱和区，目标可主要依赖相对分配。

固定评分且存在严格间隔时，低温可进入评分导数为零的饱和区；仍处于上下限之间的响应斜率则含 $1/\tau$。前向连续性由值的极限描述，这些导数在趋零温度下另有各自的边界行为。

### 8.4 与 softmax、entmax 的关系及高温极限

在第 7.8 节的单纯形条件下，$\mathrm{ent}$ 是 $\alpha$-entmax：$\alpha=1$ 给出该节的 softmax，$\alpha=2$ 给出 sparsemax，二次族也给出 sparsemax。唯一最高分下，这些单纯形函数的零温极限均为 Top-1。固定正温度时，各函数按自己的正分量激活节点。式 (12) 与硬选择的极限关系见第 9 节。

当约束允许不同的发送强度总和时，正则中的线性项会影响最优解：

$$
R^{\mathrm{ent}}_{\alpha=2}
=R^{\mathrm{quad}}+\frac12\sum_vc_v.
\tag{29}
$$

因此相同 $t,\tau$ 下，$\alpha=2$ 的解等于二次族在 $t+\tau/2$ 下的解。要恢复同一数值，取 $\eta_j^{\mathrm{ent},2}=\eta_j^{\mathrm{quad}}+\tau/2$。发送强度之和固定时，这项差别消失。ent 在本文的一般可行域上还保留每个候选的发送上限，以及第 4.2 节的总和区间。

固定评分、发送上限和 $k$，令 $\tau\to\infty$，则解趋向可行集上正则的唯一最大值：quad 在 $S=b$ 上取最小范数分配；bern 在 $\mu/2$ 可行时取它；ent 取其受约束的熵最大值。此结论由目标除以 $\tau$、紧性及严格凹性得到。不同正则的高温发送强度之和因而可以不同。

### 8.5 Attention 权重与 query 的导数

在第 7.8 节的 softmax 情形，固定有效候选集合、发送上限与温度。按有效候选编号，评分到发送强度的 Jacobian 为

$$
J_s=\frac{\operatorname{diag}(c)-cc^\top}{\tau},
\qquad
\frac{\partial c_v}{\partial s_u}
=\frac{c_v}{\tau}\bigl(\mathbf1[v=u]-c_u\bigr).
$$

该矩阵对称，每行绝对值之和为 $2c_v(1-c_v)/\tau\le1/(2\tau)$，故 $\|J_s\|_2\le1/(2\tau)$。有限评分下，至少两个有效候选时各自的对角导数为正；只有一个有效候选时整个 Jacobian 为零。所有评分同时平移不改变分配。

沿用第 8.3 节的 $g_v=\partial\mathcal L/\partial c_v$，由上述 Jacobian 得

$$
\frac{\partial\mathcal L}{\partial s_v}
=\frac{c_v}{\tau}\left(g_v-\sum_u c_u g_u\right).
$$

固定 keys 与局部评分，仅沿式 (26) 的匹配评分求导，则在选择函数的可微分支内有

$$
\nabla_{Q_j^{\mathrm{sel}}}\mathcal L
=\frac{\alpha_j^{\mathrm{sel}}}{\sqrt{d_{\mathrm{sel}}}}
 \sum_{v\in C}\frac{\partial\mathcal L}{\partial s_v}K_v^{\mathrm{sel}}.
$$

完整参数导数还需沿 query 的汇集、keys、局部评分、发送上限及记忆依赖回传。在固定发送上限、keys、局部评分和温度的条件下，quad 将调整后评分除以温度，再欧氏投影到固定的多面体 $F(\mu)$，故 $Q_j^{\mathrm{sel}}\mapsto c$ 分段仿射；softmax 则对 query 光滑。这里描述的是局部映射的性质。

## 9. 数值连续性与软硬极限

本节分别考察输入变化和温度变化。每项结论都固定图、模型参数及相应配置；运行从空记忆开始。有限时间范围内的值按消息的原始身份对齐，完整证明见附录 A。

### 9.1 比较消息与有效记忆

取整数时间边界 $B>0$，称为切面；它分开已处理时刻 $[0,B)$ 与后续时刻。记忆长度可以变化，保存序列也可能保留已过期条目。先固定有限个可能的外部输入位置，每个位置由端口、输入序号和注入时刻确定，称为输入槽；每个槽允许有值或缺席。内部消息按边与发送时间对齐，输出按端口与输出时间对齐。节点记忆则按原始写入时刻对齐，缺失条目补零。在比较时刻 $\theta\le B$ 定义

$$
\pi_{\mathrm{KV},v,\theta}(q)
=\bigl(
\chi_{v,\theta}(\xi)w_\xi,\
\chi_{v,\theta}(\xi)w_\xi k_\xi,\
\chi_{v,\theta}(\xi)w_\xi\nu_\xi,\
\chi_{v,\theta}(\xi)w_\xi p_\xi
\bigr)_{0\le\xi\le B}.
\tag{30}
$$

候选的计算状态在其处理时间比较，切面状态在切面时间比较。这里比较的是可读的加权记忆，不要求弱条目的裸 key/value 收敛。

一条任意弱的正接收可能触发式 (6) 清掉旧过期项，而零接收保留原列表，故保存列表未必连续。式 (30) 在两种情况下都把过期项置零；这些项以后也不会重新进入窗口。前向连续性因此使用这个时刻相关投影，同一函数的精确求值仍返回其定义要求的原始状态。

### 9.2 弱消息与最后一条记忆

在有限有界输入邻域内，式 (3) 或 (20) 是内容的加权平均加有界非线性项，$u$ 有界。正极限接收强度处，$u$ 连续；总强度趋零时，$u$ 未必有唯一极限，但新条目的 $w,wk,w\nu,wp$ 全部趋零。归一化中的固定 $\epsilon>0$ 保证投影不因零范数出现奇点。

固定 $\theta$ 时，窗口遮罩和时间衰减只取决于原始时间身份。有效总权重 $W\to0$ 时，式 (16) 满足

$$
\|R_{v,h}\|_2\le a(W)\max_i\|\nu_{i,h}\|_2\longrightarrow0.
$$

固定位置函数与旋转频率后，这些结论对 NoPE、完整及部分 RoPE 均成立。旋转保持范数，固定时间槽使位置和窗口不随弱消息消失而移动。若用有效条目的序号编码位置，删除一个弱条目可能改变其后所有位置，便失去此前提。有界性与读取连续性的证明见附录 A.2--A.3。

### 9.3 零消息删除与全候选参考计算

固定 $\tau_{\mathrm{soft}}>0$，式 (12) 的解随评分与发送上限连续，并在固定各候选与总和约束的分支内分段光滑。比较候选消失时，在该节点的位置补上 $\mu_v=c_v=0$。发送上限趋于正值的候选要求评分收敛；发送上限趋零的候选只要求评分有界。时间摘要和内容检索均满足相应读取条件；区域 Attention 的加权 query 排除消失候选的影响，保留候选的评分因而收敛。

式 (9) 的发送上限使弱候选的发送强度随接收强度消失；当整个区域的发送上限之和趋零时，总和下限也趋零。接收强度为零和没有输入都保持状态，硬函数也忽略零上界。为了比较“跳过零发送”与“保留零发送”，另定义全候选参考计算：使用同一个软选择解 $c$，将激活集合改为 $A=C$。发送强度为零的节点调用式 (18) 的零分支，因而增加零 Full、零消息和相应输入记录。这个参考计算用于比较数值贡献。

由此得到：

> [!theorem] 性质 1：零消息删除
> 采用本函数族的软选择或硬选择时，增加或删除零强度消息不改变其余正强度计算及有效状态、局部消息投影和外部读出。按式 (13) 激活与全候选参考计算具有相同的这些数值；原始候选、Full、消息和输出事件记录可以不同。

选择连续性与性质 1 的正式证明见附录 A.4--A.5。比较同一函数的两种求值方法时，仍须保留该函数定义的全部事件记录。数值投影相等与反向规则相等各有自己的条件。

### 9.4 弱接收沿路径放大

令 $\alpha_{\mathrm{agg}}=\alpha_{\mathrm{att}}=\alpha_{\mathrm{ff}}=0$，每步发送强度为 $1$ 的单路径给出 $(1,u)\mapsto(1,u)$，可作为尺度基准。恢复残差分支后，尺度还受网络参数控制；带来源聚合会改变内容，不能再把整块称为恒等映射。

弱写入可以触发对已有强记忆的读取。发送贡献为 $cG_v$：有界增益可以提高 $c$，已有记忆与 Full 参数可以改变 $G_v$。两者分别影响强度与内容；新证据的写入仍为 $w(r)$，不会因唤醒旧记忆而变强。

在每区只有一个有效候选、无其他输入的单路径上，非空约束给出 $c=\mu$。若沿路固定增益均为 $4$，接收强度 $0.01$ 可依次产生 $0.04,0.16,0.64,1$ 的发送强度。弱信号因此可以在有限路径内恢复到单位强度。多个候选竞争时，发送强度可以低于上限，放大机会不保证一定被使用。

在无其他输入的长度 $L$ 单路径上，若各步增益上界为 $\Gamma_\ell<\infty$，则末端强度满足 $c_L\le r_0\prod_{\ell=1}^L\Gamma_\ell$。固定有限路径上，$r_0\to0$ 仍使发送及有界内容的贡献趋零。若要求任意小的正接收都立即产生固定非零强度，就会在零处不连续。本文的固定有限增益兼容弱接收放大与零边界连续性，不给出无限路径上的一致稳定性。增益增大使截断条件更早满足；上界饱和后，增益到上界的局部导数为零。

### 9.5 固定正温度的连续性

> [!theorem] 命题 2：固定正温度的数值连续性
> 固定有限正时延图、有限输入槽集合及其注入时刻、全部参数与配置，包括窗口、位置函数和旋转频率，以及有限切面 $B$。从空缓存开始，若输入的式 (1) 投影收敛到极限输入，且所考察输入内容有界，则固定 $\tau_{\mathrm{soft}}>0$ 下，切面以前按时间对齐的局部消息与 Full 各载荷的式 (1) 投影、KV 状态的式 (30) 投影及切面以前有限输出槽的连续读出收敛到极限输入对应的运行。相同结论适用于 $\tau_{\mathrm{soft}}$ 趋向一个正值。

证明见附录 A.6。弱写入与弱发送带趋零权重，区域 query 按发送上限加权，位置及窗口按固定时间槽解释。证明覆盖第 2—7 节的全部聚合、记忆描述、评分、有界增益与预算正则组合；$\alpha_j^{\mathrm{ent}}$ 和 $\gamma_{\max}$ 属于固定配置。

内部消息逐边比较，输出逐端口比较。命题允许候选消失、有效候选全空和正时延反馈；原始缓存列表、激活集合、消息条数与 Full 调用数可以变化。连续依赖上述读出的标量目标也连续。

### 9.6 一次选择的零温极限

先只比较同一个有限候选集合上的优化问题。令温度 $\tau_n\downarrow0$、发送上限 $\mu^{(n)}\to\mu^*$；在 $\mu_v^*>0$ 的候选上，调整后评分 $t_v^{(n)}\to t_v^*$，其余评分保持有界，并在极限问题中取 $t_v^*=0$。整数 $k$、正则类型及 ent 的形状参数固定。若极限线性问题

$$
\mathop{\arg\max}_{c\in F(\mu^*)}\sum_v t_v^*c_v
$$

只有一个最优解，则软选择解收敛到它。证明见引理 A.3：正则在可行范围内有界，乘以趋零温度后消失，可行集也随发送上限连续变化。固定 $\mu,t$ 而只改变温度，是这一结论的特例。

这个结论首先确定一个线性优化问题的解。它与第 4.4 节硬选择的关系，取决于极限发送上限和评分。下一节给出整网运行中两者相等的条件。

### 9.7 单位输入的整网软硬收敛

固定同一个图、参数和外部输入，分别让每次区域选择采用软函数或硬函数，称为软运行、硬运行。软运行中，消息、记忆、发送上限和评分都可能随温度变化；硬运行直接使用第 4.4 节的排序规则。

先考察硬运行。外部载荷取 $(1,z)$，这里限制的是强度坐标，内容 $z$ 可为任意给定的有限向量。更早的硬发送强度为 $0/1$ 时，当前接收总强度是非负整数；$1\le\gamma_v\le\gamma_{\max}$ 使

$$
\mu_v=\min(1,\gamma_v r_v)\in\{0,1\},\qquad
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in A]\in\{0,1\}.
$$

按逻辑时间归纳，硬运行的发送强度、发送上限和写入权重均取零或一。此步只使用硬函数与单位外部强度。

对硬运行中每次选择，以下评分条件保证第 9.6 节的极限线性问题有唯一最优解，且该解等于式 (14)：

- 有效候选至多一个时，无须评分条件。
- $k_j=1$ 且有效候选至少两个时，最高分与次高分严格分离。
- $k_j>1$ 且有效候选至少两个时，各有效调整后评分 $t_v\ne0$。正评分数超过 $k_j$ 时，第 $k_j$ 名与下一名严格分离；没有正评分时，最高分与次高分严格分离。

各情形的唯一性见附录 A.4。将其与第 9.6 节的局部极限结合，可沿逻辑时间逐次推进。

> [!theorem] 命题 3：单位输入的整网软硬收敛
> 固定有限正时延图、有限切面、全部模型参数与配置，以及单位强度外部输入 $(1,z)$，从空缓存开始。若硬运行的每次选择均满足上述对应情形的评分条件，则软运行 $\tau_{\mathrm{soft}}\downarrow0$ 的消息、有效缓存和连续读出投影收敛到硬运行。

证明按时间归纳：更早的软发送收敛，当前接收、有效记忆、上界与相关评分随之收敛；端点是刚才独立确定的硬运行，其发送上限均为零或一，局部唯一性再给出控制量收敛。逐次推进即可得到整网结论，正式证明见附录 A.7。

正温度的软运行允许某些 $0<\mu_v<1$；这些上限与消息、状态一起随温度变化。上述结论对满足条件的每个固定输入及有限切面成立，涵盖全连接、稀疏 HB、多区域与正时延反馈图。参数和配置随训练步骤变化时，所得轨迹还包含这些额外变化。

### 9.8 条件的作用与反例

**选择边界。** 取 $\mu=(1,1,1)$、$t=(3,3,1)$、$k=2$ 给出唯一发送强度分配 $(1,1,0)$；相等评分位于已经选中的集合内部。改为 $t=(3,1,1)$ 时，预算边界有平票，线性最优解可在后两个坐标分配。固定节点序决定硬函数的一个结果，软极限由正则及趋近方式决定。

最小的传播例子是两个发送上限均为 $1$ 的节点、相同评分、$k=1$ 与 quad。每个正温度均有 $c=(1/2,1/2)$；各自再连向一个独立区域的单节点，固定增益为 $1$，下游上界与发送均为 $1/2$。这是合法的两层 SettleGraph，说明还需评分条件才能由硬运行的零或一发送强度，推出软运行收敛到它。

**阈值边界。** 取 $\mu=(1,1)$、$k=2$ 与 quad，局部评分列 $t^\tau=(1,\tau/2)$ 在 $0<\tau<1$ 时给出 $c^\tau=(1,1/2)$。端点评分为 $(1,0)$，硬函数给出 $(1,0)$。这里缺少阈值间隔，极限线性问题有多个最优解。

**固定介于零和一之间的发送上限。** 取 $\mu=(0.9,0.8)$、$t=(-2,-1)$、$k=1$。软可行域要求发送强度之和为 $1$，唯一线性最优解为 $(0.2,0.8)$；硬函数保留最高分候选，给出 $(0,0.8)$。这里仅降低温度，始终固定 $\mu=(0.9,0.8)$；命题 3 则比较同一外部输入下的整网运行，发送上限随运行一起趋于零或一。

### 9.9 在正温度精确得到硬选择的分配

固定每个 $\mu_v\in\{0,1\}$，并固定满足 §9.7 条件的评分。有效候选至多一个时，可行集为单点，全部正则在任意正温度都给出硬选择的发送强度。其余情况下，quad 的充分温度界为：

| 情形 | 足够的温度界 |
|---|---|
| $k=1$，或全部有效评分为负 | $\tau\le t_{(1)}-t_{(2)}$ |
| $k>1$，正评分数在 $1$ 至 $k$ 之间 | $\tau\le\min_{t_v>0}t_v$ |
| 正评分数超过 $k$ | $\tau\le t_{(k)}-t_{(k+1)}$ |

$t_{(i)}$ 表示有效候选按调整后评分降序排列的第 $i$ 项。ent 在固定 $\alpha>1$ 时也有充分小的正温度区间，精确产生同一硬选择的发送强度；其零与单位响应阈值见附录 A.4。bern 与 Shannon 在正温度保持每个有效候选的发送强度为正，硬运行排除候选时通过极限达到零值。

这些界把所需温度与相关评分间隔联系起来。共同缩放 $t$ 与 $\tau$ 保持式 (12) 的解；固定阈值而只缩放原始 $s$，则还改变其相对阈值。整网比较采用 §9.7 的时间归纳，局部温度界用于已固定的评分与发送上限。

## 10. 正典接口、拓扑组合与继续

前述局部函数适用于有限正时延图。它们分别实例化 [[positive-delay-graph-finite-cut-learning-note|PositiveDelayGraph]]、[[timed-dag-region-selector-learning-note|TimedDAG]] 与 [[settlegraph-learning-note|SettleGraph]] 的共同接口：图无环时得到 TimedDAG；区域严格分层且各输入位置的到达时间对齐时得到 SettleGraph。结构与时间条件由相应教材或架构实例声明。

### 10.1 函数与参数对应

正典把一次节点作用分为准备 P、区域选择 S、状态采用 U 和完整计算 F。本文依次使用 Agg、Upd、Read、SelStep、Next 和 Full 实现这些步骤。计算状态 $q^{\mathrm{cmp}}$ 在程序表示中也称快照。

正典的 $K_j$ 是区域每次允许激活的节点数量上限，即要求 $|A|\le K_j$。本文按所用选择函数绑定它：

| 选择函数 | 参数 $k_j$ 的用途 | 正典容量 $K_j$ |
|---|---|---|
| 软选择 | 约束 $\sum_vc_v\le k_j$ | $\lvert\mathcal R_j\rvert$ |
| 硬选择 | 约束 $\lvert A\rvert\le k_j$ | $k_j$ |

第 7.8 节的固定尺度 Attention 属于表中的软选择，取 $K_j=|\mathcal R_j|$。第 9.3 节的全候选参考计算也取这一容量。$K_j$ 声明接口允许的激活数量；实际返回的 $A$ 由所选函数确定。

实际 Read 使用式 (10) 的更新后状态。为使正典的三种读取模式均有定义，另定义

$$
\begin{aligned}
\operatorname{Read}_v^-(q,\theta,h)&=\operatorname{Describe}_v(q,\theta,h),\\
\operatorname{Read}_v^0(\theta,h)&=\operatorname{Describe}_v((),\theta,h).
\end{aligned}
\tag{31}
$$

它们分别读取旧状态与空状态。实际描述模式取 $\tau_j=+$；此处的 $\tau_j$ 是正典的模式符号，选择温度始终记为 $\tau_{\mathrm{soft}}$。正典参数 $\kappa_j=1$ 表示所有候选采用接收更新后的状态，称为 BO；本文的 Next 取式 (15)。

| 正典对象 | 本文定义 |
|---|---|
| $P,X_v$ | $\mathbb R^{1+d}$，分别表示消息与聚合结果 |
| $S_v,q_v^{\mathrm{init}}$ | 式 (4) 的有限序列，初态为空 |
| $D_v,\mathsf C_v,Y_j$ | $D_v^{\mathfrak s_j}$、$[0,1]$、$\{*\}$ |
| $\operatorname{Agg}_v,\operatorname{Upd}_v$ | 式 (3) 或 (20)，以及式 (6) |
| $\operatorname{Read}_v^{+, -,0}$ | 式 (10)、(31)，按所选 Describe 读取 |
| $\operatorname{SelStep}_{j,C}$ | 先从描述量取得评分，再按式 (12)、(13) 或式 (14) 返回；历史保持 $*$ |
| $\operatorname{Next}_v$ | 式 (15) |
| $\operatorname{Full}_v$ | $\Delta_v\circ\operatorname{EmitValue}_v$，式 (18) 给出载荷 |
| $\operatorname{ReadOut}_\Lambda$ | 式 (19)，在指定输出坐标集合上读出 |

Agg 接收完整原子集合；Full 返回分别按出边、输出端口编号的两个值族。参数次序与返回值族沿用正典。

### 10.2 局部配置与组合条件

一次运行按区域选择以下函数，未替换时使用表中第一项：

| 选择 | 取值 | 定义位置 |
|---|---|---|
| 聚合投影 | 区域共享、节点独立、来源独立或适配 | §2.1、§7.1 |
| 记忆描述 $\mathfrak m_j$ | sum、qry | §3.1、§7.3 |
| 局部评分 $\mathfrak f_j$ | cat、match | §3.2、§7.4 |
| 区域评分 $\mathfrak s_j$ | ind、att | §3.4、§7.6 |
| 发送增益 $\mathfrak g_j$ | fixed、context | §3.3、§7.5 |
| 软选择的正则 $\mathfrak b_j$ | quad、bern、ent | §4.1、§7.7 |

配置还给出宽度、窗口、归一化常数、矩阵与偏置、残差与评分尺度、摘要衰减、增益界、$k_j,\eta_j$，以及 Read 和 Full 各自的位置旋转。软选择另给正温度，ent 另给固定形状参数。图与时间组合再给出端口日程、来源映射、位置函数和读出坐标集合。

组合须满足 $1\le k_j\le|\mathcal R_j|$；来源映射覆盖全部输入端口和入边；共享矩阵与节点宽度相容；Read 的描述空间与区域 SelStep 相容；窗口、衰减、位置及读出时刻按同一时间安排解释。分段继续同一次运行时保持这些函数与参数。收敛到硬运行另使用第 9.7 节的单位输入与评分条件。

<a id="6-局部批量契约"></a>

### 10.3 联合求值

固定区域 $j$ 与有限逻辑时间窗口 $I=[b,c)$，给定空初态可达运行在 $b$ 的区域节点状态，以及窗口内**区域全部节点、全部时间的完整输入集合**，包括空纤维。边界缓存的写入时间均小于 $b$；输入完整性要求窗口内会到达的输入均已确定，缺席也已确定。区域历史是单点。

1. 对非空纤维应用已绑定的式 (3) 或 (20)，对正接收计算式 (5) 的 KV、摘要特征与权重。
2. 按原始时间构造新增条目的前缀及时间窗口。正接收时过滤并追加，零接收或空纤维时保留原序列，精确恢复各时刻的保存状态。式 (7) 可用窗口和与衰减扫描；式 (22) 可将各次 Read 查询在各自因果窗口上联合求值。
3. Read 产生所选类型的描述量，按区域与时间取得独立或区域匹配评分，再求式 (12) 或 (14)，返回激活、控制和式 (15) 的快照、下一状态。区域 query 只汇集同一时刻的完整候选。
4. 对每节点收集正式 Full 的时间集合 $\Theta$，将激活时刻的查询组成时间批；每个查询只读取其快照内的因果时间窗口。全候选参考计算还返回全部廉价零 Full 及零消息。

前两步的写入不依赖本地选择或 Full，因此这些前缀恰好等于逐次递归状态；第三步得到同样的描述量与选择。它们构成 [[timed-dag-chunk-prefill-learning-note#3.5 区域控制—状态契约|区域控制—状态契约]] 的见证。第四步在确定快照上求同一个 Full，再按边和端口展开，构成 [[timed-dag-chunk-prefill-learning-note#3.2 逐坐标完整输出契约|逐节点 Full 契约]] 的见证。其中 $\operatorname{RefRegionState}_{j,I}$ 是逐次求值区域准备、选择与状态采用所得的记录；$K^F_{v,\Theta}$ 是节点 $v$ 在时间集合 $\Theta$ 上的 Full 块，$\operatorname{RefBlock}$ 是其逐次求值记录。两个联合函数满足

$$
\begin{aligned}
\operatorname{BatchRegionState}^{\mathrm{KV}}_{j,I}
 &=\operatorname{RefRegionState}_{j,I},\\
\operatorname{BatchFull}^{\mathrm{KV}}_{v,\Theta}
 &=\operatorname{RefBlock}_{K^F_{v,\Theta}}.
\end{aligned}
\tag{32}
$$

第一式返回实际存在的 $P/S/U$ 作用坐标、全部作用值和右边界状态；第二式返回全部正式 $F$ 值及经 $\operatorname{ExpandFull}$ 展开的消息、输出，输入输出类型均沿用正典。

这些契约何时可调用、各层级可得到怎样的批次，由 [[timed-dag-chunk-prefill-learning-note|分块预填充教材]]、[[settlegraph-learning-note#11. 节点级时间批的含义|SettleGraph]] 与 [[positive-delay-graph-finite-cut-learning-note|正时延图教材]] 给出。契约确定联合求值的数值与记录，工作量见附录 S.4。

### 10.4 分段继续

切面 $b$ 上，保存节点状态 $q_v^b$、区域历史 $y_j^b$，以及此前已发出而将在 $b$ 或以后到达的消息集合 $W_b$。沿用正典的边界状态与区间转导：

$$
Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b),
\qquad
\Phi_{a,b}(Q_a,E_{[a,b)})=(\mathcal U_{[a,b)},Q_b).
$$

其中 $E_{[a,b)}$ 是区间内的外部输入，$\mathcal U_{[a,b)}$ 是区间作用记录，$\Phi_{a,b}$ 返回这份记录与右边界状态。由相同 $Q_b$ 开始下一段，条目保留原始 $\xi_i$，新作用沿用全局 $\theta$，所以位置、遮罩、摘要及 Attention 与整段求值相同。相邻区间记录按正典的粘合运算 $\odot_b$ 合并。任意有限次切分，包括有空档的区间，均得到同一完整记录和右边界状态。

本函数族的 $y_j^b=*$；一般切面的 $W_b$ 仍须保留。SettleGraph 的位置边界 $b=Dt$ 满足 $W_b=\varnothing$，可由该位置及各节点状态继续。分段边界不重置时间或位置函数。可并行的批次由图与可用联合契约确定。

## 附录 A：数值连续性的正式证明

### A.1 比较域与时间槽

固定有限正时延图、区域和端口、来源映射、全部模型参数与配置，以及整数切面 $B>0$。窗口允许 $T_v=\infty$，位置函数和频率固定。输入在 $[0,B)$ 内取自一个固定有限槽集合；各槽可有值或缺席。考虑从空缓存开始的一列运行，外部载荷内容一致有界，式 (1) 的槽投影收敛到某个极限输入。温度的变化在相应命题中另行指定。

内部消息按边身份和发送时间对齐，输出按端口和输出时间对齐，写入按节点和原始时间对齐。缺席槽的投影取零。有限图、有限切面与正时延保证潜在槽只有有限个，包括切面前已发送而尚未到达的消息。以下收敛均为这些有限维投影的通常收敛。

同一时间的所有候选在区域内共同选择。证明中可将缺席节点补成 $\mu_v=0,c_v=0$，不增加规范作用；补入坐标的描述特征任取有界值，其对区域 query 的贡献为零；预算比较中零上界坐标的评分也可任取有界值。缓存投影始终在当前比较时刻使用式 (30)。

### A.2 有界性引理

**引理 A.1。** 在 A.1 的条件下，切面以前所有实际聚合内容、KV 内容、摘要、评分与 Full 内容一致有界。该界可选为与正温度无关。

**证明。** 对任意 $x$，$\|\mathcal N_p(x)\|_2\le\sqrt p$。因此式 (5) 的 $k,\nu,p$ 具有固定界，式 (3) 或 (20) 的来源非线性项也有固定界。输入槽数有限、输入投影收敛，使外部有效强度一致有界；内部发送强度由 $0\le c_v\le1$ 控制。每个纤维的潜在原子数有限，故接收强度有界。

按逻辑时间归纳。给定此前发送内容的界，式 (3) 或 (20) 的加权均值范数至多为本次输入内容范数的最大值，加来源项后仍有界。每节点在 $[0,B)$ 至多写 $B$ 项，$0\le w_i\le1$，式 (7) 的摘要有界。式 (22) 的投影、固定时间槽上的旋转和 logit 有界，检索结果为有界 value 的凸组合乘以至多为 $1$ 的尺度，故同样有界；式 (8) 与 (23) 的局部评分由有界输入、固定归一化和有限参数保持有界。式 (9)、(24) 所用的两种增益均处于固定区间 $[1,\gamma_{\max}]$。式 (25) 的特征与 key 有界，式 (26) 的加权汇集范数不超过特征范数的最大值，经过固定连续网络后，区域 query 与全部评分也有界。旋转矩阵范数为 $1$；有限个时间槽的位置值与距离偏置有限，所以式 (16) 及其位置变式 (21) 的匹配分数一致有界。Attention 是有界 value 的凸组合乘 $a(W)\le1$，仍有界。式 (17) 的前馈分支输入经归一化有界，故 Full 内容有界，完成归纳。正时延使这一步只使用更早时间的界。$\square$

本引理只给出固定有限切面上的界，不断言界随 $B$ 增大仍一致。

### A.3 聚合、写入与读取引理

**引理 A.2。** 在 A.2 的有界范围内，有下列结论：

1. 输入槽的式 (1) 投影收敛时，$r$ 收敛；若极限 $r^*>0$，则 $u\to u^*$。
2. 输入槽投影与旧缓存的有效投影均收敛时，接收后的有效投影也收敛。此结论包含 $r^*=0$ 和纤维缺席。
3. 有效缓存投影收敛时，式 (7) 的摘要收敛；若同时 $u\to u^*$，则式 (22)、(16)--(17) 的检索、读取与内容函数收敛。正极限接收处的局部描述特征因此收敛，其余处保持有界。
4. 在同一区域所有候选同时满足以上条件时，式 (26) 的 query 收敛，正极限上界处的最终评分收敛，其余评分保持有界。

**证明。** 各槽有效强度及强度乘内容均收敛，故 $r$ 及加权内容和收敛。正极限强度槽的内容可从这两个坐标相除恢复；零极限强度槽对有界来源非线性项的加权贡献趋零。若 $r^*>0$，式 (3) 或 (20) 的加权分子收敛，分母趋于正数，得到第一项。

正极限接收处，式 (5) 的投影函数和 $w(r)$ 连续。若 $r\to0$，其有界性给出

$$
(w(r),w(r)k_v(u),w(r)\nu_v(u),w(r)p_v(u))\longrightarrow0.
$$

旧槽的遮罩按固定 $\xi$ 取值；式 (6) 清掉的条目在当前时刻的有效投影已经为零。可达旧条目均写于当前时刻以前，以后遮罩也不会从零变回一。因此零接收时保留旧列表与微弱正接收时清理旧列表具有相同的投影极限，并可继续传到下一个比较时刻，得到第二项。

式 (7) 是有效 $w,wp$ 坐标乘固定衰减后求和，再除以至少为 $1$ 的连续分母，故摘要连续。对 Attention，记 $\widehat w_i=\chi_{v,\theta}(\xi_i)w_i$。若极限 $W^*>0$，每个正极限权重槽的 $k_i,\nu_i$ 可由有效加权坐标除以权重恢复；其 logit 与 value 收敛。零极限权重槽的 $\widehat w_i e^{\ell_{i,h}}$ 与 $\widehat w_i e^{\ell_{i,h}}\nu_{i,h}$ 趋零，因为引理 A.1 给出一致界。分母极限严格为正，故商收敛。若 $W\to0$，则

$$
\|R_{v,h}\|_2\le\min(1,W)\max_i\|\nu_{i,h}\|_2\longrightarrow0,
$$

其中空列表的上界取零。式 (22) 的 $W_a$ 使用固定时间衰减，投影与旋转连续且有界，故逐项重复上述商与零总权重论证，得到检索连续性。再应用式 (17)、(8)、(23)、(25) 的连续运算，得到第三项。正极限接收处，两种增益连续，故发送上限收敛；零极限处由 $0\le\mu_v\le\gamma_{\max}(r_v)_+$ 同样得到上界收敛，即使裸内容没有唯一极限。

最后在区域中将缺席候选补成零上界。若 $\mu_v^*>0$，则 $r_v^*>0$，其 $x_v^{\mathrm{sel}},K_v^{\mathrm{sel}},s_v^{\mathrm{loc}}$ 收敛；若 $\mu_v\to0$，有界性给出 $\mu_v x_v^{\mathrm{sel}}\to0$。式 (26) 的分子和分母因此收敛，分母至少为 $1$，故 query 收敛。正极限上界候选的匹配评分随之收敛，其余评分由引理 A.1 保持有界，得到第四项。$\square$

### A.4 带总和上下限的选择引理

**引理 A.3。** 固定含 $m$ 个节点的候选集、整数参数 $k\ge1$ 及式 (11)、(27) 中的一个正则族；entmax 的 $\alpha$ 固定。设 $\mu^{(n)}\to\mu^*$，各上界属于 $[0,1]$，评分 $t^{(n)}$ 一致有界，且在 $\mu_v^*>0$ 的坐标上收敛到 $t_v^*$。令 $c^{(n)}$ 是式 (12) 在温度 $\tau_n>0$ 下的解。

- 若 $\tau_n\to\tau_*>0$，则 $c^{(n)}$ 收敛到相应正温度解。
- 若 $\tau_n\to0$，且极限线性问题的最优解唯一，则 $c^{(n)}$ 收敛到该唯一解。

**证明。** 记

$$
M(\mu)=\sum_v\mu_v,\qquad b(\mu)=\min(1,M(\mu)),
\qquad F(\mu)=\{c:0\le c\le\mu,\ b(\mu)\le\textstyle\sum_v c_v\le k\}.
$$

所有解属于紧集 $[0,1]^m$。若 $c^{(n_l)}\to\bar c$，由 $b$ 连续和闭约束得 $\bar c\in F(\mu^*)$。反之，对任意 $d\in F(\mu^*)$，先取 $a_v^{(n)}=\min(d_v,\mu_v^{(n)})$。若 $\sum_va_v^{(n)}\ge b(\mu^{(n)})$，令 $d^{(n)}=a^{(n)}$；否则令

$$
\begin{aligned}
\delta_n&=b(\mu^{(n)})-\sum_va_v^{(n)},\qquad
R_n=\sum_v(\mu_v^{(n)}-a_v^{(n)}),\\
d_v^{(n)}&=a_v^{(n)}+
 \frac{\delta_n}{R_n}(\mu_v^{(n)}-a_v^{(n)}).
\end{aligned}
$$

后一分支有 $0<\delta_n\le R_n$，修正后发送强度之和为 $b(\mu^{(n)})\le k$，故 $d^{(n)}\in F(\mu^{(n)})$。又因 $a^{(n)}\to d$ 且 $\sum_vd_v\ge b(\mu^*)$，修正量 $\delta_n\to0$，从而 $d^{(n)}\to d$。

令 $I_0=\{v:\mu_v^*=0\}$，将这些坐标的评分改成零，得到 $\widetilde t^{(n)}$。若原评分绝对值至多为 $L_t$，这个替换在整个 $F(\mu^{(n)})$ 上改变目标至多

$$
\epsilon_n=L_t\sum_{v\in I_0}\mu_v^{(n)}\longrightarrow0.
$$

在紧集 $\mathcal D=\{(\mu,c):0\le c\le\mu\le1\}$ 上，三种正则都联合连续且有界。二次与 entmax 项直接由各坐标函数的连续性得到。二元熵在 $\mu_v>0$ 处连续；趋零上界处有

$$
0\le\mu_v h_B(c_v/\mu_v)\le\mu_v\log2\longrightarrow0,
$$

故按零延拓也连续。固定正温度时，目标对有效坐标严格凹；零上界坐标已被约束固定，所以最优解唯一。

记 $\widetilde f_n(c)=\widetilde t^{(n)}\cdot c+\tau_nR(c;\mu^{(n)})$。沿上述可行收敛子列，正温度极限由联合连续性取得；零温度极限中，有界正则乘 $\tau_n$ 趋零。对可行恢复列 $d^{(n)}$ 同理。最优性给出

$$
\widetilde f_n(c^{(n)})
\ge\widetilde f_n(d^{(n)})-2\epsilon_n.
$$

令 $f_*(c)=t^*\cdot c+\tau_*R(c;\mu^*)$，零温情形取 $\tau_*=0$。沿上述子列取极限，得到 $f_*(\bar c)\ge f_*(d)$。因此每个聚点都是极限最优解。正温度下严格凹性给出唯一性；零温度下使用假定的唯一性。所有聚点相同，整列收敛。$\square$

**硬运行的唯一性。** 若 $\mu_v^*\in\{0,1\}$，零上界坐标固定为零。有效候选为空时，可行集只含零向量；只有一个时，总和下限强制该坐标为 $1$。以下设有效候选至少两个。

$k=1$ 时发送强度之和为 $1$，最高分唯一便使全部发送强度集中于该坐标。$k>1$ 时，按第 9.7 节假设所有有效 $t_v^*\ne0$。没有正评分时，负系数使发送强度之和恰为下限 $1$；最高分唯一再确定其分配。有正评分时，负评分坐标取零：将其发送强度转向尚未达到发送上限的正评分候选，或在正评分全满后去掉负评分候选的发送强度，都严格提高目标且保持可行。正评分数不超过 $k$ 时，各正评分均取 $1$；超过 $k$ 时，第 $k$ 名的严格间隔使发送强度恰分配给前 $k$ 个。各情形均给出式 (14) 的唯一发送强度分配。

**有限温度精确性。** 有效候选至多一个时，可行集是单点。其余先看二次族：$k=1$ 或无正评分时，取 $\lambda=t_{(2)}$ 与 $\tau\le t_{(1)}-t_{(2)}$，最高分坐标为 $1$，其余为零；$k=1$ 时总和上下限同时取等号，任意符号的 $\lambda$ 均可分解为非负的 $\lambda_U-\lambda_L$；无正评分且 $k>1$ 时，$\lambda<0$ 对应下限乘子。$k>1$ 且正评分数在 $1$ 至 $k$ 之间时，取 $\lambda=0$ 与 $\tau\le\min_{t_v>0}t_v$；超过 $k$ 时，取 $\lambda=t_{(k+1)}>0$ 与 $\tau\le t_{(k)}-t_{(k+1)}$。代入式 (28) 均得到硬选择的发送强度并满足互补条件。

对 entmax 的固定 $1<\alpha\le2$，在发送上限为 $1$ 的有效候选上，响应精确为 $1$ 和 $0$ 的充分必要条件分别为

$$
t_v-\lambda\ge\tau/\alpha,\qquad
t_v-\lambda\le-\tau/[\alpha(\alpha-1)].
$$

记 $a_\tau=\tau/\alpha$、$z_\tau=\tau/[\alpha(\alpha-1)]$。选取最高分一个时，可令 $\lambda=t_{(2)}+z_\tau$，并要求 $a_\tau+z_\tau\le t_{(1)}-t_{(2)}$；无正评分且 $k>1$ 时，再要求 $z_\tau<-t_{(2)}$，使下限乘子符号正确。正评分数超过 $k$ 时，同理用 $\lambda=t_{(k+1)}+z_\tau>0$ 与预算边界间隔。选取全部正评分且数量不超过 $k$ 时，取 $\lambda=0$，要求 $a_\tau\le\min_{t_v>0}t_v$，以及有负评分时 $z_\tau\le\min_{t_v<0}(-t_v)$。严格间隔保证这些条件在充分小的温度成立，式 (28) 给出唯一硬选择的发送强度。

二元熵与 $\alpha=1$ 的响应在 $\mu_v>0$、有限乘子和正温度下严格为正，故无法精确排除有效候选。可行域单点等强制情形直接由约束处理；它们不影响引理的极限结论。

### A.5 性质 1 的证明

增加或删除零强度原子不改变式 (3) 或 (20) 的加权和。已有正接收处的写入与局部描述保持；仅含零消息的纤维有 $r=0$，式 (6) 保持状态，式 (9) 给出 $\mu=0$。式 (7) 与 (22) 的既有读取保持不变；式 (26) 中发送上限为零的候选对 query 的分子、分母贡献均为零，其他候选的最终评分也保持。因此这类候选加入软优化时只增添强制为零的坐标，$M_j,b_j$ 均不变；加入硬排序时也不进入 $C_{\mathrm{eff}}$。其他候选的控制量与单点历史保持。

按正发送强度激活的计算在这些坐标不执行 Full；全候选参考计算按式 (18) 产生零载荷。沿正时延按时间归纳，这些额外零消息只会重复上述情形，不改变后续正强度计算和状态。时间、位置、窗口均不重排，故有效状态、式 (1) 的槽投影及式 (19) 的读出相同。额外候选与零 Full、消息、输出的存在身份可以不同。$\square$

### A.6 命题 2 的证明

令正温度固定或趋于正值。按 $\theta=0,\ldots,B-1$ 归纳，并在每个切面比较有效状态。初始状态为空。正时延使当前内部输入只来自已经比较的更早发送槽，结合外部输入假设，当前完整纤维的载荷投影收敛。由引理 A.2，接收后有效缓存收敛，发送上限收敛，正极限接收处评分收敛，其余评分由引理 A.1 保持有界。缺席候选按 A.1 补成零上界，有效候选全空的情形也包含在内。

引理 A.3 给出控制量收敛。若端点 $c_v^*>0$，由 $c_v\le\mu_v\le\gamma_{\max}(r_v)_+$ 得到 $r_v^*>0$，聚合内容及 Full 内容收敛。若 $c_v^*=0$，实际 Full 内容保持有界，所以

$$
\pi_P(\operatorname{EmitValue}_v)
=(c_v,c_vG_v)\longrightarrow0;
$$

未调用 Full 的槽同样按零比较。广播逐边、逐端口保持这一结论。式 (15) 将接收后的状态直接采用，引理 A.2 的固定遮罩论证又给出下一切面的有效状态收敛，完成归纳。稀疏空档只传递原状态并推进比较时刻。

最后，式 (19) 的分子是消息投影中内容贡献的有限和，分母是有效强度和与 $1$ 的最大值，始终为正，故所有切面以前有限槽的读出收敛。$\square$

### A.7 命题 3 的证明

在硬运行中，初始无内部消息，外部强度为 $1$。若更早发送强度均为 $0/1$，当前总强度便为非负整数；两种增益均满足 $\gamma_v^{\mathfrak g_j}\ge1$，使 $\mu_v\in\{0,1\}$，式 (14) 再发送 $0/1$。按时间归纳，硬运行的所有发送上限与写入权重均取零或一。

现在让软温度趋零，按 A.6 的同一归纳比较软运行与硬运行。聚合、缓存及正接收处评分的收敛仍由引理 A.2 给出。每次硬运行选择满足第 9.7 节对应情形的评分条件，因此 A.4 给出唯一线性最优解，恰为该次硬选择的发送强度；引理 A.3 的零温度结论给出软控制量收敛。后续发送和状态采用与 A.6 相同，故消息、有效缓存及连续读出收敛。$\square$

这些命题允许有限切面内的正时延反馈，但不推出无限时域稳定性、梯度连续性或训练收敛。位置函数、频率、离散时间槽和窗口固定，是上述比较的共同前提。

## 附录 S：计算表示与数学对象

### S.1 状态、旋转与解码

沿用正典的“表示解码，再遗忘辅助坐标”两步关系。共享 KV 存储和不可变窗口视图可以表示式 (4) 的序列。设表示空间为 $\widehat S_v$、解码函数为 $\operatorname{decode}_v:\widehat S_v\to S_v$，每个 Full 视图须满足 $\operatorname{decode}_v(\widehat q^{\mathrm{cmp}}_{v,\theta})=q^{\mathrm{cmp}}_{v,\theta}$。边界缓存作为左前缀，新增条目按时间追加；视图还需保留所用函数清理后的确切序列范围，包括尚未触发清理时的过期条目身份。

联合求值可先返回这种表示，经固定 Decode 得到数学值记录，再由 $\Pi_K^{\mathrm{blk}}$ 删除辅助字段；这里 $K$ 是正典中的计算块名称。解码忠实恢复已经表示的序列、控制和快照，不调用参考递归补写或修补结果。按式 (30) 比较有效状态允许某些原始列表不同，不可据此声称同一函数配置的完整记录相等。进一步压缩或提前清理若不能解码为原状态，就需另行声明所比较的投影。

实现可保存原始 key，也可保存 $\widehat k_{i,h}=\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\xi_i))k_{i,h}$。后一表示经同一配置的逆旋转恢复原始 key；每项仍须保留 $\xi_i$，用于窗口、摘要和解码。Query 在自己的处理时间旋转，已旋转 key 避免重复旋转。节点、时间和配置身份共同确定旋转含义。

跨 chunk 继续须保存可恢复的 $Q_b$，并使用同一参数与位置配置。更改频率、坐标尺度或局部函数后，旧缓存通常已包含旧计算的结果；仅重旋转 key 不足以取得新函数配置从头运行的状态。继续、重算或显式状态转换应各自声明比较关系。

式 (22) 的检索投影须从原始 key 取得，再施加 Read 自己的旋转；Full 的已旋转 key 通常不能直接代入该投影。可额外保存检索 key/value 投影，作为固定参数下的辅助表示，主状态仍须按声明解码。

式 (16) 可对正有效权重使用 $\ell_{i,h}+\log\widehat w_i$ 的稳定 softmax，再乘 $a(W)$；零权重遮罩，空记忆直接返回零。式 (22) 同样可在正权重上采用稳定加权 softmax，并乘 $\min(1,W_a)$。KV 内容与权重分开保存，不以微小权重作除法恢复内容。有限精度下的下溢、近零阈值裁剪及替代反向需要另行声明；它们不能直接冒充本文的精确零规则或数学连续性结论。

### S.2 配置与数学函数

组合配置逐区域选择聚合共享方式、记忆描述、Read 与 SelStep 的成对绑定、节点宽度、窗口、位置函数，以及 Read 和 Full 的旋转参数，再绑定图、时间、来源及读出。宽度、坐标配对、预算和端口类型检查通过后，得到确定的参数空间和状态空间；给定参数值、初态和输入，参考递归唯一确定前向记录。

局部选项可按下表直接命名，实现名称与数学绑定一一对应：

| 配置键 | 数学对象 | 取值及定义 |
|---|---|---|
| memory | $\mathfrak m_j$ | sum：式 (7)；qry：式 (22) |
| local_score | $\mathfrak f_j$ | cat：式 (8)；match：式 (23) |
| region_score | $\mathfrak s_j$ | ind 或 att：第 3.4、7.6 节的 Describe 与 SelStep 评分 |
| send_gain | $\mathfrak g_j$ | fixed 或 context：式 (9)、(24)，另绑定 gamma_max 与相应参数 |
| budget_family | $\mathfrak b_j$ | quad、bern 或 ent：式 (11)、(27) |
| ent_alpha | $\alpha_j^{\mathrm{ent}}$ | ent 使用的固定形状参数，范围 $[1,2]$ |
| selection_mode | 所用软／硬函数 | soft：式 (12)、(13)；hard：式 (14)，另声明全候选参考计算时的记录规则 |
| tau_soft | $\tau_{\mathrm{soft}}$ | soft 使用的正温度；固定尺度选择在训练与推理中保持同一个值 |
| k | $k_j$ | 软选择的发送强度总和上限、硬选择的激活数量上限 |
| eta | $\eta_j$ | 调整后评分 $t_v=s_v-\eta_j$ 的共同阈值 |
| alpha_loc、alpha_sel | $\alpha_j^{\mathrm{loc}},\alpha_j^{\mathrm{sel}}$ | att 的局部评分与区域匹配尺度，见式 (26) |

基线依次为 sum、cat、ind、fixed、quad。每个配置确定参数空间、状态空间与相应前向函数，各族的反向目标见 S.3。相容组件可通过上述名称组合。

第 7.8 节的固定尺度 Attention 可直接绑定 region_score=att、alpha_loc=0、alpha_sel=1、selection_mode=soft、budget_family=ent、ent_alpha=1，并固定 tau_soft，例如取 $1$。取 k=1 且每次有效候选的发送上限均为 $1$ 时，用普通 softmax 求值；其他发送上限继续求原约束问题。记忆描述、位置与增益独立配置。训练温度日程和推理采用的函数分别由实验配置声明；soft 表示所用数学函数。

更改评分、正则、增益或位置配置，可能改变参数形状、前向函数与历史缓存；形状相同也不保证 checkpoint 的数值兼容。软转硬按第 9.7 节比较；其他切换的状态转换需另行给出。

异构组合可给其他区域绑定不同的状态、Upd、Read 和 Full，但须先完整定义该函数族及其组合条件。本文证明覆盖所定义的 KV 函数；循环记忆需要自己的零消息、状态连续性及批量求值论证。正时延反馈图还须由任务声明有限切面与读出时刻。

### S.3 软选择的求解与反向

**前向。** 输入为按候选编号的向量 $(t,\mu)$、整数 $k\ge1$、温度 $\tau>0$ 及固定正则配置，其中 $0\le\mu_v\le1$，输出为式 (12) 的唯一发送强度分配。先计算 $M=\sum\mu,b=\min(1,M)$，按第 4.2 节的单点可行集情形直接返回相应分配。

ent 的 $\alpha=1$、$k=1$ 且全部有效发送上限为 $1$ 时，第 7.8 节给出直接 softmax 求值，前向与评分反向均为 $O(|C|)$。在有效候选上先减去最大评分再计算指数，零上限坐标置零；这一求值具有第 8.5 节的评分与 query 导数。形状保证或本次输入满足这些条件时即可采用；其他情形使用以下约束求解。

定义 $S(\lambda)=\sum_v g_{\mathfrak b}(t_v-\lambda,\mu_v;\tau)$。$M>1$ 时先求 $\lambda=0$ 的响应。发送强度之和位于 $[b,k]$ 时直接返回；过大或过小时，分别求发送强度之和 $B=k$ 或 $B=b$ 的根。此时必有 $0<B<M$。令 $q=B/M\in(0,1)$，对有效候选定义满足 $g_{\mathfrak b}(x_v,\mu_v;\tau)=q\mu_v$ 的值：

| 正则 | $x_v$ |
|---|---|
| quad | $\tau q\mu_v$ |
| bern | $\tau\log(q/(1-q))$ |
| ent，$\alpha=1$ | $\tau[1+\log(q\mu_v)]$ |
| ent，$\alpha>1$ | $\tau[(q\mu_v)^{\alpha-1}-1/\alpha]/(\alpha-1)$ |

取

$$
\lambda_{\mathrm{lo}}=\min_{v:\mu_v>0}(t_v-x_v),\qquad
\lambda_{\mathrm{hi}}=\max_{v:\mu_v>0}(t_v-x_v).
$$

响应单调给出 $S(\lambda_{\mathrm{lo}})\ge B\ge S(\lambda_{\mathrm{hi}})$。依次二分即可保留含根区间；也可取 Newton 步 $\lambda+(S(\lambda)-B)/\sum_v a_v$，仅在斜率非零且试探点落入保留区间时采用，否则退回二分。上限根应有非负乘子，下限根应有非正乘子；根区间可与对应半轴相交。平坦区间上乘子可能不唯一，发送强度仍唯一。

若初始区间宽度为 $D>0$，达到乘子区间宽度 $\varepsilon_\lambda$ 的二分工作量为 $O(|C|\max(1,\log_2(D/\varepsilon_\lambda)))$。若两端相同则直接求值。总和约束残差与坐标误差另用斜率界或区间两端的发送强度差判断；温度越小，同样的乘子误差可能导致更大发送强度误差。停止条件同时核对可行性与最优性残差，数值实现报告实际迭代和误差，不预设固定次数总能满足精度。

二次族还能按 $t_v-\tau\mu_v,t_v$ 排序并扫描分段，工作量为 $O(|C|\log|C|)$。在未触及上下限的候选集 $\mathcal F=\{v:0<c_v<\mu_v\}$、达到发送上限的候选集 $\mathcal U=\{v:c_v=\mu_v>0\}$ 及总和 $B$ 固定时，

$$
\lambda=\frac{\sum_{v\in\mathcal F}t_v+
 \tau\sum_{v\in\mathcal U}\mu_v-\tau B}{|\mathcal F|}
\qquad(\mathcal F\ne\varnothing).
$$

候选解须位于对应分段并满足互补条件；$\mathcal F=\varnothing$ 时直接验证饱和分配。ent 的 $\alpha=2$ 可按式 (29) 移位后用同一算法。其他族均可采用上述标量求根；无需通用高维优化器。

**隐式反向。** 以下在固定约束分支与光滑区间内求导，$\tau,\alpha$ 固定。设 $x_v=t_v-\lambda$，定义 $a_v=\partial g/\partial x_v$、$e_v=\partial g/\partial\mu_v$，后者保持 $x_v$ 不变：

| 候选的发送强度状态 | $a_v$ | $e_v$ |
|---|---|---|
| quad，未触及上下限 | $1/\tau$ | $0$ |
| ent，未触及上下限 | $c_v^{2-\alpha}/\tau$；$\alpha=1$ 时为 $c_v/\tau$ | $0$ |
| bern，$p_v^{\mathrm{occ}}=c_v/\mu_v\in(0,1)$ | $\mu_vp_v^{\mathrm{occ}}(1-p_v^{\mathrm{occ}})/\tau$ | $p_v^{\mathrm{occ}}$ |
| quad 或 ent，上界饱和 | $0$ | $1$ |
| quad 或 ent，零饱和 | $0$ | $0$ |

零上界坐标作为强制零处理，是否向正上界移动属于边界约定。若发送强度之和固定在 $B$，且 $A_0=\sum_v a_v>0$，微分约束给出

$$
d\lambda=\frac{\sum_v a_v\,dt_v+\sum_v e_v\,d\mu_v-dB}{A_0},
\qquad
dc_v=a_v(dt_v-d\lambda)+e_v\,d\mu_v.
$$

令上游梯度为 $g_v^{\mathcal L}=\partial\mathcal L/\partial c_v$，并记
$\bar g=\sum_v a_vg_v^{\mathcal L}/A_0$。向量—Jacobian 乘积为

$$
\frac{\partial\mathcal L}{\partial t_v}
 =a_v(g_v^{\mathcal L}-\bar g),\qquad
\frac{\partial\mathcal L}{\partial\mu_v}
 =e_v(g_v^{\mathcal L}-\bar g)+
   \bar g\,\frac{\partial B}{\partial\mu_v}.
$$

本文 $M>1$ 时的边界是常数 $B=1$ 或 $k$，故最后一项为零。二次正则在集合 $\mathcal F$ 内的评分 Jacobian 为
$\tau^{-1}(I-\mathbf1\mathbf1^\top/|\mathcal F|)$；只有一个未触及上下限的候选且发送强度之和固定时，该评分导数为零。若总和上下限均松弛，则 $\lambda=0$ 固定，直接使用 $dc_v=a_vdt_v+e_vd\mu_v$。在第 4.2 节的 $M<1$ 分支，采用第 8.3 节给出的两个 Jacobian。

当 $A_0=0$ 时不得除以零；严格饱和区内评分导数为零，上界坐标直接沿 $c_v=\mu_v$ 求导。若扰动使总和约束取等号与各候选的饱和状态无法同时保持，则已位于分支边界，应采用声明的单侧或广义导数。$M=1$、精确断点、总和约束松紧交界及增益的 $\min$ 边界也须单独处理。若用硬选择继续训练，其替代梯度或探索另行定义。

反向只需保存发送强度、分支及必要的响应统计量，工作量为 $O(|C|)$，不必保存二分或 Newton 轨迹。这里的目标是精确最优解映射的导数；有限精度求根后代入会产生相应误差。若改为对有限次迭代本身自动求导，则应声明该不同的反向目标。完整梯度还须沿 $t=s-\eta$、上界、区域 query、keys、局部评分和记忆读取回传。若训练温度，在固定 $x,\mu$ 处有 $\partial g/\partial\tau=-a_vx_v/\tau$，再按同一总和约束修正；本文未定义训练 $\alpha$ 的反向。

**数值表示。** sigmoid 使用稳定形式；指数响应先在对数域与上界比较，饱和时直接返回原上界，避免溢出及指数还原上界的舍入误差。$\alpha$ 接近 $1$ 时，逆响应可将分子写为 $\operatorname{expm1}((\alpha-1)\log c)+(\alpha-1)/\alpha$，再除以 $\alpha-1$；正响应可在正底数上使用 log1p。计算中区分数学零、下溢零和人为裁剪零。极小 $a_v$ 与低温未触及上下限的区间具有不同的数值条件，精度对应见 [实现核对](weighted-kv-implementation-checks.md)。

### S.4 局部工作与全图成本

聚合、KV 写入和 Read 在候选上执行，Full 在激活者上执行。Read 的摘要与内容检索具有各自的工作量。下表 $m$ 为本次入消息数，$N$ 为有效 KV 项数。

| 工作 | 典型量级与条件 |
|---|---|
| 接收聚合 | $m$ 条消息的共享式 (3) 约 $O(mp_a d+p_a d)$；式 (20) 逐消息采用自己的绑定 |
| KV 与摘要投影 | 独立求值约 $O(d^2+dr_a+dd_s)$ |
| 时间摘要 | 朴素扫描 $O(Nd_s)$；窗口和与衰减累计可减少重复扫描 |
| 局部评分 | 拼接族约 $O(d_r(d+d_s))$；分组匹配族约 $O(d_r(d+d_s+d_{\mathrm{sel}}))$，含三组编码与门控残差 |
| 发送增益 | 固定增益为标量运算；上下文增益约 $O(d_r(d+d_s))$，特征可与局部评分共用 |
| 内容检索 | query 投影 $O(dd_s)$，已投影记忆上的检索 $O(Nd_s)$；直接重投影记忆另需 $O(Ndd_s)$，保存辅助投影则将此工作移到写入并增加存储 |
| 区域 Attention 描述量 | 每候选约 $O(d_{\mathrm{sel}}(d+d_s))$，局部评分残差按所用配置另计 |
| 区域 query 与匹配 | 每次选择约 $O(\lvert C\rvert d_{\mathrm{sel}}+d_{\mathrm{sel}}^2)$ |
| 发送强度分配 | 第 7.8 节的 softmax 情形为 $O(\lvert C\rvert)$；二次族断点排序为 $O(\lvert C\rvert\log\lvert C\rvert)$；通用标量求根每次 $O(\lvert C\rvert)$，另计迭代与精度；反向为 $O(\lvert C\rvert)$ |
| 激活节点的 Full | $O(d^2+dd_f+Nd)$，$N$ 为当前有效 KV 项数 |
| 每节点缓存 | 有限窗口为 $O(T_v(2d+d_s))$；全历史在切面 $B$ 前至多 $B$ 项，另有时间、权重及可选辅助投影 |

相同来源类别与载荷的多重集，加相同聚合参数，才保证相同的 $(r,u)$。满足此条件时可共享聚合与 KV 基座投影；相同参数面对不同邻域时，仍须求不同的聚合与投影。HB 中的参数共享一般只减少参数和便于批量求值，不能自动把全区域准备合为一次。共享表示还须恢复各节点的确切状态。

记 $\mathcal E_C,\mathcal E_A$ 为一段运行内候选、激活者的节点—时间坐标，$\mathcal E_S$ 为实际区域选择坐标，$\mathcal M$ 为发出的内部消息。按不重复归属的工作量或累计执行时间，全图工作量为

$$
\begin{aligned}
\mathcal W={}&\sum_{(v,\theta)\in\mathcal E_C}
 (C_{v,\theta}^{\mathrm{Agg}}+C_{v,\theta}^{\mathrm{KV}}+C_{v,\theta}^{\mathrm{Read}})
 +\sum_{(j,\theta)\in\mathcal E_S}C_{j,\theta}^{\mathrm{Sel}}\\
 &+\sum_{(v,\theta)\in\mathcal E_A}C_{v,\theta}^{\mathrm{Full}}
 +\sum_{m\in\mathcal M}C_m^{\mathrm{msg}}.
\end{aligned}
$$

这里各 $C$ 是声明的工作代价，共享计算计一次，缓存读写与输出汇集计入相应项。该和式给出加性工作量；并行执行的跨度还依赖计算之间的偏序。

上游不发送可使下游整组输入缺席，进而移除相应准备、选择、Full 与消息。候选覆盖由出度、父邻域重叠和外部注入共同确定。[全连接实例](weighted-kv-layered-example.md#4-整窗口求值与架构成本)与 [HB 实例](weighted-kv-hb-lattice-example.md#4-候选传播与全图成本)给出具体计数。
