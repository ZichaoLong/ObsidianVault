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

# 带权 KV 与稀疏 Full：局部计算语义与退火

本文定义一族接收驱动的神经计算模块：带来源信息的消息聚合、私有带权 KV、当前内容与记忆的描述量、保证非空选择的预算分配，以及带权多头 Attention 和前馈残差。记忆读取可选时间摘要或内容检索，评分可选节点独立评分或区域 Attention；各组合共用写入、预算与 Full。节点接收后先形成记忆和描述量，区域选择决定哪些节点应用 Full；有正发送上界的候选时至少激活一个。

函数采用四篇正典的共同签名与作用结果。学过 [[settlegraph-learning-note|SettleGraph]] 或 [[timed-dag-region-selector-learning-note|TimedDAG]] 后，可沿第 2 节的定义与第 3 节的手算阅读，所用工具为向量、矩阵和基本神经网络函数。第 4--5 节说明弱消息消失及软选择趋向硬选择的条件，正式证明见附录 A；第 6--7 节给出精确联合求值、分段继续与全图成本。附录 S 给出计算表示和实现验证要求。

[[weighted-kv-layered-example|全连接分层实例]] 与 [[weighted-kv-hb-lattice-example|HB-Lattice 实例]] 分别绑定拓扑、时间和边界，并给出任务接入、训练与成本比较。局部函数和空间连接可分别选择，再按第 2.9 节检查组合。

## 1. 适用结构与基本对象

### 1.1 图、局部函数与组合参数

固定有限正时延图及其区域划分、输入输出端口和注入日程，另固定节点全序用于硬选择平票。以下函数适用于 PositiveDelayGraph；满足无环条件或单次结算条件时，分别得到 TimedDAG、SettleGraph 中的同名函数。

节点保存私有 KV，初态为空；区域选择历史取单点集 $Y_j=\{*\}$。同一区域可共享声明的参数，节点各自保有状态与计算快照。消息与状态按正典的逻辑时间 $\theta$ 读取。

一个组合需给出图与日程、来源类别映射、位置坐标，以及所比较的输出槽集合。来源映射把端口或边身份变为聚合使用的类别；输出槽集合指定数值读出比较哪些端口和时刻。第 2.9 节列出全部局部绑定。每次前向中的图、参数、时间规则、窗口与选择配置固定，训练步骤之间可以按声明的算法调整参数。

### 1.2 宽度、归一化与参数

取正整数内容宽度 $d$、Attention 头数 $H_{\mathrm{att}}$ 与每头宽度 $d_h$，满足 $H_{\mathrm{att}}d_h=d$。另取聚合瓶颈宽度 $p_a$、记忆描述宽度 $d_s$、评分隐藏宽度 $d_r$、选择匹配宽度 $d_{\mathrm{sel}}$、KV 适配秩 $r_a$ 与前馈宽度 $d_f$，均为正整数。较小的准备侧宽度提供低成本基线；较丰富的准备计算是否合算，取决于选择质量及全图后续工作量。内容宽度 $d$ 在相连区域间相容，其余宽度可逐区域声明。

固定 $\epsilon>0$，对任意宽度 $p$ 定义无仿射参数的 RMS 归一化和逐坐标激活：

$$
\mathcal N_p(x)=\frac{x}{\sqrt{\epsilon+\|x\|_2^2/p}},
\qquad
\sigma(x)=\frac1{1+e^{-x}},
\qquad
\operatorname{SiLU}(x)=x\,\sigma(x).
\tag{1}
$$

$\epsilon$ 是模型函数的一部分。下文所有矩阵、偏置和残差尺度均为有限实参数；$\odot$ 表示逐坐标乘法，方括号表示向量拼接。共享范围和参数约束在使用处给出。

### 1.3 消息、强度与数值比较

消息载荷空间取 $P=\mathbb R^{1+d}$，写作 $(m,z)$，其中 $m$ 是强度坐标，$z\in\mathbb R^d$ 是内容。令 $m_+=\max(m,0)$，所有接收函数用 $m_+$ 解释强度，因此在整个 $P$ 上有定义；本模型实际发出的强度非负。局部消息的数值投影为

$$
\pi_P(m,z)=(m_+,m_+z),
\qquad \pi_P(\bot)=0\in\mathbb R^{1+d}.
\tag{2}
$$

内容单独保存，其贡献由强度乘一次得到。$(0,z)$ 是存在的零强度消息，仍可使接收方成为候选；$\bot$ 是缺席，不提供候选资格。式 (2) 定义后文连续性所比较的数值对象，不把这两种规范记录视为相同。

### 1.4 逻辑时间与位置坐标

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

$o_v^{\mathrm{pos}}=0,s_v^{\mathrm{pos}}=1$ 直接编码逻辑时间。SettleGraph 的 $\theta_{v,t}=Dt+r_v$ 可取 $o_v^{\mathrm{pos}}=r_v,s_v^{\mathrm{pos}}=D$，于是 $\operatorname{Pos}_v(\theta_{v,t})=t$，恢复通常的输入位置。一般图中，同一纤维可以汇合不同输入位置的消息；这里编码当前聚合的处理时间和历史条目的写入时间，无需给混合内容指定唯一来源位置。

位置函数在整条继续运行中固定，不随接收次数、激活次数或分段边界改变。更一般的固定实值位置函数也可用于下文定义与有限切面证明；具体组合须给出其完整定义。

## 2. 完整局部定义

### 2.1 带来源信息的接收聚合

对区域 $j$，固定有限来源类别集，以及从每个节点输入端口或父边标签到来源类别的映射 $\operatorname{SrcClass}_v$。具体类别由组合配置给出，不依赖当前候选数或消息到达次序。不同来源可以使用同一类别，所有原子仍分别参与聚合。

区域共享 $A_j\in\mathbb R^{p_a\times d}$、$B_j\in\mathbb R^{d\times p_a}$ 和来源嵌入 $e_{j,a}\in\mathbb R^{p_a}$，固定尺度 $\alpha_{\mathrm{agg}}\ge0$。对 $z=(\mathrm{ext},i,k,p)$ 取来源标签 $(\mathrm{ext},i)$，对 $z=(\mathrm{msg},\eta,a,p)$ 取 $(\mathrm{msg},a)$，记为 $\operatorname{source}(z)$。对任意有限 $B\subseteq\mathsf{Atom}_v$，将各原子的来源和值记为 $(a_i,(m_i,z_i))$；这个枚举只用于求和，仍保留所有原子。定义

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

当 $r=0$ 时不求两个商。在三层均取 $X_v=P=\mathbb R^{1+d}$，并令

$$
\operatorname{Agg}_v:\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)\to X_v,
\qquad \operatorname{Agg}_v(\theta,B)=(r,u).
$$

空集同样由式 (3) 得到 $(0,0)$；实际没有输入时保持无节点作用。来源分类可忽略不需要的时间坐标，原子和规范记录仍保留这些坐标。

均值残差保留内容尺度；非线性来源项使相反内容、不同来源的组合不必因均值相同而不可区分。它将输入内容压缩为 $d$ 维摘要，部分消息信息会丢失。$\alpha_{\mathrm{agg}}=0$ 恢复普通加权均值，适合隔离聚合机制的作用；主方案从小的正尺度开始，让来源项获得任务反馈。

零强度项不进入两个加权和。全体强度同时缩放且仍为正时，$u$ 不变，$r$ 改变；下述写入、评分与发送上界分别读取这个强度信息。

共享的 $A_j,B_j$ 让节点在共同特征空间解释来源，减少参数，并在输入相同时允许复用聚合。来源嵌入进入非线性之前，能改变不同来源的响应，但仍共享投影方向。稀疏图中不同节点收到不同邻域的消息，即使参数共享，内容和历史也会分化。

需要更强的节点或来源分工时，可将式 (3) 的非线性残差写为

$$
\begin{aligned}
F_{v,a}(z)&=B_{v,a}\operatorname{SiLU}
 (A_{v,a}\mathcal N_d(z)+e_{v,a}),\\
u&=\bar z+\frac{\alpha_{\mathrm{agg}}}{r}
 \sum_i(m_i)_+F_{v,\operatorname{SrcClass}_v(a_i)}(z_i)
 \quad(r>0),
\qquad u=0\quad(r=0).
\end{aligned}
\tag{3a}
$$

其中 $A_{v,a}\in\mathbb R^{p_a\times d}$、$B_{v,a}\in\mathbb R^{d\times p_a}$、$e_{v,a}\in\mathbb R^{p_a}$。下列绑定均给出完整的 Agg：

| 聚合配置 | 参数绑定 | 主要取舍 |
|---|---|---|
| 区域共享 | $A_{v,a}=A_j,B_{v,a}=B_j,e_{v,a}=e_{j,a}$ | 恢复式 (3)，共享特征空间与参数 |
| 节点独立 | $A_{v,a}=A_v,B_{v,a}=B_v$，嵌入按节点和类别声明 | 节点可在压缩前提取不同信息，增加准备成本 |
| 来源独立 | $A_{v,a}=A_{j,a},B_{v,a}=B_{j,a},e_{v,a}=e_{j,a}$ | 不同来源采用不同投影，参数随类别数增长 |
| 节点与来源适配 | $A_{v,a}=A_j+L^A_{v,a}R^A_{v,a}$，$B_{v,a}=B_j+L^B_{v,a}R^B_{v,a}$ | 以指定秩控制分化与成本 |

最后一行取正整数秩 $r_{\mathrm{agg}}$；$L^A,R^A,L^B,R^B$ 的形状依次为 $p_a\times r_{\mathrm{agg}}$、$r_{\mathrm{agg}}\times d$、$d\times r_{\mathrm{agg}}$、$r_{\mathrm{agg}}\times p_a$，嵌入另行声明。按需共享其中因子也属于这个绑定。

这些差异发生在消息被压缩之前；聚合后的节点适配一般无法恢复已经丢失的信息。独立投影是否改善分工，须与共享参数及相同成本的对照比较。附录 A 的证明适用于上述全部绑定：所需条件是固定、连续且在有界内容上有界的 $F_{v,a}$，以及强度加权。

### 2.2 接收驱动的时间窗口 KV

节点状态空间 $S_v$ 是全部有限序列

$$
q=((\xi_i,k_i,\nu_i,p_i,w_i))_{i=1}^N,
\quad \xi_i\in\mathbb N,\quad
k_i,\nu_i\in\mathbb R^d,\quad
p_i\in\mathbb R^{d_s},\quad w_i\ge0.
\tag{4}
$$

$k_i,\nu_i$ 按头分成 $d_h$ 维子向量；$p_i$ 是供 Read 使用的摘要特征，$w_i$ 是独立的写入权重，$\xi_i$ 是原始逻辑时间。初态为空；可达运行中每节点每逻辑时间至多写一项。

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

