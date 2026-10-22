---
type: mathematical-learning-note
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - local-semantics
  - regional-allocation
---

# 区域共享放大额度

节点向区域提供当前内容、记忆及接收信息。区域计算一份共享的放大额度，再根据评分共同分配发送强度。每个节点保留由自身接收确定的发送上限；共享额度限制本次各节点超出自身接收的发送量之和。

本文实现[共同架构](architecture-learning-note.md)的 Describe 与 SelStep，复用[区域评分教材](region-allocation-learning-note.md)的特征、局部评分和区域匹配。先构造描述和额度，再定义分配及完整返回，随后给出例子、求解、导数与组合性质。记忆模块仍独立实现 Upd、Mem、当前特征与 Full 内容。

## 1. 输入与发送上限

固定区域 $j$ 的一次作用，候选集为 $C\subseteq\mathcal R_j$。候选 $v$ 的聚合输入为 $h_v=(r_v^{\mathrm{in}},u_v)$；描述模式指定状态 $q_v^{\mathrm{read}}$。沿用 Mem 的两个记忆向量、两个接收统计量、当前特征 $p_v(u_v)$，以及区域评分教材 §2.1 的共同特征 $f_v\in\mathbb R^{d+4d_s+3}$。

取固定有限 $\gamma_{\max}\ge1$，定义截断接收量与节点发送上限：

$$
w_v=\min(1,(r_v^{\mathrm{in}})_+),\qquad
\mu_v^{\max}=\min(1,\gamma_{\max}w_v).
\tag{1}
$$

$\mu_v^{\max}$ 相当于区域评分教材中将增益固定为 $\gamma_{\max}$ 时的发送上限，满足 $w_v\le\mu_v^{\max}\le\gamma_{\max}w_v$。本候选的可学习放大由区域额度控制。记忆写入仍使用所选 Upd；$w_v$、$\mu_v^{\max}$ 和最终发送 $c_v$ 分别承担接收、最大允许幅度和实际幅度的作用。

计算依次为

$$
\text{本地接收与记忆}\longrightarrow(d_v)_{v\in C}
\longrightarrow\bigl((s_v)_{v\in C},E_j\bigr)
\longrightarrow(c_v)_{v\in C}.
$$

其中 $s_v$ 是区域评分，$E_j$ 是本次共享额度。二者从同一描述族分别计算，发送分配再同时使用它们。

## 2. Describe：供评分与额度使用的证据

### 2.1 局部评分与额度特征

局部评分 $s_v^{\mathrm{loc}}$ 选用区域评分教材 §2.2 的 cat 或 match。额度有固定比例和上下文两种形式，在第 3 节分别定义；上下文形式需要节点提供内容与记忆的向量证据。

取正整数额度特征宽度 $d_E$。固定比例形式令 $z_v^E=0\in\mathbb R^{d_E}$；上下文形式取 $W_v^E\in\mathbb R^{d_E\times(d+4d_s+3)}$、$b_v^E\in\mathbb R^{d_E}$，定义

$$
z_v^E=\mathcal N_{d_E}(W_v^E f_v+b_v^E).
\tag{2}
$$

归一化 $\mathcal N$ 沿用共同架构的正数 $\epsilon$。它使 $\|z_v^E\|\le\sqrt{d_E}$。$f_v$ 已包含当前内容、记忆、接收统计及内容与记忆的乘积；式 (2) 把这些信息投影成传给区域的额度特征。评分与额度投影的参数分别给定。

### 2.2 两种描述与完整返回

独立评分只需局部评分；区域 Attention 评分另需当前内容投影 $x_v^{\mathrm{sel}}$ 与记忆 key $K_v^{\mathrm{sel}}$，二者使用区域评分教材式 (5) 的投影定义。相应描述空间与返回值为

$$
\begin{aligned}
D_v^{E,\mathrm{ind}}&=[0,1]\times\mathbb R\times\mathbb R^{d_E},
&d_v&=(w_v,s_v^{\mathrm{loc}},z_v^E),\\
D_v^{E,\mathrm{att}}&=[0,1]\times\mathbb R\times\mathbb R^{d_E}\times
 \mathbb R^{d_{\mathrm{sel}}}\times\mathbb R^{d_{\mathrm{sel}}},
