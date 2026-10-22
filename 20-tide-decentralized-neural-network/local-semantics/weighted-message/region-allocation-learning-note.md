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

节点用当前接收与自身记忆参与区域分工。本章实现[局部架构](architecture-learning-note.md)中的两个接口：Describe 把本节点的信息变为描述，SelStep 收齐区域描述后决定各节点的发送强度。

计算依次为：当前接收与记忆形成节点描述，区域收齐描述后计算评分及所需的总量或阈值，再分配发送控制。指定总量直接规定本次发送强度之和；区域阈值调节共同发送意愿；逐节点增益另可调节各节点的接收相关发送量。评分参与候选之间的分配。下文先构造这些量，再给出约束优化、Attention 份额、按比例分配与硬选择的完整返回，随后讨论例子、求解、导数和组合性质。

## 1. 已有输入与接口任务

固定区域 $j$ 的一次选择，候选集为 $C\subseteq\mathcal R_j$。节点 $v$ 的聚合输入为 $h_v=(r_v^{\mathrm{in}},u_v)$，两项分别是接收强度和 $d$ 维内容。消息、候选、归一化及广播沿用[局部架构](architecture-learning-note.md)；矩阵和偏置均为有限参数。

沿用[架构 §3.2](architecture-learning-note.md#32-从状态取得记忆描述)的描述宽度 $d_s$ 和当前内容特征 $p_v(u_v)\in\mathbb R^{d_s}$。描述模式确定本次读取的状态 $q_v^{\mathrm{read}}$，从该状态取得记忆描述：

$$
\operatorname{Mem}_v(q_v^{\mathrm{read}},\theta,u_v)
=(M_{v,\mathrm{short}},M_{v,\mathrm{long}},W_{v,\mathrm{short}},W_{v,\mathrm{long}}).
$$

两个 $M_{v,a}\in\mathbb R^{d_s}$ 提供记忆内容，两个 $W_{v,a}\ge0$ 提供接收积累的统计量，$a\in\{\mathrm{short},\mathrm{long}\}$。$p_v$ 与 Mem 的具体计算由所选记忆模块给定。

Describe 从这些输入中构造区域所需的字段。不同发送函数需要不同字段；下表先说明它们的用途，第 2 节再给出具体构造。

| 节点内部产生的量 | 用途 | 使用它的分配 |
|---|---|---|
| 局部评分 $s_v^{\mathrm{loc}}\in\mathbb R$ | 提供本节点的相关性评分，随后形成区域评分 $s_v$ | 使用评分的各候选 |
| 区域证据 $z_v^{\mathrm{reg}}\in\mathbb R^{d_{\mathrm{reg}}}$ | 向区域提供内容与记忆信息，供其决定发送总量或阈值 | 指定总量、区域阈值 |
| 节点增益 $\gamma_v\in[1,\gamma_{\max}]$ | 调节本节点由接收得到的发送量 $\mu_v$，其上限或权重用途由分配给定 | 节点增益与固定阈值分配及使用 $\mu_v$ 的其他规则 |

$d_{\mathrm{reg}}$ 是正整数证据宽度，$\gamma_{\max}\ge1$ 是有限最大倍率。采用区域 Attention 评分时，描述另含当前内容投影与记忆 key；它们供区域构造 query 并计算匹配。各字段按所选函数计算，输出参数分别给定。

Describe 将区域需要的字段组装为描述 $d_v$。沿用架构的参数化记法，

$$
d_v=\operatorname{Describe}_v[\operatorname{Mem}_v,p_v]
 (q_v^{\mathrm{read}},\theta,h_v)\in D_v.
$$

方括号内的函数在模型绑定时选定，以下省略；各次调用使用它们在当前输入上的值。描述空间 $D_v$ 随区域评分与发送函数配套确定。

SelStep 收齐描述族，得到区域评分及所需的控制输出，再分配发送。控制 $c_v\in[0,1]$ 表示发送强度，$\mathcal A=\{v\in C:c_v>0\}$；区域历史为单点 $*$，故完整返回为

$$
\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_{v\in C})
=(\mathcal A,(c_v)_{v\in C},*).
$$

组成模型时，在下列位置分别选择函数。表中名称先指出可替换的计算，后文按依赖次序定义它们。

| 选择位置 | 候选及作用 | 构造位置 |
|---|---|---|
| 局部评分 | 拼接（cat）或分组匹配（match），产生 $s_v^{\mathrm{loc}}$ | §2.3 |
| 区域评分 | 独立评分直接使用局部评分；区域 Attention 另加入共同 query 与节点 key 的匹配 | §2.4、§3.1—3.2 |
| 区域证据 | 上下文总量或阈值使用拼接（cat）或分组（grouped）证据；固定控制使用零证据 | §2.5、§3.3—3.4 |
| 节点增益 | 使用节点增益描述的函数，选择固定增益或拼接上下文增益 | §2.6 |
| 发送分配 | 约束分配及其配对函数、Attention 份额分配、按比例分配 | §4 |

局部评分、记忆 key 与区域证据分别绑定。例如 match 评分可以配 cat 证据和内容 key；各自参数默认独立，共享时显式声明。选择发送函数同时确定所需描述：指定总量、区域阈值及各自配对函数使用 §2.5 的描述，其余发送使用 §2.6 的描述；区域评分再决定其中是否包含 query 输入与 key。

一次求值沿同一条主线进行：第 2 节由当前接收与记忆组装 $d_v$；第 3 节收齐 $(d_v)_{v\in C}$，计算评分及所需的总量或阈值；第 4 节得到 $(c_v)_{v\in C}$ 并完成 SelStep 返回。第 5 节先算指定总量的完整例子，再在相同输入上更换分配。

## 2. 构造节点描述

### 2.1 当前接收与记忆信息

本节使用第 1 节的 $r_v^{\mathrm{in}},u_v,p_v(u_v)$ 与 Mem 返回值。内容用于判断本次接收及历史之间的关系，两个写入量用于提供接收积累的统计。定义截断接收量

$$
w_v=\min(1,(r_v^{\mathrm{in}})_+).
$$

取正整数隐藏宽度 $d_r$ 和匹配宽度 $d_{\mathrm{sel}}$。以下计算本节点时省略接收和记忆量的节点下标；记忆量均在所选状态及当前 $\theta,u$ 上求值。

评分与区域证据分别选择如何处理这些信息。下面先给出拼接特征与分组编码，再构造局部评分、区域匹配向量与区域证据。§2.5 给出指定总量、区域阈值的完整描述；使用节点增益的规则按 §2.6 构造描述。

### 2.2 拼接特征与分组编码

这两种构造从当前接收与记忆取得内部特征，随后形成局部评分、区域证据或记忆 key。不同用途分别给定参数。

#### 2.2.1 拼接特征

拼接评分、拼接区域证据和拼接上下文增益使用以下向量：

$$
\begin{aligned}
f_v=\big[&\mathcal N_d(u);\log(1+(r^{\mathrm{in}})_+);M_{\mathrm{short}};M_{\mathrm{long}};
 \log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}});\\
 &p_v(u)\odot M_{\mathrm{short}};p_v(u)\odot M_{\mathrm{long}}\big].
\end{aligned}
$$

$f_v$ 的宽度为 $d+4d_s+3$。两个逐分量乘积提供当前内容与记忆的交互，其余分量保留内容和接收统计。

| 部件 | 对 $f_v$ 的使用 |
|---|---|
| 拼接评分 | 输入评分网络，得到标量 $s_v^{\mathrm{cat}}$ |
| 拼接区域证据 | 投影并归一化，得到向量 $z_v^{\mathrm{reg,cat}}$ |
| 拼接上下文增益 | 输入独立增益网络，得到 $\gamma_v$ |

这些部件使用各自的参数。按所选函数计算所需特征；固定区域控制取零证据，固定增益直接给定，二者均无需 $f_v$。

#### 2.2.2 分组编码

分组匹配评分与分组区域证据先分别处理当前内容、记忆与统计量；内容 key 只使用其中的记忆编码。共同输入为

$$
\begin{aligned}
z^{\mathrm{cur}}&=\mathcal N_d(u),\\
z^{\mathrm{mem}}&=[M_{\mathrm{short}};M_{\mathrm{long}}],\\
z^{\mathrm{stat}}&=[\log(1+(r^{\mathrm{in}})_+);\log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})].
\end{aligned}
$$

令组别 $g\in\{\mathrm{cur},\mathrm{mem},\mathrm{stat}\}$ 的输入宽度为 $d_{\mathrm{cur}}=d$、$d_{\mathrm{mem}}=2d_s$、$d_{\mathrm{stat}}=3$。用途标记 $h\in\{\mathrm{score},\mathrm{reg},\mathrm{key}\}$ 分别表示局部评分、区域证据和内容 key。对各用途实际使用的组别，取
$B_v^{h,g}\in\mathbb R^{d_r\times d_g}$、
$C_v^{h,g}\in\mathbb R^{d_{\mathrm{sel}}\times d_r}$、
$b_v^{h,g}\in\mathbb R^{d_r}$、
$a_v^{h,g}\in\mathbb R^{d_{\mathrm{sel}}}$，定义

$$
E_v^{h,g}(z)=\mathcal N_{d_{\mathrm{sel}}}
\left(C_v^{h,g}\operatorname{SiLU}(B_v^{h,g}z+b_v^{h,g})+a_v^{h,g}\right).
$$

各组输出均为 $d_{\mathrm{sel}}$ 维向量，连续依赖输入且范数不超过 $\sqrt{d_{\mathrm{sel}}}$。评分与区域证据分别使用 score、reg 的三组编码；内容 key 只使用 $E_v^{\mathrm{key,mem}}$。各用途的参数默认独立，同形参数的共享须在模型绑定中明确给出。

### 2.3 局部评分的候选

局部评分将本节点的当前接收与记忆信息变为一个实数 $s_v^{\mathrm{loc}}$。它随后写入描述 $d_v$，供第 3 节的区域评分使用。这里可选拼接评分（cat）或分组匹配评分（match）；先定义两种函数，再给出所选评分及其性质。

#### 2.3.1 候选函数

##### 拼接评分（cat）

取 $W_v^r\in\mathbb R^{d_r\times(d+4d_s+3)}$、$b_v^r,a_v^{\mathrm{cat}}\in\mathbb R^{d_r}$ 和标量 $b_v$，对 §2.2 的拼接特征定义

$$
s_v^{\mathrm{cat}}=b_v+(a_v^{\mathrm{cat}})^\top\operatorname{SiLU}(W_v^r f_v+b_v^r).
\tag{1}
$$

##### 分组匹配评分（match）

使用 §2.2.2 的分组输入与评分编码。取隐藏宽度为 $d_r$ 的门控残差参数，以及非负尺度 $\alpha_v^{\mathrm{match}},\alpha_v^{\mathrm{res}}$，定义

$$
\begin{aligned}
x_v&=E_v^{\mathrm{score,cur}}(z^{\mathrm{cur}}),\quad
 e_v=E_v^{\mathrm{score,mem}}(z^{\mathrm{mem}}),\\
z_v&=E_v^{\mathrm{score,stat}}(z^{\mathrm{stat}}),\quad
 f_v^{\mathrm{match}}=[x_v;e_v;z_v],\\
F_v^{\mathrm{match}}(f)&=(w_v^{\mathrm{match}})^\top
 \big[\operatorname{SiLU}(W_v^{\mathrm{match,gate}}f+b_v^{\mathrm{match,gate}})\\
 &\qquad{}\odot(W_v^{\mathrm{match,up}}f+b_v^{\mathrm{match,up}})\big],\\
s_v^{\mathrm{match}}&=b_v^{\mathrm{match}}+
 \alpha_v^{\mathrm{match}}x_v^\top e_v/\sqrt{d_{\mathrm{sel}}}
 +\alpha_v^{\mathrm{res}}F_v^{\mathrm{match}}(f_v^{\mathrm{match}}).