共享基座给出区域共同的 KV 投影，节点差异由秩至多为 $r_a$ 的乘积提供。相同输入的基座投影可共同求值，各节点仍保存私有条目。取 $r_a=d$、$W_j^{\mathrm{KV}}=0$、$V_v^{\mathrm{ad}}=I_d$ 与 $U_v=[W_v^K;W_v^V]$，即可表示任意独立的 K、V 投影。式 (5) 定义写入；Attention 读取由第 2.7 节给出。

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

$\oplus$ 表示追加。每个正强度纤维只写一条，KV 内容不预乘 $w$；全部零消息不追加，也不触发清理。是否执行本节点 Full 不参与写入决定。

所有读取同样使用 $\chi_{v,\theta}$。没有候选或只有零强度输入时，保存序列可以含已过期条目，但它们不会再被读出；下一次正接收再清理。有限 $T_v$ 下，由每逻辑时间至多写一项，可达保存序列始终至多含 $T_v$ 项。$T_v=\infty$ 保留全部接收历史，在每个有限切面仍只有有限项。历史覆盖范围取决于该节点实际收到的内容。

窗口按时间而不按“最近收到多少条”定义：一条趋零的输入不会挤掉一条仍在时间窗口内的强记忆。窗口长度固定，内容驱动淘汰或计数淘汰属于其他函数族。

### 2.3 记忆描述与成对的 Read、SelStep

先选择记忆描述，再选择区域评分。两项在区域内固定；不同区域可作不同选择。节点的 Read 给出描述量，SelStep 将该类型的描述量转成评分和控制。

**时间摘要。** 对每节点取 $\beta_{v,\mathrm{long}}=0$、$\beta_{v,\mathrm{short}}>0$，均按逻辑时间计量。固定节点后省略部分下标，对 $a\in\{\mathrm{short},\mathrm{long}\}$ 定义

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

**内容检索。** 另取节点矩阵 $W_v^{\mathrm{RQ}},W_v^{\mathrm{RK}},W_v^{\mathrm{RV}}\in\mathbb R^{d_s\times d}$，定义

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
\tag{7a}
$$

取偶数 $0\le d_v^{\mathrm{rot,read}}\le d_s$、坐标配对及有限频率 $\omega_{v,a}^{\mathrm{rot,read}}$。$\operatorname{Rot}_v^{\mathrm{read}}$ 使用第 2.7 节的旋转矩阵族，宽度换为 $d_s$，采用这些独立参数；零旋转维数给出内容匹配。它沿用同一 $\operatorname{Pos}_v$，与 Full 的位置配置分别选择。两个时间尺度共用本次检索 logit。此时先用当前内容查询私有 KV，再把检索结果交给评分；无须执行 Full 的输出投影或前馈。宽度与检索量允许接近 Full，成本按实际配置计量。

固定 $\mathfrak m_j\in\{\mathrm{sum},\mathrm{qry}\}$ 后，以下 $M_a$ 表示相应记忆描述，均在 $(q,\theta,u)$ 的适用自变量上求值。定义

$$
\begin{aligned}
f_v(q,\theta,r,u)=
\big[&\mathcal N_d(u);\ \log(1+r_+);\
 M_{\mathrm{short}};\ M_{\mathrm{long}};\\
 &\log(1+W_{\mathrm{short}});\
 \log(1+W_{\mathrm{long}});\\
 &p_v(u)\odot M_{\mathrm{short}};\
 p_v(u)\odot M_{\mathrm{long}}\big],\\
s_v^{\mathrm{loc}}(q,\theta,r,u)
 &=b_v+a_v^\top
   \operatorname{SiLU}(W_v^r f_v(q,\theta,r,u)+b_v^r).
\end{aligned}
\tag{8}
$$

$f_v$ 的宽度为 $d+4d_s+3$，$W_v^r\in\mathbb R^{d_r\times(d+4d_s+3)}$，$a_v,b_v^r\in\mathbb R^{d_r}$，$b_v\in\mathbb R$，均按节点独立。当前内容、接收强度、记忆质量和内容—记忆交互均可影响这个标量。

写入强度与发送上界分开。为每节点固定或训练一个有界参数 $1\le\gamma_v\le\gamma_{\max}<\infty$，定义

$$
\mu_v(r)=\min(1,\gamma_v r_+).
\tag{9}
$$

$\gamma_v>1$ 允许弱接收唤醒已有记忆，同时仍保证 $r\to0$ 时发送上界趋零；写入仍用 $w(r)$。训练可取 $\gamma_v=1+(\gamma_{\max}-1)\sigma(\zeta_v)$，其中 $\zeta_v\in\mathbb R$；$\gamma_{\max}=1$ 给出不放大的对照。

**独立评分。** 选择 $\mathfrak s_j=\mathrm{ind}$ 时，取

$$
D_v^{\mathrm{ind}}=[0,1]\times\mathbb R,\qquad
\operatorname{Describe}_v^{\mathrm{ind}}(q,\theta,(r,u))
  =(\mu_v(r),s_v^{\mathrm{loc}}(q,\theta,r,u)).
$$

描述量是两个标量：发送上界和节点评分。丰富的当前内容与记忆已由式 (8) 压缩为评分；SelStep 直接取 $s_v=s_v^{\mathrm{loc}}$。

**区域 Attention 评分。** 选择 $\mathfrak s_j=\mathrm{att}$ 时，定义

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
 &=(\mu_v(r),x_v^{\mathrm{sel}}(u),K_v^{\mathrm{sel}}(q,\theta,u),s_v^{\mathrm{loc}}(q,\theta,r,u)).
\end{aligned}
\tag{9a}
$$

$W_v^{\mathrm{loc}}$、$W_v^{\mathrm{mem}}$ 的形状为 $d_{\mathrm{sel}}\times d$、$d_{\mathrm{sel}}\times(2d_s+2)$，两个偏置属于 $\mathbb R^{d_{\mathrm{sel}}}$。同一区域共享匹配宽度和坐标含义，投影参数按节点声明。

对完整候选集 $C$，SelStep 内部先形成共享 query，再产生各候选评分：

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
\tag{9b}
$$

两个区域矩阵均为 $d_{\mathrm{sel}}\times d_{\mathrm{sel}}$，偏置为 $d_{\mathrm{sel}}$ 维，尺度为固定非负有限参数。取 $\alpha_j^{\mathrm{loc}}=1,\alpha_j^{\mathrm{sel}}=0$ 恢复独立评分的数值；取 $\alpha_j^{\mathrm{loc}}=0$ 隔离区域匹配的作用。空候选仍直接返回空选择。

共享 query 表达该区域当前收到的信息，keys 表达各节点的私有记忆；$\mathrm{qry}$ 配置还让 keys 随本次内容检索而改变。Attention 匹配产生评分，第 2.4--2.5 节再决定预算分配和激活。这里的单 query 匹配对候选数是线性工作量，无须构造候选两两匹配矩阵。

$\mu_v$ 加权使零上界候选不影响其他节点的 query，趋零候选的影响也趋零；按候选数直接取均值一般不具备这个性质。区域划分同时规定选择可共享的信息范围。多个局部区域分别形成 query，无须在整个层上集中选择。

两种评分各自绑定 $D_v=D_v^{\mathfrak s_j}$，并使用对应 Describe，三个全函数统一为

$$
\begin{aligned}
\operatorname{Read}_v^+(\widetilde q,\theta,h)
 &=\operatorname{Describe}_v^{\mathfrak s_j}(\widetilde q,\theta,h),\\
\operatorname{Read}_v^-(q,\theta,h)
 &=\operatorname{Describe}_v^{\mathfrak s_j}(q,\theta,h),\\
\operatorname{Read}_v^0(\theta,h)
 &=\operatorname{Describe}_v^{\mathfrak s_j}((),\theta,h).
\end{aligned}
\tag{10}
$$

实际描述模式取 $\tau_j=+$；这里 $j=\rho(v)$。四个 $(\mathfrak m_j,\mathfrak s_j)$ 组合均已定义；Read 和 SelStep 成对选择，后者只读对应描述量，不自行访问节点状态。时间摘要的独立评分提供基线，内容检索与区域匹配可分别增加，以测量各自的收益。

### 2.4 保证非空的软选择

对区域 $j$，令 $C\subseteq\mathcal R_j$ 是完整候选集，按第 2.3 节的成对绑定从描述量取得 $(\mu_v,s_v)$。固定整数质量预算上限 $1\le k_j\le|\mathcal R_j|$、阈值 $\eta_j\in\mathbb R$ 与平滑参数 $\tau_{\mathrm{soft}}>0$，记调整后评分 $t_v=s_v-\eta_j$。阈值与其他配置在本次前向固定，不读取运行队列或 batch 同伴。

定义有效候选、可用总质量与发送质量下限

$$
C_{\mathrm{eff}}=\{v\in C:\mu_v>0\},\qquad
M_j=\sum_{v\in C}\mu_v,\qquad b_j=\min(1,M_j).
$$

控制空间取 $\mathsf C_v=[0,1]$。门控是以下严格凹问题的唯一解：

$$
\begin{aligned}
c^{\tau_{\mathrm{soft}}}
  &=\mathop{\arg\max}_{c}
  \left\{\sum_{v\in C}t_vc_v
    -\frac{\tau_{\mathrm{soft}}}{2}\sum_{v\in C}c_v^2\right\},\\
&\hspace{1em}0\le c_v\le\mu_v,\qquad
b_j\le\sum_{v\in C}c_v\le k_j.
\end{aligned}
\tag{11}
$$

由于 $b_j\le M_j$ 且 $b_j\le1\le k_j$，可行集非空、紧且凸，故解存在且唯一。$C_{\mathrm{eff}}\ne\varnothing$ 时总发送质量为正，至少一个节点激活；$M_j\to0$ 时下限同步趋零，保持弱输入消失的连续性。正典允许空激活的通用接口可直接容纳这一局部约束。

令 $\operatorname{clip}(x,l,h)=\min(h,\max(l,x))$，并记 $S=\sum_vc_v$。解等价于

$$
\begin{aligned}
c_v&=\operatorname{clip}
   \left(\frac{t_v-\lambda}{\tau_{\mathrm{soft}}},0,\mu_v\right),\\
\lambda&=\lambda_U-\lambda_L,\qquad \lambda_U,\lambda_L\ge0,\\
b_j&\le S\le k_j,\qquad
\lambda_U(S-k_j)=0,\qquad \lambda_L(b_j-S)=0.
\end{aligned}
\tag{12}
$$