&d_v&=(w_v,s_v^{\mathrm{loc}},z_v^E,x_v^{\mathrm{sel}},K_v^{\mathrm{sel}}).
\end{aligned}
\tag{3}
$$

选定描述形式及参数后，上述构造给出 $\operatorname{Describe}_v[\operatorname{Mem}_v,p_v] (q_v^{\mathrm{read}},\theta,h_v)$。这两种元组分别供本章的 ind、att 使用；字段次序与原区域教材中含 $\mu_v$ 的描述分别定义。固定比例形式无需计算额度投影，但仍按式 (3) 返回零向量。

同一区域使用相容的描述宽度。不同区域可以独立选择记忆模块、局部评分、描述模式和额度形式。

## 3. SelStep：区域评分与共享额度

### 3.1 区域评分

ind 取 $s_v=s_v^{\mathrm{loc}}$。att 使用区域评分教材 §3.2 的 query、key 匹配与局部评分合成，但 query 的汇集权重固定为 $w_v$，即 query_weight=received。区域读取式 (3) 中的 $x_v^{\mathrm{sel}},K_v^{\mathrm{sel}}$。

因此评分只依赖已有描述，额度也只依赖已有描述。二者在本次作用内没有相互等待的依赖；零接收候选对 query 的贡献为零。

### 3.2 可用放大量与区域摘要

下面先计算所有节点最多能够增加的发送量，再决定本次允许使用其中多少。记

$$
W_j^{\mathrm{recv}}=\sum_{v\in C}w_v,\qquad
E_j^{\max}=\sum_{v\in C}(\mu_v^{\max}-w_v),\qquad
\bar z_j^E=\frac{\sum_{v\in C}w_vz_v^E}{\max(1,W_j^{\mathrm{recv}})}.
\tag{4}
$$

$W_j^{\mathrm{recv}}$ 是当前区域的截断接收总量，与 Mem 的历史统计量分别使用。$E_j^{\max}$ 是逐节点最大增加量之和；$\bar z_j^E$ 汇集当前候选的内容与记忆证据。节点在这三个和中各计一次，广播出度另行计量。

### 3.3 额度的两种形式

固定比例形式给定 $a_j^E\in[0,1]$。上下文形式令 $a_j^E=\sigma(H_j^E(f_j^E))$，其中

$$
\begin{aligned}
f_j^E&=[\bar z_j^E;\log(1+W_j^{\mathrm{recv}});\log(1+E_j^{\max})],\\
H_j^E(f)&=b_j^{E,\mathrm{out}}+
 (a_j^{E,\mathrm{out}})^\top
 \operatorname{SiLU}(W_j^{E,h}f+b_j^{E,h}).
\end{aligned}
$$

隐藏宽度沿用局部评分的 $d_r$，故 $W_j^{E,h}$ 为 $d_r\times(d_E+2)$ 矩阵，$a_j^{E,\mathrm{out}},b_j^{E,h}$ 为 $d_r$ 维向量，$b_j^{E,\mathrm{out}}$ 为标量。$f_j^E$ 是本次额度头的输入特征，无需保存到后续作用。

选定固定或上下文比例后，共享额度统一为

$$
E_j=a_j^E E_j^{\max},\qquad 0\le E_j\le E_j^{\max}.
\tag{5}
$$

$a_j^E$ 控制可用放大量的使用比例，$E_j$ 才是按发送强度计量的额度上限。没有额外可用量时 $E_j^{\max}=E_j=0$。上下文形式按固定尺度求值，选择温度不进入额度头。

## 4. 共同分配与完整返回

### 4.1 放大额度约束

对一个候选控制族 $c$，定义其放大量

$$
\operatorname{Amp}(c,w)=\sum_{v\in C}(c_v-w_v)_+.
\tag{6}
$$

每项只计算本节点超出截断接收量的发送部分。例如 $w=(0.6,0.1)$、$c=(0.4,0.3)$ 时，放大量为 $0.2$。其他节点少发不会抵扣这一项。因此本定义与仅约束净增加量 $\sum c_v-\sum w_v$ 的函数具有不同可行域。