\end{aligned}
\tag{2}
$$

#### 2.3.2 所选评分与性质

选定一种函数后，本节点的局部评分为

$$
s_v^{\mathrm{loc}}=
\begin{cases}
s_v^{\mathrm{cat}},&\text{选择拼接评分},\\
s_v^{\mathrm{match}},&\text{选择分组匹配评分}.
\end{cases}
$$

两种函数的参数默认按节点独立，允许显式共享同形参数。给定当前特征与记忆描述后，式 (1)、(2) 均连续依赖于所用的数值输入。

拼接评分将内容、统计量及当前内容与记忆的逐分量乘积一起送入非线性变换。分组匹配评分先分别编码内容、记忆和统计量，再将内容与记忆的内积同门控残差相加。两者均提供当前内容与记忆的交互，区别在于如何组织这些交互。所选 $s_v^{\mathrm{loc}}$ 进入 §2.5 或 §2.6 的描述结构。

### 2.4 区域匹配所用的向量

区域 Attention 评分（att）需要节点提供当前内容投影 $x_v^{\mathrm{sel}}$ 和记忆 key $K_v^{\mathrm{sel}}$。区域将汇集前者形成 query，再与各节点的后者匹配；独立评分（ind）直接使用局部评分。

#### 2.4.1 当前内容投影

两种 key 共用相同的 query 输入构造。取 $W_v^{\mathrm{loc}}\in\mathbb R^{d_{\mathrm{sel}}\times d}$、$b_v^{\mathrm{loc}}\in\mathbb R^{d_{\mathrm{sel}}}$，定义

$$
x_v^{\mathrm{sel}}=W_v^{\mathrm{loc}}\mathcal N_d(u_v)+b_v^{\mathrm{loc}}.
$$

#### 2.4.2 记忆 key 的候选

记忆 key 向共同 query 提供本节点参与匹配的信息。记忆与统计 key 使用 Mem 的全部四项；内容 key 编码两个记忆向量，写入统计仍可由已有局部评分使用。两者都返回 $d_{\mathrm{sel}}$ 维向量。

使用 §2.2.2 的记忆向量 $z^{\mathrm{mem}}$。记忆与统计 key 取 $W_v^{\mathrm{mem}}\in\mathbb R^{d_{\mathrm{sel}}\times(2d_s+2)}$、$b_v^{\mathrm{mem}}\in\mathbb R^{d_{\mathrm{sel}}}$；内容 key 取该节的独立编码 $E_v^{\mathrm{key,mem}}$。选定构造后，

$$
K_v^{\mathrm{sel}}=
\begin{cases}
W_v^{\mathrm{mem}}
 [z^{\mathrm{mem}};\log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})]
 +b_v^{\mathrm{mem}},
 &\text{记忆与统计 key},\\
E_v^{\mathrm{key,mem}}(z^{\mathrm{mem}}),
 &\text{内容 key}.
\end{cases}
\tag{3}
$$

#### 2.4.3 描述字段与依赖

局部评分、记忆 key 与区域证据分别选择。采用 att 时，将本节的 $x_v^{\mathrm{sel}},K_v^{\mathrm{sel}}$ 放入 §2.5 或 §2.6 的描述；§3.2 用同一个评分公式处理两种 key。采用 ind 时无需本节的两个向量。

两种 key 均连续依赖其数值输入；内容 key 另满足 $\|K_v^{\mathrm{sel}}\|\le\sqrt{d_{\mathrm{sel}}}$。固定两个记忆向量时，内容 key 对 $W_{v,\mathrm{short}},W_{v,\mathrm{long}}$ 无直接依赖。编码含偏置，零记忆向量不强制得到零 key。

Mem 的读取方式决定记忆向量本身的依赖：KV 的 qry、循环记忆的 state 已使用当前内容查询记忆；Read$^+$ 还可能把当前接收纳入所读状态。这里的 key 使用该次 Mem 返回值，参数共享与计算复用须保留这组输入和状态快照。

### 2.5 指定总量与区域阈值所用的描述

这两个候选用区域信息决定发送强弱。节点提供接收相关上限、评分及控制证据；选择 att 时还提供 §2.4 的匹配向量。

#### 2.5.1 节点发送上限

固定第 1 节的最大倍率，定义每节点发送上限

$$
\mu_v^{\max}=\min(1,\gamma_{\max}w_v).
$$

因此 $w_v\le\mu_v^{\max}\le\gamma_{\max}w_v$。区域在这些上限内分配；记忆写入仍由所选 Upd 决定，例如 KV 的写入量取 $w_v$。

#### 2.5.2 区域证据的候选

区域证据把节点的当前内容、记忆与统计信息交给区域，用于决定发送总量或阈值。上下文控制选择以下一种构造，均返回 $d_{\mathrm{reg}}$ 维向量；局部评分与证据构造分别选择。

##### 拼接区域证据（cat）

使用 §2.2.1 的拼接特征，取投影矩阵与偏置，定义

$$
z_v^{\mathrm{reg,cat}}=\mathcal N_{d_{\mathrm{reg}}}
 (W_v^{\mathrm{reg}}f_v+b_v^{\mathrm{reg}}),
\qquad
W_v^{\mathrm{reg}}\in\mathbb R^{d_{\mathrm{reg}}\times(d+4d_s+3)},
\quad b_v^{\mathrm{reg}}\in\mathbb R^{d_{\mathrm{reg}}}.
$$

##### 分组区域证据（grouped）

使用 §2.2.2 的独立证据编码，先得到当前内容、记忆和统计的表示：

$$
x_v^{\mathrm{reg}}=E_v^{\mathrm{reg,cur}}(z^{\mathrm{cur}}),\quad
e_v^{\mathrm{reg}}=E_v^{\mathrm{reg,mem}}(z^{\mathrm{mem}}),\quad
\ell_v^{\mathrm{reg}}=E_v^{\mathrm{reg,stat}}(z^{\mathrm{stat}}).
$$

取四个矩阵 $A_v^{\mathrm{reg,cur}},A_v^{\mathrm{reg,mem}},A_v^{\mathrm{reg,stat}},A_v^{\mathrm{reg,int}}\in\mathbb R^{d_{\mathrm{reg}}\times d_{\mathrm{sel}}}$ 与 $b_v^{\mathrm{reg,grouped}}\in\mathbb R^{d_{\mathrm{reg}}}$，定义

$$
\begin{aligned}
z_v^{\mathrm{reg,grouped}}=\mathcal N_{d_{\mathrm{reg}}}\big(&
A_v^{\mathrm{reg,cur}}x_v^{\mathrm{reg}}
+A_v^{\mathrm{reg,mem}}e_v^{\mathrm{reg}}
+A_v^{\mathrm{reg,stat}}\ell_v^{\mathrm{reg}}\\
&+A_v^{\mathrm{reg,int}}(x_v^{\mathrm{reg}}\odot e_v^{\mathrm{reg}})
+b_v^{\mathrm{reg,grouped}}\big).
\end{aligned}
$$

#### 2.5.3 所选证据与完整描述

固定控制直接使用给定的比例或阈值，无需节点证据；上下文控制使用所选向量：

$$
z_v^{\mathrm{reg}}=
\begin{cases}
0,&\text{固定控制},\\
z_v^{\mathrm{reg,cat}},&\text{上下文控制，选择拼接区域证据},\\
z_v^{\mathrm{reg,grouped}},&\text{上下文控制，选择分组区域证据}.
\end{cases}
$$

两种证据均保留内容、统计及内容与记忆的交互。拼接构造直接投影已有特征；分组构造先独立编码，再组合各组与匹配乘积。两者连续且满足 $\|z_v^{\mathrm{reg}}\|\le\sqrt{d_{\mathrm{reg}}}$，同一区域的证据宽度相同。§3.3 汇集该向量，§3.4 据此计算区域控制。

按区域评分选择下面的描述空间：

$$
\begin{aligned}
D_v^{\mathrm{reg,ind}}
 &=\{(w,\mu,s,z):0\le w\le1,\ \mu=\min(1,\gamma_{\max}w),
      s\in\mathbb R,\ z\in\mathbb R^{d_{\mathrm{reg}}}\},\\
D_v^{\mathrm{reg,att}}
 &=\{(w,\mu,x,K,s,z):(w,\mu,s,z)\in D_v^{\mathrm{reg,ind}},
      x,K\in\mathbb R^{d_{\mathrm{sel}}}\}.
\end{aligned}
$$

Describe 的返回分别为

$$
d_v=
\begin{cases}
(w_v,\mu_v^{\max},s_v^{\mathrm{loc}},z_v^{\mathrm{reg}}),&\mathrm{ind},\\
(w_v,\mu_v^{\max},x_v^{\mathrm{sel}},K_v^{\mathrm{sel}},
 s_v^{\mathrm{loc}},z_v^{\mathrm{reg}}),&\mathrm{att}.
\end{cases}
$$

这已给出指定总量、区域阈值所需的完整节点描述。§3 从同一描述族分别计算区域评分与控制；这两个候选使用固定最大倍率，不计算逐节点增益。

### 2.6 使用节点增益的描述

节点增益与固定阈值分配及第 4 节使用 $\mu_v$ 的其他规则，允许节点用固定或上下文增益调节接收相关发送量。下面定义增益，再组装这些规则所需的描述。

#### 2.6.1 增益与接收相关发送量

取

$$
1\le\gamma_v\le\gamma_{\max},\qquad
\mu_v=\min(1,\gamma_v(r_v^{\mathrm{in}})_+).
\tag{4}
$$

$w_v$ 描述本次接收，$\mu_v$ 允许有界放大。节点增益与固定阈值分配、直接 Attention 与硬选择将 $\mu_v$ 用作节点发送上限；其他规则按自己的定义使用它作为权重或总量依据。始终有 $w_v\le\mu_v\le\gamma_{\max}w_v$，两者具有相同的正分量位置。

以下两种增益可分别与 cat 或 match 评分组合。

##### 固定增益

直接给定 $\gamma_v\in[1,\gamma_{\max}]$，或以有限标量参数 $\zeta_v$ 定义
$\gamma_v=1+(\gamma_{\max}-1)\sigma(\zeta_v)$。它在一次调用中不依赖当前内容或记忆。

##### 拼接上下文增益

使用 §2.2 的拼接特征 $f_v$。取 $W_v^\gamma\in\mathbb R^{d_r\times(d+4d_s+3)}$、$a_v^\gamma,b_v^{\gamma,h}\in\mathbb R^{d_r}$ 和标量 $b_v^\gamma$，定义

$$
\gamma_v=1+(\gamma_{\max}-1)\sigma\bigl(b_v^\gamma+
 (a_v^\gamma)^\top\operatorname{SiLU}(W_v^\gamma f_v+b_v^{\gamma,h})\bigr).
\tag{5}
$$

#### 2.6.2 所选增益与完整描述

选定增益后，用式 (4) 得到 $\mu_v$。评分与增益采用不同参数，可分别选择函数；固定增益无需 $f_v$。取 $\gamma_v=\gamma_{\max}$ 时，$\mu_v$ 与 §2.5 的 $\mu_v^{\max}$ 数值相同。

区域评分为 ind 或 att 时，分别取

$$
\begin{aligned}
D_v^{\mathrm{ind}}
 &=\{(w,\mu,s):0\le w\le\mu\le1,\ \mu\le\gamma_{\max}w,\ s\in\mathbb R\},\\
D_v^{\mathrm{att}}
 &=\{(w,\mu,x,K,s):(w,\mu,s)\in D_v^{\mathrm{ind}},\
       x,K\in\mathbb R^{d_{\mathrm{sel}}}\}.
\end{aligned}
$$

相应返回为

$$
d_v=
\begin{cases}
(w_v,\mu_v,s_v^{\mathrm{loc}}),&\mathrm{ind},\\
(w_v,\mu_v,x_v^{\mathrm{sel}},K_v^{\mathrm{sel}},s_v^{\mathrm{loc}}),&\mathrm{att}.
\end{cases}
$$

