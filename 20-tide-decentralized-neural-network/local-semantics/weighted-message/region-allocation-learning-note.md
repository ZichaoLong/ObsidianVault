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

# 区域评分与发送分配

区域接收候选节点的描述，先形成评分，再决定各节点发送多少。本文将信息读取、评分和分配分别定义。相同评分可以接稠密 Attention、约束优化或硬排序；各函数的支持、梯度和极限由自己的定义确定。

消息、候选、归一化和广播沿用[局部架构教材](architecture-learning-note.md)。固定区域 $j$ 的一次选择，候选集为 $C\subseteq\mathcal R_j$。$r_v^{\mathrm{in}},u_v$ 是候选 $v$ 的接收强度与聚合内容，记忆模块提供 $p_v(u_v)$、两个 $d_s$ 维描述 $M_{v,a}$ 和非负统计量 $W_{v,a}$，$a\in\{\mathrm{short},\mathrm{long}\}$。矩阵、偏置均为有限参数。

## 1. 节点向区域提供什么

### 1.1 接收量与发送增益

定义截断后的接收量 $w_v=\min(1,(r_v^{\mathrm{in}})_+)$。取有限 $\gamma_{\max}\ge1$，令

$$
1\le\gamma_v\le\gamma_{\max},\qquad
\mu_v=\min(1,\gamma_v(r_v^{\mathrm{in}})_+).
\tag{1}
$$

$w_v$ 描述本次接收，$\mu_v$ 允许有界放大。在约束分配、直接 Attention 与硬选择中，$\mu_v$ 是发送上限；其他分配会使用它作为权重或总量依据。始终有 $w_v\le\mu_v\le\gamma_{\max}w_v$，两者具有相同的正分量位置。

固定增益直接给定，或取 $\gamma_v=1+(\gamma_{\max}-1)\sigma(\zeta_v)$。上下文增益可由当前内容与记忆计算，具体参数化见下节。

### 1.2 独立局部评分

为简洁省略节点下标，所有记忆量均在所选 Read 状态、当前 $\theta,u$ 上求值。取正整数隐藏宽度 $d_r$、矩阵 $W_v^r\in\mathbb R^{d_r\times(d+4d_s+3)}$、向量 $b_v^r,a_v^{\mathrm{cat}}\in\mathbb R^{d_r}$ 和标量 $b_v$。拼接评分（cat）定义为

$$
\begin{aligned}
f_v=\big[&\mathcal N_d(u);\log(1+(r^{\mathrm{in}})_+);M_{\mathrm{short}};M_{\mathrm{long}};
 \log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}});\\
 &p_v(u)\odot M_{\mathrm{short}};p_v(u)\odot M_{\mathrm{long}}\big],\\
s_v^{\mathrm{cat}}&=b_v+(a_v^{\mathrm{cat}})^\top\operatorname{SiLU}(W_v^r f_v+b_v^r).
\end{aligned}
\tag{2}
$$

$f_v$ 的宽度为 $d+4d_s+3$。矩阵的不同列分别作用于内容、统计量与交互项。

另一种评分先分组编码。令

$$
z^{\mathrm{cur}}=\mathcal N_d(u),\quad
z^{\mathrm{mem}}=[M_{\mathrm{short}};M_{\mathrm{long}}],\quad
z^{\mathrm{stat}}=[\log(1+(r^{\mathrm{in}})_+);\log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})].
$$

固定正整数匹配宽度 $d_{\mathrm{sel}}$。对 $g\in\{\mathrm{cur},\mathrm{mem},\mathrm{stat}\}$，取相容形状的矩阵与偏置，定义两层编码
$E_v^g(z)=\mathcal N_{d_{\mathrm{sel}}}(C_v^{\mathrm{enc},g}\operatorname{SiLU}(B_v^{\mathrm{enc},g}z+b_v^{\mathrm{enc},g})+d_v^{\mathrm{enc},g})$，中间宽度为 $d_r$，并定义

$$
\begin{aligned}
x_v&=E_v^{\mathrm{cur}}(z^{\mathrm{cur}}),\quad e_v=E_v^{\mathrm{mem}}(z^{\mathrm{mem}}),
 \quad z_v=E_v^{\mathrm{stat}}(z^{\mathrm{stat}}),\quad f_v^{\mathrm{match}}=[x_v;e_v;z_v],\\
F_v^{\mathrm{match}}(f)&=(w_v^{\mathrm{match}})^\top
 [\operatorname{SiLU}(W_v^{\mathrm{match,gate}}f+b_v^{\mathrm{match,gate}})
 \odot(W_v^{\mathrm{match,up}}f+b_v^{\mathrm{match,up}})],\\
s_v^{\mathrm{match}}&=b_v^{\mathrm{match}}+
 \alpha_v^{\mathrm{match}}x_v^\top e_v/\sqrt{d_{\mathrm{sel}}}
 +\alpha_v^{\mathrm{res}}F_v^{\mathrm{match}}(f_v^{\mathrm{match}}).
\end{aligned}
\tag{3}
$$

门控残差的隐藏宽度为 $d_r$，两个尺度非负。选择 $s_v^{\mathrm{loc}}=s_v^{\mathrm{cat}}$ 或 $s_v^{\mathrm{match}}$。参数默认按节点独立，允许显式共享同形参数。分组的非线性、归一化和匹配构成函数差异。

取 $W_v^\gamma\in\mathbb R^{d_r\times(d+4d_s+3)}$、$a_v^\gamma,b_v^{\gamma,h}\in\mathbb R^{d_r}$ 和标量 $b_v^\gamma$。特征 $f_v$ 进入独立的增益头，定义上下文增益