取整数 $1\le k\le|\mathcal R_j|$，令 $b=\min(1,W_j^{\mathrm{recv}})$，定义

$$
F_E(w)=\left\{c:
 0\le c_v\le\mu_v^{\max},\quad
 b\le\sum_vc_v\le k,\quad
 \operatorname{Amp}(c,w)\le E_j\right\}.
\tag{7}
$$

这是非空紧凸集。令 $c_v^0=w_v/\max(1,W_j^{\mathrm{recv}})$，则其总和为 $b$，各分量不超过 $w_v$，放大量为零，故任意允许的 $E_j$ 都有这一可行向量。

总量下界按本次接收定义，保证零额度时仍可行。有正接收时 $b>0$，因此至少一个控制为正。$E_j=0$ 时所有控制都不超过 $w_v$；若还满足 $W_j^{\mathrm{recv}}\le1$，则强制 $c=w$。正额度下即使 $\sum\mu_v^{\max}\le1$，可行集也未必为单点。

$E_j^{\max}$ 由各节点上限相加取得，未计入总发送上限。始终有 $\operatorname{Amp}(c,w)\le\sum_vc_v\le k$，因此 $E_j\ge k$ 时额度约束冗余；$E_j<k$ 时是否起作用还取决于接收和评分。

### 4.2 正则分配与返回

取阈值 $\eta\in\mathbb R$、正温度 $\tau=\tau_{\mathrm{sel}}>0$，令 $t_v=s_v-\eta$。本候选使用区域教材式 (8) 中的 quad 或 ent 正则，ent 的形状固定为 $\alpha\in[1,2]$，$\alpha=1$ 为 Shannon。将所选正则写为 $R(c)=\sum_vR_v(c_v)$，其中 $R_v$ 为对应的单节点项。定义

$$
c^\tau=\arg\max_{c\in F_E(w)}\{t\cdot c+\tau R(c)\},\qquad
\mathcal A=\{v\in C:c_v^\tau>0\},\qquad
\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_{v\in C})
=(\mathcal A,(c_v^\tau)_{v\in C},*).
\tag{8}
$$

严格凹性给出唯一控制族。空候选返回 $(\varnothing,(),*)$，全零接收返回全零控制。正典容量取 $K_j=|\mathcal R_j|$；$k$ 限制发送总强度，$E_j$ 限制放大量，两者都不直接限制激活个数。quad 与 $\alpha>1$ 的 ent 可以产生精确零；Shannon 在每个正接收候选上产生正控制，证明见附录 A。

以上完成 Describe 与 SelStep 的绑定。全部候选仍按共同 Next 保留更新，只有正控制节点执行 Full，并沿每条出边发送 $(c_v,G_v)$。本次额度和乘子都是区域函数的内部量，精确继续无需增加持久状态。

## 5. 两节点的额度分配

取 $w=(0.8,0.4)$、$\gamma_{\max}=2$，于是 $\mu^{\max}=(1,0.8)$、$b=1$、$E_j^{\max}=0.6$。用固定比例 $a_j^E=1/6$ 得 $E_j=0.1$。取 ind、cat、$s=(0,2)$、$\eta=0$、$k=1$、quad、$\tau=1$。评分头输出权重置零、偏置取 $0,2$ 即可实现这两个评分；额度特征为零，Mem 可以使用任意已绑定模块。

总和固定为 $1$。第二个节点最多在原有 $0.4$ 上增加 $0.1$，评分使它取得这个额度，故 $c=(0.5,0.5)$。两个节点均未达到自己的发送上限。保持其余量不变，额度变化给出

| $E_j$ | 最优控制 $c$ | 实际放大量 |
|---|---|---|
| $0$ | $(0.6,0.4)$ | $0$ |
| $0.1$ | $(0.5,0.5)$ | $0.1$ |
| $0.2$ | $(0.4,0.6)$ | $0.2$ |
| $0.4$ | $(0.2,0.8)$ | $0.4$ |
| $0.6$ | $(0.2,0.8)$ | $0.4$ |

在 $0<E_j<0.4$ 内，增加额度把发送强度从第一个节点移给第二个节点。$E_j>0.4$ 时额度松弛，小幅改变额度不改变分配。节点上限松弛与区域额度松弛是不同条件。