### 2.7 完成 Describe 的构造

给定 Mem、$p_v$、局部评分、区域评分方式及所需 key、发送候选及其所需证据或增益的构造与参数后，§2.5 或 §2.6 确定了函数 $\operatorname{Describe}_v[\operatorname{Mem}_v,p_v]$。一次求值使用 $(q,\theta,h)$，返回对应元组；架构的 Read 将 $q$ 取为描述模式指定的 $q_v^{\mathrm{read}}$。

局部评分进入 $s_v^{\mathrm{loc}}$ 字段；att 的两个匹配向量由 §2.4 给出。指定总量、区域阈值还传入节点上限与区域证据；使用节点增益的规则传入由所选增益得到的 $\mu_v$。这些构造分别从当前内容与记忆取得所需信息，第 3 节开始使用完整描述族。

## 3. 从描述族得到区域评分与控制

SelStep 收齐 $(d_v)_{v\in C}$ 后，按 §3.1 或 §3.2 得到实数评分 $s_v$。区域控制描述保留 $w_v,\mu_v^{\max},z_v^{\mathrm{reg}}$，并按 §3.3—3.4 计算本次总量或阈值；节点增益描述保留 $w_v,\mu_v$。所有这些量随后进入发送分配。

### 3.1 独立评分

对 ind 描述，定义 $s_v=s_v^{\mathrm{loc}}$。最终评分只使用本节点的信息；区域控制描述与节点增益描述均按同名字段求值，§2.3 的两种局部评分都能接入。

### 3.2 区域 Attention 评分

对 att 描述，当前内容投影共同形成 query，各节点的记忆 key 决定其与 query 的匹配程度。记汇集权重为 $q_v^{\mathrm{wt}}$：区域控制描述取 $q_v^{\mathrm{wt}}=w_v$；节点增益描述可选 $q_v^{\mathrm{wt}}=w_v$ 或 $q_v^{\mathrm{wt}}=\mu_v$。

区域从完整候选集形成一个 query。取 $W_j^{\mathrm{in}},W_j^{\mathrm{out}}\in\mathbb R^{d_{\mathrm{sel}}\times d_{\mathrm{sel}}}$、$b_j^{\mathrm{in}},b_j^{\mathrm{out}}\in\mathbb R^{d_{\mathrm{sel}}}$ 和非负尺度 $\alpha_j^{\mathrm{loc}},\alpha_j^{\mathrm{sel}}$，定义

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

内容 key 配合非零 $\alpha_j^{\mathrm{loc}}$ 时，两个记忆向量参与共同 query 的匹配，当前接收与写入统计仍可经局部评分影响 $s_v$。取 $\alpha_j^{\mathrm{loc}}=0$ 会关闭局部评分项；在固定 $Q_j^{\mathrm{sel}}$ 与两个记忆向量时，显式写入统计对 $s_v$ 无影响。完整模型仍保留记忆读取、query 权重、发送上限与区域控制各自的统计依赖。

对内容 key，由 §2.4 的范数界和 Cauchy–Schwarz 不等式，

$$
\left|\frac{(Q_j^{\mathrm{sel}})^\top K_v^{\mathrm{sel}}}
 {\sqrt{d_{\mathrm{sel}}}}\right|\le\|Q_j^{\mathrm{sel}}\|.
$$

该匹配项的幅度还随 query 及 $\alpha_j^{\mathrm{sel}}$ 变化；区域 query 沿用本节的共同函数。

区域 query 的汇集量由本节直接定义。它与记忆模块的写入量可以数值相同，也可以不同；更换记忆模块不会隐式改变 query。

本节的 Attention 产生区域评分。第 4 节的 Attention 分配将评分转为发送份额；记忆模块中的 Attention 则用于读取历史。它们处于不同计算步骤，可分别选择。

### 3.3 区域控制的共同输入

指定总量与区域阈值都从整个区域的内容与记忆判断本次发送。它们使用 §2.5 的区域控制描述，并取整数 $1\le k\le|\mathcal R_j|$。先计算接收总量、节点上限之和与接收加权摘要：

$$
W^{\mathrm{recv}}=\sum_vw_v,\qquad
M^{\max}=\sum_v\mu_v^{\max},\qquad
\bar z_j^{\mathrm{reg}}
 =\frac{\sum_vw_vz_v^{\mathrm{reg}}}{\max(1,W^{\mathrm{recv}})}.
$$

定义区域头的输入与允许的总量范围：

$$
\begin{aligned}
f_j^{\mathrm{reg}}&=
 [\bar z_j^{\mathrm{reg}};\log(1+W^{\mathrm{recv}});\log(1+M^{\max})],\\
b^{\mathrm{recv}}&=\min(1,W^{\mathrm{recv}}),\quad
 U=\min(k,M^{\max}).
\end{aligned}
$$

由 $w_v\le\mu_v^{\max}$ 得 $0\le b^{\mathrm{recv}}\le U$。零接收节点对三个和均无贡献；趋弱节点的有界证据在摘要中的影响趋零。区域评分与控制头从同一描述族分别计算。

### 3.4 区域输出：指定总量或共同阈值

固定控制直接给定参数；上下文控制使用一个实值函数 $H_j(f)$。取
$W_j^H\in\mathbb R^{d_r\times(d_{\mathrm{reg}}+2)}$、
$a_j^H,b_j^{H,h}\in\mathbb R^{d_r}$ 和标量 $b_j^{H,\mathrm{out}}$，令

$$
H_j(f)=b_j^{H,\mathrm{out}}+
 (a_j^H)^\top\operatorname{SiLU}(W_j^H f+b_j^{H,h}).
$$

$H_j$ 的输入由 §3.3 给出，其参数与评分参数分别给定。以下两个候选各自绑定所需的区域头；区域头不使用选择温度，也不增加持久状态。

#### 3.4.1 指定总量

先得到允许范围内的比例：

$$
\rho_j=
\begin{cases}
\text{给定的 }[0,1]\text{ 中的数},&\text{固定控制},\\
\sigma(H_j(f_j^{\mathrm{reg}})),&\text{上下文控制}.
\end{cases}
$$

再定义本次实际发送总量

$$
B=b^{\mathrm{recv}}+\rho_j(U-b^{\mathrm{recv}}).
$$

因此 $B\in[b^{\mathrm{recv}},U]$，有正接收时 $B>0$，全零接收时 $B=0$。§4.1.3 在这一指定总量下按评分分配。

#### 3.4.2 区域阈值

另一候选输出从全部评分减去的共同阈值：

$$
\eta_j=
\begin{cases}
\text{给定的实数},&\text{固定控制},\\
H_j(f_j^{\mathrm{reg}}),&\text{上下文控制}.
\end{cases}
$$

§4.1.4 使用调整后评分 $s_v-\eta_j$，在允许范围内确定实际发送总量与各节点分配。

## 4. 发送分配与 SelStep 返回

下面的函数从所选描述、评分及区域输出得到控制族 $(c_v)_{v\in C}$。空候选一律返回空族。统一记有正接收的候选集与实际发送总量为

$$
C_{\mathrm{eff}}=\{v\in C:w_v>0\},\qquad S=\sum_{v\in C}c_v.
$$

$C_{\mathrm{eff}}$ 也恰是 $\mu_v$ 或 $\mu_v^{\max}$ 为正的候选集。使用节点增益描述时另记 $M=\sum_{v\in C}\mu_v$；区域控制描述沿用 §3.3 的 $M^{\max}$。这些总和按节点分别计一次。

需要温度的函数取 $\tau_{\mathrm{sel}}>0$，单次选择中简写为 $\tau$。温度调节评分差异对分配的影响；正典的描述模式 $\tau_j$ 指定 Read 使用的状态快照。

### 4.1 约束分配及其配对函数

#### 4.1.1 共同问题与正则

下面三个正温度分配共用一个优化问题：给定节点评分 $t$、节点上限 $\mu$ 和总量范围 $[\underline S,\overline S]$，在允许范围内分配发送。这里 $\mu$ 是优化函数的上限参数；候选可传入 $\mu_v$ 或 $\mu_v^{\max}$。假设 $0\le\mu_v\le1$、$0\le\underline S\le\overline S$ 且 $\underline S\le\sum_v\mu_v$，定义

$$
\mathcal F(\mu;\underline S,\overline S)
 =\{c:0\le c_v\le\mu_v,\quad
       \underline S\le\sum_vc_v\le\overline S\}.
\tag{7}
$$

先定义二元熵 $h_B(p)=-p\log p-(1-p)\log(1-p)$、Shannon 熵项 $h_1(c)=-c\log c$，以及 $\alpha>1$ 时的 $h_\alpha(c)=(c-c^\alpha)/[\alpha(\alpha-1)]$。端点按 $0\log0=0$ 延拓。正则函数 $R$ 取下表中的一种：

| 名称 | 正则 |
|---|---|
| quad | $R=-\tfrac12\sum_vc_v^2$ |
| bern | $R=\sum_{v:\mu_v>0}\mu_v h_B(c_v/\mu_v)$ |
| ent | $R=\sum_vh_\alpha(c_v)$，固定 $\alpha\in[1,2]$ |

零上限的 bern 项取零。给定 $R$ 和正温度 $\tau=\tau_{\mathrm{sel}}$，定义共同分配函数

$$
\operatorname{Alloc}_\tau(t,\mu;\underline S,\overline S)
 =\arg\max_{c\in\mathcal F(\mu;\underline S,\overline S)}
   \{t\cdot c+\tau R(c;\mu)\}.
\tag{8}
$$

可行集非空、紧且凸，目标在可改变的分量上严格凹，故分配唯一。ent 的 $\alpha=1$ 称为约束 Shannon 选择。指定总量对应 $\underline S=\overline S$，仍使用同一个函数。

#### 4.1.2 两种硬函数共用的排序规则

区域阈值与节点增益的硬函数共用下面的规则。给定整数 $1\le k\le|\mathcal R_j|$、调整后评分 $t$ 与节点上限 $\mu$，只对正上限候选按 $t_v$ 从高到低排序，同分使用固定节点序。有正评分时取前 $\min(k,\#\{v:\mu_v>0,t_v>0\})$ 个正评分候选；全非正时取最高分的一个；无正上限候选时取空集。将所得集合记为 $\mathcal A$，定义

$$
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in\mathcal A].
\tag{9}
$$

这里的 $\mu$ 是规则的上限参数；下文分别传入 $\mu^{\max}$ 或节点增益得到的 $\mu$。两种绑定都使 $k$ 限制激活数量，选中节点发送其对应上限。该规则无需温度；与正温度优化的关系在第 7 节证明。

#### 4.1.3 指定总量分配

使用同一份区域控制描述及 §3.4 的 $B$，定义

$$
c^\tau=\operatorname{Alloc}_\tau(s,\mu^{\max};B,B).
$$

这是配置 regional_total 的完整定义。总发送精确为 $B$，评分在该总量下决定分配。若再从所有评分减去共同阈值，目标只增加常数 $-\eta B$，故此候选不使用 $\eta$。

当 $b^{\mathrm{recv}}=U$ 时，区域头没有调节总量的空间；若 $B=M^{\max}$，所有节点都达到上限。前者仍可能有评分决定的分配，后者的可行集为单点。这两个边界在求解和反向中分别处理。

另定义同一总量下的**零温分配**（regional_total_zero）。保留 Describe、评分、节点上限及产生 $B$ 的区域头，按 $s_v$ 从高到低排列正接收候选 $v_1,\ldots,v_m$，同分按固定节点序，逐个填入允许的发送量：

$$
c_{v_i}^0=\min\left(\mu_{v_i}^{\max},
       \left[B-\sum_{h<i}\mu_{v_h}^{\max}\right]_+\right).
$$