$$
\gamma_v=1+(\gamma_{\max}-1)\sigma\bigl(b_v^\gamma+
 (a_v^\gamma)^\top\operatorname{SiLU}(W_v^\gamma f_v+b_v^{\gamma,h})\bigr).
\tag{4}
$$

评分与增益采用不同参数。KV 的写入量取 $w_v$，增益不改变这次写入。

### 1.3 描述量与区域评分

独立评分 ind 的描述空间为

$$
D_v^{\mathrm{ind}}=\{(w,\mu,s):0\le w\le\mu\le1,\ \mu\le\gamma_{\max}w,\ s\in\mathbb R\}.
$$

节点传递 $(w_v,\mu_v,s_v^{\mathrm{loc}})$，最终评分 $s_v=s_v^{\mathrm{loc}}$。

区域 Attention 评分 att 另传递当前特征和记忆 key。取 $W_v^{\mathrm{loc}}\in\mathbb R^{d_{\mathrm{sel}}\times d}$、$W_v^{\mathrm{mem}}\in\mathbb R^{d_{\mathrm{sel}}\times(2d_s+2)}$ 及两个 $d_{\mathrm{sel}}$ 维偏置，定义

$$
\begin{aligned}
x_v^{\mathrm{sel}}&=W_v^{\mathrm{loc}}\mathcal N_d(u_v)+b_v^{\mathrm{loc}},\\
K_v^{\mathrm{sel}}&=W_v^{\mathrm{mem}}[M_{v,\mathrm{short}};M_{v,\mathrm{long}};
 \log(1+W_{v,\mathrm{short}});\log(1+W_{v,\mathrm{long}})]+b_v^{\mathrm{mem}},\\
D_v^{\mathrm{att}}&=\{(w,\mu,x,K,s):(w,\mu,s)\in D_v^{\mathrm{ind}},\ x,K\in\mathbb R^{d_{\mathrm{sel}}}\},\\
d_v&=(w_v,\mu_v,x_v^{\mathrm{sel}},K_v^{\mathrm{sel}},s_v^{\mathrm{loc}}).
\end{aligned}
\tag{5}
$$

区域从完整候选集形成一个 query。取 $W_j^{\mathrm{in}},W_j^{\mathrm{out}}\in\mathbb R^{d_{\mathrm{sel}}\times d_{\mathrm{sel}}}$、$b_j^{\mathrm{in}},b_j^{\mathrm{out}}\in\mathbb R^{d_{\mathrm{sel}}}$ 和非负尺度 $\alpha_j^{\mathrm{loc}},\alpha_j^{\mathrm{sel}}$。选择汇集权重 $q_v^{\mathrm{wt}}=\mu_v$ 或 $q_v^{\mathrm{wt}}=w_v$，定义

$$
\begin{aligned}
\bar x_j&=\frac{\sum_{v\in C}q_v^{\mathrm{wt}}x_v^{\mathrm{sel}}}
 {\max(1,\sum_{v\in C}q_v^{\mathrm{wt}})},\\
Q_j^{\mathrm{sel}}&=\psi_j(\bar x_j),\quad
 \psi_j(x)=W_j^{\mathrm{out}}\operatorname{SiLU}(W_j^{\mathrm{in}}x+b_j^{\mathrm{in}})+b_j^{\mathrm{out}},\\
s_v&=\alpha_j^{\mathrm{loc}}s_v^{\mathrm{loc}}+
 \alpha_j^{\mathrm{sel}}(Q_j^{\mathrm{sel}})^\top K_v^{\mathrm{sel}}/\sqrt{d_{\mathrm{sel}}}.
\end{aligned}
\tag{6}
$$

取 $(\alpha_j^{\mathrm{loc}},\alpha_j^{\mathrm{sel}})=(1,0)$ 恢复独立评分的数值。两个汇集权重都使零接收候选对 query 无影响；弱候选的影响趋零。使用 $w_v$ 时，在固定接收和记忆描述的条件下，改变发送增益不改变 query。

区域 query 的汇集量由本节直接定义。它与记忆模块的写入量可以数值相同，也可以不同；更换记忆模块不会隐式改变 query。

## 2. 从评分得到发送强度

控制量 $c_v\in[0,1]$ 表示发送强度，激活集合为 $\mathcal A=\{v\in C:c_v>0\}$。区域历史沿用共同架构的单点 $*$。以下各函数均令 SelStep 返回 $(\mathcal A,(c_v)_{v\in C},*)$，空候选返回空族。记

$$
C_{\mathrm{eff}}=\{v\in C:\mu_v>0\},\quad
M=\sum_{v\in C}\mu_v,\quad S=\sum_{v\in C}c_v.
$$

$C_{\mathrm{eff}}$ 是有正接收的候选，$M$ 是接收相关量 $\mu$ 的总和，$S$ 是本次实际发送强度之和。每个节点在这两个和中分别计一次。

需要温度的函数取 $\tau_{\mathrm{sel}}>0$，单次选择中简写为 $\tau$。温度调节评分差异对分配的影响；它与正典的读取模式 $\tau_j$ 是不同参数。

### 2.1 约束分配

固定整数 $1\le k\le|\mathcal R_j|$、阈值 $\eta\in\mathbb R$ 和温度 $\tau_{\mathrm{sel}}>0$。定义 $t_v=s_v-\eta$、$b=\min(1,M)$，以及

$$
F(\mu)=\{c:0\le c_v\le\mu_v,\quad b\le\sum_vc_v\le k\}.
\tag{7}
$$