## 6. 求解与反向

### 6.1 两个乘子与单节点响应

令 $\lambda=\lambda_U-\lambda_L$ 为发送总和的净乘子，$\xi\ge0$ 为放大量的乘子。沿用区域教材 §6.1 的响应 $g(x,\mu^{\max};\tau)$，把上限参数取为 $\mu^{\max}$。对固定 $0\le w\le\mu^{\max}\le1$，定义

$$
h(x,\mu^{\max},w;\tau,\xi)=
\begin{cases}
g(x,\mu^{\max};\tau),&g(x,\mu^{\max};\tau)<w,\\
g(x-\xi,\mu^{\max};\tau),&g(x-\xi,\mu^{\max};\tau)>w,\\
w,&\text{其余情形}.
\end{cases}
\tag{9}
$$

第一种情形未使用放大额度，第二种情形为超出接收的发送支付乘子 $\xi$；中间情形停在 $c=w$。式 (9) 是 $[0,\mu^{\max}]$ 上最大化 $xc+\tau R_v(c)-\xi(c-w)_+$ 的唯一解，分段边界的值一致。

记 $S=\sum_vc_v$。最优性条件为

$$
\begin{aligned}
c_v&=h(t_v-\lambda,\mu_v^{\max},w_v;\tau,\xi),\\
\lambda_U,\lambda_L,\xi&\ge0,\quad \lambda=\lambda_U-\lambda_L,\\
\lambda_U(S-k)&=0,\quad \lambda_L(b-S)=0,\quad \xi(\operatorname{Amp}(c,w)-E_j)=0,
\end{aligned}
\tag{10}
$$

并满足式 (7)。乘子可能不唯一，控制族仍唯一。

### 6.2 嵌套的标量求解

固定 $\xi$，式 (9) 随 $\lambda$ 单调不增。先试 $\lambda=0$，总和过大时求和为 $k$ 的非负根，过小时求和为 $b$ 的非正根。用二分处理平台区，保留原上下限与残差检查。

由此得到的 $c(\xi)$ 最大化带惩罚 $-\xi\operatorname{Amp}(c,w)$ 的严格凹目标，并满足节点与总和约束。其放大量随 $\xi$ 单调不增：写出两个乘子下的最优性不等式，相加即可得到这个结论。唯一性还给出连续性。

先取 $\xi=0$；若放大量已不超过额度，求解结束。否则在 $E_j>0$ 时倍增外层乘子上界，直到放大量不超过额度，再二分使放大量等于 $E_j$。零放大向量始终可行，所以 $\xi\to\infty$ 时最优放大量趋零；正额度可取得有限括区间。$E_j=0$ 直接把节点上限改为 $w_v$，求带总和下界 $b$ 的单乘子问题。$E_j=E_j^{\max}$ 时放大量约束冗余。

每次响应扫描的工作为 $O(|C|)$；嵌套迭代次数另计。实现须同时检查原始约束、互补条件及式 (9)，不能沿用原约束分配的“$\sum\mu_v^{\max}\le1$ 则直接返回 $\mu^{\max}$”分支。

### 6.3 额度与评分的梯度

反向针对精确最优解映射。先固定 $w,\mu^{\max},b,\tau$，并处于约束状态不变的可微分支。额度严格松弛时，分配对 $E_j$ 的导数为零。额度取等号时，先区分未到节点上下限、且不等于 $w_v$ 的节点；称这些节点的集合为 $\mathcal F$。对 $v\in\mathcal F$，令

$$
\chi_v^{\mathrm{amp}}=\mathbf1[c_v>w_v],\qquad
a_v^{\mathrm{resp}}=\begin{cases}1/\tau,&\mathrm{quad},\\c_v^{2-\alpha}/\tau,&\mathrm{ent},\end{cases}
\quad
A_0=\sum_{\mathcal F}a_v^{\mathrm{resp}},\quad A_1=\sum_{\mathcal F}\chi_v^{\mathrm{amp}}a_v^{\mathrm{resp}}.
\tag{11}
$$

$\chi_v^{\mathrm{amp}}$ 标记该节点是否使用放大量；$a_v^{\mathrm{resp}}$ 是固定乘子时的单节点响应导数。当发送总和与放大量均取等号，且 $0<A_1<A_0$ 时，有