先尝试 $\lambda=0$；若 $S>k_j$，取非负乘子使 $S=k_j$；若 $S<b_j$，取非正乘子使 $S=b_j$。式 (12) 为分段线性方程，可按断点排序精确求解，也可数值求根；具体求解与导数见附录 S.3。乘子可以不唯一，门控唯一。即使全部有效候选评分低于阈值，也会分配下限所要求的质量。

完成平方表明，式 (11) 是 $t/\tau_{\mathrm{soft}}$ 到上述凸集的欧氏投影。$k_j=1$ 且所有有效上界为 $1$ 时，它就是通常的单纯形 [sparsemax](https://arxiv.org/abs/1602.02068)。更一般地，$M_j\le1$ 时约束强制 $c=\mu$；$k_j=1,M_j\ge1$ 时总质量恒为 $1$，共同阈值 $\eta_j$ 只给目标增加常数，不影响分配。$k_j>1$ 时阈值可调节超过下限的用量。将质量固定为 $\min(k_j,M_j)$ 可作为用满可用预算的对照。

**质量预算 $k_j$ 不等于正式执行容量 $K_j$。** 软规格取 $K_j=|\mathcal R_j|$，返回

$$
A=\{v\in C:c_v>0\},\qquad (c_v)_{v\in C},\qquad *.
\tag{13}
$$

所有候选都有控制量，只有正门控节点激活。空候选返回空集合、空控制族和原历史；非空但全为零上界时，同样不激活任何节点。零上界节点既不占预算，也不会因高分被激活。支持集规格与硬规格在单位外部输入的普通运行中只发正强度消息，因此非空候选集就是非空有效候选集。

另可声明一个全候选参考规格 $A=C$，保持同一门控，令零门控节点走第 2.7 节的廉价零分支。它保留额外的 Full 与零消息记录。这个参考规格不同于为所有节点提供正门控的稠密训练；第 5 节分别讨论二者。

### 2.5 硬选择与质量预算的边界

$\tau_{\mathrm{soft}}=0$ 时另行定义硬函数，不代入式 (12)。硬规格取 $K_j=k_j$。令

$$
C_+=\{v\in C_{\mathrm{eff}}:t_v>0\}.
$$

若 $C_+\ne\varnothing$，按 $t_v$ 降序选择前 $\min(k_j,|C_+|)$ 个。若 $C_+=\varnothing$ 且 $C_{\mathrm{eff}}\ne\varnothing$，选择有效候选中评分最高的一个；$C_{\mathrm{eff}}=\varnothing$ 时取 $A=\varnothing$。两种排序的平票均按固定节点序。返回

$$
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in A]\quad(v\in C),
\qquad \text{下一历史为 }*.
\tag{14}
$$

这是对所有描述量都有定义的全函数。有效候选非空时，$1\le|A|\le\min(k_j,|C_{\mathrm{eff}}|)$；零上界候选始终不参与选择。阈值决定是否在最优的一个节点以外继续选取。

式 (11) 的零温极限何时等于式 (14)，需要额外条件。二元上界与适当的评分间隔给出第 5.2 节的充分条件。小数上界时，硬函数只保证非空及激活数上限，未必满足软问题的质量下限：三个上界均为 $0.4$、$k_j=1$、调整后评分均为 $1$，软门控均为 $1/3$；硬函数只能选一个并发送 $0.4$。此时软极限与该硬函数不同。

### 2.6 BO、计算快照与下一状态

取 BO，即 $\kappa_j=1$，并采用默认 Next。对每个候选，

$$
q^{\mathrm{cmp}}=\widetilde q,\qquad
\operatorname{Next}_v(q,q^{\mathrm{cmp}},\theta,h,
             \mathbf1[v\in A],c_v)=q^{\mathrm{cmp}}.
\tag{15}
$$

因此候选状态、Full 的计算快照、下一持久状态相同。未选中者也保留接收更新；没有输入者保持原状态。节点无需等待本次选择才决定如何写入，本次 Full 的结果也不回写自己的 KV。

### 2.7 Full：带权多头 Attention 与前馈残差

以下先定义正门控时的昂贵内容函数。对每个头 $1\le h\le H_{\mathrm{att}}$，取 $W^Q_{v,h}\in\mathbb R^{d_h\times d}$。固定偶数 $0\le d^{\mathrm{rot}}_{v,h}\le d_h$、坐标配对与有限频率 $\omega^{\mathrm{rot}}_{v,h,a}$，定义

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

另可取非负距离偏置斜率 $b^{\mathrm{pos}}_{v,h}$，通常置零。定义

$$
\begin{aligned}
Q_{v,h}(u)&=W^Q_{v,h}\mathcal N_d(u),\\
\widehat w_i&=\chi_{v,\theta}(\xi_i)w_i,\qquad
W=\sum_i\widehat w_i,\qquad a(W)=\min(1,W),\\
\ell_{i,h}&=\frac{
 [\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\theta))Q_{v,h}(u)]^\top
 [\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\xi_i))k_{i,h}]}{\sqrt{d_h}}
 -b^{\mathrm{pos}}_{v,h}
   (\operatorname{Pos}_v(\theta)-\operatorname{Pos}_v(\xi_i))_+,\\
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

数学状态中的 $k_i$ 保持未旋转形式，$\nu_i,p_i$ 也不施加旋转。上述旋转满足

$$
\operatorname{Rot}_{v,h}(p)^\top\operatorname{Rot}_{v,h}(q)
=\operatorname{Rot}_{v,h}(q-p),
$$

故旋转后的匹配依赖相对坐标，并包含各频率对应的相位信息。下面三种配置共用式 (16)：

| 配置 | 旋转维数 | 距离偏置 |
|---|---|---|
| NoPE | $d^{\mathrm{rot}}_{v,h}=0$ | $b^{\mathrm{pos}}_{v,h}=0$ |
| 完整 RoPE | $d^{\mathrm{rot}}_{v,h}=d_h$，要求 $d_h$ 为偶数 | 通常为零 |
| 部分 RoPE | $0<d^{\mathrm{rot}}_{v,h}<d_h$，旋转维数为偶数 | 通常为零 |

NoPE 的 Full 匹配使用内容，时间窗口、摘要和状态顺序仍保留时间信息。可选的线性距离偏置在 softmax 中乘入 $e^{-b^{\mathrm{pos}}_{v,h}\Delta p_+}$，是一种距离衰减；它与 RoPE 的旋转可以分别配置。

非空有效记忆的权重全为 $1$ 时，式 (16) 恰为所选位置配置下的普通多头 Attention；结合式 (5) 的独立投影特例可恢复常用的 K、V 参数化。最后一条弱记忆消失时，$a(W)$ 使读出趋零；只把弱权重放进 softmax 分子、分母会相互抵消，不能得到这一性质。$a(1)=1$，单位记忆保持原尺度。

取 $W_v^O\in\mathbb R^{d\times d}$、$W_v^{\mathrm{gate}},W_v^{\mathrm{up}}\in\mathbb R^{d_f\times d}$、$W_v^{\mathrm{down}}\in\mathbb R^{d\times d_f}$ 以及非负残差尺度 $\alpha_{\mathrm{att}},\alpha_{\mathrm{ff}}$，定义

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

第二行为预归一化的 SwiGLU 前馈残差。查询、Attention 和前馈只在需要正门控内容时求值。载荷函数 $\operatorname{EmitValue}_v:S_v\times\mathbb N\times X_v\times\mathsf C_v\to P$ 定义为

$$
\operatorname{EmitValue}_v(q^{\mathrm{cmp}},\theta,(r,u),c)
=\begin{cases}
(0,0),&c=0,\\
(c,G_v(q^{\mathrm{cmp}},\theta,u)),&c>0.
\end{cases}
\tag{18}
$$

发送贡献是 $cG_v$，门控作用于整个内容，包括输入残差。上界已经约束 $c$，不再发送 $(\mu_v c,\cdot)$，也不把内容预先写成 $cG_v$ 后再乘一次 $c$。记忆权重、Attention 归一化权重与发送门控承担不同角色。

在三个层级中统一定义广播提升

$$
\Delta_v(p)=
\bigl((p)_{a\in\operatorname{Out}(v)},
      (p)_{o\in\operatorname{OutPort}(v)}\bigr),
\qquad \operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v.
$$

三层都只对 $v\in A$ 调用 Full。一次激活向所有出边和输出端口发送同一个载荷；来源信息在接收时由固定边标签提供。本设计未再加入按出边分配的门控。

零分支使 Full 在整个控制空间上有定义。支持集规格不调用它；全候选参考规格可以在 Attention 前直接返回。Full 只读既定快照，产生的内容经下游接收影响下游记忆。

### 2.8 输出边界与连续读出

先固定有限输出槽集合 $\Lambda\subseteq\mathbb N\times\mathsf O$。从完整输出记录 $Z$ 取

$$
Z_\Lambda=\{z\in Z:(\operatorname{outtime}(z),\operatorname{outport}(z))\in\Lambda\}.
$$

对任意有限输出记录集合 $\mathcal M$，将其载荷记为 $(m_i,z_i)$，定义

$$
O(\mathcal M)=\frac{\sum_i(m_i)_+z_i}{\max(1,\sum_i(m_i)_+)},\qquad
\operatorname{ReadOut}_\Lambda(Z)=O(Z_\Lambda).
\tag{19}
$$

空集合给零向量。待声明槽位全部确定后求值。一个单位载荷原样读出，多个相同单位载荷的读出保持原尺度，总强度趋零时读出趋零。原始输出的端口和时间身份仍保留在 $Z$ 中；全零输出与缺席输出均读出零。

组合配置选择有限集合 $\Lambda$，并声明其任务含义。例如序列模型可为每个输入位置指定一组 $\Lambda_t$，令 $O_t=\operatorname{ReadOut}_{\Lambda_t}(Z)$。这种数值汇集发生在图外，不增加图内作用或输出记录。

### 2.9 局部绑定与组合条件

本函数族的配置先选择聚合绑定、记忆描述 $\mathfrak m_j$ 与评分 $\mathfrak s_j$，再给出各宽度、$T_v,\epsilon$、矩阵与偏置、残差与评分尺度、摘要衰减率、位置函数、Read 与 Full 各自的旋转维数和频率、可选距离偏置、$\gamma_v$，以及各区域的 $k_j,\eta_j$。软规格另给 $\tau_{\mathrm{soft}}$ 和支持集／全候选规则；硬规格采用第 2.5 节。它们在单次前向期间不变；分段继续同一次运行时使用同一配置。