其余节点取零；空候选返回空族。零温函数仍精确发送总量 $B$，至多一个节点严格处于零与自身上限之间。它与正温度函数均取容量 $K_j=|\mathcal R_j|$；一般节点上限较小时，激活数可超过 $k$。§7.2 给出两种函数的收敛关系及评分条件。

#### 4.1.4 区域阈值分配

使用区域控制描述及 §3.4 的 $\eta_j$，定义

$$
t_v=s_v-\eta_j,\qquad
c^\tau=\operatorname{Alloc}_\tau
 (t,\mu^{\max};b^{\mathrm{recv}},k).
$$

这是配置 regional_threshold 的完整定义。评分和阈值共同决定实际总量，范围为 $[b^{\mathrm{recv}},U]$。固定其他输入时，提高共同阈值使总发送单调不增；在同一可微分支上如何改变各分量见 §6.2。下界使用截断接收之和，允许放大上限增加而最低发送量保持。

其**配对硬选择**（regional_threshold_hard）保留同一 Describe、节点上限、评分和阈值函数，向 §4.1.2 的排序规则传入 $t=s-\eta_j$ 与 $\mu^{\max}$。硬函数取 $K_j=k_j$，正温度函数取 $K_j=|\mathcal R_j|$。一般非二元接收时，硬函数未必满足下界 $b^{\mathrm{recv}}$；两者在单位输入与评分条件下的关系见 §7.4。

#### 4.1.5 节点增益与固定阈值分配

使用 §2.6 节点增益描述中的 $\mu_v$，取整数 $1\le k\le|\mathcal R_j|$ 和固定阈值 $\eta\in\mathbb R$，令

$$
b=\min(1,M),\qquad t_v=s_v-\eta,\qquad
F(\mu)=\mathcal F(\mu;b,k),\qquad
c^\tau=\operatorname{Alloc}_\tau(t,\mu;b,k).
$$

这是配置 constrained 的完整定义。$M\le1$ 时，下限等于所有节点上限之和，故唯一可行向量为 $c=\mu$；在 $M<1$ 的开区域，评分 Jacobian 为零，对 $\mu$ 的 Jacobian 为单位阵。$k=1$ 时总和恒为 $\min(1,M)$，共同阈值不影响分配。

其**配对硬选择**（hard_selection）使用相同的节点增益描述与固定阈值，向 §4.1.2 传入 $t=s-\eta$ 与 $\mu$。硬函数取 $K_j=k_j$，正温度函数取 $K_j=|\mathcal R_j|$。§7.5 比较这两份运行，§7.6 给出条件不满足时的例子。

#### 4.1.6 发送总量与激活数量

三个正温度候选都在有正接收时产生正总量。指定总量与区域阈值使用 $b^{\mathrm{recv}}$ 为下界，节点增益与固定阈值分配使用 $\min(1,M)$。若 $W^{\mathrm{recv}}\ge1$ 且 $k=1$，两个区域控制候选的总量均固定为 $1$；弱总接收时，$k=1$ 仍可能有 $b^{\mathrm{recv}}<U$。

对这三个正温度函数，$k$ 约束发送总和。每个 $c_v\le1$ 只给出 $\sum c_v\le|\mathcal A|$，不能由总和上限推出正分量个数的上限。例如 $(0.8,0.6,0.4,0.2)$ 的总和为 $2$，激活四个节点。给定正总量 $S$ 和节点上限 $\mu$，还必有

$$
|\mathcal A|\ge\left\lceil S/\max_v\mu_v\right\rceil.
$$

总量下界与较小的节点上限因而可能共同要求很多节点激活。quad 与 ent 的 $\alpha>1$ 可在正温度产生精确零；Shannon 与 bern 在本章三个候选的正接收节点上全正，证明见附录 A.1。

### 4.2 通过 Attention 份额分配

这一组规则先用 Attention 计算候选之间的归一化份额，再按各自公式将份额变为发送强度。三种候选共用以下内部计算，无需求解约束乘子。

给定非负基权重 $a_v$ 和正温度，归一化分母 $Z$ 与份额 $p_v^{\mathrm{sel}}$ 定义为

$$
Z=\sum_ua_ue^{s_u/\tau_{\mathrm{sel}}},\qquad
p_v^{\mathrm{sel}}=\begin{cases}a_ve^{s_v/\tau_{\mathrm{sel}}}/Z,&Z>0,\\0,&Z=0.\end{cases}
\tag{10}
$$

记 $p=(p_v^{\mathrm{sel}})_{v\in C}$。有正基权重时，$p$ 的和为 $1$，正分量恰在 $a_v>0$ 的候选上。非空候选集上取全部 $a_v=1$，得到通常的 $\operatorname{softmax}(s/\tau_{\mathrm{sel}})$。$p_v^{\mathrm{sel}}$ 是共同的中间量；各候选最终给出的 $c_v$ 才是 SelStep 的控制。

#### 4.2.1 直接 Attention

取 $a_v=\mu_v$ 或 $a_v=w_v$，定义

$$
c_v=\mu_vp_v^{\mathrm{sel}}.
\tag{11}
$$

两种基权重的支持相同，均激活全部有效候选。有效候选非空时，总和是各节点上限的加权平均：$0<S\le\max_v\mu_v\le1$；无有效候选时 $S=0$。每个节点保留 $c_v\le\mu_v$，区域不施加约束优化中的总量下限。只有一个有效候选时发送 $c_v=\mu_v$。

使用 $\mu$ 时，增益既参与份额又参与幅度；使用 $w$ 时，固定评分和接收后，增益只通过本节点外乘的 $\mu_v$ 生效。再将式 (6) 的 query 权重取为 $w$，就同时移除了增益经 query 影响其他评分的直接依赖。后续消息和未来记忆仍连接整个网络。

#### 4.2.2 固定总强度 Attention

取 $a_v=1$ 或 $a_v=\mu_v$，定义

$$
c_v=p_v^{\mathrm{sel}}.
\tag{12}
$$

有正基权重时 $S=1$，每节点只受 $c_v\le1$ 限制。$a=1$ 激活全部真实候选，包括只收到零强度消息的候选；$a=\mu$ 激活全部有效候选，全零接收时返回零。两种函数均为固定正温度的稠密设计。

在非空单候选处，任意正接收可触发单位发送；$a=\mu$ 在接收趋零处因而不连续。$a=1$ 还保留零强度候选的参与。写入和发送各按自己的定义进行。

#### 4.2.3 总量缩放 Attention

取 $a_v=\mu_v$，先定总量 $B=\min(1,M)$，再定义

$$
c_v=Bp_v^{\mathrm{sel}}.
\tag{13}
$$

$M>0$ 时全部有效候选激活，总和为 $B$；$M=0$ 时全部为零。这里 $\mu_v$ 决定份额及区域总量，单节点上限为 $1$。例如 $\mu=(0.1,0.1)$、$p=(0.9,0.1)$ 时，$c=(0.18,0.02)$，第一项超过本节点的 $\mu_1$。

全部接收趋零时 $B\to0$，故总发送趋零；低总量时仍可依评分重新分配。固定正温度的完整连续性见附录 A。这个函数的温度趋零行为需另行分析。

### 4.3 按比例分配

固定整数 $1\le k\le|\mathcal R_j|$，定义

$$
c_v=\begin{cases}\mu_v\min(k,M)/M,&M>0,\\0,&M=0.\end{cases}
\tag{14}
$$

它将总量 $\min(k,M)$ 按各节点 $\mu_v$ 所占的比例分配，属于 $F(\mu)$，在有效候选上全正。评分不参与该函数，因此没有从分配到评分的直接导数。它可以组成完整模型，也可用于研究中的稠密参照。

### 4.4 完成区域返回与性质对照

选定发送函数后，令 $\mathcal A=\{v\in C:c_v>0\}$，SelStep 返回 $(\mathcal A,(c_v)_{v\in C},*)$；空候选返回 $(\varnothing,(),*)$。所选正典容量须覆盖该函数可能产生的激活数量：

| 发送规则 | 每节点上限 | 有正发送时的总和 | 激活范围 | 正典容量 $K_j$ |
|---|---|---|---|---|
| 指定总量分配 | $\mu_v^{\max}$ | $B$ | quad／ent 的 $\alpha>1$ 可稀疏；Shannon／bern 全有效 | $\lvert\mathcal R_j\rvert$ |
| 指定总量的零温分配 | $\mu_v^{\max}$ | $B$ | 按评分填满，可有一个未饱和节点 | $\lvert\mathcal R_j\rvert$ |
| 区域阈值分配 | $\mu_v^{\max}$ | $[b^{\mathrm{recv}},U]$ | quad／ent 的 $\alpha>1$ 可稀疏；Shannon／bern 全有效 | $\lvert\mathcal R_j\rvert$ |
| 节点增益与固定阈值，quad／ent，$\alpha>1$ | $\mu_v$ | $[\min(1,M),\min(k,M)]$ | 可以精确稀疏 | $\lvert \mathcal R_j\rvert$ |
| 节点增益与固定阈值，Shannon／bern | $\mu_v$ | 同上 | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 直接 Attention，两种基权重 | $\mu_v$ | $(0,\max\mu]$ | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 固定总强度 Attention | $1$ | $1$ | 全部真实或全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 总量缩放 Attention | $1$ | $\min(1,M)$ | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 按比例分配 | $\mu_v$ | $\min(k,M)$ | 全部有效候选 | $\lvert \mathcal R_j\rvert$ |
| 区域阈值的配对硬选择 | $\mu_v^{\max}$ | $\sum_{v\in\mathcal A}\mu_v^{\max}$ | $1$ 至 $k$ 个有效候选 | $k$ |
| 节点增益与固定阈值的硬选择 | $\mu_v$ | $\sum_{v\in \mathcal A}\mu_v$ | $1$ 至 $k$ 个有效候选 | $k$ |

正典 $K_j$ 只声明允许的激活数量，$\mathcal A$ 仍由具体函数返回。训练或推理使用哪一种函数由配置给出。固定正温度的任一种函数均可持续使用。

区域控制候选须同时绑定 §2.5 的描述空间与本节的 SelStep；其正控制仍调用共同 Full，全部候选仍按 Next 保留更新。区域头与求解器只产生本次内部量，精确继续无需增加持久状态。

## 5. 例子与恢复关系

### 5.1 指定总量的完整计算

沿用[架构 §4.5](architecture-learning-note.md#45-一组贯穿例子)的三个候选 $a,b,c$，聚合分别为 $(1,1),(1,-1),(0,0)$。选择 cat 局部评分、ind 区域评分和指定总量分配。取 $\gamma_{\max}=2$、$d_{\mathrm{reg}}=1$；区域控制为 fixed，比例 $\rho_j=0.4$，故证据为零。将评分网络输出权重置零，偏置取 $2,1,100$。任意相容记忆在本例中都得到

$$
(w_v)_v=(\mu_v^{\max})_v=(1,1,0),\qquad
(s_v^{\mathrm{loc}})_v=(s_v)_v=(2,1,100).
$$

Describe 返回 $d_a=(1,1,2,0)$、$d_b=(1,1,1,0)$、$d_c=(0,0,100,0)$。区域取 $k=2$、正典容量 $K_j=3$，从描述族计算

$$
W^{\mathrm{recv}}=M^{\max}=2,\qquad
b^{\mathrm{recv}}=1,\quad U=2,\qquad
B=1+0.4(2-1)=1.4.
$$

SelStep 使用 quad、$\tau_{\mathrm{sel}}=2$。第三项的上限为零；前两项满足 $c_a+c_b=1.4$。内部最优性给出 $2-2c_a=1-2c_b$，于是

$$
(c_a,c_b,c_c)=(0.95,0.45,0),\qquad
\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_v)
=(\{a,b\},(0.95,0.45,0),*).
$$