$$
\begin{pmatrix}A_0&A_1\\A_1&A_1\end{pmatrix}
\begin{pmatrix}d\lambda\\d\xi\end{pmatrix}
=\begin{pmatrix}\sum_{\mathcal F}a_v^{\mathrm{resp}}\,dt_v\\
\sum_{\mathcal F}\chi_v^{\mathrm{amp}}a_v^{\mathrm{resp}}\,dt_v-dE_j\end{pmatrix},\qquad
dc_v=a_v^{\mathrm{resp}}(dt_v-d\lambda-\chi_v^{\mathrm{amp}}d\xi).
\tag{12}
$$

记 $g_v^{\mathcal L}=\partial\mathcal L/\partial c_v$ 为下游任务损失的反传值。固定评分时，式 (12) 给出

$$
\frac{\partial\mathcal L}{\partial E_j}
=\frac{\sum_{\mathcal F:\chi_v^{\mathrm{amp}}=1}a_v^{\mathrm{resp}}g_v^{\mathcal L}}{A_1}
-\frac{\sum_{\mathcal F:\chi_v^{\mathrm{amp}}=0}a_v^{\mathrm{resp}}g_v^{\mathcal L}}{A_0-A_1}.
\tag{13}
$$

这比较增加放大的节点与让出发送强度的节点的任务边际影响。第 5 节在 $E_j=0.1$ 处给出 $dc/dE_j=(-1,1)$。仅放大量约束取等号且 $A_1>0$ 时，式 (13) 保留第一项；仅总和约束取等号时使用原区域教材的总和修正，额度导数为零。

同时固定额度与接收时，两个紧约束分别固定放大自由组和未放大自由组的控制总和，评分只能在各组内部重新分配。第 5 节两组各只有一个节点，所以该分支的评分 Jacobian 为零，额度导数仍为 $(-1,1)$。额度能获得反馈与评分能获得反馈分别判断。

上下文头还使用 $dE_j=E_j^{\max}\,da_j^E+a_j^E\,dE_j^{\max}$。因此额度头在本次分配中仍可能因额度松弛、任务边际影响相同、sigmoid 饱和或 $E_j^{\max}=0$ 得不到反馈。乘子 $\xi$ 表示分配目标对额度的敏感性，任务损失的额度梯度按式 (13) 求得。

接收、节点上限和下界变化的完整微分见附录 B。约束切换、进入或离开 $c_v=w_v$ 平台的边界以及矩阵奇异处分别声明单侧或广义导数；有限次求根迭代的自动微分与精确解映射的反向分别定义。

## 7. 数值性质与软硬关系

### 7.1 零接收与正温度连续性

**命题 1。** 设记忆与内容满足共同架构 §6.1 的四项条件，则本候选满足该架构 §6.2 的零接收与正温度连续条件。比较时参数、额度形式和正则形状固定，各区域温度趋向正值。

零接收节点有 $w_v=\mu_v^{\max}=0$，对区域摘要、接收总量和可用放大量均无贡献，控制固定为零。弱接收节点满足 $c_v\le\gamma_{\max}w_v\to0$，有界的额度特征在加权摘要中的影响也趋零。其余控制的连续性由可行集与严格凹目标的连续变化得到，证明见附录 A。

结合相应记忆模块的局部引理，共同架构命题 1、2 给出固定有限时间内的零消息删除与输入连续性。精确分段继续比较同一份完整模型，区域内部求额度不增加持久状态。

### 7.2 一次分配的零温极限

**命题 2。** 固定候选槽、$k,\gamma_{\max}$ 与正则形状。设各次接收与额度满足上述定义，$w^{(n)}\to w^*$、$E_j^{(n)}\to E_j^*$、$\tau_n\downarrow0$，评分有界并在正极限接收处收敛到 $t_v^*$；零极限接收处的 $t_v^*$ 任取有限值。若线性问题 $\max_{c\in F_{E^*}(w^*)}t^*\cdot c$ 有唯一解，则正则分配收敛到该解。