| 共同对象 | 局部绑定 |
|---|---|
| $P,X_v$ | $\mathbb R^{1+d}$ |
| $S_v,q_v^{\mathrm{init}}$ | 式 (4) 的有限 KV 序列、空初态 |
| $D_v,\mathsf C_v,Y_j$ | 第 2.3 节的 $D_v^{\mathfrak s_j}$，$[0,1]$，$\{*\}$ |
| $\operatorname{Agg}_v,\operatorname{Upd}_v$ | 式 (3) 或 (3a)、式 (6) |
| $\operatorname{Read}^{0,-,+}_v$ | 式 (10)，实际描述模式 $\tau_j=+$ |
| $\operatorname{SelStep}_{j,C}$ | 由第 2.3 节取得评分，再取软式 (11)--(13) 或硬式 (14)，历史保持 |
| $\kappa_j,\operatorname{Next}_v$ | $\kappa_j=1$、式 (15) |
| $\operatorname{Full}_v$ | 三层均取 $\Delta_v\circ\operatorname{EmitValue}_v$，载荷由式 (18) 给出 |
| 数值读出 | 式 (19) 的 $\operatorname{ReadOut}_\Lambda$，槽集合由组合配置给出 |

空候选时 $\operatorname{SelStep}_{j,\varnothing}(*,\theta,())=(\varnothing,(),*)$。所有函数沿正典参数次序，Agg 接收完整原子集合，Full 返回逐边／逐端口两个值族。正典中的描述模式 $\tau_j$ 与平滑参数 $\tau_{\mathrm{soft}}$ 分别定义。

组合时还须满足：$1\le k_j\le|\mathcal R_j|$；来源映射覆盖所有输入端口和入边标签；共享参数与各节点宽度相容；Read 的描述空间与该区域 SelStep 相容；窗口、摘要衰减和位置坐标的尺度明确；每个读出组的端口、时刻及输入位置含义明确。硬化结论另需第 5.2 节的输入与间隔条件。

## 3. 一个区域的完整流程

### 3.1 先接收写入，再选择 Full

取无内部边的区域 $\{a,b,c\}$，初始缓存为空，$d=d_s=H_{\mathrm{att}}=1$、$\epsilon=1$、$\alpha_{\mathrm{agg}}=0$、$\gamma_v=1$，位置配置取 NoPE，采用时间摘要与独立评分。本次 $a$ 收到 $(0.5,1),(0.5,1)$，$b$ 收到 $(1,-1)$，$c$ 收到 $(0,9)$。三个节点都是候选。令 key、query 为零，value 与摘要投影均为 $\sqrt2$，故单位内容的归一化投影仍是 $\pm1$。

评分网络输出常数 $s=(2,1,100)$，可由零输出权重与相应偏置实现。取 $\eta_j=0,k_j=1,\tau_{\mathrm{soft}}=2$。

| 节点 | 聚合 $(r,u)$ | 新写入 $(k,\nu,p,w)$ | 上界 $\mu$ | 评分 $s$ | 门控 $c$ |
|---|---|---|---|---|---|
| $a$ | $(1,1)$ | $(0,1,1,1)$ | $1$ | $2$ | $0.75$ |
| $b$ | $(1,-1)$ | $(0,-1,-1,1)$ | $1$ | $1$ | $0.25$ |
| $c$ | $(0,0)$ | 不追加 | $0$ | $100$ | $0$ |

式 (12) 取 $\lambda=0.5$。零强度的 $c$ 不占预算。三者都完成状态采用，此时尚未计算 Full。

令 $W_v^O=1,\alpha_{\mathrm{att}}=1,\alpha_{\mathrm{ff}}=0$。$a,b$ 的 Attention 分别读出 $1,-1$，Full 内容为 $2,-2$，发送 $(0.75,2),(0.25,-2)$。若直接作为终端，$O=1$；若共同到达采用式 (3) 且 $\alpha_{\mathrm{agg}}=0$ 的下游，则下游得到 $(r,u)=(1,1)$，再开始自己的接收流程。

保持评分不变，将温度降到 $0.5$，门控已经是 $(1,0,0)$，只执行 $a$ 的 Full，终端 $O=2$。将阈值改为 $\eta_j=3$，同一温度下门控保持不变；在原温度 $2$ 下仍为 $(0.75,0.25,0)$，可取 $\lambda=-2.5$。这里上下质量界都为 $1$，共同阈值不改变分配。硬函数在全部有效评分低于阈值时仍选最高分的 $a$；$c$ 的零上界使其始终不参与选择。

这里的零前馈尺度用于手算。训练时可用非零小残差尺度，让对应参数从任务中取得反馈。

### 3.2 未激活节点的记忆如何在以后有用

再取同一区域的两个节点 $a,b$，各有输入与输出端口，没有内部边。各输入端口在时间 $1,4$ 分别收到 $(1,1),(1,-1)$，取 $T_a=T_b\ge4$。沿用上一例的投影与 Full，每次读出同刻两个端口的输出；硬规格 $k_j=1,\eta_j=0$，评分改为

$$
s_a=0.5,\qquad
s_b=0.75-M_{\mathrm{long}}^{\mathrm{sum}}(\widetilde q_b,\theta).
$$

这属于式 (8) 的网络：$\operatorname{SiLU}(x)-\operatorname{SiLU}(-x)=x$，两个隐藏单元即可表达该线性项。

| 位置 | 两节点新写入的 $(\xi,\nu,p,w)$ | $M_{\mathrm{long}}$ | $(s_a,s_b)$ | 激活者 | 终端 $O$ |
|---|---|---|---|---|---|
| $0$ | $(1,1,1,1)$ | $1$ | $(0.5,-0.25)$ | $a$ | $2$ |
| $1$ | $(4,-1,-1,1)$ | $0$ | $(0.5,0.75)$ | $b$ | $-1$ |

第一次 $b$ 未激活，但保留 $+1$ 的记忆。第二次它的 Attention 读出 $(1-1)/2=0$，残差内容为 $-1$；若误删第一次未激活时的写入，Attention 会返回 $-1$，Full 内容变成 $-2$。私有状态提供了跨位置的选择与计算依据，但能否学会利用这种依据，仍取决于后续 loss 的信用路径。

### 3.3 区域 query 如何随候选变化

取 $d_{\mathrm{sel}}=2$，两个候选的描述量满足

$$
\begin{aligned}
\mu_a=1,\quad &x_a^{\mathrm{sel}}=(1,0),\quad K_a^{\mathrm{sel}}=(\sqrt2,0),\\
\mu_b=\varepsilon,\quad &x_b^{\mathrm{sel}}=(-1,0),\quad K_b^{\mathrm{sel}}=(-\sqrt2,0),
\qquad 0\le\varepsilon\le\tfrac12.
\end{aligned}
$$

取 $\alpha_j^{\mathrm{loc}}=0,\alpha_j^{\mathrm{sel}}=1$，$\psi_j(x_1,x_2)=(x_1,0)$。这个函数属于式 (9b)：取零偏置、$W_j^{\mathrm{in,sel}}=\left(\begin{smallmatrix}1&0\\-1&0\end{smallmatrix}\right)$、$W_j^{\mathrm{out,sel}}=\left(\begin{smallmatrix}1&-1\\0&0\end{smallmatrix}\right)$，利用 SiLU 的差恒等式即可。

于是

$$
Q_j^{\mathrm{sel}}=\left(\frac{1-\varepsilon}{1+\varepsilon},0\right),\qquad
s_a=\frac{1-\varepsilon}{1+\varepsilon},\quad s_b=-s_a.
$$

取 $k_j=1,\eta_j=0,\tau_{\mathrm{soft}}=1$。总质量为 $1$，投影给出

$$
c_b=\max\left(0,\frac{3\varepsilon-1}{2(1+\varepsilon)}\right),
\qquad c_a=1-c_b.
$$

在给定范围内 $c_b\le\varepsilon$。当 $\varepsilon=1/2$ 时，门控为 $(5/6,1/6)$；当 $\varepsilon\le1/3$ 时为 $(1,0)$。$b$ 在未激活但有正上界时仍参与 query，其上界趋零后影响连续消失，得到只保留 $a$ 的结果。加入任意零上界候选也不会改变 query 或这些控制量。

## 4. 零消息、状态投影与数值尺度

### 4.1 在同一逻辑时刻比较有效缓存

缓存长度可以变化，过期条目也可能尚未物理清理。固定有限切面 $B$，对从空初态可达的缓存按原始时间槽对齐，缺失槽补零。在比较时刻 $\theta\le B$ 定义

$$
\pi_{\mathrm{KV},v,\theta}(q)
=\bigl(
\chi_{v,\theta}(\xi)w_\xi,\
\chi_{v,\theta}(\xi)w_\xi k_\xi,\
\chi_{v,\theta}(\xi)w_\xi\nu_\xi,\
\chi_{v,\theta}(\xi)w_\xi p_\xi
\bigr)_{0\le\xi\le B}.
\tag{20}
$$

候选快照在其处理时间比较，切面状态在切面时间比较。这里比较的是可读的加权记忆，不要求弱条目的裸 key/value 收敛。

一条任意弱的正接收可能触发式 (6) 清掉旧过期项，而零接收保留原列表，故保存列表未必连续。式 (20) 在两种情况下都把过期项置零；这些项以后也不会重新进入窗口。前向连续性因此使用这个时刻相关投影，固定规格的精确求值仍须返回该规格要求的原始状态。

### 4.2 弱消息与最后一条记忆

在有限有界输入邻域内，式 (3) 或 (3a) 是内容的加权平均加有界非线性项，$u$ 有界。正极限接收强度处，$u$ 连续；总强度趋零时，$u$ 未必有唯一极限，但新条目的 $w,wk,w\nu,wp$ 全部趋零。归一化中的固定 $\epsilon>0$ 保证投影不因零范数出现奇点。

固定 $\theta$ 时，窗口遮罩和时间衰减只取决于原始时间身份。有效总权重 $W\to0$ 时，式 (16) 满足

$$
\|R_{v,h}\|_2\le a(W)\max_i\|\nu_{i,h}\|_2\longrightarrow0.
$$

固定位置函数与旋转频率后，这些结论对 NoPE、完整及部分 RoPE 均成立。旋转保持范数，固定时间槽使位置和窗口不随弱消息消失而移动。若用有效条目的序号编码位置，删除一个弱条目可能改变其后所有位置，便失去此前提。有界性与读取连续性的证明见附录 A.2--A.3。

### 4.3 选择与候选消失

固定 $\tau_{\mathrm{soft}}>0$，式 (11) 的解随评分与上界连续，并在固定截断模式内分段光滑。候选消失可按上界为零的坐标比较。正极限上界处评分须收敛，趋零上界处评分有界即可。时间摘要和内容检索均满足相应读取条件；区域 Attention 的加权 query 排除消失候选的影响，保留候选的评分因而收敛。

接收上界使弱候选的门控随接收强度消失；当整个区域的可用质量趋零时，质量下限也趋零。全零纤维与无纤维都保持状态，硬函数也忽略零上界。由此得到：