这里 $k$ 限制发送强度之和。先定义二元熵 $h_B(p)=-p\log p-(1-p)\log(1-p)$、Shannon 熵项 $h_1(c)=-c\log c$，以及 $\alpha>1$ 时的 $h_\alpha(c)=(c-c^\alpha)/[\alpha(\alpha-1)]$。端点按 $0\log0=0$ 延拓。正则函数 $R$ 取下表中的一种：

| 名称 | 正则 |
|---|---|
| quad | $R=-\tfrac12\sum_vc_v^2$ |
| bern | $R=\sum_{v:\mu_v>0}\mu_v h_B(c_v/\mu_v)$ |
| ent | $R=\sum_vh_\alpha(c_v)$，固定 $\alpha\in[1,2]$ |

零上限的 bern 项取零。给定 $R$，定义分配

$$
c^{\tau_{\mathrm{sel}}}=\arg\max_{c\in F(\mu)}
 \{t\cdot c+\tau_{\mathrm{sel}}R(c;\mu)\}.
\tag{8}
$$

可行集非空、紧且凸，目标在可改变的分量上严格凹，故分配唯一。ent 的 $\alpha=1$ 称为约束 Shannon 选择。

**两个约束性质。** 当 $M\le1$ 时，唯一可行向量为 $c=\mu$：此时下限等于所有上限之和，每个非负差 $\mu_v-c_v$ 必须为零。这个开区域 $M<1$ 内，评分 Jacobian 为零，对 $\mu$ 的 Jacobian 为单位阵。当 $k=1$ 时，总和恒为 $\min(1,M)$，阈值项 $-\eta S$ 是常数；共同阈值不影响解。

一般地，$b\le S\le\min(k,M)$。在同一次优化的可行范围内，总和可以取不同值；给定全部输入后解仍唯一。每个 $c_v\le1$ 给出 $S\le|\mathcal A|$，因此 $k$ 不限制正分量个数。例如 $(0.8,0.6,0.4,0.2)$ 的总和为 $2$，激活四个节点。

**例：分配与饱和。**

记 $\operatorname{clip}(x,l,h)=\min(h,\max(l,x))$。取 $\mu=(1,1),k=1$，评分差 $\Delta=s_1-s_2$，quad 的解为

$$
c_1=\operatorname{clip}\left(\tfrac12+\tfrac\Delta{2\tau},0,1\right),\qquad c_2=1-c_1,
$$

$|\Delta|<\tau$ 时两者均激活；$\Delta>\tau$ 时分配保持 $(1,0)$，小幅评分变化不再改变控制。分量固定在零或发送上限的范围称为饱和区。

取四个单位上限、$t=(4,3,2,1),k=2$，quad 在温度 $5,2,0.4$ 时分别给出 $(0.8,0.6,0.4,0.2)$、$(1,0.75,0.25,0)$、$(1,1,0,0)$。正温度可以产生真实零分量；其是否节约下游准备取决于图。

### 2.2 加权 Attention 的共同定义

给定非负基权重 $a_v$ 和正温度，归一化分母 $Z$ 与份额 $p_v^{\mathrm{sel}}$ 定义为

$$
Z=\sum_ua_ue^{s_u/\tau_{\mathrm{sel}}},\qquad
p_v^{\mathrm{sel}}=\begin{cases}a_ve^{s_v/\tau_{\mathrm{sel}}}/Z,&Z>0,\\0,&Z=0.\end{cases}
\tag{9}
$$

记 $p=(p_v^{\mathrm{sel}})_{v\in C}$。有正基权重时，$p$ 的和为 $1$，正分量恰在 $a_v>0$ 的候选上。非空候选集上取全部 $a_v=1$，得到通常的 $\operatorname{softmax}(s/\tau_{\mathrm{sel}})$。下列三种发送规则均直接使用这个函数，无需求解乘子。

### 2.3 直接 Attention

取 $a_v=\mu_v$ 或 $a_v=w_v$，定义

$$
c_v=\mu_vp_v^{\mathrm{sel}}.
\tag{10}
$$

两种基权重的支持相同，均激活全部有效候选。总和是各节点上限的加权平均：$0<S\le\max_v\mu_v\le1$。每个节点保留 $c_v\le\mu_v$，区域没有式 (7) 的下限。只有一个有效候选时发送 $c_v=\mu_v$。

使用 $\mu$ 时，增益既参与份额又参与幅度；使用 $w$ 时，固定评分和接收后，增益只通过本节点外乘的 $\mu_v$ 生效。再将式 (6) 的 query 权重取为 $w$，就同时移除了增益经 query 影响其他评分的直接依赖。后续消息和未来记忆仍连接整个网络。

### 2.4 固定总强度 Attention

取 $a_v=1$ 或 $a_v=\mu_v$，定义

$$
c_v=p_v^{\mathrm{sel}}.
\tag{11}
$$

有正基权重时 $S=1$，每节点只受 $c_v\le1$ 限制。$a=1$ 激活全部真实候选，包括只收到零强度消息的候选；$a=\mu$ 激活全部有效候选，全零接收时返回零。两种函数均为固定正温度的稠密设计。

在非空单候选处，任意正接收可触发单位发送；$a=\mu$ 在接收趋零处因而不连续。$a=1$ 还保留零强度候选的参与。写入和发送各按自己的定义进行。

### 2.5 区域总量分配

取 $a_v=\mu_v$，先定总量 $B=\min(1,M)$，再定义

$$
c_v=Bp_v^{\mathrm{sel}}.
\tag{12}
$$