两个正控制进入共同 Full；三个候选均按 Next 保留接收更新。高分的零接收节点 $c$ 对发送无影响。[KV §5.1](kv-memory-learning-note.md#51-从接收到输出)用这组控制继续计算记忆、完整内容与端口读出。

固定评分和温度，只改区域比例，结果为：

| $\rho_j$ | 指定总量 $B$ | 控制 $(c_a,c_b,c_c)$ |
|---|---|---|
| $0$ | $1$ | $(0.75,0.25,0)$ |
| $0.4$ | $1.4$ | $(0.95,0.45,0)$ |
| $0.8$ | $1.8$ | $(1,0.8,0)$ |

上下文控制也可给出中间一行：将区域头输出权重置零，输出偏置取 $\log(2/3)$，即可令 $\sigma(H_j)=0.4$；选择拼接区域证据，其投影可取零。此时改变头的输出偏置会改变 $B$。保持 $\rho_j=0.4$，将温度降到 $0.5$，控制为 $(1,0.4,0)$，总量仍是 $1.4$。

若把 $k$ 改为 $1$，则 $b^{\mathrm{recv}}=U=1$，总量头失去调节空间，评分仍可改变节点之间的分配。

### 5.2 更换阈值与节点增益

保持 §5.1 的接收、评分、上限和 quad，先取温度 $0.5$。指定总量 $B=1.4$ 得到 $(1,0.4,0)$；区域阈值取固定控制 $\eta_j=0.8$，也得到同一向量。前者强制总和为 $1.4$，后者在总量范围 $[1,2]$ 内达到该值。第 6 节进一步比较它们的乘子与导数。

再采用节点增益描述，取固定 $\gamma_v=1$，于是 $\mu=(1,1,0)$。Describe 返回
$d_a=(1,1,2)$、$d_b=(1,1,1)$、$d_c=(0,0,100)$。
节点增益与固定阈值分配取 $k=2,\eta=0.8$、温度 $0.5$，仍给出 $(1,0.4,0)$。这里接收已使节点上限饱和，不同分配在这些参数上数值相同。

节点增益与固定阈值分配再取 $k=1,\eta=0,\tau_{\mathrm{sel}}=2$，总和被约束为 $1$。由 $c_a+c_b=1$ 得

$$
c_a=\tfrac12+\frac{2-1}{2\cdot2}=\tfrac34,\qquad
c_b=\tfrac14,\qquad
\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_v)
=(\{a,b\},(3/4,1/4,0),*).
$$