> [!theorem] 性质 1：零消息删除
> 在本函数族的软或硬规格中，增加或删除零强度消息不改变其余正强度计算及有效状态、局部消息投影和外部读出。软支持集规格与全候选参考规格具有相同的这些数值；原始候选、Full、消息和输出事件记录可以不同。

选择连续性与性质 1 的正式证明见附录 A.4--A.5。同一固定规格的等价求值必须保留全部规范记录；前向投影相等与反向规则相等分别检验。

### 4.4 各种权重的职责与衰减

| 数量 | 含义 | 避免的混淆 |
|---|---|---|
| $r,u$ | 收到多少强度、其聚合内容 | 不把 $u$ 先乘 $r$ 再写入 |
| $w(r)$ | 当前信息进入记忆的权重 | 不由本节点是否选中决定 |
| $\mu_v(r)$ | 当前可发送强度的上界 | 可以适度放大可用性，不篡改写入证据 |
| Attention 权重与 $a(W)$ | 记忆内的读取比例、总记忆消失的尺度 | 单位记忆不固定衰减 |
| $c_v$ | 整个 Full 内容的发送强度 | 不再额外乘一次 $\mu_v$ 或 $c_v$ |

令 $\alpha_{\mathrm{agg}}=\alpha_{\mathrm{att}}=\alpha_{\mathrm{ff}}=0$，单位门控单路径给出 $(1,u)\mapsto(1,u)$，可作为尺度基准。恢复残差分支后，尺度还受网络参数控制；带来源聚合会改变内容，不能再把整块称为恒等映射。

真实弱记忆和真实弱发送仍可能各带一个小因子。多层竞争也可能积累衰减；反之，较大的 $\gamma_v$ 会在非零接收处补偿可用性，并较快进入饱和区。内容残差、可调上界及非零小残差尺度旨在改善这些权衡，不保证深层梯度或任务质量。

## 5. 退火、训练与硬稀疏端点

### 5.1 有限切面上的软连续性

> [!theorem] 命题 2：固定正平滑参数的数值连续性
> 固定有限正时延图、有限输入槽集合、时间编码、全部参数与配置，包括窗口、位置函数和旋转频率，以及有限切面 $B$。从空缓存开始，若输入的式 (2) 投影收敛到合法端点输入，且所考察输入内容有界，则固定 $\tau_{\mathrm{soft}}>0$ 下，切面以前按时间对齐的局部消息与 Full 各载荷的式 (2) 投影、KV 状态的式 (20) 投影及切面以前有限输出槽的连续读出收敛到端点运行。相同结论适用于 $\tau_{\mathrm{soft}}$ 趋向一个正值。

证明见附录 A.6。关键是弱写入与弱发送都带趋零权重，区域 query 使用发送上界加权，且位置及窗口按固定时间槽解释。证明适用于第 2 节的全部聚合、记忆描述与评分组合。

本命题的局部 Full 断言指式 (18) 的节点载荷，在三个层级均逐边、逐端口比较；外部汇集按第 2.8 节的读出比较。本命题允许候选消失、有效候选全空和正时延反馈。原始缓存列表、激活集合、消息条数与 Full 调用数不在连续性断言内；输入槽的离散时间身份和窗口长度也不随极限变化。连续依赖这些读出的 loss 随之连续，梯度连续和优化收敛则是其他问题。

### 5.2 收敛到硬模型所需的间隔

先看一次选择的极限问题。设端点 $\mu_v\in\{0,1\}$，有效候选按 $t_v$ 降序排列。以下条件保证线性目标 $\sum_vt_vc_v$ 在式 (11) 的极限可行集上有唯一最优解，恰为式 (14)：

- 有效候选至多一个时，无须评分条件。
- $k_j=1$ 且有效候选至少两个时，最高分与次高分严格分离；无须阈值间隔。
- $k_j>1$ 且有效候选至少两个时，各有效评分满足 $t_v\ne0$。若正评分数超过 $k_j$，要求第 $k_j$ 名与下一名严格分离；若没有正评分，要求最高分与次高分严格分离。

让 $\tau_{\mathrm{soft}}\downarrow0$，上界收敛，正极限上界候选的评分收敛，消失候选的评分有界，则软解收敛到硬解。稳定 ID 平票只定义硬函数，不决定软极限。选择极限及下述有限温度结论的证明见附录 A.4。

对已经固定的二元上界与评分，这些条件还使足够小的正温度精确达到硬门控。有效候选至多一个时，任意正温度都精确。其余情况下，$k_j=1$ 或无正评分时，可取温度不大于最高分与次高分之差；$k_j>1$ 且正评分数在 $1$ 至 $k_j$ 之间时，可取温度不大于最小正评分；正评分数超过 $k_j$ 时，可取温度不大于第 $k_j$ 名与下一名之差。

> [!theorem] 命题 3：单位输入的硬化连续性
> 固定有限正时延图、有限切面、全部模型参数与配置，以及单位强度外部输入 $(1,z)$。若硬端点运行的每次选择均满足上述对应情形的评分条件，则软规格 $\tau_{\mathrm{soft}}\downarrow0$ 的消息、有效缓存和连续读出投影收敛到硬规格。

证明见附录 A.7。单位外部强度沿硬运行给出二元发送与写入，因而满足上述选择极限的上界条件。固定的 NoPE、完整及部分 RoPE，以及第 2.3 节的四种描述与评分组合均可使用这一结论。

上述两个命题适用于任意固定有限正时延图，包括全连接分层图、连接较丰富的 HB 图、稀疏 HB 图及有反馈的图。证明按逻辑时间归纳，无需全连接或每层只有一个区域；拓扑只需在所比较的运行间固定。

这个结论依赖所列端点条件。例如 $k_j=2$、二元上界、调整后评分 $(1,0)$ 时，端点硬门控为 $(1,0)$；若第二项以 $\tau_{\mathrm{soft}}/2$ 趋零，软门控却趋于 $(1,1/2)$。选择边界平票时，软解也可能分摊而硬函数按 ID 选择。小数端点上界的反例见第 2.5 节。训练中同时改变参数、阈值或预算，还需检查它们的收敛与端点条件。

### 5.3 训练中何时真正减少计算

固定调整后评分 $t=(4,3,2,1)$、上界全为 $1$、预算 $k_j=2$：

| $\tau_{\mathrm{soft}}$ | 软门控 | 支持集规格的 Full 数／昂贵分支数 |
|---|---|---|
| $5$ | $(0.8,0.6,0.4,0.2)$ | $4/4$ |
| $2$ | $(1,0.75,0.25,0)$ | $3/3$ |
| $0.4$ | $(1,1,0,0)$ | $2/2$ |

精确零门控出现时即可省去对应 Full 和发送；若下游某节点的整个纤维因此缺席，还会省去它的聚合、KV 写入、Read 及可能的后续激活，影响可继续向后传播。当前已经收到消息的候选仍完成准备与状态更新。小而非零的门控通常仍需算完内容。软规格的正式容量仍是区域宽度，硬规格再以 $K_j=k_j$ 给出每次激活数上限。全候选参考规格可以省零分支的昂贵内容，但仍有对应 Full 与零消息记录。

固定空间拓扑上，选择决定每次实际使用的计算路径。硬化以后，有效候选非空的区域每次激活 $1$ 至 $k_j$ 个节点；具体激活者随输入和历史变化。未使用的空间边仍可在其他输入或时刻承载消息。

实际训练的评分、接收强度和记忆也在变化，因此降低温度不保证支持数量单调减少。在单次选择中固定评分、上界、温度与预算，提高阈值使各门控不增，达到质量下限后保持分配；减小预算收紧总质量上限。$k_j=1$ 时共同阈值始终无效。训练中改变这些量须分别记录，支持数、正式容量、门控质量和全图实际工作量也分别计量。命题 3 比较的是固定预算、阈值和参数下的温度极限；永久删除空间边属于另一种结构变更。

### 5.4 信用路径与饱和区

语义任务 loss 经发送贡献 $c_vG_v$，既可训练 Full，也可通过式 (11) 的门控训练评分网络、摘要与 KV 投影。区域 Attention 还将分配梯度传给共享 query、各候选 key 和内容检索；一个候选可通过共享 query 影响其他候选的评分。未激活节点的写入还可能通过未来的 Read 或 Full 获得反馈，前提是这条反向路径被保留。私有记忆让评分读取“当前输入与本节点已存证据的关系”；它增加可用条件信息，不自动提供未计算 Full 的反事实价值。

精确导数见附录 S.3。固定截断模式时，上下质量界均松弛的自由坐标有 $\partial c_v/\partial s_v=1/\tau_{\mathrm{soft}}$；任一质量界取等号时，自由坐标间通过共同乘子耦合。处于零或上界的坐标可能没有评分梯度，全部饱和时更明显。$M_j\le1$ 时 $c=\mu$，评分不影响分配；只有一个自由坐标且总质量固定时，也没有分配自由度。区域 Attention 中，零门控候选若仍有正发送上界，其内容特征可经共享 query 获得其他候选的梯度；这与其自身评分的直接导数分别计算。

归一化还会消去部分信号：当所有发送贡献同比例缩放，接收均值不变；若写入、发送上界和读出都已饱和，任务 loss 可能主要训练相对选择，难以判断绝对用量。显式的 $r$ 特征提供强度信息，成本目标偏好较少的正门控。总质量固定时，训练仍可改变质量在节点间的集中程度；这些机制均不保证有效梯度覆盖。

零门控节点不会免费获得“执行该 Full 会怎样”的内容梯度。使用精确投影的普通分段导数作为软阶段基线；在截断、$\min/\max$ 和支持边界上，实际反向规则须单独声明。始终算内容再乘零与直接跳过内容前向数值相同，某些边界反向却可不同。硬部署不需要梯度；若继续硬训练，则需另外选择替代梯度或探索机制，本文不隐含直通估计器。

同时缩放 $t$ 与温度可保持门控，因此退火要观察评分相对尺度。若固定阈值，仅放大原始 $s$，一般不等于降低温度。

### 5.5 稠密控制与训练起点

为明确稠密监督的含义，另定义训练用稠密控制，沿用 $M_j=\sum_{v\in C}\mu_v$：

$$
c_v^{\mathrm{dense}}=
\begin{cases}
\displaystyle\mu_v\frac{\min(k_j,M_j)}{M_j},&M_j>0,\\
0,&M_j=0.
\end{cases}
\tag{21}
$$

它满足式 (11) 的上下质量界，对每个正上界候选给正门控，正式容量为区域宽度，可用来预训练 Full 与记忆，或产生稠密教师。它不根据评分分配，单独使用不会训练评分网络。给已经为零的门控补一个廉价零 Full 事件，也不能替代这种稠密暴露。