$M>0$ 时全部有效候选激活，总和为 $B$；$M=0$ 时全部为零。这里 $\mu_v$ 决定份额及区域总量，单节点上限为 $1$。例如 $\mu=(0.1,0.1)$、$p=(0.9,0.1)$ 时，$c=(0.18,0.02)$，第一项超过本节点的 $\mu_1$。

全部接收趋零时 $B\to0$，故总发送趋零；低总量时仍可依评分重新分配。固定正温度的完整连续性见附录 A。这个函数的温度趋零行为需另行分析。

### 2.6 按比例分配

固定整数 $1\le k\le|\mathcal R_j|$，定义

$$
c_v=\begin{cases}\mu_v\min(k,M)/M,&M>0,\\0,&M=0.\end{cases}
\tag{13}
$$

它将总量 $\min(k,M)$ 按各节点 $\mu_v$ 所占的比例分配，满足式 (7)，在有效候选上全正。评分不参与该函数，因此没有从分配到评分的直接导数。它可以组成完整模型，也可用于研究中的稠密参照。

### 2.7 硬选择

固定整数 $1\le k\le|\mathcal R_j|$ 和阈值 $\eta$，按 $t_v=s_v-\eta$ 对有效候选排序，同分使用固定节点序。有正评分时取前 $\min(k,\#\{v:t_v>0\})$ 个正评分候选；全非正时取最高分的一个；无有效候选时取空集。将所得集合记为 $\mathcal A$，定义

$$
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in \mathcal A].
\tag{14}
$$

此时 $k$ 限制激活数量。硬选择是单独定义的函数，发送强度为 $0$ 或对应 $\mu_v$。它与式 (8) 的关系见第 5 节。

### 2.8 参数与性质对照

| 发送规则 | 每节点上限 | 有正发送时的总和 | 激活范围 | 正典容量 $K_j$ |
|---|---|---|---|---|
| 约束 quad／ent，$\alpha>1$ | $\mu_v$ | $[\min(1,M),\min(k,M)]$ | 可以精确稀疏 | $\lvert \mathcal R_j\rvert$ |
| 约束 Shannon／bern | $\mu_v$ | 同上 | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 直接 Attention，两种基权重 | $\mu_v$ | $(0,\max\mu]$ | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 固定总强度 Attention | $1$ | $1$ | 全部真实或全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 区域总量分配 | $1$ | $\min(1,M)$ | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 按比例分配 | $\mu_v$ | $\min(k,M)$ | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 硬选择 | $\mu_v$ | $\sum_{v\in \mathcal A}\mu_v$ | $1$ 至 $k$ 个有效候选 | $k$ |

正典 $K_j$ 只声明允许的激活数量，$\mathcal A$ 仍由具体函数返回。训练或推理使用哪一种函数由配置给出。固定正温度的任一种函数均可持续使用。

## 3. 例子与恢复关系

### 3.1 同一组输入下的稠密规则

取 $\mu=w=(0.2,1)$、相等评分，约束 Shannon 使用 $k=1$：

| 规则 | $c$ |
|---|---|
| 固定总强度，基权重 $1$ | $(1/2,1/2)$ |
| 固定总强度，基权重 $\mu$ | $(1/6,5/6)$ |
| 直接 Attention | $(1/30,5/6)$ |
| 区域总量分配 | $(1/6,5/6)$ |
| 约束 Shannon | $(0.2,0.8)$ |

四个候选均有 $\mu=w=0.1$ 且评分相等时，上述规则每节点分别发送 $0.25,0.25,0.025,0.1,0.1$。最后两种的同分前向相同，改变评分后的响应可以不同。

### 3.2 与 softmax、sparsemax、entmax 的关系

有效候选非空、各自的 $\mu_v=1$ 且 $k=1$ 时，式 (7) 为概率单纯形 $\{c:c_v\ge0,\sum_vc_v=1\}$。ent 在此集合上的解称为 $\alpha$-entmax；$\alpha=1$ 给出 softmax，$\alpha=2$ 给出称为 sparsemax 的欧氏投影 $\arg\min_{c\in F(\mu)}\|c-s/\tau\|_2^2$，quad 也给出同一投影。最高分唯一时，零温极限只选该候选，称为 Top-1。

上限全为 $1$ 保证上述等式对任意评分成立。对给定评分，更一般的 Shannon 判定是：取 $k=1$，在非空有效候选集上令 $p=\operatorname{softmax}(s/\tau_{\mathrm{sel}})$；若每个 $p_v\le\mu_v$，则 $c=p$。这些不等式蕴含 $M\ge1$，故总和为 $1$，而 $p$ 已在整个概率单纯形上最大化 Shannon 目标。例如 $\mu=(0.6,0.6)$、相等评分给出 $c=(0.5,0.5)$。

固定上限，所有 $p_v<\mu_v$ 时，这一等式在评分的邻域内保持，评分导数就是通常的 softmax 导数。等于某个上限时，前向等值仍成立，边界反向须按 §4.2 的分支分别判断。

一般总和区间上有

$$
R^{\mathrm{ent}}_{\alpha=2}=R^{\mathrm{quad}}+\tfrac12\sum_vc_v.
\tag{15}
$$

要取得相同分配，取 $\eta_{\mathrm{ent},2}=\eta_{\mathrm{quad}}+\tau/2$；总和固定时无需这项移位。固定评分和上限令温度趋于无穷时，解趋于可行集上正则的唯一最大点，见附录 A。

## 4. 求解与导数

### 4.1 一个标量乘子