固定非二元接收时，这个解可以是小数。例如 $w=(0.2,0.2)$、$E_j=0$ 时强制 $c=w$，任何温度都如此。一般非二元接收上的硬规则须另行定义并满足额度约束；直接按排名发送 $\mu_v^{\max}$ 可能超额。

### 7.3 单位输入与配对硬选择

为比较软硬运行，先定义配对硬函数。保留本章的 Describe、评分和节点上限，在 $w_v>0$ 的候选上按 $t_v=s_v-\eta$ 从高到低排序：选前 $\min(k,\#\{v:w_v>0,t_v>0\})$ 个正评分者，全非正时保留最高分一个，同分按固定节点序；没有正接收时选空集。若所得集合为 $\mathcal A^{\mathrm{hard}}$，则返回 $(\mathcal A^{\mathrm{hard}},(\mu_v^{\max}\mathbf1[v\in\mathcal A^{\mathrm{hard}}])_{v\in C},*)$，正典容量取 $K_j=k$。这是区域评分教材 §4.4 的硬规则在本章描述上的绑定；非二元接收时，它不一定满足式 (7) 的区域额度。

当 $w_v\in\{0,1\}$ 时，$\mu^{\max}=w$、$E_j^{\max}=E_j=0$。式 (7) 恰为原区域教材中二元上限的可行集。评分满足该文 §7.1 的条件时，其唯一线性最优解就是上述硬向量。

**命题 3。** 固定有限正时延图、参数、初态与有限切面，外部输入强度均为 $1$。记忆满足共同架构 §6.1 的条件，配对硬运行每次选择满足区域评分教材 §7.1 的评分条件。以相同 Describe、评分、$k,\eta$、记忆及内容函数比较本章正则运行与该硬运行，则区域温度共同趋零时，消息投影、有效状态与 ReadOut 收敛到硬运行。quad 与固定 $\alpha>1$ 的 ent 还有充分小正温度下完整记录精确相同的结论。

**证明。** 硬运行每条实际消息的强度为 $1$，接收强度为非负整数，故每步 $w$ 二元。对软运行按逻辑时间归纳，命题 1 的有界性与弱接收边界、命题 2 的唯一线性极限验证共同架构命题 3 的局部假设。在硬运行输入处，可行集与原二元分配相同，原区域教材 §7.3 的有限温度界同样适用；共同架构的精确运行推论完成最后一项。$\square$

单位输入的硬运行及对应的精确正温运行中，额度均为零，上下文额度头对控制没有数值作用。它主要参与尚有弱接收的软运行，或允许非单位输入的其他任务。训练期间参数变化与固定参数的温度极限分别讨论。

## 附录 A：可行集与极限的证明

固定候选槽集合，缺席节点补 $w=0$。利用

$$
\operatorname{Amp}(c,w)
=\max_{T\subseteq C}\sum_{v\in T}(c_v-w_v),
$$

式 (7) 可写成具有固定系数矩阵的有限线性不等式组，其右端连续依赖 $w,E_j$。下面给出所需的多面体事实。

**引理。** 对固定实矩阵 $A$，存在有限常数 $H$，使每个非空 $P_b=\{y:Ay\le b\}$ 满足 $\operatorname{dist}(x,P_b)\le H\|(Ax-b)_+\|_2$。

**证明。** 取 $x$ 在 $P_b$ 上的最近点 $y$。投影的最优性条件允许写 $x-y=A_I^\top\lambda$，其中 $I$ 由线性独立的紧约束法向量组成，$\lambda\ge0$。于是
$\|x-y\|^2=\lambda^\top(A_Ix-b_I)\le\|\lambda\|\|(Ax-b)_+\|$。
线性独立给出 $\|\lambda\|\le H_I\|x-y\|$，有限个可能的 $I$ 取最大常数即可。$x=y$ 时直接成立。$\square$

**证明命题 1、2 的分配连续性。** 取任意极限可行向量 $d$，它对第 $n$ 个可行集的约束违反量趋零。可行集始终非空，引理给出可行 $d^{(n)}\to d$。另一方面，可行收敛列的极限由约束连续性仍可行；所有向量都在固定紧集 $[0,1]^{|C|}$ 中。

quad 和 ent 在此紧集上连续有界。零极限接收处 $c_v\le\gamma_{\max}w_v\to0$，有界评分的对应目标贡献趋零。将最优性与可行恢复列比较并取极限，每个聚点最大化极限目标；正温度的严格凹性或命题 2 的线性唯一性给出整列收敛。额度摘要的零节点贡献为零，正接收特征连续，故由式 (4)、(5) 得到额度连续。零候选增删保持同一可行集的非零坐标，完成命题 1。$\square$

**Shannon 的正支持。** 有正接收时，基准可行向量 $c^0=w/\max(1,W_j^{\mathrm{recv}})$ 的每个有效分量都正。若最优向量有有效零分量，向 $c^0$ 作足够小的凸组合仍可行，新增正分量的 $-c\log c$ 增益支配其他项的线性变化，与最优性矛盾。$\square$

## 附录 B：接收与额度同时变化的反向

在固定可微分支上，将节点分为自由集 $\mathcal F$、严格零分量、节点上限集 $\mathcal U$、以及停在 $c_v=w_v$ 的集合 $\mathcal H$。后两类的微分分别为 $d\mu_v^{\max}$、$dw_v$；严格零分量的微分为零。重合边界不纳入本分支公式。

沿用式 (11) 的自由集标记，并在非自由节点上也记 $\chi_v^{\mathrm{amp}}=\mathbf1[c_v>w_v]$。自由节点满足式 (12) 的 $dc_v$。发送总和与额度都取等号时，完整右端为

$$
\begin{pmatrix}A_0&A_1\\A_1&A_1\end{pmatrix}
\begin{pmatrix}d\lambda\\d\xi\end{pmatrix}
=\begin{pmatrix}
\sum_{\mathcal F}a_v^{\mathrm{resp}}dt_v+\sum_{v\notin\mathcal F}dc_v-dB\\
\sum_{\mathcal F}\chi_v^{\mathrm{amp}}a_v^{\mathrm{resp}}dt_v+\sum_{v\notin\mathcal F}\chi_v^{\mathrm{amp}}dc_v
 -\sum_{c_v>w_v}dw_v-dE_j
\end{pmatrix}.
\tag{14}
$$

总和在下限时 $B=b$，在上限时 $B=k$。不紧的约束保持对应乘子为零，并删除该行、列；总和上下限重合时只保留一条总和等式。紧约束限制到自由坐标后，其系数向量线性独立才给出可逆系统；退化分支不能直接求逆。

由该系统取得向量—Jacobian 乘积，再沿 $t=s-\eta$、$\mu^{\max}=\min(1,\gamma_{\max}w)$、$b=\min(1,\sum w)$、式 (4)、(5) 及描述函数回传。$\tau$ 与正则形状在这里固定；训练这些参数时须加入响应的相应偏导。节点上限截断、总和下界截断和分段切换各使用声明的边界反向。

## 附录 S：配置与求值对应

| 配置 | 本章绑定 |
|---|---|
| selection_mode | shared_amplification，式 (7)、(8) |
| local_score、region_score | cat／match；ind／att；使用式 (3) 的对应描述 |
| query_weight | att 固定 received；ind 不使用 |
| amplification_mode | fixed 或 context，分别使用固定比例或上下文额度头 |
| amplification_fraction | fixed 的 $a_j^E\in[0,1]$ |
| amplification_width | $d_E$；context 的逐节点额度特征宽度 |
| gamma_max | 固定最大倍率 $\gamma_{\max}\ge1$ |
| regularizer、ent_alpha | quad，或 ent 且固定 $\alpha\in[1,2]$ |
| k、eta、allocation_temperature | 总发送上限、共同评分阈值、正温度 |

send_gain 与 allocation_base 不参与本候选。context 的投影、区域隐藏层及偏置按第 2—3 节给定；描述模式与记忆函数由共同架构绑定。该配置不自动定义温度等于零时的求值函数，单位输入的比较硬运行按 §7.3 单独绑定。

实现核对集中在[共享额度检查](../../reference/weighted-message-implementation-checks.md#35-区域共享放大额度)。额度投影与汇集计入 Read／SelStep，嵌套求解与反向计入 SelStep；Full、消息数和下游准备按实际支持与拓扑计量。浮点近零裁剪、有限迭代误差和替代梯度分别记录。