软训练可从多个候选具有自由门控坐标的配置开始。例如在各候选上界均为 $1$、$|C|>k_j$ 时，让调整后评分接近 $\tau_{\mathrm{soft}}k_j/|C|$ 并带小差异，可以取得多个自由坐标与接近预算的总质量。固定评分、上界和预算，让温度趋于无穷时，门控趋向总质量为 $b_j$ 的最小范数分配；有效候选非空时，总质量保持正值，但评分差异的影响减弱。训练起点需同时校准评分尺度、温度与预算。

非零小残差尺度可以保留相应参数的任务反馈。KV 适配器的两个因子不宜同时初始化为零，否则二者的乘积路径在初始时均无梯度。对称初始化、相同输入与相同历史也可能长期保持节点冗余，节点分化需由数据与优化过程形成。

### 5.6 训练中的参数与状态

温度、阈值、预算以及参数在一次前向期间固定。第 5.2 节的硬化定理固定模型参数；训练轨迹同时改变这些量时，还须检查参数收敛、端点上界及阈值和排序间隔。前向数值连续与梯度连续、优化收敛分别判断。

有状态序列按自身逻辑历史继续，不同序列分别保存缓存。参数更新后旧缓存是否重算、是否截断反向、何时重置，均属于训练算法的选择；它们影响从写入到未来读出的信用路径。