先按 §2.1 处理单点可行集，其余有 $M>1$。对实数 $x$、上限 $\mu\in[0,1]$ 和正温度 $\tau$，定义响应函数：

| 正则 | $g(x,\mu;\tau)$ |
|---|---|
| quad | $\operatorname{clip}(x/\tau,0,\mu)$ |
| bern | $\mu\sigma(x/\tau)$ |
| Shannon | $\min(\mu,e^{x/\tau-1})$ |
| ent，$\alpha>1$ | $\min(\mu,[(\alpha-1)x/\tau+1/\alpha]_+^{1/(\alpha-1)})$ |

定义 $S(\lambda)=\sum_vg(t_v-\lambda,\mu_v;\tau)$，表示给定乘子时的发送总和。令 $\lambda_U,\lambda_L$ 分别为总和上限、下限的非负乘子，$\lambda=\lambda_U-\lambda_L$。最优性条件为

$$
\begin{aligned}
c_v&=g(t_v-\lambda,\mu_v;\tau),\qquad\lambda=\lambda_U-\lambda_L,\\
\lambda_U,\lambda_L&\ge0,\quad \lambda_U(S-k)=0,\quad\lambda_L(b-S)=0.
\end{aligned}
\tag{16}
$$

先用 $\lambda=0$；总和过大时求 $S(\lambda)=k$ 的非负根，过小时求 $S(\lambda)=b$ 的非正根。响应单调，二分或有区间保护的 Newton 法即可求解。quad 还可排序断点。乘子可能不唯一，发送向量仍唯一。

Shannon 在零处的熵导数无穷大；从正分量移入足够小的量到零分量会增加目标，故有效候选全正。bern 在 $M>1$ 时均处于上下限之间。quad 与 ent 的 $\alpha>1$ 可在正温度达到零和上限。

### 4.2 约束分配的反向

固定温度和正则形状。在保持零、内部、上限状态及总和约束松紧不变的光滑分支上，记
$x_v^{\mathrm{resp}}=t_v-\lambda$，并在此处求响应导数 $a_v^{\mathrm{resp}}=\partial g/\partial x$、$e_v^{\mathrm{resp}}=\partial g/\partial\mu$。

| 分支 | $a_v^{\mathrm{resp}}$ | $e_v^{\mathrm{resp}}$ |
|---|---|---|
| quad，$0<c_v<\mu_v$ | $1/\tau$ | $0$ |
| ent，$0<c_v<\mu_v$ | $c_v^{2-\alpha}/\tau$ | $0$ |
| bern，$p_v^{\mathrm{occ}}=c_v/\mu_v$ | $\mu_vp_v^{\mathrm{occ}}(1-p_v^{\mathrm{occ}})/\tau$ | $p_v^{\mathrm{occ}}$ |
| quad／ent，上限饱和 | $0$ | $1$ |
| quad／ent，零饱和 | $0$ | $0$ |

总和固定在 $B=1$ 或 $k$ 且 $A_0=\sum_va_v^{\mathrm{resp}}>0$ 时，微分给出

$$
d\lambda=\frac{\sum_va_v^{\mathrm{resp}}dt_v+\sum_ve_v^{\mathrm{resp}}d\mu_v-dB}{A_0},\qquad
dc_v=a_v^{\mathrm{resp}}(dt_v-d\lambda)+e_v^{\mathrm{resp}}d\mu_v.
\tag{17}
$$

对标量目标 $\mathcal L$，记 $g_v^{\mathcal L}=\partial\mathcal L/\partial c_v$、$\bar g=\sum_va_v^{\mathrm{resp}}g_v^{\mathcal L}/A_0$，则

$$
\frac{\partial\mathcal L}{\partial t_v}=a_v^{\mathrm{resp}}(g_v^{\mathcal L}-\bar g),\qquad
\frac{\partial\mathcal L}{\partial\mu_v}=e_v^{\mathrm{resp}}(g_v^{\mathcal L}-\bar g)+\bar g\frac{\partial B}{\partial\mu_v}.
\tag{18}
$$

本分支的 $B$ 为常数，末项为零。提高一个未饱和评分会在可响应的候选之间重新分配；其负梯度方向比较该候选与加权平均的任务边际影响。总和上下限都松弛时，$\lambda=0$ 固定，直接用 $dc_v=a_v^{\mathrm{resp}}dt_v+e_v^{\mathrm{resp}}d\mu_v$。

对 quad，固定上限并令 $\mathcal F=\{v:0<c_v<\mu_v\}$，记 $I$ 为 $|\mathcal F|$ 维单位矩阵，$\mathbf1$ 为同维的全一向量。在 $\mathcal F\ne\varnothing$ 且约束状态保持的光滑分支上，未饱和分量对其评分的 Jacobian 为

$$
\frac{\partial c_{\mathcal F}}{\partial t_{\mathcal F}}
=\begin{cases}
\displaystyle\frac1\tau\left(I-\frac{\mathbf1\mathbf1^\top}{|\mathcal F|}\right),
 &\text{总和固定在下限或上限},\\
\displaystyle\frac1\tau I,&\text{总和上下限都松弛}.
\end{cases}
$$

例如 $\mu=(1,1,1),k=3,\tau=1,t=(0.4,0.5,0.6)$ 时，$c=t$ 且 $1<\sum c_v<3$；全部评分同时小幅增加，全部控制量随之增加。

总和固定且只有一个未饱和候选时，评分导数为零；式 (18) 中各可响应候选的任务边际影响相同时，评分梯度也为零。$A_0=0$ 时不得除零，应沿严格饱和分支求导。分支切换处另给单侧或广义导数。