这组控制对应[架构 §4.5](architecture-learning-note.md#45-一组贯穿例子)的节点增益与固定阈值一行；[KV §5.1](kv-memory-learning-note.md#51-从接收到输出)在共同记忆与内容上分别完成本分支和 §5.1 的指定总量分支。保持这个 $k=1$ 的配置，只将温度降到 $0.5$，控制变为 $(1,0,0)$。它与指定 $B=1.4$ 的温度变化使用不同的总量条件。

### 5.3 弱接收的发送范围

取 $w=(0.2,0.2)$、$\gamma_{\max}=2$、$k=1$，得到
$\mu^{\max}=(0.4,0.4)$、$b^{\mathrm{recv}}=0.4$、$U=0.8$。
使用 cat、ind，将评分头的输出权重置零、偏置取 $(1,0)$，故 $s=(1,0)$。
区域控制取 fixed，Describe 返回 $(0.2,0.4,1,0)$ 与 $(0.2,0.4,0,0)$，最后一项为所选宽度的零向量。任意相容记忆均可接入。用 quad、$\tau=1$：

| 指定比例 $\rho_j$ | 实际总量 $B$ | 控制 $c$ |
|---|---|---|
| $0$ | $0.4$ | $(0.4,0)$ |
| $1/2$ | $0.6$ | $(0.4,0.2)$ |
| $1$ | $0.8$ | $(0.4,0.4)$ |

在 $0.4<B<0.8$ 内，第一节点已达上限，增加总量全部进入第二节点。即使两个节点上限之和小于 $1$，也不能直接返回全部上限。作为比较，节点增益与固定阈值分配在相同节点上限下的下界为 $0.8$，因而强制 $(0.4,0.4)$。

### 5.4 同一组输入下的稠密规则

取 $\mu=w=(0.2,1)$、相等评分；表中的约束 Shannon 使用节点增益与固定阈值分配，$k=1$：

| 规则 | $c$ |
|---|---|
| 固定总强度，基权重 $1$ | $(1/2,1/2)$ |
| 固定总强度，基权重 $\mu$ | $(1/6,5/6)$ |
| 直接 Attention | $(1/30,5/6)$ |
| 总量缩放 Attention | $(1/6,5/6)$ |
| 约束 Shannon | $(0.2,0.8)$ |

四个候选均有 $\mu=w=0.1$ 且评分相等时，上述规则每节点分别发送 $0.25,0.25,0.025,0.1,0.1$。最后两种的同分前向相同，改变评分后的响应可以不同。

### 5.5 分配与饱和

本节使用节点增益与固定阈值分配。记 $\operatorname{clip}(x,l,h)=\min(h,\max(l,x))$。取 $\mu=(1,1),k=1$，评分差 $\Delta=s_1-s_2$，quad 的解为

$$
c_1=\operatorname{clip}\left(\tfrac12+\tfrac\Delta{2\tau},0,1\right),\qquad c_2=1-c_1,
$$

$|\Delta|<\tau$ 时两者均激活；$\Delta>\tau$ 时分配保持 $(1,0)$，小幅评分变化不再改变控制。分量固定在零或发送上限的范围称为饱和区。

取四个单位上限、$t=(4,3,2,1),k=2$，quad 在温度 $5,2,0.4$ 时分别给出 $(0.8,0.6,0.4,0.2)$、$(1,0.75,0.25,0)$、$(1,1,0,0)$。正温度可以产生真实零分量；其是否节约下游准备取决于图。

### 5.6 与 softmax、sparsemax、entmax 的关系

有效候选非空、各自的 $\mu_v=1$ 且 $k=1$ 时，节点增益与固定阈值分配的可行集 $F(\mu)$ 为概率单纯形 $\{c:c_v\ge0,\sum_vc_v=1\}$。ent 在此集合上的解称为 $\alpha$-entmax；$\alpha=1$ 给出 softmax，$\alpha=2$ 给出称为 sparsemax 的欧氏投影 $\arg\min_{c\in F(\mu)}\|c-s/\tau\|_2^2$，quad 也给出同一投影。最高分唯一时，零温极限只选该候选，称为 Top-1。

上限全为 $1$ 保证上述等式对任意评分成立。对给定评分，更一般的 Shannon 判定是：取 $k=1$，在非空有效候选集上令 $p=\operatorname{softmax}(s/\tau_{\mathrm{sel}})$；若每个 $p_v\le\mu_v$，则 $c=p$。这些不等式蕴含 $M\ge1$，故总和为 $1$，而 $p$ 已在整个概率单纯形上最大化 Shannon 目标。例如 $\mu=(0.6,0.6)$、相等评分给出 $c=(0.5,0.5)$。

固定上限，所有 $p_v<\mu_v$ 时，这一等式在评分的邻域内保持，评分导数就是通常的 softmax 导数。等于某个上限时，前向等值仍成立，边界反向须按 §6.2 的分支分别判断。

一般总和区间上有

$$
R^{\mathrm{ent}}_{\alpha=2}=R^{\mathrm{quad}}+\tfrac12\sum_vc_v.
\tag{15}
$$

要取得相同分配，取 $\eta_{\mathrm{ent},2}=\eta_{\mathrm{quad}}+\tau/2$；总和固定时无需这项移位。固定评分和上限令温度趋于无穷时，解趋于可行集上正则的唯一最大点，见附录 A。

## 6. 求解与导数

### 6.1 一个标量乘子

下面求解共同函数 Alloc；$\mu,t,\underline S,\overline S$ 按所选候选传入，记 $M=\sum_v\mu_v$。先处理单点情形：$M=0$ 或 $\overline S=0$ 时返回零，$\underline S=M$ 时返回 $\mu$。其余情形对实数 $x$、上限 $\mu\in[0,1]$ 和正温度 $\tau$ 定义响应函数：

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
\lambda_U,\lambda_L&\ge0,\quad
 \lambda_U(S-\overline S)=0,\quad\lambda_L(\underline S-S)=0.
\end{aligned}
\tag{16}
$$

先用 $\lambda=0$；总和过大时求 $S(\lambda)=\overline S$ 的非负根，过小时求 $S(\lambda)=\underline S$ 的非正根。指定总量时两端均为 $B$，求 $S(\lambda)=B$，乘子可取任意符号。响应单调，二分或有区间保护的 Newton 法即可求解。quad 还可排序断点。乘子可能不唯一，发送向量仍唯一。

指定总量候选的响应输入为 $s_v-\lambda$，乘子用于达到指定的 $B$。区域阈值候选的响应输入为 $s_v-\eta_j-\lambda$，其中 $\eta_j$ 是区域头输出，乘子保证总量约束。两个候选均只求一个标量乘子。

本章三个候选的 Shannon 在有效节点上全正；bern 在 $0<S<M$ 时各有效分量都严格处于上下限之间，$S=M$ 时全取上限。quad 与 ent 的 $\alpha>1$ 可在正温度达到零和上限。各端点及证明见附录 A.1。

### 6.2 约束分配的反向

固定温度和正则形状。在保持零、内部、上限状态及总和约束松紧不变的光滑分支上，记
$x_v^{\mathrm{resp}}=t_v-\lambda$，并在此处求响应导数 $a_v^{\mathrm{resp}}=\partial g/\partial x$、$e_v^{\mathrm{resp}}=\partial g/\partial\mu$。

| 分支 | $a_v^{\mathrm{resp}}$ | $e_v^{\mathrm{resp}}$ |
|---|---|---|
| quad，$0<c_v<\mu_v$ | $1/\tau$ | $0$ |
| ent，$0<c_v<\mu_v$ | $c_v^{2-\alpha}/\tau$ | $0$ |
| bern，$p_v^{\mathrm{occ}}=c_v/\mu_v$ | $\mu_vp_v^{\mathrm{occ}}(1-p_v^{\mathrm{occ}})/\tau$ | $p_v^{\mathrm{occ}}$ |
| quad／ent，上限饱和 | $0$ | $1$ |
| quad／ent，零饱和 | $0$ | $0$ |

若总和在本分支由一个等式确定，将其值记为 $T$：它可以是起作用的下界、上界，或指定总量 $B$。当 $A_0=\sum_va_v^{\mathrm{resp}}>0$ 时，微分给出

$$
\begin{aligned}
d\lambda&=\frac{\sum_va_v^{\mathrm{resp}}dt_v+\sum_ve_v^{\mathrm{resp}}d\mu_v-dT}{A_0},\\
dc_v&=a_v^{\mathrm{resp}}(dt_v-d\lambda)+e_v^{\mathrm{resp}}d\mu_v.
\end{aligned}
\tag{17}
$$

对标量目标 $\mathcal L$，记 $g_v^{\mathcal L}=\partial\mathcal L/\partial c_v$、$\bar g=\sum_va_v^{\mathrm{resp}}g_v^{\mathcal L}/A_0$，则

$$
\begin{aligned}
\frac{\partial\mathcal L}{\partial t_v}&=a_v^{\mathrm{resp}}(g_v^{\mathcal L}-\bar g),\\
\frac{\partial\mathcal L}{\partial\mu_v}&=e_v^{\mathrm{resp}}(g_v^{\mathcal L}-\bar g),\\
\frac{\partial\mathcal L}{\partial T}&=\bar g.
\end{aligned}
\tag{18}
$$

式 (18) 将 $t,\mu,T$ 当作独立输入求偏导，再沿其定义使用链式法则。指定总量候选取 $T=B$；区域阈值候选的下界 $T=b^{\mathrm{recv}}$ 随接收变化；节点增益与固定阈值分配在 $M>1$ 时，$T=1$ 或 $k$ 为常数。提高一个未饱和评分会在可响应的候选之间重新分配；其负梯度方向比较该候选与加权平均的任务边际影响。总和上下限都松弛时，$\lambda=0$ 固定，直接用 $dc_v=a_v^{\mathrm{resp}}dt_v+e_v^{\mathrm{resp}}d\mu_v$。

对 quad，固定上限并令 $\mathcal I=\{v:0<c_v<\mu_v\}$，记 $I$ 为 $|\mathcal I|$ 维单位矩阵，$\mathbf1$ 为同维的全一向量。在 $\mathcal I\ne\varnothing$ 且约束状态保持的光滑分支上，未饱和分量对其评分的 Jacobian 为

$$
\frac{\partial c_{\mathcal I}}{\partial t_{\mathcal I}}
=\begin{cases}
\displaystyle\frac1\tau\left(I-\frac{\mathbf1\mathbf1^\top}{|\mathcal I|}\right),
 &\text{总和固定在下限或上限},\\
\displaystyle\frac1\tau I,&\text{总和上下限都松弛}.
\end{cases}
$$

例如节点增益与固定阈值分配取 $\mu=(1,1,1),k=3,\tau=1,t=(0.4,0.5,0.6)$ 时，$c=t$ 且 $1<\sum c_v<3$；全部评分同时小幅增加，全部控制量随之增加。

总和固定且只有一个未饱和候选时，评分导数为零；式 (18) 中各可响应候选的任务边际影响相同时，评分梯度也为零。$A_0=0$ 时不得除零，应沿严格饱和分支求导。分支切换处另给单侧或广义导数。

**区域头的反向。** 固定评分和节点上限，在上述非退化等式分支，指定总量满足

$$
\begin{gathered}
\frac{\partial c_v}{\partial B}=\frac{a_v^{\mathrm{resp}}}{A_0},\qquad
\frac{\partial\mathcal L}{\partial B}=\bar g,\\
dB=(1-\rho_j)\,db^{\mathrm{recv}}+\rho_j\,dU+
       (U-b^{\mathrm{recv}})\,d\rho_j.
\end{gathered}
$$

quad 的未饱和节点集 $\mathcal I$ 上，$\partial c_v/\partial B=1/|\mathcal I|$。总量头在 $U=b^{\mathrm{recv}}$ 时无作用；上下文 sigmoid 饱和或任务边际影响相消也可能使反馈很弱。

区域阈值的 $dt_v=ds_v-d\eta_j$。固定其他量，总和被等式固定时，共同平移由 $\lambda$ 抵消，$\partial c/\partial\eta_j=0$；总和上下界均松弛时，

$$
\frac{\partial c_v}{\partial\eta_j}=-a_v^{\mathrm{resp}},\qquad
\frac{\partial\mathcal L}{\partial\eta_j}
 =-\sum_va_v^{\mathrm{resp}}g_v^{\mathcal L}.
$$

§5.2 的例子仅列 $a,b$ 两项。在 $\tau=0.5$ 时，指定总量的 $dc/dB=(0,1)$，区域阈值的 $dc/d\eta_j=(0,-2)$。分别固定 $B$ 或 $\eta_j$，两者对评分 $s$ 的 Jacobian 为

$$
\left.\frac{\partial c}{\partial s}\right|_B
 =\begin{pmatrix}0&0\\0&0\end{pmatrix},
\qquad
\left.\frac{\partial c}{\partial s}\right|_{\eta_j}
 =\begin{pmatrix}0&0\\0&2\end{pmatrix}.
$$

这些偏导描述固定分支；完整反向还经过 $b^{\mathrm{recv}},U,\mu^{\max}$、区域摘要、所选证据构造、评分和记忆。截断接收、节点上限及 min 的转折分别声明边界导数。所有分量都固定在边界时，指定总量的独立变化可能立即切换分支，此时不能使用除以 $A_0$ 的公式。

### 6.3 Attention 分配的反向

在式 (10) 的 $Z>0$ 分支，把评分和基权重看作独立输入，记 $J_p=\operatorname{diag}(p)-pp^\top$，有

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
\text{总量缩放 Attention：}&dc_v=p_v^{\mathrm{sel}}dB+Bdp_v^{\mathrm{sel}},\quad B=\min(1,M).
\end{array}
\tag{20}
$$

对直接 Attention 的 $a=\mu$，这给出
$\partial c_v/\partial\mu_u=2p_v^{\mathrm{sel}}\mathbf1[v=u]-c_ve^{s_u/\tau}/Z$；$a=w$ 时固定 $w,s$ 则为 $p_v^{\mathrm{sel}}\mathbf1[v=u]$。评分 Jacobian 分别为 $\operatorname{diag}(\mu)J_p/\tau$、$J_p/\tau$、$BJ_p/\tau$。由 $\|J_p\|_2\le1/2$ 得到相应范数界。固定总强度的评分反向为

$$
\frac{\partial\mathcal L}{\partial s_v}
 =\frac{p_v^{\mathrm{sel}}}{\tau}\left(g_v^{\mathcal L}-\sum_up_u^{\mathrm{sel}}g_u^{\mathcal L}\right).
$$

这些局部公式还须沿评分、基权重与增益的真实依赖回传。全零权重处，固定总强度的 $a=\mu$ 不连续；直接 Attention 与总量缩放 Attention 连续但一般不可微。例如直接 Attention 的 $a=\mu$ 分支沿 $\mu=\varepsilon\delta$ 的方向导数为
$\delta_v^2e^{s_v/\tau}/\sum_u\delta_ue^{s_u/\tau}$，一般不关于方向 $\delta$ 线性。

### 6.4 评分与记忆的依赖

固定 keys，沿区域匹配项有

$$
\nabla_{Q_j^{\mathrm{sel}}}\mathcal L=
 \frac{\alpha_j^{\mathrm{sel}}}{\sqrt{d_{\mathrm{sel}}}}
 \sum_v\frac{\partial\mathcal L}{\partial s_v}K_v^{\mathrm{sel}}.
\tag{21}
$$

完整反向还经过 query 汇集、keys、局部评分、记忆读取、写入与消息。正接收但零发送的候选可以通过 query 或未来记忆获得反馈；未执行的 Full 不提供该步替代分支的内容反馈。

所有正温度族都涉及评分相对温度的尺度。低温未饱和区的斜率可含 $1/\tau$，严格饱和区的直接评分导数可以为零。固定温度时，query/key 范数和匹配尺度的变化仍会改变集中程度。这些是导数性质，训练效果的判断见设计备忘。

## 7. 温度极限与硬选择

### 7.1 一次约束分配

固定有限候选槽和正则形状。设节点上限、总量上下界收敛，各次共同可行集均非空，$\tau_n\downarrow0$；评分有界，并在 $\mu_v^*>0$ 的坐标收敛到 $t_v^*$。若线性问题

$$
\arg\max_{c\in\mathcal F(\mu^*;\underline S^*,\overline S^*)}t^*\cdot c
\tag{22}
$$

有唯一解，式 (8) 的解收敛到它。零上限处的评分任取有限值。此命题覆盖三个约束候选，证明见附录 A.1。

### 7.2 指定总量的零温分配

§4.1.3 的零温函数求解线性问题
$\max\{s\cdot c:0\le c_v\le\mu_v^{\max},\ \sum c_v=B\}$。

交换较低评分节点的发送与较高评分节点的剩余容量，可知该函数返回的向量最大化线性目标。所有有效评分互异足以保证唯一性；更一般地只需可交换的分配边界有严格评分间隔。全零或全部上限的单点情形不需要评分条件。同分固定序给出了确定函数，但线性问题多解时，正则极限未必选择该序对应的顶点。

例如 §5.1 的 $B=1.4$、有效节点的单位上限和分离评分，使零温函数返回 $(1,0.4,0)$。这个向量也将成为下述正温度运行的比较目标。

**命题。** 固定有限正时延图、参数、初态与有限时间范围，记忆满足共同架构 §6.1 的条件，外部输入有界。若这份零温运行每次区域分配的线性最优解唯一，则区域温度共同趋零时，消息投影、有效状态和读出趋向该运行。全部区域取 quad 或固定 $\alpha>1$ 的 ent 时，还存在使完整运行精确相同的共同正温度界。

**证明。** $b^{\mathrm{recv}},U,B$ 连续依赖接收与区域摘要，弱候选满足 $c_v\le\gamma_{\max}w_v\to0$。§7.1 因而验证共同架构命题 3 的局部条件，得到整网数值收敛。固定零温输入时，线性目标的唯一顶点最优性与正则的有界斜率给出正温度精确性，证明见附录 A.4；有限次作用使用共同架构的精确运行推论。$\square$

该比较允许非单位输入和小数发送。它比较固定参数的函数族；固定正温度使用、训练退火与显式零温求值分别绑定，不将 $\tau=0$ 代入正温度响应公式。

### 7.3 二元上限与硬选择

#### 7.3.1 评分条件

节点增益与固定阈值、区域阈值的硬化都使用二元上限，即每个节点上限为 $0$ 或 $1$。取总量下界为 $\min(1,\sum_v\mu_v)$、上界为整数 $k\ge1$，以下评分条件使式 (22) 的唯一解恰为 §4.1.2 的排序结果：

- 有效候选至多一个，无评分条件。
- $k=1$ 且至少两个有效候选，最高分唯一。
- $k>1$ 且至少两个有效候选，各有效 $t_v\ne0$；正评分数超过 $k$ 时，第 $k$ 名与下一名严格分离；全负时最高分唯一。

这些条件只要求相关选择边界有间隔。已经选中的两个节点同分可以不影响唯一性。

#### 7.3.2 正温度的精确性

固定二元上限与 §7.3.1 的分离评分，将有效候选的调整后评分从高到低记为 $t_{(1)},t_{(2)},\ldots$。至少有两个有效候选时，quad 达到硬向量的充分条件为：

| 情形 | 温度界 |
|---|---|
| $k=1$，或有效评分全负 | $\tau\le t_{(1)}-t_{(2)}$ |
| $k>1$，正评分数介于 $1$ 与 $k$ | $\tau\le\min_{t_v>0}t_v$ |
| 正评分数超过 $k$ | $\tau\le t_{(k)}-t_{(k+1)}$ |

例如 $t=(4,3,2,1),k=1$ 时，温度界为 $1$；$\tau=2$ 给出 $(0.75,0.25,0,0)$，$\tau=1$ 给出 $(1,0,0,0)$。有效候选至多一个时任意正温度均成立。ent 的固定 $\alpha>1$ 也有这样的充分小正温区间；Shannon 和 bern 在正温度保持全部有效分量为正。附录 A 给出响应阈值及证明。

整网的消息、评分和上限会随温度共同变化。§7.4—7.5 将这些局部结论用于完整运行。

### 7.4 区域阈值与单位强度硬选择

本节比较 §4.1.4 已定义的区域阈值正温度函数与配对硬函数；两份运行使用同一 Describe、评分和阈值函数。

**命题。** 固定有限正时延图、参数、初态与有限切面。各记忆满足共同架构 §6.1 的四项条件，全部外部输入强度为 $1$。若该配对硬运行每次选择满足 §7.3.1 的评分条件，则区域阈值的正温度运行趋向它。quad 与固定 $\alpha>1$ 的 ent 还有充分小正温度下完整记录精确相同的结论。

**证明。** 硬运行每条实际发送均为 $1$，故 $w,\mu^{\max}$ 二元；有效候选非空时 $b^{\mathrm{recv}}=1$。该次可行集正是 §7.3.1 的二元可行集。接收加权摘要使上下文阈值随有效状态和正接收内容连续，弱候选的贡献消失；$c_v\le\gamma_{\max}w_v$ 保证弱发送趋零。因此 §7.1 验证共同架构命题 3 的局部前提。固定硬运行的输入后，§7.3.2 的正温度界仍适用，再用共同架构的精确运行推论。$\square$

这项结论保留同一阈值函数，运行时的阈值可以随输入和历史变化。一般非二元接收上的排序硬函数未必满足 $b^{\mathrm{recv}}$，其分配极限仍须按式 (22) 判断。

### 7.5 节点增益与固定阈值的硬化

固定有限正时延图、有限切面、参数和初态。各记忆模块满足[架构 §6.1](architecture-learning-note.md#61-比较对象与局部条件)的四项条件。两份运行使用相同的输入、评分、增益、$k_j,\eta_j$、记忆与内容函数；全部外部输入强度为 $1$。

一份在各区域使用 §4.1.5 的节点增益与固定阈值分配，正则形状固定，正典容量取 $K_j=|\mathcal R_j|$；另一份使用硬选择，容量取 $K_j=k_j$。

**命题。** 若硬运行在切面以前的每次区域选择满足 §7.3.1 的评分条件，则各区域温度共同趋零时，约束运行的消息投影、有效状态与 ReadOut 收敛到硬运行。各区域可使用不同的趋零序列及固定正则形状。

**证明。** 硬运行从单位外部输入开始，每条实际发送的强度仍为 $1$：接收强度是非负整数，$\gamma_v\ge1$ 使 $\mu_v$ 为 $0$ 或 $1$，硬选择的正控制遂为 $1$。

若更早消息与有效状态已收敛，局部更新和读取条件使本次正极限接收处的增益、描述、评分收敛，上限也趋向硬运行的二元上限。趋零接收处有 $c_v\le\mu_v\le\gamma_{\max}(r_v^{\mathrm{in}})_+\to0$，评分仍有界。§7.1 因而给出本次控制收敛，包括硬运行的空槽。这验证了[架构命题 3](architecture-learning-note.md#63-局部分配极限与整网极限)的前提，得到整网结论。$\square$

软运行中的 $\mu_v$ 可以介于零和一之间；它们随上游一起趋向硬运行的端点。固定某些非二元上限只降低温度时，仍使用 §7.6 的局部反例。

**推论。** 在上述条件下，若各区域正则为 quad 或固定 $\alpha>1$ 的 ent，则存在 $\tau_*>0$，使全部区域温度满足 $0<\tau_{\mathrm{sel},j}\le\tau_*$ 时，两份运行在切面以前的全部正式作用、原始状态、消息、端口记录及继续状态精确相同。

**证明。** §7.3.2 在每次固定硬输入上给出正温度界。实际选择事件有限，取这些界的最小值，应用架构 §6.3 的精确性推论。$\square$

此界依赖所固定的输入、参数与时间范围。Shannon 与 bern 一般只有数值收敛；训练改变参数后，评分条件与温度界需重新判断。

### 7.6 条件与反例

使用节点增益与固定阈值分配，固定 $\mu=(0.9,0.8),t=(-2,-1),k=1$ 时，线性问题的唯一解是 $(0.2,0.8)$，硬选择给 $(0,0.8)$。这里的上限始终是这两个介于零和一之间的数。

$\mu=(1,1),t=(1,1),k=1$ 时，quad 在每个正温度给出 $(1/2,1/2)$。若分别送到两个单节点区域且增益为 $1$，下游也保持半强度。单位外部输入仍需评分条件才能推出整网软硬相等的极限。

阈值边界也有影响：$\mu=(1,1),k=2,t^\tau=(1,\tau/2)$ 在 $0<\tau<1$ 时给 quad 解 $(1,1/2)$，端点硬函数为 $(1,0)$。

## 8. 发送规则如何满足架构条件

### 8.1 零接收与正温度连续性

架构的区域条件针对 Read 与 SelStep 的完整复合。先看评分：两种 query 汇集权重均随接收趋零；零接收候选对 query 无贡献，正极限接收处的评分连续。§2.4 的两种 key 均为连续函数；有界记忆描述、当前内容和有限参数给出有界评分与增益，内容 key 还有该节的统一范数界。因此两种 key 均可用于下述组合条件。

§2.5 的两种区域证据都是连续函数的复合；归一化给出共同界

$$
\|w_vz_v^{\mathrm{reg}}\|\le w_v\sqrt{d_{\mathrm{reg}}}.
$$

因此零接收节点对区域摘要无贡献；接收趋零时，即使该节点的内容或记忆描述没有极限，其证据贡献仍趋零。在正极限接收节点的输入与记忆描述收敛时，区域摘要连续。两个控制头在固定参数、固定有限区域上连续且有界，节点上限、总量边界及指定总量也连续。固定控制直接满足相同条件。然后核对各发送函数，下表各项分别配合其引用处的条件。

| 发送规则 | 零接收条件 | 正温度连续条件 | 零温比较 |
|---|---|---|---|
| 指定总量分配 | 满足 | 满足 | §7.2：自身的唯一线性最优分配 |
| 区域阈值分配 | 满足 | 满足 | §7.4：单位输入的配对硬选择 |
| 节点增益与固定阈值分配 | 满足 | 满足 | §7.5：单位输入的配对硬选择 |
| 直接 Attention，两种基权重 | 满足 | 满足 | 未纳入 |
| 固定总强度 Attention，$a=\mu$ | 满足 | 一般不满足 | 未纳入 |
| 固定总强度 Attention，$a=1$ | 一般不满足 | 一般不满足 | 未纳入 |
| 总量缩放 Attention | 满足 | 满足 | 未纳入 |
| 按比例分配 | 满足 | 满足 | 未纳入 |
| 硬选择 | 满足 | 一般不满足 | 硬端 |

三个约束候选的连续性由附录 A.1 给出：零接收处节点上限趋零，有界评分的影响消失，剩余控制由共同优化问题的连续性确定。三种连续的无求根规则由附录 A.3 给出；硬选择仅在有效候选中排序。由此可分别使用架构的零消息删除和正温度连续性命题。

固定总强度 $a=\mu$ 在单候选 $\mu=\varepsilon>0$ 时始终发送 $1$，到 $\mu=0$ 时发送 $0$。它允许删除精确零候选，但正接收趋零时不连续。向一个候选加入同分零接收候选，$a=\mu$ 的控制由 $(1)$ 变为 $(1,0)$；$a=1$ 则变为 $(1/2,1/2)$。两种函数仍可按架构第 5、7 节组成模型并精确继续。

### 8.2 弱接收的放大

对满足 $c_v\le\mu_v$ 的规则，由增益定义得到

$$
c_v\le\min(1,\gamma_v(r_v^{\mathrm{in}})_+),
\qquad 1\le\gamma_v\le\gamma_{\max}.
$$

在无其他输入、每步只有一条入边的长度 $L$ 路径上，第 $\ell$ 步增益上界记为 $\Gamma_\ell$，则末端强度不超过

$$
r_0^{\mathrm{in}}\prod_{\ell=1}^L\Gamma_\ell.
$$

固定有限路径允许弱信号放大，同时保持 $r_0^{\mathrm{in}}\to0$ 时末端趋零。单候选、每步增益为 $4$ 且发送达到上限时，$0.01$ 可依次变为 $0.04,0.16,0.64,1$。区域竞争可以使实际发送低于上限。

两个区域控制候选使用 $\mu_v^{\max}\le\gamma_{\max}w_v$，同样满足上述有限路径界；实际发送是否达到上限由指定总量或区域阈值与评分共同决定。

## 附录 A：连续性与极限证明

### A.1 约束解的连续性

固定候选槽和正则形状。设 $\mu^{(n)},\underline S_n,\overline S_n$ 收敛，共同可行集均非空，评分一致有界且在正极限上限处收敛。温度趋向正值时，解趋向相应正温度解；温度趋零且式 (22) 唯一时，解趋向该线性最优解。

**证明。** 可行向量均在紧集 $[0,1]^{|C|}$ 中，任何可行收敛列的极限仍可行。反之，对极限可行向量 $d$，先取 $a_v^{(n)}=\min(d_v,\mu_v^{(n)})$。若其和超过 $\overline S_n$，按同一比例缩至该上界；若随后低于 $\underline S_n$，按剩余容量 $\mu_v^{(n)}-a_v^{(n)}$ 的比例补到下界。可行性保证容量足够；两次修改的总量均趋零，且下界不超过上界。因此得到各次可行的 $d^{(n)}\to d$，也覆盖上下界重合。

零极限上限坐标的线性目标绝对值受 $L\sum_{\mu_v^*=0}\mu_v^{(n)}$ 控制，趋于零。三种正则在 $0\le c\le\mu\le1$ 上联合连续有界；bern 在 $\mu\to0$ 时由 $0\le\mu h_B(c/\mu)\le\mu\log2$ 得到延拓。将最优性不等式与上述可行恢复列比较并取极限，每个聚点都是极限目标的最优解。正温度由严格凹性给出唯一性；零温度使用假设的唯一性。因此整列收敛。$\square$

同理，固定 $\mu,t$ 时将目标除以趋于无穷的温度，紧性与正则严格凹性给出 §5.6 的高温结论。

**正支持与端点。** 对本章三个候选，有正接收时总量下界为正。若可行集强制总量为 $M$，向量只能为 $\mu$；否则可选一个可行的 $T\in(0,M)$，向量 $\widetilde c=T\mu/M$ 在每个有效坐标都严格处于上下限之间。若最优向量有有效零分量，朝 $\widetilde c$ 作足够小凸组合，Shannon 或 bern 的零端熵增益为正的 $\varepsilon|\log\varepsilon|$ 量级，支配其他有限斜率项。bern 在上限也有同样的向内增益。因此 Shannon 全有效分量为正，bern 在可行集非单点时均严格处于上下限之间。空接收返回零。$\square$

### A.2 二元上限与有限温度

**证明 §7.3.1 的硬向量唯一性。** 零上限坐标固定。无有效候选或只有一个时可行集为单点；$k=1$ 时最高分唯一使单位总量集中于它。$k>1$ 且全负时，总和取下限 $1$，再由最高分唯一决定分配。有正评分时，负分量可移向未满的正分量，或在正分量全满后直接删除，从而严格提高目标。正评分数不超过 $k$ 时它们全部取 $1$；超过 $k$ 时严格截断间隔唯一确定前 $k$ 个。$\square$

**证明 §7.3.2。** quad 中，选最高分一个时取 $\lambda=t_{(2)}$，选全部正评分时取 $\lambda=0$，选前 $k$ 个正评分时取 $\lambda=t_{(k+1)}$。表中温度界使式 (16) 逐坐标为所需的零或一，并满足乘子符号和互补条件。总和上下限同时取等号时，$\lambda$ 可为任意符号。

ent 的 $\alpha>1$ 在单位上限处，响应为 $1$ 和 $0$ 的条件分别是

$$
t_v-\lambda\ge\tau/\alpha,\qquad
t_v-\lambda\le-\tau/[\alpha(\alpha-1)].
$$

在截断边界取 $\lambda=t_{(k+1)}+\tau/[\alpha(\alpha-1)]$，最高分一项的情形用第二名；间隔足够大时可同时满足两界。全负时还需该乘子为负。选全部正评分时取 $\lambda=0$，分别利用正负评分距零的严格间隔。充分小正温度满足这些有限个条件。严格凹性确定同一解。$\square$

### A.3 无求根规则的零边界

固定候选槽、$\tau_n\to\tau_*>0$。设 $w^{(n)},\mu^{(n)}$ 收敛且满足 $w\le\mu\le\gamma_{\max}w$，评分有界并在正极限接收处收敛。直接 Attention 的两种基权重、总量缩放 Attention、按比例分配均连续，并允许增删零接收坐标。

**证明。** 有正极限接收时，式 (10) 中相应项收敛到正值，零极限项因有界指数趋零，故分母趋正，份额收敛。全部接收趋零时，直接 Attention 用 $c\le\mu$，总量缩放 Attention 用 $\sum c=\min(1,M)$，均得 $c\to0$。按比例规则在 $M>0$ 直接连续，零处仍有 $c\le\mu$。零接收坐标对各分母、总量和发送均无贡献。$\square$

在有正极限接收的情形，总量缩放 Attention 还有 $c_v\to0$ 对应于 $r_v^{\mathrm{in}}\to0$；这是组合消息连续性所需的单候选结论。固定总强度 $a=\mu$ 允许增删精确零接收坐标：它们对分母与发送均无贡献；但分母趋零时一般不连续。固定总强度 $a=1$ 把真实零接收候选计入分母，增删它们一般改变其他份额。两种比较分别对应共同架构的零接收条件和正温度连续条件，具体反例见 §8.1。

正温度连续性不能直接用于温度同时趋零：例如 $\mu=(1,\varepsilon_\tau)$、$s=(0,1)$、$\varepsilon_\tau=e^{-1/(2\tau)}$，总量缩放 Attention 使第二候选份额趋于 $1$，尽管它的接收权重趋零。对这类分配的整网温度极限需另外给出条件；§7.5 的单位输入软硬结论使用约束分配与式 (9)。

### A.4 指定总量的正温度精确性

固定本次输入和非空可行多面体 $P=\mathcal F(\mu^{\max};B,B)$。若线性目标有唯一最优解 $c^0$，则它是顶点。单点情形直接成立；否则对其他有限个顶点取

$$
\delta=\min_{v\in\operatorname{Vert}(P),\,v\ne c^0}
 \frac{s\cdot(c^0-v)}{\|c^0-v\|_1}>0.
$$

将任意 $c\in P$ 写成顶点的凸组合，得到
$s\cdot(c^0-c)\ge\delta\|c^0-c\|_1$。
quad 与固定 $\alpha>1$ 的 ent 在 $[0,1]^{|C|}$ 上有有界一阶导数，故存在有限 $L_R>0$，使
$|R(c)-R(c^0)|\le L_R\|c-c^0\|_1$。
当 $0<\tau<\delta/L_R$ 时，任意 $c\ne c^0$ 都有严格较小的正则目标，故正温度解精确为 $c^0$。

Shannon 与 bern 在端点的斜率无界，不能使用这个证明。它们在非单点可行集上的正支持也说明，含零分量的线性最优解通常只能在零温极限达到。$\square$

## 附录 S：配置、求解与边界反向

### S.1 配置名称

selection_mode 指定完整发送函数及其求值方式。第 4 节的正温度函数与配对函数分别绑定：

| 函数 | 配置值 | 定义 | 正典容量 $K_j$ |
|---|---|---|---|
| 指定总量分配 | regional_total | §3.4.1 的总量与 §4.1.3 | $\lvert\mathcal R_j\rvert$ |
| 指定总量的零温分配 | regional_total_zero | §4.1.3 的排序填入 | $\lvert\mathcal R_j\rvert$ |
| 区域阈值分配 | regional_threshold | §3.4.2 的阈值与 §4.1.4 | $\lvert\mathcal R_j\rvert$ |
| 区域阈值的配对硬选择 | regional_threshold_hard | §4.1.4，保留区域阈值函数 | $k_j$ |
| 节点增益与固定阈值分配 | constrained | §2.6 的节点增益与 §4.1.5 | $\lvert\mathcal R_j\rvert$ |
| 节点增益与固定阈值的硬选择 | hard_selection | §2.6 的节点增益与式 (9) | $k_j$ |
| 直接 Attention | direct_attention | 式 (11) | $\lvert\mathcal R_j\rvert$ |
| 固定总强度 Attention | unit_attention | 式 (12) | $\lvert\mathcal R_j\rvert$ |
| 总量缩放 Attention | pooled_attention | 式 (13) | $\lvert\mathcal R_j\rvert$ |
| 按比例分配 | proportional | 式 (14) | $\lvert\mathcal R_j\rvert$ |

regional_total 与 regional_total_zero 保留同一 Describe、评分和总量头；regional_threshold 与 regional_threshold_hard 保留同一 Describe、评分和阈值头。两组都使用 §2.5 的区域控制描述。constrained 与 hard_selection 使用 §2.6 的节点增益描述。下表中“指定总量”“区域阈值”的描述与控制参数同时适用于各自的配对函数。

其余配置对应已定义的参数与函数选择：

| 名称 | 取值与含义 |
|---|---|
| local_score | cat、match，式 (1)、(2) |
| region_score | ind、att；指定总量、区域阈值配套使用 $D^{\mathrm{reg,ind}}$／$D^{\mathrm{reg,att}}$，其余使用节点增益描述 |
| region_key | att 使用 content_stats／content，分别对应 §2.4.2 的记忆与统计 key、内容 key；默认 content_stats |
| send_gain | fixed、context，式 (4)、(5)，用于节点增益描述；区域控制描述不使用 |
| gamma_max | 有限最大倍率；指定总量与区域阈值直接使用 $\mu_v^{\max}=\min(1,\gamma_{\max}w_v)$ |
| query_weight | 节点增益描述的 att mu／received 分别使用 $\mu_v,w_v$，默认 mu；区域控制 att 固定 received |
| allocation_base | direct_attention 使用 mu 或 received，默认 mu；unit_attention 使用 uniform 或 mu，默认 uniform；pooled_attention 固定 mu |
| regularizer、ent_alpha | regional_total、regional_threshold、constrained 的 quad／bern／ent；ent 另指定固定 $\alpha\in[1,2]$ |
| allocation_temperature | 上述三个正温度函数及 Attention 份额候选的正温度，与正典描述模式 $\tau_j$ 分别命名 |
| k | 三个约束候选、regional_total_zero、proportional 的总发送强度上限；regional_threshold_hard、hard_selection 的激活数量上限 |
| eta | constrained、hard_selection 的固定阈值；区域阈值在 fixed 控制时使用 |
| region_control_mode | 指定总量、区域阈值的 fixed／context，§3.4 |
| region_evidence | context 控制下的 cat／grouped，§2.5.2，默认 cat；与 local_score 独立选择 |
| region_control_width | $d_{\mathrm{reg}}$，指定总量、区域阈值的描述证据宽度 |
| total_fraction | 指定总量在 fixed 控制时的 $\rho_j\in[0,1]$；context 由区域头给出比例 |
| alpha_loc、alpha_sel | att 的局部评分与区域匹配尺度；content key 配非零 alpha_loc 时保留已有局部评分通路 |

三个正温度约束候选都允许持续稠密和可精确稀疏的正则。region_control_mode=context 时，region_evidence=cat 给定拼接证据投影；grouped 给定 §2.2.2 的三组证据编码及 §2.5.2 的组合矩阵与偏置，编码使用 $d_r,d_{\mathrm{sel}}$，输出宽度为 $d_{\mathrm{reg}}$。两种构造都另给同型区域头的全部参数。local_score=match 与 region_evidence=grouped 的编码参数默认独立，共享关系须显式绑定。

fixed 返回零证据，只使用指定的 eta 或 total_fraction，region_evidence 不参与求值。指定总量、区域阈值及各自配对函数均不使用 send_gain 或 allocation_base；指定总量不叠加 eta。其他发送函数不使用 region_evidence。direct_attention、unit_attention、pooled_attention 均不使用 k、eta 或 regularizer。

region_key 仅用于 att。content_stats 给定 $W_v^{\mathrm{mem}},b_v^{\mathrm{mem}}$；content 给定 $E_v^{\mathrm{key,mem}}$ 的两个矩阵与两个偏置，输入宽度为 $2d_s$，中间宽度为 $d_r$，输出宽度为 $d_{\mathrm{sel}}$。两者均使用相同的当前内容投影与区域 query，描述元组形状保持。key 编码与局部评分、区域证据的参数默认独立；同形共享须显式声明。ind 不读取 region_key。

regional_total_zero、regional_threshold_hard、hard_selection 直接计算各自的排序规则，不使用 allocation_temperature、regularizer 或 ent_alpha。配置检查须识别不适用的字段；显式选择配对函数时移除这些求解参数，正温度函数的温度仍要求严格为正。

regional_total_zero 精确保持 $B$，可有小数发送，激活数一般可超过 $k_j$。两种 hard 配置对所有输入均限制至多 $k_j$ 个激活；它们与正温度函数的收敛关系分别使用 §7.4、§7.5 的单位输入及评分条件。配置切换选择了另一份运行函数，各自从初态产生状态；保留旧缓存后切换的结果另行比较。

### S.2 标量求解与隐式反向

按 §6.1 排除全零与全上限情形后，需要求根的目标总和记为 $T$，有 $0<T<M$；它可以来自区间边界或指定总量 $B$。令 $q=T/M\in(0,1)$，对有效候选定义逆响应点 $x_v^{\mathrm{bracket}}$，使 $g(x_v^{\mathrm{bracket}},\mu_v;\tau)=q\mu_v$：

| 正则 | $x_v^{\mathrm{bracket}}$ |
|---|---|
| quad | $\tau q\mu_v$ |
| bern | $\tau\log(q/(1-q))$ |
| Shannon | $\tau[1+\log(q\mu_v)]$ |
| ent，$\alpha>1$ | $\tau[(q\mu_v)^{\alpha-1}-1/\alpha]/(\alpha-1)$ |

令 $\lambda_{\mathrm{lo}}=\min_v(t_v-x_v^{\mathrm{bracket}})$、$\lambda_{\mathrm{hi}}=\max_v(t_v-x_v^{\mathrm{bracket}})$。单调性给出 $S(\lambda_{\mathrm{lo}})\ge T\ge S(\lambda_{\mathrm{hi}})$。二分维持此区间；Newton 候选步为 $\lambda+(S(\lambda)-T)/\sum_va_v^{\mathrm{resp}}$，其中导数在本轮的 $t_v-\lambda$ 处求值，仅在斜率非零且候选步落入保留区间时使用。上下界不同且某一边起作用时可与对应半轴相交；指定总量不限制乘子符号。

每轮工作量为 $O(|C|)$。初始区间宽度 $D$ 到精度 $\varepsilon_\lambda$ 所需轮数为 $O(\max(1,\log_2(D/\varepsilon_\lambda)))$；同宽零区间直接求值。终止同时检查坐标误差、可行性及最优性残差，低温时相同乘子误差可造成更大坐标误差。quad 可排序 $t_v-\tau\mu_v,t_v$ 后扫描断点，工作量 $O(|C|\log|C|)$；ent 的 $\alpha=2$ 先按式 (15) 移位。

反向使用 §6.2 的最优解映射导数，在求得的最优乘子处取 $x_v^{\mathrm{resp}}=t_v-\lambda$，保存分配、分支及响应统计，工作量 $O(|C|)$。对有限次迭代自动求导定义了另一种反向目标。单点可行集、精确断点、总和约束松紧交界、上下界重合和增益截断均需声明边界约定。若训练温度，在光滑分支上固定 $x,\mu$ 时有 $\partial g/\partial\tau=-a_v^{\mathrm{resp}}x_v^{\mathrm{resp}}/\tau$，再按总和约束修正；两个区域控制头不直接使用温度。可训练 $\alpha$ 的反向须另行定义。

### S.3 稳定求值与支持

式 (10) 在正基权重上计算 $s_v/\tau+\log a_v$，减去最大值后 softmax；全零权重直接返回零。uniform 的候选掩码按输入存在性确定。总量缩放 Attention 与直接 Attention 按自己的公式外乘，正分量支持按精确数学函数确定。

指数响应先在对数域与上限比较；达到上限时直接返回原上限。sigmoid 采用稳定形式；ent 在 $\alpha$ 接近 $1$ 时使用 log1p／expm1 形式。数学零、浮点下溢零与人为裁剪零分别记录。

Attention 规则的 $Z>0$ 边界按式 (19) 核对右导数。全零分支一般没有通常 Jacobian；实现可声明返回零反向，须与方向导数分别记录。跳过 Full 与求出内容再乘零的边界反向也需按所选目标比较。具体核对项见[实现对应](../../reference/weighted-message-implementation-checks.md)。