任务接入、成本目标、教师轨迹与分阶段日程见 [[weighted-kv-layered-example#4. 训练目标与使用阶段|分层架构实例第 4 节]]。其他组合可采用自己的任务读出与训练方案，同时沿用本节的控制函数和连续性条件。

## 6. 局部批量契约

### 6.1 完整驱动纤维上的联合求值

固定区域 $j$ 与有限逻辑时间窗口 $I=[b,c)$，给定空初态可达运行在 $b$ 的区域节点状态，以及窗口内**区域全部节点、全部时间的完整输入纤维**，包括空纤维。边界缓存的写入时间均小于 $b$；关闭证据保证这些驱动纤维完整。区域历史是单点。

1. 对非空纤维应用已绑定的式 (3) 或 (3a)，对正接收计算式 (5) 的 KV、摘要特征与权重。
2. 按原始时间构造新增条目的前缀及时间窗口。正接收时过滤并追加，零接收或空纤维时保留原序列，精确恢复各时刻的保存状态。式 (7) 可用窗口和与衰减扫描；式 (7a) 可将各次 Read 查询在各自因果窗口上联合求值。
3. Read 产生所选类型的描述量，按区域与时间取得独立或区域匹配评分，再求式 (11) 或 (14)，返回激活、控制和式 (15) 的快照、下一状态。区域 query 只汇集同一时刻的完整候选。
4. 对每节点收集正式 Full 的时间集合 $\Theta$，将正门控查询组成时间批；每个查询只读取其快照内的因果时间窗口。全候选参考规格还返回全部廉价零 Full 及零消息。

前两步的写入不依赖本地选择或 Full，因此这些前缀恰好等于逐次递归状态；第三步得到同样的描述量与选择。它们构成 [[timed-dag-chunk-prefill-learning-note#3.5 区域控制—状态契约|区域控制—状态契约]] 的见证。第四步在确定快照上求同一个 Full，再按边和端口展开，构成 [[timed-dag-chunk-prefill-learning-note#3.2 逐坐标完整输出契约|逐节点 Full 契约]] 的见证。分别记为

$$
\begin{aligned}
\operatorname{BatchRegionState}^{\mathrm{KV}}_{j,I}
 &=\operatorname{RefRegionState}_{j,I},\\
\operatorname{BatchFull}^{\mathrm{KV}}_{v,\Theta}
 &=\operatorname{RefBlock}_{K^F_{v,\Theta}}.
\end{aligned}
\tag{22}
$$

第一式返回实际 $P/S/U$ 支持集、全部作用值和右边界状态；第二式返回全部正式 $F$ 值及经 $\operatorname{ExpandFull}$ 展开的消息、输出，输入输出类型均沿用正典。

这些契约何时可调用、各层级可得到怎样的批次，由 [[timed-dag-chunk-prefill-learning-note|分块预填充教材]]、[[settlegraph-learning-note#11. 节点级时间批的含义|SettleGraph]] 与 [[positive-delay-graph-finite-cut-learning-note|正时延图教材]] 给出。联合函数存在不等于特定设备上一定获得加速。

### 6.2 位置配置与分段继续

固定位置配置后，各局部函数仍只读取既定自变量。切面继续沿用正典的

$$
Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b),
\qquad
\Phi_{a,b}(Q_a,E_{[a,b)})=(\mathcal U_{[a,b)},Q_b).
$$

由相同 $Q_b$ 开始下一段，条目保留原始 $\xi_i$，新作用沿用全局 $\theta$，所以位置、遮罩、摘要及 Attention 与整段求值相同。精确区间记录仍按 $\odot_b$ 粘合。任意有限次切分，包括有空档的区间，均得到同一完整记录和右边界状态。

本函数族的 $y_j^b=*$；一般切面的 $W_b$ 仍须保留。SettleGraph 的位置边界 $b=Dt$ 满足 $W_b=\varnothing$，可由该位置及各节点状态继续。分段边界不重置时间或位置函数。这个结论保证分段求值的数学等价；可并行的批次与实际收益仍由图、可用联合契约及计算成本决定。

## 7. 局部工作与全图成本

聚合、KV 写入和 Read 在候选上执行，Full 在激活者上执行。Read 可以采用较轻的摘要，也可以承担内容检索；两者的取舍应计入后续路径所需的全部工作。下表 $m$ 为本次入消息数，$N$ 为有效 KV 项数。

| 工作 | 典型量级与条件 |
|---|---|
| 接收聚合 | $m$ 条消息的共享式 (3) 约 $O(mp_a d+p_a d)$；式 (3a) 逐消息采用自己的绑定 |
| KV 与摘要投影 | 独立求值约 $O(d^2+dr_a+dd_s)$ |
| 时间摘要、独立评分 | 朴素摘要扫描 $O(Nd_s)$；窗口和与衰减累计可减少重复扫描；评分约 $O(d_r(d+d_s))$ |
| 内容检索 | query 投影 $O(dd_s)$，已投影记忆上的检索 $O(Nd_s)$；直接重投影记忆另需 $O(Ndd_s)$，保存辅助投影则将此工作移到写入并增加存储 |
| 区域 Attention 描述量 | 每候选约 $O(d_{\mathrm{sel}}(d+d_s))$，局部评分残差按所用配置另计 |
| 区域 query 与匹配 | 每次选择约 $O(\lvert C\rvert d_{\mathrm{sel}}+d_{\mathrm{sel}}^2)$ |
| 预算分配 | 断点排序求解 $O(\lvert C\rvert\log\lvert C\rvert)$；数值求根另计精度与迭代 |
| 正门控 Full | $O(d^2+dd_f+Nd)$，$N$ 为当前有效 KV 项数 |
| 每节点缓存 | 有限窗口为 $O(T_v(2d+d_s))$；全历史在切面 $B$ 前至多 $B$ 项，另有时间、权重及可选辅助投影 |

相同来源类别与载荷的多重集，加相同聚合参数，才保证相同的 $(r,u)$。满足此条件时可共享聚合与 KV 基座投影；相同参数面对不同邻域时，仍须求不同的聚合与投影。HB 中的参数共享一般只减少参数和便于批量求值，不能自动把全区域准备合为一次。共享表示还须恢复各节点的确切状态。

记 $\mathcal E_C,\mathcal E_A$ 为一段运行内候选、激活者的节点—时间坐标，$\mathcal E_S$ 为实际区域选择坐标，$\mathcal M$ 为发出的内部消息。按不重复归属的工作量或累计执行时间，全图账本为

$$
\begin{aligned}
\mathcal W={}&\sum_{(v,\theta)\in\mathcal E_C}
 (C_{v,\theta}^{\mathrm{Agg}}+C_{v,\theta}^{\mathrm{KV}}+C_{v,\theta}^{\mathrm{Read}})
 +\sum_{(j,\theta)\in\mathcal E_S}C_{j,\theta}^{\mathrm{Sel}}\\
 &+\sum_{(v,\theta)\in\mathcal E_A}C_{v,\theta}^{\mathrm{Full}}
 +\sum_{m\in\mathcal M}C_m^{\mathrm{msg}}.
\end{aligned}
$$

共享计算计一次，必要的缓存读写和输出汇集计入相应项；算术工作量、累计执行时间和端到端时间分别报告；并行端到端时间一般不等于各项时间之和。单 query 的区域匹配未必比各节点独立 MLP 更贵；私有 KV 检索、宽投影或更大描述量则可能显著增加准备与带宽。

上游不发送，可使下游整个输入纤维缺席，从而减少后续准备、选择、Full 与消息。候选覆盖受出度、父邻域重叠和外部注入共同决定。图较宽且后续覆盖较独立时，较强的 selector 可能通过更好的路径选择抵偿本次额外成本；宽度本身不能保证这个收益，准备成本占比也不一定下降。

[[weighted-kv-layered-example#5. 整窗口求值与架构成本|全连接实例]] 与 [[weighted-kv-hb-lattice-example#4. 候选传播与全图成本|HB 实例]] 给出具体计数。比较局部方案时，同时记录任务质量、当前 Read 成本、下游候选覆盖、KV 读写、消息及总时间；较轻的局部函数与较少的全图工作是需要分别验证的结果。

## 附录 A：数值连续性的正式证明

### A.1 比较域与时间槽

固定有限正时延图、区域和端口、来源映射、全部模型参数与配置，以及整数切面 $B>0$。窗口允许 $T_v=\infty$，位置函数和频率固定。输入在 $[0,B)$ 内取自一个固定有限槽集合；各槽可有值或缺席。考虑从空缓存开始的一列运行，外部载荷内容一致有界，式 (2) 的槽投影收敛到某个合法端点输入。平滑参数的变化在相应命题中另行指定。

内部消息按边身份和发送时间对齐，输出按端口和输出时间对齐，写入按节点和原始时间对齐。缺席槽的投影取零。有限图、有限切面与正时延保证潜在槽只有有限个，包括切面前已发送而尚未到达的消息。以下收敛均为这些有限维投影的通常收敛。

同一时间的所有候选在区域内共同选择。证明中可将缺席节点补成 $\mu_v=0,c_v=0$，不增加规范作用；补入坐标的描述特征任取有界值，其对区域 query 的贡献为零；预算比较中零上界坐标的评分也可任取有界值。缓存投影始终在当前比较时刻使用式 (20)。

### A.2 有界性引理

**引理 A.1。** 在 A.1 的条件下，切面以前所有实际聚合内容、KV 内容、摘要、评分与 Full 内容一致有界。该界可选为与正温度无关。

**证明。** 对任意 $x$，$\|\mathcal N_p(x)\|_2\le\sqrt p$。因此式 (5) 的 $k,\nu,p$ 具有固定界，式 (3) 或 (3a) 的来源非线性项也有固定界。输入槽数有限、输入投影收敛，使外部有效强度一致有界；内部发送强度由 $0\le c_v\le1$ 控制。每个纤维的潜在原子数有限，故接收强度有界。

按逻辑时间归纳。给定此前发送内容的界，式 (3) 或 (3a) 的加权均值范数至多为本次输入内容范数的最大值，加来源项后仍有界。每节点在 $[0,B)$ 至多写 $B$ 项，$0\le w_i\le1$，式 (7) 的摘要有界。式 (7a) 的投影、固定时间槽上的旋转和 logit 有界，检索结果为有界 value 的凸组合乘以至多为 $1$ 的尺度，故同样有界；式 (8) 的局部评分随之有界。式 (9a) 的特征与 key 有界，式 (9b) 的加权汇集范数不超过特征范数的最大值，经过固定连续网络后，区域 query 与全部评分也有界。旋转矩阵范数为 $1$；有限个时间槽的位置值与距离偏置有限，所以式 (16) 的有效 logit 一致有界。Attention 是有界 value 的凸组合乘 $a(W)\le1$，仍有界。式 (17) 的前馈分支输入经归一化有界，故 Full 内容有界，完成归纳。正时延使这一步只使用更早时间的界。$\square$

本引理只给出固定有限切面上的界，不断言界随 $B$ 增大仍一致。

### A.3 聚合、写入与读取引理

**引理 A.2。** 在 A.2 的有界范围内，有下列结论：

1. 输入槽的式 (2) 投影收敛时，$r$ 收敛；若极限 $r^*>0$，则 $u\to u^*$。
2. 输入槽投影与旧缓存的有效投影均收敛时，接收后的有效投影也收敛。此结论包含 $r^*=0$ 和纤维缺席。
3. 有效缓存投影收敛时，式 (7) 的摘要收敛；若同时 $u\to u^*$，则式 (7a)、(16)--(17) 的检索、读取与内容函数收敛。正极限接收处的局部描述特征因此收敛，其余处保持有界。
4. 在同一区域所有候选同时满足以上条件时，式 (9b) 的 query 收敛，正极限上界处的最终评分收敛，其余评分保持有界。

**证明。** 各槽有效强度及强度乘内容均收敛，故 $r$ 及加权内容和收敛。正极限强度槽的内容可从这两个坐标相除恢复；零极限强度槽对有界来源非线性项的加权贡献趋零。若 $r^*>0$，式 (3) 或 (3a) 的加权分子收敛，分母趋于正数，得到第一项。

正极限接收处，式 (5) 的投影函数和 $w(r)$ 连续。若 $r\to0$，其有界性给出

$$
(w(r),w(r)k_v(u),w(r)\nu_v(u),w(r)p_v(u))\longrightarrow0.
$$

旧槽的遮罩按固定 $\xi$ 取值；式 (6) 清掉的条目在当前时刻的有效投影已经为零。可达旧条目均写于当前时刻以前，以后遮罩也不会从零变回一。因此零接收时保留旧列表与微弱正接收时清理旧列表具有相同的投影极限，并可继续传到下一个比较时刻，得到第二项。

式 (7) 是有效 $w,wp$ 坐标乘固定衰减后求和，再除以至少为 $1$ 的连续分母，故摘要连续。对 Attention，记 $\widehat w_i=\chi_{v,\theta}(\xi_i)w_i$。若极限 $W^*>0$，每个正极限权重槽的 $k_i,\nu_i$ 可由有效加权坐标除以权重恢复；其 logit 与 value 收敛。零极限权重槽的 $\widehat w_i e^{\ell_{i,h}}$ 与 $\widehat w_i e^{\ell_{i,h}}\nu_{i,h}$ 趋零，因为引理 A.1 给出一致界。分母极限严格为正，故商收敛。若 $W\to0$，则

$$
\|R_{v,h}\|_2\le\min(1,W)\max_i\|\nu_{i,h}\|_2\longrightarrow0,
$$

其中空列表的上界取零。式 (7a) 的 $W_a$ 使用固定时间衰减，投影与旋转连续且有界，故逐项重复上述商与零总权重论证，得到检索连续性。再应用式 (17)、(8)、(9a) 的连续运算，得到第三项。

最后在区域中将缺席候选补成零上界。若 $\mu_v^*>0$，则 $r_v^*>0$，其 $x_v^{\mathrm{sel}},K_v^{\mathrm{sel}},s_v^{\mathrm{loc}}$ 收敛；若 $\mu_v\to0$，有界性给出 $\mu_v x_v^{\mathrm{sel}}\to0$。式 (9b) 的分子和分母因此收敛，分母至少为 $1$，故 query 收敛。正极限上界候选的匹配评分随之收敛，其余评分由引理 A.1 保持有界，得到第四项。$\square$

### A.4 带上下质量界的选择引理

**引理 A.3。** 固定含 $m$ 个坐标的有限候选集与整数预算 $k\ge1$。设 $\mu^{(n)}\to\mu^*$，各上界属于 $[0,1]$，评分 $t^{(n)}$ 一致有界，且在 $\mu_v^*>0$ 的坐标上收敛到 $t_v^*$。令 $c^{(n)}$ 是式 (11) 在温度 $\tau_n>0$ 下的解。

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

后一分支有 $0<\delta_n\le R_n$，修正后总质量为 $b(\mu^{(n)})\le k$，故 $d^{(n)}\in F(\mu^{(n)})$。又因 $a^{(n)}\to d$ 且 $\sum_vd_v\ge b(\mu^*)$，修正量 $\delta_n\to0$，从而 $d^{(n)}\to d$。

令 $I_0=\{v:\mu_v^*=0\}$，将这些坐标的评分改成零，得到 $\widetilde t^{(n)}$。若原评分绝对值至多为 $M$，这个替换在整个 $F(\mu^{(n)})$ 上改变目标至多

$$
\epsilon_n=M\sum_{v\in I_0}\mu_v^{(n)}\longrightarrow0.
$$

替换后的目标 $\widetilde f_n(c)=\widetilde t^{(n)}\cdot c-\tau_n\|c\|_2^2/2$ 在 $[0,1]^m$ 上一致收敛到极限目标 $f_*$。最优性给出

$$
\widetilde f_n(c^{(n)})
\ge\widetilde f_n(d^{(n)})-2\epsilon_n.
$$

沿上述子列取极限，得到 $f_*(\bar c)\ge f_*(d)$。因此每个聚点都是极限最优解。正温度下严格凹性给出唯一性；零温度下使用假定的唯一性。所有聚点相同，整列收敛。$\square$

**硬端点的唯一性。** 若 $\mu_v^*\in\{0,1\}$，零上界坐标固定为零。有效候选为空时，可行集只含零向量；只有一个时，质量下限强制该坐标为 $1$。以下设有效候选至少两个。

$k=1$ 时总质量为 $1$，最高分唯一便使全部质量集中于该坐标。$k>1$ 时，按第 5.2 节假设所有有效 $t_v^*\ne0$。没有正评分时，负系数使总质量恰为下限 $1$；最高分唯一再确定其分配。有正评分时，负评分坐标取零：将其质量转向未满的正评分坐标，或在正评分全满后去掉负评分质量，都严格提高目标且保持可行。正评分数不超过 $k$ 时，各正评分均取 $1$；超过 $k$ 时，第 $k$ 名的严格间隔使质量恰分配给前 $k$ 个。各情形均给出式 (14) 的唯一门控。

固定这样的评分与二元上界时，还能直接验证有限温度结论。有效候选至多一个时，可行集是单点。其余情况下，$k=1$ 或无正评分时，取 $\lambda=t_{(2)}$ 与 $\tau\le t_{(1)}-t_{(2)}$，最高分坐标为 $1$，其余为零；$k=1$ 时上下质量界同时取等号，任意符号的 $\lambda$ 均可分解为非负的 $\lambda_U-\lambda_L$；无正评分且 $k>1$ 时，$\lambda<0$ 对应下限乘子。$k>1$ 且正评分数在 $1$ 至 $k$ 之间时，取 $\lambda=0$ 与 $\tau\le\min_{t_v>0}t_v$；超过 $k$ 时，取 $\lambda=t_{(k+1)}>0$ 与 $\tau\le t_{(k)}-t_{(k+1)}$。代入式 (12) 均得到硬门控并满足互补条件。

### A.5 性质 1 的证明

增加或删除零强度原子不改变式 (3) 或 (3a) 的加权和。已有正接收处的写入与局部描述保持；仅含零消息的纤维有 $r=0$，式 (6) 保持状态，式 (9) 给出 $\mu=0$。式 (7) 与 (7a) 的既有读取保持不变；式 (9b) 中零上界候选对 query 的分子、分母贡献均为零，其他候选的最终评分也保持。因此这类候选加入软优化时只增添强制为零的坐标，$M_j,b_j$ 均不变；加入硬排序时也不进入 $C_{\mathrm{eff}}$。其他候选的控制量与单点历史保持。

支持集规格在这些坐标不执行 Full；全候选参考规格按式 (18) 产生零载荷。沿正时延按时间归纳，这些额外零消息只会重复上述情形，不改变后续正强度计算和状态。时间、位置、窗口均不重排，故有效状态、式 (2) 的槽投影及式 (19) 的读出相同。额外候选与零 Full、消息、输出的存在身份可以不同。$\square$

### A.6 命题 2 的证明

令正温度固定或趋于正值。按 $\theta=0,\ldots,B-1$ 归纳，并在每个切面比较有效状态。初始状态为空。正时延使当前内部输入只来自已经比较的更早发送槽，结合外部输入假设，当前完整纤维的载荷投影收敛。由引理 A.2，接收后有效缓存收敛，发送上界收敛，正极限接收处评分收敛，其余评分由引理 A.1 保持有界。缺席候选按 A.1 补成零上界，有效候选全空的情形也包含在内。

引理 A.3 给出控制量收敛。若端点 $c_v^*>0$，由 $c_v\le\mu_v(r)$ 得到 $r_v^*>0$，聚合内容及 Full 内容收敛。若 $c_v^*=0$，实际 Full 内容保持有界，所以

$$
\pi_P(\operatorname{EmitValue}_v)
=(c_v,c_vG_v)\longrightarrow0;
$$

未调用 Full 的槽同样按零比较。广播逐边、逐端口保持这一结论。BO 与默认 Next 将接收后的状态直接采用，引理 A.2 的固定遮罩论证又给出下一切面的有效状态收敛，完成归纳。稀疏空档只传递原状态并推进比较时刻。

最后，式 (19) 的分子是消息投影中内容贡献的有限和，分母是有效强度和与 $1$ 的最大值，始终为正，故所有切面以前有限槽的读出收敛。$\square$

### A.7 命题 3 的证明

在硬端点运行中，初始无内部消息，外部强度为 $1$。若更早发送强度均为 $0/1$，当前总强度便为非负整数；$\gamma_v\ge1$ 使 $\mu_v\in\{0,1\}$，式 (14) 再发送 $0/1$。按时间归纳，所有硬端点上界与非零写入权重均为二元值。

现在让软温度趋零，按 A.6 的同一归纳比较软运行与硬端点。聚合、缓存及正接收处评分的收敛仍由引理 A.2 给出。每次硬端点选择满足第 5.2 节对应情形的评分条件，因此 A.4 给出唯一线性最优解，恰为该次硬门控；引理 A.3 的零温度结论给出软控制量收敛。后续发送和状态采用与 A.6 相同，故消息、有效缓存及连续读出收敛。$\square$

这些命题允许有限切面内的正时延反馈，但不推出无限时域稳定性、梯度连续性或训练收敛。位置函数、频率、离散时间槽和窗口固定，是上述比较的共同前提。

## 附录 S：计算表示与数学对象

### S.1 状态、旋转与解码

沿用正典的“表示解码，再遗忘辅助坐标”两步关系。共享 KV 存储和不可变窗口视图可以表示式 (4) 的序列。设表示空间为 $\widehat S_v$、解码函数为 $\operatorname{decode}_v:\widehat S_v\to S_v$，每个 Full 视图须满足 $\operatorname{decode}_v(\widehat q^{\mathrm{cmp}}_{v,\theta})=q^{\mathrm{cmp}}_{v,\theta}$。边界缓存作为左前缀，新增条目按时间追加；视图还需保留本规格清理后的确切序列范围，包括尚未触发清理时的过期条目身份。

联合求值可先返回这种表示，经固定 Decode 得到数学值记录，再由 $\Pi_K^{\mathrm{blk}}$ 删除辅助字段。解码忠实恢复已经表示的序列、控制和快照，不调用参考递归补写或修补结果。按式 (20) 比较有效状态允许某些原始列表不同，不可据此声称同一规格的完整记录相等。进一步压缩或提前清理若不能解码为原状态，就需另行声明所比较的投影。

实现可保存原始 key，也可保存 $\widehat k_{i,h}=\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\xi_i))k_{i,h}$。后一表示经同一配置的逆旋转恢复原始 key；每项仍须保留 $\xi_i$，用于窗口、摘要和解码。Query 在自己的处理时间旋转，已旋转 key 避免重复旋转。节点、时间和配置身份共同确定旋转含义。

跨 chunk 继续须保存可恢复的 $Q_b$，并使用同一参数与位置配置。更改频率、坐标尺度或局部函数后，旧缓存通常已包含旧计算的结果；仅重旋转 key 不足以取得新规格从头运行的状态。继续、重算或显式状态转换应各自声明比较关系。

式 (7a) 的检索投影须从原始 key 取得，再施加 Read 自己的旋转；Full 的已旋转 key 通常不能直接代入该投影。可额外保存检索 key/value 投影，作为固定参数下的辅助表示，主状态仍须按声明解码。

式 (16) 可对正有效权重使用 $\ell_{i,h}+\log\widehat w_i$ 的稳定 softmax，再乘 $a(W)$；零权重遮罩，空记忆直接返回零。式 (7a) 同样可在正权重上采用稳定加权 softmax，并乘 $\min(1,W_a)$。KV 内容与权重分开保存，不以微小权重作除法恢复内容。有限精度下的下溢、近零阈值裁剪及替代反向需要另行声明；它们不能直接冒充本文的精确零规则或数学连续性结论。

### S.2 配置与数学规格

组合配置逐区域选择聚合共享方式、记忆描述、Read 与 SelStep 的成对绑定、节点宽度、窗口、位置函数，以及 Read 和 Full 的旋转参数，再绑定图、时间、来源及读出。宽度、坐标配对、预算和端口类型检查通过后，得到确定的参数空间和状态空间；给定参数值、初态和输入，参考递归唯一确定前向记录。

下游可以为这些模块提供同名构造器，从配置建立可训练模型，训练后以相同配置加载参数进行推理。切换已支持的 NoPE、完整或部分 RoPE、区域窗口和频率，不必人工修改源代码；是否重新生成计算图或专用内核由实现决定。配置变化可能改变参数形状与训练所得函数，已有权重的兼容性另行验证。

异构组合可给其他区域绑定不同的状态、Upd、Read 和 Full，但须先完整定义该函数族及其组合条件。本文证明覆盖所定义的 KV 函数；循环记忆需要自己的零消息、状态连续性及批量求值论证。正时延反馈图还须由任务声明有限切面与读出时刻。

### S.3 预算投影的求解与反向

先计算 $M_j,b_j$；$M_j\le1$ 时直接返回 $c=\mu$。其余情况下，式 (12) 的每个坐标在 $t_v-\tau_{\mathrm{soft}}\mu_v$ 与 $t_v$ 处改变截断模式。先求 $\lambda=0$ 的门控；质量超过 $k_j$ 时在非负半轴上求和为 $k_j$ 的解，低于 $b_j$ 时在非正半轴上求和为 $b_j$ 的解，其余保持 $\lambda=0$。排序相应断点并扫描即可定位有效区间。

令自由集为 $F=\{v:0<c_v<\mu_v\}$，上界集为 $U=\{v:c_v=\mu_v>0\}$。当总质量固定于某一边界 $B\in\{b_j,k_j\}$ 且 $F\ne\varnothing$ 时，

$$
\lambda=
\frac{\sum_{v\in F}t_v+\tau_{\mathrm{soft}}\sum_{v\in U}\mu_v
 -\tau_{\mathrm{soft}}B}{|F|}.
$$

验证它落在该区间并满足互补条件，即得到唯一门控；$F=\varnothing$ 时在满足截断与互补条件的乘子区间取值。乘子不唯一不影响门控。排序与扫描的工作量为 $O(|C|\log|C|)$；二分求根可作为另一实现，须声明终止误差。无需在网络中嵌入通用迭代优化器。

在固定截断模式和质量约束分支的内部，固定上界、预算、阈值与温度。上下质量界均松弛时，自由坐标的评分 Jacobian 为 $I/\tau_{\mathrm{soft}}$；任一质量界取等号时，其自由子块为

$$
\frac{\partial c_F}{\partial s_F}
=\frac1{\tau_{\mathrm{soft}}}
 \left(I-\frac{\mathbf1\mathbf1^\top}{|F|}\right).
$$

若上游梯度为 $g_v=\partial\mathcal L/\partial c_v$，总质量固定时自由评分的梯度是 $(g_v-\operatorname{mean}_{u\in F}g_u)/\tau_{\mathrm{soft}}$，零与上界饱和坐标的直接评分导数为零。$|F|=1$ 时该自由块也为零。上界的梯度须另计：在质量边界且 $F\ne\varnothing$ 时，固定评分有

$$
dc_v=d\mu_v\ (v\in U),\qquad
dc_v=\frac{dB-\sum_{u\in U}d\mu_u}{|F|}\ (v\in F),
$$

其余坐标为零。$M_j>1$ 时，边界 $B$ 为常数 $1$ 或 $k_j$，故 $dB=0$；上下质量界均松弛时，自由坐标不受上界变化影响。$M_j<1$ 时直接由 $c=\mu$ 得到零评分 Jacobian 与恒等的上界 Jacobian。这些是固定模式内的偏导，完整反向还须经过 $\mu$、区域 query、keys、局部评分及记忆读取的依赖。趋小温度会放大自由区导数，饱和则可能切断评分反馈。

在断点、质量界的松紧交界、$M_j=1$、$\min/\max$ 和支持边界上，选定并验证所用导数约定。排序仅用于定位分段，反向可直接使用上述分段公式。硬规格若继续训练，替代梯度或探索机制另行定义。

### S.4 下游必须核对的性质

采用本函数族的实现应固定上游提交、配置、参数和比较关系，并提供以下验证。正式证明给出数学目标，数值试验用于发现实现偏离。

| 验证对象 | 必须覆盖的情况 |
|---|---|
| 局部函数及作用结果 | 第 3 节手算、完整纤维与来源身份、未激活者写入、空候选与全零上界，以及共同 P/S/U/F 返回值族 |
| 非空选择 | 有效候选非空时至少激活一个；全低分的最高分保留、单候选、硬容量、零上界排除；$M_j\le1$ 时软门控等于上界，$k_j=1$ 时共同阈值无效 |
| 描述量与评分绑定 | 四种记忆描述／评分组合；独立评分恢复关系；区域内候选顺序置换；零上界候选不改变 query；禁止跨区域汇集 |
| 聚合与参数化 | 区域、节点、来源与适配绑定；相同标记输入时复用，邻域不同时分别求值；独立 K/V 投影 |
| 位置与检索 | Read 与 Full 的 NoPE、完整及部分 RoPE；有效权重全为单位时对应普通 Attention；SettleGraph 的 $\operatorname{Pos}_v(Dt+r_v)=t$ |
| 零消息删除 | 零载荷存在与缺席、全零纤维、支持集与全候选参考规格；数值投影相等及原始记录的差别 |
| 正温度连续性 | 弱消息、弱候选和最后一条记忆趋零；含长空档、窗口到期与清理分支；允许弱条目的裸内容有不同有界极限 |
| 硬化条件 | 固定稠密、稀疏及多区域图上逐情形满足评分条件时的温度误差；全低分最高分间隔、$k_j=1$ 的阈值无关性；$k_j>1$ 的阈值临界、边界平票和小数上界反例；验证消息与状态投影，不要求事件数连续 |
| 求解与梯度 | KKT、空集、下限／上限／双界等号与双界松弛、空／单自由集、$M_j=0,1$ 及两侧；与独立数值求解比较；自由区有限差分，query、key、检索与上界梯度；饱和和边界按声明判断 |
| 分段继续与联合求值 | 整段、不同长度的连续 chunk、逐位置 decode；无接收区间、窗口临界、位置内部切面与跨界消息；比较完整记录、快照及右边界 |
| 缓存表示 | 原始 key 与已旋转 key 的解码；相同配置继续；配置或参数改变时拒绝错误沿用等价声明 |
| 有限精度与反向 | 分别声明浮点容差、下溢和裁剪规则、各分段边界的导数约定及训练状态截断 |

含 RoPE 的比较应使用非零 query/key 和非零相对距离，并覆盖不同频率、位置尺度与稀疏写入时间。分段测试保持固定参数，在相同输入与切面条件下比较；训练途中更新参数的实验另外记录其状态管理规则。