### 4.3 Attention 分配的反向

在式 (9) 的 $Z>0$ 分支，把评分和基权重看作独立输入，记 $J_p=\operatorname{diag}(p)-pp^\top$，有

$$
\frac{\partial p_v^{\mathrm{sel}}}{\partial s_u}=\frac{p_v^{\mathrm{sel}}}{\tau}(\mathbf1[v=u]-p_u^{\mathrm{sel}}),\qquad
\frac{\partial p_v^{\mathrm{sel}}}{\partial a_u}=\frac{e^{s_u/\tau}}Z(\mathbf1[v=u]-p_v^{\mathrm{sel}}).
\tag{19}
$$

零基权重处第二式表示向正值移动的右导数。各发送规则再使用

$$
\begin{array}{ll}
\text{直接 Attention：}&dc_v=p_v^{\mathrm{sel}}d\mu_v+\mu_vdp_v^{\mathrm{sel}},\\
\text{固定总强度：}&dc_v=dp_v^{\mathrm{sel}},\\
\text{区域总量分配：}&dc_v=p_v^{\mathrm{sel}}dB+Bdp_v^{\mathrm{sel}},\quad B=\min(1,M).
\end{array}
\tag{20}
$$

对直接 Attention 的 $a=\mu$，这给出
$\partial c_v/\partial\mu_u=2p_v^{\mathrm{sel}}\mathbf1[v=u]-c_ve^{s_u/\tau}/Z$；$a=w$ 时固定 $w,s$ 则为 $p_v^{\mathrm{sel}}\mathbf1[v=u]$。评分 Jacobian 分别为 $\operatorname{diag}(\mu)J_p/\tau$、$J_p/\tau$、$BJ_p/\tau$。由 $\|J_p\|_2\le1/2$ 得到相应范数界。固定总强度的评分反向为

$$
\frac{\partial\mathcal L}{\partial s_v}
 =\frac{p_v^{\mathrm{sel}}}{\tau}\left(g_v^{\mathcal L}-\sum_up_u^{\mathrm{sel}}g_u^{\mathcal L}\right).
$$

这些局部公式还须沿评分、基权重与增益的真实依赖回传。全零权重处，固定总强度的 $a=\mu$ 不连续；直接与区域总量函数连续但一般不可微。例如原直接函数沿 $\mu=\varepsilon\delta$ 的方向导数为
$\delta_v^2e^{s_v/\tau}/\sum_u\delta_ue^{s_u/\tau}$，一般不关于方向 $\delta$ 线性。

### 4.4 评分与记忆的依赖

固定 keys，沿区域匹配项有

$$
\nabla_{Q_j^{\mathrm{sel}}}\mathcal L=
 \frac{\alpha_j^{\mathrm{sel}}}{\sqrt{d_{\mathrm{sel}}}}
 \sum_v\frac{\partial\mathcal L}{\partial s_v}K_v^{\mathrm{sel}}.
\tag{21}
$$

完整反向还经过 query 汇集、keys、局部评分、记忆读取、写入与消息。正接收但零发送的候选可以通过 query 或未来记忆获得反馈；未执行的 Full 不提供该步替代分支的内容反馈。

所有正温度族都涉及评分相对温度的尺度。低温未饱和区的斜率可含 $1/\tau$，严格饱和区的直接评分导数可以为零。固定温度时，query/key 范数和匹配尺度的变化仍会改变集中程度。这些是导数性质，训练效果的判断见设计备忘。

## 5. 温度极限与硬选择

### 5.1 一次约束分配

固定有限候选集和正则形状。设 $\mu^{(n)}\to\mu^*$、$\tau_n\downarrow0$，评分有界，并在 $\mu_v^*>0$ 的坐标收敛到 $t_v^*$。若线性问题

$$
\arg\max_{c\in F(\mu^*)}t^*\cdot c
\tag{22}
$$

有唯一解，式 (8) 的解收敛到它。零上限处的评分任取有限值。证明见附录 A。

当每个极限上限为 $0$ 或 $1$ 时，以下条件使该唯一解恰为硬选择：

- 有效候选至多一个，无评分条件。
- $k=1$ 且至少两个有效候选，最高分唯一。
- $k>1$ 且至少两个有效候选，各有效 $t_v\ne0$；正评分数超过 $k$ 时，第 $k$ 名与下一名严格分离；全负时最高分唯一。

这些条件只要求相关选择边界有间隔。已经选中的两个节点同分可以不影响唯一性。

### 5.2 条件与反例

固定 $\mu=(0.9,0.8),t=(-2,-1),k=1$ 时，线性问题的唯一解是 $(0.2,0.8)$，硬选择给 $(0,0.8)$。这里的上限始终是这两个介于零和一之间的数。

$\mu=(1,1),t=(1,1),k=1$ 时，quad 在每个正温度给出 $(1/2,1/2)$。若分别送到两个单节点区域且增益为 $1$，下游也保持半强度。单位外部输入仍需评分条件才能推出整网软硬相等的极限。

阈值边界也有影响：$\mu=(1,1),k=2,t^\tau=(1,\tau/2)$ 在 $0<\tau<1$ 时给 quad 解 $(1,1/2)$，端点硬函数为 $(1,0)$。

### 5.3 正温度的精确性

固定二元上限与 §5.1 的分离评分，将有效候选的调整后评分从高到低记为 $t_{(1)},t_{(2)},\ldots$。至少有两个有效候选时，quad 达到硬向量的充分条件为：

