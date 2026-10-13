---
type: technical-note
status: active
tags:
  - technical-notes
  - attention
  - position-encoding
  - recurrent-memory
cssclasses:
  - textbook-math
evidence_checked: 2026-09-28
original_updated: 2026-09-29
updated: 2026-10-13
---

# 局部性、位置机制与循环记忆

**从注意力核与状态转移理解三种架构维度**

理论与实验资料核对至 **2026-09-28**；原稿重写于 2026-09-29，2026-10-13 迁入本库并整理格式。模型配置单列于 [[30-technical-notes/attention-model-configurations|模型配置对照]]，其核对日期为 2026-09-29。

本文假设读者熟悉 Transformer、因果注意力、Q/K/V、RoPE 和 KV cache。目标是把局部／全局、NoPE／RoPE、SSM／Delta 类更新放进统一的数学框架，再讨论它们的组合、实证结果与适用边界。默认讨论因果语言模型；公式以单层、单头为主，省略与当前论点无关的残差、FFN 和外围归一化。

阅读顺序：[[#1. 统一框架：支持集、位置算子与历史表示|统一框架]] → [[#2. 局部性与显式位置机制：同一注意力算子的两种修改|局部性与位置机制]] → [[#3. 第三维：状态转移如何改变有效历史核|循环状态]] → [[#4. 三个维度怎样组合|组合]] → [[#5. 实证：分别检验哪些维度及其交互|实验]] → [[#6. 由三维框架分析训练、外推与资源成本|训练、外推与成本]] → [[30-technical-notes/attention-model-configurations|模型实例]]。

## 1. 统一框架：支持集、位置算子与历史表示

设 $x_t$ 为本层输入，$q_t,k_t\in\mathbb R^{d_k}$，$v_t\in\mathbb R^{d_v}$。将一类注意力写成

$$
\begin{aligned}
z_{ts}&=\frac{q_t^\top P_{ts}k_s}{\sqrt{d_k}}+b_{ts}+m_{ts},\\
a_{ts}&=\operatorname{softmax}_{s\le t}(z_{ts}),
\qquad o_t=\sum_{s\le t}a_{ts}v_s.
\end{aligned}
\tag{1}
$$
^apm-eq-01

其中 $m_{ts}\in\{0,-\infty\}$ 是 mask，$P_{ts}\in\mathbb R^{d_k\times d_k}$ 是显式位置算子，$b_{ts}$ 是可选的附加偏置。标准 NoPE 对应 $P_{ts}=I,b_{ts}=0$；标准 RoPE 对应 $P_{ts}=R_t^\top R_s=R_{s-t},b_{ts}=0$。后文会用 $b_{ts}$ 表示内容依赖的遗忘偏置。

三种维度在此有不同的数学对象：

| 维度 | 数学对象 | 主要选择 | 改变的能力或约束 |
|---|---|---|---|
| **① 直接访问范围** | $\mathcal V_t=\{s:m_{ts}=0\}$ | 全局、滑窗、分块等 | 当前查询可直接匹配哪些历史记录。 |
| **② 显式位置机制** | $P_{ts}$，以及显式位置偏置 | NoPE、RoPE、部分 RoPE | 内容匹配怎样依赖位置坐标。 |
| **③ 历史表示与更新** | 逐词元 KV，或固定大小状态 $Z_t$ | 保留记录；$Z_t=F_t(Z_{t-1},x_t)$；二者混合 | 历史是否仍可逐条寻址，或已被压缩、衰减、覆盖。 |

前两维直接改变[[#^apm-eq-01|式 (1)]]，第三维则可能改变[[#^apm-eq-01|式 (1)]] 的实现形式乃至算子本身。循环模型即使能展开为

$$
o_t=\sum_{s\le t}\kappa_{ts}v_s,
\tag{2}
$$
^apm-eq-02

也不意味着它存有所有 $(k_s,v_s)$；$\kappa_{ts}$ 还可能不满足非负、和为 1 等 softmax 性质。

因此，“三维”是三个分析角度，不是独立的三个二元开关。对纯循环模块，第一维不能直接标成“全局注意力”：**历史影响的支持集可以覆盖整个前缀，而查询时可逐条访问的历史记录可以为空。**

## 2. 局部性与显式位置机制：同一注意力算子的两种修改

### 2.1 局部性改变 mask

令滑窗宽度 $W$ 包含当前位置，定义

$$
\begin{aligned}
\mathcal V_t^{G}&=\{1,\ldots,t\},\\
\mathcal V_t^{W}&=\{\max(1,t-W+1),\ldots,t\},\\
m_{ts}^{\mathcal V}&=\begin{cases}
0,&s\in\mathcal V_t,\\
-\infty,&s\notin\mathcal V_t.
\end{cases}
\end{aligned}
\tag{3}
$$
^apm-eq-03

全局与滑窗的差别是某项是否进入 softmax，而不是距离权重的强弱。若只有 $D$ 层宽度为 $W$ 的滑窗注意力，且没有其他跨位置通路，则给定输入的一次前向计算中，末位置的理论感受野长度满足

$$
L_{\mathrm{RF}}\le\min\{L,\ 1+D(W-1)\}.
\tag{4}
$$
^apm-eq-04

多层传播扩大了影响范围，但远处信息必须经过中间表示。全局注意力提供直接读取路径；两者都不保证训练后保留或正确利用了相关信息。分块局部注意力的 mask 不同，不能直接套用滑窗的[[#^apm-eq-04|式 (4)]]。

### 2.2 RoPE 改变匹配的双线性形式

记二维旋转为 $\operatorname{Rot}(\phi)$。固定频率 $\omega_j$ 下，

$$
\begin{aligned}
R_t&=\bigoplus_j\operatorname{Rot}(t\omega_j),
\qquad R_t^\top R_s=R_{s-t},\\
z_{ts}^{\mathrm{RoPE}}&=\frac{q_t^\top R_{s-t}k_s}{\sqrt{d_k}}+m_{ts}.
\end{aligned}
\tag{5}
$$
^apm-eq-05

这里的相对性属于位置算子；$q_t,k_s$ 仍依赖内容和上游表示。旋转也不蕴含单调距离衰减：一个二维分量即可产生随 $s-t$ 振荡的匹配项。[R01]

对部分 RoPE，分解 $q_t=(q_t^c,q_t^r)$、$k_s=(k_s^c,k_s^r)$，其中不旋转维数为 $d_c$、旋转维数为偶数 $d_r$，且 $d_c+d_r=d_k$。于是

$$
\begin{aligned}
P_{ts}&=I_{d_c}\oplus R_{s-t},\\
z_{ts}&=\frac{(q_t^c)^\top k_s^c+(q_t^r)^\top R_{s-t}k_s^r}
{\sqrt{d_k}}+m_{ts}.
\end{aligned}
\tag{6}
$$
^apm-eq-06

它将不旋转的内容匹配与旋转匹配放在同一次读取中。NoPE、部分 RoPE、完整 RoPE 分别对应 $d_r=0$、$0<d_r<d_k$、$d_r=d_k$。

### 2.3 NoPE 的含义是没有本层显式位置项

对一层没有位置项的注意力，令 $\Pi$ 为位置置换矩阵，$M$ 为其 mask 矩阵，则有

$$
\operatorname{Attn}_{M}(\Pi X)
=\Pi\operatorname{Attn}_{\Pi^\top M\Pi}(X).
\tag{7}
$$
^apm-eq-07

无 mask 时，这给出置换等变性；固定因果 mask 一般不满足 $\Pi^\top M\Pi=M$，所以不能由 $P_{ts}=I$ 推出整个因果模型不区分顺序。

此外，第 $j$ 层的输入可以写为 $x_t^{(j)}=F_j(x_{1:t}^{(0)})$。即使第 $j$ 层采用 NoPE，$F_j$ 仍可能包含上游的 RoPE、卷积和循环更新。理论构造与实验均表明，因果 NoPE Transformer 可以形成位置表示；这不保证所有数据与优化设置都会学到所需表示，也不保证任意长度外推。[R02][R03]

### 2.4 二维平面的四格

以下均取 $b_{ts}=0$：

|  | **NoPE：$P_{ts}=I$** | **RoPE：$P_{ts}=R_{s-t}$** |
|---|---|---|
| **全局：$\mathcal V_t=\mathcal V_t^G$** | 可直接匹配所有记录；顺序关系依赖内部表示与结构；候选数随长度增长。 | 可直接匹配所有记录；显式使用相对位移；候选数与最大相对位移均随长度增长。 |
| **滑窗：$\mathcal V_t=\mathcal V_t^W$** | 只匹配窗口内记录；无额外旋转；大规模受控证据较少。 | 只匹配窗口内记录；显式相对位移被限制在 $[-W+1,0]$。 |

两个维度在公式上可以分别选择。**局部性给出硬支持集；RoPE 给出支持集内的匹配结构。** 去掉 RoPE 不会扩大支持集，增加 RoPE 也不会补回不可访问的记录。

只在第一层使用 RoPE、后续层采用 NoPE，是一种合法的逐层混合。后续层仍可利用上游形成的位置表示，但其分数不再直接具有本层的[[#^apm-eq-05|式 (5)]]。它不等价于每层都使用 RoPE。

## 3. 第三维：状态转移如何改变有效历史核

### 3.1 SSM：历史贡献由转移矩阵乘积决定

令输入 $x_t\in\mathbb R^{d_x}$，状态 $h_t\in\mathbb R^n$。离散状态空间模型（SSM）的基本形式为

$$
h_t=A_th_{t-1}+B_tx_t,
\qquad
o_t=C_th_t,
\tag{8}
$$
^apm-eq-08

其中 $A_t\in\mathbb R^{n\times n}$、$B_t\in\mathbb R^{n\times d_x}$、$C_t\in\mathbb R^{d_v\times n}$。选择式 SSM 允许其中部分系数依赖输入；Mamba 系列通过约束这些矩阵的结构获得高效算法。[R09][R10]

设 $h_0=0$，定义传播算子 $\Phi(t,s)=A_tA_{t-1}\cdots A_{s+1}$，并约定 $\Phi(t,t)=I$，则

$$
\begin{aligned}
h_t&=\sum_{s=1}^t\Phi(t,s)B_sx_s,\\
o_t&=\sum_{s=1}^t C_t\Phi(t,s)B_sx_s.
\end{aligned}
\tag{9}
$$
^apm-eq-09

$C_t\Phi(t,s)B_s$ 是历史位置 $s$ 到当前位置 $t$ 的有效线性算子。它可以对任意远的 $s$ 非零，而实现只需保留 $h_t$。

若 $A_j=\alpha_jI$、$0<\alpha_j\le1$，定义累计衰减量 $\tau(t,s)=-\sum_{j=s+1}^t\log\alpha_j$，则

$$
\Phi(t,s)=\left(\prod_{j=s+1}^t\alpha_j\right)I=e^{-\tau(t,s)}I.
\tag{10}
$$
^apm-eq-10

固定 $\alpha_j=e^{-\lambda}$ 时，$\tau(t,s)=\lambda(t-s)$，确实得到距离相关权重；当 $\alpha_j$ 由内容决定时，$\tau(t,s)$ 依赖中间内容，不再仅由 $t-s$ 决定。**这同时是时序结构和信息保留机制，不能仅理解为另一种位置坐标。**

循环执行本身也不保证顺序敏感：$A_t=B_t=I$ 时，$h_t=\sum_{s\le t}x_s$ 对输入排列不变。顺序能力必须由具体的转移和写入规则解释。

### 3.2 矩阵状态：从线性注意力到 Delta 类更新

为统一方向，以下把矩阵状态记为 $S_t\in\mathbb R^{d_v\times d_k}$；部分论文使用其转置。考虑

$$
S_t=S_{t-1}T_t+\eta_t v_tk_t^\top,
\qquad
o_t=S_tq_t,
\tag{11}
$$
^apm-eq-11

其中 $T_t\in\mathbb R^{d_k\times d_k}$ 是状态转移，$\eta_t$ 是写入系数。它对状态是仿射的，但 $T_t,\eta_t,q_t,k_t,v_t$ 可以依赖输入，整个模型不必对输入线性。

设 $S_0=0$，定义按时间从左到右相乘的 $\Psi(s,t)=T_{s+1}\cdots T_t$、$\Psi(t,t)=I$，得到

$$
\begin{aligned}
S_t&=\sum_{s=1}^t\eta_s v_sk_s^\top\Psi(s,t),\\
o_t&=\sum_{s=1}^t
\underbrace{\eta_s k_s^\top\Psi(s,t)q_t}_{\kappa_{ts}}
v_s.
\end{aligned}
\tag{12}
$$
^apm-eq-12

[[#^apm-eq-12|式 (12)]] 是连接三个维度的关键：$\kappa_{ts}$ 可以覆盖全历史、包含顺序与内容依赖，但全部历史已合并进一个 $S_t$，没有逐词元 KV。它也没有 softmax 归一化，不能直接等同于[[#^apm-eq-01|式 (1)]]。

对给定 Q/K/V，Delta 类更新的 $\kappa_{ts}$ 通常还依赖中间的 $k_{s+1:t}$ 与门序列，不是固定的 $f(t-s)$。这是本层状态更新产生的路径依赖；将其全部称为“隐式距离编码”会遗漏定向改写的作用。

令 $\beta_t$ 为 Delta 更新强度、$\alpha_t$ 为标量保留门，$D_t=\operatorname{Diag}(\alpha_{t,1},\ldots,\alpha_{t,d_k})$ 为通道保留门，几种更新可放在同一张表中：

| 核心机制 | $T_t$ | $\eta_t$ | 主要作用 |
|---|---|---|---|
| 未归一化线性注意力 | $I$ | $1$ | 叠加键值外积。 |
| 标量门控线性注意力 | $\alpha_tI$ | $1$ | 对旧关联统一衰减。 |
| DeltaNet | $I-\beta_tk_tk_t^\top$ | $\beta_t$ | 沿当前键方向修正旧关联。 |
| Gated DeltaNet | $\alpha_t(I-\beta_tk_tk_t^\top)$ | $\beta_t$ | 统一衰减＋定向修正。[R11] |
| Kimi Delta Attention（KDA） | $D_t(I-\beta_tk_tk_t^\top)$ | $\beta_t$ | 通道衰减＋定向修正。[R12] |

KDA 的 $D_t$ 与 $I-\beta_tk_tk_t^\top$ 一般不交换，乘法顺序不能任意更改。表中省略了各架构的输出门、归一化与短卷积；这些组件会影响实际结果。

### 3.3 Delta rule 是对状态的误差修正

Gated DeltaNet 可写成先衰减、再修正的形式：

$$
\begin{aligned}
\widetilde S_t&=\alpha_tS_{t-1},
\qquad \mathcal L_t(S)=\tfrac12\|Sk_t-v_t\|_2^2,\\
S_t&=\widetilde S_t-\beta_t\nabla_S\mathcal L_t(\widetilde S_t)\\
&=\widetilde S_t+\beta_t(v_t-\widetilde S_tk_t)k_t^\top.
\end{aligned}
\tag{13}
$$
^apm-eq-13

这里更新的是请求相关状态，不是模型的预训练参数。若 $\|k_t\|_2=1$，则

$$
\begin{aligned}
S_tk_t&=(1-\beta_t)\widetilde S_tk_t+\beta_tv_t,\\
(S_t-\widetilde S_t)u&
=\beta_t(v_t-\widetilde S_tk_t)(k_t^\top u).
\end{aligned}
\tag{14}
$$
^apm-eq-14

第一式表示沿当前键进行插值覆盖；第二式说明对其他方向 $u$ 的干扰由 $k_t^\top u$ 控制。这比“累积内容再统一衰减”多出了一项基于关联误差的记忆管理。

原始 Gated DeltaNet 常用 $0<\alpha_t,\beta_t<1$。对单位键，其转移特征值为

$$
\begin{aligned}
T_tk_t&=\alpha_t(1-\beta_t)k_t,\\
T_tu&=\alpha_tu\quad(u\perp k_t).
\end{aligned}
\tag{15}
$$
^apm-eq-15

因此它同时包含统一衰减和额外的方向性抑制。不同键产生的 $T_t$ 一般不交换，顺序信息既来自衰减次数，也来自状态变换的次序。

某些后续方法扩大更新范围，或组合多个方向变换。比如单位向量 $u$ 对应的 $I-2uu^\top$ 是 Householder 反射，可以翻转一个方向。DeltaProduct 等工作利用更丰富的转移提高状态跟踪能力。[R18] 这些改变涉及可执行的状态运算，不宜只称作“位置编码增强”。

### 3.4 固定状态的容量限制与转移表达能力

若模型参数固定，读完长度 $L$ 的输入后只保留 $M$ 比特状态，且不能访问外部历史记录，要精确复述词表大小为 $V$ 的任意输入，必须满足

$$
2^M\ge V^L
\quad\Longrightarrow\quad
M\ge L\log_2V.
\tag{16}
$$
^apm-eq-16

这是有限精度下的容量限制。[R16] RoPE、NoPE 或更复杂的转移都不能消除它。全局 KV 也不保证无损保存输入，但其请求相关存储允许随 $L$ 增长。

相反，奇偶状态只需一比特。对 $b_t\in\{0,1\}$、$u_t\in\{-1,1\}$，递推 $u_t=(-1)^{b_t}u_{t-1}$ 可处理任意长操作序列。此时关键是转移族能否表示并学会相应运算，而不是状态容量。

关于 SSM 状态跟踪的理论上界依赖具体深度、精度和转移约束。[R17] 应分别判断 **容量、转移表达能力、优化是否学到正确更新**；不能从“有状态”推出任意状态跟踪能力，也不能把某个受限 SSM 的上界推广到所有循环模型。

## 4. 三个维度怎样组合

### 4.1 衰减与旋转可以同时进入循环核

先取 $T_j=\alpha_jI$、$\eta_j=1$，并令 $g_t=\prod_{j=1}^t\alpha_j>0$。[[#^apm-eq-12|式 (12)]] 可以改写为

$$
\kappa_{ts}=\frac{g_t}{g_s}q_t^\top k_s
=(g_tq_t)^\top(k_s/g_s).
\tag{17}
$$
^apm-eq-17

同一种衰减核既能表述为状态递推，也能表述为对 Q/K 的不同缩放。若门依赖内容，缩放便依赖内容历史。这个代数重写不增加状态容量，直接计算很小的 $g_s$ 的倒数也可能数值不稳定。

**RetNet** 将距离衰减与旋转组合。对固定 $0<\gamma<1$，其核心可写为

$$
\begin{aligned}
S_t&=\gamma S_{t-1}+v_t(R_tk_t)^\top,\\
o_t&=S_tR_tq_t
=\sum_{s\le t}\gamma^{t-s}
q_t^\top R_{s-t}k_s\,v_s.
\end{aligned}
\tag{18}
$$
^apm-eq-18

它同时有相对旋转与有限状态实现，但没有标准 softmax。[R13]

**Mamba-3** 进一步研究内容依赖旋转。用一个二维状态块说明该部分机制：若 $A_j=\rho_j\operatorname{Rot}(\theta_j)$，则

$$
\Phi(t,s)
=\left(\prod_{j=s+1}^t\rho_j\right)
\operatorname{Rot}\!\left(\sum_{j=s+1}^t\theta_j\right).
\tag{19}
$$
^apm-eq-19

$\rho_j$ 控制幅度，$\theta_j$ 控制相位。当 $\theta_j=\omega$ 固定时，相位差正比于词元距离；当 $\theta_j$ 由输入决定时，相位差由中间事件决定。Mamba-3 的完整结构还包含更丰富的离散化和读写形式，[[#^apm-eq-19|式 (19)]] 只抽取其旋转机制。[R15]

这也说明“显式／隐式”不一定是互斥标签：一种状态变换可以等价写成读写向量的变换。需要具体记录它依赖固定位置坐标还是输入内容，以及历史是否仍被压入固定状态。

### 4.2 遗忘偏置也可以用于保留完整 KV 的 softmax 注意力

Forgetting Transformer（FoX）取 $P_{ts}=I$，引入内容依赖保留门 $f_j\in(0,1)$。令 $F_{ts}=\prod_{j=s+1}^t f_j$，其注意力可写为

$$
\begin{aligned}
z_{ts}&=q_t^\top k_s/\sqrt{d_k}+\log F_{ts}+m_{ts},\\
a_{ts}&
=\frac{\exp(q_t^\top k_s/\sqrt{d_k})F_{ts}}
{\sum_{u\in\mathcal V_t}\exp(q_t^\top k_u/\sqrt{d_k})F_{tu}}
\quad(s\in\mathcal V_t).
\end{aligned}
\tag{20}
$$
^apm-eq-20

这里的遗忘降低旧记录的权重，但记录仍可逐条保存与匹配。默认 FoX 不用 RoPE，也不因此获得固定状态模型的存储复杂度。[R14]

[[#^apm-eq-18|式 (18)]] 与[[#^apm-eq-20|式 (20)]] 都有衰减，却属于不同的历史表示。前者在有限状态里汇总贡献；后者仍在 KV 上计算 softmax。**遗忘、旋转、固定状态压缩应分别标注。**

### 4.3 混合结构应按层指定三个维度

记 $\mathcal A_G^I,\mathcal A_G^R,\mathcal A_W^I,\mathcal A_W^R$ 为第 2 节四类注意力模块，$\mathcal F_T$ 为具有相应转移规则的循环模块。不同层的参数独立。两种常见层序如下，第二行的 $P$ 可取 $I$ 或 $R$：

$$
\begin{aligned}
\mathcal A_W^R&\ \longrightarrow\ \cdots\ \longrightarrow\ \mathcal A_W^R
\ \longrightarrow\ \mathcal A_G^I,\\
\mathcal F_T&\ \longrightarrow\ \cdots\ \longrightarrow\ \mathcal F_T
\ \longrightarrow\ \mathcal A_G^P.
\end{aligned}
\tag{21}
$$
^apm-eq-21

前面的局部或循环层先改变 $x_t$，后面的全局层再从这些表示构造 Q/K/V。因此，全局 NoPE 层的 $P_{ts}=I$ 不意味着输入缺少顺序结构。其可能的收益是：由前序模块组织局部关系或状态，而全局读取不再额外施加本层的固定相对旋转。收益是否出现是实证问题。

| 模块组合 | 远处逐词元记录 | 额外状态通路 | 关键边界 |
|---|---|---|---|
| 局部＋全局注意力 | 全局层保留 | 无 | 远距离直接读取依赖全局层。 |
| 纯循环 | 无 | 有 | 所有历史信息必须经过有限状态。 |
| 循环＋局部注意力 | 窗口外无独立记录可供全局读取 | 有 | 窗口内可直接检索，窗口外依赖状态及逐层传播。 |
| 循环＋全局注意力 | 全局层保留 | 有 | 状态和逐词元记录共存；缓存仍随长度增长。 |

局部模块与循环模块可能承担重叠的短中程处理，但其存储结构不同。用局部注意力替换循环层，或删除混合模型的全局层，都必须重新检验任务行为。

### 4.4 MLA 的压缩发生在不同轴上

多头潜在注意力（MLA）压缩每个词元的 KV 表示；记压缩后的记录为 $c_s\in\mathbb R^r$，则通常仍保存 $\{c_s\}_{s=1}^L$。矩阵循环状态则只保存 $S_L$。忽略其他缓存分量，有

$$
M_{\mathrm{MLA}}=\Theta(Lr),
\qquad
M_{\mathrm{recurrent}}=\Theta(d_vd_k).
\tag{22}
$$
^apm-eq-22

MLA 降低单条记录的大小，循环状态压缩跨词元历史。DeepSeek-V3 还将内容分量与 RoPE 分量解耦；这既不是整个层 NoPE，也不是把全部历史压成一个状态。[R22]

## 5. 实证：分别检验哪些维度及其交互

以下数字来自论文，未重新训练复现。参数与训练 token 使用 B、T 表示十亿、万亿；长度沿用论文的 K、M 记法。任务分数越高越好，loss／PPL 越低越好。RULER 衡量长上下文检索与聚合等能力，NIAH 为其中的目标信息检索任务；RepoQA 侧重代码仓库查询，LongBench V2 侧重复杂长上下文理解。

### 5.1 第一维与第二维：缩小范围不等于删除位置旋转

[R07] 的一组对照约为 0.66B 参数、100B token、16K 训练长度；混合模型的局部／全局层比例为 1∶1，$W=128$。

| 结构 | 短任务均分 | 16K RULER | NIAH 子集 |
|---|---:|---:|---:|
| 全局 RoPE | 40.46 | 47.17 | 67.14 |
| 局部 RoPE＋全局 RoPE | 41.31 | 46.13 | 65.91 |
| 局部 RoPE＋全局 NoPE | 41.32 | **52.88** | **82.31** |

第一步主要改变 $m_{ts}$，没有改善长上下文成绩；第二步在相同混合结构中改变全局层的 $P_{ts}$，才出现明显改善。这支持访问范围与位置机制之间存在交互，不能分别排列“全局优于局部”或“NoPE 优于 RoPE”。

[R05] 的 8B、5T-token 版本使用三个局部 RoPE 层配一个全局 NoPE 层，$W=4096$；后续继续训练与微调最高到 128K：

| 测试长度 | 全局 RoPE：RULER 检索 | 混合：RULER 检索 | 全局 RoPE：RULER 问答 | 混合：RULER 问答 |
|---|---:|---:|---:|---:|
| 128K | 83.0 | **90.0** | 36.0 | **46.0** |
| 256K | 57.1 | **74.8** | 30.0 | **42.5** |

该论文另一个 8B、约 750B-token 预训练加监督微调的实验中，128K Needles 评分依次为：全局 RoPE 7.40、全局 RoPE／NoPE 交替 8.04、局部 RoPE／全局 NoPE 交替 9.56。后两者保持 RoPE 频率等配置一致，局部窗口为 8192；前两者还改变了频率，不能把差值全部归因于 NoPE。

这些结果支持[[#^apm-eq-21|式 (21)]] 的第一类分工。它们来自相应架构的训练，普通任务也有升有降；256K 的外推改善不意味着任意长度都可靠。

### 5.2 第三维内部：保留、遗忘与定向覆盖的取舍

[R11] 比较约 1.3B 参数、100B token、4K 训练长度的架构：

| 检索任务 | DeltaNet | Mamba-2 | Gated DeltaNet |
|---|---:|---:|---:|
| 简单重复背景中的密码，8K | **98.8** | 30.4 | 91.8 |
| 真实文章背景中的数字，4K | 18.6 | 56.2 | **92.2** |
| 真实文章背景中的随机标识符，4K | 22.4 | 4.6 | **27.6** |

简单背景下有效写入较少，额外衰减可能损害保留；复杂背景中，累积干扰使清理与定向修正更重要。这与[[#^apm-eq-10|式 (10)]]、(14) 的机制一致。最后一行仍然很低，表明改善有限状态的检索，不等于解决任意历史细节的保存。

这些是架构对照，状态容量和外围组件并未全部固定，不能把全部差异归到单个 $\alpha_t$ 或 $\beta_t$。同文的 0.4B 消融中，删除短卷积使平均 PPL 从 27.35 上升到 28.95，也说明模型的顺序能力不能只由状态衰减解释。

### 5.3 第二维与第三维：循环层不变，全局层的位置方案仍然重要

Kimi Linear [R12] 对照总参数约 48B、激活参数约 3B、1.4T 训练 token 的模型；混合结构为三个 KDA 层配一个全局 MLA 层，并包含后续长上下文训练。

| 结构 | RULER | RepoQA | LongBench V2 |
|---|---:|---:|---:|
| 全局 MLA 基线 | 81.3 | 63.0 | **36.1** |
| KDA＋全局 RoPE | 78.8 | 66.5 | 35.4 |
| KDA＋全局 NoPE | **84.3** | **68.5** | 35.0 |

后两行保持循环结构，改变全局层的位置机制：RULER 上升 5.5，RepoQA 上升 2.0，LongBench V2 下降 0.4。检索优势没有转化为每项复杂理解指标的优势。

这支持“循环表示＋全局 NoPE”是一种有效组合，同时表明全局位置机制仍需单独选择。模型保留全局 KV，结果不能归因于循环状态独自记住全部长输入，也不是仅在 4K 训练后的无校准外推。

### 5.4 位置机制的训练效果与任务效果没有统一排序

| 研究设置 | 观察 | 能支持的结论 |
|---|---|---|
| [R05] 的纯全局对照 | NoPE／RoPE 验证 loss 为 1.58／1.52；65K Needles 为 9.03／9.82。 | 混合结构中全局 NoPE 的收益，不能推广为整个模型纯 NoPE 的优势。 |
| [R08]，1B、8B 的部分 RoPE | 旋转约 10% 维度通常接近完整 RoPE 的收敛；部分纯 NoPE 配置出现 loss spike 或不收敛。 | 少量显式旋转可能已提供有效的优化结构；结果依赖配置。 |
| [R03]，短长度训练的合成任务 | 部分复制、排序、算术任务中 NoPE 外推优于 RoPE。 | 固定位置结构会影响学到的规则，不能从语言建模 loss 推出所有算法任务的排序。 |
| [R15]，Mamba-3 的状态跟踪消融 | 内容依赖旋转优于论文中的标准 RoPE 和无旋转变体。 | 相位随事件变化可增强状态运算；它与固定位置旋转承担不同功能。 |
| [R14]，FoX 消融 | 完整 Pro 版本再加 RoPE 对验证 PPL 基本无改善，部分其他变体有小幅改善。 | 已有遗忘结构时，额外旋转的收益仍依赖架构。 |

[R08] 中 Q/K 归一化缓解了部分 NoPE 优化问题，但没有在所有设置中消除最终差距。Mamba-3 论文中某些 Delta 对照也使用更丰富的转移设定，不能与原始 Gated DeltaNet 的门范围混为一谈。

### 5.5 混合模型是否实际使用了循环层的长期记忆

[R07] 通过限制各模块的历史范围发现，在其混合模型中，远距离检索主要依赖全局注意力：限制全局访问的损失较大，限制循环模块的远距离影响损失较小。[R19] 的较小规模模型中，以 $W=128$ 的局部 RoPE 替换 Gated DeltaNet，可改善部分检索与外推，但部分普通任务下降。

这区分了两个命题：循环核在数学上具有全历史支持；训练后的模型在某项任务上实际依赖这条长期通路。只有干预后者才能确定模块职责。相关研究的参数规模、状态大小、外围组件和训练预算均有限，尚不足以断言大型量产混合模型不使用长期状态。

## 6. 由三维框架分析训练、外推与资源成本

### 6.1 复杂度主要由访问范围和历史表示决定

固定模型宽度、层数和状态大小，只看长度 $L$ 与窗口 $W$ 的增长：

| 模块 | Prefill 主要计算量 | 单步 decode 历史处理量 | 持续保存的历史 |
|---|---:|---:|---|
| 全局注意力 | $O(L^2)$ | $O(L)$ | $O(L)$ 条 KV |
| 滑窗注意力 | $O(LW)$ | $O(W)$ | $O(W)$ 条 KV |
| 固定状态循环模块 | $O(L)$ | 对 $L$ 为常数 | 固定状态及必要的卷积缓存 |
| 循环／滑窗＋部分全局层 | 仍含二次项 | 仍含随 $L$ 增长的项 | 有界部分＋增长的全局 KV |

对[[#^apm-eq-13|式 (13)]] 的矩阵状态，利用外积和矩阵向量乘法，单步核心成本为 $O(d_vd_k)$，不需要显式构造稠密 $T_t$ 再进行矩阵乘法。该常数可能较大，所以固定状态在短上下文上不一定比少量 KV 更省。

令全局、局部、循环层的索引集合分别为 $\mathcal G,\mathcal W,\mathcal R$；第 $j$ 个注意力层每条 KV 占 $c_j$ 字节，局部窗口为 $W_j$，循环层的固定历史状态占 $m_j$ 字节，则

$$
\begin{aligned}
M_{\mathrm{history}}(L)
&\approx\sum_{j\in\mathcal G}c_jL\\
&\quad+\sum_{j\in\mathcal W}c_j\min(L,W_j)
+\sum_{j\in\mathcal R}m_j.
\end{aligned}
\tag{23}
$$
^apm-eq-23

NoPE 不改变这里的主要阶数；MLA 降低 $c_j$；减少全局层会减少第一项，但只要保留全局层，存储一般仍随 $L$ 增长。模型参数和临时工作区不在[[#^apm-eq-23|式 (23)]] 中，KV 降幅也不等于总显存降幅。

FlashAttention 改善 IO 和中间显存，但精确全局注意力的主要配对数量仍为二次。实际速度还取决于长度、批量、数值精度和 kernel 成熟度：[R11] 的短序列实验中，成熟的注意力实现可优于一些线性复杂度模型；[R12] 在其 1M 配置中报告约六倍解码加速，包含减少全局层和提高批量等收益，不能单独归因于 NoPE。

### 6.2 状态递推的训练：可并行性与梯度传播

若给定输入后更新对状态为仿射，两个更新可以组合为

$$
(A_2,b_2)\circ(A_1,b_1)
=(A_2A_1,\ A_2b_1+b_2).
\tag{24}
$$
^apm-eq-24

该组合满足结合律，因此递推语义不要求训练时逐 token 串行。结构化 scan 或分块算法可利用这一点；Gated DeltaNet、KDA 的高效实现还依赖对转移结构的专门处理。[R10][R11][R12] 若系数本身依赖尚未计算出的同层状态，则不能直接套用这种并行化。

另一方面，对[[#^apm-eq-08|式 (8)]]，固定本层输入及相应系数时，有

$$
\begin{aligned}
\frac{\partial h_t}{\partial h_s}&=\Phi(t,s),\\
\|\Phi(t,s)\|_2&\le\prod_{j=s+1}^t\|A_j\|_2.
\end{aligned}
\tag{25}
$$
^apm-eq-25

因此衰减既影响读出时的历史贡献，也影响这条状态通路的训练信号。过强衰减限制长期影响，过多保留又可能增加不同写入之间的干扰；门的初始化、键归一化、状态维数和精度都参与这一取舍。[[#^apm-eq-25|式 (25)]] 只描述该状态通路，不是整个深层网络的完整梯度。

窗口还会改变优化分工。[R07] 报告的 Large-Window Laziness 是：较大的局部窗口已解决大量短期预测依赖，使全局检索形成更慢。这是训练动态的观察，不是局部模块表达能力高于全局模块的定理。

### 6.3 长度外推分别面对位置、归一化与状态三类变化

| 模块 | 长度增长时的主要变化 | 不能由结构直接保证的性质 |
|---|---|---|
| 全局 RoPE | 可见候选数增加；$s-t$ 扩展到训练外范围。 | 在新相位关系下仍能正确匹配。 |
| 局部 RoPE | 在固定旋转规则下，始终有 $\lvert s-t\rvert\le W-1$。 | 窗口外细节可恢复，或整个模型表示分布不变。 |
| 全局 NoPE | 没有本层显式相位外推，但候选数与隐表示分布仍变化。 | softmax 不被干扰项稀释。 |
| 固定状态 | $\Phi$ 或 $\Psi$ 包含更多转移；写入与数值误差持续累积。 | 任意远信息仍可分离读出。 |

NoPE 的一个基本外推障碍可以直接算出。假设目标 logit 比每个干扰项高 $\Delta$，共有 $N$ 个同分干扰项；若希望目标权重至少为 $p\in(0,1)$，则

$$
\begin{aligned}
a_\star=\frac{e^\Delta}{e^\Delta+N}\ge p
\quad\Longleftrightarrow\quad
\Delta&\ge\log N\\
&\quad+\log\frac{p}{1-p}.
\end{aligned}
\tag{26}
$$
^apm-eq-26

因此，去掉旋转不等于消除长度分布变化。分数缩放 $z_{ts}\mapsto\lambda(L)z_{ts}$ 可以提高集中度，但也会改变选择行为；NoPE 长度泛化研究对这一问题已有实验分析。[R04]

SWAN-GPT [R06] 的局部 RoPE＋全局 NoPE 小模型在一个 1K 训练设置中，16K 单针检索未经缩放为 0.5%，缩放后为 90.7%。缩放函数使用长文档校准数据拟合，所以这个数字应与校准条件一起报告，不能当作无长数据接触的综合 16K 能力。

循环模型避免了随 $L$ 增长的存储，却仍受[[#^apm-eq-10|式 (10)]]、(12)、(16) 限制。能够继续递推、能够保留某个低维状态、能够恢复任意历史细节，是不同的外推目标。

评估长上下文声明时，应分别记录预训练、继续训练、校准和测试的长度。Kimi Linear、RNoPE-SWA 等模型的强长上下文结果包含后续长训练；支持 1M 本身无法反推出所有训练阶段的长度或所有任务的有效记忆范围。

### 6.4 缓存有效性是计算规则的一致性问题

令 $X_{1:t}$ 为模型输入前缀，$\theta$ 表示模型参数，$\pi$ 表示位置、mask 和状态更新等计算规则，完整的逐层历史缓存记为

$$
\mathcal C_t^{(\pi)}
=\operatorname{Cache}_{\theta,\pi}(X_{1:t}).
\tag{27}
$$
^apm-eq-27

若继续生成时，既有位置对应的计算规则保持不变，因果性允许从 $\mathcal C_t^{(\pi)}$ 增量得到下一步缓存。跨过训练长度不会自动破坏这个等价关系；质量下降与缓存不一致是两件事。

例如从 4K 开始就采用同一套面向 128K 的固定位置设置，到 32K＋1 不需重算过去 KV。超过 128K 可能遇到质量或实现限制，但不会仅因越过这个数值使旧缓存自动失效。若为了扩展而改成 $\pi'$，则不能一般地假设 $\mathcal C_t^{(\pi')}=\mathcal C_t^{(\pi)}$。仅修正缓存 K 的旋转，也未必修复上游隐藏表示的改变。

标准 RoPE 通常缓存旋转后的 K 和未旋转的 V；MLA 可保存压缩形式。循环层保存状态及必要的卷积缓存。原生滑窗可以删除不再允许读取的 KV；对原本全局的模型临时截断缓存，则改变了其算子。

回退时，保留了所需历史的全局 KV 通常可按前缀截断。循环状态通常需要快照或重放：覆盖可能不可逆，即使某个转移理论可逆，接近零的转移特征值也会放大逆运算误差。修改前缀中间内容时，两类架构都需要重建受影响的后续计算。

### 6.5 任务取舍：先区分所需信息，再比较模型

| 任务结构 | 主要需求 | 三维框架下的判断 |
|---|---|---|
| $y_t=f(x_{t-W+1:t})$ | 局部内容与顺序 | 合适窗口可覆盖直接依赖；RoPE、卷积、状态更新可提供不同的顺序结构。 |
| $z_t=f(z_{t-1},x_t)$，再从 $z_t$ 回答 | 状态转移表达能力与稳定更新 | 固定状态可能高效，但必须能表示并学会任务的递推规则。 |
| 输入后才给出索引 $i$，要求返回 $x_i$ | 事先未知的历史细节 | 在最坏情形要求精确回答任意 $i$ 时，固定总信息容量构成根本约束；全局记录具有存储优势。 |
| 多文档、多记录的联合推理 | 检索、信息交换与中间计算 | 单针检索成绩不足以判断整体能力；全局层分布、状态更新和训练均可能重要。 |

自然语言任务通常不要求无损保存每个 token，任务相关信息量也不等于原始长度。因此固定状态并非天然只能处理短上下文；同样，完整 KV 提供读取路径也不保证模型会正确使用它。架构性质给出约束，质量比较仍需匹配任务和预算的实验。

## 参考文献

下列来源支持文中的机制描述和实验数字；公式采用本文统一的状态方向与记号。模型配置和实现链接见 [[30-technical-notes/attention-model-configurations|模型配置对照]]。

### 位置机制、访问范围与混合分工

| 编号 | 论文 |
|---|---|
| [R01] | Round and Round We Go! What makes Rotary Positional Encodings useful? |
| [R02] | Transformer Language Models without Positional Encodings Still Learn Positional Information |
| [R03] | The Impact of Positional Encoding on Length Generalization in Transformers |
| [R04] | Length Generalization of Causal Transformers without Position Encoding |
| [R05] | RoPE to NoPE and Back Again: A New Hybrid Attention Strategy |
| [R06] | SWAN-GPT: An Efficient and Scalable Approach for Long-Context Language Modeling |
| [R07] | Rethinking the Role of Efficient Attention in Hybrid Architectures |
| [R08] | Fractional Rotation, Full Potential? Investigating Performance and Convergence of Partial RoPE |
| [R19] | Modern Transformers Are Implicit Hybrids: From Functional Differentiation to Principled Hybrid Architecture Design |

### 循环记忆、更新规则与理论边界

| 编号 | 论文 |
|---|---|
| [R09] | Mamba: Linear-Time Sequence Modeling with Selective State Spaces |
| [R10] | Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality |
| [R11] | Gated Delta Networks: Improving Mamba2 with Delta Rule |
| [R12] | Kimi Linear: An Expressive, Efficient Attention Architecture |
| [R13] | Retentive Network: A Successor to Transformer for Large Language Models |
| [R14] | Forgetting Transformer: Softmax Attention with a Forget Gate |
| [R15] | Mamba-3: Improved Sequence Modeling using State Space Principles |
| [R16] | Repeat After Me: Transformers are Better than State Space Models at Copying |
| [R17] | The Illusion of State in State-Space Models |
| [R18] | DeltaProduct: Improving State-Tracking in Linear RNNs via Householder Products |

### 模型结构报告

| 编号 | 论文 |
|---|---|
| [R20] | Griffin: Mixing Gated Linear Recurrences with Local Attention for Efficient Language Models |
| [R21] | Gemma 3 Technical Report |
| [R22] | DeepSeek-V3 Technical Report |

[R01]: https://arxiv.org/abs/2410.06205
[R02]: https://arxiv.org/abs/2203.16634
[R03]: https://arxiv.org/abs/2305.19466
[R04]: https://arxiv.org/abs/2404.12224
[R05]: https://arxiv.org/abs/2501.18795
[R06]: https://arxiv.org/abs/2504.08719
[R07]: https://arxiv.org/abs/2606.15378
[R08]: https://arxiv.org/abs/2603.11611
[R09]: https://arxiv.org/abs/2312.00752
[R10]: https://arxiv.org/abs/2405.21060
[R11]: https://arxiv.org/abs/2412.06464
[R12]: https://arxiv.org/abs/2510.26692
[R13]: https://arxiv.org/abs/2307.08621
[R14]: https://arxiv.org/abs/2503.02130
[R15]: https://arxiv.org/abs/2603.15569
[R16]: https://arxiv.org/abs/2402.01032
[R17]: https://arxiv.org/abs/2404.08819
[R18]: https://arxiv.org/abs/2502.10297
[R19]: https://arxiv.org/abs/2609.02986
[R20]: https://arxiv.org/abs/2402.19427
[R21]: https://arxiv.org/abs/2503.19786
[R22]: https://arxiv.org/abs/2412.19437

## 文档来源

本笔记由 [[90-archive/attention-position-memory/attention-position-memory-2026-09-29|2026-09-29 完整原稿]] 整理，保留统一的机制分析与实验证据，将模型配置移至独立笔记。较早的二维讨论保存在 [[90-archive/attention-position-memory/global-local-rope-nope-dialogue|全局／局部与 RoPE／NoPE 原始问答]]。