| 情形 | 温度界 |
|---|---|
| $k=1$，或有效评分全负 | $\tau\le t_{(1)}-t_{(2)}$ |
| $k>1$，正评分数介于 $1$ 与 $k$ | $\tau\le\min_{t_v>0}t_v$ |
| 正评分数超过 $k$ | $\tau\le t_{(k)}-t_{(k+1)}$ |

例如 $t=(4,3,2,1),k=1$ 时，温度界为 $1$；$\tau=2$ 给出 $(0.75,0.25,0,0)$，$\tau=1$ 给出 $(1,0,0,0)$。有效候选至多一个时任意正温度均成立。ent 的固定 $\alpha>1$ 也有这样的充分小正温区间；Shannon 和 bern 在正温度保持全部有效分量为正。附录 A 给出响应阈值及证明。

整网的消息、评分和上限会随温度共同变化。[共同架构 §6.3](architecture-learning-note.md#63-单位输入的软硬极限)将本节的局部结论沿逻辑时间组合，各记忆教材验证相应状态条件。该定理比较固定参数、固定输入与有限时间；训练日程由研究配置给出。

## 附录 A：连续性与极限证明

### A.1 约束解的连续性

固定正则形状。设 $\mu^{(n)}\to\mu^*$，评分一致有界且在正极限上限处收敛。温度趋向正值时，解趋向相应正温度解；温度趋零且式 (22) 唯一时，解趋向该线性最优解。

**证明。** 可行向量均在紧集 $[0,1]^{|C|}$ 中，任何可行收敛列的极限仍可行。反之，对 $d\in F(\mu^*)$，先取 $a_v^{(n)}=\min(d_v,\mu_v^{(n)})$。若其和小于 $b_n=\min(1,\sum_v\mu_v^{(n)})$，按剩余容量 $\mu_v^{(n)}-a_v^{(n)}$ 的比例补足到 $b_n$；剩余容量足够，补量趋零。若和已足够，保持原向量。所得 $d^{(n)}\in F(\mu^{(n)})$ 且 $d^{(n)}\to d$。

零极限上限坐标的线性目标绝对值受 $L\sum_{\mu_v^*=0}\mu_v^{(n)}$ 控制，趋于零。三种正则在 $0\le c\le\mu\le1$ 上联合连续有界；bern 在 $\mu\to0$ 时由 $0\le\mu h_B(c/\mu)\le\mu\log2$ 得到延拓。将最优性不等式与上述可行恢复列比较并取极限，每个聚点都是极限目标的最优解。正温度由严格凹性给出唯一性；零温度使用假设的唯一性。因此整列收敛。$\square$

同理，固定 $\mu,t$ 时将目标除以趋于无穷的温度，紧性与正则严格凹性给出 §3.2 的高温结论。

### A.2 二元上限与有限温度

**证明 §5.1 的硬向量唯一性。** 零上限坐标固定。无有效候选或只有一个时可行集为单点；$k=1$ 时最高分唯一使单位总量集中于它。$k>1$ 且全负时，总和取下限 $1$，再由最高分唯一决定分配。有正评分时，负分量可移向未满的正分量，或在正分量全满后直接删除，从而严格提高目标。正评分数不超过 $k$ 时它们全部取 $1$；超过 $k$ 时严格截断间隔唯一确定前 $k$ 个。$\square$

**证明 §5.3。** quad 中，选最高分一个时取 $\lambda=t_{(2)}$，选全部正评分时取 $\lambda=0$，选前 $k$ 个正评分时取 $\lambda=t_{(k+1)}$。表中温度界使式 (16) 逐坐标为所需的零或一，并满足乘子符号和互补条件。总和上下限同时取等号时，$\lambda$ 可为任意符号。

ent 的 $\alpha>1$ 在单位上限处，响应为 $1$ 和 $0$ 的条件分别是

$$
t_v-\lambda\ge\tau/\alpha,\qquad
t_v-\lambda\le-\tau/[\alpha(\alpha-1)].
$$

在截断边界取 $\lambda=t_{(k+1)}+\tau/[\alpha(\alpha-1)]$，最高分一项的情形用第二名；间隔足够大时可同时满足两界。全负时还需该乘子为负。选全部正评分时取 $\lambda=0$，分别利用正负评分距零的严格间隔。充分小正温度满足这些有限个条件。严格凹性确定同一解。$\square$

### A.3 无求根规则的零边界

固定候选槽、$\tau_n\to\tau_*>0$。设 $w^{(n)},\mu^{(n)}$ 收敛且满足 $w\le\mu\le\gamma_{\max}w$，评分有界并在正极限接收处收敛。直接 Attention 的两种基权重、区域总量分配、按比例分配均连续，并允许增删零接收坐标。

**证明。** 有正极限接收时，式 (9) 中相应项收敛到正值，零极限项因有界指数趋零，故分母趋正，份额收敛。全部接收趋零时，直接规则用 $c\le\mu$，总量规则用 $\sum c=\min(1,M)$，均得 $c\to0$。按比例规则在 $M>0$ 直接连续，零处仍有 $c\le\mu$。零接收坐标对各分母、总量和发送均无贡献。$\square$

在有正极限接收的情形，总量规则还有 $c_v\to0$ 对应于 $r_v^{\mathrm{in}}\to0$；这是组合消息连续性所需的单候选结论。固定总强度 $a=\mu$ 允许增删精确零接收坐标：它们对分母与发送均无贡献；但分母趋零时一般不连续。固定总强度 $a=1$ 把真实零接收候选计入分母，增删它们一般改变其他份额。两种比较的整网范围及算例见[共同架构 §6.2](architecture-learning-note.md#62-零消息与正温度输入)。

正温度连续性不能直接用于温度同时趋零：例如 $\mu=(1,\varepsilon_\tau)$、$s=(0,1)$、$\varepsilon_\tau=e^{-1/(2\tau)}$，总量规则使第二候选份额趋于 $1$，尽管它的接收权重趋零。对这类分配的整网温度极限需另外给出条件；共同架构的软硬极限定理仅使用约束分配与式 (14)。

## 附录 S：配置、求解与边界反向

### S.1 配置名称

selection_mode 指定发送函数：

| 函数 | 配置值 | 定义 |
|---|---|---|
| 约束分配 | constrained | 式 (8) |
| 直接 Attention | direct_attention | 式 (10) |
| 固定总强度 Attention | unit_attention | 式 (11) |
| 区域总量分配 | pooled_attention | 式 (12) |
| 按比例分配 | proportional | 式 (13) |
| 硬选择 | hard_selection | 式 (14) |

其余配置对应已定义的参数与函数选择：

| 名称 | 取值与含义 |
|---|---|
| local_score | cat、match，式 (2)、(3) |
| region_score | ind、att，§1.3 的描述空间与评分 |
| send_gain | fixed、context，式 (1)、(4) |
| query_weight | mu、received：式 (6) 分别使用 $\mu_v,w_v$；默认 mu |
| allocation_base | direct_attention 使用 mu 或 received，默认 mu；unit_attention 使用 uniform 或 mu，默认 uniform；pooled_attention 固定 mu |
| regularizer、ent_alpha | constrained 的 quad／bern／ent；ent 另指定固定 $\alpha\in[1,2]$ |
| allocation_temperature | constrained、direct_attention、unit_attention、pooled_attention 使用的正温度，与正典读取模式 $\tau_j$ 分别命名 |
| k | constrained、proportional 的总发送强度上限；hard_selection 的激活数量上限 |
| eta | constrained、hard_selection 的共同评分阈值；其余规则不使用 |
| alpha_loc、alpha_sel | att 的局部评分与区域匹配尺度 |

constrained 是约束优化函数的配置名称，包含持续稠密和可精确稀疏的族。direct_attention、unit_attention、pooled_attention 均不使用 k、eta 或 regularizer。参数的无效分支须能由配置检查识别。

### S.2 标量求解与隐式反向

对 §4.1 中需要取边界总和 $B$ 的情形，有 $0<B<M$。令 $q=B/M\in(0,1)$，对有效候选取满足 $g(x_v^{\mathrm{resp}},\mu_v;\tau)=q\mu_v$ 的逆响应：

| 正则 | $x_v^{\mathrm{resp}}$ |
|---|---|
| quad | $\tau q\mu_v$ |
| bern | $\tau\log(q/(1-q))$ |
| Shannon | $\tau[1+\log(q\mu_v)]$ |
| ent，$\alpha>1$ | $\tau[(q\mu_v)^{\alpha-1}-1/\alpha]/(\alpha-1)$ |

令 $\lambda_{\mathrm{lo}}=\min_v(t_v-x_v^{\mathrm{resp}})$、$\lambda_{\mathrm{hi}}=\max_v(t_v-x_v^{\mathrm{resp}})$。单调性给出 $S(\lambda_{\mathrm{lo}})\ge B\ge S(\lambda_{\mathrm{hi}})$。二分维持此区间；Newton 候选步为 $\lambda+(S(\lambda)-B)/\sum_va_v^{\mathrm{resp}}$，仅在斜率非零且落入保留区间时使用。根区间可与乘子的对应半轴相交。

每轮工作量为 $O(|C|)$。初始区间宽度 $D$ 到精度 $\varepsilon_\lambda$ 所需轮数为 $O(\max(1,\log_2(D/\varepsilon_\lambda)))$；同宽零区间直接求值。终止同时检查坐标误差、可行性及最优性残差，低温时相同乘子误差可造成更大坐标误差。quad 可排序 $t_v-\tau\mu_v,t_v$ 后扫描断点，工作量 $O(|C|\log|C|)$；ent 的 $\alpha=2$ 先按式 (15) 移位。

反向使用 §4.2 的最优解映射导数，只保存分配、分支及响应统计，工作量 $O(|C|)$。对有限次迭代自动求导定义了另一种反向目标。$M=1$、精确断点、总和约束松紧交界和增益截断均需声明边界约定。若训练温度，固定 $x,\mu$ 时 $\partial g/\partial\tau=-a_v^{\mathrm{resp}}x_v^{\mathrm{resp}}/\tau$，再按总和约束修正；可训练 $\alpha$ 的反向须另行定义。

### S.3 稳定求值与支持

式 (9) 在正基权重上计算 $s_v/\tau+\log a_v$，减去最大值后 softmax；全零权重直接返回零。uniform 的候选掩码按输入存在性确定。总量与直接规则按自己的公式外乘，正分量支持按精确数学函数确定。

指数响应先在对数域与上限比较；达到上限时直接返回原上限。sigmoid 采用稳定形式；ent 在 $\alpha$ 接近 $1$ 时使用 log1p／expm1 形式。数学零、浮点下溢零与人为裁剪零分别记录。

Attention 规则的 $Z>0$ 边界按式 (19) 核对右导数。全零分支一般没有通常 Jacobian；实现可声明返回零反向，须与方向导数分别记录。跳过 Full 与求出内容再乘零的边界反向也需按所选目标比较。具体核对项见[实现对应](../../reference/weighted-message-implementation-checks.md)。
